"""Deterministic arm-independent r06 population and RNG-coordinate contract."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Iterable

from .production_contract import (
    BLOCKS,
    EVALUATION_SCHEDULES,
    REGIMES,
    RNG_PREFIX,
    SLOTS_PER_SPEED,
    SPEEDS,
    SPEED_STRATA,
    TestAuthority,
)


TEST_MASTER = hashlib.sha256(b"TEST/DISH-RBHR-R06/POPULATION/RNG/V1").digest()
SPLIT_BY_SCHEDULE = {
    "K4": "CALIBRATION", "K8": "CLAIM", "K12": "CALIBRATION",
    "K4_TO_K12": "CLAIM", "K12_TO_K4": "CLAIM",
}
X_OFFSETS = (-80, -40, 40, 80)
Y_OFFSETS = (-180, -120, 120, 180)


class PopulationError(RuntimeError):
    pass


@dataclass(frozen=True, order=True)
class EvaluationCoordinate:
    block: int
    regime: str
    schedule: str
    speed_stratum: str
    within_speed_slot: int

    @property
    def speed_ordinal(self) -> int:
        return SPEED_STRATA.index(self.speed_stratum)

    @property
    def route_speed(self) -> int:
        return SPEEDS[self.speed_ordinal]

    @property
    def evaluation_slot(self) -> int:
        return 16 * self.speed_ordinal + self.within_speed_slot

    @property
    def split(self) -> str:
        return SPLIT_BY_SCHEDULE[self.schedule]

    @property
    def regime_ordinal(self) -> int:
        return REGIMES.index(self.regime)

    @property
    def delta(self) -> int:
        return (
            5 * self.block + 3 * self.regime_ordinal +
            7 * EVALUATION_SCHEDULES.index(self.schedule) + 11 * self.speed_ordinal
        ) % 16

    @property
    def geometry_ordinal(self) -> int:
        return (self.within_speed_slot + self.delta) % 16

    @property
    def initial_ux(self) -> int:
        return X_OFFSETS[self.geometry_ordinal % 4]

    @property
    def initial_uy(self) -> int:
        return Y_OFFSETS[self.geometry_ordinal // 4]

    @property
    def reflection(self) -> int:
        return 1 if (self.within_speed_slot & 1) == 0 else -1

    @property
    def initial_owner(self) -> int:
        return (self.within_speed_slot >> 1) & 1

    @property
    def qa_owner(self) -> int:
        return (self.within_speed_slot >> 2) & 1

    @property
    def turn_magnitude_deg(self) -> int:
        index = (
            self.within_speed_slot + self.block + 2 * self.regime_ordinal +
            EVALUATION_SCHEDULES.index(self.schedule) + self.speed_ordinal
        ) % 3
        return (25, 35, 45)[index]

    @property
    def turn_sign(self) -> int:
        index = (
            self.within_speed_slot + self.block + self.regime_ordinal +
            EVALUATION_SCHEDULES.index(self.schedule) + self.speed_ordinal
        ) % 2
        return (-1, 1)[index]

    @property
    def tau_d_tick(self) -> int:
        return 10 * (42, 54, 66)[self.evaluation_slot % 3]

    @property
    def k_pair(self) -> tuple[int, int]:
        return {
            "K4": (4, 4), "K8": (8, 8), "K12": (12, 12),
            "K4_TO_K12": (4, 12), "K12_TO_K4": (12, 4),
        }[self.schedule]

    @property
    def switch_tick(self) -> int:
        if self.k_pair[0] == self.k_pair[1]:
            return 1199
        return 10 * (36, 48, 60, 72)[(self.evaluation_slot % 12) // 3]

    def phase(self, phase_offset: int) -> int:
        k_initial = self.k_pair[0]
        if not 0 <= phase_offset < k_initial:
            raise PopulationError("r06 phase offset differs")
        return (self.evaluation_slot + phase_offset) % k_initial

    def canonical_key(self) -> str:
        return "/".join((
            RNG_PREFIX, "EVALUATION_COORDINATE", str(self.block), self.split,
            self.regime, self.schedule, str(self.evaluation_slot),
        ))


def complete_evaluation_coordinates() -> tuple[EvaluationCoordinate, ...]:
    rows = tuple(
        EvaluationCoordinate(block, regime, schedule, speed, slot)
        for block in range(BLOCKS)
        for regime in REGIMES
        for schedule in EVALUATION_SCHEDULES
        for speed in SPEED_STRATA
        for slot in range(SLOTS_PER_SPEED)
    )
    keys = tuple(row.canonical_key() for row in rows)
    if len(rows) != 11_520 or len(set(keys)) != 11_520:
        raise PopulationError("r06 population cardinality or uniqueness differs")
    return rows


def address(
    *, purpose: str, block: int | None, split: str, regime: str,
    schedule: str, evaluation_slot: int | None, lane: int | None = None,
    cycle: int | None = None, arm_substream: str = "COMMON",
    degradation_flag: str = "PAIR_SHARED", fork_branch: str = "PREFORK",
    episode: int | None = None, tick: int | None = None,
    message_type: str = "NONE", packet_sequence: int | None = None,
    hop: str = "NONE", inference_resample: int | None = None,
    field: str, draw_index: int,
) -> str:
    scalar = lambda value: "NONE" if value is None else str(value)
    value = "/".join((
        RNG_PREFIX, purpose, scalar(block), split, regime, schedule,
        scalar(evaluation_slot), scalar(lane), scalar(cycle), arm_substream,
        degradation_flag, fork_branch, scalar(episode), scalar(tick),
        message_type, scalar(packet_sequence), hop, scalar(inference_resample),
        field, str(draw_index),
    ))
    if "accepted_slot" in value or "candidate_attempt" in value or not value.startswith(RNG_PREFIX + "/"):
        raise PopulationError("r06 RNG address contains a deleted coordinate")
    return value


def test_uniform(address_value: str, authority: TestAuthority) -> float:
    authority.require_test_only()
    if not address_value.startswith(RNG_PREFIX + "/"):
        raise PopulationError("TEST RNG address is outside r06")
    digest = hashlib.sha256(TEST_MASTER + b"\0" + address_value.encode("utf-8")).digest()
    value = ((int.from_bytes(digest[:8], "big") >> 11) + 0.5) / 2**53
    if not 0.0 < value < 1.0 or not math.isfinite(value):
        raise PopulationError("r06 open uniform differs")
    return value


def population_manifest() -> dict[str, object]:
    rows = complete_evaluation_coordinates()
    encoded = ("\n".join(row.canonical_key() for row in rows) + "\n").encode("ascii")
    geometry_complete = True
    identity_balanced = True
    clock_nonempty = True
    for block in range(BLOCKS):
        for regime in REGIMES:
            for schedule in EVALUATION_SCHEDULES:
                for speed in SPEED_STRATA:
                    cell = tuple(row for row in rows if (
                        row.block, row.regime, row.schedule, row.speed_stratum
                    ) == (block, regime, schedule, speed))
                    geometry_complete &= {(row.initial_ux, row.initial_uy) for row in cell} == {
                        (x, y) for x in X_OFFSETS for y in Y_OFFSETS
                    }
                    identity_balanced &= all(
                        sum((row.reflection, row.initial_owner, row.qa_owner) == identity for row in cell) == 2
                        for identity in ((r, owner, qa) for r in (-1, 1) for owner in (0, 1) for qa in (0, 1))
                    )
                    clock_nonempty &= len({row.tau_d_tick for row in cell}) == 3
                    if cell[0].k_pair[0] != cell[0].k_pair[1]:
                        clock_nonempty &= len({(row.tau_d_tick, row.switch_tick) for row in cell}) == 12
    magnitude_counts_exact = all(
        sorted(sum(
            row.turn_magnitude_deg == magnitude
            for row in rows
            if (row.regime, row.schedule, row.speed_stratum) == (regime, schedule, speed)
        ) for magnitude in (25, 35, 45)) == [128, 128, 128]
        for regime in REGIMES for schedule in EVALUATION_SCHEDULES for speed in SPEED_STRATA
    )
    return {
        "schema": "DISH_RBHR_R06_DETERMINISTIC_POPULATION_MANIFEST_V1",
        "coordinate_count": len(rows),
        "coordinate_manifest_sha256": hashlib.sha256(encoded).hexdigest(),
        "geometry_factorial_complete": bool(geometry_complete),
        "identity_combinations_twice_per_speed_cell": bool(identity_balanced),
        "clock_support_nonempty_per_speed_cell": bool(clock_nonempty),
        "turn_magnitude_exact_across_blocks": bool(magnitude_counts_exact),
        "candidate_attempt_coordinate": False,
        "rejection_or_search": False,
        "arm_independent": True,
        "scientific_admission_failure_probability": 0.0,
        "test_only": True,
        "question_relevant_output": False,
    }


__all__ = [
    "EvaluationCoordinate", "PopulationError", "address",
    "complete_evaluation_coordinates", "population_manifest", "test_uniform",
]
