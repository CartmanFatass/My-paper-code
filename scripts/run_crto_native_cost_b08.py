#!/usr/bin/env python3
"""B08 execution and collection-time complete-wall accounting (external admission)."""
import time
STARTED = time.perf_counter()

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv=None):
    parser = argparse.ArgumentParser(description="CRTO native-cost B08")
    parser.add_argument("command", choices=("project-cost", "run", "account"))
    parser.add_argument("--seed", type=int, choices=(0,), default=0)
    parser.add_argument("--output-dir")
    parser.add_argument("--historical-summary")
    parser.add_argument("--execution-node")
    parser.add_argument("--complete-wall-seconds", type=float)
    args = parser.parse_args(argv)
    from experiments.candidates.commitment_residual_triggered_options.native_cost_b08.experiment import (
        project_cost, run_experiment, publish_complete_accounting,
    )
    if args.command == "project-cost":
        print(json.dumps(project_cost(), indent=2, allow_nan=False))
    elif args.command == "account":
        if not args.output_dir or args.complete_wall_seconds is None:
            parser.error("account requires --output-dir and terminal supervisor --complete-wall-seconds")
        print(json.dumps(publish_complete_accounting(args.output_dir, args.complete_wall_seconds), indent=2))
    else:
        if not args.output_dir or not args.execution_node or not args.historical_summary:
            parser.error("run requires --output-dir, --execution-node and --historical-summary")
        run_experiment(args.output_dir, historical_summary=args.historical_summary,
            seed=args.seed, execution_node=args.execution_node, started=STARTED,
            argv=([sys.executable, *sys.orig_argv[1:]] if argv is None else
                  [sys.executable, str(Path(__file__).resolve()), *argv]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
