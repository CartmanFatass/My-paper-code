#!/usr/bin/env python3
"""Admission-guarded entry for one fixed B15 confirmation cell."""
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


CELL_BINDINGS = {
    "b1_h6": (994101, "s1_bounded_confirmation_b15_b1_h6_s994101"),
    "b1_set": (994101, "s1_bounded_confirmation_b15_b1_set_s994101"),
    "b2_set": (994102, "s1_bounded_confirmation_b15_b2_set_s994102"),
    "b2_h6": (994102, "s1_bounded_confirmation_b15_b2_h6_s994102"),
    "b3_h6": (994103, "s1_bounded_confirmation_b15_b3_h6_s994103"),
    "b3_set": (994103, "s1_bounded_confirmation_b15_b3_set_s994103"),
}


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", required=True, choices=tuple(CELL_BINDINGS))
    parser.add_argument("--seed", required=True, type=int, choices=(994101, 994102, 994103))
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    expected_seed, expected_tag = CELL_BINDINGS[args.cell]
    if args.seed != expected_seed:
        parser.error(f"--seed for {args.cell} must be {expected_seed}")
    if args.out.name != expected_tag:
        parser.error(f"--out basename must be {expected_tag}")
    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.agent_count_generalization.bounded_confirmation_b15.runner import (
        CELL_BY_KEY, run_fit, spec_for,
    )
    cell = CELL_BY_KEY[args.cell]
    if cell.tag != expected_tag or cell.seed != expected_seed:
        raise ValueError("B15 CLI/candidate cell bindings disagree")
    if run_fn is None:
        run_fn = run_fit
    return run_fn(
        args.out.resolve(), cell, args.launch_sha, admission, spec_for(cell),
        command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
