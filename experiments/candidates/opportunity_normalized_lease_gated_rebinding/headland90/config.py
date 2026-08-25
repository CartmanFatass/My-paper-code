"""Frozen constants and input objects for HEADLAND-90 conformance."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import math
from typing import Iterable, Sequence


CARD_REVISION = "ONLGR-TBH-HOST-CARD-20260815-03"
HOST_ID = "HEADLAND-90-TRACK-RELAY-2UAV-v1"
PRODUCTION_NAMESPACE = "ONLGR-TBH-HEADLAND90-20260815-v1"
FIXTURE_NAMESPACE = "ONLGR-TBH-HEADLAND90-CONFORMANCE-v1"

DT = 0.25
LOCK_TICKS = 16
BLACKOUT_TICKS = 4
PREROLL_TICKS = 16
SHORT_SCORED_TICKS = 32
LONG_SCORED_TICKS = 128
MAX_TICKS = PREROLL_TICKS + LONG_SCORED_TICKS
MAX_STATES = MAX_TICKS + 1
VG = 4.0 * math.pi


class RouteClass(str, Enum):
    SHORT = "SHORT"
    LONG = "LONG"

    @property
    def scored_ticks(self) -> int:
        return SHORT_SCORED_TICKS if self is RouteClass.SHORT else LONG_SCORED_TICKS


@dataclass(frozen=True)
class EncounterSpec:
    route_class: RouteClass
    direction: int
    lateral_offset: int
    namespace: str = FIXTURE_NAMESPACE

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_class", RouteClass(self.route_class))
        if self.direction not in (-1, 1):
            raise ValueError("direction must be -1 or +1")
        if self.lateral_offset not in (-8, 8):
            raise ValueError("lateral_offset must be -8 or +8")

    @property
    def total_ticks(self) -> int:
        return PREROLL_TICKS + self.route_class.scored_ticks


def encounter_order(replicate: int, block: int) -> tuple[RouteClass, RouteClass]:
    if replicate < 0 or block not in range(20):
        raise ValueError("replicate must be nonnegative and block must be in 0,...,19")
    if (replicate + block) % 2 == 0:
        return (RouteClass.SHORT, RouteClass.LONG)
    return (RouteClass.LONG, RouteClass.SHORT)


def template_index(replicate: int, block: int) -> int:
    if replicate < 0 or block not in range(20):
        raise ValueError("replicate must be nonnegative and block must be in 0,...,19")
    return (replicate + 3 * block) % 4


def template_parameters(index: int) -> tuple[int, int]:
    if index not in range(4):
        raise ValueError("template index must be in 0,...,3")
    try:
        return ((1, 8), (1, -8), (-1, 8), (-1, -8))[index]
    except IndexError as error:
        raise ValueError("template index must be in 0,...,3") from error


def block_specs(
    replicate: int,
    block: int,
    *,
    namespace: str = FIXTURE_NAMESPACE,
) -> tuple[EncounterSpec, EncounterSpec]:
    direction, lateral = template_parameters(template_index(replicate, block))
    return tuple(
        EncounterSpec(route_class, direction, lateral, namespace=namespace)
        for route_class in encounter_order(replicate, block)
    )  # type: ignore[return-value]


@dataclass(frozen=True)
class ControllerSpec:
    """Exact finite-family controller coefficients in units of one eighth.

    A lookup or constant controller has zero slopes.  ``explicit`` controllers
    carry one exact rational for every scored tick and are intended only for
    deterministic conformance fixtures.
    """

    alpha_short: int = 0
    alpha_long: int = 0
    beta_short: int = 0
    beta_long: int = 0
    gamma_short: int = 0
    gamma_long: int = 0
    explicit: tuple[Fraction, ...] | None = None

    def __post_init__(self) -> None:
        for name in (
            "alpha_short", "alpha_long", "beta_short", "beta_long",
            "gamma_short", "gamma_long",
        ):
            value = getattr(self, name)
            if not isinstance(value, int):
                raise TypeError(f"{name} must be an integer eighth-unit")
        if self.explicit is not None:
            exact = tuple(Fraction(value) for value in self.explicit)
            if any(value < 0 or value > Fraction(7, 8) for value in exact):
                raise ValueError("explicit rates must lie in [0, 7/8]")
            object.__setattr__(self, "explicit", exact)

    @classmethod
    def constant(cls, q: Fraction | int | float) -> "ControllerSpec":
        value = Fraction(q)
        units_exact = value * 8
        if units_exact.denominator != 1:
            raise ValueError("constant q must be a member of Q")
        units = units_exact.numerator
        if not 0 <= units <= 7:
            raise ValueError("constant q must lie in Q")
        return cls(alpha_short=units, alpha_long=units)

    @classmethod
    def lookup(cls, q_short_units: int, q_long_units: int) -> "ControllerSpec":
        if q_short_units not in range(8) or q_long_units not in range(8):
            raise ValueError("lookup rates must be eighth-units 0,...,7")
        return cls(alpha_short=q_short_units, alpha_long=q_long_units)

    @classmethod
    def explicit_rates(cls, rates: Iterable[Fraction | int | float]) -> "ControllerSpec":
        return cls(explicit=tuple(Fraction(value) for value in rates))

    def rate_fraction(
        self,
        route_class: RouteClass,
        scored_index: int,
        anchor_index: int,
    ) -> Fraction:
        scored_ticks = route_class.scored_ticks
        if not 0 <= scored_index < scored_ticks:
            raise IndexError("scored_index outside route")
        if self.explicit is not None:
            if len(self.explicit) != scored_ticks:
                raise ValueError("explicit rate tape length does not match route")
            return self.explicit[scored_index]
        if route_class is RouteClass.SHORT:
            alpha, beta, gamma = self.alpha_short, self.beta_short, self.gamma_short
        else:
            alpha, beta, gamma = self.alpha_long, self.beta_long, self.gamma_long
        remaining = Fraction(scored_ticks - scored_index, scored_ticks)
        age = min(Fraction(scored_index - anchor_index, 128), Fraction(1))
        value = (
            Fraction(alpha, 8)
            + Fraction(beta, 8) * (remaining - Fraction(1, 2))
            + Fraction(gamma, 8) * (age - Fraction(1, 2))
        )
        return min(max(value, Fraction(0)), Fraction(7, 8))


def _float_tuple(values: Sequence[float], expected: int, name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) != expected:
        raise ValueError(f"{name} must contain exactly {expected} values")
    if not all(math.isfinite(value) for value in result):
        raise ValueError(f"{name} contains a non-finite value")
    return result


def _vec_tuple(
    values: Sequence[Sequence[float]], expected: int, name: str
) -> tuple[tuple[float, float], ...]:
    result = tuple(tuple(float(component) for component in value) for value in values)
    if len(result) != expected or any(len(value) != 2 for value in result):
        raise ValueError(f"{name} must have shape ({expected}, 2)")
    if not all(math.isfinite(component) for value in result for component in value):
        raise ValueError(f"{name} contains a non-finite value")
    return result  # type: ignore[return-value]


@dataclass(frozen=True)
class FixtureTape:
    """All action-independent words for one explicit encounter fixture."""

    target_lateral: tuple[float, ...]
    wind_t: tuple[tuple[float, float], ...]
    wind_r: tuple[tuple[float, float], ...]
    sensor: tuple[tuple[float, float], ...]
    shadow_tr: tuple[float, ...]
    shadow_rb: tuple[float, ...]
    link_tr: tuple[float, ...]
    link_rb: tuple[float, ...]
    action: tuple[float, ...]

    @classmethod
    def from_sequences(
        cls,
        spec: EncounterSpec,
        *,
        target_lateral: Sequence[float],
        wind_t: Sequence[Sequence[float]],
        wind_r: Sequence[Sequence[float]],
        sensor: Sequence[Sequence[float]],
        shadow_tr: Sequence[float],
        shadow_rb: Sequence[float],
        link_tr: Sequence[float],
        link_rb: Sequence[float],
        action: Sequence[float],
    ) -> "FixtureTape":
        if spec.namespace != FIXTURE_NAMESPACE:
            raise PermissionError("explicit fixture tapes require the conformance namespace")
        states, ticks = spec.total_ticks + 1, spec.total_ticks
        result = cls(
            target_lateral=_float_tuple(target_lateral, states, "target_lateral"),
            wind_t=_vec_tuple(wind_t, states, "wind_t"),
            wind_r=_vec_tuple(wind_r, states, "wind_r"),
            sensor=_vec_tuple(sensor, states, "sensor"),
            shadow_tr=_float_tuple(shadow_tr, states, "shadow_tr"),
            shadow_rb=_float_tuple(shadow_rb, states, "shadow_rb"),
            link_tr=_float_tuple(link_tr, ticks, "link_tr"),
            link_rb=_float_tuple(link_rb, ticks, "link_rb"),
            action=_float_tuple(action, ticks, "action"),
        )
        for name in ("link_tr", "link_rb", "action"):
            if any(value < 0.0 or value >= 1.0 for value in getattr(result, name)):
                raise ValueError(f"{name} uniforms must lie in [0,1)")
        return result

    @classmethod
    def constant(
        cls,
        spec: EncounterSpec,
        *,
        normal: float = 0.0,
        uniform: float = 0.5,
    ) -> "FixtureTape":
        """Build a literal constant fixture; this does not materialize PRNG words."""
        states, ticks = spec.total_ticks + 1, spec.total_ticks
        scalar = [normal] * states
        vectors = [(normal, normal)] * states
        uniforms = [uniform] * ticks
        return cls.from_sequences(
            spec,
            target_lateral=scalar,
            wind_t=vectors,
            wind_r=vectors,
            sensor=vectors,
            shadow_tr=scalar,
            shadow_rb=scalar,
            link_tr=uniforms,
            link_rb=uniforms,
            action=uniforms,
        )
