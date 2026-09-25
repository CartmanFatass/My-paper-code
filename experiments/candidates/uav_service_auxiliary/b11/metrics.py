"""Guard branches and actual low-margin waiting on completed B11 physical traces."""

from __future__ import annotations

import numpy as np

from ..b10.metrics import station_intervals as _station_intervals


def station_intervals(snapshots: list[dict], diagnostics: dict, *, terminal_type: str) -> dict:
    result = _station_intervals(snapshots, diagnostics, terminal_type=terminal_type)
    if terminal_type == "terminated":
        for row in result["waiting_intervals"]:
            if row["end"] == "observation_censored":
                row["end"] = "episode_terminated"
        for row in result["charging_spells"]:
            if row["end"] == "observation_censored":
                row["end"] = "episode_terminated"
        for name, rows, key in (("wait_interval_end_counts", result["waiting_intervals"], "end"),
                                ("charging_spell_end_counts", result["charging_spells"], "end")):
            result[name]["episode_terminated"] = sum(row[key] == "episode_terminated" for row in rows)
            result[name]["observation_censored"] = 0
    length = len(snapshots)
    charged = np.asarray(diagnostics["charger_input_wh"], dtype=float) > 0.0
    if charged.shape != (length, len(snapshots[0]["raw_margin_before_input"])):
        raise ValueError("guard snapshot and charger input lengths differ")
    counts = {name: 0 for name in (
        "station_ticks", "eligible_station_ticks", "trigger_same_selection",
        "trigger_changes_continuity_to_O", "no_trigger_non_O_continuity",
        "actual_G_fallback_station_ticks", "actual_G_non_O_station_ticks",
        "negative_excluded_by_C_uav_ticks", "negative_excluded_by_C_actual_input_uav_ticks",
        "negative_excluded_by_C_actual_wait_uav_ticks",
        "negative_actual_waiter_uav_ticks", "negative_actual_waiter_deficit_sum",
        "negative_excluded_by_C_deficit_sum",
    )}
    negative_wait = np.zeros_like(charged, dtype=bool)
    for tick, snap in enumerate(snapshots):
        margins = np.asarray(snap["raw_margin_before_input"], dtype=float)
        if margins.shape != (charged.shape[1],) or not np.isfinite(margins).all():
            raise ValueError("invalid current raw margins")
        eligible_all = set()
        for station, members in snap["eligible_by_station"].items():
            o = set(snap["original_selected"][station])
            c = set(snap["continuous_selected"][station])
            actual = set(snap["actual_selected"][station])
            trigger = bool(snap["guard_trigger"][station])
            excluded = set(members) - c
            negative_excluded = {m for m in excluded if margins[m] < 0.0}
            if trigger != bool(negative_excluded):
                raise RuntimeError("guard trigger does not match C-excluded raw margins")
            expected = o if trigger or snap["rule"] == "O" else c
            if actual != expected:
                raise RuntimeError("actual selection does not match guard")
            counts["station_ticks"] += 1
            counts["eligible_station_ticks"] += bool(members)
            counts["trigger_same_selection"] += trigger and o == c
            counts["trigger_changes_continuity_to_O"] += trigger and o != c
            counts["no_trigger_non_O_continuity"] += (not trigger) and actual != o
            counts["actual_G_fallback_station_ticks"] += snap["rule"] == "G" and trigger and o != c
            counts["actual_G_non_O_station_ticks"] += snap["rule"] == "G" and actual != o
            counts["negative_excluded_by_C_uav_ticks"] += len(negative_excluded)
            counts["negative_excluded_by_C_actual_input_uav_ticks"] += sum(charged[tick, m] for m in negative_excluded)
            counts["negative_excluded_by_C_actual_wait_uav_ticks"] += sum(not charged[tick, m] for m in negative_excluded)
            counts["negative_excluded_by_C_deficit_sum"] += float(sum(-margins[m] for m in negative_excluded))
            eligible_all.update(members)
        for member in eligible_all:
            if margins[member] < 0.0 and not charged[tick, member]:
                negative_wait[tick, member] = True
                counts["negative_actual_waiter_uav_ticks"] += 1
                counts["negative_actual_waiter_deficit_sum"] += float(-margins[member])
    negative_rows = []
    for member in range(charged.shape[1]):
        padded = np.r_[False, negative_wait[:, member], False].astype(np.int8)
        for start, stop in zip(np.flatnonzero(np.diff(padded) == 1),
                               np.flatnonzero(np.diff(padded) == -1), strict=True):
            negative_rows.append({"member": member, "start": int(start), "stop": int(stop),
                                  "actual_negative_wait_steps": int(stop - start),
                                  "right_censored": bool(stop == length and terminal_type == "truncated"),
                                  "end": ("observation_censored" if terminal_type == "truncated" else
                                          "episode_terminated") if stop == length else
                                         ("actual_input" if charged[stop, member] else "margin_or_eligibility_changed"),
                                  "minimum_raw_margin": float(min(
                                      snapshots[t]["raw_margin_before_input"][member]
                                      for t in range(start, stop))),
                                  "margin_deficit_sum": float(sum(
                                      -snapshots[t]["raw_margin_before_input"][member]
                                      for t in range(start, stop)))})
    result["guard_counts"] = counts
    result["guard_count_semantics"] = (
        "trigger counts describe the prospective O/C branch in both panels; "
        "actual_G counts are executed G interventions"
    )
    result["negative_wait_intervals"] = negative_rows
    result["negative_wait_interval_end_counts"] = {
        key: sum(row["end"] == key for row in negative_rows)
        for key in ("actual_input", "margin_or_eligibility_changed", "observation_censored", "episode_terminated")
    }
    result["negative_wait_interval_count"] = len(negative_rows)
    result["negative_wait_max_steps"] = max((row["actual_negative_wait_steps"] for row in negative_rows), default=0)
    return result


def aggregate_station_summaries(worlds: list[dict]) -> dict:
    from ..b10.metrics import aggregate_station_summaries as base_aggregate
    result = base_aggregate(worlds)
    counts = [row["station"]["guard_counts"] for row in worlds]
    result["guard_counts"] = {key: sum(row[key] for row in counts) for key in counts[0]}
    for name in ("wait_interval_end_counts", "charging_spell_end_counts"):
        result[name]["episode_terminated"] = sum(
            row["station"][name].get("episode_terminated", 0) for row in worlds)
    result["negative_wait_interval_end_counts"] = {
        key: sum(row["station"]["negative_wait_interval_end_counts"][key] for row in worlds)
        for key in worlds[0]["station"]["negative_wait_interval_end_counts"]
    }
    result["negative_wait_interval_count"] = sum(row["station"]["negative_wait_interval_count"] for row in worlds)
    result["maximum_negative_wait_steps"] = max(row["station"]["negative_wait_max_steps"] for row in worlds)
    return result


def suffix_reading(trace: dict, detail: dict, start: int, *, time_step_seconds: float,
                   allocation_difference_exists: bool = True) -> dict:
    """Describe an actual episode from the common first allocation difference."""
    from ..b04.evaluation import TRACE_FIELDS

    rewards = np.asarray(trace["native_reward"], dtype=float)
    metrics = np.asarray(trace["metrics"], dtype=float)
    length = len(rewards)
    if start < 0 or start > length or metrics.shape != (length, len(TRACE_FIELDS)):
        raise ValueError("invalid actual suffix boundary or metric trace")
    segment = slice(start, length)
    column = lambda name: metrics[segment, TRACE_FIELDS.index(name)]
    qos = column("qos_satisfaction_ratio")
    throughput = column("delivered_end_to_end_throughput_mbps")
    cost = column("return_constraint_cost")
    wait_age = np.asarray(trace["charging_wait_age"])[segment]
    eligible = np.asarray(trace["charging_eligible"])[segment]
    charged = np.asarray(trace["charger_input_wh"])[segment] > 0.0
    waiting = eligible & ~charged
    raw_margin = np.asarray(trace["station_raw_margin_selection"])[segment]
    station = detail["station"]
    opportunity = detail["recovery_opportunity"]
    wait_intervals = [row for row in station["waiting_intervals"] if start < length and row["stop"] > start]
    negative_intervals = [row for row in station["negative_wait_intervals"] if start < length and row["stop"] > start]
    recovery_intervals = [row for row in opportunity["intervals"] if start < length and
                          row["start_step"] < length and
                          (row["exit_step"] is None or row["exit_step"] >= start)]
    anchor = opportunity["first_qualifying_exit_anchor"]
    service_intervals = [row for row in detail["service_free_intervals"] if start < length and row["stop"] > start]
    return {
        "start": start, "actual_stop": length, "actual_steps": length - start,
        "native_J": float(rewards[segment].sum()),
        "cumulative_qos": float(qos.sum()),
        "actual_delivered_megabits": float(throughput.sum() * time_step_seconds),
        "native_return_cost": float(cost.sum()),
        "raw_negative_return_margin_uav_ticks": int((raw_margin < 0.0).sum()),
        "minimum_raw_pre_input_margin": float(raw_margin.min()) if raw_margin.size else None,
        "actual_waiting_uav_ticks": int(waiting.sum()),
        "actual_negative_waiting_uav_ticks": int((waiting & (raw_margin < 0.0)).sum()),
        "maximum_wait_age": int(wait_age.max()) if wait_age.size else 0,
        "wait_intervals_intersecting": len(wait_intervals),
        "wait_intervals_crossing_boundary": sum(row["start"] < start for row in wait_intervals),
        "negative_wait_intervals_intersecting": len(negative_intervals),
        "negative_wait_intervals_crossing_boundary": sum(row["start"] < start for row in negative_intervals),
        "recovery_intervals_intersecting": len(recovery_intervals),
        "recovery_intervals_crossing_boundary": sum(row["start_step"] < start for row in recovery_intervals),
        "qualifying_positive_gain_exits": sum(
            bool(row["qualifying_positive_gain_exit"]) and row["exit_step"] >= start
            for row in recovery_intervals),
        "first_recovery_anchor_step": None if anchor is None else int(anchor["anchor_step"]),
        "first_recovery_precedes_allocation_difference": (
            bool(anchor is not None and anchor["anchor_step"] < start)
            if allocation_difference_exists else None),
        "service_free_intervals_intersecting": len(service_intervals),
        "service_free_intervals_crossing_boundary": sum(row["start"] < start for row in service_intervals),
        "service_free_steps": int((qos <= 0.0).sum()),
    }
