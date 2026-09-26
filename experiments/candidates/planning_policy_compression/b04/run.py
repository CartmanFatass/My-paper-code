#!/usr/bin/env python3
"""Admitted B04 two-block standalone O/BC own-roll-in study."""

import argparse
import os
from pathlib import Path
import sys
import time

ENTRY_STARTED = time.perf_counter()
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TAG = "b04_standalone_rollin_s926501_20260926"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=926501)
    args = parser.parse_args(argv)
    if args.seed != 926501:
        parser.error("B04 initialization seed is fixed at 926501")
    if args.out.name != TAG:
        parser.error(f"B04 output tag is fixed at {TAG}")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="planning_policy_compression")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch-sha disagrees with native admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.planning_policy_compression.b04.study import Config, run_study
    run_study(args.out, args.launch_sha, Config(), entry_started=ENTRY_STARTED)


if __name__ == "__main__":
    main()
