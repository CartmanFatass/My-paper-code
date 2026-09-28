#!/usr/bin/env python3
"""Admission-guarded fixed B01 analytical coordination panel."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--threads", type=int, default=1)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.seed != 31092801 or args.workers < 1 or args.threads != 1:
        raise ValueError("B01 requires seed 31092801, positive workers and one numeric thread")
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_energy_coordination")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    from experiments.candidates.uav_energy_coordination.b01.runner import run

    return run(args.out, args.launch_sha, workers=args.workers, threads=args.threads)


if __name__ == "__main__":
    if main()["status"] != "complete":
        raise SystemExit(1)
