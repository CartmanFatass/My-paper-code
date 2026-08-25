"""Frozen MGTAP two-role/four-task environment primitives."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import DISPLAYED_COORDINATES, TRUE_UTILITY, demand


@dataclass(frozen=True)
class PublicState:
    n: int
    pair: tuple[int, int]
    load: str
    epoch: int
    binding: str

    @property
    def demand(self) -> np.ndarray:
        return np.asarray(demand(self.n, self.pair, self.load, self.epoch), dtype=np.int16)

    @property
    def feature(self) -> np.ndarray:
        return np.asarray((1.0, *(self.demand.astype(np.float64) / self.n), self.epoch - 1.0), dtype=np.float64)

    @property
    def displayed_coordinates(self) -> np.ndarray:
        return np.asarray(DISPLAYED_COORDINATES[self.binding], dtype=np.float64)


def canonical_roles(n: int) -> np.ndarray:
    return np.concatenate((np.zeros(n // 2, dtype=np.int8), np.ones(n // 2, dtype=np.int8)))


def canonicalize_task_values(presented_values: np.ndarray, presented_tokens: np.ndarray) -> np.ndarray:
    """Scatter presented task columns back to fixed semantic-token order."""
    result = np.empty_like(presented_values)
    np.put_along_axis(result, presented_tokens, presented_values, axis=1)
    return result


def reward(roles: np.ndarray, actions: np.ndarray, residual: np.ndarray) -> np.ndarray:
    """Return batch rewards. Actions use 0..3 tasks and 4 for IDLE."""
    utility = np.asarray(TRUE_UTILITY, dtype=np.float64)
    batch = actions.shape[0]
    result = np.zeros(batch, dtype=np.float64)
    # Canonical role/task aggregation makes semantic reward independent of the
    # presented agent-row order, including the final floating-point summation.
    for role in (0, 1):
        for task in range(4):
            counts = ((roles == role) & (actions == task)).sum(axis=1)
            result += counts * utility[role, task]
    result -= 0.05 * (actions == 4).sum(axis=1)
    result -= 0.05 * residual.sum(axis=1)
    return result


def coupling_from_actions(actions: np.ndarray, demand_values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    batch, n = actions.shape
    x = np.zeros((batch, n, 4), dtype=np.int8)
    idle = (actions == 4).astype(np.int8)
    for task in range(4):
        x[:, :, task] = actions == task
    assigned = x.sum(axis=1, dtype=np.int16)
    unmet = demand_values.astype(np.int16) - assigned
    return x, idle, unmet


def feasibility_residuals(x: np.ndarray, idle: np.ndarray, unmet: np.ndarray, demand_values: np.ndarray) -> np.ndarray:
    row = x.sum(axis=2, dtype=np.int16) + idle - 1
    col = x.sum(axis=1, dtype=np.int16) + unmet - demand_values
    return np.concatenate((row, col), axis=1)


def alignment(actions: np.ndarray, roles: np.ndarray, pair: tuple[int, int], n: int) -> np.ndarray:
    if pair in ((0, 3), (3, 0)):
        selected = ((roles == 0) & (actions == 0)) | ((roles == 1) & (actions == 3))
    elif pair in ((1, 2), (2, 1)):
        selected = ((roles == 0) & (actions == 1)) | ((roles == 1) & (actions == 2))
    else:
        return np.full(actions.shape[0], np.nan, dtype=np.float64)
    return selected.sum(axis=1) / float(n)
