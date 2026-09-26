#!/usr/bin/env python3
"""Admission-guarded entry for one fixed B04 entropy-zero cell."""
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
    "h6_zero": "s1_entropy_b04_h6_zero_s942201",
    "set_zero": "s1_entropy_b04_set_zero_s943201",
}


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", choices=tuple(CELL_BINDINGS), required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    tag = CELL_BINDINGS[args.cell]
    if args.out.name != tag:
        parser.error(f"--out basename must be {tag}")

    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.agent_count_generalization.entropy_b04.runner import (
        CELL_BY_KEY, run_fit,
    )
    cell = CELL_BY_KEY[args.cell]
    if cell.tag != tag:
        raise ValueError("B04 CLI/candidate fixed-cell bindings disagree")
    if run_fn is None:
        run_fn = run_fit
    return run_fn(
        args.out.resolve(), cell, args.launch_sha, admission,
        command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
