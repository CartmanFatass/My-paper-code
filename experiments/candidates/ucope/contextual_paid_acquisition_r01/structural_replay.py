"""Training-only deterministic row replay for the structural certificate.

This module deliberately has no package-relative imports.  The certificate runner supplies the
already-bound counter RNG module, while this surface freezes only the odd-period host primitives
needed to reproduce one retained training row before any fit is entered.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping


K_TRAIN = (1, 3, 5, 7, 9)
MARK_COUNT = 6
SEED_SLOTS = tuple(f"cpa-r01-fresh-slot-{index:02d}" for index in range(10))
LINKAGES = ("LINKED", "SEVERED")
RELIABILITIES = (Fraction(13, 20), Fraction(17, 20))
TOTAL_COSTS = (Fraction(9, 100), Fraction(7, 50))


def _as_fraction(value: Any) -> Fraction:
    if isinstance(value, bool):
        raise ValueError("boolean is not an exact context value")
    return value if isinstance(value, Fraction) else Fraction(value)


def _context_fields(context: Mapping[str, Any]) -> tuple[str, Fraction, Fraction, str]:
    if not isinstance(context, Mapping) or set(context) != {
        "link", "reliability", "total_cost",
    }:
        raise ValueError("context field inventory mismatch")
    link = context["link"]
    reliability = _as_fraction(context["reliability"])
    total_cost = _as_fraction(context["total_cost"])
    if link not in LINKAGES or reliability not in RELIABILITIES or total_cost not in TOTAL_COSTS:
        raise ValueError("context is outside the frozen population")
    cell = (
        f"{link}-p{reliability.numerator}_{reliability.denominator}"
        f"-c{total_cost.numerator}_{total_cost.denominator}"
    )
    return str(link), reliability, total_cost, cell


def _marks(
    regime: str,
    reliability: Fraction,
    namespace: str,
    seed_slot: str,
    index: int,
    rng: Any,
) -> tuple[str, ...]:
    if regime not in ("SHORT", "LONG"):
        raise ValueError("mark regime is outside the frozen alphabet")
    probability_short = reliability if regime == "SHORT" else 1 - reliability
    return tuple(
        "SHORT"
        if rng.bernoulli(float(probability_short), namespace, seed_slot, index, mark)
        else "LONG"
        for mark in range(MARK_COUNT)
    )


def _tail_probability(regime: str, period: int) -> Fraction:
    center = 2 if regime == "SHORT" else 8
    return Fraction(95, 100) - Fraction((period - center) ** 2, 100)


def expected_episode_row(
    *,
    seed_slot: str,
    context: Mapping[str, Any],
    index: int,
    root_action: str,
    period: int,
    regime: str,
    display_regime: str | None,
    rng: Any,
) -> dict[str, Any]:
    """Return the exact baseline row using only training-period laws and bound RNG calls."""

    if seed_slot not in SEED_SLOTS:
        raise ValueError("seed slot is outside the frozen panel")
    if type(index) is not int or index < 0:
        raise ValueError("episode index must be a nonnegative integer")
    if root_action not in ("PROBE", "IMMEDIATE") or period not in K_TRAIN:
        raise ValueError("behavior action or period is outside the training plan")
    if regime not in ("SHORT", "LONG"):
        raise ValueError("latent regime is outside the frozen alphabet")
    link, reliability, total_cost, cell = _context_fields(context)

    actual_marks = _marks(
        regime, reliability, "mark-uniform", seed_slot, index, rng
    )
    if link == "LINKED":
        if display_regime is not None and display_regime != regime:
            raise ValueError("linked display regime must equal the latent regime")
        displayed_regime = regime
        displayed_marks = actual_marks
    else:
        if display_regime not in ("SHORT", "LONG"):
            raise ValueError("severed context requires a balanced display regime")
        displayed_regime = display_regime
        displayed_marks = _marks(
            display_regime, reliability, "display-mark", seed_slot, index, rng
        )

    if root_action == "PROBE":
        probe_service_exact = Fraction(2, 25) * Fraction(
            actual_marks.count("SHORT"), MARK_COUNT
        )
        probe_time_exact = -Fraction(3, 100)
        probe_energy_exact = -(total_cost - Fraction(3, 100))
    else:
        probe_service_exact = probe_time_exact = probe_energy_exact = Fraction(0)

    tail_service = (
        1.0
        if rng.bernoulli(
            float(_tail_probability(regime, period)),
            "tail-service",
            seed_slot,
            index,
            period,
        )
        else 0.0
    )
    tail_time = float(-Fraction(period, 100))
    tail_energy = float(-Fraction(period * period, 1000))
    probe_service = float(probe_service_exact)
    probe_time = float(probe_time_exact)
    probe_energy = float(probe_energy_exact)
    tail_return = tail_service + tail_time + tail_energy
    probe_return = probe_service + probe_time + probe_energy
    unshaped_return = tail_return + probe_return

    return {
        "index": index,
        "seed_slot": seed_slot,
        "context_id": cell,
        "link": link,
        "reliability": str(reliability),
        "total_cost": str(total_cost),
        "regime": regime,
        "actual_marks": actual_marks,
        "displayed_regime": displayed_regime,
        "displayed_marks": displayed_marks,
        "displayed_short_count": displayed_marks.count("SHORT"),
        "root_action": root_action,
        "period": period,
        "primitive_ledger": {
            "tail_service": tail_service,
            "tail_time": tail_time,
            "tail_energy": tail_energy,
            "probe_service": probe_service,
            "probe_time": probe_time,
            "probe_energy": probe_energy,
            "executed_probe_count": 1 if root_action == "PROBE" else 0,
            "executed_probe_mark_count": MARK_COUNT if root_action == "PROBE" else 0,
            "executed_probe_time_units": 2 if root_action == "PROBE" else 0,
            "executed_tail_commit_count": 1,
            "executed_tail_period_units": period,
        },
        "tail_return": tail_return,
        "immediate_return": tail_return if root_action == "IMMEDIATE" else 0.0,
        "unshaped_return": unshaped_return,
    }
