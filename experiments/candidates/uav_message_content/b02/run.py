#!/usr/bin/env python3
"""Admitted fixed B/O/L preserved-content continuation."""

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
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--checkpoint-sha256", required=True)
    args = parser.parse_args(argv)
    if args.seed != 19451:
        parser.error("B02 fixes first continuation seed 19451")
    if str(args.checkpoint) != "/home/wu/projects/HMASD/runs/uav_message_content/b01_s19431/C/final.pt":
        parser.error("B02 fixes the retained C checkpoint path")
    if args.checkpoint_sha256 != "456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad":
        parser.error("B02 fixes the retained C checkpoint digest")
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_message_content")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA does not match admission")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    import torch
    torch.set_num_interop_threads(1)
    from experiments.candidates.uav_message_content.b02.study import run_batch

    return run_batch(args.out, args.launch_sha, args.checkpoint,
                     args.checkpoint_sha256, args.seed)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
