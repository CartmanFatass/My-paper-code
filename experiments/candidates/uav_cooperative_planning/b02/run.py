#!/usr/bin/env python3
"""Admission-guarded fixed B02 transit-value entry point."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=29092791,
                        help="fixed B02 fit seed; collection/evaluation seed blocks are fixed")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--threads", type=int, default=1)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_cooperative_planning")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    if args.seed != 29092791 or args.workers != 2 or args.threads != 1:
        raise ValueError("B02 fixes the fit seed, two workers and one numeric thread each")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.uav_cooperative_planning.b02.runner import run

    return run(args.out, args.launch_sha, workers=args.workers, threads=args.threads)


if __name__ == "__main__":
    if main()["status"] != "complete":
        raise SystemExit(1)
