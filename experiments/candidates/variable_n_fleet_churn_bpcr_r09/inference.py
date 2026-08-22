"""Finite exact revision-09 complementary-subset sign-flip inference."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import heapq
import math
from typing import Iterable, Sequence


ROWS = 16
H = 1 << 15
FAMILY_Q = {12: 28, 24: 14, 8: 41, 28: 12, 18: 19}
FAMILY_NONCOVERAGE_NUMERATOR = {12: 324, 24: 312, 8: 320, 28: 308, 18: 324}


def exact_dyadic(value: float) -> Fraction:
    if not math.isfinite(value):
        raise ValueError("inference input must be a finite canonical binary64")
    return Fraction.from_float(float(value))


@dataclass(frozen=True)
class ExactInterval:
    lower: Fraction
    upper: Fraction
    q: int
    partition_visits: int = H
    subset_mean_constructions: int = 2 * (H - 1)
    comparison_ceiling: int = (H - 1) + 26 * H


def complementary_subset_interval(values: Sequence[float | Fraction], family_size: int) -> ExactInterval:
    if len(values) != ROWS or family_size not in FAMILY_Q:
        raise ValueError("revision-09 inference requires 16 rows and a frozen family size")
    x = tuple(item if isinstance(item, Fraction) else exact_dyadic(float(item)) for item in values)
    total = sum(x, Fraction())
    q = FAMILY_Q[family_size]
    keep = q - 1  # one infinite endpoint occupies the registered q-th rank
    lower_max_heap: list[Fraction] = []
    upper_min_heap: list[Fraction] = []
    # Row zero is always in P. code bits address rows 1..15.
    for code in range(H - 1):
        subset_sum = x[0]; count = 1
        for row in range(1, ROWS):
            if code & (1 << (row - 1)):
                subset_sum += x[row]; count += 1
        complement_count = ROWS - count
        a = subset_sum / count
        b = (total - subset_sum) / complement_count
        lower=min(a,b);upper=max(a,b)
        if len(lower_max_heap)<keep:heapq.heappush(lower_max_heap,-lower)
        elif lower < -lower_max_heap[0]:heapq.heapreplace(lower_max_heap,-lower)
        if len(upper_min_heap)<keep:heapq.heappush(upper_min_heap,upper)
        elif upper > upper_min_heap[0]:heapq.heapreplace(upper_min_heap,upper)
    # The omitted all-row partition contributes (-infinity,+infinity), hence
    # finite rank q-1 in one-based notation, or index q-2 here.
    lower = -lower_max_heap[0]
    upper = upper_min_heap[0]
    return ExactInterval(lower, upper, q)


def family_intervals(rows: Sequence[Sequence[float]], family_size: int) -> tuple[ExactInterval, ...]:
    materialized = tuple(tuple(row) for row in rows)
    if len(materialized) != ROWS or any(len(row) != family_size for row in materialized):
        raise ValueError("family matrix must have shape (16,family_size)")
    return tuple(
        complementary_subset_interval(tuple(row[j] for row in materialized), family_size)
        for j in range(family_size)
    )


def inference_contract() -> dict[str, object]:
    return {
        "schema": "VNFC-BPCR-R09-EXACT-INFERENCE-v1",
        "rows": ROWS,
        "canonical_partitions_per_coordinate": H,
        "family_sizes": [12, 24, 8, 28, 18],
        "q": [28, 14, 41, 12, 19],
        "noncoverage_numerators": [324, 312, 320, 308, 324],
        "all_coordinate_partition_visits": 2_949_120,
        "all_subset_mean_constructions": 5_898_060,
        "exact_rational_comparison_ceiling": 79_626_150,
        "joint_coverage_lower_bound": Fraction(32768 - 1588, 32768),
        "continuous_search": False,
        "multivariate_projection": False,
    }


def studentized_tail_count(values: Sequence[float | Fraction], center: float | Fraction) -> int:
    """Independent exact 2^16 equality-inclusive studentized tail checker."""
    if len(values) != ROWS:
        raise ValueError("studentized checker requires 16 rows")
    x = tuple(item if isinstance(item, Fraction) else exact_dyadic(float(item)) for item in values)
    t = center if isinstance(center, Fraction) else exact_dyadic(float(center))

    def statistic(signs: tuple[int, ...]) -> tuple[int, Fraction]:
        y = tuple(sign * (item - t) for sign, item in zip(signs, x))
        mean = sum(y, Fraction()) / ROWS
        ss = sum(((item - mean) ** 2 for item in y), Fraction())
        if ss == 0:
            return (0 if mean == 0 else (1 if mean > 0 else -1), Fraction())
        # Compare |4m/s| by its exact square; common factor 16*15 cancels.
        return (2, mean * mean / ss)

    observed = statistic((1,) * ROWS)

    def absolute_ge(candidate: tuple[int, Fraction], reference: tuple[int, Fraction]) -> bool:
        if candidate[0] in (-1, 1):
            return True
        if reference[0] in (-1, 1):
            return False
        return candidate[1] >= reference[1]

    count = 0
    for code in range(1 << ROWS):
        signs = tuple(1 if code & (1 << row) else -1 for row in range(ROWS))
        count += int(absolute_ge(statistic(signs), observed))
    return count
