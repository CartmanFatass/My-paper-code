#!/usr/bin/env python3
"""Admission-guarded B01 zero-new-training reference study (energy_relay_benchmark)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PHASES = ("equivalence", "null", "heuristic-dev", "reference", "grid", "all")
DEFAULT_THREADS = 2
HEURISTICS = ("H1", "H2", "H3")
CONTROLLERS = ("N", *HEURISTICS)


def default_workers() -> int:
    return max(1, min(8, (os.cpu_count() or 1) // 2))


def _controllers(value: str) -> tuple[str, ...]:
    names = tuple(item.strip() for item in value.split(",") if item.strip())
    unknown = [name for name in names if name not in CONTROLLERS]
    if not names or unknown:
        raise argparse.ArgumentTypeError(f"controllers must be a comma list from {CONTROLLERS}")
    return names


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--phase", choices=PHASES, required=True)
    parser.add_argument("--heuristic", choices=HEURISTICS, default="H1",
                        help="variant for --phase reference (Hlocal params) and --phase grid; "
                             "--phase all uses the heuristic-dev selection")
    parser.add_argument("--controllers", type=_controllers, default=None,
                        help="grid controllers for --phase grid (default N,<--heuristic>); "
                             "--phase all uses N + selected heuristic")
    parser.add_argument("--workers", type=int, default=default_workers())
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    # Admission precedes candidate imports, output creation, and torch effects.
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="energy_relay_benchmark")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    from dataclasses import replace

    from experiments.candidates.energy_relay_benchmark.b01.native import B01Spec, run_native

    spec = replace(B01Spec(), heuristic=args.heuristic,
                   controllers=None if args.controllers is None else tuple(args.controllers),
                   workers=int(args.workers), threads=int(args.threads))
    return run_native(out=args.out, launch_sha=args.launch_sha, checkpoint=args.checkpoint,
                      phase=args.phase, spec=spec, device_name=args.device,
                      argv=sys.argv if argv is None else argv)


if __name__ == "__main__":
    main()
