"""Exact Fraction conditional-Q/Rao--Blackwell absorption fixture."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from .core import ContractError

MODES = ("PERSIST", "REPLACE", "EXPIRE")


@dataclass(frozen=True, slots=True)
class EGRCRRow:
    content: int
    mode: str
    action: int
    probability: Fraction
    utility: Fraction
    pathwise_effect: Fraction


def exact_fixture_rows() -> tuple[EGRCRRow, ...]:
    rows = []
    probability = Fraction(1, 12)
    for content in (1, -1):
        for mode in MODES:
            effect = Fraction(content if mode != "EXPIRE" else 0)
            for action in (0, 1):
                # Frozen potential-outcome table: baseline is 0 for c=+1 and 1 for c=-1.
                baseline = Fraction(0 if content == 1 else 1)
                utility = baseline + action * effect
                rows.append(EGRCRRow(content, mode, action, probability, utility, effect))
    return tuple(rows)


def conditional_q(content: int, action: int) -> Fraction:
    if content not in (-1, 1) or action not in (0, 1):
        raise ContractError("EGRCR conditional-Q support is c in +/-1 and a in {0,1}")
    baseline = Fraction(0 if content == 1 else 1)
    return baseline + Fraction(action * 2 * content, 3)


def _score_update(rows: Iterable[EGRCRRow], *, rao_blackwell: bool) -> tuple[Fraction, Fraction]:
    rows = tuple(rows)
    expected_support = {(c, mode, action) for c in (-1, 1) for mode in MODES for action in (0, 1)}
    if {(row.content, row.mode, row.action) for row in rows} != expected_support or len(rows) != 12:
        raise ContractError("EGRCR rows do not have exact finite support")
    if any(row.probability != Fraction(1, 12) for row in rows) or sum((row.probability for row in rows), Fraction()) != 1:
        raise ContractError("EGRCR rows do not have exact probability mass")
    intercept = Fraction(0)
    content_coordinate = Fraction(0)
    for row in rows:
        target = conditional_q(row.content, row.action) if rao_blackwell else row.utility
        score = Fraction(row.action, 1) - Fraction(1, 2)
        intercept += row.probability * score * target
        content_coordinate += row.probability * score * target * row.content
    return intercept, content_coordinate


def association_population_update(rows: Iterable[EGRCRRow] | None = None) -> tuple[Fraction, Fraction]:
    return _score_update(exact_fixture_rows() if rows is None else rows, rao_blackwell=False)


def rao_blackwell_population_update(rows: Iterable[EGRCRRow] | None = None) -> tuple[Fraction, Fraction]:
    return _score_update(exact_fixture_rows() if rows is None else rows, rao_blackwell=True)


def assert_rao_blackwell_equality() -> tuple[Fraction, Fraction]:
    association = association_population_update()
    generic = rao_blackwell_population_update()
    if association != generic or generic != (Fraction(0), Fraction(1, 6)):
        raise ContractError("EGRCR exact population equality failed")
    return generic
