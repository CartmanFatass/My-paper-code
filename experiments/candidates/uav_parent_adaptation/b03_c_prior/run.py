#!/usr/bin/env python3
"""Admitted three-fit ordinary-C categorical development; fixed B03 envelope."""

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
    args = parser.parse_args(argv)
    if args.seed != 303031:
        parser.error("B03 fixes first master303031 and all three roots")
    if len(args.launch_sha) != 40 or any(c not in "0123456789abcdef" for c in args.launch_sha):
        parser.error("launch-sha must be a full lowercase Git SHA")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_parent_adaptation")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA differs from admission")
    usage = resource.getrusage(resource.RUSAGE_SELF)
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.uav_parent_adaptation.b03_c_prior.study import run_batch
    return run_batch(args.out, args.launch_sha, start_usage=usage)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
