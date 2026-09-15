#!/usr/bin/env python3
"""One indexed fresh clustered C01 fit and its three final deployment panels."""
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

from experiments.candidates.acvc.cluster_fixed_recipe_c01.protocol import (
    ARMS, CARD, OBJECT, PLANNING_SECONDS, TRAIN_EPISODES,
    make_cluster, publish, unit_identity,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--unit", type=int, choices=range(1, 7), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--execution-seconds", type=float, choices=[1800.0], required=True)
    args = parser.parse_args(argv)
    unit_index, master, namespace = unit_identity(args.unit)
    if args.output.name != f"unit_{unit_index:02d}":
        parser.error("output basename must match the indexed unit identity")
    prior_scientific_outputs = (
        "summary.json", "episodes.jsonl", "updates.jsonl", "final_DENSE.pt"
    )
    if any((args.output / name).exists() for name in prior_scientific_outputs):
        parser.error("refusing to reuse prior fixed-recipe unit output")

    from scripts.run_acvc_fresh_dense_reuse_b01 import run

    code = run(
        args.output,
        args.launch_sha,
        PROCESS_START,
        args.execution_seconds,
        make_env=make_cluster,
        train_episodes=TRAIN_EPISODES,
        master=master,
        evaluation_namespace=namespace,
        object_name=OBJECT,
        card_path=CARD,
        mode="PROVISIONAL_SINGLE_TASK_C_BENCH_UNIT",
        allocation_seconds=PLANNING_SECONDS,
        train_rule="C",
        eval_arms=ARMS,
    )
    complete = publish(args.output, PROCESS_START, unit_index)
    return code or int(not complete)


if __name__ == "__main__":
    raise SystemExit(main())
