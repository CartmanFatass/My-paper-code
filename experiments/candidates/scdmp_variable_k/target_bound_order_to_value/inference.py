from __future__ import annotations

from itertools import product

import numpy as np
from scipy.stats import t as student_t

from .config import ASSAY_COMPONENTS, ASSAY_MARGINS, K_TARGET, PHYSICAL_MARGINS


def t_bounds(values: list[float], confidence: float) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (10,) or not np.all(np.isfinite(array)):
        return {"mean": float("nan"), "sample_sd": float("nan"),
                "quantile": float("nan"), "lower": float("nan"), "upper": float("nan")}
    mean = float(np.mean(array))
    sd = float(np.std(array, ddof=1))
    quantile = float(student_t.ppf(confidence, df=9))
    half = quantile * sd / np.sqrt(10.0)
    return {"mean": mean, "sample_sd": sd, "quantile": quantile,
            "lower": mean - half, "upper": mean + half}


def exact_sign_randomization(values: list[float]) -> dict[str, float | int]:
    paired_effects = np.asarray(values, dtype=np.float64)
    observed = float(np.mean(paired_effects))
    statistics = np.asarray([
        np.mean(paired_effects * np.asarray(signs, dtype=np.float64))
        for signs in product((-1.0, 1.0), repeat=10)
    ])
    exceed = int(np.sum(statistics >= observed - 1.0e-15))
    return {"null": "paired seed-level component equals zero",
            "observed_mean": observed, "enumerations": 1_024,
            "one_sided_p_greater": exceed / 1_024.0}


def complete_inference(seed_results: list[dict[str, object]]) -> dict[str, object]:
    if len(seed_results) != 10 or [int(row["seed_index"]) for row in seed_results] != list(range(10)):
        raise ValueError("atomic Stage-A inference requires exact seed indices 0,...,9")
    physical: dict[str, dict[str, float]] = {}
    for name, margin in PHYSICAL_MARGINS.items():
        values = [float(row["physical"][name]) for row in seed_results]
        physical[name] = {**t_bounds(values, 1.0 - 0.05 / 9.0), "margin": margin}

    assay: dict[str, dict[str, object]] = {}
    for component in ASSAY_COMPONENTS:
        values = [float(row["pooled"][component]) for row in seed_results]
        assay[component] = {
            **t_bounds(values, 1.0 - 0.05 / 3.0),
            "margin": ASSAY_MARGINS[component],
            "paired_sign_randomization": exact_sign_randomization(values),
        }

    target_ratios = [float(row["competence"]["target"]["ratio"]) for row in seed_results]
    target_bound = t_bounds(target_ratios, 0.95)
    target_gate = bool(
        np.all(np.isfinite(target_ratios)) and target_bound["mean"] <= 0.85
        and target_bound["upper"] < 0.95
    )
    competence = {
        "fit_support_all": all(bool(row["competence"]["fit_support"]["passed"])
                               for row in seed_results),
        "target_ratios": target_ratios,
        "target_ratio_bound": target_bound,
        "target_ratio_gate": target_gate,
        "coordinate_variance_all": all(
            bool(item["passed"]) for row in seed_results
            for item in row["competence"]["coordinate_variance"]
        ),
        "action_sensitivity_all": all(
            bool(item["passed"]) for row in seed_results
            for item in row["competence"]["action_sensitivity"]
        ),
    }
    competence["COMP_A"] = all(competence[key] for key in (
        "fit_support_all", "target_ratio_gate", "coordinate_variance_all",
        "action_sensitivity_all",
    ))

    phys_excluded = any(row["upper"] < row["margin"] for row in physical.values())
    phys_passed = all(row["lower"] > row["margin"] for row in physical.values())
    denom_ok = all(
        np.isfinite(float(row["physical"][f"{name}_k{k}"]))
        and float(row["physical"][f"{name}_k{k}"]) > 0.0
        for row in seed_results for k in K_TARGET for name in ("T", "R")
    ) and all(
        np.isfinite(float(row["per_k"][str(k)]["h"]))
        and float(row["per_k"][str(k)]["h"]) > 0.0
        for row in seed_results for k in K_TARGET
    )
    lower_f, lower_r, lower_q = (assay[name]["lower"] for name in ASSAY_COMPONENTS)
    upper_f, upper_r, upper_q = (assay[name]["upper"] for name in ASSAY_COMPONENTS)
    action_adverse = upper_q < -0.05
    select_tr = lower_f > 0.20 and lower_r > 0.20 and lower_q > 0.10
    select_q = (not action_adverse) and lower_f > 0.20 and lower_r > 0.20 and upper_q < 0.05
    assay_negative = upper_f < 0.05 or upper_r < 0.05
    if phys_excluded:
        branch = "DELETE-FROM-OBJECT--PHYSICAL-OPPORTUNITY-EXCLUDED"
    elif not phys_passed:
        branch = "PHYSICAL-OPPORTUNITY-INDETERMINATE"
    elif not denom_ok:
        branch = "STAGE-A-ASSAY-DENOMINATOR-NONIDENTIFICATION"
    elif not competence["COMP_A"]:
        branch = "MODIFY-CHECKPOINT"
    elif action_adverse:
        branch = "ASSAY-ACTION-ADVERSE--DELETE-FROM-OBJECT"
    elif select_tr:
        branch = "SELECT-ORDER-TR"
    elif select_q:
        branch = "MODIFY-TO-ORDER-Q"
    elif assay_negative:
        branch = "ASSAY-NEGATIVE--DELETE-FROM-OBJECT"
    else:
        branch = "ASSAY-INDETERMINATE"
    return {
        "physical_bounds": physical,
        "assay_bounds": assay,
        "competence": competence,
        "predicates": {
            "PHYS_EXCLUDED": phys_excluded, "PHYS_PASSED": phys_passed,
            "ASSAY_DENOM_OK": denom_ok, "ACTION_ADVERSE": action_adverse,
            "SELECT_TR": select_tr, "SELECT_Q": select_q,
            "ASSAY_NEGATIVE": assay_negative,
        },
        "branch": branch,
        "partial_selection_permitted": False,
    }
