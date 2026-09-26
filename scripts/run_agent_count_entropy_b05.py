#!/usr/bin/env python3
"""Admission-guarded entry for one fixed B05 SET entropy cell."""
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
    "set_l05": "s1_entropy_b05_set_l05_s953201",
    "set_l0": "s1_entropy_b05_set_l0_s953201",
}


def _sha256(value: str) -> str:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise argparse.ArgumentTypeError(
            "must be 64 lowercase hexadecimal SHA-256 characters"
        )
    return value


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", choices=tuple(CELL_BINDINGS), required=True)
    parser.add_argument("--seed", type=int, choices=(953201,), required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--control-summary", type=Path)
    parser.add_argument("--control-sha256", type=_sha256)
    args = parser.parse_args(argv)

    tag = CELL_BINDINGS[args.cell]
    if args.out.name != tag:
        parser.error(f"--out basename must be {tag}")
    has_path = args.control_summary is not None
    has_digest = args.control_sha256 is not None
    if args.cell == "set_l0" and not (has_path and has_digest):
        parser.error("set_l0 requires --control-summary and --control-sha256")
    if args.cell == "set_l05" and (has_path or has_digest):
        parser.error("set_l05 rejects control-summary arguments")
    if has_path != has_digest:
        parser.error("control summary path and SHA-256 must be supplied together")

    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.agent_count_generalization.entropy_b05.runner import (
        CELL_BY_KEY,
        ControlBinding,
        run_fit,
    )
    cell = CELL_BY_KEY[args.cell]
    if cell.tag != tag or cell.seed != args.seed:
        raise ValueError("B05 CLI/candidate fixed-cell bindings disagree")
    binding = (
        ControlBinding(args.control_summary.resolve(), args.control_sha256)
        if has_path else None
    )
    if run_fn is None:
        run_fn = run_fit
    return run_fn(
        args.out.resolve(), cell, args.launch_sha, admission,
        command_start=COMMAND_START, control_binding=binding,
    )


if __name__ == "__main__":
    raise SystemExit(main())
