"""Ordered seven-branch A/RECON result rule."""

from __future__ import annotations


def decide_branch(
    *,
    resource_ready: bool,
    integrity_valid: bool,
    source_population_established: bool,
    w: int,
    r7: int,
    r13: int,
) -> str:
    if not resource_ready:
        return "A_NO_RESULT_RESOURCE_REFUSAL"
    if not integrity_valid:
        return "A_INVALID_EVIDENCE"
    if not source_population_established:
        return "A_SOURCE_POPULATION_NOT_ESTABLISHED"
    if w > 0 and r7 == 1 and r13 == 1:
        return "A_TWO_SIDED_DURATION_ACTION_RELEVANCE"
    if w > 0 and r7 + r13 == 1:
        return "A_ONE_SIDED_DURATION_ACTION_RELEVANCE"
    if w > 0:
        return "A_ACTION_RELEVANT_NO_MATERIAL_CROSS_K_PREFERENCE"
    return "A_ZERO_ACTION_VALUE_SPAN"


__all__ = ["decide_branch"]
