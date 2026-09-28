"""Descriptive common-world contrasts for one trained instance and fixed programs."""

from __future__ import annotations

from experiments.candidates.energy_relay_availability.readout import paired
from experiments.candidates.uav_information_value.readout import distribution, number


ARMS = ("L0", "L1", "H", "P", "A")
CONTRASTS = (("L1", "L0"), ("L1", "A"), ("L1", "P"), ("L1", "H"),
             ("A", "H"), ("P", "H"), ("A", "P"))
EXCLUDED = {"seed", "raw_bytes", "worker_wall_seconds", "worker_cpu_seconds", "worker_peak_rss_kib"}
TAIL_FIELDS = {"raw_native_J", "qos_per_step", "episode_minimum_battery_ratio",
               "return_constraint_cost_raw_per_step", "return_constraint_cost_per_step",
               "reserve10_uav_step_fraction", "cutoff_event_count_sum", "depletion_event_count_sum"}


def summarize(rows, jobs, *, horizon=3000):
    expected = {row["job_key"]: row for row in jobs}
    indexed = {row["job_key"]: row for row in rows}
    if len(indexed) != len(rows) or set(indexed) - set(expected):
        raise ValueError("duplicate or unexpected evaluation world")
    for key, row in indexed.items():
        if any(row[field] != expected[key][field] for field in ("arm", "seed")):
            raise ValueError("evaluation row identity differs from the declared job")
    complete = len(rows) == len(jobs) and all(
        row["status"] == "completed" and row["actual_length"] == horizon for row in rows)
    groups = {arm: [row for row in rows if row["arm"] == arm and row["status"] == "completed"]
              for arm in ARMS}
    fields = sorted({field for panel in groups.values() for row in panel for field, value in row.items()
                     if number(value) and field not in EXCLUDED})
    panels = {}
    for arm, panel in groups.items():
        panels[arm] = {
            "completed_worlds": len(panel), "zero_service_worlds": [r["seed"] for r in panel if r.get("zero_service")],
            "metrics": {field: distribution([r[field] for r in panel if number(r.get(field))]) |
                        {"missing": sum(not number(r.get(field)) for r in panel)} for field in fields},
            "terminal_types": {kind: sum(r["terminal_type"] == kind for r in panel)
                               for kind in ("terminated", "truncated", "horizon")},
        }
    contrasts = {}
    if complete:
        by_arm = {arm: {row["seed"]: row for row in panel} for arm, panel in groups.items()}
        seeds = sorted(by_arm["L0"])
        if any(sorted(panel) != seeds for panel in by_arm.values()):
            raise ValueError("evaluation arms do not have the same common-world panel")
        for field in fields:
            contrasts[field] = {}
            for left, right in CONTRASTS:
                name = f"{left}-{right}"
                if any(not number(by_arm[arm][seed].get(field)) for arm in (left, right) for seed in seeds):
                    contrasts[field][name] = {"status": "not_comparable"}
                    continue
                differences = [by_arm[left][seed][field] - by_arm[right][seed][field] for seed in seeds]
                result = paired(differences, [0.0] * len(differences))
                result.update(positive=sum(v > 0 for v in differences), negative=sum(v < 0 for v in differences),
                              minimum=min(differences), maximum=max(differences))
                if field in TAIL_FIELDS:
                    result["by_seed"] = dict(zip(map(str, seeds), differences))
                contrasts[field][name] = result
    return {
        "status": "complete" if complete else "incomplete", "planned_jobs": len(jobs),
        "completed_jobs": sum(map(len, groups.values())),
        "missing_jobs": [key for key in expected if key not in indexed],
        "failed_jobs": [row["job_key"] for row in rows if row["status"] != "completed"],
        "panels": panels, "contrasts": contrasts, "n_train": 1,
        "estimand": "total closed-loop deployment of fixed policies with common legal information",
        "inference_unit": "initial evaluation-world seed, conditional on one trained instance",
        "intervals": "exploratory paired t95, no multiplicity adjustment, no learning replication",
    }
