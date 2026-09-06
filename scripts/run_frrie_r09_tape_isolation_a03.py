"""Entry for FRRIE R09 A03 tape-isolation arms T0 and T1."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.finite_resource_relational_inductive_efficiency.tape_isolation_a03 import (
    run_arm,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("T0", "T1"), required=True)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--updates", type=int, default=2)
    parser.add_argument("--eval-episodes", type=int, default=256)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--admission-receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.out.is_absolute():
        raise SystemExit("--out must be an absolute path")
    if not args.admission_receipt.is_file():
        raise SystemExit(f"admission receipt missing: {args.admission_receipt}")
    run_arm(
        args.arm,
        args.repeat,
        args.out,
        updates=args.updates,
        eval_episodes=args.eval_episodes,
        launch_sha=args.launch_sha,
        admission_receipt=args.admission_receipt,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
