"""Candidate-native S0 path, deliberately independent from the oracle module."""

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


def _bounded(value: float, minimum: float, maximum: float) -> float:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def _native_setup(fixture: FixtureInput) -> tuple[TaskState, SetupSnapshot]:
    mode = 0
    reserve = 0.0
    for event in fixture.event_order.tokens:
        if event == "CROSSWIND":
            reserve = _bounded(reserve + 0.55 * mode, 0.0, 1.0)
        elif event == "RETENSION":
            mode = 1
        else:  # pragma: no cover - EventOrder owns the complete registry
            raise AssertionError("unregistered event")
    state = TaskState(
        x=0.0,
        v=fixture.initial_v,
        phi=fixture.initial_phi,
        omega=0.0,
        z=0.0,
        f=0.0,
        tensions=(0.0, 0.0, 0.0),
        previous=(0, 0, 0),
        hidden_d=reserve,
        mode=mode,
        n=0,
    )
    snapshot = SetupSnapshot(
        public_observation=public_observation(state, fixture.regime.initial_k),
        hidden_d_fixture_audit=reserve,
        mode=mode,
        event_tokens=fixture.event_order.tokens,
        chronology_q_fixture_audit=fixture.event_order.q,
    )
    return state, snapshot


def _native_endpoint(records: list[TickRecord], state: TaskState) -> MissionEndpoint:
    final = records[-1]
    count = len(records)
    failed = final.overload or final.swing or final.formation
    return MissionEndpoint(
        allocated_slots=HORIZON,
        integrated_ticks=count,
        masked_post_absorption_slots=HORIZON - count,
        policy_queries=sum(int(row.policy_queried) for row in records),
        delivery=final.delivery,
        timeout=final.timeout,
        physical_failure=failed,
        overload=final.overload,
        swing=final.swing,
        formation=final.formation,
        terminal_tick=count,
        delivery_time_seconds=count / 10.0 if final.delivery else None,
        completion_time_seconds=count / 10.0 if final.delivery else 42.0,
        cumulative_reward=sum(row.reward for row in records),
        mean_active_effort=sum(row.effort for row in records) / count,
        final_state=state,
    )


def native_run_fixture(fixture: FixtureInput) -> MissionResult:
    fixture.validate()
    state, setup = _native_setup(fixture)
    rows: list[TickRecord] = []
    action_index = 0
    absorbed = False
    while state.n < HORIZON and not absorbed:
        announced_k = fixture.regime.initial_k
        if fixture.regime.switched and state.n >= fixture.switch_tick:
            announced_k = fixture.regime.final_k
        encoded = fixture.actions[action_index]
        control = decode_action(encoded)
        action_index += 1
        for hold_offset in range(announced_k):
            if absorbed or state.n == HORIZON:
                break
            primitive_tick = state.n
            old_x = state.x
            mean_command = (control[0] + control[1] + control[2]) / 3.0
            dispersion = max(abs(item - mean_command) for item in control)
            new_tensions = tuple(
                0.42
                + 0.17 * item
                + 0.11 * abs(item - mean_command)
                + 0.20 * state.hidden_d * mean_command**2
                + 0.07 * abs(state.phi)
                for item in control
            )
            capacity = 1.04 - 0.16 * state.hidden_d
            epsilon = max(0.0, max(new_tensions) - capacity)
            new_omega = (
                0.90 * state.omega
                - 0.12 * state.phi
                + 0.055 * dispersion
                + 0.035 * state.hidden_d * mean_command
                + fixture.eta_omega[primitive_tick]
            )
            new_phi = _bounded(state.phi + 0.1 * new_omega, -0.70, 0.70)
            new_v = _bounded(
                0.94 * state.v
                + 0.06 * mean_command
                - 0.018 * state.hidden_d * mean_command * mean_command
                - 0.025 * abs(new_phi)
                + fixture.eta_v[primitive_tick],
                0.0,
                1.8,
            )
            new_x = state.x + 0.1 * new_v
            new_z = 0.86 * state.z + epsilon
            new_f = 0.84 * state.f + 0.09 * dispersion + 0.08 * abs(new_phi)
            new_n = state.n + 1
            overload = new_z > 0.55
            swing = abs(new_phi) > 0.48
            formation = new_f > 0.42
            failed = overload or swing or formation
            delivered = not failed and new_x >= 36.0
            timed_out = not failed and not delivered and new_n >= HORIZON
            absorbed = failed or delivered or timed_out
            squared = sum(item * item for item in control)
            tick_reward = (
                0.02 * (new_x - old_x)
                - 0.001 * squared / 3.0
                - 0.002 * new_phi * new_phi
                - 0.002 * new_f * new_f
            )
            if delivered:
                tick_reward += 1.0
            elif failed:
                tick_reward -= 1.0
            elif timed_out:
                tick_reward -= 0.5
            state = TaskState(
                new_x,
                new_v,
                new_phi,
                new_omega,
                new_z,
                new_f,
                new_tensions,
                control,
                state.hidden_d,
                state.mode,
                new_n,
            )
            rows.append(
                TickRecord(
                    primitive_tick,
                    announced_k,
                    hold_offset == 0,
                    encoded,
                    control,
                    old_x,
                    new_x,
                    new_v,
                    new_phi,
                    new_omega,
                    new_z,
                    new_f,
                    new_tensions,
                    tick_reward,
                    squared / 12.0,
                    overload,
                    swing,
                    formation,
                    delivered,
                    timed_out,
                    absorbed,
                )
            )
    return MissionResult(setup, tuple(rows), _native_endpoint(rows, state))
