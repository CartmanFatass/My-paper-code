"""Frozen q_d behavior-window dataset utilities for R24 diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class QDWindowBatch:
    action: np.ndarray
    effect: np.ndarray
    condition: np.ndarray
    labels: np.ndarray
    pre_action: np.ndarray
    pre_effect: np.ndarray
    pre_valid: np.ndarray
    env_id: np.ndarray
    agent_id: np.ndarray
    duration_idx: np.ndarray
    segment_length: np.ndarray
    total_steps: np.ndarray
    update_idx: np.ndarray


FIELDS = tuple(QDWindowBatch.__dataclass_fields__.keys())
FEATURE_FIELDS = ("action", "effect", "condition", "pre_action", "pre_effect", "pre_valid")
INT_FIELDS = ("labels", "env_id", "agent_id", "duration_idx", "segment_length", "total_steps", "update_idx")


def _as_array(value, dtype: np.dtype) -> np.ndarray:
    return np.asarray(value, dtype=dtype)


def _validate(batch: QDWindowBatch) -> QDWindowBatch:
    arrays = {field: np.asarray(getattr(batch, field)) for field in FIELDS}
    n = int(arrays["labels"].reshape(-1).shape[0])
    for field, array in arrays.items():
        if array.shape[0] != n:
            raise ValueError(f"{field} has {array.shape[0]} rows, expected {n}")
    return QDWindowBatch(
        action=_as_array(batch.action, np.float32),
        effect=_as_array(batch.effect, np.float32),
        condition=_as_array(batch.condition, np.float32),
        labels=_as_array(batch.labels, np.int64).reshape(-1),
        pre_action=_as_array(batch.pre_action, np.float32),
        pre_effect=_as_array(batch.pre_effect, np.float32),
        pre_valid=_as_array(batch.pre_valid, np.float32).reshape(-1),
        env_id=_as_array(batch.env_id, np.int64).reshape(-1),
        agent_id=_as_array(batch.agent_id, np.int64).reshape(-1),
        duration_idx=_as_array(batch.duration_idx, np.int64).reshape(-1),
        segment_length=_as_array(batch.segment_length, np.int64).reshape(-1),
        total_steps=_as_array(batch.total_steps, np.int64).reshape(-1),
        update_idx=_as_array(batch.update_idx, np.int64).reshape(-1),
    )


def write_qd_window_shard(path: Path, batch: QDWindowBatch) -> None:
    batch = _validate(batch)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **{field: getattr(batch, field) for field in FIELDS})


def read_qd_window_shards(root: Path) -> QDWindowBatch:
    root = Path(root)
    paths = sorted(root.glob("*.npz"))
    if not paths:
        raise FileNotFoundError(f"no q_d window shards found under {root}")
    chunks = {field: [] for field in FIELDS}
    for path in paths:
        with np.load(path) as data:
            missing = [field for field in FIELDS if field not in data]
            if missing:
                raise ValueError(f"{path} missing fields: {missing}")
            for field in FIELDS:
                chunks[field].append(np.asarray(data[field]))
    return _validate(QDWindowBatch(**{field: np.concatenate(chunks[field], axis=0) for field in FIELDS}))


def sample_qd_rows(batch: QDWindowBatch, max_rows: int, seed: int) -> QDWindowBatch:
    batch = _validate(batch)
    n = int(batch.labels.shape[0])
    if max_rows <= 0 or n <= max_rows:
        return batch
    rng = np.random.default_rng(int(seed))
    idx = np.sort(rng.choice(n, size=int(max_rows), replace=False))
    return QDWindowBatch(**{field: getattr(batch, field)[idx] for field in FIELDS})
