"""Block 1 / Block 2 of ``b04_geometry_probe_a01``: zero-fit geometry-response probe of SET c06.

Worlds are generator-consistent edits of a real ``env.reset(seed)``: raw entity positions are
changed on the raw env and the reset materialisation sequence is re-run (energy_aware.py
461-486 after routed_core.py 2130-2171 state); feature vectors are never edited.  Conditions
(``CONDITIONS``) and the fixed rules the declaration left open are the constants below; every
applied displacement, clip, matching and support check is recorded per world.

Station recomputation replays the env's own ``_init_charging_stations`` from the RandomState
captured at its entry during the real reset, so the anchor rule, the +-960 m jitter draws and the
min-separation rejection loop are the generator's (``RESET_RECORD``).  ROT / MIR_X / MIR_Y map
every entity by the square's symmetry and regenerate the spawn grid in the transformed corner
with the recorded per-slot jitter; t > 0 (UAVs off the grid) maps UAV positions and permutes them
by the t = 0 matching; ROT_KEEP keeps indices.  Per-index energy state and the GRU history stay
with the index.
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest import mock

import numpy as np
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import (
    _sync_agent, initialization_fingerprint, make_env, preserved_rng, seed_everything,
)
from hmasd.agent import HMASDAgent

from ..b01 import evaluation as b01_evaluation
from ..b01.evaluation import (
    PolicyController, HeuristicController, WorldTask, learner_eval_config, load_learner_policy,
    make_eval_config,
)
from ..b01.feedback import PRODUCTION_PARAMS, apply_feedback_params
from ..b01.heuristic import UnobservedRegime, _assign
from ..b01.native import B01Spec, heuristic_params
from ..b01.observation import own_positions

HORIZON = 3000
CONDITIONS = ("ID", "BS_A", "BS_B", "ST", "CL_1", "CL_2", "ROT", "MIR_X", "MIR_Y", "ROT_KEEP")
DECLARED = {  # condition: (consistent, in_support); None = derived per world (support_rules)
    "ID": (True, True), "BS_A": (True, True), "BS_B": (False, None), "ST": (True, True),
    "CL_1": (True, True), "CL_2": (True, True), "ROT": (True, None), "MIR_X": (True, None),
    "MIR_Y": (True, None), "ROT_KEEP": (True, False)}
REFLECTIONS = {"ROT": (-1.0, -1.0), "MIR_X": (-1.0, 1.0), "MIR_Y": (1.0, -1.0), "ROT_KEEP": (-1.0, -1.0)}
QUERY_STEPS = tuple(range(0, 100, 10))
PREFIX_STEPS = 100
DISPLACEMENT_M = 1500.0
# Rules the declaration leaves open (recorded, reported as deviations):
BS_SIGN_RULE = ("along the BS's own edge, away from the edge midpoint (toward the quadrant's "
                "corner); the opposite sign if that leaves [0.1A, 0.9A]; clip only if both fail")
CL_CLUSTER = 1   # first central cluster in generation order (routed_core.py 721-758: remote first)
CL_AXES = {"CL_1": 0, "CL_2": 1}   # translate along x / y, sign toward the central square's centre
ST_RNG_SALT = 1  # ST re-jitter stream: RandomState([seed, ST_RNG_SALT])
MATCH_EXACT_M = 60.0
PLANNERS = ("H_local", "H_central")
SUPPORT_RULES = {
    "spawn_corner": "envs/pettingzoo/relay/routed_core.py:1137-1150 (corner = randint(0, 4))",
    "spawn_grid": "envs/pettingzoo/relay/routed_core.py:1161-1191 (3x3, i outer / j inner, +-20 m)",
    "base_station": "envs/pettingzoo/relay/routed_core.py:657-674 (edge band 0.05A, along-edge [0.1A, 0.9A])",
    "remote_cluster": "envs/pettingzoo/relay/routed_core.py:721-746 (corner opposite the BS quadrant, +-0.1A, clip [0.05A, 0.95A])",
    "central_clusters": "envs/pettingzoo/relay/routed_core.py:748-758 (uniform in the central square)",
    "stations": "envs/pettingzoo/relay/energy_aware.py:340-353, 390-421 (anchor + U(+-960), clip to the 0.08A margin)",
}


# --------------------------------------------------------------------------- reset and records
@dataclass
class ResetRecord:
    seed: int
    station_rng_state: tuple
    corner: int
    jitter: np.ndarray            # [n, 2] recorded spawn-slot jitter (routed_core.py 1181-1182)
    bs_xy: np.ndarray
    stations_xy: np.ndarray
    users_xy: np.ndarray
    cluster_centres: np.ndarray


def _corner_box(raw, corner: int):
    size = min(raw.uav_start_area_size, raw.area_size / 2 - 50)
    lo, hi = 50.0, raw.area_size - size - 50.0
    x0 = lo if corner in (0, 3) else hi
    y0 = lo if corner in (0, 1) else hi
    return x0, y0, size


def slot_centres(raw, corner: int) -> np.ndarray:
    """Spawn-grid slot centres (index = slot) in ``corner`` (routed_core.py 1161-1177)."""
    x0, y0, size = _corner_box(raw, corner)
    grid = int(np.ceil(np.sqrt(raw.n_uavs)))
    cells = [(i, j) for i in range(grid) for j in range(grid)][: raw.n_uavs]
    return np.array([[x0 + size * (i + 0.5) / grid, y0 + size * (j + 0.5) / grid] for i, j in cells])


def spawn_corner(raw, xy: np.ndarray) -> int | None:
    """The corner whose slot grid holds every UAV within the +-20 m jitter, else None."""
    for corner in range(4):
        if np.all(np.abs(xy - slot_centres(raw, corner)) <= 20.0 + 1e-9):
            return corner
    return None


def reset_with_record(adapter, seed: int):
    """``adapter.reset(seed)`` recording the RandomState at the entry of the station sampler."""
    raw = adapter.env
    captured: dict[str, Any] = {}
    original = raw._init_charging_stations

    def recorder(*args, **kwargs):
        captured["state"] = raw.np_random.get_state()
        return original(*args, **kwargs)

    raw._init_charging_stations = recorder
    try:
        obs, info = adapter.reset(seed=int(seed))
    finally:
        del raw._init_charging_stations
    xy = raw.uav_positions[:, :2].copy()
    corner = spawn_corner(raw, xy)
    if corner is None or "state" not in captured:
        raise RuntimeError("reset did not produce a recognisable spawn grid / station draw")
    record = ResetRecord(int(seed), captured["state"], corner, xy - slot_centres(raw, corner),
                         raw.ground_bs_positions[:, :2].copy(),
                         raw.charging_station_positions[:, :2].copy(),
                         raw.user_positions[:, :2].copy(), raw.cluster_centers_history.copy())
    return record, obs, info


def _replay_stations(raw, rng_state) -> np.ndarray:
    """The env's own station sampler on the current raw world from ``rng_state``; RNG restored."""
    saved = raw.np_random.get_state()
    try:
        raw.np_random.set_state(rng_state)
        raw._init_charging_stations()
        return raw.charging_station_positions.copy()
    finally:
        raw.np_random.set_state(saved)


# --------------------------------------------------------------------------- geometry rules
def bs_edge(raw, xy) -> int:
    area = raw.area_size
    if xy[1] <= 0.05 * area:
        return 0
    if xy[0] >= 0.95 * area:
        return 1
    if xy[1] >= 0.95 * area:
        return 2
    if xy[0] <= 0.05 * area:
        return 3
    return -1


def moved_bs(raw, xy):
    """BS moved DISPLACEMENT_M along its own edge by ``BS_SIGN_RULE``; (new_xy, record)."""
    area, edge = raw.area_size, bs_edge(raw, xy)
    axis = 0 if edge in (0, 2) else 1
    lo, hi, mid = 0.1 * area, 0.9 * area, area / 2.0
    u = float(xy[axis])
    away = 1.0 if u >= mid else -1.0
    new = xy.copy()
    for sign in (away, -away):
        candidate = u + sign * DISPLACEMENT_M
        if lo <= candidate <= hi and (candidate >= mid) == (u >= mid):
            new[axis] = candidate
            return new, {"edge": edge, "axis": axis, "sign": sign, "clipped": False}
    new[axis] = float(np.clip(u + away * DISPLACEMENT_M, lo, hi))
    return new, {"edge": edge, "axis": axis, "sign": away, "clipped": True}


def cluster_members(raw, cluster: int) -> np.ndarray:
    """Users generated in ``cluster`` (routed_core.py 766-796: index blocks in cluster order)."""
    counts = [raw.n_users // raw.n_clusters + (1 if i < raw.n_users % raw.n_clusters else 0)
              for i in range(raw.n_clusters)]
    start = int(sum(counts[:cluster]))
    return np.arange(start, start + counts[cluster])


def reflect_xy(raw, xy, signs):
    area = raw.area_size
    out = np.array(xy, dtype=np.float64, copy=True)
    for axis, sign in enumerate(signs):
        if sign < 0:
            out[..., axis] = area - out[..., axis]
    return out


def remote_corner_of(raw, bs_xy):
    """Remote user-cluster corner for a BS centre (routed_core.py 727-738)."""
    area, centre = raw.area_size, raw.area_size / 2.0
    x = 0.95 * area if bs_xy[0] < centre else 0.05 * area
    y = 0.95 * area if bs_xy[1] < centre else 0.05 * area
    return np.array([x, y])


def support_check(raw, uav_xy, bs_xy, centres, stations, anchors) -> dict[str, Any]:
    """Per-rule membership of a world in the generator's support (``SUPPORT_RULES``)."""
    area, tol = raw.area_size, 1e-6
    corner = spawn_corner(raw, uav_xy)
    edge = bs_edge(raw, bs_xy[0])
    along = bs_xy[0][0 if edge in (0, 2) else 1] if edge >= 0 else float("nan")
    bs_ok = edge >= 0 and 0.1 * area - tol <= along <= 0.9 * area + tol
    remote = remote_corner_of(raw, bs_xy.mean(0))
    box_lo = np.clip(remote - 0.1 * area, 0.05 * area, 0.95 * area)
    box_hi = np.clip(remote + 0.1 * area, 0.05 * area, 0.95 * area)
    remote_ok = bool(np.all(centres[0] >= box_lo - tol) and np.all(centres[0] <= box_hi + tol))
    size = area * raw.central_area_ratio
    margin = (area - size) / 2.0
    central_ok = bool(np.all(centres[1:] >= margin - tol) and np.all(centres[1:] <= margin + size + tol))
    jitter, low, high = raw.charging_station_jitter_m, 0.08 * area, 0.92 * area
    station_ok = bool(np.all(stations >= np.clip(anchors - jitter, low, high) - tol)
                      and np.all(stations <= np.clip(anchors + jitter, low, high) + tol))
    rules = {"spawn_corner": corner is not None, "spawn_grid": corner is not None,
             "base_station": bool(bs_ok), "remote_cluster": remote_ok,
             "central_clusters": central_ok, "stations": station_ok}
    labels = ("SW", "SE", "NE", "NW")
    return {"tuple": {"spawn_corner": labels[corner] if corner is not None else None,
                      "bs_edge": ("S", "E", "N", "W")[edge] if edge >= 0 else None,
                      "bs_along_half": (None if edge < 0 else ("low" if along < area / 2 else "high")),
                      "remote_corner": labels[[(0.05, 0.05), (0.95, 0.05), (0.95, 0.95),
                                               (0.05, 0.95)].index(tuple(np.round(remote / area, 2)))]},
            "rules": rules, "producible": bool(all(rules.values()))}


def station_anchors(raw, bs_xy, users_xy) -> np.ndarray:
    """``_charging_station_anchor_points`` for given BS / user xy (energy_aware.py 405-421)."""
    bs_centre, service = bs_xy.mean(0), users_xy.mean(0)
    relay = 0.70 * bs_centre + 0.30 * service
    anchors = [relay, service]
    for idx in range(2, raw.max_energy_charging_stations):
        t = idx / max(1, raw.max_energy_charging_stations - 1)
        anchors.append((1.0 - t) * relay + t * service)
    return np.array(anchors[: raw.max_energy_charging_stations])


def plan_conditions(adapter, record: ResetRecord, conditions=CONDITIONS) -> dict[str, dict]:
    """Per-condition geometry fixed at reset time (applied unchanged at every query step)."""
    raw = adapter.env
    plans: dict[str, dict] = {}
    base_support = support_check(raw, raw.uav_positions[:, :2], record.bs_xy,
                                 record.cluster_centres, record.stations_xy,
                                 station_anchors(raw, record.bs_xy, record.users_xy))
    for condition in conditions:
        plan: dict[str, Any] = {"condition": condition, "consistent": DECLARED[condition][0],
                                "declared_in_support": DECLARED[condition][1], "clips": []}
        scratch = copy.deepcopy(raw)
        if condition in ("BS_A", "BS_B"):
            new, info = moved_bs(raw, record.bs_xy[0])
            plan.update(bs_xy=new, bs_move=info, bs_displacement_m=(new - record.bs_xy[0]).tolist())
            if info["clipped"]:
                plan["clips"].append("bs_along_edge")
            scratch.ground_bs_positions[0, :2] = new
            plan["stations"] = (_replay_stations(scratch, record.station_rng_state)[:, :2]
                                if condition == "BS_A" else record.stations_xy.copy())
        elif condition == "ST":
            rng = np.random.RandomState([record.seed, ST_RNG_SALT])
            plan["stations"] = _replay_stations(scratch, rng.get_state())[:, :2]
            plan["st_rng"] = [record.seed, ST_RNG_SALT]
        elif condition in CL_AXES:
            axis = CL_AXES[condition]
            size = raw.area_size * raw.central_area_ratio
            margin = (raw.area_size - size) / 2.0
            centre = record.cluster_centres[CL_CLUSTER]
            sign = 1.0 if centre[axis] < raw.area_size / 2.0 else -1.0
            target = float(np.clip(centre[axis] + sign * DISPLACEMENT_M, margin, margin + size))
            if target != centre[axis] + sign * DISPLACEMENT_M:
                plan["clips"].append("cluster_centre_central_square")
            shift = np.zeros(2)
            shift[axis] = target - centre[axis]
            plan.update(cluster=CL_CLUSTER, members=cluster_members(raw, CL_CLUSTER).tolist(),
                        shift=shift)
            _translate_cluster(scratch, plan, t=0)
            plan["stations"] = _replay_stations(scratch, record.station_rng_state)[:, :2]
        elif condition in REFLECTIONS:
            signs = REFLECTIONS[condition]
            plan["signs"] = signs
            plan["stations"] = reflect_xy(raw, record.stations_xy, signs)
            reflected = reflect_xy(raw, raw.uav_positions[:, :2], signs)
            if condition == "ROT_KEEP":
                plan.update(corner=None, spawn_xy=reflected, matching=list(range(raw.n_uavs)))
            else:
                box = _corner_box(raw, record.corner)
                centre = reflect_xy(raw, np.array(box[:2]) + box[2] / 2.0, signs)
                corner = next(c for c in range(4) if np.allclose(
                    np.array(_corner_box(raw, c)[:2]) + _corner_box(raw, c)[2] / 2.0, centre))
                spawn = np.clip(slot_centres(raw, corner) + record.jitter, 10, raw.area_size - 10)
                plan.update(corner=corner, spawn_xy=spawn, matching=match_agents(spawn, reflected))
            plan["matching_distance_m"] = [float(np.linalg.norm(plan["spawn_xy"][j] - reflected[i]))
                                           for j, i in enumerate(plan["matching"])]
            plan["exact_match"] = [d < MATCH_EXACT_M for d in plan["matching_distance_m"]]
        if condition in REFLECTIONS or condition == "ID":
            signs = REFLECTIONS.get(condition, (1.0, 1.0))
            uav_xy = plan.get("spawn_xy", raw.uav_positions[:, :2])
            bs = reflect_xy(raw, record.bs_xy, signs)
            centres = reflect_xy(raw, record.cluster_centres, signs)
            users = reflect_xy(raw, record.users_xy, signs)
        else:
            uav_xy = raw.uav_positions[:, :2]
            bs = plan.get("bs_xy", record.bs_xy[0])[None, :]
            centres, users = scratch.cluster_centers_history.copy(), scratch.user_positions[:, :2].copy()
        stations = plan.get("stations", record.stations_xy)
        plan["support"] = support_check(raw, uav_xy, bs, centres, stations,
                                        station_anchors(raw, bs, users))
        plan["original_support"] = base_support
        declared = DECLARED[condition][1]
        plan["in_support"] = bool(plan["support"]["producible"]) if declared is None else declared
        plan["station_displacement_m"] = (np.asarray(stations) - record.stations_xy).tolist()
        plans[condition] = plan
    return plans


def match_agents(spawn: np.ndarray, reflected: np.ndarray) -> list[int]:
    """m(j): the ID agent matched to constructed agent j.  Pairs closer than MATCH_EXACT_M (same
    grid cell up to jitter; unique) first, the rest by min-cost assignment (a permutation)."""
    cost = np.linalg.norm(spawn[:, None, :] - reflected[None, :, :], axis=-1)
    matching = [-1] * len(spawn)
    for j in range(len(spawn)):
        close = np.flatnonzero(cost[j] < MATCH_EXACT_M)
        if close.size == 1 and np.sum(cost[:, close[0]] < MATCH_EXACT_M) == 1:
            matching[j] = int(close[0])
    rows = [j for j in range(len(spawn)) if matching[j] < 0]
    cols = [i for i in range(len(spawn)) if i not in matching]
    for r, c in _assign(cost[np.ix_(rows, cols)]):
        matching[rows[r]] = cols[c]
    return matching


def _translate_cluster(raw, plan, t: int) -> None:
    """Translate the cluster's generated users, the waypoints anchored on it and its reference
    point; velocities re-aimed (speed kept) where exactly one of position / waypoint moved."""
    shift, cluster = np.asarray(plan["shift"]), plan["cluster"]
    members = np.zeros(raw.n_users, dtype=bool)
    members[plan["members"]] = True
    anchored = np.asarray(raw.user_cluster_assignments) == cluster
    raw.user_positions[members, :2] += shift
    raw.user_waypoints[anchored] += shift
    raw.cluster_centers_history[cluster] += shift
    raw.cluster_waypoints[cluster] += shift
    for user in np.flatnonzero(members ^ anchored):
        direction = raw.user_waypoints[user] - raw.user_positions[user, :2]
        distance, speed = np.linalg.norm(direction), np.linalg.norm(raw.user_velocities[user, :2])
        raw.user_velocities[user, :2] = direction / distance * speed if distance > 1e-6 else 0.0


def _reflect_world(raw, plan, t: int) -> None:
    signs = np.asarray(plan["signs"])
    raw.ground_bs_positions[:, :2] = reflect_xy(raw, raw.ground_bs_positions[:, :2], signs)
    raw.user_positions[:, :2] = reflect_xy(raw, raw.user_positions[:, :2], signs)
    raw.user_waypoints[:] = reflect_xy(raw, raw.user_waypoints, signs)
    raw.cluster_centers_history[:] = reflect_xy(raw, raw.cluster_centers_history, signs)
    raw.cluster_waypoints[:] = reflect_xy(raw, raw.cluster_waypoints, signs)
    raw.user_velocities[:, :2] *= signs
    raw.cluster_velocities[:] *= signs
    raw.last_actual_velocities[:, :2] *= signs
    if t == 0:
        raw.uav_positions[:, :2] = plan["spawn_xy"]
    else:
        reflected = raw.uav_positions.copy()
        reflected[:, :2] = reflect_xy(raw, reflected[:, :2], signs)
        raw.uav_positions[:] = reflected[plan["matching"]]      # xyz of the matched ID agent
    for bs_idx, (normalized, flag) in list(raw.global_bs_cache.items()):
        mapped = np.array(normalized, dtype=np.float64, copy=True)
        mapped[:2] *= signs
        raw.global_bs_cache[bs_idx] = (mapped, flag)


def rematerialise(adapter, t: int, previous_serving_sets=None):
    """Re-run the reset materialisation (t = 0) or the step's view materialisation (t > 0) on the
    current raw positions; returns (observations [n, obs] float32, state float32) via the adapter."""
    raw = adapter.env
    raw._step_communication_cache = None
    raw._relay_geometry_state = None
    if t == 0:   # pristine pre-materialisation state of the base reset (routed_core.py 2130-2171)
        raw.global_bs_cache = {}
        raw.last_global_sync_step = -1
        raw.connections = np.zeros((raw.n_uavs, raw.n_users), dtype=bool)
        raw.sinr_matrix = np.zeros((raw.n_uavs, raw.n_users))
        raw.uav_connections = np.zeros((raw.n_uavs, raw.n_uavs), dtype=bool)
        raw.uav_bs_connections = np.zeros((raw.n_uavs, raw.n_ground_bs), dtype=bool)
        raw.routing_paths = {}
        raw.handover_count = raw.ping_pong_count = 0
        raw.user_serving_uav.fill(-1)
        raw.user_serving_sets = [[] for _ in range(raw.n_users)]
        raw.serving_set_changes = raw.uav_joins_count = raw.uav_leaves_count = 0
        raw.user_handover_history = [[] for _ in range(raw.n_users)]
        raw.last_min_station_distance_before = raw._min_distances_to_charging_stations(raw.uav_positions)
        raw.last_min_station_distance_after = raw.last_min_station_distance_before.copy()
    elif previous_serving_sets is not None:
        raw.user_serving_sets = copy.deepcopy(previous_serving_sets)
    raw._update_return_energy_state()
    if t == 0:
        raw.last_energy_reward_components = raw._calculate_energy_reward_components()
    raw._update_channel_state()
    raw._update_uav_connections()
    if raw.routing_protocol == "hggr":
        raw.hop_map = raw._calculate_hop_map()
    raw._compute_routing_paths()
    if t > 0:   # user_serviced_status as set by the step (routed_core.py 1271-1278, 1352)
        served = np.zeros(raw.n_users, dtype=bool)
        for user in range(raw.n_users):
            served[user] = any(uav in raw.routing_paths and raw.routing_paths[uav][0]
                               for uav in np.flatnonzero(raw.connections[:, user]))
        raw.user_serviced_status = served
    raw.last_energy_reward_components = raw._calculate_energy_reward_components()
    raw.current_graph_potential = (raw._graph_service_potential() if raw.scenario7_reward_variant in {
        "qos_fixed_safety_graph_pbrs", "qos_fixed_safety_unbounded_graph_pbrs",
        "qos_adaptive_safety_graph_pbrs"} else 0.0)
    views = raw._update_observations_dict({agent: raw._get_observation(agent) for agent in raw.agents})
    raw.state = raw._get_state()
    return adapter._dict_to_array(views).astype(np.float32), adapter._state_array()


def construct_world(base, condition: str, *, rng_offsets: dict, t: int = 0,
                    previous_serving_sets=None, in_place: bool = False):
    """A copy of ``base`` (an adapter just after ``reset(seed)`` for t = 0, or at step t) with the
    condition's raw edits and the materialisation re-run.  ``rng_offsets``: the recorded reset
    draws and per-condition plans from ``plan_conditions``.  Returns (adapter, obs, state)."""
    adapter = base if in_place else copy.deepcopy(base)
    raw, plan = adapter.env, rng_offsets[condition]
    if condition in ("BS_A", "BS_B"):
        raw.ground_bs_positions[0, :2] = plan["bs_xy"]
        for bs_idx, (normalized, flag) in list(raw.global_bs_cache.items()):
            mapped = np.array(normalized, dtype=np.float64, copy=True)
            mapped[:2] = (plan["bs_xy"] - raw.area_size / 2.0) / raw.area_size
            raw.global_bs_cache[bs_idx] = (mapped, flag)
    elif condition in CL_AXES:
        _translate_cluster(raw, plan, t)
    elif condition in REFLECTIONS:
        _reflect_world(raw, plan, t)
    if "stations" in plan:
        raw.charging_station_positions[:, :2] = plan["stations"]
    obs, state = rematerialise(adapter, t, previous_serving_sets)
    return adapter, obs, state


# --------------------------------------------------------------------------- queries
def share_rng_memo(evaluator) -> dict:
    """deepcopy memo sharing the agent's two lock-holding helpers (untouched by ``step``)."""
    return {id(evaluator.env_state_manager): evaluator.env_state_manager,
            id(evaluator.metrics_collector): evaluator.metrics_collector}


def _digest(array) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()[:16]


def query_policy(controller: PolicyController, adapter, obs, state, t: int, previous_done, modes):
    """One proposal at decision step t from a deep copy of ``controller`` (history fixed)."""
    evaluator = controller.evaluator
    probe = copy.deepcopy(controller, share_rng_memo(evaluator))
    if t == 0:
        probe.reset()
    hidden_before = _digest(probe.evaluator.actor_hidden_np) if t > 0 else "reset"
    with preserved_rng():
        proposal = probe.propose(obs, state, t, np.asarray(previous_done).copy(), modes.copy())
    timer = int(probe.evaluator.env_timers.get(0, -1))
    fresh = bool(np.array_equal(probe.evaluator._central_snapshot_states[0], state.astype(np.float64))
                 and np.array_equal(probe.evaluator._central_snapshot_obs[0], obs))
    if timer != 0 or not fresh:
        raise RuntimeError(f"query at t={t} is not a fresh decision step (timer {timer}, fresh {fresh})")
    decision = apply_feedback_params(obs, proposal, modes.copy(), PRODUCTION_PARAMS)
    raw = adapter.env
    guarded = np.array([bool(raw.enable_backhaul_action_guard and raw.reward_type == "load_balance"
                             and raw.routing_paths and raw._is_backhaul_guarded_uav(i))
                        for i in range(raw.n_uavs)])
    return {"proposal": proposal, "modes": decision.modes.copy(), "guard": guarded,
            "hidden": hidden_before}


def planner_actions(adapter, obs, state, name: str):
    """H_local / H_central proposal at t = 0 on a constructed world (fresh controller)."""
    spec = B01Spec()
    params = heuristic_params("Hlocal" if name == "H_local" else "H1", spec)
    controller = HeuristicController(params, adapter)
    controller.reset()
    modes = np.zeros(obs.shape[0], dtype=bool)
    try:
        proposal = controller.propose(obs, state, 0, np.ones(1, dtype=bool), modes)
    except UnobservedRegime:
        return np.full((obs.shape[0], 4), np.nan, dtype=np.float32), modes
    decision = apply_feedback_params(obs, proposal, modes, PRODUCTION_PARAMS)
    return np.asarray(proposal, dtype=np.float32), decision.modes.copy()


def _users_in_access_range(raw) -> int:
    return int((np.max(raw.sinr_matrix, axis=0) >= raw.min_sinr).sum())


@dataclass(frozen=True)
class ProbeTask:
    seed: int
    checkpoint_dir: str
    threads: int = 2
    node_trace: str | None = None
    log_dir: str | None = None


def _learner(task: ProbeTask, device):
    checkpoint_dir = Path(task.checkpoint_dir)
    record = json.loads((checkpoint_dir / "record.json").read_text(encoding="utf-8"))
    policy_seed = int(record["training_seed"])
    world = WorldTask(controller="L", seed=task.seed, params=PRODUCTION_PARAMS, horizon=HORIZON,
                      policy_seed=policy_seed, threads=task.threads,
                      checkpoint=str(checkpoint_dir / record["agent_pt"]),
                      checkpoint_record=str(checkpoint_dir / "record.json"))
    config = learner_eval_config(make_eval_config(HORIZON, policy_seed), record)
    return world, record, config


def probe_world(task: ProbeTask) -> dict[str, Any]:
    """Block 1 for one world: ID prefix of PREFIX_STEPS steps with queries at QUERY_STEPS."""
    import tempfile
    started = time.perf_counter()
    torch.set_num_threads(int(task.threads))
    device = torch.device("cpu")
    world, record, config = _learner(task, device)
    n, c = config.n_agents, len(CONDITIONS)
    out = {key: np.zeros(shape, dtype) for key, shape, dtype in (
        ("proposals", (len(QUERY_STEPS), c, n, 4), np.float32),
        ("modes", (len(QUERY_STEPS), c, n), bool), ("guard", (len(QUERY_STEPS), c, n), bool),
        ("planner_proposals", (len(PLANNERS), c, n, 4), np.float32),
        ("planner_modes", (len(PLANNERS), c, n), bool), ("id_xyz", (PREFIX_STEPS, n, 3), np.float32))}
    diagnostics: dict[str, Any] = {"id_construct_max_abs": {}, "id_query_repeat_exact": {},
                                   "hidden_digest": {}, "timings_s": {}}
    with tempfile.TemporaryDirectory(prefix="b04-probe-", dir=task.log_dir) as log_dir:
        agent, identity = load_learner_policy(world, record, config, device, log_dir)
        with preserved_rng():
            seed_everything(int(world.policy_seed), device)
            evaluator = HMASDAgent(copy.deepcopy(config), log_dir=log_dir, device=device)
            _sync_agent(agent, evaluator)
            evaluator.train(False)
            if initialization_fingerprint(evaluator) != identity["policy_fingerprint"]:
                raise RuntimeError("evaluator policy differs from restored checkpoint")
            controller = PolicyController(evaluator, deterministic=True)
            adapter = make_env(config, task.seed)
            controller.reset()
            rec, obs, info = reset_with_record(adapter, task.seed)
            obs = np.asarray(obs, dtype=np.float32)
            state = np.asarray(info["state"], dtype=np.float32)
            access = _users_in_access_range(adapter.env)
            began = time.perf_counter()
            plans = plan_conditions(adapter, rec)
            diagnostics["timings_s"]["plan_conditions"] = time.perf_counter() - began
            began = time.perf_counter()
            _, id_obs, id_state = construct_world(adapter, "ID", rng_offsets=plans, t=0)
            diagnostics["timings_s"]["construct_world_ID_t0"] = time.perf_counter() - began
            gate_a = bool(np.array_equal(id_obs, obs) and np.array_equal(id_state, state)
                          and id_obs.dtype == obs.dtype and id_state.dtype == state.dtype)
            previous_done = np.ones(1, dtype=bool)
            modes = np.zeros(n, dtype=bool)
            previous_sets = None
            for step in range(PREFIX_STEPS):
                out["id_xyz"][step] = own_positions(obs)
                if step in QUERY_STEPS:
                    q = QUERY_STEPS.index(step)
                    hidden = set()
                    for k, condition in enumerate(CONDITIONS):
                        began = time.perf_counter()
                        built, c_obs, c_state = construct_world(
                            adapter, condition, rng_offsets=plans, t=step,
                            previous_serving_sets=previous_sets)
                        result = query_policy(controller, built, c_obs, c_state, step,
                                              previous_done, modes)
                        diagnostics["timings_s"].setdefault("condition_query", []).append(
                            time.perf_counter() - began)
                        out["proposals"][q, k] = result["proposal"]
                        out["modes"][q, k] = result["modes"]
                        out["guard"][q, k] = result["guard"]
                        hidden.add(result["hidden"])
                        if condition == "ID":
                            diagnostics["id_construct_max_abs"][str(step)] = [
                                float(np.max(np.abs(c_obs - obs))), float(np.max(np.abs(c_state - state)))]
                            id_proposal = result["proposal"]
                        if step == 0:
                            for p, name in enumerate(PLANNERS):
                                out["planner_proposals"][p, k], out["planner_modes"][p, k] = \
                                    planner_actions(built, c_obs, c_state, name)
                    diagnostics["hidden_digest"][str(step)] = sorted(hidden)
                began = time.perf_counter()
                proposal = controller.propose(obs, state, step, previous_done, modes.copy())
                if step in QUERY_STEPS:
                    diagnostics["id_query_repeat_exact"][str(step)] = bool(
                        np.array_equal(proposal, id_proposal))
                decision = apply_feedback_params(obs, proposal, modes, PRODUCTION_PARAMS)
                modes = decision.modes
                if step + 1 in QUERY_STEPS:
                    previous_sets = copy.deepcopy(adapter.env.user_serving_sets)
                obs, _, terminated, truncated, info = adapter.step(decision.submitted_actions)
                obs = np.asarray(obs, dtype=np.float32)
                state = np.asarray(info["next_state"], dtype=np.float32)
                previous_done[:] = terminated or truncated
                diagnostics["timings_s"].setdefault("id_step", []).append(time.perf_counter() - began)
            adapter.close()
    trace = trace_deviation(task.node_trace, task.seed, out["id_xyz"]) if task.node_trace else None
    conditions = {name: _jsonable(plan) for name, plan in plans.items()}
    return {"seed": task.seed, "arrays": out, "gate_a": gate_a, "trace": trace,
            "users_in_access_range_t0": access, "conditions": conditions,
            "identity": identity, "diagnostics": diagnostics,
            "wall_seconds": time.perf_counter() - started}


def trace_deviation(path: str, seed: int, xyz: np.ndarray) -> dict[str, Any]:
    """Max |local ID own_xyz - node trace own_xyz| over the first len(xyz) steps (float32)."""
    archive = np.load(path)
    for key in archive.files:
        if key.endswith("_seed") and int(archive[key]) == int(seed):
            node = np.asarray(archive[key[: -len("seed")] + "own_xyz"], dtype=np.float32)[: len(xyz)]
            return {"max_abs_m": float(np.max(np.abs(node - xyz))), "steps": int(len(node))}
    return {"max_abs_m": None, "steps": 0}


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


# --------------------------------------------------------------------------- Block 2
class ConstructedResetEnv:
    """Adapter wrapper whose ``reset(seed)`` returns the constructed ``condition`` world; step and
    close delegate (``raw_guard_env`` reaches the raw env through ``.env``)."""

    def __init__(self, adapter, condition: str = "ROT"):
        self.env = adapter
        self.condition = condition
        self.construction: dict[str, Any] | None = None

    def reset(self, seed=None, options=None):
        record, _, info = reset_with_record(self.env, int(seed))
        plans = plan_conditions(self.env, record, conditions=(self.condition,))
        _, obs, state = construct_world(self.env, self.condition, rng_offsets=plans, t=0, in_place=True)
        self.construction = _jsonable(plans[self.condition])
        return obs, {"state": state}

    def step(self, actions):
        return self.env.step(actions)

    def close(self):
        self.env.close()


def rotated_episode(task: WorldTask, condition: str = "ROT") -> dict[str, Any]:
    """B01 ``evaluate_task`` (controller L, deterministic) on the constructed world."""
    holder: dict[str, ConstructedResetEnv] = {}

    def factory(config, seed):
        holder["env"] = ConstructedResetEnv(make_env(config, seed), condition)
        return holder["env"]

    with mock.patch.object(b01_evaluation, "make_env", factory):
        result = b01_evaluation.evaluate_task(task)
    result["construction"] = holder["env"].construction
    result.pop("arrays", None)
    return result


def paired_rotation(rotated_rows, recorded_panel: dict) -> dict[str, Any]:
    """Per-world (constructed - recorded) qos_per_step and raw_native_J with paired SE."""
    recorded = {int(row["seed"]): row for row in recorded_panel["worlds"]}
    pairs = []
    for row in rotated_rows:
        base = recorded[int(row["seed"])]
        pairs.append({"seed": int(row["seed"]), "in_support": row.get("in_support"),
                      **{f"{key}_{side}": float(src[key]) for key in ("qos_per_step", "raw_native_J")
                         for side, src in (("original", base), ("rotated", row))}})
    summary = {}
    for key in ("qos_per_step", "raw_native_J"):
        diff = np.array([p[f"{key}_rotated"] - p[f"{key}_original"] for p in pairs])
        for p, d in zip(pairs, diff):
            p[f"{key}_difference"] = float(d)
        summary[key] = {"n": int(diff.size), "mean_paired_difference": float(diff.mean()),
                        "paired_se": float(diff.std(ddof=1) / np.sqrt(diff.size)) if diff.size > 1 else None}
    return {"pairs": pairs, "summary": summary}


# --------------------------------------------------------------------------- capacity curve
def capacity_vs_distance(config, seed: int = 955001, distances=None) -> dict[str, Any]:
    """Relaxed / actual access capacity and relaxed UAV->BS capacity against horizontal distance,
    from the env's own functions on world ``seed`` at t = 0 (UAV 0 moved; others at spawn)."""
    distances = np.arange(100.0, 8000.0 + 1e-9, 100.0) if distances is None else np.asarray(distances)
    adapter = make_env(config, seed)
    try:
        adapter.reset(seed=int(seed))
        raw = adapter.env
        user, uav = 0, 0
        z = float(raw.uav_positions[uav, 2])
        access_bandwidth = raw.bandwidth / max(raw.n_uavs, 1) if raw.use_fdma else raw.bandwidth
        candidate = access_bandwidth / max(1, int(np.ceil(raw.n_users / max(raw.n_uavs, 1))))
        centre = np.full(2, raw.area_size / 2.0)
        rows = {"access": [], "uav_to_bs": []}
        for label, anchor in (("access", raw.user_positions[user, :2]), ("uav_to_bs", raw.ground_bs_positions[0, :2])):
            direction = (centre - anchor) / np.linalg.norm(centre - anchor)
            for distance in distances:
                raw.uav_positions[uav] = [*(anchor + distance * direction), z]
                raw._step_communication_cache = None
                raw._relay_geometry_state = None
                if label == "access":
                    loss = raw._compute_air_to_ground_path_loss(raw.uav_positions[uav], raw.user_positions[user])
                    sinr = raw._compute_uav_to_user_sinr(uav, user, raw.tx_power - loss)
                    rows[label].append({"distance_m": float(distance), "sinr_db": float(sinr),
                                        "relaxed_bps": raw._access_capacity_bps(uav, user, candidate, True, can_reuse_sinr=False),
                                        "actual_bps": raw._access_capacity_bps(uav, user, candidate, False, can_reuse_sinr=False)})
                else:
                    loss = raw._compute_air_to_ground_path_loss(raw.uav_positions[uav], raw.ground_bs_positions[0])
                    sinr = raw._compute_link_sinr("uav", uav, "ground_bs", 0, raw.tx_power - loss)
                    rows[label].append({"distance_m": float(distance), "sinr_db": float(sinr),
                                        "relaxed_bps": raw._relaxed_backhaul_capacity_bps(uav, "ground_bs", 0),
                                        "actual_bps": float(raw._get_link_capacity("uav", uav, "ground_bs", 0))})
        return {"seed": int(seed), "t": 0, "uav": uav, "user": user, "uav_z_m": z,
                "sweep": "UAV 0 on the line from the anchor toward the arena centre; other UAVs at their t = 0 positions",
                "other_uav_xyz": _jsonable(np.delete(raw.uav_positions, uav, axis=0)),
                "config": {"candidate_bandwidth_hz": float(candidate), "access_bandwidth_hz": float(access_bandwidth),
                           "bandwidth_hz": float(raw.bandwidth), "use_fdma": bool(raw.use_fdma),
                           "min_sinr_db": float(raw.min_sinr), "tx_power_dbm": float(raw.tx_power),
                           "noise_power_dbm": float(raw.noise_power), "carrier_frequency": float(raw.carrier_frequency),
                           "interference_radius_m": float(raw._compute_interference_radius()),
                           "mcs_max_efficiency": float(max(e for _, e in raw.mcs_table)),
                           "environment_type": str(getattr(raw, "environment_type", "urban"))},
                "rows": _jsonable(rows)}
    finally:
        adapter.close()
