#!/usr/bin/env python3
"""Admission-guarded entry for one fixed C01 paired training block."""
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


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", required=True, type=int, choices=range(5))
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    expected_seed = 263000101 + args.block
    tag = f"s1_spatial_coverage_c01_b{args.block}_s{expected_seed}"
    if args.seed != expected_seed:
        parser.error(f"--seed for block {args.block} must be {expected_seed}")
    if args.out.name != tag:
        parser.error(f"--out basename for block {args.block} must be {tag}")
    if args.out.exists():
        admission_owned = {"launch-manifest.json", "launch-status.json",
                           "admission-preflight.json", "stdout.log", "stderr.log"}
        scientific = [path.name for path in args.out.iterdir() if path.name not in admission_owned]
        if scientific:
            parser.error(f"existing C01 scientific output: {scientific}")
    admission = require_admission(__file__, direction="spatial_demand_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.spatial_demand_generalization.c01.runner import run_block
    if run_fn is None:
        run_fn = run_block
    return run_fn(args.out.resolve(), args.launch_sha, admission, args.block,
                  command_start=COMMAND_START)


if __name__ == "__main__":
    raise SystemExit(main())
