"""Prespecified DEARS-B1 cell, flip, interval, and leakage analysis."""

from __future__ import annotations

from collections import defaultdict
import math
from typing import Mapping, Sequence

import numpy as np
from scipy.stats import t as student_t
import torch

from .domain import (
    GRU_DUAL, GRU_ORACLE, GRU_RAW, GRU_SNAPSHOT, GRU_UNBOUND,
    GRU_VALIDITY, LEARNED_ARMS, Action, Example,
)


INFORMATION_CEILINGS = {
    GRU_DUAL: 1.0, GRU_SNAPSHOT: 1.0 / 3.0, GRU_UNBOUND: 0.5,
    GRU_VALIDITY: 0.5, GRU_ORACLE: 1.0, GRU_RAW: 1.0,
}


def interval95(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or len(array) < 2 or not np.isfinite(array).all():
        raise ValueError("Student-t interval requires at least two finite seed-level values")
    mean = float(array.mean())
    standard_error = float(array.std(ddof=1) / math.sqrt(len(array)))
    half = float(student_t.ppf(0.975, len(array) - 1) * standard_error)
    return {"mean": mean, "lower": mean - half, "upper": mean + half,
            "standard_error": standard_error, "n": len(array)}


def expected_refined_cells() -> set[str]:
    return {
        "|".join((authentication, owner, lease, str(bit)))
        for authentication in ("GENUINE", "PAYLOAD_FLIP_BAD_TAG", "FOREIGN_ISSUER")
        for owner in ("SURVIVES", "BREAK_EDGE_1", "BREAK_EDGE_2")
        for lease in ("SURVIVES", "REFERENCE_BREAK_EDGE_1", "REFERENCE_BREAK_EDGE_2", "GAP_EDGE_1", "GAP_EDGE_2")
        for bit in (0, 1)
    }


def _group_probabilities(
    examples: Sequence[Example], probabilities: np.ndarray, field: str,
) -> dict[str, dict[str, object]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for index, example in enumerate(examples):
        groups[str(getattr(example, field))].append(index)
    return {
        key: {"count": len(indices), "mean_action_probabilities": probabilities[indices].mean(axis=0).tolist()}
        for key, indices in sorted(groups.items())
    }


def _flip_metrics(examples: Sequence[Example], probabilities: np.ndarray) -> dict[str, object]:
    lookup = {(row.superblock, row.authentication, row.owner_survives,
               row.lease_survives, row.displayed_bit): index
              for index, row in enumerate(examples)}
    greedy = probabilities.argmax(axis=1)
    definitions = {
        "owner_survival": lambda sb, bit: (
            lookup[(sb, True, True, True, bit)], lookup[(sb, True, False, True, bit)]),
        "lease_survival": lambda sb, bit: (
            lookup[(sb, True, True, True, bit)], lookup[(sb, True, True, False, bit)]),
        "authentication": lambda sb, bit: (
            lookup[(sb, True, True, True, bit)], lookup[(sb, False, True, True, bit)]),
        "content": lambda sb, _bit: (
            lookup[(sb, True, True, True, 0)], lookup[(sb, True, True, True, 1)]),
    }
    result = {}
    superblocks = sorted({row.superblock for row in examples})
    for name, pair_fn in definitions.items():
        pairs = [pair_fn(sb, bit) for sb in superblocks for bit in ((0,) if name == "content" else (0, 1))]
        endpoints = [index for pair in pairs for index in pair]
        endpoint_correct = [int(greedy[index]) == int(examples[index].correct_action) for index in endpoints]
        joint = [
            int(greedy[left]) == int(examples[left].correct_action)
            and int(greedy[right]) == int(examples[right].correct_action)
            for left, right in pairs
        ]
        result[name] = {
            "pairs": len(pairs), "endpoints": len(endpoints),
            "greedy_endpoint_accuracy": float(np.mean(endpoint_correct)),
            "greedy_joint_pair_accuracy": float(np.mean(joint)),
        }
    return result


def summarize_arm(examples: Sequence[Example], probabilities: torch.Tensor | np.ndarray) -> dict[str, object]:
    values = probabilities.detach().cpu().numpy() if isinstance(probabilities, torch.Tensor) else np.asarray(probabilities)
    if values.shape != (len(examples), 3) or not np.isfinite(values).all():
        raise ValueError("probability panel shape/finiteness failure")
    if np.max(np.abs(values.sum(axis=1) - 1.0)) > 1e-6 or np.min(values) < -1e-7:
        raise ValueError("invalid temperature-one probability simplex")
    by_cell: dict[str, list[int]] = defaultdict(list)
    for index, example in enumerate(examples):
        by_cell[example.refined_cell].append(index)
    missing = expected_refined_cells() - set(by_cell)
    extra = set(by_cell) - expected_refined_cells()
    if missing or extra:
        raise ValueError(f"refined-cell panel mismatch missing={sorted(missing)} extra={sorted(extra)}")
    greedy = values.argmax(axis=1)
    cells: dict[str, dict[str, object]] = {}
    for cell, indices in sorted(by_cell.items()):
        actions = {int(examples[index].correct_action) for index in indices}
        if len(actions) != 1:
            raise ValueError(f"refined cell has multiple correct actions: {cell}")
        action = actions.pop()
        cells[cell] = {
            "count": len(indices), "correct_action": Action(action).name,
            "mean_action_probabilities": values[indices].mean(axis=0).tolist(),
            "q_correct": float(values[indices, action].mean()),
            "greedy_accuracy": float(np.mean(greedy[indices] == action)),
        }
    return {
        "refined_cell_count": len(cells), "per_refined_cell": cells,
        "W": min(float(row["q_correct"]) for row in cells.values()),
        "worst_cell_greedy_top_one_accuracy": min(float(row["greedy_accuracy"]) for row in cells.values()),
        "matched_action_flips": _flip_metrics(examples, values),
        "action_probabilities_by_authentication_subtype": _group_probabilities(examples, values, "authentication_detail"),
        "action_probabilities_by_owner_subtype": _group_probabilities(examples, values, "owner_detail"),
        "action_probabilities_by_lease_subtype": _group_probabilities(examples, values, "lease_detail"),
    }


def analyze_registered(seed_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if len(seed_rows) != 10:
        raise ValueError("registered analysis requires exactly ten paired seeds")
    per_arm = {}
    w_by_arm: dict[str, list[float]] = {}
    for arm in LEARNED_ARMS:
        values = [float(row["test"][arm]["W"]) for row in seed_rows]  # type: ignore[index]
        w_by_arm[arm] = values
        per_arm[arm] = {"seed_W": values, "mean_W_student_t_95": interval95(values)}
    paired = {}
    for comparator in (GRU_SNAPSHOT, GRU_UNBOUND, GRU_VALIDITY, GRU_ORACLE, GRU_RAW):
        differences = [dual - other for dual, other in zip(w_by_arm[GRU_DUAL], w_by_arm[comparator], strict=True)]
        paired[comparator] = {"seed_differences": differences, "student_t_95": interval95(differences)}
    violations = {
        arm: [index for index, value in enumerate(w_by_arm[arm]) if value > ceiling + 1e-6]
        for arm, ceiling in INFORMATION_CEILINGS.items() if ceiling < 1.0
    }
    dual_interval = per_arm[GRU_DUAL]["mean_W_student_t_95"]
    oracle_interval = per_arm[GRU_ORACLE]["mean_W_student_t_95"]
    return {
        "per_arm": per_arm,
        "paired_dual_minus_comparator": paired,
        "information_ceilings": dict(INFORMATION_CEILINGS),
        "information_ceiling_violation_seed_indices": violations,
        "statements": {
            "learned_verifier_sufficiency": (
                dual_interval["lower"] > 0.90 and paired[GRU_ORACLE]["student_t_95"]["lower"] > -0.05
            ),
            "finite_budget_abstraction_advantage_over_raw": paired[GRU_RAW]["student_t_95"]["lower"] > 0.10,
            "raw_within_or_interval_spans_0.05_band": (
                abs(float(np.mean(paired[GRU_RAW]["seed_differences"]))) <= 0.05
                or paired[GRU_RAW]["student_t_95"]["lower"] <= 0.05 <= paired[GRU_RAW]["student_t_95"]["upper"]
            ),
            "oracle_common_learner_reliable": oracle_interval["lower"] > 0.90,
        },
    }
