"""Deterministic algebraic conformance surfaces for the frozen controllers.

These functions encode no trainable parameters or optimizer state.  They only
prove the prospectively specified containment, reversal, and set-compositor
relationships on caller-supplied finite fixture logits.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .config import ACTION_COUNT, EventOrder, decode_action


def risk_order(action: int | tuple[int, int, int]) -> float:
    command = decode_action(action) if isinstance(action, int) else tuple(action)
    if len(command) != 3 or any(value not in (0, 1, 2) for value in command):
        raise ValueError("risk_order requires one legal three-carrier command")
    mean = sum(command) / 3.0
    imbalance = max(abs(value - mean) for value in command)
    return 0.75 * (mean / 2.0) + 0.25 * (imbalance / (4.0 / 3.0))


RISK_VECTOR = tuple(risk_order(code) for code in range(ACTION_COUNT))


def _finite_vector(values: Iterable[float], name: str) -> tuple[float, ...]:
    vector = tuple(float(value) for value in values)
    if len(vector) != ACTION_COUNT or not all(math.isfinite(value) for value in vector):
        raise ValueError(f"{name} must contain exactly 27 finite logits")
    return vector


def treatment_logits(base: Iterable[float], *, alpha: float, q: float) -> tuple[float, ...]:
    base_vector = _finite_vector(base, "base")
    if not math.isfinite(alpha) or alpha < 0.0:
        raise ValueError("alpha must be finite and nonnegative")
    if q not in (0.0, 0.5, 1.0):
        raise ValueError("fixture chronology input must be 0, 0.5, or 1")
    return tuple(value - q * alpha * rho for value, rho in zip(base_vector, RISK_VECTOR))


def free_logits(
    base: Iterable[float],
    *,
    alpha: float,
    q: float,
    residual: Iterable[float],
) -> tuple[float, ...]:
    direct = treatment_logits(base, alpha=alpha, q=q)
    residual_vector = _finite_vector(residual, "residual")
    return tuple(value + delta for value, delta in zip(direct, residual_vector))


def reversed_logits(base: Iterable[float], *, alpha: float, true_q: float) -> tuple[float, ...]:
    if true_q not in (0.0, 1.0):
        raise ValueError("true_q must be a tied physical chronology bit")
    return treatment_logits(base, alpha=alpha, q=1.0 - true_q)


@dataclass(frozen=True)
class SetCompositorInput:
    """Order-free controller input; no position/timestamp/recency field exists."""

    public_observation: tuple[float, ...]
    event_multiset: tuple[tuple[str, float], ...]
    q_set: float = 0.5


def set_compositor(
    public_observation: Iterable[float],
    first: tuple[str, float],
    second: tuple[str, float],
) -> SetCompositorInput:
    public = tuple(float(value) for value in public_observation)
    if len(public) != 14 or not all(math.isfinite(value) for value in public):
        raise ValueError("SET compositor requires the exact finite public 14-vector")
    events = (first, second)
    if sorted(name for name, _ in events) != ["CROSSWIND", "RETENSION"]:
        raise ValueError("SET compositor requires exactly the registered event multiset")
    if not all(math.isfinite(float(magnitude)) for _, magnitude in events):
        raise ValueError("event magnitudes must be finite")
    canonical = tuple(sorted(((str(name), float(magnitude)) for name, magnitude in events)))
    return SetCompositorInput(public_observation=public, event_multiset=canonical)


def strict_containment_witness() -> dict[str, object]:
    """Return an explicit residual which violates the treatment risk ordering."""

    base = (0.0,) * ACTION_COUNT
    zero = (0.0,) * ACTION_COUNT
    treatment = treatment_logits(base, alpha=1.0, q=1.0)
    contained = free_logits(base, alpha=1.0, q=1.0, residual=zero)
    residual = [0.0] * ACTION_COUNT
    residual[26] = 2.0  # raise rho((2,2,2)) only when q=1 in the fixture witness
    outside = free_logits(base, alpha=1.0, q=1.0, residual=residual)
    return {
        "zero_residual_exact": contained == treatment,
        "low_risk_code": 0,
        "high_risk_code": 26,
        "treatment_high_minus_low": treatment[26] - treatment[0],
        "free_high_minus_low": outside[26] - outside[0],
        "strictly_outside_treatment_ordering": outside[26] > outside[0],
    }


def chronology_bit(order: EventOrder) -> float:
    return order.q
