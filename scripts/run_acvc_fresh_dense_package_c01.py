#!/usr/bin/env python3
"""One fixed C01 fresh fit and its complete C/F/dwell panels."""
import time

PROCESS_START = time.monotonic()

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.acvc.fresh_dense_package_c01.protocol import CARD, CAPS, OBJECT, UNITS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=[master for master, _q in UNITS], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--execution-seconds", type=float, required=True)
    args = parser.parse_args()
    from scripts.run_acvc_fresh_dense_reuse_b01 import run

    return run(args.output, args.launch_sha, PROCESS_START, args.execution_seconds,
               master=args.seed, evaluation_namespace=dict(UNITS)[args.seed],
               object_name=OBJECT, card_path=CARD, mode="PROVISIONAL_SINGLE_TASK_C_BENCH_UNIT",
               allocation_seconds=CAPS)


if __name__ == "__main__":
    raise SystemExit(main())
