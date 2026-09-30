"""Compact complete-trajectory comparisons and the prospective research screens."""
from __future__ import annotations

import numpy as np
from scipy.stats import t as student_t

from .contract import ARMS


METRICS = (
    "J", "mean_served", "service_p10", "min_served", "zero_service_steps",
    "mean_sinr_quality", "mean_path_length_m", "xy_boundary_uav_steps",
    "lower_altitude_uav_steps", "decision_query_cpu_seconds", "decision_query_wall_seconds",
    "cpu_seconds", "wall_seconds",
)


def episode_metrics(raw):
    reward = np.asarray(raw["reward"], dtype=np.float64)
    served = np.asarray(raw["served"], dtype=np.int64)
    positions = np.asarray(raw["positions"], dtype=np.float64)
    quality = np.asarray(raw["sinr_quality"], dtype=np.float64)
    post = positions[1:]
    boundary = ((post[..., 0] <= .001) | (post[..., 0] >= 999.999)
                | (post[..., 1] <= .001) | (post[..., 1] >= 999.999))
    return {
        "steps": len(reward), "J": float(reward.mean()), "return_sum": float(reward.sum()),
        "mean_served": float(served.mean()), "service_p10": float(np.quantile(served, .1)),
        "min_served": int(served.min()), "zero_service_steps": int(np.count_nonzero(served == 0)),
        "mean_sinr_quality": float(quality.mean()),
        "coverage_reward": float(.7 * served.mean() / 50), "quality_reward": float(.3 * quality.mean()),
        "mean_path_length_m": float(np.linalg.norm(np.diff(positions, axis=0), axis=-1).sum(axis=0).mean()),
        "xy_boundary_uav_steps": int(boundary.sum()),
        "lower_altitude_uav_steps": int(np.count_nonzero(post[..., 2] <= 50.001)),
        "fallback_decisions": int(np.count_nonzero(raw["fallback"])),
        "command_counts": np.bincount(np.asarray(raw["action_index"]).reshape(-1), minlength=27).tolist(),
        "zero_displacement_uav_ticks": int(np.count_nonzero(np.all(np.diff(positions, axis=0) == 0, axis=-1))),
        "policy_cache_hits": int(np.count_nonzero(raw["memo_hit"])),
        "policy_decisions": int(np.asarray(raw["action_index"]).size),
    }


def numeric_summary(values):
    a = np.asarray(values, dtype=np.float64)
    if a.ndim != 1 or not len(a) or not np.isfinite(a).all():
        raise ValueError("finite nonempty scalar sample required")
    mean = float(a.mean())
    sd = float(a.std(ddof=1)) if len(a) > 1 else None
    half = float(student_t.ppf(.975, len(a) - 1) * sd / np.sqrt(len(a))) if sd is not None else None
    return {"n": len(a), "mean": mean, "sd": sd, "min": float(a.min()), "max": float(a.max()),
            "descriptive_t95": [mean - half, mean + half] if half is not None else None}


def read_comparisons(rows, worlds, *, actual_learning):
    evaluation = [row for row in rows if row["kind"] == "evaluation"]
    by_key = {(r["arm"], r["world"]): r for r in evaluation}
    if len(by_key) != len(evaluation) or len(evaluation) != len(ARMS) * len(worlds):
        raise ValueError("incomplete or duplicated fixed evaluation panel")
    if any((arm, world) not in by_key for arm in ARMS for world in worlds):
        raise ValueError("wrong evaluation identities")
    means = {arm: {metric: numeric_summary([by_key[arm, w][metric] for w in worlds])
                   for metric in METRICS} for arm in ARMS}
    pairs = (("S_greedy", "C_memo"), ("S_sampled", "C_memo"), ("BC", "C_memo"),
             ("C7_memo", "C_memo"), ("S_greedy", "S0"), ("S_greedy", "BC"),
             ("S_sampled", "S_greedy"), ("S_greedy", "C7_memo"), ("S_sampled", "C7_memo"))
    comparisons = {}
    for left, right in pairs:
        data = {}
        for metric in METRICS:
            delta = np.array([by_key[left, w][metric] - by_key[right, w][metric] for w in worlds])
            data[metric] = {**numeric_summary(delta), "differences": delta.tolist(),
                            "positive": int(np.count_nonzero(delta > 0)),
                            "negative": int(np.count_nonzero(delta < 0)),
                            "zero": int(np.count_nonzero(delta == 0))}
        comparisons[f"{left}-{right}"] = data

    def near_c(arm):
        pair = comparisons[f"{arm}-C_memo"]
        new_zero = [w for w in worlds if by_key[arm, w]["zero_service_steps"] > 0
                    and by_key["C_memo", w]["zero_service_steps"] == 0]
        conditions = {"J_margin": pair["J"]["mean"] >= -.01,
                      "service_margin": pair["mean_served"]["mean"] >= -.5,
                      "service_p10_margin": pair["service_p10"]["mean"] >= -1.0,
                      "no_new_zero_service_world": not new_zero}
        return {"conditions": conditions, "pass": all(conditions.values()),
                "new_zero_service_worlds": new_zero}

    greedy, sampled, bc = (near_c(a) for a in ("S_greedy", "S_sampled", "BC"))
    learned_pair = comparisons["S_greedy-S0"]
    development = {"actual_learning": bool(actual_learning),
                   "positive_J_over_S0": learned_pair["J"]["mean"] > 0,
                   "positive_service_over_S0": learned_pair["mean_served"]["mean"] > 0}
    primary_pass = greedy["pass"] and all(development.values())
    return {"worlds": list(worlds), "means": means, "paired": comparisons,
            "screens": {"greedy_near_C": greedy, "sampled_near_C": sampled,
                        "BC_milestone_only": bc, "development_conditions": development,
                        "greedy_primary_pass": primary_pass,
                        "both_starting_asset_screens_pass": primary_pass and sampled["pass"]},
            "scope": "exploratory point screens and world-paired descriptive intervals for one training lineage; "
                     "sampled final has one fixed independently indexed realization per world; not noninferiority, "
                     "training-population inference, later PPO, or checkpoint/decoder selection"}


def sum_counts(items):
    result = {}
    for item in items:
        for key, value in item.items():
            result[key] = result.get(key, 0) + int(value)
    return result


def cost_totals(rows):
    full_c = []
    c7 = []
    helper = []
    neural = []
    for row in rows:
        if row["kind"] == "training":
            full_c.append(row["expert_counts"])
        elif row["arm"] == "C_memo":
            full_c.append(row["policy_counts"])
        if row["arm"] == "C7_memo":
            c7.append(row["policy_counts"])
        for counts in (row["policy_counts"], row["feature_counts"]):
            helper.append({k: v for k, v in counts.items() if k.startswith("helper_")})
            neural.append({k: v for k, v in counts.items() if k in ("neural_rows", "sampled_draws")})
    return {"full_C": sum_counts(full_c), "C7": sum_counts(c7),
            "helper": sum_counts(helper), "neural": sum_counts(neural),
            "scope": "actual recorded computations; expert roll-in C policy and expert labels share one query, "
                     "counted once in full_C; caches reset per agent/episode; cache byte counts exclude Python overhead"}
