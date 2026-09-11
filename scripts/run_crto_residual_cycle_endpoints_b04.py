#!/usr/bin/env python3
"""Project or execute the fixed CRTO B04 comparison after external memory admission."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.commitment_residual_triggered_options.residual_cycle_endpoints_b04.experiment import (
    project_cost, run_experiment,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description="CRTO residual complete-cycle endpoints B04")
    parser.add_argument("command", choices=("project-cost", "run"))
    parser.add_argument("--seed", type=int, choices=(0,), default=0)
    parser.add_argument("--output-dir")
    parser.add_argument("--execution-node")
    parser.add_argument("--toy", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.command == "project-cost":
        print(json.dumps(project_cost(args.seed), indent=2, allow_nan=False))
    else:
        if not args.output_dir or not args.execution_node:
            parser.error("run requires --output-dir and --execution-node")
        run_experiment(
            args.output_dir, seed=args.seed, toy=args.toy, execution_node=args.execution_node,
            argv=([sys.executable, *sys.orig_argv[1:]] if argv is None else
                  [sys.executable, str(Path(__file__).resolve()), *argv]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
