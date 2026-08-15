"""Prespecified seed-level analysis for VNFC-B1."""

from __future__ import annotations

import math
import statistics
from typing import Mapping, Sequence

from .models import A_JOINT, A_MASS, B_REBIND, G_MEAN


T95_DF7 = 2.3646242515927844
T90_DF7 = 1.894578605061305


def interval(values: Sequence[float], critical: float) -> dict[str, float | list[float]]:
    if len(values) != 8:
        raise ValueError("VNFC-B1 intervals require exactly eight seed values")
    center = statistics.fmean(values)
    standard_deviation = statistics.stdev(values)
    margin = critical * standard_deviation / math.sqrt(8)
    return {
        "seed_values": list(values),
        "mean": center,
        "standard_deviation": standard_deviation,
        "lower": center - margin,
        "upper": center + margin,
    }


def contrast(
    seed_rows: Sequence[Mapping[str, object]], left: str, right: str, metric: str,
) -> dict[str, object]:
    values = [
        float(row["arms"][left][metric]) - float(row["arms"][right][metric])  # type: ignore[index]
        for row in seed_rows
    ]
    return {
        "left": left,
        "right": right,
        "metric": metric,
        "student_t_95": interval(values, T95_DF7),
        "student_t_90": interval(values, T90_DF7),
        "practically_equivalent_90_inside_plus_minus_0_03": (
            float(interval(values, T90_DF7)["lower"]) >= -0.03
            and float(interval(values, T90_DF7)["upper"]) <= 0.03
        ),
    }


def analyze(seed_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if len(seed_rows) != 8:
        raise ValueError("VNFC-B1 analysis requires eight complete seed blocks")
    contrasts: dict[str, object] = {}
    for left, right in (
        (A_MASS, G_MEAN), (A_JOINT, G_MEAN), (B_REBIND, G_MEAN),
        (A_JOINT, A_MASS), (B_REBIND, A_JOINT),
    ):
        for metric in (
            "P", "H", "Ogap", "X", "capacity_normalized_N6_minus_N4",
        ):
            key = f"{left}_minus_{right}:{metric}"
            contrasts[key] = contrast(seed_rows, left, right, metric)

    def lower(key: str) -> float:
        return float(contrasts[key]["student_t_95"]["lower"])  # type: ignore[index]

    def mean(key: str) -> float:
        return float(contrasts[key]["student_t_95"]["mean"])  # type: ignore[index]

    criteria: dict[str, object] = {}
    # A-JOINT is a causal decoder diagnostic, never a project-facing candidate.
    for candidate in (A_MASS, B_REBIND):
        h_key = f"{candidate}_minus_{G_MEAN}:H"
        p_key = f"{candidate}_minus_{G_MEAN}:P"
        criteria[candidate] = {
            "robustness_materiality_and_positive_lower_bound": mean(h_key) >= 0.05 and lower(h_key) > 0.0,
            "performance_materiality_and_positive_lower_bound": mean(p_key) >= 0.05 and lower(p_key) > 0.0,
            "either_project_facing_support_condition": (
                mean(h_key) >= 0.05 and lower(h_key) > 0.0
            ) or (
                mean(p_key) >= 0.05 and lower(p_key) > 0.0
            ),
        }
    b_h_key = f"{B_REBIND}_minus_{A_JOINT}:H"
    b_p_key = f"{B_REBIND}_minus_{A_JOINT}:P"
    criteria["additional_named_conditions"] = {
        "true_expansion_capture_by_candidate": {
            candidate: (
                mean(f"{candidate}_minus_{G_MEAN}:X") >= 0.03
                and lower(f"{candidate}_minus_{G_MEAN}:X") > 0.0
            )
            for candidate in (A_MASS, B_REBIND)
        },
        "B_specific_persistence_on_H_or_P": (
            mean(b_h_key) >= 0.03 and lower(b_h_key) > 0.0
        ) or (
            mean(b_p_key) >= 0.03 and lower(b_p_key) > 0.0
        ),
    }
    return {"contrasts": contrasts, "prespecified_support_conditions": criteria}
