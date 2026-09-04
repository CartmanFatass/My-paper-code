"""Frozen ordered eight-branch result rule."""

from __future__ import annotations

import math
import statistics


def decide_branch(facts: dict[str, object]) -> str:
    if facts.get("integrity_valid") is not True:
        return "INVALID_EVIDENCE"
    if facts.get("host_pass") is not True:
        return "HOST_NOT_DURATION_DISCRIMINATING"
    exposures = facts.get("exposure_final", {})
    exposure_values = [
        float(value) for arm in ("D6", "D8")
        for value in exposures.get(arm, [])
    ] if isinstance(exposures, dict) else []
    if (
        len(exposure_values) != 6
        or any(not math.isfinite(value) or value < 0.0 for value in exposure_values)
    ):
        return "INVALID_EVIDENCE"
    if any(value == 0.0 for value in exposure_values):
        return "EXPOSURE_NOT_ACHIEVED"

    d6 = [bool(value) for value in facts["d6_competent"]]
    d8 = [bool(value) for value in facts["d8_competent"]]
    if len(d6) != 3 or len(d8) != 3:
        return "INVALID_EVIDENCE"
    if not all(d8):
        return "D8_COMPARATOR_NOT_COMPETENT"

    delta_t = [float(value) for value in facts["delta_t"]]
    delta_auc = [float(value) for value in facts["delta_auc"]]
    witnesses = [bool(value) for value in facts["witness"]]
    returns = [float(value) for value in facts["final_return_difference"]]
    if not all(len(values) == 3 for values in (delta_t, delta_auc, witnesses, returns)):
        return "INVALID_EVIDENCE"
    if any(not math.isfinite(value) for value in (*delta_t, *delta_auc, *returns)):
        return "INVALID_EVIDENCE"
    med_t = statistics.median(delta_t)
    med_auc = statistics.median(delta_auc)
    tick = 1.0 / 364.0
    if (
        all(d6) and med_t >= 20.0 and med_auc >= 0.05
        and sum(witnesses) >= 2 and all(value >= -tick for value in returns)
    ):
        return "PRELIMINARY_CROSS_K_VALUE_SHARING_SIGNAL"
    if sum(not value for value in d6) >= 2 or (med_t <= -20.0 and med_auc <= -0.05):
        return "PRELIMINARY_NEGATIVE_TRANSFER"
    if (
        all(d6) and abs(med_t) < 20.0 and abs(med_auc) < 0.05
        and all(-tick <= value <= tick for value in returns)
    ):
        return "NO_MATERIAL_VALUE_SHARING_DIFFERENCE"
    return "INSTABILITY_OR_STATE_HETEROGENEITY"


__all__ = ["decide_branch"]
