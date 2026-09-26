"""Waiting and charging denominators for the B10 closed-loop traces."""

from __future__ import annotations

import numpy as np


def station_intervals(snapshots: list[dict], diagnostics: dict, *, terminal_type: str) -> dict:
    length = len(snapshots)
    charged = np.asarray(diagnostics["charger_input_wh"], dtype=float) > 0.0
    battery = np.asarray(diagnostics["physical_post_battery"], dtype=float)
    wait_age = np.asarray(diagnostics["charging_wait_age"], dtype=int)
    if charged.shape != battery.shape or charged.shape != wait_age.shape or charged.shape[0] != length:
        raise ValueError("station snapshot and energy trace lengths differ")
    members = charged.shape[1]
    station = np.full((length, members), -1, dtype=int)
    original = np.zeros((length, members), dtype=bool)
    actual = np.zeros((length, members), dtype=bool)
    for tick, snap in enumerate(snapshots):
        for key, candidates in snap["eligible_by_station"].items():
            station[tick, candidates] = int(key)
        for key, candidates in snap["original_selected"].items():
            original[tick, candidates] = True
        for key, candidates in snap["actual_selected"].items():
            actual[tick, candidates] = True
    eligible = station >= 0
    waiting = eligible & ~charged
    wait_rows = []
    spell_rows = []
    for member in range(members):
        start = None
        wait_station = -1
        for tick in range(length):
            if start is not None and station[tick, member] != wait_station:
                wait_rows.append({"member": member, "start": start, "stop": tick,
                                  "actual_wait_steps": tick - start,
                                  "end": "lost_eligibility_or_departed",
                                  "previous_station": wait_station,
                                  "next_station": int(station[tick, member]),
                                  "battery_min_during_wait": float(battery[start:tick, member].min())})
                start = None
            if waiting[tick, member] and start is None:
                start = tick
                wait_station = int(station[tick, member])
            if start is not None and (not waiting[tick, member]):
                gained = bool(charged[tick, member])
                wait_rows.append({"member": member, "start": start, "stop": tick,
                                  "actual_wait_steps": tick - start,
                                  "end": "actual_input" if gained else "lost_eligibility_or_departed",
                                  "previous_station": wait_station,
                                  "next_station": int(station[tick, member]),
                                  "battery_min_during_wait": float(battery[start:tick, member].min())})
                start = None
        if start is not None:
            wait_rows.append({"member": member, "start": start, "stop": length,
                              "actual_wait_steps": length - start,
                              "end": "observation_censored", "terminal_type": terminal_type,
                              "previous_station": wait_station,
                              "next_station": None,
                              "battery_min_during_wait": float(battery[start:length, member].min())})
        start = None
        active_station = -1
        for tick in range(length + 1):
            current_station = int(station[tick, member]) if tick < length and charged[tick, member] else -1
            if start is not None and current_station != active_station:
                if tick == length:
                    ending = "observation_censored"
                elif (int(snapshots[tick]["current_target_station"][member]) >= 0
                      and int(snapshots[tick]["current_target_station"][member]) != active_station):
                    ending = "station_changed"
                elif station[tick, member] < 0:
                    ending = "ineligible"
                elif station[tick, member] != active_station:
                    ending = "station_changed"
                elif actual[tick, member]:
                    ending = "selected_without_positive_input"
                else:
                    ending = "rule_replacement"
                spell_rows.append({"member": member, "station": active_station,
                                   "start": start, "stop": tick, "actual_input_steps": tick - start,
                                   "end": ending, "terminal_type": terminal_type if tick == length else None,
                                   "input_wh": float(np.asarray(diagnostics["charger_input_wh"])[start:tick, member].sum()),
                                   "signed_stored_wh": float(np.asarray(diagnostics["signed_stored_energy_delta_wh"])[start:tick, member].sum())})
                start = None
            if current_station >= 0 and start is None:
                start, active_station = tick, current_station
    waiting_battery = battery[waiting]
    waiting_ages = wait_age[waiting]
    first_input = [int(np.flatnonzero(charged[:, member])[0]) if charged[:, member].any() else None
                   for member in range(members)]
    incumbent_replacements = 0
    differing_local_sorts = 0
    for tick, snap in enumerate(snapshots):
        if any(set(snap["actual_selected"][key]) != set(snap["original_selected"][key])
               for key in snap["eligible_by_station"]):
            differing_local_sorts += 1
        for key, candidates in snap["eligible_by_station"].items():
            incumbent_replacements += sum(
                snap["prior_actual_station"][member] == int(key)
                for member in candidates if member not in snap["actual_selected"][key]
            )
    return {
        "waiting_intervals": wait_rows,
        "charging_spells": spell_rows,
        "waiting_eligible_uav_ticks": int(waiting.sum()),
        "waiting_steps_by_member": waiting.sum(axis=0).astype(int).tolist(),
        "waiting_min_battery": float(waiting_battery.min()) if waiting_battery.size else None,
        "waiting_battery_p10": float(np.quantile(waiting_battery, .1)) if waiting_battery.size else None,
        "waiting_battery_p50": float(np.median(waiting_battery)) if waiting_battery.size else None,
        "waiting_age_p95_tick_weighted": float(np.quantile(waiting_ages, .95)) if waiting_ages.size else None,
        "first_actual_input_step_by_member": first_input,
        "eligible_never_charged_members": [member for member in range(members)
                                           if eligible[:, member].any() and first_input[member] is None],
        "wait_interval_end_counts": {name: sum(row["end"] == name for row in wait_rows)
                                     for name in ("actual_input", "lost_eligibility_or_departed", "observation_censored")},
        "charging_spell_end_counts": {name: sum(row["end"] == name for row in spell_rows)
                                      for name in ("ineligible", "station_changed", "rule_replacement", "selected_without_positive_input", "observation_censored")},
        "same_station_eligible_incumbent_replacements": int(incumbent_replacements),
        "ticks_where_C_differs_from_local_original_sort": int(differing_local_sorts),
    }


def aggregate_station_summaries(rows: list[dict]) -> dict:
    station = [row["station"] for row in rows]
    wait_names = ("actual_input", "lost_eligibility_or_departed", "observation_censored")
    spell_names = ("ineligible", "station_changed", "rule_replacement",
                   "selected_without_positive_input", "observation_censored")
    batteries = [row["waiting_min_battery"] for row in station
                 if row["waiting_min_battery"] is not None]
    return {
        "worlds": len(rows),
        "waiting_eligible_uav_ticks": sum(row["waiting_eligible_uav_ticks"] for row in station),
        "eligible_never_charged_members": sum(len(row["eligible_never_charged_members"]) for row in station),
        "lowest_waiting_battery": min(batteries) if batteries else None,
        "same_station_eligible_incumbent_replacements": sum(
            row["same_station_eligible_incumbent_replacements"] for row in station),
        "ticks_where_C_differs_from_local_original_sort": sum(
            row["ticks_where_C_differs_from_local_original_sort"] for row in station),
        "wait_interval_end_counts": {key: sum(row["wait_interval_end_counts"][key] for row in station)
                                     for key in wait_names},
        "charging_spell_end_counts": {key: sum(row["charging_spell_end_counts"][key] for row in station)
                                      for key in spell_names},
    }
