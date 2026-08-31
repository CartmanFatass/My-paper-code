"""Result-blind endpoint/accounting reducer for the 6,912 source-factored cells."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Sequence

import numpy as np

from .production_source_factored_contract import CLAIM_ROWS, ENDPOINTS, ClaimCoordinate, complete_claim_inventory


SIGNS: Final = {"MEAN": 1, "TAIL": 1, "DEFICIT": -1, "DELAY": -1}
MATERIAL_MARGINS: Final = {"MEAN": 0.03, "TAIL": 0.05, "DEFICIT": 0.25, "DELAY": 0.5}
NONINFERIORITY_MARGINS: Final = {"MEAN": 0.01, "TAIL": 0.02, "DEFICIT": 0.25, "DELAY": 0.5}
BRANCHES: Final = (
    "INVALID_PROTOCOL_OR_MEASUREMENT",
    "MISSING_COMPETENCE_OPPORTUNITY_OR_SUPPORT",
    "NONANSWERABLE_OR_IMPRECISE",
    "NONHARM_FAILURE",
    "SHADOW_ABSORBED",
    "SHADOW_SPECIFIC_VALUE",
    "GENERIC_TRANSFER_ONLY",
    "TARGET_SPECIFIC_NO_MATERIAL",
    "UNRESOLVED",
)


class SourceFactoredReducerError(RuntimeError):
    pass


def fractional_worst_10(values: Sequence[float]) -> float:
    rows = np.sort(np.asarray(values, dtype=np.float64))
    if rows.ndim != 1 or rows.size == 0 or not np.isfinite(rows).all():
        raise SourceFactoredReducerError("tail rows differ")
    mass = 0.1 * rows.size; whole = int(np.floor(mass)); total = float(rows[:whole].sum())
    if whole < rows.size:
        total += (mass - whole) * float(rows[whole])
    return total / mass


def recovery_delay(row: np.ndarray) -> float:
    original = np.asarray(row)
    try:
        valid = np.isfinite(original).all() and np.logical_or(original == 0, original == 1).all()
    except TypeError:
        valid = False
    if original.shape != (100,) or not valid:
        raise SourceFactoredReducerError("recovery row differs")
    service = original.astype(np.int8)
    failures = np.flatnonzero(service == 0)
    if failures.size == 0:
        return 0.0
    origin = int(failures[0])
    for tick in range(origin, 91):
        if bool(np.all(service[tick:tick + 10] == 1)):
            return 0.1 * (tick - origin)
    return 10.0


@dataclass(frozen=True)
class EndpointRows:
    service: np.ndarray

    def reduce(self) -> Mapping[str, float]:
        original = np.asarray(self.service)
        try:
            valid = np.isfinite(original).all() and np.logical_or(original == 0, original == 1).all()
        except TypeError:
            valid = False
        if original.ndim != 2 or original.shape[0] == 0 or original.shape[1] != 100 or not valid:
            raise SourceFactoredReducerError("100-tick endpoint rows differ")
        rows = original.astype(np.int8)
        fractions = rows.mean(axis=1)
        values = {
            "MEAN": float(fractions.mean()),
            "TAIL": fractional_worst_10(fractions),
            "DEFICIT": float((0.1 * (100 - rows.sum(axis=1))).mean()),
            "DELAY": float(np.mean([recovery_delay(row) for row in rows])),
        }
        if tuple(values) != ENDPOINTS:
            raise SourceFactoredReducerError("endpoint order differs")
        return values


def signed_benefit(treatment: Mapping[str, float], comparator: Mapping[str, float]) -> Mapping[str, float]:
    if set(treatment) != set(ENDPOINTS) or set(comparator) != set(ENDPOINTS):
        raise SourceFactoredReducerError("endpoint comparison inventory differs")
    return {name: SIGNS[name] * (float(treatment[name]) - float(comparator[name])) for name in ENDPOINTS}


@dataclass(frozen=True)
class NonharmObservation:
    invalid_commit_events: int
    token_gap_events: int
    dual_owner_events: int
    dual_payload_events: int
    buffer_clear_events: int
    command_slew_breach_events: int
    separation_breach_events: int
    min_separation_m: float
    energy_ratio: float
    receipt_schema_valid: bool
    extra_application_ticks: int = 0

    def passes(self) -> bool:
        return bool(
            all(value == 0 for value in (
                self.invalid_commit_events, self.token_gap_events, self.dual_owner_events,
                self.dual_payload_events, self.buffer_clear_events,
                self.command_slew_breach_events, self.separation_breach_events,
            )) and
            np.isfinite(self.min_separation_m) and self.min_separation_m >= 15.0 and
            np.isfinite(self.energy_ratio) and self.energy_ratio <= 0.03 and
            self.receipt_schema_valid and self.extra_application_ticks == 0
        )


@dataclass(frozen=True)
class BranchEvidence:
    protocol_and_measurement_valid: bool = True
    competence_opportunity_support: bool = True
    answerable_and_precise: bool = True
    nonharm_pass: bool = True
    replay_absorbs_shadow: bool = False
    shadow_specific_material: bool = False
    generic_transfer_material: bool = False
    target_specific_nonmaterial: bool = False


def first_match_branch(value: BranchEvidence) -> str:
    predicates = (
        (not value.protocol_and_measurement_valid, BRANCHES[0]),
        (not value.competence_opportunity_support, BRANCHES[1]),
        (not value.answerable_and_precise, BRANCHES[2]),
        (not value.nonharm_pass, BRANCHES[3]),
        (value.replay_absorbs_shadow, BRANCHES[4]),
        (value.shadow_specific_material, BRANCHES[5]),
        (value.generic_transfer_material, BRANCHES[6]),
        (value.target_specific_nonmaterial, BRANCHES[7]),
        (True, BRANCHES[8]),
    )
    return next(branch for matched, branch in predicates if matched)


class CompleteClaimAccounting:
    """Tracks all cells including explicit no-trigger rows; exposes no effect."""

    def __init__(self) -> None:
        self._keys = tuple(row.key() for row in complete_claim_inventory())
        self._written: dict[str, bool] = {}

    def put(self, coordinate: ClaimCoordinate, *, trigger_present: bool) -> None:
        key = coordinate.key()
        if key not in self._keys or key in self._written:
            raise SourceFactoredReducerError("claim accounting row is absent or duplicate")
        self._written[key] = bool(trigger_present)

    @property
    def complete(self) -> bool:
        return len(self._written) == CLAIM_ROWS and set(self._written) == set(self._keys)

    def seal_scaffold(self) -> Mapping[str, object]:
        if not self.complete:
            raise SourceFactoredReducerError("6,912-row claim accounting is incomplete")
        return {
            "schema": "DISH_PROMOTION_SOURCE_FORK_R01_ACCOUNTING_V1",
            "row_count": CLAIM_ROWS, "trigger_rows": sum(self._written.values()),
            "no_trigger_rows": CLAIM_ROWS - sum(self._written.values()),
            "no_trigger_rows_preserved": True, "result_values_exposed": False,
            "question_relevant_output": False,
        }


__all__ = [
    "BRANCHES", "BranchEvidence", "CompleteClaimAccounting", "EndpointRows", "MATERIAL_MARGINS",
    "NONINFERIORITY_MARGINS", "NonharmObservation", "SIGNS", "SourceFactoredReducerError",
    "first_match_branch", "fractional_worst_10", "recovery_delay", "signed_benefit",
]
