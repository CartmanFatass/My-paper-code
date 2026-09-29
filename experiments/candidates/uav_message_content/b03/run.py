#!/usr/bin/env python3
"""Admitted B03 evaluation of four frozen UAV content assets."""

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
    parser.add_argument("--assets-root", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.seed != 19461:
        parser.error("B03 fixes invocation seed 19461")
    if str(args.assets_root) != "/home/wu/hmasd-inputs/uav_message_content-b03":
        parser.error("B03 fixes the staged external assets root")
    if str(args.out) != "/home/wu/projects/HMASD/runs/uav_message_content/b03_frozen_assets":
        parser.error("B03 fixes the declared output directory")
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_message_content")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA does not match admission")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    import torch
    torch.set_num_interop_threads(1)
    from experiments.candidates.uav_message_content.b03.study import run_batch

    return run_batch(args.out, args.launch_sha, args.assets_root, args.seed)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
