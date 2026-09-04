"""Exact deterministic 24-point finite-panel descriptors and branch law."""

from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from typing import Sequence


DELTA = 1.0 / 32.0
BRANCHES = (
    "INVALID", "RAW_INCOMPETENT", "NO_RESOLVABLE_HEADROOM",
    "VALID_NARROW_CBSC_INDUCTIVE_BIAS", "GENERIC_FACTORIZATION_OR_CONDITIONING",
    "NO_CAPABILITY_SPECIFIC_ATTRIBUTION", "PRACTICAL_EQUIVALENCE",
    "RAW_OR_SHAM_MATERIALLY_SUPERIOR", "UNRESOLVED",
)


@dataclass(frozen=True)
class CoordinateDescriptor:
    minimum: float
    maximum: float
    range: float
    mean: float
    absolute_maximum: float


@dataclass(frozen=True)
class FinitePanelDecision:
    block_count: int
    coordinates: tuple[str, str, str]
    vectors: tuple[tuple[float, float, float], ...]
    descriptors: tuple[CoordinateDescriptor, CoordinateDescriptor, CoordinateDescriptor]


def reduce_finite_panel(vectors: Sequence[Sequence[float]]) -> FinitePanelDecision:
    if len(vectors) != 24 or any(len(vector) != 3 for vector in vectors):
        raise ValueError("exact finite panel requires 24 complete paired 3-vectors")
    material: list[tuple[float, float, float]] = []
    for vector in vectors:
        if any(type(value) is not float or not math.isfinite(value) for value in vector):
            raise TypeError("finite-panel coordinates must be finite float64 reductions")
        material.append((vector[0], vector[1], vector[2]))
    descriptors = []
    for coordinate in range(3):
        values = [vector[coordinate] for vector in material]
        minimum, maximum = min(values), max(values)
        descriptors.append(CoordinateDescriptor(
            minimum, maximum, maximum - minimum,
            float(np.asarray(values, dtype=np.float64).mean(dtype=np.float64)),
            max(abs(value) for value in values),
        ))
    if any(abs(value) > 11.0 / 8.0 for vector in material for value in vector[:2]):
        raise ValueError("d_SR/d_SS outside exact finite regret bound")
    if any(abs(vector[2]) > 2 for vector in material):
        raise ValueError("psi outside exact finite regret bound")
    return FinitePanelDecision(
        24, ("d_SR", "d_SS", "psi"), tuple(material), tuple(descriptors),
    )


def select_branch(
    decision: FinitePanelDecision | None,
    *, valid: bool, raw_competent: bool, no_resolvable_headroom: bool,
    structured_endpoint_gate: bool,
) -> str:
    if not valid or decision is None or decision.block_count != 24:
        return "INVALID"
    if not raw_competent:
        return "RAW_INCOMPETENT"
    if no_resolvable_headroom:
        return "NO_RESOLVABLE_HEADROOM"
    minimum = tuple(item.minimum for item in decision.descriptors)
    maximum = tuple(item.maximum for item in decision.descriptors)
    if all(value > DELTA for value in minimum) and structured_endpoint_gate:
        return "VALID_NARROW_CBSC_INDUCTIVE_BIAS"
    if minimum[0] > DELTA and minimum[1] <= DELTA:
        return "GENERIC_FACTORIZATION_OR_CONDITIONING"
    if minimum[0] > DELTA and minimum[1] > DELTA and minimum[2] <= DELTA:
        return "NO_CAPABILITY_SPECIFIC_ATTRIBUTION"
    if all(item.absolute_maximum <= DELTA for item in decision.descriptors):
        return "PRACTICAL_EQUIVALENCE"
    if maximum[0] < -DELTA or maximum[1] < -DELTA:
        return "RAW_OR_SHAM_MATERIALLY_SUPERIOR"
    return "UNRESOLVED"


__all__ = [
    "BRANCHES", "CoordinateDescriptor", "DELTA", "FinitePanelDecision",
    "reduce_finite_panel", "select_branch",
]
