"""
基于流形的目标导向HMASD代理
将原有的技能发现机制重构为目标导向的强化学习框架
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.optim import Adam
from torch.distributions import Normal
import os
from collections import deque
from torch.utils.tensorboard import SummaryWriter

# 确保在多进程环境中使用安全的matplotlib后端
import matplotlib
if matplotlib.get_backend() != 'Agg':
    matplotlib.use('Agg')

from hmasd.logging import main_logger
from manifold_hmasd.vae import StateManifoldVAE
from manifold_hmasd.her_replay_buffer import HERReplayBuffer, create_manifold_her_buffer
from hmasd.utils import compute_gae

class GoalConditionedPolicy(nn.Module):
    """
    目标导向策略网络
    输入：观测 + 目标状态
    输出：动作分布
    """
    def __init__(self, obs_dim, goal_dim, action_dim, hidden_dim=128, use_goal_conditioning=True):
        super(GoalConditionedPolicy, self).__init__()
        
        self.obs_dim = obs_dim
        self.goal_dim = goal_dim
        self.action_dim = action_dim
        self.use_goal_conditioning = use_goal_conditioning
        
        # 输入维度：观测 + 目标状态（如果启用目标导向）
        input_dim = obs_dim + (goal_dim if use_goal_conditioning else 0)
        
        # 特征提取网络
        self.feature_net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # 动作均值和标准差
        self.action_mean = nn.Linear(hidden_dim, action_dim)
        self.action_log_std = nn.Linear(hidden_dim, action_dim)
        
        # 价值函数（状态-动作价值）
        self.value_head = nn.Linear(hidden_dim, 1)
        
        # 权重初始化
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=1.0)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
        
        # 动作标准差初始化为较小值
        nn.init.constant_(self.action_log_std.bias, -1.0)
    
    def forward(self, obs, goal=None, deterministic=False):
        """
        前向传播
        
        参数:
            obs: 观测 [batch_size, obs_dim]
            goal: 目标状态 [batch_size, goal_dim]
            deterministic: 是否使用确定性策略
            
        返回:
            action: 动作 [batch_size, action_dim]
            action_logprob: 动作对数概率 [batch_size]
            value: 状态价值 [batch_size, 1]
            action_dist: 动作分布
        """
        # 确保输入是float32类型
        obs = obs.float()
        
        # 构造输入
        if self.use_goal_conditioning and goal is not None:
            goal = goal.float()
            policy_input = torch.cat([obs, goal], dim=-1)
        else:
            policy_input = obs
        
        # 特征提取
        features = self.feature_net(policy_input)
        
        # 动作分布
        action_mean = self.action_mean(features)
        action_log_std = torch.clamp(self.action_log_std(features), min=-10, max=2)
        action_std = torch.exp(action_log_std)
        
        # 创建正态分布
        action_dist = Normal(action_mean, action_std)
        
        # 采样动作
        if deterministic:
            action = action_mean
        else:
            action = action_dist.sample()
        
        # 计算对数概率
        action_logprob = action_dist.log_prob(action).sum(dim=-1)
        
        # 状态价值
        value = self.value_head(features)
        
        return action, action_logprob, value, action_dist

class GoalGenerator(nn.Module):
    """
    目标生成器：从VAE潜空间采样目标
    """
    def __init__(self, vae_model, goal_strategy='random', curriculum_config=None):
        super(GoalGenerator, self).__init__()
        
        self.vae_model = vae_model
        self.goal_strategy = goal_strategy
        self.curriculum_config = curriculum_config or {}
        
        # 目标难度课程
        self.current_difficulty = 0.0  # [0, 1]
        self.difficulty_update_steps = 0
        
        main_logger.info(f"目标生成器初始化: 策略={goal_strategy}")
    
    def sample_goals(self, batch_size, device, current_states=None):
        """
        采样目标状态
        
        参数:
            batch_size: 批大小
            device: 设备
            current_states: 当前状态（用于相对目标生成）
            
        返回:
            goals: 目标状态 [batch_size, state_dim]
            goal_info: 目标信息字典
        """
        if self.goal_strategy == 'random':
            # 从VAE先验分布随机采样
            goals, latent_goals = self.vae_model.sample_from_latent(batch_size, device)
            
        elif self.goal_strategy == 'curriculum':
            # 课程学习：逐渐增加目标难度
            goals, latent_goals = self._sample_curriculum_goals(batch_size, device, current_states)
            
        elif self.goal_strategy == 'adaptive':
            # 自适应采样：基于当前成功率调整目标分布
            goals, latent_goals = self._sample_adaptive_goals(batch_size, device, current_states)
            
        else:
            raise ValueError(f"未知的目标策略: {self.goal_strategy}")
        
        goal_info = {
            'strategy': self.goal_strategy,
            'difficulty': self.current_difficulty,
            'latent_goals': latent_goals
        }
        
        return goals, goal_info
    
    def _sample_curriculum_goals(self, batch_size, device, current_states):
        """课程学习目标采样"""
        # 简化版课程：根据难度调整采样范围
        if self.current_difficulty < 0.3:
            # 简单目标：在当前状态附近采样
            if current_states is not None:
                mu, _ = self.vae_model.encode(current_states)
                # 在当前潜变量附近采样
                noise_scale = 0.5
                latent_goals = mu + torch.randn_like(mu) * noise_scale
                goals = self.vae_model.decode(latent_goals)
            else:
                goals, latent_goals = self.vae_model.sample_from_latent(batch_size, device)
        else:
            # 困难目标：随机采样
            goals, latent_goals = self.vae_model.sample_from_latent(batch_size, device)
        
        return goals, latent_goals
    
    def _sample_adaptive_goals(self, batch_size, device, current_states):
        """自适应目标采样"""
        # 简化版：目前与随机采样相同
        return self.vae_model.sample_from_latent(batch_size, device)
    
    def update_difficulty(self, success_rate, step):
        """更新目标难度"""
        self.difficulty_update_steps += 1
        
        # 基于成功率调整难度
        target_success_rate = 0.3  # 目标成功率
        
        if success_rate > target_success_rate + 0.1:
            # 成功率过高，增加难度
            self.current_difficulty = min(1.0, self.current_difficulty + 0.01)
        elif success_rate < target_success_rate - 0.1:
            # 成功率过低，降低难度
            self.current_difficulty = max(0.0, self.current_difficulty - 0.01)
        
        # 记录到日志
        if self.difficulty_update_steps % 100 == 0:
            main_logger.info(f"目标难度更新: {self.current_difficulty:.3f}, "
                           f"当前成功率: {success_rate:.3f}")

class ManifoldHMASDAgent:
    """
    基于流形的目标导向HMASD代理
    """
    def __init__(self, config, vae_model_path, log_dir='logs/manifold_hmasd', device=None):
        """
        初始化代理
        
        参数:
            config: 配置对象
            vae_model_path: 训练好的VAE模型路径
            log_dir: TensorBoard日志目录
            device: 计算设备
        """
        self.config = config
        self.device = device if device is not None else torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        
        # 确保环境维度已设置
        assert config.state_dim is not None, "必须先设置state_dim"
        assert config.obs_dim is not None, "必须先设置obs_dim"
        
        # 初始化TensorBoard
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.writer = SummaryWriter(log_dir)
        self.global_step = 0
        
        # 加载VAE模型
        self.vae_model = self._load_vae_model(vae_model_path)
        self.vae_model.eval()  # 训练期间VAE保持评估模式
        
        # 创建目标生成器
        self.goal_generator = GoalGenerator(
            vae_model=self.vae_model,
            goal_strategy='random'  # 初期使用随机策略
        )
        
        # 创建目标导向策略网络
        self.policy = GoalConditionedPolicy(
            obs_dim=config.obs_dim,
            goal_dim=config.state_dim,  # 目标是全局状态
            action_dim=config.action_dim,
            hidden_dim=config.hidden_size,
            use_goal_conditioning=True
        ).to(self.device)
        
        # 创建优化器
        self.policy_optimizer = Adam(
            self.policy.parameters(),
            lr=config.lr_discoverer,
            weight_decay=config.weight_decay
        )
        
        # 创建HER经验回放缓冲区
        self.replay_buffer = create_manifold_her_buffer(
            capacity=config.buffer_size,
            vae_model=self.vae_model,
            her_strategy='future',
            her_k=4,
            distance_threshold=0.1
        )
        
        # 当前目标和episode状态
        self.current_goals = {}  # 各环境的当前目标
        self.episode_starts = {}  # 各环境的episode开始标志
        
        # 训练统计
        self.training_info = {
            'policy_loss': [],
            'value_loss': [],
            'success_rate': [],
            'episode_rewards': [],
            'goal_distances': [],
            'reconstruction_errors': []
        }
        
        main_logger.info(f"ManifoldHMASD代理初始化完成，设备: {self.device}")
    
    def _load_vae_model(self, vae_model_path):
        """加载训练好的VAE模型"""
        if not os.path.exists(vae_model_path):
            raise FileNotFoundError(f"VAE模型文件不存在: {vae_model_path}")
        
        checkpoint = torch.load(vae_model_path, map_location=self.device)
        
        # 创建VAE模型
        model_config = checkpoint['model_config']
        vae_model = StateManifoldVAE(
            state_dim=model_config['state_dim'],
            latent_dim=model_config['latent_dim'],
            hidden_dims=model_config['hidden_dims']
        ).to(self.device)
        
        # 加载权重
        vae_model.load_state_dict(checkpoint['model_state_dict'])
        
        # 保存标准化参数
        self.state_mean = checkpoint['normalization']['state_mean'].to(self.device)
        self.state_std = checkpoint['normalization']['state_std'].to(self.device)
        
        main_logger.info(f"VAE模型加载成功: {vae_model_path}")
        main_logger.info(f"模型配置: {model_config}")
        
        return vae_model
    
    def normalize_state(self, state):
        """标准化状态（与VAE训练时一致）"""
        state_tensor = torch.tensor(state, dtype=torch.float32, device=self.device)
        if state_tensor.dim() == 1:
            state_tensor = state_tensor.unsqueeze(0)
        
        normalized = (state_tensor - self.state_mean) / self.state_std
        return normalized
    
    def denormalize_state(self, normalized_state):
        """反标准化状态"""
        return normalized_state * self.state_std + self.state_mean
    
    def step(self, observations, global_state, env_id=0, episode_step=0):
        """
        执行一个环境步骤
        
        参数:
            observations: 所有智能体的观测 [n_agents, obs_dim]
            global_state: 全局状态 [state_dim]
            env_id: 环境ID
            episode_step: 当前episode步数
            
        返回:
            actions: 所有智能体的动作 [n_agents, action_dim]
            info: 额外信息
        """
        # 检查是否需要生成新目标（episode开始）
        if env_id not in self.current_goals or episode_step == 0:
            self._generate_new_goal(global_state, env_id)
            self.episode_starts[env_id] = True
        else:
            self.episode_starts[env_id] = False
        
        # 获取当前目标
        current_goal = self.current_goals[env_id]
        
        # 为所有智能体选择动作
        actions, action_logprobs = self._select_actions(observations, current_goal)
        
        info = {
            'goal': current_goal.cpu().numpy(),
            'action_logprobs': action_logprobs,
            'episode_start': self.episode_starts[env_id],
            'env_id': env_id
        }
        
        return actions, info
    
    def _generate_new_goal(self, global_state, env_id):
        """为指定环境生成新目标"""
        # 标准化当前状态
        current_state_normalized = self.normalize_state(global_state)
        
        # 生成目标
        goals, goal_info = self.goal_generator.sample_goals(
            batch_size=1,
            device=self.device,
            current_states=current_state_normalized
        )
        
        # 反标准化目标（用于环境交互）
        goal_denormalized = self.denormalize_state(goals[0])
        
        self.current_goals[env_id] = goal_denormalized
        
        # 记录目标信息
        main_logger.debug(f"环境{env_id}生成新目标，难度: {goal_info['difficulty']:.3f}")
    
    def _select_actions(self, observations, goal, deterministic=False):
        """为所有智能体选择动作"""
        n_agents = observations.shape[0]
        
        # 将目标扩展到所有智能体
        goals_expanded = goal.unsqueeze(0).expand(n_agents, -1)
        
        # 转换为张量
        obs_tensor = torch.FloatTensor(observations).to(self.device)
        
        with torch.no_grad():
            actions, action_logprobs, values, action_dist = self.policy(
                obs_tensor, goals_expanded, deterministic
            )
        
        return actions.cpu().numpy(), action_logprobs.cpu().numpy()
    
    def store_transition(self, state, next_state, observations, actions, reward, 
                        done, info, env_id=0):
        """
        存储环境交互经验
        
        参数:
            state: 当前状态
            next_state: 下一状态
            observations: 观测
            actions: 动作
            reward: 原始环境奖励
            done: 是否结束
            info: 额外信息
            env_id: 环境ID
        """
        # 获取目标
        goal = self.current_goals.get(env_id)
        if goal is None:
            return  # 如果没有目标，跳过存储
        
        # 计算目标导向奖励（基于流形距离）
        goal_reward = self._compute_goal_reward(next_state, goal.cpu().numpy())
        
        # 存储到HER缓冲区
        self.replay_buffer.store_transition(
            state=state,
            action=actions,  # 这里假设actions是所有智能体的动作
            reward=goal_reward,
            next_state=next_state,
            done=done,
            goal=goal.cpu().numpy(),
            info={'env_reward': reward}
        )
        
        # 如果episode结束，处理HER
        if done:
            self.replay_buffer.store_episode()
            
            # 重置环境状态
            if env_id in self.current_goals:
                del self.current_goals[env_id]
            if env_id in self.episode_starts:
                del self.episode_starts[env_id]
    
    def _compute_goal_reward(self, achieved_state, goal_state):
        """
        计算基于流形的目标奖励
        
        参数:
            achieved_state: 实际达到的状态
            goal_state: 目标状态
            
        返回:
            reward: 目标奖励
        """
        # 标准化状态
        achieved_normalized = self.normalize_state(achieved_state)
        goal_normalized = self.normalize_state(goal_state)
        
        with torch.no_grad():
            # 在潜空间中计算距离
            mu_achieved, _ = self.vae_model.encode(achieved_normalized)
            mu_goal, _ = self.vae_model.encode(goal_normalized)
            
            # 欧几里得距离
            distance = torch.norm(mu_achieved - mu_goal, dim=1)
            
            # 转换为奖励（距离越小奖励越高）
            reward = -distance.item()
        
        return reward
    
    def update(self):
        """更新策略网络"""
        if len(self.replay_buffer) < self.config.batch_size:
            return {}
        
        # 从HER缓冲区采样数据
        batch_data = self.replay_buffer.sample_tensors(self.config.batch_size, self.device)
        if batch_data is None:
            return {}
        
        states, actions, rewards, next_states, dones, goals = batch_data
        
        # 假设我们只使用第一个智能体的观测作为代表
        # 在实际应用中，这里需要更精细的处理
        obs = states  # 简化：假设states就是观测
        
        # 计算当前策略输出
        current_actions, current_logprobs, current_values, current_dist = self.policy(obs, goals)
        
        # 计算GAE
        next_values = torch.zeros_like(current_values)  # 简化：假设下一状态价值为0
        advantages, returns = compute_gae(
            rewards, current_values.squeeze(-1), next_values.squeeze(-1), dones,
            self.config.gamma, self.config.gae_lambda
        )
        
        # 标准化优势
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 策略损失（PPO）
        # 简化：假设没有旧的log概率，直接使用当前log概率
        ratio = torch.exp(current_logprobs - current_logprobs.detach())
        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon) * advantages
        policy_loss = -torch.min(surr1, surr2).mean()
        
        # 价值损失
        value_loss = F.mse_loss(current_values.squeeze(-1), returns)
        
        # 熵损失
        entropy_loss = -current_dist.entropy().mean() * 0.01
        
        # 总损失
        total_loss = policy_loss + 0.5 * value_loss + entropy_loss
        
        # 更新网络
        self.policy_optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.config.max_grad_norm)
        self.policy_optimizer.step()
        
        # 记录训练信息
        self.training_info['policy_loss'].append(policy_loss.item())
        self.training_info['value_loss'].append(value_loss.item())
        
        # 计算成功率（简化）
        goal_distances = torch.norm(states - goals, dim=1)
        success_rate = (goal_distances < 0.1).float().mean().item()
        self.training_info['success_rate'].append(success_rate)
        
        # 记录到TensorBoard
        self.writer.add_scalar('Loss/Policy', policy_loss.item(), self.global_step)
        self.writer.add_scalar('Loss/Value', value_loss.item(), self.global_step)
        self.writer.add_scalar('Loss/Total', total_loss.item(), self.global_step)
        self.writer.add_scalar('Performance/SuccessRate', success_rate, self.global_step)
        
        self.global_step += 1
        
        return {
            'policy_loss': policy_loss.item(),
            'value_loss': value_loss.item(),
            'total_loss': total_loss.item(),
            'success_rate': success_rate
        }
    
    def save_model(self, path):
        """保存模型"""
        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.policy_optimizer.state_dict(),
            'config': self.config,
            'global_step': self.global_step,
            'training_info': self.training_info
        }, path)
        main_logger.info(f"模型已保存到 {path}")
    
    def load_model(self, path):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        
        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.policy_optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.global_step = checkpoint.get('global_step', 0)
        self.training_info = checkpoint.get('training_info', self.training_info)
        
        main_logger.info(f"模型已从 {path} 加载")
    
    def get_statistics(self):
        """获取训练统计信息"""
        buffer_stats = self.replay_buffer.get_statistics()
        
        stats = {
            'global_step': self.global_step,
            'policy_loss_mean': np.mean(self.training_info['policy_loss'][-100:]) if self.training_info['policy_loss'] else 0,
            'value_loss_mean': np.mean(self.training_info['value_loss'][-100:]) if self.training_info['value_loss'] else 0,
            'success_rate_mean': np.mean(self.training_info['success_rate'][-100:]) if self.training_info['success_rate'] else 0,
            'buffer_stats': buffer_stats,
            'goal_difficulty': self.goal_generator.current_difficulty
        }
        
        return stats
