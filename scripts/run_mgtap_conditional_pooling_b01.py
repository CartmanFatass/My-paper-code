#!/usr/bin/env python3
"""Run the sole allocated native COND/DENSE master after adjacent admission."""

import os
import time

# The enclosing committed command starts this clock before destination admission.
PROCESS_START = time.monotonic() - (time.time() - float(os.environ["MGTAP_CHAIN_STARTED_UNIX"]))
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.candidates.metric_ground_transport_allocation.mgtap_conditional_pooling_b01.study import MASTER, run_pair


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=(MASTER,), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run_pair(args.seed, args.out, PROCESS_START)
    print(json.dumps({"status": result["status"], "primary": result["primary"]}, allow_nan=False))
    raise SystemExit(0 if result["status"] == "COMPLETE" else 1)
