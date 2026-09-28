#!/usr/bin/env python3
"""Admitted entrypoint for the fixed lawful station-prior B02 comparison."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args(argv)
    if not 1 <= args.workers <= 4 or args.threads != 1:
        parser.error("B02 requires one to four workers and one numeric thread per worker")
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_information_value")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA does not match admission")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    from experiments.candidates.uav_information_value.b02.batch import run

    return run(args.out, args.launch_sha, workers=args.workers, threads=args.threads)


if __name__ == "__main__":
    if main()["status"] != "complete":
        raise SystemExit(1)
