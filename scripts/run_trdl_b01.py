#!/usr/bin/env python3
"""Two separately admitted original arms; pure final pair reduction is a subcommand."""
import time
PROCESS_START = time.monotonic()

import argparse
import os
from pathlib import Path
import sys

for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.set_default_dtype(torch.float32)
torch.set_default_device("cpu")
from experiments.candidates.tail_return_distributional_learning.trdl_b01.study import (
    publish_pair, run_arm)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    arm = sub.add_parser("arm")
    arm.add_argument("--arm", choices=("SCALAR", "Q32"), required=True)
    arm.add_argument("--seed", type=int, default=9601)
    arm.add_argument("--out", type=Path, required=True)
    arm.add_argument("--launch-sha", required=True)
    arm.add_argument("--max-seconds", type=float, default=900)
    pair = sub.add_parser("pair")
    pair.add_argument("--scalar", type=Path, required=True)
    pair.add_argument("--quantile", type=Path, required=True)
    pair.add_argument("--out", type=Path, required=True)
    pair.add_argument("--launch-sha", required=True)
    args = parser.parse_args()
    if args.mode == "pair":
        result = publish_pair(args.scalar, args.quantile, args.out, args.launch_sha)
        print(result["branch"], result["delta_tail"])
        return 0
    result = run_arm(args.arm, args.seed, args.out, args.launch_sha,
                     args.max_seconds, PROCESS_START)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
