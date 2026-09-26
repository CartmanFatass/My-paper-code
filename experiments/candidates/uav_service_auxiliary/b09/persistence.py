"""B09 counter journal and atomic completed-boundary summaries."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import gzip

from ..b01.native import _json_default


def compact_opportunity(value: dict) -> dict:
    """Retain the anchor and all denominators; raw JSON holds interval lists."""
    compact = {key: item for key, item in value.items() if key != "intervals"}
    anchor = compact.get("first_qualifying_exit_anchor")
    if anchor is not None:
        compact["first_qualifying_exit_anchor"] = {
            key: item for key, item in anchor.items() if key != "window_zero_service_intervals"
        }
    return compact


def write_raw_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, default=_json_default, allow_nan=False,
                         separators=(",", ":"))
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(payload)


def write_summary(path: Path, value: dict) -> None:
    """Replace a complete JSON summary only after serialization has succeeded."""
    path = Path(path)
    payload = json.dumps(value, default=_json_default, allow_nan=False, separators=(",", ":")) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=".summary-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_progress(out: Path, event: dict, counts: dict) -> None:
    """Write only current counters; growing episode/phase/world arrays stay out."""
    row = {"event": event, "counts": counts}
    with (Path(out) / "progress.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=_json_default, allow_nan=False,
                                separators=(",", ":")) + "\n")
