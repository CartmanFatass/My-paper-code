"""Initial-world inference for the six fixed information programs."""

from __future__ import annotations

import math

import numpy as np

from experiments.candidates.energy_relay_availability.readout import paired


CONTRASTS = {
    "U-L": {"U": 1, "L": -1},
    "F-B": {"F": 1, "B": -1},
    "B-L": {"B": 1, "L": -1},
    "F-U": {"F": 1, "U": -1},
    "interaction": {"F": 1, "U": -1, "B": -1, "L": 1},
    "F-L": {"F": 1, "L": -1},
    "R-F": {"R": 1, "F": -1},
    "R-L": {"R": 1, "L": -1},
    "H_BS-L": {"H_BS": 1, "L": -1},
}
TAIL_FIELDS = {
    "qos_per_step", "raw_native_J", "episode_minimum_battery_ratio",
    "return_constraint_cost_per_step", "return_constraint_cost_raw_per_step",
    "cutoff_event_count_sum", "depletion_event_count_sum",
}
EXCLUDED_FIELDS = {
    "seed", "raw_bytes", "worker_wall_seconds", "worker_cpu_seconds", "worker_peak_rss_kib",
}


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def distribution(values):
    data = np.asarray(values, dtype=np.float64)
    return {
        "n": len(data), "mean": float(data.mean()) if len(data) else None,
        "sd": float(data.std(ddof=1)) if len(data) > 1 else None,
        "min": float(data.min()) if len(data) else None,
        "max": float(data.max()) if len(data) else None,
    }


def summarize(rows, jobs):
    expected = {job["job_key"]: job for job in jobs}
    by_key = {row["job_key"]: row for row in rows}
    if len(by_key) != len(rows) or set(by_key) - set(expected):
        raise ValueError("duplicate or unexpected world rows")
    for key, row in by_key.items():
        job = expected[key]
        if row["arm"] != job["arm"] or row["seed"] != job["seed"]:
            raise ValueError("world identity does not match the fixed job")
    groups = {job["arm"]: [] for job in jobs}
    for row in rows:
        if row["status"] == "completed":
            groups[row["arm"]].append(row)
    numeric_fields = sorted({field for row in rows if row["status"] == "completed"
                             for field, value in row.items()
                             if number(value) and field not in EXCLUDED_FIELDS})
    panels = {}
    for arm, panel in groups.items():
        fields = {}
        for field in numeric_fields:
            values = [float(row[field]) for row in panel if number(row.get(field))]
            fields[field] = distribution(values) | {"missing": len(panel) - len(values)}
        panels[arm] = {
            "planned_worlds": sum(job["arm"] == arm for job in jobs),
            "completed_worlds": len(panel), "metrics": fields,
            "zero_service_worlds": [row["seed"] for row in panel if row.get("zero_service")],
            "terminal_types": {kind: sum(row["terminal_type"] == kind for row in panel)
                               for kind in ("terminated", "truncated", "horizon")},
        }
    missing = [key for key in expected if key not in by_key]
    failures = {status: [key for key, row in by_key.items() if row["status"] == status]
                for status in ("failed", "cancelled", "unreconciled")}
    complete = not missing and all(row["status"] == "completed" for row in rows)
    contrasts = {}
    if complete:
        indexed = {arm: {row["seed"]: row for row in panel} for arm, panel in groups.items()}
        seeds = sorted(indexed["L"])
        if any(sorted(panel) != seeds for panel in indexed.values()):
            raise ValueError("six arms do not share the same initial-world seeds")
        for field in numeric_fields:
            contrasts[field] = {}
            for name, weights in CONTRASTS.items():
                unavailable = {arm: [seed for seed in seeds if not number(indexed[arm][seed].get(field))]
                               for arm in weights}
                if any(unavailable.values()):
                    contrasts[field][name] = {"status": "not_comparable", "missing": unavailable}
                    continue
                differences = [sum(weight * indexed[arm][seed][field] for arm, weight in weights.items())
                               for seed in seeds]
                result = paired(differences, [0.0] * len(differences))
                result.update(positive=sum(value > 0 for value in differences),
                              negative=sum(value < 0 for value in differences),
                              minimum=min(differences), maximum=max(differences))
                if field in TAIL_FIELDS:
                    result["by_seed"] = dict(zip(map(str, seeds), differences))
                contrasts[field][name] = result
    return {
        "status": "complete" if complete else "incomplete",
        "planned_jobs": len(jobs), "completed_jobs": sum(map(len, groups.values())),
        "missing_jobs": missing, **{f"{key}_jobs": value for key, value in failures.items()},
        "panels": panels, "contrasts": contrasts, "inference_unit": "initial world seed",
        "estimand": "total closed-loop consequence of fixed programs; trajectories may diverge",
        "intervals": "nominal paired t95; exploratory; no multiplicity adjustment or optimal VoI",
    }
