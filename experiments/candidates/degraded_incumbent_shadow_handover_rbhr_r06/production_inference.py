"""Result-blind speed-stratum reducers and common-anchor r06 inference law."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .production_backend import rng_words_native
from .production_population import address

from .production_contract import (
    ARMS, BOOTSTRAP_RESAMPLES, BRANCHES, CLAIM_SCHEDULES, ENDPOINTS,
    REGIMES, SPEED_STRATA,
)


FULL_CONTRASTS = ("S-N", "F-S", "F-N", "I-N", "I-S", "H-N", "H-S")
ALL_CONTRASTS = (*FULL_CONTRASTS, "REAL-SHAM")
HARD_EVENTS = (
    "invalid_commit", "token_gap", "dual_owner", "dual_payload", "buffer_clear",
    "command_slew_breach", "separation_breach",
)
PHASES_BY_SCHEDULE = {"K8": tuple(range(8)), "K4_TO_K12": tuple(range(4)), "K12_TO_K4": tuple(range(12))}
POSITIVE_LABELS = {
    "SIMPLE_RULE_SUFFICIENT[IMMEDIATE]", "SIMPLE_RULE_SUFFICIENT[HYSTERESIS]",
    "FLEXIBLE_CONTAINER_SUPERIOR", "STRUCTURED_ATOMIC_VALUE",
}


class InferenceError(RuntimeError):
    pass


def classify_atomic(vector: Mapping[str, object]) -> tuple[int, str]:
    get = lambda name, default=False: bool(vector.get(name, default))
    if not get("protocol_ok"): return 1, BRANCHES[0]
    if not get("comp"): return 2, BRANCHES[1]
    if not get("witness"): return 3, BRANCHES[2]
    if not get("headroom", True) or not get("precision", True): return 4, BRANCHES[3]
    if not get("support"):
        if get("rule_fallback_i"): return 5, BRANCHES[8]
        if get("rule_fallback_h"): return 5, BRANCHES[9]
        return 5, BRANCHES[4]
    if get("harm"): return 6, BRANCHES[5]
    if get("package_effect"): return 7, BRANCHES[6]
    if get("fork_excluded") and not get("nm_all"): return 8, BRANCHES[7]
    if get("rulequal_i"): return 9, BRANCHES[8]
    if get("rulequal_h"): return 10, BRANCHES[9]
    if get("flexqual"): return 11, BRANCHES[10]
    if get("flex_rel"): return 12, BRANCHES[11]
    if get("core") and not get("flex_rel"): return 13, BRANCHES[12]
    if get("nm_all"): return 14, BRANCHES[13]
    return 15, BRANCHES[14]


def value_at_anchor(
    intervals: Mapping[str, Mapping[str, tuple[float, float]]],
    *, anchor: str, material_margin: Mapping[str, float], noninferiority_margin: Mapping[str, float],
) -> bool:
    if set(intervals) != set(SPEED_STRATA) or anchor not in SPEED_STRATA:
        raise InferenceError("speed interval inventory differs")
    for speed in SPEED_STRATA:
        if set(intervals[speed]) != set(ENDPOINTS):
            raise InferenceError("endpoint interval inventory differs")
        for endpoint, (lower, upper) in intervals[speed].items():
            if not math.isfinite(lower) or not math.isfinite(upper) or lower > upper:
                raise InferenceError("interval differs")
            if lower < -float(noninferiority_margin[endpoint]):
                return False
    return any(
        intervals[anchor][endpoint][0] >= float(material_margin[endpoint])
        for endpoint in ENDPOINTS
    )


def common_anchor_classify(
    common_vector: Mapping[str, object],
    anchor_vectors: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    if set(anchor_vectors) != set(SPEED_STRATA):
        raise InferenceError("common-anchor vector inventory differs")
    classified = {
        speed: classify_atomic({**common_vector, **anchor_vectors[speed]})
        for speed in SPEED_STRATA
    }
    selected_branch = min(branch for branch, _ in classified.values())
    selected_labels = {
        label for branch, label in classified.values() if branch == selected_branch
    }
    if len(selected_labels) != 1:
        raise InferenceError("first-match branch maps to multiple labels")
    selected_label = next(iter(selected_labels))
    anchors = tuple(
        speed for speed in SPEED_STRATA if classified[speed] == (selected_branch, selected_label)
    ) if selected_label in POSITIVE_LABELS else ()
    return {
        "branch": selected_branch,
        "label": selected_label,
        "qualifying_anchor_speeds": list(anchors),
        "per_anchor": {speed: {"branch": branch, "label": label} for speed, (branch, label) in classified.items()},
    }


def aggregate_schedule_regime_intersections(
    atomic: Mapping[tuple[str, str], Mapping[str, object]],
) -> dict[str, object]:
    expected = {(regime, schedule) for regime in REGIMES for schedule in CLAIM_SCHEDULES}
    if set(atomic) != expected:
        raise InferenceError("atomic schedule/regime inventory differs")
    per_regime: dict[str, dict[str, object]] = {}
    for regime in REGIMES:
        rows = [atomic[(regime, schedule)] for schedule in CLAIM_SCHEDULES]
        labels = tuple(str(row["label"]) for row in rows)
        intersection = set(SPEED_STRATA)
        for row in rows:
            intersection &= set(row.get("qualifying_anchor_speeds", ()))
        if len(set(labels)) == 1 and labels[0] in POSITIVE_LABELS and intersection:
            label = labels[0]
        elif labels[0] in POSITIVE_LABELS and (len(set(labels)) != 1 or not intersection):
            label = "FIXED_ONLY_NO_SWITCH_K_VALUE[" + "|".join(labels) + "]"
        else:
            label = "NO_COMMON_THREE_SCHEDULE_RETAINED_VALUE[" + "|".join(labels) + "]"
        per_regime[regime] = {"label": label, "common_anchor_speeds": sorted(intersection)}
    cross_intersection = set(SPEED_STRATA)
    for value in per_regime.values():
        cross_intersection &= set(value["common_anchor_speeds"])
    regime_labels = {value["label"] for value in per_regime.values()}
    if len(regime_labels) == 1 and cross_intersection:
        cross = next(iter(regime_labels))
    else:
        cross = "PACKAGE_SPECIFIC_OR_NO_COMMON_CROSS_REGIME_VALUE"
    return {
        "atomic": {f"{regime}/{schedule}": dict(atomic[(regime, schedule)]) for regime in REGIMES for schedule in CLAIM_SCHEDULES},
        "regime": per_regime,
        "cross_regime": {"label": cross, "common_anchor_speeds": sorted(cross_intersection)},
    }


def complete_branch_payload(
    atomic_vectors: Mapping[tuple[str, str], Mapping[str, object]],
) -> dict[str, object]:
    """Build the frozen complete first-match payload without interpreting it.

    Every regime/schedule cell carries all three anchor vectors and the common
    protocol/support predicates.  Missing booleans fail closed so a producer
    cannot silently rely on ``classify_atomic`` defaults.
    """

    expected = {(regime, schedule) for regime in REGIMES for schedule in CLAIM_SCHEDULES}
    if set(atomic_vectors) != expected:
        raise InferenceError("complete branch atomic inventory differs")
    common_names = (
        "protocol_ok", "comp", "witness", "headroom", "precision", "support",
        "rule_fallback_i", "rule_fallback_h", "harm", "package_effect",
        "fork_excluded", "nm_all", "rulequal_i", "rulequal_h", "flexqual",
        "flex_rel", "core",
    )
    atomic: dict[tuple[str, str], Mapping[str, object]] = {}
    for coordinate in sorted(expected):
        value = atomic_vectors[coordinate]
        if any(name not in value or not isinstance(value[name], bool) for name in common_names):
            raise InferenceError("complete branch common predicate inventory differs")
        anchors = value.get("anchors")
        if not isinstance(anchors, Mapping) or set(anchors) != set(SPEED_STRATA):
            raise InferenceError("complete branch anchor inventory differs")
        per_anchor = {}
        for speed in SPEED_STRATA:
            row = anchors[speed]
            if not isinstance(row, Mapping) or any(name not in row or not isinstance(row[name], bool) for name in common_names):
                raise InferenceError("complete branch anchor predicate inventory differs")
            per_anchor[speed] = dict(row)
        atomic[coordinate] = common_anchor_classify(
            {name: value[name] for name in common_names}, per_anchor,
        )
    aggregate = aggregate_schedule_regime_intersections(atomic)
    return {
        "schema": "DISH_RBHR_R06_COMPLETE_15_BRANCH_PAYLOAD_V1",
        "branch_catalog": list(BRANCHES),
        "branch_count": len(BRANCHES),
        "first_match": True,
        "payload": aggregate,
        "complete": True,
    }


def fractional_cvar_10(values: Sequence[float]) -> float:
    rows = np.sort(np.asarray(values, dtype=np.float64))
    if rows.shape != (16,) or not np.isfinite(rows).all():
        raise InferenceError("speed-cell CVaR requires exactly sixteen finite tapes")
    mass = 1.6
    return float((rows[0] + 0.6 * rows[1]) / mass)


def reduce_speed_cell(service: np.ndarray, onset_ticks: Sequence[int]) -> dict[str, float]:
    rows = np.asarray(service, dtype=np.int8)
    onset = np.asarray(onset_ticks, dtype=np.int64)
    if rows.shape != (16, 1_200) or onset.shape != (16,) or not np.isin(rows, (0, 1)).all():
        raise InferenceError("speed-cell reducer shape differs")
    windows = np.stack([rows[index, tick:tick + 200] for index, tick in enumerate(onset)])
    fractions = windows.mean(axis=1)
    deficits = 0.1 * (200 - windows.sum(axis=1))
    delays = []
    for row in windows:
        first = np.flatnonzero(row == 0)
        delay = 0.0
        if first.size:
            delay = 20.0
            for index in range(int(first[0]), 191):
                if np.all(row[index:index + 10] == 1):
                    delay = 0.1 * (index - int(first[0])); break
        delays.append(delay)
    return {
        "MEAN": float(fractions.mean()),
        "TAIL": fractional_cvar_10(fractions),
        "DEFICIT": float(deficits.mean()),
        "DELAY": float(np.mean(delays)),
    }


def _test_block_indices(start: int, count: int) -> np.ndarray:
    key = b"TEST/DISH/RBHR/R06/MAX-T/V1"
    values = np.empty((count, 24), dtype=np.int16)
    for local in range(count):
        for block in range(24):
            address = f"DISH/RBHR/R06/INFERENCE/{start + local + 1}/{block}".encode("ascii")
            word = int.from_bytes(hashlib.sha256(key + b"\0" + address).digest()[:8], "big")
            values[local, block] = int(24 * (((word >> 11) + 0.5) / 2**53))
    return values


def _production_block_indices(master: bytes, start: int, count: int) -> np.ndarray:
    raw_master = bytes(master)
    if len(raw_master) != 32:
        raise InferenceError("production inference master must be exactly 256 bits")
    addresses = tuple(
        address(
            purpose="INFERENCE", block=None, split="BOOTSTRAP", regime="NONE",
            schedule="NONE", evaluation_slot=None, inference_resample=start + local + 1,
            tick=block, field="BOOTSTRAP_BLOCK", draw_index=0,
        )
        for local in range(count) for block in range(24)
    )
    words = np.asarray(rng_words_native(raw_master, addresses), dtype=np.uint64).reshape(count, 24)
    return np.floor(24.0 * (((words >> np.uint64(11)).astype(np.float64) + 0.5) / 2**53)).astype(np.int16)


def joint_max_t(
    block_values: np.ndarray, *, resamples: int = BOOTSTRAP_RESAMPLES,
    chunk_size: int = 512, master: bytes | None = None,
) -> dict[str, object]:
    values = np.asarray(block_values, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != 24 or values.shape[1] == 0 or not np.isfinite(values).all():
        raise InferenceError("max-t input must be finite [24,H]")
    theta = values.mean(axis=0); se = values.std(axis=0, ddof=1) / np.sqrt(24.0)
    identical = np.all(values == values[:1], axis=0)
    maxima = np.empty(resamples, dtype=np.float64)
    cursor = 0
    while cursor < resamples:
        count = min(chunk_size, resamples - cursor)
        indices = _test_block_indices(cursor, count) if master is None else _production_block_indices(master, cursor, count)
        sampled = values[indices]
        theta_star = sampled.mean(axis=1); se_star = sampled.std(axis=1, ddof=1) / np.sqrt(24.0)
        numerator = np.abs(theta_star - theta)
        statistic = np.zeros_like(numerator)
        finite = (~identical) & (se_star > 0.0)
        statistic[finite] = numerator[finite] / se_star[finite]
        statistic[(~identical) & (se_star == 0.0) & (numerator > 0.0)] = np.inf
        maxima[cursor:cursor + count] = statistic.max(axis=1); cursor += count
    critical = float(np.partition(maxima, 94_999)[94_999])
    lower = theta - critical * se; upper = theta + critical * se
    lower[identical] = theta[identical]; upper[identical] = theta[identical]
    return {"resamples": resamples, "critical": critical, "estimands": values.shape[1], "lower": lower.tolist(), "upper": upper.tolist(), "all_finite": bool(np.isfinite(lower).all() and np.isfinite(upper).all()), "test_only": master is None}


def complete_estimand_manifest() -> tuple[str, ...]:
    rows: list[str] = []
    def add(family: str, *coords: object) -> None: rows.append("/".join((family, *(str(value) for value in coords))))
    for arm in ARMS:
        for regime in REGIMES:
            for schedule in ("K4", "K12"):
                for speed in SPEED_STRATA: add("COMPETENCE_NO_DEGRADATION", arm, regime, schedule, speed)
    for arm in ARMS:
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEED_STRATA: add("COMPETENCE_PRE_ONSET", arm, regime, schedule, speed)
    for quantity in ("Q", "DROP", "MAINTAIN", "WITNESS_GAIN", "WITNESS_CONTINUITY"):
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEED_STRATA: add("OPPORTUNITY", quantity, regime, schedule, speed)
    for arm in ("STRUCTURED", "FLEX"):
        for quantity in ("TRIGGER_RATE", "BEHAVIOR_CHANGING_SUPPORT"):
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for speed in SPEED_STRATA: add("ADAPTIVE_SUPPORT", arm, quantity, regime, schedule, speed)
    for quantity in ("NEVER_EVENT_MEAN", "WITNESS_MINUS_NEVER_EVENT_MEAN"):
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEED_STRATA: add("NEVER_HEADROOM", quantity, regime, schedule, speed)
    for contrast in ALL_CONTRASTS:
        for endpoint in ENDPOINTS:
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for speed in SPEED_STRATA: add("ENDPOINT_EFFECT", contrast, endpoint, regime, schedule, speed)
    for contrast in ALL_CONTRASTS:
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEED_STRATA: add("ENERGY_RATIO", contrast, regime, schedule, speed)
    for population in (*ARMS, "REAL", "SHAM"):
        for event in HARD_EVENTS:
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for speed in SPEED_STRATA: add("HARD_EVENT_RATE", population, event, regime, schedule, speed)
    for contrast in FULL_CONTRASTS:
        for endpoint in ENDPOINTS:
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for speed in SPEED_STRATA:
                        for phase in PHASES_BY_SCHEDULE[schedule]: add("PHASE_ENDPOINT_DIFFERENCE", contrast, endpoint, regime, schedule, speed, phase)
    for contrast in FULL_CONTRASTS:
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEED_STRATA:
                    for phase in PHASES_BY_SCHEDULE[schedule]: add("PHASE_ENERGY_DIFFERENCE", contrast, regime, schedule, speed, phase)
    if len(rows) != 6_990 or len(set(rows)) != 6_990:
        raise InferenceError("r06 estimand inventory differs")
    return tuple(rows)


def inference_manifest() -> dict[str, object]:
    rows = complete_estimand_manifest()
    encoded = ("\n".join(rows) + "\n").encode("ascii")
    return {
        "schema": "DISH_RBHR_R06_INFERENCE_MANIFEST_V1",
        "estimand_count": len(rows),
        "estimand_sha256": hashlib.sha256(encoded).hexdigest(),
        "speed_strata": list(SPEED_STRATA),
        "common_anchor_required_within_class": True,
        "schedule_anchor_intersection_required": True,
        "regime_anchor_intersection_required": True,
        "first_match_branch_count": len(BRANCHES),
        "joint_resamples": BOOTSTRAP_RESAMPLES,
        "value_bearing": False,
    }


def run_production_inference(block_values: np.ndarray, *, master: bytes) -> dict[str, object]:
    values = np.asarray(block_values, dtype=np.float64)
    if values.shape != (24, 6_990) or not np.isfinite(values).all():
        raise InferenceError("complete production estimand matrix differs")
    result = joint_max_t(values, master=master)
    if result["estimands"] != 6_990 or result["resamples"] != 99_999 or not result["all_finite"]:
        raise InferenceError("complete production inference differs")
    if result["test_only"]:
        raise InferenceError("production inference used TEST bootstrap")
    return {"schema": "DISH_RBHR_R06_COMPLETE_INFERENCE_V1", **result, "complete": True}


def accept_complete_result(path: Path, payload: Mapping[str, object]) -> dict[str, object]:
    if payload.get("schema") != "DISH_RBHR_R06_COMPLETE_RESULT_V1" or payload.get("complete") is not True:
        raise InferenceError("result firewall rejects incomplete payload")
    required = {"identity_sha256", "population_count", "training_jobs", "evaluation_episodes", "estimands", "resamples", "branch_result"}
    if not required.issubset(payload) or (payload["population_count"], payload["training_jobs"], payload["evaluation_episodes"], payload["estimands"], payload["resamples"]) != (11_520, 120, 115_200, 6_990, 99_999):
        raise InferenceError("result firewall inventory differs")
    encoded = (json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise InferenceError("complete result is create-only") from error
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    return {"path": str(path), "sha256": hashlib.sha256(encoded).hexdigest(), "complete": True}


__all__ = [
    "InferenceError", "aggregate_schedule_regime_intersections", "classify_atomic",
    "common_anchor_classify", "complete_branch_payload", "complete_estimand_manifest", "fractional_cvar_10",
    "accept_complete_result", "inference_manifest", "joint_max_t", "reduce_speed_cell", "run_production_inference", "value_at_anchor",
]
