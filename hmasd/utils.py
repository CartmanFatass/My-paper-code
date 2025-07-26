import torch
import numpy as np
from collections import deque
import random
from logger import main_logger

class ReplayBuffer:
    """经验回放缓冲区，用于存储和采样训练数据"""
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
        self._total_added = 0
        self._total_sampled = 0
        self._structure_validated = False
    
    def push(self, experience):
        """
        将经验存入缓冲区
        
        参数:
            experience: 经验元组，或参数列表(通过*args收集的多个参数)
        """
        # 如果传入的是多个参数，自动打包为元组
        if not isinstance(experience, tuple):
            experience = (experience,)
        
        # 记录添加计数
        if len(self.buffer) >= self.capacity:
            self._total_added += 1
        
        self.buffer.append(experience)
        
    def clear(self):
        """清空缓冲区"""
        self.buffer.clear()
        self._total_added = 0
        self._total_sampled = 0
        self._structure_validated = False
    
    def sample(self, batch_size):
        """从缓冲区中随机采样一批经验"""
        sampled_batch = random.sample(self.buffer, min(len(self.buffer), batch_size))
        self._total_sampled += len(sampled_batch)
        
        # 验证样本结构
        if not self._structure_validated and sampled_batch:
            sample_structure = len(sampled_batch[0])
            main_logger.debug(f"缓冲区样本结构: 包含 {sample_structure} 个元素")
            self._structure_validated = True
            
        return sampled_batch
    
    def __len__(self):
        """返回缓冲区的当前大小"""
        return len(self.buffer)
    
    def get_stats(self):
        """获取缓冲区统计信息"""
        return {
            "size": len(self.buffer),
            "capacity": self.capacity,
            "total_added": self._total_added,
            "total_sampled": self._total_sampled,
            "utilization": len(self.buffer) / self.capacity if self.capacity > 0 else 0
        }

class RolloutBuffer:
    """
    统一的Rollout缓冲区，同时存储高层和低层策略的数据，确保正确对齐
    数据按 (时间步, 环境, 智能体, 特征) 的维度组织，支持序列采样
    """
    def __init__(self, num_steps, num_envs, n_agents, obs_dim, action_dim, gru_hidden_size, n_Z, n_z, state_dim):
        self.num_steps = num_steps
        self.num_envs = num_envs
        self.n_agents = n_agents
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.gru_hidden_size = gru_hidden_size
        self.n_Z = n_Z  # 团队技能数量
        self.n_z = n_z  # 个体技能数量
        self.state_dim = state_dim  # 全局状态维度
        
        # === 低层策略数据 (每个智能体每步) ===
        self.obs = np.zeros((num_steps, num_envs, n_agents, obs_dim), dtype=np.float32)
        self.actions = np.zeros((num_steps, num_envs, n_agents, action_dim), dtype=np.float32)
        self.rewards = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.values = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.log_probs = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.dones = np.zeros((num_steps, num_envs, n_agents), dtype=np.bool_)
        
        # 全局状态信息和技能信息
        self.states = np.zeros((num_steps, num_envs, state_dim), dtype=np.float32)
        self.team_skills = np.zeros((num_steps, num_envs), dtype=np.int64)
        self.agent_skills = np.zeros((num_steps, num_envs, n_agents), dtype=np.int64)
        
        # 存储每一步决策前的隐状态
        self.gru_hidden_states = np.zeros((num_steps, num_envs, n_agents, gru_hidden_size), dtype=np.float32)
        
        # 新增：存储内在奖励的详细组成部分
        self.rewards_env = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.rewards_team_disc = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.rewards_ind_disc = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        
        # === 高层策略专属数据 (每个环境每k步) ===
        self.high_level_rewards = np.zeros((num_steps, num_envs), dtype=np.float32)  # k步累积奖励
        self.high_level_values = np.zeros((num_steps, num_envs), dtype=np.float32)   # 高层价值估计
        self.high_level_joint_log_probs = np.zeros((num_steps, num_envs), dtype=np.float32)  # 联合log概率
        self.high_level_advantages = np.zeros((num_steps, num_envs), dtype=np.float32)
        self.high_level_returns = np.zeros((num_steps, num_envs), dtype=np.float32)
        
        # 标记哪些时间步有有效的高层决策数据
        self.high_level_valid_mask = np.zeros((num_steps, num_envs), dtype=np.bool_)
        
        # GAE计算结果（低层）
        self.advantages = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.returns = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        
        # 移除了 self.ptr 和 self.full，现在由外部管理时间步索引
        
    def reset(self):
        """重置缓冲区，准备收集新的rollout"""
        # 移除了ptr和full属性，缓冲区重置由外部管理
        pass
        
    def add(self, t, state, obs, action, reward, done, value, log_prob, gru_hidden_state, env_idx, team_skill=None, agent_skills=None, reward_env=None, reward_team_disc=None, reward_ind_disc=None):
        """
        在指定的时间步 t 和环境索引 env_idx 存储数据。
        
        参数:
            t: 时间步索引
            state: 全局状态 [state_dim]
            obs: 观测数据 [n_agents, obs_dim]
            action: 动作数据 [n_agents, action_dim]
            reward: 奖励数据 [n_agents] 或 单个值
            done: 完成标志 [n_agents] 或 单个值
            value: 价值估计 [n_agents]
            log_prob: 对数概率 [n_agents]
            gru_hidden_state: GRU隐状态 [n_agents, hidden_size]
            env_idx: 环境索引
            team_skill: 团队技能索引
            agent_skills: 个体技能索引 [n_agents]
            reward_env: 环境奖励
            reward_team_disc: 团队判别器奖励
            reward_ind_disc: 个体判别器奖励
        """
        if t >= self.num_steps:
            main_logger.error(f"RolloutBuffer: 尝试在越界的时间步 {t} 添加数据")
            return
        
        # 使用 t 作为索引，而不是 self.ptr
        self.obs[t, env_idx] = obs
        self.actions[t, env_idx] = action
        
        # 处理奖励和done标志（可能是标量或数组）
        if np.isscalar(reward):
            self.rewards[t, env_idx] = reward
        else:
            self.rewards[t, env_idx] = reward
            
        if np.isscalar(done):
            self.dones[t, env_idx] = done
        else:
            self.dones[t, env_idx] = done
        
        # 存储价值和对数概率
        self.values[t, env_idx] = value
        self.log_probs[t, env_idx] = log_prob
        
        # 存储GRU隐状态
        self.gru_hidden_states[t, env_idx] = gru_hidden_state
        
        # 存储真正的全局状态，而不是obs.flatten()
        self.states[t, env_idx] = state
        
        # 存储技能信息
        if team_skill is not None:
            self.team_skills[t, env_idx] = team_skill
        if agent_skills is not None:
            self.agent_skills[t, env_idx] = agent_skills
            
        # 新增：存储奖励组成
        if reward_env is not None:
            self.rewards_env[t, env_idx] = reward_env
        if reward_team_disc is not None:
            self.rewards_team_disc[t, env_idx] = reward_team_disc
        if reward_ind_disc is not None:
            self.rewards_ind_disc[t, env_idx] = reward_ind_disc
    
    def add_high_level_data(self, env_idx, time_step, value, joint_log_prob, accumulated_reward):
        """
        为高层策略添加数据到指定的时间步和环境
        
        参数:
            env_idx: 环境索引
            time_step: 时间步索引（通常是技能分配时的时间步）
            value: 高层价值估计
            joint_log_prob: 联合对数概率（团队技能+个体技能）
            accumulated_reward: k步累积奖励
        """
        if time_step >= self.num_steps:
            main_logger.warning(f"时间步{time_step}超出缓冲区容量{self.num_steps}")
            return
        
        self.high_level_values[time_step, env_idx] = value
        self.high_level_joint_log_probs[time_step, env_idx] = joint_log_prob
        self.high_level_rewards[time_step, env_idx] = accumulated_reward
        self.high_level_valid_mask[time_step, env_idx] = True
        
        main_logger.debug(f"存储高层数据: env={env_idx}, step={time_step}, "
                         f"value={value:.4f}, log_prob={joint_log_prob:.4f}, reward={accumulated_reward:.4f}")
    
    def compute_advantages(self, last_values, dones, gamma=0.99, gae_lambda=0.95):
        """
        【修复版本】标准化的GAE计算方法，在整个rollout收集完毕后调用一次。
        这确保了严格的on-policy更新流程。

        参数:
            last_values (np.ndarray): Rollout最后一步之后的状态价值，Shape (num_envs, n_agents)
            dones (np.ndarray): 最后一步的完成标志，Shape (num_envs, n_agents) 或 (num_envs,)
            gamma (float): 折扣因子
            gae_lambda (float): GAE lambda参数
        """
        # 确保dones的形状正确
        if dones.ndim == 1:
            # 如果dones是 (num_envs,)，扩展为 (num_envs, n_agents)
            dones = np.broadcast_to(dones[:, np.newaxis], (self.num_envs, self.n_agents))
        
        # 将dones转换为masks，方便计算
        # masks[t] = 1.0 if a transition from t -> t+1 is not terminal, else 0.0
        masks = 1.0 - self.dones.astype(np.float32)

        last_advantage = np.zeros((self.num_envs, self.n_agents), dtype=np.float32)
        
        # 从后往前计算GAE
        for t in reversed(range(self.num_steps)):
            # 如果是缓冲区的最后一步，next_value就是传入的last_values
            if t == self.num_steps - 1:
                next_values = last_values
                next_done = dones.astype(np.float32)
            else:
                next_values = self.values[t + 1]
                next_done = self.dones[t + 1].astype(np.float32)
            
            # delta_t = r_t + gamma * V(s_{t+1}) * (1 - done_{t+1}) - V(s_t)
            delta = (self.rewards[t] + 
                    gamma * next_values * (1.0 - next_done) - 
                    self.values[t])
            
            # advantage_t = delta_t + gamma * lambda * advantage_{t+1} * (1 - done_t)
            last_advantage = (delta + 
                            gamma * gae_lambda * last_advantage * (1.0 - next_done))
            self.advantages[t] = last_advantage

        # 计算Returns = GAE + V(s)
        self.returns = self.advantages + self.values
        main_logger.info("RolloutBuffer: 标准化GAE和Returns计算完成。")

    def compute_high_level_advantages(self, high_level_last_values=None, num_steps=None, gamma=0.99, gae_lambda=0.95):
        """
        为高层策略计算GAE优势和返回值
        
        参数:
            high_level_last_values: 最后状态的高层价值估计 [num_envs]
            num_steps: 实际收集的时间步数
            gamma: 折扣因子
            gae_lambda: GAE参数
        """
        if high_level_last_values is None:
            high_level_last_values = np.zeros(self.num_envs, dtype=np.float32)
        
        if num_steps is None:
            main_logger.error("compute_high_level_advantages: 必须提供 num_steps 参数")
            return
        
        # 为每个环境分别计算高层策略的GAE
        for env_idx in range(self.num_envs):
            # 找到该环境的所有有效高层决策时间步
            valid_steps = []
            for t in range(num_steps):
                if self.high_level_valid_mask[t, env_idx]:
                    valid_steps.append(t)
            
            if len(valid_steps) == 0:
                continue
            
            # 提取该环境的高层序列数据
            rewards_seq = self.high_level_rewards[valid_steps, env_idx]
            values_seq = self.high_level_values[valid_steps, env_idx]
            
            # 计算next_values序列
            next_values_seq = np.zeros_like(values_seq)
            if len(valid_steps) > 1:
                next_values_seq[:-1] = values_seq[1:]
            next_values_seq[-1] = high_level_last_values[env_idx]
            
            # 高层策略没有中间的done信号，所以全部设为False
            dones_seq = np.zeros_like(values_seq, dtype=np.float32)
            
            # 转换为tensor并计算GAE
            rewards_tensor = torch.tensor(rewards_seq, dtype=torch.float32)
            values_tensor = torch.tensor(values_seq, dtype=torch.float32)
            next_values_tensor = torch.tensor(next_values_seq, dtype=torch.float32)
            dones_tensor = torch.tensor(dones_seq, dtype=torch.float32)
            
            advantages, returns = compute_gae(
                rewards_tensor, values_tensor, next_values_tensor, dones_tensor, gamma, gae_lambda
            )
            
            # 存储结果回对应的时间步
            for i, t in enumerate(valid_steps):
                self.high_level_advantages[t, env_idx] = advantages[i].item()
                self.high_level_returns[t, env_idx] = returns[i].item()
        
        main_logger.debug(f"高层策略GAE计算完成，共处理{np.sum(self.high_level_valid_mask[:num_steps])}个有效决策")
    
    # 删除了 finish_rollout 和 finish_path 方法，它们依赖于已移除的 self.ptr
    # 现在统一使用 compute_advantages 方法
    
    def get_discoverer_sampler(self, num_steps, ppo_epochs, num_sequences_per_batch):
        """
        为Discoverer（低层策略）生成正确的序列采样器。
        Discoverer需要独立的智能体序列：num_envs * n_agents 个序列。
        
        参数:
            num_steps: 实际收集的时间步数
            ppo_epochs: PPO训练轮数
            num_sequences_per_batch: 每个批次包含的序列数量
            
        返回:
            生成器，每次产生一个序列批次
        """
        if num_steps <= 0:
            main_logger.warning("无效的时间步数，无法进行序列采样")
            return None
        
        # 我们有 num_envs * n_agents 个独立的序列
        num_total_sequences = self.num_envs * self.n_agents

        # 【关键修复】使用 swapaxes 和 reshape 来安全地展平 E 和 A 维度
        # 原始维度: (T, E, A, F) -> (E, A, T, F) -> (E*A, T, F)
        # 然后再换回 (T, E*A, F)
        def flatten_sequences(arr):
            # T, E, A, ... -> E, A, T, ...
            swapped = arr[:num_steps].swapaxes(0, 1).swapaxes(1, 2) 
            # E, A, T, ... -> E*A, T, ...
            flat = swapped.reshape(num_total_sequences, num_steps, *swapped.shape[3:])
            # E*A, T, ... -> T, E*A, ...
            return flat.swapaxes(0, 1)

        obs_flat = flatten_sequences(self.obs)
        actions_flat = flatten_sequences(self.actions)
        log_probs_flat = flatten_sequences(self.log_probs)
        advantages_flat = flatten_sequences(self.advantages)
        returns_flat = flatten_sequences(self.returns)
        
        # 对于没有Agent维度的数据
        def flatten_sequences_no_agent(arr):
            swapped = arr[:num_steps].swapaxes(0, 1) # T, E, ... -> E, T, ...
            # 扩展Agent维度
            expanded = np.repeat(swapped[:, :, np.newaxis], self.n_agents, axis=2) # E, T, A
            flat = expanded.reshape(num_total_sequences, num_steps, *expanded.shape[3:])
            return flat.swapaxes(0, 1)
        
        global_states_flat = flatten_sequences_no_agent(self.states)
        team_skills_flat = flatten_sequences_no_agent(self.team_skills)
        agent_skills_flat = flatten_sequences(self.agent_skills)

        # 初始隐状态的变形也需要修正
        # 原始维度 (T, E, A, H) -> [0] -> (E, A, H) -> (E*A, H)
        initial_hxs = self.gru_hidden_states[0].reshape(num_total_sequences, -1)
        
        sequence_indices = np.arange(num_total_sequences)
        
        main_logger.debug(f"Discoverer采样器: {num_total_sequences}个序列({self.num_envs}环境 × {self.n_agents}智能体), "
                         f"每批{num_sequences_per_batch}个序列, {ppo_epochs}个epoch")
        
        for epoch in range(ppo_epochs):
            np.random.shuffle(sequence_indices)
            
            for start in range(0, num_total_sequences, num_sequences_per_batch):
                end = min(start + num_sequences_per_batch, num_total_sequences)
                batch_indices = sequence_indices[start:end]
                
                # 【关键修改】在yield中加入初始隐状态
                yield {
                    'observations': torch.from_numpy(obs_flat[:, batch_indices]).float(),  # Shape: (T, batch_size, obs_dim)
                    'actions': torch.from_numpy(actions_flat[:, batch_indices]).float(),
                    'log_probs': torch.from_numpy(log_probs_flat[:, batch_indices]).float(),
                    'advantages': torch.from_numpy(advantages_flat[:, batch_indices]).float(),
                    'returns': torch.from_numpy(returns_flat[:, batch_indices]).float(),
                    'global_states': torch.from_numpy(global_states_flat[:, batch_indices]).float(),  # 新增
                    'team_skills': torch.from_numpy(team_skills_flat[:, batch_indices]).long(),   # 新增
                    'agent_skills': torch.from_numpy(agent_skills_flat[:, batch_indices]).long(),
                    # **** 新增 ****
                    'initial_hxs': torch.from_numpy(initial_hxs[batch_indices]).float()
                }

    def get_coordinator_sampler(self, num_steps, ppo_epochs, num_sequences_per_batch):
        """
        【重构版本】为Coordinator（高层策略）生成正确的序列采样器。
        现在使用高层专属数据，确保数据的准确性和对齐。
        
        参数:
            num_steps: 实际收集的时间步数
            ppo_epochs: PPO训练轮数
            num_sequences_per_batch: 每个批次包含的序列数量
            
        返回:
            生成器，每次产生一个序列批次
        """
        if num_steps <= 0:
            main_logger.warning("无效的时间步数，无法进行序列采样")
            return None
        
        # 检查高层数据的有效性
        valid_steps = np.sum(self.high_level_valid_mask[:num_steps])
        if valid_steps == 0:
            main_logger.warning("没有有效的高层策略数据，无法进行Coordinator采样")
            return None
        
        main_logger.info(f"Coordinator采样器: 发现{valid_steps}个有效高层决策步骤（总共{num_steps}步）")
        
        # 筛选出有有效高层数据的时间步
        valid_time_steps = []
        valid_env_indices = []
        
        for t in range(num_steps):
            for env_idx in range(self.num_envs):
                if self.high_level_valid_mask[t, env_idx]:
                    valid_time_steps.append(t)
                    valid_env_indices.append(env_idx)
        
        num_valid_samples = len(valid_time_steps)
        if num_valid_samples == 0:
            main_logger.warning("没有找到有效的高层策略样本")
            return None
        
        # 构建高层策略的采样数据
        # 使用高层专属数据，而不是近似值
        valid_indices = np.arange(num_valid_samples)
        
        main_logger.debug(f"Coordinator采样器: {num_valid_samples}个有效样本, "
                         f"每批{num_sequences_per_batch}个样本, {ppo_epochs}个epoch")
        
        for epoch in range(ppo_epochs):
            np.random.shuffle(valid_indices)
            
            for start in range(0, num_valid_samples, num_sequences_per_batch):
                end = min(start + num_sequences_per_batch, num_valid_samples)
                batch_indices = valid_indices[start:end]
                batch_size = len(batch_indices)
                
                # 收集批次数据
                batch_observations = []
                batch_states = []
                batch_team_skills = []
                batch_agent_skills = []
                batch_log_probs = []
                batch_advantages = []
                batch_returns = []
                batch_values = []
                
                for i, idx in enumerate(batch_indices):
                    t = valid_time_steps[idx]
                    env_idx = valid_env_indices[idx]
                    
                    # 使用高层专属数据
                    batch_observations.append(self.obs[t, env_idx])  # (n_agents, obs_dim)
                    batch_states.append(self.states[t, env_idx])     # (state_dim,)
                    batch_team_skills.append(self.team_skills[t, env_idx])
                    batch_agent_skills.append(self.agent_skills[t, env_idx])  # (n_agents,)
                    
                    # 关键：使用准确的高层数据，不是近似值
                    batch_log_probs.append(self.high_level_joint_log_probs[t, env_idx])
                    batch_advantages.append(self.high_level_advantages[t, env_idx])
                    batch_returns.append(self.high_level_returns[t, env_idx])
                    batch_values.append(self.high_level_values[t, env_idx])
                
                # 转换为张量 - 单个时间步数据，不是序列
                yield {
                    'observations': torch.from_numpy(np.stack(batch_observations)).float(),     # (batch_size, n_agents, obs_dim)
                    'states': torch.from_numpy(np.stack(batch_states)).float(),               # (batch_size, state_dim)
                    'team_skills': torch.from_numpy(np.stack(batch_team_skills)).long(),       # (batch_size,)
                    'agent_skills': torch.from_numpy(np.stack(batch_agent_skills)).long(),     # (batch_size, n_agents)
                    'log_probs': torch.from_numpy(np.stack(batch_log_probs)).float(),         # (batch_size,)
                    'advantages': torch.from_numpy(np.stack(batch_advantages)).float(),       # (batch_size,)
                    'returns': torch.from_numpy(np.stack(batch_returns)).float(),             # (batch_size,)
                    'values': torch.from_numpy(np.stack(batch_values)).float(),               # (batch_size,)
                    'actions': torch.from_numpy(np.stack(batch_agent_skills)).float(),        # 个体技能作为"动作"
                    'initial_hxs': torch.zeros(batch_size, self.gru_hidden_size)             # Transformer不需要，但保持接口一致
                }

    def get_sequence_sampler(self, num_steps, ppo_epochs, num_sequences_per_batch):
        """
        保留原有接口用于向后兼容，默认使用Discoverer采样器。
        建议直接使用 get_discoverer_sampler 或 get_coordinator_sampler。
        """
        main_logger.warning("使用了已废弃的get_sequence_sampler方法，建议使用get_discoverer_sampler或get_coordinator_sampler")
        return self.get_discoverer_sampler(num_steps, ppo_epochs, num_sequences_per_batch)
    
    # 删除了依赖 self.ptr 和 self.full 的方法，这些现在由外部管理

class StateSkillDataset:
    """状态-技能对数据集，用于训练技能判别器"""
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
        self._total_added = 0
        self._total_sampled = 0
    
    def push(self, state, team_skill, observations, agent_skills):
        """将状态-技能对存入数据集"""
        experience = (state, team_skill, observations, agent_skills)
        
        # 记录添加计数
        if len(self.buffer) >= self.capacity:
            self._total_added += 1
            
        self.buffer.append(experience)
        
    def clear(self):
        """清空数据集"""
        self.buffer.clear()
        self._total_added = 0
        self._total_sampled = 0
    
    def sample(self, batch_size):
        """从数据集中随机采样一批数据"""
        sampled_batch = random.sample(self.buffer, min(len(self.buffer), batch_size))
        self._total_sampled += len(sampled_batch)
        return sampled_batch
    
    def __len__(self):
        """返回数据集的当前大小"""
        return len(self.buffer)
        
    def get_stats(self):
        """获取数据集统计信息"""
        return {
            "size": len(self.buffer),
            "capacity": self.capacity,
            "total_added": self._total_added,
            "total_sampled": self._total_sampled,
            "utilization": len(self.buffer) / self.capacity if self.capacity > 0 else 0
        }

def compute_gae(rewards, values, next_values, dones, gamma, lam):
    """
    计算广义优势估计（GAE）
    
    参数:
        rewards: 一批奖励 [batch_size]
        values: 当前状态价值 [batch_size]
        next_values: 下一状态价值 [batch_size]
        dones: 终止标志 [batch_size]
        gamma: 折扣因子
        lam: GAE参数
        
    返回:
        advantages: 优势函数估计值 [batch_size]
        returns: 目标收益值 [batch_size]
    """
    advantages = torch.zeros_like(rewards)
    last_gae = 0
    
    # 逆序遍历时序数据进行计算
    for t in reversed(range(len(rewards))):
        if t == len(rewards) - 1:
            next_value = next_values[t]
        else:
            next_value = values[t + 1]
            
        delta = rewards[t] + gamma * next_value * (1 - dones[t]) - values[t]
        advantages[t] = last_gae = delta + gamma * lam * (1 - dones[t]) * last_gae
    
    returns = advantages + values
    
    return advantages, returns

def compute_ppo_loss(policy, values, old_log_probs, actions, advantages, returns, 
                     clip_epsilon, entropy_coef, value_loss_coef):
    """
    计算PPO损失函数
    
    参数:
        policy: 策略分布 [batch_size, ...]
        values: 价值函数 [batch_size]
        old_log_probs: 旧策略的动作对数概率 [batch_size]
        actions: 执行的动作 [batch_size, action_dim]
        advantages: 优势函数值 [batch_size]
        returns: 目标收益值 [batch_size]
        clip_epsilon: PPO裁剪参数
        entropy_coef: 熵损失系数
        value_loss_coef: 价值损失系数
        
    返回:
        loss: 总损失值
        policy_loss: 策略损失值
        value_loss: 价值损失值
        entropy_loss: 熵损失值
    """
    # 计算当前策略对动作的对数概率
    dist = policy
    log_probs = dist.log_prob(actions)
    
    # 计算策略比率并限制在[1-epsilon, 1+epsilon]范围内
    ratio = torch.exp(log_probs - old_log_probs)
    surr1 = ratio * advantages
    surr2 = torch.clamp(ratio, 1.0 - clip_epsilon, 1.0 + clip_epsilon) * advantages
    policy_loss = -torch.min(surr1, surr2).mean()
    
    # 计算价值损失（均方误差）
    value_loss = 0.5 * ((returns - values) ** 2).mean()
    
    # 计算熵，鼓励探索
    entropy_loss = -dist.entropy().mean()
    
    # 加权组合三个损失
    loss = policy_loss + value_loss_coef * value_loss + entropy_coef * entropy_loss
    
    return loss, policy_loss, value_loss, entropy_loss

def one_hot(indices, depth):
    """
    将索引转换为独热编码
    
    参数:
        indices: 索引张量 [batch_size]
        depth: 独热编码的维度
        
    返回:
        one_hot: 独热编码张量 [batch_size, depth]
    """
    if isinstance(indices, int):
        indices = torch.tensor([indices])
    elif isinstance(indices, list):
        indices = torch.tensor(indices)
    if indices.dim() == 0:
        indices = indices.unsqueeze(0)
    
    device = indices.device
    one_hot = torch.zeros(indices.size(0), depth, device=device)
    one_hot.scatter_(1, indices.unsqueeze(1), 1)
    
    return one_hot

def setup_optimizer(model, lr):
    """设置优化器"""
    return torch.optim.Adam(model.parameters(), lr=lr)
