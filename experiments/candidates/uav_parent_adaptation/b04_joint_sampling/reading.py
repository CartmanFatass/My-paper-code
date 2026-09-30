"""Complete episode reductions and 32-world paired exploratory comparisons."""
from __future__ import annotations

import numpy as np
from experiments.candidates.uav_fleet_adaptation.b02.reading import (
    episode_metrics as original_metrics, numeric_summary, sum_counts,
)
from .contract import ARMS, STOCHASTIC

METRICS = ("J", "mean_served", "service_p10", "min_served", "zero_service_steps",
           "longest_zero_service_gap", "mean_sinr_quality", "mean_path_length_m",
           "xy_boundary_uav_steps", "lower_altitude_uav_steps", "requested_departures",
           "multi_departure_blocks", "decision_query_cpu_seconds", "decision_query_wall_seconds",
           "sampler_cpu_seconds", "sampler_wall_seconds", "cpu_seconds", "wall_seconds")
PAIRS = (("S_A", "S_I"), ("S_B", "S_I"), ("Q_A", "Q_I"), ("Q_B", "Q_I"),
         ("S_I", "Q_I"), ("S_A", "Q_A"), ("S_B", "Q_B")) + tuple((a, "C") for a in STOCHASTIC)


def episode_metrics(raw):
    result = original_metrics(raw)
    streak = longest = 0
    for value in raw["served"]:
        streak = streak + 1 if value == 0 else 0
        longest = max(longest, streak)
    departures = np.asarray(raw["action_index"]) != np.asarray(raw["modal_index"])
    result.update(longest_zero_service_gap=longest,
                  per_agent_path_length_m=np.linalg.norm(np.diff(raw["positions"], axis=0), axis=-1).sum(axis=0).tolist(),
                  requested_departures=int(departures.sum()),
                  multi_departure_blocks=int(np.count_nonzero(departures.sum(axis=1) >= 2)))
    return result


def cost_totals(rows):
    return {family: sum_counts(row["policy_counts"] for row in rows
                              if ("S" if row["arm"].startswith("S_") else "C") == family)
            for family in ("C", "S")}


def read_comparisons(rows, protocol):
    by_key = {(r["arm"], r["world"], r["tape"]): r for r in rows}
    expected = set(protocol.schedule())
    if len(by_key) != len(rows) or set(by_key) != expected:
        raise ValueError("incomplete/duplicated/wrong evaluation schedule")

    def value(arm, world, metric):
        tapes = (-1,) if arm == "C" else protocol.tapes
        return float(np.mean([by_key[arm, world, tape][metric] for tape in tapes]))

    means = {arm: {m: numeric_summary([value(arm, w, m) for w in protocol.worlds])
                   for m in METRICS} for arm in ARMS}
    for arm in ARMS:
        episodes = [r["J"] for r in rows if r["arm"] == arm]
        means[arm]["episode_J_p10"] = float(np.quantile(episodes, .1))
    paired = {}
    for left, right in PAIRS:
        data = {}
        for metric in METRICS:
            delta = np.array([value(left, w, metric) - value(right, w, metric) for w in protocol.worlds])
            data[metric] = {**numeric_summary(delta), "differences": delta.tolist(),
                            "positive": int(np.count_nonzero(delta > 0)),
                            "negative": int(np.count_nonzero(delta < 0)), "zero": int(np.count_nonzero(delta == 0))}
        paired[f"{left}-{right}"] = data
    primary = paired["S_A-S_I"]
    intervals = [primary[m]["descriptive_t95"] for m in ("J", "service_p10")]
    return dict(worlds=list(protocol.worlds), means=means, paired=paired,
                primary=dict(point_prediction_met=primary["J"]["mean"] > 0 and primary["service_p10"]["mean"] >= 0,
                             stronger_descriptive_support=bool(all(i is not None for i in intervals)
                                                              and intervals[0][0] > 0 and intervals[1][0] >= 0),
                             continuity_harm_not_excluded=intervals[1] is None or intervals[1][0] < 0),
                scope="Two paired tape effects are averaged within each world; worlds get equal weight. "
                      "Unadjusted descriptive intervals, one retained fitted asset; not noninferiority, "
                      "training replication, a physical net-benefit claim or retrospective primary selection.")
