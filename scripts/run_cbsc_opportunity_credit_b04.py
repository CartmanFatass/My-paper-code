"""One selected CBSC B04 engineering call, or one complete formal arm."""
import argparse
import json
from pathlib import Path
import runpy
import subprocess
import sys
import time

STARTED = time.perf_counter()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04.run import (
    ARMS, OBJECT, expected_seed, run_arm, write_read,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engineering", action="store_true")
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw-result", type=Path)
    args = parser.parse_args()
    if args.seed != expected_seed(args.engineering):
        parser.error("seed differs from selected profile")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if args.engineering:
        if args.arm is not None or args.raw_result is not None:
            parser.error("engineering is the complete combined two-arm call")
        args.output.mkdir(parents=True, exist_ok=False)
        checks = runpy.run_path(str(ROOT / "tests/experiments/candidates/capability_bound_semantic_currentness/opportunity_credit_b04/test_credit.py"))
        checks["test_constructed_credit"]()
        raw = run_arm(arm=ARMS[0], seed=args.seed, output=args.output / "raw",
                      launch_sha=sha, engineering=True, started=STARTED)
        structured = run_arm(arm=ARMS[1], seed=args.seed, output=args.output / "struct",
                             launch_sha=sha, engineering=True, started=STARTED,
                             raw_result=args.output / "raw/summary.json")
        assert raw["counters"]["adam_steps"] + structured["counters"]["adam_steps"] == 32
        transitions = sum(r["counters"]["train_transitions"] + r["evaluation_transitions"]
                          for r in (raw, structured))
        assert transitions == 3040
        result = write_read(args.output / "summary.json", {
            "object": OBJECT, "profile": "ENGINEERING_ONLY", "seed": args.seed,
            "launch_sha": sha, "constructed_checks": "passed", "adam_steps": 32,
            "transitions": transitions, "paired_summary": "struct/paired_summary.json",
            "wall_seconds_through_readback": time.perf_counter() - STARTED})
    else:
        if args.arm is None:
            parser.error("formal arm is required")
        result = run_arm(arm=args.arm, seed=args.seed, output=args.output,
                         launch_sha=sha, raw_result=args.raw_result, started=STARTED)
    print(json.dumps({"object": OBJECT, "output": str(args.output),
                      "profile": result["profile"], "complete": True}))


if __name__ == "__main__":
    main()
