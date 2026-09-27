"""Complete paired native readout for the fixed one-fit B02 panel."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_availability.readout import paired

ARMS = ("P", "H", "L")
FIELDS = ("qos_per_step", "qos_sum_over_3000", "raw_native_J", "actual_length",
          "return_constraint_cost_sum", "return_constraint_cost_per_step",
          "episode_minimum_battery_ratio", "below_fixed_reserve_uav_step_fraction",
          "service_cutoff_uav_step_fraction", "cutoff_event_count_sum",
          "depletion_event_count_sum", "charging_uav_steps", "guard_checked_actions",
          "guard_blocked_actions", "feedback_entry_count", "feedback_exit_count",
          "selected_hold_windows")


def summarize(rows, collection_seeds, evaluation_seeds, fit_reading=None, pairing=None):
    by_key = {row["job_key"]: row for row in rows}
    expected = ([f"collect/{seed}" for seed in collection_seeds] +
                [f"{arm}/{seed}" for arm in ARMS for seed in evaluation_seeds])
    missing = [key for key in expected if key not in by_key]
    failed = [key for key in expected if key in by_key and
              by_key[key].get("status") != "completed"]
    groups = {arm: [by_key[f"{arm}/{seed}"] for seed in evaluation_seeds
                    if by_key.get(f"{arm}/{seed}", {}).get("status") == "completed"]
              for arm in ARMS}
    panels = {}
    for arm, worlds in groups.items():
        minima = sorted(float(row["episode_minimum_battery_ratio"]) for row in worlds)
        panels[arm] = {
            "completed_worlds": len(worlds),
            "means": {field: float(np.mean([row[field] for row in worlds]))
                      if worlds and all(field in row for row in worlds) else None
                      for field in FIELDS},
            "lowest_eight_episode_minimum_battery_mean": (
                float(np.mean(minima[:8])) if len(minima) >= 8 else None),
            "zero_service_worlds": [row["seed"] for row in worlds if row["zero_service"]],
            "cutoff_worlds": [row["seed"] for row in worlds if row["cutoff_event_count_sum"] > 0],
            "depletion_worlds": [row["seed"] for row in worlds if row["depletion_event_count_sum"] > 0],
            "terminal_types": {kind: sum(row["terminal_type"] == kind for row in worlds)
                               for kind in ("terminated", "truncated", "horizon")},
            "actual_steps": sum(row["actual_length"] for row in worlds),
            "candidate_plans": sum(row.get("candidate_plan_evaluations", 0) for row in worlds),
            "service_snapshots": sum(row.get("service_snapshot_calls", 0) for row in worlds),
            "inference_candidates": sum(row.get("inference_candidate_count", 0) for row in worlds),
        }
    complete = (not missing and not failed and fit_reading is not None and
                all(len(groups[arm]) == len(evaluation_seeds) for arm in ARMS) and
                pairing is not None and pairing.get("valid") is True)
    contrasts, pair_worlds = {}, []
    if complete:
        maps = {arm: {row["seed"]: row for row in groups[arm]} for arm in ARMS}
        for reference in ("P", "H"):
            contrasts[f"L_minus_{reference}"] = {
                field: paired([maps["L"][seed][field] for seed in evaluation_seeds],
                              [maps[reference][seed][field] for seed in evaluation_seeds])
                for field in FIELDS}
        for seed in evaluation_seeds:
            pair_worlds.append({
                "seed": seed,
                **{f"L_minus_{reference}_{field}": float(maps["L"][seed][field] -
                                                       maps[reference][seed][field])
                   for reference in ("P", "H") for field in FIELDS},
                **{f"L_new_zero_service_vs_{reference}": bool(
                    maps["L"][seed]["zero_service"] and
                    not maps[reference][seed]["zero_service"])
                   for reference in ("P", "H")},
                **{f"L_more_{event}_vs_{reference}": bool(
                    maps["L"][seed][f"{event}_event_count_sum"] >
                    maps[reference][seed][f"{event}_event_count_sum"])
                   for reference in ("P", "H") for event in ("cutoff", "depletion")},
            })
    decision = "incomplete_evidence"
    if complete:
        clears = all(contrasts[f"L_minus_{reference}"]["qos_per_step"]["mean"] >= 0.03
                     and contrasts[f"L_minus_{reference}"]["raw_native_J"]["mean"] > 0
                     for reference in ("P", "H"))
        no_new_adverse = not any(
            item[f"L_new_zero_service_vs_{reference}"] or
            item[f"L_more_cutoff_vs_{reference}"] or
            item[f"L_more_depletion_vs_{reference}"]
            for item in pair_worlds for reference in ("P", "H"))
        if clears and no_new_adverse:
            decision = "conditional_candidate_subject_to_tail_and_return_cost_use_judgment"
        elif (contrasts["L_minus_P"]["qos_per_step"]["mean"] >= 0.03 and
              contrasts["L_minus_P"]["raw_native_J"]["mean"] > 0 and
              not (contrasts["L_minus_H"]["qos_per_step"]["mean"] >= 0.03 and
                   contrasts["L_minus_H"]["raw_native_J"]["mean"] > 0)):
            decision = "beats_P_but_not_H_reject_portfolio_improvement"
        elif clears and not no_new_adverse:
            decision = "mean_gain_with_adverse_world_conflict"
        else:
            decision = "fixed_package_does_not_clear_utility_rule"
    return {"status": "complete" if complete else "incomplete",
            "planned_collection_worlds": len(collection_seeds),
            "planned_evaluation_worlds": len(evaluation_seeds) * len(ARMS),
            "completed_collection_worlds": sum(by_key.get(f"collect/{seed}", {}).get("status") == "completed"
                                               for seed in collection_seeds),
            "missing_jobs": missing, "failed_jobs": failed,
            "fit": fit_reading, "panels": panels, "contrasts": contrasts,
            "paired_worlds": pair_worlds, "pairing": pairing,
            "decision_rule_reading": decision,
            "inference_unit": "32 paired worlds conditional on one fixed fit; descriptive t31 intervals"}
