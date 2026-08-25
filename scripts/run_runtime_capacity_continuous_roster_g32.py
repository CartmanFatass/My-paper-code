"""Train, evaluate, and analyze runtime-capacity G32 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import runtime_capacity_continuous_roster_g32 as source
from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    maximum_state_difference,
    optimize_fast_anchor_update,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.return_to_go_direction_balanced_full_actor_g31 import (
    ReturnToGoDirectionBalancedFullActorPolicy,
    optimize_return_to_go_direction_balanced_update,
)
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = "RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32"
AUTHORIZATION_TOKEN = "AUTHORIZE_RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_FORMAL_CPU_V1"
INVALID_BRANCH = "INVALID_RUNTIME_CAPACITY_G32"
NO_PADDING_BRANCH = "NO_PADDING_CAPACITY_INVARIANCE_G32"
NO_TRAIN_BRANCH = "NO_TRAIN_CAPACITY_ACCESS_G32"
NO_CHURN_BRANCH = "NO_COUNT_CHURN_ACCESS_G32"
UNSTABLE_BRANCH = "UNSTABLE_RUNTIME_CAPACITY_G32"
USABLE_BRANCH = "USABLE_RUNTIME_CAPACITY_G32"
NONFORMAL_BRANCH = "NONFORMAL_RUNTIME_CAPACITY_G32_EXERCISE_COMPLETE"

GAMMA = 0.99
HIDDEN_DIM = 32
LEARNING_RATE = 1e-3
INITIAL_LOG_STD = -1.0
REPLAY_TOLERANCE = 1e-6
UTILITY_FLOOR = 0.90
GAIN_FLOOR = 0.0
CORRELATION_FLOOR = 0.90
MAE_CEILING = 0.05
MINIMUM_HELDOUT_REPLICATE_FLOOR = 0.85
HELDOUT_STOCHASTIC_FLOOR = 0.80
FORMAL_REPLICATES = 3
FORMAL_FAST_UPDATES = 100
FORMAL_RETURN_TO_GO_UPDATES = 100
FORMAL_NUM_ENVS = 8
FORMAL_PPO_PASSES = 2
FORMAL_EVAL_EPISODES = 128
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
EXERCISE_REPLICATES = 1
EXERCISE_FAST_UPDATES = 1
EXERCISE_RETURN_TO_GO_UPDATES = 1
EXERCISE_NUM_ENVS = 2
EXERCISE_PPO_PASSES = 1
EXERCISE_EVAL_EPISODES = 4
BOOTSTRAP_SEED = 10_320_032
SEED_BASES = {
    "model": 10_321_000,
    "ledger": 10_322_000,
    "action": 10_323_000,
    "evaluation_ledger": 10_324_000,
    "evaluation_action": 10_325_000,
}

PROFILES = {
    "train_capacity_8": roster_env.TRAIN_PROFILES,
    "padding_capacity_8": (roster_env.PADDING_CAPACITY_8,),
    "small_capacity_6": (roster_env.SMALL_CAPACITY_6,),
    "large_capacity_12": (roster_env.LARGE_CAPACITY_12,),
}
PADDING_MISMATCH_FIELDS = (
    "observation", "value", "action", "reward", "hidden"
)


def configure_runtime(seed: int) -> None:
    torch.set_num_threads(1)
    torch.manual_seed(int(seed))


def _runtime_identity() -> dict[str, Any]:
    return {
        "backend": "cpu", "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _counts(*, formal: bool) -> dict[str, int]:
    if formal:
        return {
            "replicates": FORMAL_REPLICATES, "fast_updates": FORMAL_FAST_UPDATES,
            "return_to_go_updates": FORMAL_RETURN_TO_GO_UPDATES,
            "num_envs": FORMAL_NUM_ENVS, "ppo_passes": FORMAL_PPO_PASSES,
            "eval_episodes": FORMAL_EVAL_EPISODES,
            "bootstrap_repetitions": FORMAL_BOOTSTRAP_REPETITIONS,
        }
    return {
        "replicates": EXERCISE_REPLICATES, "fast_updates": EXERCISE_FAST_UPDATES,
        "return_to_go_updates": EXERCISE_RETURN_TO_GO_UPDATES,
        "num_envs": EXERCISE_NUM_ENVS, "ppo_passes": EXERCISE_PPO_PASSES,
        "eval_episodes": EXERCISE_EVAL_EPISODES, "bootstrap_repetitions": 0,
    }


def _configuration(*, formal: bool) -> dict[str, Any]:
    return {
        **_counts(formal=formal), "gamma": GAMMA, "hidden_dim": HIDDEN_DIM,
        "learning_rate": LEARNING_RATE, "initial_log_std": INITIAL_LOG_STD,
        "train_capacity": roster_env.TRAIN_CAPACITY,
        "evaluation_capacities": list(roster_env.EVALUATION_CAPACITIES),
        "base_critic_input": "context_input_plus_fixed_width_critic_state",
        "slow_critic_input": "fixed_width_critic_state_plus_log1p_active_count",
        "member_capacity": "runtime_only_nonserialized",
        "successor_actor_target": "detached_discounted_realized_future_tail_excluding_current",
        "actor_gradient_rule": "equal_global_unit_gradient_directions",
        "checkpoint_selection": "final_only",
        "evaluation_optimizer_steps": 0,
        "residual": "exact_zero_frozen",
    }


def _seeds(replicate: int, *, formal: bool) -> dict[str, int]:
    offset = int(replicate) + (0 if formal else 900_000)
    return {name: value + offset for name, value in SEED_BASES.items()}


def make_model(member_capacity: int) -> ReturnToGoDirectionBalancedFullActorPolicy:
    model = ReturnToGoDirectionBalancedFullActorPolicy(
        roster_env.OBSERVATION_DIM, roster_env.CRITIC_STATE_DIM,
        member_capacity=int(member_capacity), action_dim=roster_env.ACTION_DIM,
        hidden_dim=HIDDEN_DIM,
    )
    with torch.no_grad():
        model.log_std.fill_(INITIAL_LOG_STD)
    return model


def _copy_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: row.detach().cpu().clone() for name, row in model.state_dict().items()}


def _state_shapes(model: torch.nn.Module) -> dict[str, list[int]]:
    return {name: list(row.shape) for name, row in model.state_dict().items()}


def _state_digest(state: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        row = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(row.dtype).encode("ascii"))
        digest.update(np.asarray(row.shape, dtype=np.int64).tobytes())
        digest.update(row.numpy().tobytes())
    return digest.hexdigest()


def _checkpoint_reference(replicate: int, kind: str) -> str:
    return f"checkpoints/replicate_{replicate}_{kind}.pt"


def _save_checkpoint(
    path: Path, *, source_commit: str, formal: bool, replicate: int,
    fast_updates: int, return_to_go_updates: int,
    configuration: dict[str, Any], model: torch.nn.Module,
) -> None:
    torch.save({
        "schema_version": SCHEMA_VERSION, "algorithm": ALGORITHM_ID,
        "source_commit": source_commit, "formal": formal, "replicate": replicate,
        "completed_fast_updates": fast_updates,
        "completed_return_to_go_updates": return_to_go_updates,
        "configuration": configuration, "model_state": model.state_dict(),
    }, path)


def _load_checkpoint(
    path: Path, *, source_commit: str, formal: bool, replicate: int, kind: str,
    configuration: dict[str, Any], member_capacity: int,
) -> tuple[ReturnToGoDirectionBalancedFullActorPolicy, dict[str, Any]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    fast = 0 if kind == "zero" else int(configuration["fast_updates"])
    rtg = 0 if kind == "zero" else int(configuration["return_to_go_updates"])
    expected = {
        "schema_version": SCHEMA_VERSION, "algorithm": ALGORITHM_ID,
        "source_commit": source_commit, "formal": formal, "replicate": replicate,
        "completed_fast_updates": fast, "completed_return_to_go_updates": rtg,
        "configuration": configuration,
    }
    if not isinstance(payload, dict):
        raise ValueError("G32 checkpoint is not a dictionary")
    for name, value in expected.items():
        if payload.get(name) != value:
            raise ValueError(f"G32 checkpoint {name} mismatch")
    state = payload.get("model_state")
    if not isinstance(state, dict):
        raise ValueError("G32 checkpoint model state missing")
    configure_runtime(_seeds(replicate, formal=formal)["model"])
    model = make_model(member_capacity)
    incompatible = model.load_state_dict(state, strict=True)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise ValueError("G32 strict-load key mismatch")
    return model, payload


def _lifecycle_valid(trajectory: Any) -> bool:
    active = trajectory.active_mask
    inactive_zero = (
        torch.count_nonzero(trajectory.actions[~active]) == 0
        and torch.count_nonzero(trajectory.old_log_probs[~active]) == 0
    )
    reset = trajectory.terminal_hidden_reset_mask
    reset_zero = not bool(reset.any()) or torch.count_nonzero(trajectory.hidden_before[reset]) == 0
    schedules = all(
        outcome.roster_sizes == ledger.expected_roster_sizes
        for outcome, ledger in zip(trajectory.outcomes, trajectory.ledgers)
    )
    return bool(inactive_zero and reset_zero and schedules)


def _collect(model: ReturnToGoDirectionBalancedFullActorPolicy, *, episode_ids: tuple[int, ...], seeds: dict[str, int]):
    raw = source.collect_trajectory(
        model, episode_ids=episode_ids, ledger_seed=seeds["ledger"],
        action_seed=seeds["action"], device=torch.device("cpu"),
        profiles=roster_env.TRAIN_PROFILES,
    )
    return attach_credit_baselines(model, raw, device=torch.device("cpu"))


def _train_replicate(
    *, run_root: Path, source_commit: str, formal: bool, replicate: int,
    configuration: dict[str, Any], seeds: dict[str, int],
) -> dict[str, Any]:
    configure_runtime(seeds["model"])
    model = make_model(roster_env.TRAIN_CAPACITY)
    zero_state = _copy_state(model)
    for kind in ("zero",):
        _save_checkpoint(
            run_root / _checkpoint_reference(replicate, kind),
            source_commit=source_commit, formal=formal, replicate=replicate,
            fast_updates=0, return_to_go_updates=0,
            configuration=configuration, model=model,
        )
    replay_max: dict[str, float] = {}
    lifecycle_valid = True
    finite = True
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.credit_baselines.parameters()),
        lr=LEARNING_RATE,
    )
    for update in range(int(configuration["fast_updates"])):
        first = update * int(configuration["num_envs"])
        trajectory = _collect(model, episode_ids=tuple(range(first, first + int(configuration["num_envs"]))), seeds=seeds)
        lifecycle_valid &= _lifecycle_valid(trajectory)
        metrics = optimize_fast_anchor_update(
            model, fast_optimizer, trajectory, device=torch.device("cpu"),
            ppo_passes=int(configuration["ppo_passes"]),
        )
        finite &= bool(metrics["finite_update"])
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                replay_max[name] = max(replay_max.get(name, 0.0), float(value))
    direction_start = {name: row.detach().clone() for name, row in zip(model.full_actor_parameter_names(), model.full_actor_parameters())}
    model.begin_direction_balanced_phase()
    actor_optimizer = torch.optim.Adam(model.full_actor_parameters(), lr=LEARNING_RATE)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=LEARNING_RATE)
    min_dot, max_identity, min_step = float("inf"), 0.0, float("inf")
    max_rtg, max_terminal = 0.0, 0.0
    for update in range(int(configuration["return_to_go_updates"])):
        first = (int(configuration["fast_updates"]) + update) * int(configuration["num_envs"])
        trajectory = _collect(model, episode_ids=tuple(range(first, first + int(configuration["num_envs"]))), seeds=seeds)
        lifecycle_valid &= _lifecycle_valid(trajectory)
        metrics = optimize_return_to_go_direction_balanced_update(
            model, actor_optimizer, critic_optimizer, trajectory,
            device=torch.device("cpu"), ppo_passes=int(configuration["ppo_passes"]), gamma=GAMMA,
        )
        finite &= bool(metrics["finite_update"])
        min_dot = min(min_dot, float(metrics["minimum_direction_immediate_dot"]))
        max_identity = max(max_identity, float(metrics["maximum_direction_composition_identity_error"]))
        min_step = min(min_step, float(metrics["minimum_actor_optimizer_step_increment"]))
        max_rtg = max(max_rtg, float(metrics["maximum_return_to_go_target_absolute_value"]))
        max_terminal = max(max_terminal, float(metrics["terminal_return_to_go_error"]))
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                replay_max[name] = max(replay_max.get(name, 0.0), float(value))
    final_ref = _checkpoint_reference(replicate, "final")
    _save_checkpoint(
        run_root / final_ref, source_commit=source_commit, formal=formal,
        replicate=replicate, fast_updates=int(configuration["fast_updates"]),
        return_to_go_updates=int(configuration["return_to_go_updates"]),
        configuration=configuration, model=model,
    )
    return {
        "replicate": replicate, "seeds": seeds,
        "fast_updates": int(configuration["fast_updates"]),
        "return_to_go_updates": int(configuration["return_to_go_updates"]),
        "finite_updates": finite, "lifecycle_contract_valid": lifecycle_valid,
        "maximum_replay_errors": replay_max,
        "actor_maximum_difference": maximum_state_difference(direction_start, {
            name: row.detach().clone() for name, row in zip(model.full_actor_parameter_names(), model.full_actor_parameters())
        }),
        "parameter_drift": maximum_state_difference(zero_state, _copy_state(model)),
        "residual_output_layer_maximum_absolute_value": model.residual_output_layer_maximum_absolute_value(),
        "minimum_direction_immediate_dot": min_dot,
        "maximum_direction_composition_identity_error": max_identity,
        "minimum_actor_optimizer_step_increment": min_step,
        "maximum_return_to_go_target_absolute_value": max_rtg,
        "maximum_terminal_return_to_go_error": max_terminal,
        "zero_checkpoint": _checkpoint_reference(replicate, "zero"),
        "final_checkpoint": final_ref,
    }


def train(*, run_root: Path, source_commit: str, formal: bool, authorization_token: str | None) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G32 run requires an integrated 40-hex source commit")
    if formal and authorization_token != AUTHORIZATION_TOKEN:
        raise ValueError("formal G32 authorization token mismatch")
    if not formal and authorization_token is not None:
        raise ValueError("nonformal G32 exercise cannot carry formal authority")
    configuration = _configuration(formal=formal)
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "checkpoints").mkdir(exist_ok=True)
    rows = [
        _train_replicate(
            run_root=run_root, source_commit=source_commit, formal=formal,
            replicate=replicate, configuration=configuration,
            seeds=_seeds(replicate, formal=formal),
        ) for replicate in range(int(configuration["replicates"]))
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION, "algorithm": ALGORITHM_ID,
        "stage": "train", "status": "COMPLETE", "formal": formal,
        "source_commit": source_commit, "authorization_token": authorization_token,
        "runtime": _runtime_identity(), "configuration": configuration,
        "source_controls": source.source_controls(), "replicate_results": rows,
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _profile_cell(model: ReturnToGoDirectionBalancedFullActorPolicy, *, name: str, seeds: dict[str, int], eval_episodes: int, deterministic: bool) -> dict[str, Any]:
    profiles = PROFILES[name]
    outcomes = source.evaluate_policy(
        model, episode_ids=range(eval_episodes),
        ledger_seed=seeds["evaluation_ledger"],
        action_seed=seeds["evaluation_action"], device=torch.device("cpu"),
        profiles=profiles, deterministic=deterministic,
    )
    expected_schedules = [
        tuple(
            count
            for count in profiles[index % len(profiles)].segment_counts
            for _ in range(roster_env.HORIZON // 4)
        )
        for index in range(eval_episodes)
    ]
    return {
        "profile": name, "member_capacity": model.member_capacity,
        "deterministic": deterministic,
        "utility": [float(row.utility) for row in outcomes],
        "minimum_step_utility": min(float(row.minimum_step_utility) for row in outcomes),
        "roster_controls_valid": all(
            row.roster_sizes == expected_schedules[index]
            for index, row in enumerate(outcomes)
        ),
    }


def _mapping_diagnostic(
    model: ReturnToGoDirectionBalancedFullActorPolicy, *,
    seeds: dict[str, int], eval_episodes: int,
) -> dict[str, float]:
    state_before = _state_digest(_copy_state(model))
    ledgers = tuple(
        roster_env.make_ledger(
            episode, master_seed=seeds["evaluation_ledger"],
            profile=roster_env.TRAIN_PROFILES[episode % len(roster_env.TRAIN_PROFILES)],
        )
        for episode in range(eval_episodes)
    )
    envs = tuple(roster_env.RuntimeCapacityRosterEnv(row) for row in ledgers)
    hidden = torch.zeros((eval_episodes, 8, HIDDEN_DIM))
    targets, predictions = [[], []], [[], []]
    with torch.no_grad():
        for _time in range(roster_env.HORIZON):
            views = tuple(env.observe() for env in envs)
            source._delete_terminal_hidden(hidden, views)
            output = model.forward_step(
                observations=torch.as_tensor(np.stack([row.observations for row in views])),
                active_mask=torch.as_tensor(np.stack([row.active_mask for row in views])),
                critic_state=torch.as_tensor(np.stack([row.critic_state for row in views])),
                hidden=hidden, deterministic=True,
            )
            actions = output.actions.numpy()
            for index, (env, view) in enumerate(zip(envs, views)):
                active = actions[index, view.active_mask]
                targets[0].append(view.load)
                targets[1].append(view.target_mix)
                predictions[0].append(float(((active[:, 0] + 1.0) / 2.0).mean()))
                predictions[1].append(float(((active[:, 1] + 1.0) / 2.0).mean()))
                env.step(actions[index])
            hidden = output.next_hidden
    arrays = [np.asarray(row, dtype=np.float64) for row in (*targets, *predictions)]
    def correlation(left: np.ndarray, right: np.ndarray) -> float:
        if float(left.std()) == 0.0 or float(right.std()) == 0.0:
            return 0.0
        return float(np.corrcoef(left, right)[0, 1])
    return {
        "effort_correlation": correlation(arrays[0], arrays[2]),
        "mix_correlation": correlation(arrays[1], arrays[3]),
        "effort_mae": float(np.abs(arrays[0] - arrays[2]).mean()),
        "mix_mae": float(np.abs(arrays[1] - arrays[3]).mean()),
        "state_before": state_before,
        "state_after": _state_digest(_copy_state(model)),
        "optimizer_steps": 0,
    }


def _padding_diagnostic(
    model_state: Mapping[str, torch.Tensor], *, seeds: dict[str, int],
    eval_episodes: int = 1,
) -> dict[str, Any]:
    models = {}
    state_before = {}
    for capacity in (8, 12):
        configure_runtime(seeds["model"])
        model = make_model(capacity)
        model.load_state_dict(model_state, strict=True)
        models[capacity] = model
        state_before[capacity] = _state_digest(_copy_state(model))
    profiles = {8: roster_env.PADDING_CAPACITY_8, 12: roster_env.PADDING_CAPACITY_12}
    envs = {
        capacity: tuple(
            roster_env.RuntimeCapacityRosterEnv(
                roster_env.make_ledger(
                    episode, master_seed=seeds["evaluation_ledger"], profile=profile
                )
            )
            for episode in range(eval_episodes)
        )
        for capacity, profile in profiles.items()
    }
    hidden = {
        capacity: torch.zeros((eval_episodes, capacity, HIDDEN_DIM))
        for capacity in (8, 12)
    }
    maxima = {name: 0.0 for name in ("observation", "value", "action", "reward", "hidden")}
    lifecycle_equal = True
    inactive_zero = True
    with torch.no_grad():
        for _time in range(roster_env.HORIZON):
            outputs = {}
            views = {}
            for capacity in (8, 12):
                view_rows = tuple(env.observe() for env in envs[capacity])
                views[capacity] = view_rows
                source._delete_terminal_hidden(hidden[capacity], view_rows)
                output = models[capacity].forward_step(
                    observations=torch.as_tensor(np.stack([row.observations for row in view_rows])),
                    active_mask=torch.as_tensor(np.stack([row.active_mask for row in view_rows])),
                    critic_state=torch.as_tensor(np.stack([row.critic_state for row in view_rows])),
                    hidden=hidden[capacity], deterministic=True,
                )
                outputs[capacity] = output
            common = np.stack([row.active_mask for row in views[8]])
            observations8 = np.stack([row.observations for row in views[8]])
            observations12 = np.stack([row.observations[:8] for row in views[12]])
            maxima["observation"] = max(maxima["observation"], float(np.max(np.abs(observations8[common] - observations12[common]), initial=0.0)))
            maxima["value"] = max(maxima["value"], float(torch.max(torch.abs(outputs[8].value - outputs[12].value))))
            maxima["action"] = max(maxima["action"], float(torch.max(torch.abs(outputs[8].actions - outputs[12].actions[:, :8]))))
            maxima["hidden"] = max(maxima["hidden"], float(torch.max(torch.abs(outputs[8].next_hidden - outputs[12].next_hidden[:, :8]))))
            inactive_zero &= bool(torch.count_nonzero(outputs[12].actions[:, 8:]) == 0 and torch.count_nonzero(outputs[12].token_log_probs[:, 8:]) == 0 and torch.count_nonzero(outputs[12].next_hidden[:, 8:]) == 0)
            lifecycle_equal &= all(
                left.membership_change == right.membership_change
                for left, right in zip(views[8], views[12])
            )
            rewards = {}
            for capacity in (8, 12):
                rewards[capacity] = np.asarray([
                    env.step(outputs[capacity].actions[index].numpy())[0]
                    for index, env in enumerate(envs[capacity])
                ])
                hidden[capacity] = outputs[capacity].next_hidden
            maxima["reward"] = max(maxima["reward"], float(np.max(np.abs(rewards[8] - rewards[12]))))
    return {
        **{f"maximum_{name}_mismatch": value for name, value in maxima.items()},
        "lifecycle_equal": lifecycle_equal,
        "inactive_padding_zero": inactive_zero,
        "state_identity": all(
            state_before[capacity] == _state_digest(_copy_state(models[capacity]))
            for capacity in (8, 12)
        ),
        "optimizer_steps": 0,
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    if training.get("algorithm") != ALGORITHM_ID or training.get("status") != "COMPLETE":
        raise ValueError("G32 evaluation requires complete training")
    formal = bool(training["formal"])
    configuration = _configuration(formal=formal)
    if training.get("configuration") != configuration:
        raise ValueError("G32 evaluation configuration mismatch")
    cells, padding_rows, shape_rows, mapping_rows = [], [], [], []
    for row in training["replicate_results"]:
        replicate, seeds = int(row["replicate"]), row["seeds"]
        for kind in ("zero", "final"):
            for profile_name, profiles in PROFILES.items():
                capacity = profiles[0].member_capacity
                model, payload = _load_checkpoint(
                    run_root / row[f"{kind}_checkpoint"],
                    source_commit=training["source_commit"], formal=formal,
                    replicate=replicate, kind=kind, configuration=configuration,
                    member_capacity=capacity,
                )
                before = _state_digest(_copy_state(model))
                cell = _profile_cell(
                    model, name=profile_name, seeds=seeds,
                    eval_episodes=int(configuration["eval_episodes"]), deterministic=True,
                )
                after = _state_digest(_copy_state(model))
                cells.append({"replicate": replicate, "checkpoint": kind, **cell, "optimizer_steps": 0, "state_before": before, "state_after": after})
                if kind == "final" and profile_name in ("small_capacity_6", "large_capacity_12"):
                    before = _state_digest(_copy_state(model))
                    stochastic = _profile_cell(model, name=profile_name, seeds=seeds, eval_episodes=int(configuration["eval_episodes"]), deterministic=False)
                    cells.append({"replicate": replicate, "checkpoint": kind, **stochastic, "optimizer_steps": 0, "state_before": before, "state_after": _state_digest(_copy_state(model))})
                if kind == "final":
                    shape_rows.append({"replicate": replicate, "member_capacity": capacity, "state_shapes": _state_shapes(model), "strict_load": True})
            if kind == "final":
                payload = torch.load(run_root / row["final_checkpoint"], map_location="cpu", weights_only=False)
                padding_rows.append({"replicate": replicate, **_padding_diagnostic(payload["model_state"], seeds=seeds, eval_episodes=int(configuration["eval_episodes"]))})
                model, _payload = _load_checkpoint(
                    run_root / row["final_checkpoint"],
                    source_commit=training["source_commit"], formal=formal,
                    replicate=replicate, kind="final", configuration=configuration,
                    member_capacity=8,
                )
                mapping_rows.append({
                    "replicate": replicate,
                    **_mapping_diagnostic(
                        model, seeds=seeds,
                        eval_episodes=int(configuration["eval_episodes"]),
                    ),
                })
    manifest = {
        "schema_version": SCHEMA_VERSION, "algorithm": ALGORITHM_ID,
        "stage": "evaluate", "status": "COMPLETE", "formal": formal,
        "source_commit": training["source_commit"], "runtime": _runtime_identity(),
        "configuration": configuration, "source_controls": source.source_controls(),
        "cells": cells, "padding_diagnostics": padding_rows,
        "state_shape_diagnostics": shape_rows,
        "mapping_diagnostics": mapping_rows,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def select_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["padding_capacity_invariant"]):
        return NO_PADDING_BRANCH
    if not (
        float(metrics["capacity_8_utility_ci95"][0]) >= UTILITY_FLOOR
        and float(metrics["capacity_8_gain_ci95"][0]) > GAIN_FLOOR
        and bool(metrics["mapping_lifecycle_gate"])
    ):
        return NO_TRAIN_BRANCH
    if not (
        float(metrics["capacity_6_utility_ci95"][0]) >= UTILITY_FLOOR
        and float(metrics["capacity_12_utility_ci95"][0]) >= UTILITY_FLOOR
        and float(metrics["heldout_gain_ci95"][0]) > GAIN_FLOOR
    ):
        return NO_CHURN_BRANCH
    if (
        float(metrics["minimum_heldout_replicate"]) < MINIMUM_HELDOUT_REPLICATE_FLOOR
        or float(metrics["heldout_stochastic_mean"]) < HELDOUT_STOCHASTIC_FLOOR
    ):
        return UNSTABLE_BRANCH
    return USABLE_BRANCH


def _padding_capacity_invariant(evaluation: Mapping[str, Any]) -> bool:
    """Return the behavioral padding predicate after structural validation."""

    return all(
        all(
            float(row[f"maximum_{name}_mismatch"]) == 0.0
            for name in PADDING_MISMATCH_FIELDS
        )
        and row["lifecycle_equal"] is True
        and row["inactive_padding_zero"] is True
        for row in evaluation["padding_diagnostics"]
    )


def _artifact_errors(run_root: Path, training: dict[str, Any], evaluation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    formal = bool(training.get("formal"))
    configuration = _configuration(formal=formal)
    commit = training.get("source_commit")
    if re.fullmatch(r"[0-9a-f]{40}", str(commit)) is None:
        errors.append("source commit invalid")
    for artifact, stage in ((training, "train"), (evaluation, "evaluate")):
        if artifact.get("schema_version") != SCHEMA_VERSION or artifact.get("algorithm") != ALGORITHM_ID or artifact.get("stage") != stage or artifact.get("status") != "COMPLETE":
            errors.append(f"{stage} identity mismatch")
        if artifact.get("formal") is not formal or artifact.get("source_commit") != commit or artifact.get("configuration") != configuration:
            errors.append(f"{stage} configuration mismatch")
        runtime = artifact.get("runtime", {})
        if runtime.get("backend") != "cpu" or runtime.get("torch_threads") != 1 or runtime.get("torch") != str(torch.__version__):
            errors.append(f"{stage} runtime mismatch")
        if artifact.get("source_controls") != source.source_controls():
            errors.append(f"{stage} source controls mismatch")
    if formal and training.get("authorization_token") != AUTHORIZATION_TOKEN:
        errors.append("formal authorization token mismatch")
    if not formal and training.get("authorization_token") is not None:
        errors.append("nonformal artifact carries formal authority")
    rows = training.get("replicate_results", [])
    if len(rows) != int(configuration["replicates"]):
        errors.append("training replicate inventory mismatch")
    for index, row in enumerate(rows):
        try:
            if row["replicate"] != index or row["seeds"] != _seeds(index, formal=formal):
                raise ValueError("training seed/replicate mismatch")
            values = row["maximum_replay_errors"]
            if not values or max(float(value) for value in values.values()) > REPLAY_TOLERANCE:
                raise ValueError("training replay mismatch")
            if not row["finite_updates"] or not row["lifecycle_contract_valid"] or row["parameter_drift"] <= 0 or row["actor_maximum_difference"] <= 0 or row["residual_output_layer_maximum_absolute_value"] != 0 or row["minimum_actor_optimizer_step_increment"] != 1 or row["maximum_return_to_go_target_absolute_value"] <= 0 or row["maximum_terminal_return_to_go_error"] != 0:
                raise ValueError("training invariant mismatch")
            for kind in ("zero", "final"):
                _load_checkpoint(
                    run_root / row[f"{kind}_checkpoint"], source_commit=str(commit),
                    formal=formal, replicate=index, kind=kind,
                    configuration=configuration, member_capacity=8,
                )
        except (KeyError, TypeError, ValueError, OSError) as error:
            errors.append(str(error))
    expected_cells = int(configuration["replicates"]) * 10
    cells = evaluation.get("cells", [])
    if len(cells) != expected_cells:
        errors.append("evaluation cell inventory mismatch")
    keys = set()
    for cell in cells:
        try:
            key = (int(cell["replicate"]), str(cell["checkpoint"]), str(cell["profile"]), bool(cell["deterministic"]))
            if key in keys:
                raise ValueError("evaluation cell duplicate")
            keys.add(key)
            if cell["optimizer_steps"] != 0 or cell["state_before"] != cell["state_after"]:
                raise ValueError("evaluation zero-step state identity mismatch")
            if cell.get("roster_controls_valid") is not True:
                raise ValueError("evaluation roster controls mismatch")
            utilities = np.asarray(cell["utility"], dtype=np.float64)
            if utilities.shape != (int(configuration["eval_episodes"]),) or not np.isfinite(utilities).all() or np.any((utilities < 0) | (utilities > 1)):
                raise ValueError("evaluation utility support mismatch")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
    shape_rows = evaluation.get("state_shape_diagnostics", [])
    for replicate in range(int(configuration["replicates"])):
        selected = [row for row in shape_rows if row.get("replicate") == replicate]
        capacities = {row.get("member_capacity") for row in selected}
        shapes = [row.get("state_shapes") for row in selected]
        if capacities != {6, 8, 12} or len(shapes) != 4 or any(row is not True for row in [item.get("strict_load") for item in selected]) or any(shape != shapes[0] for shape in shapes[1:]):
            errors.append("state shape or strict-load mismatch")
    padding = evaluation.get("padding_diagnostics", [])
    if not isinstance(padding, list) or len(padding) != int(configuration["replicates"]):
        errors.append("padding diagnostic inventory mismatch")
    else:
        observed_padding_replicates: set[int] = set()
        for row in padding:
            try:
                replicate = row["replicate"]
                if (
                    not isinstance(replicate, int)
                    or isinstance(replicate, bool)
                    or replicate < 0
                    or replicate >= int(configuration["replicates"])
                    or replicate in observed_padding_replicates
                ):
                    raise ValueError("padding diagnostic replicate mismatch")
                observed_padding_replicates.add(replicate)
                mismatch = np.asarray(
                    [
                        row[f"maximum_{name}_mismatch"]
                        for name in PADDING_MISMATCH_FIELDS
                    ],
                    dtype=np.float64,
                )
                if (
                    mismatch.shape != (len(PADDING_MISMATCH_FIELDS),)
                    or not np.isfinite(mismatch).all()
                    or np.any(mismatch < 0.0)
                    or not isinstance(row["lifecycle_equal"], bool)
                    or not isinstance(row["inactive_padding_zero"], bool)
                ):
                    raise ValueError("padding diagnostic malformed")
                if row.get("state_identity") is not True or row.get("optimizer_steps") != 0:
                    raise ValueError("padding zero-step state identity mismatch")
            except (KeyError, TypeError, ValueError) as error:
                errors.append(str(error))
        if observed_padding_replicates != set(
            range(int(configuration["replicates"]))
        ):
            errors.append("padding diagnostic replicate inventory mismatch")
    mapping = evaluation.get("mapping_diagnostics", [])
    if len(mapping) != int(configuration["replicates"]):
        errors.append("mapping diagnostic inventory mismatch")
    else:
        for index, row in enumerate(mapping):
            values = np.asarray([
                row.get("effort_correlation"), row.get("mix_correlation"),
                row.get("effort_mae"), row.get("mix_mae"),
            ], dtype=np.float64)
            if row.get("replicate") != index or not np.isfinite(values).all() or row.get("state_before") != row.get("state_after") or row.get("optimizer_steps") != 0:
                errors.append("mapping diagnostic invalid")
    return errors


def _cells(evaluation: dict[str, Any], *, profile: str, checkpoint: str, deterministic: bool) -> np.ndarray:
    rows = sorted((row for row in evaluation["cells"] if row["profile"] == profile and row["checkpoint"] == checkpoint and row["deterministic"] is deterministic), key=lambda row: row["replicate"])
    return np.asarray([row["utility"] for row in rows], dtype=np.float64)


def analyze(*, run_root: Path, require_formal: bool = False) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal analysis requires formal G32 artifacts")
    errors = _artifact_errors(run_root, training, evaluation)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if formal and not errors:
        repetitions = FORMAL_BOOTSTRAP_REPETITIONS
        cap8 = _cells(evaluation, profile="train_capacity_8", checkpoint="final", deterministic=True)
        cap8_zero = _cells(evaluation, profile="train_capacity_8", checkpoint="zero", deterministic=True)
        cap6 = _cells(evaluation, profile="small_capacity_6", checkpoint="final", deterministic=True)
        cap6_zero = _cells(evaluation, profile="small_capacity_6", checkpoint="zero", deterministic=True)
        cap12 = _cells(evaluation, profile="large_capacity_12", checkpoint="final", deterministic=True)
        cap12_zero = _cells(evaluation, profile="large_capacity_12", checkpoint="zero", deterministic=True)
        heldout = np.concatenate((cap6, cap12), axis=1)
        heldout_zero = np.concatenate((cap6_zero, cap12_zero), axis=1)
        stochastic = np.concatenate((
            _cells(evaluation, profile="small_capacity_6", checkpoint="final", deterministic=False),
            _cells(evaluation, profile="large_capacity_12", checkpoint="final", deterministic=False),
        ), axis=1)
        mapping = evaluation["mapping_diagnostics"]
        mapping_lifecycle_gate = (
            min(float(row["effort_correlation"]) for row in mapping) >= CORRELATION_FLOOR
            and min(float(row["mix_correlation"]) for row in mapping) >= CORRELATION_FLOOR
            and max(float(row["effort_mae"]) for row in mapping) <= MAE_CEILING
            and max(float(row["mix_mae"]) for row in mapping) <= MAE_CEILING
            and all(row["lifecycle_contract_valid"] for row in training["replicate_results"])
        )
        metrics.update({
            "padding_capacity_invariant": _padding_capacity_invariant(
                evaluation
            ),
            "mapping_lifecycle_gate": mapping_lifecycle_gate,
            "capacity_8_utility_ci95": g17_runner._hierarchical_ci(cap8, seed=BOOTSTRAP_SEED, repetitions=repetitions),
            "capacity_8_gain_ci95": g17_runner._hierarchical_ci(cap8 - cap8_zero, seed=BOOTSTRAP_SEED + 1, repetitions=repetitions),
            "capacity_6_utility_ci95": g17_runner._hierarchical_ci(cap6, seed=BOOTSTRAP_SEED + 2, repetitions=repetitions),
            "capacity_12_utility_ci95": g17_runner._hierarchical_ci(cap12, seed=BOOTSTRAP_SEED + 3, repetitions=repetitions),
            "heldout_gain_ci95": g17_runner._hierarchical_ci(heldout - heldout_zero, seed=BOOTSTRAP_SEED + 4, repetitions=repetitions),
            "minimum_heldout_replicate": float(heldout.mean(axis=1).min()),
            "heldout_stochastic_mean": float(stochastic.mean()),
        })
    branch = select_result_branch(metrics) if formal and not errors else (NONFORMAL_BRANCH if not errors else INVALID_BRANCH)
    result = {
        "schema_version": SCHEMA_VERSION, "algorithm": ALGORITHM_ID,
        "stage": "analyze", "status": "COMPLETE" if not errors else "INVALID",
        "formal": formal, "source_commit": training.get("source_commit"),
        "operational_valid": not errors, "operational_errors": errors,
        "branch": branch, "metrics": metrics,
        "thresholds": {
            "utility_floor": UTILITY_FLOOR, "gain_floor_strict": GAIN_FLOOR,
            "minimum_heldout_replicate_floor": MINIMUM_HELDOUT_REPLICATE_FLOOR,
            "heldout_stochastic_floor": HELDOUT_STOCHASTIC_FLOOR,
            "replay_tolerance": REPLAY_TOLERANCE,
            "correlation_floor": CORRELATION_FLOOR,
            "mae_ceiling": MAE_CEILING,
        },
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(*, run_root: Path, source_commit: str = "0" * 40) -> dict[str, Any]:
    train(run_root=run_root, source_commit=source_commit, formal=False, authorization_token=None)
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit", default="")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--require-formal", action="store_true")
    args = parser.parse_args()
    if args.mode == "train":
        value = train(run_root=args.run_root, source_commit=args.source_commit, formal=args.formal, authorization_token=args.authorization_token)
    elif args.mode == "evaluate":
        value = evaluate(run_root=args.run_root)
    elif args.mode == "analyze":
        value = analyze(run_root=args.run_root, require_formal=args.require_formal)
    else:
        value = exercise(run_root=args.run_root, source_commit=args.source_commit or "0" * 40)
    print(json.dumps({"algorithm": ALGORITHM_ID, "stage": value["stage"], "status": value["status"], "branch": value.get("branch")}, sort_keys=True))


if __name__ == "__main__":
    main()
