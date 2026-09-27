"""Paired, adverse-inclusive world-seed readout for B03."""

from __future__ import annotations

import math

from experiments.candidates.energy_relay_availability.readout import (
    _distribution,
    _interval,
    _number,
    paired,
)


ARMS = ("distance_hysteresis", "energy_fraction")
EXCLUDED = {"seed", "worker_peak_rss_kib", "worker_cpu_seconds",
            "worker_wall_seconds", "raw_bytes"}
PRIMARY_FIELDS = (
    "qos_per_step",
    "raw_native_J",
    "native_J_per_step",
    "return_constraint_cost_raw_per_step",
    "return_constraint_cost_per_step",
    "episode_minimum_battery_ratio",
    "negative_return_margin_uav_step_fraction",
    "below_dynamic_return_threshold_uav_step_fraction",
    "below_fixed_reserve_uav_step_fraction",
    "service_cutoff_uav_step_fraction",
    "cutoff_event_count_sum",
    "depletion_event_count_sum",
    "actual_length",
)
PAIR_HASHES = ("initial_state_sha256", "user_xy_trace_sha256",
               "failure_trace_sha256", "rng_state_stream_sha256")


def _complete_by_seed(groups: dict[str, list[dict]], expected_n: int) -> bool:
    return all(len(groups[arm]) == expected_n for arm in ARMS)


def _arm_distribution(values: list[float]) -> dict:
    result = _distribution(values)
    n = result["n"]
    if n > 1:
        df = n - 1
        se = result["sd"] / math.sqrt(n)
        interval = _interval(result["mean"], se, df)
    else:
        df, se, interval = None, None, None
    return result | {"se": se, "df": df, "t95": interval}


def summarize(rows: list[dict], expected_keys: list[str], expected_seeds: list[int]) -> dict:
    expected_n = len(expected_seeds)
    by_key = {row["job_key"]: row for row in rows}
    missing = [key for key in expected_keys if key not in by_key]
    failed = [key for key in expected_keys if key in by_key and by_key[key]["status"] == "failed"]
    unreconciled = [key for key in expected_keys
                    if key in by_key and by_key[key]["status"] == "unreconciled"]
    cancelled = [key for key in expected_keys
                 if key in by_key and by_key[key]["status"] == "cancelled"]
    groups = {arm: [] for arm in ARMS}
    for key in expected_keys:
        row = by_key.get(key)
        if row and row["status"] == "completed":
            groups[row["arm"]].append(row)
    numeric_fields = sorted({field for group in groups.values() for row in group
                             for field, value in row.items()
                             if _number(value) and field not in EXCLUDED})
    panels = {}
    for arm, group in groups.items():
        metrics = {}
        for field in numeric_fields:
            values = [float(row[field]) for row in group if _number(row.get(field))]
            metrics[field] = _arm_distribution(values) | {"missing": len(group) - len(values)}
        panels[arm] = {
            "planned_worlds": expected_n,
            "completed_worlds": len(group),
            "metrics": metrics,
            "zero_service_worlds": sum(bool(row.get("zero_service", False)) for row in group),
            "terminal_types": {kind: sum(row.get("terminal_type") == kind for row in group)
                               for kind in ("terminated", "truncated", "horizon")},
            "failed_worlds": sum(row["status"] == "failed" for row in rows
                                  if row.get("arm") == arm),
        }
    complete = (not missing and not failed and not unreconciled and not cancelled
                and _complete_by_seed(groups, expected_n))
    pair_rows = []
    contrasts = {}
    hash_agreement = {key: {"equal_pairs": 0, "different_pairs": 0,
                            "unobserved_pairs": 0} for key in PAIR_HASHES}
    initial_pairs_valid = complete
    strict_stream_pairs = complete
    if complete:
        maps = {arm: {row["seed"]: row for row in groups[arm]} for arm in ARMS}
        if sorted(maps[ARMS[0]]) != sorted(expected_seeds) or \
                sorted(maps[ARMS[1]]) != sorted(expected_seeds):
            raise ValueError("B03 rows do not match the immutable paired seed list")
        for seed in expected_seeds:
            baseline = maps["distance_hysteresis"][seed]
            candidate = maps["energy_fraction"][seed]
            equal = {}
            for field in PAIR_HASHES:
                a, b = baseline.get(field), candidate.get(field)
                same = bool(a and b and a == b)
                equal[field] = same if a and b else None
                if equal[field] is None:
                    hash_agreement[field]["unobserved_pairs"] += 1
                elif same:
                    hash_agreement[field]["equal_pairs"] += 1
                else:
                    hash_agreement[field]["different_pairs"] += 1
            initial_pairs_valid &= equal["initial_state_sha256"] is True
            strict_stream_pairs &= all(equal[field] is True for field in
                                       ("user_xy_trace_sha256", "failure_trace_sha256",
                                        "rng_state_stream_sha256"))
            deltas = {}
            for field in numeric_fields:
                a, b = candidate.get(field), baseline.get(field)
                deltas[field] = (float(a) - float(b)
                                 if _number(a) and _number(b) else None)
            pair_rows.append({
                "seed": int(seed),
                "initial_state_equal": equal["initial_state_sha256"],
                "user_xy_trace_equal": equal["user_xy_trace_sha256"],
                "failure_trace_equal": equal["failure_trace_sha256"],
                "rng_state_stream_equal": equal["rng_state_stream_sha256"],
                "deltas_energy_minus_distance": deltas,
                "distance_zero_service": bool(baseline.get("zero_service", False)),
                "energy_zero_service": bool(candidate.get("zero_service", False)),
            })
        for field in numeric_fields:
            left = [maps["energy_fraction"][seed].get(field) for seed in expected_seeds]
            right = [maps["distance_hysteresis"][seed].get(field) for seed in expected_seeds]
            if not initial_pairs_valid:
                contrasts[field] = {"status": "not_comparable",
                                    "reason": "at least one initialized-world pair differs"}
            elif all(_number(a) and _number(b) for a, b in zip(left, right)):
                contrasts[field] = {"status": "paired", **paired(
                    [float(value) for value in left], [float(value) for value in right])}
            else:
                contrasts[field] = {"status": "not_comparable",
                                    "missing_pairs": sum(not (_number(a) and _number(b))
                                                         for a, b in zip(left, right))}
    return {
        "status": "complete" if complete else "incomplete",
        "planned_jobs": len(expected_keys),
        "completed_jobs": sum(len(group) for group in groups.values()),
        "missing_jobs": missing,
        "failed_jobs": failed,
        "unreconciled_jobs": unreconciled,
        "cancelled_jobs": cancelled,
        "panels": panels,
        "primary_fields": list(PRIMARY_FIELDS),
        "contrasts_energy_minus_distance": contrasts,
        "world_pairs": pair_rows,
        "pairing_diagnostics": {
            "unit": "same initialized world seed, verified by state hash",
            "initial_state_pairs_valid": bool(initial_pairs_valid),
            "strict_exogenous_trace_pairing": bool(strict_stream_pairs),
            "hash_agreement": hash_agreement,
            "interpretation": (
                "Strict common stochastic paths are claimed only for equal per-step user, "
                "failure and environment RNG digests. Paired-world inference otherwise "
                "conditions on verified equal reset states; UAV paths are allowed to differ."),
        },
        "inference_unit": "paired initialized world seed; approximate t31 intervals",
        "prediction_reading": "assignment-energy estimates are diagnostics, not native outcomes",
    }
