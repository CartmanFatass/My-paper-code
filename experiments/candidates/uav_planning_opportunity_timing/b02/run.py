#!/usr/bin/env python3
"""Admitted complete rolling timing study, with no resume/retry/scientific-size switches."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--launch-sha", required=True)
    p.add_argument("--seed", required=True, type=int)
    return p


def main(argv=None):
    started = time.monotonic()
    p = parser()
    args = p.parse_args(argv)
    if args.seed != 29524000 or not args.out.is_absolute():
        p.error("fixed timing identity seed29524000 and absolute admitted output required")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_planning_opportunity_timing")
    if admission["sha"] != args.launch_sha:
        raise ValueError("launch/source SHA differs from admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
        os.environ[name] = "1"
    try:
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        from experiments.candidates.uav_planning_opportunity_timing.b02.study import run_study
        return run_study(args, admission, started)
    except BaseException as error:
        args.out.mkdir(parents=True, exist_ok=True)
        path = args.out / "runner-failure.json"
        with path.open("x") as stream:
            json.dump({"status": "FAILED_CLOSED", "purchase_closed": True, "type": type(error).__name__,
                       "message": str(error), "traceback": traceback.format_exc(),
                       "elapsed_runner_wall_seconds": time.monotonic() - started}, stream, indent=2)
            stream.write("\n")
        raise


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
