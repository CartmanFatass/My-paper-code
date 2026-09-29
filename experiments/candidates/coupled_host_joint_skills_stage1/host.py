"""Coupled relay host for coupled_host_joint_skills_stage1 b01 (host contract, cell 0).

``CoupledRelayHost`` subclasses the shared scenario-2 environment
(``envs/pettingzoo/scenario2.py::UAVCooperativeNetworkEnv``) without editing it.  It
changes exactly two things:

* ``_compute_reward`` returns the declared contract reward
  ``r = 0.5 * (C_bh + S / D)`` (no clip), where

  - ``C_bh`` = (users connected to a UAV ``i`` with ``i in self.routing_paths``) / n_users,
  - ``S``    = sum over UAVs ``i`` with a routing path and >= 1 connected user of
    ``self._compute_uav_frontend_capacity(i, users_connected_to_i)`` -- the same call and
    the same condition as the base method (scenario2.py 786-806); it is the
    "front-end capacity of UAVs with a backhaul path", not end-to-end bottlenecked rate,
  - ``D``    = n_uavs * bandwidth * log2(1 + 10**3), a constant fixed at construction.

* ``_update_uav_connections`` consults ``self.a2a_enabled`` (default True).  With False the
  UAV-UAV adjacency is cleared after the base update, so ``_compute_routing_paths`` can only
  produce direct UAV -> ground-BS paths.  UAV-BS links are untouched.  Observations do not
  depend on this flag (the base observation reads ``uav_sinr_matrix``, not
  ``uav_connections``).

``step()`` clips every UAV's normalised action to the unit 3-ball (L2 <= 1, so the executed
3-D speed never exceeds ``max_speed``; the base env does not clip, uav_env.py 280-291) and
counts the clipped UAVs of the step in ``reward_info["action_clip_events"]`` (and the episode
total in ``self.action_clip_events_episode``).  The caller's action arrays are never mutated:
clipped copies are passed to the parent.  Otherwise the parent step runs unchanged, so the
per-agent reward stays the team scalar / n_uavs (scenario2.py 289-290).  Note that ``MultiUAVEnv.step`` (uav_env.py 303) already calls
``_compute_reward`` once with the new user connections and the *previous* routing paths;
scenario2's ``step`` then refreshes the UAV links and routing and calls it again
(scenario2.py 286).  The second value is the one returned and the one left in
``reward_info``.

``reward_info["original_normalized_reward"]`` is obtained by *calling the parent
implementation* (``super()._compute_reward()``) on the same state, for diagnostics only.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv

DIRECTION = "coupled_host_joint_skills_stage1"

#: Constructor arguments fixed by the b01 host contract (area_size and seed are per call).
HOST_CONTRACT_KWARGS: dict[str, Any] = {
    "n_uavs": 6,
    "n_users": 50,
    "height_range": (50, 150),
    "max_speed": 30,
    "time_step": 1.0,
    "max_steps": 500,
    "user_distribution": "cluster",
    "channel_model": "free_space",
    "min_sinr": 3,
    "max_connections": 10,
    "max_hops": 3,
    "n_ground_bs": 1,
    "max_observed_uavs": 6,
    "max_observed_users": 20,
    "use_fdma": True,
    "bandwidth": 20e6,
    "ground_bs_tx_power": 23,
    "use_shadowing": False,
}

#: An action counts as a clip event when its L2 norm exceeds 1 by more than this.
CLIP_EVENT_TOL = 1e-9

#: SINR (dB) of the base class's per-UAV front-end ceiling (scenario2.py 745-746).
FRONTEND_CEILING_SINR_DB = 30.0


class ContractError(RuntimeError):
    """The constructed host does not satisfy the declared b01 host contract."""


def contract_denominator(n_uavs: int, bandwidth: float) -> float:
    """D = n_uavs * B * log2(1 + 10**(30/10)) in bps; independent of positions."""
    return float(n_uavs) * float(bandwidth) * math.log2(1.0 + 10.0 ** (FRONTEND_CEILING_SINR_DB / 10.0))


class CoupledRelayHost(UAVCooperativeNetworkEnv):
    """Scenario-2 host with the b01 contract reward and an A2A switch."""

    def __init__(self, *args: Any, a2a_enabled: bool = True, **kwargs: Any) -> None:
        # MultiUAVEnv.__init__ calls reset(), which calls _update_uav_connections(): the flag
        # must exist before the parent constructor runs.
        self.a2a_enabled = bool(a2a_enabled)
        self.world_seed = kwargs.get("seed")
        super().__init__(*args, **kwargs)
        self.contract_denominator_bps = contract_denominator(self.n_uavs, self.bandwidth)

    # ------------------------------------------------------------------ step / action clip

    def reset(self, seed: Any = None, options: Any = None):
        self.action_clip_events_episode = 0
        return super().reset(seed=seed, options=options)

    def step(self, actions: Any):
        """Clip each UAV's normalised action to the unit 3-ball, then run the parent step."""
        clipped: dict[Any, Any] = {}
        events = 0
        for agent, action in actions.items():
            array = np.array(action, copy=True)
            if not np.issubdtype(array.dtype, np.floating):
                array = array.astype(float)
            norm = float(np.linalg.norm(array))
            if not np.isfinite(norm):
                raise ValueError(f"non-finite action for {agent!r}")
            if norm > 1.0:
                array = array / norm
                # Rounding-level excess (a unit vector built as delta / |delta|) is rescaled but
                # not reported as a clip event.
                events += int(norm > 1.0 + CLIP_EVENT_TOL)
            clipped[agent] = array
        result = super().step(clipped)
        self.action_clip_events_episode = int(getattr(self, "action_clip_events_episode", 0)) + events
        # scenario2 hands ``self.reward_info`` to every agent's info by reference, so the key
        # is visible there too; the contract reward is not touched.
        self.reward_info["action_clip_events"] = int(events)
        self.reward_info["action_clip_events_episode"] = int(self.action_clip_events_episode)
        return result

    # ------------------------------------------------------------------ connections

    def _update_uav_connections(self) -> None:
        super()._update_uav_connections()
        if not getattr(self, "a2a_enabled", True):
            self.uav_connections[:, :] = False

    # ------------------------------------------------------------------ reward

    def _compute_reward(self) -> float:
        # Parent call first: it overwrites self.reward_info with its own dict.
        original_normalized = float(super()._compute_reward())
        parent_info = dict(self.reward_info)

        n_users = int(self.n_users)
        backhauled_users = 0
        frontend_with_path = 0.0
        for i in range(self.n_uavs):
            users_i = np.flatnonzero(self.connections[i]).tolist()
            if not users_i:
                continue
            if i in self.routing_paths:
                backhauled_users += len(users_i)
                frontend_with_path += float(self._compute_uav_frontend_capacity(i, users_i))

        denominator = self.contract_denominator_bps
        coverage_backhauled = backhauled_users / n_users
        throughput_term = frontend_with_path / denominator
        reward = 0.5 * (coverage_backhauled + throughput_term)

        routed = self.routing_paths
        self.reward_info = {
            "contract_reward": float(reward),
            "coverage_access": float(parent_info["coverage_reward"]),
            "coverage_backhauled": float(coverage_backhauled),
            "frontend_capacity_with_path_mbps": frontend_with_path / 1e6,
            "throughput_term": float(throughput_term),
            "original_normalized_reward": original_normalized,
            "original_reward_source": "parent call: UAVCooperativeNetworkEnv._compute_reward",
            "avg_hops": float(parent_info["avg_hops"]),
            "mean_relays_per_routed_uav": (
                sum(len(path) - 2 for path in routed.values()) / len(routed) if routed else 0.0
            ),
            "routed_uavs": len(routed),
            "connected_users": int(parent_info["connected_users"]),
            "backhauled_users": int(backhauled_users),
            "a2a_enabled": bool(getattr(self, "a2a_enabled", True)),
        }
        return float(reward)


def check_contract(env: CoupledRelayHost) -> None:
    """Raise ContractError unless the constructed host carries the declared constants."""
    checks = {
        "channel_model": (env.channel_model, "free_space"),
        "max_connections": (env.max_connections, 10),
        "noise_power": (env.noise_power, -80),
        "tx_power": (env.tx_power, 23),
        "min_sinr": (env.min_sinr, 3),
        "carrier_frequency": (env.carrier_frequency, 2e9),
        "bandwidth": (env.bandwidth, 20e6),
        "ground_bs_tx_power": (env.ground_bs_tx_power, 23),
        "n_uavs": (env.n_uavs, 6),
        "n_users": (env.n_users, 50),
        "n_ground_bs": (env.n_ground_bs, 1),
        "max_hops": (env.max_hops, 3),
        "use_fdma": (env.use_fdma, True),
        "user_distribution": (env.user_distribution, "cluster"),
        "max_steps": (env.max_steps, 500),
        "paper_reward": (env.paper_reward, False),
        "use_shadowing": (env.use_shadowing, False),
    }
    failed = {name: pair for name, pair in checks.items() if pair[0] != pair[1]}
    if failed:
        raise ContractError(f"host contract violated (actual, declared): {failed}")
    expected_bs = np.array([[env.area_size / 2, env.area_size / 2, 30.0]])
    if env.ground_bs_positions.shape != (1, 3) or not np.allclose(env.ground_bs_positions, expected_bs):
        raise ContractError(f"ground BS not at the centre: {env.ground_bs_positions.tolist()}")


def make_host(world_seed: int, area_size: int = 5000) -> CoupledRelayHost:
    """Construct the b01 host for one world (reset seed = world_seed) and check the contract."""
    if isinstance(world_seed, bool) or not isinstance(world_seed, (int, np.integer)):
        raise TypeError("world_seed must be an integer")
    env = CoupledRelayHost(area_size=area_size, seed=int(world_seed), **HOST_CONTRACT_KWARGS)
    check_contract(env)
    return env


def static_evaluate(
    env: CoupledRelayHost, uav_positions_xyz: Any, allow_a2a: bool = True
) -> dict[str, Any]:
    """Evaluate the contract reward of a placement without advancing the step counter.

    Sets ``env.uav_positions`` and ``env.a2a_enabled = allow_a2a`` (both persist: the caller
    owns the env), then refreshes the channel state, user connections, UAV links and routing
    paths with the env's own methods and returns a copy of ``reward_info``.  Positions must lie
    inside the arena and the height range; the caller (planner) owns clipping.
    """
    positions = np.array(uav_positions_xyz, dtype=float).reshape(env.n_uavs, 3)
    if not np.all(np.isfinite(positions)):
        raise ValueError("UAV positions must be finite")
    tol = 1e-9
    if (
        np.any(positions[:, :2] < -tol)
        or np.any(positions[:, :2] > env.area_size + tol)
        or np.any(positions[:, 2] < env.height_range[0] - tol)
        or np.any(positions[:, 2] > env.height_range[1] + tol)
    ):
        raise ValueError("UAV positions outside the arena or height range")
    env.a2a_enabled = bool(allow_a2a)
    env.uav_positions = np.ascontiguousarray(positions)
    env._begin_path_loss_step()
    env._update_channel_state()
    env._update_uav_connections()
    env._compute_routing_paths()
    env._compute_reward()
    info = dict(env.reward_info)
    info["uav_connection_count"] = int(np.sum(np.triu(env.uav_connections, 1)))
    return info
