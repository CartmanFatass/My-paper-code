import csv

from ha_ctse_process.metrics_io import append_csv, read_csv_records, write_csv


def test_metrics_io_csv_helpers_preserve_existing_behavior(tmp_path):
    appended = tmp_path / "metrics" / "appended.csv"
    append_csv(appended, {"step": 1, "legacy": "kept"}, ("step", "legacy"))
    with appended.open(newline="", encoding="utf-8") as handle:
        assert list(csv.DictReader(handle)) == [{"step": "1", "legacy": "kept"}]

    append_csv(appended, {"step": 2, "loss": 0.5}, ("step", "loss"))
    with appended.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["step", "loss", "legacy"]
        assert list(reader) == [
            {"step": "1", "loss": "", "legacy": "kept"},
            {"step": "2", "loss": "0.5", "legacy": ""},
        ]

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
    empty = tmp_path / "metrics" / "empty.csv"
    empty.write_text("value\n", encoding="utf-8")
    assert read_csv_records(empty) == []
