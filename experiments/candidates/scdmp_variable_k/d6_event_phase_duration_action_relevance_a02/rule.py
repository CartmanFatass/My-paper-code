"""Ordered nine-branch A02 finite result rule."""

from __future__ import annotations


def decide_branch(
    *,
    resource_ready: bool,
    integrity_valid: bool,
    population_established: bool,
    k7: int,
    k78: int,
    n7_plus: int,
    n7_minus: int,
    n78_minus: int,
    n78_plus: int,
    all_zero: bool,
) -> str:
    if not resource_ready:
        return "A02_NO_RESULT_RESOURCE_REFUSAL"
    if not integrity_valid:
        return "A02_INVALID_EVIDENCE"
    if not population_established:
        return "A02_EVENT_PHASE_POPULATION_NOT_ESTABLISHED"
    short = k7 >= 192 and n7_plus >= 4 and n7_minus <= 1
    long = k78 <= -192 and n78_minus >= 4 and n78_plus <= 1
    if short and long:
        return "A02_EXPECTED_TWO_SIDED_EVENT_ALIGNMENT"
    if (k7 <= -192 and n7_minus >= 4) or (k78 >= 192 and n78_plus >= 4):
        return "A02_REVERSED_EVENT_ALIGNMENT"
    if short:
        return "A02_SHORT_ALIGNMENT_ONLY"
    if long:
        return "A02_LONG_ALIGNMENT_ONLY"
    if all_zero:
        return "A02_ZERO_DURATION_POLICY_SPAN"
    return "A02_NONMATERIAL_OR_HETEROGENEOUS_EVENT_ALIGNMENT"


__all__ = ["decide_branch"]
