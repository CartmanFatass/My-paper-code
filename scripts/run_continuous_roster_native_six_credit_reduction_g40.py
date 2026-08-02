"""Train, evaluate, and analyze the frozen G40 credit comparison."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
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

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as source
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from envs.continuous_roster import runtime_capacity as roster_env
from scripts import run_continuous_roster_native_six_coordinate_training_g39 as g39_runner
from scripts import run_continuous_roster_reactive_reduction_g35 as g35_runner
from scripts import run_continuous_roster_six_coordinate_cs_g38 as g38_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_ALIGNMENT_AUDIT"
)

INVALID_BRANCH = "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40"
SOURCE_FAILURE_BRANCH = "SOURCE_OR_COMMON_ACCESS_FAILURE_G40"
ORDINARY_SUFFICIENT_BRANCH = "ORDINARY_TEAM_GAE_CREDIT_SUFFICIENT_G40"
G31_ADVANTAGE_BRANCH = "G31_REALIZED_TAIL_CREDIT_ADVANTAGE_G40"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_CREDIT_REDUCTION_G40"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_EXERCISE_COMPLETE"
)
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

UTILITY_FLOOR = 0.90
EVENT_FLOOR = 0.85
SEGMENT_FLOOR = 0.85
PROCESS_MARGIN = -0.05
STOCHASTIC_FLOOR = 0.80
MINIMUM_REPLICATE_FLOOR = 0.85
CREDIT_MARGIN = 0.05
REPLAY_TOLERANCE = 1e-6
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
FORMAL_WALL_CLOCK_CAP_SECONDS = 28_800.0

FORMAL_REPLICATES = 3
FORMAL_ANCHOR_UPDATES = 100
FORMAL_BRANCH_UPDATES = 100
FORMAL_NUM_ENVS = 8
FORMAL_PPO_PASSES = 2
FORMAL_EVAL_EPISODES = 64
FORMAL_BOOTSTRAP_REPETITIONS = 10_000

EXERCISE_REPLICATES = 1
EXERCISE_ANCHOR_UPDATES = 10
EXERCISE_BRANCH_UPDATES = 10
EXERCISE_NUM_ENVS = 8
EXERCISE_PPO_PASSES = 2
EXERCISE_EVAL_EPISODES = 6
EXERCISE_BOOTSTRAP_REPETITIONS = 250

TRAINING_BRANCH_UPDATE_WORKERS = 2
EVALUATION_CELL_WORKERS = 1

configure_runtime = g39_runner.configure_runtime
_runtime_identity = g39_runner._runtime_identity
_write_json = g39_runner._write_json
_read_json = g39_runner._read_json
_artifact_digest = g39_runner._artifact_digest
_state_digest = g39_runner._state_digest


def _native_backend_identity() -> dict[str, object]:
    module = source.toy_cpp.load_continuous_roster_toy_cpp_backend()
    return {
        "kind": "ContinuousRosterToyBatch_CPU_CPP",
        "required": True,
        "python_fallback": False,
        "module": str(module.__name__),
        "build_identity": source.toy_cpp._build_identity(),
    }


def _counts(*, formal: bool) -> dict[str, int]:
    if formal:
        return {
            "replicates": FORMAL_REPLICATES,
            "anchor_updates": FORMAL_ANCHOR_UPDATES,
            "branch_updates_per_arm": FORMAL_BRANCH_UPDATES,
            "num_envs": FORMAL_NUM_ENVS,
            "ppo_passes": FORMAL_PPO_PASSES,
            "evaluation_episodes_per_cell": FORMAL_EVAL_EPISODES,
            "bootstrap_resamples": FORMAL_BOOTSTRAP_REPETITIONS,
        }
    return {
        "replicates": EXERCISE_REPLICATES,
        "anchor_updates": EXERCISE_ANCHOR_UPDATES,
        "branch_updates_per_arm": EXERCISE_BRANCH_UPDATES,
        "num_envs": EXERCISE_NUM_ENVS,
        "ppo_passes": EXERCISE_PPO_PASSES,
        "evaluation_episodes_per_cell": EXERCISE_EVAL_EPISODES,
        "bootstrap_resamples": EXERCISE_BOOTSTRAP_REPETITIONS,
    }


def _configuration(*, formal: bool) -> dict[str, object]:
    counts = _counts(formal=formal)
    replicates = int(counts["replicates"])
    anchor = int(counts["anchor_updates"])
    branch = int(counts["branch_updates_per_arm"])
    envs = int(counts["num_envs"])
    passes = int(counts["ppo_passes"])
    episodes = int(counts["evaluation_episodes_per_cell"])
    cells_per_replicate = len(source.ARMS) * len(g34.CAPACITIES) * len(MODEL_CELLS)
    anchor_transitions = replicates * anchor * envs * roster_env.HORIZON
    branch_transitions = (
        replicates * len(source.ARMS) * branch * envs * roster_env.HORIZON
    )
    evaluation_transitions = (
        replicates * cells_per_replicate * episodes * roster_env.HORIZON
    )
    optimizer_steps = replicates * (
        anchor * passes + len(source.ARMS) * branch * passes * 2
    )
    return {
        **counts,
        "arms": list(source.ARMS),
        "common_anchor": "COMMON_NATIVE6_FAST_ANCHOR",
        "stored_training_observation_dim": 6,
        "critic_state_dim": roster_env.CRITIC_STATE_DIM,
        "action_dim": roster_env.ACTION_DIM,
        "actor_width": source.g39.HIDDEN_DIM,
        "training_capacity": roster_env.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "gamma": source.GAMMA,
        "gae_lambda": source.GAE_LAMBDA,
        "gae_return_identity_tolerance": source.GAE_IDENTITY_TOLERANCE,
        "entropy_coefficient": source.ENTROPY_COEFFICIENT,
        "learning_rate": source.LEARNING_RATE,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)",
        "gradient_clipping": "none",
        "minibatches": "none",
        "actor_credit_optimizer": (
            "native_six_actor|log_std|immediate_baseline|successor_baseline"
        ),
        "slow_critic_optimizer": "centralized_slow_critic_only",
        "optimizer_steps_per_ppo_pass_per_branch_arm": 2,
        "checkpoint_selection": "common_anchor_plus_branch_final_only",
        "zero_checkpoint": "common_pre_training_zero_not_anchor",
        "episode_exclusions": "none",
        "cells_per_arm_capacity": len(MODEL_CELLS),
        "cells_per_replicate": cells_per_replicate,
        "total_cells": replicates * cells_per_replicate,
        "anchor_training_transitions": anchor_transitions,
        "branch_training_transitions": branch_transitions,
        "training_transitions": anchor_transitions + branch_transitions,
        "evaluation_transitions": evaluation_transitions,
        "total_real_transitions": (
            anchor_transitions + branch_transitions + evaluation_transitions
        ),
        "optimizer_steps": optimizer_steps,
        "evaluation_optimizer_steps": 0,
        "training_branch_update_workers": TRAINING_BRANCH_UPDATE_WORKERS,
        "training_parallelism": "paired_collect_serial_then_disjoint_branch_optimizers",
        "evaluation_cell_workers": EVALUATION_CELL_WORKERS,
        "evaluation_parallelism": "serial_cells_cpp_batched_episodes",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_python_fallback": False,
        "paired_collection_before_update": True,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }


def _checkpoint_reference(replicate: int, kind: str) -> str:
    if kind == "anchor":
        label = "common_native6_fast_anchor"
    elif kind in source.ARMS:
        label = f"{kind.lower()}_branch_final"
    else:
        raise ValueError("G40 checkpoint kind mismatch")
    return f"checkpoints/replicate_{replicate}_{label}.pt"


def _checkpoint_payload(
    *,
    source_commit: str,
    formal: bool,
    replicate: int,
    kind: str,
    configuration: Mapping[str, object],
    seeds: Mapping[str, int],
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": source_commit,
        "formal": formal,
        "replicate": replicate,
        "kind": kind,
        "completed_anchor_updates": int(configuration["anchor_updates"]),
        "completed_branch_updates": (
            0 if kind == "anchor" else int(configuration["branch_updates_per_arm"])
        ),
        "configuration": dict(configuration),
        "seeds": dict(seeds),
    }


def _save_checkpoint(
    path: Path,
    *,
    source_commit: str,
    formal: bool,
    replicate: int,
    kind: str,
    configuration: Mapping[str, object],
    seeds: Mapping[str, int],
    model: source.G40NativeSixPolicy,
) -> None:
    payload = _checkpoint_payload(
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        kind=kind,
        configuration=configuration,
        seeds=seeds,
    )
    payload["model_state"] = model.state_dict()
    torch.save(payload, path)


def _load_checkpoint(
    path: Path,
    *,
    source_commit: str,
    formal: bool,
    replicate: int,
    kind: str,
    configuration: Mapping[str, object],
    seeds: Mapping[str, int],
    member_capacity: int,
) -> tuple[source.G40NativeSixPolicy, dict[str, Any]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    expected = _checkpoint_payload(
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        kind=kind,
        configuration=configuration,
        seeds=seeds,
    )
    if not isinstance(payload, dict) or any(
        payload.get(name) != value for name, value in expected.items()
    ):
        raise ValueError("G40 checkpoint identity mismatch")
    model = source.make_model(
        int(member_capacity), initialization_seed=int(seeds["anchor_model"])
    )
    if kind in source.ARMS:
        model.begin_credit_branch_phase()
    state = payload.get("model_state")
    if not isinstance(state, dict):
        raise ValueError("G40 checkpoint state missing")
    model.load_state_dict(state, strict=True)
    return model, payload


def _optimizer(parameters: Sequence[torch.nn.Parameter]) -> torch.optim.Adam:
    return torch.optim.Adam(
        parameters,
        lr=source.LEARNING_RATE,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
    )


_REPLAY_KEYS = (
    "logp_max_error",
    "joint_logp_max_error",
    "value_max_error",
    "immediate_baseline_max_error",
    "successor_baseline_max_error",
    "hidden_max_error",
    "prefix_max_error",
    "inactive_logp_max_abs",
)


def _max_replay_error(metrics: Mapping[str, float]) -> float:
    return max(float(metrics[name]) for name in _REPLAY_KEYS)


def _lifecycle_valid(trajectory: Any) -> bool:
    active = trajectory.active_mask
    reset = trajectory.terminal_hidden_reset_mask
    return bool(
        torch.count_nonzero(trajectory.actions[~active]) == 0
        and torch.count_nonzero(trajectory.old_log_probs[~active]) == 0
        and (
            not bool(reset.any())
            or torch.count_nonzero(trajectory.hidden_before[reset]) == 0
        )
        and torch.count_nonzero(trajectory.hidden_before) == 0
        and torch.count_nonzero(trajectory.hidden_after) == 0
        and all(
            outcome.roster_sizes == ledger.expected_roster_sizes
            for outcome, ledger in zip(trajectory.outcomes, trajectory.ledgers)
        )
    )


def _train_replicate(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    replicate: int,
    configuration: Mapping[str, object],
) -> dict[str, Any]:
    seeds = source.seed_block(replicate, formal=formal)
    configure_runtime(seeds["anchor_model"])
    zero = source.make_model(
        roster_env.TRAIN_CAPACITY, initialization_seed=seeds["anchor_model"]
    )
    zero_digest = _state_digest(zero)
    anchor = zero
    source_audit = source.source_preflight_audit()
    if source_audit["passed"] is not True:
        raise RuntimeError("G40 source/constructive witness gate failed")
    anchor_optimizer = _optimizer(anchor.actor_credit_parameters())
    if anchor_optimizer.state != {}:
        raise RuntimeError("G40 common anchor Adam state was not empty")
    common_finite = True
    common_replay = 0.0
    common_steps = 0
    pre_common_gradient: dict[str, object] | None = None
    common_lifecycle = True
    for update in range(int(configuration["anchor_updates"])):
        first = update * int(configuration["num_envs"])
        ids = tuple(range(first, first + int(configuration["num_envs"])))
        trajectory = source.collect_g40_trajectory(
            anchor,
            episode_ids=ids,
            ledger_seed=seeds["anchor_ledger"],
            action_seed=seeds["anchor_action"],
            device=torch.device("cpu"),
        )
        common_lifecycle &= _lifecycle_valid(trajectory)
        if update == 0:
            pre_common_gradient = source.pre_common_gradient_audit(anchor, trajectory)
            if not source.validate_pre_common_gradient_audit(pre_common_gradient):
                raise RuntimeError("G40 pre-common registered-group gradient gate failed")
        metrics = source.optimize_common_fast_anchor_update(
            anchor,
            anchor_optimizer,
            trajectory,
            ppo_passes=int(configuration["ppo_passes"]),
        )
        common_finite &= bool(metrics["finite_update"])
        common_replay = max(common_replay, _max_replay_error(metrics))
        common_steps += int(metrics["optimizer_steps"])
    if pre_common_gradient is None:
        raise RuntimeError("G40 common anchor inventory was empty")
    common_optimizer_discarded = bool(anchor_optimizer.state)
    del anchor_optimizer
    anchor_path = run_root / _checkpoint_reference(replicate, "anchor")
    _save_checkpoint(
        anchor_path,
        source_commit=source_commit,
        formal=formal,
        replicate=replicate,
        kind="anchor",
        configuration=configuration,
        seeds=seeds,
        model=anchor,
    )
    anchor_digest = _state_digest(anchor)

    models = source.clone_anchor_models(anchor)
    for model in models.values():
        model.begin_credit_branch_phase()
    actor_optimizers = {
        arm: _optimizer(model.actor_credit_parameters())
        for arm, model in models.items()
    }
    slow_optimizers = {
        arm: _optimizer(model.slow_critic_parameters())
        for arm, model in models.items()
    }
    all_optimizers: dict[str, torch.optim.Optimizer] = {
        **{f"{arm}:actor": row for arm, row in actor_optimizers.items()},
        **{f"{arm}:critic": row for arm, row in slow_optimizers.items()},
    }
    boundary = source.branch_boundary_audit(anchor, models, all_optimizers)
    if boundary["passed"] is not True:
        raise RuntimeError("G40 branch-boundary clone/optimizer gate failed")

    first_forward: dict[str, object] | None = None
    first_trajectory: dict[str, object] | None = None
    gradient_audit: dict[str, object] | None = None
    branch_finite = {arm: True for arm in source.ARMS}
    branch_lifecycle = {arm: True for arm in source.ARMS}
    branch_replay = {arm: 0.0 for arm in source.ARMS}
    actor_steps = {arm: 0 for arm in source.ARMS}
    critic_steps = {arm: 0 for arm in source.ARMS}
    identity_errors = {arm: 0.0 for arm in source.ARMS}
    torch_rng_before = torch.random.get_rng_state().clone()
    for update in range(int(configuration["branch_updates_per_arm"])):
        first = update * int(configuration["num_envs"])
        ids = tuple(range(first, first + int(configuration["num_envs"])))
        ledger_seed = (
            seeds["branch_gradient_probe"]
            if update == 0
            else seeds["branch_ledger"]
        )
        action_seed = (
            seeds["branch_gradient_probe"]
            if update == 0
            else seeds["branch_action"]
        )
        trajectories = {
            arm: source.collect_g40_trajectory(
                model,
                episode_ids=ids,
                ledger_seed=ledger_seed,
                action_seed=action_seed,
                device=torch.device("cpu"),
            )
            for arm, model in models.items()
        }
        for arm, trajectory in trajectories.items():
            branch_lifecycle[arm] &= _lifecycle_valid(trajectory)
        if update == 0:
            left, right = (trajectories[arm] for arm in source.ARMS)
            first_trajectory = source.branch_trajectory_match(left, right)
            noise = torch.as_tensor(
                roster_env.make_action_noise(
                    ids,
                    action_seed=action_seed,
                    member_capacity=roster_env.TRAIN_CAPACITY,
                )[0]
            )
            first_forward = source.branch_forward_match(
                models[source.G31_ARM],
                models[source.GAE1_ARM],
                observations=left.observations[0],
                active_mask=left.active_mask[0],
                critic_state=left.critic_states[0],
                sampling_noise=noise,
            )
            gradient_audit = source.branch_gradient_audit(models, trajectories)
            if not (
                first_forward["passed"] is True
                and first_trajectory["passed"] is True
                and source.validate_branch_gradient_audit(gradient_audit)
                and all(branch_lifecycle.values())
            ):
                raise RuntimeError("G40 first branch batch gate failed before optimizer step")
        with ThreadPoolExecutor(
            max_workers=TRAINING_BRANCH_UPDATE_WORKERS,
            thread_name_prefix="g40-credit-arm",
        ) as executor:
            futures = {
                arm: executor.submit(
                    source.optimize_credit_branch_update,
                    arm,
                    models[arm],
                    actor_optimizers[arm],
                    slow_optimizers[arm],
                    trajectories[arm],
                    ppo_passes=int(configuration["ppo_passes"]),
                )
                for arm in source.ARMS
            }
            update_metrics = {arm: futures[arm].result() for arm in source.ARMS}
        for arm, metrics in update_metrics.items():
            branch_finite[arm] &= bool(metrics["finite_update"])
            branch_replay[arm] = max(
                branch_replay[arm], _max_replay_error(metrics)
            )
            actor_steps[arm] += int(metrics["actor_optimizer_steps"])
            critic_steps[arm] += int(metrics["slow_critic_optimizer_steps"])
            identity_errors[arm] = max(
                identity_errors[arm], float(metrics["gae1_return_identity_error"])
            )
    torch_rng_unchanged = torch.equal(torch_rng_before, torch.random.get_rng_state())
    if not torch_rng_unchanged:
        raise RuntimeError("G40 branch objective advanced global torch RNG")
    if first_forward is None or first_trajectory is None or gradient_audit is None:
        raise RuntimeError("G40 branch inventory was empty")

    arms: dict[str, dict[str, object]] = {}
    for arm, model in models.items():
        path = run_root / _checkpoint_reference(replicate, arm)
        _save_checkpoint(
            path,
            source_commit=source_commit,
            formal=formal,
            replicate=replicate,
            kind=arm,
            configuration=configuration,
            seeds=seeds,
            model=model,
        )
        arms[arm] = {
            "finite_updates": branch_finite[arm],
            "lifecycle_contract_valid": branch_lifecycle[arm],
            "maximum_replay_error": branch_replay[arm],
            "completed_branch_updates": int(configuration["branch_updates_per_arm"]),
            "actor_optimizer_steps": actor_steps[arm],
            "slow_critic_optimizer_steps": critic_steps[arm],
            "gae1_return_identity_max_error": identity_errors[arm],
            "final_checkpoint": _checkpoint_reference(replicate, arm),
            "final_state_digest": _state_digest(model),
        }
    return {
        "replicate": replicate,
        "seeds": seeds,
        "zero_checkpoint_kind": "common_pre_training_zero_not_anchor",
        "zero_state_digest": zero_digest,
        "source_preflight_audit": source_audit,
        "pre_common_gradient_audit": pre_common_gradient,
        "common_anchor": {
            "finite_updates": common_finite,
            "lifecycle_contract_valid": common_lifecycle,
            "maximum_replay_error": common_replay,
            "optimizer_steps": common_steps,
            "optimizer_state_discarded": common_optimizer_discarded,
            "checkpoint": _checkpoint_reference(replicate, "anchor"),
            "state_digest": anchor_digest,
        },
        "branch_boundary_audit": boundary,
        "paired_collection_before_update": True,
        "first_branch_forward_match": first_forward,
        "first_branch_trajectory_match": first_trajectory,
        "first_branch_gradient_audit": gradient_audit,
        "torch_rng_unchanged_by_branch_objective": torch_rng_unchanged,
        "gae1_return_identity_max_error": max(identity_errors.values()),
        "arms": arms,
    }


def _finite_seconds(value: object, name: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not np.isfinite(value)
        or value < 0
    ):
        raise ValueError(f"G40 {name} timing invalid")
    return float(value)


def _preflight_digests(root: Path) -> dict[str, str]:
    return {
        "training": _artifact_digest(root / "train_manifest.json"),
        "evaluation": _artifact_digest(root / "evaluation_manifest.json"),
        "analysis": _artifact_digest(root / "analysis_result.json"),
    }


def _validate_formal_preflight(
    preflight_root: Path | None,
    *,
    source_commit: str,
    alignment_disposition: str | None,
    aligned_source_commit: str | None,
) -> dict[str, str]:
    if preflight_root is None:
        raise ValueError("formal G40 execution requires a bounded preflight root")
    if alignment_disposition != "ALIGNED" or aligned_source_commit != source_commit:
        raise ValueError("formal G40 execution requires ALIGNED same-source audit")
    root = Path(preflight_root)
    training = _read_json(root / "train_manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    analysis = _read_json(root / "analysis_result.json")
    errors = _evaluation_errors(root, training, evaluation)
    if errors:
        raise ValueError("G40 formal preflight artifacts invalid: " + " | ".join(errors))
    expected = _configuration(formal=False)
    train_seconds = _finite_seconds(training.get("stage_wall_time_seconds"), "preflight train")
    eval_seconds = _finite_seconds(evaluation.get("stage_wall_time_seconds"), "preflight evaluate")
    analyze_seconds = _finite_seconds(analysis.get("stage_wall_time_seconds"), "preflight analyze")
    projection = 1.25 * (
        30.0 * train_seconds + 32.0 * eval_seconds + 40.0 * analyze_seconds
    )
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
        or analysis.get("training_manifest_digest")
        != _artifact_digest(root / "train_manifest.json")
        or analysis.get("evaluation_manifest_digest")
        != _artifact_digest(root / "evaluation_manifest.json")
        or not np.isclose(
            float(analysis.get("formal_projection_seconds", np.nan)),
            projection,
            rtol=0,
            atol=1e-9,
        )
        or analysis.get("formal_projection_executable") is not True
        or train_seconds + eval_seconds + analyze_seconds
        > NONFORMAL_WALL_CLOCK_CAP_SECONDS
        or projection > FORMAL_WALL_CLOCK_CAP_SECONDS
    ):
        raise ValueError("G40 formal preflight is not executable for aligned source")
    return _preflight_digests(root)


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    preflight_root: Path | None = None,
    alignment_disposition: str | None = None,
    aligned_source_commit: str | None = None,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G40 training requires an integrated source commit")
    preflight_digests: dict[str, str] | None = None
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("G40 formal authorization token mismatch")
        preflight_digests = _validate_formal_preflight(
            preflight_root,
            source_commit=source_commit,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
        )
    elif any(
        value is not None
        for value in (
            authorization_token,
            preflight_root,
            alignment_disposition,
            aligned_source_commit,
        )
    ):
        raise ValueError("G40 nonformal training cannot carry formal authority")
    started = time.perf_counter()
    configuration = _configuration(formal=formal)
    configure_runtime(source.bootstrap_seed(formal=formal))
    native_backend = _native_backend_identity()
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
        "preflight_root": (
            str(Path(preflight_root).resolve()) if preflight_root is not None else None
        ),
        "preflight_artifact_digests": preflight_digests,
        "runtime": _runtime_identity(),
        "native_backend": native_backend,
        "configuration": configuration,
        "source_controls": source.source_controls(),
        "gae1_return_identity_valid": all(
            float(row["gae1_return_identity_max_error"])
            <= source.GAE_IDENTITY_TOLERANCE
            for row in rows
        ),
        "stage_wall_time_seconds": time.perf_counter() - started,
        "replicate_results": rows,
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


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
        raise ValueError("G40 unknown evaluation cell")
    return contracts[name]


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
                "fixed_expected_roster_sizes": list(row.base.expected_roster_sizes),
                "signature": repr(row.signature),
            }
            for row in processes
        ],
    }


def _load_final_models(
    *, run_root: Path, training: Mapping[str, Any], replicate: int, capacity: int
) -> dict[str, source.G40NativeSixPolicy]:
    formal = bool(training["formal"])
    configuration = training["configuration"]
    seeds = source.seed_block(replicate, formal=formal)
    row = training["replicate_results"][replicate]
    return {
        arm: _load_checkpoint(
            run_root / row["arms"][arm]["final_checkpoint"],
            source_commit=str(training["source_commit"]),
            formal=formal,
            replicate=replicate,
            kind=arm,
            configuration=configuration,
            seeds=seeds,
            member_capacity=capacity,
        )[0]
        for arm in source.ARMS
    }


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
        or training.get("gae1_return_identity_valid") is not True
        or re.fullmatch(r"[0-9a-f]{40}", str(training.get("source_commit"))) is None
    ):
        return ["G40 training identity mismatch"]
    backend = training.get("native_backend")
    if (
        not isinstance(backend, Mapping)
        or backend.get("required") is not True
        or backend.get("python_fallback") is not False
        or backend.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
    ):
        errors.append("G40 native backend binding mismatch")
    if formal and (
        training.get("authorization_token") != AUTHORIZATION_TOKEN
        or training.get("alignment_audit_id") != ALIGNMENT_AUDIT_ID
        or training.get("alignment_disposition") != "ALIGNED"
        or training.get("aligned_source_commit") != training.get("source_commit")
        or not isinstance(training.get("preflight_artifact_digests"), dict)
    ):
        errors.append("G40 formal authority binding mismatch")
    if formal and not errors:
        serialized_root = training.get("preflight_root")
        if not isinstance(serialized_root, str) or not Path(serialized_root).is_absolute():
            errors.append("G40 formal preflight root mismatch")
        else:
            try:
                live = _validate_formal_preflight(
                    Path(serialized_root),
                    source_commit=str(training["source_commit"]),
                    alignment_disposition=str(training["alignment_disposition"]),
                    aligned_source_commit=str(training["aligned_source_commit"]),
                )
                if live != training.get("preflight_artifact_digests"):
                    errors.append("G40 formal preflight digest binding mismatch")
            except (OSError, TypeError, ValueError) as error:
                errors.append(f"G40 formal preflight invalid: {error}")
    if not formal and any(
        training.get(name) is not None
        for name in (
            "authorization_token",
            "alignment_audit_id",
            "alignment_disposition",
            "aligned_source_commit",
            "preflight_root",
            "preflight_artifact_digests",
        )
    ):
        errors.append("G40 nonformal artifact carried formal authority")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(configuration["replicates"]):
        return errors + ["G40 training replicate inventory mismatch"]
    expected_anchor = int(configuration["anchor_updates"]) * int(configuration["ppo_passes"])
    expected_branch = int(configuration["branch_updates_per_arm"]) * int(configuration["ppo_passes"])
    expected_files: set[str] = set()
    for replicate, row in enumerate(rows):
        try:
            boundary = row["branch_boundary_audit"]
            if (
                row["replicate"] != replicate
                or row["seeds"] != source.seed_block(replicate, formal=formal)
                or row["zero_checkpoint_kind"]
                != "common_pre_training_zero_not_anchor"
                or row["source_preflight_audit"] != source.source_preflight_audit()
                or not source.validate_pre_common_gradient_audit(
                    row["pre_common_gradient_audit"]
                )
                or row["paired_collection_before_update"] is not True
                or row["first_branch_forward_match"]["passed"] is not True
                or row["first_branch_trajectory_match"]["passed"] is not True
                or not source.validate_branch_gradient_audit(
                    row["first_branch_gradient_audit"]
                )
                or boundary["passed"] is not True
                or boundary["model_state_bytes_equal"] is not True
                or boundary["buffer_bytes_equal"] is not True
                or boundary["log_std_equal"] is not True
                or boundary["optimizer_states_empty_and_separate"] is not True
                or boundary["shared_tensor_storage_count"] != 0
                or row["torch_rng_unchanged_by_branch_objective"] is not True
                or float(row["gae1_return_identity_max_error"])
                > source.GAE_IDENTITY_TOLERANCE
            ):
                raise ValueError("G40 initialization/branch-start gate mismatch")
            anchor = row["common_anchor"]
            anchor_reference = anchor["checkpoint"]
            expected_files.add(Path(anchor_reference).name)
            if (
                anchor["finite_updates"] is not True
                or anchor["lifecycle_contract_valid"] is not True
                or float(anchor["maximum_replay_error"]) > REPLAY_TOLERANCE
                or anchor["optimizer_steps"] != expected_anchor
                or anchor["optimizer_state_discarded"] is not True
            ):
                raise ValueError("G40 common-anchor exposure mismatch")
            loaded_anchor, _ = _load_checkpoint(
                run_root / anchor_reference,
                source_commit=str(training["source_commit"]),
                formal=formal,
                replicate=replicate,
                kind="anchor",
                configuration=configuration,
                seeds=row["seeds"],
                member_capacity=roster_env.TRAIN_CAPACITY,
            )
            if _state_digest(loaded_anchor) != anchor["state_digest"]:
                raise ValueError("G40 common-anchor checkpoint digest mismatch")
            for arm in source.ARMS:
                arm_row = row["arms"][arm]
                expected_files.add(Path(arm_row["final_checkpoint"]).name)
                if (
                    arm_row["finite_updates"] is not True
                    or arm_row["lifecycle_contract_valid"] is not True
                    or float(arm_row["maximum_replay_error"]) > REPLAY_TOLERANCE
                    or arm_row["actor_optimizer_steps"] != expected_branch
                    or arm_row["slow_critic_optimizer_steps"] != expected_branch
                    or float(arm_row["gae1_return_identity_max_error"])
                    > source.GAE_IDENTITY_TOLERANCE
                ):
                    raise ValueError("G40 branch exposure mismatch")
                loaded, _ = _load_checkpoint(
                    run_root / arm_row["final_checkpoint"],
                    source_commit=str(training["source_commit"]),
                    formal=formal,
                    replicate=replicate,
                    kind=arm,
                    configuration=configuration,
                    seeds=row["seeds"],
                    member_capacity=roster_env.TRAIN_CAPACITY,
                )
                if _state_digest(loaded) != arm_row["final_state_digest"]:
                    raise ValueError("G40 branch checkpoint digest mismatch")
        except (KeyError, OSError, TypeError, ValueError) as error:
            errors.append(str(error))
    try:
        observed_files = {path.name for path in (run_root / "checkpoints").iterdir()}
        if observed_files != expected_files:
            errors.append("G40 checkpoint inventory is not anchor plus final-only branches")
    except OSError as error:
        errors.append(str(error))
    return errors


def _evaluate_cell(
    *,
    replicate: int,
    capacity: int,
    arm: str,
    name: str,
    processes: Sequence[g34.RandomProcessLedger],
    action_seed: int,
    deployed: source.G40NativeSixPolicy,
) -> dict[str, object]:
    contract = _cell_contract(name)
    before = _state_digest(deployed)
    episodes, lifecycle = source.evaluate_model(
        deployed,
        processes=processes,
        action_seed=action_seed,
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
        "state_after": _state_digest(deployed),
        "lifecycle_valid": lifecycle,
        "episodes": list(episodes),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    errors = _training_errors(run_root, training)
    if errors:
        raise ValueError("G40 training artifact invalid: " + " | ".join(errors))
    formal = bool(training["formal"])
    configuration = _configuration(formal=formal)
    configure_runtime(source.bootstrap_seed(formal=formal))
    native_backend = _native_backend_identity()
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
            finals = _load_final_models(
                run_root=run_root,
                training=training,
                replicate=replicate,
                capacity=capacity,
            )
            zero = source.make_model(
                capacity, initialization_seed=seeds["anchor_model"]
            )
            for arm in source.ARMS:
                for name in MODEL_CELLS:
                    contract = _cell_contract(name)
                    deployed = zero if contract["checkpoint"] == "zero" else finals[arm]
                    cells.append(
                        _evaluate_cell(
                            replicate=replicate,
                            capacity=capacity,
                            arm=arm,
                            name=name,
                            processes=processes,
                            action_seed=seeds["evaluation_action"],
                            deployed=deployed,
                        )
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
        "native_backend": native_backend,
        "configuration": configuration,
        "source_controls": source.source_controls(),
        "gae1_return_identity_valid": training["gae1_return_identity_valid"],
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
        or evaluation.get("gae1_return_identity_valid") is not True
        or evaluation.get("training_manifest_digest")
        != _artifact_digest(run_root / "train_manifest.json")
        or evaluation.get("direct_source_validation") is not True
    ):
        errors.append("G40 evaluation identity/source mismatch")
    backend = evaluation.get("native_backend")
    if (
        not isinstance(backend, Mapping)
        or backend.get("required") is not True
        or backend.get("python_fallback") is not False
    ):
        errors.append("G40 evaluation native backend mismatch")
    cells = evaluation.get("cells")
    if not isinstance(cells, list) or len(cells) != int(configuration["total_cells"]):
        return errors + ["G40 evaluation cell inventory mismatch"]
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
        errors.append("G40 source inventory mismatch")
    inventories = {
        (int(row["replicate"]), int(row["capacity"])): row["processes"]
        for row in evaluation.get("source_inventory", [])
    }
    observed: set[tuple[int, int, str, str]] = set()
    for cell in cells:
        try:
            key = (
                int(cell["replicate"]),
                int(cell["capacity"]),
                str(cell["arm"]),
                str(cell["cell"]),
            )
            if (
                key in observed
                or key[0] not in range(int(configuration["replicates"]))
                or key[1] not in g34.CAPACITIES
                or key[2] not in source.ARMS
                or key[3] not in MODEL_CELLS
            ):
                raise ValueError("G40 evaluation cell identity mismatch")
            observed.add(key)
            contract = _cell_contract(key[3])
            if any(cell.get(name) != value for name, value in contract.items()):
                raise ValueError("G40 evaluation route mismatch")
            if (
                cell.get("optimizer_steps") != 0
                or cell.get("state_before") != cell.get("state_after")
                or cell.get("lifecycle_valid") is not True
            ):
                raise ValueError("G40 evaluation mutation/lifecycle mismatch")
            training_row = training["replicate_results"][key[0]]
            expected_state = (
                training_row["zero_state_digest"]
                if contract["checkpoint"] == "zero"
                else training_row["arms"][key[2]]["final_state_digest"]
            )
            if cell.get("state_before") != expected_state:
                raise ValueError("G40 checkpoint-to-cell binding mismatch")
            episodes = cell.get("episodes")
            if not isinstance(episodes, list) or len(episodes) != int(
                configuration["evaluation_episodes_per_cell"]
            ):
                raise ValueError("G40 episode inventory mismatch")
            expected_rows = inventories[(key[0], key[1])]
            roster_field = (
                "random_expected_roster_sizes"
                if contract["process"] == "random"
                else "fixed_expected_roster_sizes"
            )
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
                    raise ValueError("G40 paired episode identity mismatch")
                trace = g39_runner.g34_runner._trace_evidence(episode)
                if (
                    trace["roster_size_trace"] != tuple(expected[roster_field])
                    or not g39_runner.g34_runner._summary_matches_trace(episode, trace)
                ):
                    raise ValueError("G40 trace evidence mismatch")
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
        errors.append("G40 evaluation cell key set mismatch")
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
    evaluation: Mapping[str, Any], arm: str, cell: str, metric: str
) -> dict[int, np.ndarray]:
    cells = _cell_map(evaluation)
    replicates = int(evaluation["configuration"]["replicates"])
    return {
        capacity: np.asarray(
            [
                [
                    g39_runner.g34_runner._trace_evidence(episode)[metric]
                    for episode in cells[(replicate, capacity, arm, cell)]["episodes"]
                ]
                for replicate in range(replicates)
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
            size=(repetitions, replicates, len(g34.CAPACITIES), episodes),
            dtype=np.int16,
        ),
    )


def _hierarchical_ci(
    values: Mapping[int, np.ndarray],
    *,
    capacities: Sequence[int],
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
        (
            "random_event_window",
            FINAL_RANDOM_DET,
            "minimum_event_window_utility",
            False,
        ),
        (
            "random_process_segment",
            FINAL_RANDOM_DET,
            "minimum_process_segment_utility",
            False,
        ),
    )
    component_ci: dict[str, object] = {}
    component_ucbs: list[float] = []
    for name, cell, metric, pooled in component_specs:
        delta = _difference(
            _metric_arrays(evaluation, source.G31_ARM, cell, metric),
            _metric_arrays(evaluation, source.GAE1_ARM, cell, metric),
        )
        if pooled:
            ci = _hierarchical_ci(delta, capacities=g34.CAPACITIES, plan=plan)
            component_ci[name] = ci
            component_ucbs.append(ci[2])
        else:
            rows = {
                capacity: _hierarchical_ci(
                    delta, capacities=(capacity,), plan=plan
                )
                for capacity in g34.CAPACITIES
            }
            component_ci[name] = rows
            component_ucbs.extend(row[2] for row in rows.values())
    primary_values = _difference(
        _metric_arrays(
            evaluation, source.G31_ARM, FINAL_RANDOM_DET, "utility"
        ),
        _metric_arrays(
            evaluation, source.GAE1_ARM, FINAL_RANDOM_DET, "utility"
        ),
    )
    primary = _hierarchical_ci(
        primary_values, capacities=g34.CAPACITIES, plan=plan
    )
    capacity_primary = {
        capacity: _hierarchical_ci(
            primary_values, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    ordinary_noninferior = g38_runner._inclusive_le(primary[2], CREDIT_MARGIN) and all(
        g38_runner._inclusive_le(value, CREDIT_MARGIN) for value in component_ucbs
    )
    material = g38_runner._strict_gt(primary[0], CREDIT_MARGIN) and all(
        g38_runner._strict_gt(capacity_primary[capacity][0], 0.0)
        for capacity in g34.CAPACITIES
    )
    return {
        "g31_minus_ordinary_primary_ci95": primary,
        "g31_minus_ordinary_capacity_ci95": capacity_primary,
        "component_ci95": component_ci,
        "ordinary_noninferior": bool(ordinary_noninferior),
        "material_g31_advantage": bool(material),
    }


def select_g40_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or (
        bool(metrics["g31_access_confident_fail"])
        and bool(metrics["ordinary_access_confident_fail"])
    ):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics["ordinary_access_pass"])
        and bool(metrics["ordinary_noninferior"])
        and bool(metrics["branch_start_equality_pass"])
    ):
        return ORDINARY_SUFFICIENT_BRANCH
    if bool(metrics["g31_access_pass"]) and (
        bool(metrics["ordinary_access_confident_fail"])
        or bool(metrics["material_g31_advantage"])
    ):
        return G31_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def analyze(*, run_root: Path, require_formal: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G40 analysis requires formal artifacts")
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
        branch_start = all(
            row["branch_boundary_audit"]["passed"] is True
            and row["first_branch_forward_match"]["passed"] is True
            and row["first_branch_trajectory_match"]["passed"] is True
            and source.validate_branch_gradient_audit(
                row["first_branch_gradient_audit"]
            )
            for row in training["replicate_results"]
        )
        metrics.update(
            {
                "source_valid": evaluation["direct_source_validation"] is True,
                "arm_access": access,
                "g31_access_pass": access[source.G31_ARM]["access_pass"],
                "ordinary_access_pass": access[source.GAE1_ARM]["access_pass"],
                "g31_access_confident_fail": access[source.G31_ARM][
                    "access_confident_fail"
                ],
                "ordinary_access_confident_fail": access[source.GAE1_ARM][
                    "access_confident_fail"
                ],
                "branch_start_equality_pass": bool(branch_start),
                "gae1_return_identity_valid": evaluation[
                    "gae1_return_identity_valid"
                ],
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
        projection = 1.25 * (
            30.0 * train_seconds + 32.0 * eval_seconds + 40.0 * analysis_seconds
        )
        projection_executable = bool(
            nonformal_total <= NONFORMAL_WALL_CLOCK_CAP_SECONDS
            and projection <= FORMAL_WALL_CLOCK_CAP_SECONDS
        )
    if errors:
        branch = INVALID_BRANCH
    elif formal:
        branch = select_g40_result_branch(metrics)
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
        "gae1_return_identity_valid": training.get("gae1_return_identity_valid"),
        "native_backend": evaluation.get("native_backend"),
        "training_manifest_digest": _artifact_digest(run_root / "train_manifest.json"),
        "evaluation_manifest_digest": _artifact_digest(
            run_root / "evaluation_manifest.json"
        ),
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
            "credit_margin": CREDIT_MARGIN,
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
            raise ValueError("G40 train requires --source-commit")
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
            raise ValueError("G40 exercise requires --source-commit")
        exercise(run_root=args.run_root, source_commit=args.source_commit)


if __name__ == "__main__":
    main()
