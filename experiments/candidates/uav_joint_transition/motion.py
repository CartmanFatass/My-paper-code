"""Legal-observation, joint nominal motion model for thirty-step path choices.

This predicts control, energy and station allocation. It deliberately does not
predict the native guard, radio association, users, or reward transitions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT, own_energy, own_positions, station_records,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    HORIZONTAL_SPEED_MPS, PRODUCTION_PARAMS, VERTICAL_SPEED_MPS,
)


N_UAVS = 8
N_MODES = 4
HORIZON = 30
SAMPLES = (10, 20, 30)
MODE_NAMES = ("D", "W", "B+", "B-")


@dataclass(frozen=True)
class Forecast:
    xyz: np.ndarray                 # [3, 8, 3], metres
    battery: np.ndarray             # [3, 8], ratio
    margin: np.ndarray              # [3, 8], ratio
    F: np.ndarray                   # [3, 8]
    waits: np.ndarray               # [3, 8], ticks
    cancelled: np.ndarray           # [8]
    crossed_F: np.ndarray           # [8]
    crossed_reserve: np.ndarray     # [8]
    crossed_cutoff: np.ndarray      # [8]
    travel_m: float


def waypoints(start_xyz: np.ndarray, targets_xyz: np.ndarray) -> np.ndarray:
    """The two clipped, clock-fixed intermediate targets, shape [2, 8, 3]."""
    start = np.asarray(start_xyz, dtype=np.float64)
    target = np.asarray(targets_xyz, dtype=np.float64)
    delta = target[:, :2] - start[:, :2]
    norm = np.linalg.norm(delta, axis=1)
    normal = np.zeros_like(delta)
    normal[:, 1] = 1.0
    moving = norm > 0.0
    normal[moving, 0] = -delta[moving, 1] / norm[moving]
    normal[moving, 1] = delta[moving, 0] / norm[moving]
    middle = (start + target) / 2.0
    result = np.stack((middle.copy(), middle.copy()))
    result[0, :, :2] += 150.0 * normal
    result[1, :, :2] -= 150.0 * normal
    result[:, :, :2] = np.clip(result[:, :, :2], 0.0, S7S2_LAYOUT.area_size_m)
    result[:, :, 2] = np.clip(result[:, :, 2], S7S2_LAYOUT.height_min_m,
                             S7S2_LAYOUT.height_max_m)
    return result


def toward(current: np.ndarray, target: np.ndarray, *, horizontal: float = 30.0,
           vertical: float = 5.0, dt: float = 1.0) -> np.ndarray:
    """R's capped velocity rule in physical units, for a finite target."""
    delta = np.asarray(target, dtype=np.float64) - np.asarray(current, dtype=np.float64)
    speed_xy = np.linalg.norm(delta[..., :2], axis=-1)
    factor = np.minimum(1.0, horizontal * dt / np.maximum(speed_xy, 1e-12))
    velocity = np.empty_like(delta)
    velocity[..., :2] = delta[..., :2] * factor[..., None] / dt
    velocity[..., 2] = np.clip(delta[..., 2] / dt, -vertical, vertical)
    return velocity


def proposal(current: np.ndarray, clock_start: np.ndarray, targets: np.ndarray, intermediate: np.ndarray,
             modes: np.ndarray, tick: int, cancelled: np.ndarray, dt: float) -> np.ndarray:
    selected = np.asarray(targets, dtype=np.float64).copy()
    first = tick < 15
    if first:
        hold = (modes == 1) & ~cancelled
        selected[hold] = clock_start[hold]
        for mode in (2, 3):
            chosen = (modes == mode) & ~cancelled
            selected[chosen] = intermediate[mode - 2, chosen]
    return toward(current, selected, dt=dt)


def _nearest(xyz: np.ndarray, stations: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rel = stations[None, :, :] - xyz[:, None, :]
    distance = np.linalg.norm(rel, axis=2)
    selected = np.argmin(distance, axis=1)
    return selected, rel[np.arange(N_UAVS), selected], distance[np.arange(N_UAVS), selected]


def _margins(xyz: np.ndarray, battery: np.ndarray, stations: np.ndarray, raw) -> np.ndarray:
    _, _, distance = _nearest(xyz, stations)
    return_power = raw._calculate_power_consumption(float(raw.limp_home_speed_mps), 0.0)
    required = distance / max(float(raw.limp_home_speed_mps), 1e-8) * return_power / 3600.0
    return battery - required / max(float(raw.battery_capacity_wh), 1e-8) - float(raw.return_reserve_ratio)


def legal_start(observations: np.ndarray) -> dict[str, np.ndarray]:
    """Decode only current legal own and station fields."""
    energy = own_energy(observations)
    stations = station_records(observations)
    if not stations["valid"][0].all():
        raise ValueError("S2 requires two valid observed charging stations")
    station_xyz = stations["xyz_m"][0].copy()
    # S2 capacity is one per station; the legal ratio encodes it as 1/8.
    capacity = np.rint(stations["capacity_ratio"][0] * N_UAVS).astype(np.int64)
    if not np.array_equal(capacity, [1, 1]):
        raise ValueError("unexpected S2 charging capacity")
    return {"xyz": own_positions(observations),
            "battery": energy["battery"].astype(np.float64),
            "margin": energy["return_margin"].astype(np.float64),
            "available": energy["available"].copy(),
            "charging": energy["charging"].copy(),
            "waits": energy["waiting_steps"].copy(),
            "stations": station_xyz, "capacity": capacity}


def forecast(start: dict[str, np.ndarray], targets_xyz: np.ndarray, modes: np.ndarray,
             prior_F: np.ndarray, model_env) -> Forecast:
    """Propagate one complete nominal joint plan, including coupled charging."""
    raw = getattr(model_env, "env", model_env)
    xyz = np.asarray(start["xyz"], dtype=np.float64).copy()
    battery = np.asarray(start["battery"], dtype=np.float64).copy()
    margin = np.asarray(start["margin"], dtype=np.float64).copy()
    waits = np.asarray(start["waits"], dtype=np.int64).copy()
    stations = np.asarray(start["stations"], dtype=np.float64)
    capacity = np.asarray(start["capacity"], dtype=np.int64)
    targets = np.asarray(targets_xyz, dtype=np.float64).copy()
    modes = np.asarray(modes, dtype=np.int64)
    F = np.asarray(prior_F, dtype=bool).copy()
    if xyz.shape != (N_UAVS, 3) or targets.shape != xyz.shape or modes.shape != (N_UAVS,):
        raise ValueError("joint forecast requires eight xyz targets and modes")
    if np.any((modes < 0) | (modes >= N_MODES)):
        raise ValueError("mode outside D/W/B+/B-")
    if not np.isfinite(xyz).all() or not np.isfinite(battery).all() or not np.isfinite(targets).all():
        raise ValueError("non-finite nominal start or target")
    intermediate = waypoints(xyz, targets)
    clock_start = xyz.copy()
    cancelled = np.zeros(N_UAVS, dtype=bool)
    crossed_F = np.zeros(N_UAVS, dtype=bool)
    crossed_reserve = np.zeros(N_UAVS, dtype=bool)
    crossed_cutoff = np.zeros(N_UAVS, dtype=bool)
    snapshots_xyz, snapshots_battery, snapshots_margin, snapshots_F, snapshots_waits = [], [], [], [], []
    travel = 0.0
    dt = float(raw.time_step)
    for tick in range(HORIZON):
        entered = ~F & (margin <= PRODUCTION_PARAMS.enter_margin)
        F[margin <= PRODUCTION_PARAMS.enter_margin] = True
        F[margin >= PRODUCTION_PARAMS.exit_margin] = False
        cancelled |= entered
        crossed_F |= entered
        velocity = proposal(xyz, clock_start, targets, intermediate, modes, tick, cancelled, dt)
        station_id, station_vector, distance = _nearest(xyz, stations)
        dock = F.copy()
        # Feedback's dock command is composed with the native emergency and docking controls.
        if F.any():
            vector = station_vector[F]
            duration = np.maximum.reduce((
                np.ones(len(vector)),
                np.linalg.norm(vector[:, :2], axis=1) / HORIZONTAL_SPEED_MPS,
                np.abs(vector[:, 2]) / VERTICAL_SPEED_MPS,
            ))
            velocity[F] = vector / duration[:, None]
        velocity[F & (distance <= float(raw.charging_radius_m))] = 0.0
        docking = F & (distance > float(raw.charging_capture_radius_m)) & (distance <= float(raw.charging_radius_m))
        if docking.any():
            vector = station_vector[docking]
            planar = np.linalg.norm(vector[:, :2], axis=1)
            velocity[docking, :2] = vector[:, :2] * (
                np.minimum(float(raw.docking_horizontal_speed_mps), planar / dt) /
                np.maximum(planar, 1e-12))[:, None]
            velocity[docking, 2] = np.clip(vector[:, 2] / dt,
                                           -float(raw.docking_vertical_speed_mps),
                                           float(raw.docking_vertical_speed_mps))
        limp = (battery > 0.0) & (battery <= float(raw.emergency_return_threshold))
        dock |= limp
        outer = limp & (distance > float(raw.charging_radius_m))
        limp_speed = min(max(float(raw.limp_home_speed_mps), 0.0), max(float(raw.max_speed), 1e-8))
        velocity[outer] = station_vector[outer] * (
            np.minimum(limp_speed, distance[outer] / dt) /
            np.maximum(distance[outer], 1e-12))[:, None]
        inner = limp & ~outer & (distance > float(raw.charging_capture_radius_m))
        if inner.any():
            vector = station_vector[inner]
            planar = np.linalg.norm(vector[:, :2], axis=1)
            velocity[inner, :2] = vector[:, :2] * (
                np.minimum(float(raw.docking_horizontal_speed_mps), planar / dt) /
                np.maximum(planar, 1e-12))[:, None]
            velocity[inner, 2] = np.clip(vector[:, 2] / dt,
                                          -float(raw.docking_vertical_speed_mps),
                                          float(raw.docking_vertical_speed_mps))
        velocity[limp & (distance <= float(raw.charging_capture_radius_m))] = 0.0
        velocity[battery <= 0.0] = 0.0
        old_xyz = xyz.copy()
        xyz += velocity * dt
        xyz[:, :2] = np.clip(xyz[:, :2], 0.0, S7S2_LAYOUT.area_size_m)
        xyz[:, 2] = np.clip(xyz[:, 2], S7S2_LAYOUT.height_min_m, S7S2_LAYOUT.height_max_m)
        actual = (xyz - old_xyz) / dt
        travel += float(np.linalg.norm(xyz - old_xyz, axis=1).sum())
        watts = raw._calculate_power_consumption(np.linalg.norm(actual[:, :2], axis=1), actual[:, 2])
        consumed = watts * dt / 3600.0
        battery -= consumed / float(raw.battery_capacity_wh)
        after_id, _, after_distance = _nearest(xyz, stations)
        eligible = dock & (np.linalg.norm(actual, axis=1) <= float(raw.charging_hover_speed_threshold)) & (
            after_distance <= float(raw.charging_capture_radius_m))
        # A dock request selects the nearest station before movement.
        eligible &= after_id == station_id
        selected = np.zeros(N_UAVS, dtype=bool)
        for station in range(len(stations)):
            ids = np.flatnonzero(eligible & (station_id == station))
            ordered = sorted(ids, key=lambda i: (battery[i], -waits[i], int(i)))
            selected[ordered[:int(capacity[station])]] = True
        charge = min(max(float(raw.charging_power_w), 0.0) * dt / 3600.0,
                     float(raw.battery_capacity_wh)) / float(raw.battery_capacity_wh)
        battery[selected] = np.minimum(1.0, battery[selected] + charge)
        waits = np.where(selected, 0, np.where(eligible, waits + 1, 0))
        battery = np.clip(battery, 0.0, 1.0)
        margin = _margins(xyz, battery, stations, raw)
        crossed_reserve |= battery <= float(raw.return_reserve_ratio)
        crossed_cutoff |= battery <= float(raw.service_cutoff_threshold)
        if tick + 1 in SAMPLES:
            snapshots_xyz.append(xyz.copy())
            snapshots_battery.append(battery.copy())
            snapshots_margin.append(margin.copy())
            snapshots_F.append(F.copy())
            snapshots_waits.append(waits.copy())
    return Forecast(np.asarray(snapshots_xyz), np.asarray(snapshots_battery),
                    np.asarray(snapshots_margin), np.asarray(snapshots_F),
                    np.asarray(snapshots_waits), cancelled, crossed_F,
                    crossed_reserve, crossed_cutoff, travel)
