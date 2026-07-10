from pathlib import Path

import numpy as np
import pytest

from ha_ctse_process.r26_g1_dataset import (
    G1WindowBatch,
    build_prior_context,
    grouped_reset_split,
    read_g1_window_shards,
    window_summary,
    write_g1_window_shard,
)


def make_batch(rows: int = 12) -> G1WindowBatch:
    labels = np.arange(rows, dtype=np.int64) % 3
    resets = np.repeat(np.arange(6, dtype=np.int64), 2)
    return G1WindowBatch(
        label=labels,
        post_action=np.arange(rows * 8, dtype=np.float32).reshape(rows, 8),
        post_effect=np.arange(rows * 12, dtype=np.float32).reshape(rows, 12),
        pre_action=np.zeros((rows, 8), dtype=np.float32),
        pre_effect=np.zeros((rows, 12), dtype=np.float32),
        pre_valid=np.ones(rows, dtype=np.float32),
        prior_context=np.arange(rows * 10, dtype=np.float32).reshape(rows, 10),
        reset_id=resets,
        reset_seed=100 + resets,
        episode_id=resets,
        env_id=np.zeros(rows, dtype=np.int64),
        agent_id=np.arange(rows, dtype=np.int64) % 6,
        duration_idx=np.arange(rows, dtype=np.int64) % 4,
        segment_length=np.full(rows, 10, dtype=np.int64),
        checkpoint_id=np.full(rows, "arm0_update25"),
        checkpoint_update=np.full(rows, 25, dtype=np.int64),
    )


def test_round_trip_preserves_every_field(tmp_path: Path):
    batch = make_batch()
    write_g1_window_shard(tmp_path / "reset_000.npz", batch)
    restored = read_g1_window_shards(tmp_path)
    for field in G1WindowBatch.__dataclass_fields__:
        assert np.array_equal(getattr(restored, field), getattr(batch, field))


def test_grouped_split_never_leaks_reset_ids():
    split = grouped_reset_split(make_batch(), seed=26011)
    train = set(split.train_reset_ids.tolist())
    valid = set(split.validation_reset_ids.tolist())
    test = set(split.test_reset_ids.tolist())
    assert train.isdisjoint(valid)
    assert train.isdisjoint(test)
    assert valid.isdisjoint(test)
    assert train | valid | test == set(range(6))


def test_prior_context_has_no_current_focal_skill_argument():
    kwargs = dict(
        focal_agent=1,
        n_agents=3,
        duration_idx=2,
        n_durations=4,
        previous_skill=0,
        n_skills=3,
        previous_age=4,
        team_code=1,
        num_team_codes=2,
        teammate_roster=np.asarray([2, 1, 0], dtype=np.int64),
        assignment_obs=np.asarray([0.1, 0.2], dtype=np.float32),
        omega=np.asarray([0.4, 0.6], dtype=np.float32),
        pre_action=np.asarray([0.0, 1.0], dtype=np.float32),
        pre_effect=np.asarray([1.0, 0.0], dtype=np.float32),
        pre_valid=True,
    )
    context = build_prior_context(**kwargs)
    changed_focal_slot = build_prior_context(
        **{**kwargs, "teammate_roster": np.asarray([2, 0, 0], dtype=np.int64)}
    )
    assert np.isfinite(context).all()
    assert context.ndim == 1
    assert np.array_equal(context, changed_focal_slot)


def test_window_summary_uses_delta_mean_std_and_span():
    rows = np.asarray([[1.0, 2.0], [2.0, 4.0], [4.0, 8.0]], dtype=np.float32)
    summary = window_summary(rows, feature_dim=2)
    assert summary.shape == (8,)
    assert np.allclose(summary[:2], [3.0, 6.0])


def test_writer_rejects_mismatched_row_count(tmp_path: Path):
    batch = make_batch()
    broken = G1WindowBatch(**{**batch.__dict__, "agent_id": np.zeros(3, dtype=np.int64)})
    with pytest.raises(ValueError, match="agent_id"):
        write_g1_window_shard(tmp_path / "broken.npz", broken)
