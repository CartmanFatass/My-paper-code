"""Pure NumPy substrate gate diagnostics for HA-CTSE Round 12."""

from __future__ import annotations

from dataclasses import dataclass
import json

import numpy as np


@dataclass(frozen=True)
class SubstrateThresholds:
    dwell_min_intervals: float = 3.0
    dwell_diag_margin: float = 0.20
    outcome_auc_floor: float = 0.60
    outcome_auc_margin: float = 0.05
    role_max_label_fraction: float = 0.95
    role_mi_std_margin: float = 2.0
    role_stability_margin: float = 0.10


def _unique_in_order(values: np.ndarray) -> list[object]:
    unique: list[object] = []
    for value in values:
        if not any(_labels_equal(value, existing) for existing in unique):
            unique.append(value)
    return unique


def _counts_for_unique(values: np.ndarray, unique: list[object]) -> np.ndarray:
    counts = [sum(1 for value in values if _labels_equal(value, label)) for label in unique]
    return np.asarray(counts, dtype=np.int64)


def _is_non_finite_label(value: object) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return not bool(np.isfinite(numeric))


def _labels_equal(left: object, right: object) -> bool:
    if _is_non_finite_label(left) and _is_non_finite_label(right):
        return True
    try:
        result = left == right
    except (TypeError, ValueError):
        return False
    if isinstance(result, np.ndarray):
        return bool(np.all(result))
    return bool(result)


def _label_sort_key(value: object) -> tuple[int, float, str]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return (1, 0.0, str(value))
    if np.isfinite(numeric):
        return (0, float(numeric), str(value))
    return (2, 0.0, str(value))


def _binary_classes(values: np.ndarray) -> list[object]:
    classes = _unique_in_order(values)
    if len(classes) < 2:
        return classes
    if len(classes) > 2:
        raise ValueError("auc_binary requires binary labels")

    numeric_classes: list[tuple[float, object]] = []
    for label in classes:
        try:
            numeric = float(label)
        except (TypeError, ValueError):
            numeric_classes = []
            break
        if not np.isfinite(numeric):
            numeric_classes = []
            break
        numeric_classes.append((float(numeric), label))
    if {numeric for numeric, _label in numeric_classes} == {0.0, 1.0}:
        negative = next(label for numeric, label in numeric_classes if numeric == 0.0)
        positive = next(label for numeric, label in numeric_classes if numeric == 1.0)
        return [negative, positive]

    return sorted(classes, key=_label_sort_key)


def _canonical_role_label(value: object) -> object:
    if _is_non_finite_label(value):
        return "__missing_non_finite__"
    return value


def parse_vector_field(raw: object) -> np.ndarray:
    """Parse a JSON vector field from substrate_steps.csv."""
    if raw is None:
        return np.asarray([], dtype=np.float64)
    text = str(raw).strip()
    if not text:
        return np.asarray([], dtype=np.float64)
    try:
        payload = json.loads(text)
        if not isinstance(payload, list):
            return np.asarray([], dtype=np.float64)
        values = np.asarray(payload, dtype=np.float64)
    except (TypeError, ValueError, json.JSONDecodeError):
        return np.asarray([], dtype=np.float64)
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        return np.asarray([], dtype=np.float64)
    return values


def standardize_rows(values: np.ndarray) -> np.ndarray:
    """Column-standardize a 2-D matrix while keeping constant columns at zero."""
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError("standardize_rows requires a 2-D matrix")
    if matrix.size == 0:
        return matrix.copy()
    mean = np.mean(matrix, axis=0, keepdims=True)
    std = np.std(matrix, axis=0, keepdims=True)
    safe_std = np.where(std > 1e-12, std, 1.0)
    scaled = (matrix - mean) / safe_std
    return np.where(np.isfinite(scaled), scaled, 0.0)


def choose_cluster_count(
    *,
    n_rows: int,
    omega_labels: np.ndarray,
    min_k: int = 2,
    max_k: int = 8,
) -> int:
    """Choose compact-cluster count from omega cardinality, bounded by sample count."""
    rows = max(int(n_rows), 0)
    if rows <= 1:
        return rows
    labels = np.asarray(omega_labels).reshape(-1)
    omega_k = int(np.unique(labels).size) if labels.size else int(min_k)
    k = max(int(min_k), omega_k)
    k = min(k, int(max_k), rows)
    return max(k, 1)


def deterministic_kmeans(
    values: np.ndarray,
    *,
    k: int,
    seed: int = 13,
    max_iter: int = 64,
) -> np.ndarray:
    """Small deterministic NumPy k-means for offline diagnostics."""
    matrix = standardize_rows(values)
    n_rows = matrix.shape[0]
    if n_rows == 0:
        return np.asarray([], dtype=np.int64)
    k = int(max(1, min(int(k), n_rows)))
    if k == 1:
        return np.zeros(n_rows, dtype=np.int64)

    rng = np.random.default_rng(seed)
    first = int(rng.integers(0, n_rows))
    centers = [matrix[first]]
    for _ in range(1, k):
        distances = np.min(
            np.stack(
                [np.sum((matrix - center) ** 2, axis=1) for center in centers],
                axis=1,
            ),
            axis=1,
        )
        next_idx = int(np.argmax(distances))
        centers.append(matrix[next_idx])
    centers_arr = np.asarray(centers, dtype=np.float64)

    labels = np.zeros(n_rows, dtype=np.int64)
    for _ in range(max(int(max_iter), 1)):
        dist = np.stack(
            [np.sum((matrix - center) ** 2, axis=1) for center in centers_arr],
            axis=1,
        )
        new_labels = np.argmin(dist, axis=1).astype(np.int64)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for idx in range(k):
            mask = labels == idx
            if np.any(mask):
                centers_arr[idx] = np.mean(matrix[mask], axis=0)
    return labels


def dwell_lengths(memberships: np.ndarray) -> np.ndarray:
    """Return run lengths for consecutive identical memberships."""
    values = np.asarray(memberships)
    if values.ndim != 1:
        raise ValueError("dwell_lengths requires 1-D memberships")
    if values.size == 0:
        return np.asarray([], dtype=np.float64)

    change_idx = np.nonzero(values[1:] != values[:-1])[0] + 1
    boundaries = np.concatenate(([0], change_idx, [values.size]))
    return np.diff(boundaries).astype(np.float64)


def transition_diag_mass(memberships: np.ndarray) -> float:
    """Fraction of adjacent transitions that keep the same membership."""
    values = np.asarray(memberships)
    if values.ndim != 1:
        raise ValueError("transition_diag_mass requires 1-D memberships")
    if values.size < 2:
        return 1.0
    return float(np.mean(values[1:] == values[:-1]))


def dwell_pass(
    *,
    median_dwell: float,
    transition_diag: float,
    null_transition_diag: float,
    thresholds: SubstrateThresholds | None = None,
) -> dict[str, float | bool]:
    limits = thresholds or SubstrateThresholds()
    dwell_ok = float(median_dwell) >= limits.dwell_min_intervals
    diag_margin = float(transition_diag) - float(null_transition_diag)
    diag_ok = diag_margin >= limits.dwell_diag_margin
    return {
        "pass": bool(dwell_ok and diag_ok),
        "median_dwell": float(median_dwell),
        "transition_diag": float(transition_diag),
        "null_transition_diag": float(null_transition_diag),
        "diag_margin": float(diag_margin),
        "dwell_ok": bool(dwell_ok),
        "diag_ok": bool(diag_ok),
    }


def auc_binary(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Compute binary ROC AUC with average ranks for tied scores."""
    labels = np.asarray(y_true).reshape(-1)
    values = np.asarray(scores, dtype=np.float64).reshape(-1)
    if labels.shape[0] != values.shape[0]:
        raise ValueError("y_true and scores must have the same length")

    classes = _binary_classes(labels)
    if len(classes) < 2:
        return 0.5

    finite_mask = np.isfinite(values)
    labels = labels[finite_mask]
    values = values[finite_mask]

    negatives = np.asarray([_labels_equal(label, classes[0]) for label in labels], dtype=bool)
    positives = np.asarray([_labels_equal(label, classes[1]) for label in labels], dtype=bool)
    n_pos = int(np.sum(positives))
    n_neg = int(np.sum(negatives))
    if n_pos == 0 or n_neg == 0:
        return 0.5

    order = np.argsort(values, kind="mergesort")
    sorted_scores = values[order]
    ranks = np.empty(values.shape[0], dtype=np.float64)

    start = 0
    while start < sorted_scores.size:
        end = start + 1
        while end < sorted_scores.size and sorted_scores[end] == sorted_scores[start]:
            end += 1
        avg_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = avg_rank
        start = end

    pos_rank_sum = float(np.sum(ranks[positives]))
    auc = (pos_rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def discrete_membership_auc(target: np.ndarray, labels: np.ndarray) -> dict[str, float | bool | int]:
    """Best one-vs-rest AUC over discrete membership labels."""
    y = np.asarray(target).reshape(-1)
    z = np.asarray(labels).reshape(-1)
    fail_closed = {
        "target_valid": False,
        "auc": 0.5,
        "best_label": -1,
        "best_orientation": 1,
    }
    if y.shape[0] != z.shape[0]:
        return fail_closed
    if any(_is_non_finite_label(label) for label in z):
        return fail_closed

    classes = _unique_in_order(y)
    if y.shape[0] == 0 or len(classes) != 2:
        return {
            "target_valid": False,
            "auc": 0.5,
            "best_label": -1,
            "best_orientation": 1,
        }

    best_auc = 0.5
    best_label = -1
    best_orientation = 1
    best_label_set = False
    for label in _unique_in_order(z):
        score = (z == label).astype(np.float64)
        auc = float(auc_binary(y, score))
        oriented_auc = max(auc, 1.0 - auc)
        orientation = 1 if auc >= 0.5 else -1
        if not best_label_set or oriented_auc > best_auc:
            best_auc = oriented_auc
            try:
                best_label = int(label)
            except (TypeError, ValueError):
                best_label = -1
            best_orientation = orientation
            best_label_set = True

    return {
        "target_valid": True,
        "auc": float(best_auc),
        "best_label": int(best_label),
        "best_orientation": int(best_orientation),
    }


def outcome_pass(
    *,
    auc: float,
    baseline_auc: float,
    thresholds: SubstrateThresholds | None = None,
) -> dict[str, float | bool]:
    limits = thresholds or SubstrateThresholds()
    margin = float(auc) - float(baseline_auc)
    floor_ok = float(auc) >= limits.outcome_auc_floor
    margin_ok = margin >= limits.outcome_auc_margin
    return {
        "pass": bool(floor_ok and margin_ok),
        "auc": float(auc),
        "baseline_auc": float(baseline_auc),
        "margin": float(margin),
        "floor_ok": bool(floor_ok),
        "margin_ok": bool(margin_ok),
    }


def role_label_validity(
    labels: np.ndarray,
    thresholds: SubstrateThresholds | None = None,
) -> dict[str, float | bool | int]:
    limits = thresholds or SubstrateThresholds()
    values = np.asarray(labels).reshape(-1)
    if values.size == 0:
        return {
            "valid": False,
            "variance": 0.0,
            "max_label_fraction": 1.0,
            "n_samples": 0,
            "n_unique_labels": 0,
        }

    canonical_values = np.asarray([_canonical_role_label(value) for value in values], dtype=object)
    has_non_finite = any(_is_non_finite_label(value) for value in values)
    unique_values = _unique_in_order(canonical_values)
    counts = _counts_for_unique(canonical_values, unique_values)
    try:
        numeric_values = values.astype(np.float64)
        if np.all(np.isfinite(numeric_values)):
            variance = float(np.var(numeric_values))
        else:
            variance = 0.0 if len(unique_values) <= 1 else 1.0
    except (TypeError, ValueError):
        variance = 0.0 if len(unique_values) <= 1 else 1.0
    max_label_fraction = float(np.max(counts) / values.size)
    valid = (
        not has_non_finite
        and variance > 0.0
        and max_label_fraction < limits.role_max_label_fraction
    )
    return {
        "valid": bool(valid),
        "variance": variance,
        "max_label_fraction": max_label_fraction,
        "n_samples": int(values.size),
        "n_unique_labels": int(len(unique_values)),
    }


def mutual_information_discrete(x: np.ndarray, y: np.ndarray) -> float:
    """Mutual information for two same-length discrete label arrays."""
    x_values = np.asarray(x).reshape(-1)
    y_values = np.asarray(y).reshape(-1)
    if x_values.shape[0] != y_values.shape[0]:
        raise ValueError("x and y must have the same length")
    if x_values.size == 0:
        return 0.0

    _, x_inverse = np.unique(x_values, return_inverse=True)
    _, y_inverse = np.unique(y_values, return_inverse=True)
    joint = np.zeros((x_inverse.max() + 1, y_inverse.max() + 1), dtype=np.float64)
    np.add.at(joint, (x_inverse, y_inverse), 1.0)
    joint /= float(x_values.size)

    px = np.sum(joint, axis=1, keepdims=True)
    py = np.sum(joint, axis=0, keepdims=True)
    expected = px @ py
    nz = joint > 0.0
    return float(np.sum(joint[nz] * np.log(joint[nz] / expected[nz])))


def role_pass(
    *,
    role_valid: bool,
    mi: float,
    perm_mean: float,
    perm_std: float,
    stability: float,
    perm_stability: float,
    thresholds: SubstrateThresholds | None = None,
) -> dict[str, float | bool]:
    limits = thresholds or SubstrateThresholds()
    mi_threshold = float(perm_mean) + limits.role_mi_std_margin * float(perm_std)
    stability_threshold = float(perm_stability) + limits.role_stability_margin
    mi_ok = float(mi) >= mi_threshold
    stability_ok = float(stability) >= stability_threshold
    passed = bool(role_valid) and mi_ok and stability_ok
    return {
        "pass": bool(passed),
        "role_valid": bool(role_valid),
        "mi": float(mi),
        "perm_mean": float(perm_mean),
        "perm_std": float(perm_std),
        "mi_threshold": float(mi_threshold),
        "stability": float(stability),
        "perm_stability": float(perm_stability),
        "stability_threshold": float(stability_threshold),
        "mi_ok": bool(mi_ok),
        "stability_ok": bool(stability_ok),
    }
