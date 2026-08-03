import csv

from ha_ctse_process import metrics_io
from ha_ctse_process.metrics_io import append_csv, read_csv_records, write_csv


def test_append_csv_matching_header_does_not_iterate_existing_rows_and_matches_baseline(tmp_path, monkeypatch):
    fields = ("step", "loss")
    appended = tmp_path / "metrics" / "appended.csv"
    baseline = tmp_path / "metrics" / "baseline.csv"
    write_csv(appended, [{"step": 1, "loss": 0.5}], fields)
    write_csv(
        baseline,
        [{"step": 1, "loss": 0.5}, {"step": 2, "loss": 0.25}],
        fields,
    )

    original_dict_reader = metrics_io.csv.DictReader

    class GuardedDictReader(original_dict_reader):
        row_iterations = 0

        def __next__(self):
            type(self).row_iterations += 1
            raise AssertionError("matching headers must not iterate existing rows")

    monkeypatch.setattr(metrics_io.csv, "DictReader", GuardedDictReader)
    append_csv(appended, {"step": 2, "loss": 0.25, "ignored": "value"}, fields)

    assert GuardedDictReader.row_iterations == 0
    assert appended.read_bytes() == baseline.read_bytes()


def test_append_csv_migrates_mismatched_header_with_requested_then_legacy_fields(tmp_path):
    migrated = tmp_path / "metrics" / "migrated.csv"
    migrated.parent.mkdir(parents=True)
    migrated.write_bytes(b"legacy,step\r\nkept,1\r\nolder,2\r\n")

    append_csv(migrated, {"step": 3, "loss": 0.25, "ignored": "value"}, ("step", "loss"))

    with migrated.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["step", "loss", "legacy"]
        assert list(reader) == [
            {"step": "1", "loss": "", "legacy": "kept"},
            {"step": "2", "loss": "", "legacy": "older"},
            {"step": "3", "loss": "0.25", "legacy": ""},
        ]


def test_append_csv_preserves_new_empty_and_ignored_extra_behavior(tmp_path):
    new_file = tmp_path / "metrics" / "new.csv"
    append_csv(new_file, {"step": 1, "ignored": "value"}, ("step",))
    assert new_file.read_bytes() == b"step\r\n1\r\n"

    empty_file = tmp_path / "metrics" / "empty.csv"
    empty_file.write_bytes(b"")
    append_csv(empty_file, {"step": 2, "ignored": "value"}, ("step",))
    assert empty_file.read_bytes() == b"step\r\n2\r\n"


def test_write_csv_and_read_csv_records_preserve_existing_behavior(tmp_path):
    written = tmp_path / "metrics" / "written.csv"
    write_csv(written, [{"second": 2, "first": 1, "ignored": "value"}], ("first", "second"))
    with written.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["first", "second"]
        assert list(reader) == [{"first": "1", "second": "2"}]

    numeric = tmp_path / "metrics" / "numeric.csv"
    numeric.write_text("value,empty,text\n1.5,,not-a-number\n,,\n", encoding="utf-8")
    assert read_csv_records(numeric) == [{"value": 1.5}]
    assert read_csv_records(tmp_path / "missing.csv") == []
    empty = tmp_path / "metrics" / "header-only.csv"
    empty.write_text("value\n", encoding="utf-8")
    assert read_csv_records(empty) == []
