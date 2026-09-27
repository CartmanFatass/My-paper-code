#!/usr/bin/env python3
"""Admission-guarded B01 runner (sequential_coordinator_credit): ``chain_bandit`` at K = 4.

``calibrate``: zero training.  Single-removal statistics of the 12 (beta, s, sigma)
configurations under the uniform and the greedy-optimal policy against the relay host's
coordinates; outputs under ``<out>/calibrate/``.

``first-cell``: the binding corner (beta = .9, s = 1, sigma = .2) and ``--host-matched
beta,s,sigma`` (the DM's reading of the calibration table; refused if equal to the corner);
arms E1, E3, E4, E3*, E4* x two entropy settings x ``--seeds`` seeds x ``--updates`` updates,
exact gradient readings at the E1 snapshots, regret; outputs under ``<out>/first-cell/``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _configuration(text: str) -> tuple[float, int, float]:
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("expected beta,s,sigma")
    try:
        return float(parts[0]), int(parts[1]), float(parts[2])
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid beta,s,sigma: {text}") from exc


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    calibrate = commands.add_parser("calibrate")
    calibrate.add_argument("--out", type=Path, required=True)
    calibrate.add_argument("--launch-sha", required=True)
    cell = commands.add_parser("first-cell")
    cell.add_argument("--out", type=Path, required=True)
    cell.add_argument("--launch-sha", required=True)
    cell.add_argument("--seeds", type=int, default=100)
    cell.add_argument("--updates", type=int, default=300)
    cell.add_argument("--workers", type=int, default=8)
    cell.add_argument("--host-matched", type=_configuration, required=True,
                      help="beta,s,sigma of the host-matched configuration")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    # Admission precedes candidate imports and any output.
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="sequential_coordinator_credit")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    argv_record = sys.argv if argv is None else argv
    if args.command == "calibrate":
        from experiments.candidates.sequential_coordinator_credit.b01.calibration import (
            run_calibrate,
        )

        return run_calibrate(out=args.out, launch_sha=args.launch_sha, argv=argv_record)
    from experiments.candidates.sequential_coordinator_credit.b01.first_cell import (
        run_first_cell,
    )

    return run_first_cell(out=args.out, launch_sha=args.launch_sha, seeds=args.seeds,
                          updates=args.updates, workers=args.workers,
                          host_matched=args.host_matched, argv=argv_record)


if __name__ == "__main__":
    main()
