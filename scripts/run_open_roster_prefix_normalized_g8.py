"""Train, evaluate, and analyze prefix-normalized open-roster G8."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import re
import sys
import time
from typing import Any, Callable

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
    HELDOUT_PROFILES,
    TRAIN_PROFILES,
    OpenRosterDynamicEnv,
    make_open_roster_heldout_ledger,
    make_open_roster_training_ledger,
    open_roster_lifecycle_contract_valid,
)
from ha_ctse_process.open_roster_prefix_normalized_g8 import (
    DOMAIN_PROFILES,
    LEDGER_FACTORIES,
    BeyondCountEnv,
)


SCHEMA_VERSION = 1
ALGORITHM_ID = "PREFIX_NORMALIZED_OPEN_ROSTER_G8"
AUTHORIZATION_TOKEN = "AUTHORIZE_PREFIX_NORMALIZED_OPEN_ROSTER_G8_FORMAL_CPU_V1"
SELECTED_REPRESENTATION = {
    "active_aggregation": "sum",
    "count_coordinate": "log1p",
    "autoregressive_prefix": "active_fraction",
}
FORMAL_REPLICATES = 3
FORMAL_UPDATES = 250
FORMAL_NUM_ENVS = 8
FORMAL_EVAL_EPISODES = 128
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
MODEL_SEED_BASE = 1_381_000
TRAIN_LEDGER_SEED_BASE = 1_481_000
ACTION_SEED_BASE = 1_581_000
EVALUATION_SEED_BASE = 1_681_000
DOMAIN_LEDGER_SEEDS = {
    "iid": 1_781_000,
    "heldout": 1_781_100,
    "moderate_beyond": 1_781_200,
    "far_beyond": 1_781_300,
    "joint": 1_781_400,
}
BOOTSTRAP_SEED = 1_881_008
DOMAIN_FLOORS = {
    "iid": 0.90,
    "heldout": 0.90,
    "moderate_beyond": 0.90,
    "far_beyond": 0.90,
    "joint": 0.90,
}
MINIMUM_JOINT_REPLICATE_FLOOR = 0.85
JOINT_STOCHASTIC_MEAN_FLOOR = 0.80
EXPECTED_TORCH = "2.7.0+cpu"


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


def _model() -> DirectPrimitiveARPolicy:
    return DirectPrimitiveARPolicy(
        autoregressive_prefix=SELECTED_REPRESENTATION["autoregressive_prefix"]
    )


def _replicate_seeds(replicate: int) -> dict[str, int]:
    index = int(replicate)
    return {
        "model": MODEL_SEED_BASE + index,
        "train_ledger": TRAIN_LEDGER_SEED_BASE + index,
        "action": ACTION_SEED_BASE + index,
        "evaluation": EVALUATION_SEED_BASE + index,
    }


def _domain_spec(
    domain: str,
) -> tuple[Callable[..., Any], Callable[[Any], Any], tuple[Any, ...]]:
    if domain == "iid":
        return (
            make_open_roster_training_ledger,
            OpenRosterDynamicEnv,
            TRAIN_PROFILES,
        )
    if domain == "heldout":
        return (
            make_open_roster_heldout_ledger,
            OpenRosterDynamicEnv,
            HELDOUT_PROFILES,
        )
    if domain not in LEDGER_FACTORIES:
        raise ValueError(f"unknown G8 domain: {domain}")
    return (
        LEDGER_FACTORIES[domain],
        BeyondCountEnv,
        DOMAIN_PROFILES[domain],
    )


def _train_one_model(
    *,
    updates: int,
    num_envs: int,
    seeds: dict[str, int],
) -> tuple[DirectPrimitiveARPolicy, torch.optim.Optimizer, dict[str, Any]]:
    configure_runtime(seeds["model"])
    model = _model()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    maximum_errors = {
        "logp_max_error": 0.0,
        "joint_logp_max_error": 0.0,
        "value_max_error": 0.0,
        "hidden_max_error": 0.0,
        "prefix_max_error": 0.0,
    }
    lifecycle_valid = True
    finite = True
    for update in range(int(updates)):
        ids = tuple(range(update * int(num_envs), (update + 1) * int(num_envs)))
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
            maximum_errors[name] = max(maximum_errors[name], float(metrics[name]))
    return model, optimizer, {
        "finite_updates": bool(finite),
        "lifecycle_contract_valid": bool(lifecycle_valid),
        "maximum_replay_errors": maximum_errors,
    }


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
            raise ValueError("formal G8 authorization token mismatch")
        if (
            replicates != FORMAL_REPLICATES
            or updates != FORMAL_UPDATES
            or num_envs != FORMAL_NUM_ENVS
            or eval_episodes != FORMAL_EVAL_EPISODES
        ):
            raise ValueError("formal G8 counts differ from the frozen contract")
        if re.fullmatch(r"[0-9a-f]{40}", str(source_commit)) is None:
            raise ValueError("formal G8 source commit must be full lowercase SHA-1")
    if min(replicates, updates, num_envs, eval_episodes) <= 0:
        raise ValueError("G8 counts must be positive")
    run_root.mkdir(parents=True, exist_ok=False)
    checkpoint_root = run_root / "checkpoints"
    checkpoint_root.mkdir()
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for replicate in range(replicates):
        seeds = _replicate_seeds(replicate)
        configure_runtime(seeds["model"])
        zero_model = _model()
        zero_optimizer = torch.optim.Adam(zero_model.parameters(), lr=LEARNING_RATE)
        zero_state = model_state_copy(zero_model)
        zero_path = checkpoint_root / f"replicate_{replicate}_zero.pt"
        final_path = checkpoint_root / f"replicate_{replicate}_final.pt"
        save_checkpoint(
            zero_path,
            model=zero_model,
            optimizer=zero_optimizer,
            completed_updates=0,
            next_ledger_id=0,
        )
        model, optimizer, diagnostics = _train_one_model(
            updates=updates,
            num_envs=num_envs,
            seeds=seeds,
        )
        save_checkpoint(
            final_path,
            model=model,
            optimizer=optimizer,
            completed_updates=updates,
            next_ledger_id=updates * num_envs,
        )
        rows.append(
            {
                "replicate": replicate,
                "seeds": seeds,
                "zero_checkpoint": str(zero_path.relative_to(run_root)),
                "final_checkpoint": str(final_path.relative_to(run_root)),
                "completed_updates": updates,
                "optimizer_steps": updates * PPO_PASSES,
                "environment_steps": updates * num_envs * HORIZON,
                "parameter_drift": maximum_state_difference(
                    zero_state, model_state_copy(model)
                ),
                **diagnostics,
            }
        )
        _write_json(
            run_root / "progress.json",
            {
                "phase": "train",
                "replicate": replicate + 1,
                "replicates": replicates,
            },
        )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": bool(formal),
        "authorization_token": authorization_token,
        "source_commit": str(source_commit),
        "runtime": _runtime_identity(),
        "representation": SELECTED_REPRESENTATION,
        "counts": {
            "replicates": replicates,
            "updates": updates,
            "num_envs": num_envs,
            "eval_episodes": eval_episodes,
            "ppo_passes": PPO_PASSES,
            "bootstrap_repetitions": (
                FORMAL_BOOTSTRAP_REPETITIONS if formal else 200
            ),
        },
        "replicate_results": rows,
        "wall_seconds": time.perf_counter() - started,
    }
    _write_json(run_root / "train_manifest.json", result)
    return result


def _source_controls() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for domain in DOMAIN_FLOORS:
        ledger_factory, environment_factory, profiles = _domain_spec(domain)
        for episode_id, profile in enumerate(profiles):
            ledger = ledger_factory(
                episode_id, master_seed=DOMAIN_LEDGER_SEEDS[domain]
            )
            environment = environment_factory(ledger)
            observed_count_features: list[float] = []
            while environment.time < HORIZON:
                view = environment.observe()
                observed_count_features.append(float(view.observations[0, 1]))
                environment.step(constructive_actions(environment, view))
            outcome = environment.outcome()
            rows.append(
                {
                    "domain": domain,
                    "profile": profile.name,
                    "utility": outcome.utility,
                    "roster_sizes": list(outcome.roster_sizes),
                    "count_features": observed_count_features,
                    "short_required_total": outcome.short_required_total,
                }
            )
    return {
        "rows": rows,
        "all_constructive_utility_one": all(row["utility"] == 1.0 for row in rows),
        "all_count_features_finite": all(
            math.isfinite(value)
            for row in rows
            for value in row["count_features"]
        ),
        "maximum_count_feature": max(
            value for row in rows for value in row["count_features"]
        ),
    }


def _evaluate_checkpoint(
    *,
    model: DirectPrimitiveARPolicy,
    replicate: int,
    checkpoint: str,
    domain: str,
    deterministic: bool,
    eval_episodes: int,
    action_seed: int,
) -> dict[str, Any]:
    ledger_factory, environment_factory, profiles = _domain_spec(domain)
    episode_ids = tuple(range(eval_episodes))
    before = model_state_copy(model)
    values = evaluate_direct_policy(
        model,
        episode_ids=episode_ids,
        deterministic=deterministic,
        device=torch.device("cpu"),
        ledger_seed=DOMAIN_LEDGER_SEEDS[domain],
        action_seed=action_seed,
        ledger_factory=ledger_factory,
        environment_factory=environment_factory,
    )
    difference = maximum_state_difference(before, model_state_copy(model))
    return {
        "replicate": replicate,
        "checkpoint": checkpoint,
        "domain": domain,
        "deterministic": deterministic,
        "episode_ids": list(episode_ids),
        "profile_names": [profiles[index % len(profiles)].name for index in episode_ids],
        "persistent": values["persistent"].tolist(),
        "short": values["short"].tolist(),
        "utility": values["utility"].tolist(),
        "persistent_mean": values["persistent_mean"],
        "short_mean": values["short_mean"],
        "utility_mean": values["utility_mean"],
        "model_state_maximum_difference": difference,
        "model_state_unchanged_exact": difference == 0.0,
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    if training.get("status") != "COMPLETE":
        raise ValueError("G8 evaluation requires complete training")
    eval_episodes = int(training["counts"]["eval_episodes"])
    cells: list[dict[str, Any]] = []
    for row in training["replicate_results"]:
        replicate = int(row["replicate"])
        seeds = dict(row["seeds"])
        for checkpoint in ("zero", "final"):
            configure_runtime(int(seeds["model"]))
            model = _model()
            optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
            load_checkpoint(
                run_root / row[f"{checkpoint}_checkpoint"],
                model=model,
                optimizer=optimizer,
            )
            if checkpoint == "zero":
                cells.append(
                    _evaluate_checkpoint(
                        model=model,
                        replicate=replicate,
                        checkpoint=checkpoint,
                        domain="joint",
                        deterministic=True,
                        eval_episodes=eval_episodes,
                        action_seed=int(seeds["evaluation"]),
                    )
                )
                continue
            for domain in DOMAIN_FLOORS:
                for deterministic in (True, False):
                    cells.append(
                        _evaluate_checkpoint(
                            model=model,
                            replicate=replicate,
                            checkpoint=checkpoint,
                            domain=domain,
                            deterministic=deterministic,
                            eval_episodes=eval_episodes,
                            action_seed=int(seeds["evaluation"]),
                        )
                    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": bool(training["formal"]),
        "source_commit": training["source_commit"],
        "runtime": _runtime_identity(),
        "representation": training["representation"],
        "source_controls": _source_controls(),
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", result)
    return result


def _runtime_valid(runtime: Any) -> bool:
    return bool(
        isinstance(runtime, dict)
        and runtime.get("backend") == "cpu"
        and runtime.get("torch") == EXPECTED_TORCH
        and runtime.get("torch_threads") == 1
        and Path(str(runtime.get("python", ""))).resolve()
        == Path(sys.executable).resolve()
    )


def _training_errors(training: dict[str, Any], run_root: Path) -> list[str]:
    errors: list[str] = []
    counts = training.get("counts", {})
    if training.get("algorithm") != ALGORITHM_ID or training.get("status") != "COMPLETE":
        errors.append("training identity/status mismatch")
    if bool(training.get("formal")):
        if training.get("authorization_token") != AUTHORIZATION_TOKEN:
            errors.append("authorization token mismatch")
        if re.fullmatch(r"[0-9a-f]{40}", str(training.get("source_commit", ""))) is None:
            errors.append("source commit mismatch")
        expected_counts = {
            "replicates": FORMAL_REPLICATES,
            "updates": FORMAL_UPDATES,
            "num_envs": FORMAL_NUM_ENVS,
            "eval_episodes": FORMAL_EVAL_EPISODES,
            "ppo_passes": PPO_PASSES,
            "bootstrap_repetitions": FORMAL_BOOTSTRAP_REPETITIONS,
        }
        if counts != expected_counts:
            errors.append("formal count contract mismatch")
    if training.get("representation") != SELECTED_REPRESENTATION:
        errors.append("representation contract mismatch")
    if not _runtime_valid(training.get("runtime")):
        errors.append("training runtime mismatch")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(counts.get("replicates", -1)):
        errors.append("training replicate inventory mismatch")
        return errors
    if [row.get("replicate") for row in rows] != list(range(len(rows))):
        errors.append("training replicate sequence mismatch")
    for row in rows:
        for key in ("zero_checkpoint", "final_checkpoint"):
            if not (run_root / str(row.get(key, ""))).is_file():
                errors.append(f"missing {key}")
        if row.get("completed_updates") != counts.get("updates"):
            errors.append("completed update mismatch")
        if row.get("optimizer_steps") != int(counts.get("updates", -1)) * PPO_PASSES:
            errors.append("optimizer step mismatch")
        if not row.get("finite_updates") or not row.get("lifecycle_contract_valid"):
            errors.append("training invariant failed")
        replay = row.get("maximum_replay_errors", {})
        if not isinstance(replay, dict) or any(
            not math.isfinite(float(value)) or float(value) > REPLAY_TOLERANCE
            for value in replay.values()
        ):
            errors.append("replay tolerance failed")
        if not math.isfinite(float(row.get("parameter_drift", math.nan))):
            errors.append("parameter drift is non-finite")
    return errors


def _evaluation_errors(
    training: dict[str, Any], evaluation: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if evaluation.get("algorithm") != ALGORITHM_ID or evaluation.get("status") != "COMPLETE":
        errors.append("evaluation identity/status mismatch")
    if evaluation.get("source_commit") != training.get("source_commit"):
        errors.append("evaluation source mismatch")
    if bool(evaluation.get("formal")) != bool(training.get("formal")):
        errors.append("evaluation formal mismatch")
    if evaluation.get("representation") != SELECTED_REPRESENTATION:
        errors.append("evaluation representation mismatch")
    if not _runtime_valid(evaluation.get("runtime")):
        errors.append("evaluation runtime mismatch")
    controls = evaluation.get("source_controls", {})
    if (
        not isinstance(controls, dict)
        or not controls.get("all_constructive_utility_one")
        or not controls.get("all_count_features_finite")
        or len(controls.get("rows", [])) != 12
    ):
        errors.append("source controls failed")
    cells = evaluation.get("cells")
    if not isinstance(cells, list):
        errors.append("evaluation cell inventory missing")
        return errors
    replicates = int(training["counts"]["replicates"])
    expected = {
        (replicate, "zero", "joint", True)
        for replicate in range(replicates)
    } | {
        (replicate, "final", domain, deterministic)
        for replicate in range(replicates)
        for domain in DOMAIN_FLOORS
        for deterministic in (True, False)
    }
    actual = {
        (
            cell.get("replicate"),
            cell.get("checkpoint"),
            cell.get("domain"),
            cell.get("deterministic"),
        )
        for cell in cells
    }
    if actual != expected or len(cells) != len(expected):
        errors.append("evaluation cell inventory mismatch")
    eval_episodes = int(training["counts"]["eval_episodes"])
    for cell in cells:
        if not cell.get("model_state_unchanged_exact") or float(
            cell.get("model_state_maximum_difference", math.nan)
        ) != 0.0:
            errors.append("evaluation changed model state")
        for name in ("persistent", "short", "utility"):
            values = cell.get(name)
            if not isinstance(values, list) or len(values) != eval_episodes:
                errors.append(f"{name} array length mismatch")
                continue
            if any(
                not math.isfinite(float(value))
                or float(value) < 0.0
                or float(value) > 1.0
                for value in values
            ):
                errors.append(f"{name} array domain mismatch")
        utility = cell.get("utility", [])
        if utility and not math.isclose(
            float(np.mean(np.asarray(utility, dtype=np.float64))),
            float(cell.get("utility_mean", math.nan)),
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            errors.append("utility mean mismatch")
    return errors


def _bootstrap_replicate_ci(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(
        0, array.size, size=(FORMAL_BOOTSTRAP_REPETITIONS, array.size)
    )
    estimates = array[indices].mean(axis=1)
    return [
        float(np.quantile(estimates, 0.025)),
        float(array.mean()),
        float(np.quantile(estimates, 0.975)),
    ]


def select_result_branch(metrics: dict[str, Any]) -> str:
    branch_names = {
        "iid": "NO_IID_ACCESS_PREFIX_NORMALIZED_G8",
        "heldout": "NO_HELDOUT_ACCESS_PREFIX_NORMALIZED_G8",
        "moderate_beyond": "NO_MODERATE_ACCESS_PREFIX_NORMALIZED_G8",
        "far_beyond": "NO_FAR_ACCESS_PREFIX_NORMALIZED_G8",
        "joint": "NO_JOINT_ACCESS_PREFIX_NORMALIZED_G8",
    }
    for domain in DOMAIN_FLOORS:
        if float(metrics[f"{domain}_deterministic_utility_ci95"][0]) < DOMAIN_FLOORS[domain]:
            return branch_names[domain]
    if float(metrics["joint_final_minus_zero_ci95"][0]) <= 0.0:
        return "NO_LEARNING_GAIN_PREFIX_NORMALIZED_G8"
    if (
        float(metrics["joint_min_replicate_mean"])
        < MINIMUM_JOINT_REPLICATE_FLOOR
        or float(metrics["joint_stochastic_mean"])
        < JOINT_STOCHASTIC_MEAN_FLOOR
    ):
        return "UNSTABLE_PREFIX_NORMALIZED_G8"
    return "USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8"


def analyze(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    errors = _training_errors(training, run_root) + _evaluation_errors(
        training, evaluation
    )
    operational_valid = not errors
    metrics: dict[str, Any] = {}
    branch = "INVALID_PREFIX_NORMALIZED_OPEN_ROSTER_G8"
    if operational_valid:
        cells = evaluation["cells"]
        for domain in DOMAIN_FLOORS:
            means = [
                float(cell["utility_mean"])
                for cell in cells
                if cell["checkpoint"] == "final"
                and cell["domain"] == domain
                and cell["deterministic"]
            ]
            metrics[f"{domain}_deterministic_utility_ci95"] = _bootstrap_replicate_ci(means)
        joint_final = [
            float(cell["utility_mean"])
            for cell in cells
            if cell["checkpoint"] == "final"
            and cell["domain"] == "joint"
            and cell["deterministic"]
        ]
        joint_zero = [
            float(cell["utility_mean"])
            for cell in cells
            if cell["checkpoint"] == "zero"
            and cell["domain"] == "joint"
            and cell["deterministic"]
        ]
        joint_stochastic = [
            float(cell["utility_mean"])
            for cell in cells
            if cell["checkpoint"] == "final"
            and cell["domain"] == "joint"
            and not cell["deterministic"]
        ]
        metrics.update(
            {
                "joint_replicate_means": joint_final,
                "joint_min_replicate_mean": min(joint_final),
                "joint_stochastic_mean": float(np.mean(joint_stochastic)),
                "joint_zero_replicate_means": joint_zero,
                "joint_final_minus_zero_ci95": _bootstrap_replicate_ci(
                    [final - zero for final, zero in zip(joint_final, joint_zero)]
                ),
            }
        )
        branch = (
            select_result_branch(metrics)
            if bool(training["formal"])
            else "NONFORMAL_PREFIX_NORMALIZED_G8_EXERCISE_COMPLETE"
        )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "analyze",
        "status": "COMPLETE",
        "formal": bool(training.get("formal")),
        "source_commit": training.get("source_commit"),
        "operational_valid": operational_valid,
        "operational_errors": errors,
        "metrics": metrics,
        "thresholds": {
            "domain_deterministic_lcb_floors": DOMAIN_FLOORS,
            "minimum_joint_replicate_mean_floor": MINIMUM_JOINT_REPLICATE_FLOOR,
            "joint_stochastic_mean_floor": JOINT_STOCHASTIC_MEAN_FLOOR,
            "joint_final_minus_zero_lcb_strict": 0.0,
        },
        "bootstrap_seed": BOOTSTRAP_SEED,
        "branch": branch,
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
        result = train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            replicates=args.replicates,
            updates=args.updates,
            num_envs=args.num_envs,
            eval_episodes=args.eval_episodes,
        )
    elif args.mode == "evaluate":
        result = evaluate(run_root=args.run_root)
    elif args.mode == "analyze":
        result = analyze(run_root=args.run_root)
    else:
        result = exercise(run_root=args.run_root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
