"""Independent Python oracle for the frozen HEADLAND-90 host transition."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Iterable

from .config import (
    BLACKOUT_TICKS,
    DT,
    FIXTURE_NAMESPACE,
    LOCK_TICKS,
    PREROLL_TICKS,
    VG,
    ControllerSpec,
    EncounterSpec,
    FixtureTape,
    RouteClass,
)
from .event_transform import event_transform

Vec2 = tuple[float, float]
Vec3 = tuple[float, float, float]

B: Vec3 = (-450.0, 250.0, 15.0)
G_X = (-550.0, 550.0)
G_Y = (-350.0, 350.0)
O_X = (-80.0, 80.0)
O_Y = (-260.0, 80.0)
O_Z = (0.0, 140.0)
TERRAIN_CLEARANCE = 20.0
MIN_SEPARATION = 30.0


def _add(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] + b[0], a[1] + b[1])


def _sub(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] - b[0], a[1] - b[1])


def _scale(a: Vec2, scale: float) -> Vec2:
    return (a[0] * scale, a[1] * scale)


def _dot(a: Vec2, b: Vec2) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _norm(a: Vec2) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1])


def _clip(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def clip_norm(value: Vec2, limit: float) -> Vec2:
    norm = _norm(value)
    if norm <= limit or norm == 0.0:
        return value
    return _scale(value, limit / norm)


def distance_to_obstacle(point: Vec2) -> float:
    dx = max(O_X[0] - point[0], 0.0, point[0] - O_X[1])
    dy = max(O_Y[0] - point[1], 0.0, point[1] - O_Y[1])
    return math.sqrt(dx * dx + dy * dy)


def legal_point(point: Vec2) -> bool:
    return (
        G_X[0] <= point[0] <= G_X[1]
        and G_Y[0] <= point[1] <= G_Y[1]
        and distance_to_obstacle(point) >= TERRAIN_CLEARANCE
    )


def _projection_candidates(point: Vec2) -> list[Vec2]:
    candidates: list[Vec2] = []
    clamped = (_clip(point[0], *G_X), _clip(point[1], *G_Y))
    if legal_point(clamped):
        candidates.append(clamped)
    candidates.extend(
        [
            (-100.0, _clip(point[1], *O_Y)),
            (100.0, _clip(point[1], *O_Y)),
            (_clip(point[0], *O_X), -280.0),
            (_clip(point[0], *O_X), 100.0),
        ]
    )
    for cx, cy, sx, sy in (
        (-80.0, -260.0, -1, -1),
        (-80.0, 80.0, -1, 1),
        (80.0, -260.0, 1, -1),
        (80.0, 80.0, 1, 1),
    ):
        delta = (point[0] - cx, point[1] - cy)
        length = _norm(delta)
        if length > 0.0:
            radial = (cx + 20.0 * delta[0] / length, cy + 20.0 * delta[1] / length)
            if sx * (radial[0] - cx) >= 0.0 and sy * (radial[1] - cy) >= 0.0:
                candidates.append(radial)
        candidates.append((cx + 20.0 * sx, cy))
        candidates.append((cx, cy + 20.0 * sy))
    return [candidate for candidate in candidates if legal_point(candidate)]


def project_legal(point: Vec2) -> Vec2:
    if legal_point(point):
        return point
    candidates = _projection_candidates(point)
    if not candidates:
        raise ArithmeticError("closed-set projection has no candidate")
    return min(candidates, key=lambda p: ((_sub(p, point)[0] ** 2 + _sub(p, point)[1] ** 2), p[0], p[1]))


def _orient(a: Vec2, b: Vec2, c: Vec2) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Vec2, b: Vec2, p: Vec2) -> bool:
    return (
        min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
        and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
        and _orient(a, b, p) == 0.0
    )


def _segments_intersect(a: Vec2, b: Vec2, c: Vec2, d: Vec2) -> bool:
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    if ((o1 > 0.0 and o2 < 0.0) or (o1 < 0.0 and o2 > 0.0)) and (
        (o3 > 0.0 and o4 < 0.0) or (o3 < 0.0 and o4 > 0.0)
    ):
        return True
    return (
        (o1 == 0.0 and _on_segment(a, b, c))
        or (o2 == 0.0 and _on_segment(a, b, d))
        or (o3 == 0.0 and _on_segment(c, d, a))
        or (o4 == 0.0 and _on_segment(c, d, b))
    )


def _point_segment_distance_sq(p: Vec2, a: Vec2, b: Vec2) -> float:
    ab = _sub(b, a)
    denom = _dot(ab, ab)
    t = 0.0 if denom == 0.0 else _clip(_dot(_sub(p, a), ab) / denom, 0.0, 1.0)
    q = _add(a, _scale(ab, t))
    delta = _sub(p, q)
    return _dot(delta, delta)


def _segment_segment_distance_sq(a: Vec2, b: Vec2, c: Vec2, d: Vec2) -> float:
    if _segments_intersect(a, b, c, d):
        return 0.0
    return min(
        _point_segment_distance_sq(a, c, d),
        _point_segment_distance_sq(b, c, d),
        _point_segment_distance_sq(c, a, b),
        _point_segment_distance_sq(d, a, b),
    )


def segment_distance_to_obstacle_sq(a: Vec2, b: Vec2) -> float:
    corners = ((-80.0, -260.0), (80.0, -260.0), (80.0, 80.0), (-80.0, 80.0))
    if O_X[0] <= a[0] <= O_X[1] and O_Y[0] <= a[1] <= O_Y[1]:
        return 0.0
    if O_X[0] <= b[0] <= O_X[1] and O_Y[0] <= b[1] <= O_Y[1]:
        return 0.0
    return min(
        _segment_segment_distance_sq(a, b, corners[index], corners[(index + 1) % 4])
        for index in range(4)
    )


def legal_linear_tick(position: Vec2, velocity: Vec2) -> bool:
    endpoint = _add(position, _scale(velocity, DT))
    return (
        G_X[0] <= position[0] <= G_X[1]
        and G_Y[0] <= position[1] <= G_Y[1]
        and G_X[0] <= endpoint[0] <= G_X[1]
        and G_Y[0] <= endpoint[1] <= G_Y[1]
        and segment_distance_to_obstacle_sq(position, endpoint) >= TERRAIN_CLEARANCE**2
    )


def _segment_hits_closed_prism_open(a: Vec3, d: Vec3) -> bool:
    low, high = -math.inf, math.inf
    for av, dv, bounds in zip(a, d, (O_X, O_Y, O_Z)):
        delta = dv - av
        if delta == 0.0:
            if av < bounds[0] or av > bounds[1]:
                return False
            continue
        first, second = (bounds[0] - av) / delta, (bounds[1] - av) / delta
        if first > second:
            first, second = second, first
        low, high = max(low, first), min(high, second)
        if low > high:
            return False
    return low <= high and high > 0.0 and low < 1.0


def line_of_sight(a: Vec3, d: Vec3) -> bool:
    return not _segment_hits_closed_prism_open(a, d)


def route_geometry(spec: EncounterSpec, tick: int) -> tuple[Vec2, Vec2, Vec2]:
    scored_ticks = spec.route_class.scored_ticks
    time = (tick - PREROLL_TICKS) * DT
    if spec.route_class is RouteClass.SHORT:
        duration = scored_ticks * DT
        u = max(time, 0.0) / duration
        phi = math.pi / 4.0 + spec.direction * (u - 0.5) * math.pi / 2.0
        nominal = (
            80.0 + 64.0 * math.cos(phi) + spec.lateral_offset / math.sqrt(2.0),
            80.0 + 64.0 * math.sin(phi) + spec.lateral_offset / math.sqrt(2.0),
        )
        tangent = (
            spec.direction * -math.sin(phi),
            spec.direction * math.cos(phi),
        )
        if time < 0.0:
            phi0 = math.pi / 4.0 - spec.direction * math.pi / 4.0
            nominal0 = (
                80.0 + 64.0 * math.cos(phi0) + spec.lateral_offset / math.sqrt(2.0),
                80.0 + 64.0 * math.sin(phi0) + spec.lateral_offset / math.sqrt(2.0),
            )
            tangent = (spec.direction * -math.sin(phi0), spec.direction * math.cos(phi0))
            nominal = _add(nominal0, _scale(tangent, time * VG))
    else:
        duration = scored_ticks * DT
        u = max(time, 0.0) / duration
        nominal = (spec.direction * 64.0 * math.pi * (2.0 * u - 1.0), 200.0 + spec.lateral_offset)
        tangent = (float(spec.direction), 0.0)
        if time < 0.0:
            nominal0 = (-spec.direction * 64.0 * math.pi, 200.0 + spec.lateral_offset)
            nominal = _add(nominal0, _scale(tangent, time * VG))
    normal = (-tangent[1], tangent[0])
    return nominal, tangent, normal


def _target_position(spec: EncounterSpec, tick: int, zeta: float) -> tuple[Vec2, Vec2, Vec2]:
    base, tangent, normal = route_geometry(spec, tick)
    return _add(base, _scale(normal, zeta)), tangent, normal


def _margin_no_shadow(a: Vec3, d: Vec3) -> float:
    distance = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, d)))
    return 25.0 - 20.0 * math.log10(max(distance, 1.0) / 100.0) - (0.0 if line_of_sight(a, d) else 30.0)


def _plan(x_hat: Vec2, v_hat: Vec2, p_r: Vec2) -> tuple[Vec2, Vec2] | None:
    waypoint_t = project_legal(_add(x_hat, _scale(v_hat, 2.0)))
    w_t3 = (waypoint_t[0], waypoint_t[1], 80.0)
    candidates: list[tuple[float, float, float, float, Vec2]] = []
    for fraction in (0.5, 0.75, 1.0):
        base = (
            B[0] + fraction * (waypoint_t[0] - B[0]),
            B[1] + fraction * (waypoint_t[1] - B[1]),
        )
        for offset in ((0.0, 0.0), (120.0, 0.0), (-120.0, 0.0), (0.0, 120.0), (0.0, -120.0)):
            candidate = _add(base, offset)
            if not legal_point(candidate):
                continue
            c3 = (candidate[0], candidate[1], 100.0)
            travel = _norm(_sub(candidate, p_r))
            score = min(_margin_no_shadow(w_t3, c3), _margin_no_shadow(c3, B)) - 0.01 * travel
            candidates.append((-score, travel, candidate[0], candidate[1], candidate))
    if not candidates:
        return None
    return waypoint_t, min(candidates)[-1]


def _velocity_registry(vmax: float) -> tuple[Vec2, ...]:
    values: list[Vec2] = [(0.0, 0.0)]
    for factor in (0.5, 1.0):
        for heading in range(16):
            angle = 2.0 * math.pi * heading / 16.0
            values.append((factor * vmax * math.cos(angle), factor * vmax * math.sin(angle)))
    return tuple(values)


AIR_T = _velocity_registry(18.0)
AIR_R = _velocity_registry(22.0)


def _minimum_relative_distance(p_t: Vec2, vg_t: Vec2, p_r: Vec2, vg_r: Vec2) -> float:
    relative = _sub(p_t, p_r)
    velocity = _sub(vg_t, vg_r)
    denom = _dot(velocity, velocity)
    time = 0.0 if denom == 0.0 else _clip(-_dot(relative, velocity) / denom, 0.0, DT)
    return _norm(_add(relative, _scale(velocity, time)))


def _control(
    p_t: Vec2,
    p_r: Vec2,
    waypoint_t: Vec2,
    waypoint_r: Vec2,
    wind_t: Vec2,
    wind_r: Vec2,
) -> tuple[int, int, Vec2, Vec2, Vec2, Vec2, tuple[int, int], float] | None:
    nominal_t = clip_norm(_scale(_sub(waypoint_t, p_t), 0.5), 18.0)
    nominal_r = clip_norm(_scale(_sub(waypoint_r, p_r), 0.5), 22.0)
    ground_t = tuple(_add(air, wind_t) for air in AIR_T)
    ground_r = tuple(_add(air, wind_r) for air in AIR_R)
    unconstrained = min(
        (
            (_dot(_sub(vt, nominal_t), _sub(vt, nominal_t)) + _dot(_sub(vr, nominal_r), _sub(vr, nominal_r))),
            _norm(AIR_T[it]) + _norm(AIR_R[ir]), it, ir,
        )
        for it, vt in enumerate(ground_t)
        for ir, vr in enumerate(ground_r)
    )
    legal_t = [legal_linear_tick(p_t, value) for value in ground_t]
    legal_r = [legal_linear_tick(p_r, value) for value in ground_r]
    feasible: list[tuple[float, float, int, int, float]] = []
    for it, vt in enumerate(ground_t):
        if not legal_t[it]:
            continue
        for ir, vr in enumerate(ground_r):
            if not legal_r[ir]:
                continue
            separation = _minimum_relative_distance(p_t, vt, p_r, vr)
            if separation < MIN_SEPARATION:
                continue
            objective = _dot(_sub(vt, nominal_t), _sub(vt, nominal_t)) + _dot(_sub(vr, nominal_r), _sub(vr, nominal_r))
            feasible.append((objective, _norm(AIR_T[it]) + _norm(AIR_R[ir]), it, ir, separation))
    if not feasible:
        return None
    chosen = min(feasible)
    it, ir = chosen[2], chosen[3]
    return it, ir, AIR_T[it], AIR_R[ir], ground_t[it], ground_r[ir], (unconstrained[2], unconstrained[3]), chosen[4]


def _radio(a: Vec3, d: Vec3, shadow: float, uniform: float) -> tuple[bool, float, float, bool]:
    los = line_of_sight(a, d)
    distance = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, d)))
    margin = 25.0 - 20.0 * math.log10(max(distance, 1.0) / 100.0) - (0.0 if los else 30.0) + shadow
    probability = 1.0 / (1.0 + math.exp(-margin / 3.0))
    return los, margin, probability, uniform < probability


@dataclass(frozen=True)
class TickRecord:
    tick: int
    time: float
    scored: bool
    scored_index: int
    action: str
    legal_opportunity: bool
    action_uniform_consumed: bool
    action_uniform: float
    rate_numerator: int
    rate_denominator: int
    rate_q: float
    event_lambda: float
    event_probability: float
    eligible_time: float
    target: Vec2
    tangent: Vec2
    normal: Vec2
    zeta: float
    wind_tracker: Vec2
    wind_relay: Vec2
    tracker_position: Vec2
    relay_position: Vec2
    estimator_position: Vec2
    estimator_velocity: Vec2
    sensor_visible: bool
    sensor_observation: Vec2 | None
    buffer_count: int
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
    battery_exhausted: bool


@dataclass(frozen=True)
class EncounterResult:
    spec: EncounterSpec
    logical_tag: str
    ticks: tuple[TickRecord, ...]
    scored_valid_ticks: int
    voluntary_updates: int
    voluntary_keeps: int
    opportunity_rows: int
    safety_overrides: int
    hard_failure: bool
    no_planner_solution: bool
    no_safe_control: bool
    battery_exhausted: bool

    @property
    def service_fraction(self) -> Fraction:
        return Fraction(self.scored_valid_ticks, self.spec.route_class.scored_ticks)


class Headland90Host:
    """State-local oracle.  Instances hold no state between encounters."""

    def run(
        self,
        spec: EncounterSpec,
        tape: FixtureTape,
        controller: ControllerSpec,
        *,
        logical_tag: str = "CONFORMANCE",
    ) -> EncounterResult:
        if spec.namespace != FIXTURE_NAMESPACE:
            raise PermissionError("production controller ticks are not authorized")
        total_ticks = spec.total_ticks
        if len(tape.target_lateral) != total_ticks + 1 or len(tape.action) != total_ticks:
            raise ValueError("fixture tape shape does not match encounter")

        zeta = _clip(2.0 * tape.target_lateral[0], -6.0, 6.0)
        target, tangent, normal = _target_position(spec, 0, zeta)
        p_t, p_r = target, (0.0, 180.0)
        wind_t = clip_norm(_scale(tape.wind_t[0], 2.0), 4.0)
        wind_r = clip_norm(_scale(tape.wind_r[0], 2.0), 4.0)
        shadow_tr, shadow_rb = 3.0 * tape.shadow_tr[0], 3.0 * tape.shadow_rb[0]
        energy_t, energy_r = 40000.0, 45000.0
        estimator_x: Vec2 = (math.nan, math.nan)
        estimator_v: Vec2 = (math.nan, math.nan)
        waypoint_t: Vec2 = p_t
        waypoint_r: Vec2 = p_r
        buffer: list[tuple[float, Vec2]] = []
        lockout_until, blackout_until = 0, 0
        last_update_anchor = 0
        no_planner = no_safe = battery_exhausted = hard_failure = False
        records: list[TickRecord] = []
        scored_valid = voluntary_updates = voluntary_keeps = opportunities = overrides = 0

        for tick in range(total_ticks):
            time = (tick - PREROLL_TICKS) * DT
            scored = tick >= PREROLL_TICKS
            scored_index = tick - PREROLL_TICKS
            current_visible = _norm(_sub(target, p_t)) <= 250.0 and line_of_sight(
                (target[0], target[1], 0.0), (p_t[0], p_t[1], 80.0)
            )
            current_observation = _add(target, _scale(tape.sensor[tick], 3.0)) if current_visible else None
            if tick == 0:
                if not current_visible or current_observation is None:
                    hard_failure = True
                    raise RuntimeError("initial target sample is not visible")
                buffer.append((time, current_observation))
                estimator_x = current_observation
                estimator_v = clip_norm(_scale(tangent, VG), 20.0)
                planned = _plan(estimator_x, estimator_v, p_r)
                if planned is None:
                    no_planner = hard_failure = True
                else:
                    waypoint_t, waypoint_r = planned
                buffer.clear()
                action = "BOOT"
                lockout_until, blackout_until = LOCK_TICKS, BLACKOUT_TICKS
            else:
                action = "KEEP"

            legal_opportunity = scored and tick >= lockout_until and not hard_failure
            action_consumed = legal_opportunity
            action_uniform = tape.action[tick] if action_consumed else math.nan
            rate = Fraction(0)
            event_lambda = event_probability = eligible_time = 0.0
            if legal_opportunity:
                opportunities += 1
                rate = controller.rate_fraction(spec.route_class, scored_index, last_update_anchor)
                eligible_time = DT
                _, event_lambda, event_probability = event_transform(rate)
                if action_uniform < event_probability:
                    action = "JOINT-UPDATE"
                    voluntary_updates += 1
                    if len(buffer) >= 2:
                        (t1, z1), (t2, z2) = buffer[-2:]
                        estimator_x = z2
                        estimator_v = clip_norm(_scale(_sub(z2, z1), 1.0 / (t2 - t1)), 20.0)
                    elif len(buffer) == 1:
                        estimator_x = buffer[-1][1]
                    buffer.clear()
                    planned = _plan(estimator_x, estimator_v, p_r)
                    if planned is None:
                        no_planner = hard_failure = True
                    else:
                        waypoint_t, waypoint_r = planned
                    lockout_until, blackout_until = tick + LOCK_TICKS, tick + BLACKOUT_TICKS
                    last_update_anchor = scored_index
                else:
                    voluntary_keeps += 1

            blackout = tick < blackout_until
            lockout = tick < lockout_until
            tracker3 = (p_t[0], p_t[1], 80.0)
            relay3 = (p_r[0], p_r[1], 100.0)
            los_tr, margin_tr, probability_tr, raw_trial_tr = _radio(tracker3, relay3, shadow_tr, tape.link_tr[tick])
            los_rb, margin_rb, probability_rb, raw_trial_rb = _radio(relay3, B, shadow_rb, tape.link_rb[tick])
            trial_tr = raw_trial_tr and not blackout
            trial_rb = raw_trial_rb and not blackout
            packet_valid = trial_tr and trial_rb
            tracking_error = _norm(_sub(estimator_x, target))
            tracking_valid = tracking_error <= 15.0

            energy_before_t, energy_before_r = energy_t, energy_r
            control = None if hard_failure or battery_exhausted else _control(
                p_t, p_r, waypoint_t, waypoint_r, wind_t, wind_r
            )
            if control is None:
                if not hard_failure:
                    no_safe = hard_failure = True
                it = ir = uit = uir = -1
                air_t = air_r = ground_t = ground_r = (0.0, 0.0)
                minimum_separation = _norm(_sub(p_t, p_r))
                override = False
            else:
                it, ir, air_t, air_r, ground_t, ground_r, unconstrained, minimum_separation = control
                uit, uir = unconstrained
                override = (it, ir) != unconstrained
                overrides += int(override)

            service = int(
                scored and tracking_valid and packet_valid and not blackout
                and not battery_exhausted and not hard_failure
            )
            scored_valid += service

            next_p_t = p_t if battery_exhausted else _add(p_t, _scale(ground_t, DT))
            next_p_r = p_r if battery_exhausted else _add(p_r, _scale(ground_r, DT))
            update_charge = 200.0 if action in ("BOOT", "JOINT-UPDATE") else 0.0
            energy_t = max(0.0, energy_t - DT * (300.0 + _dot(air_t, air_t)) - update_charge)
            energy_r = max(0.0, energy_r - DT * (350.0 + _dot(air_r, air_r)) - update_charge)
            if energy_t == 0.0 or energy_r == 0.0:
                battery_exhausted = hard_failure = True

            records.append(
                TickRecord(
                    tick=tick, time=time, scored=scored, scored_index=scored_index,
                    action=action, legal_opportunity=legal_opportunity,
                    action_uniform_consumed=action_consumed, action_uniform=action_uniform,
                    rate_numerator=rate.numerator, rate_denominator=rate.denominator,
                    rate_q=float(rate), event_lambda=event_lambda,
                    event_probability=event_probability, eligible_time=eligible_time,
                    target=target, tangent=tangent, normal=normal, zeta=zeta,
                    wind_tracker=wind_t, wind_relay=wind_r,
                    tracker_position=p_t, relay_position=p_r,
                    estimator_position=estimator_x, estimator_velocity=estimator_v,
                    sensor_visible=current_visible, sensor_observation=current_observation,
                    buffer_count=len(buffer), tracker_waypoint=waypoint_t,
                    relay_waypoint=waypoint_r, tracking_error=tracking_error,
                    tracking_valid=tracking_valid, shadow_tr=shadow_tr, shadow_rb=shadow_rb,
                    los_tr=los_tr, los_rb=los_rb, margin_tr=margin_tr, margin_rb=margin_rb,
                    probability_tr=probability_tr, probability_rb=probability_rb,
                    link_uniform_tr=tape.link_tr[tick], link_uniform_rb=tape.link_rb[tick],
                    raw_trial_tr=raw_trial_tr, raw_trial_rb=raw_trial_rb,
                    trial_tr=trial_tr, trial_rb=trial_rb, packet_valid=packet_valid,
                    blackout_active=blackout, lockout_active=lockout,
                    tracker_energy_before=energy_before_t, relay_energy_before=energy_before_r,
                    tracker_energy_after=energy_t, relay_energy_after=energy_r,
                    tracker_air_velocity=air_t, relay_air_velocity=air_r,
                    tracker_ground_velocity=ground_t, relay_ground_velocity=ground_r,
                    tracker_control_index=it, relay_control_index=ir,
                    unconstrained_tracker_index=uit, unconstrained_relay_index=uir,
                    safety_override=override, minimum_separation=minimum_separation,
                    terrain_distance_tracker_after=distance_to_obstacle(next_p_t),
                    terrain_distance_relay_after=distance_to_obstacle(next_p_r),
                    terrain_penetration=(
                        distance_to_obstacle(next_p_t) < TERRAIN_CLEARANCE
                        or distance_to_obstacle(next_p_r) < TERRAIN_CLEARANCE
                    ),
                    geofence_exit=not (
                        G_X[0] <= next_p_t[0] <= G_X[1]
                        and G_Y[0] <= next_p_t[1] <= G_Y[1]
                        and G_X[0] <= next_p_r[0] <= G_X[1]
                        and G_Y[0] <= next_p_r[1] <= G_Y[1]
                    ),
                    separation_breach=minimum_separation < MIN_SEPARATION,
                    service=service, hard_failure=hard_failure,
                    no_planner_solution=no_planner, no_safe_control=no_safe,
                    battery_exhausted=battery_exhausted,
                )
            )

            p_t, p_r = next_p_t, next_p_r
            estimator_x = _add(estimator_x, _scale(estimator_v, DT))
            next_tick = tick + 1
            zeta = _clip(
                0.96 * zeta + 2.0 * math.sqrt(1.0 - 0.96**2) * tape.target_lateral[next_tick],
                -6.0,
                6.0,
            )
            target, tangent, normal = _target_position(spec, next_tick, zeta)
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
            next_time = (next_tick - PREROLL_TICKS) * DT
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
            logical_tag=logical_tag,
            ticks=tuple(records),
            scored_valid_ticks=scored_valid,
            voluntary_updates=voluntary_updates,
            voluntary_keeps=voluntary_keeps,
            opportunity_rows=opportunities,
            safety_overrides=overrides,
            hard_failure=hard_failure,
            no_planner_solution=no_planner,
            no_safe_control=no_safe,
            battery_exhausted=battery_exhausted,
        )


def run_reference_batch(
    fixtures: Iterable[tuple[EncounterSpec, FixtureTape, ControllerSpec, str]],
) -> tuple[EncounterResult, ...]:
    host = Headland90Host()
    return tuple(host.run(spec, tape, controller, logical_tag=tag) for spec, tape, controller, tag in fixtures)
