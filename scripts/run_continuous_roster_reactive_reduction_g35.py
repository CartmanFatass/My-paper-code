"""Train, evaluate, and analyze the frozen matched-arm G35 contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import continuous_roster_reactive_reduction_g35 as source
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    optimize_fast_anchor_update,
)
from ha_ctse_process.return_to_go_direction_balanced_full_actor_g31 import (
    optimize_return_to_go_direction_balanced_update,
)
from scripts import run_continuous_roster_random_process_g34 as g34_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "AUTHORIZE_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_FORMAL_CPU_V1"
)

INVALID_BRANCH = "INVALID_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35"
SOURCE_FAILURE_BRANCH = "SOURCE_OR_COMMON_ACCESS_FAILURE_G35"
CS_SUFFICIENT_BRANCH = "CURRENT_STATE_REDUCTION_SUFFICIENT_G35"
REC_ADVANTAGE_BRANCH = "RECURRENT_STATE_INDUCTIVE_BIAS_ADVANTAGE_G35"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_REACTIVE_REDUCTION_G35"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_EXERCISE_COMPLETE"
)
NON_EXECUTABLE_BRANCH = "NON_EXECUTABLE_EVIDENCE_DESIGN"

CONSTRUCTIVE_RANDOM = "CONSTRUCTIVE_RANDOM"
ZERO_RANDOM_DET = "ZERO_RANDOM_DET"
FINAL_FIXED_DET = "FINAL_FIXED_DET"
FINAL_FIXED_STOCH = "FINAL_FIXED_STOCH"
FINAL_RANDOM_DET = "FINAL_RANDOM_DET"
FINAL_RANDOM_STOCH = "FINAL_RANDOM_STOCH"
MODEL_CELLS = (
    ZERO_RANDOM_DET,
    FINAL_FIXED_DET,
    FINAL_FIXED_STOCH,
    FINAL_RANDOM_DET,
    FINAL_RANDOM_STOCH,
)

GAMMA = 0.99
LEARNING_RATE = 1e-3
REPLAY_TOLERANCE = 1e-6
UTILITY_FLOOR = 0.90
EVENT_FLOOR = 0.85
SEGMENT_FLOOR = 0.85
PROCESS_MARGIN = -0.05
STOCHASTIC_FLOOR = 0.80
MINIMUM_REPLICATE_FLOOR = 0.85
RECURRENCE_MARGIN = 0.05
CONSTRUCTIVE_TOLERANCE = 2e-7
FORMAL_WALL_CLOCK_CAP_SECONDS = 28_800.0

FORMAL_REPLICATES = 3
FORMAL_FAST_UPDATES = 100
FORMAL_RETURN_TO_GO_UPDATES = 100
FORMAL_NUM_ENVS = 8
FORMAL_PPO_PASSES = 2
FORMAL_EVAL_EPISODES = 128
FORMAL_BOOTSTRAP_REPETITIONS = 10_000

EXERCISE_REPLICATES = 1
EXERCISE_FAST_UPDATES = 10
EXERCISE_RETURN_TO_GO_UPDATES = 10
EXERCISE_NUM_ENVS = 8
EXERCISE_PPO_PASSES = 2
EXERCISE_EVAL_EPISODES = 8
EXERCISE_BOOTSTRAP_REPETITIONS = 250


def configure_runtime(seed: int) -> None:
    torch.set_num_threads(1)
    torch.manual_seed(int(seed))


def _runtime_identity() -> dict[str, object]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _counts(*, formal: bool) -> dict[str, int]:
    if formal:
        return {
            "replicates": FORMAL_REPLICATES,
            "fast_updates": FORMAL_FAST_UPDATES,
            "return_to_go_updates": FORMAL_RETURN_TO_GO_UPDATES,
            "num_envs": FORMAL_NUM_ENVS,
            "ppo_passes": FORMAL_PPO_PASSES,
            "evaluation_episodes_per_cell": FORMAL_EVAL_EPISODES,
            "bootstrap_resamples": FORMAL_BOOTSTRAP_REPETITIONS,
        }
    return {
        "replicates": EXERCISE_REPLICATES,
        "fast_updates": EXERCISE_FAST_UPDATES,
        "return_to_go_updates": EXERCISE_RETURN_TO_GO_UPDATES,
        "num_envs": EXERCISE_NUM_ENVS,
        "ppo_passes": EXERCISE_PPO_PASSES,
        "evaluation_episodes_per_cell": EXERCISE_EVAL_EPISODES,
        "bootstrap_resamples": EXERCISE_BOOTSTRAP_REPETITIONS,
    }


def _configuration(*, formal: bool) -> dict[str, object]:
    counts = _counts(formal=formal)
    replicates = int(counts["replicates"])
    fast_updates = int(counts["fast_updates"])
    rtg_updates = int(counts["return_to_go_updates"])
    num_envs = int(counts["num_envs"])
    ppo_passes = int(counts["ppo_passes"])
    eval_episodes = int(counts["evaluation_episodes_per_cell"])
    cells_per_replicate = 33
    train_transitions = (
        len(source.ARMS)
        * replicates
        * (fast_updates + rtg_updates)
        * num_envs
        * g32.HORIZON
    )
    evaluation_transitions = (
        replicates * cells_per_replicate * eval_episodes * g32.HORIZON
    )
    optimizer_steps = (
        len(source.ARMS)
        * replicates
        * (fast_updates * ppo_passes + 2 * rtg_updates * ppo_passes)
    )
    return {
        **counts,
        "arms": list(source.ARMS),
        "observation_dim": g32.OBSERVATION_DIM,
        "critic_state_dim": g32.CRITIC_STATE_DIM,
        "action_dim": g32.ACTION_DIM,
        "actor_width": source.HIDDEN_DIM,
        "training_capacity": g32.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "gamma": GAMMA,
        "learning_rate": LEARNING_RATE,
        "initial_log_std": source.INITIAL_LOG_STD,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)",
        "minibatches": "none",
        "checkpoint_selection": "final_only",
        "episode_exclusions": "none",
        "cells_per_replicate": cells_per_replicate,
        "total_cells": replicates * cells_per_replicate,
        "training_transitions": train_transitions,
        "evaluation_transitions": evaluation_transitions,
        "total_real_transitions": train_transitions + evaluation_transitions,
        "optimizer_steps": optimizer_steps,
        "evaluation_optimizer_steps": 0,
        "replay_tolerance": REPLAY_TOLERANCE,
        "initial_equality_tolerance": source.INITIAL_EQUALITY_TOLERANCE,
        "initial_gradient_live_tolerance": source.GRADIENT_LIVE_TOLERANCE,
        "paired_collection_before_update": True,
        "historical_checkpoint_loading": "forbidden",
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
    }


def _copy_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: row.detach().cpu().clone()
        for name, row in model.state_dict().items()
    }


def _state_digest(state_or_model: Mapping[str, torch.Tensor] | torch.nn.Module) -> str:
    state = (
        state_or_model.state_dict()
        if isinstance(state_or_model, torch.nn.Module)
        else state_or_model
    )
    digest = hashlib.sha256()
    for name in sorted(state):
        row = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(row.dtype).encode("ascii"))
        digest.update(np.asarray(row.shape, dtype=np.int64).tobytes())
        digest.update(row.numpy().tobytes())
    return digest.hexdigest()


def _checkpoint_reference(replicate: int, arm: str, kind: str) -> str:
    return f"checkpoints/replicate_{replicate}_{arm.lower()}_{kind}.pt"


def _save_checkpoint(
    path: Path,
    *,
    source_commit: str,
    formal: bool,
    replicate: int,
    arm: str,
    kind: str,
    configuration: Mapping[str, object],
    seeds: Mapping[str, int],
    model: source.G35MatchedStateCarryPolicy,
) -> None:
    fast = 0 if kind == "zero" else int(configuration["fast_updates"])
    rtg = 0 if kind == "zero" else int(configuration["return_to_go_updates"])
    torch.save(
        {
            "schema_version": SCHEMA_VERSION,
            "algorithm": ALGORITHM_ID,
            "source_id": source.SOURCE_ID,
            "source_commit": source_commit,
            "formal": formal,
            "replicate": replicate,
            "arm": arm,
            "carry_mode": arm,
            "kind": kind,
            "completed_fast_updates": fast,
            "completed_return_to_go_updates": rtg,
            "configuration": dict(configuration),
            "seeds": dict(seeds),
            "model_state": model.state_dict(),
        },
        path,
    )


def _load_checkpoint(
    path: Path,
    *,
    source_commit: str,
    formal: bool,
    replicate: int,
    arm: str,
    kind: str,
    configuration: Mapping[str, object],
    seeds: Mapping[str, int],
    member_capacity: int,
) -> tuple[source.G35MatchedStateCarryPolicy, dict[str, Any]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError("G35 checkpoint is not a dictionary")
    expected = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": source_commit,
        "formal": formal,
        "replicate": replicate,
        "arm": arm,
        "carry_mode": arm,
        "kind": kind,
        "completed_fast_updates": (
            0 if kind == "zero" else int(configuration["fast_updates"])
        ),
        "completed_return_to_go_updates": (
            0
            if kind == "zero"
            else int(configuration["return_to_go_updates"])
        ),
        "configuration": dict(configuration),
        "seeds": dict(seeds),
    }
    for name, value in expected.items():
        if payload.get(name) != value:
            raise ValueError(f"G35 checkpoint {name} mismatch")
    state = payload.get("model_state")
    if not isinstance(state, dict):
        raise ValueError("G35 checkpoint model state missing")
    configure_runtime(int(seeds["model"]))
    model = source.make_model(
        member_capacity,
        carry_mode=arm,
        initialization_seed=int(seeds["model"]),
    )
    incompatible = model.load_state_dict(state, strict=True)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise ValueError("G35 checkpoint strict-load mismatch")
    return model, payload


def _lifecycle_valid(trajectory: Any, *, arm: str) -> bool:
    active = trajectory.active_mask
    reset = trajectory.terminal_hidden_reset_mask
    valid = (
        torch.count_nonzero(trajectory.actions[~active]) == 0
        and torch.count_nonzero(trajectory.old_log_probs[~active]) == 0
        and (
            not bool(reset.any())
            or torch.count_nonzero(trajectory.hidden_before[reset]) == 0
        )
        and all(
            outcome.roster_sizes == ledger.expected_roster_sizes
            for outcome, ledger in zip(trajectory.outcomes, trajectory.ledgers)
        )
    )
    if arm == source.CS_ARM:
        valid = valid and torch.count_nonzero(trajectory.hidden_before) == 0
        valid = valid and torch.count_nonzero(trajectory.hidden_after) == 0
    return bool(valid)


def _collect(
    model: source.G35MatchedStateCarryPolicy,
    *,
    episode_ids: tuple[int, ...],
    ledger_seed: int,
    action_seed: int,
) -> Any:
    raw = g32.collect_trajectory(
        model,
        episode_ids=episode_ids,
        ledger_seed=int(ledger_seed),
        action_seed=int(action_seed),
        device=torch.device("cpu"),
        profiles=g32.TRAIN_PROFILES,
    )
    return attach_credit_baselines(model, raw, device=torch.device("cpu"))


def _max_replay_error(metrics: Mapping[str, float]) -> float:
    values = [
        float(value)
        for name, value in metrics.items()
        if name.endswith("_error") or name.endswith("_max_abs")
    ]
    return max(values, default=0.0)


def _validate_formal_preflight(
    preflight_root: Path | None, *, source_commit: str
) -> None:
    if preflight_root is None:
        raise ValueError("formal G35 execution requires a bounded preflight root")
    result = _read_json(preflight_root / "analysis_result.json")
    if (
        result.get("formal") is not False
        or result.get("source_commit") != source_commit
        or result.get("operational_valid") is not True
        or result.get("branch") != NONFORMAL_BRANCH
        or result.get("formal_projection_executable") is not True
        or float(result.get("formal_projection_seconds", float("inf")))
        > FORMAL_WALL_CLOCK_CAP_SECONDS
    ):
        raise ValueError("G35 formal preflight is not executable for this source")


def _train_replicate(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    replicate: int,
    configuration: Mapping[str, object],
) -> dict[str, Any]:
    seeds = source.seed_block(replicate, formal=formal)
    configure_runtime(seeds["model"])
    models = source.make_paired_models(
        g32.TRAIN_CAPACITY, initialization_seed=seeds["model"]
    )
    zero_digests = {arm: _state_digest(model) for arm, model in models.items()}
    if len(set(zero_digests.values())) != 1:
        raise RuntimeError("G35 initial arm states diverged")
    for arm, model in models.items():
        _save_checkpoint(
            run_root / _checkpoint_reference(replicate, arm, "zero"),
            source_commit=source_commit,
            formal=formal,
            replicate=replicate,
            arm=arm,
            kind="zero",
            configuration=configuration,
            seeds=seeds,
            model=model,
        )

    optimizers = {
        arm: torch.optim.Adam(
            model.fast_actor_parameters()
            + tuple(model.credit_baselines.parameters()),
            lr=LEARNING_RATE,
        )
        for arm, model in models.items()
    }
    maximum_replay = {arm: 0.0 for arm in source.ARMS}
    lifecycle_valid = {arm: True for arm in source.ARMS}
    finite = {arm: True for arm in source.ARMS}
    initial_equality: dict[str, float] | None = None
    gradient_audits: dict[str, dict[str, object]] = {}
    fast_steps = {arm: 0 for arm in source.ARMS}

    for update in range(int(configuration["fast_updates"])):
        first = update * int(configuration["num_envs"])
        ids = tuple(range(first, first + int(configuration["num_envs"])))
        if update == 0:
            ledger_seed = seeds["initial_gradient_probe"]
            action_seed = seeds["initial_gradient_probe"]
        else:
            ledger_seed = seeds["training_ledger"]
            action_seed = seeds["training_action"]
        trajectories = {
            arm: _collect(
                model,
                episode_ids=ids,
                ledger_seed=ledger_seed,
                action_seed=action_seed,
            )
            for arm, model in models.items()
        }
        if update == 0:
            rec_row, cs_row = (
                trajectories[source.REC_ARM],
                trajectories[source.CS_ARM],
            )
            initial_equality = {
                "pre_tanh": float(
                    (rec_row.pre_tanh_actions[0] - cs_row.pre_tanh_actions[0])
                    .abs()
                    .max()
                ),
                "actions": float(
                    (rec_row.actions[0] - cs_row.actions[0]).abs().max()
                ),
                "token_log_prob": float(
                    (rec_row.old_log_probs[0] - cs_row.old_log_probs[0])
                    .abs()
                    .max()
                ),
                "value": float(
                    (rec_row.old_values[0] - cs_row.old_values[0]).abs().max()
                ),
            }
            if max(initial_equality.values()) > source.INITIAL_EQUALITY_TOLERANCE:
                raise RuntimeError("G35 forced initial equality failed")
            gradient_audits = {
                arm: source.g35_initial_gradient_audit(
                    model, trajectories[arm], gamma=GAMMA
                )
                for arm, model in models.items()
            }
            if not all(bool(row["passed"]) for row in gradient_audits.values()):
                raise RuntimeError("G35 initial gradient audit failed")
        for arm in source.ARMS:
            lifecycle_valid[arm] &= _lifecycle_valid(
                trajectories[arm], arm=arm
            )
        for arm in source.ARMS:
            metrics = optimize_fast_anchor_update(
                models[arm],
                optimizers[arm],
                trajectories[arm],
                device=torch.device("cpu"),
                ppo_passes=int(configuration["ppo_passes"]),
            )
            finite[arm] &= bool(metrics["finite_update"])
            maximum_replay[arm] = max(
                maximum_replay[arm], _max_replay_error(metrics)
            )
            fast_steps[arm] += int(metrics["optimizer_steps"])

    actor_optimizers: dict[str, torch.optim.Adam] = {}
    critic_optimizers: dict[str, torch.optim.Adam] = {}
    for arm, model in models.items():
        model.begin_direction_balanced_phase()
        actor_optimizers[arm] = torch.optim.Adam(
            model.full_actor_parameters(), lr=LEARNING_RATE
        )
        critic_optimizers[arm] = torch.optim.Adam(
            model.critic_parameters(), lr=LEARNING_RATE
        )
    actor_steps = {arm: 0 for arm in source.ARMS}
    critic_steps = {arm: 0 for arm in source.ARMS}

    for update in range(int(configuration["return_to_go_updates"])):
        first = (
            int(configuration["fast_updates"]) + update
        ) * int(configuration["num_envs"])
        ids = tuple(range(first, first + int(configuration["num_envs"])))
        trajectories = {
            arm: _collect(
                model,
                episode_ids=ids,
                ledger_seed=seeds["training_ledger"],
                action_seed=seeds["training_action"],
            )
            for arm, model in models.items()
        }
        for arm in source.ARMS:
            lifecycle_valid[arm] &= _lifecycle_valid(
                trajectories[arm], arm=arm
            )
        for arm in source.ARMS:
            metrics = optimize_return_to_go_direction_balanced_update(
                models[arm],
                actor_optimizers[arm],
                critic_optimizers[arm],
                trajectories[arm],
                device=torch.device("cpu"),
                ppo_passes=int(configuration["ppo_passes"]),
                gamma=GAMMA,
            )
            finite[arm] &= bool(metrics["finite_update"])
            maximum_replay[arm] = max(
                maximum_replay[arm], _max_replay_error(metrics)
            )
            actor_steps[arm] += int(configuration["ppo_passes"])
            critic_steps[arm] += int(configuration["ppo_passes"])

    source.assert_parameter_match(
        models[source.REC_ARM],
        models[source.CS_ARM],
        require_byte_identity=False,
    )
    arms: dict[str, dict[str, object]] = {}
    for arm, model in models.items():
        final_reference = _checkpoint_reference(replicate, arm, "final")
        _save_checkpoint(
            run_root / final_reference,
            source_commit=source_commit,
            formal=formal,
            replicate=replicate,
            arm=arm,
            kind="final",
            configuration=configuration,
            seeds=seeds,
            model=model,
        )
        arms[arm] = {
            "carry_mode": arm,
            "finite_updates": finite[arm],
            "lifecycle_contract_valid": lifecycle_valid[arm],
            "maximum_replay_error": maximum_replay[arm],
            "completed_fast_updates": int(configuration["fast_updates"]),
            "completed_return_to_go_updates": int(
                configuration["return_to_go_updates"]
            ),
            "fast_optimizer_steps": fast_steps[arm],
            "return_to_go_actor_optimizer_steps": actor_steps[arm],
            "return_to_go_critic_optimizer_steps": critic_steps[arm],
            "total_optimizer_steps": (
                fast_steps[arm] + actor_steps[arm] + critic_steps[arm]
            ),
            "zero_checkpoint": _checkpoint_reference(replicate, arm, "zero"),
            "final_checkpoint": final_reference,
            "zero_state_digest": zero_digests[arm],
            "final_state_digest": _state_digest(model),
        }
    assert initial_equality is not None
    return {
        "replicate": replicate,
        "seeds": seeds,
        "paired_collection_before_update": True,
        "initial_parameter_contract": {
            "state_dict_keys_equal": True,
            "state_dict_shapes_equal": True,
            "trainable_masks_equal": True,
            "parameter_counts_equal": True,
            "initial_state_bytes_equal": True,
        },
        "forced_initial_equality_max_errors": initial_equality,
        "initial_gradient_audits": gradient_audits,
        "arms": arms,
    }


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    preflight_root: Path | None = None,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G35 training requires an integrated source commit")
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("G35 formal authorization token mismatch")
        _validate_formal_preflight(preflight_root, source_commit=source_commit)
    elif authorization_token is not None or preflight_root is not None:
        raise ValueError("G35 nonformal training cannot carry formal authority")
    started = time.perf_counter()
    configuration = _configuration(formal=formal)
    configure_runtime(source.bootstrap_seed(formal=formal))
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "checkpoints").mkdir(exist_ok=True)
    rows = [
        _train_replicate(
            run_root=run_root,
            source_commit=source_commit,
            formal=formal,
            replicate=replicate,
            configuration=configuration,
        )
        for replicate in range(int(configuration["replicates"]))
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": source_commit,
        "authorization_token": authorization_token,
        "preflight_root": (
            str(preflight_root.resolve()) if preflight_root is not None else None
        ),
        "runtime": _runtime_identity(),
        "configuration": configuration,
        "source_controls": source.source_controls(),
        "stage_wall_time_seconds": time.perf_counter() - started,
        "replicate_results": rows,
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _training_errors(
    run_root: Path, training: Mapping[str, Any]
) -> list[str]:
    errors: list[str] = []
    formal = bool(training.get("formal"))
    configuration = _configuration(formal=formal)
    if (
        training.get("schema_version") != SCHEMA_VERSION
        or training.get("algorithm") != ALGORITHM_ID
        or training.get("source_id") != source.SOURCE_ID
        or training.get("stage") != "train"
        or training.get("status") != "COMPLETE"
        or training.get("configuration") != configuration
        or training.get("source_controls") != source.source_controls()
        or re.fullmatch(r"[0-9a-f]{40}", str(training.get("source_commit")))
        is None
    ):
        errors.append("G35 training identity mismatch")
    runtime = training.get("runtime", {})
    if (
        runtime.get("backend") != "cpu"
        or runtime.get("torch_threads") != 1
        or runtime.get("torch") != str(torch.__version__)
    ):
        errors.append("G35 training runtime mismatch")
    if formal and training.get("authorization_token") != AUTHORIZATION_TOKEN:
        errors.append("G35 formal training authority mismatch")
    if not formal and (
        training.get("authorization_token") is not None
        or training.get("preflight_root") is not None
    ):
        errors.append("G35 nonformal training carried formal state")
    stage_seconds = training.get("stage_wall_time_seconds")
    if (
        not isinstance(stage_seconds, (int, float))
        or isinstance(stage_seconds, bool)
        or not np.isfinite(stage_seconds)
        or stage_seconds < 0.0
    ):
        errors.append("G35 training timing invalid")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(configuration["replicates"]):
        errors.append("G35 training replicate inventory mismatch")
        return errors
    expected_fast_steps = int(configuration["fast_updates"]) * int(
        configuration["ppo_passes"]
    )
    expected_rtg_steps = int(configuration["return_to_go_updates"]) * int(
        configuration["ppo_passes"]
    )
    source_commit = str(training.get("source_commit"))
    for replicate, row in enumerate(rows):
        try:
            seeds = source.seed_block(replicate, formal=formal)
            if (
                row.get("replicate") != replicate
                or row.get("seeds") != seeds
                or row.get("paired_collection_before_update") is not True
                or row.get("initial_parameter_contract")
                != {
                    "state_dict_keys_equal": True,
                    "state_dict_shapes_equal": True,
                    "trainable_masks_equal": True,
                    "parameter_counts_equal": True,
                    "initial_state_bytes_equal": True,
                }
            ):
                raise ValueError("G35 paired training contract mismatch")
            equality = row["forced_initial_equality_max_errors"]
            if (
                set(equality)
                != {"pre_tanh", "actions", "token_log_prob", "value"}
                or any(
                    not np.isfinite(float(value))
                    or float(value) > source.INITIAL_EQUALITY_TOLERANCE
                    for value in equality.values()
                )
            ):
                raise ValueError("G35 forced initial equality artifact mismatch")
            audits = row["initial_gradient_audits"]
            if set(audits) != set(source.ARMS):
                raise ValueError("G35 gradient-audit arm inventory mismatch")
            for audit in audits.values():
                if audit.get("passed") is not True:
                    raise ValueError("G35 initial gradient audit did not pass")
                group_rows = {
                    name: value for name, value in audit.items() if name != "passed"
                }
                expected_groups = {
                    "member_encoder",
                    "context_encoder",
                    "gated_cell_input_weights",
                    "gated_cell_recurrent_weights",
                    "gated_cell_biases",
                    "action_head",
                    "current_readout",
                    "log_std",
                    "centralized_slow_critic",
                    "immediate_baseline",
                    "successor_baseline",
                }
                if set(group_rows) != expected_groups or any(
                    value.get("finite") is not True
                    or value.get("live") is not True
                    or max(
                        float(value["fast_objective_gradient_norm"]),
                        float(value["return_to_go_objective_gradient_norm"]),
                    )
                    <= source.GRADIENT_LIVE_TOLERANCE
                    for value in group_rows.values()
                ):
                    raise ValueError("G35 gradient-audit group mismatch")
            arms = row["arms"]
            if set(arms) != set(source.ARMS):
                raise ValueError("G35 training arm inventory mismatch")
            loaded: dict[
                tuple[str, str], source.G35MatchedStateCarryPolicy
            ] = {}
            for arm in source.ARMS:
                arm_row = arms[arm]
                expected_total = expected_fast_steps + 2 * expected_rtg_steps
                if (
                    arm_row.get("carry_mode") != arm
                    or arm_row.get("finite_updates") is not True
                    or arm_row.get("lifecycle_contract_valid") is not True
                    or float(arm_row.get("maximum_replay_error", float("inf")))
                    > REPLAY_TOLERANCE
                    or arm_row.get("completed_fast_updates")
                    != int(configuration["fast_updates"])
                    or arm_row.get("completed_return_to_go_updates")
                    != int(configuration["return_to_go_updates"])
                    or arm_row.get("fast_optimizer_steps") != expected_fast_steps
                    or arm_row.get("return_to_go_actor_optimizer_steps")
                    != expected_rtg_steps
                    or arm_row.get("return_to_go_critic_optimizer_steps")
                    != expected_rtg_steps
                    or arm_row.get("total_optimizer_steps") != expected_total
                    or arm_row.get("zero_checkpoint")
                    != _checkpoint_reference(replicate, arm, "zero")
                    or arm_row.get("final_checkpoint")
                    != _checkpoint_reference(replicate, arm, "final")
                ):
                    raise ValueError("G35 arm exposure mismatch")
                for kind in ("zero", "final"):
                    model, _ = _load_checkpoint(
                        run_root / arm_row[f"{kind}_checkpoint"],
                        source_commit=source_commit,
                        formal=formal,
                        replicate=replicate,
                        arm=arm,
                        kind=kind,
                        configuration=configuration,
                        seeds=seeds,
                        member_capacity=g32.TRAIN_CAPACITY,
                    )
                    loaded[(arm, kind)] = model
                    if _state_digest(model) != arm_row[f"{kind}_state_digest"]:
                        raise ValueError("G35 checkpoint digest mismatch")
            source.assert_parameter_match(
                loaded[(source.REC_ARM, "zero")],
                loaded[(source.CS_ARM, "zero")],
                require_byte_identity=True,
            )
            source.assert_parameter_match(
                loaded[(source.REC_ARM, "final")],
                loaded[(source.CS_ARM, "final")],
                require_byte_identity=False,
            )
        except (KeyError, TypeError, ValueError, OSError) as error:
            errors.append(str(error))
    return errors


def _source_inventory(
    *, replicate: int, capacity: int, episode_count: int, formal: bool
) -> tuple[tuple[g34.RandomProcessLedger, ...], dict[str, object]]:
    processes = source.make_process_ledgers(
        replicate=replicate,
        capacity=capacity,
        episode_count=episode_count,
        formal=formal,
    )
    return processes, {
        "replicate": replicate,
        "capacity": capacity,
        "seeds": source.seed_block(replicate, formal=formal),
        "processes": [
            {
                "local_episode_id": row.local_episode_id,
                "episode_id": row.episode_id,
                "profile": row.profile.name,
                "event_times": list(row.event_times),
                "event_order": list(row.event_order),
                "count_trajectory": list(row.count_trajectory),
                "random_expected_roster_sizes": list(row.expected_roster_sizes),
                "fixed_expected_roster_sizes": list(
                    row.base.expected_roster_sizes
                ),
                "temporarily_absent": list(row.base.temporarily_absent),
                "fresh_join": list(row.base.fresh_join),
                "terminal_leave": list(row.base.terminal_leave),
                "signature": repr(row.signature),
            }
            for row in processes
        ],
    }


def _constructive_cell(
    replicate: int,
    capacity: int,
    processes: Sequence[g34.RandomProcessLedger],
) -> dict[str, object]:
    return {
        "replicate": replicate,
        "capacity": capacity,
        "arm": "CONSTRUCTIVE",
        "cell": CONSTRUCTIVE_RANDOM,
        "checkpoint": "constructive",
        "process": "random",
        "deterministic": True,
        "optimizer_steps": 0,
        "state_before": None,
        "state_after": None,
        "lifecycle_valid": True,
        "episodes": list(g34.evaluate_constructive(processes)),
    }


def _cell_contract(name: str) -> dict[str, object]:
    contracts = {
        ZERO_RANDOM_DET: {
            "checkpoint": "zero",
            "process": "random",
            "deterministic": True,
        },
        FINAL_FIXED_DET: {
            "checkpoint": "final",
            "process": "fixed",
            "deterministic": True,
        },
        FINAL_FIXED_STOCH: {
            "checkpoint": "final",
            "process": "fixed",
            "deterministic": False,
        },
        FINAL_RANDOM_DET: {
            "checkpoint": "final",
            "process": "random",
            "deterministic": True,
        },
        FINAL_RANDOM_STOCH: {
            "checkpoint": "final",
            "process": "random",
            "deterministic": False,
        },
    }
    if name not in contracts:
        raise ValueError("G35 unknown model cell")
    return contracts[name]


def _model_cell(
    *,
    replicate: int,
    capacity: int,
    arm: str,
    name: str,
    model: source.G35MatchedStateCarryPolicy,
    processes: Sequence[g34.RandomProcessLedger],
    action_seed: int,
) -> dict[str, object]:
    contract = _cell_contract(name)
    before = _state_digest(model)
    episodes, lifecycle_valid = g34.evaluate_model(
        model,
        processes=processes,
        action_seed=int(action_seed),
        process_kind=str(contract["process"]),
        deterministic=bool(contract["deterministic"]),
    )
    return {
        "replicate": replicate,
        "capacity": capacity,
        "arm": arm,
        "cell": name,
        **contract,
        "optimizer_steps": 0,
        "state_before": before,
        "state_after": _state_digest(model),
        "lifecycle_valid": lifecycle_valid,
        "episodes": list(episodes),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    errors = _training_errors(run_root, training)
    if errors:
        raise ValueError("G35 training artifact invalid: " + " | ".join(errors))
    formal = bool(training["formal"])
    source_commit = str(training["source_commit"])
    configuration = _configuration(formal=formal)
    configure_runtime(source.bootstrap_seed(formal=formal))
    cells: list[dict[str, object]] = []
    inventories: list[dict[str, object]] = []
    rows = training["replicate_results"]
    for replicate in range(int(configuration["replicates"])):
        seeds = source.seed_block(replicate, formal=formal)
        for capacity in g34.CAPACITIES:
            processes, inventory = _source_inventory(
                replicate=replicate,
                capacity=capacity,
                episode_count=int(
                    configuration["evaluation_episodes_per_cell"]
                ),
                formal=formal,
            )
            inventories.append(inventory)
            cells.append(_constructive_cell(replicate, capacity, processes))
            for arm in source.ARMS:
                arm_row = rows[replicate]["arms"][arm]
                loaded = {
                    kind: _load_checkpoint(
                        run_root / arm_row[f"{kind}_checkpoint"],
                        source_commit=source_commit,
                        formal=formal,
                        replicate=replicate,
                        arm=arm,
                        kind=kind,
                        configuration=configuration,
                        seeds=seeds,
                        member_capacity=capacity,
                    )[0]
                    for kind in ("zero", "final")
                }
                for name in MODEL_CELLS:
                    kind = str(_cell_contract(name)["checkpoint"])
                    cells.append(
                        _model_cell(
                            replicate=replicate,
                            capacity=capacity,
                            arm=arm,
                            name=name,
                            model=loaded[kind],
                            processes=processes,
                            action_seed=seeds["evaluation_action"],
                        )
                    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": source_commit,
        "authorization_token": training["authorization_token"],
        "runtime": _runtime_identity(),
        "configuration": configuration,
        "source_controls": source.source_controls(),
        "training_manifest_digest": hashlib.sha256(
            (run_root / "train_manifest.json").read_bytes()
        ).hexdigest(),
        "stage_wall_time_seconds": time.perf_counter() - started,
        "source_inventory": inventories,
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def _evaluation_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> list[str]:
    errors = _training_errors(run_root, training)
    formal = bool(training.get("formal"))
    configuration = _configuration(formal=formal)
    if (
        evaluation.get("schema_version") != SCHEMA_VERSION
        or evaluation.get("algorithm") != ALGORITHM_ID
        or evaluation.get("source_id") != source.SOURCE_ID
        or evaluation.get("stage") != "evaluate"
        or evaluation.get("status") != "COMPLETE"
        or evaluation.get("formal") is not formal
        or evaluation.get("source_commit") != training.get("source_commit")
        or evaluation.get("authorization_token")
        != training.get("authorization_token")
        or evaluation.get("configuration") != configuration
        or evaluation.get("source_controls") != source.source_controls()
        or evaluation.get("training_manifest_digest")
        != hashlib.sha256((run_root / "train_manifest.json").read_bytes()).hexdigest()
    ):
        errors.append("G35 evaluation identity mismatch")
    runtime = evaluation.get("runtime", {})
    if (
        runtime.get("backend") != "cpu"
        or runtime.get("torch_threads") != 1
        or runtime.get("torch") != str(torch.__version__)
    ):
        errors.append("G35 evaluation runtime mismatch")
    stage_seconds = evaluation.get("stage_wall_time_seconds")
    if (
        not isinstance(stage_seconds, (int, float))
        or isinstance(stage_seconds, bool)
        or not np.isfinite(stage_seconds)
        or stage_seconds < 0.0
    ):
        errors.append("G35 evaluation timing invalid")
    replicate_count = int(configuration["replicates"])
    episode_count = int(configuration["evaluation_episodes_per_cell"])
    expected_inventory: list[dict[str, object]] = []
    for replicate in range(replicate_count):
        for capacity in g34.CAPACITIES:
            _, inventory = _source_inventory(
                replicate=replicate,
                capacity=capacity,
                episode_count=episode_count,
                formal=formal,
            )
            expected_inventory.append(inventory)
    if evaluation.get("source_inventory") != expected_inventory:
        errors.append("G35 source inventory mismatch")
    cells = evaluation.get("cells")
    if not isinstance(cells, list) or len(cells) != int(
        configuration["total_cells"]
    ):
        errors.append("G35 evaluation cell inventory mismatch")
        return errors
    inventories = {
        (int(row["replicate"]), int(row["capacity"])): row["processes"]
        for row in expected_inventory
    }
    checkpoint_digests: dict[tuple[int, int, str, str], str] = {}
    try:
        training_rows = training["replicate_results"]
        source_commit = str(training["source_commit"])
        for replicate in range(replicate_count):
            seeds = source.seed_block(replicate, formal=formal)
            for capacity in g34.CAPACITIES:
                for arm in source.ARMS:
                    arm_row = training_rows[replicate]["arms"][arm]
                    for kind in ("zero", "final"):
                        model, _ = _load_checkpoint(
                            run_root / arm_row[f"{kind}_checkpoint"],
                            source_commit=source_commit,
                            formal=formal,
                            replicate=replicate,
                            arm=arm,
                            kind=kind,
                            configuration=configuration,
                            seeds=seeds,
                            member_capacity=capacity,
                        )
                        checkpoint_digests[(replicate, capacity, arm, kind)] = (
                            _state_digest(model)
                        )
    except (KeyError, TypeError, ValueError, OSError) as error:
        errors.append(str(error))
    observed: set[tuple[int, int, str, str]] = set()
    for cell in cells:
        try:
            replicate = int(cell["replicate"])
            capacity = int(cell["capacity"])
            arm = str(cell["arm"])
            name = str(cell["cell"])
            key = (replicate, capacity, arm, name)
            if (
                replicate not in range(replicate_count)
                or capacity not in g34.CAPACITIES
                or key in observed
            ):
                raise ValueError("G35 cell identity mismatch")
            observed.add(key)
            constructive = arm == "CONSTRUCTIVE"
            if constructive:
                if (
                    name != CONSTRUCTIVE_RANDOM
                    or cell.get("checkpoint") != "constructive"
                    or cell.get("process") != "random"
                    or cell.get("deterministic") is not True
                    or cell.get("state_before") is not None
                    or cell.get("state_after") is not None
                ):
                    raise ValueError("G35 constructive cell route mismatch")
            else:
                if arm not in source.ARMS or name not in MODEL_CELLS:
                    raise ValueError("G35 model cell identity mismatch")
                contract = _cell_contract(name)
                if any(cell.get(field) != value for field, value in contract.items()):
                    raise ValueError("G35 model cell route mismatch")
                digest = checkpoint_digests.get(
                    (replicate, capacity, arm, str(contract["checkpoint"]))
                )
                if (
                    digest is None
                    or cell.get("state_before") != digest
                    or cell.get("state_after") != digest
                ):
                    raise ValueError("G35 checkpoint-to-cell binding mismatch")
            if (
                cell.get("optimizer_steps") != 0
                or cell.get("lifecycle_valid") is not True
            ):
                raise ValueError("G35 evaluation lifecycle or step mismatch")
            episodes = cell["episodes"]
            if not isinstance(episodes, list) or len(episodes) != episode_count:
                raise ValueError("G35 evaluation episode count mismatch")
            expected_processes = inventories[(replicate, capacity)]
            process_kind = str(cell["process"])
            for index, episode in enumerate(episodes):
                expected = expected_processes[index]
                if (
                    episode.get("local_episode_id") != index
                    or episode.get("episode_id") != expected["episode_id"]
                    or episode.get("profile") != expected["profile"]
                    or episode.get("event_times") != expected["event_times"]
                    or episode.get("event_order") != expected["event_order"]
                    or episode.get("count_trajectory")
                    != expected["count_trajectory"]
                    or episode.get("signature") != expected["signature"]
                ):
                    raise ValueError("G35 episode pairing mismatch")
                trace = g34_runner._trace_evidence(episode)
                roster_field = (
                    "random_expected_roster_sizes"
                    if process_kind == "random"
                    else "fixed_expected_roster_sizes"
                )
                if (
                    trace["roster_size_trace"]
                    != tuple(expected[roster_field])
                    or episode.get("roster_sizes_valid") is not True
                    or not g34_runner._summary_matches_trace(episode, trace)
                ):
                    raise ValueError("G35 trace evidence mismatch")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
    expected_keys = {
        (replicate, capacity, "CONSTRUCTIVE", CONSTRUCTIVE_RANDOM)
        for replicate in range(replicate_count)
        for capacity in g34.CAPACITIES
    } | {
        (replicate, capacity, arm, name)
        for replicate in range(replicate_count)
        for capacity in g34.CAPACITIES
        for arm in source.ARMS
        for name in MODEL_CELLS
    }
    if observed != expected_keys:
        errors.append("G35 evaluation cell key set mismatch")
    return errors


def _cell_map(
    evaluation: Mapping[str, Any],
) -> dict[tuple[int, int, str, str], Mapping[str, Any]]:
    return {
        (
            int(row["replicate"]),
            int(row["capacity"]),
            str(row["arm"]),
            str(row["cell"]),
        ): row
        for row in evaluation["cells"]
    }


def _metric_arrays(
    evaluation: Mapping[str, Any], arm: str, cell_name: str, metric: str
) -> dict[int, np.ndarray]:
    configuration = evaluation["configuration"]
    cells = _cell_map(evaluation)
    return {
        capacity: np.asarray(
            [
                [
                    g34_runner._trace_evidence(episode)[metric]
                    for episode in cells[
                        (replicate, capacity, arm, cell_name)
                    ]["episodes"]
                ]
                for replicate in range(int(configuration["replicates"]))
            ],
            dtype=np.float64,
        )
        for capacity in g34.CAPACITIES
    }


def _difference(
    left: Mapping[int, np.ndarray], right: Mapping[int, np.ndarray]
) -> dict[int, np.ndarray]:
    return {capacity: left[capacity] - right[capacity] for capacity in left}


def _bootstrap_plan(
    *, formal: bool, replicates: int, episodes: int, repetitions: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(source.bootstrap_seed(formal=formal))
    return (
        rng.integers(
            0, replicates, size=(repetitions, replicates), dtype=np.int16
        ),
        rng.integers(
            0,
            episodes,
            size=(
                repetitions,
                replicates,
                len(g34.CAPACITIES),
                episodes,
            ),
            dtype=np.int16,
        ),
    )


def _hierarchical_ci(
    values: Mapping[int, np.ndarray],
    *,
    capacities: Sequence[int],
    plan: tuple[np.ndarray, np.ndarray],
) -> list[float]:
    replicate_draws, episode_draws = plan
    totals = np.zeros(len(replicate_draws), dtype=np.float64)
    count = 0
    for capacity in capacities:
        array = np.asarray(values[capacity], dtype=np.float64)
        capacity_index = g34.CAPACITIES.index(capacity)
        for slot in range(replicate_draws.shape[1]):
            replicate = replicate_draws[:, slot]
            episodes = episode_draws[:, slot, capacity_index]
            totals += array[replicate[:, None], episodes].sum(axis=1)
            count += array.shape[1]
    return [
        float(value)
        for value in np.percentile(totals / count, (2.5, 50.0, 97.5))
    ]


def _minimum_replicate_mean(values: Mapping[int, np.ndarray]) -> float:
    replicates = next(iter(values.values())).shape[0]
    return min(
        float(
            np.concatenate(
                [values[capacity][replicate] for capacity in g34.CAPACITIES]
            ).mean()
        )
        for replicate in range(replicates)
    )


def _arm_access(
    evaluation: Mapping[str, Any],
    arm: str,
    plan: tuple[np.ndarray, np.ndarray],
) -> dict[str, object]:
    fixed = _metric_arrays(evaluation, arm, FINAL_FIXED_DET, "utility")
    fixed_stochastic = _metric_arrays(
        evaluation, arm, FINAL_FIXED_STOCH, "utility"
    )
    random_utility = _metric_arrays(
        evaluation, arm, FINAL_RANDOM_DET, "utility"
    )
    random_event = _metric_arrays(
        evaluation, arm, FINAL_RANDOM_DET, "minimum_event_window_utility"
    )
    random_segment = _metric_arrays(
        evaluation, arm, FINAL_RANDOM_DET, "minimum_process_segment_utility"
    )
    random_stochastic = _metric_arrays(
        evaluation, arm, FINAL_RANDOM_STOCH, "utility"
    )
    zero = _metric_arrays(evaluation, arm, ZERO_RANDOM_DET, "utility")
    process_delta = _difference(random_utility, fixed)
    learned_gain = _difference(random_utility, zero)
    fixed_ci = {
        capacity: _hierarchical_ci(
            fixed, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    random_ci = {
        capacity: _hierarchical_ci(
            random_utility, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    event_ci = {
        capacity: _hierarchical_ci(
            random_event, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    segment_ci = {
        capacity: _hierarchical_ci(
            random_segment, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    process_ci = {
        capacity: _hierarchical_ci(
            process_delta, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    fixed_stochastic_ci = _hierarchical_ci(
        fixed_stochastic, capacities=g34.CAPACITIES, plan=plan
    )
    random_stochastic_ci = _hierarchical_ci(
        random_stochastic, capacities=g34.CAPACITIES, plan=plan
    )
    learned_gain_ci = _hierarchical_ci(
        learned_gain, capacities=g34.CAPACITIES, plan=plan
    )
    minimum_fixed = _minimum_replicate_mean(fixed)
    minimum_random = _minimum_replicate_mean(random_utility)
    access_pass = (
        all(fixed_ci[capacity][0] >= UTILITY_FLOOR for capacity in g34.CAPACITIES)
        and fixed_stochastic_ci[0] >= STOCHASTIC_FLOOR
        and minimum_fixed >= MINIMUM_REPLICATE_FLOOR
        and all(random_ci[capacity][0] >= UTILITY_FLOOR for capacity in g34.CAPACITIES)
        and all(event_ci[capacity][0] >= EVENT_FLOOR for capacity in g34.CAPACITIES)
        and all(segment_ci[capacity][0] >= SEGMENT_FLOOR for capacity in g34.CAPACITIES)
        and all(process_ci[capacity][0] >= PROCESS_MARGIN for capacity in g34.CAPACITIES)
        and random_stochastic_ci[0] >= STOCHASTIC_FLOOR
        and minimum_random >= MINIMUM_REPLICATE_FLOOR
        and learned_gain_ci[0] > 0.0
    )
    confident_fail = (
        any(fixed_ci[capacity][2] < UTILITY_FLOOR for capacity in g34.CAPACITIES)
        or fixed_stochastic_ci[2] < STOCHASTIC_FLOOR
        or minimum_fixed < MINIMUM_REPLICATE_FLOOR
        or any(random_ci[capacity][2] < UTILITY_FLOOR for capacity in g34.CAPACITIES)
        or any(event_ci[capacity][2] < EVENT_FLOOR for capacity in g34.CAPACITIES)
        or any(segment_ci[capacity][2] < SEGMENT_FLOOR for capacity in g34.CAPACITIES)
        or any(process_ci[capacity][2] < PROCESS_MARGIN for capacity in g34.CAPACITIES)
        or random_stochastic_ci[2] < STOCHASTIC_FLOOR
        or minimum_random < MINIMUM_REPLICATE_FLOOR
        or learned_gain_ci[2] <= 0.0
    )
    return {
        "fixed_utility_ci95": fixed_ci,
        "fixed_stochastic_pooled_ci95": fixed_stochastic_ci,
        "minimum_fixed_deterministic_replicate_mean": minimum_fixed,
        "random_utility_ci95": random_ci,
        "random_event_window_ci95": event_ci,
        "random_process_segment_ci95": segment_ci,
        "random_minus_fixed_ci95": process_ci,
        "random_stochastic_pooled_ci95": random_stochastic_ci,
        "minimum_random_deterministic_replicate_mean": minimum_random,
        "learned_gain_ci95": learned_gain_ci,
        "access_pass": bool(access_pass),
        "access_confident_fail": bool(confident_fail),
    }


def select_g35_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or (
        bool(metrics["rec_access_confident_fail"])
        and bool(metrics["cs_access_confident_fail"])
    ):
        return SOURCE_FAILURE_BRANCH
    if bool(metrics["current_state_sufficient"]):
        return CS_SUFFICIENT_BRANCH
    if bool(metrics["recurrent_advantage"]):
        return REC_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def analyze(*, run_root: Path, require_formal: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G35 analysis requires formal artifacts")
    configure_runtime(source.bootstrap_seed(formal=formal))
    errors = _evaluation_errors(run_root, training, evaluation)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        cells = _cell_map(evaluation)
        constructive_valid = all(
            min(
                float(g34_runner._trace_evidence(episode)[field])
                for episode in cell["episodes"]
                for field in (
                    "utility",
                    "minimum_step_utility",
                    "minimum_event_window_utility",
                    "minimum_process_segment_utility",
                )
            )
            >= 1.0 - CONSTRUCTIVE_TOLERANCE
            for key, cell in cells.items()
            if key[2:] == ("CONSTRUCTIVE", CONSTRUCTIVE_RANDOM)
        )
        source_valid = constructive_valid and all(
            bool(cell["lifecycle_valid"]) for cell in cells.values()
        )
        configuration = evaluation["configuration"]
        plan = _bootstrap_plan(
            formal=formal,
            replicates=int(configuration["replicates"]),
            episodes=int(configuration["evaluation_episodes_per_cell"]),
            repetitions=int(configuration["bootstrap_resamples"]),
        )
        access = {
            arm: _arm_access(evaluation, arm, plan) for arm in source.ARMS
        }
        rec_utility = _metric_arrays(
            evaluation, source.REC_ARM, FINAL_RANDOM_DET, "utility"
        )
        cs_utility = _metric_arrays(
            evaluation, source.CS_ARM, FINAL_RANDOM_DET, "utility"
        )
        recurrence_delta = _difference(rec_utility, cs_utility)
        pooled_delta_ci = _hierarchical_ci(
            recurrence_delta, capacities=g34.CAPACITIES, plan=plan
        )
        capacity_delta_ci = {
            capacity: _hierarchical_ci(
                recurrence_delta, capacities=(capacity,), plan=plan
            )
            for capacity in g34.CAPACITIES
        }
        cs_sufficient = bool(access[source.CS_ARM]["access_pass"]) and (
            pooled_delta_ci[2] <= RECURRENCE_MARGIN
            and all(
                capacity_delta_ci[capacity][2] <= RECURRENCE_MARGIN
                for capacity in g34.CAPACITIES
            )
        )
        recurrent_advantage = bool(access[source.REC_ARM]["access_pass"]) and (
            pooled_delta_ci[0] > RECURRENCE_MARGIN
            and all(
                capacity_delta_ci[capacity][0] > 0.0
                for capacity in g34.CAPACITIES
            )
        )
        metrics.update(
            {
                "constructive_source_valid": constructive_valid,
                "source_valid": source_valid,
                "arm_access": access,
                "rec_access_pass": access[source.REC_ARM]["access_pass"],
                "cs_access_pass": access[source.CS_ARM]["access_pass"],
                "rec_access_confident_fail": access[source.REC_ARM][
                    "access_confident_fail"
                ],
                "cs_access_confident_fail": access[source.CS_ARM][
                    "access_confident_fail"
                ],
                "rec_minus_cs_pooled_ci95": pooled_delta_ci,
                "rec_minus_cs_capacity_ci95": capacity_delta_ci,
                "current_state_sufficient": cs_sufficient,
                "recurrent_advantage": recurrent_advantage,
            }
        )
    analysis_seconds = time.perf_counter() - started
    projection: float | None = None
    projection_executable: bool | None = None
    if not formal and not errors:
        projection = 1.25 * (
            30.0 * float(training["stage_wall_time_seconds"])
            + 48.0 * float(evaluation["stage_wall_time_seconds"])
            + 40.0 * analysis_seconds
        )
        projection_executable = projection <= FORMAL_WALL_CLOCK_CAP_SECONDS
    if errors:
        branch = INVALID_BRANCH
    elif formal:
        branch = select_g35_result_branch(metrics)
    elif projection_executable:
        branch = NONFORMAL_BRANCH
    else:
        branch = NON_EXECUTABLE_BRANCH
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": formal,
        "source_commit": training.get("source_commit"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "stage_wall_time_seconds": analysis_seconds,
        "formal_projection_seconds": projection,
        "formal_projection_executable": projection_executable,
        "formal_wall_clock_cap_seconds": FORMAL_WALL_CLOCK_CAP_SECONDS,
        "thresholds": {
            "utility_floor": UTILITY_FLOOR,
            "event_floor": EVENT_FLOOR,
            "segment_floor": SEGMENT_FLOOR,
            "process_noninferiority_margin": PROCESS_MARGIN,
            "stochastic_floor": STOCHASTIC_FLOOR,
            "minimum_replicate_floor": MINIMUM_REPLICATE_FLOOR,
            "learned_gain_strict_floor": 0.0,
            "recurrence_materiality_margin": RECURRENCE_MARGIN,
            "constructive_tolerance": CONSTRUCTIVE_TOLERANCE,
        },
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    train(
        run_root=run_root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
    )
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit", default="")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--require-formal", action="store_true")
    args = parser.parse_args()
    if args.mode == "train":
        value = train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            preflight_root=args.preflight_root,
        )
    elif args.mode == "evaluate":
        value = evaluate(run_root=args.run_root)
    elif args.mode == "analyze":
        value = analyze(
            run_root=args.run_root, require_formal=args.require_formal
        )
    else:
        if args.formal or args.authorization_token or args.preflight_root:
            raise ValueError("G35 exercise cannot carry formal authority")
        value = exercise(
            run_root=args.run_root, source_commit=args.source_commit
        )
    print(json.dumps(value, sort_keys=True))


if __name__ == "__main__":
    main()
