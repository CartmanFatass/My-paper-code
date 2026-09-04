#!/usr/bin/env python3
"""CLI for UCOPE-B-EXPLORE-THREE-WITNESS-HINGE-R01."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.three_witness_hinge_r01.experiment import (  # noqa: E402
    B1_SEEDS,
    LaunchRefusal,
    project_cost,
    run_object,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = value.add_subparsers(dest="command", required=True)
    cost = commands.add_parser("project-cost", allow_abbrev=False)
    cost.add_argument("--output")
    run = commands.add_parser("run", allow_abbrev=False)
    run.add_argument("--output-root", required=True)
    run.add_argument("--admission-receipt", required=True)
    run.add_argument("--seed", action="append", required=True)
    run.add_argument("--thread-cap", type=int, choices=(1,), required=True)
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "project-cost":
            result = project_cost()
            encoded = json.dumps(result, indent=2, sort_keys=True)
            if args.output:
                Path(args.output).write_text(encoded + "\n", encoding="utf-8")
            print(encoded)
            return 0
        if tuple(args.seed) != tuple(B1_SEEDS):
            raise LaunchRefusal("--seed order must equal the frozen B1_SEEDS sequence")
        path = run_object(
            args.output_root, admission_receipt=args.admission_receipt, seeds=tuple(args.seed),
            thread_cap=args.thread_cap, argv=sys.argv)
        result = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps({"summary": str(path), **result["reading_rule"]}, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, LaunchRefusal) as exc:
        print(f"UCOPE three-witness stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
