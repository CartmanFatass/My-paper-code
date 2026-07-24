"""Configure frozen-G8 evaluation for atomic cohort replacement G14."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.open_roster_atomic_replacement_g14 import (
    DOMAIN_PROFILES,
    LEDGER_FACTORIES,
)
from ha_ctse_process.open_roster_high_churn_g9 import (
    HighChurnEnv,
    expected_roster_schedule,
    high_churn_lifecycle_contract_valid,
)
from scripts import run_open_roster_high_churn_g9 as core


ALGORITHM_ID = "ATOMIC_COHORT_REPLACEMENT_G14"
AUTHORIZATION_TOKEN = "AUTHORIZE_ATOMIC_COHORT_REPLACEMENT_G14_FORMAL_CPU_V1"
INVALID_BRANCH = "INVALID_ATOMIC_COHORT_REPLACEMENT_G14"
NONFORMAL_BRANCH = "NONFORMAL_ATOMIC_REPLACEMENT_G14_EXERCISE_COMPLETE"
FORMAL_REPLICATES = core.FORMAL_REPLICATES
FORMAL_EVAL_EPISODES = 32
FORMAL_BOOTSTRAP_REPETITIONS = core.FORMAL_BOOTSTRAP_REPETITIONS
DOMAIN_LEDGER_SEEDS = {
    "atomic_moderate": 3_881_000,
    "atomic_wide": 3_881_100,
    "mixed_churn": 3_881_200,
}
ACTION_SEED_BASE = 3_981_000
BOOTSTRAP_SEED = 4_081_014
DOMAIN_FLOORS = {
    "atomic_moderate": 0.90,
    "atomic_wide": 0.90,
    "mixed_churn": 0.90,
}
MINIMUM_MIXED_REPLICATE_FLOOR = 0.85
MIXED_STOCHASTIC_MEAN_FLOOR = 0.80
EXPECTED_EVENT_COUNT = 6
DEFAULT_G8_RUN_ROOT = core.DEFAULT_G8_RUN_ROOT


def select_result_branch(metrics: dict[str, object]) -> str:
    if (
        float(metrics["atomic_moderate_deterministic_utility_ci95"][0])
        < DOMAIN_FLOORS["atomic_moderate"]
    ):
        return "NO_ATOMIC_MODERATE_ACCESS_G14"
    if (
        float(metrics["atomic_wide_deterministic_utility_ci95"][0])
        < DOMAIN_FLOORS["atomic_wide"]
    ):
        return "NO_ATOMIC_WIDE_ACCESS_G14"
    if (
        float(metrics["mixed_churn_deterministic_utility_ci95"][0])
        < DOMAIN_FLOORS["mixed_churn"]
    ):
        return "NO_ATOMIC_ULTRA_ACCESS_G14"
    if (
        float(metrics["mixed_churn_min_replicate_mean"])
        < MINIMUM_MIXED_REPLICATE_FLOOR
        or float(metrics["mixed_churn_stochastic_mean"])
        < MIXED_STOCHASTIC_MEAN_FLOOR
    ):
        return "UNSTABLE_ATOMIC_REPLACEMENT_G14"
    return "ROBUST_ATOMIC_COHORT_REPLACEMENT_G14"


def _activate_contract() -> None:
    core.ALGORITHM_ID = ALGORITHM_ID
    core.AUTHORIZATION_TOKEN = AUTHORIZATION_TOKEN
    core.INVALID_BRANCH = INVALID_BRANCH
    core.NONFORMAL_BRANCH = NONFORMAL_BRANCH
    core.FORMAL_EVAL_EPISODES = FORMAL_EVAL_EPISODES
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
    core.EXPECTED_EVENT_COUNT = EXPECTED_EVENT_COUNT
    core.REQUIRE_UNIQUE_PROFILES = True
    core.REQUIRED_EVENT_OPERATIONS = ("joined", "terminally_left")
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
