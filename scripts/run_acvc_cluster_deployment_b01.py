#!/usr/bin/env python3
"""One newly allocated cluster C-fit with final C/F/own-dwell panels."""
import time

PROCESS_START = time.monotonic()

import os

for _name in (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS",
):
    os.environ[_name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.acvc.cluster_deployment_b01.protocol import (
    ARMS, CAPS, CARD, EVALUATION_NAMESPACE, MASTER, OBJECT, make_cluster, publish,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=[MASTER], default=MASTER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--execution-seconds", type=float, required=True)
    args = parser.parse_args(argv)
    from scripts.run_acvc_fresh_dense_reuse_b01 import run

    code = run(args.output, args.launch_sha, PROCESS_START, args.execution_seconds,
               make_env=make_cluster, master=args.seed, evaluation_namespace=EVALUATION_NAMESPACE,
               object_name=OBJECT, card_path=CARD, mode="UAV_B_EXPLORE", allocation_seconds=CAPS,
               train_rule="C", eval_arms=ARMS)
    complete = publish(args.output, PROCESS_START)
    return code or int(not complete)


if __name__ == "__main__":
    raise SystemExit(main())
