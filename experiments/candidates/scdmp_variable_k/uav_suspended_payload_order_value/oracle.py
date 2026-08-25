"""Fixture-only Python oracle for the frozen native host semantics.

The oracle is intentionally unreachable from production preactivity and only
accepts the deterministic construction namespace.  It is a conformance oracle,
not a fallback implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import EventOrder, FixtureInput, HORIZON, Regime, decode_action
from .host_types import (
    MissionEndpoint,
    MissionResult,
    PublicObservation,
    SetupSnapshot,
    TickRecord,
)


@dataclass
class _State:
    x: float
    v: float
    phi: float
    omega: float
    z: float
    f: float
    tensions: tuple[float, float, float]
    previous: tuple[int, int, int]
    d: float
    mode: int
    n: int


def _clip(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _current_k(regime: Regime, switch_tick: int, tick: int) -> int:
    if not regime.switched or tick < switch_tick:
        return regime.initial_k
    return regime.final_k


def _public(state: _State, k: int) -> PublicObservation:
    """Expose the exact 14-vector; latent reserve is structurally absent."""

    return PublicObservation(
        x=state.x / 36.0,
        v=state.v / 1.8,
        phi=state.phi / 0.48,
        omega=state.omega / 0.5,
        z=state.z / 0.55,
        f=state.f / 0.42,
        tau_1=state.tensions[0] / 1.25,
        tau_2=state.tensions[1] / 1.25,
        tau_3=state.tensions[2] / 1.25,
        u_1_previous=state.previous[0] / 2.0,
        u_2_previous=state.previous[1] / 2.0,
        u_3_previous=state.previous[2] / 2.0,
        mission_fraction=state.n / 420.0,
        k_scaled=k / 14.0,
    )


def setup_fixture(fixture: FixtureInput) -> tuple[_State, SetupSnapshot]:
    """Apply both setup slots, then the exact public recentering operation."""

    fixture.validate()
    d = 0.0
    mode = 0
    for token in fixture.event_order.tokens:
        if token == "RETENSION":
            mode = 1
        elif token == "CROSSWIND":
            d = _clip(d + 0.55 * mode, 0.0, 1.0)
        else:  # pragma: no cover - enum owns the complete token registry
            raise AssertionError(f"unknown setup token {token}")
    state = _State(
        x=0.0,
        v=fixture.initial_v,
        phi=fixture.initial_phi,
        omega=0.0,
        z=0.0,
        f=0.0,
        tensions=(0.0, 0.0, 0.0),
        previous=(0, 0, 0),
        d=d,
        mode=mode,
        n=0,
    )
    snapshot = SetupSnapshot(
        public=_public(state, fixture.regime.initial_k),
        hidden_d_fixture_audit=d,
        mode=mode,
        event_tokens=fixture.event_order.tokens,
        chronology_q=fixture.event_order.q,
    )
    return state, snapshot


def run_fixture(fixture: FixtureInput) -> MissionResult:
    """Run one deterministic fixture from setup through absorption/timeout."""

    state, setup = setup_fixture(fixture)
    records: list[TickRecord] = []
    query = 0
    terminal = False
    final_flags = (False, False, False)
    delivered = False
    timed_out = False

    while state.n < HORIZON and not terminal:
        k = _current_k(fixture.regime, fixture.switch_tick, state.n)
        if query >= len(fixture.actions):
            raise ValueError("fixture action tape ended before the mission terminal")
        code = fixture.actions[query]
        command = decode_action(code)
        query += 1

        for offset in range(k):
            if state.n >= HORIZON or terminal:
                break
            tick = state.n
            x_before = state.x
            a = sum(command) / 3.0
            b = max(abs(value - a) for value in command)
            tensions = tuple(
                0.42
                + 0.17 * value
                + 0.11 * abs(value - a)
                + 0.20 * state.d * a * a
                + 0.07 * abs(state.phi)
                for value in command
            )
            capacity = 1.04 - 0.16 * state.d
            epsilon = max(0.0, max(tensions) - capacity)
            omega = (
                0.90 * state.omega
                - 0.12 * state.phi
                + 0.055 * b
                + 0.035 * state.d * a
                + fixture.eta_omega[tick]
            )
            phi = _clip(state.phi + 0.1 * omega, -0.70, 0.70)
            v = _clip(
                0.94 * state.v
                + 0.06 * a
                - 0.018 * state.d * a * a
                - 0.025 * abs(phi)
                + fixture.eta_v[tick],
                0.0,
                1.8,
            )
            x = state.x + 0.1 * v
            z = 0.86 * state.z + epsilon
            f = 0.84 * state.f + 0.09 * b + 0.08 * abs(phi)
            next_n = state.n + 1

            overload = z > 0.55
            swing = abs(phi) > 0.48
            formation = f > 0.42
            physical_failure = overload or swing or formation
            delivery = (not physical_failure) and x >= 36.0
            timeout = (
                (not physical_failure) and (not delivery) and next_n >= HORIZON
            )
            terminal = physical_failure or delivery or timeout
            effort = sum(value * value for value in command) / 12.0
            reward = (
                0.02 * (x - state.x)
                - 0.001 * sum(value * value for value in command) / 3.0
                - 0.002 * phi * phi
                - 0.002 * f * f
            )
            if delivery:
                reward += 1.0
            elif physical_failure:
                reward -= 1.0
            elif timeout:
                reward -= 0.5

            state = _State(
                x=x,
                v=v,
                phi=phi,
                omega=omega,
                z=z,
                f=f,
                tensions=tensions,
                previous=command,
                d=state.d,
                mode=state.mode,
                n=next_n,
            )
            records.append(
                TickRecord(
                    tick=tick,
                    k=k,
                    policy_queried=offset == 0,
                    action_code=code,
                    command=command,
                    x_before=x_before,
                    x_after=x,
                    v_after=v,
                    phi_after=phi,
                    omega_after=omega,
                    z_after=z,
                    f_after=f,
                    tensions_after=tensions,
                    reward=reward,
                    effort=effort,
                    overload=overload,
                    swing=swing,
                    formation=formation,
                    delivery=delivery,
                    timeout=timeout,
                    terminal=terminal,
                )
            )
            if terminal:
                final_flags = (overload, swing, formation)
                delivered, timed_out = delivery, timeout

    trace = tuple(records)
    endpoint = _endpoint_from_parts(
        trace=trace,
        state=state,
        queries=query,
        delivered=delivered,
        timed_out=timed_out,
        flags=final_flags,
    )
    result = MissionResult(setup=setup, trace=trace, endpoint=endpoint)
    recomputed = recompute_endpoint(result)
    if recomputed != endpoint:
        raise AssertionError("fixture oracle endpoint is not trace-recomputable")
    return result


def _endpoint_from_parts(
    *,
    trace: tuple[TickRecord, ...],
    state: _State,
    queries: int,
    delivered: bool,
    timed_out: bool,
    flags: tuple[bool, bool, bool],
) -> MissionEndpoint:
    integrated = len(trace)
    physical = any(flags)
    return MissionEndpoint(
        allocated_slots=HORIZON,
        integrated_ticks=integrated,
        masked_post_absorption_slots=HORIZON - integrated,
        policy_queries=queries,
        delivery=delivered,
        timeout=timed_out,
        physical_failure=physical,
        overload=flags[0],
        swing=flags[1],
        formation=flags[2],
        terminal_tick=integrated,
        delivery_time_seconds=0.1 * integrated if delivered else None,
        completion_time_seconds=0.1 * integrated if delivered else 42.0,
        cumulative_reward=sum(record.reward for record in trace),
        mean_active_effort=(
            sum(record.effort for record in trace) / integrated if integrated else 0.0
        ),
        final_x=state.x,
        final_v=state.v,
        final_phi=state.phi,
        final_omega=state.omega,
        final_z=state.z,
        final_f=state.f,
        final_tensions=state.tensions,
        hidden_d_fixture_audit=state.d,
        mode=state.mode,
    )


def recompute_endpoint(result: MissionResult) -> MissionEndpoint:
    """Recompute every endpoint/accounting field solely from the trace."""

    trace = result.trace
    if not trace:
        raise ValueError("a complete reset-to-terminal trace cannot be empty")
    last = trace[-1]
    if not last.terminal or any(record.terminal for record in trace[:-1]):
        raise ValueError("trace must contain exactly one final terminal record")
    if any(record.tick != index for index, record in enumerate(trace)):
        raise ValueError("trace primitive ticks are not contiguous from zero")
    queries = sum(record.policy_queried for record in trace)
    physical = last.overload or last.swing or last.formation
    if physical and last.delivery:
        raise ValueError("physical failure must dominate same-tick delivery")
    integrated = len(trace)
    return MissionEndpoint(
        allocated_slots=HORIZON,
        integrated_ticks=integrated,
        masked_post_absorption_slots=HORIZON - integrated,
        policy_queries=queries,
        delivery=last.delivery,
        timeout=last.timeout,
        physical_failure=physical,
        overload=last.overload,
        swing=last.swing,
        formation=last.formation,
        terminal_tick=integrated,
        delivery_time_seconds=0.1 * integrated if last.delivery else None,
        completion_time_seconds=0.1 * integrated if last.delivery else 42.0,
        cumulative_reward=sum(record.reward for record in trace),
        mean_active_effort=sum(record.effort for record in trace) / integrated,
        final_x=last.x_after,
        final_v=last.v_after,
        final_phi=last.phi_after,
        final_omega=last.omega_after,
        final_z=last.z_after,
        final_f=last.f_after,
        final_tensions=last.tensions_after,
        hidden_d_fixture_audit=result.setup.hidden_d_fixture_audit,
        mode=result.setup.mode,
    )
