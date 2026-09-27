"""Paired world-seed B02 readout, with nullable diagnostics and full adverse pairs."""

from __future__ import annotations

from .events import aggregate_events
from .readout import _distribution, _number, paired


ARMS = ("clock30", "availability_event")
EXCLUDED = {"seed", "worker_peak_rss_kib", "worker_cpu_seconds",
            "worker_wall_seconds", "raw_bytes"}
PAIR_FIELDS = ("raw_native_J", "qos_per_step", "return_constraint_cost_per_step",
               "episode_minimum_battery_ratio", "actual_length", "plan_call_count",
               "extra_plan_count", "planning_cpu_seconds", "planning_wall_seconds",
               "world_mean_response_lag")


def summarize(rows: list[dict], expected_keys: list[str]) -> dict:
    by_key = {row["job_key"]: row for row in rows}
    missing = [key for key in expected_keys if key not in by_key]
    failures = {status: [key for key in expected_keys if key in by_key
                         and by_key[key]["status"] == status]
                for status in ("failed", "unreconciled", "cancelled")}
    groups = {arm: [] for arm in ARMS}
    for key in expected_keys:
        row = by_key.get(key)
        if row and row["status"] == "completed":
            groups[row["arm"]].append(row)
    fields = sorted({field for group in groups.values() for row in group
                     for field, value in row.items() if _number(value) and field not in EXCLUDED})
    panels = {}
    for arm, group in groups.items():
        metrics = {}
        for field in fields:
            observed = [float(row[field]) for row in group if _number(row.get(field))]
            metrics[field] = _distribution(observed) | {"missing": len(group) - len(observed)}
        panels[arm] = {
            "planned_worlds": 32, "completed_worlds": len(group), "metrics": metrics,
            "zero_service_worlds": sum(bool(row.get("zero_service", False)) for row in group),
            "terminal_types": {kind: sum(row["terminal_type"] == kind for row in group)
                               for kind in ("terminated", "truncated", "horizon")},
            "events": {kind: aggregate_events(group, kind) for kind in ("onset", "recovery")},
            "response_changes": sum(row["response_changes"] for row in group),
            "response_censored": sum(row["response_censored"] for row in group),
            "terminal_changes": sum(row["terminal_changes"] for row in group),
            "response_worlds": sum(row["response_changes"] > 0 for row in group),
            "no_response_worlds": sum(row["response_changes"] == 0 for row in group),
        }
    complete = not missing and not any(failures.values()) and all(
        len(group) == 32 for group in groups.values())
    contrasts = {}
    world_pairs = []
    trace_agreement = None
    if complete:
        maps = {arm: {row["seed"]: row for row in group} for arm, group in groups.items()}
        if sorted(maps["clock30"]) != sorted(maps["availability_event"]):
            raise ValueError("B02 arms do not pair on the declared seeds")
        seeds = sorted(maps["clock30"])
        for field in fields:
            missing_by_arm = {arm: sum(not _number(row.get(field)) for row in group)
                              for arm, group in groups.items()}
            if any(missing_by_arm.values()):
                contrasts[field] = {"status": "not_comparable", "missing_by_arm": missing_by_arm}
            else:
                contrasts[field] = paired(
                    [maps["availability_event"][seed][field] for seed in seeds],
                    [maps["clock30"][seed][field] for seed in seeds])
        for seed in seeds:
            clock, event = maps["clock30"][seed], maps["availability_event"][seed]
            world_pairs.append({
                "seed": seed, "fault_trace_equal":
                    clock["fault_trace_sha256"] == event["fault_trace_sha256"],
                "clock_zero_service": bool(clock.get("zero_service", False)),
                "event_zero_service": bool(event.get("zero_service", False)),
                "deltas_event_minus_clock": {
                    field: (event[field] - clock[field]
                            if _number(event.get(field)) and _number(clock.get(field)) else None)
                    for field in PAIR_FIELDS},
            })
        trace_agreement = {
            "equal_pairs": sum(pair["fault_trace_equal"] for pair in world_pairs),
            "different_pairs": sum(not pair["fault_trace_equal"] for pair in world_pairs),
            "unit": "paired world seed; equality is observed diagnostic only",
        }
    return {"status": "complete" if complete else "incomplete", "planned_jobs": len(expected_keys),
            "completed_jobs": sum(map(len, groups.values())), "missing_jobs": missing,
            "failed_jobs": failures["failed"], "unreconciled_jobs": failures["unreconciled"],
            "cancelled_jobs": failures["cancelled"], "panels": panels,
            "contrasts_event_minus_clock": contrasts, "world_pairs": world_pairs,
            "fault_trace_agreement": trace_agreement,
            "inference_unit": "paired initial world seed; approximate t31 intervals",
            "event_reading": "descriptive; native fault timing and response events are not independent samples"}
