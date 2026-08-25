"""Run the bounded dual-source G18 fast/slow credit screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.separated_credit_g18 import (
    SeparatedCreditPolicy,
    attach_credit_baselines,
    collect_battery_trajectory,
    evaluate_battery_policy,
    optimize_separated_update,
)
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = "ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18"
AUTHORIZATION_TOKEN = "AUTHORIZE_ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18_FORMAL_CPU_V1"
GAMMA = 0.99
HIDDEN_DIM = 32
LEARNING_RATE = 1e-3
INITIAL_LOG_STD = -1.0
PPO_PASSES = 2
NUM_ENVS = 8
G17_UPDATES = 100
G18_UPDATES = 300
FORMAL_REPLICATES = 3
FORMAL_EVAL_EPISODES = 128
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
EXERCISE_REPLICATES = 1
EXERCISE_G17_UPDATES = 1
EXERCISE_G18_UPDATES = 1
EXERCISE_NUM_ENVS = 2
EXERCISE_EVAL_EPISODES = 4
EXERCISE_PPO_PASSES = 1

SEED_BASES = {
    "g17": {
        "model": 2_218_000,
        "ledger": 2_228_000,
        "action": 2_238_000,
        "evaluation_ledger": 2_248_000,
        "evaluation_action": 2_258_000,
    },
    "g18": {
        "model": 2_318_000,
        "action": 2_338_000,
    },
}
BOOTSTRAP_SEED = 2_368_018

REPLAY_TOLERANCE = 1e-6
G17_UTILITY_FLOOR = 0.90
G17_GAIN_FLOOR = 0.10
G17_MINIMUM_EPISODE_FLOOR = 0.80
G17_CORRELATION_FLOOR = 0.90
G17_MAE_CEILING = 0.05
G18_UTILITY_FLOOR = 0.95
G18_GAIN_FLOOR = 0.10
G18_SPIKE_UTILITY_FLOOR = 0.90
G18_ROTATING_EFFORT_SHARE_FLOOR = 0.75

INVALID_BRANCH = "INVALID_ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18"
NO_G17_BRANCH = "NO_G17_COMPATIBILITY_CRITIC_ISOLATED_G18"
NO_G18_ACCESS_BRANCH = "NO_DELAYED_ACCESS_CRITIC_ISOLATED_G18"
NO_G18_MECHANISM_BRANCH = "NO_DELAYED_MECHANISM_CRITIC_ISOLATED_G18"
UNSTABLE_BRANCH = "UNSTABLE_ACTOR_CRITIC_ISOLATED_CREDIT_G18"
USABLE_BRANCH = "USABLE_DELAYED_DYNAMIC_ROSTER_CREDIT_G18"
NONFORMAL_BRANCH = "NONFORMAL_CRITIC_ISOLATED_FORMAL_PATH_EXERCISE_COMPLETE"


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


def _runtime_identity() -> dict[str, Any]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _source_dimensions(source: str) -> tuple[int, int, int, int]:
    if source == "g17":
        return (
            g17_source.OBSERVATION_DIM,
            g17_source.CRITIC_STATE_DIM,
            g17_source.CAPACITY,
            g17_source.ACTION_DIM,
        )
    if source == "g18":
        return (
            battery_source.OBSERVATION_DIM,
            battery_source.CRITIC_STATE_DIM,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        )
    raise ValueError(f"unknown separated-credit source: {source}")


def make_model(source: str) -> SeparatedCreditPolicy:
    observation_dim, critic_state_dim, capacity, action_dim = _source_dimensions(
        source
    )
    model = SeparatedCreditPolicy(
        observation_dim,
        critic_state_dim,
        member_capacity=capacity,
        action_dim=action_dim,
        hidden_dim=HIDDEN_DIM,
        current_observation_residual=True,
    )
    with torch.no_grad():
        model.log_std.fill_(INITIAL_LOG_STD)
    return model


def _copy_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }


def _maximum_state_difference(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> float:
    if left.keys() != right.keys():
        return float("inf")
    return max(
        float(torch.max(torch.abs(left[name] - right[name])).item())
        for name in left
    )


def _save_checkpoint(
    path: Path,
    *,
    source: str,
    source_commit: str,
    formal: bool,
    replicate: int,
    completed_updates: int,
    configuration: dict[str, Any],
    model: SeparatedCreditPolicy,
) -> None:
    torch.save(
        {
            "schema_version": SCHEMA_VERSION,
            "algorithm": ALGORITHM_ID,
            "formal": bool(formal),
            "source": source,
            "source_commit": source_commit,
            "replicate": int(replicate),
            "completed_updates": int(completed_updates),
            "configuration": configuration,
            "model_state": model.state_dict(),
        },
        path,
    )


def _load_checkpoint(
    path: Path,
    *,
    source: str,
    source_commit: str,
    formal: bool,
    replicate: int,
    completed_updates: int,
    configuration: dict[str, Any],
    seeds: dict[str, int],
) -> SeparatedCreditPolicy:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    expected = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "formal": bool(formal),
        "source": source,
        "source_commit": source_commit,
        "replicate": int(replicate),
        "completed_updates": int(completed_updates),
        "configuration": configuration,
    }
    if not isinstance(payload, dict):
        raise ValueError("G18 separated-credit checkpoint is not a dictionary")
    for name, value in expected.items():
        if payload.get(name) != value:
            raise ValueError(f"G18 separated-credit checkpoint {name} mismatch")
    g17_runner.configure_runtime(seeds["model"])
    model = make_model(source)
    model.load_state_dict(payload["model_state"])
    return model


def _counts(*, formal: bool) -> dict[str, int]:
    if formal:
        return {
            "replicates": FORMAL_REPLICATES,
            "g17_updates": G17_UPDATES,
            "g18_updates": G18_UPDATES,
            "num_envs": NUM_ENVS,
            "eval_episodes": FORMAL_EVAL_EPISODES,
            "ppo_passes": PPO_PASSES,
            "bootstrap_repetitions": FORMAL_BOOTSTRAP_REPETITIONS,
        }
    return {
        "replicates": EXERCISE_REPLICATES,
        "g17_updates": EXERCISE_G17_UPDATES,
        "g18_updates": EXERCISE_G18_UPDATES,
        "num_envs": EXERCISE_NUM_ENVS,
        "eval_episodes": EXERCISE_EVAL_EPISODES,
        "ppo_passes": EXERCISE_PPO_PASSES,
        "bootstrap_repetitions": 0,
    }


def _seeds(source: str, replicate: int, *, formal: bool) -> dict[str, int]:
    offset = int(replicate) + (0 if formal else 900_000)
    return {
        name: int(value) + offset
        for name, value in SEED_BASES[source].items()
    }


def _configuration(*, formal: bool) -> dict[str, Any]:
    counts = _counts(formal=formal)
    return {
        "gamma": GAMMA,
        "hidden_dim": HIDDEN_DIM,
        "learning_rate": LEARNING_RATE,
        "initial_log_std": INITIAL_LOG_STD,
        **counts,
        "current_observation_residual": True,
        "successor_weight": 1.0,
        "actor_channel_combination": "independent_normalization_equal_weight",
        "slow_critic": "state_only_actor_gradient_isolated",
    }


def _collect_trajectory(
    source: str,
    model: SeparatedCreditPolicy,
    *,
    episode_ids: tuple[int, ...],
    seeds: dict[str, int],
) -> Any:
    if source == "g17":
        raw = g17_source.collect_trajectory(
            model,
            episode_ids=episode_ids,
            ledger_seed=seeds["ledger"],
            action_seed=seeds["action"],
            device=torch.device("cpu"),
            profiles=g17_source.TRAIN_PROFILES,
        )
        return attach_credit_baselines(
            model, raw, device=torch.device("cpu")
        )
    return collect_battery_trajectory(
        model,
        episode_ids=episode_ids,
        action_seed=seeds["action"],
        device=torch.device("cpu"),
    )


def _trajectory_contract_valid(source: str, trajectory: Any) -> bool:
    inactive_actions = torch.where(
        trajectory.active_mask.unsqueeze(-1),
        torch.zeros_like(trajectory.actions),
        trajectory.actions,
    )
    if int(torch.count_nonzero(inactive_actions)) != 0:
        return False
    if not all(
        bool(torch.isfinite(row).all())
        for row in (
            trajectory.observations,
            trajectory.critic_states,
            trajectory.actions,
            trajectory.pre_tanh_actions,
            trajectory.old_log_probs,
            trajectory.old_values,
            trajectory.old_immediate_baselines,
            trajectory.old_successor_baselines,
            trajectory.rewards,
        )
    ):
        return False
    for ledger, outcome in zip(trajectory.ledgers, trajectory.outcomes):
        if source == "g17":
            if outcome.roster_sizes != ledger.expected_roster_sizes:
                return False
        elif outcome.roster_sizes != (
            4,
            4,
            4,
            4,
            4,
            4,
            2,
            2,
            2,
            2,
            4,
            4,
        ):
            return False
    return True


def _train_source(
    *,
    run_root: Path,
    source: str,
    source_commit: str,
    formal: bool,
    replicate: int,
    configuration: dict[str, Any],
    seeds: dict[str, int],
    updates: int,
) -> dict[str, Any]:
    g17_runner.configure_runtime(seeds["model"])
    model = make_model(source)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    zero_state = _copy_state(model)
    checkpoint_root = run_root / "checkpoints"
    zero_path = checkpoint_root / f"replicate_{replicate}_{source}_zero.pt"
    final_path = checkpoint_root / f"replicate_{replicate}_{source}_final.pt"
    _save_checkpoint(
        zero_path,
        source=source,
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        completed_updates=0,
        configuration=configuration,
        model=model,
    )
    maximum_errors: dict[str, float] = {}
    finite = True
    lifecycle_valid = True
    active_rows = 0
    for update in range(int(updates)):
        num_envs = int(configuration["num_envs"])
        first_episode = update * num_envs
        episode_ids = tuple(range(first_episode, first_episode + num_envs))
        trajectory = _collect_trajectory(
            source, model, episode_ids=episode_ids, seeds=seeds
        )
        lifecycle_valid = lifecycle_valid and _trajectory_contract_valid(
            source, trajectory
        )
        metrics = optimize_separated_update(
            model,
            optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=int(configuration["ppo_passes"]),
            gamma=GAMMA,
        )
        finite = finite and bool(metrics["finite_update"])
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                maximum_errors[name] = max(
                    maximum_errors.get(name, 0.0), float(value)
                )
        active_rows += trajectory.active_token_count
        _write_json(
            run_root / "progress.json",
            {
                "phase": "train",
                "replicate": int(replicate),
                "source": source,
                "update": update + 1,
                "updates": int(updates),
            },
        )
    _save_checkpoint(
        final_path,
        source=source,
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        completed_updates=updates,
        configuration=configuration,
        model=model,
    )
    return {
        "source": source,
        "replicate": int(replicate),
        "updates": int(updates),
        "environment_steps": int(
            updates
            * int(configuration["num_envs"])
            * (g17_source.HORIZON if source == "g17" else battery_source.HORIZON)
        ),
        "optimizer_steps": int(updates * int(configuration["ppo_passes"])),
        "active_rows": int(active_rows),
        "zero_checkpoint": str(zero_path.relative_to(run_root)),
        "final_checkpoint": str(final_path.relative_to(run_root)),
        "maximum_replay_errors": maximum_errors,
        "lifecycle_contract_valid": bool(lifecycle_valid),
        "finite_updates": bool(finite),
        "parameter_drift": _maximum_state_difference(
            zero_state, _copy_state(model)
        ),
        "parameter_count": model.parameter_count,
        "seeds": seeds,
    }


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
) -> dict[str, Any]:
    if not source_commit or source_commit == "NONFORMAL_WORKTREE":
        raise ValueError("G18 run requires an integrated source commit")
    if formal and authorization_token != AUTHORIZATION_TOKEN:
        raise ValueError("formal G18 authorization token mismatch")
    if not formal and authorization_token is not None:
        raise ValueError("nonformal G18 exercise cannot carry formal authority")
    run_root.mkdir(parents=True, exist_ok=False)
    (run_root / "checkpoints").mkdir()
    configuration = _configuration(formal=formal)
    g17_runner.configure_runtime(_seeds("g17", 0, formal=formal)["model"])
    started = time.perf_counter()
    rows = []
    for replicate in range(int(configuration["replicates"])):
        for source in ("g17", "g18"):
            rows.append(
                _train_source(
                    run_root=run_root,
                    source=source,
                    source_commit=source_commit,
                    formal=formal,
                    replicate=replicate,
                    configuration=configuration,
                    seeds=_seeds(source, replicate, formal=formal),
                    updates=int(configuration[f"{source}_updates"]),
                )
            )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": bool(formal),
        "authorization_token": authorization_token,
        "source_commit": source_commit,
        "runtime": _runtime_identity(),
        "configuration": configuration,
        "source_results": rows,
        "wall_seconds": float(time.perf_counter() - started),
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _g17_cell(
    model: SeparatedCreditPolicy,
    *,
    domain: str,
    seeds: dict[str, int],
    eval_episodes: int,
) -> dict[str, Any]:
    profiles = (
        g17_source.TRAIN_PROFILES
        if domain == "iid"
        else g17_source.HELDOUT_PROFILES
    )
    outcomes = g17_source.evaluate_policy(
        model,
        episode_ids=range(eval_episodes),
        ledger_seed=seeds["evaluation_ledger"],
        action_seed=seeds["evaluation_action"],
        device=torch.device("cpu"),
        profiles=profiles,
        deterministic=True,
    )
    utilities = [float(outcome.utility) for outcome in outcomes]
    return {
        "domain": domain,
        "utility": utilities,
        "utility_mean": float(np.mean(utilities)),
        "minimum_episode": float(np.min(utilities)),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    if (
        training.get("algorithm") != ALGORITHM_ID
        or training.get("status") != "COMPLETE"
    ):
        raise ValueError("G18 evaluation requires complete training")
    formal = bool(training.get("formal"))
    configuration = _configuration(formal=formal)
    if training.get("configuration") != configuration:
        raise ValueError("G18 evaluation configuration mismatch")
    source_commit = str(training["source_commit"])
    cells: list[dict[str, Any]] = []
    for row in training["source_results"]:
        source = str(row["source"])
        replicate = int(row["replicate"])
        seeds = {name: int(value) for name, value in row["seeds"].items()}
        for checkpoint_kind in ("zero", "final"):
            model = _load_checkpoint(
                run_root / row[f"{checkpoint_kind}_checkpoint"],
                source=source,
                source_commit=source_commit,
                formal=formal,
                replicate=replicate,
                completed_updates=(
                    0 if checkpoint_kind == "zero" else int(row["updates"])
                ),
                configuration=configuration,
                seeds=seeds,
            )
            if source == "g18":
                cells.append(
                    {
                        "source": source,
                        "replicate": replicate,
                        "checkpoint": checkpoint_kind,
                        "slot_rows": evaluate_battery_policy(
                            model, device=torch.device("cpu")
                        ),
                    }
                )
                continue
            for domain in ("iid", "heldout"):
                cells.append(
                    {
                        "source": source,
                        "replicate": replicate,
                        "checkpoint": checkpoint_kind,
                        **_g17_cell(
                            model,
                            domain=domain,
                            seeds=seeds,
                            eval_episodes=int(configuration["eval_episodes"]),
                        ),
                    }
                )
            if checkpoint_kind == "final":
                cells.append(
                    {
                        "source": source,
                        "replicate": replicate,
                        "checkpoint": "final",
                        "domain": "mapping",
                        **g17_runner._mapping_diagnostic(
                            model,
                            episode_ids=tuple(
                                range(int(configuration["eval_episodes"]))
                            ),
                            ledger_seed=seeds["evaluation_ledger"],
                        ),
                    }
                )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": source_commit,
        "runtime": _runtime_identity(),
        "source_controls": {
            "g17": g17_runner._source_controls(),
            "g18": battery_source.run_information_gate(),
        },
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def select_result_branch(metrics: dict[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    g17_ok = (
        float(metrics["g17_iid_utility_ci95"][0]) >= G17_UTILITY_FLOOR
        and float(metrics["g17_heldout_utility_ci95"][0])
        >= G17_UTILITY_FLOOR
        and float(metrics["g17_gain_ci95"][0]) >= G17_GAIN_FLOOR
        and float(metrics["g17_minimum_episode"])
        >= G17_MINIMUM_EPISODE_FLOOR
        and float(metrics["g17_minimum_effort_correlation"])
        >= G17_CORRELATION_FLOOR
        and float(metrics["g17_minimum_mix_correlation"])
        >= G17_CORRELATION_FLOOR
        and float(metrics["g17_maximum_effort_mae"]) <= G17_MAE_CEILING
        and float(metrics["g17_maximum_mix_mae"]) <= G17_MAE_CEILING
    )
    if not g17_ok:
        return NO_G17_BRANCH
    g18_access = (
        float(metrics["g18_utility_ci95"][0]) >= G18_UTILITY_FLOOR
        and float(metrics["g18_gain_ci95"][0]) >= G18_GAIN_FLOOR
        and float(metrics["g18_spike_utility_ci95"][0])
        >= G18_SPIKE_UTILITY_FLOOR
    )
    if not g18_access:
        return NO_G18_ACCESS_BRANCH
    if (
        float(metrics["g18_rotating_effort_share_ci95"][0])
        < G18_ROTATING_EFFORT_SHARE_FLOOR
    ):
        return NO_G18_MECHANISM_BRANCH
    if float(metrics["g18_minimum_replicate_utility"]) < 0.90:
        return UNSTABLE_BRANCH
    return USABLE_BRANCH


def _only_cell(cells: list[dict[str, Any]], **criteria: str) -> dict[str, Any]:
    matches = [
        row
        for row in cells
        if all(row.get(name) == value for name, value in criteria.items())
    ]
    if len(matches) != 1:
        raise ValueError(f"G18 cell inventory mismatch: {criteria}")
    return matches[0]


def analyze(
    *, run_root: Path, require_formal: bool = False
) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal analysis requires formal artifacts")
    errors: list[str] = []
    source_commit = training.get("source_commit")
    if (
        not isinstance(source_commit, str)
        or not source_commit
        or source_commit == "NONFORMAL_WORKTREE"
    ):
        errors.append("source commit invalid")
    for artifact in (training, evaluation):
        if artifact.get("algorithm") != ALGORITHM_ID:
            errors.append("algorithm mismatch")
        if artifact.get("status") != "COMPLETE":
            errors.append("artifact incomplete")
        if artifact.get("formal") is not formal:
            errors.append("formal identity mismatch")
        if artifact.get("source_commit") != training.get("source_commit"):
            errors.append("source commit mismatch")
        runtime = artifact.get("runtime", {})
        if runtime.get("backend") != "cpu" or runtime.get("torch_threads") != 1:
            errors.append("runtime identity mismatch")
    configuration = _configuration(formal=formal)
    if training.get("configuration") != configuration:
        errors.append("configuration mismatch")
    if formal and training.get("authorization_token") != AUTHORIZATION_TOKEN:
        errors.append("formal authorization mismatch")
    if not formal and training.get("authorization_token") is not None:
        errors.append("nonformal authorization mismatch")
    rows = training.get("source_results", [])
    expected_inventory = {
        (replicate, source)
        for replicate in range(int(configuration["replicates"]))
        for source in ("g17", "g18")
    }
    actual_inventory = {
        (int(row.get("replicate", -1)), row.get("source")) for row in rows
    }
    if actual_inventory != expected_inventory or len(rows) != len(expected_inventory):
        errors.append("training source inventory mismatch")
    for row in rows:
        source = str(row.get("source"))
        replicate = int(row.get("replicate", -1))
        if (replicate, source) not in expected_inventory:
            errors.append("training row identity invalid")
            continue
        if row.get("seeds") != _seeds(source, replicate, formal=formal):
            errors.append(f"{source} seed mismatch")
        if int(row.get("updates", -1)) != int(configuration.get(f"{source}_updates", -2)):
            errors.append(f"{source} update count mismatch")
        if not bool(row.get("finite_updates")):
            errors.append(f"{row.get('source')} non-finite update")
        if not bool(row.get("lifecycle_contract_valid")):
            errors.append(f"{row.get('source')} lifecycle contract invalid")
        if float(row.get("parameter_drift", 0.0)) <= 0.0:
            errors.append(f"{row.get('source')} parameter did not move")
        replay_values = row.get("maximum_replay_errors", {}).values()
        if not replay_values or max(float(value) for value in replay_values) > REPLAY_TOLERANCE:
            errors.append(f"{row.get('source')} replay mismatch")
    controls = evaluation.get("source_controls", {})
    if not bool(controls.get("g17", {}).get("constructive_access_valid")):
        errors.append("G17 source access control failed")
    if controls.get("g18", {}).get("branch") != battery_source.PASS_BRANCH:
        errors.append("G18 information gate control failed")

    cells = evaluation.get("cells", [])
    if len(cells) != 7 * int(configuration["replicates"]):
        errors.append("evaluation cell inventory mismatch")
    expected_roster = [4, 4, 4, 4, 4, 4, 2, 2, 2, 2, 4, 4]
    for cell in [row for row in cells if row.get("source") == "g18"]:
        slot_rows = cell.get("slot_rows", [])
        if len(slot_rows) != len(battery_source.GATE_SLOT_ORDERS) or not all(
            bool(row.get("inactive_action_zero"))
            and row.get("roster_sizes") == expected_roster
            for row in slot_rows
        ):
            errors.append("G18 evaluation lifecycle contract invalid")

    metrics: dict[str, Any] = {
        "operational_valid": not errors,
        "maximum_replay_error": (
            max(
                float(value)
                for row in rows
                for value in row.get("maximum_replay_errors", {}).values()
            )
            if rows and all(row.get("maximum_replay_errors") for row in rows)
            else float("inf")
        ),
    }
    if formal and not errors:
        replicate_count = int(configuration["replicates"])

        def ordered_cells(**criteria: str) -> list[dict[str, Any]]:
            selected = [
                row
                for row in cells
                if all(row.get(name) == value for name, value in criteria.items())
            ]
            selected.sort(key=lambda row: int(row["replicate"]))
            if len(selected) != replicate_count:
                raise ValueError(f"G18 cell inventory mismatch: {criteria}")
            return selected

        try:
            g17_iid_rows = ordered_cells(
                source="g17", checkpoint="final", domain="iid"
            )
            g17_heldout_rows = ordered_cells(
                source="g17", checkpoint="final", domain="heldout"
            )
            g17_zero_rows = ordered_cells(
                source="g17", checkpoint="zero", domain="heldout"
            )
            mapping_rows = ordered_cells(
                source="g17", checkpoint="final", domain="mapping"
            )
            g18_final_rows = ordered_cells(source="g18", checkpoint="final")
            g18_zero_rows = ordered_cells(source="g18", checkpoint="zero")
            g17_iid = np.asarray(
                [row["utility"] for row in g17_iid_rows], dtype=np.float64
            )
            g17_heldout = np.asarray(
                [row["utility"] for row in g17_heldout_rows], dtype=np.float64
            )
            g17_zero = np.asarray(
                [row["utility"] for row in g17_zero_rows], dtype=np.float64
            )
            g18_final = np.asarray(
                [
                    [slot["utility"] for slot in row["slot_rows"]]
                    for row in g18_final_rows
                ],
                dtype=np.float64,
            )
            g18_zero = np.asarray(
                [
                    [slot["utility"] for slot in row["slot_rows"]]
                    for row in g18_zero_rows
                ],
                dtype=np.float64,
            )
            g18_spike = np.asarray(
                [
                    [slot["spike_utility"] for slot in row["slot_rows"]]
                    for row in g18_final_rows
                ],
                dtype=np.float64,
            )
            g18_rotating = np.asarray(
                [
                    [slot["low_rotating_effort_share"] for slot in row["slot_rows"]]
                    for row in g18_final_rows
                ],
                dtype=np.float64,
            )
            repetitions = int(configuration["bootstrap_repetitions"])
            metrics.update(
                {
                    "g17_iid_utility_ci95": g17_runner._hierarchical_ci(
                        g17_iid, seed=BOOTSTRAP_SEED, repetitions=repetitions
                    ),
                    "g17_heldout_utility_ci95": g17_runner._hierarchical_ci(
                        g17_heldout,
                        seed=BOOTSTRAP_SEED + 1,
                        repetitions=repetitions,
                    ),
                    "g17_gain_ci95": g17_runner._hierarchical_ci(
                        g17_heldout - g17_zero,
                        seed=BOOTSTRAP_SEED + 2,
                        repetitions=repetitions,
                    ),
                    "g17_minimum_episode": float(
                        min(g17_iid.min(), g17_heldout.min())
                    ),
                    "g17_minimum_effort_correlation": min(
                        float(row["effort_correlation"]) for row in mapping_rows
                    ),
                    "g17_minimum_mix_correlation": min(
                        float(row["mix_correlation"]) for row in mapping_rows
                    ),
                    "g17_maximum_effort_mae": max(
                        float(row["effort_mae"]) for row in mapping_rows
                    ),
                    "g17_maximum_mix_mae": max(
                        float(row["mix_mae"]) for row in mapping_rows
                    ),
                    "g18_utility_ci95": g17_runner._hierarchical_ci(
                        g18_final,
                        seed=BOOTSTRAP_SEED + 3,
                        repetitions=repetitions,
                    ),
                    "g18_gain_ci95": g17_runner._hierarchical_ci(
                        g18_final - g18_zero,
                        seed=BOOTSTRAP_SEED + 4,
                        repetitions=repetitions,
                    ),
                    "g18_spike_utility_ci95": g17_runner._hierarchical_ci(
                        g18_spike,
                        seed=BOOTSTRAP_SEED + 5,
                        repetitions=repetitions,
                    ),
                    "g18_rotating_effort_share_ci95": g17_runner._hierarchical_ci(
                        g18_rotating,
                        seed=BOOTSTRAP_SEED + 6,
                        repetitions=repetitions,
                    ),
                    "g18_minimum_replicate_utility": float(
                        g18_final.mean(axis=1).min()
                    ),
                    "operational_valid": True,
                }
            )
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
            metrics = {
                "operational_valid": False,
                "maximum_replay_error": metrics["maximum_replay_error"],
            }
    branch = (
        select_result_branch(metrics)
        if formal
        else (NONFORMAL_BRANCH if not errors else INVALID_BRANCH)
    )
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
        "metrics": metrics,
        "thresholds": {
            "g17_utility_floor": G17_UTILITY_FLOOR,
            "g17_gain_floor": G17_GAIN_FLOOR,
            "g17_minimum_episode_floor": G17_MINIMUM_EPISODE_FLOOR,
            "g17_correlation_floor": G17_CORRELATION_FLOOR,
            "g17_mae_ceiling": G17_MAE_CEILING,
            "g18_utility_floor": G18_UTILITY_FLOOR,
            "g18_gain_floor": G18_GAIN_FLOOR,
            "g18_spike_utility_floor": G18_SPIKE_UTILITY_FLOOR,
            "g18_rotating_effort_share_floor": G18_ROTATING_EFFORT_SHARE_FLOOR,
            "replay_tolerance": REPLAY_TOLERANCE,
        },
        "interpretation": (
            "formal dual-source delayed-credit evidence; no UAV claim"
            if formal
            else "bounded formal-path exercise only; no scientific evidence"
        ),
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "analyze"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--require-formal", action="store_true")
    arguments = parser.parse_args()
    if arguments.mode == "train":
        value = train(
            run_root=arguments.run_root,
            source_commit=str(arguments.source_commit or ""),
            formal=bool(arguments.formal),
            authorization_token=arguments.authorization_token,
        )
    elif arguments.mode == "evaluate":
        value = evaluate(run_root=arguments.run_root)
    else:
        value = analyze(
            run_root=arguments.run_root,
            require_formal=bool(arguments.require_formal),
        )
    print(
        json.dumps(
            {
                "algorithm": value["algorithm"],
                "stage": value["stage"],
                "status": value["status"],
                "formal": value["formal"],
                "run_root": str(arguments.run_root),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
