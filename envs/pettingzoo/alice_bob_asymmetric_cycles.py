"""Alice--Bob surrogate with deliberately asymmetric task time scales.

The geometry keeps the original button/diamond complementarity, while the
task clock makes one agent hold a button across several high-level checks and
the other visit a different target at every check.  Role assignment is visible
only in the centralized state; the low actor must receive it through its skill.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np
from pettingzoo.utils.env import ParallelEnv


class AliceBobAsymmetricCyclesEnv(ParallelEnv):
    metadata = {"name": "alice_bob_asymmetric_cycles_v0", "render_modes": []}

    def __init__(self, config=None, render_mode=None, seed=None):
        super().__init__()
        self.render_mode = render_mode
        self.world_size = float(getattr(config, "alice_bob_world_size", 8.0))
        self.short_period = int(getattr(config, "alice_bob_short_period", 10))
        self.long_periods = int(getattr(config, "alice_bob_long_periods", 4))
        self.num_short_periods = int(
            getattr(config, "alice_bob_num_short_periods", 8)
        )
        self.action_scale = float(getattr(config, "alice_bob_action_scale", 0.75))
        self.contact_radius = float(
            getattr(config, "alice_bob_contact_radius", 0.70)
        )
        self.progress_reward_coef = float(
            getattr(config, "alice_bob_progress_reward_coef", 0.20)
        )
        if self.short_period <= 0 or self.long_periods <= 0:
            raise ValueError("Alice--Bob periods must be positive")
        if self.num_short_periods < 2 * self.long_periods:
            raise ValueError(
                "Alice--Bob episode must contain at least two long-role phases"
            )

        self.long_period = self.short_period * self.long_periods
        self.max_steps = self.short_period * self.num_short_periods
        self.possible_agents = ["alice", "bob"]
        self.agents = self.possible_agents.copy()
        self.agent_ids = {name: idx for idx, name in enumerate(self.possible_agents)}

        self.button_pos = np.asarray(
            [[1.0, self.world_size - 1.0], [self.world_size - 1.0, self.world_size - 1.0]],
            dtype=np.float32,
        )
        self.target_pos = np.asarray(
            [[1.0, 1.0], [self.world_size - 1.0, 1.0]], dtype=np.float32
        )
        self._action_spaces = {
            agent: gym.spaces.Box(-1.0, 1.0, shape=(2,), dtype=np.float32)
            for agent in self.possible_agents
        }
        # own position (2), other relative position (2), two button offsets (4),
        # two target offsets (4).  Active role/side is intentionally omitted.
        self._observation_spaces = {
            agent: gym.spaces.Box(-1.0, 1.0, shape=(12,), dtype=np.float32)
            for agent in self.possible_agents
        }
        self.np_random = np.random.default_rng(seed)

    def action_space(self, agent):
        return self._action_spaces[agent]

    def observation_space(self, agent):
        return self._observation_spaces[agent]

    def get_obs_dim(self) -> int:
        return 12

    def get_state_dim(self) -> int:
        # positions (4), holder/plate/target one-hot (6), two clock phases (2),
        # current-window collected and holder-contact flags (2).
        return 14

    def reset(self, seed=None, options=None):
        del options
        if seed is not None:
            self.np_random = np.random.default_rng(seed)
        self.agents = self.possible_agents.copy()
        self.steps = 0
        self.agent_pos = self._sample_initial_positions()
        self.active_holder = int(self.np_random.integers(0, 2))
        self.active_plate = int(self.np_random.integers(0, 2))
        self.active_target = int(self.np_random.integers(0, 2))
        self.window_target_collected = False
        self.targets_completed = 0
        self.windows_completed = 0
        self.holder_contact_steps = 0
        self.runner_target_steps = 0
        self.role_switch_count = 0
        observations = self._get_obs()
        infos = self._get_infos(
            step_reward=0.0,
            collection_event=False,
            progress_reward=0.0,
        )
        return observations, infos

    def _sample_initial_positions(self) -> np.ndarray:
        low = 0.35 * self.world_size
        high = 0.65 * self.world_size
        first = self.np_random.uniform(low, high, size=2)
        second = self.np_random.uniform(low, high, size=2)
        if np.linalg.norm(first - second) < 0.75:
            second = np.asarray([high, low], dtype=np.float32)
        return np.asarray([first, second], dtype=np.float32)

    def _touches(self, position: np.ndarray, target: np.ndarray) -> bool:
        return bool(np.linalg.norm(position - target) <= self.contact_radius)

    def _holder_on_plate(self) -> bool:
        return self._touches(
            self.agent_pos[self.active_holder], self.button_pos[self.active_plate]
        )

    def _runner_on_target(self) -> bool:
        runner = 1 - self.active_holder
        return self._touches(
            self.agent_pos[runner], self.target_pos[self.active_target]
        )

    def _task_potential(self) -> float:
        runner = 1 - self.active_holder
        holder_distance = np.linalg.norm(
            self.agent_pos[self.active_holder] - self.button_pos[self.active_plate]
        )
        runner_distance = np.linalg.norm(
            self.agent_pos[runner] - self.target_pos[self.active_target]
        )
        normalizer = 2.0 * np.sqrt(2.0) * self.world_size
        return -float((holder_distance + runner_distance) / normalizer)

    def _get_obs(self) -> dict[str, np.ndarray]:
        observations = {}
        scale = max(self.world_size, 1.0)
        for agent, idx in self.agent_ids.items():
            own = self.agent_pos[idx]
            other = self.agent_pos[1 - idx]
            vector = np.concatenate(
                [
                    2.0 * own / scale - 1.0,
                    (other - own) / scale,
                    ((self.button_pos - own) / scale).reshape(-1),
                    ((self.target_pos - own) / scale).reshape(-1),
                ]
            )
            observations[agent] = np.clip(vector, -1.0, 1.0).astype(np.float32)
        return observations

    def _get_state(self) -> np.ndarray:
        holder_onehot = np.eye(2, dtype=np.float32)[self.active_holder]
        plate_onehot = np.eye(2, dtype=np.float32)[self.active_plate]
        target_onehot = np.eye(2, dtype=np.float32)[self.active_target]
        short_phase = (self.steps % self.short_period) / float(self.short_period)
        long_phase = (self.steps % self.long_period) / float(self.long_period)
        return np.concatenate(
            [
                (self.agent_pos / self.world_size).reshape(-1),
                holder_onehot,
                plate_onehot,
                target_onehot,
                np.asarray(
                    [
                        short_phase,
                        long_phase,
                        float(self.window_target_collected),
                        float(self._holder_on_plate()),
                    ],
                    dtype=np.float32,
                ),
            ]
        ).astype(np.float32)

    def _task_metrics(self) -> dict[str, float]:
        elapsed = max(self.steps, 1)
        elapsed_windows = self.windows_completed + int(
            self.steps % self.short_period != 0
        )
        elapsed_windows = max(elapsed_windows, 1)
        return {
            "alice_bob_targets_completed": float(self.targets_completed),
            "alice_bob_cycle_success_rate": float(
                self.targets_completed / elapsed_windows
            ),
            "alice_bob_holder_occupancy_fraction": float(
                self.holder_contact_steps / elapsed
            ),
            "alice_bob_runner_target_fraction": float(
                self.runner_target_steps / elapsed
            ),
            "alice_bob_role_switch_count": float(self.role_switch_count),
            "alice_bob_active_holder": float(self.active_holder),
            "alice_bob_active_plate": float(self.active_plate),
            "alice_bob_active_target": float(self.active_target),
            "alice_bob_window_index": float(self.steps // self.short_period),
        }

    def get_current_state(self) -> dict[str, object]:
        return {
            **self._task_metrics(),
            "agent_positions": self.agent_pos.copy(),
            "button_positions": self.button_pos.copy(),
            "target_positions": self.target_pos.copy(),
            "max_steps": self.max_steps,
            "current_step": self.steps,
        }

    def _get_infos(
        self,
        step_reward: float,
        collection_event: bool,
        progress_reward: float,
    ):
        metrics = self._task_metrics()
        reward_info = {
            **metrics,
            "task_reward": float(step_reward),
            "alice_bob_progress_reward": float(progress_reward),
            "alice_bob_collection_reward": float(collection_event),
            "alice_bob_collection_event": float(collection_event),
        }
        return {
            agent: {
                "scenario": "alice_bob_asymmetric_cycles",
                "reward_info": reward_info,
                "task_metrics": metrics,
            }
            for agent in self.agents
        }

    def step(self, actions):
        if not self.agents:
            raise RuntimeError("step() called after the Alice--Bob episode ended")

        potential_before = self._task_potential()
        for agent, action in actions.items():
            idx = self.agent_ids[agent]
            delta = np.asarray(action, dtype=np.float32).reshape(2)
            delta = np.clip(delta, -1.0, 1.0) * self.action_scale
            self.agent_pos[idx] = np.clip(
                self.agent_pos[idx] + delta, 0.0, self.world_size
            )

        holder_on_plate = self._holder_on_plate()
        runner_on_target = self._runner_on_target()
        self.holder_contact_steps += int(holder_on_plate)
        self.runner_target_steps += int(runner_on_target)

        collection_event = bool(
            holder_on_plate and runner_on_target and not self.window_target_collected
        )
        progress_reward = self.progress_reward_coef * (
            self._task_potential() - potential_before
        )
        reward = float(collection_event) + float(progress_reward)
        if collection_event:
            self.window_target_collected = True
            self.targets_completed += 1

        self.steps += 1
        if self.steps % self.short_period == 0:
            self.windows_completed += 1
            self.active_target = 1 - self.active_target
            self.window_target_collected = False
            if self.steps % self.long_period == 0 and self.steps < self.max_steps:
                self.active_holder = 1 - self.active_holder
                self.active_plate = 1 - self.active_plate
                self.role_switch_count += 1

        truncated = self.steps >= self.max_steps
        observations = self._get_obs()
        rewards = {agent: reward for agent in self.agents}
        terminations = {agent: False for agent in self.agents}
        truncations = {agent: truncated for agent in self.agents}
        infos = self._get_infos(reward, collection_event, progress_reward)
        return observations, rewards, terminations, truncations, infos

    def close(self):
        return None
