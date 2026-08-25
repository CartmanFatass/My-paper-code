"""Frozen construction constants and deterministic fixture inputs.

Only the namespace below is executable in this construction package.  The
fixture factory uses fixed, non-random tapes and therefore cannot create a
master, seed, coordinate, rollout, or scientific result.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import math
from typing import Final, Iterable


DIRECTION_ID: Final[str] = "semigroup_consistent_duration_model_policy"
CARD_REVISION: Final[str] = "SCDMP-UAV-SP-ORDER-VALUE-SCIENCE-20260820-02"
CONSTRUCTION_OBJECT: Final[str] = (
    "SCDMP-UAV-SP-R02-NATIVE-CONSTRUCTION-AND-CONFORMANCE"
)
HOST_ID: Final[str] = "TRI-UAV-SLING-CORRIDOR-36M-v1"
COMPONENT: Final[str] = "scdmp.uav_sp_order_value.r02.full_host"
FIXTURE_NAMESPACE: Final[str] = "SCDMP-UAV-SP-R02/deterministic-conformance-fixture"

HORIZON: Final[int] = 420
MAX_QUERIES: Final[int] = 105  # ceil(420 / min registered k=4)
ACTION_COUNT: Final[int] = 27
FIXTURE_MAGIC: Final[int] = 0x5343444D50553032


class EventOrder(IntEnum):
    """Exact equal-slot setup histories."""

    RG = 0  # RETENSION, CROSSWIND
    GR = 1  # CROSSWIND, RETENSION

    @property
    def q(self) -> float:
        return 1.0 if self is EventOrder.RG else 0.0

    @property
    def tokens(self) -> tuple[str, str]:
        if self is EventOrder.RG:
            return ("RETENSION", "CROSSWIND")
        return ("CROSSWIND", "RETENSION")


class Regime(IntEnum):
    FIXED_4 = 0
    FIXED_10 = 1
    FIXED_6 = 2
    FIXED_14 = 3
    SWITCH_6_TO_14 = 4
    SWITCH_14_TO_6 = 5

    @property
    def initial_k(self) -> int:
        return (4, 10, 6, 14, 6, 14)[int(self)]

    @property
    def final_k(self) -> int:
        return (4, 10, 6, 14, 14, 6)[int(self)]

    @property
    def switched(self) -> bool:
        return self in (Regime.SWITCH_6_TO_14, Regime.SWITCH_14_TO_6)


@dataclass(frozen=True)
class FixtureInput:
    """One fully materialized, deterministic, construction-only host input."""

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
            raise PermissionError(
                "SCDMP UAV native execution is restricted to the deterministic "
                "construction-fixture namespace"
            )
        if not isinstance(self.event_order, EventOrder):
            raise TypeError("event_order must be an EventOrder")
        if not isinstance(self.regime, Regime):
            raise TypeError("regime must be a Regime")
        if self.regime.switched:
            if self.switch_tick not in (168, 252):
                raise ValueError("switch regimes require switch_tick 168 or 252")
        elif self.switch_tick != 0:
            raise ValueError("fixed regimes require switch_tick 0")
        if not math.isfinite(self.initial_v) or not 0.0 <= self.initial_v <= 0.04:
            raise ValueError("initial_v must lie in the frozen [0,0.04] interval")
        if not math.isfinite(self.initial_phi) or not -0.015 <= self.initial_phi <= 0.015:
            raise ValueError("initial_phi must lie in the frozen [-0.015,0.015] interval")
        if len(self.actions) != MAX_QUERIES:
            raise ValueError(f"fixture action tape must contain exactly {MAX_QUERIES} codes")
        if any(isinstance(code, bool) or not isinstance(code, int) or not 0 <= code < ACTION_COUNT for code in self.actions):
            raise ValueError("every action code must be an integer in [0,27)")
        if len(self.eta_v) != HORIZON or any(value not in (-0.004, 0.004) for value in self.eta_v):
            raise ValueError("eta_v must contain exactly 420 registered +/-0.004 values")
        if len(self.eta_omega) != HORIZON or any(value not in (-0.006, 0.006) for value in self.eta_omega):
            raise ValueError("eta_omega must contain exactly 420 registered +/-0.006 values")


def action_code(command: Iterable[int]) -> int:
    values = tuple(command)
    if len(values) != 3 or any(isinstance(value, bool) or value not in (0, 1, 2) for value in values):
        raise ValueError("a joint command must contain three values from {0,1,2}")
    return values[0] * 9 + values[1] * 3 + values[2]


def decode_action(code: int) -> tuple[int, int, int]:
    if isinstance(code, bool) or not isinstance(code, int) or not 0 <= code < ACTION_COUNT:
        raise ValueError("action code must be an integer in [0,27)")
    return (code // 9, (code // 3) % 3, code % 3)


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
    """Create a non-random alternating-sign semantic fixture."""

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
