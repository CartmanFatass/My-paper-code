"""Finite 3x3 controller-composition algebra and paired-world uncertainty."""
from __future__ import annotations

import numpy as np

PAIRS = ((0, 1), (0, 2), (1, 2))
MIXED = tuple((i, j) for i in range(3) for j in range(3) if i != j)


def contrasts(matrix: np.ndarray) -> dict:
    """Apply every contrast to one 3x3 panel (or a leading batch of panels)."""
    v = np.asarray(matrix, dtype=np.float64)
    if v.shape[-2:] != (3, 3) or not np.isfinite(v).all():
        raise ValueError("contrasts require finite [...,3,3] input")
    diag = np.diagonal(v, axis1=-2, axis2=-1)
    residual = v - v.mean(axis=-1, keepdims=True) - v.mean(axis=-2, keepdims=True) + v.mean(axis=(-2, -1), keepdims=True)
    pair = np.stack([(v[..., i, i] + v[..., j, j] - v[..., i, j] - v[..., j, i]) / 2 for i, j in PAIRS], axis=-1)
    differences = np.stack([np.stack((v[..., i, j] - v[..., i, i], v[..., i, j] - v[..., j, j]), axis=-1) for i, j in MIXED], axis=-2)
    return {
        "V": v,
        "C": pair,
        "D": diag.mean(axis=-1) - np.stack([v[..., i, j] for i, j in MIXED], axis=-1).mean(axis=-1),
        "R": residual,
        "R_symmetric": (residual + np.swapaxes(residual, -1, -2)) / 2,
        "R_antisymmetric": (residual - np.swapaxes(residual, -1, -2)) / 2,
        "kappa": (v[..., 0, 1] + v[..., 1, 2] + v[..., 2, 0] - v[..., 1, 0] - v[..., 2, 1] - v[..., 0, 2]) / 6,
        "mixed_minus_source_diagonals": differences,
    }


def reduce_panel(j: np.ndarray, service: np.ndarray, *, draws: int = 10_000, seed: int = 92_525_999) -> dict:
    """World axis first; one bootstrap index resamples the whole J/service block."""
    j, service = np.asarray(j, dtype=np.float64), np.asarray(service, dtype=np.float64)
    if j.shape != service.shape or j.ndim != 3 or j.shape[1:] != (3, 3) or j.shape[0] < 2:
        raise ValueError("J and service need matching [world,3,3] panels")
    if draws <= 0:
        raise ValueError("bootstrap draws must be positive")
    rng = np.random.default_rng(seed)
    indices = rng.integers(j.shape[0], size=(draws, j.shape[0]))
    result = {"world_count": int(j.shape[0]), "bootstrap_draws": int(draws), "bootstrap_seed": int(seed),
              "interval_interpretation": "pointwise conditional on fixed sources/partition and iid exchangeable world generator; no training-population uncertainty",
              "pairs": [[i + 1, k + 1] for i, k in PAIRS],
              "mixed_cells": [[i + 1, k + 1] for i, k in MIXED]}
    for key, block in (("J", j), ("S_served_users_per_step", service)):
        worlds = contrasts(block)
        finite = contrasts(block.mean(axis=0))
        draws_values = contrasts(block[indices].mean(axis=1))
        result[key] = {
            "finite_panel": {name: np.asarray(value).tolist() for name, value in finite.items()},
            "per_world": {name: np.asarray(value).tolist() for name, value in worlds.items()},
            "pointwise_95_percentiles": {name: np.percentile(value, [2.5, 97.5], axis=0).tolist()
                                         for name, value in draws_values.items()},
        }
    return result
