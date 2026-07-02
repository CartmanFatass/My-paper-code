from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np


REQUIRED_FIELDS = (
    "opt_aggregation_entropy",
    "opt_cd_loss",
    "opt_cmi_loss",
    "compact_norm_mean",
)


def _to_float(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float("nan")
    if not np.isfinite(parsed):
        return float("nan")
    return parsed


def _field_stats(rows: list[dict[str, str]], field: str) -> dict[str, float | int]:
    values = np.asarray([_to_float(row.get(field)) for row in rows], dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {
            "count": 0,
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "last": 0.0,
        }
    return {
        "count": int(values.size),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "last": float(values[-1]),
    }


def summarize_csv(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = set(reader.fieldnames or ())

    return {
        "path": str(path),
        "rows": len(rows),
        "missing_fields": [field for field in REQUIRED_FIELDS if field not in fieldnames],
        "fields": {field: _field_stats(rows, field) for field in REQUIRED_FIELDS},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Round-12 existing-CSV OPT triage.")
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    output = Path(args.output)
    paths = sorted(root.glob("**/metrics/train_updates.csv"))
    runs = [summarize_csv(path) for path in paths]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"root": str(root), "runs": runs}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"r12_csv_triage runs={len(runs)} output={output}")
    for run in runs:
        missing = ",".join(run["missing_fields"]) if run["missing_fields"] else "none"
        print(f"{run['path']} rows={run['rows']} missing_fields={missing}")


if __name__ == "__main__":
    main()
