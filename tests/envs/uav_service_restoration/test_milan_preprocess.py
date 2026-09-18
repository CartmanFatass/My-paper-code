"""Milan ingestion: column mapping, units, country codes, duplicates, missingness, geography."""

from __future__ import annotations

import json

import numpy as np
import pytest

from envs.uav_service_restoration.preprocess_milan import (
    DEFAULT_UTM_ZONE,
    PreprocessConfig,
    PreprocessError,
    ingest_activity,
    inspect_raw_sample,
    load_preprocess_config,
    prepare_milan_dataset,
    read_milano_grid,
    rome_time_of_day_label,
    select_region,
    utc_date_label,
    utm_to_wgs84,
    utm_zone_central_meridian_deg,
    wgs84_to_utm,
)
from envs.uav_service_restoration.config import ConfigError

DAY1 = 1_383_264_000_000  # 2013-11-01T00:00:00Z
DAY2 = DAY1 + 86_400_000
INTERVAL = 600_000


@pytest.fixture
def preprocess_config(milan_sample_dir) -> PreprocessConfig:
    return load_preprocess_config(milan_sample_dir / "preprocess_small.json")


@pytest.fixture
def grid(milan_sample_dir):
    return read_milano_grid(milan_sample_dir / "grid_small.geojson")


def write_rows(path, rows):
    path.write_text("\n".join("\t".join(str(value) for value in row) for row in rows) + "\n",
                    encoding="utf-8")
    return path


def row(cell, timestamp, country, internet, n_columns=8):
    values = [cell, timestamp, country, 1.0, 1.0, 1.0, 1.0, internet]
    return values[:n_columns]


# --------------------------------------------------------------------------------------
# Projection
# --------------------------------------------------------------------------------------


def test_central_meridian_maps_to_the_false_easting_exactly():
    easting, _ = wgs84_to_utm(np.array([45.47]), np.array([utm_zone_central_meridian_deg(32)]), 32)
    assert float(easting[0]) == pytest.approx(500_000.0, abs=1e-6)
    assert utm_zone_central_meridian_deg(32) == pytest.approx(9.0)


def test_projection_round_trips_to_sub_millimetre():
    latitudes = np.array([45.40, 45.46, 45.52])
    longitudes = np.array([9.10, 9.19, 9.28])
    easting, northing = wgs84_to_utm(latitudes, longitudes, DEFAULT_UTM_ZONE)
    back_lat, back_lon = utm_to_wgs84(easting, northing, DEFAULT_UTM_ZONE)
    np.testing.assert_allclose(back_lat, latitudes, atol=1e-8)
    np.testing.assert_allclose(back_lon, longitudes, atol=1e-8)


def test_projected_distances_match_a_local_ellipsoidal_reference():
    """Metre distances are physical, not a constant times degrees."""

    latitude = 45.47
    # Local metres per degree on the WGS84 ellipsoid at this latitude.
    phi = np.deg2rad(latitude)
    a, f = 6378137.0, 1.0 / 298.257223563
    e2 = f * (2.0 - f)
    meridian = (
        a * (1.0 - e2) / (1.0 - e2 * np.sin(phi) ** 2) ** 1.5 * np.pi / 180.0
    )
    parallel = a / np.sqrt(1.0 - e2 * np.sin(phi) ** 2) * np.cos(phi) * np.pi / 180.0

    e0, n0 = wgs84_to_utm(np.array([latitude]), np.array([9.19]), 32)
    e1, n1 = wgs84_to_utm(np.array([latitude + 0.01]), np.array([9.19]), 32)
    e2_, n2 = wgs84_to_utm(np.array([latitude]), np.array([9.20]), 32)
    north_step = float(np.hypot(e1[0] - e0[0], n1[0] - n0[0]))
    east_step = float(np.hypot(e2_[0] - e0[0], n2[0] - n0[0]))
    assert north_step == pytest.approx(0.01 * meridian, rel=2e-3)
    assert east_step == pytest.approx(0.01 * parallel, rel=2e-3)


def test_projection_is_not_a_constant_scaling_of_degrees():
    """The same longitude step spans fewer metres further north."""

    step = 0.05
    low = wgs84_to_utm(np.array([45.0, 45.0]), np.array([9.19, 9.19 + step]), 32)
    high = wgs84_to_utm(np.array([60.0, 60.0]), np.array([9.19, 9.19 + step]), 32)
    low_span = float(np.hypot(low[0][1] - low[0][0], low[1][1] - low[1][0]))
    high_span = float(np.hypot(high[0][1] - high[0][0], high[1][1] - high[1][0]))
    assert high_span < 0.8 * low_span


def test_grid_reader_projects_and_orders_by_cell_id(grid):
    assert grid.cell_ids.tolist() == [1, 2, 3, 4]
    assert np.all(np.diff(grid.cell_ids) > 0)
    # Cell spacing in the fixture is 0.03 deg longitude and 0.02 deg latitude.
    east_pair = abs(grid.easting_m[1] - grid.easting_m[0])
    north_pair = abs(grid.northing_m[2] - grid.northing_m[0])
    assert east_pair == pytest.approx(2340.0, rel=0.02)
    assert north_pair == pytest.approx(2223.0, rel=0.02)


def test_grid_reader_refuses_an_unknown_crs(tmp_path, milan_sample_dir):
    document = json.loads((milan_sample_dir / "grid_small.geojson").read_text(encoding="utf-8"))
    document["crs"] = {"type": "name", "properties": {"name": "EPSG:3003"}}
    path = tmp_path / "projected_grid.geojson"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(PreprocessError, match="CRS"):
        read_milano_grid(path)


def test_grid_reader_refuses_coordinates_that_are_already_metres(tmp_path, milan_sample_dir):
    document = json.loads((milan_sample_dir / "grid_small.geojson").read_text(encoding="utf-8"))
    for feature in document["features"]:
        feature["geometry"]["coordinates"] = [
            [[point[0] * 100000.0, point[1] * 100000.0] for point in ring]
            for ring in feature["geometry"]["coordinates"]
        ]
    path = tmp_path / "metres_grid.geojson"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(PreprocessError, match="latitude/longitude"):
        read_milano_grid(path)


def test_region_selection_records_its_rule(grid, preprocess_config):
    indices, record = select_region(grid, preprocess_config.region)
    assert indices.size == 4
    assert record["rule"] == "latlon_bbox"
    assert "not chosen from test-set results" in record["selection_basis"]


def test_region_selection_refuses_an_empty_or_oversized_box(grid, preprocess_config):
    from envs.uav_service_restoration.preprocess_milan import RegionSelection

    empty = RegionSelection(min_lat_deg=10.0, max_lat_deg=11.0, min_lon_deg=10.0, max_lon_deg=11.0)
    with pytest.raises(PreprocessError, match="selects no grid cell"):
        select_region(grid, empty)
    tight = RegionSelection(
        min_lat_deg=preprocess_config.region.min_lat_deg,
        max_lat_deg=preprocess_config.region.max_lat_deg,
        min_lon_deg=preprocess_config.region.min_lon_deg,
        max_lon_deg=preprocess_config.region.max_lon_deg,
        max_cells=2,
    )
    with pytest.raises(PreprocessError, match="max_cells"):
        select_region(grid, tight)


# --------------------------------------------------------------------------------------
# Row-level validation
# --------------------------------------------------------------------------------------


def test_wrong_column_count_is_rejected(tmp_path, grid, preprocess_config):
    path = write_rows(tmp_path / "short.txt", [row(1, DAY1, 39, 5.0, n_columns=6)])
    with pytest.raises(PreprocessError, match="columns, expected"):
        ingest_activity([path], grid, preprocess_config)


def test_negative_activity_is_rejected(tmp_path, grid, preprocess_config):
    path = write_rows(tmp_path / "negative.txt", [row(1, DAY1, 39, -1.0)])
    with pytest.raises(PreprocessError, match="negative"):
        ingest_activity([path], grid, preprocess_config)


def test_non_numeric_activity_is_rejected(tmp_path, grid, preprocess_config):
    path = write_rows(tmp_path / "text.txt", [row(1, DAY1, 39, "n/a")])
    with pytest.raises(PreprocessError, match="non-numeric"):
        ingest_activity([path], grid, preprocess_config)


def test_nan_activity_is_rejected(tmp_path, grid, preprocess_config):
    path = write_rows(tmp_path / "nan.txt", [row(1, DAY1, 39, "nan")])
    with pytest.raises(PreprocessError, match="not finite"):
        ingest_activity([path], grid, preprocess_config)


def test_absurd_activity_is_rejected_not_clipped(tmp_path, grid, preprocess_config):
    path = write_rows(tmp_path / "huge.txt", [row(1, DAY1, 39, 1e12)])
    with pytest.raises(PreprocessError, match="max_activity_value"):
        ingest_activity([path], grid, preprocess_config)


def test_timestamps_in_seconds_are_caught_by_the_alignment_check(tmp_path, grid, preprocess_config):
    seconds = DAY1 // 1000 + 1  # not a multiple of 600000
    path = write_rows(tmp_path / "seconds.txt", [row(1, seconds, 39, 5.0)])
    with pytest.raises(PreprocessError, match="not in milliseconds"):
        ingest_activity([path], grid, preprocess_config)


def test_unknown_cell_ids_are_counted_not_fatal(tmp_path, grid, preprocess_config):
    path = write_rows(
        tmp_path / "mixed.txt",
        [row(1, DAY1, 39, 5.0), row(99_999, DAY1, 39, 5.0)],
    )
    result = ingest_activity([path], grid, preprocess_config)
    assert result["counters"].rows_outside_region == 1
    assert result["counters"].accepted_rows == 1


def test_rows_on_dates_outside_every_split_are_excluded(tmp_path, grid, preprocess_config):
    outside = DAY1 + 5 * 86_400_000
    path = write_rows(
        tmp_path / "dates.txt", [row(1, DAY1, 39, 5.0), row(1, outside, 39, 5.0)]
    )
    result = ingest_activity([path], grid, preprocess_config)
    assert result["counters"].rows_outside_splits == 1


# --------------------------------------------------------------------------------------
# Aggregation and duplication
# --------------------------------------------------------------------------------------


def test_country_code_rows_are_summed_for_the_same_cell_and_interval(
    tmp_path, grid, preprocess_config
):
    path = write_rows(
        tmp_path / "countries.txt",
        [row(1, DAY1, 39, 4.0), row(1, DAY1, 44, 6.0), row(1, DAY1, 1, 1.5)],
    )
    result = ingest_activity([path], grid, preprocess_config)
    assert result["activity"][0, 0] == pytest.approx(11.5)
    assert result["counters"].as_dict()["distinct_country_codes"] == 3
    # Three country rows are one spatial demand point, not three.
    assert result["activity"].shape[1] == 4


def test_duplicate_keys_are_rejected_by_default(tmp_path, grid, preprocess_config):
    path = write_rows(
        tmp_path / "dupe.txt", [row(1, DAY1, 39, 4.0), row(1, DAY1, 39, 4.0)]
    )
    with pytest.raises(PreprocessError, match="duplicate"):
        ingest_activity([path], grid, preprocess_config)


def test_declared_duplicate_rule_keeps_the_first_value(tmp_path, grid, preprocess_config):
    config = PreprocessConfig(
        **{**preprocess_config.__dict__, "duplicate_key_rule": "first_declared"}
    )
    path = write_rows(
        tmp_path / "dupe.txt", [row(1, DAY1, 39, 4.0), row(1, DAY1, 39, 100.0)]
    )
    result = ingest_activity([path], grid, config)
    assert result["activity"][0, 0] == pytest.approx(4.0)
    assert result["counters"].duplicate_keys == 1


def test_identical_input_files_are_refused_so_activity_never_doubles(
    tmp_path, grid, preprocess_config
):
    rows = [row(1, DAY1, 39, 4.0)]
    first = write_rows(tmp_path / "a.txt", rows)
    second = write_rows(tmp_path / "b.txt", rows)
    with pytest.raises(PreprocessError, match="same SHA-256"):
        ingest_activity([first, second], grid, preprocess_config)


# --------------------------------------------------------------------------------------
# Missingness
# --------------------------------------------------------------------------------------


def test_empty_field_stays_unknown_and_is_counted_separately(
    tmp_path, grid, preprocess_config
):
    path = write_rows(
        tmp_path / "blank.txt",
        [row(1, DAY1, 39, ""), row(2, DAY1, 39, 0.0), row(3, DAY1, 39, 7.0)],
    )
    result = ingest_activity([path], grid, preprocess_config)
    observed = result["observed_mask"][0]
    assert observed[0] == np.False_          # empty field: unknown
    assert observed[1] == np.True_           # explicit zero: observed and zero
    assert observed[2] == np.True_
    assert result["activity"][0, 1] == 0.0
    assert result["counters"].empty_field_values == 1
    assert result["counters"].explicit_zero_values == 1


def test_declared_zero_fill_is_possible_but_must_be_chosen(tmp_path, grid, preprocess_config):
    config = PreprocessConfig(
        **{**preprocess_config.__dict__, "missing_value_policy": "zero_fill_declared"}
    )
    path = write_rows(tmp_path / "blank.txt", [row(1, DAY1, 39, ""), row(2, DAY1, 39, 3.0)])
    result = ingest_activity([path], grid, config)
    assert result["observed_mask"][0, 0] == np.True_
    assert result["activity"][0, 0] == 0.0


def test_absent_rows_are_recorded_as_unobserved(tmp_path, grid, preprocess_config):
    path = write_rows(tmp_path / "partial.txt", [row(1, DAY1, 39, 5.0)])
    result = ingest_activity([path], grid, preprocess_config)
    assert result["observed_mask"][0].tolist() == [True, False, False, False]
    assert result["missing_rows"] == 3


def test_missing_intervals_are_counted_per_utc_date(tmp_path, grid, preprocess_config):
    path = write_rows(
        tmp_path / "two_intervals.txt",
        [row(1, DAY1, 39, 5.0), row(1, DAY1 + INTERVAL, 39, 6.0)],
    )
    result = ingest_activity([path], grid, preprocess_config)
    # One date is touched; a 10-minute grid has 144 interval starts per day.
    assert len(result["missing_intervals_utc_ms"]) == 144 - 2


def test_no_usable_row_is_a_clear_error(tmp_path, grid, preprocess_config):
    path = write_rows(tmp_path / "elsewhere.txt", [row(99_999, DAY1, 39, 5.0)])
    with pytest.raises(PreprocessError, match="no row fell inside"):
        ingest_activity([path], grid, preprocess_config)


# --------------------------------------------------------------------------------------
# Time axis
# --------------------------------------------------------------------------------------


def test_dates_come_from_utc_and_labels_from_rome():
    assert utc_date_label(DAY1) == "2013-11-01"
    # 00:00 UTC on 1 November is 01:00 CET in Rome; the machine's timezone is irrelevant.
    assert rome_time_of_day_label(DAY1).endswith("01:00 CET")


def test_config_split_dates_must_not_overlap(preprocess_config):
    with pytest.raises(ConfigError, match="overlap"):
        PreprocessConfig(
            **{
                **preprocess_config.__dict__,
                "train_dates": ("2013-11-01",),
                "test_dates": ("2013-11-01",),
            }
        ).validate()


def test_config_requires_training_dates(preprocess_config):
    with pytest.raises(ConfigError, match="train_dates"):
        PreprocessConfig(**{**preprocess_config.__dict__, "train_dates": ()}).validate()


def test_config_refuses_summed_activity(preprocess_config):
    with pytest.raises(ConfigError, match="never summed"):
        PreprocessConfig(
            **{**preprocess_config.__dict__, "activity_field": "all_activity"}
        ).validate()


def test_column_mapping_collision_is_rejected():
    from envs.uav_service_restoration.preprocess_milan import ColumnMapping

    with pytest.raises(ConfigError, match="same column"):
        ColumnMapping(square_id=0, time_interval_ms=0).validate("columns")
    with pytest.raises(ConfigError, match="outside n_columns"):
        ColumnMapping(internet_activity=99).validate("columns")


# --------------------------------------------------------------------------------------
# Full preparation
# --------------------------------------------------------------------------------------


def test_prepared_cache_records_provenance_and_fits_scale_on_training_only(
    tmp_path, milan_sample_dir, preprocess_config
):
    root = tmp_path / "prepared"
    metadata = prepare_milan_dataset(
        [
            milan_sample_dir / "activity_2013-11-01.txt",
            milan_sample_dir / "activity_2013-11-02.txt",
        ],
        milan_sample_dir / "grid_small.geojson",
        preprocess_config,
        root,
        is_real_activity_data=False,
        kind="synthetic_fixture_milan_shaped",
    )
    for key in (
        "raw_column_mapping",
        "aggregation_rule",
        "missing_data_policy",
        "region_selection_rule",
        "crs",
        "activity_reference_scale",
        "reference_scale_rule",
        "content_sha256",
        "file_sha256",
        "raw_file_sha256",
        "license_note",
        "source_url",
        "spatial_discretization",
    ):
        assert key in metadata, key
    assert metadata["is_real_activity_data"] is False
    assert "training dates only" in metadata["reference_scale_rule"]

    activity = np.load(root / "activity.npy")
    observed = np.load(root / "observed_mask.npy")
    timestamps = np.load(root / "timestamps_utc_ms.npy")
    train = np.asarray([utc_date_label(int(value)) == "2013-11-01" for value in timestamps])
    # The fitted scale must be reproducible from the training rows alone.
    from envs.uav_service_restoration.demand import reference_scale_from_training

    assert metadata["activity_reference_scale"] == pytest.approx(
        reference_scale_from_training(
            activity[train], observed[train], preprocess_config.reference_scale_quantile
        )
    )
    # It must differ from a scale fitted on everything, or the test proves nothing.
    assert metadata["activity_reference_scale"] != pytest.approx(
        reference_scale_from_training(
            activity, observed, preprocess_config.reference_scale_quantile
        )
    )


def test_quality_report_separates_the_kinds_of_absence(
    tmp_path, milan_sample_dir, preprocess_config
):
    root = tmp_path / "prepared"
    prepare_milan_dataset(
        [
            milan_sample_dir / "activity_2013-11-01.txt",
            milan_sample_dir / "activity_2013-11-02.txt",
        ],
        milan_sample_dir / "grid_small.geojson",
        preprocess_config,
        root,
        is_real_activity_data=False,
        kind="synthetic_fixture_milan_shaped",
    )
    report = json.loads((root / "quality_report.json").read_text(encoding="utf-8"))
    counters = report["counters"]
    # The fixture holds one blanked cell-interval (two country rows) and one absent row.
    assert counters["empty_field_values"] == 2
    assert report["missing_rows"] == 2
    assert counters["duplicate_keys"] == 0
    assert counters["files_read"] == 2
    assert report["n_missing_intervals"] == 2 * (144 - 6)
    assert "historical_period_note" in report
    assert report["observed_fraction"] < 1.0


def test_inspect_reports_what_the_file_actually_contains(milan_sample_dir, preprocess_config):
    report = inspect_raw_sample(
        milan_sample_dir / "activity_2013-11-01.txt", preprocess_config
    )
    assert report["column_count_matches_declared"] is True
    assert report["distinct_country_codes"] == 2
    assert report["timestamps_aligned_to_interval"] is True
    assert report["timestamp_min_utc"] == "2013-11-01"
    assert "not Mbps" in report["warning"]
