#!/usr/bin/env python3
"""Admission-guarded fixed B06 checkpoint feedback evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--b04-source", type=Path, required=True)
    parser.add_argument("--b05-source", type=Path, required=True)
    parser.add_argument("--device", choices=("cuda",), default="cuda")
    parser.add_argument("--threads", type=int, choices=(4,), default=4)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    # Admission precedes candidate imports, source reads, output creation and CUDA effects.
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_service_auxiliary")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    from experiments.candidates.uav_service_auxiliary.b06.native import run_native
    return run_native(
        b04_source=args.b04_source,
        b05_source=args.b05_source,
        out=args.out,
        launch_sha=args.launch_sha,
        device_name=args.device,
        threads=args.threads,
    )


if __name__ == "__main__":
    main()
