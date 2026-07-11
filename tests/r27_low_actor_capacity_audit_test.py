from __future__ import annotations

import numpy as np
import pytest

from ha_ctse_process.low_actor_capacity_audit import (
    CapacitySnapshotBatch,
    cluster_bootstrap_difference,
    grouped_reset_split,
    read_capacity_snapshot_shards,
    write_capacity_snapshot_shard,
)


def make_snapshots(
    *, resets: int = 10, rows_per_reset: int = 4
) -> CapacitySnapshotBatch:
    reset_id = np.repeat(np.arange(resets, dtype=np.int64), rows_per_reset)
    rows = int(reset_id.size)
    return CapacitySnapshotBatch(
        observation=np.arange(rows * 6, dtype=np.float32).reshape(rows, 6) / 10.0,
        actor_hidden=np.arange(rows * 8, dtype=np.float32).reshape(rows, 8) / 20.0,
        natural_skill=np.arange(rows, dtype=np.int64) % 4,
        previous_skill=(np.arange(rows, dtype=np.int64) + 1) % 4,
        duration_idx=np.arange(rows, dtype=np.int64) % 4,
        skill_age=np.arange(rows, dtype=np.int64) % 9,
        episode_done_mask=np.zeros(rows, dtype=np.bool_),
        reset_id=reset_id,
        reset_seed=27000 + reset_id,
        episode_id=reset_id.copy(),
        env_id=np.zeros(rows, dtype=np.int64),
        agent_id=np.arange(rows, dtype=np.int64) % 6,
        checkpoint_id=np.full(rows, "arm0_final"),
        checkpoint_update=np.full(rows, 32, dtype=np.int64),
    )


def test_snapshot_shard_roundtrip_preserves_every_field(tmp_path):
    expected = make_snapshots()
    write_capacity_snapshot_shard(tmp_path / "reset_0000.npz", expected)

    actual = read_capacity_snapshot_shards(tmp_path)

    for field in CapacitySnapshotBatch.__dataclass_fields__:
        np.testing.assert_array_equal(getattr(actual, field), getattr(expected, field))


def test_grouped_split_is_deterministic_and_never_leaks_resets():
    batch = make_snapshots(resets=10)

    first = grouped_reset_split(batch.reset_id, seed=27011)
    second = grouped_reset_split(batch.reset_id, seed=27011)

    for field in ("train", "validation", "test"):
        np.testing.assert_array_equal(getattr(first, field), getattr(second, field))
    assert first.train_reset_ids == second.train_reset_ids
    assert first.validation_reset_ids == second.validation_reset_ids
    assert first.test_reset_ids == second.test_reset_ids
    assert set(first.train_reset_ids).isdisjoint(first.validation_reset_ids)
    assert set(first.train_reset_ids).isdisjoint(first.test_reset_ids)
    assert set(first.validation_reset_ids).isdisjoint(first.test_reset_ids)
    assert len(first.train_reset_ids) == 6
    assert len(first.validation_reset_ids) == 2
    assert len(first.test_reset_ids) == 2


def test_reset_cluster_bootstrap_is_deterministic_and_positive():
    reset_ids = np.repeat(np.arange(8, dtype=np.int64), 4)
    active = np.linspace(0.2, 0.8, reset_ids.size)
    inactive = active - 0.1

    first = cluster_bootstrap_difference(
        active, inactive, reset_ids, reps=500, seed=27012
    )
    second = cluster_bootstrap_difference(
        active, inactive, reset_ids, reps=500, seed=27012
    )

    assert first == second
    assert first.lower > 0.0


def test_snapshot_rejects_nonfinite_hidden_state(tmp_path):
    batch = make_snapshots()
    batch.actor_hidden[3, 2] = np.nan

    with pytest.raises(ValueError, match="actor_hidden contains non-finite"):
        write_capacity_snapshot_shard(tmp_path / "bad.npz", batch)
