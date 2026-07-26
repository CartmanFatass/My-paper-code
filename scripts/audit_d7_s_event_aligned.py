"""D7.S event-aligned source audit.

Contract (frozen, verbatim authority for every semantic choice):
    docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md (FROZEN 2026-07-26)
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

Honest scope of `main()` (implementer, 2026-07-26): it is NOT a completed
audit runner. It executes the section 9 topology-template construction and
serializes each topology's pinning record (`build_topology_template` /
`build_topology_record` / `write_topology_record`) -- genuinely real,
lightweight environment construction, no episode stepping -- but it does NOT
run episodes, does NOT detect or certify events against a live environment,
and does NOT execute the bootstrap. The event-detection -> legal-SET ->
bootstrap pipeline above is proved by the focused test suite against
synthetic/pure inputs only. Wiring it to real episodes is the proof-sized
exercise named in the contract's evidence order (section 11, item 2) and is a
later evidence action, not attempted here.

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
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

CONTRACT_PATH = "docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md"
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
N_SELECT = 4
N_EVAL = 8
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


def build_topology_record(coords: dict, coord_hash: str, *, topology_seed: int) -> dict:
    """Section 9's mandatory per-topology record: coordinates, canonical
    hash, topology seed, reinitialization procedure version."""
    return {
        "topology_seed": int(topology_seed),
        "ground_bs": [[float(v) for v in row] for row in coords["ground_bs"]],
        "charging_stations": [[float(v) for v in row] for row in coords["charging_stations"]],
        "coordinate_hash": coord_hash,
        "procedure_version": TOPOLOGY_PROCEDURE_VERSION,
    }


def write_topology_record(out_dir, record: dict) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"topology_{record['topology_seed']}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=2)
    return path


def build_pinned_env(config, *, episode_seed: int, coords: dict, coord_hash: str,
                      energy_stage: str = "S3"):
    """Steps 3-7 of the section 9 pinning procedure, in the load-bearing order:
    fresh env, reset with the EPISODE seed, restore the recorded coordinates
    only AFTER that reset (Scenario 7's reset calls `_init_charging_stations`,
    so restoring before it is insufficient), rebuild channel/routing state,
    and assert the hash before any prefix replay."""
    from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv

    env = UAVEnergyAwareRelayEnv(config=config, energy_stage=energy_stage)
    env.reset(seed=int(episode_seed))                       # step 4
    env.ground_bs_positions = coords["ground_bs"].copy()     # step 5 (no RNG consumed)
    env.charging_station_positions = coords["charging_stations"].copy()
    env._update_channel_state()                              # step 6
    env._update_uav_connections()
    env._compute_routing_paths()
    actual_hash = coordinate_hash(env.ground_bs_positions,    # step 7
                                   env.charging_station_positions)
    if actual_hash != coord_hash:
        raise TopologyMismatchError(
            f"topology hash mismatch: expected {coord_hash}, got {actual_hash}"
        )
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


def primary_g_degenerate(*, component_sequences_arm_invariant: bool,
                          b_m_positive_lcb: bool) -> bool:
    """PRIMARY_G_DEGENERATE fires when all four component sequences are
    exactly arm-invariant under pairing, OR B_m cannot establish a positive
    source-control contrast."""
    return component_sequences_arm_invariant or not b_m_positive_lcb


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
# Section 10 -- ten-branch first-match decision
# =============================================================================

def decide_branch(*, conformance_ok: bool, support_ok: bool,
                   primary_g_degenerate_flag: bool, part_a_contradiction: bool,
                   b_stable_lcb: float, t_stable_ucb: float, t_stable_lcb: float,
                   b_flex_lcb: float, t_flex_lcb: float, t_flex_ucb: float) -> str:
    """First-match precedence over the ten registered branches."""
    if not conformance_ok:
        return "INVALID_EVENT_ALIGNED_AUDIT"
    if not support_ok:
        return "SOURCE_EVENT_SUPPORT_INSUFFICIENT"
    if primary_g_degenerate_flag:
        return "PRIMARY_G_DEGENERATE"
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

    return {
        "b_stable_lcb": b_stable["lo"],
        "b_flex_lcb": b_flex["lo"],
        "t_stable_ucb": float(np.percentile(t_stable_finite, 95)) if t_stable_finite.size else float("nan"),
        "t_stable_lcb": float(np.percentile(t_stable_finite, 5)) if t_stable_finite.size else float("nan"),
        "t_flex_lcb": float(np.percentile(t_flex_finite, 5)) if t_flex_finite.size else float("nan"),
        "t_flex_ucb": float(np.percentile(t_flex_finite, 95)) if t_flex_finite.size else float("nan"),
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", action="store_true",
                         help="Use the development-only topology 20260725; no scientific reading.")
    parser.add_argument("--out", default="")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    topology_seeds = [TOPOLOGY_SEED_DEV] if args.dev else list(TOPOLOGY_SEEDS_INITIAL)
    config = build_config()

    # Section 9 steps 1-2 only: construct each topology template and
    # serialize its pinning record. Real, lightweight environment
    # construction (no episode stepping) -- see the module docstring for
    # exactly what this does and does not cover.
    topology_records = []
    for seed in topology_seeds:
        coords, coord_hash = build_topology_template(config, topology_seed=seed)
        record = build_topology_record(coords, coord_hash, topology_seed=seed)
        topology_records.append(record)
        if args.out:
            write_topology_record(args.out, record)

    result = {
        "contract": CONTRACT_PATH,
        "contract_id": CONTRACT_ID,
        "note": (
            "Orchestration scaffold, not a completed audit: this run executed section 9's "
            "topology-template construction and pinning-record serialization ONLY (real, "
            "lightweight environment construction, no episode stepping). The "
            "event-detection -> legal-SET -> bootstrap pipeline is proved by the focused "
            "test suite against synthetic inputs and was NOT executed against a real "
            "environment here -- see the module docstring and the accompanying report."
        ),
        "topology_seeds": topology_seeds,
        "topology_records": [
            {"topology_seed": r["topology_seed"], "coordinate_hash": r["coordinate_hash"]}
            for r in topology_records
        ],
        "heldout_low": [float(x) for x in HELDOUT_LOW],
        "thresholds": {
            "X_stable_m": X_STABLE_DISPLACEMENT_M,
            "Y_flex_steps": Y_FLEX_STEPS,
            "Z_flex_transit_steps": Z_FLEX_TRANSIT_STEPS,
            "H_stable": H_STABLE,
            "H_flex": H_FLEX,
            "t_e_max": T_E_MAX,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        with (out / "d7_s_event_aligned.json").open("w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
