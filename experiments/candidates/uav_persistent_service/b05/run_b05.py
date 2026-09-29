#!/usr/bin/env python3
"""Admitted service-shift panel against sixteen exact retained R worlds."""

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
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--workers", type=int, choices=(1, 2, 3, 4), default=4)
    args = parser.parse_args(argv)
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_persistent_service")
    if args.launch_sha != admission["sha"]:
        raise ValueError("scientific source SHA differs from admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.uav_persistent_service.b05.readout import SEEDS
    if args.seed is not None and tuple(args.seed) != SEEDS:
        parser.error("--seed must list all sixteen fixed B03/B04 worlds in order")
    from experiments.candidates.uav_persistent_service.b05.batch import run

    result = run(args.out, args.launch_sha, workers=args.workers)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
