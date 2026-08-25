"""Frozen numerical HMM/GLS reference; it is never named or used as an oracle."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt

import numpy as np

from .config import ACTIONS, HORIZON, MU, RHO, TIE_PRIORITY, ReferenceGrid, analytic_information

ACTION_INDEX = {name: index for index, name in enumerate(ACTIONS)}


def _transition_vector(ell: np.ndarray, k: int) -> np.ndarray:
    return 2.0 * np.arctanh((1.0 - 2.0 * 0.04) ** k * np.tanh(ell / 2.0))


def _commit_values(ell: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p_plus = np.empty_like(ell)
    positive = ell >= 0
    p_plus[positive] = 1.0 / (1.0 + np.exp(-ell[positive]))
    exp_ell = np.exp(ell[~positive])
    p_plus[~positive] = exp_ell / (1.0 + exp_ell)
    return p_plus, 1.0 - p_plus  # minus error, plus error


@dataclass
class ReferenceSurface:
    grid: ReferenceGrid
    n: int
    k: int
    regime: str
    ell_grid: np.ndarray
    values: dict[int, np.ndarray]
    action_values: dict[int, np.ndarray]

    @classmethod
    def construct(cls, grid: ReferenceGrid, n: int, k: int, regime: str) -> "ReferenceSurface":
        ell_grid = np.arange(grid.lower, grid.upper + grid.spacing / 2.0, grid.spacing, dtype=np.float64)
        nodes, weights = np.polynomial.hermite.hermgauss(grid.quadrature_nodes)
        weights = weights.astype(np.float64) / sqrt(np.pi)
        information = analytic_information(n, regime)
        values: dict[int, np.ndarray] = {}
        action_values: dict[int, np.ndarray] = {}
        # All primitive ticks are defined because the frozen 96-state activity
        # panel deliberately includes ticks that are not reached from t=0 for
        # every k. A continuation still advances by exactly k ticks.
        for t in range(HORIZON, -1, -1):
            minus_error, plus_error = _commit_values(ell_grid)
            q_matrix = np.full((4, ell_grid.size), np.inf, dtype=np.float64)
            q_matrix[ACTION_INDEX["COMMIT_MINUS"]] = minus_error
            q_matrix[ACTION_INDEX["COMMIT_PLUS"]] = plus_error
            if HORIZON - t >= k:
                next_t = t + k
                if next_t not in values:
                    raise AssertionError("reference time lattice is incomplete")
                ell_minus = _transition_vector(ell_grid, k)
                q_matrix[ACTION_INDEX["RELAY"]] = (
                    0.20 * k / 30.0
                    + 0.01
                    + np.interp(ell_minus, ell_grid, values[next_t], left=values[next_t][0], right=values[next_t][-1])
                )
                p_plus = 1.0 / (1.0 + np.exp(-ell_minus))
                continuation = np.zeros_like(ell_grid)
                normal_scale = sqrt(2.0 * information)
                for node, weight in zip(nodes, weights):
                    noise = normal_scale * node
                    plus_posterior = ell_minus + 2.0 * (information + noise)
                    minus_posterior = ell_minus + 2.0 * (-information + noise)
                    plus_value = np.interp(
                        plus_posterior,
                        ell_grid,
                        values[next_t],
                        left=values[next_t][0],
                        right=values[next_t][-1],
                    )
                    minus_value = np.interp(
                        minus_posterior,
                        ell_grid,
                        values[next_t],
                        left=values[next_t][0],
                        right=values[next_t][-1],
                    )
                    continuation += weight * (p_plus * plus_value + (1.0 - p_plus) * minus_value)
                q_matrix[ACTION_INDEX["SENSE"]] = 0.20 * k / 30.0 + 0.02 + continuation
            chosen = np.full(ell_grid.size, ACTION_INDEX["COMMIT_MINUS"], dtype=np.int8)
            best = np.full(ell_grid.size, np.inf, dtype=np.float64)
            for action_name in TIE_PRIORITY:
                index = ACTION_INDEX[action_name]
                candidate = q_matrix[index]
                replace = candidate < best - 1e-12
                chosen[replace] = index
                best[replace] = candidate[replace]
            values[t] = best
            action_values[t] = q_matrix
        return cls(grid, n, k, regime, ell_grid, values, action_values)

    def q_values(self, t: int, ell: float) -> np.ndarray:
        if t not in self.action_values:
            raise ValueError(f"tick {t} is not on the k={self.k} lattice")
        matrix = self.action_values[t]
        return np.asarray(
            [np.interp(ell, self.ell_grid, row, left=row[0], right=row[-1]) for row in matrix],
            dtype=np.float64,
        )

    def action(self, t: int, ell: float) -> int:
        values = self.q_values(t, ell)
        best_value = np.inf
        best_action = ACTION_INDEX["COMMIT_MINUS"]
        for action_name in TIE_PRIORITY:
            index = ACTION_INDEX[action_name]
            if values[index] < best_value - 1e-12:
                best_value = values[index]
                best_action = index
        return best_action

    def value(self, t: int, ell: float) -> float:
        row = self.values[t]
        return float(np.interp(ell, self.ell_grid, row, left=row[0], right=row[-1]))


class NumericalReference:
    """Lazily materialized frozen surfaces shared across all seed blocks."""

    def __init__(self, grid: ReferenceGrid, resource_check=None) -> None:
        self.grid = grid
        self.resource_check = resource_check
        self._surfaces: dict[tuple[int, int, str], ReferenceSurface] = {}

    def surface(self, n: int, k: int, regime: str) -> ReferenceSurface:
        key = (n, k, regime)
        if key not in self._surfaces:
            if self.resource_check is not None:
                self.resource_check()
            self._surfaces[key] = ReferenceSurface.construct(self.grid, n, k, regime)
            if self.resource_check is not None:
                self.resource_check()
        return self._surfaces[key]

    def action(self, n: int, k: int, regime: str, t: int, ell: float) -> int:
        return self.surface(n, k, regime).action(t, ell)

    def value(self, n: int, k: int, regime: str, t: int, ell: float) -> float:
        return self.surface(n, k, regime).value(t, ell)


def compare_references(fine: NumericalReference, coarse: NumericalReference) -> dict:
    max_action_value_error = 0.0
    minimizer_mismatches = 0
    checked_states = 0
    for n in (2, 5, 8):
        for k in (1, 3, 5):
            for regime in ("DUP", "CORR", "IND"):
                fine_surface = fine.surface(n, k, regime)
                coarse_surface = coarse.surface(n, k, regime)
                for t, coarse_matrix in coarse_surface.action_values.items():
                    for action_index in range(4):
                        coarse_row = coarse_matrix[action_index]
                        finite = np.isfinite(coarse_row)
                        if not np.any(finite):
                            continue
                        fine_values = np.interp(
                            coarse_surface.ell_grid[finite],
                            fine_surface.ell_grid,
                            fine_surface.action_values[t][action_index],
                        )
                        max_action_value_error = max(
                            max_action_value_error,
                            float(np.max(np.abs(fine_values - coarse_row[finite]))),
                        )
                    for position, ell in enumerate(coarse_surface.ell_grid):
                        coarse_values = coarse_matrix[:, position]
                        finite_values = coarse_values[np.isfinite(coarse_values)]
                        ordered = np.sort(finite_values)
                        gap = ordered[1] - ordered[0] if ordered.size > 1 else np.inf
                        if gap > 1e-12:
                            coarse_action = coarse_surface.action(t, float(ell))
                            fine_action = fine_surface.action(t, float(ell))
                            minimizer_mismatches += int(coarse_action != fine_action)
                        checked_states += 1
    return {
        "max_action_value_error": max_action_value_error,
        "minimizer_mismatches": minimizer_mismatches,
        "checked_states": checked_states,
        "passed": max_action_value_error <= 1e-4 and minimizer_mismatches == 0,
    }


def reference_gap(reference: NumericalReference) -> float:
    return (reference.value(5, 3, "DUP", 0, 0.0) - reference.value(5, 3, "IND", 0, 0.0)) / 1.8


def eligible_activity_states(fine: NumericalReference) -> list[tuple[int, int, float]]:
    eligible: list[tuple[int, int, float]] = []
    signed_ell = tuple(sign * magnitude for magnitude in (0.25, 0.75, 1.25, 1.75) for sign in (-1.0, 1.0))
    for t in (5, 10, 15, 20):
        for k in (1, 3, 5):
            for ell in signed_ell:
                actions = {
                    fine.action(5, k, regime, t, ell)
                    for regime in ("DUP", "CORR", "IND")
                }
                if len(actions) > 1:
                    eligible.append((t, k, ell))
    return eligible
