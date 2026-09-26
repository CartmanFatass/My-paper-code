#!/usr/bin/env python3
"""Admission-guarded fixed B03 fit, with exact shared factual/scale artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=("D", "S", "G"))
    parser.add_argument("--seed", type=int, required=True, choices=(912211, 912347))
    parser.add_argument("--device", choices=("cuda",), default="cuda")
    parser.add_argument("--threads", type=int, default=4, choices=(4,))
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--facts", type=Path)
    parser.add_argument("--facts-sha256")
    parser.add_argument("--calibration", type=Path)
    parser.add_argument("--calibration-sha256")
    args = parser.parse_args(argv)
    artifacts = (args.facts, args.facts_sha256, args.calibration, args.calibration_sha256)
    if args.arm != "D" and any(value is None for value in artifacts):
        parser.error("S/G require --facts, --facts-sha256, --calibration and --calibration-sha256")
    if args.arm == "D" and any(value is not None for value in artifacts):
        parser.error("D creates its initial facts and calibration")
    return args


def main(argv=None):
    args = parse_args(argv)
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_service_auxiliary")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    from experiments.candidates.uav_service_auxiliary.b03.native import production_spec, run_native
    return run_native(
        arm=args.arm, out=args.out, launch_sha=args.launch_sha,
        device_name=args.device, threads=args.threads, facts=args.facts,
        facts_sha256=args.facts_sha256, calibration=args.calibration,
        calibration_sha256=args.calibration_sha256, spec=production_spec(args.seed),
    )


if __name__ == "__main__":
    main()
