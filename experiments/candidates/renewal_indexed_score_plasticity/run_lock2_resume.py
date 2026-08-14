"""Continue the one active RISP-B1 revision-07 campaign from a blind atomic frontier."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    parser.add_argument("--output", type=Path, default=here / "RISP_B1_LOCK2_20260813_07.json")
    parser.add_argument("--checkpoint-dir", type=Path, default=here / "RISP_B1_LOCK2_CHECKPOINTS_20260813_07")
    parser.add_argument("--lock1", type=Path, default=here / "RISP_B1_LOCK1_20260813_07.json")
    parser.add_argument("--activity-marker", type=Path, default=here / "RISP_B1_LOCK2_ACTIVITY_20260813_07.json")
    parser.add_argument("--incomplete-receipt", type=Path, default=here / "RISP_B1_LOCK2_INCOMPLETE_20260813_07.json")
    parser.add_argument("--resume-root", type=Path, default=here / "RISP_B1_LOCK2_RESUME_20260813_07")
    parser.add_argument("--slice-wall-seconds", type=float, default=13_800.0)
    args = parser.parse_args()

    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)

    from lock2_resume import run_resume

    try:
        result = run_resume(
            args.output.resolve(),
            args.checkpoint_dir.resolve(),
            args.lock1.resolve(),
            args.activity_marker.resolve(),
            args.incomplete_receipt.resolve(),
            args.resume_root.resolve(),
            args.slice_wall_seconds,
        )
    except BaseException as exc:
        print(json.dumps({
            "schema": "RISP-B1-LOCK2-RESUME-20260813-07",
            "status": "ENGINEERING_EXCEPTION",
            "exception_type": type(exc).__name__,
            "reason": str(exc),
            "partial_scientific_values_exposed": False,
        }, sort_keys=True), file=sys.stderr, flush=True)
        raise

    public_result = {key: value for key, value in result.items() if key != "analysis"}
    public_result["schema"] = "RISP-B1-LOCK2-RESUME-20260813-07"
    public_result["partial_scientific_values_exposed"] = False
    print(json.dumps(public_result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
