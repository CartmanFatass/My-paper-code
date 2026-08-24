"""Exact result-blind mapping from frozen block metrics to 6,990 estimands."""

from __future__ import annotations

from typing import Mapping

import math

from .production_inference import complete_estimand_manifest


CONTRAST_ARMS = {
    "S-N": ("STRUCTURED", "NEVER"), "F-S": ("FLEX", "STRUCTURED"),
    "F-N": ("FLEX", "NEVER"), "I-N": ("IMMEDIATE", "NEVER"),
    "I-S": ("IMMEDIATE", "STRUCTURED"), "H-N": ("HYSTERESIS", "NEVER"),
    "H-S": ("HYSTERESIS", "STRUCTURED"), "REAL-SHAM": ("REAL", "SHAM"),
}


class EstimandAssemblyError(RuntimeError):
    pass


def _finite(metrics: Mapping[tuple[str, ...], float], key: tuple[str, ...]) -> float:
    try:
        value = float(metrics[key])
    except (KeyError, TypeError, ValueError) as error:
        raise EstimandAssemblyError("required block metric is absent: " + "/".join(key)) from error
    if not math.isfinite(value):
        raise EstimandAssemblyError("required block metric is nonfinite: " + "/".join(key))
    return value


def _endpoint_contrast(
    metrics: Mapping[tuple[str, ...], float], contrast: str, endpoint: str,
    regime: str, schedule: str, speed: str, phase: str | None = None,
) -> float:
    treatment, control = CONTRAST_ARMS[contrast]
    prefix = "PHASE_ENDPOINT" if phase is not None else "ENDPOINT"
    suffix = (regime, schedule, speed, endpoint) if phase is None else (regime, schedule, speed, phase, endpoint)
    a = _finite(metrics, (prefix, treatment, *suffix)); c = _finite(metrics, (prefix, control, *suffix))
    return a - c if endpoint in ("MEAN", "TAIL") else c - a


def _energy_ratio(
    metrics: Mapping[tuple[str, ...], float], contrast: str,
    regime: str, schedule: str, speed: str, phase: str | None = None,
) -> float:
    treatment, control = CONTRAST_ARMS[contrast]
    prefix = "PHASE_ENERGY" if phase is not None else "ENERGY"
    suffix = (regime, schedule, speed) if phase is None else (regime, schedule, speed, phase)
    a = _finite(metrics, (prefix, treatment, *suffix)); c = _finite(metrics, (prefix, control, *suffix))
    if c == 0.0:
        if a == 0.0:
            return 0.0
        raise EstimandAssemblyError("positive treatment energy has zero comparator energy")
    return (a - c) / c


def assemble_complete_block_rows(metrics: Mapping[tuple[str, ...], float]) -> dict[str, float]:
    rows: dict[str, float] = {}
    for identity in complete_estimand_manifest():
        fields = identity.split("/"); family = fields[0]
        if family == "COMPETENCE_NO_DEGRADATION":
            arm, regime, schedule, speed = fields[1:]
            value = _finite(metrics, ("COMPETENCE_NO_DEGRADATION", arm, regime, schedule, speed))
        elif family == "COMPETENCE_PRE_ONSET":
            arm, regime, schedule, speed = fields[1:]
            value = _finite(metrics, ("COMPETENCE_PRE_ONSET", arm, regime, schedule, speed))
        elif family == "OPPORTUNITY":
            quantity, regime, schedule, speed = fields[1:]
            value = _finite(metrics, ("OPPORTUNITY", quantity, regime, schedule, speed))
        elif family == "ADAPTIVE_SUPPORT":
            arm, quantity, regime, schedule, speed = fields[1:]
            value = _finite(metrics, ("ADAPTIVE_SUPPORT", arm, quantity, regime, schedule, speed))
        elif family == "NEVER_HEADROOM":
            quantity, regime, schedule, speed = fields[1:]
            value = _finite(metrics, ("NEVER_HEADROOM", quantity, regime, schedule, speed))
        elif family == "ENDPOINT_EFFECT":
            contrast, endpoint, regime, schedule, speed = fields[1:]
            value = _endpoint_contrast(metrics, contrast, endpoint, regime, schedule, speed)
        elif family == "ENERGY_RATIO":
            contrast, regime, schedule, speed = fields[1:]
            value = _energy_ratio(metrics, contrast, regime, schedule, speed)
        elif family == "HARD_EVENT_RATE":
            population, event, regime, schedule, speed = fields[1:]
            value = _finite(metrics, ("HARD_EVENT_RATE", population, event, regime, schedule, speed))
        elif family == "PHASE_ENDPOINT_DIFFERENCE":
            contrast, endpoint, regime, schedule, speed, phase = fields[1:]
            value = _endpoint_contrast(metrics, contrast, endpoint, regime, schedule, speed, phase) - _endpoint_contrast(metrics, contrast, endpoint, regime, schedule, speed)
        elif family == "PHASE_ENERGY_DIFFERENCE":
            contrast, regime, schedule, speed, phase = fields[1:]
            value = _energy_ratio(metrics, contrast, regime, schedule, speed, phase) - _energy_ratio(metrics, contrast, regime, schedule, speed)
        else:  # pragma: no cover - complete manifest owns the family set
            raise EstimandAssemblyError("unregistered estimand family: " + family)
        rows[identity] = value
    if len(rows) != 6_990 or len(set(rows)) != 6_990:
        raise EstimandAssemblyError("assembled block estimand inventory differs")
    return rows


__all__ = ["EstimandAssemblyError", "assemble_complete_block_rows"]
