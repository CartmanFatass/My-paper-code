"""Configure the frozen-G8 evaluation core for scale-by-churn G10."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.open_roster_high_churn_g9 import (
    HighChurnEnv,
    expected_roster_schedule,
    high_churn_lifecycle_contract_valid,
)
from ha_ctse_process.open_roster_scale_churn_g10 import (
    DOMAIN_PROFILES,
    LEDGER_FACTORIES,
)
from scripts import run_open_roster_high_churn_g9 as core


ALGORITHM_ID = "SCALE_CHURN_COMPOSITION_G10"
AUTHORIZATION_TOKEN = "AUTHORIZE_SCALE_CHURN_COMPOSITION_G10_FORMAL_CPU_V1"
INVALID_BRANCH = "INVALID_SCALE_CHURN_COMPOSITION_G10"
NONFORMAL_BRANCH = "NONFORMAL_SCALE_CHURN_G10_EXERCISE_COMPLETE"
FORMAL_REPLICATES = core.FORMAL_REPLICATES
FORMAL_EVAL_EPISODES = core.FORMAL_EVAL_EPISODES
FORMAL_BOOTSTRAP_REPETITIONS = core.FORMAL_BOOTSTRAP_REPETITIONS
DOMAIN_LEDGER_SEEDS = {
    "moderate_scale_churn": 2_381_000,
    "far_scale_churn": 2_381_100,
    "mixed_churn": 2_381_200,
}
ACTION_SEED_BASE = 2_481_000
BOOTSTRAP_SEED = 2_581_010
DOMAIN_FLOORS = {
    "moderate_scale_churn": 0.90,
    "far_scale_churn": 0.90,
    "mixed_churn": 0.90,
}
MINIMUM_MIXED_REPLICATE_FLOOR = 0.85
MIXED_STOCHASTIC_MEAN_FLOOR = 0.80
DEFAULT_G8_RUN_ROOT = core.DEFAULT_G8_RUN_ROOT


def select_result_branch(metrics: dict[str, object]) -> str:
    if (
        float(metrics["moderate_scale_churn_deterministic_utility_ci95"][0])
        < DOMAIN_FLOORS["moderate_scale_churn"]
    ):
        return "NO_MODERATE_SCALE_CHURN_ACCESS_G10"
    if (
        float(metrics["far_scale_churn_deterministic_utility_ci95"][0])
        < DOMAIN_FLOORS["far_scale_churn"]
    ):
        return "NO_FAR_SCALE_CHURN_ACCESS_G10"
    if (
        float(metrics["mixed_churn_deterministic_utility_ci95"][0])
        < DOMAIN_FLOORS["mixed_churn"]
    ):
        return "NO_MIXED_SCALE_CHURN_ACCESS_G10"
    if (
        float(metrics["mixed_churn_min_replicate_mean"])
        < MINIMUM_MIXED_REPLICATE_FLOOR
        or float(metrics["mixed_churn_stochastic_mean"])
        < MIXED_STOCHASTIC_MEAN_FLOOR
    ):
        return "UNSTABLE_SCALE_CHURN_COMPOSITION_G10"
    return "ROBUST_SCALE_CHURN_COMPOSITION_G10"


def _activate_contract() -> None:
    core.ALGORITHM_ID = ALGORITHM_ID
    core.AUTHORIZATION_TOKEN = AUTHORIZATION_TOKEN
    core.INVALID_BRANCH = INVALID_BRANCH
    core.NONFORMAL_BRANCH = NONFORMAL_BRANCH
    core.DOMAIN_PROFILES = DOMAIN_PROFILES
    core.LEDGER_FACTORIES = LEDGER_FACTORIES
    core.HighChurnEnv = HighChurnEnv
    core.expected_roster_schedule = expected_roster_schedule
    core.high_churn_lifecycle_contract_valid = high_churn_lifecycle_contract_valid
    core.DOMAIN_LEDGER_SEEDS = DOMAIN_LEDGER_SEEDS
    core.ACTION_SEED_BASE = ACTION_SEED_BASE
    core.BOOTSTRAP_SEED = BOOTSTRAP_SEED
    core.DOMAIN_FLOORS = DOMAIN_FLOORS
    core.MINIMUM_MIXED_REPLICATE_FLOOR = MINIMUM_MIXED_REPLICATE_FLOOR
    core.MIXED_STOCHASTIC_MEAN_FLOOR = MIXED_STOCHASTIC_MEAN_FLOOR
    core.select_result_branch = select_result_branch


_activate_contract()

_read_json = core._read_json
_write_json = core._write_json
_model = core._model
train = core.train
evaluate = core.evaluate
analyze = core.analyze
exercise = core.exercise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit", default=None)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token", default=None)
    parser.add_argument("--g8-run-root", type=Path, default=DEFAULT_G8_RUN_ROOT)
    parser.add_argument("--replicates", type=int, default=FORMAL_REPLICATES)
    parser.add_argument("--eval-episodes", type=int, default=FORMAL_EVAL_EPISODES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "train":
        if args.source_commit is None:
            raise ValueError("train requires --source-commit")
        result = train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            g8_run_root=args.g8_run_root,
            replicates=args.replicates,
            eval_episodes=args.eval_episodes,
        )
    elif args.mode == "evaluate":
        result = evaluate(run_root=args.run_root)
    elif args.mode == "analyze":
        result = analyze(run_root=args.run_root)
    else:
        result = exercise(run_root=args.run_root, g8_run_root=args.g8_run_root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
