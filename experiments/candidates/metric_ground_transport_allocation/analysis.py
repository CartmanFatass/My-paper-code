"""Registered seed-level estimands, intervals, and ordered revision-04 map."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
_T_QUANTILES: dict[tuple[float, int], float] = {
    (0.9979166666666667, 15): 3.374933202443401,
}


def _student_t_ppf(probability: float, degrees_of_freedom: int) -> float:
    for (known_probability, known_degrees), quantile in _T_QUANTILES.items():
        if (
            degrees_of_freedom == known_degrees
            and math.isclose(probability, known_probability, rel_tol=0.0, abs_tol=1e-15)
        ):
            return quantile
    raise RuntimeError(
        "scipy is not installed and this frozen analysis only carries the registered "
        f"t quantile for p={probability!r}, df={degrees_of_freedom!r}"
    )

from .config import (
    BINDING_ACTION_MARGIN, BINDING_VALUE_MARGIN, FINAL_SEEDS,
    INERT_ACTION_EPSILON, INERT_VALUE_EPSILON, NONINFERIORITY_MARGIN,
    PERFORMANCE_MARGIN, ROBUSTNESS_MARGIN,
)


def _mean_endpoint(data: dict[str, np.ndarray], arm: int, binding: int, n: int, pairs: set[int] | None = None) -> float:
    mask = (data["arm"] == arm) & (data["binding"] == binding) & (data["N"] == n) & (data["epoch"] == 1)
    if pairs is not None:
        mask &= np.isin(data["ordered_pair_index"], tuple(pairs))
    return float(data["normalized_endpoint"][mask].mean())


def _mean_alignment(data: dict[str, np.ndarray], binding: int, n: int, pairs: set[int]) -> float:
    mask = (
        (data["arm"] == 0) & (data["binding"] == binding) & (data["N"] == n)
        & (data["epoch"] == 1) & np.isin(data["ordered_pair_index"], tuple(pairs))
    )
    return float(data["alignment"][mask].mean())


def seed_estimands(path: Path) -> dict[str, float]:
    with np.load(path, allow_pickle=False) as packet:
        data = {key: packet[key] for key in packet.files}
    binding_pairs = {2, 9}  # ORDERED_PAIRS: (0,3), (3,0)
    inert_pairs = {4, 7}    # ORDERED_PAIRS: (1,2), (2,1)
    v = {(a, c, n): _mean_endpoint(data, a, c, n) for a in (0, 1) for c in (0, 1) for n in (4, 6, 8, 12)}
    result: dict[str, float] = {}
    result["Delta(6)"] = v[0, 0, 6] - v[1, 0, 6]
    result["Delta(12)"] = v[0, 0, 12] - v[1, 0, 12]
    d_m = 0.5 * (v[0, 0, 4] + v[0, 0, 8]) - min(v[0, 0, 6], v[0, 0, 12])
    d_f = 0.5 * (v[1, 0, 4] + v[1, 0, 8]) - min(v[1, 0, 6], v[1, 0, 12])
    result["Delta_R"] = d_f - d_m
    result["T"] = 0.5 * ((v[0, 0, 4] - v[1, 0, 4]) + (v[0, 0, 8] - v[1, 0, 8]))
    for n in (6, 12):
        result[f"Theta_B({n})"] = _mean_endpoint(data, 0, 0, n, binding_pairs) - _mean_endpoint(data, 0, 1, n, binding_pairs)
        result[f"Theta_J({n})"] = _mean_endpoint(data, 0, 0, n, inert_pairs) - _mean_endpoint(data, 0, 1, n, inert_pairs)
        result[f"Gamma_B({n})"] = _mean_alignment(data, 0, n, binding_pairs) - _mean_alignment(data, 1, n, binding_pairs)
        result[f"Gamma_J({n})"] = _mean_alignment(data, 0, n, inert_pairs) - _mean_alignment(data, 1, n, inert_pairs)
    return result


def _interval(values: np.ndarray) -> dict[str, float]:
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    quantile = _student_t_ppf(1.0 - 0.05 / (2.0 * 12.0), 15)
    half = quantile * sd / math.sqrt(16.0)
    return {"mean": mean, "sd": sd, "lower": mean - half, "upper": mean + half, "quantile": quantile}


def _positive(interval: dict[str, float], margin: float) -> str:
    if interval["lower"] > margin:
        return "SUPPORTED_POSITIVE"
    if interval["upper"] <= margin:
        return "AFFIRMATIVELY_BELOW_MATERIAL"
    return "POSITIVE_UNRESOLVED"


def _equivalence(interval: dict[str, float], epsilon: float) -> str:
    if interval["lower"] >= -epsilon and interval["upper"] <= epsilon:
        return "EQUIVALENT"
    if interval["upper"] < -epsilon or interval["lower"] > epsilon:
        return "AFFIRMATIVELY_OUTSIDE_EQUIVALENCE"
    return "EQUIVALENCE_UNRESOLVED"


def analyze(root: Path, structural_valid: bool, optimization_valid: bool) -> dict[str, object]:
    per_seed = {str(seed): seed_estimands(root / f"seed_{seed}.npz") for seed in FINAL_SEEDS}
    names = list(next(iter(per_seed.values())).keys())
    intervals = {name: _interval(np.asarray([per_seed[str(seed)][name] for seed in FINAL_SEEDS])) for name in names}
    if any(item["sd"] == 0.0 or not all(np.isfinite(item[k]) for k in ("mean", "sd", "lower", "upper")) for item in intervals.values()):
        structural_valid = False

    d6, d12 = intervals["Delta(6)"], intervals["Delta(12)"]
    if d6["lower"] > PERFORMANCE_MARGIN and d12["lower"] > PERFORMANCE_MARGIN:
        primary = "METRIC_MATERIALLY_BETTER"
    elif d6["upper"] < -PERFORMANCE_MARGIN and d12["upper"] < -PERFORMANCE_MARGIN:
        primary = "FREE_MATERIALLY_BETTER"
    elif all(x["lower"] >= -PERFORMANCE_MARGIN and x["upper"] <= PERFORMANCE_MARGIN for x in (d6, d12)):
        primary = "PRACTICALLY_EQUIVALENT"
    elif ((d6["lower"] > PERFORMANCE_MARGIN and d12["upper"] < -PERFORMANCE_MARGIN)
          or (d12["lower"] > PERFORMANCE_MARGIN and d6["upper"] < -PERFORMANCE_MARGIN)):
        primary = "SIZE_INTERACTION"
    else:
        primary = "UNRESOLVED"

    robustness_statuses = {
        "Delta_R": _positive(intervals["Delta_R"], ROBUSTNESS_MARGIN),
        "Delta(6)": _positive(d6, NONINFERIORITY_MARGIN),
        "Delta(12)": _positive(d12, NONINFERIORITY_MARGIN),
        "T": _positive(intervals["T"], NONINFERIORITY_MARGIN),
    }
    if all(value == "SUPPORTED_POSITIVE" for value in robustness_statuses.values()):
        robustness = "ROBUSTNESS_SUPPORTED"
    elif any(value == "AFFIRMATIVELY_BELOW_MATERIAL" for value in robustness_statuses.values()):
        robustness = "ROBUSTNESS_AFFIRMATIVELY_REJECTED"
    else:
        robustness = "ROBUSTNESS_UNRESOLVED"
    heldout = primary == "METRIC_MATERIALLY_BETTER" or robustness == "ROBUSTNESS_SUPPORTED"

    causal: dict[str, str] = {}
    for n in (6, 12):
        causal[f"Theta_B({n})"] = _positive(intervals[f"Theta_B({n})"], BINDING_VALUE_MARGIN)
        causal[f"Theta_J({n})"] = _equivalence(intervals[f"Theta_J({n})"], INERT_VALUE_EPSILON)
        causal[f"Gamma_B({n})"] = _positive(intervals[f"Gamma_B({n})"], BINDING_ACTION_MARGIN)
        causal[f"Gamma_J({n})"] = _equivalence(intervals[f"Gamma_J({n})"], INERT_ACTION_EPSILON)
    all_metric = all(causal[f"Theta_B({n})"] == "SUPPORTED_POSITIVE" and causal[f"Theta_J({n})"] == "EQUIVALENT"
                     and causal[f"Gamma_B({n})"] == "SUPPORTED_POSITIVE" and causal[f"Gamma_J({n})"] == "EQUIVALENT"
                     for n in (6, 12))
    affirmative_nonmetric = any(value in ("AFFIRMATIVELY_BELOW_MATERIAL", "AFFIRMATIVELY_OUTSIDE_EQUIVALENCE") for value in causal.values())

    if not structural_valid or not optimization_valid:
        branch = "BOUNDED_NONIDENTIFICATION_STRUCTURAL"
    elif heldout and all_metric:
        branch = "RETAIN_METRIC_FINITE_BUDGET"
    elif primary == "FREE_MATERIALLY_BETTER" or (primary == "PRACTICALLY_EQUIVALENT" and robustness == "ROBUSTNESS_AFFIRMATIVELY_REJECTED"):
        branch = "DELETE_METRIC_EQUAL_CLASS"
    elif heldout and affirmative_nonmetric:
        branch = "GENERIC_FINITE_BUDGET_EFFECT"
    elif primary == "SIZE_INTERACTION":
        branch = "SIZE_INTERACTION"
    else:
        branch = "BOUNDED_NONIDENTIFICATION"
    return {
        "per_seed": per_seed,
        "intervals": intervals,
        "primary_relation": primary,
        "robustness_relation": robustness,
        "robustness_statuses": robustness_statuses,
        "heldout_value_clears": heldout,
        "causal_statuses": causal,
        "branch": branch,
        "structural_valid": structural_valid,
        "optimization_valid": optimization_valid,
    }
