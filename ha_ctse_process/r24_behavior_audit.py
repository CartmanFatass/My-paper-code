"""Pure helpers for R24 assignment-to-behavior audit metrics."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class R24AuditRecord:
    horizon: int
    forced_kind: str
    action_distance: float
    effect_distance: float
    label: int
    action_feature: tuple[float, ...] = ()
    effect_feature: tuple[float, ...] = ()


def _as_feature_rows(values) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim == 0:
        return arr.reshape(1, 1)
    if arr.ndim == 1:
        return arr.reshape(1, -1)
    return arr.reshape(arr.shape[0], -1)


def _as_sample_rows(values) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim == 0:
        return arr.reshape(1, 1)
    if arr.ndim == 1:
        return arr.reshape(-1, 1)
    return arr.reshape(arr.shape[0], -1)


def _row_normalize(values: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    clipped = np.clip(values, eps, None)
    sums = np.sum(clipped, axis=1, keepdims=True)
    return clipped / np.maximum(sums, eps)


def action_feature_kl(p, q) -> np.ndarray:
    p_rows = _as_feature_rows(p)
    q_rows = _as_feature_rows(q)
    if p_rows.shape != q_rows.shape:
        raise ValueError("shape mismatch")

    p_probs = _row_normalize(p_rows)
    q_probs = _row_normalize(q_rows)
    return np.sum(p_probs * (np.log(p_probs) - np.log(q_probs)), axis=1)


def action_feature_distance(forced, base) -> float:
    forced_rows = _as_feature_rows(forced)
    base_rows = _as_feature_rows(base)
    if forced_rows.shape != base_rows.shape:
        return 0.0

    forced_sums = np.sum(forced_rows, axis=1)
    base_sums = np.sum(base_rows, axis=1)
    forced_is_prob = np.all(forced_rows >= 0.0) and np.allclose(forced_sums, 1.0, atol=1e-4)
    base_is_prob = np.all(base_rows >= 0.0) and np.allclose(base_sums, 1.0, atol=1e-4)
    if forced_is_prob and base_is_prob:
        return float(np.mean(action_feature_kl(forced_rows, base_rows)))

    return float(np.mean(np.linalg.norm(forced_rows - base_rows, axis=1)))


def effect_distance(base_start, base_end, forced_start, forced_end) -> float:
    base_start_arr = np.ravel(np.asarray(base_start, dtype=np.float64))
    base_end_arr = np.ravel(np.asarray(base_end, dtype=np.float64))
    forced_start_arr = np.ravel(np.asarray(forced_start, dtype=np.float64))
    forced_end_arr = np.ravel(np.asarray(forced_end, dtype=np.float64))
    if base_start_arr.shape != base_end_arr.shape or forced_start_arr.shape != forced_end_arr.shape:
        return 0.0

    base_delta = base_end_arr - base_start_arr
    forced_delta = forced_end_arr - forced_start_arr
    if base_delta.shape != forced_delta.shape:
        return 0.0
    return float(np.linalg.norm(forced_delta - base_delta))


def between_within_ratio(features, labels) -> float:
    feature_rows = _as_sample_rows(features)
    label_rows = np.ravel(np.asarray(labels))
    if feature_rows.shape[0] != label_rows.shape[0]:
        raise ValueError("row mismatch")
    if feature_rows.shape[0] <= 1:
        return 0.0

    unique_labels = np.unique(label_rows)
    if unique_labels.size <= 1:
        return 0.0

    groups = [feature_rows[label_rows == label] for label in unique_labels]
    if any(group.shape[0] < 2 for group in groups):
        return 0.0

    grand_mean = np.mean(feature_rows, axis=0)
    between = sum(group.shape[0] * float(np.sum((np.mean(group, axis=0) - grand_mean) ** 2)) for group in groups)
    within = sum(float(np.sum((group - np.mean(group, axis=0)) ** 2)) for group in groups)
    between /= float(feature_rows.shape[0])
    within /= float(feature_rows.shape[0])
    return float(between / max(within, 1e-12))


def _same_group_matrix(labels: np.ndarray) -> np.ndarray:
    rows = np.ravel(np.asarray(labels))
    return rows[:, None] == rows[None, :]


def shuffled_between_within_ratio(features, labels, seed: int = 0, n_shuffles: int = 32) -> float:
    label_rows = np.ravel(np.asarray(labels))
    if label_rows.size <= 1:
        return 0.0
    rng = np.random.default_rng(int(seed))
    original_partition = _same_group_matrix(label_rows)
    ratios: list[float] = []
    for _ in range(int(max(n_shuffles, 1))):
        shuffled = np.array(label_rows, copy=True)
        rng.shuffle(shuffled)
        if np.array_equal(_same_group_matrix(shuffled), original_partition):
            continue
        ratios.append(between_within_ratio(features, shuffled))
    if not ratios:
        return 0.0
    return float(np.mean(np.asarray(ratios, dtype=np.float64)))


def _label_entropy(labels: list[int]) -> float:
    if not labels:
        return 0.0
    _, counts = np.unique(np.asarray(labels), return_counts=True)
    probs = counts.astype(np.float64) / float(np.sum(counts))
    return float(round(-float(np.sum(probs * np.log(np.clip(probs, 1e-12, 1.0)))), 12))


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(round(float(np.mean(np.asarray(values, dtype=np.float64))), 12))


def _feature_rows(records: list[R24AuditRecord], field: str) -> np.ndarray | None:
    values = [tuple(getattr(record, field)) for record in records if tuple(getattr(record, field))]
    if len(values) != len(records):
        return None
    return _as_sample_rows(values)


def _rounded_ratio(value: float) -> float:
    return float(round(float(value), 12))


def summarize_audit_records(records, shuffle_seed: int = 0) -> dict[str, float]:
    records = list(records)
    metrics: dict[str, float] = {"r24_audit_records": float(len(records))}
    groups: dict[tuple[str, int], list[R24AuditRecord]] = {}
    for record in records:
        groups.setdefault((str(record.forced_kind), int(record.horizon)), []).append(record)

    for (forced_kind, horizon), group in sorted(groups.items()):
        prefix = f"r24_{forced_kind}"
        suffix = f"h{horizon}"
        metrics[f"{prefix}_action_distance_{suffix}"] = _mean([float(record.action_distance) for record in group])
        metrics[f"{prefix}_effect_distance_{suffix}"] = _mean([float(record.effect_distance) for record in group])
        metrics[f"{prefix}_label_entropy_{suffix}"] = _label_entropy([int(record.label) for record in group])
        labels = [int(record.label) for record in group]
        for feature_name, metric_name in (
            ("action_feature", "action_between_within"),
            ("effect_feature", "effect_between_within"),
        ):
            rows = _feature_rows(group, feature_name)
            if rows is None:
                continue
            ratio = between_within_ratio(rows, labels)
            shuffled_ratio = shuffled_between_within_ratio(rows, labels, seed=int(shuffle_seed) + int(horizon))
            metrics[f"{prefix}_{metric_name}_ratio_{suffix}"] = _rounded_ratio(ratio)
            metrics[f"{prefix}_{metric_name}_shuffled_ratio_{suffix}"] = _rounded_ratio(shuffled_ratio)
            metrics[f"{prefix}_{metric_name}_lift_{suffix}"] = _rounded_ratio(
                ratio / max(float(shuffled_ratio), 1e-12)
            )

    return metrics


def write_audit_csv(path, metrics) -> None:
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted(metrics.keys())
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerow({key: metrics[key] for key in keys})
