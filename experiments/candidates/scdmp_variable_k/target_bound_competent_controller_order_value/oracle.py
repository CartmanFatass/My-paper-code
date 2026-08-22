"""TEST-ONLY Python oracle for TBCC native-host conformance.

THIS MODULE IS NOT A PRODUCTION ENVIRONMENT OR ROLLOUT PATH.  Production code
must use :mod:`native_backend`; these routines exist solely to compare frozen
deterministic fixtures against the task-specific C++ implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import fabs, pi, sin

from .config import ACTIONS, FORMATION_ROTATE, HOOK_HANDOFF, HORIZON_TICKS, MAX_HOLD_TICKS
from .host_types import HostOutput, RenewalLane, ResetLane

TEST_ONLY_ORACLE = True


def test_only_compose_setup(events: tuple[int, int]) -> tuple[tuple[int, ...], int]:
    """Return the latent assignment/q for a frozen deterministic TEST fixture."""

    if events not in (
        (HOOK_HANDOFF, FORMATION_ROTATE),
        (FORMATION_ROTATE, HOOK_HANDOFF),
    ):
        raise ValueError("events must be the exact H/R permutation")
    p = (1, 2, 3, 4)
    for event in events:
        if event == HOOK_HANDOFF:
            p = (p[1], p[0], p[2], p[3])
        else:
            p = (p[3], p[0], p[1], p[2])
    if p == (4, 2, 1, 3):
        return p, 1
    if p == (1, 4, 2, 3):
        return p, 0
    raise AssertionError("frozen setup composition produced an unregistered assignment")


@dataclass(frozen=True, slots=True)
class TestOnlyState:
    """Complete latent oracle state; never accepted by the production loader."""

    x: float
    v: float
    y: float
    w: float
    phi: float
    omega: float
    z: tuple[float, float, float, float]
    formation: float
    prior_a: int
    prior_r: tuple[int, int, int, int]
    p: tuple[int, int, int, int]
    q: int
    tick: int
    current_k: int
    k_after: int
    switch_tick: int
    switched: bool
    terminal: bool = False
    active: bool = True
    safe_dock: bool = False
    timeout: bool = False
    cable_overload: bool = False
    gantry_contact: bool = False
    attitude_loss: bool = False
    formation_loss: bool = False
    cumulative_reward: float = 0.0
    cumulative_energy: float = 0.0
    energy_ticks: int = 0
    dock_tick: int = -1
    last_primitive_reward: float = 0.0
    last_hold_rewards: tuple[float, ...] = ()


def _b(q: int) -> tuple[float, float, float, float]:
    return (1.0, -1.0, 0.0, 0.0) if q == 1 else (0.0, 0.0, 1.0, -1.0)


def _y_ref(x: float) -> float:
    if 8.0 <= x < 16.0:
        return 0.18 * sin(pi * (x - 8.0) / 8.0)
    return 0.0


def _clip(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def test_only_reset(reset: ResetLane) -> TestOnlyState:
    reset.validate()
    p, q = test_only_compose_setup(reset.middle_events)
    return TestOnlyState(
        x=0.0,
        v=float(reset.initial_v),
        y=float(reset.initial_y),
        w=0.0,
        phi=float(reset.initial_phi),
        omega=0.0,
        z=(0.0, 0.0, 0.0, 0.0),
        formation=0.0,
        prior_a=1,
        prior_r=(0, 0, 0, 0),
        p=p,
        q=q,
        tick=0,
        current_k=reset.k_initial,
        k_after=reset.resolved_k_after,
        switch_tick=reset.resolved_switch_tick,
        switched=False,
        active=reset.active,
        terminal=not reset.active,
    )


def _activate_switch(state: TestOnlyState) -> TestOnlyState:
    if state.switch_tick and not state.switched and state.tick == state.switch_tick:
        return replace(state, current_k=state.k_after, switched=True)
    return state


def test_only_observation(state: TestOnlyState) -> tuple[float, ...]:
    return (
        state.x / 24.5,
        state.v / 1.6,
        state.y / 0.40,
        state.w / 0.25,
        state.phi / 0.35,
        state.omega / 0.40,
        *(value / 0.25 for value in state.z),
        state.formation / 0.40,
        state.prior_a / 2.0,
        *(float(value) for value in state.prior_r),
        state.current_k / 13.0,
        state.tick / 364.0,
    )


def test_only_primitive(
    state: TestOnlyState,
    action: int,
    eta_v: float,
    eta_y: float,
    eta_omega: float,
) -> TestOnlyState:
    """Apply exactly one frozen primitive tick for conformance only."""

    if state.terminal or not state.active:
        raise ValueError("TEST oracle cannot advance an inactive/terminal state")
    a, *r_values = ACTIONS[action]
    r = tuple(int(value) for value in r_values)
    b = _b(state.q)
    e = state.y - _y_ref(state.x)
    tau = tuple(
        0.38 + 0.12 * a + 0.16 * a * max(component, 0.0)
        - 0.10 * r_i + 0.04 * fabs(state.phi) + 0.03 * fabs(e)
        for component, r_i in zip(b, r)
    )
    tau_bar = sum(tau) / 4.0
    mu = 0.5 * sum(component * (load - tau_bar) for component, load in zip(b, tau))
    nu = 0.25 * (r[0] + r[3] - r[1] - r[2])
    omega = 0.90 * state.omega - 0.12 * state.phi + 0.08 * mu + 0.02 * state.w + eta_omega
    phi = _clip(state.phi + 0.1 * omega, -0.50, 0.50)
    w = 0.88 * state.w - 0.10 * e - 0.03 * state.phi + 0.025 * nu + eta_y
    y = state.y + 0.1 * w
    v = _clip(
        0.92 * state.v + 0.08 * (0.75 * a) - 0.02 * fabs(phi) - 0.02 * fabs(e) + eta_v,
        0.0,
        1.60,
    )
    x = state.x + 0.1 * v
    z = tuple(0.84 * value + max(0.0, load - 0.88) for value, load in zip(state.z, tau))
    formation = 0.86 * state.formation + 0.04 * max(abs(value) for value in r) + 0.05 * fabs(phi) + 0.04 * fabs(e)
    tick = state.tick + 1
    cable = max(z) > 0.25
    gantry = 8.0 <= x <= 16.0 and 0.30 - fabs(y - _y_ref(x)) - 0.55 * fabs(phi) <= 0.0
    attitude = fabs(phi) > 0.32
    form_loss = formation > 0.40
    physical_failure = cable or gantry or attitude or form_loss
    safe = (
        not physical_failure and x >= 24.5 and fabs(y) <= 0.08 and fabs(phi) <= 0.08
        and max(z) <= 0.25 and formation <= 0.40
    )
    timeout = tick >= HORIZON_TICKS and not safe and not physical_failure
    terminal = physical_failure or safe or timeout
    mean_power = sum((a + 0.35 * value) ** 2 for value in r) / 4.0
    reward = (
        0.015 * (x - state.x)
        - 0.001 * mean_power
        - 0.002 * phi * phi
        - 0.002 * (y - _y_ref(x)) ** 2
    )
    if safe:
        reward += 1.0
    elif physical_failure:
        reward -= 1.0
    elif timeout:
        reward -= 0.4
    return replace(
        state,
        x=x,
        v=v,
        y=y,
        w=w,
        phi=phi,
        omega=omega,
        z=z,
        formation=formation,
        prior_a=a,
        prior_r=r,
        tick=tick,
        terminal=terminal,
        safe_dock=safe,
        timeout=timeout,
        cable_overload=cable,
        gantry_contact=gantry,
        attitude_loss=attitude,
        formation_loss=form_loss,
        cumulative_reward=state.cumulative_reward + reward,
        cumulative_energy=state.cumulative_energy + mean_power,
        energy_ticks=state.energy_ticks + 1,
        dock_tick=tick if safe else state.dock_tick,
        last_primitive_reward=reward,
    )


def test_only_renewal(state: TestOnlyState, row: RenewalLane) -> tuple[TestOnlyState, int]:
    row.validate()
    state = _activate_switch(state)
    if not row.active:
        return state, len(state.last_hold_rewards)
    if state.terminal or not state.active:
        raise ValueError("TEST oracle cannot advance an inactive/terminal state")
    held_k = state.current_k
    steps = min(held_k, HORIZON_TICKS - state.tick)
    advanced = 0
    rewards: list[float] = []
    for offset in range(steps):
        state = test_only_primitive(
            state,
            row.action,
            row.eta_v[offset],
            row.eta_y[offset],
            row.eta_omega[offset],
        )
        rewards.append(state.last_primitive_reward)
        advanced += 1
        if state.terminal:
            break
    state = _activate_switch(state)
    state = replace(state, last_hold_rewards=tuple(rewards))
    return state, advanced


def test_only_output(state: TestOnlyState, *, advanced: int, hold_k: int) -> HostOutput:
    rewards = state.last_hold_rewards
    if len(rewards) != advanced:
        raise ValueError("TEST oracle reward trace/count does not match advanced ticks")
    padded_rewards = rewards + (0.0,) * (MAX_HOLD_TICKS - len(rewards))
    return HostOutput(
        advanced=advanced > 0,
        active=state.active and not state.terminal,
        terminal=state.terminal,
        ticks_advanced=advanced,
        tick=state.tick,
        hold_k=hold_k,
        next_k=state.current_k,
        observation=test_only_observation(state),
        safe_dock=state.safe_dock,
        timeout=state.timeout,
        cable_overload=state.cable_overload,
        gantry_contact=state.gantry_contact,
        attitude_loss=state.attitude_loss,
        formation_loss=state.formation_loss,
        cumulative_reward=state.cumulative_reward,
        cumulative_energy=state.cumulative_energy,
        energy_ticks=state.energy_ticks,
        dock_tick=None if state.dock_tick < 0 else state.dock_tick,
        last_hold_reward_count=len(rewards),
        last_hold_rewards=padded_rewards,
    )


def test_only_public_first_renewal(reset: ResetLane) -> tuple[float, ...]:
    """Public first-renewal alias used only by deterministic conformance tests."""

    return test_only_observation(test_only_reset(reset))
