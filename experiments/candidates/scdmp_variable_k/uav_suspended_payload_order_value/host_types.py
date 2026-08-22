"""Immutable host observations, traces, and endpoint records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PublicObservation:
    x: float
    v: float
    phi: float
    omega: float
    z: float
    f: float
    tau_1: float
    tau_2: float
    tau_3: float
    u_1_previous: float
    u_2_previous: float
    u_3_previous: float
    mission_fraction: float
    k_scaled: float

    def vector(self) -> tuple[float, ...]:
        return tuple(self.__dict__.values())


@dataclass(frozen=True)
class SetupSnapshot:
    public: PublicObservation
    hidden_d_fixture_audit: float
    mode: int
    event_tokens: tuple[str, str]
    chronology_q: float


@dataclass(frozen=True)
class TickRecord:
    tick: int
    k: int
    policy_queried: bool
    action_code: int
    command: tuple[int, int, int]
    x_before: float
    x_after: float
    v_after: float
    phi_after: float
    omega_after: float
    z_after: float
    f_after: float
    tensions_after: tuple[float, float, float]
    reward: float
    effort: float
    overload: bool
    swing: bool
    formation: bool
    delivery: bool
    timeout: bool
    terminal: bool


@dataclass(frozen=True)
class MissionEndpoint:
    allocated_slots: int
    integrated_ticks: int
    masked_post_absorption_slots: int
    policy_queries: int
    delivery: bool
    timeout: bool
    physical_failure: bool
    overload: bool
    swing: bool
    formation: bool
    terminal_tick: int
    delivery_time_seconds: float | None
    completion_time_seconds: float
    cumulative_reward: float
    mean_active_effort: float
    final_x: float
    final_v: float
    final_phi: float
    final_omega: float
    final_z: float
    final_f: float
    final_tensions: tuple[float, float, float]
    hidden_d_fixture_audit: float
    mode: int


@dataclass(frozen=True)
class MissionResult:
    setup: SetupSnapshot
    trace: tuple[TickRecord, ...]
    endpoint: MissionEndpoint


@dataclass(frozen=True)
class RenewalAccounting:
    allocated_slots: int
    integrated_ticks: int
    masked_post_absorption_slots: int
    policy_queries: int
    terminal_tick: int | None
    delivery_time_seconds: float | None
    completion_time_seconds: float | None
    cumulative_reward: float
    mean_active_effort: float


@dataclass(frozen=True)
class RenewalTransition:
    """Controller-facing native renewal output with no latent host state."""

    public: PublicObservation
    event_tokens: tuple[str, str]
    chronology_q: float
    realized_duration: int
    primitive_rewards: tuple[float, ...]
    reward: float
    terminal: bool
    delivery: bool
    timeout: bool
    physical_failure: bool
    overload: bool
    swing: bool
    formation: bool
    accounting: RenewalAccounting
