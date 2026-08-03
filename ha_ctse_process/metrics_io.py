"""CSV helpers for HA-CTSE training metrics."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def append_csv(path: Path, row: dict[str, Any], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            old_fields = tuple(reader.fieldnames or ())
            if old_fields != fields:
                rows = list(reader)
        if old_fields != fields:
            preserved = tuple(field for field in old_fields if field not in fields)
            merged_fields = (*fields, *preserved)
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(merged_fields), extrasaction="ignore")
                writer.writeheader()
                for old_row in rows:
                    writer.writerow({field: old_row.get(field, "") for field in merged_fields})
            fields = merged_fields
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})


def write_csv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_records(path: Path) -> list[dict[str, float]]:
    if not path.exists():
        return []
    records: list[dict[str, float]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record = {}
            for key, value in row.items():
                if value == "":
                    continue
                try:
                    record[key] = float(value)
                except ValueError:
                    continue
            if record:
                records.append(record)
    return records
