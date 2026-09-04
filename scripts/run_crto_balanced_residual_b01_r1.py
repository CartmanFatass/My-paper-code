#!/usr/bin/env python3
"""Run or inspect the CRTO balanced-residual B01-R1 object."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.candidates.commitment_residual_triggered_options.balanced_residual_b01_r1.experiment import (  # noqa: E402
    observe_lower_domain, project_cost, run_experiment,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CRTO balanced residual B01-R1")
    commands = parser.add_subparsers(dest="command", required=True)
    cost = commands.add_parser("project-cost")
    cost.add_argument("--seed", type=int, choices=(0,), default=0)
    lower = commands.add_parser("observe-lower-domain")
    lower.add_argument("--seed", type=int, choices=(0,), default=0)
    run = commands.add_parser("run")
    run.add_argument("--seed", type=int, choices=(0,), default=0)
    run.add_argument("--admission-receipt", required=True)
    run.add_argument("--output-dir", required=True)
    run.add_argument("--toy", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(arguments)
    if args.command == "project-cost":
        value = project_cost(args.seed)
    elif args.command == "observe-lower-domain":
        value = observe_lower_domain()
    else:
        exact_argv = [sys.executable, str(Path(__file__).resolve()), *arguments]
        value = run_experiment(
            args.output_dir, admission_receipt=args.admission_receipt,
            argv=exact_argv, seed=args.seed, toy=args.toy,
        )
    print(json.dumps(value, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
