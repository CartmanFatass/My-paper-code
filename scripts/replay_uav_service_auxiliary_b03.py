#!/usr/bin/env python3
"""Admission-guarded, zero-update B03 common-endpoint replay."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True, choices=(912211, 912347))
    parser.add_argument("--device", choices=("cuda",), default="cuda")
    parser.add_argument("--threads", type=int, choices=(4,), default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--training-sha", required=True)
    for arm in ("d", "s", "g"):
        parser.add_argument(f"--{arm}-run", type=Path, required=True)
        parser.add_argument(f"--{arm}-summary-sha256", required=True)
    args = parser.parse_args(argv)
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_service_auxiliary")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    from experiments.candidates.uav_service_auxiliary.b03.endpoint_replay import run_replay
    return run_replay(inputs={arm.upper(): (getattr(args, f"{arm}_run"), getattr(args, f"{arm}_summary_sha256"))
                              for arm in ("d", "s", "g")},
                      seed=args.seed, out=args.out, launch_sha=args.launch_sha,
                      training_sha=args.training_sha,
                      device_name=args.device, threads=args.threads)


if __name__ == "__main__":
    main()
