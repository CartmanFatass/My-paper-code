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
        
        # === 【关键修复】添加专门的存储状态跟踪数组 ===
        self.low_level_stored_mask = np.zeros((num_steps, num_envs), dtype=np.bool_)  # 低层数据存储状态
        self.high_level_stored_mask = np.zeros((num_steps, num_envs), dtype=np.bool_)  # 高层数据存储状态
        
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
        
        # === 【关键修复】高层策略专属数据 - 分离团队技能和个体技能 ===
        self.high_level_rewards = np.zeros((num_steps, num_envs), dtype=np.float32)  # k步累积奖励
        
        # 分离的价值函数存储
        self.high_level_state_values = np.zeros((num_steps, num_envs), dtype=np.float32)   # 状态价值 V^h(ŝ)
        self.high_level_agent_values = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)  # 智能体价值 V^h(ô_i)
        
        # 分离的log概率存储
        self.high_level_team_log_probs = np.zeros((num_steps, num_envs), dtype=np.float32)  # 团队技能log概率
        self.high_level_agent_log_probs = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)  # 个体技能log概率
        self.high_level_joint_log_probs = np.zeros((num_steps, num_envs), dtype=np.float32)  # 联合log概率（向后兼容）
        
        # 分离的优势函数和回报
        self.high_level_team_advantages = np.zeros((num_steps, num_envs), dtype=np.float32)
        self.high_level_agent_advantages = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.high_level_team_returns = np.zeros((num_steps, num_envs), dtype=np.float32)
        self.high_level_agent_returns = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        
        # 向后兼容的统一存储（将被逐步废弃）
        self.high_level_advantages = np.zeros((num_steps, num_envs), dtype=np.float32)
        self.high_level_returns = np.zeros((num_steps, num_envs), dtype=np.float32)
        self.high_level_values = np.zeros((num_steps, num_envs), dtype=np.float32)
        
        # 标记哪些时间步有有效的高层决策数据
        self.high_level_valid_mask = np.zeros((num_steps, num_envs), dtype=np.bool_)
        
        # GAE计算结果（低层）
        self.advantages = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.returns = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        
        # 移除了 self.ptr 和 self.full，现在由外部管理时间步索引
        
        # === 【关键修复】添加存储操作统计和调试信息 ===
        self.storage_stats = {
            'total_low_level_attempts': 0,
            'total_low_level_success': 0,
            'total_high_level_attempts': 0,
            'total_high_level_success': 0,
            'duplicate_low_level_attempts': 0,
            'duplicate_high_level_attempts': 0,
            'last_storage_info': {}  # 记录最近的存储操作信息
        }
        
    def reset(self):
        """重置缓冲区，准备收集新的rollout"""
        # 【关键修复】重置存储状态跟踪数组
        self.low_level_stored_mask.fill(False)
        self.high_level_stored_mask.fill(False)
        self.high_level_valid_mask.fill(False)
        
        # 重置存储统计信息
        self.storage_stats = {
            'total_low_level_attempts': 0,
            'total_low_level_success': 0,
            'total_high_level_attempts': 0,
            'total_high_level_success': 0,
            'duplicate_low_level_attempts': 0,
            'duplicate_high_level_attempts': 0,
            'last_storage_info': {}
        }
        
        main_logger.debug("RolloutBuffer已重置，存储状态跟踪数组已清空")
        
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
        # 【关键修复】更新存储统计信息
        self.storage_stats['total_low_level_attempts'] += 1
        
        # 【关键修复】添加边界检查和详细调试信息
        if t >= self.num_steps:
            main_logger.error(f"RolloutBuffer.add: 时间步越界! t={t} >= num_steps={self.num_steps}, env_idx={env_idx}")
            return False
        
        if env_idx >= self.num_envs:
            main_logger.error(f"RolloutBuffer.add: 环境索引越界! env_idx={env_idx} >= num_envs={self.num_envs}, t={t}")
            return False
        
        # 【关键修复】使用专门的存储状态跟踪数组检查重复存储
        if self.low_level_stored_mask[t, env_idx]:
            self.storage_stats['duplicate_low_level_attempts'] += 1
            main_logger.warning(f"RolloutBuffer.add: 重复存储低层数据! time_step={t}, env_idx={env_idx}")
            main_logger.warning(f"低层数据存储失败（可能重复存储），环境{env_idx}，时间步: {t}")
            return False  # 阻止重复写入
        
        # 【关键修复】数据形状验证
        try:
            # 验证观测形状
            if obs.shape != (self.n_agents, self.obs_dim):
                main_logger.error(f"RolloutBuffer.add: 观测形状不匹配! 期望{(self.n_agents, self.obs_dim)}, 实际{obs.shape}, t={t}, env_idx={env_idx}")
                return False
            
            # 验证动作形状
            if action.shape != (self.n_agents, self.action_dim):
                main_logger.error(f"RolloutBuffer.add: 动作形状不匹配! 期望{(self.n_agents, self.action_dim)}, 实际{action.shape}, t={t}, env_idx={env_idx}")
                return False
            
            # 验证状态形状
            if state.shape != (self.state_dim,):
                main_logger.error(f"RolloutBuffer.add: 状态形状不匹配! 期望{(self.state_dim,)}, 实际{state.shape}, t={t}, env_idx={env_idx}")
                return False
            
            # 验证价值和log_prob形状
            if value.shape != (self.n_agents,):
                main_logger.error(f"RolloutBuffer.add: 价值形状不匹配! 期望{(self.n_agents,)}, 实际{value.shape}, t={t}, env_idx={env_idx}")
                return False
            
            if log_prob.shape != (self.n_agents,):
                main_logger.error(f"RolloutBuffer.add: log_prob形状不匹配! 期望{(self.n_agents,)}, 实际{log_prob.shape}, t={t}, env_idx={env_idx}")
                return False
        
        except Exception as e:
            main_logger.error(f"RolloutBuffer.add: 数据验证时出错! t={t}, env_idx={env_idx}, 错误={e}")
            return False
        
        # 【关键修复】数据合理性检查
        if np.isnan(obs).any() or np.isinf(obs).any():
            main_logger.error(f"RolloutBuffer.add: 无效的观测数据! t={t}, env_idx={env_idx}")
            return False
        
        if np.isnan(action).any() or np.isinf(action).any():
            main_logger.error(f"RolloutBuffer.add: 无效的动作数据! t={t}, env_idx={env_idx}")
            return False
        
        if np.isnan(value).any() or np.isinf(value).any():
            main_logger.error(f"RolloutBuffer.add: 无效的价值数据! t={t}, env_idx={env_idx}")
            return False
        
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
        self.gru_hidden_states[t, env_idx] = gru_hidden_state.cpu().numpy()
        
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
        
        # 【关键修复】标记该位置已存储低层数据
        self.low_level_stored_mask[t, env_idx] = True
        self.storage_stats['total_low_level_success'] += 1
        
        # 【关键修复】记录最近的存储操作信息
        self.storage_stats['last_storage_info'] = {
            'type': 'low_level',
            'time_step': t,
            'env_idx': env_idx,
            'team_skill': team_skill,
            'reward_mean': np.mean(reward) if hasattr(reward, '__len__') else reward
        }
        
        # 【关键修复】添加详细的调试信息（仅在必要时）
        if t % 500 == 0 or env_idx == 0:  # 减少日志频率
            main_logger.debug(f"RolloutBuffer.add: 成功存储数据 t={t}, env_idx={env_idx}, "
                             f"team_skill={team_skill}, reward={np.mean(reward) if hasattr(reward, '__len__') else reward:.4f}")
        
        return True
    
    def add_high_level_data(self, env_idx, time_step, state_value=None, agent_values=None, 
                           team_log_prob=None, agent_log_probs=None, joint_log_prob=None, 
                           accumulated_reward=None, value=None):
        """
        【关键修复】为高层策略添加分离的数据到指定的时间步和环境
        
        参数:
            env_idx: 环境索引
            time_step: 时间步索引（通常是技能分配时的时间步）
            state_value: 状态价值 V^h(ŝ) [标量]
            agent_values: 智能体价值列表 V^h(ô_i) [n_agents]
            team_log_prob: 团队技能log概率 [标量]
            agent_log_probs: 个体技能log概率列表 [n_agents]
            joint_log_prob: 联合log概率（向后兼容）[标量]
            accumulated_reward: k步累积奖励 [标量]
            value: 统一价值估计（向后兼容）[标量]
        """
        # 【关键修复】更新存储统计信息
        self.storage_stats['total_high_level_attempts'] += 1
        
        # 【第三优先级修复】增强边界检查和数据验证
        if time_step >= self.num_steps:
            main_logger.error(f"add_high_level_data: 时间步越界! time_step={time_step} >= num_steps={self.num_steps}, env_idx={env_idx}")
            return False
        
        if env_idx >= self.num_envs:
            main_logger.error(f"add_high_level_data: 环境索引越界! env_idx={env_idx} >= num_envs={self.num_envs}, time_step={time_step}")
            return False
        
        # 【关键修复】使用专门的存储状态跟踪数组检查重复存储
        if self.high_level_valid_mask[time_step, env_idx]:
            self.storage_stats['duplicate_high_level_attempts'] += 1
            main_logger.warning(f"add_high_level_data: 重复存储高层数据! time_step={time_step}, env_idx={env_idx}")
            return False  # 阻止重复写入
        
        # 【关键修复】处理向后兼容性和新的分离数据格式
        # 优先使用新的分离数据格式，如果没有提供则使用旧格式
        final_state_value = state_value if state_value is not None else value
        final_agent_values = agent_values if agent_values is not None else [value] * self.n_agents
        final_team_log_prob = team_log_prob if team_log_prob is not None else joint_log_prob
        final_agent_log_probs = agent_log_probs if agent_log_probs is not None else [joint_log_prob / self.n_agents] * self.n_agents
        final_joint_log_prob = joint_log_prob if joint_log_prob is not None else (final_team_log_prob + sum(final_agent_log_probs))
        final_accumulated_reward = accumulated_reward if accumulated_reward is not None else 0.0
        
        # 【第三优先级修复】数据合理性检查
        if final_state_value is not None and (np.isnan(final_state_value) or np.isinf(final_state_value)):
            main_logger.error(f"add_high_level_data: 无效的状态价值! state_value={final_state_value}, time_step={time_step}, env_idx={env_idx}")
            return False
        
        if final_agent_values is not None:
            for i, agent_val in enumerate(final_agent_values):
                if np.isnan(agent_val) or np.isinf(agent_val):
                    main_logger.error(f"add_high_level_data: 无效的智能体{i}价值! agent_value={agent_val}, time_step={time_step}, env_idx={env_idx}")
                    return False
        
        if final_team_log_prob is not None and (np.isnan(final_team_log_prob) or np.isinf(final_team_log_prob)):
            main_logger.error(f"add_high_level_data: 无效的团队log概率! team_log_prob={final_team_log_prob}, time_step={time_step}, env_idx={env_idx}")
            return False
        
        if final_agent_log_probs is not None:
            for i, agent_log_prob in enumerate(final_agent_log_probs):
                if np.isnan(agent_log_prob) or np.isinf(agent_log_prob):
                    main_logger.error(f"add_high_level_data: 无效的智能体{i}log概率! agent_log_prob={agent_log_prob}, time_step={time_step}, env_idx={env_idx}")
                    return False
        
        if np.isnan(final_accumulated_reward) or np.isinf(final_accumulated_reward):
            main_logger.error(f"add_high_level_data: 无效的累积奖励! accumulated_reward={final_accumulated_reward}, time_step={time_step}, env_idx={env_idx}")
            return False
        
        # 【关键修复】存储分离的高层数据
        if final_state_value is not None:
            self.high_level_state_values[time_step, env_idx] = final_state_value
        
        if final_agent_values is not None:
            self.high_level_agent_values[time_step, env_idx] = final_agent_values
        
        if final_team_log_prob is not None:
            self.high_level_team_log_probs[time_step, env_idx] = final_team_log_prob
        
        if final_agent_log_probs is not None:
            self.high_level_agent_log_probs[time_step, env_idx] = final_agent_log_probs
        
        # 存储联合数据和累积奖励
        self.high_level_joint_log_probs[time_step, env_idx] = final_joint_log_prob
        self.high_level_rewards[time_step, env_idx] = final_accumulated_reward
        
        # 向后兼容：存储统一价值（使用状态价值）
        self.high_level_values[time_step, env_idx] = final_state_value if final_state_value is not None else 0.0
        
        # 标记有效数据
        self.high_level_valid_mask[time_step, env_idx] = True
        
        # 【关键修复】标记该位置已存储高层数据并更新统计
        self.high_level_stored_mask[time_step, env_idx] = True
        self.storage_stats['total_high_level_success'] += 1
        
        # 【关键修复】记录最近的高层存储操作信息
        self.storage_stats['last_storage_info'] = {
            'type': 'high_level',
            'time_step': time_step,
            'env_idx': env_idx,
            'state_value': final_state_value,
            'team_log_prob': final_team_log_prob,
            'accumulated_reward': final_accumulated_reward
        }
        
        main_logger.debug(f"add_high_level_data: 成功存储分离的高层数据 env={env_idx}, step={time_step}, "
                         f"state_value={final_state_value:.4f}, team_log_prob={final_team_log_prob:.4f}, "
                         f"reward={final_accumulated_reward:.4f}")
        return True
    
    def compute_advantages(self, last_values, dones, gamma=0.99, gae_lambda=0.95, denormalized_values=None, denormalized_last_values=None):
        """
        【修复版本】标准化的GAE计算方法，在整个rollout收集完毕后调用一次。
        这确保了严格的on-policy更新流程。

        参数:
            last_values (np.ndarray): Rollout最后一步之后的状态价值，Shape (num_envs, n_agents)
            dones (np.ndarray): 最后一步的完成标志，Shape (num_envs, n_agents) 或 (num_envs,)
            gamma (float): 折扣因子
            gae_lambda (float): GAE lambda参数
            denormalized_values (np.ndarray, optional): 【新增】反归一化后的价值估计。如果提供，将使用此值计算GAE。
            denormalized_last_values (np.ndarray, optional): 【新增】反归一化后的最后一步价值。
        """
        # 【第三优先级修复】增强输入验证和调试信息
        main_logger.debug(f"compute_advantages: 开始计算GAE，last_values形状={last_values.shape}, dones形状={dones.shape}")
        
        # 验证输入形状
        if last_values.shape != (self.num_envs, self.n_agents):
            main_logger.error(f"compute_advantages: last_values形状错误! 期望{(self.num_envs, self.n_agents)}, 实际{last_values.shape}")
            return
        
        # 确保dones的形状正确
        if dones.ndim == 1:
            # 如果dones是 (num_envs,)，扩展为 (num_envs, n_agents)
            dones = np.broadcast_to(dones[:, np.newaxis], (self.num_envs, self.n_agents))
            main_logger.debug(f"compute_advantages: 扩展dones形状为 {dones.shape}")
        
        # 【第三优先级修复】检查数据中的NaN/Inf值
        if np.isnan(last_values).any() or np.isinf(last_values).any():
            main_logger.error("compute_advantages: last_values中发现NaN或Inf值!")
            return
        
        if np.isnan(self.rewards).any() or np.isinf(self.rewards).any():
            main_logger.error("compute_advantages: rewards中发现NaN或Inf值!")
            return
        
        if np.isnan(self.values).any() or np.isinf(self.values).any():
            main_logger.error("compute_advantages: values中发现NaN或Inf值!")
            return

        # 【核心修改】选择用于计算的价值
        values_for_gae = denormalized_values if denormalized_values is not None else self.values
        last_values_for_gae = denormalized_last_values if denormalized_last_values is not None else last_values
        
        # 将dones转换为masks，方便计算
        # masks[t] = 1.0 if a transition from t -> t+1 is not terminal, else 0.0
        masks = 1.0 - self.dones.astype(np.float32)

        last_advantage = np.zeros((self.num_envs, self.n_agents), dtype=np.float32)
        
        # 【第三优先级修复】添加详细的计算过程调试信息
        nan_count = 0
        inf_count = 0
        
        # 从后往前计算GAE
        for t in reversed(range(self.num_steps)):
            # 如果是缓冲区的最后一步，next_value就是传入的last_values
            if t == self.num_steps - 1:
                next_values = last_values_for_gae
                next_done = dones.astype(np.float32)
            else:
                next_values = values_for_gae[t + 1]
                next_done = self.dones[t + 1].astype(np.float32)
            
            # delta_t = r_t + gamma * V(s_{t+1}) * (1 - done_{t+1}) - V(s_t)
            delta = (self.rewards[t] + 
                    gamma * next_values * (1.0 - next_done) - 
                    values_for_gae[t])
            
            # advantage_t = delta_t + gamma * lambda * advantage_{t+1} * (1 - done_t)
            last_advantage = (delta + 
                            gamma * gae_lambda * last_advantage * (1.0 - next_done))
            self.advantages[t] = last_advantage
            
            # 【第三优先级修复】检查每步计算结果
            if np.isnan(last_advantage).any():
                nan_count += 1
                if nan_count <= 3:  # 只记录前几个错误
                    main_logger.error(f"compute_advantages: 步骤{t}产生NaN优势值! delta范围=[{np.min(delta):.4f}, {np.max(delta):.4f}]")
            
            if np.isinf(last_advantage).any():
                inf_count += 1
                if inf_count <= 3:  # 只记录前几个错误
                    main_logger.error(f"compute_advantages: 步骤{t}产生Inf优势值! delta范围=[{np.min(delta):.4f}, {np.max(delta):.4f}]")

        # 计算Returns = GAE + V(s)
        self.returns = self.advantages + values_for_gae
        
        # 【第三优先级修复】最终结果验证和统计
        adv_mean = np.mean(self.advantages)
        adv_std = np.std(self.advantages)
        ret_mean = np.mean(self.returns)
        ret_std = np.std(self.returns)
        
        main_logger.info(f"compute_advantages: GAE计算完成。优势值统计: 均值={adv_mean:.4f}, 标准差={adv_std:.4f}")
        main_logger.info(f"compute_advantages: Returns统计: 均值={ret_mean:.4f}, 标准差={ret_std:.4f}")
        
        if nan_count > 0:
            main_logger.error(f"compute_advantages: 发现{nan_count}个时间步产生NaN值!")
        if inf_count > 0:
            main_logger.error(f"compute_advantages: 发现{inf_count}个时间步产生Inf值!")

    def compute_high_level_advantages(self, high_level_last_values=None, num_steps=None, gamma=0.99, gae_lambda=0.95):
        """
        【关键修复】为高层策略计算分离的GAE优势和返回值
        支持团队技能和个体技能的分离价值函数
        
        参数:
            high_level_last_values: 最后状态的高层价值估计，可以是：
                - dict: {'state': [num_envs], 'agents': [num_envs, n_agents]}
                - array: [num_envs] (向后兼容，将用作状态价值)
            num_steps: 实际收集的时间步数
            gamma: 折扣因子
            gae_lambda: GAE参数
        """
        if num_steps is None:
            main_logger.error("compute_high_level_advantages: 必须提供 num_steps 参数")
            return
        
        # 处理最后价值的输入格式
        if high_level_last_values is None:
            last_state_values = np.zeros(self.num_envs, dtype=np.float32)
            last_agent_values = np.zeros((self.num_envs, self.n_agents), dtype=np.float32)
        elif isinstance(high_level_last_values, dict):
            last_state_values = high_level_last_values.get('state', np.zeros(self.num_envs, dtype=np.float32))
            last_agent_values = high_level_last_values.get('agents', np.zeros((self.num_envs, self.n_agents), dtype=np.float32))
        else:
            # 向后兼容：将单一价值用作状态价值
            last_state_values = high_level_last_values
            last_agent_values = np.tile(high_level_last_values[:, np.newaxis], (1, self.n_agents))
        
        # 为每个环境分别计算高层策略的GAE
        for env_idx in range(self.num_envs):
            # 找到该环境的所有有效高层决策时间步
            valid_steps = []
            for t in range(num_steps):
                if self.high_level_valid_mask[t, env_idx]:
                    valid_steps.append(t)
            
            if len(valid_steps) == 0:
                continue
            
            # 【关键修复】分别处理团队技能和个体技能的GAE计算
            
            # === 1. 团队技能GAE计算（使用状态价值函数） ===
            rewards_seq = self.high_level_rewards[valid_steps, env_idx]
            state_values_seq = self.high_level_state_values[valid_steps, env_idx]
            
            # 计算next_values序列
            next_state_values_seq = np.zeros_like(state_values_seq)
            if len(valid_steps) > 1:
                next_state_values_seq[:-1] = state_values_seq[1:]
            next_state_values_seq[-1] = last_state_values[env_idx]
            
            # 高层策略没有中间的done信号，所以全部设为False
            dones_seq = np.zeros_like(state_values_seq, dtype=np.float32)
            
            # 转换为tensor并计算团队技能GAE
            rewards_tensor = torch.tensor(rewards_seq, dtype=torch.float32)
            state_values_tensor = torch.tensor(state_values_seq, dtype=torch.float32)
            next_state_values_tensor = torch.tensor(next_state_values_seq, dtype=torch.float32)
            dones_tensor = torch.tensor(dones_seq, dtype=torch.float32)
            
            team_advantages, team_returns = compute_gae(
                rewards_tensor, state_values_tensor, next_state_values_tensor, dones_tensor, gamma, gae_lambda
            )
            
            # 存储团队技能的结果
            for i, t in enumerate(valid_steps):
                self.high_level_team_advantages[t, env_idx] = team_advantages[i].item()
                self.high_level_team_returns[t, env_idx] = team_returns[i].item()
            
            # === 2. 个体技能GAE计算（使用智能体价值函数） ===
            agent_values_seq = self.high_level_agent_values[valid_steps, env_idx]  # (len(valid_steps), n_agents)
            
            # 为每个智能体分别计算GAE
            for agent_idx in range(self.n_agents):
                agent_values_single = agent_values_seq[:, agent_idx]
                
                # 计算next_values序列
                next_agent_values_seq = np.zeros_like(agent_values_single)
                if len(valid_steps) > 1:
                    next_agent_values_seq[:-1] = agent_values_single[1:]
                next_agent_values_seq[-1] = last_agent_values[env_idx, agent_idx]
                
                # 转换为tensor并计算个体技能GAE
                agent_values_tensor = torch.tensor(agent_values_single, dtype=torch.float32)
                next_agent_values_tensor = torch.tensor(next_agent_values_seq, dtype=torch.float32)
                
                agent_advantages, agent_returns = compute_gae(
                    rewards_tensor, agent_values_tensor, next_agent_values_tensor, dones_tensor, gamma, gae_lambda
                )
                
                # 存储个体技能的结果
                for i, t in enumerate(valid_steps):
                    self.high_level_agent_advantages[t, env_idx, agent_idx] = agent_advantages[i].item()
                    self.high_level_agent_returns[t, env_idx, agent_idx] = agent_returns[i].item()
            
            # === 3. 向后兼容：计算统一的优势和回报 ===
            # 使用团队技能的结果作为统一结果（向后兼容）
            for i, t in enumerate(valid_steps):
                self.high_level_advantages[t, env_idx] = team_advantages[i].item()
                self.high_level_returns[t, env_idx] = team_returns[i].item()
        
        main_logger.debug(f"高层策略分离GAE计算完成，共处理{np.sum(self.high_level_valid_mask[:num_steps])}个有效决策")
    
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

        # 使用 swapaxes 和 reshape 来安全地展平 E 和 A 维度
        # (T, E, A, F) -> (E, A, T, F) -> (E*A, T, F) -> (T, E*A, F)
        def flatten_sequences(arr):
            # T, E, A, ... -> E, A, T, ...
            swapped = arr[:num_steps].swapaxes(0, 1).swapaxes(1, 2).copy()
            # E, A, T, ... -> E*A, T, ...
            flat = swapped.reshape(num_total_sequences, num_steps, *swapped.shape[3:])
            # E*A, T, ... -> T, E*A, ...
            return flat.swapaxes(0, 1)

        obs_flat = flatten_sequences(self.obs)
        actions_flat = flatten_sequences(self.actions)
        log_probs_flat = flatten_sequences(self.log_probs)
        advantages_flat = flatten_sequences(self.advantages)
        returns_flat = flatten_sequences(self.returns)
        dones_flat = flatten_sequences(self.dones)
        
        # 对于没有Agent维度的数据，通过重复扩展以匹配序列总数
        def flatten_sequences_no_agent(arr):
            # T, E, ... -> E, T, ...
            swapped = arr[:num_steps].swapaxes(0, 1)
            # E, T, ... -> E, 1, T, ...
            expanded = np.expand_dims(swapped, axis=1)
            # E, 1, T, ... -> E, A, T, ...
            repeated = np.repeat(expanded, self.n_agents, axis=1)
            # E, A, T, ... -> E*A, T, ...
            flat = repeated.reshape(num_total_sequences, num_steps, *repeated.shape[3:])
            # E*A, T, ... -> T, E*A, ...
            return flat.swapaxes(0, 1)
        
        global_states_flat = flatten_sequences_no_agent(self.states)
        team_skills_flat = flatten_sequences_no_agent(self.team_skills)
        agent_skills_flat = flatten_sequences(self.agent_skills)

        # 初始隐状态 (T, E, A, H) -> [0] -> (E, A, H) -> (E*A, H)
        initial_hxs = self.gru_hidden_states[0].reshape(num_total_sequences, -1)
        
        sequence_indices = np.arange(num_total_sequences)
        
        main_logger.debug(f"Discoverer sampler: {num_total_sequences} sequences, {num_sequences_per_batch} per batch, {ppo_epochs} epochs.")
        
        for epoch in range(ppo_epochs):
            np.random.shuffle(sequence_indices)
            
            for start in range(0, num_total_sequences, num_sequences_per_batch):
                end = min(start + num_sequences_per_batch, num_total_sequences)
                batch_indices = sequence_indices[start:end]
                
                obs_tensor = torch.from_numpy(obs_flat[:, batch_indices]).float()
                hxs_tensor = torch.from_numpy(initial_hxs[batch_indices]).float()

                yield {
                    'observations': obs_tensor,
                    'actions': torch.from_numpy(actions_flat[:, batch_indices]).float(),
                    'log_probs': torch.from_numpy(log_probs_flat[:, batch_indices]).float(),
                    'advantages': torch.from_numpy(advantages_flat[:, batch_indices]).float(),
                    'returns': torch.from_numpy(returns_flat[:, batch_indices]).float(),
                    'global_states': torch.from_numpy(global_states_flat[:, batch_indices]).float(),
                    'team_skills': torch.from_numpy(team_skills_flat[:, batch_indices]).long(),
                    'agent_skills': torch.from_numpy(agent_skills_flat[:, batch_indices]).long(),
                    'initial_hxs': hxs_tensor,
                    'dones': torch.from_numpy(dones_flat[:, batch_indices]).float()
                }

    def diagnose_buffer_state(self, num_steps=None):
        """
        【第三优先级修复】诊断缓冲区状态，检查数据完整性和一致性
        
        参数:
            num_steps: 要检查的步数，如果为None则检查所有步数
        """
        if num_steps is None:
            num_steps = self.num_steps
        
        main_logger.info("=" * 50)
        main_logger.info("RolloutBuffer 诊断报告")
        main_logger.info("=" * 50)
        
        # 基础信息
        main_logger.info(f"缓冲区配置: {self.num_steps}步 x {self.num_envs}环境 x {self.n_agents}智能体")
        main_logger.info(f"检查范围: 前{num_steps}步")
        
        # 检查低层数据完整性
        obs_filled = np.any(self.obs[:num_steps] != 0, axis=(2, 3))  # (T, E)
        actions_filled = np.any(self.actions[:num_steps] != 0, axis=(2, 3))  # (T, E)
        rewards_filled = np.any(self.rewards[:num_steps] != 0, axis=2)  # (T, E)
        values_filled = np.any(self.values[:num_steps] != 0, axis=2)  # (T, E)
        
        obs_fill_rate = np.mean(obs_filled) * 100
        actions_fill_rate = np.mean(actions_filled) * 100
        rewards_fill_rate = np.mean(rewards_filled) * 100
        values_fill_rate = np.mean(values_filled) * 100
        
        main_logger.info(f"低层数据填充率:")
        main_logger.info(f"  观测: {obs_fill_rate:.1f}%, 动作: {actions_fill_rate:.1f}%")
        main_logger.info(f"  奖励: {rewards_fill_rate:.1f}%, 价值: {values_fill_rate:.1f}%")
        
        # 检查高层数据完整性
        high_level_count = np.sum(self.high_level_valid_mask[:num_steps])
        high_level_rate = high_level_count / (num_steps * self.num_envs) * 100
        
        main_logger.info(f"高层数据:")
        main_logger.info(f"  有效决策: {high_level_count}个 ({high_level_rate:.1f}%)")
        
        # 按环境统计高层数据分布
        env_high_level_counts = np.sum(self.high_level_valid_mask[:num_steps], axis=0)
        main_logger.info(f"  各环境高层决策数: {env_high_level_counts}")
        
        # 检查数据质量
        nan_issues = []
        inf_issues = []
        
        # 检查观测数据
        if np.isnan(self.obs[:num_steps]).any():
            nan_issues.append("观测")
        if np.isinf(self.obs[:num_steps]).any():
            inf_issues.append("观测")
        
        # 检查奖励数据
        if np.isnan(self.rewards[:num_steps]).any():
            nan_issues.append("奖励")
        if np.isinf(self.rewards[:num_steps]).any():
            inf_issues.append("奖励")
        
        # 检查价值数据
        if np.isnan(self.values[:num_steps]).any():
            nan_issues.append("价值")
        if np.isinf(self.values[:num_steps]).any():
            inf_issues.append("价值")
        
        # 检查高层数据
        if np.isnan(self.high_level_values[:num_steps]).any():
            nan_issues.append("高层价值")
        if np.isinf(self.high_level_values[:num_steps]).any():
            inf_issues.append("高层价值")
        
        if nan_issues:
            main_logger.error(f"发现NaN值: {', '.join(nan_issues)}")
        if inf_issues:
            main_logger.error(f"发现Inf值: {', '.join(inf_issues)}")
        
        if not nan_issues and not inf_issues:
            main_logger.info("数据质量检查: 通过 ✓")
        
        # 奖励统计
        reward_mean = np.mean(self.rewards[:num_steps])
        reward_std = np.std(self.rewards[:num_steps])
        reward_min = np.min(self.rewards[:num_steps])
        reward_max = np.max(self.rewards[:num_steps])
        
        main_logger.info(f"奖励统计: 均值={reward_mean:.4f}, 标准差={reward_std:.4f}")
        main_logger.info(f"奖励范围: [{reward_min:.4f}, {reward_max:.4f}]")
        
        # 技能分布统计
        if np.any(self.team_skills[:num_steps] >= 0):
            team_skill_counts = np.bincount(self.team_skills[:num_steps].flatten(), minlength=self.n_Z)
            main_logger.info(f"团队技能分布: {team_skill_counts}")
        
        main_logger.info("=" * 50)
        return {
            'obs_fill_rate': obs_fill_rate,
            'actions_fill_rate': actions_fill_rate,
            'rewards_fill_rate': rewards_fill_rate,
            'values_fill_rate': values_fill_rate,
            'high_level_count': high_level_count,
            'high_level_rate': high_level_rate,
            'has_nan': len(nan_issues) > 0,
            'has_inf': len(inf_issues) > 0,
            'reward_stats': {
                'mean': reward_mean,
                'std': reward_std,
                'min': reward_min,
                'max': reward_max
            }
        }

    def get_all_high_level_returns(self, num_steps):
        """
        获取所有有效的高层回报，用于更新Value Normalization统计量。
        """
        valid_returns = []
        for t in range(num_steps):
            for env_idx in range(self.num_envs):
                if self.high_level_valid_mask[t, env_idx]:
                    valid_returns.append(self.high_level_returns[t, env_idx])
        return np.array(valid_returns, dtype=np.float32)

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
    
    def get_storage_stats(self):
        """
        【关键修复】获取存储操作的统计信息，用于调试和监控
        
        返回:
            dict: 包含存储统计信息的字典
        """
        stats = self.storage_stats.copy()
        
        # 计算成功率
        if stats['total_low_level_attempts'] > 0:
            stats['low_level_success_rate'] = stats['total_low_level_success'] / stats['total_low_level_attempts']
        else:
            stats['low_level_success_rate'] = 0.0
            
        if stats['total_high_level_attempts'] > 0:
            stats['high_level_success_rate'] = stats['total_high_level_success'] / stats['total_high_level_attempts']
        else:
            stats['high_level_success_rate'] = 0.0
        
        # 计算重复率
        if stats['total_low_level_attempts'] > 0:
            stats['low_level_duplicate_rate'] = stats['duplicate_low_level_attempts'] / stats['total_low_level_attempts']
        else:
            stats['low_level_duplicate_rate'] = 0.0
            
        if stats['total_high_level_attempts'] > 0:
            stats['high_level_duplicate_rate'] = stats['duplicate_high_level_attempts'] / stats['total_high_level_attempts']
        else:
            stats['high_level_duplicate_rate'] = 0.0
        
        # 添加存储状态掩码的统计
        stats['low_level_stored_positions'] = int(np.sum(self.low_level_stored_mask))
        stats['high_level_stored_positions'] = int(np.sum(self.high_level_stored_mask))
        stats['high_level_valid_positions'] = int(np.sum(self.high_level_valid_mask))
        
        return stats
    
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
