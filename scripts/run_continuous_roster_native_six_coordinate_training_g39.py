"""Train, evaluate, and analyze the frozen G39 native-six contract."""

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

from ha_ctse_process import continuous_roster_native_six_coordinate_training_g39 as source
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    optimize_fast_anchor_update,
)
from ha_ctse_process.return_to_go_direction_balanced_full_actor_g31 import (
    optimize_return_to_go_direction_balanced_update,
)
from scripts import run_continuous_roster_random_process_g34 as g34_runner
from scripts import run_continuous_roster_reactive_reduction_g35 as g35_runner
from scripts import run_continuous_roster_six_coordinate_cs_g38 as g38_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = "CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_FORMAL_AUTHORIZATION_V1"
ALIGNMENT_AUDIT_ID = "CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_CODE_SCIENCE_ALIGNMENT_AUDIT"

INVALID_BRANCH = "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_TRAINING_G39"
SOURCE_FAILURE_BRANCH = "SOURCE_OR_COMMON_ACCESS_FAILURE_G39"
NATIVE_SUFFICIENT_BRANCH = "NATIVE_SIX_COORDINATE_TRAINING_SUFFICIENT_G39"
CONST_ADVANTAGE_BRANCH = "CONSTANT_OVERPARAMETERIZED_TRAINING_ADVANTAGE_G39"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_NATIVE_SIX_TRAINING_G39"
NONFORMAL_BRANCH = "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_TRAINING_G39_EXERCISE_COMPLETE"
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
TRAINING_MARGIN = 0.05
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
FORMAL_WALL_CLOCK_CAP_SECONDS = 28_800.0

FORMAL_REPLICATES = 3
FORMAL_FAST_UPDATES = 100
FORMAL_RETURN_TO_GO_UPDATES = 100
FORMAL_NUM_ENVS = 8
FORMAL_PPO_PASSES = 2
FORMAL_EVAL_EPISODES = 64
FORMAL_BOOTSTRAP_REPETITIONS = 10_000

EXERCISE_REPLICATES = 1
EXERCISE_FAST_UPDATES = 10
EXERCISE_RETURN_TO_GO_UPDATES = 10
EXERCISE_NUM_ENVS = 8
EXERCISE_PPO_PASSES = 2
EXERCISE_EVAL_EPISODES = 6
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
    training = len(source.ARMS) * replicates * (fast + rtg) * envs * g32.HORIZON
    evaluation = replicates * cells_per_replicate * episodes * g32.HORIZON
    optimizer_steps = len(source.ARMS) * replicates * (fast * passes + 2 * rtg * passes)
    return {
        **counts,
        "arms": list(source.ARMS),
        "stored_training_observation_dim": 6,
        "const_raw_input_affines": ["member_input:Linear(10,32)", "current_readout:Linear(10,2)"],
        "native_raw_input_affines": ["member_input:Linear(6,32)", "current_readout:Linear(6,2)"],
        "removed_actor_weights": 136,
        "critic_state_dim": g32.CRITIC_STATE_DIM,
        "action_dim": g32.ACTION_DIM,
        "actor_width": source.HIDDEN_DIM,
        "training_capacity": g32.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "gamma": GAMMA,
        "learning_rate": LEARNING_RATE,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)",
        "gradient_clipping": "none",
        "minibatches": "none",
        "checkpoint_selection": "final_only",
        "episode_exclusions": "none",
        "cells_per_arm_capacity": len(MODEL_CELLS),
        "cells_per_replicate": cells_per_replicate,
        "total_cells": replicates * cells_per_replicate,
        "training_transitions": training,
        "evaluation_transitions": evaluation,
        "total_real_transitions": training + evaluation,
        "optimizer_steps": optimizer_steps,
        "evaluation_optimizer_steps": 0,
        "paired_collection_before_update": True,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }


def _checkpoint_reference(replicate: int, arm: str, *, folded: bool = False) -> str:
    suffix = "_folded6" if folded else ""
    return f"checkpoints/replicate_{replicate}_{arm.lower()}_final{suffix}.pt"


def _checkpoint_payload(
    *, source_commit: str, formal: bool, replicate: int, arm: str,
    configuration: Mapping[str, object], seeds: Mapping[str, int], folded: bool,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": source_commit,
        "formal": formal,
        "replicate": replicate,
        "arm": arm,
        "kind": "final",
        "folded": folded,
        "completed_fast_updates": int(configuration["fast_updates"]),
        "completed_return_to_go_updates": int(configuration["return_to_go_updates"]),
        "configuration": dict(configuration),
        "seeds": dict(seeds),
    }


def _save_checkpoint(
    path: Path, *, source_commit: str, formal: bool, replicate: int, arm: str,
    configuration: Mapping[str, object], seeds: Mapping[str, int], model: source.G39Policy,
    folded: bool = False, pre_fold_digest: str | None = None,
) -> None:
    payload = _checkpoint_payload(
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        arm=arm,
        configuration=configuration,
        seeds=seeds,
        folded=folded,
    )
    payload.update(
        {
            "input_mode": model.input_mode,
            "pre_fold_source_digest": pre_fold_digest,
            "optimizer_steps_after_fold": 0 if folded else None,
            "model_state": model.state_dict(),
        }
    )
    torch.save(payload, path)


def _load_checkpoint(
    path: Path, *, source_commit: str, formal: bool, replicate: int, arm: str,
    configuration: Mapping[str, object], seeds: Mapping[str, int], member_capacity: int,
    folded: bool = False,
) -> tuple[source.G39Policy, dict[str, Any]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    expected = _checkpoint_payload(
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        arm=arm,
        configuration=configuration,
        seeds=seeds,
        folded=folded,
    )
    if not isinstance(payload, dict) or any(payload.get(name) != value for name, value in expected.items()):
        raise ValueError("G39 checkpoint identity mismatch")
    configure_runtime(int(seeds["model"]))
    if folded:
        model: source.G39Policy = source.g38.make_model(
            member_capacity,
            input_mode=source.g38.FOLDED6_INPUT,
            initialization_seed=int(seeds["model"]),
        )
    else:
        model = source.make_paired_models(
            member_capacity, initialization_seed=int(seeds["model"])
        )[arm]
    state = payload.get("model_state")
    if not isinstance(state, dict):
        raise ValueError("G39 checkpoint state missing")
    model.load_state_dict(state, strict=True)
    return model, payload


def _optimizer(model: torch.nn.Module, parameters: Sequence[torch.nn.Parameter]) -> torch.optim.Adam:
    del model
    return torch.optim.Adam(
        parameters,
        lr=LEARNING_RATE,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
    )


def _optimizers_empty_and_separate(optimizers: Mapping[str, torch.optim.Adam]) -> bool:
    rows = tuple(optimizers.values())
    return bool(
        all(optimizer.state == {} for optimizer in rows)
        and len({id(optimizer) for optimizer in rows}) == len(rows)
        and len({id(optimizer.state) for optimizer in rows}) == len(rows)
    )


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
    model: source.G39Policy, *, episode_ids: tuple[int, ...], ledger_seed: int,
    action_seed: int,
) -> Any:
    raw = source.collect_g39_trajectory(
        model,
        episode_ids=episode_ids,
        ledger_seed=int(ledger_seed),
        action_seed=int(action_seed),
        device=torch.device("cpu"),
    )
    return attach_credit_baselines(model, raw, device=torch.device("cpu"))


def _max_replay_error(metrics: Mapping[str, float]) -> float:
    return g35_runner._max_replay_error(metrics)


def _train_replicate(
    *, run_root: Path, source_commit: str, formal: bool, replicate: int,
    configuration: Mapping[str, object],
) -> dict[str, Any]:
    seeds = source.seed_block(replicate, formal=formal)
    configure_runtime(seeds["model"])
    models = source.make_paired_models(g32.TRAIN_CAPACITY, initialization_seed=seeds["model"])
    source.assert_no_shared_state(models[source.CONST10_ARM], models[source.NATIVE6_ARM])
    zero_const_folded = source.fold_const_checkpoint(models[source.CONST10_ARM])
    zero_digests = {arm: _state_digest(model) for arm, model in models.items()}
    zero_function_digest_equal = _state_digest(zero_const_folded) == zero_digests[source.NATIVE6_ARM]
    if not zero_function_digest_equal:
        raise RuntimeError("G39 zero function checkpoints are not bitwise equal")

    fast_optimizers = {
        arm: _optimizer(
            model,
            model.fast_actor_parameters() + tuple(model.credit_baselines.parameters()),
        )
        for arm, model in models.items()
    }
    initial_fast_states = _optimizers_empty_and_separate(fast_optimizers)
    if not initial_fast_states:
        raise RuntimeError("G39 initial fast Adam states are not empty and separate")
    maximum_replay = {arm: 0.0 for arm in source.ARMS}
    lifecycle = {arm: True for arm in source.ARMS}
    finite = {arm: True for arm in source.ARMS}
    fast_steps = {arm: 0 for arm in source.ARMS}
    replay_widths = {arm: set() for arm in source.ARMS}
    initial_forward: dict[str, object] | None = None
    initial_trajectory: dict[str, object] | None = None
    gradient_audit: dict[str, object] | None = None
    collection_before_update = True

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
            replay_widths[arm].add(int(trajectory.observations.shape[-1]))
            lifecycle[arm] &= _lifecycle_valid(trajectory)
        if update == 0:
            const_row = trajectories[source.CONST10_ARM]
            native_row = trajectories[source.NATIVE6_ARM]
            initial_trajectory = source.initial_trajectory_match(const_row, native_row)
            noise = torch.as_tensor(
                g32.make_action_noise(ids, action_seed=action_seed, member_capacity=g32.TRAIN_CAPACITY)[0]
            )
            initial_forward = source.initial_forward_match(
                models[source.CONST10_ARM],
                models[source.NATIVE6_ARM],
                observations=const_row.observations[0],
                active_mask=const_row.active_mask[0],
                critic_state=const_row.critic_states[0],
                sampling_noise=noise,
            )
            gradient_audit = source.initial_gradient_audit(
                models[source.CONST10_ARM],
                models[source.NATIVE6_ARM],
                const_row,
                native_row,
                gamma=GAMMA,
            )
            if not (initial_forward["passed"] and initial_trajectory["passed"] and gradient_audit["passed"]):
                raise RuntimeError("G39 initial function/trajectory/gradient gate failed")
        for arm in source.ARMS:
            metrics = optimize_fast_anchor_update(
                models[arm],
                fast_optimizers[arm],
                trajectories[arm],
                device=torch.device("cpu"),
                ppo_passes=int(configuration["ppo_passes"]),
            )
            finite[arm] &= bool(metrics["finite_update"])
            maximum_replay[arm] = max(maximum_replay[arm], _max_replay_error(metrics))
            fast_steps[arm] += int(metrics["optimizer_steps"])

    fast_state_discarded = all(bool(optimizer.state) for optimizer in fast_optimizers.values())
    del fast_optimizers
    actor_optimizers: dict[str, torch.optim.Adam] = {}
    critic_optimizers: dict[str, torch.optim.Adam] = {}
    for arm, model in models.items():
        model.begin_direction_balanced_phase()
        actor_optimizers[arm] = _optimizer(model, model.full_actor_parameters())
        critic_optimizers[arm] = _optimizer(model, model.critic_parameters())
    direction_optimizers: dict[str, torch.optim.Adam] = {
        **{f"{arm}:actor": optimizer for arm, optimizer in actor_optimizers.items()},
        **{f"{arm}:critic": optimizer for arm, optimizer in critic_optimizers.items()},
    }
    fresh_direction_states = _optimizers_empty_and_separate(direction_optimizers)
    if not fresh_direction_states:
        raise RuntimeError("G39 direction-balanced Adam states are not fresh and separate")
    actor_steps = {arm: 0 for arm in source.ARMS}
    critic_steps = {arm: 0 for arm in source.ARMS}
    for update in range(int(configuration["return_to_go_updates"])):
        first = (int(configuration["fast_updates"]) + update) * int(configuration["num_envs"])
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
        for arm, trajectory in trajectories.items():
            replay_widths[arm].add(int(trajectory.observations.shape[-1]))
            lifecycle[arm] &= _lifecycle_valid(trajectory)
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
            maximum_replay[arm] = max(maximum_replay[arm], _max_replay_error(metrics))
            actor_steps[arm] += int(configuration["ppo_passes"])
            critic_steps[arm] += int(configuration["ppo_passes"])

    arms: dict[str, dict[str, object]] = {}
    for arm, model in models.items():
        path = run_root / _checkpoint_reference(replicate, arm)
        _save_checkpoint(
            path,
            source_commit=source_commit,
            formal=formal,
            replicate=replicate,
            arm=arm,
            configuration=configuration,
            seeds=seeds,
            model=model,
        )
        arms[arm] = {
            "input_mode": model.input_mode,
            "finite_updates": finite[arm],
            "lifecycle_contract_valid": lifecycle[arm],
            "maximum_replay_error": maximum_replay[arm],
            "stored_replay_observation_width": next(iter(replay_widths[arm])) if len(replay_widths[arm]) == 1 else None,
            "completed_fast_updates": int(configuration["fast_updates"]),
            "completed_return_to_go_updates": int(configuration["return_to_go_updates"]),
            "fast_optimizer_steps": fast_steps[arm],
            "return_to_go_actor_optimizer_steps": actor_steps[arm],
            "return_to_go_critic_optimizer_steps": critic_steps[arm],
            "total_optimizer_steps": fast_steps[arm] + actor_steps[arm] + critic_steps[arm],
            "zero_state_digest": zero_digests[arm],
            "final_checkpoint": _checkpoint_reference(replicate, arm),
            "final_state_digest": _state_digest(model),
        }
    folded = source.fold_const_checkpoint(models[source.CONST10_ARM])
    folded_path = run_root / _checkpoint_reference(replicate, source.CONST10_ARM, folded=True)
    pre_fold_digest = _state_digest(models[source.CONST10_ARM])
    _save_checkpoint(
        folded_path,
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        arm=source.CONST10_ARM,
        configuration=configuration,
        seeds=seeds,
        model=folded,
        folded=True,
        pre_fold_digest=pre_fold_digest,
    )
    assert initial_forward is not None and initial_trajectory is not None and gradient_audit is not None
    return {
        "replicate": replicate,
        "seeds": seeds,
        "paired_collection_before_update": collection_before_update,
        "raw_input_inventory": source.raw_input_inventory(models),
        "zero_function_digest_equal": zero_function_digest_equal,
        "initial_forward_match": initial_forward,
        "initial_trajectory_match": initial_trajectory,
        "initial_gradient_audit": gradient_audit,
        "initial_fast_optimizer_states_empty_separate": initial_fast_states,
        "fast_optimizer_states_discarded": fast_state_discarded,
        "direction_optimizer_states_fresh_empty_separate": fresh_direction_states,
        "arms": arms,
        "folded_const_final": {
            "checkpoint": _checkpoint_reference(replicate, source.CONST10_ARM, folded=True),
            "state_digest": _state_digest(folded),
            "pre_fold_source_digest": pre_fold_digest,
            "optimizer_steps_after_fold": 0,
        },
    }


def _finite_seconds(value: object, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not np.isfinite(value) or value < 0:
        raise ValueError(f"G39 {name} timing invalid")
    return float(value)


def _preflight_digests(root: Path) -> dict[str, str]:
    return {
        "training": _artifact_digest(root / "train_manifest.json"),
        "evaluation": _artifact_digest(root / "evaluation_manifest.json"),
        "analysis": _artifact_digest(root / "analysis_result.json"),
    }


def _validate_formal_preflight(
    preflight_root: Path | None, *, source_commit: str,
    alignment_disposition: str | None, aligned_source_commit: str | None,
) -> dict[str, str]:
    if preflight_root is None:
        raise ValueError("formal G39 execution requires a bounded preflight root")
    if alignment_disposition != "ALIGNED" or aligned_source_commit != source_commit:
        raise ValueError("formal G39 execution requires ALIGNED same-source audit")
    root = Path(preflight_root)
    training = _read_json(root / "train_manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    analysis = _read_json(root / "analysis_result.json")
    artifact_errors = _evaluation_errors(root, training, evaluation)
    if artifact_errors:
        raise ValueError(
            "G39 formal preflight artifacts are invalid: "
            + " | ".join(artifact_errors)
        )
    expected = _configuration(formal=False)
    train_seconds = _finite_seconds(training.get("stage_wall_time_seconds"), "preflight train")
    eval_seconds = _finite_seconds(evaluation.get("stage_wall_time_seconds"), "preflight evaluate")
    analyze_seconds = _finite_seconds(analysis.get("stage_wall_time_seconds"), "preflight analyze")
    projection = 1.25 * (30.0 * train_seconds + 32.0 * eval_seconds + 40.0 * analyze_seconds)
    if (
        training.get("formal") is not False
        or evaluation.get("formal") is not False
        or analysis.get("formal") is not False
        or training.get("source_commit") != source_commit
        or evaluation.get("source_commit") != source_commit
        or analysis.get("source_commit") != source_commit
        or training.get("configuration") != expected
        or evaluation.get("configuration") != expected
        or analysis.get("algorithm") != ALGORITHM_ID
        or analysis.get("source_id") != source.SOURCE_ID
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
        raise ValueError("G39 formal preflight is not executable for this aligned source")
    return _preflight_digests(root)


def train(
    *, run_root: Path, source_commit: str, formal: bool,
    authorization_token: str | None, preflight_root: Path | None = None,
    alignment_disposition: str | None = None, aligned_source_commit: str | None = None,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G39 training requires an integrated source commit")
    preflight_digests: dict[str, str] | None = None
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("G39 formal authorization token mismatch")
        preflight_digests = _validate_formal_preflight(
            preflight_root,
            source_commit=source_commit,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
        )
    elif any(value is not None for value in (authorization_token, preflight_root, alignment_disposition, aligned_source_commit)):
        raise ValueError("G39 nonformal training cannot carry formal authority")
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
        raise ValueError("G39 unknown evaluation cell")
    return contracts[name]


def _source_inventory(
    *, replicate: int, capacity: int, episode_count: int, formal: bool,
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
                "fixed_expected_roster_sizes": list(row.base.expected_roster_sizes),
                "signature": repr(row.signature),
            }
            for row in processes
        ],
    }


def _load_final_models(
    *, run_root: Path, training: Mapping[str, Any], replicate: int, capacity: int,
) -> tuple[dict[str, source.G39Policy], source.G39Policy]:
    formal = bool(training["formal"])
    configuration = training["configuration"]
    seeds = source.seed_block(replicate, formal=formal)
    models: dict[str, source.G39Policy] = {}
    row = training["replicate_results"][replicate]
    for arm in source.ARMS:
        model, _ = _load_checkpoint(
            run_root / row["arms"][arm]["final_checkpoint"],
            source_commit=str(training["source_commit"]),
            formal=formal,
            replicate=replicate,
            arm=arm,
            configuration=configuration,
            seeds=seeds,
            member_capacity=capacity,
        )
        models[arm] = model
    folded, payload = _load_checkpoint(
        run_root / row["folded_const_final"]["checkpoint"],
        source_commit=str(training["source_commit"]),
        formal=formal,
        replicate=replicate,
        arm=source.CONST10_ARM,
        configuration=configuration,
        seeds=seeds,
        member_capacity=capacity,
        folded=True,
    )
    if payload.get("pre_fold_source_digest") != _state_digest(models[source.CONST10_ARM]):
        raise ValueError("G39 folded CONST source binding mismatch")
    return models, folded


def _training_errors(run_root: Path, training: Mapping[str, Any]) -> list[str]:
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
        return ["G39 training identity mismatch"]
    if formal and (
        training.get("authorization_token") != AUTHORIZATION_TOKEN
        or training.get("alignment_audit_id") != ALIGNMENT_AUDIT_ID
        or training.get("alignment_disposition") != "ALIGNED"
        or training.get("aligned_source_commit") != training.get("source_commit")
        or not isinstance(training.get("preflight_artifact_digests"), dict)
    ):
        errors.append("G39 formal authority binding mismatch")
    if formal and not errors:
        serialized_root = training.get("preflight_root")
        if (
            not isinstance(serialized_root, str)
            or not serialized_root.strip()
            or not Path(serialized_root).is_absolute()
        ):
            errors.append("G39 formal preflight root mismatch")
        else:
            try:
                live_digests = _validate_formal_preflight(
                    Path(serialized_root),
                    source_commit=str(training.get("source_commit")),
                    alignment_disposition=str(training.get("alignment_disposition")),
                    aligned_source_commit=str(training.get("aligned_source_commit")),
                )
                if live_digests != training.get("preflight_artifact_digests"):
                    errors.append("G39 formal preflight digest binding mismatch")
            except (OSError, TypeError, ValueError) as error:
                errors.append(f"G39 formal preflight invalid: {error}")
    if not formal and any(
        training.get(name) is not None
        for name in (
            "authorization_token", "alignment_audit_id", "alignment_disposition",
            "aligned_source_commit", "preflight_root", "preflight_artifact_digests",
        )
    ):
        errors.append("G39 nonformal artifact carried formal authority")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(configuration["replicates"]):
        return errors + ["G39 training replicate inventory mismatch"]
    expected_fast = int(configuration["fast_updates"]) * int(configuration["ppo_passes"])
    expected_rtg = int(configuration["return_to_go_updates"]) * int(configuration["ppo_passes"])
    for replicate, row in enumerate(rows):
        try:
            inventory = row["raw_input_inventory"]
            if (
                row["replicate"] != replicate
                or row["seeds"] != source.seed_block(replicate, formal=formal)
                or row["paired_collection_before_update"] is not True
                or row["zero_function_digest_equal"] is not True
                or row["initial_forward_match"]["passed"] is not True
                or row["initial_trajectory_match"]["passed"] is not True
                or row["initial_gradient_audit"]["passed"] is not True
                or row["initial_fast_optimizer_states_empty_separate"] is not True
                or row["fast_optimizer_states_discarded"] is not True
                or row["direction_optimizer_states_fresh_empty_separate"] is not True
                or inventory["const_member_input_shape"] != [32, 10]
                or inventory["native_member_input_shape"] != [32, 6]
                or inventory["parameter_delta"] != 136
            ):
                raise ValueError("G39 initialization/training gate mismatch")
            for arm in source.ARMS:
                arm_row = row["arms"][arm]
                if (
                    arm_row["finite_updates"] is not True
                    or arm_row["lifecycle_contract_valid"] is not True
                    or arm_row["stored_replay_observation_width"] != 6
                    or float(arm_row["maximum_replay_error"]) > REPLAY_TOLERANCE
                    or arm_row["fast_optimizer_steps"] != expected_fast
                    or arm_row["return_to_go_actor_optimizer_steps"] != expected_rtg
                    or arm_row["return_to_go_critic_optimizer_steps"] != expected_rtg
                ):
                    raise ValueError("G39 arm exposure mismatch")
                loaded, _ = _load_checkpoint(
                    run_root / arm_row["final_checkpoint"],
                    source_commit=str(training["source_commit"]),
                    formal=formal,
                    replicate=replicate,
                    arm=arm,
                    configuration=configuration,
                    seeds=row["seeds"],
                    member_capacity=g32.TRAIN_CAPACITY,
                )
                if _state_digest(loaded) != arm_row["final_state_digest"]:
                    raise ValueError("G39 final checkpoint digest mismatch")
            folded_row = row["folded_const_final"]
            folded, payload = _load_checkpoint(
                run_root / folded_row["checkpoint"],
                source_commit=str(training["source_commit"]),
                formal=formal,
                replicate=replicate,
                arm=source.CONST10_ARM,
                configuration=configuration,
                seeds=row["seeds"],
                member_capacity=g32.TRAIN_CAPACITY,
                folded=True,
            )
            if (
                folded_row["optimizer_steps_after_fold"] != 0
                or payload.get("optimizer_steps_after_fold") != 0
                or payload.get("pre_fold_source_digest")
                != row["arms"][source.CONST10_ARM]["final_state_digest"]
                or folded_row["pre_fold_source_digest"]
                != row["arms"][source.CONST10_ARM]["final_state_digest"]
                or _state_digest(folded) != folded_row["state_digest"]
            ):
                raise ValueError("G39 folded final checkpoint binding mismatch")
        except (KeyError, OSError, TypeError, ValueError) as error:
            errors.append(str(error))
    return errors


def evaluate(*, run_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    errors = _training_errors(run_root, training)
    if errors:
        raise ValueError("G39 training artifact invalid: " + " | ".join(errors))
    formal = bool(training["formal"])
    configuration = _configuration(formal=formal)
    configure_runtime(source.bootstrap_seed(formal=formal))
    cells: list[dict[str, object]] = []
    inventories: list[dict[str, object]] = []
    direct_source_valid = True
    for replicate in range(int(configuration["replicates"])):
        seeds = source.seed_block(replicate, formal=formal)
        for capacity in g34.CAPACITIES:
            processes, inventory = _source_inventory(
                replicate=replicate,
                capacity=capacity,
                episode_count=int(configuration["evaluation_episodes_per_cell"]),
                formal=formal,
            )
            inventories.append(inventory)
            direct_source_valid &= g38_runner._direct_source_validation(processes)
            final_models, final_folded = _load_final_models(
                run_root=run_root,
                training=training,
                replicate=replicate,
                capacity=capacity,
            )
            zero_models = source.make_paired_models(capacity, initialization_seed=seeds["model"])
            zero_folded = source.fold_const_checkpoint(zero_models[source.CONST10_ARM])
            for arm in source.ARMS:
                for name in MODEL_CELLS:
                    contract = _cell_contract(name)
                    zero = contract["checkpoint"] == "zero"
                    if arm == source.CONST10_ARM:
                        pre = zero_models[arm] if zero else final_models[arm]
                        deployed = zero_folded if zero else final_folded
                        episodes, lifecycle_valid, fold_audit = source.g38.verify_g38_fold_equivalence(
                            pre,
                            deployed,
                            processes=processes,
                            action_seed=seeds["evaluation_action"],
                            process_kind=str(contract["process"]),
                            deterministic=bool(contract["deterministic"]),
                        )
                    else:
                        pre = zero_models[arm] if zero else final_models[arm]
                        deployed = pre
                        episodes, lifecycle_valid = source.evaluate_g39_model(
                            deployed,
                            processes=processes,
                            action_seed=seeds["evaluation_action"],
                            process_kind=str(contract["process"]),
                            deterministic=bool(contract["deterministic"]),
                        )
                        fold_audit = None
                    cells.append(
                        {
                            "replicate": replicate,
                            "capacity": capacity,
                            "arm": arm,
                            "cell": name,
                            **contract,
                            "optimizer_steps": 0,
                            "state_before": _state_digest(deployed),
                            "state_after": _state_digest(deployed),
                            "pre_fold_state_digest": _state_digest(pre) if arm == source.CONST10_ARM else None,
                            "lifecycle_valid": lifecycle_valid,
                            "fold_equivalence": fold_audit,
                            "episodes": list(episodes),
                        }
                    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": training["source_commit"],
        "authorization_token": training["authorization_token"],
        "alignment_audit_id": training["alignment_audit_id"],
        "alignment_disposition": training["alignment_disposition"],
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
        or evaluation.get("authorization_token") != training.get("authorization_token")
        or evaluation.get("alignment_audit_id") != training.get("alignment_audit_id")
        or evaluation.get("alignment_disposition") != training.get("alignment_disposition")
        or evaluation.get("aligned_source_commit") != training.get("aligned_source_commit")
        or evaluation.get("preflight_artifact_digests")
        != training.get("preflight_artifact_digests")
        or evaluation.get("configuration") != configuration
        or evaluation.get("source_controls") != source.source_controls()
        or evaluation.get("training_manifest_digest") != _artifact_digest(run_root / "train_manifest.json")
        or evaluation.get("direct_source_validation") is not True
    ):
        errors.append("G39 evaluation identity/source mismatch")
    cells = evaluation.get("cells")
    if not isinstance(cells, list) or len(cells) != int(configuration["total_cells"]):
        return errors + ["G39 evaluation cell inventory mismatch"]
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
        errors.append("G39 source inventory mismatch")
    inventories = {
        (int(row["replicate"]), int(row["capacity"])): row["processes"]
        for row in evaluation.get("source_inventory", [])
    }
    observed: set[tuple[int, int, str, str]] = set()
    for cell in cells:
        try:
            key = (int(cell["replicate"]), int(cell["capacity"]), str(cell["arm"]), str(cell["cell"]))
            if key in observed or key[0] not in range(int(configuration["replicates"])) or key[1] not in g34.CAPACITIES or key[2] not in source.ARMS or key[3] not in MODEL_CELLS:
                raise ValueError("G39 evaluation cell identity mismatch")
            observed.add(key)
            contract = _cell_contract(key[3])
            if any(cell.get(name) != value for name, value in contract.items()):
                raise ValueError("G39 evaluation route mismatch")
            if cell.get("optimizer_steps") != 0 or cell.get("state_before") != cell.get("state_after") or cell.get("lifecycle_valid") is not True:
                raise ValueError("G39 evaluation mutation/lifecycle mismatch")
            training_row = training["replicate_results"][key[0]]
            zero = contract["checkpoint"] == "zero"
            expected_deployed = (
                training_row["arms"][source.NATIVE6_ARM]["zero_state_digest"]
                if zero
                else training_row["folded_const_final"]["state_digest"]
                if key[2] == source.CONST10_ARM
                else training_row["arms"][source.NATIVE6_ARM]["final_state_digest"]
            )
            if cell.get("state_before") != expected_deployed:
                raise ValueError("G39 checkpoint-to-cell binding mismatch")
            if key[2] == source.CONST10_ARM:
                fold = cell.get("fold_equivalence")
                if not isinstance(fold, dict) or fold.get("passed") is not True or fold.get("environment_trajectories_per_episode") != 1:
                    raise ValueError("G39 CONST fold-equivalence mismatch")
                expected_pre = training_row["arms"][source.CONST10_ARM][
                    "zero_state_digest" if zero else "final_state_digest"
                ]
                if cell.get("pre_fold_state_digest") != expected_pre:
                    raise ValueError("G39 CONST pre-fold checkpoint binding mismatch")
            elif cell.get("fold_equivalence") is not None:
                raise ValueError("G39 native cell carried a fold path")
            episodes = cell.get("episodes")
            if not isinstance(episodes, list) or len(episodes) != int(configuration["evaluation_episodes_per_cell"]):
                raise ValueError("G39 episode inventory mismatch")
            expected_rows = inventories[(key[0], key[1])]
            roster_field = "random_expected_roster_sizes" if contract["process"] == "random" else "fixed_expected_roster_sizes"
            for index, episode in enumerate(episodes):
                expected = expected_rows[index]
                if (
                    episode.get("local_episode_id") != index
                    or episode.get("episode_id") != expected["episode_id"]
                    or episode.get("signature") != expected["signature"]
                    or episode.get("event_times") != expected["event_times"]
                    or episode.get("event_order") != expected["event_order"]
                    or episode.get("roster_sizes_valid") is not True
                ):
                    raise ValueError("G39 paired episode identity mismatch")
                trace = g34_runner._trace_evidence(episode)
                if (
                    trace["roster_size_trace"] != tuple(expected[roster_field])
                    or not g34_runner._summary_matches_trace(episode, trace)
                ):
                    raise ValueError("G39 trace evidence mismatch")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
    expected = {
        (replicate, capacity, arm, name)
        for replicate in range(int(configuration["replicates"]))
        for capacity in g34.CAPACITIES
        for arm in source.ARMS
        for name in MODEL_CELLS
    }
    if observed != expected:
        errors.append("G39 evaluation cell key set mismatch")
    return errors


def _cell_map(evaluation: Mapping[str, Any]) -> dict[tuple[int, int, str, str], Mapping[str, Any]]:
    return {
        (int(row["replicate"]), int(row["capacity"]), str(row["arm"]), str(row["cell"])): row
        for row in evaluation["cells"]
    }


def _metric_arrays(
    evaluation: Mapping[str, Any], arm: str, cell: str, metric: str
) -> dict[int, np.ndarray]:
    cells = _cell_map(evaluation)
    replicates = int(evaluation["configuration"]["replicates"])
    return {
        capacity: np.asarray(
            [
                [g34_runner._trace_evidence(episode)[metric] for episode in cells[(replicate, capacity, arm, cell)]["episodes"]]
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
        rng.integers(0, episodes, size=(repetitions, replicates, len(g34.CAPACITIES), episodes), dtype=np.int16),
    )


def _hierarchical_ci(
    values: Mapping[int, np.ndarray], *, capacities: Sequence[int],
    plan: tuple[np.ndarray, np.ndarray],
) -> list[float]:
    return g35_runner._hierarchical_ci(values, capacities=capacities, plan=plan)


def _arm_access(
    evaluation: Mapping[str, Any], arm: str, plan: tuple[np.ndarray, np.ndarray]
) -> dict[str, object]:
    return g38_runner._arm_access(evaluation, arm, plan)


def _comparison(
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
            _metric_arrays(evaluation, source.CONST10_ARM, cell, metric),
            _metric_arrays(evaluation, source.NATIVE6_ARM, cell, metric),
        )
        if pooled:
            ci = _hierarchical_ci(delta, capacities=g34.CAPACITIES, plan=plan)
            component_ci[name] = ci
            component_ucbs.append(ci[2])
        else:
            rows = {capacity: _hierarchical_ci(delta, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
            component_ci[name] = rows
            component_ucbs.extend(row[2] for row in rows.values())
    primary_values = _difference(
        _metric_arrays(evaluation, source.CONST10_ARM, FINAL_RANDOM_DET, "utility"),
        _metric_arrays(evaluation, source.NATIVE6_ARM, FINAL_RANDOM_DET, "utility"),
    )
    primary = _hierarchical_ci(primary_values, capacities=g34.CAPACITIES, plan=plan)
    capacity_primary = {capacity: _hierarchical_ci(primary_values, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
    noninferior = g38_runner._inclusive_le(primary[2], TRAINING_MARGIN) and all(
        g38_runner._inclusive_le(value, TRAINING_MARGIN) for value in component_ucbs
    )
    material = g38_runner._strict_gt(primary[0], TRAINING_MARGIN) and all(
        g38_runner._strict_gt(capacity_primary[capacity][0], 0.0) for capacity in g34.CAPACITIES
    )
    return {
        "const_minus_native_primary_ci95": primary,
        "const_minus_native_capacity_ci95": capacity_primary,
        "component_ci95": component_ci,
        "native_noninferior": bool(noninferior),
        "material_const_advantage": bool(material),
    }


def select_g39_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or (
        bool(metrics["const_access_confident_fail"])
        and bool(metrics["native_access_confident_fail"])
    ):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics["native_access_pass"])
        and bool(metrics["native_noninferior"])
        and bool(metrics["initial_match_pass"])
    ):
        return NATIVE_SUFFICIENT_BRANCH
    if bool(metrics["const_access_pass"]) and (
        bool(metrics["native_access_confident_fail"])
        or bool(metrics["material_const_advantage"])
    ):
        return CONST_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def analyze(*, run_root: Path, require_formal: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G39 analysis requires formal artifacts")
    configure_runtime(source.bootstrap_seed(formal=formal))
    errors = _evaluation_errors(run_root, training, evaluation)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        configuration = evaluation["configuration"]
        plan = _bootstrap_plan(
            formal=formal,
            replicates=int(configuration["replicates"]),
            episodes=int(configuration["evaluation_episodes_per_cell"]),
            repetitions=int(configuration["bootstrap_resamples"]),
        )
        access = {arm: _arm_access(evaluation, arm, plan) for arm in source.ARMS}
        comparison = _comparison(evaluation, plan)
        initial_match = all(
            row["initial_forward_match"]["passed"] is True
            and row["initial_trajectory_match"]["passed"] is True
            and row["initial_gradient_audit"]["passed"] is True
            and row["zero_function_digest_equal"] is True
            for row in training["replicate_results"]
        )
        metrics.update(
            {
                "source_valid": evaluation["direct_source_validation"] is True,
                "arm_access": access,
                "const_access_pass": access[source.CONST10_ARM]["access_pass"],
                "native_access_pass": access[source.NATIVE6_ARM]["access_pass"],
                "const_access_confident_fail": access[source.CONST10_ARM]["access_confident_fail"],
                "native_access_confident_fail": access[source.NATIVE6_ARM]["access_confident_fail"],
                "initial_match_pass": bool(initial_match),
                **comparison,
            }
        )
    analysis_seconds = time.perf_counter() - started
    projection: float | None = None
    projection_executable: bool | None = None
    nonformal_total: float | None = None
    if not formal and not errors:
        train_seconds = float(training["stage_wall_time_seconds"])
        eval_seconds = float(evaluation["stage_wall_time_seconds"])
        nonformal_total = train_seconds + eval_seconds + analysis_seconds
        projection = 1.25 * (30.0 * train_seconds + 32.0 * eval_seconds + 40.0 * analysis_seconds)
        projection_executable = nonformal_total <= NONFORMAL_WALL_CLOCK_CAP_SECONDS and projection <= FORMAL_WALL_CLOCK_CAP_SECONDS
    if errors:
        branch = INVALID_BRANCH
    elif formal:
        branch = select_g39_result_branch(metrics)
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
            "training_margin": TRAINING_MARGIN,
        },
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    train(run_root=run_root, source_commit=source_commit, formal=False, authorization_token=None)
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
            raise ValueError("G39 train requires --source-commit")
        train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            preflight_root=args.preflight_root,
            alignment_disposition=args.alignment_disposition,
            aligned_source_commit=args.aligned_source_commit,
        )
    elif args.stage == "evaluate":
        evaluate(run_root=args.run_root)
    elif args.stage == "analyze":
        analyze(run_root=args.run_root, require_formal=args.formal)
    else:
        if args.source_commit is None:
            raise ValueError("G39 exercise requires --source-commit")
        exercise(run_root=args.run_root, source_commit=args.source_commit)


if __name__ == "__main__":
    main()
