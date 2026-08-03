"""Pure causal-contrast arithmetic for the event-commitment audit."""

from __future__ import annotations

import math
from typing import Any, Mapping

from ha_ctse_process.noncalendar_commitment_testbed import CAUSAL_AUDIT_BRANCHES


def _causal_contrasts(
    natural_action: str, outcomes: Mapping[str, Mapping[str, Any]],
) -> dict[str, float]:
    keep = float(outcomes["KEEP_HELD_MARK"]["utility"])
    deranged = float(outcomes["RENEW_DERANGED_MARK"]["utility"])
    candidate = float(outcomes["RENEW_CANDIDATE_MARK"]["utility"])
    if natural_action == "KEEP":
        return {
            "total": keep - candidate,
            "timing": keep - deranged,
            "mark": deranged - candidate,
        }
    return {
        "total": candidate - keep,
        "timing": deranged - keep,
        "mark": candidate - deranged,
    }


def _contrast_additivity_evidence(
    contrasts: Mapping[str, float], outcomes: Mapping[str, Mapping[str, Any]],
) -> dict[str, float]:
    """Account only for deterministic binary64 subtraction/addition rounding."""

    values = [
        float(contrasts[name]) for name in ("total", "timing", "mark")
    ] + [
        float(outcomes[name]["utility"]) for name in CAUSAL_AUDIT_BRANCHES
    ]
    residual = abs(values[0] - (values[1] + values[2]))
    bound = 4.0 * max(math.ulp(value) for value in values)
    return {"residual": residual, "bound": bound}
