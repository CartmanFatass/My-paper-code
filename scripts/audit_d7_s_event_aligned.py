"""D7.S event-aligned source audit.

Contract (frozen, verbatim authority for every semantic choice):
    docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md (FROZEN 2026-07-26)
    supersedes R2, which superseded D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md.
    R2 kept n_select=2/n_eval=2, shared-prefix cloning and the selection
    diagnostic; R3 replaces prefix RECONSTRUCTION with direct capture off the
    live certified environment, replaces the narrow state hash with a
    complete-state fingerprint, and restates condition 1 as 1A/1B/1C.
G2 binding reference (CONSTRUCTIVE_CHARGE_ROTATION, LEAVE/REJOIN lifecycle,
heldout_low profile):
    docs/research/designs/UAV_CHARGE_ROTATION_ROSTER_G2.md
Ruling behind the contract's exact wording:
    docs/external-review/rounds/20260726_d7_s_event_aligned_contract_freeze/21_PRO_OPEN_RAW.md

Supersedes the Part B realization of D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md.
Evaluation-only: no training, no policy, no learned checkpoint. Every arm is a
scripted source control.

This module is organized as a pure, independently testable logic layer (event
detection and certification, legal-SET construction, window-local safety-event
latching, the primary-G analyzer, the ten-branch decision, seed derivation, and
the nested/rerun bootstrap) followed by a thin orchestration layer that wires
the section 9 topology-pinning procedure to a real `UAVEnergyAwareRelayEnv`
instance. The pure layer is what the focused test suite exercises and is what
the ten branches, the bootstrap and the safety-event latching are actually
proved against.

Honest scope of `main()` (updated 2026-07-26, R2): it IS wired to real
episodes. It builds the section 9 pinned topology, rolls real prefixes to find
and certify the joint event, materializes the canonical `EventSnapshot`, forks
every continuation from clones of it, and assembles the bootstrap result. The
earlier note here -- that `main()` ran no episodes -- described the state
before the driver was wired and is retired.

Known repository fact, load-bearing (see
`docs/research/cdc/EVIDENCE_NOTES/20260726_D7_S_PREFIX_REPLAY_IS_NOT_FIXED_HISTORY.md`):
two FRESHLY CONSTRUCTED environments carrying the same episode seed do NOT
share a user population -- the user layout is fixed by construction-time state
that `reset(seed=)` does not re-derive, and it differs by kilometres between
constructions. `compute_state_hash` covers no user, cluster or channel state,
so it cannot detect this. That is precisely why the R2 shared-prefix
realization is a correctness fix and not merely an optimization: only one env
construction per event means all arms of that event share one user world.
Never reintroduce a per-replicate `replay_prefix` call.

Repository-fact note (implementer, 2026-07-26): the environment has no literal
`ACTIVE` / `CHARGE_ABSENT` / `TERMINAL` state machine or `CONSTRUCTIVE_CHARGE_
ROTATION` controller class -- G2's lifecycle vocabulary is a design-level
description that this audit realizes directly against the raw scenario-7
surface (`uav_charging`, `uav_dock_requests`, `uav_battery_ratios`,
`station_occupancy`, `station_queue_lengths`). A UAV is ACTIVE (airborne, duty-
holding) whenever it is not currently charging; it is CHARGE_ABSENT for the
steps in which `uav_charging` is True. LEAVE is the rising edge of
`uav_charging`; REJOIN is realized here as the controller releasing its dock
request once the battery ratio reaches `REJOIN_BATTERY_RATIO = 0.80` (the
environment's own charging physics keeps charging a docked UAV toward 1.0 --
G2's 0.80 rejoin point is a scripted-controller decision, not an environment
field, exactly as it is for the registered G2 roster).
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

CONTRACT_PATH = "docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md"

# DO NOT change CONTRACT_ID with the contract path. It is an input to
# `stream_seed`, so every registered continuation stream in the audit derives
# from it; the R2 amendment states explicitly that `stream_seed` semantics are
# unchanged. Renaming this would silently redraw every continuation RNG stream
# while every other registered quantity kept its name.
CONTRACT_ID = "D7_S_EVENT_ALIGNED_SOURCE_AUDIT"

# --- section 0: environment instance ----------------------------------------
PRESET = "S7-S3"
EPISODE_STEPS = 1500
HELDOUT_LOW = np.array([0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80])
REJOIN_BATTERY_RATIO = 0.80

# --- sections 1/2/3: estimand, event window, horizons -----------------------
DELTA = 10
X_STABLE_DISPLACEMENT_M = 50.0
Y_FLEX_STEPS = 10
Z_FLEX_TRANSIT_STEPS = 139
H_STABLE = 139
H_FLEX = 550
H_DIAGNOSTIC = EPISODE_STEPS
T_E_MAX = EPISODE_STEPS - H_FLEX  # 950, section 2 eligibility deadline

# --- section 5: calibration --------------------------------------------------
N_CALIBRATION_EPISODES = 8
N_AUDIT_EPISODES = 8

# --- section 8: replicates, seeds, bootstrap, equivalence -------------------
# R2 (2026-07-26): the scientific floor, not a tuning choice. n_select=1 is
# inadmissible -- the bootstrap reruns the argmax inside every iteration, so a
# singleton selection array fixes the winner across all inner iterations and
# selection-uncertainty propagation goes algebraically inert, which changes the
# estimand and errs in the claim-favouring direction on the stable limb.
N_SELECT = 2
N_EVAL = 2
BOOTSTRAP_SEED = 2026072601
BOOTSTRAP_ITERS = 10000
EQUIVALENCE_DELTA = 0.05
EVAL_SHARED_CANDIDATE_TOKEN = "paired"
MATERIALITY_COEFFICIENT = 0.10  # section 8: T_stable = U*_stable + 0.10*B_stable,
                                 # T_flex = U*_flex - 0.10*B_flex

# --- section 9: topology population -----------------------------------------
TOPOLOGY_SEED_DEV = 20260725
TOPOLOGY_SEEDS_INITIAL = tuple(range(20260726, 20260734))
TOPOLOGY_SEEDS_EXPANSION = tuple(range(20260734, 20260742))
MIN_SUPPORT_TOPOLOGIES = 6
MIN_SUPPORT_EPISODES_PER_TOPOLOGY = 4

# --- exclusion-reason vocabulary (section 2) --------------------------------
EXCLUDE_CENSORED = "censored_t_e_gt_950"
EXCLUDE_QUEUE_OR_OCCUPIED = "queue_or_occupied_station"
EXCLUDE_EMERGENCY = "emergency_cutoff_or_depletion"
EXCLUDE_TEMP_FAILURE = "temporary_failure"
EXCLUDE_OFF_SCHEDULE = "not_from_constructive_schedule"
EXCLUDE_EMPTY_SET_ALT = "no_legal_set_alternative"

# --- Q-E2 per-topology rejection-reason reporting vocabulary ---------------
# Task-brief-mandated reporting keys, rolled up per topology from the SAME
# eligibility/certification reasons the section-2 predicates above already
# compute -- never a re-derivation of any predicate, only a relabeling of an
# outcome those functions already decided.
REJECT_CENSORED = "censored_after_950"
REJECT_STATION_CONTENTION = "station_contention"
REJECT_CUTOFF_OR_DEPLETION = "cutoff_or_depletion_path"
REJECT_TEMPORARY_FAILURE = "temporary_failure"
REJECT_OFF_SCHEDULE = "off_schedule"
REJECT_NO_STABLE_INCUMBENT = "no_stable_incumbent"
REJECT_NO_FLEX_SURVIVOR = "no_flex_survivor"
REJECT_EMPTY_LEGAL_SET = "empty_legal_set"

REJECTION_REASON_KEYS = (
    REJECT_CENSORED, REJECT_STATION_CONTENTION, REJECT_CUTOFF_OR_DEPLETION,
    REJECT_TEMPORARY_FAILURE, REJECT_OFF_SCHEDULE, REJECT_NO_STABLE_INCUMBENT,
    REJECT_NO_FLEX_SURVIVOR, REJECT_EMPTY_LEGAL_SET,
)

_ELIGIBILITY_REJECTION_MAP = {
    EXCLUDE_CENSORED: REJECT_CENSORED,
    EXCLUDE_QUEUE_OR_OCCUPIED: REJECT_STATION_CONTENTION,
    EXCLUDE_EMERGENCY: REJECT_CUTOFF_OR_DEPLETION,
    EXCLUDE_TEMP_FAILURE: REJECT_TEMPORARY_FAILURE,
    EXCLUDE_OFF_SCHEDULE: REJECT_OFF_SCHEDULE,
}


def map_rejection_reasons(*, eligibility_reasons=(), stable_ok: bool = True,
                           stable_reasons=(), flex_ok: bool = True,
                           flex_reasons=()) -> set:
    """Maps the ALREADY-COMPUTED `check_leave_eligibility`/`certify_stable`/
    `certify_flex` reason strings onto the per-topology reporting vocabulary
    above -- never re-derives any predicate, only relabels an outcome those
    functions already decided. A LEAVE that fails eligibility never reaches
    certification (mirrors `roll_prefix_and_find_event`'s own short-circuit),
    so `eligibility_reasons` alone decides the mapping whenever it is
    non-empty. Past eligibility, a single LEAVE can land in more than one
    bucket at once -- e.g. a flex vacancy that is BOTH uncovered
    (no_flex_survivor) and has an empty legal-SET alternative
    (empty_legal_set, Q-C4: the empty-alternative-set predicate applies to
    BOTH limbs)."""
    mapped: set = set()
    for r in eligibility_reasons:
        if r in _ELIGIBILITY_REJECTION_MAP:
            mapped.add(_ELIGIBILITY_REJECTION_MAP[r])
    if eligibility_reasons:
        return mapped
    if not stable_ok:
        mapped.add(REJECT_NO_STABLE_INCUMBENT)
        if EXCLUDE_EMPTY_SET_ALT in stable_reasons:
            mapped.add(REJECT_EMPTY_LEGAL_SET)
    if not flex_ok:
        if "no_covering_survivor" in flex_reasons:
            mapped.add(REJECT_NO_FLEX_SURVIVOR)
        if EXCLUDE_EMPTY_SET_ALT in flex_reasons:
            mapped.add(REJECT_EMPTY_LEGAL_SET)
    return mapped


# =============================================================================
# Section 8 / Q-I2 -- stable 64-bit stream seed derivation
# =============================================================================

def stream_seed(*, topology_seed, block, episode_seed, limb, event_index,
                 candidate_target_id, phase, replicate_index,
                 contract_id: str = CONTRACT_ID) -> int:
    """The nine-field stable hash the contract freezes, mapped to a 64-bit seed.

    `candidate_target_id` is the phase's disjointness lever. During
    `phase="select"` it is the candidate z's own id, so every candidate gets
    an independent selection stream. During `phase="evaluate"` callers must
    pass the fixed sentinel `EVAL_SHARED_CANDIDATE_TOKEN` so KEEP and the
    selected SET land on the identical continuation seed per replicate index
    -- the CRN pairing the contract requires ("SET and KEEP use the same
    eight continuation base streams"). Selection and evaluation namespaces
    are disjoint because `phase` is itself part of the hashed key.
    """
    fields = (
        str(contract_id), str(topology_seed), str(block), str(episode_seed),
        str(limb), str(event_index), str(candidate_target_id), str(phase),
        str(replicate_index),
    )
    digest = hashlib.sha256("|".join(fields).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


# =============================================================================
# Section 9 -- topology pinning
# =============================================================================

def coordinate_hash(ground_bs: np.ndarray, charging_stations: np.ndarray) -> str:
    buf = (np.asarray(ground_bs, dtype=float).tobytes()
           + np.asarray(charging_stations, dtype=float).tobytes())
    return hashlib.sha256(buf).hexdigest()


class TopologyMismatchError(RuntimeError):
    """Raised when a restored topology's coordinate hash does not match the
    recorded template hash. Never repaired -- the run is invalid (branch 1)."""


TOPOLOGY_PROCEDURE_VERSION = "d7s_event_aligned_v1"


def build_topology_template(config, *, topology_seed: int, energy_stage: str = "S3"):
    """Steps 1-2 of the section 9 pinning procedure: construct once under the
    topology seed and record coordinates + their hash.

    Repository-fact correction (measured 2026-07-26): `_init_ground_bs` and
    `_init_charging_stations` draw from `self.np_random`, but that stream is
    NOT a reproducible function of `topology_seed` on its own. Construction
    seeds it from `RandomState(None)` -- unseeded OS entropy,
    `scenario_base.py:328`, since `seed_val` defaults to `None` and no seed
    kwarg is passed to `__init__` here -- before any topology seed is known.
    `env.reset(seed=...)` only reseeds `np_random` and reruns user/UAV/
    channel initialization; Scenario 7's own `reset` reruns
    `_init_charging_stations()` (never `_init_ground_bs()`) automatically.
    So `env.reset(seed=topology_seed)` followed by explicit
    `_init_ground_bs()`/`_init_charging_stations()` calls (the prior
    approach) still depends on exactly how many draws `reset()`'s other
    initialization consumed first -- measured: three different coordinate
    hashes from three calls with the identical `topology_seed`.

    The fix substitutes a PRIVATE `RandomState` bound ONLY to
    `topology_seed`, assigned immediately before the two init calls, so the
    topology draw is a pure function of `topology_seed` regardless of what
    else ever touches `env.np_random` before or after. `RandomState` (not
    `default_rng`) is used because the two init methods call
    `.randint`/`.uniform`/`.multivariate_normal`/`.choice`, an API
    `default_rng`'s `Generator` does not fully implement (no `.randint`).
    """
    from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv

    env = UAVEnergyAwareRelayEnv(config=config, energy_stage=energy_stage)
    env.np_random = np.random.RandomState(int(topology_seed))
    env._init_ground_bs()
    env._init_charging_stations()
    coords = {
        "ground_bs": np.asarray(env.ground_bs_positions, dtype=float).copy(),
        "charging_stations": np.asarray(env.charging_station_positions, dtype=float).copy(),
    }
    return coords, coordinate_hash(coords["ground_bs"], coords["charging_stations"])


def classify_bs_quadrant(ground_bs, area_size: float) -> str:
    """Ruling 2026-07-27 (Q3(a), "Scope of the eight topologies"): the eight
    registered topology seeds cover only three of the four BS-quadrant
    classes, and topology records must expose that composition -- never
    rebalance or reselect seeds to fix it, only make it visible.

    Mirrors, exactly, the quadrant test `_generate_forced_relay_cluster_positions`
    (`envs/pettingzoo/scenario_base.py`) uses to pick the remote-cluster
    corner from the mean ground-BS position: this is not an independent
    quadrant definition, it is the same four-way branch, including its tie
    fold-through (any tie on the area center lands in the same branch that
    env's own trailing `else` does), so a topology record's `bs_quadrant`
    always names the corner that topology's episodes actually draw remote
    users toward."""
    bs = np.asarray(ground_bs, dtype=float)
    if bs.size == 0:
        return "no_ground_bs"
    bs_center = np.mean(bs[:, :2], axis=0)
    area_center = float(area_size) / 2.0
    if bs_center[0] < area_center and bs_center[1] < area_center:
        return "bs_bottom_left"
    if bs_center[0] > area_center and bs_center[1] < area_center:
        return "bs_bottom_right"
    if bs_center[0] < area_center and bs_center[1] > area_center:
        return "bs_top_left"
    return "bs_top_right"


def build_topology_record(coords: dict, coord_hash: str, *, topology_seed: int,
                           config=None) -> dict:
    """Section 9's mandatory per-topology record: coordinates, canonical
    hash, topology seed, reinitialization procedure version, and (ruling
    2026-07-27) the BS-quadrant class this topology's ground-BS layout
    belongs to, so the eventual paper can report quadrant composition across
    the registered topology set. Exposure only -- this field must never
    become an input to reselecting or rebalancing the frozen topology seed
    list.

    `area_size` is read the same way `UAVEnergyAwareRelayEnv` itself reads it
    (`getattr(config, 'area_size', 2500)`, `scenario_base.py:159`), so the
    quadrant classification agrees with the geometry the real environment
    used to build this topology's coordinates."""
    area_size = float(getattr(config, "area_size", 2500))
    return {
        "topology_seed": int(topology_seed),
        "ground_bs": [[float(v) for v in row] for row in coords["ground_bs"]],
        "charging_stations": [[float(v) for v in row] for row in coords["charging_stations"]],
        "coordinate_hash": coord_hash,
        "procedure_version": TOPOLOGY_PROCEDURE_VERSION,
        "bs_quadrant": classify_bs_quadrant(coords["ground_bs"], area_size),
    }


def write_topology_record(out_dir, record: dict) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"topology_{record['topology_seed']}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=2)
    return path


def build_pinned_env(config, *, episode_seed: int, coords: dict, coord_hash: str,
                      energy_stage: str = "S3", user_world_seed: Optional[int] = None):
    """Steps 3-8 of the section 9 pinning procedure, in the load-bearing order:
    fresh env, reset with the EPISODE seed, restore the recorded coordinates
    only AFTER that reset (Scenario 7's reset calls `_init_charging_stations`,
    so restoring before it is insufficient), rebuild channel/routing state,
    assert the hash, and only THEN derive the user world from its registered
    seed.

    Step 8 (R3 section E) must follow the hash assert, not precede it. The user
    layout is a function of the ground-BS geometry as well as the RNG stream, so
    deriving it before the topology is proven pinned would reproduce nothing:
    the same `user_world_seed` against two different BS layouts gives two
    different worlds. Passing `user_world_seed=None` keeps the pre-R3 behaviour,
    where the world comes from construction-time state and no provenance can be
    claimed for it."""
    from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv

    env = UAVEnergyAwareRelayEnv(config=config, energy_stage=energy_stage)
    env.reset(seed=int(episode_seed))                       # step 4
    env.ground_bs_positions = coords["ground_bs"].copy()     # step 5 (no RNG consumed)
    env.charging_station_positions = coords["charging_stations"].copy()
    actual_hash = coordinate_hash(env.ground_bs_positions,    # step 7, moved ahead of step 6
                                   env.charging_station_positions)
    if actual_hash != coord_hash:
        raise TopologyMismatchError(
            f"topology hash mismatch: expected {coord_hash}, got {actual_hash}"
        )
    # Reproducibility needs BOTH halves: the registered seed AND a pinned
    # topology, because the user world is a function of the BS quadrant too.
    # Recording the proven hash here is what lets `episode_world_fingerprint`
    # witness the second half instead of assuming it.
    env.pinned_coordinate_hash = actual_hash
    # Step 6 runs exactly ONCE, and after the world is final. `coordinate_hash`
    # reads only the two coordinate arrays, so the assert never needed the
    # channel rebuild ahead of it. Rebuilding before step 8 would rebuild
    # against a user world step 8 is about to discard, and
    # `_update_uav_connections` ACCUMULATES lifecycle counters -- a second pass
    # books the world swap as ~18 UAV "leaves" that never happened, which then
    # travel into the include-by-default state fingerprint.
    if user_world_seed is not None:                           # step 8
        env.regenerate_user_world(user_world_seed=int(user_world_seed))
    else:
        env._update_channel_state()                          # step 6
        env._update_uav_connections()
        env._compute_routing_paths()
    return env


# =============================================================================
# Section 8 Q-I2 -- fixed-history prefix replay
# =============================================================================

class PrefixReplayMismatchError(RuntimeError):
    """An equality failure invalidates the pair; it is never repaired."""


def compute_state_hash(snapshot: dict) -> str:
    """Hash over positions, battery, charging state, station/queue state, duty
    map and lifecycle mask -- the exact fixed-history surface the contract
    requires to be asserted equal before forking a replicate continuation."""
    parts: list[bytes] = []
    array_keys = ("positions", "battery_ratios", "charging_mask",
                  "station_occupancy", "station_queue", "lifecycle_mask")
    for key in array_keys:
        arr = np.asarray(snapshot.get(key, []), dtype=float)
        parts.append(key.encode("utf-8"))
        parts.append(str(arr.shape).encode("utf-8"))
        parts.append(arr.tobytes())
    duty_items = tuple(sorted(dict(snapshot.get("duty_map", {})).items()))
    parts.append(b"duty_map")
    parts.append(repr(duty_items).encode("utf-8"))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def assert_state_hash_equal(hash_a: str, hash_b: str, *, context: str = "") -> None:
    if hash_a != hash_b:
        suffix = f": {context}" if context else ""
        raise PrefixReplayMismatchError(f"prefix replay state hash mismatch{suffix}")


# =============================================================================
# Section 2 -- event detection, eligibility, certification
# =============================================================================

def check_leave_eligibility(cand: dict, *, t_e: int) -> list[str]:
    """Section 2 complete-case eligibility plus the planned-event exclusions
    (ruling Q-E1/Q-E2). `station_occupancy_excluding_self` and
    `station_queue_length` describe contention from OTHER UAVs at the moment
    of capture -- the environment's own `station_occupancy` counts the
    capturing UAV itself, which would spuriously exclude every LEAVE if used
    directly, so callers must supply occupancy net of the capturing UAV."""
    reasons: list[str] = []
    if t_e > T_E_MAX:
        reasons.append(EXCLUDE_CENSORED)
    if cand.get("station_occupancy_excluding_self", 0) > 0 or cand.get(
        "station_queue_length", 0
    ) > 0:
        reasons.append(EXCLUDE_QUEUE_OR_OCCUPIED)
    if cand.get("cutoff_at_leave", False) or cand.get("depletion_at_leave", False):
        reasons.append(EXCLUDE_EMERGENCY)
    if cand.get("temporary_failure", False):
        reasons.append(EXCLUDE_TEMP_FAILURE)
    if cand.get("schedule_identity") != "constructive_mixed":
        reasons.append(EXCLUDE_OFF_SCHEDULE)
    return reasons


def certify_stable(*, active: bool, has_valid_incumbent: bool,
                    future_target_displacement_m: float,
                    scheduled_to_leave_within_delta: bool,
                    has_legal_set_alternative: bool) -> tuple[bool, list[str]]:
    """Section 2 stable certification, all four predicates required."""
    reasons: list[str] = []
    if not (active and has_valid_incumbent):
        reasons.append("no_valid_incumbent")
    if future_target_displacement_m > X_STABLE_DISPLACEMENT_M:
        reasons.append("displacement_exceeds_X")
    if scheduled_to_leave_within_delta:
        reasons.append("scheduled_to_leave_within_delta")
    if not has_legal_set_alternative:
        reasons.append(EXCLUDE_EMPTY_SET_ALT)
    return (len(reasons) == 0, reasons)


def certify_flex(*, leave_step: int, prior_check_step: int, t_e: int,
                  queue_or_cutoff_caused: bool,
                  survivors: dict[int, dict],
                  has_legal_set_alternative: bool = True
                  ) -> tuple[bool, list[str], Optional[int]]:
    """Section 2 flex vacancy certification. `survivors` maps uav_idx to
    {"transit_steps": int, "support_ok": bool}; only entries within
    `Z_FLEX_TRANSIT_STEPS` and with hard support intact qualify to cover. The
    focal is the minimum-transit qualifier, ties broken by ascending physical
    UAV index (the canonical anonymous ordering adopted here, since no
    conformance derivation yet fixes one; this is a tie-break only and does
    not change which vacancies certify).

    Q-C4 applies the empty-legal-alternative-set predicate to BOTH limbs, not
    only stable: `has_legal_set_alternative` must be True or the history is
    ineligible (SET is never defined as KEEP, no synthetic zero) regardless
    of how the coverage/timing checks come out."""
    reasons: list[str] = []
    if not (prior_check_step < leave_step <= t_e):
        reasons.append("leave_not_after_preceding_check")
    if (t_e - leave_step) > Y_FLEX_STEPS:
        reasons.append("leave_too_far_before_t_e")
    if queue_or_cutoff_caused:
        reasons.append(EXCLUDE_EMERGENCY)
    if not has_legal_set_alternative:
        reasons.append(EXCLUDE_EMPTY_SET_ALT)

    qualifying = {
        u: info["transit_steps"] for u, info in survivors.items()
        if info["transit_steps"] <= Z_FLEX_TRANSIT_STEPS and info.get("support_ok", True)
    }
    focal: Optional[int] = None
    if not qualifying:
        reasons.append("no_covering_survivor")
    else:
        min_steps = min(qualifying.values())
        focal = min(u for u, s in qualifying.items() if s == min_steps)
    return (len(reasons) == 0, reasons, focal)


def flex_transit_steps_for_env(env, distance_m: float) -> int:
    """Binds the Z=139-step coverage predicate's `v_max` to the registered
    UAV `max_speed` (30 m/s in S7-S3, `scenario_base.py:56/161`), never the
    5 m/s S3 user/cluster speed override -- the two are physically different
    quantities (UAV transit vs. ordinary user mobility), and section 2/Q-C5's
    coverage predicate `ceil(|p_i - z_vac| / (v_max * dt)) <= Z` is about UAV
    transit. This is the orchestration-boundary binding point: any caller
    building `certify_flex`'s `survivors` transit times from a real env must
    go through this function rather than hardcode a speed."""
    return transit_steps(distance_m, max_speed=float(env.max_speed), dt=float(env.time_step))


def transit_steps(distance_m: float, max_speed: float, dt: float) -> int:
    return int(math.ceil(distance_m / max(max_speed * dt, 1e-9)))


def select_joint_event(leave_candidates: list[dict],
                        certify_fn: Callable[[dict], tuple]) -> tuple[Optional[dict], list[dict]]:
    """Section 2 / Q-E4: exactly one joint event per episode -- the first
    LEAVE with BOTH a certified stable incumbent and a certified flex
    vacancy at the same t_e. Earlier non-joint-qualifying candidates are
    recorded as exclusions and search stops at the first joint qualifier.

    `certify_fn(candidate) -> (stable_ok, stable_reasons, flex_ok,
    flex_reasons, focal_flex_uav)`.
    """
    exclusions: list[dict] = []
    for cand in leave_candidates:
        stable_ok, stable_reasons, flex_ok, flex_reasons, focal = certify_fn(cand)
        if stable_ok and flex_ok:
            return (
                {"t_e": cand["t_e"], "leave_candidate": cand, "focal_flex_uav": focal},
                exclusions,
            )
        exclusions.append({
            "t_e": cand.get("t_e"),
            "stable_certified": stable_ok,
            "stable_reasons": stable_reasons,
            "flex_certified": flex_ok,
            "flex_reasons": flex_reasons,
        })
    return None, exclusions


def build_event_conformance_record(cand: dict) -> dict:
    """Section 2's mandatory per-event conformance record."""
    return {
        "pre_service_status": cand.get("pre_service_status"),
        "post_service_status": cand.get("post_service_status"),
        "capture_edge": cand.get("capture_edge"),
        "last_charging_arrival": cand.get("last_charging_arrival"),
        "uav_charging": cand.get("uav_charging"),
        "uav_dock_requests": cand.get("uav_dock_requests"),
        "uav_target_stations": cand.get("uav_target_stations"),
        "battery_ratio": cand.get("battery_ratio"),
        "return_energy_margin": cand.get("return_energy_margin"),
        "uav_position": cand.get("uav_position"),
        "station_position": cand.get("station_position"),
        "station_occupancy": cand.get("station_occupancy"),
        "station_queue_length": cand.get("station_queue_length"),
        "source_control_schedule_identity": cand.get("schedule_identity"),
    }


# =============================================================================
# Section 6 -- legal SET alternatives
# =============================================================================

def legal_set_targets(*, post_leave_targets: list, vacated_pre_leave_target,
                       focal_incumbent_target, domain_bounds=None,
                       geometry_tol: float = 1e-6) -> list[np.ndarray]:
    """Z(h) = {post-LEAVE relay/service targets} u {vacated pre-LEAVE target},
    deduplicated geometrically, minus only the exclusions the contract names.
    Never excludes for unreachability within Delta -- transit cost is part of
    SET's causal consequence."""
    candidates = list(post_leave_targets) + [vacated_pre_leave_target]
    deduped: list[np.ndarray] = []
    for raw in candidates:
        t = np.asarray(raw, dtype=float)
        if not any(np.linalg.norm(t - d) <= geometry_tol for d in deduped):
            deduped.append(t)

    focal_target = np.asarray(focal_incumbent_target, dtype=float)
    legal: list[np.ndarray] = []
    for t in deduped:
        if np.linalg.norm(t - focal_target) <= geometry_tol:
            continue  # exclude the focal incumbent target
        if domain_bounds is not None:
            lo, hi = domain_bounds
            if np.any(t < lo) or np.any(t > hi):
                continue  # outside the physical source/action domain
        legal.append(t)
    return legal


def focal_eligible_to_act(*, absent: bool, charging: bool, failed: bool,
                           non_acting: bool) -> bool:
    """Assignments requiring the focal to be absent/charging/failed/non-acting
    are excluded -- this is a precondition on the focal, not on any target."""
    return not (absent or charging or failed or non_acting)


# =============================================================================
# Section 7 -- primary G and window-local safety-event latching
# =============================================================================

def compute_G(*, qos_satisfaction_ratio: float, return_constraint_cost: float,
              new_cutoff_count: int, new_depletion_count: int) -> float:
    """G_t = qos_satisfaction_ratio - 2*return_constraint_cost(capped)
    - 5*new_cutoff - 10*new_depletion. Analyzer-computed from component
    fields; never reuses `safety_reward_before_pbrs`."""
    return (qos_satisfaction_ratio
            - 2.0 * return_constraint_cost
            - 5.0 * new_cutoff_count
            - 10.0 * new_depletion_count)


def window_series_length(h: int) -> int:
    """Pinned alignment convention (section 7, item 11): a window-local latch
    series holds exactly `H + 1` rows -- row 0 is the previous-step baseline
    recorded AT `t_e` ("record the current cutoff/depletion masks as the
    previous-step state"), and rows `1..H` are the `H` in-window steps
    checked for a rising edge. Pinned to `H+1` (not `H`) so callers building
    a real series from `H_stable`/`H_flex` have one unambiguous length to
    target; `window_latched_counts` itself infers its shape from whatever it
    is given, so this is the convention callers must follow, not a runtime
    check inside that function."""
    return int(h) + 1


def window_latched_counts(cutoff_series: np.ndarray, depletion_series: np.ndarray) -> dict:
    """Window-local event latching. Row 0 of each series is the previous-step
    baseline recorded AT t_e (contributes zero by definition); each
    subsequent row counts at most the first false->true transition per UAV
    per type within the window -- a post-recovery recurrence counts only if
    it is the window's first transition of that type. Callers must size
    their series per `window_series_length` (H+1 rows: baseline + H steps)."""
    cutoff_series = np.asarray(cutoff_series, dtype=bool)
    depletion_series = np.asarray(depletion_series, dtype=bool)
    n_steps, n_uavs = cutoff_series.shape
    cutoff_counted = np.zeros(n_uavs, dtype=bool)
    depletion_counted = np.zeros(n_uavs, dtype=bool)
    cutoff_new = np.zeros(n_steps, dtype=int)
    depletion_new = np.zeros(n_steps, dtype=int)
    prev_cutoff = cutoff_series[0] if n_steps else np.zeros(n_uavs, dtype=bool)
    prev_depletion = depletion_series[0] if n_steps else np.zeros(n_uavs, dtype=bool)

    for t in range(1, n_steps):
        rising_c = cutoff_series[t] & ~prev_cutoff
        rising_d = depletion_series[t] & ~prev_depletion
        newly_c = rising_c & ~cutoff_counted
        newly_d = rising_d & ~depletion_counted
        cutoff_new[t] = int(np.sum(newly_c))
        depletion_new[t] = int(np.sum(newly_d))
        cutoff_counted |= newly_c
        depletion_counted |= newly_d
        prev_cutoff = cutoff_series[t]
        prev_depletion = depletion_series[t]

    return {
        "cutoff_count": int(np.sum(cutoff_counted)),
        "depletion_count": int(np.sum(depletion_counted)),
        "cutoff_per_step": cutoff_new,
        "depletion_per_step": depletion_new,
    }


def episode_latched_new_counts(full_series: np.ndarray, window_start: int,
                                window_len: int) -> int:
    """Reference implementation of the environment's own episode-latched
    convention (`cutoff_event_seen`/`depletion_event_seen`: 'new' only the
    first time ever since reset), restricted to a window -- used only to
    demonstrate the required divergence from window-local latching. The
    analyzer must gate on window-local, never on this."""
    full_series = np.asarray(full_series, dtype=bool)
    n_uavs = full_series.shape[1]
    seen = np.zeros(n_uavs, dtype=bool)
    count_in_window = 0
    for t in range(full_series.shape[0]):
        newly = full_series[t] & ~seen
        if window_start <= t < window_start + window_len:
            count_in_window += int(np.sum(newly))
        seen |= full_series[t]
    return count_in_window


def user_step_saturation_fraction(qos_user_step) -> float:
    """Section 7's mandatory QoS saturation fraction, computed on the
    user-step unit -- NOT the per-step arm mean. `qos_user_step` is the
    per-user rate/ratio matrix (shape steps x users) or any flattened
    user-step series of the SAME clip(rate/target, 0, 1) quantity.

    Fixed defect (measured): computing saturation from the already-averaged
    per-step arm mean returns 0.0 saturation in a 29-of-30-users-saturated
    regime, because the 30th user's low ratio pulls every step's MEAN below
    the 1.0 ceiling even though 29 of 30 individual users sit AT it. The
    per-step mean and the user-step unit are different quantities; only the
    latter is what section 7 defines "user-step QoS saturation fraction" to
    mean."""
    arr = np.asarray(qos_user_step, dtype=float)
    return float(np.mean(arr >= 1.0 - 1e-9)) if arr.size else 0.0


def nondegeneracy_report(*, qos_series, qos_user_step, return_cost_series,
                          cutoff_incidence: int, depletion_incidence: int,
                          g_series, secondary_series) -> dict:
    """Section 7 mandatory non-degeneracy record, per arm/topology/limb.

    `qos_series`: the per-step arm-level mean QoS ratio (the same quantity
    `compute_G` consumes) -- feeds `qos_mean`/`qos_var`. `qos_user_step`: the
    finer per-(user, step) ratio matrix or series -- feeds
    `qos_saturation_fraction` exclusively, via `user_step_saturation_fraction`
    (see its docstring for why the two inputs must not be conflated)."""
    qos = np.asarray(qos_series, dtype=float)
    rc = np.asarray(return_cost_series, dtype=float)
    secondary = np.asarray(secondary_series, dtype=float)
    saturation_fraction = user_step_saturation_fraction(qos_user_step)
    return {
        "qos_mean": float(np.mean(qos)) if qos.size else float("nan"),
        "qos_var": float(np.var(qos)) if qos.size else float("nan"),
        "return_cost_mean": float(np.mean(rc)) if rc.size else float("nan"),
        "return_cost_var": float(np.var(rc)) if rc.size else float("nan"),
        "cutoff_incidence": int(cutoff_incidence),
        "depletion_incidence": int(depletion_incidence),
        "total_G": float(np.sum(g_series)) if len(g_series) else float("nan"),
        "qos_saturation_fraction": saturation_fraction,
        "secondary_metric_mean": float(np.mean(secondary)) if secondary.size else float("nan"),
    }


def qos_component_saturated(*, per_arm_qos_means: dict, saturation_fraction: float) -> bool:
    values = list(per_arm_qos_means.values())
    qos_range = (max(values) - min(values)) if values else 0.0
    return saturation_fraction >= 0.95 and qos_range < 0.01


def primary_g_degenerate(*, stable_b_identified: bool, flex_b_identified: bool) -> bool:
    """PRIMARY_G_DEGENERATE fires when NEITHER limb's normalizer establishes
    a positive LCB95 (ruling 2026-07-27, VERDICT_Q2 -- disjunctive across
    limbs): `b_m_positive_lcb = b_stable_positive OR b_flex_positive`, so
    `NOT b_m_positive_lcb == (LCB95(B_stable) <= 0) AND (LCB95(B_flex) <=
    0)`. A conjunctive definition would let the global degeneracy branch
    preempt a valid result from one limb merely because the OTHER limb's
    normalizer failed, conflicting with the frozen partial-result branches:
    branch 7 preserves an identified stable-persistence result while flex
    remains unresolved; branch 8 preserves an identified flex
    non-materiality result while stable does not clear; branch 9 preserves
    an identified stable non-materiality result. Each limb's substantive
    predicate already protects itself, so disjunction does not let an
    unnormalized limb make a claim -- it only stops the invalid limb from
    erasing a valid result belonging to the other limb.

    The component-invariance limb of branch 3 (conceptually
    `stable_measurement_valid = stable_components_separate AND
    stable_b_identified`, mirrored for flex, then
    `NOT (stable_measurement_valid OR flex_measurement_valid)`) is NOT
    evaluated here: `stable_components_separate`/`flex_components_separate`
    have no production derivation anywhere in this module
    (`qos_component_saturated` is dead code called from nowhere, and no
    per-limb component-separation quantity is computed or recorded) and
    must never be invented or approximated by `arm_distinct_ok` -- distinct
    duty maps do not establish that the four G component sequences differ.
    Callers must record `component_invariance_evaluated=False` in the
    result payload alongside this flag, so the missing input stays visible
    rather than silently defaulted to a convenient literal."""
    return not (stable_b_identified or flex_b_identified)


def resolve_primary_g_tristate(*, stable_b_identified: bool, flex_b_identified: bool,
                                component_invariance_evaluated: bool,
                                stable_components_separate: bool = False,
                                flex_components_separate: bool = False) -> dict:
    """Ruling 2026-07-27 (COMPONENT_INVARIANCE tri-state), implemented
    exactly per the governing task brief's quoted pseudocode. This is the
    piece `primary_g_degenerate` above deliberately leaves undone -- kept
    unmodified, per the brief's explicit instruction, and used here as
    `normalizer_forces_degenerate` -- built AROUND it rather than into it.

    Three outcomes, first match, mirroring the ruling's own if/elif/else:

    1. `normalizer_forces_degenerate` (`primary_g_degenerate(...)`) is
       independently sufficient and checked FIRST: branch 3 fires
       "regardless of whether component invariance was evaluated." Neither
       `stable_components_separate` nor `flex_components_separate` is
       consulted in this case.
    2. Otherwise, when the mandatory primary-G component audit was NOT
       evaluated, the run is `MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING`
       -- an implementation/measurement invalidity (branch 1), never
       branch 10's `SOURCE_NECESSITY_UNRESOLVED` catch-all.
    3. Only when evaluated is `primary_g_degenerate` recomputed from BOTH
       each limb's normalizer identification and its component-separation
       result: `stable_measurement_valid = stable_b_identified and
       stable_components_separate` (mirrored for flex),
       `primary_g_degenerate = not (stable_measurement_valid or
       flex_measurement_valid)`.

    Returns the two values `decide_branch` needs beyond its pre-ruling
    contract (`primary_g_degenerate_flag`, `component_invariance_evaluated`,
    fed straight into its identically-named keyword-only parameters) plus
    a `reason` string for the two branch-3/branch-1 cases (`None` when
    neither applies) and the two intermediate measurement-validity booleans,
    for direct inspection independent of the driver."""
    normalizer_forces_degenerate = primary_g_degenerate(
        stable_b_identified=stable_b_identified, flex_b_identified=flex_b_identified)
    if normalizer_forces_degenerate:
        return {
            "primary_g_degenerate_flag": True,
            "component_invariance_evaluated": component_invariance_evaluated,
            "stable_measurement_valid": False,
            "flex_measurement_valid": False,
            "reason": "NO_POSITIVE_NORMALIZER_ON_EITHER_LIMB",
        }
    if not component_invariance_evaluated:
        return {
            "primary_g_degenerate_flag": False,
            "component_invariance_evaluated": False,
            "stable_measurement_valid": False,
            "flex_measurement_valid": False,
            "reason": "MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING",
        }
    stable_measurement_valid = stable_b_identified and stable_components_separate
    flex_measurement_valid = flex_b_identified and flex_components_separate
    return {
        "primary_g_degenerate_flag": not (stable_measurement_valid or flex_measurement_valid),
        "component_invariance_evaluated": True,
        "stable_measurement_valid": stable_measurement_valid,
        "flex_measurement_valid": flex_measurement_valid,
        "reason": None,
    }


# =============================================================================
# Section 4 -- controllers (pure duty-map layer)
# =============================================================================

def constructive_mixed_update(*, duty_map: dict[int, int],
                               duty_positions: dict[int, np.ndarray],
                               airborne_positions: dict[int, np.ndarray],
                               event: Optional[str] = None,
                               event_uav: Optional[int] = None,
                               locked_duties: frozenset = frozenset()) -> dict[int, int]:
    """`constructive_mixed` (binding reference: G2 CONSTRUCTIVE_CHARGE_ROTATION).
    Preserves the duty map between lifecycle events (no full-sync permutation
    at every check); at LEAVE removes the absent UAV and re-matches the
    vacancy; at REJOIN assigns the rejoining UAV the nearest uncovered duty.
    Never deliberately leaves a coverable vacancy unserved.

    `locked_duties`: duty ids whose current incumbent is a certified stable
    incumbent (section 2) and must be preserved untouched -- withheld
    entirely from the LEAVE re-match pool, as long as that incumbent is
    still airborne.

    Fixed defect (measured, registered fleet shape 8 duties / 8 UAVs, zero
    idle survivors after a LEAVE): the previous version only ever filled
    VACATED duties from IDLE survivors (`u not in new_map.values()`). At the
    registered environment's fully-covered fleet shape every survivor
    already holds a duty, so `survivors` was always empty and the vacancy
    was silently left unserved -- identical to `null`'s frozen map (measured:
    identical maps except the absent owner -- i.e. even the buggy version's
    literal dict differed only by a stale key pointing at the now-absent
    UAV, never a live reassignment).

    Contract section 4 / Q-C1 requires: "recompute the duty set for the
    reduced airborne fleet ... and re-match, preserving certified stable
    incumbents; a duty-holding survivor may be reassigned to cover the
    vacancy; never leave a coverable vacancy unserved." "Cover the vacancy"
    means the vacated duty POSITION must end up with a live incumbent, not
    silently disappear from the duty set. Real re-clustering of live user
    geometry into a genuinely reduced target set is an orchestration-layer
    job (out of this proof-sized pure layer's scope, matching the module
    docstring's real-vs-pure split); this layer's realization keeps every
    duty position (including the vacated one) in the re-match pool and runs
    a full greedy nearest-first re-match of all unlocked duties against all
    survivors, processing the freshly vacated duty/duties FIRST so a
    duty-holding survivor is preferentially pulled to cover the vacancy --
    the "recompute for the reduced fleet" step -- and, since the fleet now
    has one fewer body than duty, EXACTLY one unlocked duty (never
    necessarily the vacated one -- whichever the greedy pass leaves stranded
    once the survivor pool empties) ends up uncovered rather than the
    vacated one being trivially dropped.
    """
    new_map = dict(duty_map)
    if event == "LEAVE" and event_uav is not None:
        vacated = [d for d, u in duty_map.items() if u == event_uav]
        for d in vacated:
            del new_map[d]
        # Guard (measured trap): never let the leaver itself be a
        # reassignment candidate, even if the caller's `airborne_positions`
        # still (erroneously) contains it.
        survivor_ids = [u for u in airborne_positions if u != event_uav]

        all_duties = list(duty_positions.keys())
        locked_here = [d for d in all_duties if d in locked_duties and d in new_map]
        unlocked_duties = [d for d in all_duties if d not in locked_here]
        locked_holders = {new_map[d] for d in locked_here}
        pool = [u for u in survivor_ids if u not in locked_holders]

        # Full re-match at the LEAVE event only (sanctioned: "recompute
        # flexible service targets for the current airborne fleet"); every
        # unlocked duty's current incumbent is up for re-optimization here,
        # never between lifecycle events.
        for d in unlocked_duties:
            new_map.pop(d, None)

        ordered = sorted(unlocked_duties, key=lambda d: (0 if d in vacated else 1, d))
        for d in ordered:
            if not pool:
                break  # more unlocked duties than survivors: this one stays uncovered
            best = min(
                pool,
                key=lambda u: np.linalg.norm(
                    np.asarray(airborne_positions[u][:2]) - np.asarray(duty_positions[d][:2])
                ),
            )
            new_map[d] = best
            pool.remove(best)
    elif event == "REJOIN" and event_uav is not None:
        uncovered = [d for d in duty_positions if d not in new_map]
        if uncovered:
            best_d = min(
                uncovered,
                key=lambda d: np.linalg.norm(
                    np.asarray(airborne_positions[event_uav][:2]) - np.asarray(duty_positions[d][:2])
                ),
            )
            new_map[best_d] = event_uav
    return new_map


def null_update(*, duty_map: dict[int, int]) -> dict[int, int]:
    """`null` / NO_PROACTIVE_ROTATION: freezes the pre-event duty ownership
    map for the whole mechanism horizon, unconditionally -- no proactive
    replacement at LEAVE, no proactive reoptimization at REJOIN."""
    return dict(duty_map)


def limb_locked_duties(*, stable_focal_duty) -> dict:
    """Which duties each limb is permitted to freeze during its intervention.

    Extracted as a pure function by the Stage B repair so the property is
    testable rather than buried in the event builder, which is where it went
    wrong.

    Section 1 is explicit that non-focal duties are **never** frozen -- for
    every candidate `z`, all other airborne assignments are reoptimized
    one-to-one under `constructive_mixed`. So:

    - **stable limb: nothing is locked.** It previously received the FLEX
      focal's incumbent duty, which restricted the stable SET joint
      continuation relative to the registered maximization and made SET look
      artificially costly. That biases toward "persistence is necessary" --
      claim-favouring, the same asymmetry that disqualified `n_select=1`.
    - **flex limb: the certified stable incumbent's duty.** This is not an
      extra constraint; preserving an active stable incumbent's target between
      lifecycle events IS `constructive_mixed` semantics (section 4).
    """
    return {
        "stable": frozenset(),
        "flex": frozenset({stable_focal_duty}) if stable_focal_duty is not None else frozenset(),
    }


def full_sync_set_update(*, duty_positions: dict[int, np.ndarray],
                          airborne_positions: dict[int, np.ndarray]) -> dict[int, int]:
    """`full_sync_SET`: reassigns every duty at every check (Part-A conformance
    diagnostic only). Deterministic greedy nearest-assignment, ascending
    duty id, so it is reproducible independent of dict ordering."""
    remaining = dict(airborne_positions)
    new_map: dict[int, int] = {}
    for d in sorted(duty_positions):
        if not remaining:
            break
        best = min(
            remaining,
            key=lambda u: np.linalg.norm(
                np.asarray(remaining[u][:2]) - np.asarray(duty_positions[d][:2])
            ),
        )
        new_map[d] = best
        del remaining[best]
    return new_map


# =============================================================================
# Section 8 -- Part-A conformance
# =============================================================================

def part_a_conformance(*, lower_contrast_lcb: float, lower_contrast_ucb: float,
                        upper_contrast_lcb: float, b_stable_lcb: float) -> str:
    """Two one-sided 5% equivalence tests of
    -0.05*B_stable < D_A < +0.05*B_stable, conditional on LCB95(B_stable) > 0.

    Callers supply the already-bootstrapped bounds of the linear contrast
    `D_A + 0.05*B_stable` (both its LCB95 `lower_contrast_lcb` and its UCB95
    `lower_contrast_ucb`) and of `0.05*B_stable - D_A` (its LCB95
    `upper_contrast_lcb`).

    Both equivalence tests pass (both LCB95s > 0) -> PART_A_CONTRADICTION
    (return-equivalence).

    CONFORMANCE_PASS ("full-sync materially worse") requires the directly
    tested condition UCB95(D_A + 0.05*B_stable) < 0 -- i.e. even the UPPER
    bound of the lower contrast's own interval is negative, so D_A is
    confidently below -0.05*B_stable. A merely-FAILING lower equivalence
    test (`lower_contrast_lcb <= 0`) is NOT sufficient for this: an LCB95 at
    or below zero with a UCB95 at or above zero means that interval
    straddles zero, which is inconclusive, not "materially worse."

    Fixed defect (measured): the previous signature never received the
    lower contrast's UCB95 at all, and instead inferred "materially worse"
    from the (unrelated) upper-contrast LCB failing to pass -- a 90% interval
    of [-0.333, +0.009] on the lower contrast (LCB95 -0.333 <= 0, so the
    lower equivalence test fails; UCB95 +0.009 >= 0, so "materially worse"
    is NOT established) was misclassified CONFORMANCE_PASS. It must be
    PART_A_CONFORMANCE_UNRESOLVED.

    Every other combination -> PART_A_CONFORMANCE_UNRESOLVED. Never applied
    on the flex limb."""
    if b_stable_lcb <= 0:
        return "NOT_APPLICABLE"
    lower_passes = lower_contrast_lcb > 0
    upper_passes = upper_contrast_lcb > 0
    if lower_passes and upper_passes:
        return "PART_A_CONTRADICTION"
    if lower_contrast_ucb < 0:
        return "CONFORMANCE_PASS"
    return "PART_A_CONFORMANCE_UNRESOLVED"


# =============================================================================
# Item 3 -- conformance_ok: real conjunction, and the arm-distinctness spot check
# =============================================================================

def arm_distinctness_check(duty_map_pairs: list) -> bool:
    """Section 4 / item 3's arm-distinctness spot check: constructive_mixed
    must differ from null on at least one certified joint event's duty maps
    -- proving the two arms are not silently identical at the registered
    fleet shape (the exact historical defect `constructive_mixed_update`'s
    own docstring documents: a buggy version left every vacancy unserved,
    so its map differed from `null`'s only by one stale dict key).
    `duty_map_pairs` is `[(duty_map_at_te, duty_map_before_leave), ...]` for
    events where a vacancy was coverable; every certified joint event
    already guarantees that (flex certification requires a covering
    survivor), so callers pass every certified event's pair unconditionally.

    An empty list (no certified events found anywhere in the run) passes
    vacuously here -- that absence is `SOURCE_EVENT_SUPPORT_INSUFFICIENT`
    (branch 2)'s failure mode, already reported by `support_ok`, and must
    not be double-counted as an arm-conformance defect (branch 1) ahead of
    it in `decide_branch`'s precedence: this check exists to catch arms
    that are indistinguishable WHEN events exist, not to re-detect that no
    events were found."""
    if not duty_map_pairs:
        return True
    return any(constructive != before_leave for constructive, before_leave in duty_map_pairs)


def compute_conformance_ok(*, invalidated_pairs: int, topology_hash_ok: bool,
                            arm_distinct_ok: bool) -> bool:
    """Item 3's real conjunction: zero tolerance on invalidated
    (`PrefixReplayMismatchError`) pairs, every pinned-topology hash assert
    passed, and the arm-distinctness spot check passed. False routes
    `decide_branch` to branch 1 (`INVALID_EVENT_ALIGNED_AUDIT`)."""
    return int(invalidated_pairs) == 0 and bool(topology_hash_ok) and bool(arm_distinct_ok)


# =============================================================================
# Section 8 -- Part-A conformance bounds (joint bootstrap wiring)
# =============================================================================

def compute_part_a_bounds(*, d_a_topology_units: list, b_stable_topology_units: list,
                           shared_topology_indices: np.ndarray, seed: int) -> Optional[dict]:
    """Bootstraps D_A jointly with B_stable, sharing the SAME
    `shared_topology_indices` every other primary quantity uses (section 8:
    "All primary quantities use the same topology/episode bootstrap
    indices"), and returns the three bounds `part_a_conformance` consumes
    (`lower_contrast_lcb`/`lower_contrast_ucb` of `D_A + 0.05*B_stable`,
    `upper_contrast_lcb` of `0.05*B_stable - D_A`) plus `b_stable_lcb` for
    its own conditioning gate.

    Returns `None` when there is no stable-limb calibration D_A data to
    bootstrap at all (every topology contributed zero qualifying stable
    events) -- the caller must not report a Part-A verdict in that case,
    per the "when and only when the stable class has events" requirement;
    a present-but-nan bound would be a silent, meaningless verdict rather
    than an honest absence."""
    if not any(len(units) for units in d_a_topology_units):
        return None
    b_stable = hierarchical_bootstrap_quantity(
        b_stable_topology_units, shared_topology_indices=shared_topology_indices, seed=seed)
    d_a = hierarchical_bootstrap_quantity(
        d_a_topology_units, shared_topology_indices=shared_topology_indices, seed=seed)
    lower_contrast_iters = d_a["u_star_iters"] + EQUIVALENCE_DELTA * b_stable["u_star_iters"]
    upper_contrast_iters = EQUIVALENCE_DELTA * b_stable["u_star_iters"] - d_a["u_star_iters"]
    lower_finite = lower_contrast_iters[np.isfinite(lower_contrast_iters)]
    upper_finite = upper_contrast_iters[np.isfinite(upper_contrast_iters)]
    return {
        "b_stable_lcb": b_stable["lo"],
        "lower_contrast_lcb": float(np.percentile(lower_finite, 5)) if lower_finite.size else float("nan"),
        "lower_contrast_ucb": float(np.percentile(lower_finite, 95)) if lower_finite.size else float("nan"),
        "upper_contrast_lcb": float(np.percentile(upper_finite, 5)) if upper_finite.size else float("nan"),
    }


def map_part_a_verdict_to_inputs(verdict: str) -> tuple:
    """Maps `part_a_conformance`'s verdict string to `decide_branch`'s
    `part_a_contradiction` boolean plus the diagnostic string that lands in
    the JSON payload only, never a branch input itself. ONLY
    `PART_A_CONTRADICTION` sets the branch input True --
    `PART_A_CONFORMANCE_UNRESOLVED` (and `NOT_APPLICABLE`,
    `CONFORMANCE_PASS`) never flip any branch input, per section 8: the
    unresolved diagnostic "does not relabel the source branch."""
    return (verdict == "PART_A_CONTRADICTION", verdict)


# =============================================================================
# Section 10 -- ten-branch first-match decision
# =============================================================================

def decide_branch(*, conformance_ok: bool, support_ok: bool,
                   primary_g_degenerate_flag: bool, part_a_contradiction: bool,
                   b_stable_lcb: float, t_stable_ucb: float, t_stable_lcb: float,
                   b_flex_lcb: float, t_flex_lcb: float, t_flex_ucb: float,
                   component_invariance_evaluated: bool) -> str:
    """First-match precedence over the ten registered branches.

    `component_invariance_evaluated` (ruling 2026-07-27, COMPONENT_INVARIANCE
    tri-state -- quoted verbatim in the governing task brief): the normalizer
    condition (`primary_g_degenerate_flag`, the caller's already-computed
    `primary_g_degenerate(stable_b_identified, flex_b_identified)`) is
    independently sufficient for branch 3 and is checked FIRST, regardless of
    whether component invariance was ever evaluated -- "branch 3 remains
    reachable through the independently sufficient normalizer condition."
    Only once that has NOT already resolved the run does this new axis
    matter: a run with at least one identified normalizer whose mandatory
    primary-G component audit was never performed is an implementation/
    measurement invalidity -- branch 1 (`INVALID_EVENT_ALIGNED_AUDIT`), never
    branch 10's `SOURCE_NECESSITY_UNRESOLVED` catch-all, because the mandatory
    audit is missing DATA, not an unresolved sign. Defaults to `True` so
    every pre-ruling caller (of which there are ~190 in this module's own
    test suite, none aware of this axis) keeps its unmodified branch outcome.
    No caller in this module passes `False` yet: the ruling's own text notes
    no production derivation for component separation exists
    (`assemble_audit_result`'s `component_invariance_evaluated=False`
    diagnostic field is reported, never fed here), so this new gate is
    currently unreachable in production and must be tested directly."""
    if not conformance_ok:
        return "INVALID_EVENT_ALIGNED_AUDIT"
    if not support_ok:
        return "SOURCE_EVENT_SUPPORT_INSUFFICIENT"
    if primary_g_degenerate_flag:
        return "PRIMARY_G_DEGENERATE"
    if not component_invariance_evaluated:
        return "INVALID_EVENT_ALIGNED_AUDIT"
    if part_a_contradiction:
        return "PART_A_CONTRADICTION"

    stable_clears = (b_stable_lcb > 0) and (t_stable_ucb < 0)
    flex_clears = (b_flex_lcb > 0) and (t_flex_lcb > 0)
    flex_affirmative_miss = (b_flex_lcb > 0) and (t_flex_ucb < 0)
    stable_affirmative_miss = (b_stable_lcb > 0) and (t_stable_lcb > 0)

    if stable_clears and flex_clears:
        return "PERSISTENCE_NECESSARY_SOURCE"
    if stable_clears and flex_affirmative_miss:
        return "STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL"
    if stable_clears:
        return "MATERIAL_STABLE_PERSISTENCE_IDENTIFIED"
    if flex_affirmative_miss:
        return "NO_MATERIAL_FLEX_RENEWAL_IDENTIFIED"
    if stable_affirmative_miss:
        return "NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED"
    return "SOURCE_NECESSITY_UNRESOLVED"


# =============================================================================
# Section 9 -- minimum support and the one permissible expansion
# =============================================================================

def check_minimum_support(topology_reports: list[dict]) -> tuple[bool, dict]:
    calib_ok = sum(
        1 for rep in topology_reports
        if rep.get("qualifying_calibration_episodes", 0) >= MIN_SUPPORT_EPISODES_PER_TOPOLOGY
    )
    audit_ok = sum(
        1 for rep in topology_reports
        if rep.get("qualifying_audit_episodes", 0) >= MIN_SUPPORT_EPISODES_PER_TOPOLOGY
    )
    support_ok = (calib_ok >= MIN_SUPPORT_TOPOLOGIES) and (audit_ok >= MIN_SUPPORT_TOPOLOGIES)
    return support_ok, {"calibration_topologies_ok": calib_ok, "audit_topologies_ok": audit_ok}


def expansion_allowed(*, conformance_ok: bool, support_ok: bool, b_stable_point: float,
                       b_flex_point: float, t_stable_intended_sign_ok: bool,
                       t_flex_intended_sign_ok: bool, any_bound_unresolved: bool,
                       already_expanded: bool) -> bool:
    """Section 9's one permissible expansion, and no more."""
    if already_expanded:
        return False
    if not (conformance_ok and support_ok):
        return False
    if b_stable_point <= 0 or b_flex_point <= 0:
        return False
    if not (t_stable_intended_sign_ok and t_flex_intended_sign_ok):
        return False
    return bool(any_bound_unresolved)


REGISTERED_EXPANSION_SEED_SET = frozenset(TOPOLOGY_SEEDS_INITIAL) | frozenset(TOPOLOGY_SEEDS_EXPANSION)


class ExpansionNotJustifiedError(RuntimeError):
    """Raised when a run's topology-seed set IS the registered 16-topology
    expansion set (`TOPOLOGY_SEEDS_INITIAL` union `TOPOLOGY_SEEDS_EXPANSION`,
    section 9's ONE permissible expansion) but the frozen `expansion_allowed`
    predicate, evaluated against the INITIAL 8 topologies' own result, does
    not license it. Never repaired: `main()` must not report a pooled
    16-topology result as a conclusion-bearing expansion when the rule that
    licenses adding the extra eight topologies was not satisfied by the
    initial batch on its own."""


def check_expansion_justified(topology_seeds: list, topology_results: list[dict],
                               topology_hash_failures: list[dict]) -> None:
    """Section 9's one-permissible-expansion gate, wired for real (ruling
    2026-07-27): `expansion_allowed` existed but was never called from
    `main()`, so a human passing `--topology-seeds` with the 16-seed union
    bypassed the frozen predicate entirely -- "the dead function does not
    make the scientific rule optional." A no-op for every topology-seed set
    OTHER than the registered expansion union -- smoke, dev, the plain
    8-seed default, or any other override -- per the "guard is on a
    conclusion-bearing expansion, not on every override" scope
    `resolve_run_plan` already draws.

    `expansion_allowed`'s inputs are evaluated against the INITIAL 8
    topologies' OWN `assemble_audit_result` -- never the pooled 16, which
    would let the extra eight topologies' data justify their own inclusion.
    `topology_results`/`topology_hash_failures` are the SAME accumulators
    `main()` already built for the full requested seed set; this function
    only re-filters them down to the initial 8 and re-runs the driver-level
    assembly (cheap relative to episode collection) over that subset.

    `t_stable_intended_sign_ok`/`t_flex_intended_sign_ok` and
    `any_bound_unresolved` apply the frozen section 8 gate definition
    directly -- stable clears iff `LCB95(B_stable) > 0 and UCB95(T_stable) <
    0`; flex clears iff `LCB95(B_flex) > 0 and LCB95(T_flex) > 0`; the
    affirmative-miss reading is the SAME B_m gate with the T_m bound read on
    the opposite side of its interval. This is `decide_branch`'s identical
    predicate, reproduced here (not imported from it) because `decide_branch`
    exposes only its final branch string, never these intermediate booleans;
    both are separately grounded in the same frozen contract text."""
    if set(topology_seeds) != REGISTERED_EXPANSION_SEED_SET:
        return

    initial_results = [r for r in topology_results
                        if r["topology_record"]["topology_seed"] in TOPOLOGY_SEEDS_INITIAL]
    initial_hash_failures = [f for f in topology_hash_failures
                              if f["topology_seed"] in TOPOLOGY_SEEDS_INITIAL]
    initial = assemble_audit_result(initial_results, initial_hash_failures)

    conformance_ok = bool(initial["conformance"]["ok"])
    support_ok = bool(initial["support"]["ok"])
    t_m = initial.get("t_m_bootstrap")

    if conformance_ok and support_ok and t_m is not None:
        b_stable_point = t_m["b_stable_point"]
        b_flex_point = t_m["b_flex_point"]
        t_stable_intended_sign_ok = t_m["t_stable_point"] < 0
        t_flex_intended_sign_ok = t_m["t_flex_point"] > 0
        stable_clears = (t_m["b_stable_lcb"] > 0) and (t_m["t_stable_ucb"] < 0)
        stable_affirmative_miss = (t_m["b_stable_lcb"] > 0) and (t_m["t_stable_lcb"] > 0)
        flex_clears = (t_m["b_flex_lcb"] > 0) and (t_m["t_flex_lcb"] > 0)
        flex_affirmative_miss = (t_m["b_flex_lcb"] > 0) and (t_m["t_flex_ucb"] < 0)
        stable_resolved = stable_clears or stable_affirmative_miss
        flex_resolved = flex_clears or flex_affirmative_miss
        any_bound_unresolved = not (stable_resolved and flex_resolved)
    else:
        # expansion_allowed's own `not (conformance_ok and support_ok)` gate
        # already refuses here; these three never reach its later checks.
        b_stable_point = b_flex_point = 0.0
        t_stable_intended_sign_ok = t_flex_intended_sign_ok = False
        any_bound_unresolved = False

    allowed = expansion_allowed(
        conformance_ok=conformance_ok, support_ok=support_ok,
        b_stable_point=b_stable_point, b_flex_point=b_flex_point,
        t_stable_intended_sign_ok=t_stable_intended_sign_ok,
        t_flex_intended_sign_ok=t_flex_intended_sign_ok,
        any_bound_unresolved=any_bound_unresolved, already_expanded=False)
    if not allowed:
        raise ExpansionNotJustifiedError(
            "the registered 16-topology expansion set was requested, but "
            "expansion_allowed refused it against the initial 8 topologies' "
            f"own result: conformance_ok={conformance_ok} support_ok={support_ok} "
            f"b_stable_point={b_stable_point!r} b_flex_point={b_flex_point!r} "
            f"t_stable_intended_sign_ok={t_stable_intended_sign_ok} "
            f"t_flex_intended_sign_ok={t_flex_intended_sign_ok} "
            f"any_bound_unresolved={any_bound_unresolved}")


# =============================================================================
# Section 8 -- nested/rerun hierarchical bootstrap (event level)
# =============================================================================

def select_maximizer(select_streams: dict[Any, np.ndarray]) -> Any:
    """Argmax candidate by mean selection-stream value."""
    return max(select_streams, key=lambda z: float(np.mean(select_streams[z])))


def hierarchical_bootstrap_events(events: list[dict], *, iters: int, seed: int,
                                   compute_point: bool = True) -> dict:
    """Innermost event-level step of the section 8 / Q-I1 nested bootstrap.

    Each event is `{"candidates": {z: {"select": [...], "eval_set": [...]}},
    "eval_keep": [...]}`. Per iteration: for EVERY event, resample each
    candidate's selection stream with replacement and RE-RUN the argmax
    (never reuse the point-level winner); then resample the winning
    candidate's eval_set together with eval_keep under the SAME resample
    index (CRN pairing is preserved under resampling), and average the
    resulting U* = mean(eval_set) - mean(eval_keep) across events. The
    topology/episode resampling layers wrap this function (see
    `hierarchical_bootstrap_quantity`) and are the caller's responsibility.

    `compute_point=False` skips the true-argmax point estimate below. It
    costs nothing when this function is called once directly, but
    `hierarchical_bootstrap_quantity` calls it once per topology slot per
    OUTER iteration (up to `BOOTSTRAP_ITERS`) with `iters=1`, and that point
    value is discarded there -- recomputing it unconditionally would
    silently redo an O(n_events) pass on every outer iteration for a value
    nobody reads.
    """
    rng = np.random.default_rng(seed)
    iters = int(iters)
    u_star_iters = np.empty(iters, dtype=float)
    selected_candidates: list[list[Any]] = []

    for i in range(iters):
        u_vals = []
        picks = []
        for event in events:
            candidates = event["candidates"]
            resampled_means = {}
            for z, streams in candidates.items():
                sel = np.asarray(streams["select"], dtype=float)
                idx = rng.integers(0, sel.size, size=sel.size)
                resampled_means[z] = sel[idx].mean()
            best_z = max(resampled_means, key=resampled_means.get)
            picks.append(best_z)

            eval_set = np.asarray(candidates[best_z]["eval_set"], dtype=float)
            eval_keep = np.asarray(event["eval_keep"], dtype=float)
            idx_eval = rng.integers(0, eval_set.size, size=eval_set.size)
            u_vals.append(float(eval_set[idx_eval].mean() - eval_keep[idx_eval].mean()))
        u_star_iters[i] = float(np.mean(u_vals)) if u_vals else float("nan")
        selected_candidates.append(picks)

    point = float("nan")
    if compute_point:
        point_u = []
        for event in events:
            candidates = event["candidates"]
            point_best = select_maximizer({z: s["select"] for z, s in candidates.items()})
            eval_set = np.asarray(candidates[point_best]["eval_set"], dtype=float)
            eval_keep = np.asarray(event["eval_keep"], dtype=float)
            point_u.append(float(eval_set.mean() - eval_keep.mean()))
        point = float(np.mean(point_u)) if point_u else float("nan")

    return {
        "point": point,
        "u_star_iters": u_star_iters,
        "lo": float(np.percentile(u_star_iters, 5)) if iters else float("nan"),
        "hi": float(np.percentile(u_star_iters, 95)) if iters else float("nan"),
        "selected_candidates_per_iter": selected_candidates,
    }


USER_WORLD_SEED_NAMESPACE = "user_world"


def user_world_seed(*, topology_seed: int, block: str, episode_index: int) -> int:
    """R3 section E: the registered seed for an episode's user world.

    Derived from existing episode provenance under a namespace **disjoint** from
    every other registered seed -- topology, energy permutation and continuation
    `stream_seed` all live in `stream_seed`'s namespace, and this one must not
    collide with them or the user world would be correlated with the arm streams
    it is supposed to be independent of.

    The registered random-user distribution is unchanged by this. The seed makes
    the draw *reproducible and recorded*; it does not make it fixed across
    episodes, because the user world is a nested episode-level random factor
    rather than part of topology identity.
    """
    fields = (USER_WORLD_SEED_NAMESPACE, CONTRACT_ID, str(int(topology_seed)),
              str(block), str(int(episode_index)))
    digest = hashlib.sha256("|".join(fields).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def episode_world_fingerprint(env, *, seed_value: Optional[int] = None) -> dict:
    """R3 section E: the episode-world provenance record, taken immediately
    after environment initialization and before any stepping.

    Records the initial user and cluster state that construction fixed, so that
    an artifact can later prove which world an episode ran in. This is the
    provenance the Stage B ruling found missing: the worlds were real, they just
    were never written down, which is why the ep64 contrasts cannot be recovered
    even in principle.
    """
    parts: list[bytes] = []
    for name in ("user_positions", "user_velocities", "user_waypoints",
                 "user_pause_times", "user_cluster_assignments",
                 "cluster_centers_history", "cluster_velocities",
                 "cluster_waypoints", "cluster_pause_times"):
        value = getattr(env, name, None)
        if value is None:
            continue
        arr = np.asarray(value)
        parts.append(name.encode("utf-8"))
        parts.append(str(arr.shape).encode("utf-8"))
        parts.append(np.ascontiguousarray(arr).tobytes())
    # Witnessed rather than declared, and it takes BOTH halves. A seed alone
    # regenerates nothing: the user world is a function of the BS quadrant as
    # well as the stream, so without a pinned topology the same seed produces a
    # different world (measured: 4 distinct worlds in 6 constructions).
    # `regenerate_user_world` is the only writer of `user_world_seed_applied`,
    # and `build_pinned_env` is the only writer of `pinned_coordinate_hash`,
    # which it sets only after the hash assert passes.
    applied = getattr(env, "user_world_seed_applied", None)
    pinned = getattr(env, "pinned_coordinate_hash", None)
    controls = (
        applied is not None
        and pinned is not None
        and seed_value is not None
        and int(applied) == int(seed_value)
    )
    return {
        "user_world_seed": None if seed_value is None else int(seed_value),
        "fingerprint": hashlib.sha256(b"".join(parts)).hexdigest(),
        "n_users": int(getattr(env, "n_users", 0)),
        # The other half of the reproduction key. A world is regenerable from
        # (this hash, this seed), never from the seed alone.
        "pinned_coordinate_hash": pinned,
        # True means: rebuilding this episode at the same pinned topology and the
        # same `user_world_seed` reproduces this fingerprint. False means the
        # fingerprint still proves which world the episode ran in, but the world
        # came from construction-time state and cannot be regenerated.
        "seed_controls_generation": bool(controls),
    }


SELECTION_DIAGNOSTIC_SEED_TAG = "selection_diagnostic"


def selection_diagnostic_seed(seed: int = BOOTSTRAP_SEED) -> int:
    """A seed deliberately DISTINCT from the primary resampling stream.

    The diagnostic re-runs only the selection half, so it cannot consume the
    inference stream in the same order as `hierarchical_bootstrap_events` and
    would not reproduce it even given the same seed. Deriving a separate seed
    makes that explicit instead of implying a correspondence that does not
    hold."""
    digest = hashlib.sha256(f"{int(seed)}|{SELECTION_DIAGNOSTIC_SEED_TAG}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def selection_diagnostic(events: list[dict], *, iters: int = BOOTSTRAP_ITERS,
                          seed: int = BOOTSTRAP_SEED) -> list[dict]:
    """R2 section 8's selection diagnostic, required in the result artifact.

    At the `2/2` floor the audit buys a materiality verdict, not a candidate
    ranking, so the artifact has to expose how concentrated the maximizer
    choice actually was. Reporting only the point winner would hide an event
    whose selection was a coin flip behind a number that looks decided.
    Candidate instability is expected to WIDEN or fail to resolve the gate --
    it never invalidates a correctly propagated interval.

    Per event: the point-selected candidate, bootstrap selection frequency for
    every legal `z`, the legal-set size, and two concentration readings (the
    Herfindahl sum of squared shares, and entropy normalized to [0,1] over the
    legal set). Ties resolve to the first candidate in insertion order, exactly
    as the primary bootstrap's `max(...)` does."""
    rng = np.random.default_rng(selection_diagnostic_seed(seed))
    iters = int(iters)
    out: list[dict] = []

    for event in events:
        candidates = event.get("candidates", {})
        z_ids = list(candidates)
        if not z_ids or iters <= 0:
            out.append({"legal_set_size": len(z_ids), "point_selected": None,
                        "selection_frequency": {}, "concentration_hhi": None,
                        "normalized_entropy": None, "bootstrap_iters": iters})
            continue

        # Vectorized: one (iters x n_select) resample per candidate, then a
        # single argmax across candidates per iteration.
        means = np.empty((len(z_ids), iters), dtype=float)
        for k, z in enumerate(z_ids):
            sel = np.asarray(candidates[z]["select"], dtype=float)
            if sel.size == 0:
                means[k] = -np.inf
                continue
            idx = rng.integers(0, sel.size, size=(iters, sel.size))
            means[k] = sel[idx].mean(axis=1)

        winners = np.argmax(means, axis=0)
        counts = np.bincount(winners, minlength=len(z_ids))
        freq = {z_ids[k]: float(counts[k]) / iters for k in range(len(z_ids))}

        hhi = float(sum(p * p for p in freq.values()))
        shares = [p for p in freq.values() if p > 0.0]
        entropy = -float(sum(p * math.log(p) for p in shares))
        normalized_entropy = (entropy / math.log(len(z_ids))) if len(z_ids) > 1 else 0.0

        out.append({
            "legal_set_size": len(z_ids),
            "point_selected": select_maximizer({z: candidates[z]["select"] for z in z_ids}),
            "selection_frequency": freq,
            "concentration_hhi": hhi,
            "normalized_entropy": float(normalized_entropy),
            "bootstrap_iters": iters,
        })
    return out


def equal_topology_weighted_mean(per_topology_values: list[list[float]]) -> float:
    """Section 9: aggregate per-topology means FIRST, then average
    topologies with EQUAL weight -- never a flat pool of every event across
    every topology, which silently weights each topology by how many events
    it happened to contribute. A topology contributing zero values here is a
    support miss for this resample and is excluded from the topology
    average, never treated as a zero.

    Fixed defect (measured): flat pooling of a construction with unequal
    per-topology event counts returned 2.0973 where equal topology weighting
    gives the correct 1.2500 (see the paired unit test for the hand-worked
    arithmetic)."""
    topo_means = [float(np.mean(vals)) for vals in per_topology_values if len(vals) > 0]
    if not topo_means:
        return float("nan")
    return float(np.mean(topo_means))


def draw_shared_topology_indices(*, n_topo: int, iters: int, seed: int) -> np.ndarray:
    """Section 8 / Q-I1's common resampling stream: the topology-with-
    replacement draw for every bootstrap iteration, pre-drawn ONCE and
    shared by every primary quantity (`B_stable`, `B_flex`, both `U*`, both
    `T_m`, the Part-A contrast) so their between-topology covariance is
    preserved -- "All primary quantities use the same topology/episode
    bootstrap indices. Do not assign separate resampling seeds to stable,
    flex and B_m, because that would discard their covariance."

    This function's own RNG is used for NOTHING else, so its output is a
    pure function of `(n_topo, iters, seed)` alone, independent of how many
    events any quantity later resamples within a topology. Returns shape
    `(iters, n_topo)`."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, int(n_topo), size=(int(iters), int(n_topo)))


def hierarchical_bootstrap_quantity(topology_units: list[list[dict]], *,
                                     shared_topology_indices: np.ndarray,
                                     seed: int) -> dict:
    """Full section 8 / Q-I1 joint bootstrap for ONE primary quantity (a
    `U*_m` or a `B_m`, whichever `topology_units` encodes -- see
    `hierarchical_bootstrap_events` for `B_m`'s degenerate one-candidate
    reuse of the same machinery).

    Topology-level resampling comes ENTIRELY from `shared_topology_indices`
    (see `draw_shared_topology_indices`), never redrawn here, so every
    quantity called with the SAME shared array uses IDENTICAL topology
    indices every iteration regardless of its own per-topology event count.

    Within each resampled topology, its own episode/event resample and the
    inner rerun-selection bootstrap are seeded per-iteration-per-slot from
    `(seed, iteration, slot)` -- independent of every other quantity and of
    every other iteration. This is the fix for the measured regression ("the
    current per-call variate consumption diverges after iteration 0"): the
    previous implementation drew topology indices from a single long-lived
    `rng` that ALSO absorbed each quantity's own variable-length per-topology
    event draws in between topology draws, so two quantities with different
    per-topology event counts silently desynchronized after iteration 0.
    Reseeding fresh per iteration here means no iteration can leak state into
    the next, and topology indices never depend on anything but the shared
    array.

    Aggregation is EQUAL topology weighting (section 9, see
    `equal_topology_weighted_mean`): each resampled topology's own mean is
    computed first (via one `hierarchical_bootstrap_events` call per
    topology slot), then topology means are averaged with equal weight.
    """
    iters, n_topo = shared_topology_indices.shape
    u_star_iters = np.empty(iters, dtype=float)
    for i in range(iters):
        topo_idx = shared_topology_indices[i]
        topo_means: list[float] = []
        for slot, ti in enumerate(topo_idx):
            events = topology_units[int(ti)]
            if not events:
                continue  # support miss for this resampled topology slot
            ev_rng = np.random.default_rng((int(seed), int(i), int(slot)))
            ev_pick = ev_rng.integers(0, len(events), size=len(events))
            resampled_events = [events[j] for j in ev_pick]
            inner_seed = int(ev_rng.integers(0, 2**63 - 1))
            inner = hierarchical_bootstrap_events(
                resampled_events, iters=1, seed=inner_seed, compute_point=False
            )
            topo_means.append(inner["u_star_iters"][0])
        u_star_iters[i] = float(np.mean(topo_means)) if topo_means else float("nan")
    finite = u_star_iters[np.isfinite(u_star_iters)]
    return {
        "u_star_iters": u_star_iters,
        "lo": float(np.percentile(finite, 5)) if finite.size else float("nan"),
        "hi": float(np.percentile(finite, 95)) if finite.size else float("nan"),
    }


def topology_weighted_point_estimate(topology_units: list[list[dict]]) -> float:
    """Section 9's equal-topology-weighted TRUE point estimate for one
    primary quantity (a `B_m` or a `U*_m`) -- reuses the SAME point path
    `hierarchical_bootstrap_quantity` never touches:
    `hierarchical_bootstrap_events(..., compute_point=True)` returns
    `point`, computed via the true-argmax `select_maximizer` with NO RNG
    consumption. `iters=0` skips the (unused, RNG-consuming) resampling
    loop entirely -- only the `point` key is read, so this costs one
    O(n_events) pass per topology and nothing else.

    A topology contributing zero events is excluded from the average, never
    treated as a zero -- mirrors `hierarchical_bootstrap_quantity`'s own
    "support miss for this resampled topology slot" handling, and
    aggregation is equal topology weighting: each topology's own point is
    computed first, then topology points are averaged with equal weight."""
    topo_points = [
        hierarchical_bootstrap_events(events, iters=0, seed=0, compute_point=True)["point"]
        for events in topology_units if events
    ]
    return float(np.mean(topo_points)) if topo_points else float("nan")


def compute_t_m_bootstrap(*, b_stable_topology_units: list[list[dict]],
                           b_flex_topology_units: list[list[dict]],
                           u_star_stable_topology_units: list[list[dict]],
                           u_star_flex_topology_units: list[list[dict]],
                           n_topo: int, iters: int = BOOTSTRAP_ITERS,
                           seed: int = BOOTSTRAP_SEED) -> dict:
    """Section 8's T_m inference, producing exactly the inputs `decide_branch`
    consumes: `T_stable = U*_stable + 0.10*B_stable` with its UCB95 (and
    LCB95, for the branch-6/9 affirmative-miss checks), `T_flex = U*_flex -
    0.10*B_flex` with its LCB95 (and UCB95, for branch 6/8), and LCB95 of
    both `B_m`. All four primary quantities share ONE pre-drawn topology
    resampling stream (`draw_shared_topology_indices`), so per-iteration
    `T_m` values are combined from `U*_m` and `B_m` draws that came from the
    SAME resampled topology mix -- required for the linear combination to be
    a valid joint bootstrap sample rather than two independently-resampled
    quantities incorrectly added together."""
    shared = draw_shared_topology_indices(n_topo=n_topo, iters=iters, seed=seed)
    b_stable = hierarchical_bootstrap_quantity(
        b_stable_topology_units, shared_topology_indices=shared, seed=seed)
    b_flex = hierarchical_bootstrap_quantity(
        b_flex_topology_units, shared_topology_indices=shared, seed=seed)
    u_stable = hierarchical_bootstrap_quantity(
        u_star_stable_topology_units, shared_topology_indices=shared, seed=seed)
    u_flex = hierarchical_bootstrap_quantity(
        u_star_flex_topology_units, shared_topology_indices=shared, seed=seed)

    t_stable_iters = u_stable["u_star_iters"] + MATERIALITY_COEFFICIENT * b_stable["u_star_iters"]
    t_flex_iters = u_flex["u_star_iters"] - MATERIALITY_COEFFICIENT * b_flex["u_star_iters"]
    t_stable_finite = t_stable_iters[np.isfinite(t_stable_iters)]
    t_flex_finite = t_flex_iters[np.isfinite(t_flex_iters)]

    # Point estimates (item 2, 2026-07-27 ruling): every point needed to
    # evaluate the frozen section 9 predicate, computed via the SAME
    # true-argmax point path the bounds above never touch (RNG-free), so
    # adding them cannot perturb a single bound computed above -- those six
    # values are unchanged from this point on.
    b_stable_point = topology_weighted_point_estimate(b_stable_topology_units)
    b_flex_point = topology_weighted_point_estimate(b_flex_topology_units)
    u_star_stable_point = topology_weighted_point_estimate(u_star_stable_topology_units)
    u_star_flex_point = topology_weighted_point_estimate(u_star_flex_topology_units)
    t_stable_point = u_star_stable_point + MATERIALITY_COEFFICIENT * b_stable_point
    t_flex_point = u_star_flex_point - MATERIALITY_COEFFICIENT * b_flex_point

    return {
        "b_stable_lcb": b_stable["lo"],
        "b_flex_lcb": b_flex["lo"],
        "t_stable_ucb": float(np.percentile(t_stable_finite, 95)) if t_stable_finite.size else float("nan"),
        "t_stable_lcb": float(np.percentile(t_stable_finite, 5)) if t_stable_finite.size else float("nan"),
        "t_flex_lcb": float(np.percentile(t_flex_finite, 5)) if t_flex_finite.size else float("nan"),
        "t_flex_ucb": float(np.percentile(t_flex_finite, 95)) if t_flex_finite.size else float("nan"),
        "b_stable_point": b_stable_point,
        "b_flex_point": b_flex_point,
        "u_star_stable_point": u_star_stable_point,
        "u_star_flex_point": u_star_flex_point,
        "t_stable_point": t_stable_point,
        "t_flex_point": t_flex_point,
        "shared_topology_indices": shared,
    }


# =============================================================================
# Orchestration -- real environment wiring
# =============================================================================

def build_config():
    import config_1
    return config_1.Config(preset=PRESET)


def draw_energy_permutation(*, energy_seed: int) -> np.ndarray:
    """G2 RNG-separation rule: a fresh private permutation of `heldout_low`
    each episode, drawn from a stream that never touches the environment's
    own user-motion/channel/station/action RNG."""
    perm = np.random.default_rng(int(energy_seed)).permutation(HELDOUT_LOW.size)
    return HELDOUT_LOW[perm].astype(float).copy()


def apply_energy_profile(env, energies: np.ndarray) -> None:
    env.uav_battery_ratios = energies.copy()
    env._update_return_energy_state()


AGENT_NAME_FMT = "uav_{}"


def agent_name(uav_idx: int) -> str:
    return AGENT_NAME_FMT.format(int(uav_idx))


# =============================================================================
# Item 1 -- real-env duty geometry (the constructive_mixed/null "targets" the
# pure duty-map layer needs, wired to live UAV/user/BS geometry)
# =============================================================================

N_RELAY_DUTIES = 2
N_SERVICE_DUTIES = 6
# Registered split for the 8-UAV S7-S3 fleet: reuses the SAME service/relay
# count the environment's own offline feasibility heuristic tries FIRST
# (`estimate_heuristic_qos_feasibility`,
# envs/pettingzoo/scenario7_energy_aware.py:1194-1198: candidates
# {n_uavs-2, n_uavs-3} tried in that preference order, i.e. 6 service / 2
# relay before 5/3) -- a grounded, deterministic choice rather than an
# invented split, fixed (not searched) here because a scripted per-step
# controller must commit to one duty count every step, not grid-search a
# static layout the way the offline certificate does.


def compute_service_duty_targets(user_xy: np.ndarray, n_service: int,
                                  prior_centroids: Optional[np.ndarray] = None,
                                  iters: int = 30) -> np.ndarray:
    """Lloyd's-iteration centroid update over LIVE user xy positions,
    warm-started from the PRIOR step's centroids so duty identity (which
    physical cluster is "duty 2") stays stable across steps instead of
    being re-seeded from scratch every call -- re-seeding every step would
    let k-means relabel clusters arbitrarily and destroy the "preserve
    target between lifecycle events" requirement (section 4). Mirrors the
    seeding/iteration scheme of the environment's own
    `estimate_heuristic_qos_feasibility`
    (envs/pettingzoo/scenario7_energy_aware.py:1199-1220), the only prior
    art in this repository for clustering `user_positions`."""
    user_xy = np.asarray(user_xy, dtype=float)
    if prior_centroids is not None and len(prior_centroids) == n_service:
        centroids = np.asarray(prior_centroids, dtype=float).copy()
    else:
        seed_indices = np.linspace(0, len(user_xy) - 1, n_service, dtype=int)
        centroids = user_xy[seed_indices].copy()
    for _ in range(iters):
        distances = np.sum((user_xy[:, None, :] - centroids[None, :, :]) ** 2, axis=2)
        labels = np.argmin(distances, axis=1)
        updated = np.array([
            np.mean(user_xy[labels == k], axis=0) if np.any(labels == k) else centroids[k]
            for k in range(n_service)
        ])
        if np.allclose(updated, centroids):
            break
        centroids = updated
    return centroids


def compute_relay_duty_targets(bs_xy: np.ndarray, service_center: np.ndarray,
                                n_relay: int) -> list:
    """Relay duties positioned along the ground-BS-to-service-center line,
    mirroring `estimate_heuristic_qos_feasibility`
    (envs/pettingzoo/scenario7_energy_aware.py:1229-1231)."""
    targets = []
    bs_xy = np.asarray(bs_xy, dtype=float)
    service_center = np.asarray(service_center, dtype=float)
    for relay_idx in range(n_relay):
        fraction = (relay_idx + 1) / (n_relay + 1)
        targets.append((1.0 - fraction) * bs_xy + fraction * service_center)
    return targets


def compute_duty_positions(env, prior_service_centroids: Optional[np.ndarray] = None):
    """Full per-step duty-target geometry: duty ids `0..N_RELAY_DUTIES-1` are
    relay duties, `N_RELAY_DUTIES..N_RELAY_DUTIES+N_SERVICE_DUTIES-1` are
    service duties (live k-means centroids of current `user_positions`).
    Returns `(duty_positions: dict[int, np.ndarray(3,)], service_centroids)`
    -- callers pass `service_centroids` back in as `prior_service_centroids`
    next step to warm-start duty identity."""
    user_xy = np.asarray(env.user_positions, dtype=float)[:, :2]
    bs_xy = np.mean(np.asarray(env.ground_bs_positions, dtype=float)[:, :2], axis=0)
    centroids = compute_service_duty_targets(user_xy, N_SERVICE_DUTIES, prior_service_centroids)
    service_center = np.mean(centroids, axis=0)
    relay_xy = compute_relay_duty_targets(bs_xy, service_center, N_RELAY_DUTIES)
    height = float(np.mean(env.height_range))
    duty_positions: dict = {}
    for i, xy in enumerate(relay_xy):
        duty_positions[i] = np.array([xy[0], xy[1], height])
    for i, xy in enumerate(centroids):
        duty_positions[N_RELAY_DUTIES + i] = np.array([xy[0], xy[1], height])
    return duty_positions, centroids


def initial_duty_map() -> dict:
    """Registered fleet shape: 8 duties / 8 UAVs, identity assignment at
    episode start. Arbitrary in the same sense the environment's own agent
    index ordering is arbitrary -- no operational meaning attaches to which
    UAV starts on which duty."""
    return {i: i for i in range(N_RELAY_DUTIES + N_SERVICE_DUTIES)}


def domain_bounds_for_env(env):
    lo = np.array([0.0, 0.0, float(env.height_range[0])])
    hi = np.array([float(env.area_size), float(env.area_size), float(env.height_range[1])])
    return lo, hi


# =============================================================================
# REGISTERED_CONSTANT: DOCK_TRIGGER_RULE -- latest-safe-station-arrival
# dock-decision formula (item 1)
# =============================================================================
#
# The frozen contract and the G2 design describe `constructive_mixed`'s
# REQUIRED BEHAVIOR ("forward-plans only its scripted energy evolution,
# schedules the latest safe station arrival") but neither specifies the
# internal trigger arithmetic numerically -- this is an ordinary
# implementation choice, frozen here as one exact constant formula so a
# later conformance derivation has a single rule to check against rather
# than an implicit runtime decision.
#
#   Let d_i        = straight-line distance from UAV i's current position
#                     to its nearest charging station
#                     (`env._nearest_charging_station`)
#       t_transit_i = ceil(d_i / (max_speed * dt))    -- worst-case transit
#                     steps at full CRUISE speed, never the slower emergency
#                     limp-home speed, because this is a PROACTIVE plan
#                     while the UAV is still fully mobile, not an emergency
#       E_transit_i = t_transit_i * calculate_power_consumption(max_speed, 0) * dt / 3600
#       dock_trigger_ratio_i = E_transit_i / battery_capacity_wh + return_reserve_ratio
#
# A UAV departs for the station (heads toward it, requesting docking) at
# the LATEST pre-action boundary at which `battery_ratio_i <=
# dock_trigger_ratio_i` still holds -- i.e. the step immediately before
# this predicate would first go False is "latest safe." This function is
# re-evaluated fresh every step from LIVE state (never a schedule built
# once at reset), so the controller naturally departs at exactly that step.
#
# `return_reserve_ratio` is the environment's OWN registered safety-buffer
# constant (0.10, envs/pettingzoo/scenario7_energy_aware.py:100) -- reused
# here rather than reinvented, so the scripted controller's forward energy
# plan shares the environment's own reserve rather than introducing a
# second, uncoordinated number.
def dock_trigger_ratio(*, distance_m: float, max_speed: float, dt: float,
                        power_transit_w: float, battery_capacity_wh: float,
                        return_reserve_ratio: float) -> float:
    t_transit = transit_steps(distance_m, max_speed=max_speed, dt=dt)
    e_transit_wh = t_transit * power_transit_w * dt / 3600.0
    return e_transit_wh / max(battery_capacity_wh, 1e-8) + return_reserve_ratio


def should_depart_for_charge(*, battery_ratio: float, trigger_ratio: float) -> bool:
    return battery_ratio <= trigger_ratio


def dock_trigger_ratio_for_env(env, uav_idx: int, distance_m: float) -> float:
    """Binds `dock_trigger_ratio` to the real env's registered constants --
    the orchestration-boundary counterpart of `flex_transit_steps_for_env`."""
    power_transit_w = float(env._calculate_power_consumption(float(env.max_speed), 0.0))
    return dock_trigger_ratio(
        distance_m=distance_m, max_speed=float(env.max_speed), dt=float(env.time_step),
        power_transit_w=power_transit_w,
        battery_capacity_wh=float(env.battery_capacity_wh),
        return_reserve_ratio=float(getattr(env, "return_reserve_ratio", 0.10)),
    )


# =============================================================================
# Action synthesis: env action <- target position (item 1)
# =============================================================================

def action_towards_target(position, target, *, max_speed: float,
                           max_vertical_speed_mps: float, dt: float,
                           dock_request: bool) -> np.ndarray:
    """Builds the 4-vector env action driving directly toward `target`,
    mirroring the environment's OWN action->velocity contract exactly
    (`_normalize_continuous_action`/`_movement_velocity_from_action`,
    envs/pettingzoo/scenario7_energy_aware.py:1584-1634): the horizontal
    component is direction-normalized THEN scaled by the reachable
    fraction (never per-axis clipped first), so per-axis [-1,1] clamping
    can never distort the intended direction; magnitude is capped at
    `max_speed`; the target is reached exactly if reachable within one
    `dt`. `action[3]` is the dock-request bit."""
    delta = np.asarray(target, dtype=float) - np.asarray(position, dtype=float)
    horizontal = delta[:2]
    h_norm = float(np.linalg.norm(horizontal))
    if h_norm > 1e-9:
        direction = horizontal / h_norm
        frac = min(h_norm / max(max_speed * dt, 1e-9), 1.0)
        action_xy = direction * frac
    else:
        action_xy = np.zeros(2, dtype=float)
    vertical_delta = float(delta[2]) if delta.shape[0] > 2 else 0.0
    vertical_speed_needed = vertical_delta / max(dt, 1e-9)
    action_z = float(np.clip(vertical_speed_needed / max(max_vertical_speed_mps, 1e-9), -1.0, 1.0))
    return np.array([action_xy[0], action_xy[1], action_z, 1.0 if dock_request else 0.0],
                     dtype=np.float32)


def scripted_source_actions(env, *, duty_map: dict, duty_positions: dict,
                             target_override: Optional[dict] = None) -> dict:
    """One step of the real-env realization of `constructive_mixed`/`null`
    (the two share this SAME per-UAV action rule -- they differ only in how
    `duty_map` is updated across LEAVE/REJOIN, driven separately by
    `update_duty_map_on_transitions`): every airborne UAV either (a)
    continues charging in place if already docked and below
    `REJOIN_BATTERY_RATIO`, (b) heads to its nearest charging station and
    requests docking once the REGISTERED_CONSTANT dock-trigger rule fires,
    or (c) otherwise flies to its assigned duty's live target.
    `target_override` forces a specific UAV's target for this step
    regardless of (a)/(b)/(c) -- the intervention machinery's SET arm."""
    uav_to_duty = {u: d for d, u in duty_map.items()}
    actions: dict = {}
    dt = float(env.time_step)
    max_speed = float(env.max_speed)
    max_vert = float(getattr(env, "max_vertical_speed_mps", 5.0))
    n_uavs = int(env.n_uavs)
    for i in range(n_uavs):
        pos = np.asarray(env.uav_positions[i], dtype=float)
        battery = float(env.uav_battery_ratios[i])
        charging = bool(env.uav_charging[i])
        if target_override is not None and i in target_override:
            target = np.asarray(target_override[i], dtype=float)
            actions[agent_name(i)] = action_towards_target(
                pos, target, max_speed=max_speed, max_vertical_speed_mps=max_vert,
                dt=dt, dock_request=False)
            continue
        if charging:
            if battery < REJOIN_BATTERY_RATIO:
                actions[agent_name(i)] = action_towards_target(
                    pos, pos, max_speed=max_speed, max_vertical_speed_mps=max_vert,
                    dt=dt, dock_request=True)
            else:
                duty_id = uav_to_duty.get(i)
                target = duty_positions[duty_id] if duty_id is not None else pos
                actions[agent_name(i)] = action_towards_target(
                    pos, target, max_speed=max_speed, max_vertical_speed_mps=max_vert,
                    dt=dt, dock_request=False)
            continue
        station_idx, _, distance = env._nearest_charging_station(i)
        trigger = dock_trigger_ratio_for_env(env, i, distance) if station_idx >= 0 else -1.0
        if station_idx >= 0 and should_depart_for_charge(battery_ratio=battery, trigger_ratio=trigger):
            station_pos = np.asarray(env.charging_station_positions[station_idx], dtype=float)
            actions[agent_name(i)] = action_towards_target(
                pos, station_pos, max_speed=max_speed, max_vertical_speed_mps=max_vert,
                dt=dt, dock_request=True)
        else:
            duty_id = uav_to_duty.get(i)
            target = duty_positions[duty_id] if duty_id is not None else pos
            actions[agent_name(i)] = action_towards_target(
                pos, target, max_speed=max_speed, max_vertical_speed_mps=max_vert,
                dt=dt, dock_request=False)
    return actions


# =============================================================================
# Item 2 -- LEAVE/REJOIN duty-map bookkeeping and per-step metrics extraction
# =============================================================================

def update_duty_map_on_transitions(*, duty_map: dict, duty_positions: dict, env,
                                    charging_before: np.ndarray, charging_after: np.ndarray,
                                    schedule: str, locked_duties: frozenset = frozenset(),
                                    step_index: int = 0):
    """Detects LEAVE (rising edge of `uav_charging`) and REJOIN (falling
    edge) per UAV and drives `duty_map` through the already-accepted PURE
    `constructive_mixed_update`/`null_update` functions -- never
    reimplements their reassignment logic. Returns
    `(new_duty_map, leave_uavs, rejoin_uavs)`.

    `schedule == "full_sync_SET"` (Part-A conformance diagnostic, section 4:
    "reassigns every duty at each check", stable limb only, never applied on
    the flex limb) bypasses the LEAVE/REJOIN edge-driven update entirely and
    recomputes the WHOLE duty map from scratch via the already-accepted
    `full_sync_set_update` -- it never preserves any incumbent, locked or not.

    CADENCE (Stage B repair, Pro ruling 2026-07-26): that recomputation happens
    only at a **shared check boundary**, `step_index % DELTA == 0`, not on every
    primitive step. The contract defines this control as reassigning "every duty
    at each check"; an every-step realization is a materially stronger control.
    Because `full_sync_SET` supplies `D_A`, its cadence can decide whether
    `PART_A_CONTRADICTION` fires, so this is claim-bearing rather than
    cosmetic. Between checks the duty map is carried forward unchanged, which is
    what "reassigns at each check" means for the steps in between."""
    charging_before = np.asarray(charging_before, dtype=bool)
    charging_after = np.asarray(charging_after, dtype=bool)
    leave_uavs = [i for i in range(len(charging_after)) if charging_after[i] and not charging_before[i]]
    rejoin_uavs = [i for i in range(len(charging_after)) if charging_before[i] and not charging_after[i]]
    airborne_positions = {
        i: np.asarray(env.uav_positions[i], dtype=float)
        for i in range(int(env.n_uavs)) if not charging_after[i]
    }
    if schedule == "full_sync_SET":
        if int(step_index) % int(DELTA) == 0:
            new_map = full_sync_set_update(
                duty_positions=duty_positions, airborne_positions=airborne_positions)
        else:
            new_map = dict(duty_map)      # between checks: carried forward, not reassigned
        return new_map, leave_uavs, rejoin_uavs
    new_map = dict(duty_map)
    for u in leave_uavs:
        if schedule == "null":
            new_map = null_update(duty_map=new_map)
        else:
            new_map = constructive_mixed_update(
                duty_map=new_map, duty_positions=duty_positions,
                airborne_positions=airborne_positions, event="LEAVE",
                event_uav=u, locked_duties=locked_duties)
    for u in rejoin_uavs:
        if schedule == "null":
            new_map = null_update(duty_map=new_map)
        else:
            new_map = constructive_mixed_update(
                duty_map=new_map, duty_positions=duty_positions,
                airborne_positions=airborne_positions, event="REJOIN",
                event_uav=u, locked_duties=locked_duties)
    return new_map, leave_uavs, rejoin_uavs


def per_user_qos_ratio(env) -> np.ndarray:
    """The per-(user) QoS-ratio vector `user_step_saturation_fraction` needs
    -- never exposed by the env's info dict (only its mean is), so it is
    reconstructed here from the same public fields the environment's own
    reward computation uses (`last_user_rates_mbps`, `user_qos_rate_mbps`)."""
    rates = np.asarray(getattr(env, "last_user_rates_mbps", []), dtype=float)
    qos_rate = max(float(getattr(env, "user_qos_rate_mbps", 1.0)), 1e-8)
    return np.clip(rates / qos_rate, 0.0, 1.0)


def extract_step_metrics(env, infos: dict) -> dict:
    """Pulls the section-7 primary-G component fields out of one
    `env.step()` call's `infos` (every agent's `reward_info` carries the
    same episode-level scalar fields -- `_energy_metrics_dict`/
    `_calculate_constrained_safety_reward`,
    envs/pettingzoo/scenario7_energy_aware.py:607-618), plus the per-UAV
    cutoff/depletion masks reconstructed from live battery state (the
    per-UAV masks are never in `infos` -- only `cutoff_event_count`/
    `depletion_event_count` scalars are, and those are EPISODE-latched,
    the wrong thing for window-local latching; see the module's real-env
    note in its header)."""
    first_agent = next(iter(infos))
    reward_info = infos[first_agent].get("reward_info", {})
    battery = np.asarray(env.uav_battery_ratios, dtype=float)
    cutoff_mask = battery <= float(getattr(env, "service_cutoff_threshold", 0.02))
    depletion_mask = battery <= float(getattr(env, "depleted_battery_threshold", 0.0))
    return {
        "qos_satisfaction_ratio": float(reward_info.get("qos_satisfaction_ratio", 0.0)),
        "return_constraint_cost": float(reward_info.get("return_constraint_cost", 0.0)),
        "return_constraint_cost_raw": float(reward_info.get("return_constraint_cost_raw", 0.0)),
        "cutoff_mask": cutoff_mask,
        "depletion_mask": depletion_mask,
    }


def real_env_state_snapshot(env, duty_map: dict) -> dict:
    """The exact fixed-history surface section 8/Q-I2 requires hashed:
    positions, battery, charging state, station/queue state, duty map and
    lifecycle mask (CHARGE_ABSENT == `uav_charging`, per the module's own
    two-state real-env realization documented in its header)."""
    charging = np.asarray(env.uav_charging, dtype=bool)
    return {
        "positions": np.asarray(env.uav_positions, dtype=float),
        "battery_ratios": np.asarray(env.uav_battery_ratios, dtype=float),
        "charging_mask": charging,
        "station_occupancy": np.asarray(env.station_occupancy, dtype=float),
        "station_queue": np.asarray(env.station_queue_lengths, dtype=float),
        "lifecycle_mask": charging,
        "duty_map": dict(duty_map),
    }


def step_once(env, *, duty_map: dict, service_centroids: Optional[np.ndarray],
              schedule: str = "constructive_mixed", target_override: Optional[dict] = None,
              locked_duties: frozenset = frozenset(), step_index: int = 0) -> dict:
    """The atomic real-env step: compute live duty geometry, synthesize
    every UAV's action (item 1), step the env (energy accounting runs
    inside `env.step`), then drive the duty map through any LEAVE/REJOIN
    edge (item 2)."""
    duty_positions, service_centroids_next = compute_duty_positions(env, service_centroids)
    charging_before = np.asarray(env.uav_charging, dtype=bool).copy()
    actions = scripted_source_actions(env, duty_map=duty_map, duty_positions=duty_positions,
                                       target_override=target_override)
    action_record = {a: np.asarray(v).copy() for a, v in actions.items()}
    # `env.step` returns `(observations, rewards, terminations, truncations,
    # infos)` -- the real `UAVEnergyAwareRelayEnv` never caches this as a
    # `self.infos` attribute (confirmed: `scenario_base.py:3547` returns the
    # tuple directly, no assignment to `self`), so the return value MUST be
    # captured here. An earlier version of this function discarded it and
    # read `env.infos` instead, which silently fell back to an all-zero
    # metrics stub for every real-env step -- caught only by re-reading the
    # real env's own step() source during the pre-return inspection, since
    # the FakeEnv test double happened to also expose a `self.infos` side
    # channel that masked the same defect.
    step_return = env.step(actions)
    infos = step_return[4] if step_return is not None else {}
    charging_after = np.asarray(env.uav_charging, dtype=bool).copy()
    new_map, leave_uavs, rejoin_uavs = update_duty_map_on_transitions(
        duty_map=duty_map, duty_positions=duty_positions, env=env,
        charging_before=charging_before, charging_after=charging_after,
        schedule=schedule, locked_duties=locked_duties, step_index=step_index)
    metrics = extract_step_metrics(env, infos) if infos else {
        "qos_satisfaction_ratio": 0.0, "return_constraint_cost": 0.0,
        "return_constraint_cost_raw": 0.0,
        "cutoff_mask": np.asarray(env.uav_battery_ratios, dtype=float) <= float(
            getattr(env, "service_cutoff_threshold", 0.02)),
        "depletion_mask": np.asarray(env.uav_battery_ratios, dtype=float) <= float(
            getattr(env, "depleted_battery_threshold", 0.0)),
    }
    return {
        "actions": action_record,
        "duty_positions": duty_positions,
        "service_centroids": service_centroids_next,
        "duty_map": new_map,
        "leave_uavs": leave_uavs,
        "rejoin_uavs": rejoin_uavs,
        "charging_before": charging_before,
        "charging_after": charging_after,
        "metrics": metrics,
        "qos_user_step": per_user_qos_ratio(env),
    }


# =============================================================================
# Section 2 evaluator-only forward replay, on a CLONE (item 2)
# =============================================================================

def evaluator_forward_replay(env, *, duty_map: dict, service_centroids: Optional[np.ndarray],
                              delta_steps: int = DELTA) -> dict:
    """Section 2's evaluator-only forward replay: an independent CLONE of
    the pinned env (never the real rollout) is advanced `delta_steps` under
    the UNPERTURBED `constructive_mixed` continuation, purely to certify
    stable/flex predicates -- it never contributes to the recorded episode
    or its replay prefix. A state-hash equality assertion runs immediately
    after cloning, before any step, so a divergent clone can never silently
    contaminate certification."""
    hash_before = compute_state_hash(real_env_state_snapshot(env, duty_map))
    clone = copy.deepcopy(env)
    hash_clone = compute_state_hash(real_env_state_snapshot(clone, duty_map))
    assert_state_hash_equal(hash_before, hash_clone, context="evaluator forward-replay clone")

    clone_duty_map = dict(duty_map)
    clone_centroids = None if service_centroids is None else np.asarray(service_centroids).copy()
    charging_ever = np.zeros(int(env.n_uavs), dtype=bool)
    duty_positions_final = None
    for _ in range(int(delta_steps)):
        step = step_once(clone, duty_map=clone_duty_map, service_centroids=clone_centroids,
                          schedule="constructive_mixed")
        clone_duty_map = step["duty_map"]
        clone_centroids = step["service_centroids"]
        duty_positions_final = step["duty_positions"]
        charging_ever |= step["charging_after"]
    return {
        "charging_ever": charging_ever,
        "duty_positions_final": duty_positions_final if duty_positions_final is not None else {},
        "duty_map_final": clone_duty_map,
    }


# =============================================================================
# Item 2 -- LEAVE-candidate assembly and joint-event search
# =============================================================================

def build_leave_candidate(env, *, uav_idx: int, t_e_step: int, schedule: str,
                           station_occupancy_after: np.ndarray, station_queue_after: np.ndarray,
                           cutoff_before: bool, depletion_before: bool) -> dict:
    """Assembles one LEAVE candidate's eligibility+conformance fields from
    real env state observed AT the LEAVE step -- the exact fields
    `check_leave_eligibility`/`build_event_conformance_record` consume.
    Occupancy/queue are read POST-step ("at the moment of capture", per
    `check_leave_eligibility`'s own docstring), with the capturing UAV's own
    slot subtracted so a 1-slot station's successful, uncontested capture
    reads as zero contention rather than spuriously excluding itself."""
    station_idx = int(env.uav_target_stations[uav_idx])
    occ_excl_self = max(0.0, float(station_occupancy_after[station_idx])) - 1.0 if station_idx >= 0 else 0.0
    occ_excl_self = max(0.0, occ_excl_self)
    queue_len = float(station_queue_after[station_idx]) if station_idx >= 0 else 0.0
    last_arrival = np.asarray(getattr(env, "last_charging_arrival",
                                       np.zeros(env.n_uavs, dtype=bool)))
    return {
        "t_e": int(t_e_step),
        "uav_idx": int(uav_idx),
        "station_occupancy_excluding_self": occ_excl_self,
        "station_queue_length": queue_len,
        "cutoff_at_leave": bool(cutoff_before),
        "depletion_at_leave": bool(depletion_before),
        "temporary_failure": bool(np.asarray(getattr(
            env, "uav_failed", np.zeros(env.n_uavs, dtype=bool)))[uav_idx]),
        "schedule_identity": schedule,
        "pre_service_status": "ACTIVE",
        "post_service_status": "CHARGE_ABSENT",
        "capture_edge": True,
        "last_charging_arrival": bool(last_arrival[uav_idx]),
        "uav_charging": True,
        "uav_dock_requests": bool(env.uav_dock_requests[uav_idx]),
        "uav_target_stations": station_idx,
        "battery_ratio": float(env.uav_battery_ratios[uav_idx]),
        "return_energy_margin": float(np.asarray(getattr(
            env, "uav_return_energy_margins", np.zeros(env.n_uavs)))[uav_idx]),
        "uav_position": np.asarray(env.uav_positions[uav_idx], dtype=float).tolist(),
        "station_position": (np.asarray(env.charging_station_positions[station_idx], dtype=float).tolist()
                              if station_idx >= 0 else None),
        "station_occupancy": occ_excl_self,
        "station_queue_length": queue_len,
    }


def _stable_candidates_at(*, duty_map: dict, duty_positions_before: dict,
                           duty_positions_after: dict, vacated_target, exclude_uav: int,
                           replay_forward: dict, domain_bounds) -> list:
    """Every OTHER active, duty-holding UAV as a stable-certification
    candidate, in ascending duty-id order (the canonical ordering already
    established for tie-breaks elsewhere in this module)."""
    candidates = []
    for d, u in sorted(duty_map.items()):
        if u == exclude_uav:
            continue
        target_before = duty_positions_before.get(d)
        target_after = replay_forward["duty_positions_final"].get(d)
        if target_before is None or target_after is None:
            continue
        displacement = float(np.linalg.norm(np.asarray(target_after[:2]) - np.asarray(target_before[:2])))
        legal = legal_set_targets(
            post_leave_targets=list(duty_positions_after.values()),
            vacated_pre_leave_target=vacated_target if vacated_target is not None else target_before,
            focal_incumbent_target=target_before, domain_bounds=domain_bounds)
        candidates.append({
            "uav": u, "duty": d, "legal_targets": legal,
            "kwargs": dict(active=True, has_valid_incumbent=True,
                           future_target_displacement_m=displacement,
                           scheduled_to_leave_within_delta=bool(replay_forward["charging_ever"][u]),
                           has_legal_set_alternative=len(legal) > 0),
        })
    return candidates


def _flex_survivors_at(env, *, duty_map: dict, vacated_target, exclude_uav: int) -> dict:
    survivors: dict = {}
    if vacated_target is None:
        return survivors
    for d, u in duty_map.items():
        if u == exclude_uav or bool(env.uav_charging[u]):
            continue
        distance = float(np.linalg.norm(
            np.asarray(env.uav_positions[u][:2], dtype=float) - np.asarray(vacated_target[:2], dtype=float)))
        transit = flex_transit_steps_for_env(env, distance)
        battery = float(env.uav_battery_ratios[u])
        power_transit = float(env._calculate_power_consumption(float(env.max_speed), 0.0))
        e_wh = transit * power_transit * float(env.time_step) / 3600.0
        support_ok = (battery - e_wh / max(float(env.battery_capacity_wh), 1e-8)) > 0.0
        survivors[u] = {"transit_steps": transit, "support_ok": support_ok}
    return survivors


def roll_prefix_and_find_event(env, *, max_step: int = T_E_MAX) -> dict:
    """Item 2's episode driver: rolls `constructive_mixed` from the env's
    CURRENT (already-reset/pinned) state, recording every action for later
    prefix replay, until the first joint-qualifying LEAVE (section 2/Q-E4)
    or `max_step` is exhausted. `t_e` is realized as the LEAVE's own step
    boundary (distance 0 from itself, which trivially satisfies "at most Y
    steps before t_e") since this realization has no reduced check cadence
    below one env step; per Q-E4, if stable does not certify at that t_e
    the search moves to the NEXT LEAVE entirely, never to a later step of
    the same LEAVE. Returns the joint event's full snapshot (duty map/
    positions, state hash, recorded action prefix) or `event=None` with the
    accumulated exclusion records on a support miss.

    Also returns the Q-E2 per-episode diagnostic counters: `leave_diagnostics`
    (one entry per OBSERVED LEAVE -- every ACTIVE->CHARGE_ABSENT capture edge
    under `constructive_mixed`, regardless of eligibility -- carrying its
    capture step, `departure_step` (the earliest step this UAV's
    `uav_dock_requests` rose before this capture, tracked as a rising edge
    the same way LEAVE/REJOIN are detected elsewhere in this module; falls
    back to the capture step itself if no onset was ever observed), uav id,
    battery ratio at that departure onset, and its mapped rejection reasons
    -- empty for whichever LEAVE ends up qualifying) and `rejected_counts`
    (the same information pre-tallied via `map_rejection_reasons`'s reporting
    vocabulary). Both are computed from reasons `check_leave_eligibility`/
    `certify_stable`/`certify_flex` already decided -- never re-derived."""
    duty_map = initial_duty_map()
    service_centroids = None
    recorded_actions: list = []
    exclusions: list = []
    domain_bounds = domain_bounds_for_env(env)

    n_uavs = int(env.n_uavs)
    dock_request_prev = np.zeros(n_uavs, dtype=bool)
    dock_onset_step: dict[int, int] = {}
    dock_onset_battery: dict[int, float] = {}
    leave_diagnostics: list = []
    rejected_counts = {k: 0 for k in REJECTION_REASON_KEYS}

    for t in range(int(max_step) + 1):
        battery_before = np.asarray(env.uav_battery_ratios, dtype=float).copy()
        cutoff_before = battery_before <= float(getattr(env, "service_cutoff_threshold", 0.02))
        depletion_before = battery_before <= float(getattr(env, "depleted_battery_threshold", 0.0))
        duty_map_before = dict(duty_map)
        duty_positions_before, _ = compute_duty_positions(env, service_centroids)

        step = step_once(env, duty_map=duty_map, service_centroids=service_centroids,
                          schedule="constructive_mixed")
        recorded_actions.append(step["actions"])
        duty_map = step["duty_map"]
        service_centroids = step["service_centroids"]

        # Departure-step tracking (Q-E2 diagnosis): a rising edge of
        # `uav_dock_requests`, mirroring the LEAVE/REJOIN edge detection
        # `update_duty_map_on_transitions` already performs on `uav_charging`.
        # `.copy()` is load-bearing: `env.uav_dock_requests` is already
        # bool-dtype, so `np.asarray(..., dtype=bool)` returns the SAME
        # array object rather than a snapshot (confirmed by a scratch
        # reproduction: without `.copy()`, an in-place mutation inside the
        # next `env.step()` call silently rewrites what `dock_request_prev`
        # points at too, so the rising-edge XOR always compares the array to
        # itself and no onset is ever recorded before capture).
        dock_request_after = np.asarray(env.uav_dock_requests, dtype=bool).copy()
        battery_after_step = np.asarray(env.uav_battery_ratios, dtype=float)
        for uu in np.nonzero(dock_request_after & ~dock_request_prev)[0]:
            dock_onset_step[int(uu)] = t + 1
            dock_onset_battery[int(uu)] = float(battery_after_step[uu])
        dock_request_prev = dock_request_after

        for u in step["leave_uavs"]:
            cand = build_leave_candidate(
                env, uav_idx=u, t_e_step=t + 1, schedule="constructive_mixed",
                station_occupancy_after=np.asarray(env.station_occupancy, dtype=float),
                station_queue_after=np.asarray(env.station_queue_lengths, dtype=float),
                cutoff_before=bool(cutoff_before[u]), depletion_before=bool(depletion_before[u]))
            capture_step = cand["t_e"]
            diag_entry = {
                "uav": int(u), "capture_step": int(capture_step),
                "departure_step": int(dock_onset_step.get(u, capture_step)),
                "battery_at_departure": float(dock_onset_battery.get(u, battery_before[u])),
            }
            elig_reasons = check_leave_eligibility(cand, t_e=cand["t_e"])
            if elig_reasons:
                reject_reasons = map_rejection_reasons(eligibility_reasons=elig_reasons)
                for r in reject_reasons:
                    rejected_counts[r] += 1
                diag_entry["rejected_reasons"] = sorted(reject_reasons)
                leave_diagnostics.append(diag_entry)
                exclusions.append({"t_e": cand["t_e"], "uav": u, "reasons": elig_reasons})
                continue

            hash_at_te = compute_state_hash(real_env_state_snapshot(env, duty_map))
            replay_forward = evaluator_forward_replay(
                env, duty_map=duty_map, service_centroids=service_centroids)

            vacated_duty = next((d for d, uu in duty_map_before.items() if uu == u), None)
            vacated_target = duty_positions_before.get(vacated_duty)

            stable_candidates = _stable_candidates_at(
                duty_map=duty_map, duty_positions_before=duty_positions_before,
                duty_positions_after=step["duty_positions"], vacated_target=vacated_target,
                exclude_uav=u, replay_forward=replay_forward, domain_bounds=domain_bounds)
            survivors = _flex_survivors_at(env, duty_map=duty_map, vacated_target=vacated_target,
                                            exclude_uav=u)
            legal_flex = legal_set_targets(
                post_leave_targets=list(step["duty_positions"].values()),
                vacated_pre_leave_target=vacated_target if vacated_target is not None else np.zeros(3),
                focal_incumbent_target=vacated_target if vacated_target is not None else np.zeros(3),
                domain_bounds=domain_bounds)
            flex_ok, flex_reasons, focal_flex = certify_flex(
                leave_step=t + 1, prior_check_step=t, t_e=t + 1,
                queue_or_cutoff_caused=False, survivors=survivors,
                has_legal_set_alternative=len(legal_flex) > 0)

            stable_ok = False
            stable_choice = None
            stable_reasons_all: set = set()
            for cand_s in stable_candidates:
                ok, reasons = certify_stable(**cand_s["kwargs"])
                if ok:
                    stable_ok = True
                    stable_choice = cand_s
                    stable_reasons_all = set()
                    break
                stable_reasons_all.update(reasons)

            if stable_ok and flex_ok:
                diag_entry["rejected_reasons"] = []
                leave_diagnostics.append(diag_entry)
                locked_for_stable = frozenset({stable_choice["duty"]})
                event = {
                    "t_e": t + 1,
                    "focal_flex_uav": focal_flex,
                    "focal_stable_uav": stable_choice["uav"],
                    "focal_stable_duty": stable_choice["duty"],
                    "duty_map_at_te": dict(duty_map),
                    "duty_positions_at_te": step["duty_positions"],
                    "service_centroids_at_te": service_centroids,
                    "hash_at_te": hash_at_te,
                    # R3 condition 1C: the complete-state fingerprint of the
                    # world the event was actually certified in, recorded HERE
                    # on the live environment. The snapshot must equal it.
                    # Duty positions and service centroids are bound into this
                    # SAME fingerprint (ruling 2026-07-27) so they are part of
                    # event identity, not side data the fingerprint is blind to.
                    "full_fingerprint_at_te": full_state_fingerprint(
                        env, duty_map=duty_map,
                        duty_positions=step["duty_positions"],
                        service_centroids=service_centroids),
                    "vacated_target": vacated_target,
                    "legal_targets": {
                        "stable": {_target_id(z): z for z in stable_choice["legal_targets"]},
                        "flex": {_target_id(z): z for z in legal_flex},
                    },
                    # Stage B repair (Pro ruling 2026-07-26). The stable limb
                    # used to receive `locked_for_flex` -- the FLEX focal's
                    # incumbent duty -- which froze a non-focal duty during the
                    # stable intervention. Section 1 says non-focal duties are
                    # never frozen: they are reoptimized one-to-one under
                    # `constructive_mixed`. Locking one restricted the stable
                    # SET joint continuation relative to the registered
                    # maximization and made SET look artificially costly, which
                    # biases TOWARD "persistence is necessary" -- the same
                    # claim-favouring asymmetry that disqualified n_select=1.
                    #
                    # The flex limb keeps `locked_for_stable`: preserving a
                    # genuinely certified stable incumbent IS `constructive_mixed`
                    # semantics ("preserves every active stable incumbent's
                    # target between lifecycle events"), not an extra constraint.
                    "locked_duties": limb_locked_duties(
                        stable_focal_duty=stable_choice["duty"]),
                    "conformance_record": build_event_conformance_record(cand),
                    # Item 3 / arm-distinctness spot check witness: the
                    # PRE-LEAVE duty map is exactly what `null` freezes for
                    # the whole mechanism horizon (`null_update` is the
                    # identity on this dict), so pairing it with
                    # `duty_map_at_te` (constructive_mixed's post-LEAVE
                    # re-match) gives a real constructive-vs-null witness at
                    # every certified joint event -- both certifications
                    # having passed already guarantees the vacancy was
                    # coverable (flex certification requires a covering
                    # survivor).
                    "duty_map_before_leave": dict(duty_map_before),
                }
                return {
                    "event": event, "exclusions": exclusions, "recorded_actions": recorded_actions,
                    "leave_diagnostics": leave_diagnostics, "rejected_counts": rejected_counts,
                }
            reject_reasons = map_rejection_reasons(
                eligibility_reasons=[], stable_ok=stable_ok, stable_reasons=stable_reasons_all,
                flex_ok=flex_ok, flex_reasons=flex_reasons)
            for r in reject_reasons:
                rejected_counts[r] += 1
            diag_entry["rejected_reasons"] = sorted(reject_reasons)
            leave_diagnostics.append(diag_entry)
            exclusions.append({
                "t_e": cand["t_e"], "stable_certified": stable_ok,
                "flex_certified": flex_ok, "flex_reasons": flex_reasons,
            })
    return {
        "event": None, "exclusions": exclusions, "recorded_actions": recorded_actions,
        "leave_diagnostics": leave_diagnostics, "rejected_counts": rejected_counts,
    }


def _target_id(target) -> str:
    t = np.asarray(target, dtype=float)
    # 6-decimal precision, tighter than `legal_set_targets`' own 1e-6
    # geometric-dedup tolerance, so two targets the dedup treats as
    # DISTINCT can never collide onto the same dict key here (which would
    # silently drop one candidate from `run_audit_event`'s `candidates`
    # dict rather than raising).
    return "z_{:.6f}_{:.6f}_{:.6f}".format(float(t[0]), float(t[1]), float(t[2]) if t.shape[0] > 2 else 0.0)


# =============================================================================
# Item 3 -- fixed-history prefix replay from a FRESH pinned env
# =============================================================================

def replay_prefix(config, *, coords: dict, coord_hash: str, episode_seed: int,
                   recorded_actions: list, expected_hash: str, duty_map_at_te: dict,
                   energy_permutation: Optional[np.ndarray] = None, energy_stage: str = "S3",
                   user_world_seed: Optional[int] = None):
    """Section 8/Q-I2's fixed-history mechanism: fresh pinned env, same
    episode seed, replay the EXACT recorded source-control actions up to
    `t_e`, assert the resulting state hash against the ORIGINAL rollout's
    recorded hash at `t_e`. A mismatch raises `PrefixReplayMismatchError`
    and is NEVER repaired -- the caller must treat that as invalidating the
    pair, never retried or silently downgraded."""
    env = build_pinned_env(config, episode_seed=episode_seed, coords=coords,
                            coord_hash=coord_hash, energy_stage=energy_stage,
                            user_world_seed=user_world_seed)
    if energy_permutation is not None:
        apply_energy_profile(env, energy_permutation)
    for actions in recorded_actions:
        env.step(actions)
    actual_hash = compute_state_hash(real_env_state_snapshot(env, duty_map_at_te))
    assert_state_hash_equal(expected_hash, actual_hash, context="prefix replay to t_e")
    return env


# =============================================================================
# R2 section 8 -- shared-prefix realization: one canonical replay, N clones
# =============================================================================

# Reviewed exclusions from the complete-state fingerprint. The default is
# INCLUDE: every ndarray, every numeric/bool scalar, and now every dict, list,
# tuple, set/frozenset and custom mutable object (recursed via its own
# `__dict__`) is covered unless it is named here. That direction is
# deliberate -- the defect this fingerprint replaces was a hash that covered a
# hand-picked subset of TYPES (arrays, scalars, flat numeric sequences only),
# so dicts, nested lists, sets and custom objects fell through with no `else`
# branch and no record of the omission. With include-by-default plus a loud
# failure for anything still uncovered (`FingerprintCoverageError`, see
# `_encode_fingerprint_value`), a newly added mutable field of a type already
# handled joins the fingerprint automatically, and a field of a genuinely new
# TYPE raises instead of silently vanishing -- an exclusion still has to be
# argued for in writing, but silence is no longer an available third option.
FINGERPRINT_EXCLUDED_ATTRS = frozenset({
    # Pure configuration: fixed for the whole run, identical across every clone
    # by construction, and noisy in a digest.
    "n_uavs", "n_users", "area_size", "time_step", "max_speed",
    "max_vertical_speed_mps", "battery_capacity_wh", "charging_power_w",
    "n_charging_stations", "return_reserve_ratio",
    "service_cutoff_threshold", "depleted_battery_threshold",
    "user_qos_rate_mbps", "episode_steps", "seed_val",
    # `np_random` is a `numpy.random.RandomState`/`Generator` instance -- a
    # C-implemented type with no `__dict__`, so the generic recursive encoder
    # cannot descend into it and would otherwise raise. It is not silently
    # dropped: it is already covered, more precisely, via the dedicated
    # `__rng__` token below (`_rng_state_token`), which reads the RNG's actual
    # bit-generator state rather than trying to walk it as a generic object.
    "np_random",
    # `observation_spaces`/`action_spaces` are dicts of `gymnasium.spaces`
    # objects. They are pure per-run configuration -- identical across every
    # clone by construction, never mutated by a continuation -- and their
    # internal attributes can include a lazily-created `Generator`/
    # `RandomState` for `.sample()`, which is exactly the opaque, `__dict__`-
    # less shape `np_random` above is excluded for. This audit never calls
    # `.sample()` on them (every arm is a scripted source control), so
    # excluding the spaces outright is simpler and safer than depending on
    # that lazy attribute staying unset.
    "observation_spaces", "action_spaces",
    # Rendering handles. Always `None` on this audit's non-interactive path
    # (nothing here ever calls `render()`); not environment state, and not a
    # shape the recursive encoder should be trusted to walk if a stray
    # `render()` call ever populated them.
    "viewer", "fig", "ax",
})


class FingerprintCoverageError(RuntimeError):
    """Raised by `full_state_fingerprint` when an attribute's value is a type
    `_encode_fingerprint_value` has no canonical encoding rule for, and the
    attribute is not named in `FINGERPRINT_EXCLUDED_ATTRS`.

    This is the fix for the defect Stage B found: the previous fingerprint
    covered exactly three shapes (`np.ndarray`, numeric/bool scalars, flat
    numeric lists/tuples) with no `else` branch, so dicts, nested lists, sets
    and custom mutable objects fell through and were never recorded, never
    raised, never logged -- silently absent from an assertion whose docstring
    claimed to cover them. A newly encountered type must now either be given
    an explicit encoding rule or a written, reviewed exclusion; it can no
    longer just fail to match any `isinstance` check and vanish.
    """


def _encode_fingerprint_value(value, *, seen: frozenset) -> bytes:
    """Canonical recursive encoding for one attribute value (or nested
    sub-value): the mechanism that replaces the narrow three-shape dispatch.

    Covers, in addition to the `np.ndarray`/numeric-scalar leaves the
    superseded hash already had: `None`; `str`/`bytes`; `dict` (canonicalized
    by sorting on the ENCODED key, so key order never affects the digest and
    the ordering stays address-independent across processes);
    `list`/`tuple` (order-preserving, arbitrarily nested); `set`/`frozenset`
    (canonicalized by sorting the ENCODED elements, since set elements need
    not be independently orderable); and any custom object exposing a
    `__dict__`, recursed into as a dict of its own attributes -- this is what
    covers a source-controller/router object's internal caches and tables
    without hand-listing every such class.

    `seen` is the set of `id()`s already on the current recursion path.
    `full_state_fingerprint` seeds it with the environment's own id, so a
    custom object holding a back-reference to the environment (e.g. a
    routing-protocol object's `self.env`, `routing_protocols.py:12`) resolves
    to a bounded `<cycle:...>` marker instead of recursing forever -- the
    environment's own state is already covered by the outer per-attribute
    loop, so re-walking it through the back-reference would be redundant as
    well as unbounded.

    Anything reaching the end of this function without a matching rule, and
    not caught by `full_state_fingerprint`'s exclusion check, raises
    `FingerprintCoverageError` rather than being silently skipped. That loud
    failure IS the design constraint this function exists to satisfy: the
    defect was not the omission, it was that the omission was invisible.
    """
    if value is None:
        return b"None"
    if isinstance(value, np.ndarray):
        return (b"ndarray:" + str(value.shape).encode("utf-8") + b":"
                + str(value.dtype).encode("utf-8") + b":"
                + np.ascontiguousarray(value).tobytes())
    if isinstance(value, (bool, np.bool_)):
        return b"bool:" + repr(bool(value)).encode("utf-8")
    if isinstance(value, (int, np.integer)):
        return b"int:" + repr(int(value)).encode("utf-8")
    if isinstance(value, (float, np.floating)):
        return b"float:" + repr(float(value)).encode("utf-8")
    if isinstance(value, (str, bytes)):
        raw = value.encode("utf-8") if isinstance(value, str) else value
        return b"str:" + raw

    obj_id = id(value)
    if isinstance(value, dict):
        if obj_id in seen:
            return b"<cycle:dict>"
        inner = seen | {obj_id}
        # Canonicalize on the ENCODED key, exactly as the set branch below does.
        # Sorting on `repr(key)` looks equivalent and is not: a key whose class
        # does not define `__repr__` reprs as `<Foo object at 0x...>`, so the
        # sort ORDER becomes address-dependent and the digest differs between
        # processes for identical state. That is the one thing a fingerprint
        # pooled across separately-invoked shards must never do, and it would
        # have been invisible in-process -- the same silent shape as the defect
        # this whole function exists to fix, one layer down.
        encoded_items = sorted(
            (_encode_fingerprint_value(k, seen=inner),
             _encode_fingerprint_value(v, seen=inner))
            for k, v in value.items())
        parts = [b"dict{"]
        for enc_k, enc_v in encoded_items:
            parts.append(enc_k)
            parts.append(b":")
            parts.append(enc_v)
            parts.append(b",")
        parts.append(b"}")
        return b"".join(parts)
    if isinstance(value, (list, tuple)):
        if obj_id in seen:
            return b"<cycle:seq>"
        inner = seen | {obj_id}
        parts = [b"list[" if isinstance(value, list) else b"tuple["]
        for v in value:
            parts.append(_encode_fingerprint_value(v, seen=inner))
            parts.append(b",")
        parts.append(b"]")
        return b"".join(parts)
    if isinstance(value, (set, frozenset)):
        if obj_id in seen:
            return b"<cycle:set>"
        inner = seen | {obj_id}
        encoded_items = sorted(_encode_fingerprint_value(v, seen=inner) for v in value)
        return b"set{" + b",".join(encoded_items) + b"}"

    obj_dict = getattr(value, "__dict__", None)
    if obj_dict is not None:
        if obj_id in seen:
            return b"<cycle:obj>"
        inner = seen | {obj_id}
        return (b"obj:" + type(value).__name__.encode("utf-8") + b"{"
                + _encode_fingerprint_value(obj_dict, seen=inner) + b"}")

    raise FingerprintCoverageError(
        f"full_state_fingerprint has no encoding rule for type {type(value)!r} "
        f"and it is not in FINGERPRINT_EXCLUDED_ATTRS; add an explicit rule or "
        f"a justified exclusion rather than letting it fall through silently")


def full_state_fingerprint(env, *, duty_map: Optional[dict] = None,
                            duty_positions: Optional[dict] = None,
                            service_centroids=None) -> str:
    """Canonical digest over every continuation-sensitive state surface.

    SCOPE, ruled 2026-07-27 (Stage B round `..._fingerprint_closure`): this is a
    process-portable identifier of ONE concrete state, used to establish
    within-event snapshot/clone identity. It is **not** an assertion that
    `build_pinned_env` reconstructs a state from its registered seeds. Two
    identically-seeded constructions measurably fingerprint differently and
    never converge, because `reset()` derives station-relative logistics before
    the registered coordinates are restored; the residue lives in
    `episode_graph_pbrs_sum`, outside primary `G`, and is shared by every limb
    of an episode before treatment. `episode_world_fingerprint` DOES reproduce
    across constructions -- that is the R3 section E claim, and it is a
    different claim from this one.

    Replaces `compute_state_hash` as the load-bearing fixed-history assertion.
    That function hashes UAV positions, battery, charging, station occupancy and
    queue, lifecycle mask and duty map -- and nothing else. It therefore
    certified two environments as the same history while their user populations
    differed by kilometres, which is the defect Stage B returned MISMATCH on.
    The narrow hash survives as a cheap subset assertion; it cannot carry
    fixed-history validity.

    Covers, via `_encode_fingerprint_value`'s recursive dispatch rather than a
    hand-picked list of shapes: step and episode counters, UAV and user
    positions and velocities, cluster assignments/centres/velocities/
    waypoints/pause timers, user waypoints and pause timers, battery/
    charging/station/queue/docking state, cutoff and depletion latches,
    connection matrices, SINR, routing paths and reusable channel/radio
    caches (dicts), service-set and handover state (lists of lists), packet
    state (lists of dicts), source-controller scheduling state (custom
    objects such as a routing-protocol instance, recursed via `__dict__`),
    the environment RNG state, lifecycle mask, and topology coordinates.

    `duty_positions` and `service_centroids` are the second half of the R3
    §C blocker: duty targets and service centroids named as continuation
    inputs, bound HERE to the same event identity as everything else rather
    than living only in the `event` dict unfingerprinted. Passing `None`
    (the default) omits that term, exactly like `duty_map=None` already did
    -- callers on the conclusion-bearing path must pass the real values.
    """
    seen = frozenset({id(env)})
    parts: list[bytes] = []
    for name in sorted(dir(env)):
        if name.startswith("__") or name in FINGERPRINT_EXCLUDED_ATTRS:
            continue
        try:
            value = getattr(env, name)
        except Exception:
            continue                      # properties that raise are not state
        if callable(value):
            continue
        parts.append(name.encode("utf-8"))
        parts.append(b"=")
        parts.append(_encode_fingerprint_value(value, seen=seen))
        parts.append(b";")

    parts.append(b"__rng__")
    parts.append(_rng_state_token(env).encode("utf-8"))

    if duty_map is not None:
        parts.append(b"__duty_map__")
        parts.append(_encode_fingerprint_value(dict(duty_map), seen=seen))
    if duty_positions is not None:
        parts.append(b"__duty_positions__")
        parts.append(_encode_fingerprint_value(dict(duty_positions), seen=seen))
    if service_centroids is not None:
        parts.append(b"__service_centroids__")
        parts.append(_encode_fingerprint_value(
            np.asarray(service_centroids, dtype=float), seen=seen))

    return hashlib.sha256(b"".join(parts)).hexdigest()


class CloneIsolationError(RuntimeError):
    """A continuation clone failed one of R2 section 8's Stage-B blocking
    conditions (clone equivalence, mutation isolation, RNG isolation, topology
    preservation, complete-state restoration). Never repaired: per R2's failure
    semantics the event emits `INVALID_EVENT_ALIGNED_AUDIT`."""


def _rng_state_token(env) -> str:
    """A stable token for the environment RNG state, used to prove that clone
    construction consumes no registered continuation randomness (condition 3).
    Tolerates both `RandomState` and `Generator`, since `fork_continuation`
    installs a `RandomState` while a fresh env may carry either.

    This is the SOLE RNG coverage inside `full_state_fingerprint`: `np_random`
    is named in `FINGERPRINT_EXCLUDED_ATTRS` precisely because this function
    reads its actual bit-generator state instead of trying to walk it as a
    generic object. A silent constant here on an unrecognized shape would
    therefore silently drop RNG state from clone condition 5 and from
    `assert_source_intact` on the day an attribute gets renamed -- the same
    silent-fallback shape `FingerprintCoverageError` exists to stop one layer
    up in `_encode_fingerprint_value`, so an unrecognized RNG shape raises
    that same error here rather than returning a constant token that can
    never move."""
    rng = getattr(env, "np_random", None)
    if rng is None:
        raise FingerprintCoverageError(
            "_rng_state_token found no 'np_random' attribute (missing or "
            "None) on env; if the env genuinely carries no continuation RNG "
            "that must be an explicit, reviewed exclusion, not a silent "
            "constant token")
    getter = getattr(rng, "get_state", None)
    if callable(getter):                      # numpy RandomState
        state = getter()
        parts = []
        for item in state:
            arr = np.asarray(item)
            parts.append(arr.tobytes() if arr.dtype != object else repr(item).encode("utf-8"))
        return hashlib.sha256(b"".join(parts)).hexdigest()
    bit_gen = getattr(rng, "bit_generator", None)   # numpy Generator
    if bit_gen is not None:
        return hashlib.sha256(repr(bit_gen.state).encode("utf-8")).hexdigest()
    raise FingerprintCoverageError(
        f"_rng_state_token has no encoding rule for env.np_random of type "
        f"{type(rng)!r} (neither a RandomState with get_state() nor a "
        f"Generator with bit_generator); add explicit support or a "
        f"justified exclusion rather than letting it fall through silently")


class EventSnapshot:
    """R2 section 8's shared-prefix realization: the **one** canonical
    evaluator-certified prefix replay for a qualifying event, held as an
    immutable complete-state snapshot from which every continuation is cloned.

    The superseded contract replayed the whole prefix inside every KEEP,
    selection and evaluation replicate. Repeated physical replay was never the
    scientific requirement -- equality of the history before forking is -- so
    deduplicating identical work does not reduce replication of the
    conclusion-bearing continuation randomness.

    Ordering is load-bearing and follows R2 steps 1-5 exactly: the snapshot is
    taken **before** any continuation-specific RNG is assigned, so issuing a
    clone cannot consume a registered continuation stream. The held env is
    never stepped again; `fork_continuation` always receives a fresh clone and
    the clone is discarded after one continuation. Multiple continuations are
    never run sequentially on one mutated clone.
    """

    def __init__(self, env, *, coord_hash: str, hash_at_te: str, duty_map_at_te: dict,
                  duty_positions_at_te: dict, service_centroids_at_te=None,
                  certified_fingerprint: Optional[str] = None):
        self._env = env
        self.coord_hash = coord_hash
        self.hash_at_te = hash_at_te
        self.duty_map_at_te = dict(duty_map_at_te)
        # R3 §C's second blocker (ruling 2026-07-27): duty targets and service
        # centroids are continuation inputs the contract names explicitly, so
        # they must be bound to event identity, not merely carried alongside
        # it. Storing them here and folding them into `full_fingerprint` below
        # is what makes two events differing only in duty positions or
        # centroids resolve to different identities instead of the same one.
        self.duty_positions_at_te = dict(duty_positions_at_te)
        self.service_centroids_at_te = (
            None if service_centroids_at_te is None
            else np.asarray(service_centroids_at_te).copy())
        self.baseline_cutoff, self.baseline_depletion = _baseline_masks(env)
        self.full_fingerprint = full_state_fingerprint(
            env, duty_map=self.duty_map_at_te,
            duty_positions=self.duty_positions_at_te,
            service_centroids=self.service_centroids_at_te)
        self._narrow_hash = compute_state_hash(
            real_env_state_snapshot(env, self.duty_map_at_te))
        self._source_rng_token = _rng_state_token(env)
        self.clones_issued = 0

        # Condition 1C -- event identity. When the snapshot is captured directly
        # off the live certified environment these are the same object, so this
        # is cheap; it still catches mutation between certification and capture.
        if certified_fingerprint is not None and certified_fingerprint != self.full_fingerprint:
            raise CloneIsolationError(
                f"event identity failed: the captured snapshot does not match the "
                f"fingerprint recorded at certification "
                f"(certified {certified_fingerprint}, captured {self.full_fingerprint})")

    # -- condition 2: the immutable source must survive every clone unchanged --
    def assert_source_intact(self, *, context: str = "") -> None:
        current = full_state_fingerprint(
            self._env, duty_map=self.duty_map_at_te,
            duty_positions=self.duty_positions_at_te,
            service_centroids=self.service_centroids_at_te)
        if current != self.full_fingerprint:
            raise CloneIsolationError(
                f"mutation isolation failed{(' (' + context + ')') if context else ''}: "
                f"the immutable event snapshot changed after a clone was issued "
                f"(expected {self.full_fingerprint}, got {current})")

    def clone(self, *, context: str = ""):
        """One independent continuation environment, cloned from the immutable
        snapshot and checked against R2's blocking conditions 2-5 before use.

        Condition 1 (clone equivalence against the previous independent-replay
        route) is not checkable from inside a single clone -- it is a
        cross-route property and is proved by
        `verify_clone_equivalence_against_replay` in the focused suite and by
        the Stage-B check on this diff."""
        rng_before = _rng_state_token(self._env)
        env = copy.deepcopy(self._env)
        self.clones_issued += 1

        # condition 3 -- clone construction consumed no continuation randomness
        rng_after = _rng_state_token(self._env)
        if rng_before != rng_after or rng_after != self._source_rng_token:
            raise CloneIsolationError(
                f"RNG isolation failed{(' (' + context + ')') if context else ''}: "
                f"cloning advanced the source environment RNG state")

        # condition 4 -- topology preservation
        clone_coord_hash = coordinate_hash(env.ground_bs_positions,
                                            env.charging_station_positions)
        if clone_coord_hash != self.coord_hash:
            raise TopologyMismatchError(
                f"clone topology hash mismatch{(' (' + context + ')') if context else ''}: "
                f"expected {self.coord_hash}, got {clone_coord_hash}")

        # condition 5 -- complete-state restoration, against the FULL fingerprint.
        # The narrow hash cannot carry this: it was equal for two environments
        # whose users differed by kilometres, which is the whole Stage B finding.
        clone_fingerprint = full_state_fingerprint(
            env, duty_map=self.duty_map_at_te,
            duty_positions=self.duty_positions_at_te,
            service_centroids=self.service_centroids_at_te)
        if clone_fingerprint != self.full_fingerprint:
            raise CloneIsolationError(
                f"complete-state restoration failed{(' (' + context + ')') if context else ''}: "
                f"clone fingerprint {clone_fingerprint} != source {self.full_fingerprint}")

        # condition 2 -- issuing the clone did not disturb the source
        self.assert_source_intact(context=context)
        return env


def capture_event_snapshot(live_env, *, coord_hash: str, event: dict) -> EventSnapshot:
    """R3: capture the immutable snapshot **directly from the live evaluator
    environment** at the moment the event was certified.

    This replaces reconstruction, and the distinction is the whole Stage B
    finding. The previous route certified the event in one world, then rebuilt a
    "canonical" snapshot by replaying the recorded actions into a FRESH
    environment -- whose user and cluster population belongs to a different
    world -- and accepted it because a narrow hash over UAV-only fields agreed.
    Every continuation then ran in that second world while the focal identities,
    legal targets, duty map and service centroids came from the first. Cloning
    made all arms share the wrong world consistently; it did not make it the
    right one.

    Capturing off the live environment removes the reconstruction step entirely,
    so there is no second world to disagree with. Ordering still matters: this
    must be called BEFORE any continuation-specific RNG is installed, so that
    issuing a clone cannot consume a registered continuation stream.

    `replay_prefix` is retained in this module as a historical diagnostic and is
    no longer on the conclusion-bearing path."""
    return EventSnapshot(
        live_env,
        coord_hash=coord_hash,
        hash_at_te=event["hash_at_te"],
        duty_map_at_te=event["duty_map_at_te"],
        duty_positions_at_te=event["duty_positions_at_te"],
        service_centroids_at_te=event["service_centroids_at_te"],
        certified_fingerprint=event.get("full_fingerprint_at_te"))


def verify_clone_conformance(snapshot: EventSnapshot, *, event: dict, limb: str,
                              continuation_seed: int, other_seed: Optional[int] = None,
                              horizon: Optional[int] = None,
                              schedule: str = "constructive_mixed") -> dict:
    """R3 conditions 1A and 1B, replacing the comparison to an independent
    replay.

    The superseded condition 1 asked a clone continuation to equal one obtained
    by rebuilding the environment from scratch. That reference route is
    nondeterministic across constructions, so the condition demanded the correct
    mechanism reproduce the broken one -- it was unsatisfiable and inverted. It
    is deleted rather than kept, along with the monkeypatched deterministic
    oracle that made it appear to pass.

    **1A same snapshot, same stream.** Two independent clones of one snapshot,
    given the same `stream_seed` and the same arm semantics, must produce
    identical G component series, total G and duty-map evolution.

    **1B stream isolation.** A clone given a different continuation stream must
    start from identical non-RNG state and differ only through the registered
    RNG. It is explicitly *not* required to produce a different trajectory -- a
    stochastic stream may go unused, or two draws may coincide -- so a
    difference is reported, never asserted.
    """
    h_val = int(horizon if horizon is not None else (H_STABLE if limb == "stable" else H_FLEX))

    def _one(seed: int) -> dict:
        env = snapshot.clone(context=f"conformance limb={limb} seed={seed}")
        pre = full_state_fingerprint(
            env, duty_map=snapshot.duty_map_at_te,
            duty_positions=snapshot.duty_positions_at_te,
            service_centroids=snapshot.service_centroids_at_te)
        baseline_cutoff, baseline_depletion = _baseline_masks(env)
        out = fork_continuation(
            env, duty_map_at_te=event["duty_map_at_te"],
            duty_positions_at_te=event["duty_positions_at_te"],
            service_centroids_at_te=event["service_centroids_at_te"],
            schedule=schedule, horizon=h_val, continuation_seed=seed)
        g = window_g_from_step_metrics(
            out["step_metrics"], out["qos_user_steps"], h=h_val,
            baseline_cutoff_mask=baseline_cutoff, baseline_depletion_mask=baseline_depletion)
        return {"pre_stream_fingerprint": pre, "g": g}

    a = _one(continuation_seed)
    b = _one(continuation_seed)

    same_stream_identical = bool(
        a["g"]["g_total"] == b["g"]["g_total"]
        and np.array_equal(a["g"]["g_series"], b["g"]["g_series"]))

    out: dict = {
        "condition_1a_same_stream_identical": same_stream_identical,
        "pre_stream_state_equal": a["pre_stream_fingerprint"] == b["pre_stream_fingerprint"],
        "g_total": float(a["g"]["g_total"]),
        "source_intact": True,
    }

    if other_seed is not None:
        c = _one(other_seed)
        out["condition_1b_pre_stream_state_equal"] = bool(
            a["pre_stream_fingerprint"] == c["pre_stream_fingerprint"])
        out["different_stream_g_total"] = float(c["g"]["g_total"])
        out["different_stream_changed_trajectory"] = bool(
            not np.array_equal(a["g"]["g_series"], c["g"]["g_series"]))

    try:
        snapshot.assert_source_intact(context="conformance")
    except CloneIsolationError:
        out["source_intact"] = False

    return out


def fork_continuation(env, *, duty_map_at_te: dict, duty_positions_at_te: dict,
                       service_centroids_at_te, schedule: str, horizon: int,
                       continuation_seed: int, focal_uav: Optional[int] = None,
                       focal_target=None, delta_steps: int = DELTA,
                       locked_duties: frozenset = frozenset()) -> dict:
    """Forks ONE continuation from an env already replayed to `t_e`:
    reseeds `env.np_random` to the stream_seed-derived continuation RNG
    (never the stream that generated the prefix), then rolls `horizon`
    steps under `schedule`. If `focal_uav` is given, its action target is
    forced to `focal_target` for the first `delta_steps` steps (the SET
    arm); KEEP is realized by omitting `focal_uav` entirely -- the
    unperturbed continuation IS the KEEP arm (section 1: "at t_e+Delta
    every constraint is released; both branches receive the same best
    legal continuation" holds identically whether or not a focal was ever
    diverted). While the focal is diverted, its OWN duty is treated as a
    virtual LEAVE (vacated, re-matched among survivors by the SAME accepted
    `constructive_mixed_update` the real LEAVE/REJOIN machinery uses) and a
    virtual REJOIN restores it at `t_e + delta_steps` -- this reuses the
    already-accepted duty-map logic rather than inventing new reassignment
    semantics for the intervention window."""
    env.np_random = np.random.RandomState(int(continuation_seed) % (2**32 - 1))
    duty_map = dict(duty_map_at_te)
    service_centroids = None if service_centroids_at_te is None else np.asarray(service_centroids_at_te).copy()
    step_metrics: list = []
    qos_user_steps: list = []

    if focal_uav is not None:
        airborne_positions = {i: np.asarray(env.uav_positions[i], dtype=float)
                               for i in range(int(env.n_uavs)) if not bool(env.uav_charging[i])}
        duty_map = constructive_mixed_update(
            duty_map=duty_map, duty_positions=duty_positions_at_te,
            airborne_positions=airborne_positions, event="LEAVE",
            event_uav=focal_uav, locked_duties=locked_duties)

    for t in range(int(horizon)):
        override = None
        if focal_uav is not None and focal_target is not None and t < int(delta_steps):
            override = {focal_uav: np.asarray(focal_target, dtype=float)}
        step = step_once(env, duty_map=duty_map, service_centroids=service_centroids,
                          schedule=schedule, target_override=override,
                          locked_duties=locked_duties, step_index=t)
        duty_map = step["duty_map"]
        service_centroids = step["service_centroids"]
        step_metrics.append(step["metrics"])
        qos_user_steps.append(step["qos_user_step"])
        if focal_uav is not None and t == int(delta_steps) - 1:
            airborne_positions = {i: np.asarray(env.uav_positions[i], dtype=float)
                                   for i in range(int(env.n_uavs)) if not bool(env.uav_charging[i])}
            duty_map = constructive_mixed_update(
                duty_map=duty_map, duty_positions=step["duty_positions"],
                airborne_positions=airborne_positions, event="REJOIN",
                event_uav=focal_uav, locked_duties=locked_duties)

    return {"step_metrics": step_metrics, "qos_user_steps": qos_user_steps}


# =============================================================================
# Item 4 -- window G accumulation from real per-step component fields
# =============================================================================

def window_g_from_step_metrics(step_metrics: list, qos_user_steps: list, *, h: int,
                                baseline_cutoff_mask: np.ndarray,
                                baseline_depletion_mask: np.ndarray) -> dict:
    """Item 4: window G accumulation from real per-step component fields
    (section 7), using the already-accepted `compute_G`/
    `window_latched_counts`/`nondegeneracy_report` -- never recomputes the
    analyzer formula independently. `baseline_*_mask` is the previous-step
    state recorded AT `t_e` (row 0 of the H+1-row convention, see
    `window_series_length`)."""
    n = min(len(step_metrics), int(h))
    n_uavs = len(baseline_cutoff_mask)
    qos_series = np.array([m["qos_satisfaction_ratio"] for m in step_metrics[:n]], dtype=float)
    return_cost_series = np.array([m["return_constraint_cost"] for m in step_metrics[:n]], dtype=float)
    return_cost_raw_series = np.array([m["return_constraint_cost_raw"] for m in step_metrics[:n]], dtype=float)

    cutoff_series = np.zeros((n + 1, n_uavs), dtype=bool)
    depletion_series = np.zeros((n + 1, n_uavs), dtype=bool)
    cutoff_series[0] = baseline_cutoff_mask
    depletion_series[0] = baseline_depletion_mask
    for i in range(n):
        cutoff_series[i + 1] = step_metrics[i]["cutoff_mask"]
        depletion_series[i + 1] = step_metrics[i]["depletion_mask"]
    latched = window_latched_counts(cutoff_series, depletion_series)

    g_series = np.array([
        compute_G(qos_satisfaction_ratio=qos_series[i], return_constraint_cost=return_cost_series[i],
                  new_cutoff_count=int(latched["cutoff_per_step"][i + 1]),
                  new_depletion_count=int(latched["depletion_per_step"][i + 1]))
        for i in range(n)
    ], dtype=float)

    qos_user_flat = (np.concatenate([np.asarray(q, dtype=float) for q in qos_user_steps[:n]])
                      if n and len(qos_user_steps) else np.array([]))
    report = nondegeneracy_report(
        qos_series=qos_series, qos_user_step=qos_user_flat, return_cost_series=return_cost_series,
        cutoff_incidence=latched["cutoff_count"], depletion_incidence=latched["depletion_count"],
        g_series=g_series, secondary_series=return_cost_raw_series)
    return {"g_total": float(np.sum(g_series)) if n else 0.0, "g_series": g_series, "report": report,
            "latched": latched,
            # Ruling 2026-07-27 (component persistence): the two raw
            # per-step component series this function already computes
            # locally, now exposed so a caller can persist them per
            # continuation. `qos_series` is the per-step arm-level QoS
            # ratio; `return_cost_series` is the ALREADY-CAPPED
            # return-constraint-cost series `compute_G` itself consumes
            # (see its docstring: "return_constraint_cost(capped)"), never
            # the uncapped `return_cost_raw_series` (that one is
            # `nondegeneracy_report`'s `secondary_metric_mean` input, a
            # different quantity).
            "qos_series": qos_series, "return_cost_series": return_cost_series}


# =============================================================================
# Ruling 2026-07-27 (D7.S component-cancellation prospective repair) --
# per-paired-continuation primary-G component persistence and exact
# arm-invariance, computed BEFORE serialization.
#
# The historical pooled artifact records only `g_total` per continuation, so
# a component-cancellation explanation of PRIMARY_G_DEGENERATE could not be
# tested at all -- the ruling requires the FUTURE instrument to retain the
# component series themselves (or a lossless canonical form), not just their
# scalar summary, and to compute exact paired-sequence equality between one
# continuation's two arms while both series are still in memory, recorded
# SEPARATELY from component totals (equal totals do not imply equal
# per-step sequences -- R2's distinct arm-invariance degeneracy condition).
# =============================================================================

def sparse_transition_series(per_step_counts) -> list:
    """Lossless canonical representation of a window-local transition count
    series (`window_latched_counts`'s `cutoff_per_step`/`depletion_per_step`
    -- almost always zero at every step, since a UAV's cutoff/depletion
    latch fires at most once per window): `[[step_index, count], ...]` for
    every NONZERO step, dropping nothing a dense array would carry (every
    zero step is implied by absence) and round-tripping via `_json_default`
    as plain JSON ints/lists. Materially smaller than the dense array for
    any window where transitions are rare, which is the registered regime
    (`window_latched_counts` counts each UAV's FIRST transition per type
    per window only)."""
    arr = np.asarray(per_step_counts)
    return [[int(i), int(v)] for i, v in enumerate(arr) if int(v) != 0]


def build_primary_g_component_record(*, window_result: dict, topology_seed, event_index,
                                       limb: str, arm: str, continuation_replicate: int) -> dict:
    """Assembles the ruling's mandatory per-paired-continuation persistence
    record from one `window_g_from_step_metrics` result: the QoS component
    series (dense, lossless -- floats are not a sparse quantity here), the
    capped return-cost series (dense, lossless), the two window-local
    transition series (`sparse_transition_series`, lossless), the four
    components' window totals, total G, user-step QoS saturation, and the
    paired arm identity (`topology_seed`/`event_index`/`limb`/`arm`/
    `continuation_replicate`) so a later analysis can pair arms without
    guessing which continuation produced which record.

    Reads via `.get` with safe defaults rather than direct indexing: several
    existing focused tests monkeypatch `window_g_from_step_metrics` down to
    a bare `{"g_total": ...}` stub to isolate unrelated behaviour (continuation
    seed wiring, clone-failure short-circuiting); this function must degrade
    to an honestly-empty record rather than crash a caller that never asked
    for component persistence in the first place. Every JSON-bound value
    (arrays, sparse pair lists, floats, ints) round-trips through the
    existing `_json_default` unchanged."""
    qos_series = np.asarray(window_result.get("qos_series", []), dtype=float)
    return_cost_series = np.asarray(window_result.get("return_cost_series", []), dtype=float)
    latched = window_result.get("latched", {}) or {}
    cutoff_per_step = np.asarray(latched.get("cutoff_per_step", []))
    depletion_per_step = np.asarray(latched.get("depletion_per_step", []))
    report = window_result.get("report", {}) or {}
    return {
        "topology_seed": int(topology_seed),
        "event_index": int(event_index),
        "limb": str(limb),
        "arm": str(arm),
        "continuation_replicate": int(continuation_replicate),
        "qos_component_series": qos_series,
        "return_cost_series": return_cost_series,
        "cutoff_transition_series": sparse_transition_series(cutoff_per_step),
        "depletion_transition_series": sparse_transition_series(depletion_per_step),
        "component_window_totals": {
            "qos_total": float(np.sum(qos_series)) if qos_series.size else 0.0,
            "return_cost_total": float(np.sum(return_cost_series)) if return_cost_series.size else 0.0,
            "cutoff_total": int(latched.get("cutoff_count", 0)),
            "depletion_total": int(latched.get("depletion_count", 0)),
        },
        "total_g": float(window_result.get("g_total", float("nan"))),
        "qos_saturation_fraction": float(report.get("qos_saturation_fraction", float("nan"))),
    }


def exact_paired_sequence_equal(record_a: dict, record_b: dict) -> bool:
    """Section 7 / ruling 2026-07-27: exact (bit-for-bit) equality of all
    FOUR primary-G component sequences between one paired continuation's two
    arms -- computed DIRECTLY from the persisted sequences themselves, never
    from `component_window_totals` or `total_g`. Two arms can share an
    identical window total while differing step-by-step (e.g. a cutoff on
    step 5 of one arm and step 9 of the other, same window count), so a
    totals-based comparison cannot establish the arm-invariance condition
    R2 made distinct from component cancellation; only a direct sequence
    comparison can."""
    return (
        np.array_equal(np.asarray(record_a["qos_component_series"]),
                        np.asarray(record_b["qos_component_series"]))
        and np.array_equal(np.asarray(record_a["return_cost_series"]),
                            np.asarray(record_b["return_cost_series"]))
        and record_a["cutoff_transition_series"] == record_b["cutoff_transition_series"]
        and record_a["depletion_transition_series"] == record_b["depletion_transition_series"]
    )


def _baseline_masks(env) -> tuple:
    battery = np.asarray(env.uav_battery_ratios, dtype=float)
    cutoff = battery <= float(getattr(env, "service_cutoff_threshold", 0.02))
    depletion = battery <= float(getattr(env, "depleted_battery_threshold", 0.0))
    return cutoff, depletion


# =============================================================================
# Item 5 -- calibration episode driver (B_m: constructive_mixed vs null)
# =============================================================================

def run_calibration_episode(config, *, topology_seed: int, episode_seed: int, energy_seed: int,
                             coords: dict, coord_hash: str, energy_stage: str = "S3",
                             episode_index: int = 0) -> dict:
    """One item-2/3/5 calibration episode: rolls `constructive_mixed` from
    reset to find the joint qualifying event (section 2/Q-E4), then forks
    at `t_e` into `constructive_mixed` vs `null` and evaluates BOTH
    `H_stable` and `H_flex` from the SAME paired continuation type (section
    5). Returns `support_miss=True` (never a synthetic zero) when no
    qualifying joint event was found.

    Part-A conformance (implementer wiring, section 8, stable limb ONLY,
    "never applied on the flex limb"): the stable limb's schedule set gains a
    THIRD fork, `full_sync_SET` (the accepted `full_sync_set_update` diagnostic
    duty policy), run through the identical prefix-replay/continuation-seed
    machinery as `constructive_mixed`/`null` above -- same CRN continuation
    construction, same `H_stable` window, same window-local G. `D_A =
    G(full_sync_SET) - G(constructive_mixed)` is accumulated per qualifying
    calibration episode, exactly mirroring `b_value`'s per-episode scalar
    shape (frozen contract section 8's bootstrap text lists "B_stable,
    B_flex, ... and the Part-A contrast" as resampled from "calibration
    episodes and audit events" together with B_m, not from the audit block's
    n_select/n_eval selection-replicate machinery, which section 8's
    "Replicates" paragraph scopes explicitly to "selected SET and KEEP" --
    so D_A is a single scalar per calibration episode, not an n_eval-length
    replicate array).

    Fixed-history discipline (section 8/Q-I2): a `PrefixReplayMismatchError`
    on ANY schedule's fresh-env prefix replay invalidates the WHOLE episode
    (every schedule's fork shares the same recorded prefix and expected
    hash, so a divergence on one schedule means the fixed-history guarantee
    itself failed for this episode, not just one arm) -- it is caught here,
    reported via `invalidated_pairs`, and the episode contributes to neither
    `B_m` nor `D_A`, never silently repaired or retried."""
    uw_seed = user_world_seed(topology_seed=topology_seed, block="calibration",
                               episode_index=episode_index)
    env = build_pinned_env(config, episode_seed=episode_seed, coords=coords,
                            coord_hash=coord_hash, energy_stage=energy_stage,
                            user_world_seed=uw_seed)
    world = episode_world_fingerprint(env, seed_value=uw_seed)
    energies = draw_energy_permutation(energy_seed=energy_seed)
    apply_energy_profile(env, energies)
    prefix = roll_prefix_and_find_event(env)
    episode_leave_report = {
        "leave_diagnostics": prefix.get("leave_diagnostics", []),
        "rejected_counts": prefix.get("rejected_counts", {}),
    }
    if prefix["event"] is None:
        return {"support_miss": True, "invalidated": False, "exclusions": prefix["exclusions"],
                "episode_report": episode_leave_report, "episode_world": world}

    event = prefix["event"]
    results = {}
    invalidated_pairs: list = []

    # R3: capture DIRECTLY off the live certified environment. No second
    # fresh-environment replay, so there is no second user world to disagree
    # with. The same snapshot serves both limbs -- they begin at the same
    # registered joint event -- while focal intervention, locked duties and
    # horizon stay limb-specific.
    try:
        snapshot = capture_event_snapshot(env, coord_hash=coord_hash, event=event)
    except CloneIsolationError as exc:
        # Condition 1C failed: the environment moved between certification and
        # capture. That voids the whole event; it is never repaired.
        invalidated_pairs.append({
            "topology_seed": topology_seed, "episode_seed": episode_seed,
            "block": "calibration", "limb": "both",
            "schedule": "live_event_capture", "reason": str(exc),
        })
        return {
            "support_miss": False, "invalidated": True,
            "invalidated_pairs": invalidated_pairs,
            "event": event["conformance_record"], "results": {},
            "duty_map_at_te": event["duty_map_at_te"],
            "duty_map_before_leave": event["duty_map_before_leave"],
            "episode_report": episode_leave_report,
            # An invalidated episode is still an episode the run visited, and the
            # audit loop's record is one entry per ATTEMPTED episode. Dropping it
            # here would make the recorded set a filtered sample of the history
            # rather than the history.
            "episode_world": world,
        }

    component_records: list = []
    for limb, h_val in (("stable", H_STABLE), ("flex", H_FLEX)):
        schedules = (("constructive_mixed", "null", "full_sync_SET") if limb == "stable"
                     else ("constructive_mixed", "null"))
        g_by_schedule = {}
        limb_invalid = False
        for schedule in schedules:
            try:
                replay_env = snapshot.clone(
                    context=f"calibration limb={limb} schedule={schedule}")
            except (CloneIsolationError, TopologyMismatchError) as exc:
                invalidated_pairs.append({
                    "topology_seed": topology_seed, "episode_seed": episode_seed,
                    "block": "calibration", "limb": limb, "schedule": schedule,
                    "reason": str(exc),
                })
                limb_invalid = True
                break
            # CRN: every schedule of one calibration episode shares the
            # continuation base stream, so `B_m = G(constructive) - G(null)` is a
            # PAIRED contrast. Passing `schedule` here instead gave each arm its
            # own stream, which is what made `bootstrap_ratio_ci`'s "arms are
            # CRN-paired inside one episode" false.
            cont_seed = stream_seed(
                topology_seed=topology_seed, block="calibration", episode_seed=episode_seed,
                limb=limb, event_index=0, candidate_target_id=EVAL_SHARED_CANDIDATE_TOKEN,
                phase="evaluate", replicate_index=0)
            out = fork_continuation(
                replay_env, duty_map_at_te=event["duty_map_at_te"],
                duty_positions_at_te=event["duty_positions_at_te"],
                service_centroids_at_te=event["service_centroids_at_te"],
                schedule=schedule, horizon=h_val, continuation_seed=cont_seed)
            g_by_schedule[schedule] = window_g_from_step_metrics(
                out["step_metrics"], out["qos_user_steps"], h=h_val,
                baseline_cutoff_mask=snapshot.baseline_cutoff,
                baseline_depletion_mask=snapshot.baseline_depletion)
            # Ruling 2026-07-27: every calibration schedule IS a paired
            # continuation (the comment above already establishes the CRN
            # sharing that makes `b_value`/`d_a` paired contrasts), so every
            # one persists its component record here, before this episode's
            # in-memory series are discarded.
            component_records.append(build_primary_g_component_record(
                window_result=g_by_schedule[schedule], topology_seed=topology_seed,
                event_index=episode_index, limb=limb, arm=schedule,
                continuation_replicate=0))
        if limb_invalid:
            continue
        result_entry = {
            "b_value": g_by_schedule["constructive_mixed"]["g_total"] - g_by_schedule["null"]["g_total"],
            "constructive": g_by_schedule["constructive_mixed"],
            "null": g_by_schedule["null"],
            # Ruling 2026-07-27: exact paired-sequence equality between the
            # two arms `b_value` itself contrasts (constructive_mixed vs
            # null), computed HERE while both arms' series are still in
            # memory and recorded separately from `b_value`/component
            # totals -- never inferred from them afterwards.
            "sequences_exactly_equal": exact_paired_sequence_equal(
                next(r for r in component_records
                     if r["limb"] == limb and r["arm"] == "null"),
                next(r for r in component_records
                     if r["limb"] == limb and r["arm"] == "constructive_mixed")),
        }
        if limb == "stable":
            result_entry["full_sync"] = g_by_schedule["full_sync_SET"]
            result_entry["d_a"] = (g_by_schedule["full_sync_SET"]["g_total"]
                                    - g_by_schedule["constructive_mixed"]["g_total"])
        results[limb] = result_entry
    return {
        "support_miss": False,
        "invalidated": bool(invalidated_pairs),
        "invalidated_pairs": invalidated_pairs,
        "event": event["conformance_record"],
        "results": results,
        "duty_map_at_te": event["duty_map_at_te"],
        "duty_map_before_leave": event["duty_map_before_leave"],
        "episode_report": episode_leave_report,
        "episode_world": world,
        "component_records": component_records,
    }


# =============================================================================
# Item 3/5 -- audit event driver (KEEP + legal-z SET, n_select/n_eval streams)
# =============================================================================

def run_audit_event(*, snapshot: EventSnapshot, topology_seed: int, episode_seed: int,
                     event: dict, limb: str, n_select: int, n_eval: int,
                     event_index: int = 0) -> dict:
    """Item 3's audit-event intervention under R2's shared-prefix realization:
    KEEP (unperturbed `constructive_mixed` continuation) plus, for every legal
    `z` in the limb's `Z(h)`, `n_select` selection-stream replicates and
    `n_eval` evaluation-stream replicates -- each executed on its own
    independent clone of the ONE canonical `EventSnapshot`, never on a fresh
    per-replicate prefix replay and never twice on one mutated clone.

    Returns the `hierarchical_bootstrap_events`-shaped per-event unit:
    `{"candidates": {z: {"select":.., "eval_set":..}}, "eval_keep":..}`.

    Failure semantics changed with R2 and the change is load-bearing. The
    superseded contract replayed independently per replicate, so one mismatch
    excluded only that replicate. There is now exactly one replay per event, so
    a clone-equivalence or isolation failure means the fixed-history guarantee
    failed for the whole event: `event_invalid=True` is returned, the caller
    drops the event, and the run reports `INVALID_EVENT_ALIGNED_AUDIT`. Never
    repaired, never retried, never downgraded to a partial event."""
    h_val = H_STABLE if limb == "stable" else H_FLEX
    focal_uav = event["focal_stable_uav"] if limb == "stable" else event["focal_flex_uav"]
    legal_targets = event["legal_targets"][limb]
    locked_duties = event["locked_duties"][limb]
    invalidated_pairs: list = []
    event_invalid = {"flag": False}
    # Ruling 2026-07-27: only "evaluate"-phase replicates are CRN-paired
    # (KEEP and the selected SET share a continuation seed per replicate
    # index -- see the seed-derivation comment below); "select"-phase
    # replicates each draw an independent stream per candidate and are
    # never paired with anything, so they are outside the ruling's "paired
    # continuation" persistence scope. Keyed by (candidate_id,
    # replicate_index), evaluate phase only.
    evaluate_component_records: dict = {}

    def _run_replicate(*, target, candidate_id: str, phase: str, replicate_index: int) -> Optional[float]:
        if event_invalid["flag"]:
            return None            # short-circuit: the event is already void
        try:
            replay_env = snapshot.clone(
                context=f"audit limb={limb} candidate={candidate_id} "
                        f"phase={phase} replicate={replicate_index}")
        except (CloneIsolationError, TopologyMismatchError) as exc:
            invalidated_pairs.append({
                "topology_seed": topology_seed, "episode_seed": episode_seed,
                "block": "audit", "limb": limb, "candidate_id": candidate_id,
                "phase": phase, "replicate_index": replicate_index, "reason": str(exc),
            })
            event_invalid["flag"] = True
            return None
        baseline_cutoff = snapshot.baseline_cutoff
        baseline_depletion = snapshot.baseline_depletion
        # CRN, and the reason `stream_seed`'s docstring gives for the sentinel
        # existing at all: during `phase="evaluate"` KEEP and the selected SET
        # must land on the SAME continuation base stream per replicate index, so
        # `U* = mean(eval_set) - mean(eval_keep)` is a paired contrast. During
        # `phase="select"` the candidate id stays, because selection needs an
        # independent stream per candidate. `phase` is itself hashed, so the two
        # namespaces remain disjoint either way.
        seed_candidate_id = (EVAL_SHARED_CANDIDATE_TOKEN if phase == "evaluate"
                             else candidate_id)
        cont_seed = stream_seed(
            topology_seed=topology_seed, block="audit", episode_seed=episode_seed,
            limb=limb, event_index=0, candidate_target_id=seed_candidate_id,
            phase=phase, replicate_index=replicate_index)
        out = fork_continuation(
            replay_env, duty_map_at_te=event["duty_map_at_te"],
            duty_positions_at_te=event["duty_positions_at_te"],
            service_centroids_at_te=event["service_centroids_at_te"],
            schedule="constructive_mixed", horizon=h_val, continuation_seed=cont_seed,
            focal_uav=focal_uav if target is not None else None, focal_target=target,
            locked_duties=locked_duties)
        g = window_g_from_step_metrics(
            out["step_metrics"], out["qos_user_steps"], h=h_val,
            baseline_cutoff_mask=baseline_cutoff, baseline_depletion_mask=baseline_depletion)
        if phase == "evaluate":
            evaluate_component_records[(candidate_id, replicate_index)] = (
                build_primary_g_component_record(
                    window_result=g, topology_seed=topology_seed, event_index=event_index,
                    limb=limb, arm=candidate_id, continuation_replicate=replicate_index))
        return g["g_total"]

    keep_eval = np.array([
        v for v in (
            _run_replicate(target=None, candidate_id="KEEP", phase="evaluate", replicate_index=r)
            for r in range(n_eval)
        ) if v is not None
    ], dtype=float)
    print(f"[progress] topology_seed={topology_seed} episode_seed={episode_seed} limb={limb} "
          f"replicate_batch=KEEP n_eval={n_eval} completed={keep_eval.size}",
          file=sys.stderr, flush=True)

    candidates = {}
    for z_id, z_target in legal_targets.items():
        select_vals = np.array([
            v for v in (
                _run_replicate(target=z_target, candidate_id=z_id, phase="select", replicate_index=r)
                for r in range(n_select)
            ) if v is not None
        ], dtype=float)
        eval_vals = np.array([
            v for v in (
                _run_replicate(target=z_target, candidate_id=z_id, phase="evaluate", replicate_index=r)
                for r in range(n_eval)
            ) if v is not None
        ], dtype=float)
        candidates[z_id] = {"select": select_vals, "eval_set": eval_vals}
        print(f"[progress] topology_seed={topology_seed} episode_seed={episode_seed} limb={limb} "
              f"replicate_batch=candidate:{z_id} n_select={n_select} n_eval={n_eval} "
              f"select_completed={select_vals.size} eval_completed={eval_vals.size}",
              file=sys.stderr, flush=True)

    # Ruling 2026-07-27: exact paired-sequence equality between KEEP and each
    # legal candidate's SET, per CRN-paired evaluate replicate, computed here
    # while both arms' records are still in memory. A replicate missing
    # either side (short-circuited by a clone failure) is skipped rather
    # than compared -- there is no pair to evaluate.
    pairwise_equality = [
        {"candidate": z_id, "replicate_index": r,
         "sequences_exactly_equal": exact_paired_sequence_equal(
             evaluate_component_records[("KEEP", r)], evaluate_component_records[(z_id, r)])}
        for z_id in candidates
        for r in range(n_eval)
        if ("KEEP", r) in evaluate_component_records and (z_id, r) in evaluate_component_records
    ]

    return {"candidates": candidates, "eval_keep": keep_eval,
            "invalidated_pairs": invalidated_pairs,
            "event_invalid": event_invalid["flag"],
            "component_audit": {
                "records": list(evaluate_component_records.values()),
                "pairwise_equality": pairwise_equality,
            }}


# =============================================================================
# Item 5 -- per-topology driver
# =============================================================================
#
# `--workers` (orchestration plumbing only, not a contract choice -- see
# `topology_unit_for_serialization`'s docstring for the same distinction drawn
# about process topology): episodes within ONE topology are provably
# independent (fresh env per episode via `build_pinned_env`/
# `build_topology_template`, seeds derived per-episode via `_derived_seed`,
# nothing carried across episodes except the accumulating report/unit lists
# this driver itself owns), so running them through a process pool and
# folding the results back in ascending episode-index order is required to
# reproduce the sequential path's output bit-for-bit -- never completion
# order, which a pool gives no guarantee about.

def _pinned_worker_env():
    """Pins BLAS/OpenMP threading to 1 for every child process a pool is
    about to spawn. Must be set in THIS (parent) process's environment
    BEFORE `ProcessPoolExecutor` creates the children -- env vars are copied
    at process-creation time, so setting them only inside a worker, after
    numpy/BLAS may already be initialized there, is too late for backends
    that fix their thread count at first use. Restored on exit so the
    orchestrator process's own environment is unaffected once the pool is
    torn down."""
    return _PinnedWorkerEnv()


class _PinnedWorkerEnv:
    _KEYS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")

    def __enter__(self):
        self._previous = {k: os.environ.get(k) for k in self._KEYS}
        for k in self._KEYS:
            os.environ[k] = "1"
        return self

    def __exit__(self, *exc_info):
        for k, v in self._previous.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


def _run_indexed_in_pool(worker_fn, indices, workers: int, **common_kwargs) -> dict:
    """Executes `worker_fn(idx=idx, **common_kwargs)` for every `idx` in
    `indices` across a `ProcessPoolExecutor` of size `workers`, returning a
    plain `{idx: result}` mapping once every task has completed.

    Deliberately the ONLY place that talks to the pool: every caller folds
    the returned mapping back in ascending `idx` order itself (never
    `as_completed`'s own yield order), so a pool's real out-of-order
    completion can never leak into accumulator order or the per-episode
    progress line's cumulative-qualifying count. Exposed as its own function
    so a test can substitute a fake that still calls the real (possibly
    monkeypatched) `worker_fn` but resolves out of ascending order, proving
    the caller re-sequences rather than merely trusting it does."""
    results: dict = {}
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(worker_fn, idx=idx, **common_kwargs): idx for idx in indices}
        for future in as_completed(futures):
            idx = futures[future]
            results[idx] = future.result()
    return results


def _calibration_episode_worker(*, idx: int, topology_seed: int, coords: dict,
                                 coord_hash: str, energy_stage: str):
    """Runs inside a pool worker process: builds its OWN config (never
    receives the parent's `config` object -- a worker must not depend on
    `config_1.Config` pickling cleanly, so every worker constructs its own
    copy via `build_config()` instead) and runs one calibration episode end
    to end via the existing, unmodified `run_calibration_episode`. Returns
    `(ep_seed, result)`; the caller folds this into the accumulators exactly
    as `run_calibration_episode`'s direct sequential-path result is folded."""
    config = build_config()
    ep_seed = _derived_seed(topology_seed=topology_seed, block="calibration", idx=idx, tag="episode_seed")
    en_seed = _derived_seed(topology_seed=topology_seed, block="calibration", idx=idx, tag="energy_seed")
    result = run_calibration_episode(
        config, topology_seed=topology_seed, episode_seed=ep_seed, energy_seed=en_seed,
        coords=coords, coord_hash=coord_hash, energy_stage=energy_stage, episode_index=idx)
    return ep_seed, result


def _compute_audit_episode(config, *, idx: int, topology_seed: int, coords: dict,
                            coord_hash: str, energy_stage: str, n_select: int, n_eval: int) -> dict:
    """Pure per-episode audit-block computation: build the pinned env, roll
    the prefix, capture the live event snapshot, and run both limbs' audit
    events. Factored out of `run_topology_audit`'s audit loop so the exact
    same computation is shared by the sequential path (using the caller's
    `config`) and the `--workers` pool path (using a freshly built `config`
    per worker, via `_audit_episode_worker`) -- never re-derives a seed or a
    predicate, only relocates the existing per-episode body into a callable
    both paths use identically."""
    ep_seed = _derived_seed(topology_seed=topology_seed, block="audit", idx=idx, tag="episode_seed")
    en_seed = _derived_seed(topology_seed=topology_seed, block="audit", idx=idx, tag="energy_seed")
    uw_seed = user_world_seed(topology_seed=topology_seed, block="audit", episode_index=idx)
    env = build_pinned_env(config, episode_seed=ep_seed, coords=coords, coord_hash=coord_hash,
                            energy_stage=energy_stage, user_world_seed=uw_seed)
    raw = {
        "ep_seed": ep_seed,
        "world_entry": {"block": "audit", "episode_index": idx, "episode_seed": ep_seed,
                         **episode_world_fingerprint(env, seed_value=uw_seed)},
    }
    energies = draw_energy_permutation(energy_seed=en_seed)
    apply_energy_profile(env, energies)
    prefix = roll_prefix_and_find_event(env)
    raw["leave_diagnostics"] = prefix.get("leave_diagnostics", [])
    raw["rejected_counts"] = prefix.get("rejected_counts", {})
    raw["event_found"] = prefix["event"] is not None
    if prefix["event"] is None:
        raw["exclusions"] = prefix["exclusions"]
        return raw
    event = prefix["event"]
    try:
        snapshot = capture_event_snapshot(env, coord_hash=coord_hash, event=event)
    except CloneIsolationError as exc:
        raw["capture_failed"] = True
        raw["capture_error"] = str(exc)
        return raw
    raw["unit_stable"] = run_audit_event(
        snapshot=snapshot, topology_seed=topology_seed, episode_seed=ep_seed,
        event=event, limb="stable", n_select=n_select, n_eval=n_eval, event_index=idx)
    raw["unit_flex"] = run_audit_event(
        snapshot=snapshot, topology_seed=topology_seed, episode_seed=ep_seed,
        event=event, limb="flex", n_select=n_select, n_eval=n_eval, event_index=idx)
    raw["event_conformance_record"] = event["conformance_record"]
    raw["duty_map_at_te"] = event["duty_map_at_te"]
    raw["duty_map_before_leave"] = event["duty_map_before_leave"]
    return raw


def _audit_episode_worker(*, idx: int, topology_seed: int, coords: dict, coord_hash: str,
                           energy_stage: str, n_select: int, n_eval: int) -> dict:
    """Pool-worker entry point for one audit-block episode: builds its own
    `config` (see `_calibration_episode_worker`) and delegates to
    `_compute_audit_episode`, returning only a plain, picklable result dict
    -- never the live env or `EventSnapshot`, which stay inside this worker
    process for their entire lifetime."""
    config = build_config()
    return _compute_audit_episode(
        config, idx=idx, topology_seed=topology_seed, coords=coords, coord_hash=coord_hash,
        energy_stage=energy_stage, n_select=n_select, n_eval=n_eval)


def _process_calibration_result(result: dict, *, idx: int, ep_seed: int, topology_seed: int,
                                 calibration_report: dict, episode_worlds: list,
                                 invalidated_pairs: list, arm_distinctness_pairs: list,
                                 calibration_units_stable: list, calibration_units_flex: list,
                                 calibration_units_d_a: list,
                                 primary_g_component_records: Optional[list] = None,
                                 primary_g_pairwise_equality: Optional[list] = None) -> None:
    """Folds one calibration episode's already-computed `result` into the
    topology-level accumulators, identically regardless of whether `result`
    came from the sequential loop or a pool worker -- this IS the sequential
    path's original per-episode tail, extracted so both paths fold results
    through the exact same code rather than two hand-kept-in-sync copies."""
    if result.get("episode_world") is not None:
        episode_worlds.append({"block": "calibration", "episode_index": idx,
                                "episode_seed": ep_seed, **result["episode_world"]})
    episode_leave_report = result.get("episode_report", {})
    _accumulate_episode_leave_stats(
        calibration_report, leave_diagnostics=episode_leave_report.get("leave_diagnostics", []),
        rejected_counts=episode_leave_report.get("rejected_counts", {}))
    if result.get("support_miss"):
        calibration_report["exclusions"].append(result.get("exclusions", []))
        print(f"[progress] topology_seed={topology_seed} calibration episode={idx} "
              f"qualifying_event=False cumulative_qualifying={calibration_report['qualifying']}",
              file=sys.stderr, flush=True)
        return
    invalidated_pairs.extend(result.get("invalidated_pairs", []))
    if primary_g_component_records is not None:
        primary_g_component_records.extend(result.get("component_records", []))
    if "stable" not in result["results"] or "flex" not in result["results"]:
        # One or both limbs invalidated by a PrefixReplayMismatchError
        # (already recorded above) -- this episode contributes neither
        # B_m nor D_A, and is not counted as qualifying.
        print(f"[progress] topology_seed={topology_seed} calibration episode={idx} "
              f"qualifying_event=False cumulative_qualifying={calibration_report['qualifying']}",
              file=sys.stderr, flush=True)
        return
    calibration_report["qualifying"] += 1
    calibration_report["qualifying_joint_events"] += 1
    arm_distinctness_pairs.append(
        (result["duty_map_at_te"], result["duty_map_before_leave"]))
    g_s, g_f = result["results"]["stable"], result["results"]["flex"]
    calibration_units_stable.append({
        "candidates": {"cvn": {"select": np.array([g_s["constructive"]["g_total"]]),
                                "eval_set": np.array([g_s["constructive"]["g_total"]])}},
        "eval_keep": np.array([g_s["null"]["g_total"]]),
    })
    calibration_units_flex.append({
        "candidates": {"cvn": {"select": np.array([g_f["constructive"]["g_total"]]),
                                "eval_set": np.array([g_f["constructive"]["g_total"]])}},
        "eval_keep": np.array([g_f["null"]["g_total"]]),
    })
    calibration_units_d_a.append({
        "candidates": {"cvn": {"select": np.array([g_s["d_a"]]),
                                "eval_set": np.array([g_s["d_a"]])}},
        "eval_keep": np.array([0.0]),
    })
    if primary_g_pairwise_equality is not None:
        for limb_name, g_entry in (("stable", g_s), ("flex", g_f)):
            if "sequences_exactly_equal" in g_entry:
                primary_g_pairwise_equality.append({
                    "topology_seed": topology_seed, "episode_index": idx, "block": "calibration",
                    "limb": limb_name, "candidate": "constructive_mixed_vs_null",
                    "sequences_exactly_equal": g_entry["sequences_exactly_equal"],
                })
    print(f"[progress] topology_seed={topology_seed} calibration episode={idx} "
          f"qualifying_event=True cumulative_qualifying={calibration_report['qualifying']}",
          file=sys.stderr, flush=True)


def _process_audit_result(raw: dict, *, idx: int, topology_seed: int, audit_report: dict,
                           episode_worlds: list, invalidated_pairs: list,
                           arm_distinctness_pairs: list, audit_units_stable: list,
                           audit_units_flex: list, audit_events_out: list,
                           primary_g_component_records: Optional[list] = None,
                           primary_g_pairwise_equality: Optional[list] = None) -> None:
    """Folds one audit-block episode's already-computed `raw` result (from
    `_compute_audit_episode`, sequential or pooled) into the topology-level
    accumulators -- the sequential path's original per-episode tail,
    extracted for the same reason as `_process_calibration_result`."""
    episode_worlds.append(raw["world_entry"])
    _accumulate_episode_leave_stats(
        audit_report, leave_diagnostics=raw.get("leave_diagnostics", []),
        rejected_counts=raw.get("rejected_counts", {}))
    if not raw["event_found"]:
        audit_report["exclusions"].append(raw["exclusions"])
        print(f"[progress] topology_seed={topology_seed} audit episode={idx} "
              f"qualifying_event=False cumulative_qualifying={audit_report['qualifying']}",
              file=sys.stderr, flush=True)
        return
    if raw.get("capture_failed"):
        invalidated_pairs.append({
            "topology_seed": topology_seed, "episode_seed": raw["ep_seed"],
            "block": "audit", "limb": "both",
            "candidate_id": "live_event_capture", "phase": "capture",
            "replicate_index": 0, "reason": raw["capture_error"],
        })
        print(f"[progress] topology_seed={topology_seed} audit episode={idx} "
              f"qualifying_event=False cumulative_qualifying={audit_report['qualifying']}",
              file=sys.stderr, flush=True)
        return
    unit_stable = raw["unit_stable"]
    unit_flex = raw["unit_flex"]
    invalidated_pairs.extend(unit_stable.get("invalidated_pairs", []))
    invalidated_pairs.extend(unit_flex.get("invalidated_pairs", []))
    if primary_g_component_records is not None:
        primary_g_component_records.extend(
            unit_stable.get("component_audit", {}).get("records", []))
        primary_g_component_records.extend(
            unit_flex.get("component_audit", {}).get("records", []))
    if primary_g_pairwise_equality is not None:
        for limb_name, unit in (("stable", unit_stable), ("flex", unit_flex)):
            for entry in unit.get("component_audit", {}).get("pairwise_equality", []):
                primary_g_pairwise_equality.append({
                    "topology_seed": topology_seed, "episode_index": idx, "block": "audit",
                    "limb": limb_name, **entry,
                })
    if unit_stable.get("event_invalid") or unit_flex.get("event_invalid"):
        print(f"[progress] topology_seed={topology_seed} audit episode={idx} "
              f"qualifying_event=False cumulative_qualifying={audit_report['qualifying']}",
              file=sys.stderr, flush=True)
        return
    audit_report["qualifying"] += 1
    audit_report["qualifying_joint_events"] += 1
    arm_distinctness_pairs.append((raw["duty_map_at_te"], raw["duty_map_before_leave"]))
    audit_units_stable.append(unit_stable)
    audit_units_flex.append(unit_flex)
    audit_events_out.append(raw["event_conformance_record"])
    print(f"[progress] topology_seed={topology_seed} audit episode={idx} "
          f"qualifying_event=True cumulative_qualifying={audit_report['qualifying']}",
          file=sys.stderr, flush=True)


def _derived_seed(*, topology_seed: int, block: str, idx: int, tag: str) -> int:
    return int(stream_seed(
        topology_seed=topology_seed, block=block, episode_seed=idx, limb="na",
        event_index=0, candidate_target_id=tag, phase="episode", replicate_index=0
    ) % (2**31 - 1))


def _new_episode_block_report() -> dict:
    """Q-E2's per-topology rolled-up report shape, shared by the calibration
    and audit blocks below."""
    return {
        "episodes_attempted": 0, "qualifying": 0, "qualifying_joint_events": 0,
        "exclusions": [], "planned_leaves_observed": 0, "leaves_before_deadline": 0,
        "rejected_counts": {k: 0 for k in REJECTION_REASON_KEYS},
        "leaves": [],
    }


def _accumulate_episode_leave_stats(report: dict, *, leave_diagnostics: list,
                                     rejected_counts: dict) -> None:
    """Rolls one episode's `roll_prefix_and_find_event` diagnostics (every
    observed LEAVE, regardless of eligibility, plus its already-computed
    rejection reasons) into the topology-level report -- called for EVERY
    attempted episode, qualifying or not, so a qualifying=0 topology still
    distinguishes 'no planned LEAVE ever occurred' from 'LEAVEs occurred but
    were rejected' (the exact ambiguity the first real smoke run collapsed)."""
    report["planned_leaves_observed"] += len(leave_diagnostics)
    report["leaves_before_deadline"] += sum(
        1 for d in leave_diagnostics if d["capture_step"] <= T_E_MAX)
    for k, v in rejected_counts.items():
        report["rejected_counts"][k] = report["rejected_counts"].get(k, 0) + v
    report["leaves"].extend(leave_diagnostics)


def run_topology_audit(config, *, topology_seed: int, n_calibration: int, n_audit: int,
                        n_select: int = N_SELECT, n_eval: int = N_EVAL, smoke: bool = False,
                        energy_stage: str = "S3", workers: int = 1) -> dict:
    """Item 5's per-topology driver: section 9 pinning, the calibration
    block (B_m, and now D_A -- Part-A conformance, stable limb only) and the
    audit block (U*_m, both limbs), assembled into the exact shapes
    `compute_t_m_bootstrap`/`compute_part_a_bounds` consume. Also
    accumulates this topology's `invalidated_pairs` (item 3: any
    `PrefixReplayMismatchError`, excluded and reported, never repaired) and
    `arm_distinctness_pairs` (item 3's spot check witnesses: every certified
    joint event's `(duty_map_at_te, duty_map_before_leave)` pair -- flex
    certification already guarantees the vacancy was coverable).

    `workers`: opt-in process parallelism ACROSS episodes WITHIN this one
    topology (never across topologies, and never splitting the calibration
    block from the audit block -- the audit block does not depend on any
    calibration-block state, so the two blocks are each parallelised
    independently, calibration first). `workers=1` (the default) takes the
    plain sequential loop below unchanged -- no pool is created, so default
    behaviour is bit-identical to every run before this option existed.
    `workers>1` runs the same per-episode computation
    (`run_calibration_episode` / `_compute_audit_episode`, untouched) inside
    a `ProcessPoolExecutor`, each worker building its own fresh `config` via
    `build_config()` rather than receiving this function's `config` argument
    (see `_calibration_episode_worker`/`_audit_episode_worker`), and folds
    the results back into the accumulators in ASCENDING episode-index order
    -- never completion order -- via `_process_calibration_result`/
    `_process_audit_result`, the exact same folding code the sequential path
    uses. This is what makes the two paths' JSON output identical; only the
    `[progress] ...` stderr line ORDER may interleave differently under
    parallelism (sub-episode replicate-level lines from `run_audit_event` in
    particular), since stderr telemetry is not part of the JSON result."""
    print(f"[progress] topology_seed={topology_seed} start "
          f"n_calibration={n_calibration} n_audit={n_audit} smoke={smoke}",
          file=sys.stderr, flush=True)
    coords, coord_hash = build_topology_template(config, topology_seed=topology_seed)
    record = build_topology_record(coords, coord_hash, topology_seed=topology_seed, config=config)
    # R2: the smoke path used to drop to n_select=1 to be cheap. n_select=1 is
    # now inadmissible, and a code path that can still run it is a footgun --
    # someone eventually reads a smoke number. At the 2/2 floor the smoke costs
    # one extra selection stream per candidate and exercises the exact
    # registered volume, so smoke and audit no longer differ in replicate shape.
    this_n_select = n_select
    this_n_eval = n_eval

    invalidated_pairs: list = []
    arm_distinctness_pairs: list = []
    # R3 section E: one provenance record per attempted episode, including the
    # ones that never qualified. A world that produced no event is still a world
    # the run visited, and dropping it would make the recorded set a filtered
    # sample rather than the run's actual history.
    episode_worlds: list = []
    # Ruling 2026-07-27: per-paired-continuation primary-G component
    # persistence and exact arm-invariance, pooled across both blocks of
    # this topology.
    primary_g_component_records: list = []
    primary_g_pairwise_equality: list = []

    calibration_units_stable, calibration_units_flex, calibration_units_d_a = [], [], []
    calibration_report = _new_episode_block_report()
    if workers <= 1:
        for idx in range(n_calibration):
            calibration_report["episodes_attempted"] += 1
            ep_seed = _derived_seed(topology_seed=topology_seed, block="calibration", idx=idx, tag="episode_seed")
            en_seed = _derived_seed(topology_seed=topology_seed, block="calibration", idx=idx, tag="energy_seed")
            result = run_calibration_episode(
                config, topology_seed=topology_seed, episode_seed=ep_seed, energy_seed=en_seed,
                coords=coords, coord_hash=coord_hash, energy_stage=energy_stage,
                episode_index=idx)
            _process_calibration_result(
                result, idx=idx, ep_seed=ep_seed, topology_seed=topology_seed,
                calibration_report=calibration_report, episode_worlds=episode_worlds,
                invalidated_pairs=invalidated_pairs, arm_distinctness_pairs=arm_distinctness_pairs,
                calibration_units_stable=calibration_units_stable,
                calibration_units_flex=calibration_units_flex,
                calibration_units_d_a=calibration_units_d_a,
                primary_g_component_records=primary_g_component_records,
                primary_g_pairwise_equality=primary_g_pairwise_equality)
    else:
        with _pinned_worker_env():
            pooled = _run_indexed_in_pool(
                _calibration_episode_worker, range(n_calibration), workers,
                topology_seed=topology_seed, coords=coords, coord_hash=coord_hash,
                energy_stage=energy_stage)
        for idx in range(n_calibration):
            calibration_report["episodes_attempted"] += 1
            ep_seed, result = pooled[idx]
            _process_calibration_result(
                result, idx=idx, ep_seed=ep_seed, topology_seed=topology_seed,
                calibration_report=calibration_report, episode_worlds=episode_worlds,
                invalidated_pairs=invalidated_pairs, arm_distinctness_pairs=arm_distinctness_pairs,
                calibration_units_stable=calibration_units_stable,
                calibration_units_flex=calibration_units_flex,
                calibration_units_d_a=calibration_units_d_a,
                primary_g_component_records=primary_g_component_records,
                primary_g_pairwise_equality=primary_g_pairwise_equality)

    audit_units_stable, audit_units_flex, audit_events_out = [], [], []
    audit_report = _new_episode_block_report()
    if workers <= 1:
        for idx in range(n_audit):
            audit_report["episodes_attempted"] += 1
            raw = _compute_audit_episode(
                config, idx=idx, topology_seed=topology_seed, coords=coords, coord_hash=coord_hash,
                energy_stage=energy_stage, n_select=this_n_select, n_eval=this_n_eval)
            _process_audit_result(
                raw, idx=idx, topology_seed=topology_seed, audit_report=audit_report,
                episode_worlds=episode_worlds, invalidated_pairs=invalidated_pairs,
                arm_distinctness_pairs=arm_distinctness_pairs,
                audit_units_stable=audit_units_stable, audit_units_flex=audit_units_flex,
                audit_events_out=audit_events_out,
                primary_g_component_records=primary_g_component_records,
                primary_g_pairwise_equality=primary_g_pairwise_equality)
    else:
        with _pinned_worker_env():
            pooled = _run_indexed_in_pool(
                _audit_episode_worker, range(n_audit), workers,
                topology_seed=topology_seed, coords=coords, coord_hash=coord_hash,
                energy_stage=energy_stage, n_select=this_n_select, n_eval=this_n_eval)
        for idx in range(n_audit):
            audit_report["episodes_attempted"] += 1
            raw = pooled[idx]
            _process_audit_result(
                raw, idx=idx, topology_seed=topology_seed, audit_report=audit_report,
                episode_worlds=episode_worlds, invalidated_pairs=invalidated_pairs,
                arm_distinctness_pairs=arm_distinctness_pairs,
                audit_units_stable=audit_units_stable, audit_units_flex=audit_units_flex,
                audit_events_out=audit_events_out,
                primary_g_component_records=primary_g_component_records,
                primary_g_pairwise_equality=primary_g_pairwise_equality)

    return {
        "topology_record": record,
        "calibration_report": calibration_report,
        "audit_report": audit_report,
        "calibration_units_stable": calibration_units_stable,
        "calibration_units_flex": calibration_units_flex,
        "calibration_units_d_a": calibration_units_d_a,
        "audit_units_stable": audit_units_stable,
        "audit_units_flex": audit_units_flex,
        "audit_events": audit_events_out,
        "qualifying_calibration_episodes": calibration_report["qualifying"],
        "qualifying_audit_episodes": audit_report["qualifying"],
        "invalidated_pairs": invalidated_pairs,
        "arm_distinctness_pairs": arm_distinctness_pairs,
        "episode_worlds": episode_worlds,
        "primary_g_component_records": primary_g_component_records,
        "primary_g_pairwise_equality": primary_g_pairwise_equality,
    }


def _json_default(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, frozenset):
        return sorted(obj)
    return str(obj)


def topology_unit_for_serialization(r: dict) -> dict:
    """Sharding support (docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md
    is silent on process topology -- this is orchestration plumbing, not a
    contract choice): the exact subset of one `run_topology_audit` topology
    result that `assemble_audit_result` reads --
    `qualifying_calibration_episodes`, `qualifying_audit_episodes`,
    `invalidated_pairs`, `arm_distinctness_pairs`, `calibration_units_stable`,
    `calibration_units_flex`, `calibration_units_d_a`, `audit_units_stable`,
    `audit_units_flex` -- plus `topology_seed` (which `assemble_audit_result`
    itself never reads) so a pooler can reorder shards' topologies back into
    ascending topology-seed order regardless of shard/argument order. This
    is what `main()` embeds under `topology_units` and what
    `scripts/pool_d7_s_event_aligned_shards.py` reconstructs from JSON --
    every numpy array nests unchanged and round-trips via `_json_default`
    (list of full-precision floats) on the way out and `np.asarray(...,
    dtype=float)` on the way back in."""
    return {
        "topology_seed": r["topology_record"]["topology_seed"],
        "qualifying_calibration_episodes": r["qualifying_calibration_episodes"],
        "qualifying_audit_episodes": r["qualifying_audit_episodes"],
        "invalidated_pairs": r["invalidated_pairs"],
        "arm_distinctness_pairs": r["arm_distinctness_pairs"],
        "calibration_units_stable": r["calibration_units_stable"],
        "calibration_units_flex": r["calibration_units_flex"],
        "calibration_units_d_a": r["calibration_units_d_a"],
        "audit_units_stable": r["audit_units_stable"],
        "audit_units_flex": r["audit_units_flex"],
        # R3 section E provenance travels WITH its shard. A pooled artifact that
        # dropped it would carry the numbers without the worlds they were
        # measured in, which is the exact gap that retired ep64.
        "episode_worlds": r.get("episode_worlds", []),
        # Ruling 2026-07-27 (D7.S component-cancellation prospective repair):
        # per-paired-continuation primary-G component records (QoS/return-
        # cost series, transition series, window totals, total G, QoS
        # saturation, paired arm identity) and the exact paired-sequence
        # equality computed per continuation before serialization. `.get`
        # defaults keep a pre-repair shard poolable (see `episode_worlds`
        # above for the same convention) -- `assemble_audit_result` never
        # reads either key, so this is additive, not load-bearing for the
        # branch decision.
        "primary_g_component_records": r.get("primary_g_component_records", []),
        "primary_g_pairwise_equality": r.get("primary_g_pairwise_equality", []),
    }


def resolve_run_plan(*, smoke: bool, dev: bool, topology_seeds_override: Optional[list],
                      episodes_calibration: Optional[int], episodes_audit: Optional[int]) -> dict:
    """CLI arg resolution (item 2): topology seed list plus episode counts.
    `--episodes-calibration`/`--episodes-audit` are honored in EVERY mode,
    `--smoke` included -- previously `--smoke` hardcoded 1/1 unconditionally,
    silently discarding any explicit override. Smoke no longer carries a
    replicate override at all: R2 made `n_select=1` inadmissible, so
    `run_topology_audit` runs the registered 2/2 volume in every mode and only
    the `SMOKE_NOT_A_RESULT` JSON labeling distinguishes them. This function
    governs only the episode COUNTS. `None` for either count means
    "use this mode's own default" -- smoke's default stays 1 calibration + 1
    audit episode when no override is given, matching its pre-existing fast
    proof-sized behavior."""
    if smoke:
        topology_seeds = [TOPOLOGY_SEED_DEV]
        default_calibration, default_audit = 1, 1
    elif topology_seeds_override:
        topology_seeds = list(topology_seeds_override)
        default_calibration, default_audit = N_CALIBRATION_EPISODES, N_AUDIT_EPISODES
    elif dev:
        topology_seeds = [TOPOLOGY_SEED_DEV]
        default_calibration, default_audit = N_CALIBRATION_EPISODES, N_AUDIT_EPISODES
    else:
        topology_seeds = list(TOPOLOGY_SEEDS_INITIAL)
        default_calibration, default_audit = N_CALIBRATION_EPISODES, N_AUDIT_EPISODES
    return {
        "topology_seeds": topology_seeds,
        "n_calibration": episodes_calibration if episodes_calibration is not None else default_calibration,
        "n_audit": episodes_audit if episodes_audit is not None else default_audit,
    }


def assemble_audit_result(topology_results: list[dict], topology_hash_failures: list[dict],
                           *, component_invariance_evaluated: bool = False) -> dict:
    """`component_invariance_evaluated` defaults **False**, which is the
    fail-closed direction (ruling 2026-07-27, COMPONENT_INVARIANCE): a run
    that is not already normalizer-forced-degenerate and never performed the
    mandatory primary-G component audit resolves to branch 1, because "later
    branches cannot fire on a future run whose mandatory component audit is
    missing." Production passes nothing and therefore gets False.

    It is a parameter rather than a hardcoded literal so a caller can declare
    the world in which the audit WAS performed -- which is what the
    branch-precedence fixtures for branches 4-10 do. Hardcoding it either way
    is the defect this whole repair exists to remove; the safe polarity is
    that omitting it can only make the instrument stricter, never looser."""
    """Item 5/8's driver-level wiring, isolated from `main()`'s CLI/env
    concerns so it can be exercised directly against synthetic
    `topology_results` (the exact shape `run_topology_audit` returns)
    without a real environment.

    Pools per-topology conformance and Part-A inputs into `decide_branch`'s
    two driver inputs exactly as section 8 specifies:

    `conformance_ok` -- `compute_conformance_ok` over the pooled
    `invalidated_pairs` count (every topology's `PrefixReplayMismatchError`
    records), the pinned-topology hash assert (`topology_hash_failures`,
    reported per topology in `main`'s per-seed loop), and
    `arm_distinctness_check` over every topology's certified-event duty-map
    pairs pooled together.

    `part_a_contradiction` -- `compute_part_a_bounds` bootstraps D_A jointly
    with B_stable from the pooled per-topology `calibration_units_d_a`/
    `calibration_units_stable`, sharing the SAME `shared_topology_indices`
    stream `compute_t_m_bootstrap` already drew (section 8's common
    resampling stream); `part_a_conformance` turns those bounds into a
    verdict string; `map_part_a_verdict_to_inputs` maps ONLY
    `PART_A_CONTRADICTION` to `part_a_contradiction=True` --
    `PART_A_CONFORMANCE_UNRESOLVED` (like `CONFORMANCE_PASS` and
    `NOT_APPLICABLE`) never flips it, per section 8: the unresolved
    diagnostic "does not relabel the source branch." It still lands in the
    JSON under `part_a.verdict` for the record.

    Both driver inputs then reach `decide_branch` for real: when there are
    at least two topologies and support holds, `decide_branch` is called
    with the pooled `conformance_ok`/`part_a_contradiction` plus the T_m
    bootstrap bounds, so a conformance failure or a Part-A contradiction
    reaches branch 1/4 through the same first-match precedence as every
    other branch. Outside that gate (a single topology, or support already
    failed) `decide_branch` cannot run a T_m bootstrap at all, so branch
    1/2 are reported directly by the same literal strings `decide_branch`
    itself would have returned first in its precedence order -- conformance
    failure is checked before support failure in both paths, matching
    `decide_branch`'s row order."""
    support_ok, support_detail = check_minimum_support([
        {"qualifying_calibration_episodes": r["qualifying_calibration_episodes"],
         "qualifying_audit_episodes": r["qualifying_audit_episodes"]}
        for r in topology_results
    ])

    invalidated_pairs_total = [p for r in topology_results for p in r["invalidated_pairs"]]
    arm_distinctness_pairs_all = [p for r in topology_results for p in r["arm_distinctness_pairs"]]
    topology_hash_ok = len(topology_hash_failures) == 0
    arm_distinct_ok = arm_distinctness_check(arm_distinctness_pairs_all)
    conformance_ok = compute_conformance_ok(
        invalidated_pairs=len(invalidated_pairs_total), topology_hash_ok=topology_hash_ok,
        arm_distinct_ok=arm_distinct_ok)

    out: dict = {
        "support": {"ok": support_ok, "detail": support_detail},
        "conformance": {
            "ok": conformance_ok,
            "invalidated_pairs_count": len(invalidated_pairs_total),
            "invalidated_pairs": invalidated_pairs_total,
            "topology_hash_ok": topology_hash_ok,
            "topology_hash_failures": topology_hash_failures,
            "arm_distinct_ok": arm_distinct_ok,
        },
    }

    # R3 section E: episode-world provenance. `all_seed_controlled` is the
    # readable verdict -- False means at least one episode ran in a world that
    # cannot be regenerated, so that episode's contrast is in the same position
    # ep64 was in and must not be read as matched causal evidence. It is
    # reported rather than gated: the run is still a valid record of what
    # happened, and whether incomplete provenance retires a reading is a
    # scientific call, not an instrument one.
    episode_worlds_all = [w for r in topology_results for w in r.get("episode_worlds", [])]
    out["episode_world_provenance"] = {
        "all_seed_controlled": all(
            bool(w.get("seed_controls_generation")) for w in episode_worlds_all
        ) if episode_worlds_all else False,
        "episodes_recorded": len(episode_worlds_all),
        "episodes_not_seed_controlled": [
            {k: w.get(k) for k in ("block", "episode_index", "episode_seed", "fingerprint")}
            for w in episode_worlds_all if not w.get("seed_controls_generation")
        ],
        "episode_worlds": episode_worlds_all,
    }

    # R2 section 8: the selection diagnostic is a required artifact field, not
    # an optional extra. At the 2/2 floor an unstable maximizer must be visible
    # rather than hidden behind a point winner.
    out["selection_diagnostic"] = {
        limb: [
            dict(topology_index=ti,
                 topology_seed=r.get("topology_record", {}).get("topology_seed"),
                 event_index=ei, **entry)
            for ti, r in enumerate(topology_results)
            for ei, entry in enumerate(selection_diagnostic(r.get(key, [])))
        ]
        for limb, key in (("stable", "audit_units_stable"), ("flex", "audit_units_flex"))
    }

    if len(topology_results) > 1 and support_ok:
        n_topo = len(topology_results)
        t_m = compute_t_m_bootstrap(
            b_stable_topology_units=[r["calibration_units_stable"] for r in topology_results],
            b_flex_topology_units=[r["calibration_units_flex"] for r in topology_results],
            u_star_stable_topology_units=[r["audit_units_stable"] for r in topology_results],
            u_star_flex_topology_units=[r["audit_units_flex"] for r in topology_results],
            n_topo=n_topo)
        out["t_m_bootstrap"] = {k: v for k, v in t_m.items() if k != "shared_topology_indices"}

        # Part-A conformance (item 2): the SAME shared topology-resampling
        # stream `compute_t_m_bootstrap` already drew, so D_A and B_stable's
        # per-iteration draws come from the identical resampled topology mix
        # as every other primary quantity (section 8's "common resampling
        # stream" / "do not assign separate resampling seeds").
        part_a_bounds = compute_part_a_bounds(
            d_a_topology_units=[r["calibration_units_d_a"] for r in topology_results],
            b_stable_topology_units=[r["calibration_units_stable"] for r in topology_results],
            shared_topology_indices=t_m["shared_topology_indices"], seed=BOOTSTRAP_SEED)
        if part_a_bounds is None:
            part_a_verdict = "NOT_APPLICABLE"
        else:
            part_a_verdict = part_a_conformance(
                lower_contrast_lcb=part_a_bounds["lower_contrast_lcb"],
                lower_contrast_ucb=part_a_bounds["lower_contrast_ucb"],
                upper_contrast_lcb=part_a_bounds["upper_contrast_lcb"],
                b_stable_lcb=part_a_bounds["b_stable_lcb"])
        part_a_contradiction, part_a_diagnostic = map_part_a_verdict_to_inputs(part_a_verdict)
        out["part_a"] = {
            "verdict": part_a_diagnostic,
            **({} if part_a_bounds is None else part_a_bounds),
        }

        # Ruling 2026-07-27 (VERDICT_Q2): B_m's positive-LCB gate is
        # disjunctive across limbs -- computed here from the SAME t_m
        # bounds, through `primary_g_degenerate` (the single place the flag
        # is computed), never re-derived inline. `stable_b_identified`/
        # `flex_b_identified` and a per-limb status string are recorded in
        # the payload so a limb whose normalizer failed to identify is
        # visible rather than folded into a generic "unresolved", and
        # `component_invariance_evaluated=False` records that this branch's
        # component-invariance input has no production derivation and was
        # not evaluated (see `primary_g_degenerate`'s docstring).
        stable_b_identified = t_m["b_stable_lcb"] > 0
        flex_b_identified = t_m["b_flex_lcb"] > 0
        primary_g_degenerate_flag = primary_g_degenerate(
            stable_b_identified=stable_b_identified, flex_b_identified=flex_b_identified)
        out["primary_g"] = {
            "degenerate": primary_g_degenerate_flag,
            "stable_b_identified": stable_b_identified,
            "flex_b_identified": flex_b_identified,
            "component_invariance_evaluated": component_invariance_evaluated,
            "stable_status": ("NORMALIZER_NOT_IDENTIFIED" if not stable_b_identified
                               else "NORMALIZER_IDENTIFIED"),
            "flex_status": ("NORMALIZER_NOT_IDENTIFIED" if not flex_b_identified
                             else "NORMALIZER_IDENTIFIED"),
        }

        out["branch"] = decide_branch(
            conformance_ok=conformance_ok, support_ok=support_ok,
            primary_g_degenerate_flag=primary_g_degenerate_flag,
            part_a_contradiction=part_a_contradiction, b_stable_lcb=t_m["b_stable_lcb"],
            t_stable_ucb=t_m["t_stable_ucb"], t_stable_lcb=t_m["t_stable_lcb"],
            b_flex_lcb=t_m["b_flex_lcb"], t_flex_lcb=t_m["t_flex_lcb"], t_flex_ucb=t_m["t_flex_ucb"],
            # Passed from the payload rather than defaulted. Today this is
            # always False, so the tri-state's missing-audit gate is live: a
            # run that is NOT normalizer-forced-degenerate but never performed
            # the mandatory component audit resolves to branch 1. That is the
            # ruling's fail-closed direction, and it has no effect on a
            # normalizer-forced run, which resolves at branch 3 first.
            component_invariance_evaluated=out["primary_g"]["component_invariance_evaluated"])
    elif not conformance_ok:
        out["branch"] = "INVALID_EVENT_ALIGNED_AUDIT"
    elif not support_ok:
        out["branch"] = "SOURCE_EVENT_SUPPORT_INSUFFICIENT"
    else:
        out["branch"] = None

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", action="store_true",
                         help="Use the development-only topology 20260725; no scientific reading.")
    parser.add_argument("--topology-seeds", type=int, nargs="*", default=None,
                         help="Override the registered topology seed list.")
    parser.add_argument("--episodes-calibration", type=int, default=None,
                         help="Override the calibration episode count for the selected mode "
                              "(including --smoke, which otherwise defaults to 1).")
    parser.add_argument("--episodes-audit", type=int, default=None,
                         help="Override the audit episode count for the selected mode "
                              "(including --smoke, which otherwise defaults to 1).")
    parser.add_argument("--out", default="")
    parser.add_argument("--smoke", action="store_true",
                         help="ONE topology, ONE calibration + ONE audit episode by default "
                              "(overridable via --episodes-calibration/--episodes-audit), full "
                              "horizon pieces at the SAME registered n_select=2/n_eval=2 volume "
                              "as the formal audit. JSON tagged SMOKE_NOT_A_RESULT. Proof-sized "
                              "only -- not the formal audit.")
    parser.add_argument("--workers", type=int, default=1,
                         help="Process-parallelise episodes WITHIN one topology (calibration "
                              "block and audit block each parallelised separately, calibration "
                              "first). Default 1 takes the plain sequential path unchanged -- no "
                              "pool is created. Results are folded back in ascending episode-"
                              "index order regardless of worker count, so the JSON output is "
                              "identical to the sequential run; only the interleaving of "
                              "per-episode [progress] stderr lines may differ under parallelism.")
    args = parser.parse_args()

    plan = resolve_run_plan(
        smoke=args.smoke, dev=args.dev, topology_seeds_override=args.topology_seeds,
        episodes_calibration=args.episodes_calibration, episodes_audit=args.episodes_audit)
    topology_seeds, n_calibration, n_audit = plan["topology_seeds"], plan["n_calibration"], plan["n_audit"]

    config = build_config()
    topology_results = []
    topology_hash_failures = []
    for seed in topology_seeds:
        # A pinned-topology `TopologyMismatchError` fails the run (never
        # repaired, section 9) -- caught HERE, per topology, so it becomes a
        # reported `INVALID_EVENT_ALIGNED_AUDIT` (branch 1) result rather
        # than an uncaught crash; the failing topology contributes no data.
        # `PrefixReplayMismatchError` is already caught per-pair inside
        # `run_calibration_episode`/`run_audit_event` (item 3: an invalidated
        # pair excludes the pair and is reported, never the whole run) and
        # never escapes here.
        try:
            topo_out = run_topology_audit(
                config, topology_seed=seed, n_calibration=n_calibration, n_audit=n_audit,
                smoke=args.smoke, workers=args.workers)
        except TopologyMismatchError as exc:
            topology_hash_failures.append({"topology_seed": seed, "reason": str(exc)})
            continue
        topology_results.append(topo_out)
        if args.out:
            write_topology_record(args.out, topo_out["topology_record"])

    # Section 9's one permissible expansion (ruling 2026-07-27): refuses a
    # run whose topology-seed set IS the registered 16-topology expansion
    # union unless the frozen predicate, evaluated against the initial 8
    # topologies alone, licenses it. A no-op for every other seed set --
    # smoke, dev, the plain 8-seed default -- so those affordances are
    # unaffected.
    check_expansion_justified(topology_seeds, topology_results, topology_hash_failures)

    result = {
        "contract": CONTRACT_PATH,
        "contract_id": CONTRACT_ID,
        "procedure_version": TOPOLOGY_PROCEDURE_VERSION,
        "topology_seeds": topology_seeds,
        "smoke": bool(args.smoke),
        "note": "SMOKE_NOT_A_RESULT" if args.smoke else "Real orchestration run.",
        "topology_records": [r["topology_record"] for r in topology_results],
        "calibration_reports": [r["calibration_report"] for r in topology_results],
        "audit_reports": [r["audit_report"] for r in topology_results],
        "audit_events": [r["audit_events"] for r in topology_results],
        # Sharding support (Task A): a complete, numerically lossless
        # per-topology serialization of every `run_topology_audit` output key
        # `assemble_audit_result` consumes, so a per-topology shard's JSON is
        # self-sufficient for `pool_d7_s_event_aligned_shards.py` to
        # reconstruct `topology_results` and call `assemble_audit_result`
        # itself over the pooled union -- see `topology_unit_for_serialization`.
        "topology_units": [topology_unit_for_serialization(r) for r in topology_results],
        "topology_hash_failures": topology_hash_failures,
    }
    result.update(assemble_audit_result(topology_results, topology_hash_failures))

    print(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        with (out / "d7_s_event_aligned.json").open("w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2, default=_json_default)


if __name__ == "__main__":
    main()
