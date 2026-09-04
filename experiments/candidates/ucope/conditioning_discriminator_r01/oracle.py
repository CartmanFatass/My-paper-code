"""Public exact finite-host equations, independent of every historical runtime."""

from __future__ import annotations

from fractions import Fraction
from math import comb

from .contract import CONTEXTS, K_EVAL, K_TRAIN, TARGET_CONTEXT_ID, context_id


def tail_q(regime: str, period: int) -> Fraction:
    if regime not in {"SHORT", "LONG"} or type(period) is not int or not 1 <= period <= 9:
        raise ValueError("invalid tail state/action")
    center = 2 if regime == "SHORT" else 8
    return Fraction(95, 100) - Fraction((period - center) ** 2, 100)


def tail_return(regime: str, period: int) -> Fraction:
    return tail_q(regime, period) - Fraction(period, 100) - Fraction(period * period, 1000)


def count_mass(regime: str, reliability: Fraction, count: int) -> Fraction:
    chance = reliability if regime == "SHORT" else 1 - reliability
    return Fraction(1, 2) * comb(6, count) * chance**count * (1 - chance) ** (6 - count)


def posterior_short(link: str, reliability: Fraction, count: int) -> Fraction:
    if link == "SEVERED":
        return Fraction(1, 2)
    if link != "LINKED" or not 0 <= count <= 6:
        raise ValueError("invalid posterior input")
    short, long = count_mass("SHORT", reliability, count), count_mass("LONG", reliability, count)
    return short / (short + long)


def expected_tail(period: int, belief: Fraction) -> Fraction:
    return belief * tail_return("SHORT", period) + (1 - belief) * tail_return("LONG", period)


def optimal_tail(periods: tuple[int, ...], belief: Fraction) -> tuple[int, Fraction, bool]:
    ranked = sorted((expected_tail(period, belief), -index, period) for index, period in enumerate(periods))
    return ranked[-1][2], ranked[-1][0], ranked[-1][0] != ranked[-2][0]


def direct_probe(cost: Fraction) -> Fraction:
    return Fraction(1, 25) - cost


def build_oracle(periods: tuple[int, ...]) -> dict[str, dict[str, object]]:
    if periods not in (K_TRAIN, K_EVAL):
        raise ValueError("oracle support must be exact odd or even inventory")
    result = {}
    for context in CONTEXTS:
        link, reliability, cost = context
        baseline_period, baseline, baseline_unique = optimal_tail(periods, Fraction(1, 2))
        learned = Fraction(0)
        tail_policy = {}
        unique = baseline_unique
        for count in range(7):
            mass = count_mass("SHORT", reliability, count) + count_mass("LONG", reliability, count)
            period, value, cell_unique = optimal_tail(periods, posterior_short(link, reliability, count))
            learned += mass * value
            tail_policy[str(count)] = period
            unique &= cell_unique
        probe_value = learned + direct_probe(cost)
        result[context_id(context)] = {
            "action": "PROBE" if probe_value > baseline else "IMMEDIATE",
            "baseline_period": baseline_period,
            "baseline": baseline,
            "probe_value": probe_value,
            "direct_probe": direct_probe(cost),
            "net_acquisition": probe_value - baseline,
            "tail_policy": tail_policy,
            "unique": unique and probe_value != baseline,
        }
    return result


def validate_host() -> dict[str, object]:
    even = build_oracle(K_EVAL)
    odd = build_oracle(K_TRAIN)
    positives = [cell for cell, row in even.items() if row["net_acquisition"] > 0]
    if positives != [TARGET_CONTEXT_ID] or any(row["direct_probe"] >= 0 for row in even.values()):
        raise ValueError("host opportunity map is nondiscriminating")
    if any(not row["unique"] for oracle in (odd, even) for row in oracle.values()):
        raise ValueError("host oracle has a nonunique choice")
    return {"valid": True, "positive_context": TARGET_CONTEXT_ID, "odd_unique": True, "even_unique": True}
