"""Complete-mission levels, paired worlds and explicitly descriptive exposure readings."""
from __future__ import annotations

import math
import numpy as np
from scipy.stats import t as student_t

from .contract import ARMS, HORIZON


def longest(values):
    values = np.asarray(values, dtype=bool).reshape(-1)
    delta = np.diff(np.r_[False, values, False].astype(np.int8))
    return int(np.max(np.flatnonzero(delta == -1) - np.flatnonzero(delta == 1), initial=0))


def describe(values):
    a = np.asarray(values, dtype=np.float64)
    if a.ndim != 1 or not len(a) or not np.isfinite(a).all():
        raise ValueError("expected complete finite world values")
    return dict(n=len(a), mean=float(a.mean()), sd=float(a.std(ddof=1)) if len(a) > 1 else None,
                minimum=float(a.min()), p10=float(np.quantile(a, .1)), median=float(np.median(a)),
                p90=float(np.quantile(a, .9)), maximum=float(a.max()))


def paired(values, seeds):
    a = np.asarray(values, dtype=np.float64)
    result = describe(a)
    se = float(a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 else None
    radius = float(student_t.ppf(.975, len(a) - 1) * se) if se is not None else None
    result.update(se=se, t95=None if radius is None else [result["mean"] - radius, result["mean"] + radius],
                  positive=int(np.count_nonzero(a > 0)), negative=int(np.count_nonzero(a < 0)),
                  ties=int(np.count_nonzero(a == 0)),
                  by_world={str(seed): float(value) for seed, value in zip(seeds, a)})
    return result


def episode_metrics(raw):
    fields = {str(name): column for column, name in enumerate(raw["metric_fields"])}
    m = raw["metrics"]
    q = m[:, fields["qos_satisfaction_ratio"]]
    length = len(q)
    battery = raw["native_battery"][1:]
    reserve = battery <= .10
    travel = np.linalg.norm(np.diff(raw["truth_uav_xyz"], axis=0), axis=2)
    result = dict(
        J_total=float(math.fsum(map(float, raw["reward"]))),
        J_per_planned_step=float(math.fsum(map(float, raw["reward"])) / HORIZON),
        cumulative_qos=float(math.fsum(map(float, q))),
        qos_per_planned_step=float(math.fsum(map(float, q)) / HORIZON),
        service_equivalent_user_seconds=float(math.fsum(map(float, q)) * 30),
        actual_length=length, zero_service_steps=int(np.count_nonzero(q == 0)),
        longest_zero_service_spell=longest(q == 0), qos_minimum=float(q.min()),
        qos_p10=float(np.quantile(q, .1)),
        travel_team_m=float(travel.sum()), travel_per_uav_m=float(travel.sum() / 8),
        native_reserve_uav_steps=int(reserve.sum()),
        native_final_reserve_uav_count=int(reserve[-1].sum()),
        native_minimum_battery_ratio=float(battery.min()),
        native_final_minimum_battery_ratio=float(battery[-1].min()),
        longest_low_reserve_spell=max(longest(reserve[:, member]) for member in range(8)),
        native_consumed_wh=float(raw["native_consumed_wh"][1:].sum()),
        native_charged_wh=float(raw["native_charged_wh"][1:].sum()),
        native_net_charged_wh=float(raw["native_net_charged_wh"][1:].sum()),
        native_depleted_uav_steps=int(np.count_nonzero(battery <= 0)),
        native_charging_uav_steps=int(raw["native_charging"][1:].sum()),
        native_route_uav_steps=int(np.count_nonzero(raw["native_routes"][1:, :, 0] >= 0)),
        plan_count=len(raw["plan_step"]),
    )
    for name, column in fields.items():
        result[name + "_sum"] = float(math.fsum(map(float, m[:, column])))
    result["low_reserve_longest_by_uav"] = [longest(reserve[:, member]) for member in range(8)]
    if "trace_tracks" in raw:
        steps = raw["plan_step"]
        current = raw["trace_current_count"][steps]
        extra = raw["plan_user_count"] - current
        tracks = raw["trace_tracks"][steps]
        valid = tracks["birth"] >= 0
        ages = steps[:, None] - tracks["last_seen"]
        speed = np.linalg.norm(tracks["v"], axis=-1)
        delta = np.linalg.norm(raw["plan_users"] - tracks["last_xy"], axis=-1)
        result.update(memory_added_point_plans=int(np.count_nonzero(extra)),
                      memory_added_point_plan_total=int(extra.sum()),
                      moving_track_plan_total=int(np.count_nonzero(valid & (speed > 0))),
                      track_age_at_plan_mean=float(ages[valid].mean()) if valid.any() else 0.,
                      track_age_at_plan_max=int(ages[valid].max()) if valid.any() else 0,
                      point_projection_at_plan_mean=float(delta[valid].mean()) if valid.any() else 0.,
                      point_projection_at_plan_max=float(delta[valid].max()) if valid.any() else 0.,
                      mean_current_point_count=float(raw["trace_current_count"].mean()))
        for key in raw:
            if key.startswith("event_count_"):
                result[key + "_total"] = int(raw[key].sum())
    else:
        result.update(memory_added_point_plans=0, memory_added_point_plan_total=0,
                      moving_track_plan_total=0, point_projection_at_plan_mean=0.,
                      point_projection_at_plan_max=0.)
    return result


COMPARISON_FIELDS = (
    "J_total", "cumulative_qos", "J_per_planned_step", "qos_per_planned_step",
    "service_equivalent_user_seconds", "actual_length", "qos_minimum", "qos_p10",
    "zero_service_steps", "longest_zero_service_spell", "travel_per_uav_m",
    "native_consumed_wh", "native_charged_wh", "native_net_charged_wh",
    "native_reserve_uav_steps", "native_final_reserve_uav_count", "longest_low_reserve_spell",
    "native_minimum_battery_ratio", "native_final_minimum_battery_ratio",
    "cutoff_event_count_sum", "depletion_event_count_sum", "return_constraint_cost_sum",
    "graph_potential_delta_sum", "delivered_end_to_end_throughput_mbps_sum",
    "native_charging_uav_steps", "native_route_uav_steps", "proposal_cpu_seconds", "worker_cpu_seconds",
)


def comparisons(rows):
    indexed = {(r["seed"], r["arm"]): r for r in rows}
    seeds = sorted({r["seed"] for r in rows})
    if len(indexed) != len(rows) or set(indexed) != {(s, a) for s in seeds for a in ARMS}:
        raise ValueError("incomplete three-arm paired panel")
    levels = {arm: {field: describe([indexed[seed, arm][field] for seed in seeds])
                    for field in COMPARISON_FIELDS} for arm in ARMS}
    contrasts = {}
    for left, right in (("V", "M"), ("M", "C"), ("V", "C")):
        contrasts[left + "-" + right] = {
            field: paired([indexed[seed, left][field] - indexed[seed, right][field] for seed in seeds], seeds)
            for field in COMPARISON_FIELDS}
    return dict(levels=levels, contrasts=contrasts, uncertainty="descriptive paired-world Student t95; df=n-1")
