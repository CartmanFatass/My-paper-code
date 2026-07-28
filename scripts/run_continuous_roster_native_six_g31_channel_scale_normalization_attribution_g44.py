"""Train, evaluate, and analyze frozen G44 channel-scale attribution."""

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
from typing import Any, Mapping, Sequence

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

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44
    as source,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from scripts import run_continuous_roster_six_coordinate_cs_g38 as g38_runner


SCHEMA_VERSION = 2
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_"
    "ATTRIBUTION_G44_FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_"
    "ATTRIBUTION_G44_CODE_SCIENCE_ALIGNMENT_AUDIT"
)
# Formal admission is bound to the independent correction recheck and still
# requires an exact same-source nonformal preflight plus the authorization token.
ALIGNED_IMPLEMENTATION_COMMIT = "1a6e046801ab3d83830d4c9f6e9724c8c47659da"
ALIGNMENT_STAGE_COMMIT = "b55578a8e57f444895da59efe9268ebe31edf511"
ACCEPTED_ANCHOR_ROOT_RELATIVE = Path(
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1"
)

INVALID_BRANCH = (
    "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_ATTRIBUTION_G44"
)
SOURCE_FAILURE_BRANCH = "SOURCE_OR_REFERENCE_ACCESS_FAILURE_G44"
POOLED_SUFFICIENT_BRANCH = "POOLED_CHANNEL_SCALE_SUFFICIENT_G44"
INDEPENDENT_ADVANTAGE_BRANCH = "INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_CHANNEL_SCALE_ATTRIBUTION_G44"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_"
    "NORMALIZATION_ATTRIBUTION_G44_EXERCISE_COMPLETE"
)
NON_EXECUTABLE_BRANCH = "NON_EXECUTABLE_EVIDENCE_DESIGN"

FINAL_FIXED_DET = "FINAL_FIXED_DET"
FINAL_FIXED_STOCH = "FINAL_FIXED_STOCH"
FINAL_RANDOM_DET = "FINAL_RANDOM_DET"
FINAL_RANDOM_STOCH = "FINAL_RANDOM_STOCH"
MODEL_CELLS = (
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
SCALE_MARGIN = 0.05
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
    "branch_ledger": 10_441_000,
    "branch_action": 10_442_000,
    "branch_gradient_probe": 10_443_000,
    "evaluation_ledger": 10_444_000,
    "evaluation_process": 10_445_000,
    "evaluation_action": 10_446_000,
}
BOOTSTRAP_SEED = 10_447_044
NONFORMAL_SEED_OFFSET = 900_000
DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 2
MAX_PROCESS_WORKERS = 6
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}


def _load_isolated_orchestration_backend() -> Any:
    path = PROJECT_ROOT / (
        "scripts/run_continuous_roster_native_six_g31_db_norm_schedule_"
        "attribution_g43.py"
    )
    name = "scripts._g44_isolated_g43_orchestration_backend"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("G44 could not load its accepted orchestration backend")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_backend = _load_isolated_orchestration_backend()
_original_activate_single_thread_worker = _backend._activate_single_thread_worker
_original_training_replicate_worker = _backend._training_replicate_worker
_original_evaluation_cell_worker = _backend._evaluation_cell_worker
_original_cpu_parallel_benchmark_worker = _backend._cpu_parallel_benchmark_worker
_original_training_errors = _backend._training_errors
_original_evaluation_errors = _backend._evaluation_errors
_original_load_checkpoint_payload = _backend._load_checkpoint_payload


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


def _digest_semantic_value(digest: Any, value: object) -> None:
    if isinstance(value, torch.Tensor):
        row = value.detach().cpu().contiguous()
        digest.update(b"tensor")
        digest.update(str(row.dtype).encode("ascii"))
        digest.update(json.dumps(list(row.shape)).encode("ascii"))
        digest.update(row.numpy().tobytes())
    elif isinstance(value, Mapping):
        digest.update(b"mapping")
        for key in sorted(value, key=lambda item: str(item)):
            digest.update(str(key).encode("utf-8"))
            _digest_semantic_value(digest, value[key])
    elif isinstance(value, (list, tuple)):
        digest.update(b"sequence")
        for item in value:
            _digest_semantic_value(digest, item)
    else:
        digest.update(type(value).__name__.encode("ascii"))
        digest.update(repr(value).encode("utf-8"))


def _optimizer_semantic_digest(optimizer: torch.optim.Optimizer) -> str:
    digest = hashlib.sha256()
    _digest_semantic_value(digest, optimizer.state_dict())
    return digest.hexdigest()


def _execute_single_proof_update(
    accepted_anchor_root: Path,
) -> tuple[
    dict[str, g41.G41NoSlowProjection],
    dict[str, torch.optim.Optimizer],
    dict[str, object],
]:
    anchor = _backend._load_accepted_anchor(Path(accepted_anchor_root), 0)
    models = source.project_g44_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    seeds = _backend.seed_block(0, formal=False)
    trajectory = _backend._collect_trajectory(
        models[source.INDEPENDENT_ARM],
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


def _g44_update_equivalence_worker(
    task: Mapping[str, object],
) -> dict[str, object]:
    _activate_single_thread_worker()
    index = int(task["index"])
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G44 update-proof worker output path is not fresh")
    models, optimizers, record = _execute_single_proof_update(
        Path(str(task["accepted_anchor_root"]))
    )
    canonical_evidence = source.serialize_diagnostics(record).encode("utf-8")
    semantic = {
        "model_state_digests": {
            arm: g41._state_digest(models[arm].state_dict()) for arm in source.ARMS
        },
        "adam_state_digests": {
            arm: _optimizer_semantic_digest(optimizers[arm]) for arm in source.ARMS
        },
        "evidence_sha256": hashlib.sha256(canonical_evidence).hexdigest(),
        "evidence_bytes": len(canonical_evidence),
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
    _backend._write_json(output_path, payload)
    return {
        "index": index,
        "output_path": str(output_path),
        "output_digest": _backend._artifact_digest(output_path),
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
        tasks, _g44_update_equivalence_worker, process_workers=2
    )
    payloads = [
        _backend._read_json(Path(str(result["output_path"])))
        for result in results
    ]
    equivalent = payloads[0]["semantic"] == payloads[1]["semantic"]
    distinct_processes = len({int(payload["pid"]) for payload in payloads}) == 2
    threads_valid = all(
        payload["torch_intraop_threads"] == 1
        and all(
            payload["thread_environment"].get(name) == "1"
            for name in WORKER_THREAD_ENV
        )
        for payload in payloads
    )
    report = {
        "proof_kind": "two_process_single_g44_update_equivalence",
        "worker_count": 2,
        "distinct_processes": distinct_processes,
        "single_thread_workers": threads_valid,
        "deterministic_preassigned_index_merge": [
            payload["index"] for payload in payloads
        ]
        == [0, 1],
        "parameters_adam_evidence_bitwise_equivalent": equivalent,
        "semantic": payloads[0]["semantic"] if equivalent else None,
        "scientific_iteration_cost": 0,
        "formal": False,
        "proof_sized_updates_per_worker": 1,
        "passed": bool(equivalent and distinct_processes and threads_valid),
    }
    _backend._write_json(root / "two_process_update_equivalence.json", report)
    if report["passed"] is not True:
        raise RuntimeError("G44 two-process update equivalence failed")
    return report


def _g44_error_text(value: object) -> str:
    return str(value).replace("G43", "G44")


def _load_checkpoint_payload(
    path: Path,
    *,
    training: Mapping[str, Any],
    replicate: int,
    arm: str,
) -> Mapping[str, Any]:
    payload = _original_load_checkpoint_payload(
        path,
        training=training,
        replicate=replicate,
        arm=arm,
    )
    certificate = payload.get("source_final_checkpoint_certificate")
    try:
        records = training["replicate_results"][replicate]["update_records"]
        final_update = records[-1]
        conclusion = training["conclusion_evidence"]
    except (IndexError, KeyError, TypeError) as error:
        raise ValueError(
            "G44 accepted-source checkpoint normalization evidence mismatch"
        ) from error
    if (
        not isinstance(certificate, Mapping)
        or certificate.get("normalization_evidence_arms") != list(source.ARMS)
        or not source._update_evidence_valid(
            certificate.get("final_update_evidence")
        )
        or certificate.get("final_update_evidence") != final_update
        or not source.validate_conclusion_evidence(
            certificate.get("conclusion_evidence")
        )
        or certificate.get("conclusion_evidence") != conclusion
    ):
        raise ValueError(
            "G44 accepted-source checkpoint normalization evidence mismatch"
        )
    return payload


_backend._load_checkpoint_payload = _load_checkpoint_payload


def _training_errors(
    run_root: Path, training: Mapping[str, Any]
) -> list[str]:
    return [_g44_error_text(value) for value in _original_training_errors(run_root, training)]


def _evaluation_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> list[str]:
    return [
        _g44_error_text(value)
        for value in _original_evaluation_errors(run_root, training, evaluation)
    ]


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
    cpu = _backend._resolve_cpu_execution(cpu_budget, process_workers)
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
        "accepted_common_anchor_updates": g41.ACCEPTED_G40_COMPLETED_ANCHOR_UPDATES,
        "accepted_common_anchor_optimizer_steps": g41.ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS,
        "accepted_g40_source_commit": source.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g42_reference_source_commit": source.ACCEPTED_G42_REFERENCE_SOURCE_COMMIT,
        "accepted_g42_aligned_source_commit": source.ACCEPTED_G42_ALIGNED_SOURCE_COMMIT,
        "accepted_g42_alignment_stage_commit": source.ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT,
        "accepted_g43_source_commit": source.ACCEPTED_G43_SOURCE_COMMIT,
        "accepted_g43_aligned_source_commit": source.ACCEPTED_G43_ALIGNED_SOURCE_COMMIT,
        "accepted_g43_alignment_stage_commit": source.ACCEPTED_G43_ALIGNMENT_STAGE_COMMIT,
        "aligned_g44_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "training_capacity": g32.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "horizon": g32.HORIZON,
        "stored_training_observation_dim": 6,
        "actor_width": g40.g39.HIDDEN_DIM,
        "learning_rate": g40.LEARNING_RATE,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)",
        "gradient_clipping": "none",
        "minibatches": "none",
        "actor_head_optimizer": "native_six_actor|log_std|shared_two_output_baseline",
        "standalone_slow_critic": "absent",
        "direction_balance": "absent",
        "channel_composition": "literal_equal_mean_0.5",
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
        "parent_source_id": g43_source_id(),
        "accepted_g40_manifest": g41.ACCEPTED_G40_MANIFEST,
        "accepted_g40_source_commit": source.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g42_reference_source_commit": source.ACCEPTED_G42_REFERENCE_SOURCE_COMMIT,
        "accepted_g42_aligned_source_commit": source.ACCEPTED_G42_ALIGNED_SOURCE_COMMIT,
        "accepted_g42_alignment_stage_commit": source.ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT,
        "accepted_g43_source_commit": source.ACCEPTED_G43_SOURCE_COMMIT,
        "accepted_g43_aligned_source_commit": source.ACCEPTED_G43_ALIGNED_SOURCE_COMMIT,
        "accepted_g43_alignment_stage_commit": source.ACCEPTED_G43_ALIGNMENT_STAGE_COMMIT,
        "aligned_g44_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
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


def g43_source_id() -> str:
    return "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_P0"


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
        delta = _backend._difference(
            _backend._metric_arrays(evaluation, source.INDEPENDENT_ARM, cell, metric),
            _backend._metric_arrays(evaluation, source.POOLED_ARM, cell, metric),
        )
        if pooled:
            ci = _backend._hierarchical_ci(delta, capacities=g34.CAPACITIES, plan=plan)
            component_ci[name] = ci
            component_ucbs.append(ci[2])
        else:
            rows = {
                capacity: _backend._hierarchical_ci(
                    delta, capacities=(capacity,), plan=plan
                )
                for capacity in g34.CAPACITIES
            }
            component_ci[name] = rows
            component_ucbs.extend(row[2] for row in rows.values())
    transport = _backend._difference(
        _backend._difference(
            _backend._metric_arrays(
                evaluation, source.INDEPENDENT_ARM, FINAL_RANDOM_DET, "utility"
            ),
            _backend._metric_arrays(
                evaluation, source.INDEPENDENT_ARM, FINAL_FIXED_DET, "utility"
            ),
        ),
        _backend._difference(
            _backend._metric_arrays(
                evaluation, source.POOLED_ARM, FINAL_RANDOM_DET, "utility"
            ),
            _backend._metric_arrays(
                evaluation, source.POOLED_ARM, FINAL_FIXED_DET, "utility"
            ),
        ),
    )
    transport_rows = {
        capacity: _backend._hierarchical_ci(
            transport, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    component_ci["random_minus_fixed_transport"] = transport_rows
    component_ucbs.extend(row[2] for row in transport_rows.values())
    primary_values = _backend._difference(
        _backend._metric_arrays(
            evaluation, source.INDEPENDENT_ARM, FINAL_RANDOM_DET, "utility"
        ),
        _backend._metric_arrays(
            evaluation, source.POOLED_ARM, FINAL_RANDOM_DET, "utility"
        ),
    )
    primary = _backend._hierarchical_ci(
        primary_values, capacities=g34.CAPACITIES, plan=plan
    )
    capacity_primary = {
        capacity: _backend._hierarchical_ci(
            primary_values, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    noninferior = g38_runner._inclusive_le(primary[2], SCALE_MARGIN) and all(
        g38_runner._inclusive_le(value, SCALE_MARGIN) for value in component_ucbs
    )
    material = g38_runner._strict_gt(primary[0], SCALE_MARGIN) and all(
        g38_runner._strict_gt(capacity_primary[capacity][0], 0.0)
        for capacity in g34.CAPACITIES
    )
    return {
        "independent_minus_pooled_primary_ci95": primary,
        "independent_minus_pooled_capacity_ci95": capacity_primary,
        "component_ci95": component_ci,
        "pooled_noninferior": bool(noninferior),
        "material_independent_advantage": bool(material),
    }


def select_g44_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or bool(
        metrics["independent_access_confident_fail"]
    ):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics["independent_access_pass"])
        and bool(metrics["pooled_access_pass"])
        and bool(metrics["pooled_noninferior"])
    ):
        return POOLED_SUFFICIENT_BRANCH
    if bool(metrics["independent_access_pass"]) and (
        bool(metrics["pooled_access_confident_fail"])
        or bool(metrics["material_independent_advantage"])
    ):
        return INDEPENDENT_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def analyze(
    *,
    run_root: Path,
    require_formal: bool = False,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    training = _backend._read_json(run_root / "train_manifest.json")
    evaluation = _backend._read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G44 analysis requires formal artifacts")
    configuration = _backend._cpu_configuration_from_artifact(
        training, formal=formal
    )
    requested = _backend._resolve_cpu_execution(
        int(configuration["cpu_budget"]) if cpu_budget is None else cpu_budget,
        int(configuration["process_workers"])
        if process_workers is None
        else process_workers,
    )
    if (cpu_budget is not None or process_workers is not None) and (
        requested["cpu_budget"] != configuration["cpu_budget"]
        or requested["process_workers"] != configuration["process_workers"]
    ):
        raise ValueError("G44 analyze CPU/process settings differ from training")
    cpu_execution = _backend._configure_cpu_execution(
        int(configuration["cpu_budget"]), int(configuration["process_workers"])
    )
    _backend.configure_runtime(_backend.bootstrap_seed(formal=formal))
    errors = _backend._evaluation_errors(run_root, training, evaluation)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        plan = _backend._bootstrap_plan(
            formal=formal,
            replicates=int(configuration["replicates"]),
            episodes=int(configuration["evaluation_episodes_per_cell"]),
            repetitions=int(configuration["bootstrap_resamples"]),
        )
        access = {
            arm: _backend._arm_access(evaluation, arm, plan) for arm in source.ARMS
        }
        comparison = _comparison(evaluation, plan)
        metrics.update(
            {
                "source_valid": evaluation["direct_source_validation"] is True,
                "arm_access": access,
                "independent_access_pass": access[source.INDEPENDENT_ARM][
                    "access_pass"
                ],
                "pooled_access_pass": access[source.POOLED_ARM]["access_pass"],
                "independent_access_confident_fail": access[
                    source.INDEPENDENT_ARM
                ]["access_confident_fail"],
                "pooled_access_confident_fail": access[source.POOLED_ARM][
                    "access_confident_fail"
                ],
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
        branch = select_g44_result_branch(metrics)
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
        "training_manifest_digest": _backend._artifact_digest(
            run_root / "train_manifest.json"
        ),
        "evaluation_manifest_digest": _backend._artifact_digest(
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
            "scale_margin": SCALE_MARGIN,
        },
    }
    _backend._write_json(run_root / "analysis_result.json", result)
    return result


def _patch_backend() -> None:
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
        "MEAN_SUFFICIENT_BRANCH": POOLED_SUFFICIENT_BRANCH,
        "DBNORM_ADVANTAGE_BRANCH": INDEPENDENT_ADVANTAGE_BRANCH,
        "UNDERPOWERED_BRANCH": UNDERPOWERED_BRANCH,
        "NONFORMAL_BRANCH": NONFORMAL_BRANCH,
        "NON_EXECUTABLE_BRANCH": NON_EXECUTABLE_BRANCH,
        "NORM_MARGIN": SCALE_MARGIN,
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
        "select_g43_result_branch": select_g44_result_branch,
    }
    for name, value in values.items():
        setattr(_backend, name, value)


_patch_backend()

# Public mechanical interfaces are the isolated backend functions after G44 binding.
configure_runtime = _backend.configure_runtime
_runtime_identity = _backend._runtime_identity
_write_json = _backend._write_json
_read_json = _backend._read_json
_artifact_digest = _backend._artifact_digest
_state_digest = _backend._state_digest
_resolve_cpu_execution = _backend._resolve_cpu_execution
_configure_cpu_execution = _backend._configure_cpu_execution
_cpu_configuration_from_artifact = _backend._cpu_configuration_from_artifact
_valid_cpu_execution_record = _backend._valid_cpu_execution_record
_valid_worker_runtime = _backend._valid_worker_runtime
_native_backend_identity = _backend._native_backend_identity
_run_indexed_worker_tasks = _backend._run_indexed_worker_tasks
benchmark_cpu_process_parallelism = _backend.benchmark_cpu_process_parallelism
seed_block = _backend.seed_block
bootstrap_seed = _backend.bootstrap_seed
_expected_anchor_root = _backend._expected_anchor_root
_bind_anchor_root = _backend._bind_anchor_root
_validate_anchor_manifest = _backend._validate_anchor_manifest
_load_accepted_anchor = _backend._load_accepted_anchor
_collect_trajectory = _backend._collect_trajectory
_paired_source_audit = _backend._paired_source_audit
_continuation_audit = _backend._continuation_audit
_apply_matched_update = _backend._apply_matched_update
_checkpoint_reference = _backend._checkpoint_reference
_save_checkpoint = _backend._save_checkpoint
_validate_formal_preflight = _backend._validate_formal_preflight
_train_replicate = _backend._train_replicate
_consume_training_worker_result = _backend._consume_training_worker_result
train = _backend.train
_cell_contract = _backend._cell_contract
_load_final_model = _backend._load_final_model
_evaluate_cell = _backend._evaluate_cell
_consume_evaluation_worker_results = _backend._consume_evaluation_worker_results
evaluate = _backend.evaluate
_source_inventory = _backend._source_inventory
_arm_access = _backend._arm_access
_bootstrap_plan = _backend._bootstrap_plan


READINESS_BRANCH = "EXECUTION_READINESS_PROOF_COMPLETE"
READINESS_CHECKPOINT_KIND = "execution_readiness_proof_only"


def _require_source_commit(value: str) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError("G44 execution readiness requires an integrated source commit")


def _readiness_proof_inventory() -> dict[str, object]:
    return {
        "accepted_anchor_replicates": [0],
        "branch_updates_per_arm": 1,
        "num_envs": 8,
        "horizon": g32.HORIZON,
        "ppo_passes": source.PPO_PASSES,
        "training_transitions": len(source.ARMS) * 8 * g32.HORIZON,
        "optimizer_steps": len(source.ARMS) * source.PPO_PASSES,
        "evaluation_capacity": 8,
        "evaluation_cell": FINAL_RANDOM_DET,
        "evaluation_episodes_per_arm": 1,
        "bootstrap_resamples": 0,
        "conclusion_bearing": False,
        "scientific_iteration_cost": 0,
    }


def _readiness_training_configuration() -> dict[str, object]:
    configuration = dict(
        _configuration(
            formal=False,
            cpu_budget=DEFAULT_CPU_BUDGET,
            process_workers=DEFAULT_PROCESS_WORKERS,
        )
    )
    configuration.update(
        {
            "branch_updates_per_arm": 1,
            "training_transitions": len(source.ARMS) * 8 * g32.HORIZON,
            "optimizer_steps": len(source.ARMS) * source.PPO_PASSES,
            "execution_readiness_proof_only": True,
            "conclusion_bearing": False,
            "scientific_iteration_cost": 0,
        }
    )
    return configuration


def readiness_interface_smoke(
    *, source_commit: str, accepted_anchor_root: Path
) -> dict[str, object]:
    """Validate the production-shaped entry without starting experiment compute."""

    _require_source_commit(source_commit)
    anchor_root = _bind_anchor_root(Path(accepted_anchor_root))
    anchor_digests = _validate_anchor_manifest(anchor_root)
    configuration = _configuration(
        formal=False,
        cpu_budget=DEFAULT_CPU_BUDGET,
        process_workers=DEFAULT_PROCESS_WORKERS,
    )
    return {
        "entry": "readiness-train",
        "production_entry": "train",
        "source_commit": source_commit,
        "accepted_anchor_root": str(anchor_root),
        "accepted_anchor_artifact_digests": anchor_digests,
        "production_configuration": configuration,
        "proof_training_configuration": _readiness_training_configuration(),
        "proof_inventory": _readiness_proof_inventory(),
        "return_schema": "G44_execution_readiness_train_manifest_v1",
        "formal": False,
        "scientific_iteration_cost": 0,
    }


def _readiness_checkpoint_reference(arm: str) -> str:
    if arm not in source.ARMS:
        raise ValueError("G44 readiness checkpoint arm is not registered")
    return f"checkpoints/replicate_0_{arm.lower()}_execution_readiness.pt"


def _save_readiness_checkpoint(
    path: Path,
    *,
    source_commit: str,
    arm: str,
    model: g41.G41NoSlowProjection,
    update_evidence_sha256: str,
) -> dict[str, object]:
    state = {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": source_commit,
        "formal": False,
        "scientific_iteration_cost": 0,
        "conclusion_bearing": False,
        "replicate": 0,
        "arm": arm,
        "kind": READINESS_CHECKPOINT_KIND,
        "completed_branch_updates": 1,
        "actor_head_optimizer_steps": source.PPO_PASSES,
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(0),
        "model_state": state,
        "model_state_digest": g41._state_digest(state),
        "update_evidence_sha256": update_evidence_sha256,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    return payload


def _load_readiness_checkpoint(
    *,
    run_root: Path,
    training: Mapping[str, Any],
    arm: str,
) -> tuple[g41.G41NoSlowProjection, Mapping[str, Any]]:
    row = training["checkpoints"][arm]
    path = Path(run_root) / str(row["reference"])
    payload = torch.load(path, map_location="cpu", weights_only=False)
    state = payload.get("model_state") if isinstance(payload, Mapping) else None
    if (
        not isinstance(payload, Mapping)
        or payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("algorithm") != ALGORITHM_ID
        or payload.get("source_id") != source.SOURCE_ID
        or payload.get("source_commit") != training.get("source_commit")
        or payload.get("formal") is not False
        or payload.get("scientific_iteration_cost") != 0
        or payload.get("conclusion_bearing") is not False
        or payload.get("replicate") != 0
        or payload.get("arm") != arm
        or payload.get("kind") != READINESS_CHECKPOINT_KIND
        or payload.get("completed_branch_updates") != 1
        or payload.get("actor_head_optimizer_steps") != source.PPO_PASSES
        or payload.get("accepted_g40_anchor_authority")
        != g41.accepted_g40_anchor_identity(0)
        or not isinstance(state, Mapping)
        or payload.get("model_state_digest") != g41._state_digest(state)
        or payload.get("update_evidence_sha256")
        != training.get("update_evidence_sha256")
    ):
        raise ValueError("G44 readiness checkpoint identity mismatch")
    anchor_root = _bind_anchor_root(Path(str(training["accepted_anchor_root"])))
    anchor = _load_accepted_anchor(anchor_root, 0)
    models = source.project_g44_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    model = models[arm]
    model.load_state_dict(state, strict=True)
    if (
        g41._state_digest(model.state_dict()) != payload["model_state_digest"]
        or hasattr(model, "slow_critic")
    ):
        raise ValueError("G44 readiness checkpoint reload mismatch")
    return model, payload


def readiness_train(
    *, run_root: Path, source_commit: str, accepted_anchor_root: Path
) -> dict[str, Any]:
    """Run one non-conclusion-bearing update and write proof-only artifacts."""

    started = time.perf_counter()
    interface = readiness_interface_smoke(
        source_commit=source_commit,
        accepted_anchor_root=accepted_anchor_root,
    )
    root = Path(run_root).resolve()
    anchor_root = Path(str(interface["accepted_anchor_root"]))
    if root == anchor_root or anchor_root in root.parents:
        raise ValueError("G44 readiness root cannot write inside the anchor root")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("G44 readiness root must be absent or empty")
    root.mkdir(parents=True, exist_ok=True)
    cpu_execution = _configure_cpu_execution(
        DEFAULT_CPU_BUDGET, DEFAULT_PROCESS_WORKERS
    )
    configure_runtime(bootstrap_seed(formal=False))
    native_backend = _native_backend_identity()
    parallel = prove_two_process_update_equivalence(
        proof_root=root / "parallel_proof",
        accepted_anchor_root=anchor_root,
    )
    proof_configuration = _readiness_training_configuration()
    production_row = _backend._train_replicate(
        formal=False,
        replicate=0,
        configuration=proof_configuration,
        accepted_anchor_root=anchor_root,
    )
    models = production_row.pop("models")
    records = production_row["update_records"]
    if not isinstance(records, list) or len(records) != 1:
        raise RuntimeError("G44 readiness production entry update inventory mismatch")
    update = records[0]
    update_json = source.serialize_diagnostics(update)
    serialized_update = json.loads(update_json)
    update_digest = hashlib.sha256(update_json.encode("utf-8")).hexdigest()
    activation = source.build_conclusion_evidence([serialized_update], formal=False)
    if not source.validate_conclusion_evidence(activation):
        raise RuntimeError("G44 readiness treatment activation proof failed")
    checkpoints: dict[str, object] = {}
    for arm in source.ARMS:
        reference = _readiness_checkpoint_reference(arm)
        payload = _save_readiness_checkpoint(
            root / reference,
            source_commit=source_commit,
            arm=arm,
            model=models[arm],
            update_evidence_sha256=update_digest,
        )
        checkpoints[arm] = {
            "reference": reference,
            "file_digest": _artifact_digest(root / reference),
            "model_state_digest": payload["model_state_digest"],
        }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "train",
        "status": "COMPLETE",
        "artifact_kind": "execution_readiness_proof_only",
        "formal": False,
        "scientific_iteration_cost": 0,
        "conclusion_bearing": False,
        "source_commit": source_commit,
        "aligned_source_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "accepted_anchor_root": str(anchor_root),
        "accepted_anchor_root_mode": "read_only_input_no_writes",
        "accepted_anchor_artifact_digests": interface[
            "accepted_anchor_artifact_digests"
        ],
        "runtime": _runtime_identity(),
        "cpu_execution": cpu_execution,
        "native_backend": native_backend,
        "production_configuration": interface["production_configuration"],
        "proof_training_configuration": proof_configuration,
        "proof_inventory": interface["proof_inventory"],
        "source_controls": source_controls(),
        "two_process_update_equivalence": parallel,
        "two_process_update_equivalence_artifact": (
            "parallel_proof/two_process_update_equivalence.json"
        ),
        "two_process_update_equivalence_artifact_digest": _artifact_digest(
            root / "parallel_proof/two_process_update_equivalence.json"
        ),
        "update_evidence": serialized_update,
        "update_evidence_sha256": update_digest,
        "proof_activation_evidence": activation,
        "production_entry_result": production_row,
        "checkpoints": checkpoints,
        "stage_wall_time_seconds": time.perf_counter() - started,
    }
    _write_json(root / "train_manifest.json", manifest)
    return manifest


def readiness_training_errors(
    run_root: Path, training: Mapping[str, Any]
) -> list[str]:
    errors: list[str] = []
    root = Path(run_root).resolve()
    try:
        source_commit = str(training["source_commit"])
        interface = readiness_interface_smoke(
            source_commit=source_commit,
            accepted_anchor_root=Path(str(training["accepted_anchor_root"])),
        )
        production = interface["production_configuration"]
        if (
            training.get("schema_version") != SCHEMA_VERSION
            or training.get("algorithm") != ALGORITHM_ID
            or training.get("source_id") != source.SOURCE_ID
            or training.get("stage") != "train"
            or training.get("status") != "COMPLETE"
            or training.get("artifact_kind") != "execution_readiness_proof_only"
            or training.get("formal") is not False
            or training.get("scientific_iteration_cost") != 0
            or training.get("conclusion_bearing") is not False
            or training.get("aligned_source_commit")
            != ALIGNED_IMPLEMENTATION_COMMIT
            or training.get("accepted_anchor_root")
            != interface["accepted_anchor_root"]
            or training.get("accepted_anchor_root_mode")
            != "read_only_input_no_writes"
            or training.get("accepted_anchor_artifact_digests")
            != interface["accepted_anchor_artifact_digests"]
            or training.get("production_configuration") != production
            or training.get("proof_training_configuration")
            != interface["proof_training_configuration"]
            or training.get("proof_inventory") != interface["proof_inventory"]
            or training.get("source_controls") != source_controls()
            or not _valid_cpu_execution_record(
                training.get("cpu_execution"), production
            )
        ):
            raise ValueError("G44 readiness training identity mismatch")
        backend = training.get("native_backend")
        if (
            not isinstance(backend, Mapping)
            or backend.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
            or backend.get("required") is not True
            or backend.get("python_fallback") is not False
        ):
            raise ValueError("G44 readiness native backend mismatch")
        parallel_reference = str(
            training["two_process_update_equivalence_artifact"]
        )
        parallel_path = root / parallel_reference
        parallel = _read_json(parallel_path)
        if (
            parallel != training.get("two_process_update_equivalence")
            or training.get("two_process_update_equivalence_artifact_digest")
            != _artifact_digest(parallel_path)
            or parallel.get("passed") is not True
            or parallel.get("worker_count") != 2
            or parallel.get("distinct_processes") is not True
            or parallel.get("single_thread_workers") is not True
            or parallel.get("deterministic_preassigned_index_merge") is not True
            or parallel.get("parameters_adam_evidence_bitwise_equivalent")
            is not True
            or parallel.get("scientific_iteration_cost") != 0
        ):
            raise ValueError("G44 readiness two-process proof mismatch")
        update = training.get("update_evidence")
        if (
            not isinstance(update, Mapping)
            or not source._update_evidence_valid(update)
            or training.get("update_evidence_sha256")
            != hashlib.sha256(source.serialize_diagnostics(update).encode("utf-8")).hexdigest()
        ):
            raise ValueError("G44 readiness update evidence mismatch")
        production_row = training.get("production_entry_result")
        if (
            not isinstance(production_row, Mapping)
            or production_row.get("replicate") != 0
            or production_row.get("branch_update_order") != list(source.ARMS)
            or production_row.get("paired_collection_before_update") is not True
            or production_row.get("update_records") != [update]
            or production_row.get("actor_head_optimizer_steps")
            != {arm: float(source.PPO_PASSES) for arm in source.ARMS}
        ):
            raise ValueError("G44 readiness production entry result mismatch")
        activation = source.build_conclusion_evidence([update], formal=False)
        if (
            activation != training.get("proof_activation_evidence")
            or not source.validate_conclusion_evidence(activation)
        ):
            raise ValueError("G44 readiness activation proof mismatch")
        checkpoints = training.get("checkpoints")
        if not isinstance(checkpoints, Mapping) or set(checkpoints) != set(source.ARMS):
            raise ValueError("G44 readiness checkpoint inventory mismatch")
        expected_names = set()
        for arm in source.ARMS:
            row = checkpoints[arm]
            reference = _readiness_checkpoint_reference(arm)
            if (
                not isinstance(row, Mapping)
                or row.get("reference") != reference
                or row.get("file_digest") != _artifact_digest(root / reference)
            ):
                raise ValueError("G44 readiness checkpoint digest mismatch")
            _, payload = _load_readiness_checkpoint(
                run_root=root, training=training, arm=arm
            )
            if row.get("model_state_digest") != payload["model_state_digest"]:
                raise ValueError("G44 readiness checkpoint reload mismatch")
            expected_names.add(Path(reference).name)
        if {path.name for path in (root / "checkpoints").iterdir()} != expected_names:
            raise ValueError("G44 readiness checkpoint set mismatch")
    except (KeyError, OSError, TypeError, ValueError) as error:
        errors.append(str(error))
    return errors


def reload_readiness_artifacts(run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    training = _read_json(root / "train_manifest.json")
    errors = readiness_training_errors(root, training)
    if errors:
        raise ValueError("G44 readiness reload rejected: " + " | ".join(errors))
    rows: dict[str, object] = {}
    for arm in source.ARMS:
        model, _ = _load_readiness_checkpoint(
            run_root=root, training=training, arm=arm
        )
        rows[arm] = {
            "model_state_digest": g41._state_digest(model.state_dict()),
            "phase": model.phase,
            "standalone_slow_critic_present": hasattr(model, "slow_critic"),
        }
    return {"passed": True, "arms": rows}


def readiness_evaluate(*, run_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    root = Path(run_root).resolve()
    evaluation_path = root / "evaluation_manifest.json"
    if evaluation_path.exists():
        raise ValueError("G44 readiness evaluation artifact already exists")
    training = _read_json(root / "train_manifest.json")
    errors = readiness_training_errors(root, training)
    if errors:
        raise ValueError("G44 readiness training invalid: " + " | ".join(errors))
    configure_runtime(seed_block(0, formal=False)["evaluation_action"])
    processes, inventory = _source_inventory(
        replicate=0, capacity=8, episode_count=6, formal=False
    )
    cells: list[dict[str, object]] = []
    for arm in source.ARMS:
        model, _ = _load_readiness_checkpoint(
            run_root=root, training=training, arm=arm
        )
        cell = _evaluate_cell(
            replicate=0,
            capacity=8,
            arm=arm,
            name=FINAL_RANDOM_DET,
            processes=processes[:1],
            action_seed=seed_block(0, formal=False)["evaluation_action"],
            deployed=model,
        )
        cells.append(cell)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "artifact_kind": "execution_readiness_proof_only",
        "formal": False,
        "scientific_iteration_cost": 0,
        "conclusion_bearing": False,
        "source_commit": training["source_commit"],
        "native_backend": _native_backend_identity(),
        "training_manifest_digest": _artifact_digest(root / "train_manifest.json"),
        "source_inventory": inventory,
        "executed_episode_ids": [processes[0].episode_id],
        "cells": cells,
        "stage_wall_time_seconds": time.perf_counter() - started,
    }
    _write_json(evaluation_path, manifest)
    return manifest


def readiness_evaluation_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> list[str]:
    errors = readiness_training_errors(run_root, training)
    if errors:
        return errors
    root = Path(run_root).resolve()
    try:
        processes, inventory = _source_inventory(
            replicate=0, capacity=8, episode_count=6, formal=False
        )
        cells = evaluation.get("cells")
        if (
            evaluation.get("schema_version") != SCHEMA_VERSION
            or evaluation.get("algorithm") != ALGORITHM_ID
            or evaluation.get("source_id") != source.SOURCE_ID
            or evaluation.get("stage") != "evaluate"
            or evaluation.get("status") != "COMPLETE"
            or evaluation.get("artifact_kind")
            != "execution_readiness_proof_only"
            or evaluation.get("formal") is not False
            or evaluation.get("scientific_iteration_cost") != 0
            or evaluation.get("conclusion_bearing") is not False
            or evaluation.get("source_commit") != training.get("source_commit")
            or evaluation.get("training_manifest_digest")
            != _artifact_digest(root / "train_manifest.json")
            or evaluation.get("source_inventory") != inventory
            or evaluation.get("executed_episode_ids") != [processes[0].episode_id]
            or not isinstance(cells, list)
            or len(cells) != len(source.ARMS)
        ):
            raise ValueError("G44 readiness evaluation identity mismatch")
        backend = evaluation.get("native_backend")
        if (
            not isinstance(backend, Mapping)
            or backend.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
            or backend.get("required") is not True
            or backend.get("python_fallback") is not False
        ):
            raise ValueError("G44 readiness evaluation backend mismatch")
        for arm, cell in zip(source.ARMS, cells, strict=True):
            if (
                cell.get("replicate") != 0
                or cell.get("capacity") != 8
                or cell.get("arm") != arm
                or cell.get("cell") != FINAL_RANDOM_DET
                or cell.get("optimizer_steps") != 0
                or cell.get("lifecycle_valid") is not True
                or len(cell.get("episodes", [])) != 1
                or cell.get("state_before") != cell.get("state_after")
            ):
                raise ValueError("G44 readiness evaluation cell mismatch")
    except (KeyError, OSError, TypeError, ValueError) as error:
        errors.append(str(error))
    return errors


def readiness_analyze(*, run_root: Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    analysis_path = root / "analysis_result.json"
    if analysis_path.exists():
        raise ValueError("G44 readiness analysis artifact already exists")
    training = _read_json(root / "train_manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    errors = readiness_evaluation_errors(root, training, evaluation)
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "artifact_kind": "execution_readiness_proof_only",
        "formal": False,
        "scientific_iteration_cost": 0,
        "conclusion_bearing": False,
        "science_disposition": None,
        "source_commit": training.get("source_commit"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": READINESS_BRANCH if not errors else INVALID_BRANCH,
        "training_manifest_digest": _artifact_digest(root / "train_manifest.json"),
        "evaluation_manifest_digest": _artifact_digest(
            root / "evaluation_manifest.json"
        ),
        "proof_checks": {
            "parameters_adam_evidence_bitwise_equivalent": training[
                "two_process_update_equivalence"
            ]["parameters_adam_evidence_bitwise_equivalent"],
            "artifact_reload": reload_readiness_artifacts(root)["passed"],
            "evaluate_entry_completed": not errors,
            "scientific_thresholds_evaluated": False,
        },
    }
    _write_json(analysis_path, result)
    if errors:
        raise ValueError("G44 readiness analysis invalid: " + " | ".join(errors))
    return result


def validate_readiness_artifacts(run_root: Path) -> list[str]:
    root = Path(run_root).resolve()
    try:
        training = _read_json(root / "train_manifest.json")
        evaluation = _read_json(root / "evaluation_manifest.json")
        analysis = _read_json(root / "analysis_result.json")
    except (OSError, TypeError, ValueError) as error:
        return [str(error)]
    errors = readiness_evaluation_errors(root, training, evaluation)
    if (
        analysis.get("schema_version") != SCHEMA_VERSION
        or analysis.get("algorithm") != ALGORITHM_ID
        or analysis.get("source_id") != source.SOURCE_ID
        or analysis.get("stage") != "analyze"
        or analysis.get("status") != "COMPLETE"
        or analysis.get("artifact_kind") != "execution_readiness_proof_only"
        or analysis.get("formal") is not False
        or analysis.get("scientific_iteration_cost") != 0
        or analysis.get("conclusion_bearing") is not False
        or analysis.get("science_disposition") is not None
        or analysis.get("source_commit") != training.get("source_commit")
        or analysis.get("operational_valid") is not True
        or analysis.get("operational_errors") != []
        or analysis.get("branch") != READINESS_BRANCH
        or analysis.get("training_manifest_digest")
        != _artifact_digest(root / "train_manifest.json")
        or analysis.get("evaluation_manifest_digest")
        != _artifact_digest(root / "evaluation_manifest.json")
        or analysis.get("proof_checks")
        != {
            "parameters_adam_evidence_bitwise_equivalent": True,
            "artifact_reload": True,
            "evaluate_entry_completed": True,
            "scientific_thresholds_evaluated": False,
        }
    ):
        errors.append("G44 readiness analysis identity mismatch")
    return errors


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
            raise ValueError(
                "G44 readiness smoke requires source and accepted anchor root"
            )
        readiness_interface_smoke(
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
        )
    elif args.stage == "readiness-train":
        if args.source_commit is None or args.accepted_anchor_root is None:
            raise ValueError(
                "G44 readiness train requires source and accepted anchor root"
            )
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
            raise ValueError("G44 train requires --source-commit")
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
            raise ValueError("G44 exercise requires source and accepted anchor root")
        exercise(
            run_root=args.run_root,
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )


if __name__ == "__main__":
    main()
