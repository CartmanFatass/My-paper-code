#!/usr/bin/env python3
"""Run the nonformal cross-lifecycle handoff information gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.cross_lifecycle_handoff_g2 import (
    build_cases,
    evaluate_information_gate,
)


def _source_commit(value: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise argparse.ArgumentTypeError("source commit must be 40 lowercase hex chars")
    return value


def run_exercise(output_dir: Path, source_commit: str) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=False)
    result = evaluate_information_gate(build_cases())
    artifact = {
        **result,
        "source_commit": source_commit,
        "backend": "cpu",
        "cpu_threads": 1,
        "command": "exercise",
    }
    (output_dir / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    exercise = subparsers.add_parser("exercise")
    exercise.add_argument("--output-dir", type=Path, required=True)
    exercise.add_argument("--source-commit", type=_source_commit, required=True)
    arguments = parser.parse_args()

    if arguments.command != "exercise":
        parser.error("only the nonformal exercise is available")
    artifact = run_exercise(arguments.output_dir, arguments.source_commit)
    print(
        json.dumps(
            {
                "formal": artifact["formal"],
                "result": artifact["result"],
                "artifact": str(arguments.output_dir / "result.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
