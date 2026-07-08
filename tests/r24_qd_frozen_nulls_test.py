import numpy as np


def test_qd_window_dataset_roundtrip(tmp_path):
    from ha_ctse_process.r24_qd_dataset import QDWindowBatch, read_qd_window_shards, write_qd_window_shard

    batch = QDWindowBatch(
        action=np.ones((3, 4), dtype=np.float32),
        effect=np.ones((3, 5), dtype=np.float32) * 2,
        condition=np.ones((3, 6), dtype=np.float32) * 3,
        labels=np.asarray([0, 1, 2], dtype=np.int64),
        pre_action=np.zeros((3, 4), dtype=np.float32),
        pre_effect=np.zeros((3, 5), dtype=np.float32),
        pre_valid=np.asarray([1, 0, 1], dtype=np.float32),
        env_id=np.asarray([0, 0, 1], dtype=np.int64),
        agent_id=np.asarray([0, 1, 0], dtype=np.int64),
        duration_idx=np.asarray([1, 2, 1], dtype=np.int64),
        segment_length=np.asarray([30, 70, 30], dtype=np.int64),
        total_steps=np.asarray([160000, 160000, 320000], dtype=np.int64),
        update_idx=np.asarray([5, 5, 10], dtype=np.int64),
    )
    write_qd_window_shard(tmp_path / "update_000005.npz", batch)

    loaded = read_qd_window_shards(tmp_path)

    assert loaded.action.shape == (3, 4)
    assert loaded.effect.shape == (3, 5)
    assert loaded.condition.shape == (3, 6)
    assert loaded.labels.tolist() == [0, 1, 2]
    assert loaded.pre_valid.tolist() == [1.0, 0.0, 1.0]
    assert loaded.action.dtype == np.float32
    assert loaded.labels.dtype == np.int64


def test_qd_window_dataset_sample_is_seeded_and_schema_stable(tmp_path):
    from ha_ctse_process.r24_qd_dataset import QDWindowBatch, sample_qd_rows

    rows = 20
    batch = QDWindowBatch(
        action=np.arange(rows * 2, dtype=np.float32).reshape(rows, 2),
        effect=np.arange(rows * 3, dtype=np.float32).reshape(rows, 3),
        condition=np.ones((rows, 4), dtype=np.float32),
        labels=np.arange(rows, dtype=np.int64),
        pre_action=np.zeros((rows, 2), dtype=np.float32),
        pre_effect=np.zeros((rows, 3), dtype=np.float32),
        pre_valid=np.ones(rows, dtype=np.float32),
        env_id=np.arange(rows, dtype=np.int64),
        agent_id=np.zeros(rows, dtype=np.int64),
        duration_idx=np.zeros(rows, dtype=np.int64),
        segment_length=np.ones(rows, dtype=np.int64),
        total_steps=np.ones(rows, dtype=np.int64),
        update_idx=np.ones(rows, dtype=np.int64),
    )

    one = sample_qd_rows(batch, max_rows=7, seed=9)
    two = sample_qd_rows(batch, max_rows=7, seed=9)

    assert one.labels.tolist() == two.labels.tolist()
    assert one.action.shape == (7, 2)
    assert one.effect.shape == (7, 3)
    assert np.all(np.diff(one.labels) > 0)


def test_shuffle_within_singleton_groups_and_homogeneous_labels_do_not_fall_back_to_global_permutation():
    from scripts.analyze_r24_qd_frozen_nulls import _shuffle_within

    rng = np.random.default_rng(42)
    singleton_labels = np.array([0, 1, 2, 3, 4, 5], dtype=np.int64)
    singleton_groups = np.array([0, 1, 2, 3, 4, 5], dtype=np.int64)
    assert np.array_equal(_shuffle_within(singleton_labels, singleton_groups, rng), singleton_labels)

    homogeneous_labels = np.array([2, 2, 2, 2, 2], dtype=np.int64)
    homogeneous_groups = np.array([0, 0, 1, 1, 1], dtype=np.int64)
    assert np.array_equal(
        _shuffle_within(homogeneous_labels, homogeneous_groups, np.random.default_rng(7)),
        homogeneous_labels,
    )


def test_grouped_variants_preserve_group_label_multiset():
    from ha_ctse_process.r24_qd_dataset import QDWindowBatch
    from scripts.analyze_r24_qd_frozen_nulls import _variant_batch

    labels = np.array([0, 0, 1, 1, 2, 2, 3, 3], dtype=np.int64)
    batch = QDWindowBatch(
        action=np.zeros((8, 2), dtype=np.float32),
        effect=np.zeros((8, 3), dtype=np.float32),
        condition=np.zeros((8, 4), dtype=np.float32),
        labels=labels.copy(),
        pre_action=np.zeros((8, 2), dtype=np.float32),
        pre_effect=np.zeros((8, 3), dtype=np.float32),
        pre_valid=np.ones(8, dtype=np.float32),
        env_id=np.zeros(8, dtype=np.int64),
        agent_id=np.array([0, 0, 0, 1, 1, 2, 2, 2], dtype=np.int64),
        duration_idx=np.array([1, 1, 1, 2, 2, 3, 3, 3], dtype=np.int64),
        segment_length=np.ones(8, dtype=np.int64),
        total_steps=np.ones(8, dtype=np.int64),
        update_idx=np.ones(8, dtype=np.int64),
    )

    duration_batch = _variant_batch(batch, "duration_matched", seed=123, num_skills=4)
    agent_batch = _variant_batch(batch, "agent_matched", seed=456, num_skills=4)

    for group in np.unique(batch.duration_idx):
        mask = batch.duration_idx == group
        assert np.array_equal(np.sort(batch.labels[mask]), np.sort(duration_batch.labels[mask]))

    for group in np.unique(batch.agent_id):
        mask = batch.agent_id == group
        assert np.array_equal(np.sort(batch.labels[mask]), np.sort(agent_batch.labels[mask]))


def test_frozen_null_analyzer_real_labels_beat_shuffled_on_synthetic_data(tmp_path):
    from ha_ctse_process.r24_qd_dataset import QDWindowBatch, write_qd_window_shard
    from scripts.analyze_r24_qd_frozen_nulls import run_frozen_null_analysis

    rng = np.random.default_rng(123)
    labels = np.repeat(np.arange(4, dtype=np.int64), 64)
    action_means = rng.normal(size=(4, 6)).astype(np.float32)
    effect_means = rng.normal(size=(4, 8)).astype(np.float32)
    action = action_means[labels] + 0.1 * rng.normal(size=(labels.size, 6)).astype(np.float32)
    effect = effect_means[labels] + 0.1 * rng.normal(size=(labels.size, 8)).astype(np.float32)
    condition = rng.normal(size=(labels.size, 5)).astype(np.float32)
    batch = QDWindowBatch(
        action=action,
        effect=effect,
        condition=condition,
        labels=labels,
        pre_action=rng.normal(size=(labels.size, 6)).astype(np.float32),
        pre_effect=rng.normal(size=(labels.size, 8)).astype(np.float32),
        pre_valid=np.ones(labels.size, dtype=np.float32),
        env_id=np.zeros(labels.size, dtype=np.int64),
        agent_id=np.zeros(labels.size, dtype=np.int64),
        duration_idx=np.zeros(labels.size, dtype=np.int64),
        segment_length=np.ones(labels.size, dtype=np.int64),
        total_steps=np.ones(labels.size, dtype=np.int64),
        update_idx=np.ones(labels.size, dtype=np.int64),
    )
    write_qd_window_shard(tmp_path / "update_000001.npz", batch)

    result = run_frozen_null_analysis(tmp_path, tmp_path, num_skills=4, steps=80, seed=7)

    assert result["real"]["residual_gain"] > result["shuffled"]["residual_gain"] + 0.20
    assert (tmp_path / "r24_qd_frozen_nulls.json").exists()
    assert (tmp_path / "r24_qd_frozen_nulls.md").exists()
