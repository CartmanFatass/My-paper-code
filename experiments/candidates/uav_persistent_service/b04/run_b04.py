#!/usr/bin/env python3
"""Admitted R-only B04 entry against the original B02 control root."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, action="append",
                        help="repeat for all eight fixed original B02 seeds")
    parser.add_argument("--workers", type=int, choices=(4,), default=4)
    args = parser.parse_args(argv)
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_persistent_service")
    if args.launch_sha != admission["sha"]:
        raise ValueError("scientific source SHA differs from admission")
    from experiments.candidates.uav_persistent_service.b04.binding import SEEDS
    if args.seed is not None and tuple(args.seed) != SEEDS:
        parser.error("--seed must list the fixed eight original B02 seeds in order")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.uav_persistent_service.b04.batch import run

    result = run(args.out, args.launch_sha, workers=args.workers)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
