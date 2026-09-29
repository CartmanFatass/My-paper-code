#!/usr/bin/env python3
"""Admitted fixed S_eta/Q32 six-fit study and pure compact reader."""
import time
import resource

PROCESS_START = time.monotonic()
_cpu = resource.getrusage(resource.RUSAGE_SELF)
CPU_START = (_cpu.ru_utime, _cpu.ru_stime)

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    batch = sub.add_parser("batch")
    batch.add_argument("--out", required=True, type=Path)
    batch.add_argument("--launch-sha", required=True)
    reader = sub.add_parser("read")
    reader.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.mode == "read":
        from experiments.candidates.tail_return_distributional_learning.b03_eta.study import read_batch
        result = read_batch(args.out)
        print(result["recurrence"])
        return 0
    if not args.launch_sha or not args.out.is_absolute():
        parser.error("batch requires an absolute output directory and nonempty launch SHA")
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
        os.environ[name] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="tail_return_distributional_learning")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA does not match admission")
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.set_default_dtype(torch.float32)
    torch.set_default_device("cpu")
    from experiments.candidates.tail_return_distributional_learning.b03_eta.study import run_batch
    result = run_batch(args.out, args.launch_sha, entry_start=PROCESS_START, entry_cpu=CPU_START)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
