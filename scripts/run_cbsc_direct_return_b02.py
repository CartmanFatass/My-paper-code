"""One complete RAW or STRUCT invocation of CBSC direct-return B02."""
import argparse
from pathlib import Path
import subprocess
import sys
import time

STARTED = time.perf_counter()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.capability_bound_semantic_currentness.direct_return_b02 import ARMS, run_arm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--seed", type=int, default=21203)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw-result", type=Path)
    args = parser.parse_args()
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result = run_arm(arm=args.arm, seed=args.seed, output=args.output,
                     raw_result=args.raw_result, launch_sha=sha, started=STARTED)
    print({"arm": result["arm"], "counters": result["counters"], "cost": result["cost"]})


if __name__ == "__main__":
    main()
