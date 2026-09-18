"""Dataset report tests: missing stays missing, and nothing is substituted for real data.

The prepared-cache fixtures are written by the repository's own preprocessing writer
(``envs.uav_service_restoration.preprocess_milan.prepare_milan_dataset``) over the committed
Milan-shaped sample, so the tests exercise the real artifact layout rather than a hand-rolled
imitation of it. Everything generated goes under ``tmp_path``; the committed sample is only
ever read.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

# See the note in ``test_readers.py``: ``tests/tools/`` shadows the checkout's ``tools``
# namespace package, so the checkout root has to come first on ``sys.path``.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_TESTS_TOOLS = str(Path(__file__).resolve().parents[1])
if str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT))
for _name in [n for n in list(sys.modules) if n == "tools" or n.startswith("tools.")]:
    _origin = getattr(sys.modules[_name], "__file__", None)
    if _origin and _origin.startswith(_TESTS_TOOLS):
        del sys.modules[_name]

from tools.research_support.cli import CliError  # noqa: E402
from tools.research_support.dataset_report import (  # noqa: E402
    DATASET_REPORT_SCHEMA,
    PREPARED_ARRAYS,
    PREPARED_COMPLETION_MARKER,
    PREPARED_SCHEMA_VERSION,
    dataset_report,
    escape_cell,
    inspect_dataset,
)

MILAN_SAMPLE = _REPO_ROOT / "tests" / "fixtures" / "uav_service_restoration" / "milan_shaped_sample"


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def prepared_cache(tmp_path_factory) -> Path:
    """A real prepared cache, written by the repository's own preprocessing writer."""

    from envs.uav_service_restoration.preprocess_milan import (
        load_preprocess_config,
        prepare_milan_dataset,
    )

    root = tmp_path_factory.mktemp("prepared_cache") / "cache"
    config = load_preprocess_config(MILAN_SAMPLE / "preprocess_small.json")
    prepare_milan_dataset(
        [MILAN_SAMPLE / "activity_2013-11-01.txt", MILAN_SAMPLE / "activity_2013-11-02.txt"],
        MILAN_SAMPLE / "grid_small.geojson",
        config,
        root,
        is_real_activity_data=False,
        kind="synthetic_fixture_milan_shaped",
    )
    return root


def _copy_cache(prepared_cache: Path, tmp_path: Path) -> Path:
    target = tmp_path / "cache_copy"
    shutil.copytree(prepared_cache, target)
    return target


def _field(report, name):
    return next(item for item in report.fields if item.name == name)


def _tree_digest(root: Path) -> dict[str, tuple[int, str]]:
    return {
        path.name: (
            path.stat().st_size,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in sorted(root.iterdir())
        if path.is_file()
    }


def _write_jsonl(path: Path, records) -> Path:
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8"
    )
    return path


# --------------------------------------------------------------------------------------
# Refusals: no fixture fallback anywhere
# --------------------------------------------------------------------------------------


def test_missing_dataset_path_raises_and_writes_nothing(tmp_path):
    output = tmp_path / "out"
    with pytest.raises(CliError) as error:
        dataset_report(tmp_path / "no_such_dataset", output)
    message = str(error.value)
    assert "does not exist" in message
    # The refusal names the substitution it is refusing to make.
    assert "fixture" in message
    assert not output.exists(), "a refused dataset must not produce a report directory"


def test_missing_dataset_never_falls_back_to_an_existing_cache(tmp_path, prepared_cache):
    """A real cache sitting next to the requested path is not silently used instead."""

    missing = prepared_cache.parent / "not_the_cache"
    assert prepared_cache.is_dir()
    with pytest.raises(CliError):
        inspect_dataset(missing)


def test_directory_without_metadata_is_refused(tmp_path):
    empty = tmp_path / "some_directory"
    empty.mkdir()
    (empty / "notes.txt").write_text("not a dataset", encoding="utf-8")
    with pytest.raises(CliError) as error:
        inspect_dataset(empty)
    assert "metadata.json" in str(error.value)


def test_unknown_file_suffix_is_refused(tmp_path):
    path = tmp_path / "dataset.parquet"
    path.write_bytes(b"\x00\x01")
    with pytest.raises(CliError) as error:
        inspect_dataset(path)
    assert "not a recognised dataset form" in str(error.value)


def test_foreign_schema_version_is_refused(tmp_path, prepared_cache):
    cache = _copy_cache(prepared_cache, tmp_path)
    payload = json.loads((cache / "metadata.json").read_text(encoding="utf-8"))
    payload["schema_version"] = "some_other_project.dataset.9"
    (cache / "metadata.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CliError) as error:
        inspect_dataset(cache)
    assert PREPARED_SCHEMA_VERSION in str(error.value)


def test_prepared_contract_matches_the_environment():
    """Drift guard: the mirrored constants must equal the environment's own."""

    from envs.uav_service_restoration import demand

    assert PREPARED_SCHEMA_VERSION == demand.PREPARED_SCHEMA_VERSION
    assert PREPARED_COMPLETION_MARKER == demand.COMPLETION_MARKER
    assert PREPARED_ARRAYS == demand._REQUIRED_ARRAYS


# --------------------------------------------------------------------------------------
# Prepared cache
# --------------------------------------------------------------------------------------


def test_prepared_cache_identity_and_counts(prepared_cache):
    report = inspect_dataset(prepared_cache)

    assert report.form == "uav_service_restoration_prepared_cache"
    assert report.form_evidence == "metadata.json:schema_version"
    assert report.counts["n_intervals"] == 12
    assert report.counts["n_aggregate_demand_points"] == 4
    assert report.counts["n_cell_interval_records"] == 48
    # Aggregate demand points are labelled as aggregates, never as people.
    assert "not a person" in report.counts["record_definition"]

    names = {Path(entry["path"]).name for entry in report.identity["files"]}
    assert set(PREPARED_ARRAYS) <= names
    assert report.identity["manifest_content_hash"].startswith("sha256:")
    for entry in report.identity["files"]:
        if Path(entry["path"]).name in PREPARED_ARRAYS:
            assert entry["sha256"].startswith("sha256:")
            assert entry["hash_agreement"] == "match"
            assert entry["bytes"] > 0
            assert entry["mtime_utc"] is not None


def test_prepared_cache_content_hash_is_recomputed_and_agrees(prepared_cache):
    report = inspect_dataset(prepared_cache)
    check = next(item for item in report.consistency if item["check"] == "content_sha256")
    assert check["agreement"] == "match"
    assert check["observed"] == check["declared"]


def test_unobserved_cells_are_missing_not_zero(prepared_cache):
    report = inspect_dataset(prepared_cache)
    activity = _field(report, "activity")

    observed = np.load(prepared_cache / "observed_mask.npy")
    values = np.load(prepared_cache / "activity.npy")
    expected_missing = int((~observed).sum())
    assert expected_missing > 0, "the fixture must contain at least one unrecorded cell"

    assert activity.n_records == int(observed.size)
    assert activity.n_present == int(observed.sum())
    assert activity.n_missing == expected_missing
    assert activity.missing_treated_as == "not_recorded"
    # The range is taken over observed values only: an unobserved cell contributes nothing,
    # and in particular does not drag the minimum to zero.
    assert activity.minimum.value == pytest.approx(float(values[observed].min()))
    assert activity.maximum.value == pytest.approx(float(values[observed].max()))
    assert report.observed["n_missing_cell_intervals"] == expected_missing
    assert any("NOT_RECORDED, not activity of zero" in note for note in activity.notes)


def test_an_all_unobserved_field_reports_absent_rather_than_zero(tmp_path, prepared_cache):
    cache = _copy_cache(prepared_cache, tmp_path)
    mask = np.load(cache / "observed_mask.npy")
    np.save(cache / "observed_mask.npy", np.zeros_like(mask), allow_pickle=False)

    report = inspect_dataset(cache)
    activity = _field(report, "activity")
    assert activity.n_present == 0
    assert activity.n_missing == int(mask.size)
    assert activity.minimum.value is None
    assert activity.minimum.validity.value == "not_recorded"
    assert activity.maximum.value is None
    assert report.observed["n_aggregate_demand_points_never_observed"] == int(mask.shape[1])
    assert any("unobserved in every interval" in text for text in report.warnings)


def test_measured_zero_stays_a_measurement(tmp_path, prepared_cache):
    cache = _copy_cache(prepared_cache, tmp_path)
    values = np.load(cache / "activity.npy")
    observed = np.load(cache / "observed_mask.npy")
    # One observed cell whose real activity is 0.0 is a measurement, not an absence.
    index = np.argwhere(observed)[0]
    values[tuple(index)] = 0.0
    np.save(cache / "activity.npy", values, allow_pickle=False)

    report = inspect_dataset(cache)
    activity = _field(report, "activity")
    assert activity.n_present == int(observed.sum())
    assert activity.minimum.validity.value == "ok"
    assert activity.minimum.value == pytest.approx(0.0)
    assert any("measured activity of exactly 0.0" in note for note in activity.notes)


def test_splits_are_reported_with_their_interval_counts(prepared_cache):
    report = inspect_dataset(prepared_cache)
    assert report.splits["status"] == "checked"
    assert report.splits["splits"]["train"]["dates"] == ["2013-11-01"]
    assert report.splits["splits"]["test"]["dates"] == ["2013-11-02"]
    assert report.splits["splits"]["train"]["n_intervals"] == 6
    assert report.splits["splits"]["test"]["n_intervals"] == 6
    assert report.splits["overlapping_dates"] == []
    assert report.splits["n_intervals_in_no_split"] == 0
    assert any("validation" in text for text in report.warnings)


def test_quality_report_declarations_are_checked_against_the_arrays(prepared_cache):
    report = inspect_dataset(prepared_cache)
    checked = {item["check"]: item for item in report.consistency}
    for name in (
        "quality_report.observed_fraction",
        "quality_report.aggregated_rows",
        "quality_report.n_valid_cells",
        "quality_report.activity_quantiles.max",
    ):
        assert checked[name]["agreement"] == "match"


def test_a_modified_array_is_reported_as_a_hash_mismatch(tmp_path, prepared_cache):
    cache = _copy_cache(prepared_cache, tmp_path)
    values = np.load(cache / "activity.npy")
    values[0, 0] += 1.0
    np.save(cache / "activity.npy", values, allow_pickle=False)

    report = inspect_dataset(cache)
    assert any("does not match the bytes on disk" in text for text in report.errors)
    entry = next(
        item for item in report.identity["files"] if Path(item["path"]).name == "activity.npy"
    )
    assert entry["hash_agreement"] == "mismatch"
    content = next(item for item in report.consistency if item["check"] == "content_sha256")
    assert content["agreement"] == "mismatch"


def test_incomplete_cache_is_reported_rather_than_hidden(tmp_path, prepared_cache):
    cache = _copy_cache(prepared_cache, tmp_path)
    (cache / PREPARED_COMPLETION_MARKER).unlink()

    report = inspect_dataset(cache)
    assert report.declared["completion_marker_present"] is False
    assert any("incomplete or still being written" in text for text in report.errors)


def test_duplicate_cell_identifiers_are_detected(tmp_path, prepared_cache):
    cache = _copy_cache(prepared_cache, tmp_path)
    cell_ids = np.load(cache / "cell_ids.npy")
    cell_ids[1] = cell_ids[0]
    np.save(cache / "cell_ids.npy", cell_ids, allow_pickle=False)

    report = inspect_dataset(cache)
    assert report.duplicates["cell_ids"]["n_duplicated_values"] == 1
    assert any("occur more than once" in text for text in report.errors)


def test_a_missing_array_is_a_missing_artifact(tmp_path, prepared_cache):
    cache = _copy_cache(prepared_cache, tmp_path)
    (cache / "positions_m.npy").unlink()

    report = inspect_dataset(cache)
    positions = _field(report, "positions_m")
    assert positions.observed is False
    assert positions.minimum.validity.value == "missing_artifact"
    assert positions.minimum.value is None
    assert "positions_m.npy" in report.observed["arrays_missing"]
    assert report.observed["content_sha256_status"] == "not_all_arrays_readable"


def test_reading_a_dataset_never_writes_into_it(tmp_path, prepared_cache):
    cache = _copy_cache(prepared_cache, tmp_path)
    before = _tree_digest(cache)
    dataset_report(cache, tmp_path / "report_out")
    assert _tree_digest(cache) == before


# --------------------------------------------------------------------------------------
# Record tables
# --------------------------------------------------------------------------------------


def test_field_present_in_every_record_versus_half(tmp_path):
    path = _write_jsonl(
        tmp_path / "episodes.jsonl",
        [
            {"episode_id": "e0", "delivered_mbit_total": 10.0, "time_to_recovery_s": 30.0},
            {"episode_id": "e1", "delivered_mbit_total": 12.0},
            {"episode_id": "e2", "delivered_mbit_total": 14.0, "time_to_recovery_s": 50.0},
            {"episode_id": "e3", "delivered_mbit_total": 16.0},
        ],
    )
    report = inspect_dataset(path)

    everywhere = _field(report, "delivered_mbit_total")
    assert (everywhere.n_records, everywhere.n_present, everywhere.n_missing) == (4, 4, 0)
    assert everywhere.minimum.value == pytest.approx(10.0)
    assert everywhere.maximum.value == pytest.approx(16.0)

    half = _field(report, "time_to_recovery_s")
    assert (half.n_records, half.n_present, half.n_missing) == (4, 2, 2)
    assert half.missing_treated_as == "not_recorded"
    # The two records without a recovery time do not enter the range as zeros.
    assert half.minimum.value == pytest.approx(30.0)
    assert half.maximum.value == pytest.approx(50.0)
    assert report.counts["n_records"] == 4


def test_a_field_absent_from_every_record_is_missing_not_zero(tmp_path):
    path = _write_jsonl(
        tmp_path / "rows.jsonl", [{"episode_id": "e0"}, {"episode_id": "e1"}]
    )
    (tmp_path / "rows.schema.json").write_text(
        json.dumps({"fields": ["episode_id", "energy_joules"], "units": {"energy_joules": "J"}}),
        encoding="utf-8",
    )
    report = inspect_dataset(path)

    energy = _field(report, "energy_joules")
    assert energy.declared is True
    assert energy.observed is False
    assert energy.n_present == 0
    assert energy.n_missing == 2
    assert energy.missing_treated_as == "missing_artifact"
    assert energy.minimum.value is None
    assert energy.minimum.validity.value == "missing_artifact"
    assert energy.unit == "J"
    assert energy.unit_source == "recorded"
    assert report.observed["declared_fields_absent_from_every_record"] == ["energy_joules"]


def test_explicit_null_is_counted_separately_from_an_absent_key(tmp_path):
    path = _write_jsonl(
        tmp_path / "rows.jsonl",
        [{"episode_id": "e0", "score": None}, {"episode_id": "e1"}, {"episode_id": "e2", "score": 3.0}],
    )
    report = inspect_dataset(path)
    score = _field(report, "score")
    assert (score.n_present, score.n_null, score.n_missing) == (1, 1, 1)
    assert score.minimum.value == pytest.approx(3.0)


def test_non_finite_values_are_invalid_not_a_range(tmp_path):
    # A historical artifact may carry the non-standard NaN token; it is still not a number.
    path = tmp_path / "rows.jsonl"
    path.write_text('{"episode_id": "e0", "score": NaN}\n', encoding="utf-8")
    report = inspect_dataset(path)
    score = _field(report, "score")
    assert score.n_present == 1
    assert score.n_non_finite == 1
    assert score.minimum.value is None
    assert score.minimum.validity.value == "invalid"


def test_duplicate_keys_are_an_error(tmp_path):
    path = _write_jsonl(
        tmp_path / "rows.jsonl",
        [{"episode_id": "e0", "v": 1}, {"episode_id": "e0", "v": 2}, {"episode_id": "e1", "v": 3}],
    )
    report = inspect_dataset(path)
    assert report.duplicates["key_fields"] == ["episode_id"]
    assert report.duplicates["n_duplicated_keys"] == 1
    assert any("occur more than once" in text for text in report.errors)


def test_a_key_in_two_splits_is_reported_as_leakage(tmp_path):
    path = _write_jsonl(
        tmp_path / "rows.jsonl",
        [
            {"episode_id": "e0", "split": "train"},
            {"episode_id": "e0", "split": "test"},
            {"episode_id": "e1", "split": "test"},
        ],
    )
    report = inspect_dataset(path)
    assert report.splits["split_field"] == "split"
    assert report.splits["counts"] == {"train": 1, "test": 2}
    assert report.splits["keys_in_more_than_one_split"]
    assert any("not disjoint" in text for text in report.errors)


def test_csv_empty_cell_is_missing_not_zero(tmp_path):
    path = tmp_path / "episodes.csv"
    path.write_text(
        "episode_id,delivered_mbps,note\ne0,1.5,ok\ne1,,\n", encoding="utf-8"
    )
    report = inspect_dataset(path)
    assert report.form == "record_table_csv"
    delivered = _field(report, "delivered_mbps")
    assert (delivered.n_present, delivered.n_missing) == (1, 1)
    assert delivered.minimum.value == pytest.approx(1.5)
    assert delivered.unit == "Mbps"


def test_episode_seed_list_reports_repeats_and_its_statistical_unit(tmp_path):
    path = tmp_path / "heldout.json"
    path.write_text(json.dumps({"episode_seeds": [11, 12, 12, 13]}), encoding="utf-8")
    report = inspect_dataset(path)

    assert report.form == "episode_seed_list"
    assert report.counts["n_records"] == 4
    assert report.duplicates["n_duplicated_keys"] == 1
    assert any("replays the same episode" in text for text in report.errors)
    assert report.statistical_units["n_statistical_units"] == 4
    assert "not independent replicates" in report.statistical_units["note"]


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------


def test_report_writes_json_and_html_and_returns_the_html(tmp_path, prepared_cache):
    output = tmp_path / "report"
    path = dataset_report(prepared_cache, output)

    assert path == output / "dataset_report.html"
    assert path.is_file()
    payload = json.loads((output / "dataset_report.json").read_text(encoding="utf-8"))
    assert payload["schema"] == DATASET_REPORT_SCHEMA
    assert payload["report_content_hash"].startswith("sha256:")
    assert payload["form"] == "uav_service_restoration_prepared_cache"


def test_html_has_no_external_reference(tmp_path, prepared_cache):
    cache = _copy_cache(prepared_cache, tmp_path)
    metadata = json.loads((cache / "metadata.json").read_text(encoding="utf-8"))
    # A declared URL is data the page displays; it must not become a fetchable reference.
    metadata["source_url"] = "https://dataverse.example.org/dataset/milan"
    (cache / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    path = dataset_report(cache, tmp_path / "report")
    html = path.read_text(encoding="utf-8")

    assert "http://" not in html
    assert "https://" not in html
    assert "dataverse.example.org" in html, "the declared URL is still shown, just not fetchable"
    for fragment in ("<script", "<link ", "<img ", "@import", "url("):
        assert fragment not in html


def test_escape_cell_neutralises_a_url_scheme():
    rendered = escape_cell("see https://example.org/x?a=1&b=2")
    assert "https://" not in rendered
    assert "example.org" in rendered
    assert "&amp;" in rendered


def test_statistical_units_refuse_a_zero_width_dispersion(prepared_cache):
    report = inspect_dataset(prepared_cache)
    dispersion = report.statistical_units["dispersion_across_units"]
    assert dispersion["value"] is None
    assert dispersion["validity"] == "not_applicable"
    assert "not zero" in dispersion["reason"]
