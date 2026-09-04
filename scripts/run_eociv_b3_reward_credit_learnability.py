"""Run the candidate-local EOCIV-B3 reward-credit experiment."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.eociv_lite.reward_credit_learnability import (
    run_experiment,
    write_result,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--output")
    args = parser.parse_args()
    # The registered model performs tiny recurrent matrix operations.  The
    # process-isolated experiment uses one CPU thread to avoid Windows thread
    # pool scheduling overhead without mutating the reusable module API.
    torch.set_num_threads(1)
    result = run_experiment(args.mode)
    if args.output:
        write_result(result, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
