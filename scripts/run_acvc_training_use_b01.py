#!/usr/bin/env python3
"""One complete fit of the allocated fixed-F training-use pair, then final F only."""
import time

PROCESS_START = time.monotonic()

import argparse
from pathlib import Path

from run_acvc_fresh_dense_reuse_b01 import run
from experiments.candidates.acvc.training_use_b01.protocol import (
    CAPS, CARD, EVALUATION_NAMESPACE, MASTER, OBJECT,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=[MASTER], default=MASTER)
    parser.add_argument("--arm", choices=["C", "F"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--execution-seconds", type=float, required=True)
    args = parser.parse_args()
    return run(args.output, args.launch_sha, PROCESS_START, args.execution_seconds,
               master=args.seed, evaluation_namespace=EVALUATION_NAMESPACE,
               object_name=OBJECT, card_path=CARD, allocation_seconds=CAPS,
               train_rule=args.arm, eval_arms=("F",))


if __name__ == "__main__":
    raise SystemExit(main())
