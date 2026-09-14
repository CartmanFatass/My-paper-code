"""Run one complete CBSC public-stream B01 arm; no engineering profile."""
import time
STARTED = time.perf_counter()

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04.run_direct_public import (
    ARMS, FORMAL_SEED, run_arm,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw-result", type=Path)
    args = parser.parse_args()
    if args.seed != FORMAL_SEED:
        parser.error("seed differs from the prospectively bound fresh pair")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result = run_arm(arm=args.arm, seed=args.seed, output=args.output,
                     launch_sha=sha, raw_result=args.raw_result, started=STARTED)
    print(json.dumps({"object": result["object"], "arm": args.arm,
                      "output": str(args.output), "complete": True}))


if __name__ == "__main__":
    main()
