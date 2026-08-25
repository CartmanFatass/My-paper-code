"""Exact paired-seed studentized max-T families; no scientific interpretation."""

from __future__ import annotations

from math import floor, sqrt

import numpy as np

from .config import BOOTSTRAP_DRAWS, INFERENCE_SEED, Phase, STREAMS
from .rng import uniform


def bootstrap_indices(resource_check=None) -> np.ndarray:
    result = np.empty((BOOTSTRAP_DRAWS, 32), dtype=np.int8)
    for resample in range(BOOTSTRAP_DRAWS):
        if resource_check is not None and resample % 128 == 0:
            resource_check()
        for slot in range(32):
            result[resample, slot] = floor(
                32 * uniform(INFERENCE_SEED, Phase.INFERENCE, STREAMS["INFERENCE_BOOTSTRAP"], resample, slot)
            )
    return result


def max_t_family(contrasts: dict[str, np.ndarray], indices: np.ndarray) -> dict:
    records: dict[str, dict] = {}
    active: list[tuple[str, np.ndarray, float, float]] = []
    for name, values in contrasts.items():
        values = np.asarray(values, dtype=np.float64)
        mean = float(np.mean(values, dtype=np.float64))
        sd = float(np.sqrt(np.sum((values - mean) ** 2, dtype=np.float64) / 31.0))
        se = sd / sqrt(32.0)
        if sd == 0.0:
            records[name] = {"mean": mean, "status": "INFERENCE_UNRESOLVED_ZERO_ORIGINAL_VARIANCE", "interval": None}
        else:
            active.append((name, values, mean, se))
    maximum = np.zeros(BOOTSTRAP_DRAWS, dtype=np.float64)
    for name, values, mean, original_se in active:
        centered = values - mean
        sampled = centered[indices]
        sampled_means = np.mean(sampled, axis=1, dtype=np.float64)
        sampled_sd = np.sqrt(np.sum((sampled - sampled_means[:, None]) ** 2, axis=1, dtype=np.float64) / 31.0)
        sampled_se = sampled_sd / sqrt(32.0)
        statistic = np.full(BOOTSTRAP_DRAWS, np.inf, dtype=np.float64)
        nonzero = sampled_se != 0.0
        statistic[nonzero] = np.abs(sampled_means[nonzero] / sampled_se[nonzero])
        maximum = np.maximum(maximum, statistic)
    critical = float(np.sort(maximum)[94_999]) if active else None
    for name, values, mean, original_se in active:
        if critical is None or not np.isfinite(critical):
            records[name] = {
                "mean": mean,
                "sample_sd_denominator": 31,
                "se": original_se,
                "status": "INFERENCE_UNRESOLVED_NONFINITE_CRITICAL",
                "critical": None,
                "interval": None,
            }
        else:
            records[name] = {
                "mean": mean,
                "sample_sd_denominator": 31,
                "se": original_se,
                "critical": critical,
                "interval": [mean - critical * original_se, mean + critical * original_se],
            }
    return {"draws": BOOTSTRAP_DRAWS, "nearest_rank_draw_one_indexed": 95_000, "contrasts": records}


def _axis_cell_keys(axis: str, regime: str | None = None) -> list[str]:
    if axis == "heldout_N":
        pairs = [(8, 1), (8, 3)]
    elif axis == "heldout_k":
        pairs = [(2, 5), (5, 5)]
    elif axis == "corner":
        pairs = [(8, 5)]
    else:
        raise ValueError(axis)
    regimes = (regime,) if regime else ("DUP", "CORR", "IND")
    return [f"N={n}|k={k}|rho={rho}" for n, k in pairs for rho in regimes]


def _arm_axis_mean(seed_table: dict, arm: str, axis: str, regime: str | None = None) -> float:
    keys = _axis_cell_keys(axis, regime)
    return float(np.mean([seed_table[key][arm]["loss_norm"] for key in keys], dtype=np.float64))


def inference_families(seed_tables: list[dict], resource_check=None) -> dict:
    indices = bootstrap_indices(resource_check)
    primary: dict[str, np.ndarray] = {}
    for comparator in ("RI-STRONG-v2", "INFO-FLEX", "ORIGIN-COUNT"):
        for axis in ("heldout_N", "heldout_k"):
            primary[f"CCIC-minus-{comparator}|{axis}"] = np.asarray(
                [_arm_axis_mean(table, "CCIC", axis) - _arm_axis_mean(table, comparator, axis) for table in seed_tables]
            )
    corner = {
        f"CCIC-minus-{comparator}|corner": np.asarray(
            [_arm_axis_mean(table, "CCIC", "corner") - _arm_axis_mean(table, comparator, "corner") for table in seed_tables]
        )
        for comparator in ("RI-STRONG-v2", "INFO-FLEX", "ORIGIN-COUNT")
    }
    specificity: dict[str, np.ndarray] = {}
    for comparator in ("RI-STRONG-v2", "INFO-FLEX", "ORIGIN-COUNT"):
        for axis in ("heldout_N", "heldout_k"):
            regime_differences = {}
            for regime in ("DUP", "CORR", "IND"):
                regime_differences[regime] = np.asarray(
                    [
                        _arm_axis_mean(table, "CCIC", axis, regime)
                        - _arm_axis_mean(table, comparator, axis, regime)
                        for table in seed_tables
                    ]
                )
            specificity[f"{comparator}|{axis}|CORR-minus-DUP"] = regime_differences["CORR"] - regime_differences["DUP"]
            specificity[f"{comparator}|{axis}|IND-minus-CORR"] = regime_differences["IND"] - regime_differences["CORR"]
    ess = {
        f"CCIC-minus-ESS-SCALAR|{axis}": np.asarray(
            [_arm_axis_mean(table, "CCIC", axis) - _arm_axis_mean(table, "ESS-SCALAR", axis) for table in seed_tables]
        )
        for axis in ("heldout_N", "heldout_k")
    }
    diagnostics = {
        f"{arm}-minus-CCIC|{axis}": np.asarray(
            [_arm_axis_mean(table, arm, axis) - _arm_axis_mean(table, "CCIC", axis) for table in seed_tables]
        )
        for arm in ("J-SHUFFLE", "J-CLAMP")
        for axis in ("heldout_N", "heldout_k")
    }
    return {
        "primary_six": max_t_family(primary, indices),
        "corner_three": max_t_family(corner, indices),
        "covariance_specificity_twelve": max_t_family(specificity, indices),
        "ess_reduction_two": max_t_family(ess, indices),
        "clock_diagnostics_four": max_t_family(diagnostics, indices),
    }
