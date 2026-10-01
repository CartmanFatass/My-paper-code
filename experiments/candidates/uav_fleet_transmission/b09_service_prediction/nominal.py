"""Retained nominal joint arithmetic with bounded, per-tick audit hashing only.

The forecast body is source-bound to uav_joint_transition/motion.py at18c9a6ba5.
No native step, guard, intermediate RF or extra action is introduced. Callback
interruptions let the reader reconstruct only a recorded partial prefix.
"""
from __future__ import annotations
import hashlib
import numpy as np
from experiments.candidates.uav_joint_transition.motion import (
    Forecast, HORIZON, N_MODES, N_UAVS, SAMPLES, waypoints, proposal, _nearest, _margins,
    S7S2_LAYOUT, PRODUCTION_PARAMS, HORIZONTAL_SPEED_MPS, VERTICAL_SPEED_MPS,
)

def forecast(start: dict[str, np.ndarray], targets_xyz: np.ndarray, modes: np.ndarray,
             prior_F: np.ndarray, model_env, *, counters: dict, on_tick=None):
    """Propagate one complete nominal joint plan, including coupled charging."""
    digest = hashlib.sha256(b"B09-nominal-ticks-v1\0")
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
        counters["joint_forecast_ticks"] = counters.get("joint_forecast_ticks", 0) + 1
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
        # Audit only: the retained arithmetic/order above is unchanged.
        for value in (xyz, battery, margin, F, waits, consumed, selected,
                      crossed_F, crossed_reserve, crossed_cutoff):
            array = np.ascontiguousarray(value)
            digest.update(str(array.dtype).encode())
            digest.update(str(array.shape).encode())
            digest.update(array.tobytes())
        counters["joint_forecast_ticks_completed"] = counters.get("joint_forecast_ticks_completed", 0) + 1
        if on_tick is not None:
            on_tick(tick + 1, digest.hexdigest())
        if tick + 1 in SAMPLES:
            snapshots_xyz.append(xyz.copy())
            snapshots_battery.append(battery.copy())
            snapshots_margin.append(margin.copy())
            snapshots_F.append(F.copy())
            snapshots_waits.append(waits.copy())
    result = Forecast(np.asarray(snapshots_xyz), np.asarray(snapshots_battery),
                    np.asarray(snapshots_margin), np.asarray(snapshots_F),
                    np.asarray(snapshots_waits), cancelled, crossed_F,
                    crossed_reserve, crossed_cutoff, travel)
    return result, digest.hexdigest()
