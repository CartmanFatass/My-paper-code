#!/usr/bin/env python3
"""Admission-guarded B03 Stage 2 runner (energy_relay_benchmark), arm "gas" (GAS-HMASD).

``train``: one GAS fit, programme "GAS-shield-on-1.2M" (200 rollouts of 2 x 3000, production
shield during training, checkpoints c00..c06 by B02's rule, decisions.jsonl per rollout);
``--resume-from checkpoints/cNN`` finishes the same fit from a saved checkpoint into a fresh
``--out`` (optionally pinned to the source launch with ``--resume-source-sha``).  Checkpoint
evaluation is a separate task (not here).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TRAINING_SEEDS = (26092711, 26092731, 925031)   # b03/configuration.py (checked after admission)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train")
    train.add_argument("--seed", type=int, choices=TRAINING_SEEDS, required=True)
    train.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    train.add_argument("--threads", type=int, default=4)
    train.add_argument("--launch-sha", required=True)
    train.add_argument("--out", type=Path, required=True)
    train.add_argument("--resume-from", type=Path, default=None,
                       help="checkpoints/c{ii} directory (agent.pt + record.json) of this recipe")
    train.add_argument("--resume-source-sha", default=None,
                       help="launch SHA the resumed checkpoint's record.json must carry")
    args = parser.parse_args(argv)
    if args.resume_source_sha is not None and args.resume_from is None:
        parser.error("--resume-source-sha requires --resume-from")
    return args


def main(argv=None):
    args = parse_args(argv)
    # Admission precedes candidate imports, output creation, and torch effects.
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="energy_relay_benchmark")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    argv_record = sys.argv if argv is None else argv
    from experiments.candidates.energy_relay_benchmark.b03.configuration import (
        TRAINING_SEEDS as DECLARED, production_spec,
    )
    from experiments.candidates.energy_relay_benchmark.b03.training import run_training

    if tuple(DECLARED) != TRAINING_SEEDS:
        raise RuntimeError(f"runner seeds {TRAINING_SEEDS} != declared {DECLARED}")
    return run_training(out=args.out, launch_sha=args.launch_sha,
                        spec=production_spec(args.seed), device_name=args.device,
                        threads=args.threads, argv=argv_record, resume_from=args.resume_from,
                        resume_source_sha=args.resume_source_sha)


if __name__ == "__main__":
    main()
