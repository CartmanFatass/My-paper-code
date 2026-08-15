"""Run the complete registered OEER-B1 boundary-relay experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.optimizer_entropy_exposure_boundary_relay.experiment import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete deterministic OEER-B1 experiment and retain JSON.")
    parser.add_argument("--output", type=Path, required=True, help="explicit retained-result JSON path")
    parser.add_argument(
        "--activity-witness",
        type=Path,
        default=None,
        help="optional JSON written immediately after the first complete master-seed quartet",
    )
    args = parser.parse_args()
    result = run_experiment(activity_witness_path=args.activity_witness)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
