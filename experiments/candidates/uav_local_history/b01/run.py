#!/usr/bin/env python3
"""Admitted complete C/H local-history comparison."""

import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    entry_start = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", required=True, type=int)
    args = parser.parse_args(argv)
    if args.seed != 29091000:
        parser.error("B01 fixes the first evaluation seed to 29091000")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_local_history")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA does not match admission")
    from experiments.candidates.uav_local_history.b01.study import run_batch

    return run_batch(args.out, args.launch_sha, entry_start=entry_start)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
