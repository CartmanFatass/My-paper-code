"""Role-free Alice--Bob surrogate with asymmetric subtask time scales.

The active button persists across several high-level checks while the active
target changes every check.  The environment never assigns either subtask to
an agent; complementary skill allocation must emerge from the controller.  Its
shared external reward is sparse: one collection event when different agents
jointly occupy the active button and target.  There is no distance or progress
reward shaping.
"""

from __future__ import annotations

import copy

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
        if self.short_period <= 0 or self.long_periods <= 0:
            raise ValueError("Alice--Bob periods must be positive")
        if self.num_short_periods < 2 * self.long_periods:
            raise ValueError(
                "Alice--Bob episode must contain at least two long-task phases"
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
        # two target offsets (4). Active subtask state is intentionally omitted.
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
        # positions (4), active plate/target one-hot (4), two clock phases (2),
        # collected flag (1), current contacts (4), and previous-window
        # per-agent button/target occupancy fractions (4).
        return 19

    def intrinsic_effect_view(self) -> np.ndarray:
        """Return the task-agnostic interaction state used by R31.

        Only normalized agent positions are exposed.  Active tasks, contacts,
        clocks, collection state, and reward-derived fields remain private to
        the environment and cannot leak into the effect posterior.
        """
        return (self.agent_pos / self.world_size).astype(np.float32, copy=True)

    def get_probe_snapshot(self) -> dict[str, object]:
        """Capture the complete mutable simulator state for shadow rollouts."""
        return {
            "agents": list(self.agents),
            "steps": int(self.steps),
            "agent_pos": self.agent_pos.copy(),
            "active_plate": int(self.active_plate),
            "active_target": int(self.active_target),
            "window_target_collected": bool(self.window_target_collected),
            "targets_completed": int(self.targets_completed),
            "windows_completed": int(self.windows_completed),
            "button_contact_steps": int(self.button_contact_steps),
            "target_contact_steps": int(self.target_contact_steps),
            "joint_coordination_steps": int(self.joint_coordination_steps),
            "button_switch_count": int(self.button_switch_count),
            "window_button_contacts": self.window_button_contacts.copy(),
            "window_target_contacts": self.window_target_contacts.copy(),
            "last_window_button_fraction": self.last_window_button_fraction.copy(),
            "last_window_target_fraction": self.last_window_target_fraction.copy(),
            "rng_state": copy.deepcopy(self.np_random.bit_generator.state),
        }

    def set_probe_snapshot(self, snapshot: dict[str, object]) -> None:
        """Restore a snapshot produced by :meth:`get_probe_snapshot`."""
        self.agents = list(snapshot["agents"])
        self.steps = int(snapshot["steps"])
        self.agent_pos = np.asarray(snapshot["agent_pos"], dtype=np.float32).copy()
        self.active_plate = int(snapshot["active_plate"])
        self.active_target = int(snapshot["active_target"])
        self.window_target_collected = bool(snapshot["window_target_collected"])
        self.targets_completed = int(snapshot["targets_completed"])
        self.windows_completed = int(snapshot["windows_completed"])
        self.button_contact_steps = int(snapshot["button_contact_steps"])
        self.target_contact_steps = int(snapshot["target_contact_steps"])
        self.joint_coordination_steps = int(snapshot["joint_coordination_steps"])
        self.button_switch_count = int(snapshot["button_switch_count"])
        self.window_button_contacts = np.asarray(
            snapshot["window_button_contacts"], dtype=np.int64
        ).copy()
        self.window_target_contacts = np.asarray(
            snapshot["window_target_contacts"], dtype=np.int64
        ).copy()
        self.last_window_button_fraction = np.asarray(
            snapshot["last_window_button_fraction"], dtype=np.float32
        ).copy()
        self.last_window_target_fraction = np.asarray(
            snapshot["last_window_target_fraction"], dtype=np.float32
        ).copy()
        self.np_random.bit_generator.state = copy.deepcopy(snapshot["rng_state"])

    def reset(self, seed=None, options=None):
        del options
        if seed is not None:
            self.np_random = np.random.default_rng(seed)
        self.agents = self.possible_agents.copy()
        self.steps = 0
        self.agent_pos = self._sample_initial_positions()
        self.active_plate = int(self.np_random.integers(0, 2))
        self.active_target = int(self.np_random.integers(0, 2))
        self.window_target_collected = False
        self.targets_completed = 0
        self.windows_completed = 0
        self.button_contact_steps = 0
        self.target_contact_steps = 0
        self.joint_coordination_steps = 0
        self.button_switch_count = 0
        self.window_button_contacts = np.zeros(2, dtype=np.int64)
        self.window_target_contacts = np.zeros(2, dtype=np.int64)
        self.last_window_button_fraction = np.zeros(2, dtype=np.float32)
        self.last_window_target_fraction = np.zeros(2, dtype=np.float32)
        observations = self._get_obs()
        infos = self._get_infos(
            step_reward=0.0,
            collection_event=False,
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

    def _button_contacts(self) -> np.ndarray:
        return np.asarray(
            [
                self._touches(position, self.button_pos[self.active_plate])
                for position in self.agent_pos
            ],
            dtype=np.bool_,
        )

    def _target_contacts(self) -> np.ndarray:
        return np.asarray(
            [
                self._touches(position, self.target_pos[self.active_target])
                for position in self.agent_pos
            ],
            dtype=np.bool_,
        )

    @staticmethod
    def _jointly_satisfied(
        button_contacts: np.ndarray,
        target_contacts: np.ndarray,
    ) -> bool:
        return bool(
            (button_contacts[0] and target_contacts[1])
            or (button_contacts[1] and target_contacts[0])
        )

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
        plate_onehot = np.eye(2, dtype=np.float32)[self.active_plate]
        target_onehot = np.eye(2, dtype=np.float32)[self.active_target]
        short_phase = (self.steps % self.short_period) / float(self.short_period)
        long_phase = (self.steps % self.long_period) / float(self.long_period)
        button_contacts = self._button_contacts().astype(np.float32)
        target_contacts = self._target_contacts().astype(np.float32)
        return np.concatenate(
            [
                (self.agent_pos / self.world_size).reshape(-1),
                plate_onehot,
                target_onehot,
                np.asarray(
                    [
                        short_phase,
                        long_phase,
                        float(self.window_target_collected),
                    ],
                    dtype=np.float32,
                ),
                button_contacts,
                target_contacts,
                self.last_window_button_fraction,
                self.last_window_target_fraction,
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
            "alice_bob_button_occupancy_fraction": float(
                self.button_contact_steps / elapsed
            ),
            "alice_bob_target_contact_fraction": float(
                self.target_contact_steps / elapsed
            ),
            "alice_bob_joint_coordination_fraction": float(
                self.joint_coordination_steps / elapsed
            ),
            "alice_bob_button_switch_count": float(self.button_switch_count),
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
    ):
        metrics = self._task_metrics()
        reward_info = {
            **metrics,
            "task_reward": float(step_reward),
            # Retained as an explicit zero-valued compatibility metric so run
            # evidence can prove that environment shaping was absent.
            "alice_bob_progress_reward": 0.0,
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

        for agent, action in actions.items():
            idx = self.agent_ids[agent]
            delta = np.asarray(action, dtype=np.float32).reshape(2)
            delta = np.clip(delta, -1.0, 1.0) * self.action_scale
            self.agent_pos[idx] = np.clip(
                self.agent_pos[idx] + delta, 0.0, self.world_size
            )

        button_contacts = self._button_contacts()
        target_contacts = self._target_contacts()
        jointly_satisfied = self._jointly_satisfied(
            button_contacts,
            target_contacts,
        )
        self.button_contact_steps += int(np.any(button_contacts))
        self.target_contact_steps += int(np.any(target_contacts))
        self.joint_coordination_steps += int(jointly_satisfied)
        self.window_button_contacts += button_contacts.astype(np.int64)
        self.window_target_contacts += target_contacts.astype(np.int64)

        collection_event = bool(
            jointly_satisfied and not self.window_target_collected
        )
        reward = float(collection_event)
        if collection_event:
            self.window_target_collected = True
            self.targets_completed += 1

        self.steps += 1
        if self.steps % self.short_period == 0:
            self.windows_completed += 1
            self.last_window_button_fraction = (
                self.window_button_contacts.astype(np.float32)
                / float(self.short_period)
            )
            self.last_window_target_fraction = (
                self.window_target_contacts.astype(np.float32)
                / float(self.short_period)
            )
            self.window_button_contacts.fill(0)
            self.window_target_contacts.fill(0)
            self.active_target = 1 - self.active_target
            self.window_target_collected = False
            if self.steps % self.long_period == 0 and self.steps < self.max_steps:
                self.active_plate = 1 - self.active_plate
                self.button_switch_count += 1

        truncated = self.steps >= self.max_steps
        observations = self._get_obs()
        rewards = {agent: reward for agent in self.agents}
        terminations = {agent: False for agent in self.agents}
        truncations = {agent: truncated for agent in self.agents}
        infos = self._get_infos(reward, collection_event)
        return observations, rewards, terminations, truncations, infos

    def close(self):
        return None
