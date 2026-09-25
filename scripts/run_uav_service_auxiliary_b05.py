#!/usr/bin/env python3
"""Admission-guarded fixed B05 native/risk-reweighted recurrence."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=("N", "R"))
    parser.add_argument("--seed", required=True, type=int, choices=(914173,))
    parser.add_argument("--device", choices=("cuda",), default="cuda")
    parser.add_argument("--threads", type=int, choices=(4,), default=4)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_service_auxiliary")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    from experiments.candidates.uav_service_auxiliary.b05.native import production_spec, run_native
    return run_native(arm=args.arm, out=args.out, launch_sha=args.launch_sha,
                      device_name=args.device, threads=args.threads, spec=production_spec(args.seed))


if __name__ == "__main__":
    main()
