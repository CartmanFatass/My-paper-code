#!/usr/bin/env python3
"""Admission-guarded fixed CADC RR / FAST_ONLY / NONE C2 evaluation."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys


for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SEED = 9302
TAG = "c2_rr_fast_none_b01_s9302"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.seed != SEED:
        parser.error(f"fixed C2 asset requires seed {SEED}")
    if re.fullmatch(r"[0-9a-f]{40}", args.launch_sha) is None:
        parser.error("--launch-sha requires a lowercase full 40-hex SHA")
    if args.out.name != TAG:
        parser.error(f"--out basename must be {TAG}")
    if args.out.exists():
        permitted = {"launch-manifest.json", "launch-status.json", "admission-preflight.json",
                     "stdout.log", "stderr.log"}
        if any(path.name not in permitted for path in args.out.iterdir()):
            parser.error("existing C2 scientific output")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="delayed_broadcast_timing")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.delayed_broadcast_timing.c2_rr_fast_none_b01.runner import run
    return run(args.out.resolve(), args.launch_sha, dict(admission))


if __name__ == "__main__":
    main()
