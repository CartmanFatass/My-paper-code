"""CSV helpers for HA-CTSE training metrics."""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from filelock import FileLock


CsvScalar = float | str


def _csv_bytes(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(fields), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return buffer.getvalue().encode("utf-8")


def _row_bytes(row: dict[str, Any], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(fields), extrasaction="ignore")
    writer.writerow({field: row.get(field, "") for field in fields})
    return buffer.getvalue().encode("utf-8")


def _atomic_replace(path: Path, payload_writer) -> None:
    """Write a same-directory replacement and durably publish it."""

    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
        ) as temp:
            temp_name = temp.name
            payload_writer(temp)
            temp.flush()
            os.fsync(temp.fileno())
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass


def append_csv(path: Path, row: dict[str, Any], fields: tuple[str, ...]) -> None:
    """Atomically append one row, migrating a legacy header under a file lock.

    A matching-header append byte-copies the existing file instead of parsing its
    rows.  This keeps the common path lossless while still making publication an
    atomic replace rather than an interruptible in-place write.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(path) + ".lock")
    with lock:
        old_fields: tuple[str, ...] = ()
        old_rows: list[dict[str, str]] | None = None
        if path.exists() and path.stat().st_size:
            with path.open("r", newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                old_fields = tuple(reader.fieldnames or ())
                if old_fields != fields:
                    old_rows = list(reader)

        if old_fields == fields:
            def copy_and_append(temp) -> None:
                with path.open("rb") as source:
                    shutil.copyfileobj(source, temp)
                with path.open("rb") as source:
                    source.seek(-1, os.SEEK_END)
                    if source.read(1) not in (b"\n", b"\r"):
                        temp.write(b"\r\n")
                temp.write(_row_bytes(row, fields))

            _atomic_replace(path, copy_and_append)
            return

        preserved = tuple(field for field in old_fields if field not in fields)
        merged_fields = (*fields, *preserved)
        migrated_rows: list[dict[str, Any]] = [] if old_rows is None else list(old_rows)
        migrated_rows.append(row)
        payload = _csv_bytes(migrated_rows, merged_fields)
        _atomic_replace(path, lambda temp: temp.write(payload))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_records(path: Path) -> list[dict[str, CsvScalar]]:
    """Read non-empty CSV cells, preserving identifiers as strings.

    Numeric cells remain floats for existing plotting consumers.  Empty cells are
    absent rather than being synthesized as zero or an empty identifier.
    """

    if not path.exists():
        return []
    records: list[dict[str, CsvScalar]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record: dict[str, CsvScalar] = {}
            for key, value in row.items():
                if value == "":
                    continue
                try:
                    record[key] = float(value)
                except ValueError:
                    record[key] = value
            if record:
                records.append(record)
    return records
