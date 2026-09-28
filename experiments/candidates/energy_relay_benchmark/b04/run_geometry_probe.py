#!/usr/bin/env python3
"""Admission-guarded runner of ``b04_geometry_probe_a01`` (energy_relay_benchmark; zero fits).

Subcommands ``block0`` (trace re-readings + capacity curve), ``block1`` (saved-c06 forward
queries on constructed worlds, identity gate), ``block2`` (32 ROT worlds, full H3000, paired with
the recorded c06 deterministic panel) and ``all`` (block1, then block0 joined to it, then block2).
Seeds: the worlds (``--worlds``, default 955001-955032) and the checkpoint's recorded training
seed; no other randomness is drawn except the fixed ST stream RandomState([world, 1]).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_CHECKPOINT = ROOT / "runs/energy_relay_benchmark/b02_s1_set_a01r/checkpoints/c06"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("block0", "block1", "block2", "all"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--worlds", default="955001-955032")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    # Admission precedes candidate imports, output creation, and torch effects.
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="energy_relay_benchmark")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    from experiments.candidates.energy_relay_benchmark.b02.checkpoint_eval import parse_worlds
    from experiments.candidates.energy_relay_benchmark.b04.probe_run import run

    manifest = run(args.command, out=args.out, launch_sha=args.launch_sha, workers=args.workers,
                   threads=args.threads, worlds=parse_worlds(args.worlds),
                   checkpoint=args.checkpoint, argv=sys.argv if argv is None else argv)
    print(f"{args.command}: wrote {args.out} (git {manifest['git_head']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
