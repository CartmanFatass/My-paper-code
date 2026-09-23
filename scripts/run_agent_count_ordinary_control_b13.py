#!/usr/bin/env python3
"""Admission-guarded entry for the fixed B13 four-policy common evaluator."""
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


TAG = "s1_ordinary_control_b13"


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=int,
                        help="constructor-only seed; evaluation worlds and policies remain fixed")
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--s1-checkpoint", type=Path, required=True)
    parser.add_argument("--s2-checkpoint", type=Path, required=True)
    parser.add_argument("--h1-checkpoint", type=Path, required=True)
    parser.add_argument("--h2-checkpoint", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.name != TAG:
        parser.error(f"--out basename must be {TAG}")

    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.agent_count_generalization.ordinary_control_b13.runner import (
        ASSETS,
        TAG as RUNNER_TAG,
        run_study,
    )
    if RUNNER_TAG != TAG or tuple(asset.key for asset in ASSETS) != ("s1", "s2", "h1", "h2"):
        raise ValueError("B13 CLI/candidate fixed-asset bindings disagree")
    if run_fn is None:
        run_fn = run_study
    checkpoints = {
        "s1": args.s1_checkpoint.resolve(), "s2": args.s2_checkpoint.resolve(),
        "h1": args.h1_checkpoint.resolve(), "h2": args.h2_checkpoint.resolve(),
    }
    return run_fn(
        args.out.resolve(), args.launch_sha, admission, checkpoints, args.seed,
        command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
