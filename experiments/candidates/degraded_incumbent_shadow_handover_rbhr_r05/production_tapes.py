"""Value-blind accepted-tape coordinate and candidate-accounting contract.

This module enumerates the frozen scanner work without evaluating a candidate
or creating a scientific master.  Candidate qualification remains a native
production-host responsibility; this inventory prevents missing, duplicated,
or completion-order-selected slots.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .production_contract import BLOCKS, EVALUATION_SCHEDULES, PACKAGES, STRATA, TAPES_PER_STRATUM


class TapeInventoryError(RuntimeError):
    pass


SPLIT_BY_SCHEDULE = {
    "K4": "CALIBRATION",
    "K8": "CLAIM",
    "K12": "CALIBRATION",
    "K4_TO_K12": "CLAIM",
    "K12_TO_K4": "CLAIM",
}


@dataclass(frozen=True, order=True)
class AcceptedTapeCoordinate:
    block: int
    package: str
    schedule: str
    stratum: str
    within_stratum_slot: int

    @property
    def split(self) -> str:
        return SPLIT_BY_SCHEDULE[self.schedule]

    @property
    def accepted_slot(self) -> int:
        return STRATA.index(self.stratum) * TAPES_PER_STRATUM + self.within_stratum_slot

    def canonical_key(self) -> str:
        return "/".join(
            (
                "DISH", "RBHR", "R05", "ACCEPTED_TAPE",
                str(self.block), self.split, self.package, self.schedule,
                str(self.accepted_slot),
            )
        )


def complete_accepted_tape_coordinates() -> tuple[AcceptedTapeCoordinate, ...]:
    rows = tuple(
        AcceptedTapeCoordinate(block, package, schedule, stratum, slot)
        for block in range(BLOCKS)
        for package in PACKAGES
        for schedule in EVALUATION_SCHEDULES
        for stratum in STRATA
        for slot in range(TAPES_PER_STRATUM)
    )
    expected = BLOCKS * len(PACKAGES) * len(EVALUATION_SCHEDULES) * len(STRATA) * TAPES_PER_STRATUM
    keys = tuple(row.canonical_key() for row in rows)
    if len(rows) != expected or len(set(keys)) != expected:
        raise TapeInventoryError("accepted-tape coordinate inventory differs")
    for row in rows:
        if not 0 <= row.accepted_slot < 48:
            raise TapeInventoryError("accepted-slot ordinal differs")
    return rows


def candidate_accounting_identity() -> dict[str, object]:
    rows = complete_accepted_tape_coordinates()
    keys = tuple(row.canonical_key() for row in rows)
    encoded = ("\n".join(keys) + "\n").encode("ascii")
    calibration = sum(row.split == "CALIBRATION" for row in rows)
    claim = sum(row.split == "CLAIM" for row in rows)
    return {
        "schema": "DISH_RBHR_R05_ACCEPTED_TAPE_CANDIDATE_ACCOUNTING_V1",
        "test_only": True,
        "scientific_master": False,
        "question_relevant_output": False,
        "coordinate_count": len(rows),
        "calibration_coordinate_count": calibration,
        "claim_coordinate_count": claim,
        "candidate_attempt_cap_per_coordinate": 100_000,
        "candidate_attempts_global_cap": len(rows) * 100_000,
        "selection_rule": "LOWEST_QUALIFYING_ATTEMPT_IN_INCREASING_INTEGER_ORDER",
        "qualification_evaluated": False,
        "coordinate_manifest_sha256": hashlib.sha256(encoded).hexdigest(),
    }


__all__ = [
    "AcceptedTapeCoordinate", "SPLIT_BY_SCHEDULE", "TapeInventoryError",
    "candidate_accounting_identity", "complete_accepted_tape_coordinates",
]
