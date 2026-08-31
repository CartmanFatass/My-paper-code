"""Prospective all-horizon calibration fitting and fixed-eight admission."""

from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence

import numpy as np

from .contracts import PredictorExample
from .host_bridge import ForecastProvider
from .packets import CalibrationTable, whitened_residual


CALIBRATION_HORIZONS = (4, 8, 12, 16)
K16_COVERAGE_THRESHOLD = 13.3615661365
K16_MINIMUM_TARGETS_PER_HORIZON = 32
K16_COVERAGE_RANGE = (0.80, 0.98)
K16_MAX_PIT_ECE = 0.10
K16_MAX_CLIP_SATURATION = 0.05
DIAGNOSTIC_REGIMES = ("K16", "K4_TO_16", "K16_TO_4")


def _forecast_residual(
    example: PredictorExample, forecast: ForecastProvider,
) -> np.ndarray:
    mean, factor = forecast(
        example.origin_history, example.option, example.k, example.target_age,
    )
    return whitened_residual(example.target, mean, factor)


def fit_calibration_from_examples(
    examples: Sequence[PredictorExample], forecast: ForecastProvider,
) -> tuple[CalibrationTable, dict[str, object]]:
    """Fit the midpoint-CDF support from every supplied eligible example."""

    ordered = tuple(sorted(examples, key=lambda item: item.canonical_key))
    if not ordered:
        raise ValueError("cannot fit calibration from an empty all-horizon population")
    if len({item.canonical_key for item in ordered}) != len(ordered):
        raise ValueError("calibration examples must have unique canonical keys")
    residuals = np.stack([_forecast_residual(item, forecast) for item in ordered])
    table = CalibrationTable(np.sort(residuals.T, axis=1))
    counts = Counter(item.target_age for item in ordered)
    return table, {
        "example_count": len(ordered),
        "episode_indices": sorted({int(item.episode_index) for item in ordered}),
        "horizon_counts": {str(horizon): int(counts[horizon]) for horizon in CALIBRATION_HORIZONS},
        "pooled_k_values": sorted({int(item.k) for item in ordered}),
        "table_record": table.canonical_record,
    }


def _diagnose_examples(
    table: CalibrationTable,
    examples: Sequence[PredictorExample],
    forecast: ForecastProvider,
) -> dict[str, object]:
    by_horizon: dict[str, object] = {}
    for horizon in CALIBRATION_HORIZONS:
        selected = tuple(item for item in examples if item.target_age == horizon)
        if not selected:
            by_horizon[str(horizon)] = {
                "target_count": 0,
                "coverage": None,
                "pit_frequencies": None,
                "pit_ece_by_coordinate": None,
                "clip_saturation": None,
            }
            continue
        residuals = np.stack([_forecast_residual(item, forecast) for item in selected])
        q = np.sum(np.square(residuals, dtype=np.float64), axis=1)
        u = table.cdf(residuals)
        bins = np.minimum(9, np.floor(10.0 * u).astype(np.int64))
        frequencies = np.empty((8, 10), dtype=np.float64)
        for coordinate in range(8):
            frequencies[coordinate] = np.bincount(
                bins[:, coordinate], minlength=10,
            ).astype(np.float64) / float(len(selected))
        ece = 0.5 * np.sum(np.abs(frequencies - 0.1), axis=1)
        by_horizon[str(horizon)] = {
            "target_count": len(selected),
            "coverage": float(np.mean(q <= K16_COVERAGE_THRESHOLD)),
            "pit_frequencies": frequencies.tolist(),
            "pit_ece_by_coordinate": ece.tolist(),
            "clip_saturation": float(np.mean(np.abs(residuals) >= 6.0)),
        }
    return by_horizon


def slot_calibration_diagnostics(
    table: CalibrationTable,
    examples_by_regime: Mapping[str, Sequence[PredictorExample]],
    forecast: ForecastProvider,
    *,
    replicate: int,
) -> dict[str, object]:
    """Compute one slot's untouched K16 gate and separate switch diagnostics."""

    unexpected = set(examples_by_regime) - set(DIAGNOSTIC_REGIMES)
    if unexpected:
        raise ValueError(f"unknown calibration diagnostic regimes: {sorted(unexpected)}")
    return {
        "replicate": int(replicate),
        "regimes": {
            regime: _diagnose_examples(table, tuple(examples_by_regime.get(regime, ())), forecast)
            for regime in DIAGNOSTIC_REGIMES
        },
    }


def _aggregate_regime(
    slot_reports: Sequence[Mapping[str, object]], regime: str,
) -> dict[str, object]:
    horizons: dict[str, object] = {}
    for horizon in CALIBRATION_HORIZONS:
        key = str(horizon)
        cells = [report["regimes"][regime][key] for report in slot_reports]  # type: ignore[index]
        counts = [int(cell["target_count"]) for cell in cells]  # type: ignore[index]
        if any(cell["coverage"] is None for cell in cells):  # type: ignore[index]
            horizons[key] = {
                "slot_target_counts": counts,
                "slot_coverages": None,
                "replicate_balanced_coverage": None,
                "replicate_balanced_pit_ece_by_coordinate": None,
                "max_replicate_balanced_pit_ece": None,
                "slot_clip_saturation": None,
                "replicate_balanced_clip_saturation": None,
            }
            continue
        coverages = [float(cell["coverage"]) for cell in cells]  # type: ignore[index]
        frequencies = np.asarray(
            [cell["pit_frequencies"] for cell in cells], dtype=np.float64,  # type: ignore[index]
        )
        mean_frequency = np.mean(frequencies, axis=0)
        ece = 0.5 * np.sum(np.abs(mean_frequency - 0.1), axis=1)
        saturation = [float(cell["clip_saturation"]) for cell in cells]  # type: ignore[index]
        horizons[key] = {
            "slot_target_counts": counts,
            "slot_coverages": coverages,
            "replicate_balanced_coverage": float(np.mean(coverages)),
            "replicate_balanced_pit_ece_by_coordinate": ece.tolist(),
            "max_replicate_balanced_pit_ece": float(np.max(ece)),
            "slot_clip_saturation": saturation,
            "replicate_balanced_clip_saturation": float(np.mean(saturation)),
        }
    return horizons


def assess_calibration(
    slot_reports: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Apply only the fixed-K16 gate; keep switch regimes descriptive."""

    ordered = tuple(slot_reports)
    issues: list[str] = []
    if [report.get("replicate") for report in ordered] != list(range(8)):
        issues.append("calibration diagnostics require exact slot order 0..7")
    if len(ordered) != 8:
        return {
            "passed": False,
            "issues": issues or ["calibration diagnostics require exactly eight slots"],
            "k16": {},
            "switch_regimes": {},
        }
    k16 = _aggregate_regime(ordered, "K16")
    for horizon in CALIBRATION_HORIZONS:
        key = str(horizon)
        row = k16[key]  # type: ignore[index]
        counts = row["slot_target_counts"]  # type: ignore[index]
        if any(int(count) < K16_MINIMUM_TARGETS_PER_HORIZON for count in counts):
            issues.append(f"fixed K16 horizon {horizon} has fewer than 32 targets in a slot")
        coverage = row["replicate_balanced_coverage"]  # type: ignore[index]
        if coverage is None or not K16_COVERAGE_RANGE[0] <= float(coverage) <= K16_COVERAGE_RANGE[1]:
            issues.append(f"fixed K16 horizon {horizon} coverage is outside [0.80,0.98]")
        pit_ece = row["max_replicate_balanced_pit_ece"]  # type: ignore[index]
        if pit_ece is None or float(pit_ece) > K16_MAX_PIT_ECE:
            issues.append(f"fixed K16 horizon {horizon} PIT ECE exceeds 0.10")
        saturation = row["replicate_balanced_clip_saturation"]  # type: ignore[index]
        if saturation is None or float(saturation) >= K16_MAX_CLIP_SATURATION:
            issues.append(f"fixed K16 horizon {horizon} clip saturation is not below 0.05")
    return {
        "passed": not issues,
        "issues": issues,
        "k16": k16,
        "switch_regimes": {
            regime: _aggregate_regime(ordered, regime)
            for regime in ("K4_TO_16", "K16_TO_4")
        },
        "switch_regimes_are_admission_gates": False,
    }


__all__ = [
    "assess_calibration",
    "fit_calibration_from_examples",
    "slot_calibration_diagnostics",
]
