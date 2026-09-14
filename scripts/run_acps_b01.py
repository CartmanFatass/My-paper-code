#!/usr/bin/env python3
"""Run one allocated ACPS-B01 arm or reduce the two preserved summaries."""
import os
import time

PROCESS_START = time.monotonic() - max(0., time.time() - float(
    os.environ.get("ACPS_ARM_WALL_START", time.time())))
for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse
import json
from pathlib import Path
import sys

import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.set_default_dtype(torch.float32)
torch.set_default_device("cpu")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.actuator_conditioned_partial_sharing.acps_b01.study import (
    MASTER, primary, run_arm,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--arm", choices=("SHARED", "ACPS"))
    mode.add_argument("--reduce", nargs=2, type=Path)
    parser.add_argument("--seed", type=int, default=MASTER, choices=[MASTER])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.reduce:
        result = primary([json.loads(path.read_text(encoding="utf-8")) for path in args.reduce])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps(result))
        return 0 if result["complete"] else 1
    result = run_arm(args.arm, args.seed, args.output, PROCESS_START)
    print(json.dumps(dict(arm=args.arm, status=result["status"], counts=result["counts"])))
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
