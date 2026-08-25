"""Train, evaluate, and analyze the frozen G38 folded-six-coordinate contract."""

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
from ha_ctse_process import continuous_roster_six_coordinate_cs_g38 as source
from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    optimize_fast_anchor_update,
)
from ha_ctse_process.return_to_go_direction_balanced_full_actor_g31 import (
    optimize_return_to_go_direction_balanced_update,
)
from scripts import run_continuous_roster_random_process_g34 as g34_runner
from scripts import run_continuous_roster_reactive_reduction_g35 as g35_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = "CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_AUTHORIZATION_V1"
ALIGNMENT_AUDIT_ID = "CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_CODE_SCIENCE_ALIGNMENT_AUDIT"

INVALID_BRANCH = "INVALID_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38"
SOURCE_FAILURE_BRANCH = "SOURCE_OR_COMMON_ACCESS_FAILURE_G38"
SIX_COORDINATE_SUFFICIENT_BRANCH = "SIX_COORDINATE_ARCHITECTURAL_REDUCTION_SUFFICIENT_G38"
FULL_INFORMATION_ADVANTAGE_BRANCH = "FULL_INFORMATION_FINITE_BUDGET_ADVANTAGE_G38"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_SIX_COORDINATE_G38"
NONFORMAL_BRANCH = "NONFORMAL_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_EXERCISE_COMPLETE"
NON_EXECUTABLE_BRANCH = "NON_EXECUTABLE_EVIDENCE_DESIGN"

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
INFORMATION_MARGIN = 0.05
CONSTRUCTIVE_WITNESS_FLOOR = 0.94048
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
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
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _artifact_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: row.detach().cpu().clone() for name, row in model.state_dict().items()}


def _state_digest(state_or_model: Mapping[str, torch.Tensor] | torch.nn.Module) -> str:
    state = state_or_model.state_dict() if isinstance(state_or_model, torch.nn.Module) else state_or_model
    digest = hashlib.sha256()
    for name in sorted(state):
        row = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(row.dtype).encode("ascii"))
        digest.update(np.asarray(row.shape, dtype=np.int64).tobytes())
        digest.update(row.numpy().tobytes())
    return digest.hexdigest()


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
    fast = int(counts["fast_updates"])
    rtg = int(counts["return_to_go_updates"])
    envs = int(counts["num_envs"])
    passes = int(counts["ppo_passes"])
    episodes = int(counts["evaluation_episodes_per_cell"])
    cells_per_replicate = len(source.ARMS) * len(g34.CAPACITIES) * len(MODEL_CELLS)
    training_transitions = len(source.ARMS) * replicates * (fast + rtg) * envs * roster_env.HORIZON
    evaluation_transitions = replicates * cells_per_replicate * episodes * roster_env.HORIZON
    optimizer_steps = len(source.ARMS) * replicates * (fast * passes + 2 * rtg * passes)
    return {
        **counts,
        "arms": list(source.ARMS),
        "common_training_observation_dim": source.FULL_OBSERVATION_DIM,
        "folded_deployment_observation_dim": source.RETAINED_OBSERVATION_DIM,
        "critic_state_dim": roster_env.CRITIC_STATE_DIM,
        "action_dim": roster_env.ACTION_DIM,
        "actor_width": source.HIDDEN_DIM,
        "raw_input_affines": ["member_input:Linear(10,32)", "current_readout:Linear(10,2)"],
        "removed_actor_weights": source.REMOVED_ACTOR_WEIGHTS,
        "training_capacity": roster_env.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "gamma": GAMMA,
        "learning_rate": LEARNING_RATE,
        "initial_log_std": source.INITIAL_LOG_STD,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)",
        "minibatches": "none",
        "checkpoint_selection": "final_only",
        "episode_exclusions": "none",
        "cells_per_arm_capacity": len(MODEL_CELLS),
        "cells_per_replicate": cells_per_replicate,
        "total_cells": replicates * cells_per_replicate,
        "training_transitions": training_transitions,
        "evaluation_transitions": evaluation_transitions,
        "total_real_transitions": training_transitions + evaluation_transitions,
        "optimizer_steps": optimizer_steps,
        "evaluation_optimizer_steps": 0,
        "paired_collection_before_update": True,
        "fold_environment_trajectories_per_episode": 1,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }


def _checkpoint_reference(replicate: int, arm: str, kind: str, *, folded: bool = False) -> str:
    suffix = "_folded6" if folded else ""
    return f"checkpoints/replicate_{replicate}_{arm.lower()}_{kind}{suffix}.pt"


def _checkpoint_payload(
    *, source_commit: str, formal: bool, replicate: int, arm: str, kind: str,
    configuration: Mapping[str, object], seeds: Mapping[str, int],
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": source_commit,
        "formal": formal,
        "replicate": replicate,
        "arm": arm,
        "kind": kind,
        "completed_fast_updates": 0 if kind == "zero" else int(configuration["fast_updates"]),
        "completed_return_to_go_updates": 0 if kind == "zero" else int(configuration["return_to_go_updates"]),
        "configuration": dict(configuration),
        "seeds": dict(seeds),
    }


def _save_checkpoint(
    path: Path, *, source_commit: str, formal: bool, replicate: int, arm: str,
    kind: str, configuration: Mapping[str, object], seeds: Mapping[str, int],
    model: source.G38FoldableMatchedCSPolicy,
) -> None:
    payload = _checkpoint_payload(
        source_commit=source_commit, formal=formal, replicate=replicate, arm=arm,
        kind=kind, configuration=configuration, seeds=seeds,
    )
    payload.update({"input_mode": model.input_mode, "model_state": model.state_dict()})
    torch.save(payload, path)


def _save_folded_checkpoint(
    path: Path, *, source_commit: str, formal: bool, replicate: int, kind: str,
    configuration: Mapping[str, object], seeds: Mapping[str, int],
    pre_fold: source.G38FoldableMatchedCSPolicy,
) -> tuple[source.G38FoldableMatchedCSPolicy, str]:
    source_digest = _state_digest(pre_fold)
    folded = source.fold_g38_constant_actor_checkpoint(pre_fold)
    payload = _checkpoint_payload(
        source_commit=source_commit, formal=formal, replicate=replicate,
        arm=source.FOLD6_ARM, kind=kind, configuration=configuration, seeds=seeds,
    )
    payload.update(
        {
            "input_mode": source.FOLDED6_INPUT,
            "pre_fold_source_digest": source_digest,
            "removed_actor_weights": source.REMOVED_ACTOR_WEIGHTS,
            "optimizer_steps_after_fold": 0,
            "model_state": folded.state_dict(),
        }
    )
    torch.save(payload, path)
    return folded, source_digest


def _load_checkpoint(
    path: Path, *, source_commit: str, formal: bool, replicate: int, arm: str,
    kind: str, configuration: Mapping[str, object], seeds: Mapping[str, int],
    member_capacity: int, folded: bool = False,
) -> tuple[source.G38FoldableMatchedCSPolicy, dict[str, Any]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError("G38 checkpoint is not a dictionary")
    expected = _checkpoint_payload(
        source_commit=source_commit, formal=formal, replicate=replicate, arm=arm,
        kind=kind, configuration=configuration, seeds=seeds,
    )
    for name, value in expected.items():
        if payload.get(name) != value:
            raise ValueError(f"G38 checkpoint {name} mismatch")
    input_mode = source.FOLDED6_INPUT if folded else (
        source.FULL10_INPUT if arm == source.FULL10_ARM else source.FOLD6_INPUT
    )
    if payload.get("input_mode") != input_mode:
        raise ValueError("G38 checkpoint input mode mismatch")
    if folded and (
        payload.get("removed_actor_weights") != source.REMOVED_ACTOR_WEIGHTS
        or payload.get("optimizer_steps_after_fold") != 0
    ):
        raise ValueError("G38 folded checkpoint contract mismatch")
    state = payload.get("model_state")
    if not isinstance(state, dict):
        raise ValueError("G38 checkpoint state missing")
    configure_runtime(int(seeds["model"]))
    model = source.make_model(
        member_capacity, input_mode=input_mode, initialization_seed=int(seeds["model"])
    )
    model.load_state_dict(state, strict=True)
    return model, payload


def _max_replay_error(metrics: Mapping[str, float]) -> float:
    return g35_runner._max_replay_error(metrics)


def _lifecycle_valid(trajectory: Any) -> bool:
    active = trajectory.active_mask
    reset = trajectory.terminal_hidden_reset_mask
    return bool(
        torch.count_nonzero(trajectory.actions[~active]) == 0
        and torch.count_nonzero(trajectory.old_log_probs[~active]) == 0
        and (not bool(reset.any()) or torch.count_nonzero(trajectory.hidden_before[reset]) == 0)
        and torch.count_nonzero(trajectory.hidden_before) == 0
        and torch.count_nonzero(trajectory.hidden_after) == 0
        and all(
            outcome.roster_sizes == ledger.expected_roster_sizes
            for outcome, ledger in zip(trajectory.outcomes, trajectory.ledgers)
        )
    )


def _collect(
    model: source.G38FoldableMatchedCSPolicy, *, episode_ids: tuple[int, ...],
    ledger_seed: int, action_seed: int,
) -> Any:
    raw = source.collect_g38_trajectory(
        model,
        episode_ids=episode_ids,
        ledger_seed=int(ledger_seed),
        action_seed=int(action_seed),
        device=torch.device("cpu"),
        profiles=roster_env.TRAIN_PROFILES,
    )
    return attach_credit_baselines(model, raw, device=torch.device("cpu"))


def _preflight_digests(preflight_root: Path) -> dict[str, str]:
    return {
        "training": _artifact_digest(preflight_root / "train_manifest.json"),
        "evaluation": _artifact_digest(preflight_root / "evaluation_manifest.json"),
        "analysis": _artifact_digest(preflight_root / "analysis_result.json"),
    }


def _finite_seconds(value: object, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not np.isfinite(value) or value < 0:
        raise ValueError(f"G38 {name} timing invalid")
    return float(value)


def _validate_formal_preflight(
    preflight_root: Path | None, *, source_commit: str,
    alignment_disposition: str | None, aligned_source_commit: str | None,
) -> dict[str, str]:
    if preflight_root is None:
        raise ValueError("formal G38 execution requires a bounded preflight root")
    if alignment_disposition != "ALIGNED" or aligned_source_commit != source_commit:
        raise ValueError("formal G38 execution requires ALIGNED same-source audit")
    root = Path(preflight_root)
    training = _read_json(root / "train_manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    analysis = _read_json(root / "analysis_result.json")
    artifact_errors = _evaluation_errors(root, training, evaluation)
    if artifact_errors:
        raise ValueError(
            "G38 formal preflight artifacts are invalid: "
            + " | ".join(artifact_errors)
        )
    expected = _configuration(formal=False)
    train_seconds = _finite_seconds(training.get("stage_wall_time_seconds"), "preflight train")
    eval_seconds = _finite_seconds(evaluation.get("stage_wall_time_seconds"), "preflight evaluate")
    analyze_seconds = _finite_seconds(analysis.get("stage_wall_time_seconds"), "preflight analyze")
    projection = 1.25 * (30.0 * train_seconds + 48.0 * eval_seconds + 40.0 * analyze_seconds)
    if (
        training.get("formal") is not False
        or evaluation.get("formal") is not False
        or analysis.get("formal") is not False
        or analysis.get("schema_version") != SCHEMA_VERSION
        or analysis.get("algorithm") != ALGORITHM_ID
        or analysis.get("source_id") != source.SOURCE_ID
        or analysis.get("stage") != "analyze"
        or analysis.get("status") != "COMPLETE"
        or training.get("source_commit") != source_commit
        or evaluation.get("source_commit") != source_commit
        or analysis.get("source_commit") != source_commit
        or training.get("configuration") != expected
        or evaluation.get("configuration") != expected
        or analysis.get("branch") != NONFORMAL_BRANCH
        or analysis.get("operational_valid") is not True
        or analysis.get("operational_errors") != []
        or analysis.get("training_manifest_digest") != _artifact_digest(root / "train_manifest.json")
        or analysis.get("evaluation_manifest_digest") != _artifact_digest(root / "evaluation_manifest.json")
        or not np.isclose(float(analysis.get("formal_projection_seconds", np.nan)), projection, rtol=0, atol=1e-9)
        or analysis.get("formal_projection_executable") is not True
        or train_seconds + eval_seconds + analyze_seconds > NONFORMAL_WALL_CLOCK_CAP_SECONDS
        or projection > FORMAL_WALL_CLOCK_CAP_SECONDS
    ):
        raise ValueError("G38 formal preflight is not executable for this aligned source")
    return _preflight_digests(root)


def _train_replicate(
    *, run_root: Path, source_commit: str, formal: bool, replicate: int,
    configuration: Mapping[str, object],
) -> dict[str, Any]:
    seeds = source.seed_block(replicate, formal=formal)
    configure_runtime(seeds["model"])
    models = source.make_paired_models(roster_env.TRAIN_CAPACITY, initialization_seed=seeds["model"])
    zero_digests = {arm: _state_digest(model) for arm, model in models.items()}
    if len(set(zero_digests.values())) != 1:
        raise RuntimeError("G38 initial arm states diverged")
    folded_rows: dict[str, dict[str, object]] = {}
    for arm, model in models.items():
        _save_checkpoint(
            run_root / _checkpoint_reference(replicate, arm, "zero"),
            source_commit=source_commit, formal=formal, replicate=replicate, arm=arm,
            kind="zero", configuration=configuration, seeds=seeds, model=model,
        )
    zero_folded, zero_source_digest = _save_folded_checkpoint(
        run_root / _checkpoint_reference(replicate, source.FOLD6_ARM, "zero", folded=True),
        source_commit=source_commit, formal=formal, replicate=replicate, kind="zero",
        configuration=configuration, seeds=seeds, pre_fold=models[source.FOLD6_ARM],
    )
    folded_rows["zero"] = {
        "checkpoint": _checkpoint_reference(replicate, source.FOLD6_ARM, "zero", folded=True),
        "state_digest": _state_digest(zero_folded),
        "pre_fold_source_digest": zero_source_digest,
    }
    optimizers = {
        arm: torch.optim.Adam(
            model.fast_actor_parameters() + tuple(model.credit_baselines.parameters()),
            lr=LEARNING_RATE,
        )
        for arm, model in models.items()
    }
    maximum_replay = {arm: 0.0 for arm in source.ARMS}
    lifecycle = {arm: True for arm in source.ARMS}
    finite = {arm: True for arm in source.ARMS}
    fast_steps = {arm: 0 for arm in source.ARMS}
    gradient_audits: dict[str, dict[str, object]] = {}
    initial_equality: dict[str, float] | None = None
    observed_replay_widths = {arm: set() for arm in source.ARMS}
    for update in range(int(configuration["fast_updates"])):
        first = update * int(configuration["num_envs"])
        ids = tuple(range(first, first + int(configuration["num_envs"])))
        ledger_seed = seeds["initial_gradient_probe"] if update == 0 else seeds["training_ledger"]
        action_seed = seeds["initial_gradient_probe"] if update == 0 else seeds["training_action"]
        trajectories = {
            arm: _collect(model, episode_ids=ids, ledger_seed=ledger_seed, action_seed=action_seed)
            for arm, model in models.items()
        }
        for arm, trajectory in trajectories.items():
            observed_replay_widths[arm].add(int(trajectory.observations.shape[-1]))
        if update == 0:
            row = trajectories[source.FOLD6_ARM]
            noise = torch.as_tensor(
                roster_env.make_action_noise(ids, action_seed=action_seed, member_capacity=roster_env.TRAIN_CAPACITY)[0]
            )
            initial_equality = source.forced_initial_equality(
                models[source.FULL10_ARM], models[source.FOLD6_ARM],
                retained_observations=row.observations[0, ..., :source.RETAINED_OBSERVATION_DIM],
                active_mask=row.active_mask[0], critic_state=row.critic_states[0],
                sampling_noise=noise,
            )
            if max(initial_equality.values()) > source.INITIAL_EQUALITY_TOLERANCE:
                raise RuntimeError("G38 forced initial equality failed")
            gradient_audits = {
                arm: source.g38_initial_gradient_audit(model, trajectories[arm], gamma=GAMMA)
                for arm, model in models.items()
            }
            if not all(bool(audit["passed"]) for audit in gradient_audits.values()):
                raise RuntimeError("G38 initial gradient audit failed")
        for arm in source.ARMS:
            lifecycle[arm] &= _lifecycle_valid(trajectories[arm])
        for arm in source.ARMS:
            metrics = optimize_fast_anchor_update(
                models[arm], optimizers[arm], trajectories[arm], device=torch.device("cpu"),
                ppo_passes=int(configuration["ppo_passes"]),
            )
            finite[arm] &= bool(metrics["finite_update"])
            maximum_replay[arm] = max(maximum_replay[arm], _max_replay_error(metrics))
            fast_steps[arm] += int(metrics["optimizer_steps"])
    actor_optimizers: dict[str, torch.optim.Adam] = {}
    critic_optimizers: dict[str, torch.optim.Adam] = {}
    for arm, model in models.items():
        model.begin_direction_balanced_phase()
        actor_optimizers[arm] = torch.optim.Adam(model.full_actor_parameters(), lr=LEARNING_RATE)
        critic_optimizers[arm] = torch.optim.Adam(model.critic_parameters(), lr=LEARNING_RATE)
    actor_steps = {arm: 0 for arm in source.ARMS}
    critic_steps = {arm: 0 for arm in source.ARMS}
    for update in range(int(configuration["return_to_go_updates"])):
        first = (int(configuration["fast_updates"]) + update) * int(configuration["num_envs"])
        ids = tuple(range(first, first + int(configuration["num_envs"])))
        trajectories = {
            arm: _collect(
                model, episode_ids=ids, ledger_seed=seeds["training_ledger"],
                action_seed=seeds["training_action"],
            )
            for arm, model in models.items()
        }
        for arm, trajectory in trajectories.items():
            observed_replay_widths[arm].add(int(trajectory.observations.shape[-1]))
        for arm in source.ARMS:
            lifecycle[arm] &= _lifecycle_valid(trajectories[arm])
        for arm in source.ARMS:
            metrics = optimize_return_to_go_direction_balanced_update(
                models[arm], actor_optimizers[arm], critic_optimizers[arm], trajectories[arm],
                device=torch.device("cpu"), ppo_passes=int(configuration["ppo_passes"]),
                gamma=GAMMA,
            )
            finite[arm] &= bool(metrics["finite_update"])
            maximum_replay[arm] = max(maximum_replay[arm], _max_replay_error(metrics))
            actor_steps[arm] += int(configuration["ppo_passes"])
            critic_steps[arm] += int(configuration["ppo_passes"])
    source.assert_parameter_match(
        models[source.FULL10_ARM], models[source.FOLD6_ARM], require_byte_identity=False
    )
    arms: dict[str, dict[str, object]] = {}
    for arm, model in models.items():
        _save_checkpoint(
            run_root / _checkpoint_reference(replicate, arm, "final"),
            source_commit=source_commit, formal=formal, replicate=replicate, arm=arm,
            kind="final", configuration=configuration, seeds=seeds, model=model,
        )
        arms[arm] = {
            "input_mode": model.input_mode,
            "finite_updates": finite[arm],
            "lifecycle_contract_valid": lifecycle[arm],
            "maximum_replay_error": maximum_replay[arm],
            "actual_history_read_counts": (
                dict(model.actual_history_read_counts)
                if arm == source.FOLD6_ARM
                else None
            ),
            "stored_replay_observation_width": (
                next(iter(observed_replay_widths[arm]))
                if len(observed_replay_widths[arm]) == 1
                else None
            ),
            "completed_fast_updates": int(configuration["fast_updates"]),
            "completed_return_to_go_updates": int(configuration["return_to_go_updates"]),
            "fast_optimizer_steps": fast_steps[arm],
            "return_to_go_actor_optimizer_steps": actor_steps[arm],
            "return_to_go_critic_optimizer_steps": critic_steps[arm],
            "total_optimizer_steps": fast_steps[arm] + actor_steps[arm] + critic_steps[arm],
            "zero_checkpoint": _checkpoint_reference(replicate, arm, "zero"),
            "final_checkpoint": _checkpoint_reference(replicate, arm, "final"),
            "zero_state_digest": zero_digests[arm],
            "final_state_digest": _state_digest(model),
        }
    final_folded, final_source_digest = _save_folded_checkpoint(
        run_root / _checkpoint_reference(replicate, source.FOLD6_ARM, "final", folded=True),
        source_commit=source_commit, formal=formal, replicate=replicate, kind="final",
        configuration=configuration, seeds=seeds, pre_fold=models[source.FOLD6_ARM],
    )
    folded_rows["final"] = {
        "checkpoint": _checkpoint_reference(replicate, source.FOLD6_ARM, "final", folded=True),
        "state_digest": _state_digest(final_folded),
        "pre_fold_source_digest": final_source_digest,
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
        "raw_input_inventory": source.raw_input_inventory(models[source.FULL10_ARM]),
        "forced_initial_equality_max_errors": initial_equality,
        "initial_gradient_audits": gradient_audits,
        "arms": arms,
        "folded_checkpoints": folded_rows,
    }


def train(
    *, run_root: Path, source_commit: str, formal: bool,
    authorization_token: str | None, preflight_root: Path | None = None,
    alignment_disposition: str | None = None, aligned_source_commit: str | None = None,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G38 training requires an integrated source commit")
    preflight_digests: dict[str, str] | None = None
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("G38 formal authorization token mismatch")
        preflight_digests = _validate_formal_preflight(
            preflight_root, source_commit=source_commit,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
        )
    elif any(
        value is not None
        for value in (authorization_token, preflight_root, alignment_disposition, aligned_source_commit)
    ):
        raise ValueError("G38 nonformal training cannot carry formal authority")
    started = time.perf_counter()
    configuration = _configuration(formal=formal)
    configure_runtime(source.bootstrap_seed(formal=formal))
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "checkpoints").mkdir(exist_ok=True)
    rows = [
        _train_replicate(
            run_root=run_root, source_commit=source_commit, formal=formal,
            replicate=replicate, configuration=configuration,
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
        "alignment_audit_id": ALIGNMENT_AUDIT_ID if formal else None,
        "alignment_disposition": alignment_disposition,
        "aligned_source_commit": aligned_source_commit,
        "preflight_root": str(Path(preflight_root).resolve()) if preflight_root is not None else None,
        "preflight_artifact_digests": preflight_digests,
        "runtime": _runtime_identity(),
        "configuration": configuration,
        "source_controls": source.source_controls(),
        "stage_wall_time_seconds": time.perf_counter() - started,
        "replicate_results": rows,
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _cell_contract(name: str) -> dict[str, object]:
    contracts = {
        ZERO_RANDOM_DET: {"checkpoint": "zero", "process": "random", "deterministic": True},
        FINAL_FIXED_DET: {"checkpoint": "final", "process": "fixed", "deterministic": True},
        FINAL_FIXED_STOCH: {"checkpoint": "final", "process": "fixed", "deterministic": False},
        FINAL_RANDOM_DET: {"checkpoint": "final", "process": "random", "deterministic": True},
        FINAL_RANDOM_STOCH: {"checkpoint": "final", "process": "random", "deterministic": False},
    }
    if name not in contracts:
        raise ValueError("G38 unknown evaluation cell")
    return contracts[name]


def _source_inventory(
    *, replicate: int, capacity: int, episode_count: int, formal: bool,
) -> tuple[tuple[g34.RandomProcessLedger, ...], dict[str, object]]:
    processes = source.make_process_ledgers(
        replicate=replicate, capacity=capacity, episode_count=episode_count, formal=formal
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
                "fixed_expected_roster_sizes": list(row.base.expected_roster_sizes),
                "temporarily_absent": list(row.base.temporarily_absent),
                "fresh_join": list(row.base.fresh_join),
                "terminal_leave": list(row.base.terminal_leave),
                "signature": repr(row.signature),
            }
            for row in processes
        ],
    }


def _direct_source_validation(processes: Sequence[g34.RandomProcessLedger]) -> bool:
    try:
        for row in processes:
            row.validate()
        loads = np.linspace(0.30, 0.70, 101, dtype=np.float64)[:, None]
        mixes = np.linspace(0.25, 0.75, 101, dtype=np.float64)[None, :]
        effort = 0.5 * (1.0 + np.tanh(2.0 * loads - 1.0))
        mix_action = 0.5 * (1.0 + np.tanh(2.0 * mixes - 1.0))
        witness = float(
            np.min(
                1.0
                - 0.5
                * (
                    np.abs(effort * mix_action / (loads * mixes) - 1.0)
                    + np.abs(
                        effort * (1.0 - mix_action)
                        / (loads * (1.0 - mixes))
                        - 1.0
                    )
                )
            )
        )
        return bool(
            witness >= CONSTRUCTIVE_WITNESS_FLOOR
            and len({row.signature for row in processes}) == len(processes)
            and all(min(row.expected_roster_sizes) > 0 for row in processes)
        )
    except (TypeError, ValueError):
        return False


def _model_cell(
    *, replicate: int, capacity: int, arm: str, name: str,
    pre_fold: source.G38FoldableMatchedCSPolicy,
    deployed: source.G38FoldableMatchedCSPolicy,
    processes: Sequence[g34.RandomProcessLedger], action_seed: int,
) -> dict[str, object]:
    contract = _cell_contract(name)
    before = _state_digest(deployed)
    if arm == source.FULL10_ARM:
        episodes, lifecycle_valid = g34.evaluate_model(
            deployed, processes=processes, action_seed=action_seed,
            process_kind=str(contract["process"]), deterministic=bool(contract["deterministic"]),
        )
        fold_audit = None
    else:
        episodes, lifecycle_valid, fold_audit = source.verify_g38_fold_equivalence(
            pre_fold, deployed, processes=processes, action_seed=action_seed,
            process_kind=str(contract["process"]), deterministic=bool(contract["deterministic"]),
        )
    return {
        "replicate": replicate,
        "capacity": capacity,
        "arm": arm,
        "cell": name,
        **contract,
        "optimizer_steps": 0,
        "state_before": before,
        "state_after": _state_digest(deployed),
        "pre_fold_state_digest": _state_digest(pre_fold) if arm == source.FOLD6_ARM else None,
        "lifecycle_valid": lifecycle_valid,
        "fold_equivalence": fold_audit,
        "episodes": list(episodes),
    }


def _training_identity_errors(run_root: Path, training: Mapping[str, Any]) -> list[str]:
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
        or re.fullmatch(r"[0-9a-f]{40}", str(training.get("source_commit"))) is None
    ):
        errors.append("G38 training identity mismatch")
        return errors
    if formal and (
        training.get("authorization_token") != AUTHORIZATION_TOKEN
        or training.get("alignment_audit_id") != ALIGNMENT_AUDIT_ID
        or training.get("alignment_disposition") != "ALIGNED"
        or training.get("aligned_source_commit") != training.get("source_commit")
        or not isinstance(training.get("preflight_artifact_digests"), dict)
    ):
        errors.append("G38 formal authority binding mismatch")
    if formal and not errors:
        serialized_root = training.get("preflight_root")
        if (
            not isinstance(serialized_root, str)
            or not serialized_root.strip()
            or not Path(serialized_root).is_absolute()
        ):
            errors.append("G38 formal preflight root mismatch")
        else:
            try:
                live_digests = _validate_formal_preflight(
                    Path(serialized_root),
                    source_commit=str(training.get("source_commit")),
                    alignment_disposition=str(training.get("alignment_disposition")),
                    aligned_source_commit=str(training.get("aligned_source_commit")),
                )
                if live_digests != training.get("preflight_artifact_digests"):
                    errors.append("G38 formal preflight digest binding mismatch")
            except (OSError, TypeError, ValueError) as error:
                errors.append(f"G38 formal preflight invalid: {error}")
    if not formal and any(
        training.get(name) is not None
        for name in (
            "authorization_token", "alignment_audit_id", "alignment_disposition",
            "aligned_source_commit", "preflight_root", "preflight_artifact_digests",
        )
    ):
        errors.append("G38 nonformal artifact carried formal authority")
    runtime = training.get("runtime", {})
    if (
        runtime.get("backend") != "cpu"
        or runtime.get("torch_threads") != 1
        or runtime.get("torch") != str(torch.__version__)
    ):
        errors.append("G38 training runtime mismatch")
    try:
        _finite_seconds(training.get("stage_wall_time_seconds"), "training")
    except ValueError as error:
        errors.append(str(error))
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(configuration["replicates"]):
        errors.append("G38 training replicate inventory mismatch")
        return errors
    expected_fast = int(configuration["fast_updates"]) * int(configuration["ppo_passes"])
    expected_rtg = int(configuration["return_to_go_updates"]) * int(configuration["ppo_passes"])
    zero_reads = source.source_controls()["fold6_actual_history_read_counts"]
    for replicate, row in enumerate(rows):
        try:
            if (
                row["replicate"] != replicate
                or row["seeds"] != source.seed_block(replicate, formal=formal)
                or row["paired_collection_before_update"] is not True
                or row["raw_input_inventory"]["only_two_raw_affines"] is not True
                or row["raw_input_inventory"]["member_input_shape"] != [32, 10]
                or row["raw_input_inventory"]["current_readout_shape"] != [2, 10]
                or max(row["forced_initial_equality_max_errors"].values()) > source.INITIAL_EQUALITY_TOLERANCE
            ):
                raise ValueError("G38 paired graph/initialization mismatch")
            for audit in row["initial_gradient_audits"].values():
                if audit.get("passed") is not True:
                    raise ValueError("G38 gradient audit did not pass")
                for affine in ("member_input", "current_readout"):
                    for column in source.REMOVABLE_COLUMNS:
                        gradient = audit[f"{affine}_column_{column}"]
                        if gradient["finite"] is not True or gradient["live"] is not True:
                            raise ValueError("G38 removable-column gradient mismatch")
            for arm in source.ARMS:
                arm_row = row["arms"][arm]
                if (
                    arm_row["finite_updates"] is not True
                    or arm_row["lifecycle_contract_valid"] is not True
                    or (
                        arm == source.FOLD6_ARM
                        and arm_row["actual_history_read_counts"] != zero_reads
                    )
                    or (
                        arm == source.FULL10_ARM
                        and arm_row["actual_history_read_counts"] is not None
                    )
                    or float(arm_row["maximum_replay_error"]) > REPLAY_TOLERANCE
                    or arm_row["stored_replay_observation_width"]
                    != (
                        source.FULL_OBSERVATION_DIM
                        if arm == source.FULL10_ARM
                        else source.RETAINED_OBSERVATION_DIM
                    )
                    or arm_row["fast_optimizer_steps"] != expected_fast
                    or arm_row["return_to_go_actor_optimizer_steps"] != expected_rtg
                    or arm_row["return_to_go_critic_optimizer_steps"] != expected_rtg
                ):
                    raise ValueError("G38 arm exposure mismatch")
            seeds = source.seed_block(replicate, formal=formal)
            loaded: dict[
                tuple[str, str], source.G38FoldableMatchedCSPolicy
            ] = {}
            for arm in source.ARMS:
                for kind in ("zero", "final"):
                    model, _ = _load_checkpoint(
                        run_root / row["arms"][arm][f"{kind}_checkpoint"],
                        source_commit=str(training["source_commit"]),
                        formal=formal,
                        replicate=replicate,
                        arm=arm,
                        kind=kind,
                        configuration=configuration,
                        seeds=seeds,
                        member_capacity=roster_env.TRAIN_CAPACITY,
                    )
                    loaded[(arm, kind)] = model
                    if _state_digest(model) != row["arms"][arm][f"{kind}_state_digest"]:
                        raise ValueError("G38 training checkpoint digest mismatch")
            source.assert_parameter_match(
                loaded[(source.FULL10_ARM, "zero")],
                loaded[(source.FOLD6_ARM, "zero")],
                require_byte_identity=True,
            )
            source.assert_parameter_match(
                loaded[(source.FULL10_ARM, "final")],
                loaded[(source.FOLD6_ARM, "final")],
                require_byte_identity=False,
            )
            for kind in ("zero", "final"):
                pre = loaded[(source.FOLD6_ARM, kind)]
                folded_row = row["folded_checkpoints"][kind]
                folded, payload = _load_checkpoint(
                    run_root / folded_row["checkpoint"],
                    source_commit=str(training["source_commit"]), formal=formal,
                    replicate=replicate, arm=source.FOLD6_ARM, kind=kind,
                    configuration=configuration, seeds=seeds, member_capacity=roster_env.TRAIN_CAPACITY,
                    folded=True,
                )
                if (
                    payload["pre_fold_source_digest"] != _state_digest(pre)
                    or folded_row["pre_fold_source_digest"] != _state_digest(pre)
                    or folded_row["state_digest"] != _state_digest(folded)
                ):
                    raise ValueError("G38 folded checkpoint digest mismatch")
                source.verify_folded_state_copy(pre, folded)
        except (KeyError, TypeError, ValueError, OSError) as error:
            errors.append(str(error))
    return errors


def evaluate(*, run_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    errors = _training_identity_errors(run_root, training)
    if errors:
        raise ValueError("G38 training artifact invalid: " + " | ".join(errors))
    formal = bool(training["formal"])
    configuration = _configuration(formal=formal)
    source_commit = str(training["source_commit"])
    configure_runtime(source.bootstrap_seed(formal=formal))
    cells: list[dict[str, object]] = []
    inventories: list[dict[str, object]] = []
    direct_source_valid = True
    for replicate in range(int(configuration["replicates"])):
        seeds = source.seed_block(replicate, formal=formal)
        for capacity in g34.CAPACITIES:
            processes, inventory = _source_inventory(
                replicate=replicate, capacity=capacity,
                episode_count=int(configuration["evaluation_episodes_per_cell"]), formal=formal,
            )
            inventories.append(inventory)
            direct_source_valid &= _direct_source_validation(processes)
            for arm in source.ARMS:
                arm_row = training["replicate_results"][replicate]["arms"][arm]
                for name in MODEL_CELLS:
                    kind = str(_cell_contract(name)["checkpoint"])
                    pre, _ = _load_checkpoint(
                        run_root / arm_row[f"{kind}_checkpoint"], source_commit=source_commit,
                        formal=formal, replicate=replicate, arm=arm, kind=kind,
                        configuration=configuration, seeds=seeds, member_capacity=capacity,
                    )
                    if arm == source.FOLD6_ARM:
                        folded_row = training["replicate_results"][replicate]["folded_checkpoints"][kind]
                        deployed, payload = _load_checkpoint(
                            run_root / folded_row["checkpoint"], source_commit=source_commit,
                            formal=formal, replicate=replicate, arm=arm, kind=kind,
                            configuration=configuration, seeds=seeds, member_capacity=capacity,
                            folded=True,
                        )
                        if payload["pre_fold_source_digest"] != _state_digest(pre):
                            raise ValueError("G38 evaluation fold source digest mismatch")
                    else:
                        deployed = pre
                    cells.append(
                        _model_cell(
                            replicate=replicate, capacity=capacity, arm=arm, name=name,
                            pre_fold=pre, deployed=deployed, processes=processes,
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
        "aligned_source_commit": training["aligned_source_commit"],
        "preflight_artifact_digests": training["preflight_artifact_digests"],
        "runtime": _runtime_identity(),
        "configuration": configuration,
        "source_controls": source.source_controls(),
        "training_manifest_digest": _artifact_digest(run_root / "train_manifest.json"),
        "stage_wall_time_seconds": time.perf_counter() - started,
        "direct_source_validation": bool(direct_source_valid),
        "source_inventory": inventories,
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def _evaluation_errors(
    run_root: Path, training: Mapping[str, Any], evaluation: Mapping[str, Any]
) -> list[str]:
    errors = _training_identity_errors(run_root, training)
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
        or evaluation.get("configuration") != configuration
        or evaluation.get("source_controls") != source.source_controls()
        or evaluation.get("training_manifest_digest") != _artifact_digest(run_root / "train_manifest.json")
        or evaluation.get("direct_source_validation") is not True
    ):
        errors.append("G38 evaluation identity/source mismatch")
    runtime = evaluation.get("runtime", {})
    if (
        runtime.get("backend") != "cpu"
        or runtime.get("torch_threads") != 1
        or runtime.get("torch") != str(torch.__version__)
    ):
        errors.append("G38 evaluation runtime mismatch")
    try:
        _finite_seconds(evaluation.get("stage_wall_time_seconds"), "evaluation")
    except ValueError as error:
        errors.append(str(error))
    expected_inventories: list[dict[str, object]] = []
    for replicate in range(int(configuration["replicates"])):
        for capacity in g34.CAPACITIES:
            _, inventory = _source_inventory(
                replicate=replicate,
                capacity=capacity,
                episode_count=int(configuration["evaluation_episodes_per_cell"]),
                formal=formal,
            )
            expected_inventories.append(inventory)
    if evaluation.get("source_inventory") != expected_inventories:
        errors.append("G38 source inventory mismatch")
    cells = evaluation.get("cells")
    if not isinstance(cells, list) or len(cells) != int(configuration["total_cells"]):
        errors.append("G38 evaluation cell inventory mismatch")
        return errors
    inventories = {
        (int(row["replicate"]), int(row["capacity"])): row["processes"]
        for row in evaluation.get("source_inventory", [])
    }
    observed: set[tuple[int, int, str, str]] = set()
    for cell in cells:
        try:
            key = (int(cell["replicate"]), int(cell["capacity"]), str(cell["arm"]), str(cell["cell"]))
            if key in observed or key[0] not in range(int(configuration["replicates"])) or key[1] not in g34.CAPACITIES or key[2] not in source.ARMS or key[3] not in MODEL_CELLS:
                raise ValueError("G38 cell identity mismatch")
            observed.add(key)
            contract = _cell_contract(key[3])
            if any(cell.get(name) != value for name, value in contract.items()):
                raise ValueError("G38 cell route mismatch")
            if cell.get("optimizer_steps") != 0 or cell.get("state_before") != cell.get("state_after") or cell.get("lifecycle_valid") is not True:
                raise ValueError("G38 evaluation mutation/lifecycle mismatch")
            kind = str(contract["checkpoint"])
            training_row = training["replicate_results"][key[0]]
            expected_deployed_digest = (
                training_row["folded_checkpoints"][kind]["state_digest"]
                if key[2] == source.FOLD6_ARM
                else training_row["arms"][source.FULL10_ARM][f"{kind}_state_digest"]
            )
            if cell.get("state_before") != expected_deployed_digest:
                raise ValueError("G38 checkpoint-to-cell binding mismatch")
            fold = cell.get("fold_equivalence")
            if key[2] == source.FOLD6_ARM:
                if not isinstance(fold, dict) or fold.get("passed") is not True or fold.get("environment_trajectories_per_episode") != 1:
                    raise ValueError("G38 fold-equivalence mismatch")
                maximum = fold.get("maximum_errors", {})
                exact = fold.get("exact", {})
                expected_maximum = {
                    "pre_tanh_mean",
                    "actions",
                    "prefix_action_sums",
                    "token_log_probability",
                    "reward_trace",
                    "summary",
                }
                expected_exact = {
                    "log_std",
                    "critic_tensors",
                    "value",
                    "inactive_actions",
                    "inactive_likelihoods",
                    "roster_sizes",
                    "membership_edits",
                    "lifecycle",
                    "zero_hidden_carry",
                }
                if (
                    set(maximum) != expected_maximum
                    or set(exact) != expected_exact
                    or not all(value is True for value in exact.values())
                    or fold.get("reward_comparisons")
                    != int(configuration["evaluation_episodes_per_cell"])
                    * roster_env.HORIZON
                    or fold.get("membership_edit_checks")
                    != int(configuration["evaluation_episodes_per_cell"])
                    * roster_env.HORIZON
                    or fold.get("summary_comparisons")
                    != int(configuration["evaluation_episodes_per_cell"]) * 10
                    or any(not np.isfinite(float(value)) or float(value) < 0 for value in maximum.values())
                    or float(maximum["pre_tanh_mean"]) > source.FOLD_MEAN_ACTION_PREFIX_TOLERANCE
                    or float(maximum["actions"]) > source.FOLD_MEAN_ACTION_PREFIX_TOLERANCE
                    or float(maximum["prefix_action_sums"]) > source.FOLD_MEAN_ACTION_PREFIX_TOLERANCE
                    or float(maximum["token_log_probability"]) > source.FOLD_LOG_PROB_TOLERANCE
                    or float(maximum["reward_trace"]) > source.FOLD_MEAN_ACTION_PREFIX_TOLERANCE
                    or float(maximum["summary"]) > source.FOLD_MEAN_ACTION_PREFIX_TOLERANCE
                ):
                    raise ValueError("G38 fold-equivalence evidence mismatch")
                if cell.get("pre_fold_state_digest") != training_row["arms"][source.FOLD6_ARM][f"{kind}_state_digest"]:
                    raise ValueError("G38 pre-fold checkpoint-to-cell binding mismatch")
            elif fold is not None:
                raise ValueError("G38 FULL10 cell carried fold audit")
            episodes = cell["episodes"]
            expected = inventories[(key[0], key[1])]
            if not isinstance(episodes, list) or len(episodes) != int(configuration["evaluation_episodes_per_cell"]):
                raise ValueError("G38 episode inventory mismatch")
            roster_field = "random_expected_roster_sizes" if contract["process"] == "random" else "fixed_expected_roster_sizes"
            for index, episode in enumerate(episodes):
                row = expected[index]
                if (
                    episode.get("local_episode_id") != index
                    or episode.get("episode_id") != row["episode_id"]
                    or episode.get("signature") != row["signature"]
                    or episode.get("event_times") != row["event_times"]
                    or episode.get("event_order") != row["event_order"]
                ):
                    raise ValueError("G38 episode pairing mismatch")
                trace = g34_runner._trace_evidence(episode)
                if (
                    trace["roster_size_trace"] != tuple(row[roster_field])
                    or episode.get("roster_sizes_valid") is not True
                    or not g34_runner._summary_matches_trace(episode, trace)
                ):
                    raise ValueError("G38 trace evidence mismatch")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
    expected_keys = {
        (replicate, capacity, arm, name)
        for replicate in range(int(configuration["replicates"]))
        for capacity in g34.CAPACITIES
        for arm in source.ARMS
        for name in MODEL_CELLS
    }
    if observed != expected_keys:
        errors.append("G38 evaluation cell key set mismatch")
    return errors


def _cell_map(evaluation: Mapping[str, Any]) -> dict[tuple[int, int, str, str], Mapping[str, Any]]:
    return {
        (int(row["replicate"]), int(row["capacity"]), str(row["arm"]), str(row["cell"])): row
        for row in evaluation["cells"]
    }


def _metric_arrays(
    evaluation: Mapping[str, Any], arm: str, cell_name: str, metric: str
) -> dict[int, np.ndarray]:
    cells = _cell_map(evaluation)
    replicates = int(evaluation["configuration"]["replicates"])
    return {
        capacity: np.asarray(
            [
                [
                    g34_runner._trace_evidence(episode)[metric]
                    for episode in cells[(replicate, capacity, arm, cell_name)]["episodes"]
                ]
                for replicate in range(replicates)
            ],
            dtype=np.float64,
        )
        for capacity in g34.CAPACITIES
    }


def _difference(left: Mapping[int, np.ndarray], right: Mapping[int, np.ndarray]) -> dict[int, np.ndarray]:
    return {capacity: left[capacity] - right[capacity] for capacity in left}


def _bootstrap_plan(
    *, formal: bool, replicates: int, episodes: int, repetitions: int,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(source.bootstrap_seed(formal=formal))
    return (
        rng.integers(0, replicates, size=(repetitions, replicates), dtype=np.int16),
        rng.integers(
            0, episodes,
            size=(repetitions, replicates, len(g34.CAPACITIES), episodes),
            dtype=np.int16,
        ),
    )


def _hierarchical_ci(
    values: Mapping[int, np.ndarray], *, capacities: Sequence[int],
    plan: tuple[np.ndarray, np.ndarray],
) -> list[float]:
    return g35_runner._hierarchical_ci(values, capacities=capacities, plan=plan)


def _minimum_replicate_mean(values: Mapping[int, np.ndarray]) -> float:
    return g35_runner._minimum_replicate_mean(values)


def _inclusive_ge(value: float, floor: float) -> bool:
    return bool(value > floor or np.isclose(value, floor, rtol=0.0, atol=1e-12))


def _inclusive_le(value: float, ceiling: float) -> bool:
    return bool(value < ceiling or np.isclose(value, ceiling, rtol=0.0, atol=1e-12))


def _strict_gt(value: float, floor: float) -> bool:
    return bool(value > floor and not np.isclose(value, floor, rtol=0.0, atol=1e-12))


def _arm_access(
    evaluation: Mapping[str, Any], arm: str, plan: tuple[np.ndarray, np.ndarray]
) -> dict[str, object]:
    fixed = _metric_arrays(evaluation, arm, FINAL_FIXED_DET, "utility")
    fixed_stoch = _metric_arrays(evaluation, arm, FINAL_FIXED_STOCH, "utility")
    random = _metric_arrays(evaluation, arm, FINAL_RANDOM_DET, "utility")
    event = _metric_arrays(evaluation, arm, FINAL_RANDOM_DET, "minimum_event_window_utility")
    segment = _metric_arrays(evaluation, arm, FINAL_RANDOM_DET, "minimum_process_segment_utility")
    random_stoch = _metric_arrays(evaluation, arm, FINAL_RANDOM_STOCH, "utility")
    zero = _metric_arrays(evaluation, arm, ZERO_RANDOM_DET, "utility")
    process = _difference(random, fixed)
    gain = _difference(random, zero)
    per_capacity = lambda values: {
        capacity: _hierarchical_ci(values, capacities=(capacity,), plan=plan)
        for capacity in g34.CAPACITIES
    }
    fixed_ci, random_ci, event_ci, segment_ci, process_ci = map(
        per_capacity, (fixed, random, event, segment, process)
    )
    fixed_stoch_ci = _hierarchical_ci(fixed_stoch, capacities=g34.CAPACITIES, plan=plan)
    random_stoch_ci = _hierarchical_ci(random_stoch, capacities=g34.CAPACITIES, plan=plan)
    gain_ci = _hierarchical_ci(gain, capacities=g34.CAPACITIES, plan=plan)
    min_fixed = _minimum_replicate_mean(fixed)
    min_random = _minimum_replicate_mean(random)
    access_pass = (
        all(_inclusive_ge(fixed_ci[c][0], UTILITY_FLOOR) for c in g34.CAPACITIES)
        and _inclusive_ge(fixed_stoch_ci[0], STOCHASTIC_FLOOR)
        and _inclusive_ge(min_fixed, MINIMUM_REPLICATE_FLOOR)
        and all(_inclusive_ge(random_ci[c][0], UTILITY_FLOOR) for c in g34.CAPACITIES)
        and all(_inclusive_ge(event_ci[c][0], EVENT_FLOOR) for c in g34.CAPACITIES)
        and all(_inclusive_ge(segment_ci[c][0], SEGMENT_FLOOR) for c in g34.CAPACITIES)
        and all(_inclusive_ge(process_ci[c][0], PROCESS_MARGIN) for c in g34.CAPACITIES)
        and _inclusive_ge(random_stoch_ci[0], STOCHASTIC_FLOOR)
        and _inclusive_ge(min_random, MINIMUM_REPLICATE_FLOOR)
        and _strict_gt(gain_ci[0], 0.0)
    )
    confident_fail = (
        any(not _inclusive_ge(fixed_ci[c][2], UTILITY_FLOOR) for c in g34.CAPACITIES)
        or not _inclusive_ge(fixed_stoch_ci[2], STOCHASTIC_FLOOR)
        or not _inclusive_ge(min_fixed, MINIMUM_REPLICATE_FLOOR)
        or any(not _inclusive_ge(random_ci[c][2], UTILITY_FLOOR) for c in g34.CAPACITIES)
        or any(not _inclusive_ge(event_ci[c][2], EVENT_FLOOR) for c in g34.CAPACITIES)
        or any(not _inclusive_ge(segment_ci[c][2], SEGMENT_FLOOR) for c in g34.CAPACITIES)
        or any(not _inclusive_ge(process_ci[c][2], PROCESS_MARGIN) for c in g34.CAPACITIES)
        or not _inclusive_ge(random_stoch_ci[2], STOCHASTIC_FLOOR)
        or not _inclusive_ge(min_random, MINIMUM_REPLICATE_FLOOR)
        or _inclusive_le(gain_ci[2], 0.0)
    )
    return {
        "fixed_utility_ci95": fixed_ci,
        "fixed_stochastic_pooled_ci95": fixed_stoch_ci,
        "minimum_fixed_deterministic_replicate_mean": min_fixed,
        "random_utility_ci95": random_ci,
        "random_event_window_ci95": event_ci,
        "random_process_segment_ci95": segment_ci,
        "random_minus_fixed_ci95": process_ci,
        "random_stochastic_pooled_ci95": random_stoch_ci,
        "minimum_random_deterministic_replicate_mean": min_random,
        "learned_gain_ci95": gain_ci,
        "access_pass": bool(access_pass),
        "access_confident_fail": bool(confident_fail),
    }


def _information_comparison(
    evaluation: Mapping[str, Any], plan: tuple[np.ndarray, np.ndarray]
) -> dict[str, object]:
    component_specs = (
        ("fixed_deterministic_utility", FINAL_FIXED_DET, "utility", False),
        ("random_deterministic_utility", FINAL_RANDOM_DET, "utility", False),
        ("fixed_stochastic_utility", FINAL_FIXED_STOCH, "utility", True),
        ("random_stochastic_utility", FINAL_RANDOM_STOCH, "utility", True),
        ("random_event_window", FINAL_RANDOM_DET, "minimum_event_window_utility", False),
        ("random_process_segment", FINAL_RANDOM_DET, "minimum_process_segment_utility", False),
    )
    component_ci: dict[str, object] = {}
    component_ucbs: list[float] = []
    for name, cell, metric, pooled in component_specs:
        delta = _difference(
            _metric_arrays(evaluation, source.FULL10_ARM, cell, metric),
            _metric_arrays(evaluation, source.FOLD6_ARM, cell, metric),
        )
        if pooled:
            ci = _hierarchical_ci(delta, capacities=g34.CAPACITIES, plan=plan)
            component_ci[name] = ci
            component_ucbs.append(ci[2])
        else:
            rows = {
                capacity: _hierarchical_ci(delta, capacities=(capacity,), plan=plan)
                for capacity in g34.CAPACITIES
            }
            component_ci[name] = rows
            component_ucbs.extend(row[2] for row in rows.values())
    primary_values = _difference(
        _metric_arrays(evaluation, source.FULL10_ARM, FINAL_RANDOM_DET, "utility"),
        _metric_arrays(evaluation, source.FOLD6_ARM, FINAL_RANDOM_DET, "utility"),
    )
    primary = _hierarchical_ci(primary_values, capacities=g34.CAPACITIES, plan=plan)
    capacity_primary = {
        capacity: _hierarchical_ci(primary_values, capacities=(capacity,), plan=plan)
        for capacity in g34.CAPACITIES
    }
    noninferior = _inclusive_le(primary[2], INFORMATION_MARGIN) and all(
        _inclusive_le(value, INFORMATION_MARGIN) for value in component_ucbs
    )
    material = _strict_gt(primary[0], INFORMATION_MARGIN) and all(
        _strict_gt(capacity_primary[capacity][0], 0.0)
        for capacity in g34.CAPACITIES
    )
    return {
        "full10_minus_fold6_primary_ci95": primary,
        "full10_minus_fold6_capacity_ci95": capacity_primary,
        "component_ci95": component_ci,
        "six_coordinate_noninferior": bool(noninferior),
        "material_info_advantage": bool(material),
    }


def select_g38_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or (
        bool(metrics["full_access_confident_fail"])
        and bool(metrics["fold_access_confident_fail"])
    ):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics["fold_access_pass"])
        and bool(metrics["six_coordinate_noninferior"])
        and bool(metrics["fold_equivalence_pass"])
    ):
        return SIX_COORDINATE_SUFFICIENT_BRANCH
    if bool(metrics["full_access_pass"]) and (
        bool(metrics["fold_access_confident_fail"])
        or bool(metrics["material_info_advantage"])
    ):
        return FULL_INFORMATION_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def analyze(*, run_root: Path, require_formal: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G38 analysis requires formal artifacts")
    configure_runtime(source.bootstrap_seed(formal=formal))
    errors = _evaluation_errors(run_root, training, evaluation)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        configuration = evaluation["configuration"]
        plan = _bootstrap_plan(
            formal=formal, replicates=int(configuration["replicates"]),
            episodes=int(configuration["evaluation_episodes_per_cell"]),
            repetitions=int(configuration["bootstrap_resamples"]),
        )
        access = {arm: _arm_access(evaluation, arm, plan) for arm in source.ARMS}
        comparison = _information_comparison(evaluation, plan)
        fold_pass = all(
            cell["fold_equivalence"]["passed"] is True
            for cell in evaluation["cells"] if cell["arm"] == source.FOLD6_ARM
        )
        metrics.update(
            {
                "source_valid": evaluation["direct_source_validation"] is True,
                "arm_access": access,
                "full_access_pass": access[source.FULL10_ARM]["access_pass"],
                "fold_access_pass": access[source.FOLD6_ARM]["access_pass"],
                "full_access_confident_fail": access[source.FULL10_ARM]["access_confident_fail"],
                "fold_access_confident_fail": access[source.FOLD6_ARM]["access_confident_fail"],
                "fold_equivalence_pass": bool(fold_pass),
                **comparison,
            }
        )
        metrics["full_information_advantage_subpredicate"] = (
            "FOLD_ACCESS_CONFIDENT_FAIL"
            if metrics["fold_access_confident_fail"]
            else "MATERIAL_INFO_ADVANTAGE"
            if metrics["material_info_advantage"]
            else None
        )
    analysis_seconds = time.perf_counter() - started
    projection: float | None = None
    projection_executable: bool | None = None
    nonformal_total: float | None = None
    if not formal and not errors:
        train_seconds = float(training["stage_wall_time_seconds"])
        eval_seconds = float(evaluation["stage_wall_time_seconds"])
        nonformal_total = train_seconds + eval_seconds + analysis_seconds
        projection = 1.25 * (30.0 * train_seconds + 48.0 * eval_seconds + 40.0 * analysis_seconds)
        projection_executable = (
            nonformal_total <= NONFORMAL_WALL_CLOCK_CAP_SECONDS
            and projection <= FORMAL_WALL_CLOCK_CAP_SECONDS
        )
    if errors:
        branch = INVALID_BRANCH
    elif formal:
        branch = select_g38_result_branch(metrics)
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
        "aligned_source_commit": training.get("aligned_source_commit"),
        "preflight_artifact_digests": training.get("preflight_artifact_digests"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "training_manifest_digest": _artifact_digest(run_root / "train_manifest.json"),
        "evaluation_manifest_digest": _artifact_digest(run_root / "evaluation_manifest.json"),
        "stage_wall_time_seconds": analysis_seconds,
        "nonformal_total_wall_time_seconds": nonformal_total,
        "nonformal_wall_clock_cap_seconds": NONFORMAL_WALL_CLOCK_CAP_SECONDS,
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
            "information_margin": INFORMATION_MARGIN,
        },
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    train(
        run_root=run_root, source_commit=source_commit, formal=False,
        authorization_token=None,
    )
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--alignment-disposition")
    parser.add_argument("--aligned-source-commit")
    args = parser.parse_args()
    if args.stage == "train":
        if args.source_commit is None:
            raise ValueError("G38 train requires --source-commit")
        train(
            run_root=args.run_root, source_commit=args.source_commit, formal=args.formal,
            authorization_token=args.authorization_token, preflight_root=args.preflight_root,
            alignment_disposition=args.alignment_disposition,
            aligned_source_commit=args.aligned_source_commit,
        )
    elif args.stage == "evaluate":
        evaluate(run_root=args.run_root)
    elif args.stage == "analyze":
        analyze(run_root=args.run_root, require_formal=args.formal)
    else:
        if args.source_commit is None:
            raise ValueError("G38 exercise requires --source-commit")
        if args.formal or any(
            value is not None
            for value in (
                args.authorization_token, args.preflight_root,
                args.alignment_disposition, args.aligned_source_commit,
            )
        ):
            raise ValueError("G38 exercise is bounded nonformal only")
        exercise(run_root=args.run_root, source_commit=args.source_commit)


if __name__ == "__main__":
    main()
