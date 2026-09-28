"""Complete-world reading for the fixed lawful station-prior comparison."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_availability.readout import paired
from experiments.candidates.uav_information_value.readout import (
    EXCLUDED_FIELDS, TAIL_FIELDS, distribution, number,
)


ARMS = ("H_BS", "P_BS")
RESERVE_RATIO = 0.10
RISK_FIELDS = {
    "native_reserve_uav_steps", "native_reserve_uav_step_fraction",
    "native_final_reserve_uav_count", "native_final_minimum_battery_ratio",
    "native_minimum_battery_ratio",
}


def battery_reading(values):
    battery = np.asarray(values, dtype=np.float64)
    if (battery.ndim != 2 or battery.shape[1] != 8 or not len(battery)
            or not np.isfinite(battery).all()
            or np.any((battery < 0.0) | (battery > 1.0))):
        raise ValueError("expected finite native post-step battery trace (time, 8)")
    reserve = battery <= RESERVE_RATIO
    return {
        "native_reserve_uav_steps": int(reserve.sum()),
        "native_reserve_uav_step_fraction": float(reserve.mean()),
        "native_final_reserve_uav_count": int(reserve[-1].sum()),
        "native_final_minimum_battery_ratio": float(battery[-1].min()),
        "native_minimum_battery_ratio": float(battery.min()),
    }


def summarize(rows, jobs):
    expected = {job["job_key"]: job for job in jobs}
    by_key = {row["job_key"]: row for row in rows}
    if len(expected) != len(jobs) or len(by_key) != len(rows) or set(by_key) - set(expected):
        raise ValueError("duplicate or unexpected world rows/jobs")
    for key, row in by_key.items():
        if any(row[field] != expected[key][field] for field in ("arm", "seed")):
            raise ValueError("world identity does not match the fixed job")
    if {job["arm"] for job in jobs} != set(ARMS):
        raise ValueError("B02 requires H_BS and P_BS")
    groups = {arm: [row for row in rows if row["arm"] == arm and row["status"] == "completed"]
              for arm in ARMS}
    fields = sorted({key for panel in groups.values() for row in panel
                     for key, value in row.items() if number(value) and key not in EXCLUDED_FIELDS})
    panels = {}
    for arm, panel in groups.items():
        metrics = {}
        for field in fields:
            values = [float(row[field]) for row in panel if number(row.get(field))]
            metrics[field] = distribution(values) | {"missing": len(panel) - len(values)}
        panels[arm] = {
            "planned_worlds": sum(job["arm"] == arm for job in jobs),
            "completed_worlds": len(panel), "metrics": metrics,
            "zero_service_worlds": [row["seed"] for row in panel if row.get("zero_service")],
            "never_seen_bs_worlds": [row["seed"] for row in panel
                                     if row.get("first_legal_bs_step") is None],
            "terminal_types": {kind: sum(row["terminal_type"] == kind for row in panel)
                               for kind in ("terminated", "truncated", "horizon")},
        }
    missing = [key for key in expected if key not in by_key]
    failures = {status: [key for key, row in by_key.items() if row["status"] == status]
                for status in ("failed", "cancelled", "unreconciled")}
    complete = not missing and all(row["status"] == "completed" for row in rows)
    contrasts, risk = {}, {}
    if complete:
        indexed = {arm: {row["seed"]: row for row in panel} for arm, panel in groups.items()}
        seeds = sorted(indexed["H_BS"])
        if sorted(indexed["P_BS"]) != seeds or any(len(indexed[arm]) != len(groups[arm]) for arm in ARMS):
            raise ValueError("two arms do not share unique initial-world seeds")
        for field in fields:
            unavailable = {arm: [seed for seed in seeds if not number(indexed[arm][seed].get(field))]
                           for arm in ARMS}
            if any(unavailable.values()):
                result = {"status": "not_comparable", "missing": unavailable}
            else:
                deltas = [indexed["P_BS"][seed][field] - indexed["H_BS"][seed][field]
                          for seed in seeds]
                result = paired(deltas, [0.0] * len(deltas))
                result.update(positive=sum(value > 0 for value in deltas),
                              negative=sum(value < 0 for value in deltas),
                              ties=sum(value == 0 for value in deltas),
                              minimum=min(deltas), maximum=max(deltas))
                if field in TAIL_FIELDS | RISK_FIELDS | {"prior_used_plans", "relay_plans"}:
                    result["by_seed"] = dict(zip(map(str, seeds), deltas))
            contrasts[field] = {"P_BS-H_BS": result}
        for field in ("cutoff_event_count_sum", "depletion_event_count_sum",
                      "native_final_reserve_uav_count"):
            available = all(number(indexed[arm][seed].get(field)) for arm in ARMS for seed in seeds)
            risk[field] = ({"additional_worlds": [seed for seed in seeds
                          if indexed["P_BS"][seed][field] > indexed["H_BS"][seed][field]]}
                          if available else {"status": "not_comparable"})
    return {
        "status": "complete" if complete else "incomplete",
        "planned_jobs": len(jobs), "completed_jobs": sum(map(len, groups.values())),
        "missing_jobs": missing, **{f"{key}_jobs": value for key, value in failures.items()},
        "panels": panels, "contrasts": contrasts, "practical_risk": risk,
        "inference_unit": "initial world seed",
        "estimand": "total closed-loop consequence of fixed legal programs; trajectories may diverge",
        "intervals": "nominal paired t95; exploratory; no multiplicity adjustment or optimal VoI",
        "reserve_ratio": RESERVE_RATIO,
    }
