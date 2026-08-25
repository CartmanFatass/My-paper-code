"""Independent fixture oracle for the frozen TBVUUS revision 03 transition.

The accepted HEADLAND geometry, planner, radio and flight-control primitives are
reused verbatim.  This module replaces only the voluntary-action surface and is
never a production execution fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from ..headland90.host import (
    B,
    G_X,
    G_Y,
    MIN_SEPARATION,
    TERRAIN_CLEARANCE,
    _add,
    _control,
    _dot,
    _norm,
    _plan,
    _radio,
    _scale,
    _sub,
    clip_norm,
    distance_to_obstacle,
    line_of_sight,
)
from .config import (
    BLACKOUT_TICKS,
    DT,
    LOCKOUT_TICKS,
    PREROLL_TICKS,
    ROAD_TEMPLATES,
    ROAD_TEMPLATE_COUNT,
    VG,
    Arm,
    EncounterSpec,
    FixtureCase,
    RouteClass,
)

Vec2 = tuple[float, float]

ACTION_NAMES = ("KEEP", "BOOT", "OVERHEAD-SHAM", "RAW-PATCH", "ROAD-PATCH")


def _clip(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def route_at_time(
    route_class: RouteClass, direction: int, lateral: int, time: float
) -> tuple[Vec2, Vec2, Vec2]:
    scored_ticks = route_class.scored_ticks
    duration = scored_ticks * DT
    if route_class is RouteClass.SHORT:
        u = max(time, 0.0) / duration
        phi = math.pi / 4.0 + direction * (u - 0.5) * math.pi / 2.0
        base = (
            80.0 + 64.0 * math.cos(phi) + lateral / math.sqrt(2.0),
            80.0 + 64.0 * math.sin(phi) + lateral / math.sqrt(2.0),
        )
        tangent = (direction * -math.sin(phi), direction * math.cos(phi))
        if time < 0.0:
            phi0 = math.pi / 4.0 - direction * math.pi / 4.0
            base0 = (
                80.0 + 64.0 * math.cos(phi0) + lateral / math.sqrt(2.0),
                80.0 + 64.0 * math.sin(phi0) + lateral / math.sqrt(2.0),
            )
            tangent = (direction * -math.sin(phi0), direction * math.cos(phi0))
            base = _add(base0, _scale(tangent, time * VG))
    else:
        u = max(time, 0.0) / duration
        base = (direction * 64.0 * math.pi * (2.0 * u - 1.0), 200.0 + lateral)
        tangent = (float(direction), 0.0)
        if time < 0.0:
            base = _add(
                (-direction * 64.0 * math.pi, 200.0 + lateral),
                _scale(tangent, time * VG),
            )
    normal = (-tangent[1], tangent[0])
    return base, tangent, normal


def _road_fit(
    samples: list[tuple[float, Vec2]], xhat_pre: Vec2, vhat_pre: Vec2
) -> tuple[bool, int, tuple[float, ...], float, float, Vec2, Vec2, bool]:
    if len(samples) != 2:
        return False, -1, (math.nan,) * ROAD_TEMPLATE_COUNT, math.nan, math.nan, xhat_pre, vhat_pre, False
    (t1, z1), (t2, z2) = samples
    if not (t1 < t2 <= 0.0):
        return False, -1, (math.nan,) * ROAD_TEMPLATE_COUNT, math.nan, math.nan, xhat_pre, vhat_pre, False
    residuals: list[float] = []
    for route_class, direction, lateral in ROAD_TEMPLATES:
        base1, _, _ = route_at_time(route_class, direction, lateral, t1)
        base2, _, _ = route_at_time(route_class, direction, lateral, t2)
        residuals.append(_dot(_sub(z1, base1), _sub(z1, base1)) + _dot(_sub(z2, base2), _sub(z2, base2)))
    selected = min(range(ROAD_TEMPLATE_COUNT), key=residuals.__getitem__)
    route_class, direction, lateral = ROAD_TEMPLATES[selected]
    base2, _, normal2 = route_at_time(route_class, direction, lateral, t2)
    base0, tangent0, normal0 = route_at_time(route_class, direction, lateral, 0.0)
    eta_raw = _dot(_sub(z2, base2), normal2)
    eta_patch = _clip(eta_raw, -15.0, 15.0)
    x_patch = _add(base0, _scale(normal0, eta_patch))
    v_patch = _scale(tangent0, VG)
    effective = _norm(_sub(x_patch, xhat_pre)) >= 1.0 or _norm(_sub(v_patch, vhat_pre)) >= 1.0
    return True, selected, tuple(residuals), eta_raw, eta_patch, x_patch, v_patch, effective


@dataclass(frozen=True)
class TickRecord:
    tick: int
    time: float
    scored: bool
    scored_index: int
    action: str
    scheduled_t0_decision: bool
    action_shell: bool
    road_fit_available: bool
    selected_template: int
    road_residuals: tuple[float, ...]
    fit_t1: float
    fit_t2: float
    fit_z1: Vec2
    fit_z2: Vec2
    eta_raw: float
    eta_patch: float
    patch_position: Vec2
    patch_velocity: Vec2
    effective_road_patch: bool
    target: Vec2
    tangent: Vec2
    normal: Vec2
    zeta: float
    wind_tracker: Vec2
    wind_relay: Vec2
    tracker_position: Vec2
    relay_position: Vec2
    estimator_position_pre: Vec2
    estimator_velocity_pre: Vec2
    estimator_position: Vec2
    estimator_velocity: Vec2
    sensor_visible: bool
    sensor_observation: Vec2 | None
    buffer_count_pre: int
    buffer_count_post: int
    tracker_waypoint: Vec2
    relay_waypoint: Vec2
    tracking_error: float
    tracking_valid: bool
    shadow_tr: float
    shadow_rb: float
    los_tr: bool
    los_rb: bool
    margin_tr: float
    margin_rb: float
    probability_tr: float
    probability_rb: float
    link_uniform_tr: float
    link_uniform_rb: float
    raw_trial_tr: bool
    raw_trial_rb: bool
    trial_tr: bool
    trial_rb: bool
    packet_valid: bool
    blackout_active: bool
    lockout_active: bool
    tracker_energy_before: float
    relay_energy_before: float
    tracker_energy_after: float
    relay_energy_after: float
    tracker_air_velocity: Vec2
    relay_air_velocity: Vec2
    tracker_ground_velocity: Vec2
    relay_ground_velocity: Vec2
    tracker_control_index: int
    relay_control_index: int
    unconstrained_tracker_index: int
    unconstrained_relay_index: int
    safety_override: bool
    minimum_separation: float
    terrain_distance_tracker_after: float
    terrain_distance_relay_after: float
    terrain_penetration: bool
    geofence_exit: bool
    separation_breach: bool
    service: int
    hard_failure: bool
    no_planner_solution: bool
    no_safe_control: bool
    numerical_fault: bool
    battery_exhausted: bool


@dataclass(frozen=True)
class EncounterResult:
    spec: EncounterSpec
    arm: Arm
    logical_tag: str
    ticks: tuple[TickRecord, ...]
    scored_valid_ticks: int
    scheduled_t0_decisions: int
    action_shells: int
    road_fit_available_count: int
    effective_road_patch_count: int
    safety_overrides: int
    terrain_penetrations: int
    geofence_exits: int
    separation_breaches: int
    hard_failure: bool
    no_planner_solution: bool
    no_safe_control: bool
    numerical_fault: bool
    battery_exhausted: bool


def run_reference(case: FixtureCase) -> EncounterResult:
    spec, tape, arm = case.spec, case.tape, case.arm
    total_ticks = spec.total_ticks
    if len(tape.target_lateral) != total_ticks + 1 or len(tape.link_tr) != total_ticks:
        raise ValueError("fixture tape shape does not match encounter")

    zeta = _clip(2.0 * tape.target_lateral[0], -6.0, 6.0)
    base, tangent, normal = route_at_time(spec.route_class, spec.direction, spec.lateral_offset, -4.0)
    target = _add(base, _scale(normal, zeta))
    p_t, p_r = target, (0.0, 180.0)
    wind_t = clip_norm(_scale(tape.wind_t[0], 2.0), 4.0)
    wind_r = clip_norm(_scale(tape.wind_r[0], 2.0), 4.0)
    shadow_tr, shadow_rb = 3.0 * tape.shadow_tr[0], 3.0 * tape.shadow_rb[0]
    energy_t, energy_r = 40000.0, 45000.0
    xhat = vhat = (math.nan, math.nan)
    waypoint_t, waypoint_r = p_t, p_r
    buffer: list[tuple[float, Vec2]] = []
    lockout_until = blackout_until = 0
    hard = no_planner = no_safe = numerical = battery = False
    records: list[TickRecord] = []
    scored_valid = scheduled_count = shell_count = fit_count = effective_count = 0
    overrides = penetrations = geofence_exits = separation_breaches = 0

    for tick in range(total_ticks):
        time = (tick - PREROLL_TICKS) * DT
        scored = tick >= PREROLL_TICKS
        scored_index = tick - PREROLL_TICKS
        visible = _norm(_sub(target, p_t)) <= 250.0 and line_of_sight(
            (target[0], target[1], 0.0), (p_t[0], p_t[1], 80.0)
        )
        observation = _add(target, _scale(tape.sensor[tick], 3.0)) if visible else None
        action_code = 0
        if tick == 0:
            if observation is None:
                raise RuntimeError("initial target sample is not visible")
            buffer.append((time, observation))
            xhat = observation
            vhat = clip_norm(_scale(tangent, VG), 20.0)
            planned = _plan(xhat, vhat, p_r)
            if planned is None:
                hard = no_planner = True
            else:
                waypoint_t, waypoint_r = planned
            buffer.clear()
            action_code = 1
            lockout_until, blackout_until = LOCKOUT_TICKS, BLACKOUT_TICKS

        scheduled = tick == PREROLL_TICKS
        xhat_pre, vhat_pre = xhat, vhat
        buffer_pre = len(buffer)
        fit_available = False
        selected = -1
        residuals = (math.nan,) * ROAD_TEMPLATE_COUNT
        fit_t1 = fit_t2 = math.nan
        fit_z1 = fit_z2 = (math.nan, math.nan)
        eta_raw = eta_patch = math.nan
        xpatch, vpatch = xhat_pre, vhat_pre
        effective = False
        shell = False
        if scheduled:
            scheduled_count += 1
            if len(buffer) == 2:
                (fit_t1, fit_z1), (fit_t2, fit_z2) = buffer
            (
                fit_available,
                selected,
                residuals,
                eta_raw,
                eta_patch,
                xpatch,
                vpatch,
                effective,
            ) = _road_fit(buffer, xhat_pre, vhat_pre)
            fit_count += int(fit_available)
            effective_count += int(effective)
            if arm is not Arm.NEVER_UPDATE:
                shell = True
                shell_count += 1
                action_code = 2 + int(arm) - 1
                lockout_until = tick + LOCKOUT_TICKS
                blackout_until = tick + BLACKOUT_TICKS
                buffer.clear()
                if arm is Arm.RAW_ESTIMATE_PATCH and fit_available:
                    xhat = fit_z2
                    vhat = clip_norm(_scale(_sub(fit_z2, fit_z1), 1.0 / (fit_t2 - fit_t1)), 20.0)
                elif arm is Arm.ROAD_TRACK_ESTIMATE_PATCH and fit_available:
                    xhat, vhat = xpatch, vpatch

        blackout = tick < blackout_until
        lockout = tick < lockout_until
        tracker3 = (p_t[0], p_t[1], 80.0)
        relay3 = (p_r[0], p_r[1], 100.0)
        los_tr, margin_tr, probability_tr, raw_trial_tr = _radio(tracker3, relay3, shadow_tr, tape.link_tr[tick])
        los_rb, margin_rb, probability_rb, raw_trial_rb = _radio(relay3, B, shadow_rb, tape.link_rb[tick])
        trial_tr, trial_rb = raw_trial_tr and not blackout, raw_trial_rb and not blackout
        packet_valid = trial_tr and trial_rb
        tracking_error = _norm(_sub(xhat, target))
        tracking_valid = tracking_error <= 15.0

        if not all(
            math.isfinite(value)
            for vector in (target, p_t, p_r, xhat, vhat, waypoint_t, waypoint_r, wind_t, wind_r)
            for value in vector
        ):
            numerical = hard = True

        energy_before_t, energy_before_r = energy_t, energy_r
        control = None if hard or battery else _control(p_t, p_r, waypoint_t, waypoint_r, wind_t, wind_r)
        if control is None:
            if not hard:
                hard = no_safe = True
            it = ir = uit = uir = -1
            air_t = air_r = ground_t = ground_r = (0.0, 0.0)
            minimum_separation = _norm(_sub(p_t, p_r))
            override = False
        else:
            it, ir, air_t, air_r, ground_t, ground_r, unconstrained, minimum_separation = control
            uit, uir = unconstrained
            override = (it, ir) != unconstrained
            overrides += int(override)
        service = int(scored and tracking_valid and packet_valid and not blackout and not battery and not hard)
        scored_valid += service
        next_p_t = p_t if battery else _add(p_t, _scale(ground_t, DT))
        next_p_r = p_r if battery else _add(p_r, _scale(ground_r, DT))
        charge = 200.0 if action_code in (1, 2, 3, 4) else 0.0
        energy_t = max(0.0, energy_t - DT * (300.0 + _dot(air_t, air_t)) - charge)
        energy_r = max(0.0, energy_r - DT * (350.0 + _dot(air_r, air_r)) - charge)
        if energy_t == 0.0 or energy_r == 0.0:
            hard = battery = True
        terrain_t = distance_to_obstacle(next_p_t)
        terrain_r = distance_to_obstacle(next_p_r)
        penetration = terrain_t < TERRAIN_CLEARANCE or terrain_r < TERRAIN_CLEARANCE
        geofence = not (
            G_X[0] <= next_p_t[0] <= G_X[1]
            and G_Y[0] <= next_p_t[1] <= G_Y[1]
            and G_X[0] <= next_p_r[0] <= G_X[1]
            and G_Y[0] <= next_p_r[1] <= G_Y[1]
        )
        separation = minimum_separation < MIN_SEPARATION
        penetrations += int(penetration)
        geofence_exits += int(geofence)
        separation_breaches += int(separation)

        records.append(
            TickRecord(
                tick=tick,
                time=time,
                scored=scored,
                scored_index=scored_index,
                action=ACTION_NAMES[action_code],
                scheduled_t0_decision=scheduled,
                action_shell=shell,
                road_fit_available=fit_available,
                selected_template=selected,
                road_residuals=residuals,
                fit_t1=fit_t1,
                fit_t2=fit_t2,
                fit_z1=fit_z1,
                fit_z2=fit_z2,
                eta_raw=eta_raw,
                eta_patch=eta_patch,
                patch_position=xpatch,
                patch_velocity=vpatch,
                effective_road_patch=effective,
                target=target,
                tangent=tangent,
                normal=normal,
                zeta=zeta,
                wind_tracker=wind_t,
                wind_relay=wind_r,
                tracker_position=p_t,
                relay_position=p_r,
                estimator_position_pre=xhat_pre,
                estimator_velocity_pre=vhat_pre,
                estimator_position=xhat,
                estimator_velocity=vhat,
                sensor_visible=visible,
                sensor_observation=observation,
                buffer_count_pre=buffer_pre,
                buffer_count_post=len(buffer),
                tracker_waypoint=waypoint_t,
                relay_waypoint=waypoint_r,
                tracking_error=tracking_error,
                tracking_valid=tracking_valid,
                shadow_tr=shadow_tr,
                shadow_rb=shadow_rb,
                los_tr=los_tr,
                los_rb=los_rb,
                margin_tr=margin_tr,
                margin_rb=margin_rb,
                probability_tr=probability_tr,
                probability_rb=probability_rb,
                link_uniform_tr=tape.link_tr[tick],
                link_uniform_rb=tape.link_rb[tick],
                raw_trial_tr=raw_trial_tr,
                raw_trial_rb=raw_trial_rb,
                trial_tr=trial_tr,
                trial_rb=trial_rb,
                packet_valid=packet_valid,
                blackout_active=blackout,
                lockout_active=lockout,
                tracker_energy_before=energy_before_t,
                relay_energy_before=energy_before_r,
                tracker_energy_after=energy_t,
                relay_energy_after=energy_r,
                tracker_air_velocity=air_t,
                relay_air_velocity=air_r,
                tracker_ground_velocity=ground_t,
                relay_ground_velocity=ground_r,
                tracker_control_index=it,
                relay_control_index=ir,
                unconstrained_tracker_index=uit,
                unconstrained_relay_index=uir,
                safety_override=override,
                minimum_separation=minimum_separation,
                terrain_distance_tracker_after=terrain_t,
                terrain_distance_relay_after=terrain_r,
                terrain_penetration=penetration,
                geofence_exit=geofence,
                separation_breach=separation,
                service=service,
                hard_failure=hard,
                no_planner_solution=no_planner,
                no_safe_control=no_safe,
                numerical_fault=numerical,
                battery_exhausted=battery,
            )
        )

        p_t, p_r = next_p_t, next_p_r
        xhat = _add(xhat, _scale(vhat, DT))
        next_tick = tick + 1
        zeta = _clip(
            0.96 * zeta + 2.0 * math.sqrt(1.0 - 0.96**2) * tape.target_lateral[next_tick],
            -6.0,
            6.0,
        )
        next_time = (next_tick - PREROLL_TICKS) * DT
        base, tangent, normal = route_at_time(spec.route_class, spec.direction, spec.lateral_offset, next_time)
        target = _add(base, _scale(normal, zeta))
        wind_t = clip_norm(
            _add(_scale(wind_t, 0.90), _scale(tape.wind_t[next_tick], 2.0 * math.sqrt(1.0 - 0.90**2))),
            4.0,
        )
        wind_r = clip_norm(
            _add(_scale(wind_r, 0.90), _scale(tape.wind_r[next_tick], 2.0 * math.sqrt(1.0 - 0.90**2))),
            4.0,
        )
        shadow_tr = 0.95 * shadow_tr + 3.0 * math.sqrt(1.0 - 0.95**2) * tape.shadow_tr[next_tick]
        shadow_rb = 0.95 * shadow_rb + 3.0 * math.sqrt(1.0 - 0.95**2) * tape.shadow_rb[next_tick]
        next_visible = _norm(_sub(target, p_t)) <= 250.0 and line_of_sight(
            (target[0], target[1], 0.0), (p_t[0], p_t[1], 80.0)
        )
        if next_visible:
            next_observation = _add(target, _scale(tape.sensor[next_tick], 3.0))
            buffer.append((next_time, next_observation))
            if len(buffer) > 2:
                del buffer[:-2]

    return EncounterResult(
        spec=spec,
        arm=arm,
        logical_tag=case.logical_tag,
        ticks=tuple(records),
        scored_valid_ticks=scored_valid,
        scheduled_t0_decisions=scheduled_count,
        action_shells=shell_count,
        road_fit_available_count=fit_count,
        effective_road_patch_count=effective_count,
        safety_overrides=overrides,
        terrain_penetrations=penetrations,
        geofence_exits=geofence_exits,
        separation_breaches=separation_breaches,
        hard_failure=hard,
        no_planner_solution=no_planner,
        no_safe_control=no_safe,
        numerical_fault=numerical,
        battery_exhausted=battery,
    )


def run_reference_batch(cases: Iterable[FixtureCase]) -> tuple[EncounterResult, ...]:
    return tuple(run_reference(case) for case in cases)
