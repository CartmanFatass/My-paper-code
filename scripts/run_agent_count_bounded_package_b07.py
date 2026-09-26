#!/usr/bin/env python3
"""Admission-guarded entry for the fixed B07 fresh H6 bounded-package fit."""
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


TAG = "s1_bounded_package_b07_h6_l05_s952201"


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=(952201,), required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--set-checkpoint", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.name != TAG:
        parser.error(f"--out basename must be {TAG}")

    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.agent_count_generalization.bounded_package_b07.runner import (
        CELL,
        TAG as RUNNER_TAG,
        run_fit,
    )
    if RUNNER_TAG != TAG or CELL.seed != args.seed or CELL.arm != "H6" or CELL.law != "clip":
        raise ValueError("B07 CLI/candidate fixed-cell bindings disagree")
    if run_fn is None:
        run_fn = run_fit
    return run_fn(
        args.out.resolve(), args.launch_sha, admission, args.set_checkpoint.resolve(),
        command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
