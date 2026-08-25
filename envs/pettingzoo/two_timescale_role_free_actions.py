"""Dense role-free toy task with two independent target time scales.

The two agents receive identical constant local observations.  The centralized
state exposes one slow and one fast action target, so the high-level roster is
the only route by which task context can select different low-level skills.
The shared task reward is the better of the two possible agent-to-target
assignments; the environment never names or fixes agent roles.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np
from pettingzoo.utils.env import ParallelEnv


class TwoTimescaleRoleFreeActionsEnv(ParallelEnv):
    metadata = {
        "name": "two_timescale_role_free_actions_v0",
        "render_modes": [],
    }

    def __init__(self, config=None, render_mode=None, seed=None):
        super().__init__()
        self.render_mode = render_mode
        self.k0 = int(getattr(config, "r39_toy_k0", 5))
        self.slow_period_blocks = int(
            getattr(config, "r39_toy_slow_period_blocks", 6)
        )
        self.max_steps = int(getattr(config, "max_steps", 40))
        if self.k0 <= 0 or self.slow_period_blocks <= 0 or self.max_steps <= 0:
            raise ValueError("toy clocks and max_steps must be positive")

        self.possible_agents = ["agent_0", "agent_1"]
        self.agents = self.possible_agents.copy()
        self._action_spaces = {
            agent: gym.spaces.Box(-1.0, 1.0, shape=(2,), dtype=np.float32)
            for agent in self.possible_agents
        }
        self._observation_spaces = {
            agent: gym.spaces.Box(-1.0, 1.0, shape=(4,), dtype=np.float32)
            for agent in self.possible_agents
        }
        self.np_random = np.random.default_rng(seed)
        self.steps = 0
        self._initial_slow_sign = 1.0
        self._initial_fast_sign = 1.0
        self._last_metrics = self._empty_metrics()

    def action_space(self, agent):
        return self._action_spaces[agent]

    def observation_space(self, agent):
        return self._observation_spaces[agent]

    def get_obs_dim(self) -> int:
        return 4

    def get_state_dim(self) -> int:
        return 6

    def reset(self, seed=None, options=None):
        del options
        if seed is not None:
            self.np_random = np.random.default_rng(seed)
        self.agents = self.possible_agents.copy()
        self.steps = 0
        self._initial_slow_sign = float(self.np_random.choice((-1.0, 1.0)))
        self._initial_fast_sign = float(self.np_random.choice((-1.0, 1.0)))
        self._last_metrics = self._empty_metrics()
        return self._get_obs(), self._get_infos(self._last_metrics)

    def _targets(self) -> tuple[np.ndarray, np.ndarray]:
        fast_block = self.steps // self.k0
        slow_block = self.steps // (self.k0 * self.slow_period_blocks)
        slow_sign = self._initial_slow_sign * (-1.0 if slow_block % 2 else 1.0)
        fast_sign = self._initial_fast_sign * (-1.0 if fast_block % 2 else 1.0)
        slow = np.asarray([slow_sign, 0.0], dtype=np.float32)
        fast = np.asarray([0.0, fast_sign], dtype=np.float32)
        return slow, fast

    def _get_obs(self) -> dict[str, np.ndarray]:
        constant = np.zeros(4, dtype=np.float32)
        return {agent: constant.copy() for agent in self.possible_agents}

    def _get_state(self) -> np.ndarray:
        slow, fast = self._targets()
        fast_phase = (self.steps % self.k0) / float(self.k0)
        slow_period = self.k0 * self.slow_period_blocks
        slow_phase = (self.steps % slow_period) / float(slow_period)
        return np.concatenate(
            [
                slow,
                fast,
                np.asarray([fast_phase, slow_phase], dtype=np.float32),
            ]
        ).astype(np.float32)

    @staticmethod
    def _match(action: np.ndarray, target: np.ndarray) -> float:
        # Unit targets make 1 - ||a-target||^2 / 2 a bounded, dense matching
        # objective after clipping: exact target=1, zero action=0.5, and an
        # orthogonal unit action=0.
        squared_error = float(np.square(action - target).sum())
        return float(np.clip(1.0 - 0.5 * squared_error, 0.0, 1.0))

    def _score_actions(self, actions) -> dict[str, float]:
        clipped = []
        for agent in self.possible_agents:
            if agent not in actions:
                raise ValueError(f"missing action for {agent}")
            action = np.asarray(actions[agent], dtype=np.float32)
            if action.shape != (2,) or not np.all(np.isfinite(action)):
                raise ValueError(f"{agent} action must be a finite shape-(2,) vector")
            clipped.append(np.clip(action, -1.0, 1.0))

        slow, fast = self._targets()
        direct_slow = self._match(clipped[0], slow)
        direct_fast = self._match(clipped[1], fast)
        swapped_slow = self._match(clipped[1], slow)
        swapped_fast = self._match(clipped[0], fast)
        direct = 0.5 * (direct_slow + direct_fast)
        swapped = 0.5 * (swapped_slow + swapped_fast)
        if direct >= swapped:
            slow_match, fast_match, score = direct_slow, direct_fast, direct
        else:
            slow_match, fast_match, score = swapped_slow, swapped_fast, swapped
        return {
            "task_reward": float(score),
            "r39_toy_task_reward": float(score),
            "r39_toy_match_score": float(score),
            "r39_toy_slow_match": float(slow_match),
            "r39_toy_fast_match": float(fast_match),
        }

    @staticmethod
    def _empty_metrics() -> dict[str, float]:
        return {
            "task_reward": 0.0,
            "r39_toy_task_reward": 0.0,
            "r39_toy_match_score": 0.0,
            "r39_toy_slow_match": 0.0,
            "r39_toy_fast_match": 0.0,
        }

    def _get_infos(self, metrics: dict[str, float]):
        return {
            agent: {
                "scenario": "two_timescale_role_free_actions",
                "reward_info": dict(metrics),
            }
            for agent in self.possible_agents
        }

    def step(self, actions):
        if not self.agents:
            raise RuntimeError("step() called after the toy episode ended")

        metrics = self._score_actions(actions)
        reward = float(metrics["task_reward"])
        self._last_metrics = metrics
        self.steps += 1
        truncated = self.steps >= self.max_steps

        observations = self._get_obs()
        rewards = {agent: reward for agent in self.possible_agents}
        terminations = {agent: False for agent in self.possible_agents}
        truncations = {agent: truncated for agent in self.possible_agents}
        infos = self._get_infos(metrics)
        if truncated:
            self.agents = []
        return observations, rewards, terminations, truncations, infos

    def get_current_state(self) -> dict[str, object]:
        slow, fast = self._targets()
        return {
            "current_step": int(self.steps),
            "max_steps": int(self.max_steps),
            "r39_toy_k0": int(self.k0),
            "r39_toy_slow_period_blocks": int(self.slow_period_blocks),
            "r39_toy_slow_target": slow.copy(),
            "r39_toy_fast_target": fast.copy(),
            **self._last_metrics,
        }

    def close(self):
        self.agents = []
