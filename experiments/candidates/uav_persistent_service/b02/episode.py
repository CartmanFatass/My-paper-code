"""B02 horizon binding and terminal-safe readings over the retained native recorder."""

from __future__ import annotations

import hashlib
import time

import numpy as np

from experiments.candidates.energy_relay_availability.b05.runner import _rng_state_bytes
from experiments.candidates.energy_relay_availability.runner import _cpu_seconds, _rss_kib
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    TRACE_FIELDS, mechanism_row, position_diagnostics, world_row,
)
from experiments.candidates.uav_information_value.b02.readout import battery_reading
from experiments.candidates.uav_persistent_service.macro_env import NativeEpisode, longest_spell
from experiments.candidates.uav_persistent_service.mechanisms import commitment_readings


HORIZON = 12000
WINDOW = 3000
LATE_START = 6000
FINAL_START = 11700
QOS = TRACE_FIELDS.index("qos_satisfaction_ratio")


def rng_state_digest(raw) -> str:
    """Hash existing RNG state; no sample or state advancement."""
    return hashlib.sha256(_rng_state_bytes(raw)).hexdigest()


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
        observed = max(0, min(length, stop) - start)
        bins.append({"start": start, "stop": stop, "planned_steps": WINDOW,
                     "observed_steps": observed,
                     "native_J": float(rewards[start:stop].sum()),
                     "mission_qos": float(qos[start:stop].sum() / WINDOW),
                     "stock_change_wh": float((battery[min(stop, length)-1] -
                         (initial_battery if start == 0 else battery[start-1])).sum() * 160)
                         if observed else None})
    return {
        "terminal_step": length,
        "terminal_reason": "terminated" if ends[-1, 0] else "truncated",
        "unserved_remaining_mission_steps": horizon - length,
        "horizon_normalized_qos": float(qos.sum() / horizon),
        "late6000_mission_qos": float(qos[LATE_START:horizon].sum() / (horizon-LATE_START)),
        "late6000_native_J": float(rewards[LATE_START:horizon].sum()),
        "late6000_observed_steps": max(0, length-LATE_START),
        "bins": bins,
        "final300_persistent_reserve_members": (
            int(np.all(battery[FINAL_START:horizon] <= .10, axis=0).sum())
            if length == horizon else None),
        "final300_observed_steps": max(0, length-FINAL_START),
        "longest_zero_qos_spell": longest_spell(qos <= 0),
        "longest_below_half_qos_spell": longest_spell(qos < .5),
        "terminal_zero_service": bool(qos[-1] <= 0),
    }


def add_block_readings(row: dict, arrays: dict) -> None:
    cutoff = TRACE_FIELDS.index("cutoff_event_count")
    depletion = TRACE_FIELDS.index("depletion_event_count")
    for index, entry in enumerate(row["bins"]):
        start, stop = entry["start"], entry["stop"]
        observed = entry["observed_steps"]
        entry.update(
            gross_charger_input_wh=float(arrays["native_charger_input_wh"][start:stop].sum()),
            native_consumed_wh=float(arrays["native_consumed_wh"][start:stop].sum()),
            native_positive_net_charge_wh=float(
                arrays["native_positive_net_charge_wh"][start:stop].sum()),
            station_occupancy_uav_steps=int(arrays["native_station_occupancy"][start:stop].sum()),
            station_queue_steps=int(arrays["native_station_queue"][start:stop].sum()),
            wait_ticks_total=int((arrays["waiting_steps"][start:stop] > 0).sum()),
            cutoff_events=float(arrays["metrics"][start:stop, cutoff].sum()),
            depletion_events=float(arrays["metrics"][start:stop, depletion].sum()),
            observed_reserve_uav_step_fraction=(float(
                (arrays["native_battery"][start:stop] <= .10).mean())
                if observed else None),
        )
        for field, value in entry.items():
            if field not in ("start", "stop", "planned_steps"):
                row[f"block{index}_{field}"] = value


class LongMissionEpisode(NativeEpisode):
    """Retained P/O episode with B02-only horizon and read-only prefix witness."""

    def __init__(self, seed: int, arm: str):
        if arm not in ("O_H", "P"):
            raise ValueError("B02 arm must be O_H or P")
        super().__init__(seed, "O" if arm == "O_H" else "P", horizon=HORIZON)
        self.external_arm = arm
        self.rng_state_sha256_by_step = [rng_state_digest(self.env.env)]

    def prepare(self):
        # NativeEpisode calls prepare from its constructor after reset and before any action.
        self.controller.heuristic.layout = self.layout
        return super().prepare()

    def step_native(self):
        reward = super().step_native()
        self.rng_state_sha256_by_step.append(rng_state_digest(self.env.env))
        return reward

    def arrays(self):
        arrays = super().arrays()
        arrays["rng_state_sha256_by_step"] = np.asarray(self.rng_state_sha256_by_step,
                                                        dtype="U64")
        return arrays

    def row(self):
        if not self.done or not 0 < self.t <= self.horizon:
            raise RuntimeError("B02 reading requires a native terminal trajectory")
        arrays = self.arrays()
        if (len(arrays["reward"]) != self.t or len(arrays["user_xy_m"]) != self.t+1
                or len(arrays["rng_state_sha256_by_step"]) != self.t+1):
            raise ValueError("trajectory and exogenous witness lengths disagree")
        row = world_row(self.seed, arrays["reward"], arrays["metrics"], arrays["ends"],
                        arrays, time_step_s=float(self.config.time_step))
        row.update(mechanism_row(arrays, self.station_xy))
        row.update(position_diagnostics(arrays["metrics"], arrays,
                                        area_size_m=float(self.config.area_size),
                                        floor_m=float(self.config.height_range[0])))
        row.update(battery_reading(arrays["native_battery"]))
        row.update(fixed_window_readings(
            arrays["reward"], arrays["metrics"][:, QOS], arrays["native_battery"],
            arrays["ends"], self.initial_battery, horizon=self.horizon))
        add_block_readings(row, arrays)
        events = [] if self.arm == "P" else self.controller.events
        decisions = [] if self.arm == "P" else self.controller.diagnostics
        snapshot_calls = (self.controller.heuristic.service_snapshot_calls if self.arm == "P"
                          else self.controller.costs["service_snapshot_calls"])
        row.update(
            arm=self.external_arm, status="completed", effective_config=self.effective_config,
            **self.pairing.digests(), ground_bs_sha256=self.bs_sha256,
            net_stored_energy_wh=float((arrays["native_battery"][-1] - self.initial_battery).sum()*160),
            native_terminal_battery_ratios=[float(value) for value in arrays["native_battery"][-1]],
            native_terminal_battery_stock_wh=float(arrays["native_battery"][-1].sum()*160),
            gross_charger_input_wh=float(arrays["native_charger_input_wh"].sum()),
            native_consumed_wh=float(arrays["native_consumed_wh"].sum()),
            native_positive_net_charge_wh=float(arrays["native_positive_net_charge_wh"].sum()),
            native_charging_eligible_uav_steps=int(arrays["native_charging_eligible"].sum()),
            native_station_occupancy_uav_steps=int(arrays["native_station_occupancy"].sum()),
            native_station_queue_steps=int(arrays["native_station_queue"].sum()),
            actual_team_travel_m=float(np.linalg.norm(
                arrays["native_post_xyz"]-arrays["native_pre_xyz"], axis=2).sum()),
            service_snapshot_calls=int(snapshot_calls),
            macro_decisions=len(decisions),
            eligible_macro_decisions=sum(bool(item["eligible"]) for item in decisions),
            requested_dispatches=sum(item["requested_action"] > 0 for item in decisions),
            executed_dispatches=sum(item["executed_action"] > 0 for item in decisions),
            controller_costs=({"service_snapshot_calls": int(snapshot_calls)} if self.arm == "P"
                              else self.controller.costs),
            option_event_counts={kind: sum(event.get("kind") == kind for event in events)
                                 for kind in sorted({str(event.get("kind")) for event in events})},
            worker_wall_seconds=time.monotonic()-self.started,
            worker_cpu_seconds=_cpu_seconds()-self.cpu_started,
            worker_peak_rss_kib=_rss_kib(),
        )
        row.update(commitment_readings(arrays, events)[1])
        return row
