"""
缓冲区管理器 - 统一管理所有经验缓冲区
"""

import torch
import numpy as np
from collections import deque

from logger import main_logger
from hmasd.utils import RolloutBuffer, DiscriminatorBuffer
from stable_baselines3.common.running_mean_std import RunningMeanStd


class BufferManager:
    """统一的缓冲区管理器，负责所有经验缓冲区的管理"""
    
    def __init__(self, config):
        self.config = config
        
        # 创建统一的Rollout缓冲区
        self._create_rollout_buffer()
        
        # 创建判别器缓冲区
        self._create_discriminator_buffer()
        
        # 初始化Value Normalization
        self._init_value_normalization()
        
        # 初始化Observation/State Normalization
        self._init_observation_normalization()
        
        main_logger.info("缓冲区管理器初始化完成")
    
    def _create_rollout_buffer(self):
        """创建统一的Rollout缓冲区"""
        rollout_length = getattr(self.config, 'rollout_length', 2048)
        num_envs = getattr(self.config, 'num_envs', 1)
        gru_hidden_size = getattr(self.config, 'gru_hidden_size', 128)
        action_space_type = getattr(self.config, 'action_space_type', 'continuous')
        
        self.rollout_buffer = RolloutBuffer(
            num_steps=rollout_length,
            num_envs=num_envs,
            n_agents=self.config.n_agents,
            obs_dim=self.config.obs_dim,
            action_dim=self.config.action_dim,
            gru_hidden_size=gru_hidden_size,
            n_Z=self.config.n_Z,
            n_z=self.config.n_z,
            state_dim=self.config.state_dim,
            action_space_type=action_space_type
        )
        
        main_logger.info(f"初始化统一Rollout Buffer: 长度={rollout_length}, 环境数={num_envs}, "
                        f"智能体数={self.config.n_agents}, 团队技能数={self.config.n_Z}, "
                        f"个体技能数={self.config.n_z}")
    
    def _create_discriminator_buffer(self):
        """创建判别器缓冲区"""
        discriminator_buffer_size = getattr(self.config, 'discriminator_buffer_size', 100000)
        self.discriminator_buffer = DiscriminatorBuffer(capacity=discriminator_buffer_size)
        
        main_logger.info(f"初始化Off-Policy判别器Buffer，容量: {discriminator_buffer_size}")
    
    def _init_value_normalization(self):
        """初始化Value Normalization"""
        if self.config.use_valuenorm:
            self.value_norm_coordinator = RunningMeanStd(shape=())
            self.value_norm_discoverer = RunningMeanStd(shape=())
            
            # 添加更新频率控制
            self.value_norm_update_freq = getattr(self.config, 'value_norm_update_freq', 10)
            self.value_norm_update_counter = 0
            
            main_logger.info(f"已启用Value Normalization (使用SB3 RunningMeanStd), "
                           f"更新频率: {self.value_norm_update_freq}")
        else:
            self.value_norm_coordinator = None
            self.value_norm_discoverer = None
            self.value_norm_update_freq = 0
            self.value_norm_update_counter = 0
            
            main_logger.info("未启用Value Normalization")
    
    def _init_observation_normalization(self):
        """初始化Observation/State Normalization"""
        # Observation Normalization
        if getattr(self.config, 'use_obsnorm', False):
            self.obs_norm = RunningMeanStd(shape=(self.config.obs_dim,))
            main_logger.info("已启用Observation Normalization (使用SB3 RunningMeanStd)")
        else:
            self.obs_norm = None
            main_logger.info("未启用Observation Normalization")
        
        # State Normalization
        if getattr(self.config, 'use_statenorm', True):
            self.state_norm = RunningMeanStd(shape=(self.config.state_dim,))
            main_logger.info("已启用State Normalization (使用SB3 RunningMeanStd) - 用于Critic输入标准化")
        else:
            self.state_norm = None
            main_logger.info("未启用State Normalization")
    
    def store_rollout_step(self, t, state, observations, actions, rewards, dones, values, 
                          log_probs, gru_hidden_states, env_id, team_skill=None, 
                          agent_skills=None, reward_components=None):
        """存储一个时间步的数据到rollout缓冲区"""
        if reward_components is None:
            main_logger.error(f"store_rollout_step: reward_components cannot be None. env={env_id}, t={t}")
            return False
        
        # 提取奖励组成部分
        reward_env = reward_components.get('env', np.zeros_like(rewards, dtype=np.float32))
        reward_team_disc = reward_components.get('team_disc', np.zeros_like(rewards, dtype=np.float32))
        reward_ind_disc = reward_components.get('ind_disc', np.zeros_like(rewards, dtype=np.float32))
        
        # 存储数据到统一rollout缓冲区
        success = self.rollout_buffer.add(
            t=t,
            state=state,
            obs=observations,
            action=actions,
            reward=rewards,
            done=dones,
            value=values,
            log_prob=log_probs,
            gru_hidden_state=gru_hidden_states.cpu(),
            env_idx=env_id,
            team_skill=team_skill,
            agent_skills=agent_skills,
            reward_env=reward_env,
            reward_team_disc=reward_team_disc,
            reward_ind_disc=reward_ind_disc
        )
        
        if not success:
            main_logger.warning(f"低层数据存储失败（可能重复存储），环境{env_id}，时间步: {t}")
            return False
        
        main_logger.debug(f"数据已存储到统一rollout缓冲区，环境{env_id}，时间步: {t}，"
                         f"奖励组成：env={np.mean(reward_env):.4f}, "
                         f"team_disc={np.mean(reward_team_disc):.4f}, "
                         f"ind_disc={np.mean(reward_ind_disc):.4f}")
        
        return True
    
    def store_high_level_data(self, env_id, time_step, state_value=None, agent_values=None,
                             team_log_prob=None, agent_log_probs=None, accumulated_reward=None):
        """存储高层策略数据"""
        success = self.rollout_buffer.add_high_level_data(
            env_idx=env_id,
            time_step=time_step,
            state_value=state_value,
            agent_values=agent_values,
            team_log_prob=team_log_prob,
            agent_log_probs=agent_log_probs,
            accumulated_reward=accumulated_reward
        )
        
        if not success:
            main_logger.warning(f"高层数据存储失败，环境{env_id}，时间步: {time_step}")
            return False
        
        main_logger.debug(f"高层数据已存储，环境{env_id}，时间步: {time_step}")
        return True
    
    def store_discriminator_data(self, next_state, team_skill, next_observations, agent_skills):
        """存储判别器数据"""
        # 存储团队技能数据
        self.discriminator_buffer.push(
            {'type': 'team', 'state': next_state, 'skill': team_skill}
        )
        
        # 存储每个智能体的个体技能数据
        for i in range(self.config.n_agents):
            self.discriminator_buffer.push(
                {'type': 'individual', 
                 'obs': next_observations[i], 
                 'team_skill': team_skill,
                 'skill': agent_skills[i]}
            )
        
        main_logger.debug(f"判别器数据已存储，团队技能: {team_skill}, 个体技能: {agent_skills}")
    
    def compute_advantages(self, last_values, dones, gamma=0.99, gae_lambda=0.95):
        """计算低层策略的GAE"""
        self.rollout_buffer.compute_advantages(last_values, dones, gamma, gae_lambda)
        main_logger.debug("低层策略GAE计算完成")
    
    def compute_high_level_advantages(self, high_level_last_values, gamma=0.99, gae_lambda=0.95):
        """计算高层策略的GAE"""
        self.rollout_buffer.compute_high_level_advantages(high_level_last_values, gamma, gae_lambda)
        main_logger.debug("高层策略GAE计算完成")
    
    def get_discoverer_sampler(self, ppo_epochs, num_sequences_per_batch):
        """获取Discoverer采样器"""
        return self.rollout_buffer.get_discoverer_sampler(ppo_epochs, num_sequences_per_batch)
    
    def get_coordinator_sampler(self, num_steps, ppo_epochs, num_sequences_per_batch):
        """获取Coordinator采样器"""
        return self.rollout_buffer.get_coordinator_sampler(num_steps, ppo_epochs, num_sequences_per_batch)
    
    def sample_discriminator_data(self, batch_size):
        """从判别器缓冲区采样数据"""
        if len(self.discriminator_buffer) < batch_size:
            main_logger.warning(f"判别器Buffer中的样本数({len(self.discriminator_buffer)})"
                              f"少于批次大小({batch_size})，跳过判别器更新")
            return None
        
        return self.discriminator_buffer.sample(batch_size)
    
    def clear_rollout_buffer(self):
        """清空rollout缓冲区"""
        main_logger.info("清空统一的on-policy经验缓冲区 (RolloutBuffer)...")
        self.rollout_buffer.reset()
        
        # 保持Off-Policy判别器Buffer不变
        main_logger.info(f"保持Off-Policy判别器Buffer不变，当前大小: {len(self.discriminator_buffer)}")
    
    def normalize_observations(self, observations, training=True):
        """归一化观测数据"""
        if not getattr(self.config, 'use_obsnorm', False) or self.obs_norm is None:
            return observations
        
        # 转换为numpy数组进行处理
        if isinstance(observations, torch.Tensor):
            obs_np = observations.cpu().numpy()
            return_tensor = True
        else:
            obs_np = observations
            return_tensor = False
        
        # 仅在训练模式下更新观测统计量
        if training:
            if obs_np.ndim == 1:
                self.obs_norm.update(obs_np)
            elif obs_np.ndim == 2:
                for i in range(obs_np.shape[0]):
                    self.obs_norm.update(obs_np[i])
            elif obs_np.ndim == 3:
                for i in range(obs_np.shape[0]):
                    for j in range(obs_np.shape[1]):
                        self.obs_norm.update(obs_np[i, j])
        
        # 归一化
        current_mean = self.obs_norm.mean
        current_var = self.obs_norm.var
        
        normalized_obs = (obs_np - current_mean) / np.sqrt(current_var + 1e-8)
        normalized_obs = np.clip(normalized_obs, -10.0, 10.0)
        
        if return_tensor:
            return torch.FloatTensor(normalized_obs).to(observations.device)
        else:
            return normalized_obs
    
    def normalize_states(self, states, training=True):
        """归一化全局状态数据"""
        if not getattr(self.config, 'use_statenorm', True) or self.state_norm is None:
            return states
        
        # 转换为numpy数组进行处理
        if isinstance(states, torch.Tensor):
            states_np = states.cpu().numpy()
            return_tensor = True
        else:
            states_np = states
            return_tensor = False
        
        # 仅在训练模式下更新状态统计量
        if training:
            if states_np.ndim == 1:
                self.state_norm.update(states_np)
            elif states_np.ndim == 2:
                for i in range(states_np.shape[0]):
                    self.state_norm.update(states_np[i])
        
        # 归一化
        current_mean = self.state_norm.mean
        current_var = self.state_norm.var
        
        normalized_states = (states_np - current_mean) / np.sqrt(current_var + 1e-8)
        normalized_states = np.clip(normalized_states, -10.0, 10.0)
        
        if return_tensor:
            return torch.FloatTensor(normalized_states).to(states.device)
        else:
            return normalized_states
    
    def normalize_values(self, values_tensor, running_mean_std):
        """使用当前的统计量归一化价值函数"""
        if not self.config.use_valuenorm or running_mean_std is None:
            return values_tensor
        
        current_mean = torch.tensor(running_mean_std.mean, device=values_tensor.device, dtype=torch.float32)
        current_var = torch.tensor(running_mean_std.var, device=values_tensor.device, dtype=torch.float32)
        
        normalized_tensor = (values_tensor - current_mean) / torch.sqrt(current_var + 1e-8)
        normalized_tensor = torch.clamp(normalized_tensor, -self.config.value_clip, self.config.value_clip)
        
        return normalized_tensor
    
    def denormalize_values(self, normalized_values_tensor, running_mean_std):
        """使用当前的统计量反归一化价值函数"""
        if not self.config.use_valuenorm or running_mean_std is None:
            return normalized_values_tensor
        
        current_mean = torch.tensor(running_mean_std.mean, device=normalized_values_tensor.device, dtype=torch.float32)
        current_var = torch.tensor(running_mean_std.var, device=normalized_values_tensor.device, dtype=torch.float32)
        
        denormalized_tensor = normalized_values_tensor * torch.sqrt(current_var + 1e-8) + current_mean
        
        return denormalized_tensor
    
    def update_value_normalization(self, coordinator_returns=None, discoverer_returns=None):
        """更新Value Normalization统计量"""
        if not self.config.use_valuenorm:
            return
        
        self.value_norm_update_counter += 1
        
        # 控制更新频率
        if self.value_norm_update_counter % self.value_norm_update_freq != 0:
            return
        
        if coordinator_returns is not None and self.value_norm_coordinator is not None:
            self.value_norm_coordinator.update(coordinator_returns)
            main_logger.debug(f"Coordinator ValueNorm已更新. 新均值: {self.value_norm_coordinator.mean:.4f}, "
                            f"新标准差: {np.sqrt(self.value_norm_coordinator.var):.4f}")
        
        if discoverer_returns is not None and self.value_norm_discoverer is not None:
            self.value_norm_discoverer.update(discoverer_returns)
            main_logger.debug(f"Discoverer ValueNorm已更新. 新均值: {self.value_norm_discoverer.mean:.4f}, "
                            f"新标准差: {np.sqrt(self.value_norm_discoverer.var):.4f}")
    
    def get_buffer_stats(self):
        """获取缓冲区统计信息"""
        rollout_data = self.rollout_buffer._get_full_rollout_data()
        
        stats = {
            'rollout_buffer': {
                'num_steps': self.rollout_buffer.num_steps,
                'num_envs': self.rollout_buffer.num_envs,
                'has_data': rollout_data is not None,
                'actual_steps': rollout_data['num_actual_steps'] if rollout_data else 0,
                'high_level_samples': np.sum(rollout_data['high_level_valid_mask']) if rollout_data else 0
            },
            'discriminator_buffer': {
                'size': len(self.discriminator_buffer),
                'capacity': self.discriminator_buffer.capacity,
                'utilization': len(self.discriminator_buffer) / self.discriminator_buffer.capacity
            }
        }
        
        if self.config.use_valuenorm:
            stats['value_normalization'] = {
                'coordinator': {
                    'mean': self.value_norm_coordinator.mean.item() if self.value_norm_coordinator else None,
                    'std': np.sqrt(self.value_norm_coordinator.var.item()) if self.value_norm_coordinator else None,
                    'count': self.value_norm_coordinator.count if self.value_norm_coordinator else None
                },
                'discoverer': {
                    'mean': self.value_norm_discoverer.mean.item() if self.value_norm_discoverer else None,
                    'std': np.sqrt(self.value_norm_discoverer.var.item()) if self.value_norm_discoverer else None,
                    'count': self.value_norm_discoverer.count if self.value_norm_discoverer else None
                }
            }
        
        return stats
    
    def save_normalization_state(self):
        """保存标准化统计信息"""
        state = {}
        
        if self.config.use_valuenorm:
            valuenorm_state = {}
            if self.value_norm_coordinator is not None:
                valuenorm_state['coordinator'] = {
                    'mean': self.value_norm_coordinator.mean,
                    'var': self.value_norm_coordinator.var,
                    'count': self.value_norm_coordinator.count
                }
            if self.value_norm_discoverer is not None:
                valuenorm_state['discoverer'] = {
                    'mean': self.value_norm_discoverer.mean,
                    'var': self.value_norm_discoverer.var,
                    'count': self.value_norm_discoverer.count
                }
            state['valuenorm_state'] = valuenorm_state
        
        # 保存观测和状态标准化统计信息
        normalization_state = {}
        if getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
            normalization_state['obs_norm'] = {
                'mean': self.obs_norm.mean,
                'var': self.obs_norm.var,
                'count': self.obs_norm.count
            }
        if getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
            normalization_state['state_norm'] = {
                'mean': self.state_norm.mean,
                'var': self.state_norm.var,
                'count': self.state_norm.count
            }
        if normalization_state:
            state['normalization_state'] = normalization_state
        
        return state
    
    def load_normalization_state(self, checkpoint):
        """加载标准化统计信息"""
        # 加载Value Normalization状态
        if self.config.use_valuenorm and 'valuenorm_state' in checkpoint:
            valuenorm_state = checkpoint['valuenorm_state']
            
            if 'coordinator' in valuenorm_state and self.value_norm_coordinator is not None:
                coord_state = valuenorm_state['coordinator']
                self.value_norm_coordinator.mean = coord_state['mean']
                self.value_norm_coordinator.var = coord_state['var']
                self.value_norm_coordinator.count = coord_state['count']
                main_logger.info("已恢复Coordinator的SB3 RunningMeanStd状态")
            
            if 'discoverer' in valuenorm_state and self.value_norm_discoverer is not None:
                disc_state = valuenorm_state['discoverer']
                self.value_norm_discoverer.mean = disc_state['mean']
                self.value_norm_discoverer.var = disc_state['var']
                self.value_norm_discoverer.count = disc_state['count']
                main_logger.info("已恢复Discoverer的SB3 RunningMeanStd状态")
        
        # 加载观测和状态标准化统计信息
        if 'normalization_state' in checkpoint:
            normalization_state = checkpoint['normalization_state']
            
            if 'obs_norm' in normalization_state and getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
                obs_state = normalization_state['obs_norm']
                self.obs_norm.mean = obs_state['mean']
                self.obs_norm.var = obs_state['var']
                self.obs_norm.count = obs_state['count']
                main_logger.info("已恢复观测标准化统计信息")
            
            if 'state_norm' in normalization_state and getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
                state_state = normalization_state['state_norm']
                self.state_norm.mean = state_state['mean']
                self.state_norm.var = state_state['var']
                self.state_norm.count = state_state['count']
                main_logger.info("已恢复状态标准化统计信息")
