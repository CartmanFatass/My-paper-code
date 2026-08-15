"""One train/evaluate/analyze entry point for EGRCR-B1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .config import DEFAULT_CALIBRATION_PATH, DEFAULT_RESULT_PATH
from .experiment import run_calibration, run_confirmation


def _write_json(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)


def _read_json(path: str) -> object:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("calibration", "confirmation", "all"), required=True)
    parser.add_argument("--calibration-output", default=DEFAULT_CALIBRATION_PATH)
    parser.add_argument("--calibration-input", default=DEFAULT_CALIBRATION_PATH)
    parser.add_argument("--result-output", default=DEFAULT_RESULT_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    calibration = None
    if args.stage in {"calibration", "all"}:
        calibration = run_calibration()
        _write_json(args.calibration_output, calibration)
        print(json.dumps({"stage": "calibration", "all_gates_passed": calibration["all_gates_passed"], "path": args.calibration_output}))
        if not calibration["all_gates_passed"]:
            return 2
    if args.stage in {"confirmation", "all"}:
        if calibration is None:
            calibration = _read_json(args.calibration_input)
        result = run_confirmation(calibration)
        _write_json(args.result_output, result)
        print(json.dumps({"stage": result["stage"], "binding_question_exposed": result["binding_question_exposed"], "path": args.result_output}))
        if result["stage"] != "confirmation_complete":
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
