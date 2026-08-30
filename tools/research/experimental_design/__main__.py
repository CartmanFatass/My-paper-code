"""CLI for deterministic, offline experimental-design schedule construction."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .engine import DesignValidationError, build_schedule, validate_schedule, write_schedule


def _load_object(path: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DesignValidationError(f"cannot read JSON input: {error}") from error
    if not isinstance(value, dict):
        raise DesignValidationError("JSON input must be an object")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.research.experimental_design",
        description="Build or validate a deterministic, offline experimental schedule.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="validate a frozen request and emit its schedule")
    generate.add_argument("--input", required=True, help="frozen protocol request JSON")
    generate.add_argument("--json-output", help="optional schedule JSON destination")
    generate.add_argument("--csv-output", help="optional schedule CSV destination")
    validate = commands.add_parser("validate", help="validate an emitted schedule hash and invariants")
    validate.add_argument("--input", required=True, help="schedule JSON artifact")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "generate":
            artifact = build_schedule(_load_object(args.input))
            if args.json_output or args.csv_output:
                write_schedule(artifact, json_path=args.json_output, csv_path=args.csv_output)
                output = {
                    "artifact_type": artifact["artifact_type"],
                    "schedule_hash": artifact["schedule_hash"],
                    "input_hash": artifact["input_hash"],
                    "row_count": len(artifact["rows"]),
                }
            else:
                output = artifact
        else:
            artifact = _load_object(args.input)
            validate_schedule(artifact)
            output = {"valid": True, "schedule_hash": artifact["schedule_hash"]}
    except DesignValidationError as error:
        print(json.dumps({"valid": False, "error": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
