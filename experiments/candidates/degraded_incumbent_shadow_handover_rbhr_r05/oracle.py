"""Deterministic Python oracle for the Gate-A native fixture boundary only."""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
import numpy as np

from .contracts import Arm, GateAFixture, GateAResult, TICKS


DT = 0.1
BASE = (-600.0, 0.0, 20.0)


def rng_u64(fixture_key: int, address: str) -> int:
    key = int(fixture_key).to_bytes(8, "big", signed=False)
    digest = hashlib.sha256(key + b"\x00" + address.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def rng_uniform(fixture_key: int, address: str) -> float:
    return ((rng_u64(fixture_key, address) >> 11) + 0.5) / float(1 << 53)


def rng_normal(fixture_key: int, address: str) -> float:
    u1 = rng_uniform(fixture_key, address + "/0")
    u2 = rng_uniform(fixture_key, address + "/1")
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def _clip_norm(x: tuple[float, float], limit: float) -> tuple[float, float]:
    norm = math.hypot(*x)
    if norm <= limit or norm == 0.0:
        return x
    scale = limit / max(norm, 1.0e-12)
    return x[0] * scale, x[1] * scale


def _terrain(x: float, y: float) -> float:
    return 135.0 * math.exp(-((x / 75.0) ** 2) - ((y / 220.0) ** 4)) + 55.0 * math.exp(
        -(((x - 90.0) / 35.0) ** 2) - (((y + 40.0) / 85.0) ** 2)
    )


def _blocked(q0: tuple[float, float, float], q1: tuple[float, float, float], clearance: float) -> bool:
    for j in range(1, 128):
        f = j / 128.0
        x = q0[0] + f * (q1[0] - q0[0])
        y = q0[1] + f * (q1[1] - q0[1])
        z = q0[2] + f * (q1[2] - q0[2])
        if z <= _terrain(x, y) + clearance:
            return True
    return False


def _radio_margin(
    fixture: GateAFixture,
    tick: int,
    hop: str,
    q0: tuple[float, float, float],
    q1: tuple[float, float, float],
    extra_penalty: float = 0.0,
) -> float:
    distance = math.dist(q0, q1)
    blocked = 1.0 if _blocked(q0, q1, 8.0) else 0.0
    epsilon = rng_normal(fixture.fixture_key, f"RADIO/{tick}/{hop}")
    return 30.0 - 20.0 * math.log10(max(distance, 1.0) / 100.0) - 35.0 * blocked - extra_penalty + epsilon


def _route(fixture: GateAFixture, tick: int) -> tuple[float, float, float, float]:
    t = tick * DT
    tau = fixture.tau_d_tick * DT
    speed = float(fixture.route_speed)
    theta = fixture.turn_sign * fixture.turn_magnitude_deg * math.pi / 180.0
    if t <= tau:
        x = -speed * tau + speed * t
        y = -120.0
        vx, vy = speed, 0.0
    else:
        x = speed * (t - tau) * math.cos(theta)
        y = -120.0 + speed * (t - tau) * math.sin(theta)
        vx, vy = speed * math.cos(theta), speed * math.sin(theta)
    return x, fixture.reflection * y, vx, fixture.reflection * vy


def _inside_visual_prism(a: tuple[float, float, float], b: tuple[float, float, float], reflection: int) -> bool:
    # Conservative exact segment/prism sampling uses the already registered ray grid.
    for j in range(129):
        f = j / 128.0
        x = a[0] + f * (b[0] - a[0])
        y = a[1] + f * (b[1] - a[1])
        z = a[2] + f * (b[2] - a[2])
        if -20.0 <= x <= 30.0 and -155.0 <= reflection * y <= -85.0 and 0.0 <= z <= 120.0:
            return True
    return False


def _hash_mix(value: int, item: int) -> int:
    value ^= item & 0xFFFFFFFFFFFFFFFF
    return (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF


@dataclass
class _Source:
    sequence: int = -1
    tick: int = -1
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    first_margin: float = -math.inf


@dataclass
class _Relay:
    exists: bool = False
    source: _Source | None = None
    relay_tick: int = -1
    epoch: int = 0
    payload_sequence: int = 0
    sender: int = 0
    second_margin: float = -math.inf


def run_oracle(fixture: GateAFixture) -> GateAResult:
    gx0, gy0, _, _ = _route(fixture, 0)
    qa = (gx0 + fixture.initial_ux, gy0 + fixture.reflection * fixture.initial_uy)
    qb = (gx0 - fixture.initial_ux, gy0 - fixture.reflection * fixture.initial_uy)
    positions = [list(qa), list(qb)]
    velocities = [[0.0, 0.0], [0.0, 0.0]]
    commands = [[0.0, 0.0], [0.0, 0.0]]
    wind = [0.0, 0.0]
    battery = [200000.0, 200000.0]
    owner = fixture.initial_owner
    service_epoch = 0
    next_sequence = 0
    handover_used = 0
    noop_count = 0
    transaction_shell_bytes = 0
    invalid_commit = token_gap = dual_owner = dual_payload = buffer_clear = 0
    separation_breach = 0
    protocol_bytes = 0
    service_ticks = 0
    terminal_tick = -1
    total_energy = 0.0
    source_buffers = [_Source(), _Source()]
    pending_sources: list[_Source | None] = [None, None]
    pending_relay: _Relay | None = None
    base = _Relay()
    countdown = fixture.phase
    k_active = fixture.k_initial
    switch_seen = False
    pending_switch = False
    digest = 1469598103934665603

    for tick in range(TICKS):
        separation = math.dist(positions[0], positions[1])
        terminal = separation < 15.0 or min(battery) <= 0.0 or terminal_tick >= 0
        if terminal and terminal_tick < 0:
            terminal_tick = tick
            separation_breach += int(separation < 15.0)
        if terminal:
            total_energy += 2.0 * 650.0 * DT
            battery[0] = max(0.0, battery[0] - 650.0 * DT)
            battery[1] = max(0.0, battery[1] - 650.0 * DT)
            continue

        for index, delivered in enumerate(pending_sources):
            if delivered is not None and delivered.sequence > source_buffers[index].sequence:
                source_buffers[index] = delivered
        if pending_relay is not None and pending_relay.exists:
            candidate = (
                pending_relay.source.sequence if pending_relay.source else -1,
                pending_relay.relay_tick,
                pending_relay.epoch,
                pending_relay.payload_sequence,
                -pending_relay.sender,
            )
            current = (
                base.source.sequence if base.exists and base.source else -1,
                base.relay_tick,
                base.epoch,
                base.payload_sequence,
                -base.sender,
            )
            if candidate > current:
                base = pending_relay
        pending_sources = [None, None]
        pending_relay = None

        if not switch_seen and fixture.k_new != fixture.k_initial and tick >= fixture.switch_tick:
            pending_switch = True
            switch_seen = True
        renew = countdown == 0
        if renew:
            if pending_switch:
                k_active = fixture.k_new
                pending_switch = False
            countdown = k_active - 1
        else:
            countdown -= 1

        if renew and not handover_used and tick >= fixture.tau_d_tick and tick + 1 < TICKS:
            if fixture.arm in (Arm.STRUCTURED, Arm.FLEX_ZERO, Arm.FORK_REAL):
                owner = 1 - owner
                service_epoch += 1
                handover_used = 1
                transaction_shell_bytes = 24
            elif fixture.arm == Arm.FORK_SHAM:
                service_epoch += 1
                handover_used = 1
                transaction_shell_bytes = 24
            elif fixture.arm == Arm.NEVER:
                noop_count += 1

        gx, gy, gvx, gvy = _route(fixture, tick)
        target = (gx, gy, 0.0)
        for i in range(2):
            role_offset = (-40.0, 0.0) if i == owner else (-300.0, 60.0 * fixture.reflection)
            desired = (gx + role_offset[0], gy + role_offset[1])
            raw = (
                0.08 * (desired[0] - positions[i][0]) - 0.60 * velocities[i][0],
                0.08 * (desired[1] - positions[i][1]) - 0.60 * velocities[i][1],
            )
            bounded = _clip_norm(raw, 3.0)
            delta = _clip_norm((bounded[0] - commands[i][0], bounded[1] - commands[i][1]), 1.5)
            commands[i] = list(_clip_norm((commands[i][0] + delta[0], commands[i][1] + delta[1]), 3.0))

        uav3 = [(positions[i][0], positions[i][1], 90.0) for i in range(2)]
        source_body = _Source(
            sequence=tick,
            tick=tick,
            x=gx + 2.0 * rng_normal(fixture.fixture_key, f"SOURCE/{tick}/PX"),
            y=gy + 2.0 * rng_normal(fixture.fixture_key, f"SOURCE/{tick}/PY"),
            vx=gvx + 0.25 * rng_normal(fixture.fixture_key, f"SOURCE/{tick}/VX"),
            vy=gvy + 0.25 * rng_normal(fixture.fixture_key, f"SOURCE/{tick}/VY"),
        )
        for i in range(2):
            margin = _radio_margin(fixture, tick, f"G_TO_U{i}", target, uav3[i])
            if margin >= 6.0:
                pending_sources[i] = _Source(**{**source_body.__dict__, "first_margin": margin})

        protocol_bytes += 40 + 128
        owner_source = source_buffers[owner]
        if owner_source.sequence >= 0:
            base_point = BASE if fixture.reflection == 1 else (BASE[0], -BASE[1], BASE[2])
            extra = 0.0
            if fixture.package == 1 and fixture.tau_d_tick <= tick < fixture.tau_d_tick + 40 and owner == fixture.initial_owner:
                extra = 35.0
            margin = _radio_margin(fixture, tick, f"U{owner}_TO_BASE", uav3[owner], base_point, extra)
            pending_relay = _Relay(
                exists=margin >= 6.0,
                source=_Source(**owner_source.__dict__),
                relay_tick=tick,
                epoch=service_epoch,
                payload_sequence=next_sequence,
                sender=owner,
                second_margin=margin,
            )
            next_sequence += 1
            protocol_bytes += 64

        if base.exists and base.source is not None:
            age = (tick - base.source.tick) * DT
            estimate = (base.source.x + age * base.source.vx, base.source.y + age * base.source.vy)
            if (
                age <= 0.5
                and math.dist(estimate, (gx, gy)) <= 8.0
                and base.source.first_margin >= 6.0
                and base.second_margin >= 6.0
            ):
                service_ticks += 1

        for i in range(2):
            power = 650.0 + 1.5 * (velocities[i][0] ** 2 + velocities[i][1] ** 2) + 12.0 * (
                commands[i][0] ** 2 + commands[i][1] ** 2
            )
            byte_energy = 0.02 * (64 + (64 if i == owner and source_buffers[i].sequence >= 0 else 0))
            total_energy += DT * power + byte_energy
            battery[i] = max(0.0, battery[i] - DT * power - byte_energy)
            positions[i][0] += DT * velocities[i][0]
            positions[i][1] += DT * velocities[i][1]
            velocities[i] = list(
                _clip_norm(
                    (
                        velocities[i][0] + DT * (commands[i][0] + wind[0]),
                        velocities[i][1] + DT * (commands[i][1] + wind[1]),
                    ),
                    18.0,
                )
            )
        wind[0] = max(-1.5, min(1.5, 0.95 * wind[0] + 0.05 * rng_normal(fixture.fixture_key, f"WIND/{tick}/X")))
        wind[1] = max(-1.5, min(1.5, 0.95 * wind[1] + 0.05 * rng_normal(fixture.fixture_key, f"WIND/{tick}/Y")))
        digest = _hash_mix(digest, tick)
        digest = _hash_mix(digest, owner)
        digest = _hash_mix(digest, service_epoch)
        digest = _hash_mix(digest, next_sequence)
        digest = _hash_mix(digest, int(base.exists))
        digest = _hash_mix(digest, int(renew))

    final_separation = math.dist(positions[0], positions[1])
    return GateAResult(
        service_ticks=service_ticks,
        owner=owner,
        service_epoch=service_epoch,
        next_payload_sequence=next_sequence,
        handover_used=handover_used,
        noop_count=noop_count,
        transaction_shell_bytes=transaction_shell_bytes,
        invalid_commit=invalid_commit,
        token_gap=token_gap,
        dual_owner=dual_owner,
        dual_payload=dual_payload,
        buffer_clear=buffer_clear,
        separation_breach=separation_breach,
        protocol_bytes=protocol_bytes,
        terminal_tick=terminal_tick,
        final_separation=final_separation,
        total_energy=total_energy,
        state_digest=digest,
    )


def generator_first_qualifying(
    fixture_key: int,
    *,
    start: int,
    count: int,
    stratum: int,
) -> int | None:
    if start < 0 or count < 0 or stratum not in (0, 1, 2):
        raise ValueError("invalid generator scan request")
    for ordinal in range(start, start + count):
        value = rng_uniform(fixture_key, f"GENERATOR/{ordinal}/ASSAY")
        if (stratum == 0 and value <= 0.01) or (stratum == 1 and 0.49 <= value <= 0.51) or (stratum == 2 and value >= 0.99):
            return ordinal
    return None


def filter_step_oracle(mean, covariance, *, camera_present: bool, z) -> tuple[tuple[float, ...], tuple[float, ...]]:
    mean_value = np.asarray(mean, dtype=np.float64)
    covariance_value = np.asarray(covariance, dtype=np.float64).reshape(4, 4)
    Fm = np.array([[1,0,DT,0],[0,1,0,DT],[0,0,1,0],[0,0,0,1]], dtype=np.float64)
    process = np.diag([0.04,0.04,0.25,0.25])
    predicted_mean = Fm @ mean_value
    predicted_covariance = Fm @ covariance_value @ Fm.T + process
    if camera_present:
        H = np.array([[1,0,0,0],[0,1,0,0]], dtype=np.float64)
        R = 4.0 * np.eye(2)
        innovation_covariance = H @ predicted_covariance @ H.T + R + 1e-9*np.eye(2)
        gain = predicted_covariance @ H.T @ np.linalg.inv(innovation_covariance)
        predicted_mean = predicted_mean + gain @ (np.asarray(z, dtype=np.float64) - H @ predicted_mean)
        identity = np.eye(4) - gain @ H
        predicted_covariance = identity @ predicted_covariance @ identity.T + gain @ R @ gain.T
    return tuple(predicted_mean), tuple(predicted_covariance.ravel())
