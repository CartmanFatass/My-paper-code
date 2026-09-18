"""Demand sources: the fixture, the prepared cache, and the no-silent-fallback rule."""

from __future__ import annotations

import json

import numpy as np
import pytest

from envs.uav_service_restoration.config import SourceConfig, SyntheticFixtureConfig
from envs.uav_service_restoration.demand import (
    COMPLETION_MARKER,
    DemandDataError,
    EpisodeSamplingError,
    PreparedDatasetDemandSource,
    SyntheticFixtureDemandSource,
    build_demand_source,
    map_activity_to_demand_mbps,
    reference_scale_from_training,
)
from envs.uav_service_restoration.preprocess_milan import (
    load_preprocess_config,
    prepare_milan_dataset,
)


@pytest.fixture
def fixture_source(smoke_config) -> SyntheticFixtureDemandSource:
    return SyntheticFixtureDemandSource(smoke_config.source)


@pytest.fixture
def prepared_root(tmp_path, milan_sample_dir):
    config = load_preprocess_config(milan_sample_dir / "preprocess_small.json")
    root = tmp_path / "prepared"
    prepare_milan_dataset(
        [
            milan_sample_dir / "activity_2013-11-01.txt",
            milan_sample_dir / "activity_2013-11-02.txt",
        ],
        milan_sample_dir / "grid_small.geojson",
        config,
        root,
        is_real_activity_data=False,
        kind="synthetic_fixture_milan_shaped",
    )
    return root


def prepared_source(root, **overrides) -> PreparedDatasetDemandSource:
    source = SourceConfig(
        kind="prepared_dataset",
        demand_scale_mbps=overrides.pop("demand_scale_mbps", 20.0),
        dataset_root=str(root),
        split=overrides.pop("split", "train"),
        region_id="fixture",
        **overrides,
    )
    return PreparedDatasetDemandSource(source)


# --------------------------------------------------------------------------------------
# Mapping
# --------------------------------------------------------------------------------------


def test_reference_scale_uses_positive_observed_values_only():
    activity = np.array([[0.0, 1.0, 2.0], [0.0, 3.0, 100.0]])
    observed = np.array([[True, True, True], [True, True, False]])
    # 100 is unobserved and the zeros are excluded, so the pool is {1, 2, 3}.
    assert reference_scale_from_training(activity, observed, 1.0) == pytest.approx(3.0)


def test_reference_scale_refuses_an_all_zero_split():
    with pytest.raises(DemandDataError, match="no positive observed activity"):
        reference_scale_from_training(np.zeros((2, 2)), np.ones((2, 2), dtype=bool))


def test_mapping_is_linear_and_preserves_total_load_variation():
    activity = np.array([1.0, 2.0, 4.0])
    demand = map_activity_to_demand_mbps(activity, 10.0, 2.0)
    np.testing.assert_allclose(demand, [5.0, 10.0, 20.0])
    # Doubling every activity value doubles total demand: no per-slice renormalisation.
    doubled = map_activity_to_demand_mbps(activity * 2.0, 10.0, 2.0)
    assert doubled.sum() == pytest.approx(2.0 * demand.sum())


# --------------------------------------------------------------------------------------
# Synthetic fixture
# --------------------------------------------------------------------------------------


def test_fixture_declares_itself_non_real(fixture_source):
    metadata = fixture_source.metadata()
    assert metadata.kind == "synthetic_fixture"
    assert metadata.is_real_activity_data is False
    assert "NOT real data" in metadata.description


def test_fixture_is_byte_reproducible(smoke_config):
    first = SyntheticFixtureDemandSource(smoke_config.source)
    again = SyntheticFixtureDemandSource(smoke_config.source)
    assert first.metadata().dataset_hash == again.metadata().dataset_hash
    np.testing.assert_array_equal(first.cell_positions_m(), again.cell_positions_m())


def test_fixture_positions_are_a_fixed_grid(fixture_source, smoke_config):
    positions = fixture_source.cell_positions_m()
    fixture = smoke_config.source.synthetic_fixture
    rows, cols = fixture.grid_shape
    assert positions.shape == (rows * cols, 2)
    # Row-major ordering, spacing exactly as configured; identity never re-sorts.
    assert positions[1, 0] - positions[0, 0] == pytest.approx(fixture.cell_spacing_m)
    assert positions[cols, 1] - positions[0, 1] == pytest.approx(fixture.cell_spacing_m)


def test_fixture_reference_scale_comes_from_the_training_half_only(smoke_config):
    source = SyntheticFixtureDemandSource(smoke_config.source)
    first, last = source.split_interval_range("train")
    assert first == 0
    assert last == smoke_config.source.synthetic_fixture.n_intervals // 2
    override = SourceConfig(
        **{**smoke_config.source.__dict__, "reference_scale_override": 7.0}
    )
    assert SyntheticFixtureDemandSource(override).reference_scale() == pytest.approx(7.0)


def test_fixture_splits_do_not_overlap(fixture_source):
    train = fixture_source.split_interval_range("train")
    test = fixture_source.split_interval_range("test")
    assert train[1] <= test[0]
    generator = np.random.default_rng(0)
    for _ in range(10):
        episode = fixture_source.sample_episode(
            "test", generator, duration_s=600.0, history_intervals=1
        )
        # Even the history of a test episode stays out of the training half.
        assert episode.history_start_utc_ms >= int(
            fixture_source._timestamps[test[0]]  # noqa: SLF001
        )


def test_fixture_refuses_an_unknown_split(fixture_source):
    with pytest.raises(EpisodeSamplingError, match="unknown split"):
        fixture_source.sample_episode("holdout", np.random.default_rng(0))


def test_reading_outside_the_episode_raises_rather_than_wrapping(fixture_source):
    episode = fixture_source.sample_episode(
        "train", np.random.default_rng(0), duration_s=600.0, history_intervals=1
    )
    with pytest.raises(DemandDataError, match="outside episode"):
        fixture_source.read_interval(episode, episode.end_utc_ms + 1)
    with pytest.raises(DemandDataError, match="outside episode"):
        fixture_source.read_interval(episode, episode.history_start_utc_ms - 1)


def test_unobserved_cells_are_masked_not_zeroed(smoke_config):
    document = dict(smoke_config.source.__dict__)
    document["synthetic_fixture"] = SyntheticFixtureConfig(
        **{**smoke_config.source.synthetic_fixture.__dict__, "unobserved_cells": (4,)}
    )
    document["require_fully_observed_episodes"] = False
    source = SyntheticFixtureDemandSource(SourceConfig(**document))
    episode = source.sample_episode(
        "train", np.random.default_rng(0), duration_s=600.0, history_intervals=1
    )
    frame = source.read_interval(episode, episode.start_utc_ms)
    assert frame.observed_mask[4] is np.False_ or frame.observed_mask[4] == False  # noqa: E712
    assert frame.observed_mask[3]
    # The masked entry carries no usable number; the mask is the fact, not the zero.
    assert frame.demand_mbps[4] == 0.0
    assert frame.demand_mbps[3] > 0.0


def _holed_fixture(smoke_config, holes, *, require, **extra):
    document = dict(smoke_config.source.__dict__)
    document["synthetic_fixture"] = SyntheticFixtureConfig(
        **{
            **smoke_config.source.synthetic_fixture.__dict__,
            "unobserved_intervals": tuple(holes),
        }
    )
    document["require_fully_observed_episodes"] = require
    document.update(extra)
    return SyntheticFixtureDemandSource(SourceConfig(**document))


def test_strict_episodes_avoid_windows_containing_an_absence(smoke_config):
    holes = (1, 4, 7)
    strict = _holed_fixture(smoke_config, holes, require=True)
    lenient = _holed_fixture(smoke_config, holes, require=False)
    timestamps = strict._timestamps  # noqa: SLF001
    holed_starts = {int(timestamps[index]) for index in holes}

    strict_starts = set()
    lenient_starts = set()
    for seed in range(40):
        strict_starts.add(
            strict.sample_episode(
                "train", np.random.default_rng(seed), duration_s=600.0, history_intervals=1
            ).start_utc_ms
        )
        lenient_starts.add(
            lenient.sample_episode(
                "train", np.random.default_rng(seed), duration_s=600.0, history_intervals=1
            ).start_utc_ms
        )
    assert not (strict_starts & holed_starts)
    assert lenient_starts & holed_starts
    assert strict_starts < lenient_starts


def test_fully_unobserved_training_split_refuses_to_fit_a_scale(smoke_config):
    with pytest.raises(DemandDataError, match="no positive observed activity"):
        _holed_fixture(smoke_config, tuple(range(12)), require=True)
    # An explicit override is still honoured, because it is not fitted from the data.
    source = _holed_fixture(
        smoke_config, tuple(range(12)), require=False, reference_scale_override=5.0
    )
    assert source.reference_scale() == pytest.approx(5.0)
    with pytest.raises(EpisodeSamplingError, match="fully observed"):
        _holed_fixture(
            smoke_config, tuple(range(12)), require=True, reference_scale_override=5.0
        ).sample_episode("train", np.random.default_rng(0), duration_s=600.0)


def test_episode_descriptor_binds_the_dataset_hash(fixture_source, smoke_config):
    episode = fixture_source.sample_episode(
        "train", np.random.default_rng(0), duration_s=600.0, history_intervals=1
    )
    other = SyntheticFixtureDemandSource(
        SourceConfig(
            **{
                **smoke_config.source.__dict__,
                "synthetic_fixture": SyntheticFixtureConfig(
                    **{**smoke_config.source.synthetic_fixture.__dict__, "base_activity": 41.0}
                ),
            }
        )
    )
    with pytest.raises(DemandDataError, match="different dataset content hash"):
        other.read_interval(episode, episode.start_utc_ms)


# --------------------------------------------------------------------------------------
# Prepared cache and the no-fallback rule
# --------------------------------------------------------------------------------------


def test_missing_dataset_root_raises_and_never_falls_back(tmp_path):
    source = SourceConfig(
        kind="milan_activity",
        demand_scale_mbps=20.0,
        dataset_root=str(tmp_path / "absent"),
    )
    with pytest.raises(DemandDataError, match="dataset_root does not exist"):
        build_demand_source(source)


def test_incomplete_cache_without_the_marker_is_refused(prepared_root):
    (prepared_root / COMPLETION_MARKER).unlink()
    with pytest.raises(DemandDataError, match="incomplete"):
        prepared_source(prepared_root)


def test_modified_array_fails_the_declared_hash(prepared_root):
    activity = np.load(prepared_root / "activity.npy")
    activity[0, 0] += 1.0
    np.save(prepared_root / "activity.npy", activity, allow_pickle=False)
    with pytest.raises(DemandDataError, match="hash mismatch"):
        prepared_source(prepared_root)


def test_real_data_kind_over_a_non_real_cache_is_refused(prepared_root):
    source = SourceConfig(
        kind="milan_activity", demand_scale_mbps=20.0, dataset_root=str(prepared_root)
    )
    with pytest.raises(DemandDataError, match="never presented as real"):
        PreparedDatasetDemandSource(source)


def test_prepared_source_reads_the_expected_values(prepared_root):
    source = prepared_source(prepared_root)
    activity = np.load(prepared_root / "activity.npy")
    episode = source.sample_episode(
        "train", np.random.default_rng(0), duration_s=600.0, history_intervals=1
    )
    frame = source.read_interval(episode, episode.start_utc_ms)
    index = int(
        np.searchsorted(
            np.load(prepared_root / "timestamps_utc_ms.npy"), episode.start_utc_ms, "right"
        )
        - 1
    )
    expected = map_activity_to_demand_mbps(
        activity[index], 20.0, source.reference_scale()
    )
    np.testing.assert_allclose(frame.demand_mbps, expected)


def test_prepared_splits_select_disjoint_intervals(prepared_root):
    source = prepared_source(prepared_root)
    train = source.split_interval_indices("train")
    test = source.split_interval_indices("test")
    assert train.size and test.size
    assert not set(train.tolist()) & set(test.tolist())


def test_prepared_episodes_do_not_straddle_a_split_boundary(prepared_root):
    source = prepared_source(prepared_root, split="test", require_fully_observed_episodes=False)
    timestamps = np.load(prepared_root / "timestamps_utc_ms.npy")
    test_indices = set(source.split_interval_indices("test").tolist())
    generator = np.random.default_rng(3)
    for _ in range(15):
        episode = source.sample_episode(
            "test", generator, duration_s=1200.0, history_intervals=1
        )
        covered = np.flatnonzero(
            (timestamps >= episode.history_start_utc_ms) & (timestamps < episode.end_utc_ms)
        )
        assert set(covered.tolist()) <= test_indices


def test_split_overlap_in_the_cache_is_refused(prepared_root):
    payload = json.loads((prepared_root / "splits.json").read_text(encoding="utf-8"))
    payload["splits"]["validation"] = payload["splits"]["train"]
    (prepared_root / "splits.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(DemandDataError, match="must not overlap"):
        prepared_source(prepared_root)


def test_unknown_split_is_refused(prepared_root):
    source = prepared_source(prepared_root)
    with pytest.raises(EpisodeSamplingError, match="unknown split"):
        source.split_interval_indices("holdout")


def test_fully_observed_requirement_excludes_the_holed_window(prepared_root):
    strict = prepared_source(
        prepared_root, split="test", require_fully_observed_episodes=True
    )
    lenient = prepared_source(
        prepared_root, split="test", require_fully_observed_episodes=False
    )
    observed = np.load(prepared_root / "observed_mask.npy")
    assert not observed.all(), "the fixture is supposed to contain absences"
    strict_starts = {
        strict.sample_episode(
            "test", np.random.default_rng(seed), duration_s=600.0, history_intervals=1
        ).start_utc_ms
        for seed in range(20)
    }
    lenient_starts = {
        lenient.sample_episode(
            "test", np.random.default_rng(seed), duration_s=600.0, history_intervals=1
        ).start_utc_ms
        for seed in range(20)
    }
    assert strict_starts < lenient_starts


def test_cache_arrays_are_memory_mapped_not_re_parsed(prepared_root):
    source = prepared_source(prepared_root)
    assert isinstance(source._arrays.activity, np.memmap)  # noqa: SLF001


def test_writing_over_an_existing_cache_is_refused(prepared_root, milan_sample_dir):
    from envs.uav_service_restoration.preprocess_milan import PreprocessError

    config = load_preprocess_config(milan_sample_dir / "preprocess_small.json")
    with pytest.raises(PreprocessError, match="already exists"):
        prepare_milan_dataset(
            [milan_sample_dir / "activity_2013-11-01.txt"],
            milan_sample_dir / "grid_small.geojson",
            config,
            prepared_root,
            is_real_activity_data=False,
        )
