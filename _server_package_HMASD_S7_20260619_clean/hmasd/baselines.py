import os
from typing import Tuple

import numpy as np
import torch

from logger import main_logger
from hmasd.agent import HMASDAgent


ALGORITHM_CHOICES = ("hmasd", "mappo", "random", "greedy_coverage")


def apply_algorithm_config(config, algorithm: str):
    """Apply algorithm-level switches while keeping the same env and logging path."""
    algorithm = (algorithm or "hmasd").lower()
    config.algorithm = algorithm
    config.baseline_algorithm = algorithm

    if algorithm == "hmasd":
        return config

    if algorithm == "mappo":
        # Flat MAPPO baseline: shared low-level actor, centralized critic, no skill discovery
        # reward or high-level coordinator learning. Skills are fixed to a single constant.
        config.n_Z = 1
        config.n_z = 1
        config.k = max(int(getattr(config, "rollout_length", 1)) + 1, 2)
        config.lambda_D = 0.0
        config.lambda_d = 0.0
        config.lambda_h = 0.0
        config.lambda_cd = 0.0
        config.lambda_mi = 0.0
        config.use_entropy_annealing = False
        config.disable_high_level_training = True
        config.disable_discriminator_training = True
        config.disable_discriminator_rewards = True
        config.collects_high_level_samples = False
        if hasattr(config, "calculate_and_set_buffer_sizes"):
            config.calculate_and_set_buffer_sizes()
        return config

    if algorithm in {"random", "greedy_coverage"}:
        config.disable_learning_updates = True
        config.collects_high_level_samples = False
        config.disable_high_level_training = True
        config.disable_discriminator_training = True
        config.disable_discriminator_rewards = True
        return config

    raise ValueError(f"Unsupported algorithm: {algorithm}")


def create_agent(config, algorithm: str, log_dir: str, device=None):
    algorithm = (algorithm or getattr(config, "algorithm", "hmasd")).lower()
    if algorithm in {"hmasd", "mappo"}:
        return HMASDAgent(config, log_dir=log_dir, device=device)
    if algorithm in {"random", "greedy_coverage"}:
        return HeuristicBaselineAgent(config, algorithm=algorithm, log_dir=log_dir, device=device)
    raise ValueError(f"Unsupported algorithm: {algorithm}")


class HeuristicBaselineAgent:
    """Non-learning baselines with the same surface used by the training loop."""

    uses_learned_value_function = False
    collects_high_level_samples = False

    def __init__(self, config, algorithm="random", log_dir="logs", device=None):
        self.config = config
        self.algorithm = algorithm
        self.log_dir = log_dir
        self.device = device if device is not None else torch.device("cpu")
        self.global_step = 0
        self.num_timesteps = 0
        self.training = True
        self.best_eval_reward = -np.inf

        os.makedirs(log_dir, exist_ok=True)

        self.env_timers = {}
        self.env_team_skills = {}
        self.env_agent_skills = {}
        self.env_log_probs = {}
        self.env_reward_sums = {}
        self.force_high_level_collection = {}
        self.high_level_samples_total = 0
        self.high_level_samples_by_env = {}
        self.high_level_samples_by_reason = {}

        self.training_info = {
            "episode_rewards": [],
            "high_level_loss": [],
            "low_level_loss": [],
            "discriminator_loss": [],
            "team_skill_entropy": [],
            "agent_skill_entropy": [],
            "action_entropy": [],
            "intrinsic_reward_low_level_average": [],
            "intrinsic_reward_env_component": [],
            "intrinsic_reward_team_disc_component": [],
            "intrinsic_reward_ind_disc_component": [],
            "coordinator_state_value_mean": [],
            "coordinator_agent_value_mean": [],
            "discoverer_value_mean": [],
        }

        main_logger.info(f"已创建非学习基线Agent: {algorithm}")

    def train(self, mode=True):
        self.training = mode

    def eval(self):
        self.train(False)

    def step(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False):
        states_batch = np.asarray(states_batch)
        num_envs = states_batch.shape[0]
        actions = []
        infos = []

        for env_id in range(num_envs):
            self.env_timers[env_id] = int(env_steps_batch[env_id])
            team_skill = 0
            agent_skills = np.zeros(self.config.n_agents, dtype=np.int64)
            self.env_team_skills[env_id] = team_skill
            self.env_agent_skills[env_id] = agent_skills

            if self.algorithm == "random":
                env_actions = self._random_actions()
            else:
                env_actions = self._greedy_coverage_actions(states_batch[env_id])

            actions.append(env_actions)
            infos.append({
                "team_skill": team_skill,
                "agent_skills": agent_skills,
                "action_logprobs": np.zeros(self.config.n_agents, dtype=np.float32),
                "values": np.zeros(self.config.n_agents, dtype=np.float32),
                "skill_changed": True,
                "skill_timer": self.env_timers[env_id],
                "log_probs": {
                    "team_log_prob": 0.0,
                    "agent_log_probs": [0.0] * self.config.n_agents,
                    "state_value": 0.0,
                    "agent_values": [0.0] * self.config.n_agents,
                },
                "env_id": env_id,
            })

        return np.asarray(actions), infos

    def _random_actions(self):
        if getattr(self.config, "action_space_type", "continuous") == "discrete":
            return np.random.randint(0, int(self.config.action_dim), size=self.config.n_agents, dtype=np.int64)
        bound = float(getattr(self.config, "baseline_action_bound", 1.0))
        return np.random.uniform(-bound, bound, size=(self.config.n_agents, self.config.action_dim)).astype(np.float32)

    def _greedy_coverage_actions(self, state):
        uav_pos, user_info = self._parse_state(state)
        if user_info.size == 0:
            return np.zeros(self.config.n_agents, dtype=np.int64) if self._is_discrete() else np.zeros((self.config.n_agents, self.config.action_dim), dtype=np.float32)

        user_xy = user_info[:, :2]
        connected = user_info[:, 4] if user_info.shape[1] > 4 else np.zeros(user_info.shape[0])
        candidate_indices = np.where(connected < 0.5)[0]
        if candidate_indices.size == 0:
            candidate_indices = np.arange(user_xy.shape[0])

        actions = []
        for i in range(self.config.n_agents):
            own_xy = uav_pos[i, :2]
            candidates = user_xy[candidate_indices]
            nearest = candidate_indices[np.argmin(np.linalg.norm(candidates - own_xy, axis=1))]
            target = np.array([user_xy[nearest, 0], user_xy[nearest, 1], 0.5], dtype=np.float32)
            direction = target - uav_pos[i]
            actions.append(self._direction_to_action(direction))

        return np.asarray(actions, dtype=np.int64 if self._is_discrete() else np.float32)

    def _parse_state(self, state) -> Tuple[np.ndarray, np.ndarray]:
        state = np.asarray(state, dtype=np.float32).flatten()
        n_agents = int(self.config.n_agents)
        n_users = int(getattr(self.config, "n_users", 0))

        uav_end = n_agents * 3
        load_end = uav_end + n_agents
        user_end = load_end + n_users * 6
        if state.size < user_end:
            return np.zeros((n_agents, 3), dtype=np.float32), np.zeros((0, 6), dtype=np.float32)

        uav_pos = state[:uav_end].reshape(n_agents, 3)
        user_info = state[load_end:user_end].reshape(n_users, 6)
        return uav_pos, user_info

    def _direction_to_action(self, direction):
        direction = np.asarray(direction, dtype=np.float32)
        norm = np.linalg.norm(direction)
        if norm < 1e-6:
            return 0 if self._is_discrete() else np.zeros(self.config.action_dim, dtype=np.float32)

        if not self._is_discrete():
            unit = direction / norm
            action_dim = int(self.config.action_dim)
            if action_dim <= 3:
                return unit[:action_dim].astype(np.float32)
            padded = np.zeros(action_dim, dtype=np.float32)
            padded[:3] = unit[:3]
            return padded

        horizontal = direction[:2]
        if abs(direction[2]) > max(np.linalg.norm(horizontal), 1e-6):
            return 9 if direction[2] > 0 and self.config.action_dim > 9 else 10 if self.config.action_dim > 10 else 0

        base_dirs = np.asarray([
            [1.0, 0.0],
            [-1.0, 0.0],
            [0.0, 1.0],
            [0.0, -1.0],
            [1.0, 1.0],
            [1.0, -1.0],
            [-1.0, 1.0],
            [-1.0, -1.0],
        ], dtype=np.float32)
        base_dirs[4:] /= np.sqrt(2.0)
        h_norm = np.linalg.norm(horizontal)
        if h_norm < 1e-6:
            return 0
        scores = base_dirs @ (horizontal / h_norm)
        action_id = int(np.argmax(scores)) + 1
        return min(action_id, int(self.config.action_dim) - 1)

    def _is_discrete(self):
        return getattr(self.config, "action_space_type", "continuous") == "discrete"

    def assign_skills(self, state, observations, deterministic=False):
        return 0, np.zeros(self.config.n_agents, dtype=np.int64), {
            "team_log_prob": 0.0,
            "agent_log_probs": [0.0] * self.config.n_agents,
            "state_value": 0.0,
            "agent_values": [0.0] * self.config.n_agents,
        }

    def reset_env_state(self, env_id):
        self.env_timers.pop(env_id, None)
        self.env_team_skills.pop(env_id, None)
        self.env_agent_skills.pop(env_id, None)
        self.env_log_probs.pop(env_id, None)
        self.env_reward_sums.pop(env_id, None)

    def store_transition_batch(self, *args, **kwargs):
        return []

    def apply_reward_weighting(self, env_indices, weight):
        return None

    def update(self, *args, **kwargs):
        self.global_step += 1
        return zero_update_info()

    def clear_buffers(self):
        return None

    def save_model(self, path):
        torch.save({"algorithm": self.algorithm, "config": self.config}, path)
        main_logger.info(f"基线配置已保存到 {path}")

    def load_model(self, path):
        if os.path.exists(path):
            main_logger.info(f"非学习基线无需加载参数，已忽略模型文件: {path}")
        else:
            main_logger.info(f"非学习基线无需模型文件: {path}")


def zero_update_info():
    return {
        "discriminator_loss": 0.0,
        "coordinator_loss": 0.0,
        "coordinator_policy_loss": 0.0,
        "coordinator_value_loss": 0.0,
        "discoverer_loss": 0.0,
        "discoverer_policy_loss": 0.0,
        "discoverer_value_loss": 0.0,
        "team_skill_entropy": 0.0,
        "agent_skill_entropy": 0.0,
        "action_entropy": 0.0,
        "avg_intrinsic_reward": 0.0,
        "avg_env_comp": 0.0,
        "avg_team_disc_comp": 0.0,
        "avg_ind_disc_comp": 0.0,
        "mean_coord_state_val": 0.0,
        "mean_coord_agent_val": 0.0,
        "avg_discoverer_val": 0.0,
        "mean_high_level_reward": 0.0,
        "cd_loss": 0.0,
    }
