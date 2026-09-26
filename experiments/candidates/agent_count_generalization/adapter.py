"""Fixed-width state adapter for native Scenario 1 count transfer."""

from __future__ import annotations

import numpy as np

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.scenario1 import UAVBaseStationEnv


MAX_UAVS = 8
N_USERS = 50
STATE_DIM = MAX_UAVS * 3 + MAX_UAVS + N_USERS * 2 + 1


class CountAdapter:
    """Keep native policy rows while exposing a count-stable scaled state.

    The wrapped adapter still owns observations, actions, rewards, termination,
    and all diagnostic information.  Only its variable-width global state is
    replaced by an eight-slot representation with explicit validity bits.
    """

    def __init__(self, env: ParallelToArrayAdapter):
        if not isinstance(env, ParallelToArrayAdapter):
            raise TypeError("CountAdapter requires ParallelToArrayAdapter")
        if int(env.n_uavs) > MAX_UAVS:
            raise ValueError(f"at most {MAX_UAVS} UAVs are supported")
        if int(env.n_users) != N_USERS:
            raise ValueError(f"count-transfer S1 requires exactly {N_USERS} users")
        self.env = env
        self.n_uavs = int(env.n_uavs)
        self.n_users = int(env.n_users)
        self.obs_dim = int(env.obs_dim)
        self.state_dim = STATE_DIM
        self.action_dim = int(env.action_dim)
        self.action_space = env.action_space
        self.observation_space = env.observation_space

    def __getattr__(self, name):
        return getattr(self.env, name)

    def _count_state(self) -> np.ndarray:
        native = self.env.env
        uavs = np.asarray(native.uav_positions, dtype=np.float32)
        users = np.asarray(native.user_positions, dtype=np.float32)
        if uavs.shape != (self.n_uavs, 3):
            raise ValueError(f"unexpected UAV position shape {uavs.shape}")
        if users.shape != (N_USERS, 2):
            raise ValueError(f"unexpected user position shape {users.shape}")

        area = float(native.area_size)
        height_low, height_high = map(float, native.height_range)
        height_span = height_high - height_low
        if not np.isfinite(area) or area <= 0.0:
            raise ValueError("environment area_size must be finite and positive")
        if not np.isfinite(height_span) or height_span <= 0.0:
            raise ValueError("environment height_range must have positive width")
        if int(native.max_steps) <= 0:
            raise ValueError("environment max_steps must be positive")

        padded_uavs = np.zeros((MAX_UAVS, 3), dtype=np.float32)
        padded_uavs[: self.n_uavs, :2] = uavs[:, :2] / area
        padded_uavs[: self.n_uavs, 2] = (uavs[:, 2] - height_low) / height_span
        valid = np.zeros(MAX_UAVS, dtype=np.float32)
        valid[: self.n_uavs] = 1.0
        scaled_users = users / area
        time = np.asarray([float(native.current_step) / float(native.max_steps)], dtype=np.float32)
        state = np.concatenate(
            [padded_uavs.reshape(-1), valid, scaled_users.reshape(-1), time]
        ).astype(np.float32, copy=False)
        if state.shape != (STATE_DIM,):
            raise AssertionError(f"count state has unexpected shape {state.shape}")
        return state

    def reset(self, seed=None, options=None):
        observations, info = self.env.reset(seed=seed, options=options)
        info = dict(info)
        info["state"] = self._count_state()
        return observations, info

    def step(self, actions):
        observations, reward, terminated, truncated, info = self.env.step(actions)
        info = dict(info)
        info["next_state"] = self._count_state()
        return observations, reward, terminated, truncated, info

    def close(self):
        return self.env.close()


def make_envs(count: int, seed: int, n_agents: int, horizon: int):
    """Create independent native uniform/free-space S1 lanes."""
    if int(count) <= 0:
        raise ValueError("count must be positive")
    envs = []
    for rank in range(int(count)):
        lane_seed = int(seed) + rank
        native = UAVBaseStationEnv(
            n_uavs=int(n_agents),
            n_users=N_USERS,
            max_steps=int(horizon),
            user_distribution="uniform",
            channel_model="free_space",
            seed=lane_seed,
        )
        envs.append(CountAdapter(ParallelToArrayAdapter(native, seed=lane_seed)))
    return envs
