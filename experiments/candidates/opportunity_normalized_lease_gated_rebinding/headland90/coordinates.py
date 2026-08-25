"""Coordinate encoding with a construction-stage production activity fence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

from .config import (
    FIXTURE_NAMESPACE,
    LONG_SCORED_TICKS,
    PREROLL_TICKS,
    PRODUCTION_NAMESPACE,
    SHORT_SCORED_TICKS,
)


STREAMS = frozenset(
    {
        "target_lateral", "wind_T", "wind_R", "sensor_x", "sensor_y",
        "shadow_TR", "shadow_RB", "link_TR", "link_RB", "action",
    }
)
STATE_STREAMS = frozenset(
    {"target_lateral", "wind_T", "wind_R", "sensor_x", "sensor_y", "shadow_TR", "shadow_RB"}
)
NORMAL_STREAMS = STATE_STREAMS


@dataclass(frozen=True)
class Coordinate:
    namespace: str
    split: str
    replicate: int
    block: int
    route_class: str
    template: int
    tick: int
    stream: str
    lane: int

    def fields(self) -> tuple[str, ...]:
        if self.stream not in STREAMS:
            raise ValueError(f"unknown stream {self.stream!r}")
        if self.namespace == PRODUCTION_NAMESPACE:
            limits = {"CAL": 48, "HOLD": 128}
            if self.split not in limits:
                raise ValueError("production split must be CAL or HOLD")
            if not 0 <= self.replicate < limits[self.split]:
                raise ValueError("replicate is outside the production split")
        elif self.namespace == FIXTURE_NAMESPACE:
            # Fixture coordinates may deliberately combine synthetic in-range
            # templates with a replicate/block for isolated conformance tests.
            if self.split != "FIXTURE":
                raise ValueError("conformance coordinates require the FIXTURE split")
            if self.replicate < 0:
                raise ValueError("fixture replicate must be nonnegative")
        else:
            raise ValueError("unknown HEADLAND-90 coordinate namespace")
        if self.block not in range(20):
            raise ValueError("block must be in 0,...,19")
        if self.route_class not in ("SHORT", "LONG"):
            raise ValueError("class must be SHORT or LONG")
        if self.template not in range(4):
            raise ValueError("template must be in 0,...,3")
        if (
            self.namespace == PRODUCTION_NAMESPACE
            and self.template != (self.replicate + 3 * self.block) % 4
        ):
            raise ValueError("template does not match the production replicate/block identity")
        physical_ticks = PREROLL_TICKS + (
            SHORT_SCORED_TICKS if self.route_class == "SHORT" else LONG_SCORED_TICKS
        )
        maximum_tick = physical_ticks if self.stream in STATE_STREAMS else physical_ticks - 1
        if not 0 <= self.tick <= maximum_tick:
            raise ValueError("tick is outside the stream's physical encounter range")
        if self.lane < 0:
            raise ValueError("lane must be nonnegative")
        return (
            self.namespace,
            self.split,
            str(self.replicate),
            str(self.block),
            self.route_class,
            str(self.template),
            str(self.tick),
            self.stream,
            str(self.lane),
        )


def encode_coordinate(coordinate: Coordinate) -> bytes:
    encoded: list[bytes] = []
    for field in coordinate.fields():
        value = field.encode("utf-8")
        encoded.append(str(len(value)).encode("ascii") + b":" + value)
    return b"|".join(encoded)


def materialize_uniform(coordinate: Coordinate) -> float:
    """Materialize fixture words only; no production permit exists in this stage."""
    if coordinate.namespace == PRODUCTION_NAMESPACE:
        raise PermissionError("production random-word materialization is not authorized")
    if coordinate.namespace != FIXTURE_NAMESPACE:
        raise PermissionError("only the registered conformance fixture namespace is allowed")
    digest = hashlib.sha256(encode_coordinate(coordinate)).digest()
    word = int.from_bytes(digest[:4], "big", signed=False)
    return (word + 0.5) / 4294967296.0


def materialize_normal_pair(lower_coordinate: Coordinate) -> tuple[float, float]:
    """Box-Muller pair with the lower even lane as radius and next as angle."""
    if lower_coordinate.stream not in NORMAL_STREAMS:
        raise ValueError("stream does not carry normal innovations")
    if lower_coordinate.lane % 2 != 0:
        raise ValueError("normal-pair coordinate must name the lower even lane")
    radius_uniform = materialize_uniform(lower_coordinate)
    angle_coordinate = Coordinate(
        namespace=lower_coordinate.namespace,
        split=lower_coordinate.split,
        replicate=lower_coordinate.replicate,
        block=lower_coordinate.block,
        route_class=lower_coordinate.route_class,
        template=lower_coordinate.template,
        tick=lower_coordinate.tick,
        stream=lower_coordinate.stream,
        lane=lower_coordinate.lane + 1,
    )
    angle_uniform = materialize_uniform(angle_coordinate)
    radius = math.sqrt(-2.0 * math.log(radius_uniform))
    angle = 2.0 * math.pi * angle_uniform
    return radius * math.cos(angle), radius * math.sin(angle)


def materialize_normal(coordinate: Coordinate) -> float:
    """Materialize the component addressed by an even/odd Box-Muller lane."""
    lower_lane = coordinate.lane - coordinate.lane % 2
    lower = Coordinate(
        namespace=coordinate.namespace,
        split=coordinate.split,
        replicate=coordinate.replicate,
        block=coordinate.block,
        route_class=coordinate.route_class,
        template=coordinate.template,
        tick=coordinate.tick,
        stream=coordinate.stream,
        lane=lower_lane,
    )
    return materialize_normal_pair(lower)[coordinate.lane % 2]


def production_activity_permitted() -> bool:
    """Construction-stage hard fence used by future runner preflights."""
    return False
