#!/usr/bin/env python3
"""Admission-guarded B02 Stage 1 runner (energy_relay_benchmark).

``train``: one SET fit, programme "SET-shield-on-1.2M" (200 rollouts of 2 x 3000, production
shield during training, checkpoints c00..c06).  ``evaluate-checkpoint``: one checkpoint with the
B01 evaluator on ``--worlds`` in ``--modes``; the hold-out 957001-957032 needs ``--final``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TRAINING_SEEDS = (925031,)   # b02/configuration.py TRAINING_SEEDS (checked after admission)
MODES = ("deterministic", "stochastic")


def _modes(value: str) -> tuple[str, ...]:
    names = tuple(item.strip() for item in value.split(",") if item.strip())
    if not names or len(set(names)) != len(names) or any(name not in MODES for name in names):
        raise argparse.ArgumentTypeError(f"modes must be a comma list from {MODES}")
    return names


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train")
    train.add_argument("--seed", type=int, choices=TRAINING_SEEDS, required=True)
    train.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    train.add_argument("--threads", type=int, default=4)
    train.add_argument("--launch-sha", required=True)
    train.add_argument("--out", type=Path, required=True)
    evaluate = commands.add_parser("evaluate-checkpoint")
    evaluate.add_argument("--checkpoint", type=Path, required=True,
                          help="checkpoints/c{ii} directory holding agent.pt and record.json")
    evaluate.add_argument("--out", type=Path, required=True,
                          help="run root runs/energy_relay_benchmark/<tag>; writes checkpoint-eval/")
    evaluate.add_argument("--worlds", default="955001-955032")
    evaluate.add_argument("--modes", type=_modes, default=MODES)
    evaluate.add_argument("--final", action="store_true",
                          help="read the once-read hold-out 957001-957032")
    evaluate.add_argument("--launch-sha", required=True)
    evaluate.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 1) // 2)))
    evaluate.add_argument("--threads", type=int, default=2)
    evaluate.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    # Admission precedes candidate imports, output creation, and torch effects.
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="energy_relay_benchmark")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    argv_record = sys.argv if argv is None else argv
    if args.command == "train":
        from experiments.candidates.energy_relay_benchmark.b02.configuration import production_spec
        from experiments.candidates.energy_relay_benchmark.b02.training import run_training

        return run_training(out=args.out, launch_sha=args.launch_sha,
                            spec=production_spec(args.seed), device_name=args.device,
                            threads=args.threads, argv=argv_record)
    from experiments.candidates.energy_relay_benchmark.b02.checkpoint_eval import (
        evaluate_checkpoint, parse_worlds,
    )

    return evaluate_checkpoint(checkpoint_dir=args.checkpoint, out=args.out,
                               worlds=parse_worlds(args.worlds), modes=args.modes,
                               final=args.final, launch_sha=args.launch_sha,
                               workers=args.workers, threads=args.threads,
                               device_name=args.device, argv=argv_record)


if __name__ == "__main__":
    main()
