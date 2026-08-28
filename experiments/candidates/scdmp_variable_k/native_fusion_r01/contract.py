"""Frozen, identity-free S0 task-law records and deterministic fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Final, Iterable


REVISION: Final[str] = "SCDMP-NATIVE-FUSION-SCIENCE-20260827-01"
S0_SLICE: Final[str] = "SCDMP-NATIVE-FUSION-R01-S0-SOURCE-CONFORMANCE-V1"
HOST: Final[str] = "TRI-UAV-SLING-CORRIDOR-36M-v1"
FIXTURE_NAMESPACE: Final[str] = (
    "SCDMP-NATIVE-FUSION-R01/S0/result-blind-conformance-fixture"
)
HORIZON: Final[int] = 420
ACTION_COUNT: Final[int] = 27
MAX_QUERIES: Final[int] = 105


class EventOrder(str, Enum):
    RG = "RG"
    GR = "GR"

    @property
    def tokens(self) -> tuple[str, str]:
        if self is EventOrder.RG:
            return ("RETENSION", "CROSSWIND")
        return ("CROSSWIND", "RETENSION")

    @property
    def q(self) -> float:
        return 1.0 if self is EventOrder.RG else 0.0


class Regime(str, Enum):
    FIXED_4 = "fixed-4"
    FIXED_10 = "fixed-10"
    FIXED_6 = "fixed-6"
    FIXED_14 = "fixed-14"
    SWITCH_6_TO_14 = "6-to-14"
    SWITCH_14_TO_6 = "14-to-6"

    @property
    def initial_k(self) -> int:
        return {
            Regime.FIXED_4: 4,
            Regime.FIXED_10: 10,
            Regime.FIXED_6: 6,
            Regime.FIXED_14: 14,
            Regime.SWITCH_6_TO_14: 6,
            Regime.SWITCH_14_TO_6: 14,
        }[self]

    @property
    def final_k(self) -> int:
        return {
            Regime.FIXED_4: 4,
            Regime.FIXED_10: 10,
            Regime.FIXED_6: 6,
            Regime.FIXED_14: 14,
            Regime.SWITCH_6_TO_14: 14,
            Regime.SWITCH_14_TO_6: 6,
        }[self]

    @property
    def switched(self) -> bool:
        return self in (Regime.SWITCH_6_TO_14, Regime.SWITCH_14_TO_6)


@dataclass(frozen=True)
class TaskState:
    x: float
    v: float
    phi: float
    omega: float
    z: float
    f: float
    tensions: tuple[float, float, float]
    previous: tuple[int, int, int]
    hidden_d: float
    mode: int
    n: int


@dataclass(frozen=True)
class SetupSnapshot:
    public_observation: tuple[float, ...]
    hidden_d_fixture_audit: float
    mode: int
    event_tokens: tuple[str, str]
    chronology_q_fixture_audit: float


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
    final_state: TaskState


@dataclass(frozen=True)
class MissionResult:
    setup: SetupSnapshot
    trace: tuple[TickRecord, ...]
    endpoint: MissionEndpoint


@dataclass(frozen=True)
class FixtureInput:
    namespace: str
    event_order: EventOrder
    regime: Regime
    switch_tick: int
    initial_v: float
    initial_phi: float
    actions: tuple[int, ...]
    eta_v: tuple[float, ...]
    eta_omega: tuple[float, ...]

    def validate(self) -> None:
        if self.namespace != FIXTURE_NAMESPACE:
            raise PermissionError("only result-blind S0 fixtures are accepted")
        if not isinstance(self.event_order, EventOrder):
            raise TypeError("event_order must be an EventOrder")
        if not isinstance(self.regime, Regime):
            raise TypeError("regime must be a Regime")
        if self.regime.switched:
            if self.switch_tick not in (168, 252):
                raise ValueError("switched regimes require tick 168 or 252")
        elif self.switch_tick != 0:
            raise ValueError("fixed regimes require switch_tick=0")
        if not math.isfinite(self.initial_v) or not 0.0 <= self.initial_v <= 0.04:
            raise ValueError("initial_v is outside the CLOSED R01 interval")
        if not math.isfinite(self.initial_phi) or not -0.015 <= self.initial_phi <= 0.015:
            raise ValueError("initial_phi is outside the CLOSED R01 interval")
        if len(self.actions) != MAX_QUERIES or any(
            isinstance(code, bool) or not isinstance(code, int) or not 0 <= code < 27
            for code in self.actions
        ):
            raise ValueError("actions must contain 105 lexicographic action codes")
        if len(self.eta_v) != HORIZON or any(x not in (-0.004, 0.004) for x in self.eta_v):
            raise ValueError("eta_v must be the exact registered fixture alphabet")
        if len(self.eta_omega) != HORIZON or any(
            x not in (-0.006, 0.006) for x in self.eta_omega
        ):
            raise ValueError("eta_omega must be the exact registered fixture alphabet")


def action_code(command: Iterable[int]) -> int:
    values = tuple(command)
    if len(values) != 3 or any(
        isinstance(value, bool) or value not in (0, 1, 2) for value in values
    ):
        raise ValueError("joint command must have three entries from {0,1,2}")
    return values[0] * 9 + values[1] * 3 + values[2]


def decode_action(code: int) -> tuple[int, int, int]:
    if isinstance(code, bool) or not isinstance(code, int) or not 0 <= code < 27:
        raise ValueError("action code must be an integer in [0,27)")
    return (code // 9, (code // 3) % 3, code % 3)


def public_observation(state: TaskState, k: int) -> tuple[float, ...]:
    return (
        state.x / 36.0,
        state.v / 1.8,
        state.phi / 0.48,
        state.omega / 0.5,
        state.z / 0.55,
        state.f / 0.42,
        state.tensions[0] / 1.25,
        state.tensions[1] / 1.25,
        state.tensions[2] / 1.25,
        state.previous[0] / 2.0,
        state.previous[1] / 2.0,
        state.previous[2] / 2.0,
        state.n / 420.0,
        k / 14.0,
    )


def deterministic_fixture(
    *,
    event_order: EventOrder,
    regime: Regime,
    switch_tick: int = 0,
    command: tuple[int, int, int] = (1, 1, 1),
    initial_v: float = 0.02,
    initial_phi: float = 0.0,
    phase: int = 0,
) -> FixtureInput:
    if isinstance(phase, bool) or not isinstance(phase, int):
        raise TypeError("phase must be an integer")
    code = action_code(command)
    fixture = FixtureInput(
        namespace=FIXTURE_NAMESPACE,
        event_order=event_order,
        regime=regime,
        switch_tick=switch_tick,
        initial_v=initial_v,
        initial_phi=initial_phi,
        actions=(code,) * MAX_QUERIES,
        eta_v=tuple(0.004 if (tick + phase) % 2 else -0.004 for tick in range(HORIZON)),
        eta_omega=tuple(0.006 if (tick + phase) % 2 else -0.006 for tick in range(HORIZON)),
    )
    fixture.validate()
    return fixture
