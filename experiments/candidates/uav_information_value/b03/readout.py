"""Complete three-arm native panel reading with paired risk additions."""

from __future__ import annotations

from experiments.candidates.energy_relay_availability.readout import paired
from experiments.candidates.uav_information_value.b02.readout import RESERVE_RATIO
from experiments.candidates.uav_information_value.readout import EXCLUDED_FIELDS, distribution, number


ARMS = ("H_BS", "P_BS", "S0_BS")
CONTRASTS = (("P_BS", "S0_BS"), ("P_BS", "H_BS"), ("S0_BS", "H_BS"))


def summarize(rows, jobs):
    expected = {job["job_key"]: job for job in jobs}
    by_key = {row["job_key"]: row for row in rows}
    if (len(expected) != len(jobs) or len(by_key) != len(rows)
            or set(by_key) - set(expected)):
        raise ValueError("duplicate or unexpected world rows/jobs")
    for key, row in by_key.items():
        if any(row[field] != expected[key][field] for field in ("arm", "seed")):
            raise ValueError("world identity does not match the fixed job")
    if {job["arm"] for job in jobs} != set(ARMS):
        raise ValueError("B03 requires the fixed three arms")
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
            "never_seen_bs_worlds": [row["seed"] for row in panel if row.get("first_legal_bs_step") is None],
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
        if (any(sorted(indexed[arm]) != seeds or len(indexed[arm]) != len(groups[arm]) for arm in ARMS)
                or len(seeds) != len(jobs) // len(ARMS)):
            raise ValueError("three arms do not share unique initial-world seeds")
        for field in fields:
            contrasts[field] = {}
            for left, right in CONTRASTS:
                label = f"{left}-{right}"
                unavailable = {arm: [seed for seed in seeds if not number(indexed[arm][seed].get(field))]
                               for arm in (left, right)}
                if any(unavailable.values()):
                    result = {"status": "not_comparable", "missing": unavailable}
                else:
                    deltas = [indexed[left][seed][field] - indexed[right][seed][field] for seed in seeds]
                    result = paired(deltas, [0.0] * len(deltas))
                    result.update(positive=sum(value > 0 for value in deltas),
                                  negative=sum(value < 0 for value in deltas),
                                  ties=sum(value == 0 for value in deltas),
                                  minimum=min(deltas), maximum=max(deltas),
                                  by_seed=dict(zip(map(str, seeds), deltas)))
                contrasts[field][label] = result
        for field in ("cutoff_event_count_sum", "depletion_event_count_sum",
                      "native_final_reserve_uav_count"):
            risk[field] = {}
            for left, right in CONTRASTS:
                available = all(number(indexed[arm][seed].get(field)) for arm in (left, right)
                                for seed in seeds)
                risk[field][f"{left}-{right}"] = (
                    {"additional_worlds": [seed for seed in seeds
                     if indexed[left][seed][field] > indexed[right][seed][field]],
                     "by_seed": {str(seed): indexed[left][seed][field] - indexed[right][seed][field]
                                 for seed in seeds}}
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
