#!/usr/bin/env python3
"""Entry point for the engineering-only MGTAP B01 adapter."""

import time
PROCESS_START = time.monotonic()

import os
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[_name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.set_default_dtype(torch.float32)
torch.set_default_device("cpu")

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.runner import main


if __name__ == "__main__":
    raise SystemExit(main(process_start=PROCESS_START))
