"""Independent literal reference oracle for deterministic S0 fixtures."""

from __future__ import annotations

from .contract import (
    FixtureInput,
    HORIZON,
    MissionEndpoint,
    MissionResult,
    SetupSnapshot,
    TaskState,
    TickRecord,
    decode_action,
    public_observation,
)


def _clip(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _setup(fixture: FixtureInput) -> tuple[TaskState, SetupSnapshot]:
    hidden_d = 0.0
    mode = 0
    for token in fixture.event_order.tokens:
        if token == "RETENSION":
            mode = 1
        else:
            hidden_d = _clip(hidden_d + 0.55 * mode, 0.0, 1.0)
    state = TaskState(
        0.0,
        fixture.initial_v,
        fixture.initial_phi,
        0.0,
        0.0,
        0.0,
        (0.0, 0.0, 0.0),
        (0, 0, 0),
        hidden_d,
        mode,
        0,
    )
    return state, SetupSnapshot(
        public_observation(state, fixture.regime.initial_k),
        hidden_d,
        mode,
        fixture.event_order.tokens,
        fixture.event_order.q,
    )


def _endpoint(trace: tuple[TickRecord, ...], state: TaskState) -> MissionEndpoint:
    last = trace[-1]
    integrated = len(trace)
    physical = last.overload or last.swing or last.formation
    return MissionEndpoint(
        HORIZON,
        integrated,
        HORIZON - integrated,
        sum(record.policy_queried for record in trace),
        last.delivery,
        last.timeout,
        physical,
        last.overload,
        last.swing,
        last.formation,
        integrated,
        0.1 * integrated if last.delivery else None,
        0.1 * integrated if last.delivery else 42.0,
        sum(record.reward for record in trace),
        sum(record.effort for record in trace) / integrated,
        state,
    )


def oracle_run_fixture(fixture: FixtureInput) -> MissionResult:
    fixture.validate()
    state, setup = _setup(fixture)
    records: list[TickRecord] = []
    query = 0
    terminal = False
    while state.n < HORIZON and not terminal:
        k = (
            fixture.regime.initial_k
            if not fixture.regime.switched or state.n < fixture.switch_tick
            else fixture.regime.final_k
        )
        command = decode_action(fixture.actions[query])
        code = fixture.actions[query]
        query += 1
        for offset in range(k):
            if state.n >= HORIZON or terminal:
                break
            tick = state.n
            a = sum(command) / 3.0
            b = max(abs(value - a) for value in command)
            tensions = tuple(
                0.42
                + 0.17 * value
                + 0.11 * abs(value - a)
                + 0.20 * state.hidden_d * a * a
                + 0.07 * abs(state.phi)
                for value in command
            )
            capacity = 1.04 - 0.16 * state.hidden_d
            excess = max(0.0, max(tensions) - capacity)
            omega = (
                0.90 * state.omega
                - 0.12 * state.phi
                + 0.055 * b
                + 0.035 * state.hidden_d * a
                + fixture.eta_omega[tick]
            )
            phi = _clip(state.phi + 0.1 * omega, -0.70, 0.70)
            v = _clip(
                0.94 * state.v
                + 0.06 * a
                - 0.018 * state.hidden_d * a * a
                - 0.025 * abs(phi)
                + fixture.eta_v[tick],
                0.0,
                1.8,
            )
            x = state.x + 0.1 * v
            z = 0.86 * state.z + excess
            formation_value = 0.84 * state.f + 0.09 * b + 0.08 * abs(phi)
            next_n = state.n + 1
            overload = z > 0.55
            swing = abs(phi) > 0.48
            formation = formation_value > 0.42
            physical = overload or swing or formation
            delivery = not physical and x >= 36.0
            timeout = not physical and not delivery and next_n >= HORIZON
            terminal = physical or delivery or timeout
            reward = (
                0.02 * (x - state.x)
                - 0.001 * sum(value * value for value in command) / 3.0
                - 0.002 * phi * phi
                - 0.002 * formation_value * formation_value
            )
            reward += 1.0 if delivery else -1.0 if physical else -0.5 if timeout else 0.0
            effort = sum(value * value for value in command) / 12.0
            state = TaskState(
                x,
                v,
                phi,
                omega,
                z,
                formation_value,
                tensions,
                command,
                state.hidden_d,
                state.mode,
                next_n,
            )
            records.append(
                TickRecord(
                    tick,
                    k,
                    offset == 0,
                    code,
                    command,
                    records[-1].x_after if records else 0.0,
                    x,
                    v,
                    phi,
                    omega,
                    z,
                    formation_value,
                    tensions,
                    reward,
                    effort,
                    overload,
                    swing,
                    formation,
                    delivery,
                    timeout,
                    terminal,
                )
            )
    trace = tuple(records)
    return MissionResult(setup, trace, _endpoint(trace, state))
