"""Exact finite-host equations; no dependency on consumed UCOPE artifacts."""

from __future__ import annotations

from fractions import Fraction
from math import comb

from .contract import CONTEXTS, K_EVAL, context_id


def tail_q(regime: str, period: int) -> Fraction:
    if regime not in {"SHORT", "LONG"} or type(period) is not int or not 1 <= period <= 9:
        raise ValueError("invalid tail state/action")
    center = 2 if regime == "SHORT" else 8
    return Fraction(95, 100) - Fraction((period - center) ** 2, 100)


def tail_return(regime: str, period: int) -> Fraction:
    return tail_q(regime, period) - Fraction(period, 100) - Fraction(period * period, 1000)


def joint_count_probability(regime: str, p: Fraction, count: int) -> Fraction:
    chance = p if regime == "SHORT" else 1 - p
    return Fraction(1, 2) * comb(6, count) * chance**count * (1 - chance) ** (6 - count)


def posterior_short(link: str, p: Fraction, count: int) -> Fraction:
    if link == "SEVERED":
        return Fraction(1, 2)
    if link != "LINKED" or not 0 <= count <= 6:
        raise ValueError("invalid posterior inputs")
    short = joint_count_probability("SHORT", p, count)
    long = joint_count_probability("LONG", p, count)
    return short / (short + long)


def expected_tail(period: int, belief: Fraction) -> Fraction:
    return belief * tail_return("SHORT", period) + (1 - belief) * tail_return("LONG", period)


def optimal_tail(periods: tuple[int, ...], belief: Fraction) -> tuple[int, Fraction, bool]:
    ranked = sorted((expected_tail(period, belief), -period, period) for period in periods)
    return ranked[-1][2], ranked[-1][0], ranked[-1][0] != ranked[-2][0]


def direct_probe(cost: Fraction) -> Fraction:
    return Fraction(1, 25) - cost


def build_oracle() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for context in CONTEXTS:
        link, p, cost = context
        baseline_period, baseline, immediate_unique = optimal_tail(K_EVAL, Fraction(1, 2))
        informed = Fraction(0)
        all_tail_unique = True
        tail = {}
        for count in range(7):
            mass = joint_count_probability("SHORT", p, count) + joint_count_probability("LONG", p, count)
            belief = posterior_short(link, p, count)
            period, value, unique = optimal_tail(K_EVAL, belief)
            informed += mass * value
            all_tail_unique &= unique
            tail[str(count)] = period
        acquisition = informed + direct_probe(cost)
        rows[context_id(context)] = {
            "action": "PROBE" if acquisition > baseline else "IMMEDIATE",
            "baseline_period": baseline_period,
            "baseline": baseline,
            "probe_value": acquisition,
            "direct_probe": direct_probe(cost),
            "net_acquisition": acquisition - baseline,
            "tail_policy": tail,
            "unique": immediate_unique and all_tail_unique and acquisition != baseline,
        }
    return rows
