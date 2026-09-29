#!/usr/bin/env python3
"""Admitted entrypoint for the fixed zero-fit H12000 P/O_H/R panel."""

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
                        help="repeat for all eight fixed common-world seeds")
    parser.add_argument("--workers", type=int, choices=(4,), default=4)
    args = parser.parse_args(argv)
    if args.seed is not None:
        from experiments.candidates.uav_persistent_service.b03.readout import SEEDS
        if tuple(args.seed) != SEEDS:
            parser.error("--seed must list the fixed eight B03 seeds in order")
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_persistent_service")
    if args.launch_sha != admission["sha"]:
        raise ValueError("scientific source SHA differs from admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.uav_persistent_service.b03.batch import run

    result = run(args.out, args.launch_sha, workers=args.workers)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
