"""Frozen fixture inputs for the ONLGR-TBVUUS revision 03 native host.

This module deliberately has no production namespace or coordinate materializer.
Callers must provide every controller-free disturbance value explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import math
from typing import Sequence


SCIENCE_REVISION = "ONLGR-TBVUUS-SCIENCE-20260821-03"
OBJECT_REVISION = "ONLGR-TBVUUS-R03-FULL-PANEL"
HOST_PACKAGE = "HEADLAND-90-ROAD-TRACK-PATCH-UTILITY-v1"
FIXTURE_NAMESPACE = "ONLGR-TBVUUS-R03-CONFORMANCE-v1"

DT = 0.25
PREROLL_TICKS = 16
BLACKOUT_TICKS = 4
LOCKOUT_TICKS = 16
SHORT_SCORED_TICKS = 32
LONG_SCORED_TICKS = 128
MAX_TICKS = PREROLL_TICKS + LONG_SCORED_TICKS
MAX_STATES = MAX_TICKS + 1
ROAD_TEMPLATE_COUNT = 8
VG = 4.0 * math.pi


class RouteClass(IntEnum):
    SHORT = 0
    LONG = 1

    @property
    def scored_ticks(self) -> int:
        return SHORT_SCORED_TICKS if self is RouteClass.SHORT else LONG_SCORED_TICKS


class Arm(IntEnum):
    NEVER_UPDATE = 0
    OVERHEAD_SHAM = 1
    RAW_ESTIMATE_PATCH = 2
    ROAD_TRACK_ESTIMATE_PATCH = 3


ROAD_TEMPLATES = tuple(
    (route_class, direction, lateral)
    for route_class in (RouteClass.SHORT, RouteClass.LONG)
    for direction in (-1, 1)
    for lateral in (-8, 8)
)


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
        if self.namespace != FIXTURE_NAMESPACE:
            raise PermissionError("TBVUUS native adapter accepts conformance fixtures only")

    @property
    def total_ticks(self) -> int:
        return PREROLL_TICKS + self.route_class.scored_ticks


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
    """Every exogenous word for one encounter; there is no action/RNG word."""

    target_lateral: tuple[float, ...]
    wind_t: tuple[tuple[float, float], ...]
    wind_r: tuple[tuple[float, float], ...]
    sensor: tuple[tuple[float, float], ...]
    shadow_tr: tuple[float, ...]
    shadow_rb: tuple[float, ...]
    link_tr: tuple[float, ...]
    link_rb: tuple[float, ...]

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
    ) -> "FixtureTape":
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
        )
        for name in ("link_tr", "link_rb"):
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
        )


@dataclass(frozen=True)
class FixtureCase:
    spec: EncounterSpec
    tape: FixtureTape
    arm: Arm
    logical_tag: str = "CONFORMANCE"

    def __post_init__(self) -> None:
        object.__setattr__(self, "arm", Arm(self.arm))
        if not isinstance(self.logical_tag, str) or not self.logical_tag:
            raise ValueError("logical_tag must be a non-empty string")
        self.validate_shape()

    def validate_shape(self) -> None:
        """Reject a tape/spec mismatch before any native input can be packed."""
        expected_states = self.spec.total_ticks + 1
        expected_ticks = self.spec.total_ticks
        state_series = (
            "target_lateral",
            "wind_t",
            "wind_r",
            "sensor",
            "shadow_tr",
            "shadow_rb",
        )
        tick_series = ("link_tr", "link_rb")
        for name in state_series:
            observed = len(getattr(self.tape, name))
            if observed != expected_states:
                raise ValueError(
                    f"{name} length {observed} does not match "
                    f"{self.spec.route_class.name} expected state count {expected_states}"
                )
        for name in tick_series:
            observed = len(getattr(self.tape, name))
            if observed != expected_ticks:
                raise ValueError(
                    f"{name} length {observed} does not match "
                    f"{self.spec.route_class.name} expected tick count {expected_ticks}"
                )
