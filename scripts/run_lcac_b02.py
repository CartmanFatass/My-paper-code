"""Run the single fixed LCAC-B02 pair after external actual-node admission."""
import argparse
from pathlib import Path
import sys
import time

START = time.monotonic()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PLAN = dict(seed=9412, train_episodes=1024, eval_episodes=32, eval_reset_offset=3000,
            object_id="LCAC_B02_1024",
            card_path="docs/research/candidates/learned_counterfactual_agent_credit/LCAC_B02_SCIENCE_CARD_20260914.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from experiments.candidates.learned_counterfactual_agent_credit.lcac_b01.study import run_pair
    result = run_pair(args.output, start=START, **PLAN)
    print(f"complete={result['complete']} summary={args.output / 'summary.json'}", flush=True)
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
