"""R24 forced assignment-to-behavior audit helpers.

These functions are diagnostic-only. They do not inject reward and do not
modify the trainer state. The operational script in scripts/ uses these helpers
to summarize forced-Z / forced-z_i rollouts from checkpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
from pathlib import Path
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class R24BehaviorAuditConfig:
    horizons: tuple[int, ...] = (10, 20, 50)
    max_states: int = 32
    max_labels: int = 6
    seed: int = 1


@dataclass(frozen=True)
class R24AuditRecord:
    horizon: int
    forced_kind: str
    action_kl: float
    effect_distance: float
    label: int


def _as_2d(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    return arr


def action_feature_kl(p: np.ndarray, q: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Row-wise KL for discrete action-probability features.

    Continuous actor features are not probabilities; callers should compare
    them with Euclidean/cosine distances instead. This helper is intentionally
    probability-specific and clips rows to avoid log(0).
    """
    p_arr = np.clip(_as_2d(p), eps, 1.0)
    q_arr = np.clip(_as_2d(q), eps, 1.0)
    if p_arr.shape != q_arr.shape:
        raise ValueError(f"action_feature_kl shape mismatch: p={p_arr.shape}, q={q_arr.shape}")
    p_arr = p_arr / np.maximum(p_arr.sum(axis=-1, keepdims=True), eps)
    q_arr = q_arr / np.maximum(q_arr.sum(axis=-1, keepdims=True), eps)
    return np.sum(p_arr * (np.log(p_arr) - np.log(q_arr)), axis=-1).astype(np.float64)


def between_within_ratio(features: np.ndarray, labels: np.ndarray, eps: float = 1e-8) -> float:
    """Return between-label centroid distance divided by within-label variance."""
    feats = _as_2d(np.asarray(features, dtype=np.float64))
    labs = np.asarray(labels, dtype=np.int64).reshape(-1)
    if feats.shape[0] != labs.shape[0]:
        raise ValueError(f"between_within_ratio row mismatch: features={feats.shape[0]}, labels={labs.shape[0]}")
    if feats.shape[0] <= 1:
        return 0.0
    unique = np.unique(labs)
    if unique.size <= 1:
        return 0.0
    global_mean = feats.mean(axis=0)
    between = 0.0
    within = 0.0
    for label in unique:
        mask = labs == int(label)
        group = feats[mask]
        if group.shape[0] < 2:
            return 0.0
        if group.size == 0:
            continue
        center = group.mean(axis=0)
        between += float(group.shape[0]) * float(np.mean((center - global_mean) ** 2))
        within += float(np.sum((group - center) ** 2)) / max(int(group.shape[0]), 1)
    between /= max(int(feats.shape[0]), 1)
    within /= max(int(unique.size), 1)
    return float(between / max(within, eps))


def summarize_audit_records(records: Sequence[R24AuditRecord]) -> dict[str, float]:
    out: dict[str, float] = {"r24_audit_records": float(len(records))}
    if not records:
        return out
    for kind in sorted({r.forced_kind for r in records}):
        for horizon in sorted({int(r.horizon) for r in records if r.forced_kind == kind}):
            subset = [r for r in records if r.forced_kind == kind and int(r.horizon) == horizon]
            if not subset:
                continue
            prefix = f"r24_{kind}"
            out[f"{prefix}_action_kl_h{horizon}"] = float(
                round(sum(r.action_kl for r in subset) / len(subset), 12)
            )
            out[f"{prefix}_effect_distance_h{horizon}"] = float(
                round(sum(r.effect_distance for r in subset) / len(subset), 12)
            )
            labels = np.asarray([r.label for r in subset], dtype=np.int64)
            out[f"{prefix}_label_entropy_h{horizon}"] = _entropy(labels)
    return out


def _entropy(labels: np.ndarray) -> float:
    if labels.size == 0:
        return 0.0
    counts = np.bincount(labels.astype(np.int64))
    probs = counts[counts > 0].astype(np.float64)
    probs = probs / probs.sum()
    return float(-np.sum(probs * np.log(probs + 1e-12)))


def write_audit_csv(path: str | Path, metrics: dict[str, float]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted(metrics.keys())
    with target.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerow({k: float(metrics.get(k, 0.0)) for k in keys})
