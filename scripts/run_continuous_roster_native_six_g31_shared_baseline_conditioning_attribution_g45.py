"""Train, evaluate, and analyze frozen G45 shared-baseline attribution."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any, Mapping

_THREAD_ENV_NAMES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
for _thread_env_name in _THREAD_ENV_NAMES:
    os.environ[_thread_env_name] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45
    as source,
)
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32


def _load_isolated_g44_orchestration() -> Any:
    path = PROJECT_ROOT / (
        "scripts/run_continuous_roster_native_six_g31_channel_scale_"
        "normalization_attribution_g44.py"
    )
    name = "scripts._g45_isolated_g44_orchestration_backend"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("G45 could not load its accepted G44 orchestration")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_base = _load_isolated_g44_orchestration()


SCHEMA_VERSION = 2
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_"
    "ATTRIBUTION_G45_FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_"
    "ATTRIBUTION_G45_CODE_SCIENCE_ALIGNMENT_AUDIT"
)
# Formal admission is bound to the independent correction recheck and still
# requires an exact same-source nonformal preflight plus the authorization token.
ALIGNED_IMPLEMENTATION_COMMIT = "a42da997712d9c941ac9a6ca08992f4c5de033a2"
ALIGNMENT_STAGE_COMMIT = "40840069c4cfe0baad67e2800d13bbee872844b0"
ACCEPTED_ANCHOR_ROOT_RELATIVE = _base.ACCEPTED_ANCHOR_ROOT_RELATIVE

INVALID_BRANCH = (
    "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_"
    "CONDITIONING_ATTRIBUTION_G45"
)
SOURCE_FAILURE_BRANCH = "SOURCE_OR_REFERENCE_ACCESS_FAILURE_G45"
NO_READ_SUFFICIENT_BRANCH = "SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45"
READ_ADVANTAGE_BRANCH = "SHARED_TRUE_STATE_BASELINE_CONDITIONING_ADVANTAGE_G45"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_SHARED_BASELINE_CONDITIONING_G45"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_"
    "CONDITIONING_ATTRIBUTION_G45_EXERCISE_COMPLETE"
)
NON_EXECUTABLE_BRANCH = _base.NON_EXECUTABLE_BRANCH

FINAL_FIXED_DET = _base.FINAL_FIXED_DET
FINAL_FIXED_STOCH = _base.FINAL_FIXED_STOCH
FINAL_RANDOM_DET = _base.FINAL_RANDOM_DET
FINAL_RANDOM_STOCH = _base.FINAL_RANDOM_STOCH
MODEL_CELLS = _base.MODEL_CELLS
UTILITY_FLOOR = _base.UTILITY_FLOOR
EVENT_FLOOR = _base.EVENT_FLOOR
SEGMENT_FLOOR = _base.SEGMENT_FLOOR
PROCESS_MARGIN = _base.PROCESS_MARGIN
STOCHASTIC_FLOOR = _base.STOCHASTIC_FLOOR
MINIMUM_REPLICATE_FLOOR = _base.MINIMUM_REPLICATE_FLOOR
BASELINE_MARGIN = 0.05
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
FORMAL_WALL_CLOCK_CAP_SECONDS = 28_800.0

FORMAL_REPLICATES = 3
FORMAL_BRANCH_UPDATES = 100
FORMAL_NUM_ENVS = 8
FORMAL_PPO_PASSES = 2
FORMAL_EVAL_EPISODES = 48
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
EXERCISE_REPLICATES = 1
EXERCISE_BRANCH_UPDATES = 10
EXERCISE_NUM_ENVS = 8
EXERCISE_PPO_PASSES = 2
EXERCISE_EVAL_EPISODES = 6
EXERCISE_BOOTSTRAP_REPETITIONS = 250
SEED_BASES = {
    "branch_ledger": 10_451_000,
    "branch_action": 10_452_000,
    "branch_gradient_probe": 10_453_000,
    "evaluation_ledger": 10_454_000,
    "evaluation_process": 10_455_000,
    "evaluation_action": 10_456_000,
}
BOOTSTRAP_SEED = 10_457_045
NONFORMAL_SEED_OFFSET = 900_000
DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 2
MAX_PROCESS_WORKERS = 6
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}

_original_comparison = _base._comparison
_original_readiness_interface_smoke = _base.readiness_interface_smoke


def _activate_single_thread_worker() -> None:
    _base._original_activate_single_thread_worker()


def _training_replicate_worker(task: Mapping[str, object]) -> dict[str, object]:
    return _base._original_training_replicate_worker(task)


def _evaluation_cell_worker(task: Mapping[str, object]) -> dict[str, object]:
    return _base._original_evaluation_cell_worker(task)


def _cpu_parallel_benchmark_worker(
    task: Mapping[str, object],
) -> dict[str, object]:
    return _base._original_cpu_parallel_benchmark_worker(task)


def _counts(*, formal: bool) -> dict[str, int]:
    if formal:
        return {
            "replicates": FORMAL_REPLICATES,
            "branch_updates_per_arm": FORMAL_BRANCH_UPDATES,
            "num_envs": FORMAL_NUM_ENVS,
            "ppo_passes": FORMAL_PPO_PASSES,
            "evaluation_episodes_per_cell": FORMAL_EVAL_EPISODES,
            "bootstrap_resamples": FORMAL_BOOTSTRAP_REPETITIONS,
        }
    return {
        "replicates": EXERCISE_REPLICATES,
        "branch_updates_per_arm": EXERCISE_BRANCH_UPDATES,
        "num_envs": EXERCISE_NUM_ENVS,
        "ppo_passes": EXERCISE_PPO_PASSES,
        "evaluation_episodes_per_cell": EXERCISE_EVAL_EPISODES,
        "bootstrap_resamples": EXERCISE_BOOTSTRAP_REPETITIONS,
    }


def _configuration(
    *,
    formal: bool,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, object]:
    cpu = _base._backend._resolve_cpu_execution(cpu_budget, process_workers)
    counts = _counts(formal=formal)
    replicates = int(counts["replicates"])
    updates = int(counts["branch_updates_per_arm"])
    envs = int(counts["num_envs"])
    passes = int(counts["ppo_passes"])
    episodes = int(counts["evaluation_episodes_per_cell"])
    cells_per_replicate = len(source.ARMS) * len(g34.CAPACITIES) * len(MODEL_CELLS)
    training = replicates * len(source.ARMS) * updates * envs * g32.HORIZON
    evaluation = replicates * cells_per_replicate * episodes * g32.HORIZON
    return {
        **counts,
        "cpu_budget": cpu["cpu_budget"],
        "process_workers": cpu["process_workers"],
        "supported_process_worker_ceiling": cpu["supported_process_worker_ceiling"],
        "cpu_parallelism_fixed_at_launch": True,
        "cpu_continuous_adaptation": False,
        "worker_start_method": "spawn",
        "training_parallel_unit": "formal_replicate_only",
        "evaluation_parallel_unit": "replicate_capacity_cell",
        "deterministic_worker_merge": "preassigned_index_not_completion_order",
        "worker_thread_controls": cpu["worker_thread_controls"],
        "arms": list(source.ARMS),
        "accepted_anchor_replicates": (
            list(source.ACCEPTED_G40_ANCHOR_REPLICATES) if formal else [0]
        ),
        "common_anchor_training": "none_read_only_accepted_G40_anchors",
        "accepted_g40_source_commit": source.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g44_formal_source_commit": source.ACCEPTED_G44_FORMAL_SOURCE_COMMIT,
        "accepted_g44_aligned_source_commit": source.ACCEPTED_G44_ALIGNED_SOURCE_COMMIT,
        "accepted_g44_alignment_stage_commit": source.ACCEPTED_G44_ALIGNMENT_STAGE_COMMIT,
        "aligned_g45_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "training_capacity": g32.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "horizon": g32.HORIZON,
        "stored_training_observation_dim": 6,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)",
        "learning_rate": 1e-3,
        "gradient_clipping": "none",
        "minibatches": "none",
        "actor_head_optimizer": "native_six_actor|log_std|shared_two_output_baseline",
        "standalone_slow_critic": "absent",
        "direction_balance": "absent",
        "channel_composition": "literal_equal_mean_0.5",
        "channel_normalization": "independent_per_channel_RMS",
        "baseline_actor_read_treatment": "READ_vs_shadow_NO_READ",
        "normalization_rows": source.NORMALIZATION_ROWS,
        "normalization_unit": "one_team_residual_row_per_primitive_step",
        "optimizer_steps_per_ppo_pass_per_arm": 1,
        "checkpoint_selection": "final_only",
        "episode_exclusions": "none",
        "cells_per_arm_capacity": len(MODEL_CELLS),
        "cells_per_replicate": cells_per_replicate,
        "total_cells": replicates * cells_per_replicate,
        "training_transitions": training,
        "evaluation_transitions": evaluation,
        "total_real_transitions": training + evaluation,
        "optimizer_steps": replicates * len(source.ARMS) * updates * passes,
        "evaluation_optimizer_steps": 0,
        "branch_update_order": list(source.ARMS),
        "order_swap_guard": "one_pre_step_disjoint_storage_commutativity_guard",
        "paired_collection_before_update": True,
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_python_fallback": False,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }


def source_controls() -> dict[str, object]:
    return {
        "source_id": source.SOURCE_ID,
        "parent_source_id": source.g44.SOURCE_ID,
        "accepted_g40_manifest": source.g41.ACCEPTED_G40_MANIFEST,
        "accepted_g40_source_commit": source.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g44_formal_source_commit": source.ACCEPTED_G44_FORMAL_SOURCE_COMMIT,
        "accepted_g44_aligned_source_commit": source.ACCEPTED_G44_ALIGNED_SOURCE_COMMIT,
        "accepted_g44_alignment_stage_commit": source.ACCEPTED_G44_ALIGNMENT_STAGE_COMMIT,
        "aligned_g45_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "training_source": "G32 capacity-8 fixed paired source",
        "evaluation_source": "G34 fixed/random capacities 6|8|12",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_backend_python_fallback": False,
        "horizon": g32.HORIZON,
        "training_capacity": g32.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "arms": list(source.ARMS),
        "seed_bases": dict(SEED_BASES),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "nonformal_seed_offset": NONFORMAL_SEED_OFFSET,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }


def _comparison(
    evaluation: Mapping[str, Any], plan: tuple[np.ndarray, np.ndarray]
) -> dict[str, object]:
    row = _original_comparison(evaluation, plan)
    return {
        "read_minus_no_read_primary_ci95": row[
            "independent_minus_pooled_primary_ci95"
        ],
        "read_minus_no_read_capacity_ci95": row[
            "independent_minus_pooled_capacity_ci95"
        ],
        "component_ci95": row["component_ci95"],
        "no_read_noninferior": row["pooled_noninferior"],
        "material_baseline_conditioning_advantage": row[
            "material_independent_advantage"
        ],
    }


def select_g45_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or bool(
        metrics["read_access_confident_fail"]
    ):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics["read_access_pass"])
        and bool(metrics["no_read_access_pass"])
        and bool(metrics["no_read_noninferior"])
    ):
        return NO_READ_SUFFICIENT_BRANCH
    if bool(metrics["read_access_pass"]) and (
        bool(metrics["no_read_access_confident_fail"])
        or bool(metrics["material_baseline_conditioning_advantage"])
    ):
        return READ_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def _g45_error_text(value: object) -> str:
    return str(value).replace("G43", "G45").replace("G44", "G45")


def _training_errors(
    run_root: Path, training: Mapping[str, Any]
) -> list[str]:
    return [
        _g45_error_text(value)
        for value in _base._original_training_errors(run_root, training)
    ]


def _evaluation_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> list[str]:
    return [
        _g45_error_text(value)
        for value in _base._original_evaluation_errors(
            run_root, training, evaluation
        )
    ]


def _patch_base_and_backend() -> None:
    values = {
        "source": source,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "ALGORITHM_ID": ALGORITHM_ID,
        "AUTHORIZATION_TOKEN": AUTHORIZATION_TOKEN,
        "ALIGNMENT_AUDIT_ID": ALIGNMENT_AUDIT_ID,
        "ALIGNED_IMPLEMENTATION_COMMIT": ALIGNED_IMPLEMENTATION_COMMIT,
        "ALIGNMENT_STAGE_COMMIT": ALIGNMENT_STAGE_COMMIT,
        "ACCEPTED_ANCHOR_ROOT_RELATIVE": ACCEPTED_ANCHOR_ROOT_RELATIVE,
        "INVALID_BRANCH": INVALID_BRANCH,
        "SOURCE_FAILURE_BRANCH": SOURCE_FAILURE_BRANCH,
        "POOLED_SUFFICIENT_BRANCH": NO_READ_SUFFICIENT_BRANCH,
        "INDEPENDENT_ADVANTAGE_BRANCH": READ_ADVANTAGE_BRANCH,
        "UNDERPOWERED_BRANCH": UNDERPOWERED_BRANCH,
        "NONFORMAL_BRANCH": NONFORMAL_BRANCH,
        "NON_EXECUTABLE_BRANCH": NON_EXECUTABLE_BRANCH,
        "SCALE_MARGIN": BASELINE_MARGIN,
        "FORMAL_REPLICATES": FORMAL_REPLICATES,
        "FORMAL_BRANCH_UPDATES": FORMAL_BRANCH_UPDATES,
        "FORMAL_NUM_ENVS": FORMAL_NUM_ENVS,
        "FORMAL_PPO_PASSES": FORMAL_PPO_PASSES,
        "FORMAL_EVAL_EPISODES": FORMAL_EVAL_EPISODES,
        "FORMAL_BOOTSTRAP_REPETITIONS": FORMAL_BOOTSTRAP_REPETITIONS,
        "EXERCISE_REPLICATES": EXERCISE_REPLICATES,
        "EXERCISE_BRANCH_UPDATES": EXERCISE_BRANCH_UPDATES,
        "EXERCISE_NUM_ENVS": EXERCISE_NUM_ENVS,
        "EXERCISE_PPO_PASSES": EXERCISE_PPO_PASSES,
        "EXERCISE_EVAL_EPISODES": EXERCISE_EVAL_EPISODES,
        "EXERCISE_BOOTSTRAP_REPETITIONS": EXERCISE_BOOTSTRAP_REPETITIONS,
        "SEED_BASES": SEED_BASES,
        "BOOTSTRAP_SEED": BOOTSTRAP_SEED,
        "NONFORMAL_SEED_OFFSET": NONFORMAL_SEED_OFFSET,
        "DEFAULT_CPU_BUDGET": DEFAULT_CPU_BUDGET,
        "DEFAULT_PROCESS_WORKERS": DEFAULT_PROCESS_WORKERS,
        "MAX_PROCESS_WORKERS": MAX_PROCESS_WORKERS,
        "WORKER_THREAD_ENV": WORKER_THREAD_ENV,
        "_configuration": _configuration,
        "source_controls": source_controls,
        "_training_replicate_worker": _training_replicate_worker,
        "_evaluation_cell_worker": _evaluation_cell_worker,
        "_cpu_parallel_benchmark_worker": _cpu_parallel_benchmark_worker,
        "_activate_single_thread_worker": _activate_single_thread_worker,
        "_training_errors": _training_errors,
        "_evaluation_errors": _evaluation_errors,
        "_comparison": _comparison,
        "select_g44_result_branch": select_g45_result_branch,
    }
    for name, value in values.items():
        setattr(_base, name, value)
    _base._patch_backend()
    _base._backend._training_errors = _training_errors
    _base._backend._evaluation_errors = _evaluation_errors


_patch_base_and_backend()
_backend = _base._backend


def _load_checkpoint_payload(
    path: Path,
    *,
    training: Mapping[str, Any],
    replicate: int,
    arm: str,
) -> Mapping[str, Any]:
    payload = _base._original_load_checkpoint_payload(
        path, training=training, replicate=replicate, arm=arm
    )
    certificate = payload.get("source_final_checkpoint_certificate")
    try:
        final_update = training["replicate_results"][replicate]["update_records"][-1]
        conclusion = training["conclusion_evidence"]
        baseline_gradient_groups = source._baseline_gradient_groups_from_pass(
            final_update["pass_records"][-1]
        )
    except (IndexError, KeyError, TypeError) as error:
        raise ValueError("G45 accepted-source checkpoint evidence mismatch") from error
    if (
        not isinstance(certificate, Mapping)
        or certificate.get("residual_evidence_arms") != list(source.ARMS)
        or not source._update_evidence_valid(certificate.get("final_update_evidence"))
        or certificate.get("final_update_evidence") != final_update
        or not source.validate_conclusion_evidence(
            certificate.get("conclusion_evidence")
        )
        or certificate.get("conclusion_evidence") != conclusion
        or not source.validate_baseline_gradient_groups_by_arm(
            certificate.get("baseline_gradient_groups_by_arm")
        )
        or certificate.get("baseline_gradient_groups_by_arm")
        != baseline_gradient_groups
        or not source._valid_composition(
            certificate.get("no_read_certificate"),
            source.BASELINE_SHADOW_NO_READ_ARM,
        )
        or certificate.get("baseline_checkpoint_selection_read_count") != 0
        or certificate.get("baseline_evaluation_metric_read_count") != 0
    ):
        raise ValueError("G45 accepted-source checkpoint evidence mismatch")
    return payload


_backend._load_checkpoint_payload = _load_checkpoint_payload

configure_runtime = _backend.configure_runtime
_runtime_identity = _backend._runtime_identity
_write_json = _backend._write_json
_read_json = _backend._read_json
_artifact_digest = _backend._artifact_digest
_resolve_cpu_execution = _backend._resolve_cpu_execution
_configure_cpu_execution = _backend._configure_cpu_execution
_native_backend_identity = _backend._native_backend_identity
seed_block = _backend.seed_block
bootstrap_seed = _backend.bootstrap_seed
_backend_train = _backend.train
_backend_evaluate = _backend.evaluate


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    accepted_anchor_root: Path | None,
    preflight_root: Path | None = None,
    alignment_disposition: str | None = None,
    aligned_source_commit: str | None = None,
    alignment_stage_commit: str | None = None,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    try:
        return _backend_train(
            run_root=run_root,
            source_commit=source_commit,
            formal=formal,
            authorization_token=authorization_token,
            accepted_anchor_root=accepted_anchor_root,
            preflight_root=preflight_root,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
            alignment_stage_commit=alignment_stage_commit,
            cpu_budget=cpu_budget,
            process_workers=process_workers,
        )
    except source.G45GradientGateError:
        raise
    except ValueError as error:
        raise ValueError(_g45_error_text(error)) from error
    except RuntimeError as error:
        raise RuntimeError(_g45_error_text(error)) from error


def evaluate(
    *,
    run_root: Path,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    try:
        return _backend_evaluate(
            run_root=run_root,
            cpu_budget=cpu_budget,
            process_workers=process_workers,
        )
    except ValueError as error:
        raise ValueError(_g45_error_text(error)) from error
    except RuntimeError as error:
        raise RuntimeError(_g45_error_text(error)) from error


def analyze(
    *,
    run_root: Path,
    require_formal: bool = False,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G45 analysis requires formal artifacts")
    configuration = _backend._cpu_configuration_from_artifact(
        training, formal=formal
    )
    requested = _resolve_cpu_execution(
        int(configuration["cpu_budget"]) if cpu_budget is None else cpu_budget,
        int(configuration["process_workers"])
        if process_workers is None
        else process_workers,
    )
    if (cpu_budget is not None or process_workers is not None) and (
        requested["cpu_budget"] != configuration["cpu_budget"]
        or requested["process_workers"] != configuration["process_workers"]
    ):
        raise ValueError("G45 analyze CPU/process settings differ from training")
    cpu_execution = _configure_cpu_execution(
        int(configuration["cpu_budget"]), int(configuration["process_workers"])
    )
    configure_runtime(bootstrap_seed(formal=formal))
    errors = _evaluation_errors(run_root, training, evaluation)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        plan = _backend._bootstrap_plan(
            formal=formal,
            replicates=int(configuration["replicates"]),
            episodes=int(configuration["evaluation_episodes_per_cell"]),
            repetitions=int(configuration["bootstrap_resamples"]),
        )
        access = {
            arm: _backend._arm_access(evaluation, arm, plan)
            for arm in source.ARMS
        }
        comparison = _comparison(evaluation, plan)
        metrics.update(
            {
                "source_valid": evaluation["direct_source_validation"] is True,
                "arm_access": access,
                "read_access_pass": access[source.BASELINE_READ_ARM]["access_pass"],
                "no_read_access_pass": access[source.BASELINE_SHADOW_NO_READ_ARM][
                    "access_pass"
                ],
                "read_access_confident_fail": access[source.BASELINE_READ_ARM][
                    "access_confident_fail"
                ],
                "no_read_access_confident_fail": access[
                    source.BASELINE_SHADOW_NO_READ_ARM
                ]["access_confident_fail"],
                "treatment_activation_valid": source.validate_conclusion_evidence(
                    training["conclusion_evidence"]
                ),
                **comparison,
            }
        )
    analysis_seconds = time.perf_counter() - started
    nonformal_total: float | None = None
    if not formal and not errors:
        nonformal_total = (
            float(training["stage_wall_time_seconds"])
            + float(evaluation["stage_wall_time_seconds"])
            + analysis_seconds
        )
    if errors:
        branch = INVALID_BRANCH
    elif formal:
        branch = select_g45_result_branch(metrics)
    elif nonformal_total is not None and nonformal_total <= NONFORMAL_WALL_CLOCK_CAP_SECONDS:
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
        "aligned_source_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "alignment_stage_commit": training.get("alignment_stage_commit"),
        "preflight_artifact_digests": training.get("preflight_artifact_digests"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "native_backend": evaluation.get("native_backend"),
        "cpu_execution": cpu_execution,
        "training_manifest_digest": _artifact_digest(
            run_root / "train_manifest.json"
        ),
        "evaluation_manifest_digest": _artifact_digest(
            run_root / "evaluation_manifest.json"
        ),
        "stage_wall_time_seconds": analysis_seconds,
        "nonformal_total_wall_time_seconds": nonformal_total,
        "nonformal_wall_clock_cap_seconds": NONFORMAL_WALL_CLOCK_CAP_SECONDS,
        "formal_projection_seconds": None,
        "formal_projection_executable": None,
        "formal_wall_clock_cap_seconds": FORMAL_WALL_CLOCK_CAP_SECONDS,
        "thresholds": {
            "utility_floor": UTILITY_FLOOR,
            "event_floor": EVENT_FLOOR,
            "segment_floor": SEGMENT_FLOOR,
            "process_noninferiority_margin": PROCESS_MARGIN,
            "stochastic_floor": STOCHASTIC_FLOOR,
            "minimum_replicate_floor": MINIMUM_REPLICATE_FLOOR,
            "baseline_margin": BASELINE_MARGIN,
        },
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def _execute_single_proof_update(
    accepted_anchor_root: Path,
) -> tuple[
    dict[str, source.g41.G41NoSlowProjection],
    dict[str, torch.optim.Optimizer],
    dict[str, object],
]:
    anchor = _backend._load_accepted_anchor(Path(accepted_anchor_root), 0)
    models = source.project_g45_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: source.g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    seeds = seed_block(0, formal=False)
    trajectory = _backend._collect_trajectory(
        models[source.BASELINE_READ_ARM],
        episode_ids=tuple(range(8)),
        ledger_seed=seeds["branch_gradient_probe"],
        action_seed=seeds["branch_gradient_probe"],
    )
    record = _backend._apply_matched_update(
        models,
        optimizers,
        {arm: trajectory for arm in source.ARMS},
        update_index=0,
        ledger_seed=seeds["branch_gradient_probe"],
        action_seed=seeds["branch_gradient_probe"],
    )
    return models, optimizers, record


def _g45_update_equivalence_worker(
    task: Mapping[str, object],
) -> dict[str, object]:
    _activate_single_thread_worker()
    index = int(task["index"])
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G45 update-proof worker output path is not fresh")
    models, optimizers, record = _execute_single_proof_update(
        Path(str(task["accepted_anchor_root"]))
    )
    canonical = source.serialize_diagnostics(record).encode("utf-8")
    semantic = {
        "model_state_digests": {
            arm: source.g41._state_digest(models[arm].state_dict())
            for arm in source.ARMS
        },
        "adam_state_digests": {
            arm: _base._optimizer_semantic_digest(optimizers[arm])
            for arm in source.ARMS
        },
        "evidence_sha256": hashlib.sha256(canonical).hexdigest(),
        "evidence_bytes": len(canonical),
        "actor_head_optimizer_steps": record["actor_head_optimizer_steps"],
        "branch_update_order": record["branch_update_order"],
        "passed": record["passed"],
    }
    payload = {
        "index": index,
        "pid": os.getpid(),
        "thread_environment": {
            name: os.environ.get(name) for name in WORKER_THREAD_ENV
        },
        "torch_intraop_threads": torch.get_num_threads(),
        "semantic": semantic,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, payload)
    return {
        "index": index,
        "output_path": str(output_path),
        "output_digest": _artifact_digest(output_path),
    }


def prove_two_process_update_equivalence(
    *, proof_root: Path, accepted_anchor_root: Path
) -> dict[str, object]:
    root = Path(proof_root).resolve()
    tasks = [
        {
            "index": index,
            "accepted_anchor_root": str(Path(accepted_anchor_root).resolve()),
            "output_path": str(root / f"worker_{index}" / "result.json"),
        }
        for index in range(2)
    ]
    results = _backend._run_indexed_worker_tasks(
        tasks, _g45_update_equivalence_worker, process_workers=2
    )
    payloads = [
        _read_json(Path(str(result["output_path"]))) for result in results
    ]
    equivalent = payloads[0]["semantic"] == payloads[1]["semantic"]
    distinct_processes = len({int(row["pid"]) for row in payloads}) == 2
    threads_valid = all(
        row["torch_intraop_threads"] == 1
        and all(
            row["thread_environment"].get(name) == "1"
            for name in WORKER_THREAD_ENV
        )
        for row in payloads
    )
    report = {
        "proof_kind": "two_process_single_g45_update_equivalence",
        "worker_count": 2,
        "distinct_processes": distinct_processes,
        "single_thread_workers": threads_valid,
        "deterministic_preassigned_index_merge": [
            row["index"] for row in payloads
        ]
        == [0, 1],
        "parameters_adam_evidence_bitwise_equivalent": equivalent,
        "semantic": payloads[0]["semantic"] if equivalent else None,
        "scientific_iteration_cost": 0,
        "formal": False,
        "proof_sized_updates_per_worker": 1,
        "passed": bool(equivalent and distinct_processes and threads_valid),
    }
    _write_json(root / "two_process_update_equivalence.json", report)
    if report["passed"] is not True:
        raise RuntimeError("G45 two-process update equivalence failed")
    return report


def readiness_interface_smoke(
    *, source_commit: str, accepted_anchor_root: Path
) -> dict[str, object]:
    row = _original_readiness_interface_smoke(
        source_commit=source_commit, accepted_anchor_root=accepted_anchor_root
    )
    row["return_schema"] = "G45_execution_readiness_train_manifest_v1"
    return row


# The inherited readiness lifecycle looks these names up dynamically.
_base.prove_two_process_update_equivalence = prove_two_process_update_equivalence
_base.readiness_interface_smoke = readiness_interface_smoke
readiness_train = _base.readiness_train
readiness_training_errors = _base.readiness_training_errors
reload_readiness_artifacts = _base.reload_readiness_artifacts
readiness_evaluate = _base.readiness_evaluate
readiness_evaluation_errors = _base.readiness_evaluation_errors
readiness_analyze = _base.readiness_analyze
validate_readiness_artifacts = _base.validate_readiness_artifacts


def exercise(
    *,
    run_root: Path,
    source_commit: str,
    accepted_anchor_root: Path,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    train(
        run_root=run_root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        accepted_anchor_root=accepted_anchor_root,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )
    evaluate(
        run_root=run_root,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )
    return analyze(
        run_root=run_root,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage",
        choices=(
            "train",
            "evaluate",
            "analyze",
            "exercise",
            "readiness-smoke",
            "readiness-train",
            "readiness-evaluate",
            "readiness-analyze",
        ),
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--accepted-anchor-root", type=Path)
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--alignment-disposition")
    parser.add_argument("--aligned-source-commit")
    parser.add_argument("--alignment-stage-commit")
    parser.add_argument("--cpu-budget", type=int)
    parser.add_argument("--process-workers", type=int)
    args = parser.parse_args()
    if args.stage == "readiness-smoke":
        if args.source_commit is None or args.accepted_anchor_root is None:
            raise ValueError("G45 readiness smoke requires source and anchor root")
        readiness_interface_smoke(
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
        )
    elif args.stage == "readiness-train":
        if args.source_commit is None or args.accepted_anchor_root is None:
            raise ValueError("G45 readiness train requires source and anchor root")
        readiness_train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
        )
    elif args.stage == "readiness-evaluate":
        readiness_evaluate(run_root=args.run_root)
    elif args.stage == "readiness-analyze":
        readiness_analyze(run_root=args.run_root)
    elif args.stage == "train":
        if args.source_commit is None:
            raise ValueError("G45 train requires --source-commit")
        train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            accepted_anchor_root=args.accepted_anchor_root,
            preflight_root=args.preflight_root,
            alignment_disposition=args.alignment_disposition,
            aligned_source_commit=args.aligned_source_commit,
            alignment_stage_commit=args.alignment_stage_commit,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )
    elif args.stage == "evaluate":
        evaluate(
            run_root=args.run_root,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )
    elif args.stage == "analyze":
        analyze(
            run_root=args.run_root,
            require_formal=args.formal,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )
    else:
        if args.source_commit is None or args.accepted_anchor_root is None:
            raise ValueError("G45 exercise requires source and anchor root")
        exercise(
            run_root=args.run_root,
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )


if __name__ == "__main__":
    main()
