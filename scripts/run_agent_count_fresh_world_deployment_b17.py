#!/usr/bin/env python3
"""Admission-guarded entry for the fixed B17 fresh-world deployment evaluator."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time


COMMAND_START = time.perf_counter()
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.hmasd_admission import require_admission


OBJECT_ID = "s1_fresh_world_deployment_b17"
TAG = "s1_fresh_world_deployment_b17_final45"
PROTOCOL_SEED = 2_145_851
DIRECTION = "agent_count_generalization"


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed", required=True, type=int, choices=(PROTOCOL_SEED,),
        help="fixed B17 protocol identity; panel RNG addresses remain internally bound",
    )
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--input-root", type=Path, required=True,
        help="declared retained-input directory containing the six digest-bound assets",
    )
    args = parser.parse_args(argv)
    if args.out.name != TAG:
        parser.error(f"--out basename must be {TAG}")
    if not args.input_root.is_absolute() or args.input_root.name != DIRECTION:
        parser.error(f"--input-root must be an absolute retained {DIRECTION} directory")

    # Admission is deliberately the first scientific operation. Candidate imports,
    # checkpoint loading, model construction, and environment interaction follow it.
    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.agent_count_generalization.fresh_world_deployment_b17.runner import (
        ASSETS,
        OBJECT_ID as RUNNER_OBJECT_ID,
        POLICY_ORDER,
        PROTOCOL_SEED as RUNNER_PROTOCOL_SEED,
        TAG as RUNNER_TAG,
        run_study,
    )
    if (RUNNER_OBJECT_ID, RUNNER_TAG, RUNNER_PROTOCOL_SEED) != (OBJECT_ID, TAG, PROTOCOL_SEED) \
            or tuple(asset.key for asset in ASSETS) != POLICY_ORDER:
        raise ValueError("B17 CLI/candidate fixed bindings disagree")
    if run_fn is None:
        run_fn = run_study
    return run_fn(
        args.out.resolve(), args.launch_sha, admission, args.input_root.resolve(), args.seed,
        command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
