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
    重构后的Rollout缓冲区，旨在解决数据污染问题。
    该缓冲区为每个环境维护一个独立的列表，用于存储一个完整rollout的数据。
    在每次训练更新后，缓冲区将被清空，确保新旧rollout数据完全隔离。
    """
    def __init__(self, num_steps, num_envs, n_agents, obs_dim, action_dim, gru_hidden_size, n_Z, n_z, state_dim, action_space_type='continuous'):
        # 存储配置参数
        self.num_steps = num_steps
        self.num_envs = num_envs
        self.n_agents = n_agents
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.gru_hidden_size = gru_hidden_size
        self.n_Z = n_Z
        self.n_z = n_z
        self.state_dim = state_dim
        self.action_space_type = action_space_type
        
        # 初始化数据存储结构
        self.reset()
        main_logger.info("已初始化重构后的RolloutBuffer，采用基于列表的独立存储。")

    def reset(self):
        """
        清空所有存储的数据，为下一个完整的rollout做准备。
        这是解决数据污染问题的核心机制。
        """
        # 为每个环境创建一个独立的存储列表
        self.buffers = [[] for _ in range(self.num_envs)]
        
        # GAE和Returns现在是实例属性，在计算时被填充
        self.advantages = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.returns = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        
        # 高层策略的GAE和Returns
        self.high_level_advantages = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_returns = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_team_advantages = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_agent_advantages = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.high_level_team_returns = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_agent_returns = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        
        main_logger.debug("RolloutBuffer已重置，所有环境的数据列表已清空。")

    def add(self, t, state, obs, action, reward, done, value, log_prob, gru_hidden_state, env_idx, team_skill=None, agent_skills=None, reward_env=None, reward_team_disc=None, reward_ind_disc=None):
        """
        将一个时间步的数据追加到指定环境的列表中。
        增强了数据验证和错误处理。
        """
        # 【修复1】增强输入验证
        if env_idx >= self.num_envs:
            main_logger.error(f"RolloutBuffer.add: 环境索引越界! env_idx={env_idx} >= num_envs={self.num_envs}")
            return False
        
        # 【修复2】验证数据维度
        try:
            obs = np.asarray(obs)
            action = np.asarray(action)
            reward = np.asarray(reward)
            done = np.asarray(done)
            value = np.asarray(value)
            log_prob = np.asarray(log_prob)
            
            # 验证观测维度
            if obs.shape != (self.n_agents, self.obs_dim):
                main_logger.error(f"观测维度错误: 期望 ({self.n_agents}, {self.obs_dim}), 实际 {obs.shape}")
                return False
            
            # 验证动作维度
            expected_action_shape = (self.n_agents, self.action_dim) if self.action_space_type == 'continuous' else (self.n_agents,)
            if action.shape != expected_action_shape:
                main_logger.error(f"动作维度错误: 期望 {expected_action_shape}, 实际 {action.shape}")
                return False
            
            # 验证GRU隐状态维度
            if isinstance(gru_hidden_state, torch.Tensor):
                if gru_hidden_state.shape != (self.n_agents, self.gru_hidden_size):
                    main_logger.error(f"GRU隐状态维度错误: 期望 ({self.n_agents}, {self.gru_hidden_size}), 实际 {gru_hidden_state.shape}")
                    return False
                gru_hidden_state_np = gru_hidden_state.cpu().numpy()
            else:
                gru_hidden_state_np = np.asarray(gru_hidden_state)
                if gru_hidden_state_np.shape != (self.n_agents, self.gru_hidden_size):
                    main_logger.error(f"GRU隐状态维度错误: 期望 ({self.n_agents}, {self.gru_hidden_size}), 实际 {gru_hidden_state_np.shape}")
                    return False
            
        except Exception as e:
            main_logger.error(f"数据类型转换失败: {e}")
            return False
        
        # 【修复3】检查时间步一致性
        if self.buffers[env_idx]:
            last_t = self.buffers[env_idx][-1].get("t", -1)
            if t <= last_t:
                main_logger.error(f"时间步倒退或重复: 环境{env_idx}, 当前t={t}, 上一个t={last_t}")
                return False
        
        # 检查当前环境的缓冲区是否已满
        if len(self.buffers[env_idx]) >= self.num_steps:
            main_logger.error(f"RolloutBuffer.add: 环境 {env_idx} 的缓冲区已满 (容量: {self.num_steps})，这表示训练循环逻辑有严重错误！")
            # 【修复4】更严格的溢出处理
            return False

        # 将所有数据打包成一个字典并追加
        experience = {
            "t": t,
            "state": np.asarray(state, dtype=np.float32),
            "obs": obs.astype(np.float32),
            "action": action,  # 保持原始类型（可能是int或float）
            "reward": reward.astype(np.float32),
            "done": done.astype(np.bool_),
            "value": value.astype(np.float32),
            "log_prob": log_prob.astype(np.float32),
            "gru_hidden_state": gru_hidden_state_np.astype(np.float32),
            "team_skill": int(team_skill) if team_skill is not None else -1,
            "agent_skills": np.asarray(agent_skills, dtype=np.int64) if agent_skills is not None else np.full(self.n_agents, -1, dtype=np.int64),
            "reward_env": np.asarray(reward_env, dtype=np.float32) if reward_env is not None else np.zeros_like(reward, dtype=np.float32),
            "reward_team_disc": np.asarray(reward_team_disc, dtype=np.float32) if reward_team_disc is not None else np.zeros_like(reward, dtype=np.float32),
            "reward_ind_disc": np.asarray(reward_ind_disc, dtype=np.float32) if reward_ind_disc is not None else np.zeros_like(reward, dtype=np.float32),
            # 高层数据占位符
            "is_high_level": False,
            "high_level_state_value": 0.0,
            "high_level_agent_values": np.zeros(self.n_agents, dtype=np.float32),
            "high_level_team_log_prob": 0.0,
            "high_level_agent_log_probs": np.zeros(self.n_agents, dtype=np.float32),
            "high_level_reward": 0.0
        }
        self.buffers[env_idx].append(experience)
        return True

    def add_high_level_data(self, env_idx, time_step, state_value=None, agent_values=None, 
                           team_log_prob=None, agent_log_probs=None, accumulated_reward=None, **kwargs):
        """
        将高层策略数据更新到指定时间步的经验字典中。
        """
        if env_idx >= self.num_envs:
            main_logger.error(f"add_high_level_data: 环境索引越界! env_idx={env_idx}")
            return False
        
        if time_step >= len(self.buffers[env_idx]):
            main_logger.error(f"add_high_level_data: 时间步索引越界! time_step={time_step} >= buffer_len={len(self.buffers[env_idx])}")
            return False

        # 更新对应时间步的字典
        experience = self.buffers[env_idx][time_step]
        experience["is_high_level"] = True
        experience["high_level_state_value"] = state_value if state_value is not None else 0.0
        experience["high_level_agent_values"] = np.array(agent_values, dtype=np.float32) if agent_values is not None else np.zeros(self.n_agents, dtype=np.float32)
        experience["high_level_team_log_prob"] = team_log_prob if team_log_prob is not None else 0.0
        experience["high_level_agent_log_probs"] = np.array(agent_log_probs, dtype=np.float32) if agent_log_probs is not None else np.zeros(self.n_agents, dtype=np.float32)
        experience["high_level_reward"] = accumulated_reward if accumulated_reward is not None else 0.0
        
        return True

    def _get_full_rollout_data(self):
        """
        在计算GAE或采样前，将存储的列表数据转换为Numpy数组。
        这是从灵活存储到高效计算的桥梁。
        """
        if not any(self.buffers):
            return None

        # 【修复】使用最大长度，并创建掩码
        max_steps = 0
        for buf in self.buffers:
            if buf:
                # 确保 't' 存在
                if 't' in buf[-1]:
                    max_steps = max(max_steps, buf[-1]['t'] + 1)
        max_steps = min(max_steps, self.num_steps)

        if max_steps == 0:
            return None
        
        num_actual_steps = max_steps
        masks = np.zeros((num_actual_steps, self.num_envs), dtype=np.bool_)
        
        # 根据数据类型和形状预分配Numpy数组
        obs = np.zeros((num_actual_steps, self.num_envs, self.n_agents, self.obs_dim), dtype=np.float32)
        if self.action_space_type == 'discrete':
            actions = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.int64)
        else:
            actions = np.zeros((num_actual_steps, self.num_envs, self.n_agents, self.action_dim), dtype=np.float32)
        rewards = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.float32)
        values = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.float32)
        log_probs = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.float32)
        dones = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.bool_)
        states = np.zeros((num_actual_steps, self.num_envs, self.state_dim), dtype=np.float32)
        team_skills = np.zeros((num_actual_steps, self.num_envs), dtype=np.int64)
        agent_skills = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.int64)
        gru_hidden_states = np.zeros((num_actual_steps, self.num_envs, self.n_agents, self.gru_hidden_size), dtype=np.float32)
        
        # 高层数据
        high_level_valid_mask = np.zeros((num_actual_steps, self.num_envs), dtype=np.bool_)
        high_level_rewards = np.zeros((num_actual_steps, self.num_envs), dtype=np.float32)
        high_level_state_values = np.zeros((num_actual_steps, self.num_envs), dtype=np.float32)
        high_level_agent_values = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.float32)
        high_level_team_log_probs = np.zeros((num_actual_steps, self.num_envs), dtype=np.float32)
        high_level_agent_log_probs = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.float32)
        
        # 【关键修复】为内在奖励组成部分预分配数组
        reward_env = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.float32)
        reward_team_disc = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.float32)
        reward_ind_disc = np.zeros((num_actual_steps, self.num_envs, self.n_agents), dtype=np.float32)

        # 填充数组
        for env_idx, buffer in enumerate(self.buffers):
            for exp in buffer:
                t = exp.get("t", -1)
                if t >= num_actual_steps or t < 0: continue
                masks[t, env_idx] = True
                obs[t, env_idx] = exp["obs"]
                actions[t, env_idx] = exp["action"]
                rewards[t, env_idx] = exp["reward"]
                values[t, env_idx] = exp["value"]
                log_probs[t, env_idx] = exp["log_prob"]
                dones[t, env_idx] = exp["done"]
                states[t, env_idx] = exp["state"]
                team_skills[t, env_idx] = exp["team_skill"]
                agent_skills[t, env_idx] = exp["agent_skills"]
                gru_hidden_states[t, env_idx] = exp["gru_hidden_state"]
                
                # 【关键修复】填充内在奖励组成部分
                if exp["reward_env"] is not None:
                    reward_env[t, env_idx] = exp["reward_env"]
                if exp["reward_team_disc"] is not None:
                    reward_team_disc[t, env_idx] = exp["reward_team_disc"]
                if exp["reward_ind_disc"] is not None:
                    reward_ind_disc[t, env_idx] = exp["reward_ind_disc"]
                
                if exp["is_high_level"]:
                    high_level_valid_mask[t, env_idx] = True
                    high_level_rewards[t, env_idx] = exp["high_level_reward"]
                    high_level_state_values[t, env_idx] = exp["high_level_state_value"]
                    high_level_agent_values[t, env_idx] = exp["high_level_agent_values"]
                    high_level_team_log_probs[t, env_idx] = exp["high_level_team_log_prob"]
                    high_level_agent_log_probs[t, env_idx] = exp["high_level_agent_log_probs"]

        return {
            "num_actual_steps": num_actual_steps,
            "masks": masks,
            "obs": obs, "actions": actions, "rewards": rewards, "values": values,
            "log_probs": log_probs, "dones": dones, "states": states,
            "team_skills": team_skills, "agent_skills": agent_skills,
            "gru_hidden_states": gru_hidden_states,
            "high_level_valid_mask": high_level_valid_mask,
            "high_level_rewards": high_level_rewards,
            "high_level_state_values": high_level_state_values,
            "high_level_agent_values": high_level_agent_values,
            "high_level_team_log_probs": high_level_team_log_probs,
            "high_level_agent_log_probs": high_level_agent_log_probs,
            # 【关键修复】在返回的字典中包含奖励组成部分
            "reward_env": reward_env,
            "reward_team_disc": reward_team_disc,
            "reward_ind_disc": reward_ind_disc
        }

    def compute_advantages(self, last_values, dones, gamma=0.99, gae_lambda=0.95):
        """
        在整个rollout收集完毕后，计算低层策略的GAE。
        """
        data = self._get_full_rollout_data()
        if data is None:
            main_logger.error("无法获取完整的Rollout数据，跳过GAE计算。")
            return

        num_actual_steps = data["num_actual_steps"]
        rewards = data["rewards"]
        values = data["values"]
        dones_rollout = data["dones"]
        masks = data.get("masks", np.ones((num_actual_steps, self.num_envs), dtype=np.bool_))

        last_advantage = np.zeros((self.num_envs, self.n_agents), dtype=np.float32)
        
        # 确保 dones 形状正确
        if dones.ndim == 1:
            dones = np.broadcast_to(dones[:, np.newaxis], (self.num_envs, self.n_agents))

        # 对终止的环境，将last_values置零
        last_values = last_values * (1.0 - dones)

        for t in reversed(range(num_actual_steps)):
            mask_t = masks[t]
            if t == num_actual_steps - 1:
                next_non_terminal = 1.0 - dones
                next_values = last_values
            else:
                next_non_terminal = 1.0 - dones_rollout[t + 1]
                next_values = values[t + 1]
            
            delta = rewards[t] + gamma * next_values * next_non_terminal - values[t]
            last_advantage = delta + gamma * gae_lambda * next_non_terminal * last_advantage
            
            # 使用掩码确保只更新有效步骤的优势
            self.advantages[t] = last_advantage * mask_t[:, np.newaxis]

        self.returns = self.advantages + values
        main_logger.debug(f"低层策略GAE计算完成，共处理 {num_actual_steps} 步。")

    def compute_high_level_advantages(self, high_level_last_values, gamma=0.99, gae_lambda=0.95):
        """
        为高层策略计算GAE。
        """
        data = self._get_full_rollout_data()
        if data is None:
            main_logger.error("无法获取完整的Rollout数据，跳过高层GAE计算。")
            return
        
        num_actual_steps = data["num_actual_steps"]
        
        # 处理不同格式的 last_values
        if isinstance(high_level_last_values, dict):
            last_state_values = high_level_last_values.get('state', np.zeros(self.num_envs))
            last_agent_values = high_level_last_values.get('agents', np.zeros((self.num_envs, self.n_agents)))
        else: # 兼容旧格式
            last_state_values = high_level_last_values
            last_agent_values = np.tile(high_level_last_values[:, np.newaxis], (1, self.n_agents))

        for env_idx in range(self.num_envs):
            valid_steps = [t for t, exp in enumerate(self.buffers[env_idx]) if exp["is_high_level"]]
            if not valid_steps:
                continue

            rewards_seq = np.array([self.buffers[env_idx][t]["high_level_reward"] for t in valid_steps])
            state_values_seq = np.array([self.buffers[env_idx][t]["high_level_state_value"] for t in valid_steps])
            
            next_state_values_seq = np.zeros_like(state_values_seq)
            if len(valid_steps) > 1:
                next_state_values_seq[:-1] = state_values_seq[1:]
            next_state_values_seq[-1] = last_state_values[env_idx]
            
            dones_seq = np.zeros_like(state_values_seq, dtype=np.float32) # 高层策略无中间done

            team_advantages, team_returns = self._compute_gae_torch(
                rewards_seq, state_values_seq, next_state_values_seq, dones_seq, gamma, gae_lambda
            )

            for i, t in enumerate(valid_steps):
                self.high_level_team_advantages[t, env_idx] = team_advantages[i].item()
                self.high_level_team_returns[t, env_idx] = team_returns[i].item()
                self.high_level_advantages[t, env_idx] = team_advantages[i].item() # 向后兼容
                self.high_level_returns[t, env_idx] = team_returns[i].item()   # 向后兼容

            # 为每个智能体计算GAE
            for agent_idx in range(self.n_agents):
                agent_values_seq = np.array([self.buffers[env_idx][t]["high_level_agent_values"][agent_idx] for t in valid_steps])
                next_agent_values_seq = np.zeros_like(agent_values_seq)
                if len(valid_steps) > 1:
                    next_agent_values_seq[:-1] = agent_values_seq[1:]
                next_agent_values_seq[-1] = last_agent_values[env_idx, agent_idx]

                agent_advantages, agent_returns = self._compute_gae_torch(
                    rewards_seq, agent_values_seq, next_agent_values_seq, dones_seq, gamma, gae_lambda
                )
                for i, t in enumerate(valid_steps):
                    self.high_level_agent_advantages[t, env_idx, agent_idx] = agent_advantages[i].item()
                    self.high_level_agent_returns[t, env_idx, agent_idx] = agent_returns[i].item()

        main_logger.debug("高层策略GAE计算完成。")

    def _compute_gae_torch(self, rewards, values, next_values, dones, gamma, lam):
        rewards = torch.tensor(rewards, dtype=torch.float32)
        values = torch.tensor(values, dtype=torch.float32)
        next_values = torch.tensor(next_values, dtype=torch.float32)
        dones = torch.tensor(dones, dtype=torch.float32)
        return compute_gae(rewards, values, next_values, dones, gamma, lam)

    def get_all_high_level_returns(self, num_steps):
        """获取所有有效的高层回报，用于更新Value Normalization"""
        data = self._get_full_rollout_data()
        if data is None:
            return np.array([])
        
        valid_mask = data["high_level_valid_mask"][:num_steps]
        team_returns = self.high_level_team_returns[:num_steps][valid_mask]
        agent_returns = self.high_level_agent_returns[:num_steps][valid_mask]
        
        # 将团队和个体回报合并为一个列表
        all_returns = np.concatenate([team_returns.flatten(), agent_returns.flatten()])
        return all_returns

    def get_discoverer_sampler(self, ppo_epochs, num_sequences_per_batch):
        """
        为Discoverer生成序列采样器。
        """
        data = self._get_full_rollout_data()
        if data is None:
            main_logger.warning("无有效数据，无法创建Discoverer采样器。")
            return None

        num_steps = data["num_actual_steps"]
        num_total_sequences = self.num_envs * self.n_agents

        def flatten_sequences(arr):
            """
            【修复】安全的序列展平，保持物理意义
            输入: (T, E, A, D) -> 输出: (T, E*A, D)
            保持时间步连续性和智能体-环境对应关系
            """
            T, E, A = arr.shape[:3]
            remaining_dims = arr.shape[3:]
            
            # 验证输入维度
            expected_shape = (num_steps, self.num_envs, self.n_agents) + remaining_dims
            if arr.shape[:3] != expected_shape[:3]:
                main_logger.error(f"flatten_sequences输入维度错误: 期望前3维{expected_shape[:3]}, 实际{arr.shape[:3]}")
                raise ValueError(f"维度不匹配: {arr.shape} vs {expected_shape}")
            
            # 安全的维度变换: (T, E, A, D) -> (T, E*A, D)
            # 方法: 先转置为 (E, A, T, D)，然后重塑为 (E*A, T, D)，最后转置为 (T, E*A, D)
            result = arr.transpose(1, 2, 0, *range(3, len(arr.shape)))  # (E, A, T, D...)
            result = result.reshape(E * A, T, *remaining_dims)  # (E*A, T, D...)
            result = result.transpose(1, 0, *range(2, len(result.shape)))  # (T, E*A, D...)
            
            # 验证输出维度
            expected_output_shape = (T, E * A) + remaining_dims
            if result.shape != expected_output_shape:
                main_logger.error(f"flatten_sequences输出维度错误: 期望{expected_output_shape}, 实际{result.shape}")
                raise ValueError(f"输出维度错误: {result.shape}")
            
            return result

        def flatten_sequences_no_agent(arr):
            """
            【修复】安全的无智能体维度序列展平
            输入: (T, E) -> 输出: (T, E*A)
            为每个环境复制智能体维度
            """
            T, E = arr.shape[:2]
            remaining_dims = arr.shape[2:]
            
            # 验证输入维度
            expected_shape = (num_steps, self.num_envs) + remaining_dims
            if arr.shape[:2] != expected_shape[:2]:
                main_logger.error(f"flatten_sequences_no_agent输入维度错误: 期望前2维{expected_shape[:2]}, 实际{arr.shape[:2]}")
                raise ValueError(f"维度不匹配: {arr.shape} vs {expected_shape}")
            
            # 安全的维度变换: (T, E, D) -> (T, E*A, D)
            # 方法: 添加智能体维度并重复，然后展平
            result = np.expand_dims(arr, axis=2)  # (T, E, 1, D...)
            result = np.repeat(result, self.n_agents, axis=2)  # (T, E, A, D...)
            result = result.reshape(T, E * self.n_agents, *remaining_dims)  # (T, E*A, D...)
            
            # 验证输出维度
            expected_output_shape = (T, E * self.n_agents) + remaining_dims
            if result.shape != expected_output_shape:
                main_logger.error(f"flatten_sequences_no_agent输出维度错误: 期望{expected_output_shape}, 实际{result.shape}")
                raise ValueError(f"输出维度错误: {result.shape}")
            
            return result

        masks_flat = flatten_sequences_no_agent(data["masks"])
        obs_flat = flatten_sequences(data["obs"])
        actions_flat = flatten_sequences(data["actions"])
        log_probs_flat = flatten_sequences(data["log_probs"])
        advantages_flat = flatten_sequences(self.advantages)
        returns_flat = flatten_sequences(self.returns)
        value_preds_flat = flatten_sequences(data["values"])
        dones_flat = flatten_sequences(data["dones"])
        global_states_flat = flatten_sequences_no_agent(data["states"])
        team_skills_flat = flatten_sequences_no_agent(data["team_skills"])
        agent_skills_flat = flatten_sequences(data["agent_skills"])
        
        # 初始隐状态
        initial_hxs = data["gru_hidden_states"][0].reshape(num_total_sequences, -1)
        initial_critic_hxs = data["gru_hidden_states"][0].reshape(num_total_sequences, -1)
        
        sequence_indices = np.arange(num_total_sequences)
        
        for epoch in range(ppo_epochs):
            np.random.shuffle(sequence_indices)
            for start in range(0, num_total_sequences, num_sequences_per_batch):
                end = min(start + num_sequences_per_batch, num_total_sequences)
                batch_indices = sequence_indices[start:end]
                
                # 检查agent_skills_flat的有效性
                agent_skills_batch = agent_skills_flat[:, batch_indices]
                if np.any(agent_skills_batch < 0) or np.any(agent_skills_batch >= self.n_z):
                    main_logger.error(f"发现无效的agent_skill值! 范围: [{np.min(agent_skills_batch)}, {np.max(agent_skills_batch)}]")
                    # 跳过这个有问题的批次
                    continue

                yield {
                    'observations': torch.from_numpy(obs_flat[:, batch_indices]).float(),
                    'actions': torch.from_numpy(actions_flat[:, batch_indices]).float(),
                    'log_probs': torch.from_numpy(log_probs_flat[:, batch_indices]).float(),
                    'advantages': torch.from_numpy(advantages_flat[:, batch_indices]).float(),
                    'returns': torch.from_numpy(returns_flat[:, batch_indices]).float(),
                    'value_preds': torch.from_numpy(value_preds_flat[:, batch_indices]).float(),
                    'global_states': torch.from_numpy(global_states_flat[:, batch_indices]).float(),
                    'team_skills': torch.from_numpy(team_skills_flat[:, batch_indices]).long(),
                    'agent_skills': torch.from_numpy(agent_skills_batch).long(),
                    'initial_hxs': torch.from_numpy(initial_hxs[batch_indices]).float(),
                    'initial_critic_hxs': torch.from_numpy(initial_critic_hxs[batch_indices]).float(),
                    'dones': torch.from_numpy(dones_flat[:, batch_indices]).float(),
                    'masks': torch.from_numpy(masks_flat[:, batch_indices]).bool()
                }

    def get_coordinator_sampler(self, num_steps, ppo_epochs, num_sequences_per_batch):
        """
        为Coordinator生成采样器。
        """
        data = self._get_full_rollout_data()
        if data is None:
            main_logger.warning("无有效数据，无法创建Coordinator采样器。")
            return None

        valid_time_steps, valid_env_indices = np.where(data["high_level_valid_mask"][:num_steps])
        num_valid_samples = len(valid_time_steps)
        if num_valid_samples == 0:
            return None

        valid_indices = np.arange(num_valid_samples)
        
        for epoch in range(ppo_epochs):
            np.random.shuffle(valid_indices)
            for start in range(0, num_valid_samples, num_sequences_per_batch):
                end = min(start + num_sequences_per_batch, num_valid_samples)
                batch_indices = valid_indices[start:end]
                
                time_batch = valid_time_steps[batch_indices]
                env_batch = valid_env_indices[batch_indices]
                
                yield {
                    'observations': torch.from_numpy(data["obs"][time_batch, env_batch]).float(),
                    'states': torch.from_numpy(data["states"][time_batch, env_batch]).float(),
                    'team_skills': torch.from_numpy(data["team_skills"][time_batch, env_batch]).long(),
                    'agent_skills': torch.from_numpy(data["agent_skills"][time_batch, env_batch]).long(),
                    'old_team_log_probs': torch.from_numpy(data["high_level_team_log_probs"][time_batch, env_batch]).float(),
                    'old_agent_log_probs': torch.from_numpy(data["high_level_agent_log_probs"][time_batch, env_batch]).float(),
                    'team_advantages': torch.from_numpy(self.high_level_team_advantages[time_batch, env_batch]).float(),
                    'agent_advantages': torch.from_numpy(self.high_level_agent_advantages[time_batch, env_batch]).float(),
                    'team_returns': torch.from_numpy(self.high_level_team_returns[time_batch, env_batch]).float(),
                    'agent_returns': torch.from_numpy(self.high_level_agent_returns[time_batch, env_batch]).float(),
                    'values': torch.from_numpy(data["high_level_state_values"][time_batch, env_batch]).float(),
                }

class DiscriminatorBuffer:
    """
    独立的、Off-Policy的判别器经验回放缓冲区。
    存储状态-技能对，用于训练判别器网络。
    """
    def __init__(self, capacity):
        """
        初始化判别器缓冲区。
        
        参数:
            capacity (int): 缓冲区的最大容量。
        """
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
        self._total_added = 0
        self._total_sampled = 0
        main_logger.info(f"初始化Off-Policy判别器Buffer，最大容量: {capacity}")

    def push(self, experience):
        """
        将单个经验存入缓冲区。
        经验应该是一个字典，包含type, state/obs, skill等信息。
        
        参数:
            experience (dict): 经验字典。
        """
        if not isinstance(experience, dict):
            main_logger.error(f"判别器Buffer只接受字典类型的经验, 但收到了 {type(experience)}")
            return
            
        self.buffer.append(experience)
        self._total_added += 1

    def sample(self, batch_size):
        """
        从缓冲区中随机采样一批经验。
        
        参数:
            batch_size (int): 采样批次的大小。
            
        返回:
            list: 包含经验字典的列表。
        """
        if len(self.buffer) < batch_size:
            # main_logger.warning(f"判别器Buffer中的样本数({len(self.buffer)})"
            #                   f"少于请求的批次大小({batch_size})，将返回所有可用样本。")
            batch_size = len(self.buffer)
            
        sampled_batch = random.sample(self.buffer, batch_size)
        self._total_sampled += len(sampled_batch)
        return sampled_batch

    def __len__(self):
        """返回缓冲区的当前大小。"""
        return len(self.buffer)

    def get_stats(self):
        """获取缓冲区统计信息。"""
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
