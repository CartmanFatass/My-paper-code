"""Arithmetic 30-second forecast from the current legal controller snapshot."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from experiments.candidates.uav_persistent_service.controllers import (
    BATTERY_WH, CAPTURE_RADIUS_M, HOVER_W, TIMEOUT, _restoration_time,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    DOCKING_RADIUS_M, HORIZONTAL_SPEED_MPS, VERTICAL_SPEED_MPS,
)

BIN_SECONDS = 30
HORIZON = 1200


@dataclass(frozen=True)
class ForecastOption:
    member: int
    station: int
    duration: int
    age: int
    arrival_age: int | None
    observed_charging_without_arrival: bool = False
    transfer: bool = False


@dataclass(frozen=True)
class ForecastInput:
    xyz: np.ndarray
    stations: np.ndarray
    targets_xy: np.ndarray
    battery: np.ndarray
    available: np.ndarray
    modes: np.ndarray
    charging: np.ndarray
    waiting: np.ndarray
    draw_w: np.ndarray
    slots: np.ndarray
    weights: np.ndarray
    q0: float
    options: tuple[ForecastOption, ...]
    remaining: int
    limp_power_w: float
    max_power_w: float
    reserve_ratio: float = .10
    cutoff_ratio: float = .02
    emergency_ratio: float = .05


def _capture_point(start: np.ndarray, station: np.ndarray) -> np.ndarray:
    vector = station - start
    distance = float(np.linalg.norm(vector))
    if distance <= CAPTURE_RADIUS_M:
        return start.copy()
    return start + vector * ((distance-CAPTURE_RADIUS_M)/distance)


def _margin(battery: np.ndarray, xyz: np.ndarray, stations: np.ndarray,
            limp_power_w: float, reserve_ratio: float) -> np.ndarray:
    distance = np.linalg.norm(xyz[:, None, :] - stations[None, :, :], axis=2).min(axis=1)
    return battery - reserve_ratio - distance/3.0*limp_power_w/(BATTERY_WH*3600.0)


def _advance(start: np.ndarray, end: np.ndarray, seconds: float, duration: float) -> np.ndarray:
    if duration <= 0:
        return end.copy()
    return start + (end-start)*min(1.0, seconds/duration)


def _station_advance(start: np.ndarray, station: np.ndarray, seconds: float,
                     limp: bool) -> tuple[np.ndarray, bool]:
    vector = station-start
    distance = float(np.linalg.norm(vector))
    if distance <= CAPTURE_RADIUS_M:
        return start.copy(), True
    direction = vector/distance
    horizontal = float(np.linalg.norm(direction[:2]))
    vertical = abs(float(direction[2]))
    outer = max(0.0, distance-DOCKING_RADIUS_M)
    inner = min(distance, DOCKING_RADIUS_M)-CAPTURE_RADIUS_M
    outer_seconds_per_m = (1.0/3.0 if limp else
                           max(horizontal/HORIZONTAL_SPEED_MPS,
                               vertical/VERTICAL_SPEED_MPS))
    inner_seconds_per_m = max(horizontal/3.0, vertical/1.0)
    outer_done = min(outer, seconds/outer_seconds_per_m)
    inner_done = min(inner, max(0.0, seconds-outer_done*outer_seconds_per_m)/inner_seconds_per_m)
    progress = outer_done+inner_done
    return start+direction*progress, progress >= distance-CAPTURE_RADIUS_M-1e-9


def forecast(view: ForecastInput, candidate: ForecastOption | None) -> dict:
    """One current choice, with no further voluntary starts or environment calls."""
    n_bins = int(math.ceil(min(HORIZON, view.remaining)/BIN_SECONDS))
    if n_bins <= 0:
        raise ValueError("forecast needs positive remaining time")
    xyz = np.asarray(view.xyz, dtype=float).copy()
    stations = np.asarray(view.stations, dtype=float)
    targets = np.asarray(view.targets_xy, dtype=float)
    battery = np.asarray(view.battery, dtype=float).copy()
    waiting = np.asarray(view.waiting, dtype=float).copy()
    draw = np.maximum(HOVER_W, np.asarray(view.draw_w, dtype=float))
    slots = np.asarray(view.slots, dtype=int)
    weights = np.asarray(view.weights, dtype=float)
    active = {o.member: o for o in view.options}
    if candidate is not None:
        active[candidate.member] = candidate
    modes = np.asarray(view.modes, dtype=bool).copy()
    charging_now = np.asarray(view.charging, dtype=bool)
    failed = ~np.asarray(view.available, dtype=bool) & (battery > view.cutoff_ratio)
    phase = np.zeros(8, dtype=np.int8)  # 0 deployed, 1 inbound, 2 docked, 3 outbound
    intended = np.full(8, -1, dtype=int)
    arrival = np.full(8, np.nan)
    age = np.zeros(8, dtype=float)
    dwell = np.zeros(8, dtype=float)
    travel = np.zeros(8, dtype=float)
    release = np.full(8, np.nan)
    readiness = np.full(8, np.nan)
    no_arrival = np.zeros(8, dtype=bool)
    for member, option in active.items():
        intended[member] = option.station
        age[member] = option.age
        dwell[member] = option.duration
        no_arrival[member] = option.observed_charging_without_arrival
        if option.arrival_age is not None:
            arrival[member] = option.arrival_age
        if option.arrival_age is not None:
            phase[member] = 2
        elif no_arrival[member]:
            phase[member] = 2
        else:
            phase[member] = 1
    for member in np.flatnonzero(modes & (phase == 0)):
        intended[member] = int(np.linalg.norm(stations-xyz[member], axis=1).argmin())
        at_capture = np.linalg.norm(stations[intended[member]]-xyz[member]) <= CAPTURE_RADIUS_M
        phase[member] = 2 if charging_now[member] or waiting[member] > 0 or at_capture else 1
    cutoff_ticks = depletion_ticks = reserve_ticks = 0
    q_values: list[float] = []
    battery_min: list[float] = []
    member_bin_updates = 0
    for bin_index in range(n_bins):
        elapsed = min(BIN_SECONDS, view.remaining-bin_index*BIN_SECONDS)
        now = bin_index*BIN_SECONDS + elapsed
        # Return margins are recomputed at each coarse point; F takes the native nearest station.
        margin = _margin(battery, xyz, stations, view.limp_power_w, view.reserve_ratio)
        modes[margin <= 0.0] = True
        modes[margin >= .05] = False
        for member in range(8):
            if failed[member]:
                continue
            motion_disabled = battery[member] <= 0.0
            limp = 0.0 < battery[member] <= view.emergency_ratio
            if modes[member] or limp:
                nearest = int(np.linalg.norm(stations-xyz[member], axis=1).argmin())
                option = active.get(member)
                if modes[member] and option is not None and option.transfer and nearest != intended[member]:
                    release[member] = bin_index*BIN_SECONDS
                    del active[member]
                intended[member] = nearest
                if phase[member] != 2:
                    phase[member] = 1
            starting_phase = phase[member]
            if motion_disabled:
                pass
            elif phase[member] == 0:
                target = np.r_[targets[member], 100.0]
                if np.isfinite(target).all():
                    trip = _restoration_time(xyz[member], targets[member])
                    xyz[member] = _advance(xyz[member], target, elapsed, trip)
            elif phase[member] == 1:
                station = stations[intended[member]]
                xyz[member], arrived = _station_advance(xyz[member], station, elapsed, limp)
                if arrived and not no_arrival[member]:
                    phase[member] = 2
                    if np.isnan(arrival[member]):
                        arrival[member] = age[member] + elapsed
            elif phase[member] == 3:
                target = np.r_[targets[member], 100.0]
                if np.isfinite(target).all():
                    trip = _restoration_time(xyz[member], targets[member])
                    xyz[member] = _advance(xyz[member], target, elapsed, trip)
                    travel[member] += elapsed
                    if trip <= elapsed:
                        phase[member] = 0
                        readiness[member] = now
            power = (HOVER_W if motion_disabled or starting_phase == 2 else
                     view.limp_power_w if limp and starting_phase == 1 else
                     view.max_power_w if starting_phase in (1, 3) else draw[member])
            battery[member] -= power*elapsed/(BATTERY_WH*3600.0)
            member_bin_updates += 1
        # Native ranks candidates after consumption; wait is in elapsed seconds here.
        for station in range(len(stations)):
            eligible = [i for i in range(8) if not failed[i] and phase[i] == 2
                        and intended[i] == station]
            selected = sorted(eligible, key=lambda i: (battery[i], -waiting[i], i))[:slots[station]]
            for member in eligible:
                if member in selected:
                    battery[member] = min(1.0, battery[member]+1000.0*elapsed/(BATTERY_WH*3600.0))
                    waiting[member] = 0
                else:
                    waiting[member] += elapsed
        waiting[(phase != 2) | failed] = 0
        battery = np.clip(battery, 0.0, 1.0)
        for member in range(8):
            option = active.get(member)
            if option is None or not np.isnan(release[member]):
                continue
            age[member] += elapsed
            full = battery[member] >= 1.0
            timeout = age[member] >= TIMEOUT
            dwell_done = np.isfinite(arrival[member]) and age[member]-arrival[member] >= dwell[member]
            if full or timeout or dwell_done:
                release[member] = now
                if phase[member] in (1, 2) and not modes[member]:
                    phase[member] = 3
                del active[member]
        # F can continue after a voluntary option releases; ready means useful deployment.
        margin = _margin(battery, xyz, stations, view.limp_power_w, view.reserve_ratio)
        modes[margin <= 0.0] = True
        modes[margin >= .05] = False
        for member in range(8):
            if phase[member] in (1, 2) and member not in active and not modes[member]:
                phase[member] = 3
            if phase[member] == 0 and modes[member]:
                phase[member] = 1
                intended[member] = int(np.linalg.norm(stations-xyz[member], axis=1).argmin())
        unready = (phase != 0) | modes | failed | (battery <= view.cutoff_ratio)
        q_values.append(float(np.clip(view.q0-np.dot(weights, unready.astype(float)), 0.0, 1.0)))
        battery_min.append(float(battery.min()))
        cutoff_ticks += int(np.count_nonzero(battery <= view.cutoff_ratio))
        depletion_ticks += int(np.count_nonzero(battery <= 0.0))
        reserve_ticks += int(np.count_nonzero(battery <= view.reserve_ratio))
    return {
        "cutoff_ticks": cutoff_ticks, "depletion_ticks": depletion_ticks,
        "min_qhat": min(q_values), "integral_qhat": float(sum(q_values)*BIN_SECONDS),
        "reserve_ticks": reserve_ticks, "qhat": q_values, "battery_min": battery_min,
        "release": [None if np.isnan(x) else float(x) for x in release],
        "readiness": [None if np.isnan(x) else float(x) for x in readiness],
        "battery_end": battery.tolist(),
        "grid_bins": n_bins, "member_bin_updates": member_bin_updates,
    }
