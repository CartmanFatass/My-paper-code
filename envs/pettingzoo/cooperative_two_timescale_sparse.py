import numpy as np
from gymnasium.spaces import Box
from pettingzoo import ParallelEnv


class CooperativeTwoTimescaleSparseEnv(ParallelEnv):
    metadata = {"name": "cooperative_two_timescale_sparse_v0"}
    possible_agents = ["agent_0", "agent_1"]

    def __init__(self, config, render_mode=None, seed=None):
        self.config = config
        self.render_mode = render_mode
        self.world_size = float(getattr(config, "r38_world_size", 6.0))
        self.action_scale = float(getattr(config, "r38_action_scale", 0.5))
        self.zone_radius = float(getattr(config, "r38_zone_radius", 0.75))
        self.anchor_required_steps = int(
            getattr(config, "r38_anchor_required_steps", 40)
        )
        self.shuttle_stages = int(getattr(config, "r38_shuttle_stages", 4))
        self.max_steps = int(getattr(config, "max_steps", 200))
        self.anchor = np.asarray([3.0, 3.0], dtype=np.float32)
        self.shuttle_zones = np.asarray(
            [[1.0, 3.0], [5.0, 3.0]], dtype=np.float32
        )
        self.shuttle_sequence = (0, 1, 0, 1)
        self._action_space = Box(-1.0, 1.0, shape=(2,), dtype=np.float32)
        self._observation_space = Box(-1.0, 1.0, shape=(10,), dtype=np.float32)
        self.np_random = np.random.default_rng(seed)
        self.agents = list(self.possible_agents)
        self.positions = np.zeros((2, 2), dtype=np.float32)
        self._reset_episode_state()

    def action_space(self, agent):
        return self._action_space

    def observation_space(self, agent):
        return self._observation_space

    def get_obs_dim(self):
        return 10

    def get_state_dim(self):
        return 10

    def _reset_episode_state(self):
        self.elapsed_steps = 0
        self.active_holder = -1
        self.anchor_streak = 0
        self.shuttle_stage = 0
        self.short_complete = False
        self.long_complete = False
        self.anchor_streak_max = 0
        self.shuttle_stage_max = 0
        self.full_success = False

    def _reset_attempt(self):
        self.active_holder = -1
        self.anchor_streak = 0
        self.shuttle_stage = 0
        self.short_complete = False
        self.long_complete = False

    def reset(self, seed=None, options=None):
        del options
        if seed is not None:
            self.np_random = np.random.default_rng(seed)
        anchor_spawn = self.anchor + self.np_random.uniform(-0.1, 0.1, size=2)
        visitor_spawn = np.asarray([2.0, 3.0]) + self.np_random.uniform(
            -0.1, 0.1, size=2
        )
        unordered = np.stack((anchor_spawn, visitor_spawn)).astype(np.float32)
        self.positions = unordered[self.np_random.permutation(2)].copy()
        self.agents = list(self.possible_agents)
        self._reset_episode_state()
        return self._get_obs(), self._get_infos(0.0)

    def _update_positions(self, actions):
        for i, agent in enumerate(self.possible_agents):
            action = np.asarray(actions[agent], dtype=np.float32)
            if action.shape != (2,) or not np.all(np.isfinite(action)):
                raise ValueError(f"{agent} action must be a finite shape-(2,) vector")
            self.positions[i] = np.clip(
                self.positions[i]
                + self.action_scale * np.clip(action, -1.0, 1.0),
                0.0,
                self.world_size,
            )

    def _anchor_contacts(self):
        return (
            np.linalg.norm(self.positions - self.anchor, axis=1) <= self.zone_radius
        )

    def _shuttle_contacts(self):
        return (
            np.linalg.norm(
                self.positions[:, None, :] - self.shuttle_zones[None, :, :], axis=2
            )
            <= self.zone_radius
        )

    def _accept_expected_shuttle_contact(self, visitor: int) -> None:
        if self.shuttle_stage >= self.shuttle_stages:
            return
        expected_zone = self.shuttle_sequence[self.shuttle_stage]
        contacts = self._shuttle_contacts()
        if bool(contacts[visitor, expected_zone]):
            self.shuttle_stage += 1
            self.shuttle_stage_max = max(self.shuttle_stage_max, self.shuttle_stage)

    def _advance_duty_cycle(self) -> bool:
        anchor = self._anchor_contacts()
        if self.active_holder < 0:
            if int(anchor.sum()) == 1:
                self.active_holder = int(np.flatnonzero(anchor)[0])
                self.anchor_streak = 1
                self.anchor_streak_max = max(self.anchor_streak_max, 1)
                self._accept_expected_shuttle_contact(1 - self.active_holder)
            return False

        holder = self.active_holder
        if not bool(anchor[holder]):
            self._reset_attempt()
            return False

        self.anchor_streak += 1
        self.anchor_streak_max = max(self.anchor_streak_max, self.anchor_streak)
        self._accept_expected_shuttle_contact(1 - holder)
        self.short_complete = self.shuttle_stage >= self.shuttle_stages
        self.long_complete = self.anchor_streak >= self.anchor_required_steps
        return bool(self.short_complete and self.long_complete)

    def _get_obs(self):
        result = {}
        for i, agent in enumerate(self.possible_agents):
            other = 1 - i
            own = self.positions[i]
            result[agent] = np.concatenate(
                (
                    2.0 * own / self.world_size - 1.0,
                    (self.positions[other] - own) / self.world_size,
                    (self.anchor - own) / self.world_size,
                    (self.shuttle_zones[0] - own) / self.world_size,
                    (self.shuttle_zones[1] - own) / self.world_size,
                )
            ).astype(np.float32)
        return result

    def _get_state(self):
        holder = np.zeros(2, dtype=np.float32)
        if self.active_holder >= 0:
            holder[self.active_holder] = 1.0
        return np.concatenate(
            (
                (2.0 * self.positions.reshape(-1) / self.world_size - 1.0),
                holder,
                np.asarray(
                    [
                        self.shuttle_stage / self.shuttle_stages,
                        min(
                            self.anchor_streak / self.anchor_required_steps, 1.0
                        ),
                        float(self.short_complete),
                        float(self.long_complete),
                    ],
                    dtype=np.float32,
                ),
            )
        ).astype(np.float32)

    def _task_metrics(self, reward):
        return {
            "r38_short_duty_complete": float(
                self.shuttle_stage_max >= self.shuttle_stages
            ),
            "r38_long_duty_complete": float(
                self.anchor_streak_max >= self.anchor_required_steps
            ),
            "r38_full_cycle_success": float(self.full_success),
            "r38_anchor_streak_max": float(self.anchor_streak_max),
            "r38_shuttle_stage_max": float(self.shuttle_stage_max),
            "r38_sparse_reward": float(reward),
            "task_reward": float(reward),
            "intrinsic_reward": 0.0,
        }

    def _get_infos(self, reward):
        metrics = self._task_metrics(reward)
        return {
            agent: {
                "scenario": "cooperative_two_timescale_sparse",
                "reward_info": dict(metrics),
            }
            for agent in self.possible_agents
        }

    def step(self, actions):
        if not self.agents:
            raise RuntimeError("step() called after the episode ended")
        self._update_positions(actions)
        self.elapsed_steps += 1
        success = self._advance_duty_cycle()
        self.full_success = bool(self.full_success or success)
        reward = 1.0 if success else 0.0
        terminated = bool(success)
        truncated = bool(not terminated and self.elapsed_steps >= self.max_steps)
        observations = self._get_obs()
        rewards = {agent: reward for agent in self.possible_agents}
        terminations = {agent: terminated for agent in self.possible_agents}
        truncations = {agent: truncated for agent in self.possible_agents}
        infos = self._get_infos(reward)
        if terminated or truncated:
            self.agents = []
        return observations, rewards, terminations, truncations, infos

    def get_current_state(self):
        return {
            "positions": self.positions.copy(),
            "active_holder": int(self.active_holder),
            "anchor_streak": int(self.anchor_streak),
            "shuttle_stage": int(self.shuttle_stage),
            "short_complete": bool(self.short_complete),
            "long_complete": bool(self.long_complete),
            "full_success": bool(self.full_success),
            "elapsed_steps": int(self.elapsed_steps),
        }

    def close(self):
        self.agents = []
