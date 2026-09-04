"""Fixed-eight address-census contrasts and fail-closed interpretation routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from .config import (
    DELTA,
    FIXED_CENSUS_METHOD,
    MATERIAL_STRATA,
    MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM,
    NUMERIC_TOLERANCE,
    RAW_LONG_MAX_MEAN_REGRET,
    REPLICATES,
)
from .contracts import Budget, Representation
from .evaluation import EvaluationSummary


CONTRASTS = (
    (Representation.RAW, Representation.TRUE_RESIDUAL, "RAW_MINUS_TRUE"),
    (Representation.CALIBRATED_DERANGEMENT, Representation.TRUE_RESIDUAL, "DERANGED_MINUS_TRUE"),
    (Representation.RAW, Representation.CALIBRATED_DERANGEMENT, "RAW_MINUS_DERANGED"),
)


@dataclass(frozen=True)
class AnalysisPolicy:
    """The prospective policy is typed and has no caller-selectable numeric fields."""

    replicates: tuple[int, ...] = field(default=REPLICATES, init=False)
    delta: float = field(default=DELTA, init=False)
    minimum_k8_rows_per_material_stratum: int = field(
        default=MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM, init=False
    )
    raw_long_max_mean_regret: float = field(default=RAW_LONG_MAX_MEAN_REGRET, init=False)
    numeric_tolerance: float = field(default=NUMERIC_TOLERANCE, init=False)
    method: str = field(default=FIXED_CENSUS_METHOD, init=False)


@dataclass(frozen=True)
class EffectHull:
    contrast: str
    budget: Budget
    slot_effects: tuple[float, ...]
    descriptive_mean: float
    lower: float
    upper: float
    width: float
    replicate_count: int
    method: str = FIXED_CENSUS_METHOD
    joint_coverage: float = 1.0
    family_alpha: None = None
    multiplicity: None = None

    def __post_init__(self) -> None:
        if len(self.slot_effects) != len(REPLICATES):
            raise ValueError("effect hull requires exactly eight slot effects")
        if not all(np.isfinite(value) for value in self.slot_effects):
            raise ValueError("effect hull slot effects must be finite")
        if self.lower != min(self.slot_effects) or self.upper != max(self.slot_effects):
            raise ValueError("effect hull endpoints must equal the exact slot extrema")
        if self.width != self.upper - self.lower:
            raise ValueError("effect hull width must equal upper minus lower")
        if self.replicate_count != len(REPLICATES):
            raise ValueError("effect hull replicate count must equal eight")


def fixed_eight_effect_hulls(
    replicate_summaries: Sequence[Mapping[tuple[Representation, Budget], EvaluationSummary]],
) -> tuple[EffectHull, ...]:
    """Return exact effect hulls over the frozen addresses, never confidence intervals."""

    if len(replicate_summaries) != len(REPLICATES):
        raise ValueError("fixed address census requires exactly slots 0..7")
    hulls: list[EffectHull] = []
    for left, right, label in CONTRASTS:
        for budget in Budget:
            base_values = tuple(
                value
                for summary in replicate_summaries
                for value in (
                    float(summary[(left, budget)].target_equal_weight_regret),
                    float(summary[(right, budget)].target_equal_weight_regret),
                )
            )
            if not all(np.isfinite(value) and value >= 0.0 for value in base_values):
                raise ValueError("base native regret values must all be finite and nonnegative")
            effects = tuple(
                float(summary[(left, budget)].target_equal_weight_regret)
                - float(summary[(right, budget)].target_equal_weight_regret)
                for summary in replicate_summaries
            )
            if not all(np.isfinite(value) for value in effects):
                raise ValueError("fixed address census effects must all be finite")
            lower, upper = min(effects), max(effects)
            hulls.append(EffectHull(
                contrast=label,
                budget=budget,
                slot_effects=effects,
                descriptive_mean=float(np.mean(np.asarray(effects, dtype=np.float64))),
                lower=lower,
                upper=upper,
                width=upper - lower,
                replicate_count=len(effects),
            ))
    return tuple(hulls)


def fixed_eight_trajectory_hulls(
    replicate_summaries: Sequence[Mapping[tuple[Representation, Budget], EvaluationSummary]],
) -> tuple[EffectHull, ...]:
    """Return the two frozen across-budget diagnostic vectors and their exact hulls."""

    if len(replicate_summaries) != len(REPLICATES):
        raise ValueError("fixed address census requires exactly slots 0..7")
    specifications = (
        (Representation.RAW, Budget.SHORT, Budget.LONG, "RAW_GAIN"),
        (Representation.TRUE_RESIDUAL, Budget.LONG, Budget.SHORT, "TRUE_DEGRADE"),
    )
    hulls: list[EffectHull] = []
    for representation, left_budget, right_budget, label in specifications:
        effects = tuple(
            float(summary[(representation, left_budget)].target_equal_weight_regret)
            - float(summary[(representation, right_budget)].target_equal_weight_regret)
            for summary in replicate_summaries
        )
        if not all(np.isfinite(value) for value in effects):
            raise ValueError("fixed address trajectory effects must all be finite")
        lower, upper = min(effects), max(effects)
        hulls.append(EffectHull(
            contrast=label,
            budget=Budget.LONG,
            slot_effects=effects,
            descriptive_mean=float(np.mean(np.asarray(effects, dtype=np.float64))),
            lower=lower,
            upper=upper,
            width=upper - lower,
            replicate_count=len(effects),
        ))
    return tuple(hulls)


def _first_match(
    hulls: tuple[EffectHull, ...], trajectory_hulls: tuple[EffectHull, ...]
) -> str:
    by_key = {(item.contrast, item.budget): item for item in hulls}
    required = {(label, budget) for _, _, label in CONTRASTS for budget in Budget}
    if set(by_key) != required:
        raise ValueError("branch routing requires the complete six-hull census")
    for budget in Budget:
        rt = by_key[("RAW_MINUS_TRUE", budget)].slot_effects
        dt = by_key[("DERANGED_MINUS_TRUE", budget)].slot_effects
        rd = by_key[("RAW_MINUS_DERANGED", budget)].slot_effects
        if any(abs(rt[index] - (rd[index] + dt[index])) > NUMERIC_TOLERANCE for index in REPLICATES):
            raise ValueError("contrast identity x_RT=x_RD+x_DT failed")
    trajectory_by_label = {item.contrast: item for item in trajectory_hulls}
    if set(trajectory_by_label) != {"RAW_GAIN", "TRUE_DEGRADE"}:
        raise ValueError("branch routing requires both fixed trajectory hulls")
    rt_short = by_key[("RAW_MINUS_TRUE", Budget.SHORT)].slot_effects
    rt_long = by_key[("RAW_MINUS_TRUE", Budget.LONG)].slot_effects
    raw_gain = trajectory_by_label["RAW_GAIN"].slot_effects
    true_degrade = trajectory_by_label["TRUE_DEGRADE"].slot_effects
    if any(
        abs((rt_short[index] - rt_long[index]) - (raw_gain[index] + true_degrade[index]))
        > NUMERIC_TOLERANCE
        for index in REPLICATES
    ):
        raise ValueError("budget identity RT_SHORT-RT_LONG=RAW_GAIN+TRUE_DEGRADE failed")

    def sup(contrast: str, budget: Budget) -> bool:
        return by_key[(contrast, budget)].lower > DELTA

    def eq(contrast: str, budget: Budget) -> bool:
        item = by_key[(contrast, budget)]
        return item.lower >= -DELTA and item.upper <= DELTA

    def no_true_benefit(budget: Budget) -> bool:
        return by_key[("RAW_MINUS_TRUE", budget)].upper <= DELTA

    if (
        sup("RAW_MINUS_TRUE", Budget.SHORT)
        and sup("RAW_MINUS_TRUE", Budget.LONG)
        and sup("DERANGED_MINUS_TRUE", Budget.SHORT)
        and sup("DERANGED_MINUS_TRUE", Budget.LONG)
    ):
        return "PERSISTENT_ALIGNED_BIAS"
    if (
        sup("RAW_MINUS_TRUE", Budget.SHORT)
        and sup("RAW_MINUS_TRUE", Budget.LONG)
        and sup("RAW_MINUS_DERANGED", Budget.SHORT)
        and sup("RAW_MINUS_DERANGED", Budget.LONG)
        and eq("DERANGED_MINUS_TRUE", Budget.SHORT)
        and eq("DERANGED_MINUS_TRUE", Budget.LONG)
    ):
        return "GENERIC_PREPROCESSING"
    if (
        sup("RAW_MINUS_TRUE", Budget.SHORT)
        and sup("DERANGED_MINUS_TRUE", Budget.SHORT)
        and eq("RAW_MINUS_TRUE", Budget.LONG)
        and eq("DERANGED_MINUS_TRUE", Budget.LONG)
        and eq("RAW_MINUS_DERANGED", Budget.LONG)
        and trajectory_by_label["RAW_GAIN"].lower > DELTA
        and trajectory_by_label["TRUE_DEGRADE"].upper <= DELTA
    ):
        return "OPTIMIZATION_EXPOSURE_ONLY"
    if no_true_benefit(Budget.SHORT) and no_true_benefit(Budget.LONG):
        return "CLOSE_TESTED_MECHANISM"
    return "UNRESOLVED"


def _census_binding_failures(
    replicate_summaries: Sequence[Mapping[tuple[Representation, Budget], EvaluationSummary]],
) -> list[str]:
    failures: list[str] = []
    if len(replicate_summaries) != len(REPLICATES):
        return ["fixed address census requires all eight slots 0..7"]
    required_keys = {
        (representation, budget) for representation in Representation for budget in Budget
    }
    for expected_slot, summaries in zip(REPLICATES, replicate_summaries):
        if not summaries:
            failures.append(f"slot {expected_slot} summary mapping is empty")
            continue
        if set(summaries) != required_keys:
            failures.append(f"slot {expected_slot} lacks the exact six representation/budget cells")
        for key, summary in summaries.items():
            if summary.replicate != expected_slot:
                failures.append(
                    f"outer slot {expected_slot} {key[0].value}/{key[1].value} is bound "
                    f"to replicate id {summary.replicate}"
                )
            if key != (summary.representation, summary.budget):
                failures.append(f"slot {expected_slot} summary key disagrees with typed cell")
    return failures


def _raw_long_competence_failures(
    raw_long_summaries: Sequence[EvaluationSummary],
    policy: AnalysisPolicy,
) -> tuple[list[str], list[str]]:
    support_failures: list[str] = []
    numeric_failures: list[str] = []
    if len(raw_long_summaries) != len(REPLICATES):
        return ["RAW-LONG competence requires exactly slots 0..7"], []
    for slot, summary in zip(REPLICATES, raw_long_summaries):
        if summary.replicate != slot:
            support_failures.append(
                f"outer slot {slot} is bound to replicate id {summary.replicate}"
            )
        if summary.representation is not Representation.RAW or summary.budget is not Budget.LONG:
            support_failures.append(f"slot {slot} is not a typed RAW-LONG summary")
        k8_count = summary.row_count_by_regime.get("K8")
        counts = summary.material_stratum_count_by_regime.get("K8", {})
        raw_means = summary.mean_regret_by_regime_and_material_stratum.get("K8", {})
        script_means = summary.logged_scripted_mean_regret_by_regime_and_material_stratum.get(
            "K8", {}
        )
        if k8_count is None or k8_count < 48:
            support_failures.append(f"slot {slot} has fewer than 48 retained K8 rows")
        for stratum in MATERIAL_STRATA:
            count = counts.get(stratum)
            raw_mean = raw_means.get(stratum)
            script_mean = script_means.get(stratum)
            if count is None or count < policy.minimum_k8_rows_per_material_stratum:
                support_failures.append(
                    f"slot {slot} K8/{stratum} has fewer than "
                    f"{policy.minimum_k8_rows_per_material_stratum} retained rows"
                )
            if raw_mean is None or not np.isfinite(raw_mean) or raw_mean < 0.0:
                support_failures.append(
                    f"slot {slot} K8/{stratum} RAW-LONG mean is missing/nonfinite/negative"
                )
            elif raw_mean > policy.raw_long_max_mean_regret + policy.numeric_tolerance:
                numeric_failures.append(
                    f"slot {slot} K8/{stratum} RAW-LONG mean exceeds "
                    f"{policy.raw_long_max_mean_regret:.12f}"
                )
            if script_mean is None or not np.isfinite(script_mean) or script_mean < 0.0:
                support_failures.append(
                    f"slot {slot} K8/{stratum} scripted mean is missing/nonfinite/negative"
                )
    return support_failures, numeric_failures


def _competence_report(
    raw_long_summaries: Sequence[EvaluationSummary],
) -> dict[str, object]:
    cells: list[dict[str, object]] = []
    for slot, summary in zip(REPLICATES, raw_long_summaries):
        counts = summary.material_stratum_count_by_regime["K8"]
        raw_means = summary.mean_regret_by_regime_and_material_stratum["K8"]
        script_means = summary.logged_scripted_mean_regret_by_regime_and_material_stratum["K8"]
        for stratum in MATERIAL_STRATA:
            raw = float(raw_means[stratum])
            script = float(script_means[stratum])
            cells.append({
                "slot": slot,
                "stratum": stratum,
                "row_count": int(counts[stratum]),
                "raw_mean_regret": raw,
                "script_mean_regret": script,
                "raw_minus_script": raw - script,
            })
    return {
        "cells": cells,
        "c_raw": max(float(cell["raw_mean_regret"]) for cell in cells),
        "max_raw_minus_script": max(float(cell["raw_minus_script"]) for cell in cells),
        "script_is_qualification_gate": False,
    }


def assess_raw_long_competence(
    raw_long_summaries: Sequence[EvaluationSummary],
    *,
    policy: AnalysisPolicy | None = None,
) -> dict[str, object]:
    """Assess only the eight RAW-LONG K8 slots before any residual-arm inspection."""

    frozen_policy = AnalysisPolicy() if policy is None else policy
    if type(frozen_policy) is not AnalysisPolicy:
        raise TypeError("competence requires the exact frozen AnalysisPolicy")
    support_failures, numeric_failures = _raw_long_competence_failures(
        raw_long_summaries, frozen_policy
    )
    if support_failures:
        return {
            "status": "NONIDENTIFYING",
            "disposition": "NONIDENTIFYING_K8_COMPETENCE_SUPPORT",
            "failures": support_failures,
            "report": None,
        }
    report = _competence_report(raw_long_summaries)
    if numeric_failures:
        return {
            "status": "STOP",
            "disposition": "STOP_RAW_LONG_INCOMPETENT",
            "failures": numeric_failures,
            "report": report,
        }
    return {
        "status": "PASS",
        "disposition": "RAW_LONG_COMPETENT",
        "failures": [],
        "report": report,
    }


def _serialized_hull(item: EffectHull) -> dict[str, object]:
    return {
        "contrast": item.contrast,
        "budget": item.budget.value,
        "slot_effects": list(item.slot_effects),
        "descriptive_mean": item.descriptive_mean,
        "lower": item.lower,
        "upper": item.upper,
        "width": item.width,
        "replicate_count": item.replicate_count,
        "method": item.method,
        "joint_coverage": item.joint_coverage,
        "family_alpha": item.family_alpha,
        "multiplicity": item.multiplicity,
    }


def analyze(
    replicate_summaries: Sequence[Mapping[tuple[Representation, Budget], EvaluationSummary]],
    *,
    policy: AnalysisPolicy | None = None,
    structural_failures: Sequence[str] = (),
) -> dict[str, object]:
    """Apply competence, completeness, and exact fixed-census first-match routing."""

    frozen_policy = AnalysisPolicy() if policy is None else policy
    if type(frozen_policy) is not AnalysisPolicy:
        raise TypeError("analysis requires the exact frozen AnalysisPolicy")
    if structural_failures:
        return {
            "status": "NONIDENTIFYING",
            "interpretation": "UNRESOLVED",
            "failures": list(structural_failures),
            "effect_hulls": [],
            "trajectory_hulls": [],
            "raw_long_competence": None,
            "close_budget_descriptions": None,
            "inference_method": FIXED_CENSUS_METHOD,
            "target_population": "FIXED_ADDRESSES_0_TO_7_NO_SEED_SUPERPOPULATION",
        }
    if len(replicate_summaries) != len(REPLICATES) or any(
        (Representation.RAW, Budget.LONG) not in summaries for summaries in replicate_summaries
    ):
        raw_long_summaries: list[EvaluationSummary] = []
    else:
        raw_long_summaries = [
            summaries[(Representation.RAW, Budget.LONG)] for summaries in replicate_summaries
        ]
    competence = assess_raw_long_competence(raw_long_summaries, policy=frozen_policy)
    if competence["status"] == "NONIDENTIFYING":
        return {
            "status": "NONIDENTIFYING",
            "interpretation": "NONIDENTIFYING_K8_COMPETENCE_SUPPORT",
            "failures": competence["failures"],
            "effect_hulls": [],
            "trajectory_hulls": [],
            "raw_long_competence": None,
            "close_budget_descriptions": None,
            "inference_method": FIXED_CENSUS_METHOD,
            "target_population": "FIXED_ADDRESSES_0_TO_7_NO_SEED_SUPERPOPULATION",
        }
    if competence["status"] == "STOP":
        return {
            "status": "NONIDENTIFYING",
            "interpretation": "STOP_RAW_LONG_INCOMPETENT",
            "failures": competence["failures"],
            "effect_hulls": [],
            "trajectory_hulls": [],
            "raw_long_competence": competence["report"],
            "close_budget_descriptions": None,
            "inference_method": FIXED_CENSUS_METHOD,
            "target_population": "FIXED_ADDRESSES_0_TO_7_NO_SEED_SUPERPOPULATION",
        }
    census_failures = _census_binding_failures(replicate_summaries)
    if census_failures:
        return {
            "status": "NONIDENTIFYING",
            "interpretation": "UNRESOLVED",
            "failures": census_failures,
            "effect_hulls": [],
            "trajectory_hulls": [],
            "raw_long_competence": competence["report"],
            "close_budget_descriptions": None,
            "inference_method": FIXED_CENSUS_METHOD,
            "target_population": "FIXED_ADDRESSES_0_TO_7_NO_SEED_SUPERPOPULATION",
        }
    try:
        hulls = fixed_eight_effect_hulls(replicate_summaries)
        trajectory_hulls = fixed_eight_trajectory_hulls(replicate_summaries)
    except (KeyError, TypeError, ValueError) as error:
        return {
            "status": "NONIDENTIFYING",
            "interpretation": "UNRESOLVED",
            "failures": [f"NONIDENTIFYING_INCOMPLETE_FIXED_CENSUS: {error}"],
            "effect_hulls": [],
            "trajectory_hulls": [],
            "raw_long_competence": competence["report"],
            "close_budget_descriptions": None,
            "inference_method": FIXED_CENSUS_METHOD,
            "target_population": "FIXED_ADDRESSES_0_TO_7_NO_SEED_SUPERPOPULATION",
        }
    interpretation = _first_match(hulls, trajectory_hulls)
    close_descriptions: dict[str, str] | None = None
    if interpretation == "CLOSE_TESTED_MECHANISM":
        by_key = {(item.contrast, item.budget): item for item in hulls}
        close_descriptions = {}
        for budget in Budget:
            item = by_key[("RAW_MINUS_TRUE", budget)]
            if item.upper < -DELTA:
                description = "RAW_SUPERIOR"
            elif item.lower >= -DELTA and item.upper <= DELTA:
                description = "PRACTICAL_EQUIVALENCE"
            else:
                description = "MIXED_OR_SMALL_TRUE_EFFECT"
            close_descriptions[budget.value] = description
    return {
        "status": "IDENTIFYING",
        "interpretation": interpretation,
        "failures": [],
        "effect_hulls": [_serialized_hull(item) for item in hulls],
        "trajectory_hulls": [_serialized_hull(item) for item in trajectory_hulls],
        "raw_long_competence": competence["report"],
        "close_budget_descriptions": close_descriptions,
        "inference_method": FIXED_CENSUS_METHOD,
        "target_population": "FIXED_ADDRESSES_0_TO_7_NO_SEED_SUPERPOPULATION",
    }
