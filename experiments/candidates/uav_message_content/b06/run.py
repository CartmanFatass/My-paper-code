#!/usr/bin/env python3
"""Admitted six-fit constant-versus-state-dependent calibration study."""

import argparse
import os
from pathlib import Path
import resource
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--checkpoint-sha256", required=True)
    args = parser.parse_args(argv)
    if args.seed != 19701:
        parser.error("B06 fixes first continuation master19701")
    if args.checkpoint_sha256 != "34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2":
        parser.error("B06 fixes retained B19451")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_message_content")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA differs from admission")
    start_usage = resource.getrusage(resource.RUSAGE_SELF)
    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.uav_message_content.b06.study import run_batch

    return run_batch(args.out, args.launch_sha, args.checkpoint, args.checkpoint_sha256,
                     seed=args.seed, start_usage=start_usage)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
