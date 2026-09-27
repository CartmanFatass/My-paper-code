#!/usr/bin/env python3
"""Admission-guarded fixed 64-world paired S7-S4 availability-response study."""

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
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--threads", type=int, default=1)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="energy_relay_availability")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    if args.threads != 1:
        raise ValueError("B02 numeric thread count is fixed at one")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    from experiments.candidates.energy_relay_availability.b02_runner import run

    return run(args.out, args.launch_sha, workers=args.workers, threads=args.threads)


if __name__ == "__main__":
    outcome = main()
    if outcome["status"] != "complete":
        raise SystemExit(1)
