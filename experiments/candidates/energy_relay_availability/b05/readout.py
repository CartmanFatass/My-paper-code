"""Paired, adverse-inclusive native readout for B05 five/ten-step versus one-step comparison."""

from __future__ import annotations

from experiments.candidates.energy_relay_availability.readout import paired


ARMS = ("one_step", "five_ten")
PRIMARY_FIELDS = (
    "qos_per_step",
    "raw_native_J",
    "native_J_per_step",
    "return_constraint_cost_per_step",
    "episode_minimum_battery_ratio",
    "below_fixed_reserve_uav_step_fraction",
    "service_cutoff_uav_step_fraction",
    "cutoff_event_count_sum",
    "depletion_event_count_sum",
    "actual_length",
)
PAIR_HASHES = ("initial_state_sha256", "user_xy_trace_sha256", "rng_state_stream_sha256")


def summarize(rows: list[dict], expected_seeds: tuple[int, ...], expected_keys: list[str]) -> dict:
    by_key = {row["job_key"]: row for row in rows}
    missing = [key for key in expected_keys if key not in by_key]
    failed = [key for key in expected_keys if key in by_key and by_key[key]["status"] == "failed"]
    unreconciled = [key for key in expected_keys
                    if key in by_key and by_key[key]["status"] == "unreconciled"]
    cancelled = [key for key in expected_keys
                 if key in by_key and by_key[key]["status"] == "cancelled"]
    groups = {arm: [row for row in rows if row.get("arm") == arm
                    and row.get("status") == "completed"] for arm in ARMS}
    complete_cells = all(len(groups[arm]) == len(expected_seeds) for arm in ARMS)
    maps = {arm: {row["seed"]: row for row in groups[arm]} for arm in ARMS}

    pair_rows = []
    hash_agreement = {name: {"equal_pairs": 0, "different_pairs": 0} for name in PAIR_HASHES}
    exogenous_pairs_valid = complete_cells
    contrasts = {}
    if complete_cells:
        for seed in expected_seeds:
            baseline, candidate = maps[ARMS[0]][seed], maps[ARMS[1]][seed]
            equal = {}
            for name in PAIR_HASHES:
                same = bool(baseline.get(name) and baseline.get(name) == candidate.get(name))
                equal[name] = same
                hash_agreement[name]["equal_pairs" if same else "different_pairs"] += 1
            exogenous_pairs_valid &= all(equal.values())
            pair = {"seed": int(seed), "hashes_equal": equal}
            for field in PRIMARY_FIELDS:
                a, b = candidate.get(field), baseline.get(field)
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    pair[f"{field}_delta"] = float(a) - float(b)
            pair_rows.append(pair)
        for field in PRIMARY_FIELDS:
            candidate_values = [float(maps[ARMS[1]][seed][field]) for seed in expected_seeds]
            baseline_values = [float(maps[ARMS[0]][seed][field]) for seed in expected_seeds]
            contrasts[field] = {"status": "paired", **paired(candidate_values, baseline_values)}

    panels = {}
    for arm in ARMS:
        worlds = groups[arm]
        panels[arm] = {
            "planned_worlds": len(expected_seeds),
            "completed_worlds": len(worlds),
            "zero_service_worlds": sum(bool(row.get("zero_service", False)) for row in worlds),
            "terminal_types": {kind: sum(row.get("terminal_type") == kind for row in worlds)
                               for kind in ("terminated", "truncated", "horizon")},
            "means": {
                field: (sum(float(row[field]) for row in worlds) / len(worlds)
                        if worlds and all(field in row for row in worlds) else None)
                for field in PRIMARY_FIELDS
            },
            "planner_hold_windows": sum(int(row.get("selected_hold_windows", 0)) for row in worlds),
            "scorer_snapshot_calls": sum(int(row.get("service_snapshot_calls", 0)) for row in worlds),
            "candidate_plan_evaluations": sum(int(row.get("candidate_plan_evaluations", 0)) for row in worlds),
            "selected_hold_near_tie_windows": sum(
                int(row.get("selected_hold_near_tie_windows", 0)) for row in worlds),
        }
    status = "complete" if (not missing and not failed and not unreconciled and not cancelled
                            and complete_cells and exogenous_pairs_valid) else "incomplete"
    adverse_pairs = sorted(
        (item for item in pair_rows if "qos_per_step_delta" in item),
        key=lambda item: (item["qos_per_step_delta"], item["seed"]),
    )
    return {
        "status": status,
        "planned_jobs": len(expected_keys),
        "completed_jobs": sum(len(values) for values in groups.values()),
        "missing_jobs": missing,
        "failed_jobs": failed,
        "unreconciled_jobs": unreconciled,
        "cancelled_jobs": cancelled,
        "panels": panels,
        "contrasts_five_ten_minus_one_step": contrasts,
        "paired_worlds": pair_rows,
        "adverse_qos_pairs_ascending": adverse_pairs,
        "pair_hash_agreement": hash_agreement,
        "exogenous_pairing_valid": bool(exogenous_pairs_valid),
        "inference_unit": "same initialized world seed; approximate paired t31 interval",
        "interpretation": "native service, J, risk and adverse pairs govern; planner scores are proxy diagnostics",
    }
