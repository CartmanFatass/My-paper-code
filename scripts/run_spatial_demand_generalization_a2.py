#!/usr/bin/env python3
"""Admission-guarded entry for the fixed A2 paired layout-training batch."""
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


SEED = 260925101
TAG = "s1_spatial_coverage_a2_s260925101"


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=int, choices=(SEED,))
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.name != TAG:
        parser.error(f"--out basename must be {TAG}")
    if args.out.exists():
        admitted_files = {"launch-manifest.json", "launch-status.json",
                          "admission-preflight.json", "stdout.log", "stderr.log"}
        scientific = [path.name for path in args.out.iterdir() if path.name not in admitted_files]
        if scientific:
            parser.error(f"existing A2 scientific output: {scientific}")
    admission = require_admission(__file__, direction="spatial_demand_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.spatial_demand_generalization.a2.runner import run_batch
    if run_fn is None:
        run_fn = run_batch
    return run_fn(
        args.out.resolve(), args.launch_sha, admission, command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
