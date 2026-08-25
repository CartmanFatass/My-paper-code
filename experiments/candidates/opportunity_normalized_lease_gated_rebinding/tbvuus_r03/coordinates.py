"""Coordinate encoding and result-blind row-set commitments for TBVUUS r03.

This module can enumerate and hash coordinates, but intentionally cannot
materialize a random word.  The production module owns that activity edge
after validating the accepted freeze, Root binding, and active lease.
"""

from __future__ import annotations

from dataclasses import dataclass
import functools
import hashlib
from typing import Iterator

from .config import LONG_SCORED_TICKS, PREROLL_TICKS, SHORT_SCORED_TICKS
from .contracts import (
    BLOCKS_PER_CONTROLLER_REPLICATE,
    DISTURBANCE_STREAMS,
    PRODUCTION_NAMESPACE,
    REPLICATES,
    ROUTE_CLASSES,
)


STATE_STREAMS = frozenset(
    {
        "target_lateral",
        "wind_T",
        "wind_R",
        "sensor_x",
        "sensor_y",
        "shadow_TR",
        "shadow_RB",
    }
)
NORMAL_STREAMS = STATE_STREAMS
UNIFORM_STREAMS = frozenset({"link_TR", "link_RB"})
STREAMS = frozenset(DISTURBANCE_STREAMS)
COORDINATE_ROW_DOMAIN = "ONLGR-TBVUUS-R03-COORDINATE-ROWS-v1"


@dataclass(frozen=True, order=True)
class EncounterIdentity:
    replicate: int
    block: int
    route_class: str

    def __post_init__(self) -> None:
        if isinstance(self.replicate, bool) or self.replicate not in range(REPLICATES):
            raise ValueError("replicate must be 0,...,127")
        if isinstance(self.block, bool) or self.block not in range(BLOCKS_PER_CONTROLLER_REPLICATE):
            raise ValueError("block must be 0,...,19")
        if self.route_class not in ROUTE_CLASSES:
            raise ValueError("route class must be SHORT or LONG")

    @property
    def template(self) -> int:
        return (self.replicate + 3 * self.block) % 4

    @property
    def encounter_ordinal(self) -> int:
        return expected_encounter_order(self.replicate, self.block).index(self.route_class)


def expected_encounter_order(replicate: int, block: int) -> tuple[str, str]:
    if replicate not in range(REPLICATES) or block not in range(BLOCKS_PER_CONTROLLER_REPLICATE):
        raise ValueError("replicate or block is outside the frozen domain")
    return ("SHORT", "LONG") if (replicate + block) % 2 == 0 else ("LONG", "SHORT")


def encounter_plan(replicate: int | None = None) -> tuple[EncounterIdentity, ...]:
    replicates = range(REPLICATES) if replicate is None else (replicate,)
    return tuple(
        EncounterIdentity(rep, block, route_class)
        for rep in replicates
        for block in range(BLOCKS_PER_CONTROLLER_REPLICATE)
        for route_class in expected_encounter_order(rep, block)
    )


@dataclass(frozen=True, order=True)
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
        encounter = EncounterIdentity(self.replicate, self.block, self.route_class)
        if self.namespace != PRODUCTION_NAMESPACE:
            raise ValueError("coordinate namespace differs from frozen TBVUUS production")
        if self.split != "HOLD":
            raise ValueError("TBVUUS r03 has only the HOLD split")
        if self.template != encounter.template:
            raise ValueError("template differs from the frozen replicate/block law")
        if self.stream not in STREAMS:
            raise ValueError("coordinate stream differs from the no-action domain")
        if isinstance(self.lane, bool) or not isinstance(self.lane, int) or self.lane < 0:
            raise ValueError("coordinate lane must be a nonnegative integer")
        if self.stream in UNIFORM_STREAMS and self.lane != 0:
            raise ValueError("link-uniform streams use lane zero only")
        total_ticks = PREROLL_TICKS + (
            SHORT_SCORED_TICKS if self.route_class == "SHORT" else LONG_SCORED_TICKS
        )
        maximum = total_ticks if self.stream in STATE_STREAMS else total_ticks - 1
        if isinstance(self.tick, bool) or not isinstance(self.tick, int) or self.tick not in range(maximum + 1):
            raise ValueError("coordinate tick is outside its exact stream domain")
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


def coordinate_for(
    encounter: EncounterIdentity, *, tick: int, stream: str, lane: int
) -> Coordinate:
    return Coordinate(
        namespace=PRODUCTION_NAMESPACE,
        split="HOLD",
        replicate=encounter.replicate,
        block=encounter.block,
        route_class=encounter.route_class,
        template=encounter.template,
        tick=tick,
        stream=stream,
        lane=lane,
    )


def iter_coordinate_rows() -> Iterator[bytes]:
    """Yield every exact no-action row in deterministic tuple order."""

    for encounter in encounter_plan():
        total_ticks = PREROLL_TICKS + (
            SHORT_SCORED_TICKS if encounter.route_class == "SHORT" else LONG_SCORED_TICKS
        )
        for tick in range(total_ticks + 1):
            for stream in sorted(STATE_STREAMS):
                # Every normal scalar commits its complete fixed Box-Muller pair.
                for lane in (0, 1):
                    yield encode_coordinate(
                        coordinate_for(encounter, tick=tick, stream=stream, lane=lane)
                    )
        for tick in range(total_ticks):
            for stream in sorted(UNIFORM_STREAMS):
                yield encode_coordinate(
                    coordinate_for(encounter, tick=tick, stream=stream, lane=0)
                )


@functools.lru_cache(maxsize=1)
def coordinate_rows_sha256() -> str:
    """Independently enumerate once per process, then reuse the exact digest."""

    digest = hashlib.sha256(COORDINATE_ROW_DOMAIN.encode("ascii") + b"\0")
    count = 0
    for row in iter_coordinate_rows():
        digest.update(len(row).to_bytes(8, "big"))
        digest.update(row)
        count += 1
    if count != 7_936_000:
        raise AssertionError(f"coordinate row count differs: {count}")
    return digest.hexdigest()


def coordinate_row_count() -> int:
    # 2 Box-Muller lanes for seven state-normal streams and one lane for two links.
    per_short = (PREROLL_TICKS + SHORT_SCORED_TICKS + 1) * 14 + (
        PREROLL_TICKS + SHORT_SCORED_TICKS
    ) * 2
    per_long = (PREROLL_TICKS + LONG_SCORED_TICKS + 1) * 14 + (
        PREROLL_TICKS + LONG_SCORED_TICKS
    ) * 2
    return REPLICATES * BLOCKS_PER_CONTROLLER_REPLICATE * (per_short + per_long)


assert coordinate_row_count() == 7_936_000
