"""Frozen low-actor capacity diagnostics for R27-G1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class CapacitySnapshotBatch:
    observation: np.ndarray
    actor_hidden: np.ndarray
    natural_skill: np.ndarray
    previous_skill: np.ndarray
    duration_idx: np.ndarray
    skill_age: np.ndarray
    episode_done_mask: np.ndarray
    reset_id: np.ndarray
    reset_seed: np.ndarray
    episode_id: np.ndarray
    env_id: np.ndarray
    agent_id: np.ndarray
    checkpoint_id: np.ndarray
    checkpoint_update: np.ndarray

    def take(self, indices: np.ndarray) -> "CapacitySnapshotBatch":
        idx = np.asarray(indices, dtype=np.int64)
        return CapacitySnapshotBatch(
            **{
                field: np.asarray(getattr(self, field))[idx]
                for field in self.__dataclass_fields__
            }
        )


@dataclass(frozen=True)
class ResetSplit:
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray
    train_reset_ids: tuple[int, ...]
    validation_reset_ids: tuple[int, ...]
    test_reset_ids: tuple[int, ...]


@dataclass(frozen=True)
class BootstrapInterval:
    mean: float
    lower: float
    upper: float


FLOAT_FIELDS = ("observation", "actor_hidden")
INT_FIELDS = (
    "natural_skill",
    "previous_skill",
    "duration_idx",
    "skill_age",
    "reset_id",
    "reset_seed",
    "episode_id",
    "env_id",
    "agent_id",
    "checkpoint_update",
)


def validate_capacity_snapshots(
    batch: CapacitySnapshotBatch,
) -> CapacitySnapshotBatch:
    arrays = {
        field: np.asarray(getattr(batch, field))
        for field in CapacitySnapshotBatch.__dataclass_fields__
    }
    rows = int(arrays["natural_skill"].reshape(-1).size)
    for field, values in arrays.items():
        if values.ndim == 0 or int(values.shape[0]) != rows:
            raise ValueError(f"{field} must have {rows} rows")
    for field in FLOAT_FIELDS:
        if not np.isfinite(arrays[field]).all():
            raise ValueError(f"{field} contains non-finite values")
    if arrays["observation"].ndim != 2 or arrays["actor_hidden"].ndim != 2:
        raise ValueError("observation and actor_hidden must be rank-2")

    values: dict[str, np.ndarray] = {}
    for field, array in arrays.items():
        if field in FLOAT_FIELDS:
            values[field] = np.asarray(array, dtype=np.float32)
        elif field in INT_FIELDS:
            values[field] = np.asarray(array, dtype=np.int64).reshape(-1)
        elif field == "episode_done_mask":
            values[field] = np.asarray(array, dtype=np.bool_).reshape(-1)
        else:
            values[field] = np.asarray(array, dtype=np.str_).reshape(-1)
    return CapacitySnapshotBatch(**values)


def write_capacity_snapshot_shard(
    path: Path, batch: CapacitySnapshotBatch
) -> None:
    validated = validate_capacity_snapshots(batch)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        **{
            field: getattr(validated, field)
            for field in CapacitySnapshotBatch.__dataclass_fields__
        },
    )


def read_capacity_snapshot_shards(root: Path) -> CapacitySnapshotBatch:
    paths = sorted(Path(root).glob("*.npz"))
    if not paths:
        raise FileNotFoundError(f"no capacity snapshot shards under {root}")

    fields = tuple(CapacitySnapshotBatch.__dataclass_fields__)
    chunks: dict[str, list[np.ndarray]] = {field: [] for field in fields}
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            missing = [field for field in fields if field not in data]
            if missing:
                raise ValueError(f"{path} missing fields: {missing}")
            shard = validate_capacity_snapshots(
                CapacitySnapshotBatch(**{field: data[field] for field in fields})
            )
            for field in fields:
                chunks[field].append(np.asarray(getattr(shard, field)))
    return validate_capacity_snapshots(
        CapacitySnapshotBatch(
            **{
                field: np.concatenate(chunks[field], axis=0)
                for field in fields
            }
        )
    )


def grouped_reset_split(reset_id: np.ndarray, seed: int) -> ResetSplit:
    ids = np.unique(np.asarray(reset_id, dtype=np.int64).reshape(-1))
    if ids.size < 5:
        raise ValueError("at least five reset groups are required")
    shuffled = ids.copy()
    np.random.default_rng(int(seed)).shuffle(shuffled)
    n_test = max(1, int(np.floor(0.2 * shuffled.size)))
    n_validation = max(1, int(np.floor(0.2 * shuffled.size)))
    test_ids = np.sort(shuffled[:n_test])
    validation_ids = np.sort(shuffled[n_test : n_test + n_validation])
    train_ids = np.sort(shuffled[n_test + n_validation :])
    reset_values = np.asarray(reset_id, dtype=np.int64).reshape(-1)
    return ResetSplit(
        train=np.flatnonzero(np.isin(reset_values, train_ids)),
        validation=np.flatnonzero(np.isin(reset_values, validation_ids)),
        test=np.flatnonzero(np.isin(reset_values, test_ids)),
        train_reset_ids=tuple(int(value) for value in train_ids),
        validation_reset_ids=tuple(int(value) for value in validation_ids),
        test_reset_ids=tuple(int(value) for value in test_ids),
    )


def cluster_bootstrap_difference(
    active: np.ndarray,
    control: np.ndarray,
    reset_ids: np.ndarray,
    *,
    reps: int,
    seed: int,
) -> BootstrapInterval:
    active_values = np.asarray(active, dtype=np.float64).reshape(-1)
    control_values = np.asarray(control, dtype=np.float64).reshape(-1)
    groups = np.asarray(reset_ids, dtype=np.int64).reshape(-1)
    if (
        active_values.shape != control_values.shape
        or active_values.shape != groups.shape
    ):
        raise ValueError("active, control, and reset_ids must be row-aligned")
    if int(reps) <= 0:
        raise ValueError("reps must be positive")
    unique_groups = np.unique(groups)
    if unique_groups.size < 5:
        raise ValueError("at least five reset groups are required for bootstrap")

    rng = np.random.default_rng(int(seed))
    estimates = np.empty(int(reps), dtype=np.float64)
    for index in range(int(reps)):
        sampled = rng.choice(
            unique_groups, size=unique_groups.size, replace=True
        )
        rows = np.concatenate(
            [np.flatnonzero(groups == group) for group in sampled]
        )
        estimates[index] = float(
            (active_values[rows] - control_values[rows]).mean()
        )
    return BootstrapInterval(
        mean=float((active_values - control_values).mean()),
        lower=float(np.quantile(estimates, 0.025)),
        upper=float(np.quantile(estimates, 0.975)),
    )
