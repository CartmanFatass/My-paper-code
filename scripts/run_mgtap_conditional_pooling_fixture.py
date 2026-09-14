#!/usr/bin/env python3
"""The sole allocated COND/DENSE encoder fixture; no native/training mode."""

import time
PROCESS_START = time.monotonic()

import argparse
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    # The existing destination preflight precedes imports and encoder construction.
    subprocess.run([sys.executable, str(ROOT / "scripts/hmasd_resource_preflight.py"),
                    "admit-memory", "--out", str(args.output / "admission.json")], check=True)
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
        os.environ[name] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.set_default_dtype(torch.float32)
    torch.set_default_device("cpu")
    from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.conditional_pooling import publish_summary

    scratch = ROOT / "temp/directions/metric_ground_transport_allocation/test/cond_pooling_20260911_8211"
    scratch.mkdir(parents=True, exist_ok=True)
    summary = {"status": "FAIL", "scientific_invocation": False}
    try:
        fixture = runpy.run_path(str(ROOT / "tests/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/test_conditional_pooling.py"))
        summary = fixture["run_fixture"](args.seed, scratch, summary)
    except Exception as error:
        summary["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        # This fixed creator-owned path is inside this checkout's temp directory.
        assert scratch.resolve().is_relative_to((ROOT / "temp").resolve())
        shutil.rmtree(scratch)
        summary.update({"source_sha": args.source_sha, "scratch": str(scratch),
                        "scratch_removed": not scratch.exists(), "threads": 1,
                        "wall_before_summary_seconds": time.monotonic() - PROCESS_START})
        path = publish_summary(args.output / "summary.json", summary)
        assert json.loads(path.read_text(encoding="utf-8")) == summary
    print(json.dumps({"status": summary["status"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
