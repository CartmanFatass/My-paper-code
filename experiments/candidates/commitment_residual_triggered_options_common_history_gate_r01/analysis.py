"""Replicate-unit simultaneous contrasts and fail-closed interpretation routing."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Mapping, Sequence

import numpy as np

from .config import DELTA
from .contracts import Budget, Representation
from .evaluation import EvaluationSummary


CONTRASTS = (
    (Representation.RAW, Representation.TRUE_RESIDUAL, "RAW_MINUS_TRUE"),
    (Representation.CALIBRATED_DERANGEMENT, Representation.TRUE_RESIDUAL, "DERANGED_MINUS_TRUE"),
    (Representation.RAW, Representation.CALIBRATED_DERANGEMENT, "RAW_MINUS_DERANGED"),
)

# IMPLEMENTATION_THRESHOLD.md freezes delta but no family alpha or interval
# construction.  This object therefore cannot make an inferential branch.
INTERVAL_POLICY_FROZEN = False


@dataclass(frozen=True)
class AnalysisPolicy:
    """Numeric decisions omitted by the threshold must be supplied prospectively."""

    minimum_retained_rows_per_cell: int | None = None
    raw_long_max_k8_regret: float | None = None
    interval_method: str | None = None
    family_alpha: float | None = None

    @property
    def complete(self) -> bool:
        return (
            INTERVAL_POLICY_FROZEN
            and
            self.minimum_retained_rows_per_cell is not None
            and self.minimum_retained_rows_per_cell >= 2
            and self.raw_long_max_k8_regret is not None
            and self.raw_long_max_k8_regret >= 0.0
            and self.interval_method in {"bonferroni_t"}
            and self.family_alpha is not None
            and 0.0 < self.family_alpha < 1.0
        )


@dataclass(frozen=True)
class SimultaneousInterval:
    contrast: str
    budget: Budget
    estimate: float
    lower: float
    upper: float
    replicate_count: int
    method: str
    family_alpha: float


def simultaneous_intervals(
    replicate_summaries: Sequence[Mapping[tuple[Representation, Budget], EvaluationSummary]],
    *, method: str, family_alpha: float,
) -> tuple[SimultaneousInterval, ...]:
    if method != "bonferroni_t":
        raise ValueError("no simultaneous interval method was prospectively declared")
    if len(replicate_summaries) < 2:
        raise ValueError("replicate-unit intervals require at least two replicates")
    try:
        from scipy.stats import t as student_t
    except ImportError as error:  # pragma: no cover - environment admission failure
        raise RuntimeError("bonferroni_t analysis requires scipy") from error
    family_size = len(CONTRASTS) * len(Budget)
    if not 0.0 < family_alpha < 1.0:
        raise ValueError("family alpha must lie strictly between zero and one")
    critical = float(student_t.ppf(
        1.0 - family_alpha / (2.0 * family_size), len(replicate_summaries) - 1
    ))
    intervals: list[SimultaneousInterval] = []
    for left, right, label in CONTRASTS:
        for budget in Budget:
            differences = np.asarray([
                summary[(left, budget)].target_equal_weight_regret
                - summary[(right, budget)].target_equal_weight_regret
                for summary in replicate_summaries
            ], dtype=np.float64)
            estimate = float(np.mean(differences))
            half_width = critical * float(np.std(differences, ddof=1)) / sqrt(len(differences))
            intervals.append(SimultaneousInterval(
                contrast=label, budget=budget, estimate=estimate,
                lower=estimate - half_width, upper=estimate + half_width,
                replicate_count=len(differences), method=method, family_alpha=family_alpha,
            ))
    return tuple(intervals)


def _first_match(intervals: tuple[SimultaneousInterval, ...]) -> str:
    by_key = {(item.contrast, item.budget): item for item in intervals}
    raw_short = by_key[("RAW_MINUS_TRUE", Budget.SHORT)]
    raw_long = by_key[("RAW_MINUS_TRUE", Budget.LONG)]
    deranged_short = by_key[("DERANGED_MINUS_TRUE", Budget.SHORT)]
    deranged_long = by_key[("DERANGED_MINUS_TRUE", Budget.LONG)]
    raw_deranged_short = by_key[("RAW_MINUS_DERANGED", Budget.SHORT)]
    raw_deranged_long = by_key[("RAW_MINUS_DERANGED", Budget.LONG)]
    if (
        raw_short.lower > DELTA and raw_long.lower > DELTA
        and deranged_short.lower > DELTA and deranged_long.lower > DELTA
    ):
        return "PERSISTENT_ALIGNED_BIAS"
    if raw_short.lower > DELTA and raw_long.lower >= -DELTA and raw_long.upper <= DELTA:
        return "OPTIMIZATION_EXPOSURE_ONLY"
    if (
        raw_short.lower > DELTA and raw_long.lower > DELTA
        and raw_deranged_short.lower > DELTA and raw_deranged_long.lower > DELTA
        and deranged_short.lower >= -DELTA and deranged_short.upper <= DELTA
        and deranged_long.lower >= -DELTA and deranged_long.upper <= DELTA
    ):
        return "GENERIC_PREPROCESSING"
    if raw_short.upper <= DELTA and raw_long.upper <= DELTA:
        return "CLOSE_TESTED_MECHANISM"
    return "UNRESOLVED"


def analyze(
    replicate_summaries: Sequence[Mapping[tuple[Representation, Budget], EvaluationSummary]],
    *,
    policy: AnalysisPolicy,
    structural_failures: Sequence[str] = (),
    retained_rows_per_cell: Sequence[Mapping[object, int]] | None = None,
) -> dict[str, object]:
    """Fail closed when the source threshold omitted a numeric admission rule."""

    failures = list(structural_failures)
    if not policy.complete:
        failures.append(
            "NONIDENTIFYING_MISSING_INTERVAL_POLICY: threshold did not freeze retained-row "
            "support, RAW-LONG competence, family alpha, and interval construction"
        )
    if len(replicate_summaries) != 8:
        failures.append("exactly eight replicate inferential units are required")
    if retained_rows_per_cell is None or len(retained_rows_per_cell) != 8:
        failures.append("retained-row support counts are required for all eight replicates")
    elif policy.minimum_retained_rows_per_cell is not None and any(
        not counts or any(value < policy.minimum_retained_rows_per_cell for value in counts.values())
        for counts in retained_rows_per_cell
    ):
        failures.append("minimum retained-row support gate failed")
    if failures:
        return {
            "status": "NONIDENTIFYING", "interpretation": "UNRESOLVED",
            "failures": failures, "intervals": [],
        }
    raw_long = [
        summary[(Representation.RAW, Budget.LONG)].k8_mean_regret
        for summary in replicate_summaries
    ]
    if any(not np.isfinite(value) or value > float(policy.raw_long_max_k8_regret) for value in raw_long):
        return {
            "status": "NONIDENTIFYING", "interpretation": "UNRESOLVED",
            "failures": ["RAW-LONG in-support competence gate failed"], "intervals": [],
        }
    intervals = simultaneous_intervals(
        replicate_summaries, method=str(policy.interval_method),
        family_alpha=float(policy.family_alpha),
    )
    return {
        "status": "IDENTIFYING",
        "interpretation": _first_match(intervals),
        "failures": [],
        "intervals": [
            {
                "contrast": item.contrast, "budget": item.budget.value,
                "estimate": item.estimate, "lower": item.lower, "upper": item.upper,
                "replicate_count": item.replicate_count, "method": item.method,
                "family_alpha": item.family_alpha,
            }
            for item in intervals
        ],
    }
