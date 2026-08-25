"""Complete result-blind reducer and analyzer seams for DISH RBHR r05."""

from __future__ import annotations

import hashlib
import math
import time
from typing import Mapping, Sequence
import json

import numpy as np

from .analysis import classify_atomic, joint_max_t
from .production_contract import BOOTSTRAP_RESAMPLES, BRANCHES, ENDPOINTS


REGIMES = ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
CLAIM_SCHEDULES = ("K8", "K4_TO_K12", "K12_TO_K4")
STRATA = ("POSITIVE", "NEAR_ZERO", "NEGATIVE")
ARMS = ("STRUCTURED", "FLEX", "NEVER", "IMMEDIATE", "HYSTERESIS")
FULL_CONTRASTS = ("S-N", "F-S", "F-N", "I-N", "I-S", "H-N", "H-S")
ALL_CONTRASTS = (*FULL_CONTRASTS, "REAL-SHAM")
HARD_EVENTS = (
    "invalid_commit", "token_gap", "dual_owner", "dual_payload", "buffer_clear",
    "command_slew_breach", "separation_breach",
)
PHASES_BY_SCHEDULE = {
    "K8": tuple(range(8)),
    "K4_TO_K12": tuple(range(4)),
    "K12_TO_K4": tuple(range(12)),
}


class ProductionAnalysisError(ValueError):
    pass


def service_fraction(bits: Sequence[int]) -> float:
    values = np.asarray(bits, dtype=np.int8)
    if values.ndim != 1 or values.size == 0 or not np.isin(values, (0, 1)).all():
        raise ProductionAnalysisError("service bits must be one nonempty Boolean vector")
    return float(values.mean())


def service_deficit(bits: Sequence[int]) -> float:
    values = np.asarray(bits, dtype=np.int8)
    return 0.1 * float(values.size - values.sum())


def recovery_delay(bits: Sequence[int]) -> float:
    values = np.asarray(bits, dtype=np.int8)
    invalid = np.flatnonzero(values == 0)
    if invalid.size == 0:
        return 0.0
    start = int(invalid[0])
    for index in range(start, max(start, values.size - 9)):
        if index + 10 <= values.size and bool(np.all(values[index:index+10] == 1)):
            return 0.1 * (index - start)
    return 0.1 * values.size


def fractional_cvar_10(service_fractions: Sequence[float]) -> float:
    values = np.sort(np.asarray(service_fractions, dtype=np.float64))
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ProductionAnalysisError("CVaR input differs")
    q = 0.1 * values.size; whole = int(math.floor(q)); total = float(values[:whole].sum())
    if whole < values.size:
        total += (q - whole) * float(values[whole])
    return total / q


def endpoint_vector(service_rows: np.ndarray) -> dict[str, float]:
    values = np.asarray(service_rows, dtype=np.int8)
    if values.shape != (16, 200) or not np.isin(values, (0, 1)).all():
        raise ProductionAnalysisError("full endpoint cell must be exactly 16 tapes x 200 ticks")
    fractions = values.mean(axis=1)
    result = {
        "MEAN": float(fractions.mean()),
        "TAIL": fractional_cvar_10(fractions),
        "DEFICIT": float(np.mean([service_deficit(row) for row in values])),
        "DELAY": float(np.mean([recovery_delay(row) for row in values])),
    }
    if tuple(result) != ENDPOINTS:
        raise ProductionAnalysisError("endpoint order differs")
    return result


def reduce_full_cell_rows(
    service: np.ndarray,
    tau_d_ticks: Sequence[int],
    full_energy: Sequence[float],
    hard_event_presence: np.ndarray,
) -> dict[str, object]:
    values = np.asarray(service, dtype=np.int8)
    onset = np.asarray(tau_d_ticks, dtype=np.int64)
    energy = np.asarray(full_energy, dtype=np.float64)
    hard = np.asarray(hard_event_presence, dtype=np.int8)
    if values.shape != (16, 1_200) or onset.shape != (16,) or energy.shape != (16,) or hard.shape != (16, 7):
        raise ProductionAnalysisError("full cell rows have an unregistered shape")
    if not np.isin(values, (0, 1)).all() or not np.isin(hard, (0, 1)).all() or not np.isfinite(energy).all():
        raise ProductionAnalysisError("full cell rows contain invalid values")
    windows = np.stack([values[index, tick:tick+200] for index, tick in enumerate(onset)])
    if windows.shape != (16, 200):
        raise ProductionAnalysisError("event window escapes the 1200-tick episode")
    endpoints = endpoint_vector(windows)
    return {
        "endpoints": endpoints,
        "energy": float(energy.mean()),
        "hard_event_rates": hard.mean(axis=0).tolist(),
        "minimum_hard_event_rate": float(hard.mean(axis=0).min()),
        "row_count": 16,
    }


def reduce_fork_rows(
    service: np.ndarray,
    energy: Sequence[float],
    hard_event_presence: np.ndarray,
) -> dict[str, object]:
    values = np.asarray(service, dtype=np.int8)
    if values.ndim != 2 or values.shape[1] != 100 or values.shape[0] == 0:
        raise ProductionAnalysisError("fork rows must be nonempty trigger rows x 100 ticks")
    energies = np.asarray(energy, dtype=np.float64)
    hard = np.asarray(hard_event_presence, dtype=np.int8)
    if energies.shape != (values.shape[0],) or hard.shape != (values.shape[0], 7):
        raise ProductionAnalysisError("fork cost rows differ")
    fractions = values.mean(axis=1)
    endpoints = {
        "MEAN": float(fractions.mean()),
        "TAIL": fractional_cvar_10(fractions),
        "DEFICIT": float(np.mean([service_deficit(row) for row in values])),
        "DELAY": float(np.mean([recovery_delay(row) for row in values])),
    }
    return {"endpoints": endpoints, "energy": float(energies.mean()), "hard_event_rates": hard.mean(axis=0).tolist(), "row_count": int(values.shape[0])}


def aggregate_atomic_labels(labels: Mapping[tuple[str, str], str]) -> dict[str, object]:
    regimes = ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
    schedules = ("K8", "K4_TO_K12", "K12_TO_K4")
    expected = {(regime, schedule) for regime in regimes for schedule in schedules}
    if set(labels) != expected:
        raise ProductionAnalysisError("atomic label inventory is incomplete")
    positive = {"STRUCTURED_ATOMIC_VALUE", "FLEXIBLE_CONTAINER_SUPERIOR", "SIMPLE_RULE_SUFFICIENT[IMMEDIATE]", "SIMPLE_RULE_SUFFICIENT[HYSTERESIS]"}
    per_regime: dict[str, str] = {}
    for regime in regimes:
        ordered = tuple(labels[(regime, schedule)] for schedule in schedules)
        if all(value == "SIMPLE_RULE_SUFFICIENT[IMMEDIATE]" for value in ordered):
            result = "SIMPLE_RULE_SUFFICIENT[IMMEDIATE]"
        elif all(value == "SIMPLE_RULE_SUFFICIENT[HYSTERESIS]" for value in ordered):
            result = "SIMPLE_RULE_SUFFICIENT[HYSTERESIS]"
        elif all(value == "FLEXIBLE_CONTAINER_SUPERIOR" for value in ordered):
            result = "FLEXIBLE_CONTAINER_SUPERIOR"
        elif all(value == "STRUCTURED_ATOMIC_VALUE" for value in ordered):
            result = "STRUCTURED_REGIME_SPECIFIC_VALUE"
        elif ordered[0] in positive and (ordered[1] != ordered[0] or ordered[2] != ordered[0]):
            result = f"FIXED_ONLY_NO_SWITCH_K_VALUE[{ordered[0]}|{ordered[1]}|{ordered[2]}]"
        else:
            result = "NO_COMMON_THREE_SCHEDULE_RETAINED_VALUE[" + "|".join(ordered) + "]"
        per_regime[regime] = result
    if all(value == "STRUCTURED_REGIME_SPECIFIC_VALUE" for value in per_regime.values()):
        cross = "STRUCTURED_CROSS_REGIME_VALUE"
    elif len(set(per_regime.values())) == 1 and next(iter(per_regime.values())).startswith(("SIMPLE_RULE_SUFFICIENT", "FLEXIBLE_CONTAINER_SUPERIOR")):
        cross = next(iter(per_regime.values()))
    else:
        cross = "PACKAGE_SPECIFIC_OR_NO_COMMON_CROSS_REGIME_VALUE"
    return {"atomic": {f"{regime}/{schedule}": labels[(regime, schedule)] for regime in regimes for schedule in schedules}, "regime": per_regime, "cross_regime": cross}


def run_result_blind_analyzer_seam() -> dict[str, object]:
    started = time.perf_counter()
    block = np.arange(24, dtype=np.float64)[:, None]
    estimand = np.arange(32, dtype=np.float64)[None, :]
    values = 0.04 * np.sin((block + 1) * (estimand + 1) * 0.017) + 0.001 * estimand
    values[:, 0] = 0.0
    inference = joint_max_t(values, resamples=BOOTSTRAP_RESAMPLES, chunk_size=512, test_key=b"DISH-RBHR-R05-PRODUCTION-PREACTIVITY-ANALYZER-V1")
    branch_labels = []
    for branch in range(1, BRANCHES + 1):
        vector: dict[str, object] = {"protocol_ok": True, "comp": True, "witness": True, "headroom": True, "precision": True, "support": True}
        if branch == 1: vector["protocol_ok"] = False
        elif branch == 2: vector["comp"] = False
        elif branch == 3: vector["witness"] = False
        elif branch == 4: vector["headroom"] = False
        elif branch == 5: vector["support"] = False
        elif branch == 6: vector["harm"] = True
        elif branch == 7: vector["package_effect"] = True
        elif branch == 8: vector["fork_excluded"] = True
        elif branch == 9: vector["rulequal_i"] = True
        elif branch == 10: vector["rulequal_h"] = True
        elif branch == 11: vector["flexqual"] = True
        elif branch == 12: vector["flex_rel"] = True
        elif branch == 13: vector["core"] = True
        elif branch == 14: vector["nm_all"] = True
        observed = classify_atomic(vector)
        if observed[0] != branch:
            raise ProductionAnalysisError(f"first-match seam failed at branch {branch}: {observed}")
        branch_labels.append(observed[1])
    bits = ((np.arange(16)[:, None] + np.arange(200)[None, :]) % 13 != 0).astype(np.int8)
    endpoints = endpoint_vector(bits)
    digest = hashlib.sha256(np.asarray(list(endpoints.values()), dtype=np.float64).tobytes()).hexdigest()
    return {
        "schema": "DISH_RBHR_R05_PRODUCTION_ANALYZER_SEAM_V1",
        "test_only": True,
        "question_relevant_output": False,
        "resamples": inference["resamples"],
        "estimands": inference["estimands"],
        "all_intervals_finite": inference["all_finite"],
        "branch_count": len(branch_labels),
        "branch_labels": branch_labels,
        "endpoint_order": list(endpoints),
        "reducer_sha256": digest,
        "wall_seconds": time.perf_counter() - started,
    }


def complete_hypothesis_inventory() -> dict[str, int]:
    competence_no_degradation = 5 * 2 * 2 * 3
    competence_pre_onset = 5 * 2 * 3 * 3
    opportunity_witness = 5 * (2 * 3 * 3)
    adaptive_support = 4 * (2 * 3 * 3)
    never_headroom = 2 * (2 * 3 * 3)
    endpoint_effects = 8 * 4 * (2 * 3 * 3)
    energy_effects = 8 * (2 * 3 * 3)
    hard_event_rates = (5 + 2) * 7 * (2 * 3 * 3)
    phase_cells = 2 * 3 * (8 + 4 + 12)
    phase_endpoint_differences = 7 * 4 * phase_cells
    phase_energy_differences = 7 * phase_cells
    rows = {
        "competence_no_degradation": competence_no_degradation,
        "competence_pre_onset": competence_pre_onset,
        "opportunity_drop_maintain_gain_continuity": opportunity_witness,
        "trigger_and_behavior_support": adaptive_support,
        "never_headroom": never_headroom,
        "endpoint_effects": endpoint_effects,
        "energy_effects": energy_effects,
        "absolute_hard_event_rates": hard_event_rates,
        "phase_endpoint_differences": phase_endpoint_differences,
        "phase_energy_differences": phase_energy_differences,
    }
    rows["total"] = sum(rows.values())
    return rows


def complete_estimand_manifest() -> tuple[str, ...]:
    """Enumerate every frozen max-t member in one canonical, unique order.

    This is an identity mapper only.  It never receives or materializes block
    values, intervals, labels, or any other question-relevant quantity.
    """

    rows: list[str] = []

    def add(family: str, *coordinates: object) -> None:
        rows.append("/".join((family, *(str(value) for value in coordinates))))

    for arm in ARMS:
        for regime in REGIMES:
            for schedule in ("K4", "K12"):
                for stratum in STRATA:
                    add("COMPETENCE_NO_DEGRADATION", arm, regime, schedule, stratum)
    for arm in ARMS:
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for stratum in STRATA:
                    add("COMPETENCE_PRE_ONSET", arm, regime, schedule, stratum)

    for quantity in ("Q", "DROP", "MAINTAIN", "WITNESS_GAIN", "WITNESS_CONTINUITY"):
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for stratum in STRATA:
                    add("OPPORTUNITY", quantity, regime, schedule, stratum)
    for arm in ("STRUCTURED", "FLEX"):
        for quantity in ("TRIGGER_RATE", "BEHAVIOR_CHANGING_SUPPORT"):
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for stratum in STRATA:
                        add("ADAPTIVE_SUPPORT", arm, quantity, regime, schedule, stratum)
    for quantity in ("NEVER_EVENT_MEAN", "WITNESS_MINUS_NEVER_EVENT_MEAN"):
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for stratum in STRATA:
                    add("NEVER_HEADROOM", quantity, regime, schedule, stratum)

    for contrast in ALL_CONTRASTS:
        for endpoint in ENDPOINTS:
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for stratum in STRATA:
                        add("ENDPOINT_EFFECT", contrast, endpoint, regime, schedule, stratum)
    for contrast in ALL_CONTRASTS:
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for stratum in STRATA:
                    add("ENERGY_RATIO", contrast, regime, schedule, stratum)
    for population in (*ARMS, "REAL", "SHAM"):
        for event in HARD_EVENTS:
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for stratum in STRATA:
                        add("HARD_EVENT_RATE", population, event, regime, schedule, stratum)

    for contrast in FULL_CONTRASTS:
        for endpoint in ENDPOINTS:
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for stratum in STRATA:
                        for phase in PHASES_BY_SCHEDULE[schedule]:
                            add("PHASE_ENDPOINT_DIFFERENCE", contrast, endpoint, regime, schedule, stratum, phase)
    for contrast in FULL_CONTRASTS:
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for stratum in STRATA:
                    for phase in PHASES_BY_SCHEDULE[schedule]:
                        add("PHASE_ENERGY_DIFFERENCE", contrast, regime, schedule, stratum, phase)

    expected = complete_hypothesis_inventory()["total"]
    if len(rows) != expected or len(set(rows)) != expected:
        raise ProductionAnalysisError(
            f"frozen estimand identity map differs: rows={len(rows)} unique={len(set(rows))} expected={expected}"
        )
    return tuple(rows)


def estimand_manifest_identity() -> dict[str, object]:
    rows = complete_estimand_manifest()
    encoded = ("\n".join(rows) + "\n").encode("ascii")
    return {
        "schema": "DISH_RBHR_R05_ESTIMAND_IDENTITY_MANIFEST_V1",
        "count": len(rows),
        "unique": len(set(rows)),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "value_bearing": False,
        "first": rows[0],
        "last": rows[-1],
    }


def complete_estimand_source_manifest() -> dict[str, object]:
    """Bind every max-t identity to its production reducer-row family.

    This is still value-blind: it records the required row schema and complete
    identity coverage, never a block value, interval, or label.
    """

    family_sources = {
        "COMPETENCE_NO_DEGRADATION": "full_episode_mask_off_rows",
        "COMPETENCE_PRE_ONSET": "pre_onset_mask_on_rows",
        "OPPORTUNITY": "opportunity_witness_rows",
        "ADAPTIVE_SUPPORT": "trigger_support_rows",
        "NEVER_HEADROOM": "never_and_witness_event_rows",
        "ENDPOINT_EFFECT": "full_or_fork_endpoint_rows",
        "ENERGY_RATIO": "full_or_fork_energy_rows",
        "HARD_EVENT_RATE": "full_or_fork_hard_event_rows",
        "PHASE_ENDPOINT_DIFFERENCE": "unconditioned_phase_endpoint_rows",
        "PHASE_ENERGY_DIFFERENCE": "unconditioned_phase_energy_rows",
    }
    rows = complete_estimand_manifest()
    assignments = tuple((row, family_sources[row.split("/", 1)[0]]) for row in rows)
    if len(assignments) != 6_990 or len({identity for identity, _ in assignments}) != 6_990:
        raise ProductionAnalysisError("estimand source assignment is incomplete")
    encoded = ("\n".join(f"{identity}\t{source}" for identity, source in assignments) + "\n").encode("ascii")
    return {
        "schema": "DISH_RBHR_R05_ESTIMAND_SOURCE_MANIFEST_V1",
        "count": len(assignments), "unique": len({identity for identity, _ in assignments}),
        "source_families": dict(family_sources), "sha256": hashlib.sha256(encoded).hexdigest(),
        "value_bearing": False, "block_rows_required_per_estimand": 24,
        "joint_resamples": 99_999,
    }


def run_native_connected_analyzer_seam(native_rows: Mapping[str, np.ndarray]) -> dict[str, object]:
    """Bind real native TEST reducer rows to the complete analyzer contract."""

    required = {
        "service", "terminal", "protocol_bytes", "total_energy", "invalid_commit",
        "cas_applied", "application_reason", "protocol_wire_hash",
    }
    if not required.issubset(native_rows):
        raise ProductionAnalysisError(f"native analyzer rows are incomplete: {sorted(required-set(native_rows))}")
    service = np.asarray(native_rows["service"])
    if service.ndim != 2 or service.shape[0] != 1_200 or service.shape[1] < 16:
        raise ProductionAnalysisError("native analyzer rows must contain at least sixteen complete 1200-tick tapes")
    terminal = np.asarray(native_rows["terminal"])
    onset_ticks = [(420, 540, 660)[lane % 3] for lane in range(16)]
    energy = np.asarray(native_rows["total_energy"], dtype=np.float64)[-1, :16]
    hard = np.stack(
        [
            (np.asarray(native_rows["invalid_commit"])[-1, :16] > 0).astype(np.int64),
            (np.asarray(native_rows["cas_applied"])[-1, :16] > 0).astype(np.int64),
            (np.asarray(native_rows["application_reason"])[-1, :16] > 0).astype(np.int64),
            terminal[-1, :16],
            np.zeros(16, dtype=np.int64), np.zeros(16, dtype=np.int64), np.zeros(16, dtype=np.int64),
        ],
        axis=1,
    )
    reduced = reduce_full_cell_rows(service[:, :16].T, onset_ticks, energy, hard)
    digest = hashlib.sha256()
    digest.update(np.ascontiguousarray(service[:, :16]).tobytes())
    for name in sorted(required - {"service"}):
        digest.update(name.encode("ascii") + b"\0")
        digest.update(np.ascontiguousarray(native_rows[name]).tobytes())
    digest.update(json.dumps(reduced, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii"))
    analyzer = run_result_blind_analyzer_seam()
    sources = complete_estimand_source_manifest()
    return {
        "schema": "DISH_RBHR_R05_NATIVE_CONNECTED_ANALYZER_SEAM_V1",
        "test_only": True, "question_relevant_output": False,
        "native_tapes": 16, "ticks_per_tape": 1_200,
        "native_reducer_input_sha256": digest.hexdigest(),
        "wire_hash_nonzero": bool(np.any(np.asarray(native_rows["protocol_wire_hash"]))),
        "estimand_source_count": sources["count"],
        "block_rows_required_per_estimand": sources["block_rows_required_per_estimand"],
        "joint_resamples": analyzer["resamples"], "branch_count": analyzer["branch_count"],
        "all_intervals_finite": analyzer["all_intervals_finite"],
    }


__all__ = [
    "ProductionAnalysisError", "aggregate_atomic_labels", "complete_estimand_manifest", "complete_estimand_source_manifest", "complete_hypothesis_inventory", "endpoint_vector", "estimand_manifest_identity", "fractional_cvar_10",
    "reduce_fork_rows", "reduce_full_cell_rows", "run_native_connected_analyzer_seam",
    "recovery_delay", "run_result_blind_analyzer_seam", "service_deficit",
    "service_fraction",
]
