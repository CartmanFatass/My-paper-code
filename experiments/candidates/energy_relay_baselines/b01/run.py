#!/usr/bin/env python3
"""Admission-guarded fresh SET fit or c00/c06 development evaluation."""

from __future__ import annotations

import argparse
import faulthandler
import sys
from pathlib import Path


def repository_root() -> Path:
    root = Path(__file__).resolve()
    for parent in root.parents:
        if (parent / "scripts" / "hmasd_admission.py").is_file():
            return parent
    raise RuntimeError("cannot find repository root")


def seed_output(value: str, seed: int) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = repository_root() / path
    path = path.resolve()
    if (path.name != f"seed-{seed}" or path.parent.parent.name != "energy_relay_baselines"
            or path.parent.parent.parent.name != "runs"):
        raise ValueError("--out must be runs/energy_relay_baselines/<tag>/seed-<seed>")
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("train", "evaluate"))
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--out", required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--checkpoint", choices=("c00", "c06"))
    parser.add_argument("--checkpoint-dir", type=Path)
    parser.add_argument("--checkpoint-sha256")
    parser.add_argument("--checkpoint-source-sha")
    parser.add_argument("--worlds", default="955001-955032")
    parser.add_argument("--device", choices=("cpu", "cuda"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--threads", type=int)
    args = parser.parse_args(argv)
    if args.operation == "evaluate" and not all((args.checkpoint_dir, args.checkpoint_sha256,
                                                   args.checkpoint_source_sha)):
        parser.error("evaluate requires --checkpoint-dir, --checkpoint-sha256 and "
                     "--checkpoint-source-sha")
    if args.operation == "train" and any((args.checkpoint, args.checkpoint_dir,
                                          args.checkpoint_sha256, args.checkpoint_source_sha)):
        parser.error("train does not accept checkpoint input")
    if args.operation == "train" and args.worlds != "955001-955032":
        parser.error("train does not accept --worlds")
    out = seed_output(args.out, args.seed)
    threads = args.threads if args.threads is not None else (4 if args.operation == "train" else 2)
    root = repository_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    # Admission precedes candidate imports, environment construction and output creation.
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="energy_relay_baselines")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")

    if args.operation == "train":
        try:
            faulthandler.enable(file=sys.stderr, all_threads=True)
        except (OSError, RuntimeError, ValueError):
            # Some test hosts provide stderr without a usable file descriptor.
            pass

    from experiments.candidates.energy_relay_baselines.b01.configuration import production_spec
    spec = production_spec(args.seed)
    if args.operation == "train":
        from experiments.candidates.energy_relay_baselines.b01.training import run_training
        run_training(out=out, launch_sha=args.launch_sha, spec=spec,
                     device_name=args.device or "cuda", threads=threads,
                     argv=sys.argv if argv is None else [__file__, *argv])
    else:
        from experiments.candidates.energy_relay_benchmark.b02.checkpoint_eval import parse_worlds
        from experiments.candidates.energy_relay_baselines.b01.evaluation import (
            check_worlds, evaluate_checkpoint,
        )
        worlds = check_worlds(parse_worlds(args.worlds))
        if args.checkpoint is not None and args.checkpoint_dir.name != args.checkpoint:
            parser.error("--checkpoint disagrees with --checkpoint-dir")
        evaluate_checkpoint(checkpoint_dir=args.checkpoint_dir,
                            out=out, spec=spec, launch_sha=args.launch_sha,
                            expected_checkpoint_sha256=args.checkpoint_sha256,
                            expected_source_sha=args.checkpoint_source_sha,
                            worlds=worlds, workers=args.workers, threads=threads,
                            device_name=args.device or "cpu",
                            argv=sys.argv if argv is None else [__file__, *argv])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
