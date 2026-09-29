"""Scenario-2 contract adapter for coupled_host_joint_skills_stage1 cell 1 (b01, T3).

Port of ``agent_count_generalization/adapter.py::CountAdapter`` onto the direction's
``CoupledRelayHost``.  The wrapped ``ParallelToArrayAdapter`` keeps observations (obs_dim 90),
actions, rewards and termination; only the native 119-dim global state (UAV xyz in metres,
user xy in metres, step fraction; ``uav_env.py`` 353-366) is replaced by the ACG 133-dim scaled
eight-slot layout:

    [0:24)    eight UAV slots (x/area, y/area, (z - 50)/100); slots 6 and 7 are zero padding
    [24:32)   validity bits (six ones, two zeros)
    [32:132)  50 users (x/area, y/area)
    [132]     current_step / max_steps

It is the same information as the native state (nothing about the BS, links or routing is
added).  Every reset must pass an explicit world seed; ``reset(seed=None)`` raises, so no
episode silently advances the host's world stream.
"""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

from .host import CoupledRelayHost, make_host

MAX_UAVS = 8
N_UAVS = 6
N_USERS = 50
OBS_DIM = 90
NATIVE_STATE_DIM = 119
STATE_DIM = MAX_UAVS * 3 + MAX_UAVS + N_USERS * 2 + 1  # 133
HORIZON = 500

#: Declared evaluation panels; training worlds must never fall inside them.
DEV_WORLDS = tuple(range(1000, 1032))
HOLDOUT_WORLDS = tuple(range(2000, 2032))
PANEL_WORLD_SET = frozenset(DEV_WORLDS) | frozenset(HOLDOUT_WORLDS)

#: Reward identity tolerances (the scalar is team / 6 in float64).
REWARD_ATOL = 1e-9
REWARD_RTOL = 1e-9


def training_world_seed(fit_seed: int, lane: int, episode: int) -> int:
    """World seed of fit ``fit_seed``, lane ``lane``, episode ``episode`` (declared rule).

    ``300000 + (fit_seed % 1000) * 100 + lane + episode * 10000``.  Paired H/SET seeds share the
    last three digits (…201, …307, …413) and therefore the whole training-world sequence.
    """
    for name, value in (("fit_seed", fit_seed), ("lane", lane), ("episode", episode)):
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise TypeError(f"{name} must be an integer")
    if not 0 <= int(lane) < 100:
        raise ValueError("lane must lie in [0, 100) for the declared world-seed rule")
    if int(episode) < 0:
        raise ValueError("episode must be non-negative")
    world = 300000 + (int(fit_seed) % 1000) * 100 + int(lane) + int(episode) * 10000
    if world in PANEL_WORLD_SET:
        raise AssertionError(f"training world {world} falls inside a declared panel")
    return world


class ContractError(RuntimeError):
    """The adapter or the host violated the declared cell-1 contract."""


def contract_reward_check(scalar: float, reward_info: dict[str, Any], n_uavs: int = N_UAVS) -> dict[str, float]:
    """Per-step identity ``n_uavs * scalar == contract_reward == 0.5 * (C_bh + S / D)``.

    Uses exactly the keys ``host.CoupledRelayHost._compute_reward`` writes.  Returns a copy of the
    reader values.
    """
    try:
        contract = float(reward_info["contract_reward"])
        c_bh = float(reward_info["coverage_backhauled"])
        throughput = float(reward_info["throughput_term"])
    except KeyError as exc:  # pragma: no cover - defensive
        raise ContractError(f"reward_info lacks the contract key {exc}") from exc
    values = np.asarray([scalar, contract, c_bh, throughput], dtype=float)
    if not np.isfinite(values).all():
        raise ContractError("non-finite reward reader")
    if not np.isclose(n_uavs * float(scalar), contract, rtol=REWARD_RTOL, atol=REWARD_ATOL):
        raise ContractError(f"n_uavs * scalar {n_uavs * float(scalar)!r} != contract_reward {contract!r}")
    formula = 0.5 * (c_bh + throughput)
    if not np.isclose(contract, formula, rtol=REWARD_RTOL, atol=REWARD_ATOL):
        raise ContractError(f"contract_reward {contract!r} != 0.5 * (C_bh + S/D) {formula!r}")
    return {
        "contract_reward": contract,
        "coverage_backhauled": c_bh,
        "throughput_term": throughput,
        "frontend_capacity_with_path_mbps": float(reward_info["frontend_capacity_with_path_mbps"]),
        "coverage_access": float(reward_info["coverage_access"]),
        "original_normalized_reward": float(reward_info["original_normalized_reward"]),
        "action_clip_events": int(reward_info.get("action_clip_events", 0)),
    }


class ContractCountAdapter:
    """Scaled eight-slot state over the b01 host; observations untouched (obs_dim 90)."""

    def __init__(self, env: ParallelToArrayAdapter):
        if not isinstance(env, ParallelToArrayAdapter):
            raise TypeError("ContractCountAdapter requires ParallelToArrayAdapter")
        native = env.env
        if not isinstance(native, CoupledRelayHost):
            raise TypeError("ContractCountAdapter requires the direction's CoupledRelayHost")
        if int(env.n_uavs) != N_UAVS:
            raise ContractError(f"cell 1 requires {N_UAVS} UAVs, got {env.n_uavs}")
        if int(env.n_users) != N_USERS:
            raise ContractError(f"cell 1 requires {N_USERS} users, got {env.n_users}")
        if int(env.obs_dim) != OBS_DIM:
            raise ContractError(f"cell 1 requires obs_dim {OBS_DIM}, got {env.obs_dim}")
        if int(env.state_dim) != NATIVE_STATE_DIM:
            raise ContractError(f"cell 1 requires native state_dim {NATIVE_STATE_DIM}, got {env.state_dim}")
        if tuple(map(float, native.height_range)) != (50.0, 150.0):
            raise ContractError("cell 1 requires height_range (50, 150)")
        self.env = env
        self.n_uavs = N_UAVS
        self.n_users = N_USERS
        self.obs_dim = OBS_DIM
        self.state_dim = STATE_DIM
        self.native_state_dim = NATIVE_STATE_DIM
        self.action_dim = int(env.action_dim)
        self.action_space = env.action_space
        self.observation_space = env.observation_space
        self.current_world_seed: int | None = None

    def __getattr__(self, name):
        return getattr(self.env, name)

    @property
    def host(self) -> CoupledRelayHost:
        return self.env.env

    def _count_state(self) -> np.ndarray:
        native = self.host
        uavs = np.array(native.uav_positions, dtype=np.float32, copy=True)
        users = np.array(native.user_positions, dtype=np.float32, copy=True)
        if uavs.shape != (N_UAVS, 3):
            raise ContractError(f"unexpected UAV position shape {uavs.shape}")
        if users.shape != (N_USERS, 2):
            raise ContractError(f"unexpected user position shape {users.shape}")
        area = float(native.area_size)
        height_low, height_high = map(float, native.height_range)
        height_span = height_high - height_low
        if not np.isfinite(area) or area <= 0.0:
            raise ContractError("area_size must be finite and positive")
        if int(native.max_steps) <= 0:
            raise ContractError("max_steps must be positive")

        padded = np.zeros((MAX_UAVS, 3), dtype=np.float32)
        padded[:N_UAVS, :2] = uavs[:, :2] / area
        padded[:N_UAVS, 2] = (uavs[:, 2] - height_low) / height_span
        valid = np.zeros(MAX_UAVS, dtype=np.float32)
        valid[:N_UAVS] = 1.0
        time = np.asarray([float(native.current_step) / float(native.max_steps)], dtype=np.float32)
        state = np.concatenate(
            [padded.reshape(-1), valid, (users / area).reshape(-1), time]
        ).astype(np.float32, copy=False)
        if state.shape != (STATE_DIM,):
            raise AssertionError(f"count state has unexpected shape {state.shape}")
        return state

    def snapshot(self) -> dict[str, Any]:
        """Copies of the host arrays the panel readers need (the host mutates them in place)."""
        native = self.host
        return {
            "connections": np.array(native.connections, dtype=bool, copy=True),
            "routing_paths": {int(k): list(v) for k, v in native.routing_paths.items()},
            "uav_positions": np.array(native.uav_positions, dtype=float, copy=True),
        }

    def reset(self, seed=None, options=None):
        if seed is None:
            raise ContractError("every reset must pass an explicit world seed")
        if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
            raise TypeError("world seed must be an integer")
        observations, info = self.env.reset(seed=int(seed), options=options)
        self.current_world_seed = int(seed)
        if observations.shape != (N_UAVS, OBS_DIM):
            raise ContractError(f"unexpected observation shape {observations.shape}")
        info = dict(info)
        info["native_state_dim"] = int(np.asarray(info["state"]).shape[-1])
        if info["native_state_dim"] != NATIVE_STATE_DIM:
            raise ContractError("native state width changed")
        info["state"] = self._count_state()
        info["world_seed"] = int(seed)
        return observations, info

    def step(self, actions):
        observations, reward, terminated, truncated, info = self.env.step(actions)
        info = dict(info)
        reward_info = info["reward_components"]["reward_info"]
        info["contract"] = contract_reward_check(reward, reward_info)
        info["next_state"] = self._count_state()
        return observations, reward, terminated, truncated, info

    def close(self):
        return self.env.close()


def make_envs(count: int, world_seeds: Iterable[int], horizon: int = HORIZON,
              area_size: int = 5000) -> list[ContractCountAdapter]:
    """Create ``count`` independent lanes, lane ``l`` constructed on ``world_seeds[l]``.

    The host contract pins ``max_steps = 500``; ``horizon`` is asserted equal to it.
    """
    seeds = [int(seed) for seed in world_seeds]
    if int(count) <= 0 or len(seeds) != int(count):
        raise ValueError("count must be positive and equal to the number of world seeds")
    if int(horizon) != HORIZON:
        raise ContractError(f"the host contract pins the horizon at {HORIZON}")
    envs = []
    for seed in seeds:
        host = make_host(seed, area_size=int(area_size))
        if int(host.max_steps) != int(horizon):
            raise ContractError("host max_steps differs from the requested horizon")
        envs.append(ContractCountAdapter(ParallelToArrayAdapter(host, seed=seed)))
    return envs
