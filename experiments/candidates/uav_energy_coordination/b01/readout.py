"""Native, adverse-inclusive B01 readings; partial panels are descriptive only."""

from __future__ import annotations

import math
from numbers import Real

import numpy as np
from scipy.stats import t as student_t

from experiments.candidates.energy_relay_benchmark.b01.evaluation import TRACE_FIELDS

ARMS = ("H", "I", "C")
CONTRASTS = (("C", "I"), ("C", "H"), ("I", "H"))
PAIR_HASHES = ("initial_state_sha256", "user_xy_trace_sha256", "rng_state_stream_sha256")
RISK_FIELDS = ("return_constraint_cost_per_step", "episode_minimum_battery_ratio",
               "below_fixed_reserve_uav_step_fraction", "service_cutoff_uav_step_fraction",
               "cutoff_event_count_sum", "depletion_event_count_sum",
               "guard_blocked_actions")
LOWER_IS_BETTER = ("return_constraint_cost", "cutoff_event", "depletion_event",
                   "guard_blocked", "max_zero_qos_gap", "max_below_half_qos_gap",
                   "zero_qos_spells", "below_half_qos_spells",
                   "below_fixed_reserve_uav_step_fraction", "service_cutoff_uav_step_fraction")
HIGHER_IS_BETTER = ("raw_native_J", "native_J_per_step", "qos_per_step", "cumulative_qos",
                    "delivered_megabits", "episode_minimum_battery_ratio",
                    "min_decoded_battery", "qos_satisfaction_ratio",
                    "delivered_end_to_end_throughput_mbps", "scenario7_reward",
                    "battery_min_ratio")
ENDPOINTS = ("raw_native_J", "native_J_per_step", "qos_per_step", "cumulative_qos",
             "delivered_megabits", "actual_length", "min_decoded_battery",
             "max_zero_qos_gap", "max_below_half_qos_gap", "zero_qos_spells_ge60",
             "below_half_qos_spells_ge60", "energy_input_wh", "energy_consumed_wh",
             "feedback_mode_uav_steps", "feedback_entry_count", "feedback_exit_count",
             "guard_checked_actions", "guard_blocked_actions", *RISK_FIELDS,
             *(f"{field}_{suffix}" for field in TRACE_FIELDS for suffix in ("sum", "per_step")))
ENDPOINTS = tuple(dict.fromkeys(ENDPOINTS))


def _spells(mask):
    padded = np.concatenate(([False], np.asarray(mask, dtype=bool), [False])).astype(np.int8)
    changes = np.diff(padded)
    return np.flatnonzero(changes == -1) - np.flatnonzero(changes == 1)


def enrich_world(row: dict, steps: dict, observed: dict, decisions: dict,
                 *, reserve_ratio: float, cutoff_ratio: float, time_step: float) -> dict:
    """Add readings from the native post-step trace without replacing its reward row."""
    length = int(row["actual_length"])
    metrics = np.asarray(steps["metrics"], dtype=np.float64)
    battery = np.asarray(steps["battery"], dtype=np.float64)
    qos = metrics[:, TRACE_FIELDS.index("qos_satisfaction_ratio")]
    throughput = metrics[:, TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")]
    if length < 1 or metrics.shape != (length, len(TRACE_FIELDS)) or battery.shape != (length, 8):
        raise ValueError("incomplete native metric/battery trace")
    row.update(
        below_fixed_reserve_uav_step_fraction=float(np.mean(battery <= reserve_ratio)),
        service_cutoff_uav_step_fraction=float(np.mean(battery <= cutoff_ratio)),
        fixed_reserve_ratio=float(reserve_ratio), service_cutoff_ratio=float(cutoff_ratio),
        energy_input_wh=float(np.sum(observed["actual_energy_input_wh"])),
        energy_consumed_wh=float(np.sum(observed["actual_energy_consumed_wh"])),
    )
    if not np.isclose(row["energy_input_wh"], row["step_charger_input_wh_sum"], rtol=1e-5, atol=1e-5):
        raise ValueError("per-UAV input differs from native team charger input")
    for name, mask in (("zero_qos", qos == 0.0), ("below_half_qos", qos < 0.5)):
        lengths = _spells(mask)
        row[f"max_{name}_gap"] = int(lengths.max()) if lengths.size else 0
        row[f"{name}_spells_ge60"] = int(np.count_nonzero(lengths >= 60))
    for start in (0, 1000, 2000):
        end = start + 1000
        view = slice(start, min(end, length))
        count = max(0, min(end, length) - start)
        row[f"bin_{start}_{end}"] = {
            "steps": count,
            "native_J": float(np.sum(steps["reward"][view])),
            "qos_mean": float(np.mean(qos[view])) if count else None,
            "throughput_megabits": float(np.sum(throughput[view]) * time_step),
            "return_constraint_cost_mean": float(np.mean(metrics[view, TRACE_FIELDS.index(
                "return_constraint_cost")])) if count else None,
        }
    if "planner_step" in decisions:
        starts = np.asarray(decisions["planner_step"], dtype=np.int64)
        samples = np.asarray(decisions["planner_sample_times"], dtype=np.int64)
        xyz = np.asarray(decisions["planner_selected_positions"], dtype=np.float64)
        bat = np.asarray(decisions["planner_selected_batteries"], dtype=np.float64)
        predicted_qos = np.asarray(decisions["planner_selected_qos"], dtype=np.float64)
        if (samples.shape != (len(starts), 3) or xyz.shape != (len(starts), 3, 8, 3)
                or bat.shape != (len(starts), 3, 8) or predicted_qos.shape != (len(starts), 3)):
            raise ValueError("planner forecast trace has the wrong shape")
        differences = {key: [] for key in ("qos", "position_m", "battery_ratio")}
        for index, start in enumerate(starts):
            for sample in range(3):
                horizon = int(samples[index, sample])
                actual = int(start) + horizon - 1  # Native row t records the result of action t.
                if horizon <= 0 or actual >= length:
                    continue
                differences["qos"].append(float(predicted_qos[index, sample] - qos[actual]))
                differences["position_m"].extend(np.linalg.norm(
                    xyz[index, sample] - observed["actual_xyz_post_m"][actual], axis=1).tolist())
                differences["battery_ratio"].extend(
                    (bat[index, sample] - battery[actual]).tolist())
        row["forecast_closed_loop_discrepancy"] = {
            "meaning": "held itinerary forecast minus realized replanning policy; not forecast accuracy or causal mechanism",
            **{key: {"n": len(values), "mean_signed": float(np.mean(values)) if values else None,
                     "mean_absolute": float(np.mean(np.abs(values))) if values else None}
               for key, values in differences.items()},
        }
    return row


def _numeric(value):
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def _distribution(values):
    values = np.asarray(values, dtype=np.float64)
    return {"n": int(values.size), "mean": float(values.mean()) if values.size else None,
            "min": float(values.min()) if values.size else None,
            "max": float(values.max()) if values.size else None}


def _contrast(deltas, *, interval):
    result = _distribution(deltas)
    result["negative_worlds"] = int(sum(delta < 0 for delta in deltas))
    result["positive_worlds"] = int(sum(delta > 0 for delta in deltas))
    result["zero_worlds"] = int(sum(delta == 0 for delta in deltas))
    result["t95_descriptive"] = None
    if interval and len(deltas) == 8:
        sd = float(np.std(deltas, ddof=1))
        half = float(student_t.ppf(0.975, 7) * sd / math.sqrt(8))
        result["t95_descriptive"] = [result["mean"] - half, result["mean"] + half]
    return result


def summarize(rows: list[dict], seeds: tuple[int, ...], expected_keys: list[str]) -> dict:
    by_key = {row["job_key"]: row for row in rows}
    if len(by_key) != len(rows) or any(key not in expected_keys for key in by_key):
        raise ValueError("duplicate or unexpected B01 result key")
    status_keys = {state: [key for key in expected_keys if by_key.get(key, {}).get("status") == state]
                   for state in ("completed", "failed", "unreconciled", "cancelled")}
    missing = [key for key in expected_keys if key not in by_key]
    completed = {arm: {row["seed"]: row for row in rows
                       if row.get("status") == "completed" and row.get("arm") == arm}
                 for arm in ARMS}
    panels = {}
    for arm in ARMS:
        group = list(completed[arm].values())
        panels[arm] = {
            "planned_worlds": len(seeds), "completed_worlds": len(group),
            "status": "observed_complete" if len(group) == len(seeds) else "observed_partial",
            "terminal_types": {kind: sum(row.get("terminal_type") == kind for row in group)
                               for kind in ("terminated", "truncated", "horizon")},
            "means": {field: _distribution([row[field] for row in group])["mean"]
                      if group and all(_numeric(row.get(field)) for row in group) else None
                      for field in ENDPOINTS},
            "zero_service_worlds": sum(bool(row.get("zero_service")) for row in group),
        }
    pair_rows = []
    hash_counts = {field: {"equal": 0, "different": 0, "unavailable": 0}
                   for field in PAIR_HASHES}
    for seed in seeds:
        available = {arm: completed[arm][seed] for arm in ARMS if seed in completed[arm]}
        if len(available) < 2:
            continue
        hashes = {}
        for field in PAIR_HASHES:
            values = [available[arm].get(field) for arm in available]
            state = ("unavailable" if any(not value for value in values) else
                     "equal" if len(set(values)) == 1 else "different")
            hashes[field] = state
            hash_counts[field][state] += 1
        pair = {"seed": seed, "available_arms": list(available), "hashes": hashes,
                "episode_lengths": {arm: row["actual_length"] for arm, row in available.items()},
                "terminal_types": {arm: row["terminal_type"] for arm, row in available.items()},
                "contrasts": {}}
        for a, b in CONTRASTS:
            if a not in available or b not in available:
                continue
            pair["contrasts"][f"{a}-{b}"] = {
                field: float(available[a][field]) - float(available[b][field])
                for field in ENDPOINTS
                if _numeric(available[a].get(field)) and _numeric(available[b].get(field))}
        pair_rows.append(pair)
    full_panel = (len(status_keys["completed"]) == len(expected_keys) == 24
                  and not missing and all(len(completed[arm]) == len(seeds) for arm in ARMS))
    missing_endpoints = {row["job_key"]: [field for field in ENDPOINTS
                                          if not _numeric(row.get(field))]
                         for row in rows if row.get("status") == "completed"}
    missing_endpoints = {key: fields for key, fields in missing_endpoints.items() if fields}
    pair_valid = full_panel and not missing_endpoints and all(
        len({completed[arm][seed].get(field) for arm in ARMS}) == 1
        and bool(completed["H"][seed].get(field))
        for seed in seeds for field in PAIR_HASHES)
    contrasts = {}
    for a, b in CONTRASTS:
        label = f"{a}-{b}"
        observations = [pair for pair in pair_rows if label in pair["contrasts"]]
        contrasts[label] = {
            "status": "paired_primary" if pair_valid else "descriptive_partial_or_unverified",
            "observed_worlds": len(observations),
            "endpoints": {field: _contrast([pair["contrasts"][label][field]
                                           for pair in observations
                                           if field in pair["contrasts"][label]], interval=pair_valid)
                          for field in ENDPOINTS},
            "loss_worlds": {field: [pair["seed"] for pair in observations
                                   if field in pair["contrasts"][label] and
                                   (pair["contrasts"][label][field] > 0 if
                                    any(token in field for token in LOWER_IS_BETTER) else
                                    pair["contrasts"][label][field] < 0)]
                            for field in ENDPOINTS
                            if any(token in field for token in LOWER_IS_BETTER)
                            or field in HIGHER_IS_BETTER
                            or (field.endswith(("_sum", "_per_step")) and any(
                                token in field for token in HIGHER_IS_BETTER))},
        }
    return {
        "status": "complete" if pair_valid else "incomplete",
        "planned_jobs": len(expected_keys), "completed_jobs": len(status_keys["completed"]),
        "missing_jobs": missing, "failed_jobs": status_keys["failed"],
        "unreconciled_jobs": status_keys["unreconciled"],
        "cancelled_jobs": status_keys["cancelled"],
        "missing_endpoints": missing_endpoints,
        "panels": panels, "paired_worlds": pair_rows, "contrasts": contrasts,
        "pair_hash_agreement": hash_counts, "exogenous_pairing_valid": bool(pair_valid),
        "inference_unit": "same initialized world seed; t7 interval descriptive only for eight verified pairs",
        "interpretation": "native closed-loop endpoints; H is a competence reference, not a clock-matched causal control",
    }
