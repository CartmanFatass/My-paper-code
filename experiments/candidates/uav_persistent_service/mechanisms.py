"""Observed commitment execution, distinct from counterfactual causal attribution."""

import numpy as np


def first_true(values, start):
    indices = np.flatnonzero(values)
    return int(start + indices[0]) if len(indices) else None


def commitment_readings(arrays, events):
    if "commit_active" not in arrays:
        return [], {}
    horizon = len(arrays["reward"])
    movement = np.linalg.norm(arrays["native_post_xyz"]-arrays["native_pre_xyz"], axis=2)
    options = []
    starts = [(index, event) for index, event in enumerate(events) if event["kind"] == "start"]
    for event_index, event in starts:
        member, start = event["member"], event["step"]
        following = next(((index, e) for index, e in starts
                          if index > event_index and e["member"] == member), None)
        next_index = len(events) if following is None else following[0]
        next_start = horizon+1 if following is None else following[1]["step"]
        own_events = [e for e in events[event_index:next_index] if e.get("member") == member]
        terminal = next((e for e in own_events if e["kind"] in ("release", "censored")), None)
        stop = horizon if terminal is None else terminal["step"]
        active = slice(start, stop)
        arrival = next((e["step"] for e in own_events if e["kind"] == "arrival"), None)
        assigned = next((e["step"] for e in own_events if e["kind"] == "assignment_restored"), None)
        allocated = arrays["charging"][active, member].astype(bool)
        native_charge = arrays["native_charger_input_wh"][active, member]
        eligible = arrays["native_charging_eligible"][active, member].astype(bool)
        charge_interruptions = int(np.count_nonzero(allocated[:-1] & ~allocated[1:]))
        before = arrays["initial_native_battery"][member] if start == 0 else arrays["native_battery"][start-1, member]
        after = before if stop == start else arrays["native_battery"][stop-1, member]
        free_stop = min(next_start, horizon)
        release_range = slice(stop, free_stop)
        released = terminal is not None and terminal["kind"] == "release"
        free_command = (~arrays["mode"][release_range, member] &
                        (arrays["submitted"][release_range, member, 3] <= .5))
        actual_move = movement[release_range, member] > 1e-6
        load = arrays["native_load"][release_range, member] > 0
        options.append(dict(member=int(member), start=int(start), stop=int(stop),
            duration_label=int(event["duration"]), initial_station=int(event["station"]),
            first_geometric_arrival=arrival, assignment_restored=assigned,
            end_kind="partial" if terminal is None else terminal["kind"],
            release_reason=None if terminal is None else terminal.get("reason"),
            commanded_steps=int(stop-start), dwell_elapsed=None if arrival is None else int(stop-arrival),
            station_changes=sum(e["kind"] == "station_change" for e in own_events),
            allocated_charging_steps=int(allocated.sum()), native_eligible_wait_steps=int((eligible & ~allocated).sum()),
            charger_input_wh=float(native_charge.sum()), consumed_wh=float(arrays["native_consumed_wh"][active, member].sum()),
            positive_net_charging_wh=float(arrays["native_positive_net_charge_wh"][active, member].sum()),
            battery_change_wh=float((after-before)*160), charging_interruptions=charge_interruptions,
            real_f_steps=int(arrays["mode"][active, member].sum()),
            real_f_entries=int(arrays["entered"][active, member].sum()),
            actual_travel_m=float(movement[active, member].sum()),
            command_overwritten_steps=int(np.any(arrays["submitted"][active, member] != arrays["proposed"][active, member], axis=1).sum()),
            first_free_service_command=first_true(free_command, stop) if released else None,
            first_free_actual_move=first_true(free_command & actual_move, stop) if released else None,
            first_post_release_connected_load=first_true(load, stop) if released else None))
    aggregate = dict(
        commitment_count=len(options),
        commitment_arrivals=sum(row["first_geometric_arrival"] is not None for row in options),
        commitment_censored=sum(row["end_kind"] == "censored" for row in options),
        commitment_failed_arrivals=sum(row["release_reason"] == "timeout_no_arrival" for row in options),
        commitment_full_releases=sum(row["release_reason"] == "full" for row in options),
        commitment_dwell_releases=sum(row["release_reason"] == "dwell" for row in options),
        commitment_elapsed_below_shortest_label=sum(row["dwell_elapsed"] is not None and row["dwell_elapsed"] < 120 for row in options),
        commitment_any_charging=sum(row["allocated_charging_steps"] > 0 for row in options),
        commitment_assignment_restored=sum(row["assignment_restored"] is not None for row in options),
        commitment_free_move_after_release=sum(row["first_free_actual_move"] is not None for row in options),
        commitment_connected_load_after_release=sum(row["first_post_release_connected_load"] is not None for row in options),
    )
    for key in ("allocated_charging_steps", "native_eligible_wait_steps", "charger_input_wh",
                "positive_net_charging_wh", "battery_change_wh", "real_f_steps", "real_f_entries",
                "actual_travel_m", "command_overwritten_steps", "charging_interruptions"):
        aggregate[f"commitment_{key}"] = sum(row[key] for row in options)
    return options, aggregate
