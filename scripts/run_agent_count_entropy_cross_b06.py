#!/usr/bin/env python3
"""Admission-guarded entry for the fixed B06 zero-fit cross-panel evaluator."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time


COMMAND_START = time.perf_counter()
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.hmasd_admission import require_admission


TAG = "s1_entropy_cross_panel_b06"


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--a-l05-checkpoint", type=Path, required=True)
    parser.add_argument("--a-l0-checkpoint", type=Path, required=True)
    parser.add_argument("--b-l05-checkpoint", type=Path, required=True)
    parser.add_argument("--b-l0-checkpoint", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.name != TAG:
        parser.error(f"--out basename must be {TAG}")

    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")

    from experiments.candidates.agent_count_generalization.entropy_cross_b06.runner import (
        ASSETS,
        TAG as RUNNER_TAG,
        run_study,
    )
    if RUNNER_TAG != TAG or tuple(asset.key for asset in ASSETS) != (
        "a_l05", "a_l0", "b_l05", "b_l0",
    ):
        raise ValueError("B06 CLI/candidate fixed-asset bindings disagree")
    if run_fn is None:
        run_fn = run_study
    return run_fn(
        args.out.resolve(), args.launch_sha, admission,
        {
            "a_l05": args.a_l05_checkpoint.resolve(),
            "a_l0": args.a_l0_checkpoint.resolve(),
            "b_l05": args.b_l05_checkpoint.resolve(),
            "b_l0": args.b_l0_checkpoint.resolve(),
        },
        command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
