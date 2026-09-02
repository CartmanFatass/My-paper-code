import torch
import numpy as np
import time
import copy
from collections import deque
import random
from hmasd.logging import main_logger
from hmasd.process_exploration import SkillProcessOutcomeExtractor


def clone_replay_data(value):
    """Detach replay data from caller-owned mutable storage recursively."""
    if torch.is_tensor(value):
        return value.detach().clone()
    if isinstance(value, np.ndarray):
        return value.copy()
    if isinstance(value, dict):
        return {clone_replay_data(key): clone_replay_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clone_replay_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(clone_replay_data(item) for item in value)
    return copy.deepcopy(value)

class ReplayBuffer:
    """经验回放缓冲区，用于存储和采样训练数据"""
    def __init__(self, capacity, rng_seed=0):
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
        self._total_added = 0
        self._total_sampled = 0
        self._structure_validated = False
        self._rng = random.Random(int(rng_seed))
    
    def push(self, experience):
        """
        将经验存入缓冲区

        参数:
            experience: 经验元组，或参数列表(通过*args收集的多个参数)
        """
        if not isinstance(experience, (tuple, dict)):
            experience = (experience,)

        if len(self.buffer) >= self.capacity:
            self._total_added += 1

        self.buffer.append(clone_replay_data(experience))
        
    def clear(self):
        """清空缓冲区"""
        self.buffer.clear()
        self._total_added = 0
        self._total_sampled = 0
        self._structure_validated = False
    
    def sample(self, batch_size):
        """从缓冲区中随机采样一批经验"""
        sampled_batch = self._rng.sample(self.buffer, min(len(self.buffer), batch_size))
        self._total_sampled += len(sampled_batch)
        
        # 验证样本结构
        if not self._structure_validated and sampled_batch:
            sample_structure = len(sampled_batch[0])
            main_logger.debug(f"缓冲区样本结构: 包含 {sample_structure} 个元素")
            self._structure_validated = True
            
        return sampled_batch

    def get_rng_state(self):
        return self._rng.getstate()

    def set_rng_state(self, state):
        restored = random.Random()
        try:
            restored.setstate(state)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid ReplayBuffer RNG state") from exc
        self._rng = restored

    def state_dict(self):
        """Return the complete replay state required for an exact continuation."""
        return {
            "version": 1,
            "capacity": self.capacity,
            "buffer": copy.deepcopy(list(self.buffer)),
            "total_added": self._total_added,
            "total_sampled": self._total_sampled,
            "structure_validated": self._structure_validated,
            "rng_state": self.get_rng_state(),
        }

    def load_state_dict(self, state):
        required = {
            "version", "capacity", "buffer", "total_added", "total_sampled",
            "structure_validated", "rng_state",
        }
        if not isinstance(state, dict) or not required.issubset(state):
            raise ValueError("ReplayBuffer checkpoint is missing strict continuation state")
        if state["version"] != 1:
            raise ValueError("unsupported ReplayBuffer checkpoint version")
        if int(state["capacity"]) != int(self.capacity):
            raise ValueError("ReplayBuffer checkpoint capacity does not match runtime topology")
        rows = state["buffer"]
        if not isinstance(rows, list) or len(rows) > self.capacity:
            raise ValueError("invalid ReplayBuffer checkpoint contents")
        for name in ("total_added", "total_sampled"):
            if not isinstance(state[name], (int, np.integer)) or int(state[name]) < 0:
                raise ValueError(f"invalid ReplayBuffer {name}")
        if not isinstance(state["structure_validated"], (bool, np.bool_)):
            raise ValueError("invalid ReplayBuffer structure-validation flag")
        self.set_rng_state(state["rng_state"])
        self.buffer = deque(copy.deepcopy(rows), maxlen=self.capacity)
        self._total_added = int(state["total_added"])
        self._total_sampled = int(state["total_sampled"])
        self._structure_validated = bool(state["structure_validated"])

    def sample_torch(self, batch_size, device):
        """Sample GNN-HMASD rows whose GAE was frozen before shuffling."""
        sampled_batch = self.sample(batch_size)
        if not sampled_batch:
            return None
        required = {
            "obs",
            "next_obs",
            "action",
            "reward",
            "done",
            "old_log_prob",
            "role",
            "old_value",
            "advantage",
            "return",
            "trajectory_id",
            "timestep",
        }
        if any(not isinstance(row, dict) or not required.issubset(row) for row in sampled_batch):
            raise ValueError(
                "GNN replay rows must be trajectory-finalized dictionaries with frozen GAE"
            )

        def tensor_column(values, *, dtype):
            if torch.is_tensor(values[0]):
                return torch.stack(
                    [value.detach().to(device=device, dtype=dtype) for value in values]
                )
            return torch.as_tensor(np.asarray(values), dtype=dtype, device=device)

        return (
            tensor_column([row["obs"] for row in sampled_batch], dtype=torch.float32),
            tensor_column([row["next_obs"] for row in sampled_batch], dtype=torch.float32),
            tensor_column([row["action"] for row in sampled_batch], dtype=torch.float32),
            tensor_column([row["reward"] for row in sampled_batch], dtype=torch.float32),
            tensor_column([row["done"] for row in sampled_batch], dtype=torch.float32),
            tensor_column([row["old_log_prob"] for row in sampled_batch], dtype=torch.float32),
            tensor_column([row["role"] for row in sampled_batch], dtype=torch.long),
            tensor_column([row["old_value"] for row in sampled_batch], dtype=torch.float32),
            tensor_column([row["advantage"] for row in sampled_batch], dtype=torch.float32),
            tensor_column([row["return"] for row in sampled_batch], dtype=torch.float32),
        )
    
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
    def __init__(
        self,
        num_steps,
        num_envs,
        n_agents,
        obs_dim,
        action_dim,
        gru_hidden_size,
        n_Z,
        n_z,
        state_dim,
        action_space_type='continuous',
        compact_dim=0,
        sampler_seed=0,
        d2_enabled=False,
    ):
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
        self.compact_dim = max(1, int(compact_dim or 0))
        # D2 policy-based interruption (ADR 01).  The per-agent segment table and
        # the team table are allocated only in `d2`; `off` keeps exactly the
        # arrays it had before.
        self.d2_enabled = bool(d2_enabled)
        self._sampler_rng = np.random.default_rng(int(sampler_seed))

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
        self.reward_process = np.zeros_like(self.reward_env)

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
        self.high_level_elapsed_steps = np.ones((self.num_steps, self.num_envs), dtype=np.int32)
        self.high_level_terminal = np.zeros((self.num_steps, self.num_envs), dtype=np.bool_)
        self.high_level_close_reason = np.zeros((self.num_steps, self.num_envs), dtype=np.int64)
        self.compact = np.zeros((self.num_steps, self.num_envs, self.compact_dim), dtype=np.float32)
        self.team_code = np.full((self.num_steps, self.num_envs), -1, dtype=np.int64)
        self.log_prob_team_code = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.entropy_team_code = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.opt_aggregation_entropy = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.active_skill_prev = np.full((self.num_steps, self.num_envs, self.n_agents), -1, dtype=np.int64)
        self.active_skill = np.full((self.num_steps, self.num_envs, self.n_agents), -1, dtype=np.int64)
        self.candidate_skill = np.full((self.num_steps, self.num_envs, self.n_agents), -1, dtype=np.int64)
        self.skill_age_prev = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.int64)
        self.skill_age = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.int64)
        self.duration_candidate = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.int64)
        self.duration_target = np.ones((self.num_steps, self.num_envs, self.n_agents), dtype=np.int64)
        self.duration_remaining = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.int64)
        self.requested_edit_mask = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.executed_edit_mask = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.log_prob_term = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.log_prob_skill = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.log_prob_duration = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.entropy_term = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.entropy_skill = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.entropy_duration = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.initial_assignment_mask = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)

        self.advantages = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.returns = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)

        self.high_level_advantages = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_returns = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_team_advantages = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_agent_advantages = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)
        self.high_level_team_returns = np.zeros((self.num_steps, self.num_envs), dtype=np.float32)
        self.high_level_agent_returns = np.zeros((self.num_steps, self.num_envs, self.n_agents), dtype=np.float32)

        if self.d2_enabled:
            self._reset_d2_tables()

        self._cached_rollout_data = None
        self._profile = {
            "full_rollout_pack": 0.0,
            "full_rollout_pack_calls": 0,
            "full_rollout_cache_hits": 0,
        }

        main_logger.debug("RolloutBuffer已重置，预分配数组已清空。")

    def add(self, t, state, obs, action, reward, done, value, log_prob, gru_hidden_state, critic_gru_hidden_state, env_idx, team_skill=None, agent_skills=None, reward_env=None, reward_team_disc=None, reward_ind_disc=None, reward_process=None):
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
            reward_process_arr = self._agent_vector(
                reward_process if reward_process is not None else np.zeros(self.n_agents, dtype=np.float32),
                np.float32,
                "reward_process",
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
        self.reward_process[t, env_idx] = reward_process_arr
        self._cached_rollout_data = None
        return True

    def add_process_rewards(self, env_idx, agent_idx, step_indices, rewards):
        env_idx = int(env_idx)
        agent_idx = int(agent_idx)
        if env_idx < 0 or env_idx >= self.num_envs or agent_idx < 0 or agent_idx >= self.n_agents:
            main_logger.error(f"add_process_rewards: 索引越界 env={env_idx}, agent={agent_idx}")
            return 0
        step_indices = np.asarray(step_indices, dtype=np.int64).reshape(-1)
        rewards = np.asarray(rewards, dtype=np.float32).reshape(-1)
        if rewards.size == 1 and step_indices.size > 1:
            rewards = np.full(step_indices.size, float(rewards[0]), dtype=np.float32)
        if rewards.size != step_indices.size:
            main_logger.error(
                f"add_process_rewards: rewards长度({rewards.size})与step_indices长度({step_indices.size})不匹配"
            )
            return 0
        applied = 0
        for step, reward in zip(step_indices, rewards):
            step = int(step)
            if step < 0 or step >= self.num_steps:
                continue
            if not self.masks[step, env_idx]:
                continue
            self.rewards[step, env_idx, agent_idx] += float(reward)
            self.reward_process[step, env_idx, agent_idx] += float(reward)
            applied += 1
        if applied > 0:
            self._cached_rollout_data = None
        return applied

    # ------------------------------------------------------------------
    # D2 policy-based interruption tables (ADR 01 revision 3, plan section 6).
    # Allocated and written only when `d2_enabled`.
    # ------------------------------------------------------------------

    def _reset_d2_tables(self):
        T, E, N = self.num_steps, self.num_envs, self.n_agents

        # Per-(step, env) replay metadata of the assignment decided at that step.
        self.d2_decision = np.zeros((T, E), dtype=np.bool_)
        self.d2_sample_Z = np.zeros((T, E), dtype=np.bool_)
        self.d2_sampled_mask = np.zeros((T, E, N), dtype=np.bool_)
        self.d2_order = np.tile(np.arange(N, dtype=np.int64), (T, E, 1))
        self.d2_team_skill = np.full((T, E), -1, dtype=np.int64)
        self.d2_agent_skills = np.full((T, E, N), -1, dtype=np.int64)
        self.d2_team_old_log_prob = np.zeros((T, E), dtype=np.float32)
        self.d2_agent_old_log_probs = np.zeros((T, E, N), dtype=np.float32)
        self.d2_team_value = np.zeros((T, E), dtype=np.float32)
        self.d2_agent_values = np.zeros((T, E, N), dtype=np.float32)
        self.d2_agent_cause = np.zeros((T, E, N), dtype=np.int64)
        self.d2_team_cause = np.zeros((T, E), dtype=np.int64)

        # Ages at the step the transition was collected (plan section 9).
        self.d2_agent_age = np.zeros((T, E, N), dtype=np.int64)
        self.d2_team_age = np.zeros((T, E), dtype=np.int64)

        # Per-agent segment table [T, E, N] and team table [T, E].  A row is
        # written at the segment's start index when the segment closes.
        self.d2_agent_valid = np.zeros((T, E, N), dtype=np.bool_)
        self.d2_agent_reward = np.zeros((T, E, N), dtype=np.float32)
        self.d2_agent_elapsed = np.ones((T, E, N), dtype=np.int32)
        self.d2_agent_terminal = np.zeros((T, E, N), dtype=np.bool_)

        self.d2_team_valid = np.zeros((T, E), dtype=np.bool_)
        self.d2_team_reward = np.zeros((T, E), dtype=np.float32)
        self.d2_team_elapsed = np.ones((T, E), dtype=np.int32)
        self.d2_team_terminal = np.zeros((T, E), dtype=np.bool_)

    def add_d2_step(self, env_idx, time_step, agent_age, team_age, decision=False,
                    team_skill=None, agent_skills=None, sampled_mask=None, sample_Z=False,
                    order=None, team_log_prob=0.0, agent_log_probs=None,
                    team_value=0.0, agent_values=None, agent_cause=None, team_cause=0):
        """Record one D2 step: the per-step ages and, on a decision, the replay metadata."""
        if not self.d2_enabled:
            raise RuntimeError("add_d2_step called on a buffer that is not in d2 mode")
        if env_idx >= self.num_envs or time_step < 0 or time_step >= self.num_steps:
            main_logger.error(
                f"add_d2_step: index out of range env_idx={env_idx}, time_step={time_step}"
            )
            return False
        if not self.masks[time_step, env_idx]:
            main_logger.error(
                f"add_d2_step: low-level data missing at env_idx={env_idx}, time_step={time_step}"
            )
            return False

        self.d2_agent_age[time_step, env_idx] = self._agent_vector(agent_age, np.int64, "d2_agent_age")
        self.d2_team_age[time_step, env_idx] = int(team_age)

        if decision:
            self.d2_decision[time_step, env_idx] = True
            self.d2_sample_Z[time_step, env_idx] = bool(sample_Z)
            self.d2_sampled_mask[time_step, env_idx] = self._agent_vector(
                sampled_mask, np.bool_, "d2_sampled_mask"
            )
            self.d2_order[time_step, env_idx] = self._agent_vector(order, np.int64, "d2_order")
            self.d2_team_skill[time_step, env_idx] = int(team_skill)
            self.d2_agent_skills[time_step, env_idx] = self._agent_vector(
                agent_skills, np.int64, "d2_agent_skills"
            )
            self.d2_team_old_log_prob[time_step, env_idx] = float(team_log_prob)
            self.d2_agent_old_log_probs[time_step, env_idx] = self._agent_vector(
                agent_log_probs, np.float32, "d2_agent_old_log_probs"
            )
            self.d2_team_value[time_step, env_idx] = float(team_value)
            self.d2_agent_values[time_step, env_idx] = self._agent_vector(
                agent_values, np.float32, "d2_agent_values"
            )
            if agent_cause is not None:
                self.d2_agent_cause[time_step, env_idx] = self._agent_vector(
                    agent_cause, np.int64, "d2_agent_cause"
                )
            self.d2_team_cause[time_step, env_idx] = int(team_cause)

        self._cached_rollout_data = None
        return True

    def close_d2_agent_segment(self, env_idx, agent_idx, start_step, reward, elapsed, terminal):
        """Write one closed per-agent segment row at its start index."""
        if not self.d2_enabled:
            raise RuntimeError("close_d2_agent_segment called on a buffer that is not in d2 mode")
        if start_step < 0 or start_step >= self.num_steps or env_idx >= self.num_envs:
            main_logger.error(
                f"close_d2_agent_segment: index out of range env={env_idx}, t={start_step}"
            )
            return False
        self.d2_agent_valid[start_step, env_idx, agent_idx] = True
        self.d2_agent_reward[start_step, env_idx, agent_idx] = float(reward)
        self.d2_agent_elapsed[start_step, env_idx, agent_idx] = max(1, int(elapsed))
        self.d2_agent_terminal[start_step, env_idx, agent_idx] = bool(terminal)
        self.high_level_valid_mask[start_step, env_idx] = True
        self._cached_rollout_data = None
        return True

    def close_d2_team_segment(self, env_idx, start_step, reward, elapsed, terminal):
        """Write one closed team segment row at its start index."""
        if not self.d2_enabled:
            raise RuntimeError("close_d2_team_segment called on a buffer that is not in d2 mode")
        if start_step < 0 or start_step >= self.num_steps or env_idx >= self.num_envs:
            main_logger.error(
                f"close_d2_team_segment: index out of range env={env_idx}, t={start_step}"
            )
            return False
        self.d2_team_valid[start_step, env_idx] = True
        self.d2_team_reward[start_step, env_idx] = float(reward)
        self.d2_team_elapsed[start_step, env_idx] = max(1, int(elapsed))
        self.d2_team_terminal[start_step, env_idx] = bool(terminal)
        self.high_level_valid_mask[start_step, env_idx] = True
        self._cached_rollout_data = None
        return True

    def get_d2_tables(self, num_steps=None):
        """Return views of the D2 tables truncated to `num_steps` (diagnostics/tests)."""
        if not self.d2_enabled:
            return None
        sl = slice(0, self.num_steps if num_steps is None else int(num_steps))
        return {
            'decision': self.d2_decision[sl],
            'sample_Z': self.d2_sample_Z[sl],
            'sampled_mask': self.d2_sampled_mask[sl],
            'order': self.d2_order[sl],
            'team_skill': self.d2_team_skill[sl],
            'agent_skills': self.d2_agent_skills[sl],
            'team_old_log_prob': self.d2_team_old_log_prob[sl],
            'agent_old_log_probs': self.d2_agent_old_log_probs[sl],
            'team_value': self.d2_team_value[sl],
            'agent_values': self.d2_agent_values[sl],
            'agent_cause': self.d2_agent_cause[sl],
            'team_cause': self.d2_team_cause[sl],
            'agent_age': self.d2_agent_age[sl],
            'team_age': self.d2_team_age[sl],
            'agent_valid': self.d2_agent_valid[sl],
            'agent_reward': self.d2_agent_reward[sl],
            'agent_elapsed': self.d2_agent_elapsed[sl],
            'agent_terminal': self.d2_agent_terminal[sl],
            'team_valid': self.d2_team_valid[sl],
            'team_reward': self.d2_team_reward[sl],
            'team_elapsed': self.d2_team_elapsed[sl],
            'team_terminal': self.d2_team_terminal[sl],
            'agent_advantages': self.high_level_agent_advantages[sl],
            'agent_returns': self.high_level_agent_returns[sl],
            'team_advantages': self.high_level_team_advantages[sl],
            'team_returns': self.high_level_team_returns[sl],
        }

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
        elapsed_steps = int(kwargs.get("elapsed_steps", 1) or 1)
        self.high_level_elapsed_steps[time_step, env_idx] = max(1, elapsed_steps)
        self.high_level_terminal[time_step, env_idx] = bool(kwargs.get("terminal", False))
        self.high_level_close_reason[time_step, env_idx] = int(kwargs.get("close_reason_code", 0) or 0)

        compact = kwargs.get("compact")
        if compact is not None:
            compact_arr = np.asarray(compact, dtype=np.float32).reshape(-1)
            if compact_arr.size != self.compact_dim:
                if compact_arr.size > self.compact_dim:
                    compact_arr = compact_arr[:self.compact_dim]
                else:
                    compact_arr = np.pad(compact_arr, (0, self.compact_dim - compact_arr.size))
            self.compact[time_step, env_idx] = compact_arr
        self.team_code[time_step, env_idx] = int(kwargs.get("team_code", -1))
        self.log_prob_team_code[time_step, env_idx] = float(kwargs.get("log_prob_team_code", 0.0))
        self.entropy_team_code[time_step, env_idx] = float(kwargs.get("entropy_team_code", 0.0))
        self.opt_aggregation_entropy[time_step, env_idx] = float(kwargs.get("opt_aggregation_entropy", 0.0))

        agent_int_fields = {
            "active_skill_prev": self.active_skill_prev,
            "active_skill": self.active_skill,
            "candidate_skill": self.candidate_skill,
            "skill_age_prev": self.skill_age_prev,
            "skill_age": self.skill_age,
            "duration_candidate": self.duration_candidate,
            "duration_target": self.duration_target,
            "duration_remaining": self.duration_remaining,
        }
        for key, target in agent_int_fields.items():
            if key in kwargs and kwargs[key] is not None:
                target[time_step, env_idx] = self._agent_vector(kwargs[key], target.dtype, key)

        agent_float_fields = {
            "requested_edit_mask": self.requested_edit_mask,
            "executed_edit_mask": self.executed_edit_mask,
            "log_prob_term": self.log_prob_term,
            "log_prob_skill": self.log_prob_skill,
            "log_prob_duration": self.log_prob_duration,
            "entropy_term": self.entropy_term,
            "entropy_skill": self.entropy_skill,
            "entropy_duration": self.entropy_duration,
            "initial_assignment_mask": self.initial_assignment_mask,
        }
        for key, target in agent_float_fields.items():
            if key in kwargs and kwargs[key] is not None:
                target[time_step, env_idx] = self._agent_vector(kwargs[key], np.float32, key)

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
            "high_level_elapsed_steps": self.high_level_elapsed_steps[sl],
            "high_level_terminal": self.high_level_terminal[sl],
            "high_level_close_reason": self.high_level_close_reason[sl],
            "compact": self.compact[sl],
            "team_code": self.team_code[sl],
            "log_prob_team_code": self.log_prob_team_code[sl],
            "entropy_team_code": self.entropy_team_code[sl],
            "opt_aggregation_entropy": self.opt_aggregation_entropy[sl],
            "active_skill_prev": self.active_skill_prev[sl],
            "active_skill": self.active_skill[sl],
            "candidate_skill": self.candidate_skill[sl],
            "skill_age_prev": self.skill_age_prev[sl],
            "skill_age": self.skill_age[sl],
            "duration_candidate": self.duration_candidate[sl],
            "duration_target": self.duration_target[sl],
            "duration_remaining": self.duration_remaining[sl],
            "requested_edit_mask": self.requested_edit_mask[sl],
            "executed_edit_mask": self.executed_edit_mask[sl],
            "log_prob_term": self.log_prob_term[sl],
            "log_prob_skill": self.log_prob_skill[sl],
            "log_prob_duration": self.log_prob_duration[sl],
            "entropy_term": self.entropy_term[sl],
            "entropy_skill": self.entropy_skill[sl],
            "entropy_duration": self.entropy_duration[sl],
            "initial_assignment_mask": self.initial_assignment_mask[sl],
            "reward_env": self.reward_env[sl],
            "reward_team_disc": self.reward_team_disc[sl],
            "reward_ind_disc": self.reward_ind_disc[sl],
            "reward_process": self.reward_process[sl],
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
                # ``dones_rollout[t]`` belongs to the transition from t to
                # t+1.  Looking at t+1 leaks the first transition of a new
                # episode into the preceding episode's GAE recursion.
                next_non_terminal = 1.0 - dones_rollout[t]
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

        if self.d2_enabled:
            return self._compute_d2_high_level_advantages(
                high_level_last_values,
                gamma=gamma,
                gae_lambda=gae_lambda,
                value_normalizer=value_normalizer,
                num_actual_steps=num_actual_steps,
            )

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
        high_level_elapsed_steps = data.get(
            "high_level_elapsed_steps",
            np.ones_like(high_level_rewards, dtype=np.int32),
        )
        high_level_terminal = data.get(
            "high_level_terminal",
            np.zeros_like(high_level_valid_mask, dtype=np.bool_),
        )

        for env_idx in range(self.num_envs):
            valid_steps = np.flatnonzero(high_level_valid_mask[:num_actual_steps, env_idx])
            if valid_steps.size == 0:
                continue

            rewards_seq = high_level_rewards[valid_steps, env_idx]
            state_values_seq = high_level_state_values[valid_steps, env_idx]
            elapsed_seq = np.maximum(
                high_level_elapsed_steps[valid_steps, env_idx].astype(np.float32),
                1.0,
            )
            discounts_seq = np.power(float(gamma), elapsed_seq).astype(np.float32)
            dones_seq = high_level_terminal[valid_steps, env_idx].astype(np.float32)

            if value_normalizer is not None:
                state_values_seq_real = state_values_seq * std + mean
            else:
                state_values_seq_real = state_values_seq

            next_state_values_seq_real = np.zeros_like(state_values_seq_real)
            if len(valid_steps) > 1:
                next_state_values_seq_real[:-1] = state_values_seq_real[1:]
            next_state_values_seq_real[-1] = last_state_values_real[env_idx]

            team_advantages, team_returns = self._compute_gae_with_discounts_torch(
                rewards_seq,
                state_values_seq_real,
                next_state_values_seq_real,
                dones_seq,
                discounts_seq,
                gae_lambda,
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

                agent_advantages, agent_returns = self._compute_gae_with_discounts_torch(
                    rewards_seq,
                    agent_values_seq_real,
                    next_agent_values_seq_real,
                    dones_seq,
                    discounts_seq,
                    gae_lambda,
                )
                for i, t in enumerate(valid_steps):
                    self.high_level_agent_advantages[t, env_idx, agent_idx] = agent_advantages[i].item()
                    self.high_level_agent_returns[t, env_idx, agent_idx] = agent_returns[i].item()

        main_logger.debug("高层策略GAE计算完成。")

    def _compute_d2_high_level_advantages(self, high_level_last_values, gamma, gae_lambda,
                                          value_normalizer, num_actual_steps):
        """
        D2 SMDP advantages (plan section 7, ADR 01 target formula).

        One discounted-GAE sequence per `(env, agent)` over that agent's valid
        segment rows, and one per env over the team table, both with
        `discounts = gamma ** elapsed`.  The last valid row of each sequence
        bootstraps with the value of the next state, exactly as `off` does via
        `high_level_last_values`.
        """
        if isinstance(high_level_last_values, dict):
            last_state_values = np.asarray(
                high_level_last_values.get('state', np.zeros(self.num_envs))
            )
            last_agent_values = np.asarray(
                high_level_last_values.get('agents', np.zeros((self.num_envs, self.n_agents)))
            )
        else:
            last_state_values = np.asarray(high_level_last_values)
            if last_state_values.ndim == 2:
                last_agent_values = last_state_values
                last_state_values = last_state_values[:, 0]
            else:
                last_agent_values = np.tile(
                    last_state_values[:, np.newaxis], (1, self.n_agents)
                )

        if value_normalizer is not None:
            mean = value_normalizer.mean
            std = np.sqrt(value_normalizer.var + 1e-8)
        else:
            mean, std = 0.0, 1.0

        last_state_values_real = last_state_values * std + mean
        last_agent_values_real = last_agent_values * std + mean

        def _sequence(rewards, values, elapsed, terminal, last_value):
            values_real = values.astype(np.float32) * std + mean
            next_values = np.zeros_like(values_real)
            if values_real.size > 1:
                next_values[:-1] = values_real[1:]
            next_values[-1] = last_value
            discounts = np.power(
                float(gamma), np.maximum(elapsed.astype(np.float32), 1.0)
            ).astype(np.float32)
            return self._compute_gae_with_discounts_torch(
                rewards.astype(np.float32),
                values_real,
                next_values,
                terminal.astype(np.float32),
                discounts,
                gae_lambda,
            )

        for env_idx in range(self.num_envs):
            team_rows = np.flatnonzero(self.d2_team_valid[:num_actual_steps, env_idx])
            if team_rows.size > 0:
                advantages, returns = _sequence(
                    self.d2_team_reward[team_rows, env_idx],
                    self.d2_team_value[team_rows, env_idx],
                    self.d2_team_elapsed[team_rows, env_idx],
                    self.d2_team_terminal[team_rows, env_idx],
                    last_state_values_real[env_idx],
                )
                for i, t in enumerate(team_rows):
                    self.high_level_team_advantages[t, env_idx] = advantages[i].item()
                    self.high_level_team_returns[t, env_idx] = returns[i].item()
                    self.high_level_advantages[t, env_idx] = advantages[i].item()
                    self.high_level_returns[t, env_idx] = returns[i].item()

            for agent_idx in range(self.n_agents):
                agent_rows = np.flatnonzero(
                    self.d2_agent_valid[:num_actual_steps, env_idx, agent_idx]
                )
                if agent_rows.size == 0:
                    continue
                advantages, returns = _sequence(
                    self.d2_agent_reward[agent_rows, env_idx, agent_idx],
                    self.d2_agent_values[agent_rows, env_idx, agent_idx],
                    self.d2_agent_elapsed[agent_rows, env_idx, agent_idx],
                    self.d2_agent_terminal[agent_rows, env_idx, agent_idx],
                    last_agent_values_real[env_idx, agent_idx],
                )
                for i, t in enumerate(agent_rows):
                    self.high_level_agent_advantages[t, env_idx, agent_idx] = advantages[i].item()
                    self.high_level_agent_returns[t, env_idx, agent_idx] = returns[i].item()

        main_logger.debug("D2 高层策略GAE计算完成。")

    def _compute_gae_torch(self, rewards, values, next_values, dones, gamma, lam):
        rewards = torch.tensor(rewards, dtype=torch.float32)
        values = torch.tensor(values, dtype=torch.float32)
        next_values = torch.tensor(next_values, dtype=torch.float32)
        dones = torch.tensor(dones, dtype=torch.float32)
        return compute_gae(rewards, values, next_values, dones, gamma, lam)

    def _compute_gae_with_discounts_torch(self, rewards, values, next_values, dones, discounts, lam):
        rewards = torch.tensor(rewards, dtype=torch.float32)
        values = torch.tensor(values, dtype=torch.float32)
        next_values = torch.tensor(next_values, dtype=torch.float32)
        dones = torch.tensor(dones, dtype=torch.float32)
        discounts = torch.tensor(discounts, dtype=torch.float32)

        advantages = torch.zeros_like(rewards)
        last_gae = torch.tensor(0.0, dtype=torch.float32)
        for t in reversed(range(len(rewards))):
            non_terminal = 1.0 - dones[t]
            effective_discount = discounts[t] * non_terminal
            delta = rewards[t] + effective_discount * next_values[t] - values[t]
            last_gae = delta + effective_discount * lam * last_gae
            advantages[t] = last_gae
        returns = advantages + values
        return advantages, returns

    def get_all_high_level_returns(self, num_steps):
        """获取所有有效的高层回报，用于更新Value Normalization"""
        data = self._get_full_rollout_data()
        if data is None:
            return np.array([])
        
        if self.d2_enabled:
            # D2 heads have their own valid masks: the team row and the agent
            # rows of one (t, e) pair do not have to be valid together.
            team_mask = self.d2_team_valid[:num_steps]
            agent_mask = self.d2_agent_valid[:num_steps]
            team_returns = self.high_level_team_returns[:num_steps][team_mask]
            agent_returns = self.high_level_agent_returns[:num_steps][agent_mask]
            return np.concatenate([team_returns.flatten(), agent_returns.flatten()])

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

        def flatten_and_chunk_joint_observations(arr):
            T, E, A, O = arr.shape
            arr = arr[:effective_steps]
            arr = np.expand_dims(arr, axis=2)
            arr = np.repeat(arr, self.n_agents, axis=2)
            arr = arr.reshape(num_chunks, actual_chunk_length, E, self.n_agents, A, O)
            arr = arr.transpose(1, 0, 2, 3, 4, 5)
            return arr.reshape(actual_chunk_length, num_chunks * E * self.n_agents, A, O)

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
        joint_observations_flat = flatten_and_chunk_joint_observations(data["obs"])
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
                'joint_observations': torch.as_tensor(joint_observations_flat, dtype=torch.float32, device=device),
                'team_skills': torch.as_tensor(team_skills_flat, dtype=torch.long, device=device),
                'agent_skills': torch.as_tensor(agent_skills_flat, dtype=torch.long, device=device),
                'initial_hxs': torch.as_tensor(initial_hxs_flat, dtype=torch.float32, device=device),
                'initial_critic_hxs': torch.as_tensor(initial_critic_hxs_flat, dtype=torch.float32, device=device),
                'dones': torch.as_tensor(dones_flat, dtype=torch.float32, device=device),
                'masks': torch.as_tensor(masks_flat, dtype=torch.bool, device=device),
            }
        
        for epoch in range(ppo_epochs):
            self._sampler_rng.shuffle(sequence_indices)
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
                        'joint_observations': tensor_cache['joint_observations'][:, batch_tensor],
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
                        'joint_observations': torch.from_numpy(joint_observations_flat[:, batch_indices]).float(),
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
                'high_level_elapsed_steps': torch.as_tensor(data["high_level_elapsed_steps"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'high_level_terminal': torch.as_tensor(data["high_level_terminal"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'high_level_close_reason': torch.as_tensor(data["high_level_close_reason"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'compact': torch.as_tensor(data["compact"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'team_code': torch.as_tensor(data["team_code"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'log_prob_team_code': torch.as_tensor(data["log_prob_team_code"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'entropy_team_code': torch.as_tensor(data["entropy_team_code"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'opt_aggregation_entropy': torch.as_tensor(data["opt_aggregation_entropy"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'active_skill_prev': torch.as_tensor(data["active_skill_prev"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'active_skill': torch.as_tensor(data["active_skill"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'candidate_skill': torch.as_tensor(data["candidate_skill"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'skill_age_prev': torch.as_tensor(data["skill_age_prev"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'skill_age': torch.as_tensor(data["skill_age"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'duration_candidate': torch.as_tensor(data["duration_candidate"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'duration_target': torch.as_tensor(data["duration_target"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'duration_remaining': torch.as_tensor(data["duration_remaining"][valid_time_steps, valid_env_indices], dtype=torch.long, device=device),
                'requested_edit_mask': torch.as_tensor(data["requested_edit_mask"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'executed_edit_mask': torch.as_tensor(data["executed_edit_mask"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'log_prob_term': torch.as_tensor(data["log_prob_term"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'log_prob_skill': torch.as_tensor(data["log_prob_skill"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'log_prob_duration': torch.as_tensor(data["log_prob_duration"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'entropy_term': torch.as_tensor(data["entropy_term"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'entropy_skill': torch.as_tensor(data["entropy_skill"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'entropy_duration': torch.as_tensor(data["entropy_duration"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'initial_assignment_mask': torch.as_tensor(data["initial_assignment_mask"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'team_advantages': torch.as_tensor(self.high_level_team_advantages[valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'agent_advantages': torch.as_tensor(self.high_level_agent_advantages[valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'team_returns': torch.as_tensor(self.high_level_team_returns[valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'agent_returns': torch.as_tensor(self.high_level_agent_returns[valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
                'values': torch.as_tensor(data["high_level_state_values"][valid_time_steps, valid_env_indices], dtype=torch.float32, device=device),
            }
        
        for epoch in range(ppo_epochs):
            self._sampler_rng.shuffle(valid_indices)
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
                        'high_level_elapsed_steps': torch.from_numpy(data["high_level_elapsed_steps"][time_batch, env_batch]).float(),
                        'high_level_terminal': torch.from_numpy(data["high_level_terminal"][time_batch, env_batch]).float(),
                        'high_level_close_reason': torch.from_numpy(data["high_level_close_reason"][time_batch, env_batch]).long(),
                        'compact': torch.from_numpy(data["compact"][time_batch, env_batch]).float(),
                        'team_code': torch.from_numpy(data["team_code"][time_batch, env_batch]).long(),
                        'log_prob_team_code': torch.from_numpy(data["log_prob_team_code"][time_batch, env_batch]).float(),
                        'entropy_team_code': torch.from_numpy(data["entropy_team_code"][time_batch, env_batch]).float(),
                        'opt_aggregation_entropy': torch.from_numpy(data["opt_aggregation_entropy"][time_batch, env_batch]).float(),
                        'active_skill_prev': torch.from_numpy(data["active_skill_prev"][time_batch, env_batch]).long(),
                        'active_skill': torch.from_numpy(data["active_skill"][time_batch, env_batch]).long(),
                        'candidate_skill': torch.from_numpy(data["candidate_skill"][time_batch, env_batch]).long(),
                        'skill_age_prev': torch.from_numpy(data["skill_age_prev"][time_batch, env_batch]).long(),
                        'skill_age': torch.from_numpy(data["skill_age"][time_batch, env_batch]).long(),
                        'duration_candidate': torch.from_numpy(data["duration_candidate"][time_batch, env_batch]).long(),
                        'duration_target': torch.from_numpy(data["duration_target"][time_batch, env_batch]).long(),
                        'duration_remaining': torch.from_numpy(data["duration_remaining"][time_batch, env_batch]).long(),
                        'requested_edit_mask': torch.from_numpy(data["requested_edit_mask"][time_batch, env_batch]).float(),
                        'executed_edit_mask': torch.from_numpy(data["executed_edit_mask"][time_batch, env_batch]).float(),
                        'log_prob_term': torch.from_numpy(data["log_prob_term"][time_batch, env_batch]).float(),
                        'log_prob_skill': torch.from_numpy(data["log_prob_skill"][time_batch, env_batch]).float(),
                        'log_prob_duration': torch.from_numpy(data["log_prob_duration"][time_batch, env_batch]).float(),
                        'entropy_term': torch.from_numpy(data["entropy_term"][time_batch, env_batch]).float(),
                        'entropy_skill': torch.from_numpy(data["entropy_skill"][time_batch, env_batch]).float(),
                        'entropy_duration': torch.from_numpy(data["entropy_duration"][time_batch, env_batch]).float(),
                        'initial_assignment_mask': torch.from_numpy(data["initial_assignment_mask"][time_batch, env_batch]).float(),
                        'team_advantages': torch.from_numpy(self.high_level_team_advantages[time_batch, env_batch]).float(),
                        'agent_advantages': torch.from_numpy(self.high_level_agent_advantages[time_batch, env_batch]).float(),
                        'team_returns': torch.from_numpy(self.high_level_team_returns[time_batch, env_batch]).float(),
                        'agent_returns': torch.from_numpy(self.high_level_agent_returns[time_batch, env_batch]).float(),
                        'values': torch.from_numpy(data["high_level_state_values"][time_batch, env_batch]).float(),
                    }

    def get_sampler_rng_state(self):
        """Return an isolated, checkpoint-safe snapshot of sampler RNG state."""
        return copy.deepcopy(self._sampler_rng.bit_generator.state)

    def set_sampler_rng_state(self, state):
        """Restore sampler RNG state, failing closed on incompatible state."""
        if not isinstance(state, dict):
            raise TypeError("sampler RNG state must be a bit-generator state dictionary")
        restored = np.random.default_rng()
        restored.bit_generator.state = copy.deepcopy(state)
        self._sampler_rng = restored

class SkillProcessSegmentBuffer:
    """Tracks variable-duration executed skill process segments.

    This buffer is intentionally diagnostic/data-contract only. It does not
    alter rewards; process rewards should be added only after segment closure
    and labeling are verified.
    """

    def __init__(self, capacity=20000, max_segment_len=250, outcome_extractor=None):
        self.capacity = int(capacity)
        self.max_segment_len = int(max_segment_len)
        self.active = {}
        self.completed = deque(maxlen=self.capacity)
        self.outcome_extractor = outcome_extractor

    def reset(self):
        self.active.clear()
        self.completed.clear()

    def _key(self, env_id, agent_id):
        return int(env_id), int(agent_id)

    def open_segment(self, env_id, agent_id, skill, team_code, compact=None,
                     start_step=0, duration_target=0):
        key = self._key(env_id, agent_id)
        if key in self.active:
            self.close_segment(env_id, agent_id, reason="reopen", end_step=start_step)
        compact_arr = None if compact is None else np.asarray(compact, dtype=np.float32).copy()
        self.active[key] = {
            "env_id": int(env_id),
            "agent_id": int(agent_id),
            "skill": int(skill),
            "team_code": int(team_code),
            "compact": compact_arr,
            "start_step": int(start_step),
            "end_step": int(start_step),
            "duration_target": int(duration_target),
            "obs_seq": [],
            "next_obs_seq": [],
            "action_seq": [],
            "reward_seq": [],
            "done_seq": [],
            "reward_info_seq": [],
            "step_seq": [],
            "close_reason": None,
        }

    def append_transition(self, env_id, agent_id, obs, action, reward, done,
                          next_obs=None, step=None, reward_info=None):
        key = self._key(env_id, agent_id)
        segment = self.active.get(key)
        if segment is None:
            return False
        if len(segment["reward_seq"]) >= self.max_segment_len:
            self.close_segment(env_id, agent_id, reason="max_len", end_step=step)
            return False
        segment["obs_seq"].append(np.asarray(obs, dtype=np.float32).copy())
        segment["next_obs_seq"].append(
            np.asarray(next_obs if next_obs is not None else obs, dtype=np.float32).copy()
        )
        segment["action_seq"].append(np.asarray(action).copy())
        segment["reward_seq"].append(float(reward))
        segment["done_seq"].append(bool(done))
        segment["reward_info_seq"].append(dict(reward_info) if isinstance(reward_info, dict) else {})
        if step is not None:
            segment["step_seq"].append(int(step))
            segment["end_step"] = int(step)
        return True

    def close_segment(self, env_id, agent_id, reason="closed", end_step=None):
        key = self._key(env_id, agent_id)
        segment = self.active.pop(key, None)
        if segment is None:
            return None
        if end_step is not None:
            segment["end_step"] = int(end_step)
        segment["close_reason"] = str(reason)
        segment["length"] = len(segment["reward_seq"])
        segment["return"] = float(np.sum(segment["reward_seq"])) if segment["reward_seq"] else 0.0
        if self.outcome_extractor is not None:
            segment.update(self.outcome_extractor.transform_segment(segment, update=True))
        self.completed.append(segment)
        return segment

    def close_env_segments(self, env_id, reason="env_done", end_step=None):
        closed = []
        keys = [key for key in self.active if key[0] == int(env_id)]
        for _, agent_id in keys:
            segment = self.close_segment(env_id, agent_id, reason=reason, end_step=end_step)
            if segment is not None:
                closed.append(segment)
        return closed

    def get_completed_segments(self):
        return list(self.completed)

    def stats(self):
        completed = list(self.completed)
        lengths = np.asarray([seg.get("length", 0) for seg in completed], dtype=np.float32)
        returns = np.asarray([seg.get("return", 0.0) for seg in completed], dtype=np.float32)
        durations = {}
        for seg in completed:
            target = int(seg.get("duration_target", 0))
            durations[target] = durations.get(target, 0) + 1
        stats = {
            "process_segments_open": len(self.active),
            "process_segments_completed": len(completed),
            "process_segment_length_mean": float(lengths.mean()) if lengths.size else 0.0,
            "process_segment_length_max": float(lengths.max()) if lengths.size else 0.0,
            "process_segment_return_mean": float(returns.mean()) if returns.size else 0.0,
            "process_duration_target_histogram": durations,
        }
        if self.outcome_extractor is not None:
            field_names = self.outcome_extractor.FIELD_NAMES
            masks = [
                np.asarray(seg.get("outcome_mask"), dtype=np.bool_)
                for seg in completed
                if "outcome_mask" in seg
            ]
            normalized = [
                np.asarray(seg.get("outcome_normalized"), dtype=np.float32)
                for seg in completed
                if "outcome_normalized" in seg
            ]
            if masks:
                mask_arr = np.stack(masks, axis=0)
                availability = mask_arr.mean(axis=0)
                stats["process_outcome_available_rate"] = float(mask_arr.mean())
                stats["process_outcome_field_availability"] = {
                    field_names[idx]: float(availability[idx])
                    for idx in range(len(field_names))
                }
            else:
                stats["process_outcome_available_rate"] = 0.0
                stats["process_outcome_field_availability"] = {
                    field: 0.0 for field in field_names
                }
            if normalized:
                norm_arr = np.stack(normalized, axis=0)
                stats["process_outcome_norm_mean_abs"] = float(np.mean(np.abs(norm_arr)))
                stats["process_outcome_norm_max_abs"] = float(np.max(np.abs(norm_arr)))
            else:
                stats["process_outcome_norm_mean_abs"] = 0.0
                stats["process_outcome_norm_max_abs"] = 0.0
        return stats


class DiscriminatorBuffer:
    """
    判别器当前rollout缓存。

    该缓存只保存当前策略版本采集到的状态-技能对，并在每次
    policy/discriminator update 后清空；不要把它当作跨update复用的
    off-policy replay buffer。
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
        main_logger.info(f"初始化On-Policy判别器Rollout缓存，最大容量: {capacity}")

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


def compute_ordered_trajectory_gae(
    rewards,
    values,
    next_values,
    dones,
    trajectory_ids,
    timesteps,
    gamma,
    lam,
):
    """Freeze GAE for one continuous, explicitly indexed trajectory segment."""
    if not all(torch.is_tensor(item) for item in (rewards, values, next_values, dones)):
        raise TypeError("trajectory GAE inputs must be torch tensors")
    if not (rewards.shape == values.shape == next_values.shape == dones.shape):
        raise ValueError(
            "trajectory GAE inputs must have identical shapes: "
            f"rewards={tuple(rewards.shape)}, values={tuple(values.shape)}, "
            f"next_values={tuple(next_values.shape)}, dones={tuple(dones.shape)}"
        )
    if rewards.ndim != 1 or rewards.numel() == 0:
        raise ValueError("trajectory GAE requires a non-empty one-dimensional segment")
    if len(trajectory_ids) != rewards.numel() or len(timesteps) != rewards.numel():
        raise ValueError("trajectory metadata length must match tensor length")
    if len(set(trajectory_ids)) != 1:
        raise ValueError("trajectory GAE segment contains multiple trajectory IDs")
    integer_timesteps = [int(timestep) for timestep in timesteps]
    if any(value != timestep for value, timestep in zip(integer_timesteps, timesteps)):
        raise ValueError("trajectory timesteps must be integers")
    expected = list(range(integer_timesteps[0], integer_timesteps[0] + rewards.numel()))
    if integer_timesteps != expected:
        raise ValueError(
            f"trajectory timesteps must be contiguous and ordered: got {integer_timesteps}"
        )
    if bool(torch.any(dones[:-1].to(torch.bool)).item()):
        raise ValueError("a terminal transition may only appear at the end of a segment")
    for name, tensor in (
        ("rewards", rewards),
        ("values", values),
        ("next_values", next_values),
        ("dones", dones),
    ):
        if not bool(torch.all(torch.isfinite(tensor)).item()):
            raise ValueError(f"trajectory GAE {name} must be finite")
    if not bool(torch.all((dones == 0) | (dones == 1)).item()):
        raise ValueError("trajectory GAE dones must contain only zero or one")
    if not np.isfinite(float(gamma)) or not np.isfinite(float(lam)):
        raise ValueError("trajectory GAE gamma and lambda must be finite")

    dones = dones.to(rewards.dtype)
    advantages = torch.zeros_like(rewards)
    last_advantage = torch.zeros((), dtype=rewards.dtype, device=rewards.device)
    for index in reversed(range(rewards.numel())):
        non_terminal = 1.0 - dones[index]
        delta = (
            rewards[index]
            + float(gamma) * non_terminal * next_values[index]
            - values[index]
        )
        last_advantage = (
            delta
            + float(gamma) * float(lam) * non_terminal * last_advantage
        )
        advantages[index] = last_advantage
    return advantages, advantages + values

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
