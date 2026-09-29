#!/usr/bin/env python3
"""Admitted exact seven-arm frozen UAV deployment comparison, with zero fits."""

import argparse
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--parent-checkpoint", required=True, type=Path)
    parser.add_argument("--endpoint-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.seed != 19801:
        parser.error("B01 fixes seed 19801")
    if not args.parent_checkpoint.is_absolute() or not args.endpoint_dir.is_absolute():
        parser.error("checkpoint inputs must be absolute")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_correction_compression")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA differs from admission")
    worker_start = (resource.getrusage(resource.RUSAGE_SELF), time.perf_counter_ns())
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.uav_correction_compression.study import run_batch
    return run_batch(args.out, args.launch_sha, args.parent_checkpoint, args.endpoint_dir,
                     seed=args.seed, worker_start=worker_start)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
