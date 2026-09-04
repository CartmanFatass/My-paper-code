"""Analyze the single bounded G18 TD(0) compatibility screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from scripts import run_continuous_service_roster_proxy_g17 as g17


SCHEMA_VERSION = 1
ALGORITHM_ID = "ONE_STEP_TD_BOOTSTRAP_G18"
UPDATES = 100
NUM_ENVS = 8
EVAL_EPISODES = 48
PPO_PASSES = 2
CREDIT_GAMMA = 0.99
GAE_LAMBDA = 0.0
SEED_OFFSET = 101_000

IID_FLOOR = 0.90
HELDOUT_FLOOR = 0.90
GAIN_FLOOR = 0.10
MINIMUM_EPISODE_FLOOR = 0.80
CORRELATION_FLOOR = 0.90
MAE_CEILING = 0.05

COMPATIBLE_BRANCH = "NONFORMAL_TD0_COMPATIBLE_G18"
NOT_COMPATIBLE_BRANCH = "NONFORMAL_TD0_NOT_COMPATIBLE_G18"
INVALID_BRANCH = "INVALID_TD0_COMPATIBILITY_SCREEN_G18"


def select_candidate(metrics: dict[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    passes = (
        float(metrics["iid_mean"]) >= IID_FLOOR
        and float(metrics["heldout_mean"]) >= HELDOUT_FLOOR
        and float(metrics["gain_mean"]) >= GAIN_FLOOR
        and float(metrics["minimum_episode"]) >= MINIMUM_EPISODE_FLOOR
        and float(metrics["minimum_effort_correlation"]) >= CORRELATION_FLOOR
        and float(metrics["minimum_mix_correlation"]) >= CORRELATION_FLOOR
        and float(metrics["maximum_effort_mae"]) <= MAE_CEILING
        and float(metrics["maximum_mix_mae"]) <= MAE_CEILING
    )
    return COMPATIBLE_BRANCH if passes else NOT_COMPATIBLE_BRANCH


def analyze(*, run_root: Path) -> dict[str, Any]:
    training = g17._read_json(run_root / "train_manifest.json")
    evaluation = g17._read_json(run_root / "evaluation_manifest.json")
    base = g17.analyze(run_root=run_root)
    errors = list(base.get("operational_errors", []))
    if training.get("formal") is not False or evaluation.get("formal") is not False:
        errors.append("G18 compatibility screen must be nonformal")
    expected_counts = {
        "replicates": 1,
        "updates": UPDATES,
        "num_envs": NUM_ENVS,
        "eval_episodes": EVAL_EPISODES,
        "ppo_passes": PPO_PASSES,
    }
    if training.get("counts") != expected_counts:
        errors.append("G18 compatibility count mismatch")
    configuration = training.get("configuration", {})
    if (
        configuration.get("credit_gamma") != CREDIT_GAMMA
        or configuration.get("gae_lambda") != GAE_LAMBDA
        or configuration.get("seed_offset") != SEED_OFFSET
        or configuration.get("current_observation_residual") is not True
        or configuration.get("active_count_curriculum") is not False
    ):
        errors.append("G18 compatibility configuration mismatch")
    rows = training.get("replicate_results", [])
    if len(rows) != 1 or rows[0].get("seeds") != g17._replicate_seeds(
        0, seed_offset=SEED_OFFSET
    ):
        errors.append("G18 compatibility seed mismatch")

    final_deterministic = [
        row
        for row in evaluation.get("cells", [])
        if row.get("checkpoint") == "final" and bool(row.get("deterministic"))
    ]
    minimum_episode = float("nan")
    if len(final_deterministic) == 2:
        utilities = np.concatenate(
            [np.asarray(row.get("utility", []), dtype=np.float64) for row in final_deterministic]
        )
        if utilities.shape == (2 * EVAL_EPISODES,) and np.isfinite(utilities).all():
            minimum_episode = float(utilities.min())
        else:
            errors.append("G18 final deterministic episode inventory mismatch")
    else:
        errors.append("G18 final deterministic cell inventory mismatch")

    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        source = base["metrics"]
        metrics.update(
            {
                "iid_mean": float(source["iid_deterministic_utility_ci95"][1]),
                "heldout_mean": float(source["heldout_deterministic_utility_ci95"][1]),
                "gain_mean": float(source["heldout_final_minus_zero_ci95"][1]),
                "minimum_episode": minimum_episode,
                "minimum_effort_correlation": float(source["minimum_effort_correlation"]),
                "minimum_mix_correlation": float(source["minimum_mix_correlation"]),
                "maximum_effort_mae": float(source["maximum_effort_mae"]),
                "maximum_mix_mae": float(source["maximum_mix_mae"]),
                "heldout_stochastic_mean": float(source["heldout_stochastic_mean"]),
                "maximum_replay_error": max(
                    float(value)
                    for value in rows[0]["maximum_replay_errors"].values()
                ),
            }
        )
    branch = select_candidate(metrics)
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": False,
        "source_commit": training.get("source_commit"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "configuration": {
            "credit_gamma": CREDIT_GAMMA,
            "gae_lambda": GAE_LAMBDA,
            "seed_offset": SEED_OFFSET,
        },
        "thresholds": {
            "iid_floor": IID_FLOOR,
            "heldout_floor": HELDOUT_FLOOR,
            "gain_floor": GAIN_FLOOR,
            "minimum_episode_floor": MINIMUM_EPISODE_FLOOR,
            "correlation_floor": CORRELATION_FLOOR,
            "mae_ceiling": MAE_CEILING,
        },
        "interpretation": (
            "bounded credit compatibility only; not formal, delayed-source, or UAV evidence"
        ),
    }
    g17._write_json(run_root / "td0_screen_result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("analyze",))
    parser.add_argument("--run-root", type=Path, required=True)
    arguments = parser.parse_args()
    value = analyze(run_root=arguments.run_root)
    print(
        json.dumps(
            {
                "algorithm": value["algorithm"],
                "status": value["status"],
                "branch": value["branch"],
                "formal": value["formal"],
                "run_root": str(arguments.run_root),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
