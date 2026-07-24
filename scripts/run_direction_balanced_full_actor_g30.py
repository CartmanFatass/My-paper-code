"""Train, evaluate, and analyze formal G30 paired-toy evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import time
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    maximum_state_difference,
    optimize_fast_anchor_update,
)
from ha_ctse_process.direction_balanced_full_actor_g30 import (
    DirectionBalancedFullActorPolicy,
    optimize_direction_balanced_update,
)
from ha_ctse_process.separated_credit_g18 import (
    collect_battery_trajectory,
    evaluate_battery_policy,
)
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner
from scripts import screen_direction_balanced_full_actor_g30 as screen


SCHEMA_VERSION = 1
ALGORITHM_ID = "DIRECTION_BALANCED_FULL_ACTOR_G30"
AUTHORIZATION_TOKEN = "AUTHORIZE_DIRECTION_BALANCED_FULL_ACTOR_G30_FORMAL_CPU_V1"

GAMMA = 0.99
HIDDEN_DIM = 32
LEARNING_RATE = 1e-3
INITIAL_LOG_STD = -1.0
FORMAL_REPLICATES = 3
FORMAL_NUM_ENVS = 8
FORMAL_PPO_PASSES = 2
FORMAL_G17_FAST_UPDATES = 100
FORMAL_G17_DIRECTION_UPDATES = 100
FORMAL_G18_FAST_UPDATES = 100
FORMAL_G18_DIRECTION_UPDATES = 300
FORMAL_EVAL_EPISODES = 128
FORMAL_BOOTSTRAP_REPETITIONS = 10_000

EXERCISE_REPLICATES = 1
EXERCISE_NUM_ENVS = 2
EXERCISE_PPO_PASSES = 1
EXERCISE_FAST_UPDATES = 1
EXERCISE_DIRECTION_UPDATES = 1
EXERCISE_EVAL_EPISODES = 4

SEED_BASES = {
    "g17": {
        "model": 7_119_000,
        "ledger": 7_129_000,
        "action": 7_139_000,
        "evaluation_ledger": 7_149_000,
        "evaluation_action": 7_159_000,
    },
    "g18": {"model": 7_219_000, "action": 7_239_000},
}
BOOTSTRAP_SEED = 7_260_030

REPLAY_TOLERANCE = 1e-6
DIRECTION_DOT_TOLERANCE = 1e-7
IDENTITY_TOLERANCE = 1e-7
G17_UTILITY_FLOOR = 0.90
G17_GAIN_FLOOR = 0.10
G17_MINIMUM_EPISODE_FLOOR = 0.80
G17_CORRELATION_FLOOR = 0.90
G17_MAE_CEILING = 0.05
G18_UTILITY_FLOOR = 0.95
G18_GAIN_FLOOR = 0.10
G18_SPIKE_UTILITY_FLOOR = 0.90
G18_ROTATING_EFFORT_SHARE_FLOOR = 0.75
G18_REPLICATE_STABILITY_FLOOR = 0.90

INVALID_BRANCH = "INVALID_DIRECTION_BALANCED_FULL_ACTOR_G30"
NO_G17_BRANCH = "NO_G17_COMPATIBILITY_DIRECTION_BALANCED_G30"
NO_G18_ACCESS_BRANCH = "NO_DELAYED_ACCESS_DIRECTION_BALANCED_G30"
NO_G18_MECHANISM_BRANCH = "NO_DELAYED_MECHANISM_DIRECTION_BALANCED_G30"
UNSTABLE_BRANCH = "UNSTABLE_DIRECTION_BALANCED_FULL_ACTOR_G30"
USABLE_BRANCH = "USABLE_DIRECTION_BALANCED_FULL_ACTOR_G30"
NONFORMAL_BRANCH = "NONFORMAL_DIRECTION_BALANCED_FORMAL_PATH_EXERCISE_COMPLETE"


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


def _counts(*, formal: bool) -> dict[str, int]:
    if formal:
        return {
            "replicates": FORMAL_REPLICATES,
            "num_envs": FORMAL_NUM_ENVS,
            "ppo_passes": FORMAL_PPO_PASSES,
            "g17_fast_updates": FORMAL_G17_FAST_UPDATES,
            "g17_direction_updates": FORMAL_G17_DIRECTION_UPDATES,
            "g18_fast_updates": FORMAL_G18_FAST_UPDATES,
            "g18_direction_updates": FORMAL_G18_DIRECTION_UPDATES,
            "eval_episodes": FORMAL_EVAL_EPISODES,
            "bootstrap_repetitions": FORMAL_BOOTSTRAP_REPETITIONS,
        }
    return {
        "replicates": EXERCISE_REPLICATES,
        "num_envs": EXERCISE_NUM_ENVS,
        "ppo_passes": EXERCISE_PPO_PASSES,
        "g17_fast_updates": EXERCISE_FAST_UPDATES,
        "g17_direction_updates": EXERCISE_DIRECTION_UPDATES,
        "g18_fast_updates": EXERCISE_FAST_UPDATES,
        "g18_direction_updates": EXERCISE_DIRECTION_UPDATES,
        "eval_episodes": EXERCISE_EVAL_EPISODES,
        "bootstrap_repetitions": 0,
    }


def _configuration(*, formal: bool) -> dict[str, Any]:
    return {
        **_counts(formal=formal),
        "gamma": GAMMA,
        "hidden_dim": HIDDEN_DIM,
        "learning_rate": LEARNING_RATE,
        "initial_log_std": INITIAL_LOG_STD,
        "actor_gradient_rule": "equal_global_unit_gradient_directions",
        "actor_global_rescale": "none_existing_gradient_clip_only",
        "actor_optimizer_state_rule": "ordinary_adam_on_applied_direction",
        "checkpoint_identity": "fresh_no_g28_g29_g30_screen_resume",
        "residual": "exact_zero_frozen",
    }


def _seeds(source: str, replicate: int, *, formal: bool) -> dict[str, int]:
    if source not in SEED_BASES:
        raise ValueError(f"unknown G30 source: {source}")
    offset = int(replicate) + (0 if formal else 900_000)
    return {
        name: int(value) + offset
        for name, value in SEED_BASES[source].items()
    }


def _copy_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }


def _checkpoint_reference(source: str, replicate: int, kind: str) -> str:
    return f"checkpoints/{source}_replicate_{replicate}_{kind}.pt"


def _save_checkpoint(
    path: Path,
    *,
    source: str,
    source_commit: str,
    formal: bool,
    replicate: int,
    fast_updates: int,
    direction_updates: int,
    configuration: dict[str, Any],
    model: DirectionBalancedFullActorPolicy,
) -> None:
    torch.save(
        {
            "schema_version": SCHEMA_VERSION,
            "algorithm": ALGORITHM_ID,
            "formal": bool(formal),
            "source": source,
            "source_commit": source_commit,
            "replicate": int(replicate),
            "completed_fast_updates": int(fast_updates),
            "completed_direction_updates": int(direction_updates),
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
    fast_updates: int,
    direction_updates: int,
    configuration: dict[str, Any],
    seeds: dict[str, int],
) -> DirectionBalancedFullActorPolicy:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    expected = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "formal": bool(formal),
        "source": source,
        "source_commit": source_commit,
        "replicate": int(replicate),
        "completed_fast_updates": int(fast_updates),
        "completed_direction_updates": int(direction_updates),
        "configuration": configuration,
    }
    if not isinstance(payload, dict):
        raise ValueError("G30 checkpoint is not a dictionary")
    for name, value in expected.items():
        if payload.get(name) != value:
            raise ValueError(f"G30 checkpoint {name} mismatch")
    if not isinstance(payload.get("model_state"), dict):
        raise ValueError("G30 checkpoint model state is missing")
    g17_runner.configure_runtime(seeds["model"])
    model = screen.make_model(source)
    model.load_state_dict(payload["model_state"])
    return model


def _collect(
    source: str,
    model: DirectionBalancedFullActorPolicy,
    *,
    episode_ids: tuple[int, ...],
    seeds: dict[str, int],
):
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


def _train_source(
    *,
    run_root: Path,
    source: str,
    source_commit: str,
    formal: bool,
    replicate: int,
    configuration: dict[str, Any],
    seeds: dict[str, int],
) -> dict[str, Any]:
    g17_runner.configure_runtime(seeds["model"])
    model = screen.make_model(source)
    zero_state = _copy_state(model)
    zero_reference = _checkpoint_reference(source, replicate, "zero")
    final_reference = _checkpoint_reference(source, replicate, "final")
    _save_checkpoint(
        run_root / zero_reference,
        source=source,
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        fast_updates=0,
        direction_updates=0,
        configuration=configuration,
        model=model,
    )
    fast_updates = int(configuration[f"{source}_fast_updates"])
    direction_updates = int(configuration[f"{source}_direction_updates"])
    num_envs = int(configuration["num_envs"])
    ppo_passes = int(configuration["ppo_passes"])
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters()
        + tuple(model.credit_baselines.parameters()),
        lr=LEARNING_RATE,
    )
    maximum_replay_errors: dict[str, float] = {}
    lifecycle_valid = True
    finite = True
    active_rows = 0
    for update in range(fast_updates):
        first_episode = update * num_envs
        trajectory = _collect(
            source,
            model,
            episode_ids=tuple(
                range(first_episode, first_episode + num_envs)
            ),
            seeds=seeds,
        )
        lifecycle_valid = (
            lifecycle_valid
            and screen.g19_screen._trajectory_contract_valid(
                source, trajectory
            )
        )
        metrics = optimize_fast_anchor_update(
            model,
            fast_optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=ppo_passes,
        )
        finite = finite and bool(metrics["finite_update"])
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                maximum_replay_errors[name] = max(
                    maximum_replay_errors.get(name, 0.0), float(value)
                )
        active_rows += trajectory.active_token_count

    direction_start = screen._actor_state(model)
    model.begin_direction_balanced_phase()
    ownership_valid = screen._optimizer_ownership_valid(model)
    actor_optimizer = torch.optim.Adam(
        model.full_actor_parameters(), lr=LEARNING_RATE
    )
    critic_optimizer = torch.optim.Adam(
        model.critic_parameters(), lr=LEARNING_RATE
    )
    minimum_direction_dot = float("inf")
    maximum_identity_error = 0.0
    minimum_step_increment = float("inf")
    for update in range(direction_updates):
        first_episode = (fast_updates + update) * num_envs
        trajectory = _collect(
            source,
            model,
            episode_ids=tuple(
                range(first_episode, first_episode + num_envs)
            ),
            seeds=seeds,
        )
        lifecycle_valid = (
            lifecycle_valid
            and screen.g19_screen._trajectory_contract_valid(
                source, trajectory
            )
        )
        metrics = optimize_direction_balanced_update(
            model,
            actor_optimizer,
            critic_optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=ppo_passes,
            gamma=GAMMA,
        )
        finite = finite and bool(metrics["finite_update"])
        minimum_direction_dot = min(
            minimum_direction_dot,
            float(metrics["minimum_direction_immediate_dot"]),
        )
        maximum_identity_error = max(
            maximum_identity_error,
            float(metrics["maximum_direction_composition_identity_error"]),
        )
        minimum_step_increment = min(
            minimum_step_increment,
            float(metrics["minimum_actor_optimizer_step_increment"]),
        )
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                maximum_replay_errors[name] = max(
                    maximum_replay_errors.get(name, 0.0), float(value)
                )
        active_rows += trajectory.active_token_count

    _save_checkpoint(
        run_root / final_reference,
        source=source,
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        fast_updates=fast_updates,
        direction_updates=direction_updates,
        configuration=configuration,
        model=model,
    )
    return {
        "source": source,
        "replicate": replicate,
        "seeds": seeds,
        "fast_updates": fast_updates,
        "direction_updates": direction_updates,
        "optimizer_steps": 2
        * (fast_updates + 2 * direction_updates),
        "active_rows": int(active_rows),
        "finite_updates": bool(finite),
        "lifecycle_contract_valid": bool(lifecycle_valid),
        "optimizer_ownership_valid": bool(ownership_valid),
        "maximum_replay_errors": maximum_replay_errors,
        "actor_maximum_difference": maximum_state_difference(
            direction_start, screen._actor_state(model)
        ),
        "parameter_drift": maximum_state_difference(
            zero_state, _copy_state(model)
        ),
        "residual_output_layer_maximum_absolute_value": (
            model.residual_output_layer_maximum_absolute_value()
        ),
        "minimum_direction_immediate_dot": float(minimum_direction_dot),
        "maximum_direction_composition_identity_error": float(
            maximum_identity_error
        ),
        "minimum_actor_optimizer_step_increment": float(
            minimum_step_increment
        ),
        "zero_checkpoint": zero_reference,
        "final_checkpoint": final_reference,
    }


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G30 run requires an integrated 40-hex source commit")
    if formal and authorization_token != AUTHORIZATION_TOKEN:
        raise ValueError("formal G30 authorization token mismatch")
    if not formal and authorization_token is not None:
        raise ValueError("nonformal G30 exercise cannot carry formal authority")
    run_root.mkdir(parents=True, exist_ok=False)
    (run_root / "checkpoints").mkdir()
    configuration = _configuration(formal=formal)
    g17_runner.configure_runtime(_seeds("g17", 0, formal=formal)["model"])
    started = time.perf_counter()
    rows = [
        _train_source(
            run_root=run_root,
            source=source,
            source_commit=source_commit,
            formal=formal,
            replicate=replicate,
            configuration=configuration,
            seeds=_seeds(source, replicate, formal=formal),
        )
        for replicate in range(int(configuration["replicates"]))
        for source in ("g17", "g18")
    ]
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
    model: DirectionBalancedFullActorPolicy,
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
        "minimum_episode": float(np.min(utilities)),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    if (
        training.get("algorithm") != ALGORITHM_ID
        or training.get("status") != "COMPLETE"
    ):
        raise ValueError("G30 evaluation requires complete training")
    formal = bool(training.get("formal"))
    configuration = _configuration(formal=formal)
    if training.get("configuration") != configuration:
        raise ValueError("G30 evaluation configuration mismatch")
    source_commit = str(training["source_commit"])
    cells: list[dict[str, Any]] = []
    for row in training["source_results"]:
        source = str(row["source"])
        replicate = int(row["replicate"])
        seeds = {name: int(value) for name, value in row["seeds"].items()}
        for kind in ("zero", "final"):
            fast_updates = 0 if kind == "zero" else int(row["fast_updates"])
            direction_updates = (
                0 if kind == "zero" else int(row["direction_updates"])
            )
            model = _load_checkpoint(
                run_root / row[f"{kind}_checkpoint"],
                source=source,
                source_commit=source_commit,
                formal=formal,
                replicate=replicate,
                fast_updates=fast_updates,
                direction_updates=direction_updates,
                configuration=configuration,
                seeds=seeds,
            )
            if source == "g18":
                cells.append(
                    {
                        "source": source,
                        "replicate": replicate,
                        "checkpoint": kind,
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
                        "checkpoint": kind,
                        **_g17_cell(
                            model,
                            domain=domain,
                            seeds=seeds,
                            eval_episodes=int(
                                configuration["eval_episodes"]
                            ),
                        ),
                    }
                )
            if kind == "final":
                cells.append(
                    {
                        "source": source,
                        "replicate": replicate,
                        "checkpoint": kind,
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
        "configuration": configuration,
        "source_controls": {
            "g17": g17_runner._source_controls(),
            "g18": battery_source.run_information_gate(),
        },
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def select_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not (
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
        and float(metrics["g17_maximum_effort_mae"])
        <= G17_MAE_CEILING
        and float(metrics["g17_maximum_mix_mae"]) <= G17_MAE_CEILING
    ):
        return NO_G17_BRANCH
    if not (
        float(metrics["g18_utility_ci95"][0]) >= G18_UTILITY_FLOOR
        and float(metrics["g18_gain_ci95"][0]) >= G18_GAIN_FLOOR
        and float(metrics["g18_spike_utility_ci95"][0])
        >= G18_SPIKE_UTILITY_FLOOR
    ):
        return NO_G18_ACCESS_BRANCH
    if (
        float(metrics["g18_rotating_effort_share_ci95"][0])
        < G18_ROTATING_EFFORT_SHARE_FLOOR
    ):
        return NO_G18_MECHANISM_BRANCH
    if (
        float(metrics["g18_minimum_replicate_utility"])
        < G18_REPLICATE_STABILITY_FLOOR
    ):
        return UNSTABLE_BRANCH
    return USABLE_BRANCH


def _ordered_cells(
    cells: list[dict[str, Any]],
    replicate_count: int,
    **criteria: str,
) -> list[dict[str, Any]]:
    selected = [
        row
        for row in cells
        if all(row.get(name) == value for name, value in criteria.items())
    ]
    selected.sort(key=lambda row: int(row["replicate"]))
    if len(selected) != replicate_count:
        raise ValueError(f"G30 cell inventory mismatch: {criteria}")
    return selected


def _validate_artifacts(
    run_root: Path,
    training: dict[str, Any],
    evaluation: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    formal = bool(training.get("formal"))
    configuration = _configuration(formal=formal)
    source_commit = training.get("source_commit")
    if re.fullmatch(r"[0-9a-f]{40}", str(source_commit)) is None:
        errors.append("source commit invalid")
    for artifact, stage in ((training, "train"), (evaluation, "evaluate")):
        if artifact.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{stage} schema mismatch")
        if artifact.get("algorithm") != ALGORITHM_ID:
            errors.append(f"{stage} algorithm mismatch")
        if artifact.get("stage") != stage:
            errors.append(f"{stage} stage mismatch")
        if artifact.get("status") != "COMPLETE":
            errors.append(f"{stage} incomplete")
        if artifact.get("formal") is not formal:
            errors.append(f"{stage} formal identity mismatch")
        if artifact.get("source_commit") != source_commit:
            errors.append(f"{stage} source mismatch")
        if artifact.get("configuration") != configuration:
            errors.append(f"{stage} configuration mismatch")
        runtime = artifact.get("runtime", {})
        if (
            runtime.get("backend") != "cpu"
            or runtime.get("torch_threads") != 1
            or runtime.get("torch") != str(torch.__version__)
        ):
            errors.append(f"{stage} runtime mismatch")
    if formal:
        if training.get("authorization_token") != AUTHORIZATION_TOKEN:
            errors.append("formal authorization token mismatch")
    elif training.get("authorization_token") is not None:
        errors.append("nonformal artifact carries formal authority")

    rows = training.get("source_results")
    expected_pairs = {
        (replicate, source)
        for replicate in range(int(configuration["replicates"]))
        for source in ("g17", "g18")
    }
    if not isinstance(rows, list) or len(rows) != len(expected_pairs):
        errors.append("training row inventory mismatch")
        rows = []
    seen: set[tuple[int, str]] = set()
    checkpoint_references: set[str] = set()
    for row in rows:
        try:
            pair = (int(row["replicate"]), str(row["source"]))
            if pair not in expected_pairs or pair in seen:
                raise ValueError("training pair duplicate or misdirected")
            seen.add(pair)
            replicate, source = pair
            seeds = _seeds(source, replicate, formal=formal)
            if row.get("seeds") != seeds:
                raise ValueError("training seeds mismatch")
            fast_updates = int(configuration[f"{source}_fast_updates"])
            direction_updates = int(
                configuration[f"{source}_direction_updates"]
            )
            if (
                row.get("fast_updates") != fast_updates
                or row.get("direction_updates") != direction_updates
            ):
                raise ValueError("training exposure mismatch")
            replay_errors = row.get("maximum_replay_errors", {})
            if (
                not row.get("finite_updates")
                or not row.get("lifecycle_contract_valid")
                or not row.get("optimizer_ownership_valid")
                or not isinstance(replay_errors, dict)
                or not replay_errors
                or max(float(value) for value in replay_errors.values())
                > REPLAY_TOLERANCE
                or float(row.get("actor_maximum_difference", 0.0)) <= 0.0
                or float(row.get("parameter_drift", 0.0)) <= 0.0
                or float(
                    row.get(
                        "residual_output_layer_maximum_absolute_value",
                        float("inf"),
                    )
                )
                != 0.0
                or float(
                    row.get("minimum_direction_immediate_dot", float("-inf"))
                )
                < -DIRECTION_DOT_TOLERANCE
                or float(
                    row.get(
                        "maximum_direction_composition_identity_error",
                        float("inf"),
                    )
                )
                > IDENTITY_TOLERANCE
                or float(
                    row.get(
                        "minimum_actor_optimizer_step_increment",
                        float("-inf"),
                    )
                )
                != 1.0
            ):
                raise ValueError("training invariant mismatch")
            for kind, completed_fast, completed_direction in (
                ("zero", 0, 0),
                ("final", fast_updates, direction_updates),
            ):
                reference = row.get(f"{kind}_checkpoint")
                expected = _checkpoint_reference(source, replicate, kind)
                if reference != expected or reference in checkpoint_references:
                    raise ValueError("checkpoint inventory mismatch")
                checkpoint_references.add(reference)
                _load_checkpoint(
                    run_root / reference,
                    source=source,
                    source_commit=str(source_commit),
                    formal=formal,
                    replicate=replicate,
                    fast_updates=completed_fast,
                    direction_updates=completed_direction,
                    configuration=configuration,
                    seeds=seeds,
                )
        except (KeyError, TypeError, ValueError, OSError) as error:
            errors.append(str(error))
    if seen != expected_pairs:
        errors.append("training pair inventory incomplete")

    controls = evaluation.get("source_controls", {})
    if controls.get("g17") != g17_runner._source_controls():
        errors.append("G17 source controls mismatch")
    if controls.get("g18") != battery_source.run_information_gate():
        errors.append("G18 source controls mismatch")
    cells = evaluation.get("cells")
    expected_cell_count = int(configuration["replicates"]) * 7
    if not isinstance(cells, list) or len(cells) != expected_cell_count:
        errors.append("evaluation cell inventory mismatch")
        cells = []
    expected_cells = {
        (replicate, "g17", checkpoint, domain)
        for replicate in range(int(configuration["replicates"]))
        for checkpoint, domain in (
            ("zero", "iid"),
            ("zero", "heldout"),
            ("final", "iid"),
            ("final", "heldout"),
            ("final", "mapping"),
        )
    } | {
        (replicate, "g18", checkpoint, "")
        for replicate in range(int(configuration["replicates"]))
        for checkpoint in ("zero", "final")
    }
    observed_cells: set[tuple[int, str, str, str]] = set()
    for cell in cells:
        try:
            key = (
                int(cell["replicate"]),
                str(cell["source"]),
                str(cell["checkpoint"]),
                str(cell.get("domain", "")),
            )
            if key not in expected_cells or key in observed_cells:
                raise ValueError("evaluation cell duplicate or misdirected")
            observed_cells.add(key)
            if key[1] == "g17" and key[3] != "mapping":
                utilities = cell.get("utility")
                if (
                    not isinstance(utilities, list)
                    or len(utilities) != int(configuration["eval_episodes"])
                    or not all(np.isfinite(float(value)) for value in utilities)
                ):
                    raise ValueError("G17 evaluation support mismatch")
            elif key[1] == "g17":
                for name in (
                    "effort_correlation",
                    "mix_correlation",
                    "effort_mae",
                    "mix_mae",
                ):
                    if not np.isfinite(float(cell[name])):
                        raise ValueError("G17 mapping metric nonfinite")
            else:
                slot_rows = cell.get("slot_rows")
                if not isinstance(slot_rows, list) or len(slot_rows) != 3:
                    raise ValueError("G18 slot-layout support mismatch")
                for slot in slot_rows:
                    if not bool(slot.get("inactive_action_zero")):
                        raise ValueError("G18 inactive action mismatch")
                    for name in (
                        "utility",
                        "spike_utility",
                        "low_rotating_effort_share",
                    ):
                        if not np.isfinite(float(slot[name])):
                            raise ValueError("G18 evaluation metric nonfinite")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
    if observed_cells != expected_cells:
        errors.append("evaluation cell inventory incomplete")
    return errors


def analyze(
    *, run_root: Path, require_formal: bool = False
) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal analysis requires formal G30 artifacts")
    errors = _validate_artifacts(run_root, training, evaluation)
    configuration = _configuration(formal=formal)
    metrics: dict[str, Any] = {
        "operational_valid": not errors,
        "maximum_replay_error": (
            max(
                float(value)
                for row in training.get("source_results", [])
                for value in row.get("maximum_replay_errors", {}).values()
            )
            if training.get("source_results")
            else float("inf")
        ),
    }
    cells = evaluation.get("cells", [])
    if formal and not errors:
        try:
            replicates = int(configuration["replicates"])
            g17_iid_rows = _ordered_cells(
                cells,
                replicates,
                source="g17",
                checkpoint="final",
                domain="iid",
            )
            g17_heldout_rows = _ordered_cells(
                cells,
                replicates,
                source="g17",
                checkpoint="final",
                domain="heldout",
            )
            g17_zero_rows = _ordered_cells(
                cells,
                replicates,
                source="g17",
                checkpoint="zero",
                domain="heldout",
            )
            mapping_rows = _ordered_cells(
                cells,
                replicates,
                source="g17",
                checkpoint="final",
                domain="mapping",
            )
            g18_final_rows = _ordered_cells(
                cells, replicates, source="g18", checkpoint="final"
            )
            g18_zero_rows = _ordered_cells(
                cells, replicates, source="g18", checkpoint="zero"
            )
            g17_iid = np.asarray(
                [row["utility"] for row in g17_iid_rows], dtype=np.float64
            )
            g17_heldout = np.asarray(
                [row["utility"] for row in g17_heldout_rows],
                dtype=np.float64,
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
                    [
                        slot["low_rotating_effort_share"]
                        for slot in row["slot_rows"]
                    ]
                    for row in g18_final_rows
                ],
                dtype=np.float64,
            )
            repetitions = int(configuration["bootstrap_repetitions"])
            metrics.update(
                {
                    "g17_iid_utility_ci95": g17_runner._hierarchical_ci(
                        g17_iid,
                        seed=BOOTSTRAP_SEED,
                        repetitions=repetitions,
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
                        float(row["effort_correlation"])
                        for row in mapping_rows
                    ),
                    "g17_minimum_mix_correlation": min(
                        float(row["mix_correlation"])
                        for row in mapping_rows
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
                    "g18_rotating_effort_share_ci95": (
                        g17_runner._hierarchical_ci(
                            g18_rotating,
                            seed=BOOTSTRAP_SEED + 6,
                            repetitions=repetitions,
                        )
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
            "g18_rotating_effort_share_floor": (
                G18_ROTATING_EFFORT_SHARE_FLOOR
            ),
            "g18_replicate_stability_floor": G18_REPLICATE_STABILITY_FLOOR,
            "replay_tolerance": REPLAY_TOLERANCE,
            "direction_dot_tolerance": DIRECTION_DOT_TOLERANCE,
            "identity_tolerance": IDENTITY_TOLERANCE,
        },
        "interpretation": (
            "formal paired-toy direction-balanced evidence; no UAV claim"
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
