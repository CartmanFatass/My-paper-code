#!/usr/bin/env python3
"""Admitted fixed B03 independent partner-exposure replication."""
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
    parser.add_argument("--seed", type=int, default=92561001)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--checkpoint-root", type=Path)
    sources.add_argument("--checkpoints", type=Path, nargs=3,
                         metavar=("SOURCE1", "SOURCE2", "SOURCE3"))
    args = parser.parse_args(argv)
    if args.seed != 92561001:
        parser.error("B03 accepts only the fixed first-block seed 92561001")
    admission = require_admission(__file__, direction="controller_composition")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.controller_composition.b01.bindings import SOURCE
    from experiments.candidates.controller_composition.b03.runner import run_study
    if args.checkpoint_root is not None:
        paths = {n: args.checkpoint_root / SOURCE[n]["tag"] / "F/raw/checkpoint_45.pt" for n in SOURCE}
    else:
        paths = dict(zip(SOURCE, args.checkpoints))
    return (run_fn or run_study)(args.out.resolve(), args.launch_sha, admission,
                                 {n: path.resolve() for n, path in paths.items()},
                                 seed=args.seed, command_start=COMMAND_START)


if __name__ == "__main__":
    main()
