#!/usr/bin/env python3
"""Admission-guarded entry point for the B02 frozen-policy action-law probe."""
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


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--panel-seed-base", type=int, default=982000)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.panel_seed_base != 982000:
        parser.error("B02 binds --panel-seed-base 982000")

    # This is deliberately before importing Torch/candidate code and before any
    # output, environment, or checkpoint access.
    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    if run_fn is None:
        from experiments.candidates.agent_count_generalization.action_law_b02.probe import run_probe
        run_fn = run_probe
    return run_fn(
        args.out.resolve(), args.checkpoint_root.resolve(), args.launch_sha, admission,
        command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
