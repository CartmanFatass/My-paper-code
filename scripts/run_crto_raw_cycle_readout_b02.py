#!/usr/bin/env python3
"""Project or execute the fixed CRTO B02 comparison after external memory admission."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.commitment_residual_triggered_options.raw_cycle_readout_b02.experiment import (
    project_cost, run_experiment,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description="CRTO full-cycle RAW readout B02")
    commands = parser.add_subparsers(dest="command", required=True)
    cost = commands.add_parser("project-cost")
    cost.add_argument("--seed", type=int, choices=(0,), default=0)
    run = commands.add_parser("run")
    run.add_argument("--seed", type=int, choices=(0,), default=0)
    run.add_argument("--output-dir", required=True)
    run.add_argument("--execution-node", required=True)
    run.add_argument("--toy", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.command == "project-cost":
        summary = project_cost(args.seed)
    else:
        summary = run_experiment(
            args.output_dir, seed=args.seed, toy=args.toy, execution_node=args.execution_node,
            argv=([sys.executable, *sys.orig_argv[1:]] if argv is None else
                  [sys.executable, str(Path(__file__).resolve()), *argv]))
    print(json.dumps(summary, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
