"""Run the frozen B01 comparison or its one non-target engineering check."""

from time import perf_counter

STARTED = perf_counter()

import argparse
import os
from pathlib import Path
import sys

for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("formal", "engineering-check"), default="formal")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--eval-seed", type=int)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)
    check = args.profile == "engineering-check"
    config = dict(profile=args.profile, namespace="B01-ENGINEERING-CHECK" if check else "VNFC-N7-DIRECT-RETURN-B01-20260905",
                  seed=args.seed if args.seed is not None else (2026090591 if check else 2026090501),
                  eval_seed=args.eval_seed if args.eval_seed is not None else (2026090592 if check else 2026090502),
                  rounds=2 if check else 64, episodes_per_round=32, eval_episodes=8 if check else 64,
                  ppo_epochs=4, minibatch=24, wall_cap=300 if check else 2700)
    from experiments.candidates.variable_n_fleet_churn_n7_direct_b01.experiment import run
    final = run(config, args.out, args.launch_sha, STARTED)
    return 0 if final["within_wall_cap"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
