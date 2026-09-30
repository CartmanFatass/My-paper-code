"""Original complete outcomes plus prospectively fixed post-t40 service tails."""
import numpy as np
from experiments.candidates.uav_fleet_transmission.study import metrics, _longest_true

METRIC_NAMES = (
    "J", "served", "quality", "height_penalty", "mean_path_per_uav", "ineligible",
    "eligible_unserved", "served_p05", "served_min", "zero_steps", "longest_zero_run", "active_mean",
    "suffix_t40_served", "suffix_t40_served_p05", "suffix_t40_served_min",
    "suffix_t40_zero_steps", "suffix_t40_longest_zero_run",
)


def suffix_metrics(connections):
    if np.asarray(connections).shape != (501, 8, 50):
        raise ValueError("suffix requires the complete H500 native connection record")
    served = np.asarray(connections)[41:].sum(axis=(1, 2))
    return {"suffix_t40_served": float(served.mean()),
            "suffix_t40_served_p05": float(np.quantile(served, .05)),
            "suffix_t40_served_min": int(served.min()),
            "suffix_t40_zero_steps": int((served == 0).sum()),
            "suffix_t40_longest_zero_run": _longest_true(served == 0)}


def complete_metrics(raw):
    return {**metrics(raw, 8), **suffix_metrics(raw["connections"])}
