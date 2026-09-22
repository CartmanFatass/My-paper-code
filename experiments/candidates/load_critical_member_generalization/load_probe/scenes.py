"""Matched native Scenario 1 scenes and service diagnostics.

This module changes only episode initialization.  Motion, channel evaluation,
assignment, reward, and termination remain the native Scenario 1 methods.
Capacity is deliberately absent from observations and state.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from typing import Any

import numpy as np

from envs.pettingzoo.scenario1 import UAVBaseStationEnv


N_USERS = 50
MAX_UAVS = 8
WORLD_IDS = tuple(range(16))
_WORLD_ADDRESS = (260922, 6)
_USER_STREAM = 1
_UAV_STREAM = 2


def _integer(name: str, value: Any) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    return int(value)


def _stream_seed(world_id: int, stream: int) -> int:
    state = np.random.SeedSequence(
        [*_WORLD_ADDRESS, world_id, stream]
    ).generate_state(1, dtype=np.uint32)
    return int(state[0])


@dataclass(frozen=True)
class MatchedWorld:
    """One complete physical world before taking an N-UAV prefix."""

    world_id: int
    user_seed: int
    uav_seed: int
    user_positions: np.ndarray
    uav_positions: np.ndarray


def matched_world(world_id: int) -> MatchedWorld:
    """Generate the declared independent 50-user and eight-UAV streams."""
    world_id = _integer("world_id", world_id)
    if world_id not in WORLD_IDS:
        raise ValueError(f"world_id must be one of {WORLD_IDS}")

    user_seed = _stream_seed(world_id, _USER_STREAM)
    user_rng = np.random.RandomState(user_seed)
    users = np.empty((N_USERS, 2), dtype=np.float64)
    for user_idx in range(N_USERS):
        users[user_idx, 0] = user_rng.uniform(0.0, 1000.0)
        users[user_idx, 1] = user_rng.uniform(0.0, 1000.0)

    uav_seed = _stream_seed(world_id, _UAV_STREAM)
    uav_rng = np.random.RandomState(uav_seed)
    uavs = np.empty((MAX_UAVS, 3), dtype=np.float64)
    for uav_idx in range(MAX_UAVS):
        uavs[uav_idx, 0] = uav_rng.uniform(0.0, 1000.0)
        uavs[uav_idx, 1] = uav_rng.uniform(0.0, 1000.0)
        uavs[uav_idx, 2] = uav_rng.uniform(50.0, 150.0)

    users.setflags(write=False)
    uavs.setflags(write=False)
    return MatchedWorld(world_id, user_seed, uav_seed, users, uavs)


def refresh_native_scene(env: UAVBaseStationEnv):
    """Refresh native caches, channel state, observations, and state in reset order."""
    if not isinstance(env, UAVBaseStationEnv):
        raise TypeError("refresh_native_scene requires UAVBaseStationEnv")
    env._begin_path_loss_step()
    env._update_channel_state()
    observations = {agent: env._get_observation(agent) for agent in env.agents}
    state = env._get_state()
    return observations, state


class MatchedWorldS1(UAVBaseStationEnv):
    """Native S1 whose resets reinstall one declared physical world."""

    def __init__(
        self,
        *,
        n_uavs: int,
        capacity: int,
        world_id: int,
        horizon: int = 500,
    ) -> None:
        n_uavs = _integer("n_uavs", n_uavs)
        capacity = _integer("capacity", capacity)
        horizon = _integer("horizon", horizon)
        if not 1 <= n_uavs <= MAX_UAVS:
            raise ValueError(f"n_uavs must be in [1, {MAX_UAVS}]")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if horizon <= 0:
            raise ValueError("horizon must be positive")

        self.matched_world = matched_world(world_id)
        # MultiUAVEnv.__init__ performs one native reset before Scenario 1 sets
        # its threshold and capacity.  Do not install the matched scene there;
        # the explicit reset below happens only after those values are final.
        self._matched_reset_ready = False
        super().__init__(
            n_uavs=n_uavs,
            n_users=N_USERS,
            max_steps=horizon,
            user_distribution="uniform",
            channel_model="free_space",
            seed=self.matched_world.user_seed,
            min_sinr=0,
            max_connections=capacity,
        )
        if self.use_fdma or self.min_sinr != 0 or self.max_connections != capacity:
            raise RuntimeError("native S1 load contract was not installed")
        self._matched_reset_ready = True
        self.reset(seed=self.matched_world.user_seed)

    def reset(self, seed=None, options=None):
        # A no-argument repeat reset also restores the local native RNG.  A
        # caller-supplied runtime seed remains lawful but cannot change geometry.
        native_seed = self.matched_world.user_seed if seed is None else seed
        observations, infos = super().reset(seed=native_seed, options=options)
        if not self._matched_reset_ready:
            return observations, infos

        np.copyto(self.user_positions, self.matched_world.user_positions)
        np.copyto(
            self.uav_positions,
            self.matched_world.uav_positions[: self.n_uavs],
        )
        observations, state = refresh_native_scene(self)
        if state.shape != (self.state_dim,):
            raise RuntimeError("native S1 state shape changed during matched reset")
        return observations, {agent: {} for agent in self.agents}


def make_native_scene(
    *,
    n_uavs: int,
    capacity: int,
    world_id: int,
    horizon: int = 500,
) -> MatchedWorldS1:
    """Return an explicitly reset native S1, ready for later adapter wrapping."""
    return MatchedWorldS1(
        n_uavs=n_uavs,
        capacity=capacity,
        world_id=world_id,
        horizon=horizon,
    )


def _ratio(numerator: int, denominator: int) -> dict[str, int | float | None]:
    return {
        "numerator": int(numerator),
        "denominator": int(denominator),
        "rate": float(numerator / denominator) if denominator else None,
    }


def service_diagnostics(env: UAVBaseStationEnv) -> dict[str, Any]:
    """Read current native service without changing the environment or any RNG."""
    if not isinstance(env, UAVBaseStationEnv):
        raise TypeError("service_diagnostics requires UAVBaseStationEnv")

    sinr = np.asarray(env.sinr_matrix)
    connections = np.asarray(env.connections, dtype=bool)
    expected_shape = (int(env.n_uavs), int(env.n_users))
    if sinr.shape != expected_shape or connections.shape != expected_shape:
        raise ValueError("native SINR/connection matrices have unexpected shapes")
    if not np.isfinite(sinr).all():
        raise ValueError("native SINR matrix must be finite")

    eligible = sinr >= float(env.min_sinr)
    eligible_per_user = np.count_nonzero(eligible, axis=0)
    connected_per_user = np.count_nonzero(connections, axis=0)
    eligible_users = eligible_per_user > 0
    served_users = connected_per_user > 0
    eligible_unserved = np.flatnonzero(eligible_users & ~served_users)
    ineligible = np.flatnonzero(~eligible_users)
    served = np.flatnonzero(served_users)

    e_i = np.count_nonzero(eligible, axis=1)
    occupancy = np.count_nonzero(connections, axis=1)
    capacity = _integer("env.max_connections", env.max_connections)
    visible_limit = _integer("env.max_observed_users", env.max_observed_users)
    visible = np.minimum(e_i, visible_limit)
    truncated = e_i - visible

    normalized_quality = np.clip(
        (sinr - float(env.min_sinr)) / 30.0,
        0.0,
        1.0,
    )
    quality_sum = float(np.sum(normalized_quality[connections]))
    served_count = int(np.count_nonzero(connections))
    quality_mean = quality_sum / max(served_count, 1)
    coverage = served_count / int(env.n_users)
    height_span = float(env.height_range[1] - env.height_range[0])
    height_penalty = (
        (float(np.mean(env.uav_positions[:, 2])) - float(env.height_range[0]))
        / height_span
        * 0.1
    )
    total_reward = (
        float(env.coverage_weight) * coverage
        + float(env.quality_weight) * quality_mean
        - height_penalty
    )

    at_most_one = bool(np.all(eligible_per_user <= 1))
    noise_linear = float(np.power(10.0, float(env.noise_power) / 10.0))
    reasons = []
    if bool(env.use_fdma):
        reasons.append("use_fdma must be False")
    if float(env.min_sinr) < 0.0:
        reasons.append("min_sinr must be at least 0 dB")
    if not np.isfinite(noise_linear) or noise_linear <= 0.0:
        reasons.append("linear noise power must be finite and positive")
    if not at_most_one:
        reasons.append("actual SINR has a user eligible to more than one UAV")
    if np.any(connections & ~eligible):
        reasons.append("native connections include an ineligible link")
    if np.any(connected_per_user > 1):
        reasons.append("native connections serve a user more than once")

    identity_applicable = not reasons
    predicted = int(np.minimum(e_i, capacity).sum()) if identity_applicable else None
    identity = {
        "applicable": identity_applicable,
        "reasons": reasons,
        "predicted_served_S_c": predicted,
        "actual_served": served_count,
        "holds": bool(predicted == served_count) if identity_applicable else None,
    }

    per_uav = []
    for index in range(int(env.n_uavs)):
        count = int(occupancy[index])
        per_uav.append(
            {
                "uav": index,
                "e_i": int(e_i[index]),
                "served": count,
                "occupancy": _ratio(count, capacity),
                "full": bool(count == capacity),
                "visible_user_truncation": _ratio(
                    int(truncated[index]), int(e_i[index])
                ),
            }
        )

    return {
        "e_i": e_i.astype(int).tolist(),
        "connections": connections.tolist(),
        "eligible_user_indices": np.flatnonzero(eligible_users).astype(int).tolist(),
        "eligible_unserved_user_indices": eligible_unserved.astype(int).tolist(),
        "ineligible_user_indices": ineligible.astype(int).tolist(),
        "served_user_indices": served.astype(int).tolist(),
        "user_counts": {
            "total": int(env.n_users),
            "eligible": int(np.count_nonzero(eligible_users)),
            "eligible_unserved": int(eligible_unserved.size),
            "ineligible": int(ineligible.size),
            "served": int(served.size),
        },
        "at_most_one_eligible": {
            "holds": at_most_one,
            "maximum_eligible_uavs_per_user": int(eligible_per_user.max(initial=0)),
        },
        "per_uav": per_uav,
        "occupancy": _ratio(served_count, int(env.n_uavs) * capacity),
        "full_uavs": _ratio(int(np.count_nonzero(occupancy == capacity)), int(env.n_uavs)),
        "visible_user_truncation": _ratio(int(truncated.sum()), int(e_i.sum())),
        "quality_composition": {
            "connected_links": served_count,
            "normalized_sinr_sum": quality_sum,
            "normalized_sinr_mean": quality_mean,
        },
        "reward_components": {
            "coverage_reward": coverage,
            "quality_reward": quality_mean,
            "energy_penalty": height_penalty,
            "total_reward": total_reward,
        },
        "capacity_identity": identity,
    }
