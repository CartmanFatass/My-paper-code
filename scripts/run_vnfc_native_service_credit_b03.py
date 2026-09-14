"""Execute the one selected N7 native-service temporal-credit training pair."""

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
    parser.add_argument("--seed", type=int, default=2026091201)
    parser.add_argument("--eval-seed", type=int, default=2026091202)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)
    config = dict(profile="formal", namespace="VNFC-N7-NATIVE-SERVICE-CREDIT-B03-20260912",
                  seed=args.seed, eval_seed=args.eval_seed, rounds=64, episodes_per_round=32,
                  eval_episodes=64, ppo_epochs=4, minibatch=24, wall_cap=600, projection_cap=600)
    from experiments.candidates.variable_n_fleet_churn.native_service_credit_b02 import learning
    from experiments.candidates.variable_n_fleet_churn_n7_direct_b01.experiment import run
    final = run(config, args.out, args.launch_sha, STARTED, learner=learning,
                object_name="VNFC-N7-NATIVE-SERVICE-CREDIT-B03", mei=.02)
    return 0 if final["within_wall_cap"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
