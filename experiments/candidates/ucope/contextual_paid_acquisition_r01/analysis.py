"""Prespecified BELIEF competence and acquisition analysis."""

from __future__ import annotations

from math import sqrt
from statistics import mean, stdev
from typing import Any, Iterable

from .contract import SEED_SLOTS
from .evaluation import validate_competence
from .schema import SeedEvaluation

ONE_SIDED_95_T_DF9 = 1.833112932653633


def signed_specificity_lower_bound(values: Iterable[float]) -> float:
    values = tuple(float(value) for value in values)
    if len(values) != 10 or any(not (-float("inf") < value < float("inf")) for value in values):
        raise ValueError("specificity bound requires ten finite paired seed values")
    standard_error = stdev(values) / sqrt(len(values))
    return mean(values) - ONE_SIDED_95_T_DF9 * standard_error


def analyze_acquisition(evaluations: list[SeedEvaluation] | tuple[SeedEvaluation, ...]) -> dict[str, Any]:
    competence = validate_competence(evaluations)
    from .oracle import construct_flip_certificate
    oracle_vector = {cell.context_id: cell.test_action for cell in construct_flip_certificate().cells}
    all_flips = all(item.action_vector == oracle_vector for item in evaluations)
    lower_bound = signed_specificity_lower_bound(item.signed_specificity for item in evaluations)
    return {
        **competence,
        "acquisition_all_flips": all_flips,
        "specificity_lower_bound": lower_bound,
        "acquisition_pass": bool(competence["competence_pass"] and all_flips and lower_bound > 0.0),
    }


def validate_analysis(evaluations: list[SeedEvaluation] | tuple[SeedEvaluation, ...]) -> dict[str, Any]:
    if {item.seed_slot for item in evaluations} != set(SEED_SLOTS):
        raise ValueError("analysis seed structure mismatch")
    return analyze_acquisition(evaluations)
