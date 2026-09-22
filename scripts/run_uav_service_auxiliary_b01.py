#!/usr/bin/env python3
"""Admission-guarded production entry point for UAV service auxiliary B01."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=("detach", "joint"))
    parser.add_argument("--seed", type=int, required=True, choices=(910021,))
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--threads", type=int, default=4, choices=(4,))
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--facts", type=Path)
    parser.add_argument("--facts-sha256")
    args = parser.parse_args(argv)
    if args.arm == "joint" and (args.facts is None or args.facts_sha256 is None):
        parser.error("joint requires --facts and --facts-sha256")
    if args.arm == "detach" and (args.facts is not None or args.facts_sha256 is not None):
        parser.error("detach creates facts and does not accept --facts")
    return args


def main(argv=None):
    args = parse_args(argv)
    # This import and call deliberately precede scientific/native imports and effects.
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_service_auxiliary")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError(
            f"--launch-sha {args.launch_sha} does not match admitted {admission['sha']}"
        )
    from experiments.candidates.uav_service_auxiliary.b01.native import run_native
    return run_native(
        arm=args.arm, out=args.out, launch_sha=args.launch_sha,
        device_name=args.device, threads=args.threads,
        facts=args.facts, facts_sha256=args.facts_sha256,
    )


if __name__ == "__main__":
    main()
