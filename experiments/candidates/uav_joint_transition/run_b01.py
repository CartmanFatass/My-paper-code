#!/usr/bin/env python3
"""Admission-guarded selected one-fit joint-transition study."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args(argv)
    if args.seed != 62092801 or args.workers != 2 or args.threads != 1:
        raise ValueError("fixed B01 requires seed62092801, two workers, one numeric thread")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_joint_transition")
    if admission["sha"] != args.launch_sha:
        raise ValueError("source identity differs from native admission")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    from experiments.candidates.uav_joint_transition.runner import run
    return run(args.out, args.launch_sha, args.workers, args.threads)


if __name__ == "__main__":
    if main()["status"] != "complete":
        raise SystemExit(1)
