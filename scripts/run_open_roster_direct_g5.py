"""Train, evaluate and analyze the open-roster direct G5 MVP."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import random
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_direct import (
    LEARNING_RATE,
    PPO_PASSES,
    REPLAY_TOLERANCE,
    DirectPrimitiveARPolicy,
    collect_direct_trajectory,
    evaluate_direct_policy,
    load_checkpoint,
    maximum_state_difference,
    model_state_copy,
    optimize_direct_update,
    save_checkpoint,
)
from ha_ctse_process.dynamic_roster_testbed import HORIZON, constructive_actions
from ha_ctse_process.open_roster_direct_mvp import (
    EVAL_LEDGER_SEED,
    HELDOUT_CAPACITY,
    HELDOUT_PROFILES,
    TRAIN_CAPACITY,
    TRAIN_LEDGER_SEED,
    TRAIN_PROFILES,
    OpenRosterDynamicEnv,
    make_open_roster_heldout_ledger,
    make_open_roster_training_ledger,
    open_roster_lifecycle_contract_valid,
)


SCHEMA_VERSION = 1
ALGORITHM_ID = "OPEN_ROSTER_DIRECT_MVP_G5"
AUTHORIZATION_TOKEN = "AUTHORIZE_OPEN_ROSTER_DIRECT_MVP_G5_FORMAL_CPU_V1"
FORMAL_REPLICATES = 3
FORMAL_UPDATES = 250
FORMAL_NUM_ENVS = 8
FORMAL_EVAL_EPISODES = 128
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
MODEL_SEED_BASE = 551_000
TRAIN_LEDGER_SEED_BASE = 651_000
ACTION_SEED_BASE = 751_000
EVALUATION_SEED_BASE = 851_000
BOOTSTRAP_SEED = 951_005
IID_ACCESS_FLOOR = 0.90
HELDOUT_ACCESS_FLOOR = 0.90
MIN_REPLICATE_FLOOR = 0.85
STOCHASTIC_MEAN_FLOOR = 0.80


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def configure_runtime(seed: int) -> None:
    random.seed(int(seed))
    np.random.seed(int(seed))
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def _runtime_identity() -> dict[str, Any]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _replicate_seeds(replicate: int) -> dict[str, int]:
    index = int(replicate)
    return {
        "model": MODEL_SEED_BASE + index,
        "train_ledger": TRAIN_LEDGER_SEED_BASE + index,
        "action": ACTION_SEED_BASE + index,
        "evaluation": EVALUATION_SEED_BASE + index,
    }


def _formal_counts_valid(
    *, replicates: int, updates: int, num_envs: int, eval_episodes: int
) -> bool:
    return (
        int(replicates) == FORMAL_REPLICATES
        and int(updates) == FORMAL_UPDATES
        and int(num_envs) == FORMAL_NUM_ENVS
        and int(eval_episodes) == FORMAL_EVAL_EPISODES
    )


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    replicates: int,
    updates: int,
    num_envs: int,
    eval_episodes: int,
) -> dict[str, Any]:
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("formal G5 authorization token mismatch")
        if not _formal_counts_valid(
            replicates=replicates,
            updates=updates,
            num_envs=num_envs,
            eval_episodes=eval_episodes,
        ):
            raise ValueError("formal G5 counts differ from the frozen contract")
    if min(replicates, updates, num_envs, eval_episodes) <= 0:
        raise ValueError("G5 counts must be positive")
    run_root.mkdir(parents=True, exist_ok=False)
    checkpoint_root = run_root / "checkpoints"
    checkpoint_root.mkdir()
    configure_runtime(MODEL_SEED_BASE)
    started = time.perf_counter()
    replicate_rows: list[dict[str, Any]] = []
    for replicate in range(replicates):
        seeds = _replicate_seeds(replicate)
        configure_runtime(seeds["model"])
        model = DirectPrimitiveARPolicy()
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
        zero_state = model_state_copy(model)
        zero_path = checkpoint_root / f"replicate_{replicate}_zero.pt"
        final_path = checkpoint_root / f"replicate_{replicate}_final.pt"
        save_checkpoint(
            zero_path,
            model=model,
            optimizer=optimizer,
            completed_updates=0,
            next_ledger_id=0,
        )
        maximum_errors = {
            "logp_max_error": 0.0,
            "joint_logp_max_error": 0.0,
            "value_max_error": 0.0,
            "hidden_max_error": 0.0,
            "prefix_max_error": 0.0,
        }
        lifecycle_valid = True
        finite = True
        profile_episodes = {profile.name: 0 for profile in TRAIN_PROFILES}
        active_rows = 0
        for update in range(updates):
            first_id = update * num_envs
            ids = tuple(range(first_id, first_id + num_envs))
            trajectory = collect_direct_trajectory(
                model,
                ledger_ids=ids,
                ledger_seed=seeds["train_ledger"],
                action_seed=seeds["action"],
                device=torch.device("cpu"),
                ledger_factory=make_open_roster_training_ledger,
                environment_factory=OpenRosterDynamicEnv,
            )
            lifecycle_valid = lifecycle_valid and open_roster_lifecycle_contract_valid(
                trajectory, ledger_seed=seeds["train_ledger"]
            )
            metrics = optimize_direct_update(
                model,
                optimizer,
                trajectory,
                device=torch.device("cpu"),
                ppo_passes=PPO_PASSES,
            )
            finite = finite and bool(metrics["finite_update"])
            for name in maximum_errors:
                maximum_errors[name] = max(
                    maximum_errors[name], float(metrics[name])
                )
            active_rows += trajectory.active_token_count
            for episode_id in ids:
                profile_episodes[
                    TRAIN_PROFILES[episode_id % len(TRAIN_PROFILES)].name
                ] += 1
            _write_json(
                run_root / "progress.json",
                {
                    "phase": "train",
                    "replicate": replicate,
                    "update": update + 1,
                    "updates": updates,
                },
            )
        save_checkpoint(
            final_path,
            model=model,
            optimizer=optimizer,
            completed_updates=updates,
            next_ledger_id=updates * num_envs,
        )
        replicate_rows.append(
            {
                "replicate": replicate,
                "seeds": seeds,
                "zero_checkpoint": str(zero_path.relative_to(run_root)),
                "final_checkpoint": str(final_path.relative_to(run_root)),
                "environment_steps": updates * num_envs * HORIZON,
                "active_rows": int(active_rows),
                "optimizer_steps": updates * PPO_PASSES,
                "profile_episodes": profile_episodes,
                "maximum_replay_errors": maximum_errors,
                "lifecycle_contract_valid": bool(lifecycle_valid),
                "finite_updates": bool(finite),
                "parameter_drift": maximum_state_difference(
                    zero_state, model_state_copy(model)
                ),
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": bool(formal),
        "authorization_token": authorization_token,
        "source_commit": str(source_commit),
        "runtime": _runtime_identity(),
        "counts": {
            "replicates": replicates,
            "updates": updates,
            "num_envs": num_envs,
            "eval_episodes": eval_episodes,
            "ppo_passes": PPO_PASSES,
        },
        "train_capacity": TRAIN_CAPACITY,
        "train_profiles": [asdict(profile) for profile in TRAIN_PROFILES],
        "replicate_results": replicate_rows,
        "wall_seconds": time.perf_counter() - started,
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _source_controls() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for domain, profiles, maker in (
        ("train", TRAIN_PROFILES, make_open_roster_training_ledger),
        ("heldout", HELDOUT_PROFILES, make_open_roster_heldout_ledger),
    ):
        for episode_id, profile in enumerate(profiles):
            ledger = maker(episode_id)
            environment = OpenRosterDynamicEnv(ledger)
            while environment.time < HORIZON:
                view = environment.observe()
                environment.step(constructive_actions(environment, view))
            outcome = environment.outcome()
            rows.append(
                {
                    "domain": domain,
                    "profile": profile.name,
                    "utility": outcome.utility,
                    "roster_sizes": list(outcome.roster_sizes),
                }
            )
    return {
        "rows": rows,
        "all_constructive_utility_one": all(row["utility"] == 1.0 for row in rows),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    if training.get("status") != "COMPLETE":
        raise ValueError("G5 evaluation requires complete training")
    configure_runtime(MODEL_SEED_BASE)
    formal = bool(training["formal"])
    eval_episodes = int(training["counts"]["eval_episodes"])
    episode_ids = tuple(range(eval_episodes))
    cells: list[dict[str, Any]] = []
    for row in training["replicate_results"]:
        replicate = int(row["replicate"])
        seeds = dict(row["seeds"])
        for checkpoint_kind in ("zero", "final"):
            configure_runtime(int(seeds["model"]))
            model = DirectPrimitiveARPolicy()
            optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
            load_checkpoint(
                run_root / row[f"{checkpoint_kind}_checkpoint"],
                model=model,
                optimizer=optimizer,
            )
            for domain, factory in (
                ("iid", make_open_roster_training_ledger),
                ("heldout", make_open_roster_heldout_ledger),
            ):
                for deterministic in (True, False):
                    values = evaluate_direct_policy(
                        model,
                        episode_ids=episode_ids,
                        deterministic=deterministic,
                        device=torch.device("cpu"),
                        ledger_seed=int(seeds["evaluation"]),
                        action_seed=int(seeds["action"]) + 10_000,
                        ledger_factory=factory,
                        environment_factory=OpenRosterDynamicEnv,
                    )
                    profiles = (
                        TRAIN_PROFILES if domain == "iid" else HELDOUT_PROFILES
                    )
                    cells.append(
                        {
                            "replicate": replicate,
                            "checkpoint": checkpoint_kind,
                            "domain": domain,
                            "deterministic": deterministic,
                            "episode_ids": list(episode_ids),
                            "profile_names": [
                                profiles[index % len(profiles)].name
                                for index in episode_ids
                            ],
                            "persistent": values["persistent"].tolist(),
                            "short": values["short"].tolist(),
                            "utility": values["utility"].tolist(),
                            "persistent_mean": values["persistent_mean"],
                            "short_mean": values["short_mean"],
                            "utility_mean": values["utility_mean"],
                        }
                    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": training["source_commit"],
        "runtime": _runtime_identity(),
        "source_controls": _source_controls(),
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", result)
    return result


def _bootstrap_replicate_ci(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(
        0,
        len(array),
        size=(FORMAL_BOOTSTRAP_REPETITIONS, len(array)),
    )
    means = array[indices].mean(axis=1)
    return [
        float(np.quantile(means, 0.025)),
        float(array.mean()),
        float(np.quantile(means, 0.975)),
    ]


def analyze(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    errors: list[str] = []
    if training.get("status") != "COMPLETE" or evaluation.get("status") != "COMPLETE":
        errors.append("train/evaluate status is incomplete")
    if training.get("source_commit") != evaluation.get("source_commit"):
        errors.append("train/evaluate source mismatch")
    if training.get("formal") != evaluation.get("formal"):
        errors.append("train/evaluate formal identity mismatch")
    if bool(training.get("formal")):
        counts = training.get("counts", {})
        if training.get("authorization_token") != AUTHORIZATION_TOKEN:
            errors.append("formal authorization token mismatch")
        if not _formal_counts_valid(
            replicates=int(counts.get("replicates", -1)),
            updates=int(counts.get("updates", -1)),
            num_envs=int(counts.get("num_envs", -1)),
            eval_episodes=int(counts.get("eval_episodes", -1)),
        ):
            errors.append("formal count contract mismatch")
    runtime = training.get("runtime", {})
    if runtime.get("backend") != "cpu" or runtime.get("torch_threads") != 1:
        errors.append("runtime is not CPU one-thread")
    if not evaluation.get("source_controls", {}).get(
        "all_constructive_utility_one", False
    ):
        errors.append("constructive source control failed")
    for row in training.get("replicate_results", []):
        if not row.get("finite_updates") or not row.get("lifecycle_contract_valid"):
            errors.append(f"replicate {row.get('replicate')} training invariant failed")
        if float(row.get("parameter_drift", 0.0)) <= 0.0:
            errors.append(f"replicate {row.get('replicate')} has zero parameter drift")
        if max(float(value) for value in row["maximum_replay_errors"].values()) > REPLAY_TOLERANCE:
            errors.append(f"replicate {row.get('replicate')} replay tolerance failed")

    def selected(
        *, checkpoint: str, domain: str, deterministic: bool
    ) -> list[dict[str, Any]]:
        return [
            row
            for row in evaluation.get("cells", [])
            if row.get("checkpoint") == checkpoint
            and row.get("domain") == domain
            and bool(row.get("deterministic")) is deterministic
        ]

    final_iid = selected(checkpoint="final", domain="iid", deterministic=True)
    final_heldout = selected(
        checkpoint="final", domain="heldout", deterministic=True
    )
    stochastic_heldout = selected(
        checkpoint="final", domain="heldout", deterministic=False
    )
    zero_heldout = selected(
        checkpoint="zero", domain="heldout", deterministic=True
    )
    expected_replicates = int(training["counts"]["replicates"])
    if not all(
        len(rows) == expected_replicates
        for rows in (final_iid, final_heldout, stochastic_heldout, zero_heldout)
    ):
        errors.append("evaluation cell inventory mismatch")

    metrics: dict[str, Any] = {}
    if not errors:
        iid_means = [float(row["utility_mean"]) for row in final_iid]
        heldout_means = [float(row["utility_mean"]) for row in final_heldout]
        stochastic_means = [
            float(row["utility_mean"]) for row in stochastic_heldout
        ]
        zero_by_replicate = {
            int(row["replicate"]): float(row["utility_mean"])
            for row in zero_heldout
        }
        gains = [
            float(row["utility_mean"]) - zero_by_replicate[int(row["replicate"])]
            for row in final_heldout
        ]
        metrics = {
            "iid_deterministic_utility_ci95": _bootstrap_replicate_ci(iid_means),
            "heldout_deterministic_utility_ci95": _bootstrap_replicate_ci(
                heldout_means
            ),
            "heldout_replicate_means": heldout_means,
            "heldout_min_replicate_mean": min(heldout_means),
            "heldout_stochastic_mean": float(np.mean(stochastic_means)),
            "heldout_final_minus_zero_ci95": _bootstrap_replicate_ci(gains),
        }
    operational_valid = not errors
    if not operational_valid:
        branch = "INVALID_OPEN_ROSTER_DIRECT_G5"
    elif metrics["iid_deterministic_utility_ci95"][0] < IID_ACCESS_FLOOR:
        branch = "NO_IID_ACCESS_OPEN_ROSTER_G5"
    elif metrics["heldout_deterministic_utility_ci95"][0] < HELDOUT_ACCESS_FLOOR:
        branch = "NO_HELDOUT_COUNT_ACCESS_OPEN_ROSTER_G5"
    elif (
        metrics["heldout_min_replicate_mean"] < MIN_REPLICATE_FLOOR
        or metrics["heldout_stochastic_mean"] < STOCHASTIC_MEAN_FLOOR
        or metrics["heldout_final_minus_zero_ci95"][0] <= 0.0
    ):
        branch = "UNSTABLE_OPEN_ROSTER_DIRECT_G5"
    else:
        branch = "USABLE_OPEN_ROSTER_DIRECT_G5"
    formal = bool(training["formal"])
    if not formal and operational_valid:
        branch = "NONFORMAL_OPEN_ROSTER_G5_EXERCISE_COMPLETE"
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "analyze",
        "status": "COMPLETE" if operational_valid else "INVALID",
        "formal": formal,
        "source_commit": training["source_commit"],
        "operational_valid": operational_valid,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "thresholds": {
            "iid_access_floor": IID_ACCESS_FLOOR,
            "heldout_access_floor": HELDOUT_ACCESS_FLOOR,
            "minimum_replicate_floor": MIN_REPLICATE_FLOOR,
            "stochastic_mean_floor": STOCHASTIC_MEAN_FLOOR,
        },
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(*, run_root: Path) -> dict[str, Any]:
    train(
        run_root=run_root,
        source_commit="NONFORMAL_WORKTREE",
        formal=False,
        authorization_token=None,
        replicates=1,
        updates=2,
        num_envs=2,
        eval_episodes=4,
    )
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit", default=None)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token", default=None)
    parser.add_argument("--replicates", type=int, default=FORMAL_REPLICATES)
    parser.add_argument("--updates", type=int, default=FORMAL_UPDATES)
    parser.add_argument("--num-envs", type=int, default=FORMAL_NUM_ENVS)
    parser.add_argument("--eval-episodes", type=int, default=FORMAL_EVAL_EPISODES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "train":
        if args.source_commit is None:
            raise ValueError("train requires --source-commit")
        value = train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=bool(args.formal),
            authorization_token=args.authorization_token,
            replicates=args.replicates,
            updates=args.updates,
            num_envs=args.num_envs,
            eval_episodes=args.eval_episodes,
        )
    elif args.mode == "evaluate":
        value = evaluate(run_root=args.run_root)
    elif args.mode == "analyze":
        value = analyze(run_root=args.run_root)
    else:
        value = exercise(run_root=args.run_root)
    print(
        json.dumps(
            {
                "algorithm": value.get("algorithm"),
                "stage": value.get("stage"),
                "status": value.get("status"),
                "branch": value.get("branch"),
                "formal": value.get("formal"),
                "run_root": str(args.run_root),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
