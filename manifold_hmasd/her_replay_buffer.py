import torch
import numpy as np
from collections import deque
import random
from logger import main_logger

class GoalConditionedExperience:
    """
    目标导向的经验样本
    """
    def __init__(self, state, action, reward, next_state, done, goal, achieved_goal, info=None):
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.done = done
        self.goal = goal  # 目标状态 s_g
        self.achieved_goal = achieved_goal  # 实际达到的状态 (通常是 next_state)
        self.info = info or {}

class HERReplayBuffer:
    """
    Hindsight Experience Replay (HER) 经验回放缓冲区
    
    核心思想：
    1. 存储原始的目标导向经验 (s, a, r, s', g)
    2. 对每个经验，生成额外的"事后"经验，其中目标被替换为实际达到的状态
    3. 重新计算对应的奖励，使失败的经验变成成功的经验
    """
    
    def __init__(self, capacity, her_strategy='future', her_k=4, reward_func=None):
        """
        初始化HER回放缓冲区
        
        参数:
            capacity: 缓冲区容量
            her_strategy: HER策略 ('future', 'episode', 'random')
            her_k: 每个原始经验生成的HER经验数量
            reward_func: 奖励函数，用于重新计算HER经验的奖励
        """
        self.capacity = capacity
        self.her_strategy = her_strategy
        self.her_k = her_k
        self.reward_func = reward_func or self._default_reward_func
        
        # 存储完整轨迹的缓冲区
        self.episode_buffer = []  # 当前episode的经验
        self.replay_buffer = deque(maxlen=capacity)  # 主回放缓冲区
        
        # 统计信息
        self.total_episodes = 0
        self.total_transitions = 0
        self.her_transitions = 0
        
        main_logger.info(f"创建HER回放缓冲区: capacity={capacity}, strategy={her_strategy}, k={her_k}")
    
    def _default_reward_func(self, achieved_goal, desired_goal, info=None):
        """
        默认奖励函数：基于目标距离的负奖励
        
        参数:
            achieved_goal: 实际达到的状态
            desired_goal: 期望的目标状态
            info: 额外信息
            
        返回:
            reward: 奖励值
        """
        # 计算欧几里得距离
        if isinstance(achieved_goal, torch.Tensor):
            achieved_goal = achieved_goal.detach().cpu().numpy()
        if isinstance(desired_goal, torch.Tensor):
            desired_goal = desired_goal.detach().cpu().numpy()
        
        distance = np.linalg.norm(achieved_goal - desired_goal)
        
        # 使用负距离作为奖励，可以添加阈值判断
        threshold = info.get('success_threshold', 0.1) if info else 0.1
        
        if distance <= threshold:
            reward = 0.0  # 成功到达目标
        else:
            reward = -distance  # 距离越远奖励越低
        
        return reward
    
    def store_transition(self, state, action, reward, next_state, done, goal, info=None):
        """
        存储单个转移经验到episode缓冲区
        
        参数:
            state: 当前状态
            action: 执行的动作
            reward: 获得的奖励
            next_state: 下一状态
            done: 是否结束
            goal: 目标状态
            info: 额外信息
        """
        achieved_goal = next_state  # 实际达到的状态就是下一状态
        
        experience = GoalConditionedExperience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            goal=goal,
            achieved_goal=achieved_goal,
            info=info
        )
        
        self.episode_buffer.append(experience)
        self.total_transitions += 1
    
    def store_episode(self):
        """
        在episode结束时，将episode缓冲区的经验处理并存储到主缓冲区
        """
        if len(self.episode_buffer) == 0:
            return
        
        episode_length = len(self.episode_buffer)
        
        # 1. 存储原始经验
        for experience in self.episode_buffer:
            self.replay_buffer.append(experience)
        
        # 2. 生成HER经验
        her_experiences = self._generate_her_experiences(self.episode_buffer)
        
        # 3. 存储HER经验
        for her_exp in her_experiences:
            self.replay_buffer.append(her_exp)
            self.her_transitions += 1
        
        # 4. 清空episode缓冲区
        self.episode_buffer = []
        self.total_episodes += 1
        
        # 记录统计信息
        if self.total_episodes % 10 == 0:
            her_ratio = self.her_transitions / max(self.total_transitions, 1)
            main_logger.debug(f"HER统计: episodes={self.total_episodes}, "
                            f"total_transitions={self.total_transitions}, "
                            f"her_transitions={self.her_transitions}, "
                            f"her_ratio={her_ratio:.3f}")
    
    def _generate_her_experiences(self, episode_experiences):
        """
        根据策略生成HER经验
        
        参数:
            episode_experiences: episode中的经验列表
            
        返回:
            her_experiences: 生成的HER经验列表
        """
        her_experiences = []
        episode_length = len(episode_experiences)
        
        for i, original_exp in enumerate(episode_experiences):
            # 为每个原始经验生成k个HER经验
            for _ in range(self.her_k):
                if self.her_strategy == 'future':
                    # Future策略：从当前时间步之后随机选择一个状态作为新目标
                    if i < episode_length - 1:
                        future_idx = random.randint(i + 1, episode_length - 1)
                        new_goal = episode_experiences[future_idx].achieved_goal
                    else:
                        continue  # 最后一步没有future，跳过
                        
                elif self.her_strategy == 'episode':
                    # Episode策略：从整个episode中随机选择一个状态作为新目标
                    episode_idx = random.randint(0, episode_length - 1)
                    new_goal = episode_experiences[episode_idx].achieved_goal
                    
                elif self.her_strategy == 'random':
                    # Random策略：随机生成目标（通常不推荐）
                    # 这里简化为从episode中随机选择
                    episode_idx = random.randint(0, episode_length - 1)
                    new_goal = episode_experiences[episode_idx].achieved_goal
                    
                else:
                    raise ValueError(f"未知的HER策略: {self.her_strategy}")
                
                # 创建HER经验
                her_exp = self._create_her_experience(original_exp, new_goal)
                her_experiences.append(her_exp)
        
        return her_experiences
    
    def _create_her_experience(self, original_exp, new_goal):
        """
        基于原始经验和新目标创建HER经验
        
        参数:
            original_exp: 原始经验
            new_goal: 新的目标状态
            
        返回:
            her_exp: HER经验
        """
        # 重新计算奖励
        new_reward = self.reward_func(
            original_exp.achieved_goal, 
            new_goal, 
            original_exp.info
        )
        
        # 创建新的经验
        her_exp = GoalConditionedExperience(
            state=original_exp.state,
            action=original_exp.action,
            reward=new_reward,
            next_state=original_exp.next_state,
            done=original_exp.done,
            goal=new_goal,  # 新的目标
            achieved_goal=original_exp.achieved_goal,  # 实际达到的状态不变
            info=original_exp.info
        )
        
        return her_exp
    
    def sample(self, batch_size):
        """
        从缓冲区中采样一批经验
        
        参数:
            batch_size: 批大小
            
        返回:
            batch: 采样的经验列表
        """
        if len(self.replay_buffer) < batch_size:
            # 如果缓冲区不够，返回全部
            return list(self.replay_buffer)
        
        return random.sample(self.replay_buffer, batch_size)
    
    def sample_tensors(self, batch_size, device):
        """
        采样并返回张量格式的批次数据
        
        参数:
            batch_size: 批大小
            device: 设备
            
        返回:
            states: 状态张量 [batch_size, state_dim]
            actions: 动作张量 [batch_size, action_dim]
            rewards: 奖励张量 [batch_size]
            next_states: 下一状态张量 [batch_size, state_dim]
            dones: 结束标志张量 [batch_size]
            goals: 目标张量 [batch_size, state_dim]
        """
        experiences = self.sample(batch_size)
        
        if len(experiences) == 0:
            return None
        
        # 提取各个组件
        states = []
        actions = []
        rewards = []
        next_states = []
        dones = []
        goals = []
        
        for exp in experiences:
            states.append(exp.state)
            actions.append(exp.action)
            rewards.append(exp.reward)
            next_states.append(exp.next_state)
            dones.append(float(exp.done))
            goals.append(exp.goal)
        
        # 转换为张量
        def to_tensor(data):
            if isinstance(data[0], torch.Tensor):
                return torch.stack(data).to(device)
            else:
                return torch.tensor(data, dtype=torch.float32, device=device)
        
        return (
            to_tensor(states),
            to_tensor(actions),
            to_tensor(rewards),
            to_tensor(next_states),
            to_tensor(dones),
            to_tensor(goals)
        )
    
    def __len__(self):
        """返回缓冲区中的经验总数"""
        return len(self.replay_buffer)
    
    def clear(self):
        """清空缓冲区"""
        self.replay_buffer.clear()
        self.episode_buffer.clear()
        self.total_episodes = 0
        self.total_transitions = 0
        self.her_transitions = 0
        main_logger.info("HER缓冲区已清空")
    
    def get_statistics(self):
        """
        获取缓冲区统计信息
        
        返回:
            stats: 统计信息字典
        """
        her_ratio = self.her_transitions / max(self.total_transitions, 1)
        
        stats = {
            'buffer_size': len(self.replay_buffer),
            'capacity': self.capacity,
            'utilization': len(self.replay_buffer) / self.capacity,
            'total_episodes': self.total_episodes,
            'total_transitions': self.total_transitions,
            'her_transitions': self.her_transitions,
            'her_ratio': her_ratio,
            'her_strategy': self.her_strategy,
            'her_k': self.her_k,
        }
        
        return stats

class ManifoldDistanceReward:
    """
    基于流形距离的奖励函数，用于HER
    """
    def __init__(self, vae_model, distance_threshold=0.1, success_reward=0.0, 
                 distance_weight=1.0, use_latent_space=True):
        """
        初始化基于流形距离的奖励函数
        
        参数:
            vae_model: 训练好的VAE模型
            distance_threshold: 成功阈值
            success_reward: 成功时的奖励
            distance_weight: 距离权重
            use_latent_space: 是否在潜空间中计算距离
        """
        self.vae_model = vae_model
        self.distance_threshold = distance_threshold
        self.success_reward = success_reward
        self.distance_weight = distance_weight
        self.use_latent_space = use_latent_space
    
    def __call__(self, achieved_goal, desired_goal, info=None):
        """
        计算基于流形的奖励
        
        参数:
            achieved_goal: 实际达到的状态
            desired_goal: 期望的目标状态
            info: 额外信息
            
        返回:
            reward: 奖励值
        """
        # 转换为张量
        if not isinstance(achieved_goal, torch.Tensor):
            achieved_goal = torch.tensor(achieved_goal, dtype=torch.float32)
        if not isinstance(desired_goal, torch.Tensor):
            desired_goal = torch.tensor(desired_goal, dtype=torch.float32)
        
        # 确保是二维张量
        if achieved_goal.dim() == 1:
            achieved_goal = achieved_goal.unsqueeze(0)
        if desired_goal.dim() == 1:
            desired_goal = desired_goal.unsqueeze(0)
        
        with torch.no_grad():
            if self.use_latent_space:
                # 在潜空间中计算距离
                mu_achieved, _ = self.vae_model.encode(achieved_goal)
                mu_desired, _ = self.vae_model.encode(desired_goal)
                distance = torch.norm(mu_achieved - mu_desired, dim=1)
            else:
                # 在原始状态空间中计算距离
                distance = torch.norm(achieved_goal - desired_goal, dim=1)
        
        distance = distance.item() if distance.numel() == 1 else distance.mean().item()
        
        # 计算奖励
        if distance <= self.distance_threshold:
            reward = self.success_reward
        else:
            reward = -self.distance_weight * distance
        
        return reward

def create_manifold_her_buffer(capacity, vae_model, her_strategy='future', 
                              her_k=4, distance_threshold=0.1):
    """
    创建使用流形距离的HER缓冲区
    
    参数:
        capacity: 缓冲区容量
        vae_model: VAE模型
        her_strategy: HER策略
        her_k: HER经验数量
        distance_threshold: 距离阈值
        
    返回:
        buffer: HER缓冲区
    """
    reward_func = ManifoldDistanceReward(
        vae_model=vae_model,
        distance_threshold=distance_threshold,
        use_latent_space=True  # 在潜空间中计算距离更合理
    )
    
    buffer = HERReplayBuffer(
        capacity=capacity,
        her_strategy=her_strategy,
        her_k=her_k,
        reward_func=reward_func
    )
    
    return buffer
