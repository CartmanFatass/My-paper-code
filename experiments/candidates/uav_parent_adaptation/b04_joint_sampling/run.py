#!/usr/bin/env python3
"""Admitted B04 collection and separately metered saved-data reading in one operation."""
import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    wall, cpu = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", required=True, type=int)
    args = parser.parse_args(argv)
    if args.seed != 29346091 or args.out.name != "b04_joint_sampling_a01":
        parser.error("the selected B04 seed/tag and complete schedule are fixed")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_parent_adaptation")
    if admission["sha"] != args.launch_sha:
        raise ValueError("launch SHA differs from admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.study import run_batch
    from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.read import read_batch
    batch = run_batch(args.out, args.launch_sha, admission=admission, scientific_invocation=True,
                      entry_wall=wall, entry_cpu=cpu)
    if batch["status"] != "COMPLETE":
        raise RuntimeError("collection did not complete")
    reading = read_batch(args.out)
    print("B04_READ_COMPLETE", reading["status"], flush=True)
    return reading


if __name__ == "__main__":
    if main()["status"] != "VERIFIED":
        raise SystemExit(1)
