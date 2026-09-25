#!/usr/bin/env python3
"""Admission-guarded entry for the fixed B20 paired roster-training batch."""
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


BLOCK_SEEDS = {1: 1_016_101, 2: 1_017_101, 3: 1_018_101}


def tag_for(block: int) -> str:
    return f"s1_ordered_roster_confirmation_b20_b{block}_s{BLOCK_SEEDS[block]}"


def main(argv=None, *, run_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", required=True, type=int, choices=tuple(BLOCK_SEEDS))
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seed != BLOCK_SEEDS[args.block]:
        parser.error(f"block {args.block} requires seed {BLOCK_SEEDS[args.block]}")
    tag = tag_for(args.block)
    if args.out.name != tag:
        parser.error(f"--out basename must be {tag}")
    if args.out.exists():
        admitted_files = {"launch-manifest.json", "launch-status.json",
                          "admission-preflight.json", "stdout.log", "stderr.log"}
        scientific = [path.name for path in args.out.iterdir() if path.name not in admitted_files]
        if scientific:
            parser.error(f"existing B20 scientific output: {scientific}")
    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20.bindings import BLOCKS
    if {number: binding.seed for number, binding in BLOCKS.items()} != BLOCK_SEEDS or \
            BLOCKS[args.block].tag != tag:
        raise ValueError("B20 CLI bindings differ from candidate bindings")
    from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20.runner import run_batch
    if run_fn is None:
        run_fn = run_batch
    return run_fn(
        args.out.resolve(), args.launch_sha, admission, args.block,
        command_start=COMMAND_START,
    )


if __name__ == "__main__":
    raise SystemExit(main())
