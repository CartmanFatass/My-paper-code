"""Source-owned scalar binary64 operations for the VNFC R02 oracle."""

from __future__ import annotations

from fractions import Fraction
import math
import struct
from typing import Sequence

from .contract import ContractViolation, ScalarTranscendentals


def rn64(value: float) -> float:
    """Materialize one finite binary64 result and canonicalize signed zero."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractViolation("RN64 accepts only real scalar primitives")
    result = float(value)
    if not math.isfinite(result):
        raise ContractViolation("nonfinite scalar is outside the frozen law")
    return 0.0 if result == 0.0 else result


def binary64_bits(value: float) -> int:
    return int.from_bytes(struct.pack(">d", rn64(value)), "big")


def _finite_vector(values: Sequence[float], *, nonempty: bool = True) -> tuple[float, ...]:
    result = tuple(rn64(value) for value in values)
    if nonempty and not result:
        raise ContractViolation("scalar vector must be nonempty")
    return result


def affine(weights: Sequence[Sequence[float]], bias: Sequence[float], inputs: Sequence[float]) -> tuple[float, ...]:
    x = _finite_vector(inputs)
    b = _finite_vector(bias)
    if len(weights) != len(b):
        raise ContractViolation("affine output shape differs from bias shape")
    output: list[float] = []
    for row, start in zip(weights, b):
        w = _finite_vector(row)
        if len(w) != len(x):
            raise ContractViolation("affine input width drift")
        accumulator = start
        for weight, value in zip(w, x):
            product = rn64(weight * value)
            accumulator = rn64(accumulator + product)
        output.append(accumulator)
    return tuple(output)


def silu(value: float, kernel: ScalarTranscendentals) -> float:
    x = rn64(value)
    sigmoid = rn64(kernel.sigmoid_R02(x))
    return rn64(x * sigmoid)


def exact_roster_mean(rows: Sequence[Sequence[float]]) -> tuple[float, ...]:
    if not rows:
        raise ContractViolation("roster mean requires N>0")
    finite_rows = tuple(_finite_vector(row) for row in rows)
    width = len(finite_rows[0])
    if any(len(row) != width for row in finite_rows):
        raise ContractViolation("roster row width drift")
    means: list[float] = []
    for column in range(width):
        exact_sum = sum((Fraction.from_float(row[column]) for row in finite_rows), Fraction(0))
        means.append(rn64(float(exact_sum / len(finite_rows))))
    return tuple(means)


def strict_roster_max(rows: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], tuple[int, ...]]:
    if not rows:
        raise ContractViolation("roster maximum requires N>0")
    finite_rows = tuple(_finite_vector(row) for row in rows)
    width = len(finite_rows[0])
    if any(len(row) != width for row in finite_rows):
        raise ContractViolation("roster row width drift")
    values = list(finite_rows[0])
    winners = [0] * width
    for row_index, row in enumerate(finite_rows[1:], start=1):
        for column, value in enumerate(row):
            if value > values[column]:
                values[column] = value
                winners[column] = row_index
    return tuple(values), tuple(winners)


def roster_mean_adjoint(incoming: Sequence[float], roster_size: int) -> tuple[tuple[float, ...], ...]:
    if isinstance(roster_size, bool) or not isinstance(roster_size, int) or roster_size <= 0:
        raise ContractViolation("roster mean adjoint requires N>0")
    gradient = tuple(rn64(value / roster_size) for value in _finite_vector(incoming))
    return tuple(gradient for _ in range(roster_size))


def roster_max_adjoint(
    incoming: Sequence[float], winners: Sequence[int], roster_size: int
) -> tuple[tuple[float, ...], ...]:
    gradient = _finite_vector(incoming)
    if len(winners) != len(gradient) or roster_size <= 0:
        raise ContractViolation("roster maximum adjoint shape drift")
    rows = [[0.0] * len(gradient) for _ in range(roster_size)]
    for column, (value, winner) in enumerate(zip(gradient, winners)):
        if isinstance(winner, bool) or not isinstance(winner, int) or not 0 <= winner < roster_size:
            raise ContractViolation("roster maximum winner index is invalid")
        rows[winner][column] = value
    return tuple(tuple(row) for row in rows)


def prefix_sum(current: Sequence[float], hidden: Sequence[float]) -> tuple[float, ...]:
    left = _finite_vector(current)
    right = _finite_vector(hidden)
    if len(left) != len(right):
        raise ContractViolation("prefix sum width drift")
    return tuple(rn64(a + b) for a, b in zip(left, right))


def prefix_max(current: Sequence[float], hidden: Sequence[float]) -> tuple[float, ...]:
    left = _finite_vector(current)
    right = _finite_vector(hidden)
    if len(left) != len(right):
        raise ContractViolation("prefix maximum width drift")
    return tuple(b if b > a else a for a, b in zip(left, right))


def update_prefix(
    sum_prefix: Sequence[float],
    max_prefix: Sequence[float],
    hidden: Sequence[float],
    *,
    max_has_value: bool,
    variable: bool,
    selected_null: bool,
) -> tuple[tuple[float, ...], tuple[float, ...], bool]:
    current_sum = _finite_vector(sum_prefix)
    current_max = _finite_vector(max_prefix)
    candidate = _finite_vector(hidden)
    if not (len(current_sum) == len(current_max) == len(candidate)):
        raise ContractViolation("prefix width drift")
    if not isinstance(max_has_value, bool):
        raise ContractViolation("prefix max occupancy must be boolean")
    if not variable or selected_null:
        return current_sum, current_max, max_has_value
    next_max = prefix_max(current_max, candidate) if max_has_value else candidate
    return prefix_sum(current_sum, candidate), next_max, True
