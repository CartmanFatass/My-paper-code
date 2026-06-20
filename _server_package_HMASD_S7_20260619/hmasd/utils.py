import torch
import numpy as np
import time
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
        if not isinstance(experience, tuple):
            experience = (experience,)

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

        self.reset()
        main_logger.info("已初始化重构后的RolloutBuffer，采用预分配数组存储。")

    def reset(self):
        """
        清空所有存储的数据，为下一个完整的rollout做准备。
        这是解决数据污染问题的核心机制。
        """
        self.masks = np.zeros((self.num_steps, self.num_envs), dtype=np.bool_)
        self.env_lengths = np.zeros(self.num_envs, dtype=np.int32)
        self.last_t_per_env = np.full(self.num_envs, -1, dtype=np.int32)

        self.states = np.zeros((self.num_steps, self.num_envs, self.state_dim), dtype=np.float32)
        self.obs = np.zeros((self.num_steps, self.num_envs, self.n_agents, self.obs_dim), dtype=np.float32)
        if self.action_space_type == 'discrete':
            self.actions = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.int64)
        else:
            self.actions = np.zeros((self.num_steps, self.num_envs, self.n_agents, self.action_dim), dtype=np.float32)
        self.rewards = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.dones = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.bool_)
        self.values = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.log_probs = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.team_skills = np.full((self.num_steps, self.num_envs), -1, dtype=np.int64)
        self.agent_skills = np.full((self.num_steps, self.num_envs, self.n_agents), -1, dtype=np.int64)
        self.gru_hidden_states = np.zeros(
            (self.num_steps, self.num_envs, self.n_agents, self.gru_hidden_size), dtype=np.float32
        )
        self.critic_gru_hidden_states = np.zeros_like(self.gru_hidden_states)
        self.reward_env = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.reward_team_disc = np.zeros_like(self.reward_env)
        self.reward_ind_disc = np.zeros_like(self.reward_env)

        self.high_level_valid_mask = np.zeros((self.num_steps, self.num_envs), dtype=np.bool_)
        self.high_level_rewards = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_state_values = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_agent_values = np.zeros(
            (self.num_steps, self.num_envs, self.n_agents), dtype=np.float32
        )
        self.high_level_team_log_probs = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_agent_log_probs = np.zeros(
            (self.num_steps, self.num_envs, self.n_agents), dtype=np.float32
        )

        self.advantages = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.returns = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)

        self.high_level_advantages = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_returns = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_team_advantages = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_agent_advantages = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.high_level_team_returns = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_agent_returns = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)

        self._cached_rollout_data = None
        self._profile = {
            "full_rollout_pack": 0.0,
            "full_rollout_pack_calls": 0,
            "full_rollout_cache_hits": 0,
        }

        main_logger.debug("RolloutBuffer已重置，预分配数组已清空。")

    def add(self, t, state, obs, action, reward, done, value, log_prob, gru_hidden_state, critic_gru_hidden_state, env_idx, team_skill=None, agent_skills=None, reward_env=None, reward_team_disc=None, reward_ind_disc=None):
        """
        将一个时间步的数据写入指定环境的预分配数组。
        增强了数据验证和错误处理。
        增加 critic_gru_hidden_state 参数。
        """
        if env_idx >= self.num_envs:
            main_logger.error(f"RolloutBuffer.add: 环境索引越界! env_idx={env_idx} >= num_envs={self.num_envs}")
            return False
        if t < 0 or t >= self.num_steps:
            main_logger.error(f"RolloutBuffer.add: 时间步索引越界! t={t}, num_steps={self.num_steps}")
            return False

        try:
            state = np.asarray(state, dtype=np.float32)
            obs = np.asarray(obs, dtype=np.float32)
            action = np.asarray(action)
            reward = self._agent_vector(reward, np.float32, "reward")
            done = self._agent_vector(done, np.bool_, "done")
            value = self._agent_vector(value, np.float32, "value")
            log_prob = self._agent_vector(log_prob, np.float32, "log_prob")

            if state.shape != (self.state_dim,):
                main_logger.error(f"状态维度错误: 期望 ({self.state_dim},), 实际 {state.shape}")
                return False
            if obs.shape != (self.n_agents, self.obs_dim):
                main_logger.error(f"观测维度错误: 期望 ({self.n_agents}, {self.obs_dim}), 实际 {obs.shape}")
                return False

            expected_action_shape = (self.n_agents, self.action_dim) if self.action_space_type == 'continuous' else (self.n_agents,)
            if action.shape != expected_action_shape:
                main_logger.error(f"动作维度错误: 期望 {expected_action_shape}, 实际 {action.shape}")
                return False

            gru_hidden_state_np = self._hidden_array(gru_hidden_state, "Actor GRU隐状态", env_idx, t)
            if gru_hidden_state_np is None:
                return False
            critic_gru_hidden_state_np = self._hidden_array(critic_gru_hidden_state, "Critic GRU隐状态", env_idx, t)
            if critic_gru_hidden_state_np is None:
                return False

            if agent_skills is None:
                agent_skills_arr = np.full(self.n_agents, -1, dtype=np.int64)
            else:
                agent_skills_arr = self._agent_vector(agent_skills, np.int64, "agent_skills")

            reward_env_arr = self._agent_vector(
                reward_env if reward_env is not None else np.zeros(self.n_agents, dtype=np.float32),
                np.float32,
                "reward_env",
            )
            reward_team_disc_arr = self._agent_vector(
                reward_team_disc if reward_team_disc is not None else np.zeros(self.n_agents, dtype=np.float32),
                np.float32,
                "reward_team_disc",
            )
            reward_ind_disc_arr = self._agent_vector(
                reward_ind_disc if reward_ind_disc is not None else np.zeros(self.n_agents, dtype=np.float32),
                np.float32,
                "reward_ind_disc",
            )

        except Exception as e:
            main_logger.error(f"数据类型转换失败: {e}")
            return False

        if t <= self.last_t_per_env[env_idx]:
            main_logger.error(f"时间步倒退或重复: 环境{env_idx}, 当前t={t}, 上一个t={self.last_t_per_env[env_idx]}")
            return False
        if self.masks[t, env_idx]:
            main_logger.error(f"RolloutBuffer.add: 重复写入 env={env_idx}, t={t}")
            return False

        self.masks[t, env_idx] = True
        self.env_lengths[env_idx] = max(self.env_lengths[env_idx], int(t) + 1)
        self.last_t_per_env[env_idx] = int(t)
        self.states[t, env_idx] = state
        self.obs[t, env_idx] = obs
        self.actions[t, env_idx] = action.astype(self.actions.dtype, copy=False)
        self.rewards[t, env_idx] = reward
        self.dones[t, env_idx] = done
        self.values[t, env_idx] = value
        self.log_probs[t, env_idx] = log_prob
        self.gru_hidden_states[t, env_idx] = gru_hidden_state_np
        self.critic_gru_hidden_states[t, env_idx] = critic_gru_hidden_state_np
        self.team_skills[t, env_idx] = int(team_skill) if team_skill is not None else -1
        self.agent_skills[t, env_idx] = agent_skills_arr
        self.reward_env[t, env_idx] = reward_env_arr
        self.reward_team_disc[t, env_idx] = reward_team_disc_arr
        self.reward_ind_disc[t, env_idx] = reward_ind_disc_arr
        self._cached_rollout_data = None
        return True

    def add_high_level_data(self, env_idx, time_step, state_value=None, agent_values=None, 
                           team_log_prob=None, agent_log_probs=None, accumulated_reward=None, **kwargs):
        """
        将高层策略数据更新到指定时间步的数组槽位中。
        """
        if env_idx >= self.num_envs:
            main_logger.error(f"add_high_level_data: 环境索引越界! env_idx={env_idx}")
            return False
        if time_step < 0 or time_step >= self.num_steps:
            main_logger.error(f"add_high_level_data: 时间步索引越界! time_step={time_step}")
            return False
        if not self.masks[time_step, env_idx]:
            main_logger.error(
                f"add_high_level_data: 时间步尚未写入低层数据! env_idx={env_idx}, time_step={time_step}"
            )
            return False

        self.high_level_valid_mask[time_step, env_idx] = True
        self.high_level_state_values[time_step, env_idx] = state_value if state_value is not None else 0.0
        self.high_level_agent_values[time_step, env_idx] = self._agent_vector(
            agent_values if agent_values is not None else np.zeros(self.n_agents, dtype=np.float32),
            np.float32,
            "high_level_agent_values",
        )
        self.high_level_team_log_probs[time_step, env_idx] = team_log_prob if team_log_prob is not None else 0.0
        self.high_level_agent_log_probs[time_step, env_idx] = self._agent_vector(
            agent_log_probs if agent_log_probs is not None else np.zeros(self.n_agents, dtype=np.float32),
            np.float32,
            "high_level_agent_log_probs",
        )
        self.high_level_rewards[time_step, env_idx] = accumulated_reward if accumulated_reward is not None else 0.0
        self._cached_rollout_data = None
        return True

    def _get_full_rollout_data(self):
        """
        返回当前rollout的有效数组视图。
        """
        if not np.any(self.masks):
            return None

        if self._cached_rollout_data is not None:
            self._profile["full_rollout_cache_hits"] += 1
            return self._cached_rollout_data

        start_time = time.perf_counter()
        num_actual_steps = int(np.max(self.env_lengths))
        num_actual_steps = min(num_actual_steps, self.num_steps)
        if num_actual_steps == 0:
            return None

        sl = slice(0, num_actual_steps)
        data = {
            "num_actual_steps": num_actual_steps,
            "masks": self.masks[sl],
            "obs": self.obs[sl],
            "actions": self.actions[sl],
            "rewards": self.rewards[sl],
            "values": self.values[sl],
            "log_probs": self.log_probs[sl],
            "dones": self.dones[sl],
            "states": self.states[sl],
            "team_skills": self.team_skills[sl],
            "agent_skills": self.agent_skills[sl],
            "gru_hidden_states": self.gru_hidden_states[sl],
            "critic_gru_hidden_states": self.critic_gru_hidden_states[sl],
            "high_level_valid_mask": self.high_level_valid_mask[sl],
            "high_level_rewards": self.high_level_rewards[sl],
            "high_level_state_values": self.high_level_state_values[sl],
            "high_level_agent_values": self.high_level_agent_values[sl],
            "high_level_team_log_probs": self.high_level_team_log_probs[sl],
            "high_level_agent_log_probs": self.high_level_agent_log_probs[sl],
            "reward_env": self.reward_env[sl],
            "reward_team_disc": self.reward_team_disc[sl],
            "reward_ind_disc": self.reward_ind_disc[sl],
        }
        self._cached_rollout_data = data
        self._profile["full_rollout_pack"] += time.perf_counter() - start_time
        self._profile["full_rollout_pack_calls"] += 1
        return data

    def _agent_vector(self, value, dtype, name):
        arr = np.asarray(value, dtype=dtype)
        if arr.ndim == 0:
            return np.full(self.n_agents, arr.item(), dtype=dtype)
        arr = arr.reshape(-1) if arr.shape != (self.n_agents,) and arr.size == self.n_agents else arr
        if arr.shape != (self.n_agents,):
            raise ValueError(f"{name}维度错误: 期望 ({self.n_agents},), 实际 {arr.shape}")
        return arr.astype(dtype, copy=False)

    def _hidden_array(self, hidden_state, name, env_idx, t):
        if isinstance(hidden_state, torch.Tensor):
            hidden_np = hidden_state.detach().cpu().numpy()
        else:
            hidden_np = np.asarray(hidden_state, dtype=np.float32)
        if hidden_np.ndim == 3 and hidden_np.shape[0] == 1:
            hidden_np = hidden_np.squeeze(0)
        if hidden_np.shape != (self.n_agents, self.gru_hidden_size):
            main_logger.error(
                f"{name}维度错误: 期望 ({self.n_agents}, {self.gru_hidden_size}), "
                f"实际 {hidden_np.shape}, env={env_idx}, t={t}"
            )
            return None
        return hidden_np.astype(np.float32, copy=False)

    def get_profile(self, reset=False):
        profile = dict(self._profile)
        if reset:
            for key in self._profile:
                self._profile[key] = 0 if key.endswith("_calls") or key.endswith("_hits") else 0.0
        return profile

    def compute_advantages(self, last_values, dones, gamma=0.99, gae_lambda=0.95, value_normalizer=None):
        """
        在整个rollout收集完毕后，计算低层策略的GAE。
        
        【RunningMeanStd归一化修复】
        如果提供了 value_normalizer，则网络输出的 values 是归一化的。
        必须将其反归一化为真实尺度，才能与真实尺度的 rewards 进行 GAE 计算。
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

        # 【反归一化逻辑】
        if value_normalizer is not None:
            mean = value_normalizer.mean
            var = value_normalizer.var
            std = np.sqrt(var + 1e-8)
            
            # 反归一化 values (网络输出)
            # 注意：我们创建一个副本用于计算，不修改 stored values (因为PPO update需要归一化的values)
            values_real = values * std + mean
            
            # 反归一化 last_values (网络输出)
            last_values_real = last_values * std + mean
            
            main_logger.debug("RolloutBuffer: 已对低层价值进行反归一化用于GAE计算。")
        else:
            values_real = values
            last_values_real = last_values

        last_advantage = np.zeros((self.num_envs, self.n_agents), dtype=np.float32)
        
        if dones.ndim == 1:
            dones = np.broadcast_to(dones[:, np.newaxis], (self.num_envs, self.n_agents))

        last_values_real = last_values_real * (1.0 - dones)

        for t in reversed(range(num_actual_steps)):
            mask_t = masks[t]

            if t == num_actual_steps - 1:
                next_non_terminal = 1.0 - dones
                curr_next_val = last_values_real
            else:
                next_non_terminal = 1.0 - dones_rollout[t + 1]
                curr_next_val = values_real[t + 1]

            curr_val = values_real[t]

            delta = rewards[t] + gamma * curr_next_val * next_non_terminal - curr_val

            last_advantage = delta + gamma * gae_lambda * next_non_terminal * last_advantage

            self.advantages[t] = last_advantage * mask_t[:, np.newaxis]

        self.returns[:num_actual_steps] = self.advantages[:num_actual_steps] + values_real
            
        main_logger.debug(f"低层策略GAE计算完成，共处理 {num_actual_steps} 步。")

    def compute_high_level_advantages(self, high_level_last_values, gamma=0.99, gae_lambda=0.95, value_normalizer=None):
        """
        为高层策略计算GAE。
        
        【RunningMeanStd归一化修复】
        如果提供了 value_normalizer，则网络输出的 values 是归一化的。
        必须将其反归一化为真实尺度，才能与真实尺度的 rewards 进行 GAE 计算。
        """
        data = self._get_full_rollout_data()
        if data is None:
            main_logger.error("无法获取完整的Rollout数据，跳过高层GAE计算。")
            return
        
        num_actual_steps = data["num_actual_steps"]
        
        if isinstance(high_level_last_values, dict):
            last_state_values = high_level_last_values.get('state', np.zeros(self.num_envs))
            last_agent_values = high_level_last_values.get('agents', np.zeros((self.num_envs, self.n_agents)))
        else:
            last_state_values = high_level_last_values
            last_agent_values = np.tile(high_level_last_values[:, np.newaxis], (1, self.n_agents))

        if value_normalizer is not None:
            mean = value_normalizer.mean
            var = value_normalizer.var
            std = np.sqrt(var + 1e-8)

            last_state_values_real = last_state_values * std + mean
            last_agent_values_real = last_agent_values * std + mean

            main_logger.debug("RolloutBuffer: 已对高层价值进行反归一化用于GAE计算。")
        else:
            mean, std = 0.0, 1.0
            last_state_values_real = last_state_values
            last_agent_values_real = last_agent_values

        high_level_valid_mask = data["high_level_valid_mask"]
        high_level_rewards = data["high_level_rewards"]
        high_level_state_values = data["high_level_state_values"]
        high_level_agent_values = data["high_level_agent_values"]

        for env_idx in range(self.num_envs):
            valid_steps = np.flatnonzero(high_level_valid_mask[:num_actual_steps, env_idx])
            if valid_steps.size == 0:
                continue

            rewards_seq = high_level_rewards[valid_steps, env_idx]
            state_values_seq = high_level_state_values[valid_steps, env_idx]

            if value_normalizer is not None:
                state_values_seq_real = state_values_seq * std + mean
            else:
                state_values_seq_real = state_values_seq

            next_state_values_seq_real = np.zeros_like(state_values_seq_real)
            if len(valid_steps) > 1:
                next_state_values_seq_real[:-1] = state_values_seq_real[1:]
            next_state_values_seq_real[-1] = last_state_values_real[env_idx]

            dones_seq = np.zeros_like(state_values_seq_real, dtype=np.float32)

            team_advantages, team_returns = self._compute_gae_torch(
                rewards_seq, state_values_seq_real, next_state_values_seq_real, dones_seq, gamma, gae_lambda
            )

            for i, t in enumerate(valid_steps):
                self.high_level_team_advantages[t, env_idx] = team_advantages[i].item()
                self.high_level_team_returns[t, env_idx] = team_returns[i].item()
                self.high_level_advantages[t, env_idx] = team_advantages[i].item()
                self.high_level_returns[t, env_idx] = team_returns[i].item()

            for agent_idx in range(self.n_agents):
                agent_values_seq = high_level_agent_values[valid_steps, env_idx, agent_idx]

                if value_normalizer is not None:
                    agent_values_seq_real = agent_values_seq * std + mean
                else:
                    agent_values_seq_real = agent_values_seq

                next_agent_values_seq_real = np.zeros_like(agent_values_seq_real)
                if len(valid_steps) > 1:
                    next_agent_values_seq_real[:-1] = agent_values_seq_real[1:]
                next_agent_values_seq_real[-1] = last_agent_values_real[env_idx, agent_idx]

                agent_advantages, agent_returns = self._compute_gae_torch(
                    rewards_seq, agent_values_seq_real, next_agent_values_seq_real, dones_seq, gamma, gae_lambda
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

    def get_discoverer_sampler(self, ppo_epochs, num_sequences_per_batch, chunk_length=None, device=None, cache_tensors=False):
        """
        为Discoverer生成序列采样器，支持基于 Chunk 的序列切分。

        关键改进：
        引入 chunk_length 参数（通常为技能步长 k），将完整 Rollout 切分为多个小片段。
        每次 yield 的数据是一个 Batch 的小片段（Chunks），而不是整个 Rollout。
        这实现了真正的 Chunk-based PPO Update，解决了长序列梯度问题并提高了样本利用率。

        参数:
            ppo_epochs: 训练轮数
            num_sequences_per_batch: 每个 Batch 包含的序列（Chunk）数量
            chunk_length: 切分长度 (default: None, 即不切分)
            device: 可选目标设备；配合 cache_tensors=True 时提前缓存为Tensor
            cache_tensors: 是否在采样前将静态rollout数据转换到目标设备
        """
        data = self._get_full_rollout_data()
        if data is None:
            main_logger.warning("无有效数据，无法创建Discoverer采样器。")
            return None

        num_steps = data["num_actual_steps"]
        num_total_env_agents = self.num_envs * self.n_agents
        
        # 如果未指定 chunk_length，则使用整个 rollout 长度（兼容旧行为）
        actual_chunk_length = chunk_length if chunk_length is not None else num_steps
        
        # 计算切分数量
        num_chunks = num_steps // actual_chunk_length
        # 如果不能整除，舍弃最后不足一个 chunk 的部分
        effective_steps = num_chunks * actual_chunk_length
        
        if num_chunks == 0:
            main_logger.warning(f"Rollout长度({num_steps})小于Chunk长度({actual_chunk_length})，无法切分。")
            actual_chunk_length = num_steps
            num_chunks = 1
            effective_steps = num_steps

        # 总的序列（Chunk）数量 = 轨迹数 * 每条轨迹的Chunk数
        num_total_sequences = num_total_env_agents * num_chunks
        
        main_logger.info(f"Creating Discoverer Sampler: Rollout={num_steps}, Chunk={actual_chunk_length}, "
                        f"Num Chunks per Traj={num_chunks}, Total Sequences={num_total_sequences}")

        def flatten_and_chunk_sequences(arr, with_agent_dim=True):
            """
            将数据展平并切分为 Chunks。
            输出形状: (chunk_length, num_total_sequences, ...)
            """
            if with_agent_dim:
                # (T, E, A, ...)
                T, E, A = arr.shape[:3]
                remaining_dims = arr.shape[3:]
                # 1. 截断无效尾部数据
                arr = arr[:effective_steps]
                # 2. (T', E, A, ...) -> (num_chunks, chunk_len, E, A, ...)
                arr = arr.reshape(num_chunks, actual_chunk_length, E, A, *remaining_dims)
                # 3. (num_chunks, chunk_len, E, A, ...) -> (chunk_len, num_chunks, E, A, ...)
                arr = arr.transpose(1, 0, 2, 3, *range(4, len(arr.shape)))
                # 4. -> (chunk_len, num_chunks * E * A, ...)
                arr = arr.reshape(actual_chunk_length, num_chunks * E * A, *remaining_dims)
                return arr
            else:
                # (T, E, ...) - 需要广播 Agent 维度
                T, E = arr.shape[:2]
                remaining_dims = arr.shape[2:]
                # 0. 扩展 Agent 维度: (T, E, ...) -> (T, E, A, ...)
                arr = np.expand_dims(arr, axis=2)
                arr = np.repeat(arr, self.n_agents, axis=2)
                
                # 1. 截断
                arr = arr[:effective_steps]
                # 2. -> (num_chunks, chunk_len, E, A, ...)
                arr = arr.reshape(num_chunks, actual_chunk_length, E, self.n_agents, *remaining_dims)
                # 3. -> (chunk_len, num_chunks, E, A, ...)
                arr = arr.transpose(1, 0, 2, 3, *range(4, len(arr.shape)))
                # 4. -> (chunk_len, num_chunks * E * A, ...)
                arr = arr.reshape(actual_chunk_length, num_chunks * E * self.n_agents, *remaining_dims)
                return arr

        # 处理所有数据
        masks_flat = flatten_and_chunk_sequences(data["masks"], with_agent_dim=False)
        obs_flat = flatten_and_chunk_sequences(data["obs"])
        actions_flat = flatten_and_chunk_sequences(data["actions"])
        log_probs_flat = flatten_and_chunk_sequences(data["log_probs"])
        advantages_flat = flatten_and_chunk_sequences(self.advantages)
        returns_flat = flatten_and_chunk_sequences(self.returns)
        value_preds_flat = flatten_and_chunk_sequences(data["values"])
        dones_flat = flatten_and_chunk_sequences(data["dones"])
        global_states_flat = flatten_and_chunk_sequences(data["states"], with_agent_dim=False)
        team_skills_flat = flatten_and_chunk_sequences(data["team_skills"], with_agent_dim=False)
        agent_skills_flat = flatten_and_chunk_sequences(data["agent_skills"])
        
        # --- 处理初始 Hidden State ---
        # 我们需要取出每个 Chunk 起始时刻的 Hidden State
        # data["gru_hidden_states"] 形状: (T, E, A, H)
        
        # 1. 取出所有 Chunk 的起始步: 0, L, 2L, ...
        chunk_start_indices = np.arange(0, effective_steps, actual_chunk_length)
        
        # 2. 提取对应时刻的 Hidden State: (num_chunks, E, A, H)
        initial_hxs_chunked = data["gru_hidden_states"][chunk_start_indices]
        initial_critic_hxs_chunked = data["critic_gru_hidden_states"][chunk_start_indices]
        
        # 3. 展平为 (num_chunks * E * A, H)
        # 注意这里的顺序必须和上面 flatten_and_chunk_sequences 中的 reshape 顺序一致
        # 上面是 (chunk_len, num_chunks, E, A) -> reshape -> (chunk_len, num_chunks * E * A)
        # 也就意味着 batch 维度的顺序是: Chunk 0 (all envs/agents), Chunk 1 (all envs/agents)...
        # 所以我们这里也要保持这个顺序
        
        initial_hxs_flat = initial_hxs_chunked.reshape(num_chunks * self.num_envs * self.n_agents, -1)
        initial_critic_hxs_flat = initial_critic_hxs_chunked.reshape(num_chunks * self.num_envs * self.n_agents, -1)

        sequence_indices = np.arange(num_total_sequences)
        tensor_cache = None
        if cache_tensors and device is not None:
            tensor_cache = {
                'observations': torch.as_tensor(obs_flat, dtype=torch.float32, device=device),
                'actions': torch.as_tensor(actions_flat, dtype=torch.float32, device=device),
                'log_probs': torch.as_tensor(log_probs_flat, dtype=torch.float32, device=device),
                'advantages': torch.as_tensor(advantages_flat, dtype=torch.float32, device=device),
                'returns': torch.as_tensor(returns_flat, dtype=torch.float32, device=device),
                'value_preds': torch.as_tensor(value_preds_flat, dtype=torch.float32, device=device),
                'global_states': torch.as_tensor(global_states_flat, dtype=torch.float32, device=device),
                'team_skills': torch.as_tensor(team_skills_flat, dtype=torch.long, device=device),
                'agent_skills': torch.as_tensor(agent_skills_flat, dtype=torch.long, device=device),
                'initial_hxs': torch.as_tensor(initial_hxs_flat, dtype=torch.float32, device=device),
                'initial_critic_hxs': torch.as_tensor(initial_critic_hxs_flat, dtype=torch.float32, device=device),
                'dones': torch.as_tensor(dones_flat, dtype=torch.float32, device=device),
                'masks': torch.as_tensor(masks_flat, dtype=torch.bool, device=device),
            }
        
        for epoch in range(ppo_epochs):
            np.random.shuffle(sequence_indices)
            for start in range(0, num_total_sequences, num_sequences_per_batch):
                end = min(start + num_sequences_per_batch, num_total_sequences)
                batch_indices = sequence_indices[start:end]
                
                # 检查agent_skills_flat的有效性
                agent_skills_batch = agent_skills_flat[:, batch_indices]
                if np.any(agent_skills_batch < 0) or np.any(agent_skills_batch >= self.n_z):
                    main_logger.error(f"发现无效的agent_skill值! 范围: [{np.min(agent_skills_batch)}, {np.max(agent_skills_batch)}]")
                    continue

                if tensor_cache is not None:
                    batch_tensor = torch.as_tensor(batch_indices, dtype=torch.long, device=device)
                    yield {
                        'observations': tensor_cache['observations'][:, batch_tensor],
                        'actions': tensor_cache['actions'][:, batch_tensor],
                        'log_probs': tensor_cache['log_probs'][:, batch_tensor],
                        'advantages': tensor_cache['advantages'][:, batch_tensor],
                        'returns': tensor_cache['returns'][:, batch_tensor],
                        'value_preds': tensor_cache['value_preds'][:, batch_tensor],
                        'global_states': tensor_cache['global_states'][:, batch_tensor],
                        'team_skills': tensor_cache['team_skills'][:, batch_tensor],
                        'agent_skills': tensor_cache['agent_skills'][:, batch_tensor],
                        'initial_hxs': tensor_cache['initial_hxs'][batch_tensor],
                        'initial_critic_hxs': tensor_cache['initial_critic_hxs'][batch_tensor],
                        'dones': tensor_cache['dones'][:, batch_tensor],
                        'masks': tensor_cache['masks'][:, batch_tensor],
                    }
                else:
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
                        'initial_hxs': torch.from_numpy(initial_hxs_flat[batch_indices]).float(),
                        'initial_critic_hxs': torch.from_numpy(initial_critic_hxs_flat[batch_indices]).float(),
                        'dones': torch.from_numpy(dones_flat[:, batch_indices]).float(),
                        'masks': torch.from_numpy(masks_flat[:, batch_indices]).bool()
                    }

    def get_coordinator_sampler(self, num_steps, ppo_epochs, num_sequences_per_batch, device=None, cache_tensors=False):
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
        tensor_cache = None
        if cache_tensors and device is not None:
            tensor_cache = {
                'observations': torch.as_tensor(data["obs"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'states': torch.as_tensor(data["states"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'team_skills': torch.as_tensor(data["team_skills"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'agent_skills': torch.as_tensor(data["agent_skills"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'old_team_log_probs': torch.as_tensor(data["high_level_team_log_probs"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'old_agent_log_probs': torch.as_tensor(data["high_level_agent_log_probs"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'team_advantages': torch.as_tensor(self.high_level_team_advantages[valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'agent_advantages': torch.as_tensor(self.high_level_agent_advantages[valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'team_returns': torch.as_tensor(self.high_level_team_returns[valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'agent_returns': torch.as_tensor(self.high_level_agent_returns[valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'values': torch.as_tensor(data["high_level_state_values"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
            }
        
        for epoch in range(ppo_epochs):
            np.random.shuffle(valid_indices)
            for start in range(0, num_valid_samples, num_sequences_per_batch):
                end = min(start + num_sequences_per_batch, num_valid_samples)
                batch_indices = valid_indices[start:end]
                
                if tensor_cache is not None:
                    batch_tensor = torch.as_tensor(batch_indices, dtype=torch.long, device=device)
                    yield {key: value[batch_tensor] for key, value in tensor_cache.items()}
                else:
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

    def extend(self, experiences):
        """
        批量追加经验，保持与 push() 相同的字典schema。
        """
        if experiences is None:
            return

        added = 0
        for experience in experiences:
            if not isinstance(experience, dict):
                main_logger.error(f"判别器Buffer只接受字典类型的经验, 但收到了 {type(experience)}")
                continue
            self.buffer.append(experience)
            added += 1

        self._total_added += added

    def clear(self):
        """清空缓冲区"""
        self.buffer.clear()
        self._total_added = 0
        self._total_sampled = 0

    def sample(self, batch_size):
        """
        从缓冲区中随机采样一批经验。
        
        参数:
            batch_size (int): 采样批次的大小。
            
        返回:
            list: 包含经验字典的列表。
        """
        if len(self.buffer) < batch_size:
            batch_size = len(self.buffer)
            
        sampled_batch = random.sample(self.buffer, batch_size)
        self._total_sampled += len(sampled_batch)
        return sampled_batch

    def get_all(self):
        """
        【论文一致性修复】获取当前 rollout 收集的全部数据。
        
        用于 On-Policy 的判别器更新，确保使用当前策略产生的完整数据进行训练。
        
        返回:
            list: 包含所有经验字典的列表。
        """
        return list(self.buffer)

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
    dist = policy
    log_probs = dist.log_prob(actions)

    ratio = torch.exp(log_probs - old_log_probs)
    surr1 = ratio * advantages
    surr2 = torch.clamp(ratio, 1.0 - clip_epsilon, 1.0 + clip_epsilon) * advantages
    policy_loss = -torch.min(surr1, surr2).mean()

    value_loss = 0.5 * ((returns - values) ** 2).mean()

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
