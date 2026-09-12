#!/usr/bin/env python3
"""Run exactly one allocated CADC arm after adjacent destination admission."""

import os
import time

STARTED = time.monotonic()-(time.time()-float(os.environ["CADC_CHAIN_STARTED_UNIX"]))
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
              "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[_name] = "1"
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
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.study import ARMS, MASTER, run_arm

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=(MASTER,), required=True)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run_arm(args.seed, args.arm, args.out, STARTED)
    print(json.dumps({"status": result["status"], "counts": result["counts"], "elapsed_wall": result["elapsed_wall"]}, allow_nan=False))
    raise SystemExit(0 if result["status"] == "COMPLETE" else 1)
