#!/usr/bin/env python3
"""Admitted fixed five-block B02 planning-policy confirmation."""

import argparse
import os
from pathlib import Path
import sys
import time

ENTRY_STARTED = time.perf_counter()
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TAG = "b02_confirm_s925951_20260925"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=925951)
    args = parser.parse_args(argv)
    if args.seed != 925951:
        parser.error("B02 training seed is frozen at 925951")
    if args.out.name != TAG:
        parser.error(f"B02 output tag is frozen at {TAG}")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="planning_policy_compression")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch-sha disagrees with native admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.planning_policy_compression.b02.study import Config, run_study
    run_study(args.out, args.launch_sha, Config(), entry_started=ENTRY_STARTED)


if __name__ == "__main__":
    main()
