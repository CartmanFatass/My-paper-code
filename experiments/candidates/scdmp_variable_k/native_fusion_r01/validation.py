"""Independent S0 trace and endpoint conformance checks."""

from __future__ import annotations

from .contract import HORIZON, MissionEndpoint, MissionResult, TaskState


def recompute_endpoint(result: MissionResult) -> MissionEndpoint:
    """Rebuild the endpoint from the public trace and setup audit fields."""

    trace = result.trace
    if not trace:
        raise ValueError("complete S0 trace cannot be empty")
    if any(row.tick != index for index, row in enumerate(trace)):
        raise ValueError("trace ticks must be contiguous from zero")
    if not trace[-1].terminal or any(row.terminal for row in trace[:-1]):
        raise ValueError("trace must have exactly one final terminal record")
    last = trace[-1]
    physical = last.overload or last.swing or last.formation
    if physical and last.delivery:
        raise ValueError("physical failure must dominate same-tick delivery")
    if sum((last.delivery, last.timeout, physical)) != 1:
        raise ValueError("terminal record must select exactly one endpoint class")
    count = len(trace)
    state = TaskState(
        x=last.x_after,
        v=last.v_after,
        phi=last.phi_after,
        omega=last.omega_after,
        z=last.z_after,
        f=last.f_after,
        tensions=last.tensions_after,
        previous=last.command,
        hidden_d=result.setup.hidden_d_fixture_audit,
        mode=result.setup.mode,
        n=count,
    )
    return MissionEndpoint(
        allocated_slots=HORIZON,
        integrated_ticks=count,
        masked_post_absorption_slots=HORIZON - count,
        policy_queries=sum(row.policy_queried for row in trace),
        delivery=last.delivery,
        timeout=last.timeout,
        physical_failure=physical,
        overload=last.overload,
        swing=last.swing,
        formation=last.formation,
        terminal_tick=count,
        delivery_time_seconds=0.1 * count if last.delivery else None,
        completion_time_seconds=0.1 * count if last.delivery else 42.0,
        cumulative_reward=sum(row.reward for row in trace),
        mean_active_effort=sum(row.effort for row in trace) / count,
        final_state=state,
    )
