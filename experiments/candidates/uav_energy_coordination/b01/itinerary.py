"""Pure, event-based B01 nominal UAV itinerary and shared-station forecast."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class ForecastConfig:
    capacity_wh: float = 160.0
    hover_w: float = 168.49
    charge_w: float = 1000.0
    outer_horizontal: float = 30.0
    outer_vertical: float = 5.0
    dock_horizontal: float = 3.0
    dock_vertical: float = 1.0
    approach_radius: float = 160.0
    capture_radius: float = 20.0
    reserve_ratio: float = 0.1
    release_margin: float = 0.05
    cutoff_ratio: float = 0.02
    limp_speed: float = 3.0
    return_power_w: float = 157.555532161


@dataclass(frozen=True)
class ForecastResult:
    times: np.ndarray
    positions: np.ndarray
    batteries: np.ndarray
    min_battery: np.ndarray
    cutoff_events: int
    depletion_events: int
    consumed_wh: float
    input_wh: float
    floor_clip_wh: float
    event_count: int
    phase_count: int
    arrival_times: np.ndarray
    release_times: np.ndarray


@dataclass
class _Member:
    index: int
    pos: np.ndarray
    energy: float
    goal: np.ndarray
    station: int
    stay: bool
    phase: str = ""
    leg: str = ""
    remaining: float = 0.0
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    power_w: float = 0.0
    route: list[tuple[np.ndarray, float, float]] = field(default_factory=list)
    destination: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))


def _duration(delta: np.ndarray, horizontal: float, vertical: float) -> float:
    return max(float(np.linalg.norm(delta[:2])) / horizontal, abs(float(delta[2])) / vertical)


def forecast_itineraries(
    positions: np.ndarray,
    batteries: np.ndarray,
    stations: np.ndarray,
    goals: np.ndarray,
    station_ids: np.ndarray,
    modes: np.ndarray,
    sample_times: np.ndarray,
    *,
    config: ForecastConfig,
    power: Callable[[float, float], float],
    cutoff_seen: np.ndarray | None = None,
    depletion_seen: np.ndarray | None = None,
) -> ForecastResult:
    """Forecast one service-return-release cycle per member, without native state reads."""
    pos = np.asarray(positions, dtype=np.float64).copy()
    battery = np.asarray(batteries, dtype=np.float64).copy()
    sites = np.asarray(stations, dtype=np.float64).copy()
    target = np.asarray(goals, dtype=np.float64).copy()
    raw_ids = np.asarray(station_ids)
    raw_modes = np.asarray(modes)
    if (not np.issubdtype(raw_ids.dtype, np.integer)
            or raw_modes.dtype != np.bool_):
        raise ValueError("station IDs must be integers and modes must be bool")
    ids = raw_ids.astype(np.int64, copy=True)
    active_f = raw_modes.copy()
    times = np.asarray(sample_times, dtype=np.float64).copy()
    n = len(battery)
    if (n < 1 or pos.shape != (n, 3) or target.shape != (n, 3) or sites.ndim != 2
            or sites.shape[1] != 3 or len(sites) < 1 or ids.shape != (n,)
            or active_f.shape != (n,) or times.shape != (3,)
            or not np.all(np.isfinite(pos)) or not np.all(np.isfinite(target))
            or not np.all(np.isfinite(sites)) or not np.all(np.isfinite(battery))
            or not np.all(np.isfinite(times)) or np.any(battery < 0)
            or np.any(battery > 1) or np.any(ids < -1) or np.any(ids >= len(sites))
            or not (0 < times[0] < times[1] < times[2] <= 600)):
        raise ValueError("invalid forecast geometry, battery, station ID, or sample times")
    positive = (config.capacity_wh, config.hover_w, config.charge_w,
                config.outer_horizontal, config.outer_vertical,
                config.dock_horizontal, config.dock_vertical,
                config.approach_radius, config.capture_radius,
                config.limp_speed, config.return_power_w)
    if (not all(np.isfinite(x) and x > 0 for x in positive)
            or config.capture_radius >= config.approach_radius
            or not 0 <= config.reserve_ratio <= 1
            or not 0 <= config.release_margin <= 1
            or not 0 <= config.cutoff_ratio <= 1):
        raise ValueError("invalid forecast constants")

    def initial_mask(mask: np.ndarray | None, threshold: float) -> np.ndarray:
        if mask is None:
            result = np.zeros(n, dtype=np.bool_)
        else:
            result = np.asarray(mask, dtype=np.bool_).copy()
            if result.shape != (n,):
                raise ValueError("event-seen mask must match member count")
        return result | (battery <= threshold)

    cut_seen = initial_mask(cutoff_seen, config.cutoff_ratio)
    dep_seen = initial_mask(depletion_seen, 0.0)
    members = [_Member(i, pos[i], float(battery[i] * config.capacity_wh), target[i],
                       int(ids[i]), bool(ids[i] >= 0)) for i in range(n)]
    arrivals = np.full(n, np.inf, dtype=np.float64)
    releases = np.full(n, np.inf, dtype=np.float64)
    samples_pos = np.empty((3, n, 3), dtype=np.float64)
    samples_battery = np.empty((3, n), dtype=np.float64)
    minima = battery.copy()
    consumed = input_wh = floor_clip = 0.0
    event_count = phase_count = 0
    now = 0.0
    eps_t = 1e-9
    eps_e = 1e-8
    max_events = 10000

    def enter(member: _Member, phase: str) -> None:
        nonlocal phase_count
        member.phase = phase
        phase_count += 1

    def nearest(point: np.ndarray) -> int:
        return int(np.argmin(np.linalg.norm(sites - point, axis=1)))

    def required_wh(point: np.ndarray) -> float:
        distance = float(np.min(np.linalg.norm(sites - point, axis=1)))
        return (config.reserve_ratio * config.capacity_wh
                + distance * config.return_power_w / (3600.0 * config.limp_speed))

    def next_segment(member: _Member) -> None:
        while member.route:
            destination, horizontal, vertical = member.route.pop(0)
            delta = destination - member.pos
            duration = _duration(delta, horizontal, vertical)
            if duration <= eps_t:
                member.pos = destination.copy()
                continue
            if member.energy <= eps_e:
                member.route.clear()
                enter(member, "frozen")
                return
            member.velocity = delta / duration
            member.remaining = duration
            member.power_w = float(power(float(np.linalg.norm(member.velocity[:2])),
                                         float(member.velocity[2])))
            if not np.isfinite(member.power_w) or member.power_w < 0:
                raise ValueError("native power must be finite and nonnegative")
            member.destination = destination
            enter(member, "travel")
            return
        if member.leg == "outbound":
            if member.energy <= eps_e:
                enter(member, "frozen")
                return
            dwell = max(0.0, member.energy - required_wh(member.pos)) * 3600.0 / config.hover_w
            if dwell > eps_t:
                member.remaining = dwell
                enter(member, "dwell")
            else:
                start_return(member)
        elif member.leg == "return":
            arrivals[member.index] = now
            enter(member, "resident" if member.stay else "charge")
        elif member.leg == "redeploy":
            enter(member, "frozen" if member.energy <= eps_e else "service")

    def start_return(member: _Member) -> None:
        if member.station < 0 or bool(active_f[member.index]):
            member.station = nearest(member.pos)
        station = sites[member.station]
        offset = member.pos - station
        distance = float(np.linalg.norm(offset))
        member.leg = "return"
        member.route = []
        if distance > config.capture_radius:
            direction = offset / distance
            if distance > config.approach_radius:
                member.route.append((station + direction * config.approach_radius,
                                     config.outer_horizontal, config.outer_vertical))
            member.route.append((station + direction * config.capture_radius,
                                 config.dock_horizontal, config.dock_vertical))
        next_segment(member)

    for i, member in enumerate(members):
        if active_f[i] or member.stay:
            start_return(member)
        else:
            member.leg = "outbound"
            member.route = [(member.goal.copy(), config.outer_horizontal, config.outer_vertical)]
            next_segment(member)
        if member.energy <= eps_e and member.phase == "travel":
            member.route.clear()
            enter(member, "frozen")

    def release_ready() -> bool:
        changed = False
        for member in members:
            if member.phase != "charge":
                continue
            distance = float(np.linalg.norm(sites[member.station] - member.pos))
            release_wh = (config.reserve_ratio + config.release_margin) * config.capacity_wh
            release_wh += distance * config.return_power_w / (3600.0 * config.limp_speed)
            if member.energy + eps_e < release_wh:
                continue
            releases[member.index] = now
            member.leg = "redeploy"
            member.route = [(member.goal.copy(), config.outer_horizontal, config.outer_vertical)]
            next_segment(member)
            changed = True
        return changed

    def slopes() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        rates = np.array([-m.power_w / 3600.0 if m.phase == "travel"
                          else -config.hover_w / 3600.0 for m in members], dtype=np.float64)
        inputs = np.zeros(n, dtype=np.float64)
        for station_id in range(len(sites)):
            eligible = [i for i, m in enumerate(members)
                        if m.station == station_id and m.phase in ("charge", "resident")]
            if not eligible:
                continue
            lowest = min(members[i].energy for i in eligible)
            group = [i for i in eligible if members[i].energy <= lowest + eps_e]
            if lowest >= config.capacity_wh - eps_e:
                for i in eligible:
                    inputs[i] = min(config.hover_w,
                                    config.charge_w / len(eligible)) / 3600.0
            else:
                for i in group:
                    inputs[i] = config.charge_w / (3600.0 * len(group))
        rates += inputs
        effective = rates.copy()
        for i, member in enumerate(members):
            if member.energy <= eps_e and effective[i] < 0:
                effective[i] = 0.0
            if member.energy >= config.capacity_wh - eps_e and effective[i] > 0:
                effective[i] = 0.0
        return rates, effective, inputs

    def next_energy_event(rates: np.ndarray) -> float:
        wait = np.inf
        for i, member in enumerate(members):
            rate = rates[i]
            if rate < -eps_e and member.energy > eps_e:
                wait = min(wait, member.energy / -rate)
                if not cut_seen[i] and member.energy > config.cutoff_ratio * config.capacity_wh:
                    wait = min(wait, (member.energy - config.cutoff_ratio * config.capacity_wh) / -rate)
            if rate > eps_e and member.energy < config.capacity_wh - eps_e:
                wait = min(wait, (config.capacity_wh - member.energy) / rate)
                if member.phase == "charge":
                    distance = float(np.linalg.norm(sites[member.station] - member.pos))
                    release_wh = (config.reserve_ratio + config.release_margin) * config.capacity_wh
                    release_wh += distance * config.return_power_w / (3600.0 * config.limp_speed)
                    if member.energy + eps_e < release_wh:
                        wait = min(wait, (release_wh - member.energy) / rate)
        for station_id in range(len(sites)):
            eligible = [i for i, m in enumerate(members)
                        if m.station == station_id and m.phase in ("charge", "resident")]
            if len(eligible) < 2:
                continue
            low = min(members[i].energy for i in eligible)
            group = [i for i in eligible if members[i].energy <= low + eps_e]
            others = [i for i in eligible if i not in group]
            if others:
                next_i = min(others, key=lambda i: members[i].energy)
                gap = members[next_i].energy - low
                relative = max(rates[i] for i in group) - rates[next_i]
                if relative > eps_e:
                    wait = min(wait, gap / relative)
        return wait

    sample_idx = 0
    while sample_idx < 3:
        if event_count >= max_events:
            raise RuntimeError("itinerary event safety limit exceeded")
        event_count += 1
        if release_ready():
            continue
        rates, effective, inputs = slopes()
        next_phase = min((m.remaining for m in members if m.phase in ("travel", "dwell")),
                         default=np.inf)
        dt = min(float(times[sample_idx] - now), next_phase, next_energy_event(effective))
        if not np.isfinite(dt) or dt < -eps_t:
            raise RuntimeError("invalid itinerary event time")
        dt = max(0.0, dt)
        old_energies = np.array([m.energy for m in members], dtype=np.float64)
        for i, member in enumerate(members):
            if member.phase == "travel":
                member.pos = member.pos + member.velocity * dt
                member.remaining -= dt
            elif member.phase == "dwell":
                member.remaining -= dt
            raw = member.energy + rates[i] * dt
            member.energy = float(np.clip(raw, 0.0, config.capacity_wh))
            floor_clip += max(0.0, -raw)
            consumed += (member.power_w if member.phase == "travel" else config.hover_w) * dt / 3600.0
            input_wh += inputs[i] * dt
            minima[i] = min(minima[i], member.energy / config.capacity_wh)
            if not cut_seen[i] and old_energies[i] > config.cutoff_ratio * config.capacity_wh and member.energy <= config.cutoff_ratio * config.capacity_wh + eps_e:
                cut_seen[i] = True
            if not dep_seen[i] and old_energies[i] > 0 and member.energy <= eps_e:
                dep_seen[i] = True
        now += dt
        for member in members:
            if member.phase == "travel" and member.remaining <= eps_t:
                member.pos = member.destination.copy()
                next_segment(member)
            elif member.phase == "dwell" and member.remaining <= eps_t:
                start_return(member)
            elif member.phase in ("travel", "dwell", "service") and member.energy <= eps_e:
                member.route.clear()
                enter(member, "frozen")
        release_ready()
        if now >= times[sample_idx] - eps_t:
            samples_pos[sample_idx] = np.stack([m.pos for m in members])
            samples_battery[sample_idx] = [m.energy / config.capacity_wh for m in members]
            sample_idx += 1
        elif dt <= eps_t:
            raise RuntimeError("itinerary event solver failed to advance")

    return ForecastResult(times, samples_pos, samples_battery, minima,
                          int(np.sum(cut_seen & ~initial_mask(cutoff_seen, config.cutoff_ratio))),
                          int(np.sum(dep_seen & ~initial_mask(depletion_seen, 0.0))),
                          consumed, input_wh, floor_clip, event_count, phase_count,
                          arrivals, releases)
