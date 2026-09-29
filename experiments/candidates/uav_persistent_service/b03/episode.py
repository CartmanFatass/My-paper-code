"""B03 finite native episode and raw evidence, including early native endings."""

from __future__ import annotations

import hashlib
import time

import numpy as np

from experiments.candidates.energy_relay_availability.b05.runner import _rng_state_bytes
from experiments.candidates.energy_relay_availability.runner import _cpu_seconds, _rss_kib, _sha256, _write_json
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    TRACE_FIELDS, mechanism_row, position_diagnostics, world_row,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import station_records
from experiments.candidates.uav_information_value.b02.readout import battery_reading
from experiments.candidates.uav_persistent_service.macro_env import NativeEpisode
from experiments.candidates.uav_persistent_service.mechanisms import commitment_readings

from .controller import ReassignmentController, TRANSFER_BASE


HORIZON = 12000
WINDOW = 3000
QOS = TRACE_FIELDS.index("qos_satisfaction_ratio")


def rng_state_digest(raw):
    return hashlib.sha256(_rng_state_bytes(raw)).hexdigest()


def longest_spell(mask):
    mask = np.asarray(mask, dtype=bool)
    edges = np.diff(np.r_[False, mask, False].astype(np.int8))
    return int(max((end-start for start, end in zip(np.flatnonzero(edges == 1),
                                                     np.flatnonzero(edges == -1))), default=0))


def fixed_window_readings(rewards, qos, battery, ends, initial_battery, *, horizon=HORIZON):
    rewards = np.asarray(rewards, dtype=np.float64)
    qos = np.asarray(qos, dtype=np.float64)
    battery = np.asarray(battery, dtype=np.float64)
    ends = np.asarray(ends, dtype=bool)
    length = len(rewards)
    if (not 0 < length <= horizon or horizon % WINDOW or qos.shape != (length,)
            or battery.shape != (length, 8) or ends.shape != (length, 2)
            or not ends[-1].any() or not np.isfinite(rewards).all()
            or not np.isfinite(qos).all() or not np.isfinite(battery).all()):
        raise ValueError("expected an actual finite native terminal trajectory")
    bins = []
    for start in range(0, horizon, WINDOW):
        stop = start + WINDOW
        observed = max(0, min(length, stop)-start)
        bins.append({"start": start, "stop": stop, "planned_steps": WINDOW,
                     "observed_steps": observed, "native_J": float(rewards[start:stop].sum()),
                     "mission_qos": float(qos[start:stop].sum()/WINDOW),
                     "stock_change_wh": (float((battery[min(stop, length)-1] -
                         (initial_battery if start == 0 else battery[start-1])).sum()*160)
                         if observed else None)})
    return {"terminal_step": length,
            "terminal_reason": "terminated" if ends[-1, 0] else "truncated",
            "unserved_remaining_mission_steps": horizon-length,
            "horizon_normalized_qos": float(qos.sum()/horizon),
            "late6000_mission_qos": float(qos[6000:horizon].sum()/6000),
            "late6000_native_J": float(rewards[6000:horizon].sum()),
            "late6000_observed_steps": max(0, length-6000),
            "bins": bins,
            "final300_persistent_reserve_members": (
                int(np.all(battery[11700:horizon] <= .10, axis=0).sum()) if length == horizon else None),
            "final300_observed_steps": max(0, length-11700),
            "longest_zero_qos_spell": longest_spell(qos <= 0),
            "longest_below_half_qos_spell": longest_spell(qos < .5),
            "terminal_zero_service": bool(qos[-1] <= 0)}


def block_readings(row, arrays):
    cutoff = TRACE_FIELDS.index("cutoff_event_count")
    depletion = TRACE_FIELDS.index("depletion_event_count")
    for index, entry in enumerate(row["bins"]):
        start, stop = entry["start"], entry["stop"]
        observed = entry["observed_steps"]
        entry.update(
            gross_charger_input_wh=float(arrays["native_charger_input_wh"][start:stop].sum()),
            native_consumed_wh=float(arrays["native_consumed_wh"][start:stop].sum()),
            native_positive_net_charge_wh=float(arrays["native_positive_net_charge_wh"][start:stop].sum()),
            station_occupancy_uav_steps=int(arrays["native_station_occupancy"][start:stop].sum()),
            station_queue_steps=int(arrays["native_station_queue"][start:stop].sum()),
            wait_ticks_total=int((arrays["waiting_steps"][start:stop] > 0).sum()),
            cutoff_events=float(arrays["metrics"][start:stop, cutoff].sum()),
            depletion_events=float(arrays["metrics"][start:stop, depletion].sum()),
            observed_reserve_uav_step_fraction=(
                float((arrays["native_battery"][start:stop] <= .10).mean()) if observed else None),
        )
        for field, value in entry.items():
            if field not in ("start", "stop", "planned_steps"):
                row[f"block{index}_{field}"] = value


def station_load_readings(row, arrays):
    eligible = arrays["native_eligible_station_count"]
    demand = arrays["native_eligible_station_demand_w"]
    charge = arrays["native_station_input_wh"]
    stock = arrays["native_station_stock_wh"]
    capacity = arrays["legal_station_capacity_w"]
    overload = demand > capacity
    for station in range(2):
        prefix = f"station{station}_"
        row[prefix+"eligible_uav_steps"] = int(eligible[:, station].sum())
        row[prefix+"eligible_demand_wh"] = float(demand[:, station].sum()/3600)
        row[prefix+"charger_input_wh"] = float(charge[:, station].sum())
        row[prefix+"overload_ticks"] = int(overload[:, station].sum())
        row[prefix+"longest_overload_spell"] = longest_spell(overload[:, station])
        final = slice(9000, 12000)
        final_observed = max(0, min(len(demand), 12000)-9000)
        row[prefix+"final3000_observed_steps"] = final_observed
        row[prefix+"final3000_mean_demand_w"] = (
            float(demand[final, station].mean()) if final_observed else None)
        row[prefix+"final3000_input_wh"] = float(charge[final, station].sum())
        row[prefix+"final3000_mean_stock_wh"] = (
            float(stock[final, station].mean()) if final_observed else None)
        row[prefix+"terminal_stock_wh"] = float(stock[-1, station])
    row["station_overload_ticks_any"] = int(overload.any(axis=1).sum())
    row["station_overload_longest_spell_any"] = longest_spell(overload.any(axis=1))


def transfer_readings(arrays, events):
    transfers = []
    xyz = arrays["native_post_xyz"]
    nearest = arrays["nearest_station"]
    for event_index, event in enumerate(events):
        if event.get("kind") != "start" or event.get("option_type") != "transfer":
            continue
        member, start, station = event["member"], event["step"], event["station"]
        next_start_index = next((index for index in range(event_index+1, len(events))
                                 if events[index].get("member") == member
                                 and events[index].get("kind") == "start"), len(events))
        own_events = [other for other in events[event_index+1:next_start_index]
                      if other.get("member") == member]
        next_start_step = (events[next_start_index]["step"] if next_start_index < len(events)
                           else len(xyz))
        terminal = next((other for other in own_events
                         if other.get("option_type") == "transfer"
                         and other.get("kind") in ("release", "censored")), None)
        stop = min(len(xyz), next_start_step,
                   terminal["step"] if terminal else len(xyz))
        active = slice(start, stop)
        arrival = next((other["step"] for other in own_events
                        if other.get("option_type") == "transfer"
                        and other.get("kind") == "arrival"
                        and other["step"] <= stop), None)
        origin = int(nearest[start, member]) if start < len(xyz) else None
        free_end = min(len(xyz), next_start_step)
        released = terminal is not None and terminal["kind"] == "release"
        restored = (next((other["step"] for other in own_events
                          if other.get("member") == member
                          and other.get("kind") == "assignment_restored"
                          and stop <= other["step"] < free_end), None) if released else None)
        free = slice(stop, free_end)
        free_command = (~arrays["mode"][free, member]
                        & (arrays["submitted"][free, member, 3] <= .5)
                        & ~arrays["commit_active"][free, member])
        recovered_load = (bool(np.any(free_command & (arrays["native_load"][free, member] > 0)))
                          if released else False)
        transfers.append({"member": member, "start": start, "stop": stop,
                          "origin": origin, "intended_station": station,
                          "crossed": bool(np.any(arrays["native_post_nearest_station"][active, member] == station)),
                          "first_decoded_arrival": arrival,
                          "charging_steps": int(arrays["charging"][active, member].sum()),
                          "charger_input_wh": float(arrays["native_charger_input_wh"][active, member].sum()),
                          "real_f_steps": int(arrays["mode"][active, member].sum()),
                          "f_overwritten_steps": int(np.any(
                              arrays["submitted"][active, member] != arrays["proposed"][active, member],
                              axis=1).sum()),
                          "actual_travel_m": float(np.linalg.norm(
                              xyz[active, member]-arrays["native_pre_xyz"][active, member], axis=1).sum()),
                          "release_reason": None if terminal is None else terminal.get("reason"),
                          "end_kind": "partial" if terminal is None else terminal["kind"],
                          "assignment_restored": restored,
                          "free_followup_stop": free_end,
                          "post_release_connected_load": recovered_load})
    return transfers


class LongMissionEpisode(NativeEpisode):
    def __init__(self, seed: int, arm: str):
        if arm not in ("P", "O_H", "R"):
            raise ValueError("B03 arm must be P, O_H or R")
        self.external_arm = arm
        factory = (lambda env, config: ReassignmentController(env, config)) if arm == "R" else None
        super().__init__(seed, "P" if arm == "P" else "O", horizon=HORIZON,
                         controller_factory=factory)
        self.rng_state_sha256_by_step = [rng_state_digest(self.env.env)]
        for key in ("station_xyz", "legal_station_capacity_w", "native_station_request",
                    "native_station_target", "native_post_nearest_station",
                    "native_eligible_station_count", "native_eligible_station_demand_w",
                    "native_station_input_wh", "native_station_stock_wh"):
            self.data[key] = []

    def prepare(self):
        self.controller.heuristic.layout = self.layout
        return super().prepare()

    def step_native(self):
        records = station_records(self.observations, self.layout)
        stations = records["xyz_m"][0].copy()
        capacities = records["capacity_ratio"][0].astype(np.float64)*8*1000.0
        reward = super().step_native()
        self.rng_state_sha256_by_step.append(rng_state_digest(self.env.env))
        post = self.data["native_post_xyz"][-1]
        native_stations = self.env.env.charging_station_positions[:2].copy()
        post_nearest = np.linalg.norm(
            post[:, None, :]-native_stations[None, :, :], axis=2).argmin(axis=1)
        request = self.env.env.uav_dock_requests.copy()
        target = self.env.env.uav_target_stations.copy()
        eligible = self.data["native_charging_eligible"][-1]
        consumed = self.data["native_consumed_wh"][-1]
        charged = self.data["native_charger_input_wh"][-1]
        if np.any(eligible & ((target < 0) | (target >= 2))):
            raise ValueError("native eligible member lacks a legal target station")
        self.data["station_xyz"].append(stations)
        self.data["legal_station_capacity_w"].append(capacities)
        self.data["native_station_request"].append(request)
        self.data["native_station_target"].append(target)
        self.data["native_post_nearest_station"].append(post_nearest)
        self.data["native_eligible_station_count"].append(
            np.bincount(target[eligible], minlength=2))
        self.data["native_eligible_station_demand_w"].append(
            np.bincount(target[eligible], weights=consumed[eligible]*3600.0,
                        minlength=2))
        self.data["native_station_input_wh"].append(
            np.bincount(target[charged > 0], weights=charged[charged > 0], minlength=2))
        self.data["native_station_stock_wh"].append(
            np.bincount(post_nearest, weights=self.data["native_battery"][-1]*160,
                        minlength=2))
        return reward

    def arrays(self):
        arrays = super().arrays()
        arrays["rng_state_sha256_by_step"] = np.asarray(self.rng_state_sha256_by_step, dtype="U64")
        return arrays

    def row(self):
        if not self.done or not 0 < self.t <= self.horizon:
            raise RuntimeError("B03 reading requires a native terminal trajectory")
        arrays = self.arrays()
        if (len(arrays["reward"]) != self.t or len(arrays["user_xy_m"]) != self.t+1
                or len(arrays["rng_state_sha256_by_step"]) != self.t+1):
            raise ValueError("trajectory and exogenous witness lengths disagree")
        row = world_row(self.seed, arrays["reward"], arrays["metrics"], arrays["ends"], arrays,
                        time_step_s=float(self.config.time_step))
        row.update(mechanism_row(arrays, self.station_xy))
        row.update(position_diagnostics(arrays["metrics"], arrays,
                                        area_size_m=float(self.config.area_size),
                                        floor_m=float(self.config.height_range[0])))
        row.update(battery_reading(arrays["native_battery"]))
        row.update(fixed_window_readings(arrays["reward"], arrays["metrics"][:, QOS],
                                         arrays["native_battery"], arrays["ends"],
                                         self.initial_battery))
        block_readings(row, arrays)
        station_load_readings(row, arrays)
        events = [] if self.arm == "P" else self.controller.events
        decisions = [] if self.arm == "P" else self.controller.diagnostics
        snapshot_calls = self.controller.heuristic.service_snapshot_calls
        transfers = transfer_readings(arrays, events) if self.external_arm == "R" else []
        row.update(arm=self.external_arm, status="completed", effective_config=self.effective_config,
                   **self.pairing.digests(), ground_bs_sha256=self.bs_sha256,
                   net_stored_energy_wh=float((arrays["native_battery"][-1]-self.initial_battery).sum()*160),
                   native_terminal_battery_ratios=arrays["native_battery"][-1].tolist(),
                   native_terminal_battery_stock_wh=float(arrays["native_battery"][-1].sum()*160),
                   gross_charger_input_wh=float(arrays["native_charger_input_wh"].sum()),
                   native_consumed_wh=float(arrays["native_consumed_wh"].sum()),
                   native_positive_net_charge_wh=float(arrays["native_positive_net_charge_wh"].sum()),
                   native_charging_eligible_uav_steps=int(arrays["native_charging_eligible"].sum()),
                   native_station_occupancy_uav_steps=int(arrays["native_station_occupancy"].sum()),
                   native_station_queue_steps=int(arrays["native_station_queue"].sum()),
                   actual_team_travel_m=float(np.linalg.norm(
                       arrays["native_post_xyz"]-arrays["native_pre_xyz"], axis=2).sum()),
                   service_snapshot_calls=int(snapshot_calls), macro_decisions=len(decisions),
                   eligible_macro_decisions=sum(bool(item["eligible"]) for item in decisions),
                   requested_dispatches=sum(item["requested_action"] > 0 for item in decisions),
                   executed_dispatches=sum(item["executed_action"] > 0 for item in decisions),
                   requested_transfers=sum(item["requested_action"] >= TRANSFER_BASE for item in decisions),
                   executed_transfers=sum(item["executed_action"] >= TRANSFER_BASE for item in decisions),
                   controller_costs=({"service_snapshot_calls": int(snapshot_calls)} if self.arm == "P"
                                     else self.controller.costs),
                   option_event_counts={kind: sum(event.get("kind") == kind for event in events)
                                        for kind in sorted({event.get("kind") for event in events})},
                   transfer_count=len(transfers), transfer_crossings=sum(t["crossed"] for t in transfers),
                   transfer_arrivals=sum(t["first_decoded_arrival"] is not None for t in transfers),
                   transfer_charge_count=sum(t["charger_input_wh"] > 0 for t in transfers),
                   transfer_release_count=sum(t["end_kind"] == "release" for t in transfers),
                   transfer_service_recovery_count=sum(t["post_release_connected_load"] for t in transfers),
                   transfer_f_other_station_count=sum(t["release_reason"] == "f_other_station" for t in transfers),
                   transfer_f_overwritten_steps=sum(t["f_overwritten_steps"] for t in transfers),
                   feasibility_rejections={key: sum(d.get("feasibility_rejections", {}).get(key, 0)
                                                    for d in decisions) for key in sorted({key for d in decisions
                                                    for key in d.get("feasibility_rejections", {})})},
                   worker_wall_seconds=time.monotonic()-self.started,
                   worker_cpu_seconds=_cpu_seconds()-self.cpu_started,
                   worker_peak_rss_kib=_rss_kib())
        row.update(commitment_readings(arrays, events)[1])
        return row

    def save(self, path, *, complete):
        from pathlib import Path
        path = Path(path)
        if path.exists():
            raise FileExistsError(path)
        arrays = self.arrays()
        np.savez_compressed(path, **arrays)
        decisions = path.with_suffix(".decisions.json")
        events = [] if self.arm == "P" else self.controller.events
        _write_json(decisions, {"complete": complete, "macros": self.macros,
                                "events": events,
                                "commitments": commitment_readings(arrays, events)[0],
                                "transfers": transfer_readings(arrays, events),
                                "controller_costs": {} if self.arm == "P" else self.controller.costs})
        return {"raw_path": str(path), "raw_sha256": _sha256(path), "raw_bytes": path.stat().st_size,
                "decisions_path": str(decisions), "decisions_sha256": _sha256(decisions)}
