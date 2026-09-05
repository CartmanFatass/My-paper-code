"""Fixed-seed B06 runner; memory admission is adjacent in the launch command."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.commitment_residual_triggered_options.raw_exposure_b06.experiment import project_cost, run_experiment


def main(argv=None):
    parser = argparse.ArgumentParser(description="CRTO RAW exposure B06")
    parser.add_argument("--seed", type=int, choices=(1, 2), required=True)
    parser.add_argument("--project-cost", action="store_true")
    parser.add_argument("--output-dir")
    parser.add_argument("--execution-node")
    parser.add_argument("--toy", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.project_cost:
        print(json.dumps(project_cost(args.seed), indent=2, allow_nan=False))
    else:
        if not args.output_dir or not args.execution_node:
            parser.error("execution requires --output-dir and --execution-node")
        run_experiment(args.output_dir, seed=args.seed, execution_node=args.execution_node, toy=args.toy,
            argv=([sys.executable, *sys.orig_argv[1:]] if argv is None else [sys.executable, __file__, *argv]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
