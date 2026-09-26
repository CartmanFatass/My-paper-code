"""Whole-world paired reduction of the fixed nineteen-cell panel."""
from __future__ import annotations

import numpy as np

from .bindings import BOOTSTRAP_DRAWS, BOOTSTRAP_SEED, EVAL_CELLS


def _readings(values: np.ndarray) -> dict[str, np.ndarray]:
    if values.shape[-1] != len(EVAL_CELLS):
        raise ValueError("B03 requires nineteen fixed cells")
    x = {cell: values[..., i] for i, cell in enumerate(EVAL_CELLS)}
    old = x["shared", "OLD3", 3]
    result = {f"{block}_{learner}_partner{partner}": x[block, learner, partner]
              for block, learner, partner in EVAL_CELLS}
    for block in ("B1", "B2"):
        delta = {}
        for partner in (1, 2, 3):
            delta[partner] = x[block, "M", partner] - x[block, "F2", partner]
            result[f"{block}_M_minus_F2_partner{partner}"] = delta[partner]
            for arm in ("F2", "M"):
                result[f"{block}_{arm}_minus_initial_partner{partner}"] = (
                    x[block, arm, partner] - x[block, "I", partner])
        for arm in ("F2", "M"):
            result[f"{block}_{arm}_minus_old3_reuse_partner3"] = x[block, arm, 3] - old
        result[f"{block}_H_partner3_relative_gain"] = delta[3] - (delta[1] + delta[2]) / 2
    return result


def reduce_panel(j: np.ndarray, service: np.ndarray, *, draws: int = BOOTSTRAP_DRAWS,
                 seed: int = BOOTSTRAP_SEED) -> dict:
    j, service = np.asarray(j, dtype=np.float64), np.asarray(service, dtype=np.float64)
    if j.shape != service.shape or j.ndim != 2 or j.shape[1] != len(EVAL_CELLS) or j.shape[0] < 2:
        raise ValueError("B03 requires matching [world,19] J and service panels")
    if not np.isfinite(j).all() or not np.isfinite(service).all() or draws < 1:
        raise ValueError("B03 requires finite panels and positive draws")
    # One index matrix resamples each world's entire two-metric/nineteen-cell block.
    indices = np.random.default_rng(seed).integers(j.shape[0], size=(draws, j.shape[0]))
    result = {"cell_order": [list(cell) for cell in EVAL_CELLS], "world_count": int(j.shape[0]),
              "bootstrap_seed": seed, "bootstrap_draws": draws,
              "interval_interpretation": "pointwise conditional on fixed weights, source library, roles and exchangeable worlds; excludes training uncertainty"}
    for name, matrix in (("J", j), ("S_served_users_per_step", service)):
        per_world = _readings(matrix)
        finite = _readings(matrix.mean(axis=0))
        bootstrap = _readings(matrix[indices].mean(axis=1))
        result[name] = {
            "finite_panel": {key: np.asarray(value).tolist() for key, value in finite.items()},
            "per_world": {key: np.asarray(value).tolist() for key, value in per_world.items()},
            "pointwise_95_percentiles": {key: np.percentile(value, [2.5, 97.5]).tolist()
                                         for key, value in bootstrap.items()},
        }
    return result
