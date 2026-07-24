"""Train, evaluate and analyze the G17 continuous-service roster candidate."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random
import sys
import time
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from ha_ctse_process.continuous_service_roster_proxy_g17 import (
    ACTION_DIM,
    CAPACITY,
    CRITIC_STATE_DIM,
    GAE_LAMBDA,
    HELDOUT_PROFILES,
    HORIZON,
    OBSERVATION_DIM,
    TRAIN_PROFILES,
    ContinuousRosterTrajectory,
    ContinuousServiceRosterEnv,
    RosterProfile,
    collect_trajectory,
    constructive_actions,
    evaluate_policy,
    make_ledger,
    optimize_update,
)


SCHEMA_VERSION = 1
ALGORITHM_ID = "CURRENT_OBSERVATION_RESIDUAL_ONE_STEP_CREDIT_G17"
AUTHORIZATION_TOKEN = "AUTHORIZE_CONTINUOUS_SERVICE_ROSTER_G17_FORMAL_CPU_V1"

FORMAL_REPLICATES = 3
FORMAL_UPDATES = 100
FORMAL_NUM_ENVS = 8
FORMAL_EVAL_EPISODES = 128
FORMAL_PPO_PASSES = 2
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
HIDDEN_DIM = 32
LEARNING_RATE = 1e-3
INITIAL_LOG_STD = -1.0
CREDIT_GAMMA = 0.0

MODEL_SEED_BASE = 1_817_000
TRAIN_LEDGER_SEED_BASE = 1_827_000
ACTION_SEED_BASE = 1_837_000
EVALUATION_LEDGER_SEED_BASE = 1_847_000
EVALUATION_ACTION_SEED_BASE = 1_857_000
BOOTSTRAP_SEED = 1_867_017

SOURCE_TOLERANCE = 2e-7
REPLAY_TOLERANCE = 1e-6
IID_ACCESS_FLOOR = 0.90
HELDOUT_ACCESS_FLOOR = 0.90
CONDITIONAL_CORRELATION_FLOOR = 0.90
CONDITIONAL_MAE_CEILING = 0.05
GAIN_MARGIN = 0.10
MINIMUM_HELDOUT_REPLICATE_FLOOR = 0.85

INVALID_BRANCH = "INVALID_CONTINUOUS_SERVICE_ROSTER_G17"
NO_IID_BRANCH = "NO_IID_ACCESS_CONTINUOUS_SERVICE_G17"
NO_HELDOUT_BRANCH = "NO_HELDOUT_ACCESS_CONTINUOUS_SERVICE_G17"
NO_CONDITIONAL_BRANCH = "NO_CONDITIONAL_MAPPING_CONTINUOUS_SERVICE_G17"
NO_GAIN_BRANCH = "NO_LEARNING_GAIN_CONTINUOUS_SERVICE_G17"
UNSTABLE_BRANCH = "UNSTABLE_CONTINUOUS_SERVICE_ROSTER_G17"
USABLE_BRANCH = "USABLE_ONE_STEP_CONTINUOUS_ROSTER_G17"
NONFORMAL_BRANCH = "NONFORMAL_CONTINUOUS_SERVICE_G17_EXERCISE_COMPLETE"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    """Write directly to avoid the Windows replace race seen in old runners."""

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


def make_model() -> ContinuousRosterPolicy:
    model = ContinuousRosterPolicy(
        OBSERVATION_DIM,
        CRITIC_STATE_DIM,
        member_capacity=CAPACITY,
        action_dim=ACTION_DIM,
        hidden_dim=HIDDEN_DIM,
        current_observation_residual=True,
    )
    with torch.no_grad():
        model.log_std.fill_(INITIAL_LOG_STD)
    return model


def _replicate_seeds(replicate: int, *, seed_offset: int = 0) -> dict[str, int]:
    index = int(replicate)
    offset = int(seed_offset)
    return {
        "model": MODEL_SEED_BASE + offset + index,
        "train_ledger": TRAIN_LEDGER_SEED_BASE + offset + index,
        "action": ACTION_SEED_BASE + offset + index,
        "evaluation_ledger": EVALUATION_LEDGER_SEED_BASE + offset + index,
        "evaluation_action": EVALUATION_ACTION_SEED_BASE + offset + index,
    }


def _formal_counts_valid(
    *, replicates: int, updates: int, num_envs: int, eval_episodes: int,
    ppo_passes: int,
) -> bool:
    return (
        int(replicates) == FORMAL_REPLICATES
        and int(updates) == FORMAL_UPDATES
        and int(num_envs) == FORMAL_NUM_ENVS
        and int(eval_episodes) == FORMAL_EVAL_EPISODES
        and int(ppo_passes) == FORMAL_PPO_PASSES
    )


def _copy_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}


def _maximum_state_difference(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> float:
    if left.keys() != right.keys():
        return float("inf")
    maximum = 0.0
    for name, left_value in left.items():
        right_value = right[name]
        if left_value.shape != right_value.shape:
            return float("inf")
        maximum = max(
            maximum,
            float(torch.max(torch.abs(left_value - right_value)).item()),
        )
    return maximum


def _checkpoint_payload(
    *, model: ContinuousRosterPolicy, optimizer: torch.optim.Optimizer,
    formal: bool, source_commit: str, replicate: int, seeds: dict[str, int],
    completed_updates: int, credit_gamma: float, gae_lambda: float,
    seed_offset: int,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "formal": bool(formal),
        "source_commit": str(source_commit),
        "replicate": int(replicate),
        "seeds": dict(seeds),
        "completed_updates": int(completed_updates),
        "configuration": {
            "hidden_dim": HIDDEN_DIM,
            "learning_rate": LEARNING_RATE,
            "initial_log_std": INITIAL_LOG_STD,
            "credit_gamma": float(credit_gamma),
            "gae_lambda": float(gae_lambda),
            "seed_offset": int(seed_offset),
            "current_observation_residual": True,
            "active_count_curriculum": False,
        },
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
    }


def _checkpoint_path(run_root: Path, relative: object) -> Path:
    value = Path(str(relative))
    if value.is_absolute():
        raise ValueError("G17 checkpoint reference must be relative")
    root = run_root.resolve()
    path = (run_root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError("G17 checkpoint reference escapes the run root") from error
    return path


def _load_checkpoint(
    path: Path, *, model: ContinuousRosterPolicy,
    optimizer: torch.optim.Optimizer, training: dict[str, Any],
    replicate: int, completed_updates: int,
) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"missing G17 checkpoint: {path}")
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError("G17 checkpoint is not a dictionary")
    checks = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "formal": bool(training["formal"]),
        "source_commit": str(training["source_commit"]),
        "replicate": int(replicate),
        "completed_updates": int(completed_updates),
    }
    for name, expected in checks.items():
        if payload.get(name) != expected:
            raise ValueError(f"G17 checkpoint {name} mismatch")
    if payload.get("configuration") != training.get("configuration"):
        raise ValueError("G17 checkpoint configuration mismatch")
    model.load_state_dict(payload["model_state"])
    optimizer.load_state_dict(payload["optimizer_state"])
    return payload


def _trajectory_contract_valid(trajectory: ContinuousRosterTrajectory) -> bool:
    if len(trajectory.ledgers) != len(trajectory.outcomes):
        return False
    inactive_actions = torch.where(
        trajectory.active_mask.unsqueeze(-1),
        torch.zeros_like(trajectory.actions),
        trajectory.actions,
    )
    if int(torch.count_nonzero(inactive_actions)) != 0:
        return False
    for ledger, outcome in zip(trajectory.ledgers, trajectory.outcomes):
        try:
            ledger.validate()
        except ValueError:
            return False
        if outcome.roster_sizes != ledger.expected_roster_sizes:
            return False
        if len(outcome.reward_trace) != HORIZON:
            return False
        if not np.isfinite(np.asarray(outcome.reward_trace)).all():
            return False
    return True


def train(
    *, run_root: Path, source_commit: str, formal: bool,
    authorization_token: str | None, replicates: int, updates: int,
    num_envs: int, eval_episodes: int, ppo_passes: int = FORMAL_PPO_PASSES,
    credit_gamma: float = CREDIT_GAMMA, gae_lambda: float = GAE_LAMBDA,
    seed_offset: int = 0,
) -> dict[str, Any]:
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("formal G17 authorization token mismatch")
        if not _formal_counts_valid(
            replicates=replicates,
            updates=updates,
            num_envs=num_envs,
            eval_episodes=eval_episodes,
            ppo_passes=ppo_passes,
        ):
            raise ValueError("formal G17 counts differ from the frozen contract")
        if not source_commit or source_commit == "NONFORMAL_WORKTREE":
            raise ValueError("formal G17 training requires an integrated source commit")
        if (
            float(credit_gamma) != CREDIT_GAMMA
            or float(gae_lambda) != GAE_LAMBDA
            or int(seed_offset) != 0
        ):
            raise ValueError("formal G17 credit or seed contract mismatch")
    if min(replicates, updates, num_envs, eval_episodes, ppo_passes) <= 0:
        raise ValueError("G17 counts must be positive")
    if not 0.0 <= float(credit_gamma) <= 1.0:
        raise ValueError("G17 credit gamma must lie in [0, 1]")
    if not 0.0 <= float(gae_lambda) <= 1.0:
        raise ValueError("G17 GAE lambda must lie in [0, 1]")
    if int(seed_offset) < 0:
        raise ValueError("G17 seed offset must be nonnegative")
    run_root.mkdir(parents=True, exist_ok=False)
    checkpoint_root = run_root / "checkpoints"
    checkpoint_root.mkdir()
    configure_runtime(MODEL_SEED_BASE + int(seed_offset))
    started = time.perf_counter()
    replicate_rows: list[dict[str, Any]] = []
    for replicate in range(int(replicates)):
        seeds = _replicate_seeds(replicate, seed_offset=int(seed_offset))
        configure_runtime(seeds["model"])
        model = make_model()
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
        zero_state = _copy_state(model)
        zero_path = checkpoint_root / f"replicate_{replicate}_zero.pt"
        final_path = checkpoint_root / f"replicate_{replicate}_final.pt"
        torch.save(
            _checkpoint_payload(
                model=model,
                optimizer=optimizer,
                formal=formal,
                source_commit=source_commit,
                replicate=replicate,
                seeds=seeds,
                completed_updates=0,
                credit_gamma=float(credit_gamma),
                gae_lambda=float(gae_lambda),
                seed_offset=int(seed_offset),
            ),
            zero_path,
        )
        maximum_errors = {
            name: 0.0
            for name in (
                "logp_max_error",
                "joint_logp_max_error",
                "value_max_error",
                "hidden_max_error",
                "prefix_max_error",
                "inactive_logp_max_abs",
            )
        }
        finite = True
        lifecycle_valid = True
        active_rows = 0
        profile_episodes = {profile.name: 0 for profile in TRAIN_PROFILES}
        for update in range(int(updates)):
            first_id = update * int(num_envs)
            episode_ids = tuple(range(first_id, first_id + int(num_envs)))
            trajectory = collect_trajectory(
                model,
                episode_ids=episode_ids,
                ledger_seed=seeds["train_ledger"],
                action_seed=seeds["action"],
                device=torch.device("cpu"),
                profiles=TRAIN_PROFILES,
            )
            lifecycle_valid = lifecycle_valid and _trajectory_contract_valid(trajectory)
            metrics = optimize_update(
                model,
                optimizer,
                trajectory,
                device=torch.device("cpu"),
                ppo_passes=int(ppo_passes),
                gamma=float(credit_gamma),
                gae_lambda=float(gae_lambda),
            )
            finite = finite and bool(metrics["finite_update"])
            for name in maximum_errors:
                maximum_errors[name] = max(maximum_errors[name], float(metrics[name]))
            active_rows += trajectory.active_token_count
            for episode_id in episode_ids:
                profile_episodes[TRAIN_PROFILES[episode_id % len(TRAIN_PROFILES)].name] += 1
            _write_json(
                run_root / "progress.json",
                {
                    "phase": "train",
                    "replicate": replicate,
                    "update": update + 1,
                    "updates": int(updates),
                },
            )
        torch.save(
            _checkpoint_payload(
                model=model,
                optimizer=optimizer,
                formal=formal,
                source_commit=source_commit,
                replicate=replicate,
                seeds=seeds,
                completed_updates=int(updates),
                credit_gamma=float(credit_gamma),
                gae_lambda=float(gae_lambda),
                seed_offset=int(seed_offset),
            ),
            final_path,
        )
        replicate_rows.append(
            {
                "replicate": replicate,
                "seeds": seeds,
                "zero_checkpoint": str(zero_path.relative_to(run_root)),
                "final_checkpoint": str(final_path.relative_to(run_root)),
                "environment_steps": int(updates) * int(num_envs) * HORIZON,
                "active_rows": int(active_rows),
                "optimizer_steps": int(updates) * int(ppo_passes),
                "profile_episodes": profile_episodes,
                "maximum_replay_errors": maximum_errors,
                "lifecycle_contract_valid": bool(lifecycle_valid),
                "finite_updates": bool(finite),
                "parameter_drift": _maximum_state_difference(zero_state, _copy_state(model)),
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
            "replicates": int(replicates),
            "updates": int(updates),
            "num_envs": int(num_envs),
            "eval_episodes": int(eval_episodes),
            "ppo_passes": int(ppo_passes),
        },
        "configuration": {
            "hidden_dim": HIDDEN_DIM,
            "learning_rate": LEARNING_RATE,
            "initial_log_std": INITIAL_LOG_STD,
            "credit_gamma": float(credit_gamma),
            "gae_lambda": float(gae_lambda),
            "seed_offset": int(seed_offset),
            "current_observation_residual": True,
            "active_count_curriculum": False,
        },
        "train_profiles": [asdict(profile) for profile in TRAIN_PROFILES],
        "heldout_profiles": [asdict(profile) for profile in HELDOUT_PROFILES],
        "replicate_results": replicate_rows,
        "wall_seconds": float(time.perf_counter() - started),
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _source_controls() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for domain, profiles in (("iid", TRAIN_PROFILES), ("heldout", HELDOUT_PROFILES)):
        for episode_id in range(2 * len(profiles)):
            ledger = make_ledger(
                episode_id,
                master_seed=EVALUATION_LEDGER_SEED_BASE + 99,
                profiles=profiles,
            )
            environment = ContinuousServiceRosterEnv(ledger)
            for _ in range(HORIZON):
                view = environment.observe()
                environment.step(constructive_actions(view))
            outcome = environment.outcome()
            rows.append(
                {
                    "domain": domain,
                    "episode_id": episode_id,
                    "profile": ledger.profile.name,
                    "utility": outcome.utility,
                    "minimum_step_utility": outcome.minimum_step_utility,
                    "roster_sizes": list(outcome.roster_sizes),
                    "expected_roster_sizes": list(ledger.expected_roster_sizes),
                }
            )
    minimum = min(float(row["minimum_step_utility"]) for row in rows)
    return {
        "rows": rows,
        "minimum_step_utility": minimum,
        "all_schedules_exact": all(
            row["roster_sizes"] == row["expected_roster_sizes"] for row in rows
        ),
        "constructive_access_valid": minimum >= 1.0 - SOURCE_TOLERANCE,
    }


def _mapping_diagnostic(
    model: ContinuousRosterPolicy, *, episode_ids: Sequence[int],
    ledger_seed: int,
) -> dict[str, float]:
    environments = tuple(
        ContinuousServiceRosterEnv(
            make_ledger(episode_id, master_seed=ledger_seed, profiles=HELDOUT_PROFILES)
        )
        for episode_id in episode_ids
    )
    hidden = torch.zeros((len(environments), CAPACITY, model.hidden_dim), dtype=torch.float32)
    target_effort: list[float] = []
    predicted_effort: list[float] = []
    target_mix: list[float] = []
    predicted_mix: list[float] = []
    model.eval()
    with torch.no_grad():
        for _ in range(HORIZON):
            views = tuple(environment.observe() for environment in environments)
            output = model.forward_step(
                observations=torch.as_tensor(np.stack([view.observations for view in views])),
                active_mask=torch.as_tensor(np.stack([view.active_mask for view in views])),
                critic_state=torch.as_tensor(np.stack([view.critic_state for view in views])),
                hidden=hidden,
                deterministic=True,
            )
            actions = output.actions.detach().cpu().numpy()
            for index, (environment, view) in enumerate(zip(environments, views)):
                active = actions[index, view.active_mask]
                target_effort.append(view.load)
                target_mix.append(view.target_mix)
                predicted_effort.append(float(((active[:, 0] + 1.0) / 2.0).mean()))
                predicted_mix.append(float(((active[:, 1] + 1.0) / 2.0).mean()))
                environment.step(actions[index])
            hidden = output.next_hidden
    effort_target = np.asarray(target_effort, dtype=np.float64)
    effort_prediction = np.asarray(predicted_effort, dtype=np.float64)
    mix_target = np.asarray(target_mix, dtype=np.float64)
    mix_prediction = np.asarray(predicted_mix, dtype=np.float64)

    def correlation(left: np.ndarray, right: np.ndarray) -> float:
        if float(left.std()) == 0.0 or float(right.std()) == 0.0:
            return 0.0
        return float(np.corrcoef(left, right)[0, 1])

    return {
        "effort_correlation": correlation(effort_target, effort_prediction),
        "mix_correlation": correlation(mix_target, mix_prediction),
        "effort_mae": float(np.abs(effort_target - effort_prediction).mean()),
        "mix_mae": float(np.abs(mix_target - mix_prediction).mean()),
    }


def _outcome_cell(
    *, replicate: int, checkpoint: str, domain: str, deterministic: bool,
    episode_ids: Sequence[int], outcomes: Sequence[Any], profiles: Sequence[RosterProfile],
) -> dict[str, Any]:
    utilities = [float(outcome.utility) for outcome in outcomes]
    return {
        "replicate": int(replicate),
        "checkpoint": checkpoint,
        "domain": domain,
        "deterministic": bool(deterministic),
        "episode_ids": [int(value) for value in episode_ids],
        "profile_names": [profiles[index % len(profiles)].name for index in episode_ids],
        "utility": utilities,
        "minimum_step_utility": [float(outcome.minimum_step_utility) for outcome in outcomes],
        "utility_mean": float(np.mean(utilities)),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    if training.get("status") != "COMPLETE":
        raise ValueError("G17 evaluation requires complete training")
    if training.get("algorithm") != ALGORITHM_ID:
        raise ValueError("G17 evaluation algorithm mismatch")
    configure_runtime(MODEL_SEED_BASE)
    eval_episodes = int(training["counts"]["eval_episodes"])
    episode_ids = tuple(range(eval_episodes))
    cells: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []
    for row in training["replicate_results"]:
        replicate = int(row["replicate"])
        seeds = {name: int(value) for name, value in row["seeds"].items()}
        for checkpoint_kind in ("zero", "final"):
            configure_runtime(seeds["model"])
            model = make_model()
            optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
            completed_updates = 0 if checkpoint_kind == "zero" else int(training["counts"]["updates"])
            _load_checkpoint(
                _checkpoint_path(run_root, row[f"{checkpoint_kind}_checkpoint"]),
                model=model,
                optimizer=optimizer,
                training=training,
                replicate=replicate,
                completed_updates=completed_updates,
            )
            for domain, profiles in (("iid", TRAIN_PROFILES), ("heldout", HELDOUT_PROFILES)):
                outcomes = evaluate_policy(
                    model,
                    episode_ids=episode_ids,
                    ledger_seed=seeds["evaluation_ledger"],
                    action_seed=seeds["evaluation_action"],
                    device=torch.device("cpu"),
                    profiles=profiles,
                    deterministic=True,
                )
                cells.append(
                    _outcome_cell(
                        replicate=replicate,
                        checkpoint=checkpoint_kind,
                        domain=domain,
                        deterministic=True,
                        episode_ids=episode_ids,
                        outcomes=outcomes,
                        profiles=profiles,
                    )
                )
            if checkpoint_kind == "final":
                stochastic = evaluate_policy(
                    model,
                    episode_ids=episode_ids,
                    ledger_seed=seeds["evaluation_ledger"],
                    action_seed=seeds["evaluation_action"],
                    device=torch.device("cpu"),
                    profiles=HELDOUT_PROFILES,
                    deterministic=False,
                )
                cells.append(
                    _outcome_cell(
                        replicate=replicate,
                        checkpoint="final",
                        domain="heldout",
                        deterministic=False,
                        episode_ids=episode_ids,
                        outcomes=stochastic,
                        profiles=HELDOUT_PROFILES,
                    )
                )
                mapping_rows.append(
                    {
                        "replicate": replicate,
                        **_mapping_diagnostic(
                            model,
                            episode_ids=episode_ids,
                            ledger_seed=seeds["evaluation_ledger"],
                        ),
                    }
                )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": bool(training["formal"]),
        "source_commit": str(training["source_commit"]),
        "runtime": _runtime_identity(),
        "source_controls": _source_controls(),
        "cells": cells,
        "mapping_diagnostics": mapping_rows,
    }
    _write_json(run_root / "evaluation_manifest.json", result)
    return result


def _hierarchical_ci(values: np.ndarray, *, seed: int, repetitions: int) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2 or min(array.shape) <= 0:
        raise ValueError("G17 hierarchical bootstrap requires [replicate, episode]")
    rng = np.random.default_rng(int(seed))
    replicate_indices = rng.integers(0, array.shape[0], size=(repetitions, array.shape[0]))
    episode_indices = rng.integers(
        0,
        array.shape[1],
        size=(repetitions, array.shape[0], array.shape[1]),
    )
    samples = array[replicate_indices[:, :, None], episode_indices]
    means = samples.mean(axis=(1, 2))
    return [
        float(np.quantile(means, 0.025)),
        float(array.mean()),
        float(np.quantile(means, 0.975)),
    ]


def select_result_branch(predicate_inputs: dict[str, Any]) -> str:
    if not bool(predicate_inputs["operational_valid"]):
        return INVALID_BRANCH
    if float(predicate_inputs["iid_lcb"]) < IID_ACCESS_FLOOR:
        return NO_IID_BRANCH
    if float(predicate_inputs["heldout_lcb"]) < HELDOUT_ACCESS_FLOOR:
        return NO_HELDOUT_BRANCH
    if (
        float(predicate_inputs["minimum_effort_correlation"])
        < CONDITIONAL_CORRELATION_FLOOR
        or float(predicate_inputs["minimum_mix_correlation"])
        < CONDITIONAL_CORRELATION_FLOOR
        or float(predicate_inputs["maximum_effort_mae"]) > CONDITIONAL_MAE_CEILING
        or float(predicate_inputs["maximum_mix_mae"]) > CONDITIONAL_MAE_CEILING
    ):
        return NO_CONDITIONAL_BRANCH
    if float(predicate_inputs["gain_lcb"]) <= GAIN_MARGIN:
        return NO_GAIN_BRANCH
    if (
        float(predicate_inputs["minimum_heldout_replicate"])
        < MINIMUM_HELDOUT_REPLICATE_FLOOR
    ):
        return UNSTABLE_BRANCH
    return USABLE_BRANCH


def _selected_cells(
    evaluation: dict[str, Any], *, checkpoint: str, domain: str,
    deterministic: bool,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in evaluation.get("cells", [])
        if row.get("checkpoint") == checkpoint
        and row.get("domain") == domain
        and bool(row.get("deterministic")) is deterministic
    ]
    return sorted(rows, key=lambda row: int(row.get("replicate", -1)))


def _artifact_errors(
    run_root: Path, training: dict[str, Any], evaluation: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if training.get("status") != "COMPLETE" or evaluation.get("status") != "COMPLETE":
        errors.append("train/evaluate status is incomplete")
    if training.get("algorithm") != ALGORITHM_ID or evaluation.get("algorithm") != ALGORITHM_ID:
        errors.append("algorithm identity mismatch")
    if training.get("source_commit") != evaluation.get("source_commit"):
        errors.append("train/evaluate source mismatch")
    if training.get("formal") != evaluation.get("formal"):
        errors.append("train/evaluate formal identity mismatch")
    for stage, artifact in (("train", training), ("evaluate", evaluation)):
        runtime = artifact.get("runtime", {})
        if runtime.get("backend") != "cpu" or runtime.get("torch_threads") != 1:
            errors.append(f"{stage} runtime is not CPU one-thread")
    counts = training.get("counts", {})
    formal = bool(training.get("formal"))
    if formal:
        if training.get("authorization_token") != AUTHORIZATION_TOKEN:
            errors.append("formal authorization token mismatch")
        try:
            counts_valid = _formal_counts_valid(
                replicates=int(counts.get("replicates", -1)),
                updates=int(counts.get("updates", -1)),
                num_envs=int(counts.get("num_envs", -1)),
                eval_episodes=int(counts.get("eval_episodes", -1)),
                ppo_passes=int(counts.get("ppo_passes", -1)),
            )
        except (TypeError, ValueError):
            counts_valid = False
        if not counts_valid:
            errors.append("formal count contract mismatch")
        configuration = training.get("configuration", {})
        if (
            configuration.get("credit_gamma") != CREDIT_GAMMA
            or configuration.get("gae_lambda") != GAE_LAMBDA
            or configuration.get("seed_offset") != 0
        ):
            errors.append("formal credit or seed contract mismatch")
    controls = evaluation.get("source_controls", {})
    if not controls.get("all_schedules_exact") or not controls.get("constructive_access_valid"):
        errors.append("constructive source control failed")
    replicate_rows = training.get("replicate_results", [])
    expected_replicates = int(counts.get("replicates", -1))
    if len(replicate_rows) != expected_replicates:
        errors.append("training replicate inventory mismatch")
    for row in replicate_rows:
        replicate = row.get("replicate")
        if not row.get("finite_updates") or not row.get("lifecycle_contract_valid"):
            errors.append(f"replicate {replicate} training invariant failed")
        if float(row.get("parameter_drift", 0.0)) <= 0.0:
            errors.append(f"replicate {replicate} has zero parameter drift")
        replay = row.get("maximum_replay_errors", {})
        if not replay or max(float(value) for value in replay.values()) > REPLAY_TOLERANCE:
            errors.append(f"replicate {replicate} replay tolerance failed")
        for kind, updates in (("zero", 0), ("final", int(counts.get("updates", -1)))):
            try:
                path = _checkpoint_path(run_root, row[f"{kind}_checkpoint"])
                model = make_model()
                optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
                _load_checkpoint(
                    path,
                    model=model,
                    optimizer=optimizer,
                    training=training,
                    replicate=int(replicate),
                    completed_updates=updates,
                )
            except (KeyError, TypeError, ValueError, RuntimeError) as error:
                errors.append(f"replicate {replicate} {kind} checkpoint invalid: {error}")
    eval_episodes = int(counts.get("eval_episodes", -1))
    expected_keys = {
        (replicate, checkpoint, domain, deterministic)
        for replicate in range(max(expected_replicates, 0))
        for checkpoint, domain, deterministic in (
            ("zero", "iid", True),
            ("zero", "heldout", True),
            ("final", "iid", True),
            ("final", "heldout", True),
            ("final", "heldout", False),
        )
    }
    observed_keys: set[tuple[int, str, str, bool]] = set()
    for cell in evaluation.get("cells", []):
        try:
            key = (
                int(cell["replicate"]),
                str(cell["checkpoint"]),
                str(cell["domain"]),
                bool(cell["deterministic"]),
            )
            utilities = np.asarray(cell["utility"], dtype=np.float64)
        except (KeyError, TypeError, ValueError):
            errors.append("malformed evaluation cell")
            continue
        if key in observed_keys:
            errors.append("duplicate evaluation cell")
        observed_keys.add(key)
        if utilities.shape != (eval_episodes,):
            errors.append(f"evaluation cell {key} episode inventory mismatch")
        elif not np.isfinite(utilities).all() or np.any((utilities < 0.0) | (utilities > 1.0)):
            errors.append(f"evaluation cell {key} utility invalid")
    if observed_keys != expected_keys:
        errors.append("evaluation cell inventory mismatch")
    mapping_rows = evaluation.get("mapping_diagnostics", [])
    if len(mapping_rows) != expected_replicates:
        errors.append("mapping diagnostic inventory mismatch")
    else:
        mapping_replicates = sorted(int(row.get("replicate", -1)) for row in mapping_rows)
        if mapping_replicates != list(range(expected_replicates)):
            errors.append("mapping diagnostic replicate mismatch")
        for row in mapping_rows:
            values = np.asarray(
                [
                    row.get("effort_correlation"),
                    row.get("mix_correlation"),
                    row.get("effort_mae"),
                    row.get("mix_mae"),
                ],
                dtype=np.float64,
            )
            if not np.isfinite(values).all():
                errors.append("mapping diagnostic contains non-finite values")
    return errors


def analyze(*, run_root: Path, require_formal: bool = False) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    if require_formal and (training.get("formal") is not True or evaluation.get("formal") is not True):
        raise ValueError("formal analysis requires formal artifacts")
    errors = _artifact_errors(run_root, training, evaluation)
    counts = training.get("counts", {})
    formal = bool(training.get("formal"))
    metrics: dict[str, Any] = {}
    predicate_inputs: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        final_iid = _selected_cells(evaluation, checkpoint="final", domain="iid", deterministic=True)
        final_heldout = _selected_cells(evaluation, checkpoint="final", domain="heldout", deterministic=True)
        zero_heldout = _selected_cells(evaluation, checkpoint="zero", domain="heldout", deterministic=True)
        stochastic_heldout = _selected_cells(evaluation, checkpoint="final", domain="heldout", deterministic=False)
        iid = np.asarray([row["utility"] for row in final_iid], dtype=np.float64)
        heldout = np.asarray([row["utility"] for row in final_heldout], dtype=np.float64)
        zero = np.asarray([row["utility"] for row in zero_heldout], dtype=np.float64)
        repetitions = FORMAL_BOOTSTRAP_REPETITIONS if formal else 512
        iid_ci = _hierarchical_ci(iid, seed=BOOTSTRAP_SEED, repetitions=repetitions)
        heldout_ci = _hierarchical_ci(
            heldout, seed=BOOTSTRAP_SEED + 1, repetitions=repetitions
        )
        gain_ci = _hierarchical_ci(
            heldout - zero, seed=BOOTSTRAP_SEED + 2, repetitions=repetitions
        )
        mapping_rows = sorted(
            evaluation["mapping_diagnostics"], key=lambda row: int(row["replicate"])
        )
        heldout_replicate_means = heldout.mean(axis=1).tolist()
        metrics = {
            "iid_deterministic_utility_ci95": iid_ci,
            "heldout_deterministic_utility_ci95": heldout_ci,
            "heldout_final_minus_zero_ci95": gain_ci,
            "heldout_replicate_means": [float(value) for value in heldout_replicate_means],
            "minimum_heldout_replicate_mean": float(min(heldout_replicate_means)),
            "heldout_stochastic_mean": float(
                np.mean([row["utility_mean"] for row in stochastic_heldout])
            ),
            "minimum_effort_correlation": min(float(row["effort_correlation"]) for row in mapping_rows),
            "minimum_mix_correlation": min(float(row["mix_correlation"]) for row in mapping_rows),
            "maximum_effort_mae": max(float(row["effort_mae"]) for row in mapping_rows),
            "maximum_mix_mae": max(float(row["mix_mae"]) for row in mapping_rows),
        }
        predicate_inputs.update(
            {
                "iid_lcb": iid_ci[0],
                "heldout_lcb": heldout_ci[0],
                "minimum_effort_correlation": metrics["minimum_effort_correlation"],
                "minimum_mix_correlation": metrics["minimum_mix_correlation"],
                "maximum_effort_mae": metrics["maximum_effort_mae"],
                "maximum_mix_mae": metrics["maximum_mix_mae"],
                "gain_lcb": gain_ci[0],
                "minimum_heldout_replicate": metrics["minimum_heldout_replicate_mean"],
            }
        )
    branch = select_result_branch(predicate_inputs)
    if not formal and not errors:
        branch = NONFORMAL_BRANCH
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": formal,
        "source_commit": training.get("source_commit"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "predicate_inputs": predicate_inputs,
        "metrics": metrics,
        "thresholds": {
            "iid_access_floor": IID_ACCESS_FLOOR,
            "heldout_access_floor": HELDOUT_ACCESS_FLOOR,
            "conditional_correlation_floor": CONDITIONAL_CORRELATION_FLOOR,
            "conditional_mae_ceiling": CONDITIONAL_MAE_CEILING,
            "gain_margin": GAIN_MARGIN,
            "minimum_heldout_replicate_floor": MINIMUM_HELDOUT_REPLICATE_FLOOR,
        },
        "counts": dict(counts),
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
        updates=1,
        num_envs=2,
        eval_episodes=3,
        ppo_passes=1,
        credit_gamma=CREDIT_GAMMA,
        gae_lambda=GAE_LAMBDA,
        seed_offset=0,
    )
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit", default=None)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--require-formal", action="store_true")
    parser.add_argument("--authorization-token", default=None)
    parser.add_argument("--replicates", type=int, default=FORMAL_REPLICATES)
    parser.add_argument("--updates", type=int, default=FORMAL_UPDATES)
    parser.add_argument("--num-envs", type=int, default=FORMAL_NUM_ENVS)
    parser.add_argument("--eval-episodes", type=int, default=FORMAL_EVAL_EPISODES)
    parser.add_argument("--ppo-passes", type=int, default=FORMAL_PPO_PASSES)
    parser.add_argument("--credit-gamma", type=float, default=CREDIT_GAMMA)
    parser.add_argument("--gae-lambda", type=float, default=GAE_LAMBDA)
    parser.add_argument("--seed-offset", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    if arguments.mode == "train":
        if arguments.source_commit is None:
            raise ValueError("G17 train requires --source-commit")
        value = train(
            run_root=arguments.run_root,
            source_commit=arguments.source_commit,
            formal=bool(arguments.formal),
            authorization_token=arguments.authorization_token,
            replicates=arguments.replicates,
            updates=arguments.updates,
            num_envs=arguments.num_envs,
            eval_episodes=arguments.eval_episodes,
            ppo_passes=arguments.ppo_passes,
            credit_gamma=arguments.credit_gamma,
            gae_lambda=arguments.gae_lambda,
            seed_offset=arguments.seed_offset,
        )
    elif arguments.mode == "evaluate":
        value = evaluate(run_root=arguments.run_root)
    elif arguments.mode == "analyze":
        value = analyze(
            run_root=arguments.run_root, require_formal=bool(arguments.require_formal)
        )
    else:
        value = exercise(run_root=arguments.run_root)
    print(
        json.dumps(
            {
                "algorithm": value.get("algorithm"),
                "stage": value.get("stage"),
                "status": value.get("status"),
                "branch": value.get("branch"),
                "formal": value.get("formal"),
                "run_root": str(arguments.run_root),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
