#!/usr/bin/env python3
"""Admitted complete B07 codec/native/reader package; fixed scientific dimensions."""

import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--launch-sha", required=True)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--input-manifest", required=True, type=Path)
    p.add_argument("--input-manifest-sha256", required=True)
    p.add_argument("--d-checkpoint", required=True, type=Path)
    p.add_argument("--d-checkpoint-sha256", required=True)
    p.add_argument("--b-checkpoint", required=True, type=Path)
    p.add_argument("--b-checkpoint-sha256", required=True)
    return p


def main(argv=None):
    start_wall, start_cpu = time.monotonic(), time.process_time()
    p = parser()
    args = p.parse_args(argv)
    if args.seed != 19811:
        p.error("B07 fixes seeds19811/19812/19813; --seed names the first")
    if any(not getattr(args, key).is_absolute() for key in ("out", "input_manifest", "d_checkpoint", "b_checkpoint")):
        p.error("B07 requires absolute output and input paths")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_message_content")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA differs from admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.uav_message_content.b07.study import run_batch
    return run_batch(args, start_wall=start_wall, start_cpu=start_cpu)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
