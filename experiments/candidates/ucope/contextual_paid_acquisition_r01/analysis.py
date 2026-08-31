"""Prespecified BELIEF competence and acquisition analysis."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

from .contract import SEED_SLOTS, as_fraction, context_id, contexts, fraction_json
from .evaluation import validate_competence
from .schema import SeedEvaluation

TARGET_CELL = "LINKED-p17_20-c9_100"
EXPECTED_CONTEXT_IDS = frozenset(context_id(context) for context in contexts())


def minimum_signed_specificity(cell_evidence: Mapping[str, Mapping[str, Any]]) -> Fraction:
    if not isinstance(cell_evidence, Mapping) or set(cell_evidence) != EXPECTED_CONTEXT_IDS:
        raise ValueError("specificity requires the exact eight-cell fixed panel")
    signed = []
    for cell, evidence in cell_evidence.items():
        if not isinstance(evidence, Mapping) or "Gamma" not in evidence:
            raise ValueError("cell evidence lacks exact Gamma")
        gamma = as_fraction(evidence["Gamma"])
        signed.append(gamma if cell == TARGET_CELL else -gamma)
    return min(signed)


def _seed_minimum(item: SeedEvaluation) -> Fraction:
    derived = minimum_signed_specificity(item.cell_evidence)
    if item.minimum_seed_signed_specificity != fraction_json(derived):
        raise ValueError("stored seed signed minimum differs from exact cell evidence")
    return derived


def analyze_acquisition(evaluations: list[SeedEvaluation] | tuple[SeedEvaluation, ...]) -> dict[str, Any]:
    competence = validate_competence(evaluations)
    from .oracle import construct_flip_certificate
    oracle_vector = {cell.context_id: cell.test_action for cell in construct_flip_certificate().cells}
    all_flips = all(item.action_vector == oracle_vector for item in evaluations)
    seed_minima = tuple(_seed_minimum(item) for item in evaluations)
    if len(seed_minima) != 10:
        raise ValueError("fixed-panel acquisition requires all ten retained seed slots")
    panel_minimum = min(seed_minima)
    acquisition_pass = bool(competence["competence_pass"] and all_flips and panel_minimum > Fraction(0))
    disposition = (
        "STOP_FIXED_PANEL_COMPETENCE"
        if not competence["competence_pass"]
        else "FIXED_PANEL_ACQUISITION_SUPPORTED"
        if acquisition_pass
        else "STOP_FIXED_PANEL_ACQUISITION"
    )
    return {
        **competence,
        "acquisition_all_flips": all_flips,
        "panel_min_signed_specificity": fraction_json(panel_minimum),
        "acquisition_pass": acquisition_pass,
        "fixed_panel_disposition": disposition,
    }


def validate_analysis(evaluations: list[SeedEvaluation] | tuple[SeedEvaluation, ...]) -> dict[str, Any]:
    if {item.seed_slot for item in evaluations} != set(SEED_SLOTS):
        raise ValueError("analysis seed structure mismatch")
    return analyze_acquisition(evaluations)
