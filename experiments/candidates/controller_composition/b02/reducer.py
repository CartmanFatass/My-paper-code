"""All fixed B02 world-paired native readings."""
from __future__ import annotations

import numpy as np

from experiments.candidates.controller_composition.b02.bindings import BOOTSTRAP_DRAWS, BOOTSTRAP_SEED

ORDER = (("I", 1), ("I", 2), ("I", 3),
         ("F1", 1), ("F1", 2), ("F1", 3),
         ("F2", 1), ("F2", 2), ("F2", 3),
         ("M", 1), ("M", 2), ("M", 3), ("OLD3", 3))


def _contrasts(v: np.ndarray) -> dict[str, np.ndarray]:
    """Last axis is the thirteen ordered cells; leading axes are world/draw."""
    if v.shape[-1] != 13:
        raise ValueError("B02 requires thirteen fixed cells")
    x = {cell: v[..., index] for index, cell in enumerate(ORDER)}
    delta = {partner: x["M", partner] - x["F2", partner] for partner in (1, 2, 3)}
    result = {f"V_{learner}_{partner}": value for (learner, partner), value in x.items()}
    result.update({f"M_minus_F2_partner{p}": delta[p] for p in (1, 2, 3)})
    result.update({f"M_minus_F1_partner{p}": x["M", p] - x["F1", p] for p in (1, 2, 3)})
    result.update({f"F1_minus_F2_partner{p}": x["F1", p] - x["F2", p] for p in (1, 2, 3)})
    result.update({f"{a}_minus_initial_partner{p}": x[a, p] - x["I", p]
                   for a in ("F1", "F2", "M") for p in (1, 2, 3)})
    result.update({f"{a}_minus_old3_reuse_partner3": x[a, 3] - x["OLD3", 3]
                   for a in ("F1", "F2", "M")})
    result["fixed_advantage_F1_on_partner1"] = x["F1", 1] - x["F2", 1]
    result["fixed_advantage_F2_on_partner2"] = x["F2", 2] - x["F1", 2]
    result["T_fixed_response_specialization"] = (
        result["fixed_advantage_F1_on_partner1"] + result["fixed_advantage_F2_on_partner2"]
    ) / 2
    result["H_partner3_relative_gain"] = delta[3] - (delta[1] + delta[2]) / 2
    return result


def reduce_panel(j: np.ndarray, service: np.ndarray, *, draws: int = BOOTSTRAP_DRAWS,
                 seed: int = BOOTSTRAP_SEED) -> dict:
    j, service = np.asarray(j, dtype=np.float64), np.asarray(service, dtype=np.float64)
    if j.shape != service.shape or j.ndim != 2 or j.shape[1] != 13 or j.shape[0] < 2:
        raise ValueError("B02 requires matching [world,13] J and service panels")
    if not np.isfinite(j).all() or not np.isfinite(service).all() or draws < 1:
        raise ValueError("B02 reducer requires finite panels and positive draw count")
    indices = np.random.default_rng(seed).integers(j.shape[0], size=(draws, j.shape[0]))
    result = {"cell_order": [[a, p] for a, p in ORDER], "world_count": int(j.shape[0]),
              "bootstrap_draws": int(draws), "bootstrap_seed": int(seed),
              "interval_interpretation": "pointwise conditional on fixed learned weights, library, partition and selection history under exchangeable worlds; no training-population uncertainty"}
    for name, matrix in (("J", j), ("S_served_users_per_step", service)):
        world = _contrasts(matrix)
        finite = _contrasts(matrix.mean(axis=0))
        sampled = _contrasts(matrix[indices].mean(axis=1))
        result[name] = {
            "finite_panel": {key: np.asarray(value).tolist() for key, value in finite.items()},
            "per_world": {key: np.asarray(value).tolist() for key, value in world.items()},
            "pointwise_95_percentiles": {key: np.percentile(value, [2.5, 97.5]).tolist()
                                         for key, value in sampled.items()},
        }
    return result
