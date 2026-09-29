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


# ================================================================================ macro-step mode (T-W)
#
# Everything below is additive: ``ContractCountAdapter`` and ``make_envs`` above are unchanged, so
# the per-step (b01) path is bit-identical.  One macro action per UAV is held for ``MACRO_K`` host
# steps and executed by the closed-loop go-to rule of ``planner.closed_loop_execute`` (the rule
# behind the sealed ``P_relay^on`` reference): straight line at ``max_speed``, the last partial
# stride exact, hold on arrival, unit-ball clip.  Every host step goes through the per-step
# adapter (contract identity check included) and, when given, an ``on_host_step(contract,
# snapshot)`` callback, so the panel readers (``runner.WorldTracker``) still see all 500 host steps.

MACRO_K = 10
MACRO_HORIZON = HORIZON // MACRO_K  # 50 macro steps per episode
CONTRACTS = ("target", "slot", "offset")
#: Offset contract bounds: horizontal disk radius and vertical half-range around the anchor.
OFFSET_RADIUS_M = 300.0
OFFSET_Z_M = 50.0
#: Zero-cost counter threshold: a decision whose target lies farther than this (3-D) from the
#: UAV's position at decision time counts as "far" (velocity-like use of the target interface).
FAR_TARGET_M = 300.0
#: A re-decision counts as a target change when the new target differs from the held one by more.
TARGET_CHANGE_TOL_M = 1e-6


def macro_training_world_seed(lane: int, episode: int) -> int:
    """Shared macro-mode training world (declared difference from b01: no fit-seed term).

    ``300000 + lane + episode * 10000``; lanes 0-15 x episodes 0-44 give the 720-world set shared
    by every macro fit (the post-final-rollout reset also touches episode 45, never stepped).
    """
    for name, value in (("lane", lane), ("episode", episode)):
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise TypeError(f"{name} must be an integer")
    if not 0 <= int(lane) < 100:
        raise ValueError("lane must lie in [0, 100) for the macro world-seed rule")
    if int(episode) < 0:
        raise ValueError("episode must be non-negative")
    world = 300000 + int(lane) + int(episode) * 10000
    if world in PANEL_WORLD_SET:
        raise AssertionError(f"training world {world} falls inside a declared panel")
    return world


def goto_actions(positions: np.ndarray, targets: np.ndarray, stride: float) -> np.ndarray:
    """The closed-loop executor's action rule (``planner.closed_loop_execute``), float64.

    Same arithmetic in the same order as the planner's closure, so a held target reproduces the
    sealed closed-loop reference bit for bit.
    """
    from .planner import ARRIVAL_TOL_M

    delta = targets - positions
    distance = np.linalg.norm(delta, axis=1)
    actions = np.zeros((positions.shape[0], 3), dtype=float)
    for i in range(positions.shape[0]):
        if distance[i] <= ARRIVAL_TOL_M:
            continue
        if distance[i] <= stride:
            actions[i] = delta[i] / stride
        else:
            actions[i] = delta[i] / distance[i]
    norms = np.linalg.norm(actions, axis=1)
    over = norms > 1.0
    actions[over] /= norms[over][:, None]
    return actions


SQUASH_MODES = ("tanh", "none")


def _squashed(raw: np.ndarray, squash: str) -> np.ndarray:
    """Actions in [-1, 1]: ``tanh(raw)`` for the Gaussian head; the bounded (``tanh_gaussian``)
    head already emits ``tanh(raw)``, which is used as is (``squash="none"``)."""
    if squash == "tanh":
        return np.tanh(raw)
    if squash == "none":
        if np.any(np.abs(raw) > 1.0 + 1e-6):
            raise ContractError("bounded-head actions must lie in [-1, 1]")
        return np.clip(raw, -1.0, 1.0)
    raise ValueError(f"unknown squash mode {squash!r}")


def decode_target(raw: np.ndarray, area_size: float, height_range=(50.0, 150.0),
                  squash: str = "tanh") -> np.ndarray:
    """``target`` contract: tanh-scaled box, ``low + (high - low) * (u + 1) / 2`` per axis with
    ``u = tanh(a)`` (Gaussian head) or ``u = a`` (bounded head, already tanh-squashed)."""
    raw = np.asarray(raw, dtype=np.float64).reshape(-1, 3)
    unit = 0.5 * (_squashed(raw, squash) + 1.0)
    low = np.array([0.0, 0.0, float(height_range[0])])
    high = np.array([float(area_size), float(area_size), float(height_range[1])])
    return low + (high - low) * unit


def decode_offset(raw: np.ndarray, squash: str = "tanh") -> np.ndarray:
    """``offset`` contract: a disk in xy (radius <= 300 m) and |dz| <= 50 m.

    Gaussian head (``squash="tanh"``): ``xy = 300 * tanh(|a_xy|) * a_xy / |a_xy|`` (zero at
    ``a_xy = 0``), ``z = 50 * tanh(a_z)``.  Bounded head (``squash="none"``, a in [-1, 1]^3):
    ``xy = 300 * a_xy / max(1, |a_xy|)`` (the square projected radially onto the unit disk),
    ``z = 50 * a_z``.
    """
    raw = np.asarray(raw, dtype=np.float64).reshape(-1, 3)
    out = np.zeros_like(raw)
    if squash == "none":
        bounded = _squashed(raw, squash)
        radius = np.linalg.norm(bounded[:, :2], axis=1)
        out[:, :2] = OFFSET_RADIUS_M * bounded[:, :2] / np.maximum(1.0, radius)[:, None]
        out[:, 2] = OFFSET_Z_M * bounded[:, 2]
        return out
    if squash != "tanh":
        raise ValueError(f"unknown squash mode {squash!r}")
    radius = np.linalg.norm(raw[:, :2], axis=1)
    nonzero = radius > 0.0
    out[nonzero, :2] = (OFFSET_RADIUS_M * np.tanh(radius[nonzero]) / radius[nonzero])[:, None] \
        * raw[nonzero, :2]
    out[:, 2] = OFFSET_Z_M * np.tanh(raw[:, 2])
    return out


class MacroCounters:
    """Zero-cost per-episode decision counters (definitions in ``DEFINITIONS``)."""

    DEFINITIONS = {
        "decisions": "UAV-level macro decisions (6 per macro step)",
        "far_target_decisions": f"decisions whose held target is > {FAR_TARGET_M:g} m (3-D) from the UAV's "
                                "position at decision time",
        "target_changes": f"re-decisions (macro step >= 1) whose target differs from the previously held "
                          f"target by > {TARGET_CHANGE_TOL_M:g} m",
        "redecisions": "UAV-level decisions at macro steps >= 1 (denominator of the target-change rate)",
        "slot_conflicts": "slot contract: per macro step, 6 minus the number of distinct slots chosen "
                          "(UAVs duplicating an already-chosen slot), summed",
        "slot_switches": "slot contract: re-decisions whose slot differs from the previously held slot",
        "offset_box_clips": "offset contract: UAV-decisions whose anchor + offset left the arena box and "
                            "was clipped to it",
        "team_decisions": "macro steps (team-level decisions)",
    }

    def __init__(self):
        self.values = {name: 0 for name in self.DEFINITIONS}

    def as_dict(self):
        out = dict(self.values)
        out["far_target_fraction"] = (out["far_target_decisions"] / out["decisions"]
                                      if out["decisions"] else None)
        out["target_change_rate"] = (out["target_changes"] / out["redecisions"]
                                     if out["redecisions"] else None)
        out["slot_conflicts_per_team_decision"] = (out["slot_conflicts"] / out["team_decisions"]
                                                   if out["team_decisions"] else None)
        return out


def merge_counters(rows: Iterable[dict]) -> dict:
    """Sum raw counters over episodes and recompute the rates."""
    counters = MacroCounters()
    n = 0
    for row in rows:
        n += 1
        for name in counters.values:
            counters.values[name] += int(row[name])
    out = counters.as_dict()
    out["episodes"] = n
    out["slot_switches_per_episode"] = counters.values["slot_switches"] / n if n else None
    return out


class MacroContractAdapter:
    """One macro action per UAV per ``MACRO_K`` host steps over the per-step contract adapter.

    ``contract``: ``"target"`` (continuous, 3 per UAV, tanh-scaled arena box), ``"slot"``
    (discrete over the world's six ``P_relay`` menu rows), ``"offset"`` (continuous, 3 per UAV,
    radial-tanh offset around the UAV's ``P_relay^on`` assigned target, clipped to the box).
    ``menu_provider(world) -> menu`` (``menus.MenuProvider``) is required for slot/offset and when
    ``menu_in_inputs``; with ``menu_in_inputs`` the 36-float menu block is appended to every
    agent's observation and to the state (``menus.menu_features``).  The macro reward is the mean
    of the ``MACRO_K`` per-step adapter scalars (team r / 6 units, as the b01 training signal).
    """

    def __init__(self, env: ContractCountAdapter, contract: str, menu_provider=None,
                 menu_in_inputs: bool | None = None, macro_k: int = MACRO_K, squash: str = "tanh"):
        if not isinstance(env, ContractCountAdapter):
            raise TypeError("MacroContractAdapter wraps a ContractCountAdapter")
        if contract not in CONTRACTS:
            raise ValueError(f"unknown macro contract {contract!r}")
        if squash not in SQUASH_MODES:
            raise ValueError(f"unknown squash mode {squash!r}")
        self.squash = squash
        if int(macro_k) <= 0 or HORIZON % int(macro_k):
            raise ContractError(f"macro_k={macro_k} must divide the {HORIZON}-step horizon")
        from .menus import MENU_WIDTH, N_SLOTS

        self.base = env
        self.contract = contract
        self.macro_k = int(macro_k)
        self.macro_horizon = HORIZON // self.macro_k
        self.menu_in_inputs = (contract == "slot") if menu_in_inputs is None else bool(menu_in_inputs)
        if (contract in ("slot", "offset") or self.menu_in_inputs) and menu_provider is None:
            raise ContractError(f"contract {contract!r} needs a menu provider")
        self.menu_provider = menu_provider
        self.menu_width = MENU_WIDTH if self.menu_in_inputs else 0
        self.n_slots = N_SLOTS
        self.n_uavs = N_UAVS
        self.n_users = N_USERS
        self.obs_dim = OBS_DIM + self.menu_width
        self.state_dim = STATE_DIM + self.menu_width
        self.action_space_type = "discrete" if contract == "slot" else "continuous"
        self.action_dim = N_SLOTS if contract == "slot" else 3
        host = env.host
        self.stride = float(host.max_speed) * float(host.time_step)
        self.area_size = float(host.area_size)
        self.height_range = tuple(map(float, host.height_range))
        self.current_world_seed: int | None = None
        self.menu = None
        self._menu_block = None
        self._reset_episode()

    def __getattr__(self, name):
        return getattr(self.base, name)

    @property
    def host(self) -> CoupledRelayHost:
        return self.base.host

    def _reset_episode(self):
        self.macro_t = 0
        self.held_targets = None
        self.held_slots = None
        self.counters = MacroCounters()

    def _augment(self, observations, state):
        if not self.menu_width:
            return observations, state
        block = self._menu_block
        tiled = np.broadcast_to(block, (observations.shape[0], block.size))
        obs = np.concatenate([observations, tiled], axis=1).astype(np.float32, copy=False)
        full = np.concatenate([state, block]).astype(np.float32, copy=False)
        return obs, full

    def reset(self, seed=None, options=None):
        observations, info = self.base.reset(seed=seed, options=options)
        self.current_world_seed = int(seed)
        self._reset_episode()
        if self.menu_provider is not None and (self.contract != "target" or self.menu_in_inputs):
            from .menus import menu_features

            menu = self.menu_provider(int(seed))
            if not np.array_equal(np.asarray(menu["initial_positions_xyz"], dtype=float),
                                  np.asarray(self.host.uav_positions, dtype=float)):
                raise ContractError(f"menu of world {seed} does not match the reset positions")
            self.menu = menu
            self._menu_positions = np.asarray(menu["positions_xyz"], dtype=float)
            self._anchors = np.asarray(menu["anchors_xyz"], dtype=float)
            self._menu_block = menu_features(menu, self.area_size, self.height_range[0],
                                             self.height_range[1] - self.height_range[0])
        observations, state = self._augment(observations, info["state"])
        info = dict(info)
        info["state"] = state
        info["macro_t"] = 0
        return observations, info

    # ------------------------------------------------------------------ decoding

    def decode(self, actions) -> tuple[np.ndarray, dict]:
        """Macro action -> held targets (6 x 3, float64) and decision facts."""
        facts: dict[str, Any] = {}
        if self.contract == "slot":
            slots = np.asarray(actions).reshape(-1)
            if slots.shape != (self.n_uavs,):
                raise ContractError(f"slot actions must have shape ({self.n_uavs},), got {np.shape(actions)}")
            if not np.all(np.isfinite(slots.astype(float))) or np.any(slots != np.round(slots)):
                raise ContractError("slot actions must be integers")
            slots = slots.astype(np.int64)
            if np.any(slots < 0) or np.any(slots >= self.n_slots):
                raise ContractError(f"slot index outside [0, {self.n_slots})")
            facts["slots"] = slots
            return self._menu_positions[slots].copy(), facts
        raw = np.asarray(actions, dtype=np.float64)
        if raw.shape != (self.n_uavs, 3) or not np.all(np.isfinite(raw)):
            raise ContractError(f"{self.contract} actions must be a finite ({self.n_uavs}, 3) array")
        if self.contract == "target":
            return decode_target(raw, self.area_size, self.height_range, self.squash), facts
        wanted = self._anchors + decode_offset(raw, self.squash)
        targets = wanted.copy()
        targets[:, :2] = np.clip(targets[:, :2], 0.0, self.area_size)
        targets[:, 2] = np.clip(targets[:, 2], *self.height_range)
        facts["offset_box_clips"] = int(np.sum(np.any(targets != wanted, axis=1)))
        return targets, facts

    def _count(self, targets, facts):
        values = self.counters.values
        positions = np.asarray(self.host.uav_positions, dtype=float)
        values["team_decisions"] += 1
        values["decisions"] += self.n_uavs
        values["far_target_decisions"] += int(np.sum(np.linalg.norm(targets - positions, axis=1)
                                                     > FAR_TARGET_M))
        if self.held_targets is not None:
            values["redecisions"] += self.n_uavs
            values["target_changes"] += int(np.sum(np.linalg.norm(targets - self.held_targets, axis=1)
                                                   > TARGET_CHANGE_TOL_M))
        if "slots" in facts:
            slots = facts["slots"]
            values["slot_conflicts"] += int(self.n_uavs - np.unique(slots).size)
            if self.held_slots is not None:
                values["slot_switches"] += int(np.sum(slots != self.held_slots))
            self.held_slots = slots.copy()
        values["offset_box_clips"] += int(facts.get("offset_box_clips", 0))
        self.held_targets = targets.copy()

    # ------------------------------------------------------------------ stepping

    def step(self, actions, on_host_step=None):
        """Decode, hold for ``macro_k`` host steps under the go-to rule; see the class doc."""
        targets, facts = self.decode(actions)
        return self.step_targets(targets, facts, on_host_step=on_host_step)

    def step_targets(self, targets, facts=None, on_host_step=None):
        """Execute explicit held targets (floors use this for uniform destinations)."""
        targets = np.asarray(targets, dtype=np.float64).reshape(self.n_uavs, 3)
        facts = {} if facts is None else facts
        if self.macro_t >= self.macro_horizon:
            raise ContractError("macro step after the episode end")
        self._count(targets, facts)
        scalar_sum = 0.0
        sums = {"contract_reward": 0.0, "coverage_backhauled": 0.0, "throughput_term": 0.0}
        clip_events = 0
        host = self.host
        terminated = truncated = False
        for j in range(self.macro_k):
            host_actions = goto_actions(np.asarray(host.uav_positions, dtype=float), targets, self.stride)
            observations, reward, terminated, truncated, info = self.base.step(host_actions)
            contract = info["contract"]
            if on_host_step is not None:
                on_host_step(contract, self.base.snapshot())
            scalar_sum += float(reward)
            for key in sums:
                sums[key] += float(contract[key])
            clip_events += int(contract["action_clip_events"])
            if truncated:
                raise ContractError("the host contract never truncates")
            if terminated and j != self.macro_k - 1:
                raise ContractError("episode ended inside a macro step")
        self.macro_t += 1
        if terminated != (self.macro_t == self.macro_horizon):
            raise ContractError("terminal flag disagrees with the macro horizon")
        observations, state = self._augment(observations, info["next_state"])
        out = {
            "next_state": state,
            "contract_mean": {key: value / self.macro_k for key, value in sums.items()},
            "contract_last": contract,
            "host_steps": self.macro_k,
            "action_clip_events": clip_events,
            "targets_xyz": targets,
            "macro_t": self.macro_t,
        }
        if "slots" in facts:
            out["slots"] = facts["slots"]
        if terminated:
            out["episode_counters"] = self.counters.as_dict()
        return observations, scalar_sum / self.macro_k, bool(terminated), bool(truncated), out

    def close(self):
        return self.base.close()


def make_macro_envs(count: int, world_seeds: Iterable[int], contract: str, menu_provider=None,
                    menu_in_inputs: bool | None = None, area_size: int = 5000,
                    macro_k: int = MACRO_K, squash: str = "tanh") -> list[MacroContractAdapter]:
    """``make_envs`` lanes wrapped in the macro contract adapter (construction world = lane seed)."""
    return [MacroContractAdapter(env, contract, menu_provider, menu_in_inputs, macro_k, squash)
            for env in make_envs(count, world_seeds, HORIZON, area_size)]
