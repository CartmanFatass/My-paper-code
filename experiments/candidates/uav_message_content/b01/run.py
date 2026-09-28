#!/usr/bin/env python3
"""Admitted fixed C/H/L seven-float content and motion study."""

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=19431)
    args = parser.parse_args(argv)
    if args.seed != 19431:
        parser.error("B01 fixes seed 19431")
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_message_content")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA does not match admission")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    from experiments.candidates.uav_message_content.b01.study import run_batch

    return run_batch(args.out, args.launch_sha, args.seed)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
