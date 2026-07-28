"""Train, evaluate, and analyze frozen G46 baseline-shadow norm attribution."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
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
    continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46
    as source,
)
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32


def _load_isolated_g45_orchestration() -> Any:
    path = PROJECT_ROOT / (
        "scripts/run_continuous_roster_native_six_g31_shared_baseline_"
        "conditioning_attribution_g45.py"
    )
    name = "scripts._g46_isolated_g45_orchestration_backend"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("G46 could not load its accepted G45 orchestration")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_base = _load_isolated_g45_orchestration()

SCHEMA_VERSION = 2
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_"
    "ATTRIBUTION_G46_FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_"
    "ATTRIBUTION_G46_CODE_SCIENCE_ALIGNMENT_AUDIT"
)
# Exact target/stage mechanically established by the independent G46 audit.
ALIGNED_IMPLEMENTATION_COMMIT: str | None = (
    "ef3a2fa273d1506c2bc88f50db8e06810e946809"
)
ALIGNMENT_STAGE_COMMIT: str | None = (
    "d073d13317c09980863a700f6241573dd6709cdf"
)
ACCEPTED_ANCHOR_ROOT_RELATIVE = _base.ACCEPTED_ANCHOR_ROOT_RELATIVE

INVALID_BRANCH = (
    "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_"
    "ATTRIBUTION_G46"
)
SOURCE_FAILURE_BRANCH = "SOURCE_OR_REFERENCE_ACCESS_FAILURE_G46"
RAW_SUFFICIENT_BRANCH = "RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46"
SHADOW_ADVANTAGE_BRANCH = "BASELINE_SHADOW_NORM_SCHEDULE_ADVANTAGE_G46"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_BASELINE_SHADOW_NORM_ATTRIBUTION_G46"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_"
    "ATTRIBUTION_G46_EXERCISE_COMPLETE"
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
SHADOW_NORM_MARGIN = 0.05
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

# G46 inherits the accepted G45 source/RNG law unchanged.
SEED_BASES = dict(_base.SEED_BASES)
BOOTSTRAP_SEED = _base.BOOTSTRAP_SEED
NONFORMAL_SEED_OFFSET = _base.NONFORMAL_SEED_OFFSET
DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 2
MAX_PROCESS_WORKERS = 6
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}

_original_training_replicate_worker = _base._training_replicate_worker
_original_evaluation_cell_worker = _base._evaluation_cell_worker
_original_cpu_parallel_benchmark_worker = _base._cpu_parallel_benchmark_worker
_original_activate_single_thread_worker = _base._activate_single_thread_worker
_original_training_errors = _base._training_errors
_original_evaluation_errors = _base._evaluation_errors
_original_comparison = _base._comparison
_original_readiness_interface_smoke = _base.readiness_interface_smoke


def _activate_single_thread_worker() -> None:
    _original_activate_single_thread_worker()


def _training_replicate_worker(task: Mapping[str, object]) -> dict[str, object]:
    return _original_training_replicate_worker(task)


def _evaluation_cell_worker(task: Mapping[str, object]) -> dict[str, object]:
    return _original_evaluation_cell_worker(task)


def _cpu_parallel_benchmark_worker(
    task: Mapping[str, object],
) -> dict[str, object]:
    return _original_cpu_parallel_benchmark_worker(task)


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
    cpu = _base._resolve_cpu_execution(cpu_budget, process_workers)
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
        "accepted_g45_formal_source_commit": (
            source.ACCEPTED_G45_FORMAL_SOURCE_COMMIT
        ),
        "accepted_g45_aligned_implementation_commit": (
            source.ACCEPTED_G45_ALIGNED_IMPLEMENTATION_COMMIT
        ),
        "accepted_g45_alignment_stage_commit": (
            source.ACCEPTED_G45_ALIGNMENT_STAGE_COMMIT
        ),
        "aligned_g46_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
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
        "channel_composition": "literal_equal_mean_0.5",
        "channel_normalization": "independent_per_channel_RMS",
        "baseline_actor_read": "absent_in_both_actual_credit_paths",
        "treatment": "baseline_shadow_norm_schedule_vs_literal_raw_norm",
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
        "parent_source_id": source.g45.SOURCE_ID,
        "accepted_g40_manifest": source.g41.ACCEPTED_G40_MANIFEST,
        "accepted_g40_source_commit": source.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g45_formal_source_commit": (
            source.ACCEPTED_G45_FORMAL_SOURCE_COMMIT
        ),
        "accepted_g45_aligned_implementation_commit": (
            source.ACCEPTED_G45_ALIGNED_IMPLEMENTATION_COMMIT
        ),
        "accepted_g45_alignment_stage_commit": (
            source.ACCEPTED_G45_ALIGNMENT_STAGE_COMMIT
        ),
        "aligned_g46_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
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
    inherited = _original_comparison(evaluation, plan)
    return {
        "shadow_minus_raw_primary_ci95": inherited[
            "read_minus_no_read_primary_ci95"
        ],
        "shadow_minus_raw_capacity_ci95": inherited[
            "read_minus_no_read_capacity_ci95"
        ],
        "component_ci95": inherited["component_ci95"],
        "raw_noninferior": inherited["no_read_noninferior"],
        "material_shadow_norm_advantage": inherited[
            "material_baseline_conditioning_advantage"
        ],
        # Compatibility keys consumed by the private accepted G45 analyzer.
        "no_read_noninferior": inherited["no_read_noninferior"],
        "material_baseline_conditioning_advantage": inherited[
            "material_baseline_conditioning_advantage"
        ],
    }


def select_g46_result_branch(metrics: Mapping[str, Any]) -> str:
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
        return RAW_SUFFICIENT_BRANCH
    if bool(metrics["read_access_pass"]) and (
        bool(metrics["no_read_access_confident_fail"])
        or bool(metrics["material_baseline_conditioning_advantage"])
    ):
        return SHADOW_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def _g46_error_text(value: object) -> str:
    return (
        str(value)
        .replace("G43", "G46")
        .replace("G44", "G46")
        .replace("G45", "G46")
    )


def _training_errors(
    run_root: Path, training: Mapping[str, Any]
) -> list[str]:
    return [
        _g46_error_text(value)
        for value in _original_training_errors(run_root, training)
    ]


def _evaluation_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> list[str]:
    return [
        _g46_error_text(value)
        for value in _original_evaluation_errors(run_root, training, evaluation)
    ]


def _patch_private_orchestration() -> None:
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
        "NO_READ_SUFFICIENT_BRANCH": RAW_SUFFICIENT_BRANCH,
        "READ_ADVANTAGE_BRANCH": SHADOW_ADVANTAGE_BRANCH,
        "UNDERPOWERED_BRANCH": UNDERPOWERED_BRANCH,
        "NONFORMAL_BRANCH": NONFORMAL_BRANCH,
        "NON_EXECUTABLE_BRANCH": NON_EXECUTABLE_BRANCH,
        "BASELINE_MARGIN": SHADOW_NORM_MARGIN,
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
        "select_g45_result_branch": select_g46_result_branch,
        "_g45_error_text": _g46_error_text,
    }
    for name, value in values.items():
        setattr(_base, name, value)
    _base._patch_base_and_backend()
    _base._backend._training_errors = _training_errors
    _base._backend._evaluation_errors = _evaluation_errors


_patch_private_orchestration()
_backend = _base._backend

configure_runtime = _base.configure_runtime
_runtime_identity = _base._runtime_identity
_write_json = _base._write_json
_read_json = _base._read_json
_artifact_digest = _base._artifact_digest
_resolve_cpu_execution = _base._resolve_cpu_execution
_configure_cpu_execution = _base._configure_cpu_execution
_native_backend_identity = _base._native_backend_identity
seed_block = _base.seed_block
bootstrap_seed = _base.bootstrap_seed
_load_checkpoint_payload = _base._load_checkpoint_payload
train = _base.train
evaluate = _base.evaluate
analyze = _base.analyze


def _execute_single_proof_update(
    accepted_anchor_root: Path,
) -> tuple[
    dict[str, source.g41.G41NoSlowProjection],
    dict[str, torch.optim.Optimizer],
    dict[str, object],
]:
    anchor = _backend._load_accepted_anchor(Path(accepted_anchor_root), 0)
    models = source.project_g46_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: source.g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    seeds = seed_block(0, formal=False)
    trajectory = _backend._collect_trajectory(
        models[source.SHADOW_NORM_ARM],
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


def _g46_update_equivalence_worker(
    task: Mapping[str, object],
) -> dict[str, object]:
    _activate_single_thread_worker()
    index = int(task["index"])
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G46 update-proof worker output path is not fresh")
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
            arm: _base._base._optimizer_semantic_digest(optimizers[arm])
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
        tasks, _g46_update_equivalence_worker, process_workers=2
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
        "proof_kind": "two_process_single_g46_update_equivalence",
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
        raise RuntimeError("G46 two-process update equivalence failed")
    return report


def readiness_interface_smoke(
    *, source_commit: str, accepted_anchor_root: Path
) -> dict[str, object]:
    row = _original_readiness_interface_smoke(
        source_commit=source_commit, accepted_anchor_root=accepted_anchor_root
    )
    row["return_schema"] = "G46_execution_readiness_train_manifest_v1"
    return row


# The inherited readiness lifecycle resolves these names dynamically.
_base.prove_two_process_update_equivalence = prove_two_process_update_equivalence
_base.readiness_interface_smoke = readiness_interface_smoke
_base._base.prove_two_process_update_equivalence = (
    prove_two_process_update_equivalence
)
_base._base.readiness_interface_smoke = readiness_interface_smoke
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
            raise ValueError("G46 readiness smoke requires source and anchor root")
        readiness_interface_smoke(
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
        )
    elif args.stage == "readiness-train":
        if args.source_commit is None or args.accepted_anchor_root is None:
            raise ValueError("G46 readiness train requires source and anchor root")
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
            raise ValueError("G46 train requires --source-commit")
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
            raise ValueError("G46 exercise requires source and anchor root")
        exercise(
            run_root=args.run_root,
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )


if __name__ == "__main__":
    main()
