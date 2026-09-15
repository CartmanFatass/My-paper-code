"""Run the single LCAC-B01 pair after external actual-node resource admission."""
import argparse
from pathlib import Path
import sys
import time

START = time.monotonic()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=9411, choices=(9411,))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from experiments.candidates.learned_counterfactual_agent_credit.lcac_b01.study import run_pair
    result = run_pair(args.output, args.seed, start=START)
    print(f"complete={result['complete']} summary={args.output / 'summary.json'}", flush=True)
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
