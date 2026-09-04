"""Immutable opposite-label raw-value reassociation control."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Sequence

from ..contracts.core import ContractError


@dataclass(frozen=True, slots=True)
class RawValueRow:
    pair_id: str
    raw_values: tuple[Fraction, ...]
    label: int
    association: str


RAW_VALUE_ROWS = (
    RawValueRow("PAIR_A", (Fraction(-1), Fraction(2)), 0, "INTACT"),
    RawValueRow("PAIR_A", (Fraction(-1), Fraction(2)), 1, "REASSOCIATED"),
    RawValueRow("PAIR_B", (Fraction(3), Fraction(1, 2)), 1, "INTACT"),
    RawValueRow("PAIR_B", (Fraction(3), Fraction(1, 2)), 0, "REASSOCIATED"),
)


def validate_opposite_label_pairs(rows: Sequence[RawValueRow] = RAW_VALUE_ROWS) -> None:
    groups: dict[str, list[RawValueRow]] = {}
    for row in rows:
        groups.setdefault(row.pair_id, []).append(row)
    if not groups:
        raise ContractError("raw-value fixture is empty")
    for pair_id, pair in groups.items():
        if len(pair) != 2 or pair[0].raw_values != pair[1].raw_values or {pair[0].label, pair[1].label} != {0, 1}:
            raise ContractError(f"raw-value pair {pair_id} is not an immutable opposite-label pair")
        if {pair[0].association, pair[1].association} != {"INTACT", "REASSOCIATED"}:
            raise ContractError(f"raw-value pair {pair_id} lacks both associations")


def balanced_accuracy(classifier: Callable[[tuple[Fraction, ...]], int], rows: Sequence[RawValueRow] = RAW_VALUE_ROWS) -> Fraction:
    validate_opposite_label_pairs(rows)
    predictions: dict[tuple[Fraction, ...], int] = {}
    for row in rows:
        prediction = classifier(row.raw_values)
        if type(prediction) is not int or prediction not in (0, 1):
            raise ContractError("raw-value prediction must be literal 0 or 1")
        if row.raw_values in predictions and predictions[row.raw_values] != prediction:
            raise ContractError("raw-value classifier is not deterministic for identical inputs")
        predictions[row.raw_values] = prediction
    recalls = []
    for label in (0, 1):
        class_rows = [row for row in rows if row.label == label]
        correct = sum(predictions[row.raw_values] == label for row in class_rows)
        recalls.append(Fraction(correct, len(class_rows)))
    return sum(recalls, Fraction()) / 2


def assert_raw_value_ceiling(classifier: Callable[[tuple[Fraction, ...]], int]) -> None:
    if balanced_accuracy(classifier) != Fraction(1, 2):
        raise ContractError("raw-value-only balanced accuracy must be exactly 1/2")
