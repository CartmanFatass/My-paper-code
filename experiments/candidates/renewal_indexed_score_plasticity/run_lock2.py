"""CLI for the complete frozen RISP-B1 revision-07 Lock-2 panel."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


# These must be set before importing NumPy, SciPy, or Torch.
for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


def main() -> None:
    launch_started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    parser.add_argument("--output", type=Path, default=here / "RISP_B1_LOCK2_20260813_07.json")
    parser.add_argument("--checkpoint-dir", type=Path, default=here / "RISP_B1_LOCK2_CHECKPOINTS_20260813_07")
    parser.add_argument("--lock1", type=Path, default=here / "RISP_B1_LOCK1_20260813_07.json")
    parser.add_argument("--activity-marker", type=Path, default=here / "RISP_B1_LOCK2_ACTIVITY_20260813_07.json")
    parser.add_argument("--incomplete-receipt", type=Path, default=here / "RISP_B1_LOCK2_INCOMPLETE_20260813_07.json")
    args = parser.parse_args()

    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from lock2_experiment import LOCK2_SCHEMA, run_lock2

    try:
        result = run_lock2(
            args.output.resolve(),
            args.checkpoint_dir.resolve(),
            args.lock1.resolve(),
            args.activity_marker.resolve(),
            args.incomplete_receipt.resolve(),
            launch_started,
        )
    except BaseException as exc:
        print(json.dumps({
            "schema": LOCK2_SCHEMA,
            "status": "INCOMPLETE_OR_REFUSED",
            "exception_type": type(exc).__name__,
            "reason": str(exc),
            "activity_marker": str(args.activity_marker.resolve()),
            "incomplete_receipt": str(args.incomplete_receipt.resolve()),
        }, sort_keys=True), file=sys.stderr, flush=True)
        raise
    print(json.dumps({
        "schema": LOCK2_SCHEMA,
        "result": str(args.output.resolve()),
        "primary_disposition": result["analysis"]["disposition"]["primary"],
        "valid": result["analysis"]["validity"]["all_conditions_pass"],
        "wall_seconds": result["runtime"]["wall_seconds"],
        "peak_rss_bytes": result["runtime"]["peak_rss_bytes"],
        "anomalies": result["anomalies"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
