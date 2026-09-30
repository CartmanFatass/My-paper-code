#!/usr/bin/env python3
"""Admitted one-fit recurrence with four new arms and two retained controls."""
import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# The raw evidence remains in its declared canonical store, outside this operation's
# source snapshot. Its five metadata pins and every control raw hash are checked
# by retained.load_retained before construction; there is no CLI input substitution.
RETAINED_ROOT = Path("/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01")


def main(argv=None):
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", required=True, type=int)
    args = parser.parse_args(argv)
    if args.seed != 29344001:
        parser.error("B03 fixes actor initialization to29344001 and all identities in contract.py")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_fleet_adaptation")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA does not match admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    from experiments.candidates.uav_fleet_adaptation.b03.study import run_batch
    return run_batch(args.out, args.launch_sha, retained_out=RETAINED_ROOT,
                     admission=admission, scientific_invocation=True,
                     entry_start=start_wall, entry_cpu=start_cpu)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
