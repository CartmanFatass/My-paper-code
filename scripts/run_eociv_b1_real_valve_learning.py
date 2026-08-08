"""Run the candidate-local EOCIV-B1 real valve-learning experiment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.eociv_lite.real_valve_learning import (
    run_experiment,
    write_result,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = run_experiment(args.mode)
    if args.output:
        write_result(result, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
