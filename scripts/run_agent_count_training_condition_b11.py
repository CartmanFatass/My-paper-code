#!/usr/bin/env python3
"""Admission-guarded entry for one fixed B11 SET training-condition cell."""
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


TAGS = {
    "t6": "s1_training_condition_b11_t6_s963201",
    "t8": "s1_training_condition_b11_t8_s963201",
}


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", required=True, choices=tuple(TAGS))
    parser.add_argument("--seed", required=True, type=int, choices=(963201,))
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.name != TAGS[args.cell]:
        parser.error(f"--out basename must be {TAGS[args.cell]}")
    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.agent_count_generalization.training_condition_b11.runner import (
        CELL_BY_KEY, run_fit, spec_for,
    )
    cell = CELL_BY_KEY[args.cell]
    if cell.tag != TAGS[args.cell] or args.seed != cell.seed:
        raise ValueError("B11 CLI/candidate cell bindings disagree")
    if run_fn is None:
        run_fn = run_fit
    return run_fn(
        args.out.resolve(), cell, args.launch_sha, admission, spec_for(cell),
        command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
