"""Deterministic canonical oracle and exact finite load diagnostic."""

from __future__ import annotations

from functools import lru_cache
from fractions import Fraction
from itertools import product

import numpy as np

from .config import TRUE_UTILITY


@lru_cache(maxsize=None)
def _compositions(total: int, width: int = 5) -> tuple[tuple[int, ...], ...]:
    if width == 1:
        return ((total,),)
    values = []
    for first in range(total + 1):
        for rest in _compositions(total - first, width - 1):
            values.append((first, *rest))
    return tuple(values)


def canonical_oracle(n: int, demand_values: tuple[int, ...]) -> dict[str, object]:
    nr = n // 2
    best_score: int | None = None
    best_vector: tuple[int, ...] | None = None
    # Integer scale 60: utilities are 60/40/20/0; idle/unmet penalty is 3.
    utility = ((60, 40, 20, 0), (0, 20, 40, 60))
    for left in _compositions(nr):
        for right in _compositions(nr):
            assigned = tuple(left[j] + right[j] for j in range(4))
            if any(assigned[j] > demand_values[j] for j in range(4)):
                continue
            unmet = tuple(demand_values[j] - assigned[j] for j in range(4))
            score = sum(left[j] * utility[0][j] + right[j] * utility[1][j] for j in range(4))
            score -= 3 * (left[4] + right[4] + sum(unmet))
            vector = (*left[:4], *right[:4], left[4], right[4], *unmet)
            if best_score is None or score > best_score or (score == best_score and vector < best_vector):
                best_score, best_vector = score, vector
    if best_score is None or best_vector is None:
        raise RuntimeError("oracle found no legal aggregate coupling")
    return {
        "role_task_counts": np.asarray((*best_vector[:4], *best_vector[4:8]), dtype=np.int16).reshape(2, 4),
        "role_idle_counts": np.asarray(best_vector[8:10], dtype=np.int16),
        "unmet_counts": np.asarray(best_vector[10:14], dtype=np.int16),
        "reward": best_score / 60.0,
    }


@lru_cache(maxsize=None)
def load_diagnostic_expectation(n: int, demand_values: tuple[int, ...]) -> float:
    utility = tuple(tuple(Fraction(str(x)).limit_denominator() for x in row) for row in TRUE_UTILITY)

    @lru_cache(maxsize=None)
    def value(left: int, right: int, residual: tuple[int, ...]) -> Fraction:
        remaining = left + right
        if remaining == 0:
            return -Fraction(1, 20) * sum(residual)
        role_terms = []
        for role, count in ((0, left), (1, right)):
            if count == 0:
                continue
            legal = [j for j in range(4) if residual[j] > 0] + [4]
            weights = [Fraction(n + demand_values[j], n) if j < 4 else Fraction(1, 1) for j in legal]
            soft_den = sum(weights)
            expected = Fraction(0, 1)
            for action, weight in zip(legal, weights):
                probability = Fraction(19, 20) * weight / soft_den + Fraction(1, 20 * len(legal))
                next_residual = list(residual)
                immediate = -Fraction(1, 20) if action == 4 else utility[role][action]
                if action < 4:
                    next_residual[action] -= 1
                nxt = value(left - (role == 0), right - (role == 1), tuple(next_residual))
                expected += probability * (immediate + nxt)
            role_terms.append(Fraction(count, remaining) * expected)
        return sum(role_terms, Fraction(0, 1))

    return float(value(n // 2, n // 2, tuple(demand_values)))
