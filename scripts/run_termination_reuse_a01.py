#!/usr/bin/env python3
"""Run one admitted, prospectively fixed A01 arm/seed."""

import argparse
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hmasd_admission import require_admission


def main(argv=None):
    start = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("one_step", "qbeta", "retrace"), required=True)
    parser.add_argument("--seed", type=int, choices=(91021, 91022, 91023), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)
    admission = require_admission(__file__, direction="termination_rule_experience_reuse")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS"):
        os.environ[key] = "1"
    # Import/construct the scientific path only after native admission.
    from experiments.candidates.termination_rule_experience_reuse.off_termination_a01.study import (
        Config, run_study,
    )
    result = run_study(Config(arm=args.arm, seed=args.seed), args.out, admission, start)
    print(f"status={result['status']} arm={args.arm} seed={args.seed}", flush=True)
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
