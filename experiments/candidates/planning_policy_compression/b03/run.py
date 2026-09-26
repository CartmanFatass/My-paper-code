#!/usr/bin/env python3
"""Admitted B03 O/S/BC retraining on the fixed B02 block0 archive."""

import argparse
import os
from pathlib import Path
import sys
import time

ENTRY_STARTED = time.perf_counter()
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TAG = "b03_osbc_archived_s926001_20260926"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=926001)
    args = parser.parse_args(argv)
    if args.seed != 926001:
        parser.error("B03 initialization seed is fixed at 926001")
    if args.out.name != TAG:
        parser.error(f"B03 output tag is fixed at {TAG}")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="planning_policy_compression")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch-sha disagrees with native admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.planning_policy_compression.b03.study import Config, run_study
    run_study(args.out, args.data, args.launch_sha, Config(), entry_started=ENTRY_STARTED)


if __name__ == "__main__":
    main()
