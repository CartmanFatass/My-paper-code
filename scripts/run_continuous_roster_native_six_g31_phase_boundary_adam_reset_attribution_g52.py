"""Train, evaluate, analyze, and readiness-check frozen G52 attribution."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import re
import sys
import time
import tracemalloc
from typing import Any, Mapping, Sequence


_THREAD_ENV_NAMES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
for _thread_name in _THREAD_ENV_NAMES:
    os.environ[_thread_name] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import (
    continuous_roster_native_six_g31_phase_boundary_adam_reset_attribution_g52
    as source,
)
from scripts import (
    run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50
    as g50_runner,
)


_base = g50_runner._base
_backend = g50_runner._backend

SCHEMA_VERSION = source.SCHEMA_VERSION
ALGORITHM_ID = source.ALGORITHM_ID
SOURCE_ID = source.SOURCE_ID
IMPLEMENTATION_HANDOFF_SHA256 = (
    "c94ae40590c79959943e9624b124c1649d990e82a81c4266de8c551e590f782c"
)
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_BOUNDARY_ADAM_RESET_ATTRIBUTION_"
    "G52_FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_BOUNDARY_ADAM_RESET_ATTRIBUTION_"
    "G52_CODE_SCIENCE_ALIGNMENT_AUDIT"
)
# These bindings are deliberately absent in the implementation candidate.
# Root/CPM must publish and align the exact clean candidate before formal
# admission can become true; no caller-provided value can bypass this closure.
ALIGNED_IMPLEMENTATION_COMMIT: str | None = None
ALIGNMENT_STAGE_COMMIT: str | None = None
ALIGNMENT_DISPOSITION: str | None = None

INVALID_BRANCH = source.INVALID_RESULT
SOURCE_FAILURE_BRANCH = source.SOURCE_FAILURE_RESULT
NULL_SUFFICIENT_BRANCH = source.PERSISTENT_SUFFICIENT_RESULT
REFERENCE_ADVANTAGE_BRANCH = source.RESET_ADVANTAGE_RESULT
UNDERPOWERED_BRANCH = source.UNDERPOWERED_RESULT
FIRST_MATCH_ORDER = source.RESULT_BRANCHES
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_BOUNDARY_ADAM_RESET_"
    "ATTRIBUTION_G52_EXERCISE_COMPLETE"
)

FINAL_FIXED_DET = _base.FINAL_FIXED_DET
FINAL_FIXED_STOCH = _base.FINAL_FIXED_STOCH
FINAL_RANDOM_DET = _base.FINAL_RANDOM_DET
FINAL_RANDOM_STOCH = _base.FINAL_RANDOM_STOCH
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
MATERIALITY_MARGIN = source.MATERIALITY_MARGIN
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
FORMAL_WALL_CLOCK_CAP_SECONDS = 28_800.0

DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 2
MAX_CPU_BUDGET = 6
MAX_PROCESS_WORKERS = 6
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}

TRAIN_MANIFEST = "train_manifest.json"
EVALUATION_MANIFEST = "evaluation_manifest.json"
ANALYSIS_RESULT = "analysis_result.json"
CHECKPOINT_DIRECTORY = "checkpoints"
READINESS_TRAIN = "readiness_train.json"
READINESS_STATE = "readiness_boundary.pt"
READINESS_VALIDATION = "readiness_validation.json"
READINESS_RELOAD = "readiness_reload.json"
READINESS_EVALUATION = "readiness_evaluation.json"
READINESS_ANALYSIS = "readiness_analysis.json"
READINESS_ARTIFACTS = (
    READINESS_TRAIN,
    READINESS_STATE,
    READINESS_VALIDATION,
    READINESS_RELOAD,
    READINESS_EVALUATION,
    READINESS_ANALYSIS,
)


def _valid_commit(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _valid_digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"G52 artifact is not an object: {path}")
    return value


def _artifact_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    """Canonicalize JSON values without key or scalar string coercion.

    Tuples intentionally normalize to JSON arrays, matching the Torch-to-JSON
    readiness boundary. Unsupported objects, non-string mapping keys, and
    nonfinite floating-point values fail closed.
    """

    def normalize(row: object) -> object:
        if row is None or isinstance(row, (bool, str, int)):
            return row
        if isinstance(row, float):
            if not math.isfinite(row):
                raise ValueError("G52 canonical JSON contains nonfinite float")
            return row
        if isinstance(row, Mapping):
            if any(not isinstance(key, str) for key in row):
                raise TypeError("G52 canonical JSON mapping key is not a string")
            return {key: normalize(item) for key, item in row.items()}
        if isinstance(row, (list, tuple)):
            return [normalize(item) for item in row]
        raise TypeError(f"G52 canonical JSON unsupported value: {type(row).__name__}")

    return json.dumps(
        normalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _readiness_certificates_match(training_value: object, state_value: object) -> bool:
    if not source.validate_boundary_activation_certificate(training_value):
        return False
    if not source.validate_boundary_activation_certificate(state_value):
        return False
    try:
        training_bytes = _canonical_json_bytes(training_value)
        state_bytes = _canonical_json_bytes(state_value)
    except (TypeError, ValueError, OverflowError):
        return False
    return bool(
        training_bytes == state_bytes
        and hashlib.sha256(training_bytes).digest()
        == hashlib.sha256(state_bytes).digest()
    )


def _activate_single_thread_worker() -> None:
    for name in _THREAD_ENV_NAMES:
        os.environ[name] = "1"
    torch.set_num_threads(1)


def _resolve_cpu_execution(
    cpu_budget: int | None, process_workers: int | None
) -> dict[str, object]:
    cpu = DEFAULT_CPU_BUDGET if cpu_budget is None else int(cpu_budget)
    workers = DEFAULT_PROCESS_WORKERS if process_workers is None else int(process_workers)
    if not 1 <= cpu <= MAX_CPU_BUDGET or not 1 <= workers <= MAX_PROCESS_WORKERS:
        raise ValueError("G52 CPU/process settings outside frozen support")
    if workers > cpu:
        raise ValueError("G52 process workers exceed CPU budget")
    return {
        "cpu_budget": cpu,
        "process_workers": workers,
        "supported_cpu_budget_ceiling": MAX_CPU_BUDGET,
        "supported_process_worker_ceiling": MAX_PROCESS_WORKERS,
        "worker_thread_controls": dict(WORKER_THREAD_ENV),
        "torch_intraop_threads": 1,
        "worker_start_method": "spawn",
        "process_isolation": "one_preassigned_replicate_per_task",
        "deterministic_merge": "preassigned_index_not_completion_order",
        "cpu_continuous_adaptation": False,
    }


def _configure_cpu_execution(
    cpu_budget: int | None, process_workers: int | None
) -> dict[str, object]:
    row = _resolve_cpu_execution(cpu_budget, process_workers)
    _activate_single_thread_worker()
    row["hardware_logical_cpu_count"] = int(os.cpu_count() or 1)
    row["effective_parent_torch_intraop_threads"] = torch.get_num_threads()
    return row


def _valid_cpu_execution_record(
    value: object, configuration: Mapping[str, object]
) -> bool:
    if not isinstance(value, Mapping):
        return False
    expected = _resolve_cpu_execution(
        int(configuration["cpu_budget"]), int(configuration["process_workers"])
    )
    return bool(
        all(value.get(name) == expected[name] for name in expected)
        and isinstance(value.get("hardware_logical_cpu_count"), int)
        and not isinstance(value.get("hardware_logical_cpu_count"), bool)
        and int(value["hardware_logical_cpu_count"]) >= 1
        and value.get("effective_parent_torch_intraop_threads") == 1
    )


def _valid_worker_runtime(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    environment = value.get("thread_environment")
    numeric = ("wall_time_seconds", "process_cpu_seconds")
    return bool(
        isinstance(value.get("pid"), int)
        and not isinstance(value.get("pid"), bool)
        and int(value["pid"]) > 0
        and all(
            isinstance(value.get(name), (int, float))
            and not isinstance(value.get(name), bool)
            and math.isfinite(float(value[name]))
            and float(value[name]) >= 0.0
            for name in numeric
        )
        and isinstance(value.get("python_peak_traced_bytes"), int)
        and not isinstance(value.get("python_peak_traced_bytes"), bool)
        and int(value["python_peak_traced_bytes"]) >= 0
        and value.get("torch_intraop_threads") == 1
        and isinstance(environment, Mapping)
        and dict(environment) == dict(WORKER_THREAD_ENV)
    )


def _worker_telemetry(
    *, started_wall: float, started_cpu: float, peak_bytes: int
) -> dict[str, object]:
    return {
        "pid": os.getpid(),
        "wall_time_seconds": time.perf_counter() - started_wall,
        "process_cpu_seconds": time.process_time() - started_cpu,
        "python_peak_traced_bytes": int(peak_bytes),
        "torch_intraop_threads": torch.get_num_threads(),
        "thread_environment": {
            name: os.environ.get(name) for name in _THREAD_ENV_NAMES
        },
    }


def _runtime_identity() -> dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "numpy": np.__version__,
        "platform": sys.platform,
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


def _checkpoint_model_state_digest(checkpoint: Mapping[str, object]) -> str:
    state = dict(checkpoint["actor_state"])  # type: ignore[arg-type]
    state["policy.log_std"] = checkpoint["log_std"]
    return _state_digest(state)  # type: ignore[arg-type]


def _configuration(
    *, formal: bool, cpu_budget: int | None = None, process_workers: int | None = None
) -> dict[str, object]:
    static = source.static_configuration_certificate(formal=formal)
    cpu = _resolve_cpu_execution(cpu_budget, process_workers)
    return {
        **static,
        "formal": bool(formal),
        "phase_A_updates_per_ancestor": static["phase_A_updates"],
        "branch_updates_per_arm": static["phase_B_updates_per_arm"],
        "evaluation_episodes_per_cell": static["episodes_per_cell"],
        "cpu_budget": cpu["cpu_budget"],
        "process_workers": cpu["process_workers"],
        "supported_cpu_budget_ceiling": MAX_CPU_BUDGET,
        "supported_process_worker_ceiling": MAX_PROCESS_WORKERS,
        "worker_start_method": "spawn",
        "training_parallel_unit": "independent_common_ancestor_root",
        "evaluation_parallel_unit": "replicate_capacity_cell",
        "process_isolation": "one_preassigned_replicate_per_task",
        "deterministic_merge": "preassigned_index_not_completion_order",
        "worker_thread_controls": dict(WORKER_THREAD_ENV),
        "torch_intraop_threads": 1,
        "training_capacity": roster_env.TRAIN_CAPACITY,
        "cells_per_arm_capacity": len(MODEL_CELLS),
        "evaluation_optimizer_steps": 0,
        "common_phase_A_ancestor_count": int(static["replicates"]),
        "forks_are_not_independent_units": True,
        "first_phase_B_batch_common_then_later_on_policy_separate": True,
        "checkpoint_selection": "final_only",
        "episode_exclusions": "none",
    }


def source_controls() -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "accepted_ancestry": list(source.ACCEPTED_ANCESTRY),
        "fresh_end_to_end_lifecycle": True,
        "predecessor_checkpoint_initialization": False,
        "predecessor_optimizer_initialization": False,
        "predecessor_trajectory_initialization": False,
        "predecessor_manifest_or_run_root_initialization": False,
        "phase_A_model_class": "G51NoBaselinePhaseAProjection",
        "phase_A_credit_baselines_package": False,
        "phase_A_objective": "G49_SINGLE_IMMEDIATE",
        "phase_B_objective": "G49_SINGLE_IMMEDIATE",
        "retained_actor_parameter_names": list(source.ACTOR_PARAMETER_NAMES),
        "retained_actor_parameter_count": 17,
        "training_source": "G32_capacity8_fixed_process",
        "evaluation_source": "G34_P0_fixed_and_random_processes_capacity_6_8_12",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_python_fallback": False,
        "paired_exogenous_assignments": True,
        "forced_common_post_first_step_trajectories": False,
        "seed_bases": dict(source.SEED_BASES),
        "bootstrap_seed": source.BOOTSTRAP_SEED,
        "nonformal_seed_offset": source.NONFORMAL_SEED_OFFSET,
        "H": source.HORIZON,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
    }


def _fresh_root(root: Path) -> Path:
    resolved = Path(root).resolve()
    if resolved.exists() and any(resolved.iterdir()):
        raise ValueError("G52 run root is not fresh")
    return resolved


def _checkpoint_reference(replicate: int, arm: str) -> str:
    if arm not in source.ARMS:
        raise ValueError("G52 checkpoint arm is not registered")
    token = "reset" if arm == source.RESET_ARM else "carry"
    return f"{CHECKPOINT_DIRECTORY}/replicate_{replicate}_{token}_final.pt"


def _preflight_digests(root: Path) -> dict[str, str]:
    return {
        "training": _artifact_digest(root / TRAIN_MANIFEST),
        "evaluation": _artifact_digest(root / EVALUATION_MANIFEST),
        "analysis": _artifact_digest(root / ANALYSIS_RESULT),
    }


def _valid_nonformal_preflight(root: Path, *, source_commit: str) -> dict[str, str]:
    training = _read_json(root / TRAIN_MANIFEST)
    evaluation = _read_json(root / EVALUATION_MANIFEST)
    analysis = _read_json(root / ANALYSIS_RESULT)
    expected = _configuration(formal=False, cpu_budget=2, process_workers=2)
    errors = [
        *_training_errors(root, training),
        *_evaluation_errors(root, training, evaluation),
        *_analysis_errors(root, training, evaluation, analysis),
    ]
    if (
        errors
        or training.get("formal") is not False
        or training.get("source_commit") != source_commit
        or training.get("configuration") != expected
        or evaluation.get("formal") is not False
        or evaluation.get("source_commit") != source_commit
        or evaluation.get("configuration") != expected
        or analysis.get("formal") is not False
        or analysis.get("source_commit") != source_commit
        or analysis.get("result_branch") != NONFORMAL_BRANCH
        or analysis.get("operational_valid") is not True
        or analysis.get("scientific_branch_selected") is not False
        or analysis.get("metrics", {}).get("treatment_activation_valid") is not True
    ):
        raise ValueError("G52 same-source preflight complete-artifact validation failed")
    times = tuple(
        float(row.get("stage_wall_time_seconds", float("nan")))
        for row in (training, evaluation, analysis)
    )
    if any(not np.isfinite(value) or value < 0.0 for value in times):
        raise ValueError("G52 preflight timing invalid")
    if sum(times) > NONFORMAL_WALL_CLOCK_CAP_SECONDS:
        raise ValueError("G52 nonformal preflight wall-clock cap exceeded")
    if 1.25 * (30.0 * times[0] + 24.0 * times[1] + 40.0 * times[2]) > FORMAL_WALL_CLOCK_CAP_SECONDS:
        raise ValueError("G52 formal wall-clock projection exceeds cap")
    return _preflight_digests(root)


def validate_formal_admission(**arguments: object) -> dict[str, object]:
    errors: list[str] = []
    source_commit = arguments.get("source_commit")
    if arguments.get("authorization_token") != AUTHORIZATION_TOKEN:
        errors.append("authorization_token")
    if not _valid_commit(ALIGNED_IMPLEMENTATION_COMMIT) or source_commit != ALIGNED_IMPLEMENTATION_COMMIT:
        errors.append("aligned_implementation_commit")
    if ALIGNMENT_DISPOSITION != "ALIGNED" or arguments.get("alignment_disposition") != "ALIGNED":
        errors.append("alignment_disposition")
    if arguments.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT:
        errors.append("aligned_source_commit")
    if not _valid_commit(ALIGNMENT_STAGE_COMMIT) or arguments.get("alignment_stage_commit") != ALIGNMENT_STAGE_COMMIT:
        errors.append("alignment_stage_commit")
    if arguments.get("implementation_handoff_sha256") != IMPLEMENTATION_HANDOFF_SHA256:
        errors.append("implementation_handoff_binding")
    try:
        cpu = _resolve_cpu_execution(
            arguments.get("cpu_budget"), arguments.get("process_workers")  # type: ignore[arg-type]
        )
        if cpu["cpu_budget"] != 2 or cpu["process_workers"] != 2:
            errors.append("formal_cpu_process_configuration")
    except (TypeError, ValueError):
        errors.append("formal_cpu_process_configuration")
    digests: dict[str, str] | None = None
    preflight_root = arguments.get("preflight_root")
    if preflight_root is None or not isinstance(source_commit, str):
        errors.append("same_source_nonformal_preflight")
    else:
        try:
            digests = _valid_nonformal_preflight(
                Path(str(preflight_root)).resolve(), source_commit=source_commit
            )
        except (FileNotFoundError, KeyError, TypeError, ValueError):
            errors.append("same_source_nonformal_preflight")
    return {"admitted": not errors, "errors": errors, "preflight_digests": digests}


def _collect_phase_A(
    model: source.g51.G51NoBaselinePhaseAProjection,
    *, episode_ids: Sequence[int], ledger_seed: int, action_seed: int
) -> Any:
    return source.g40.collect_g40_trajectory(
        model,
        episode_ids=episode_ids,
        ledger_seed=int(ledger_seed),
        action_seed=int(action_seed),
        device=torch.device("cpu"),
    )


def _collect_phase_B(
    model: source.g50.G50PhaseBProjection,
    *, episode_ids: Sequence[int], ledger_seed: int, action_seed: int
) -> Any:
    return _base._collect_trajectory(
        model,
        episode_ids=episode_ids,
        ledger_seed=int(ledger_seed),
        action_seed=int(action_seed),
    )


def _train_replicate(
    *, formal: bool, replicate: int, configuration: Mapping[str, object]
) -> dict[str, object]:
    seeds = source.seed_block(replicate, formal=formal)
    _backend.configure_runtime(seeds["phase_A_gradient_probe"])
    phase_A_model, phase_A_optimizer = source.make_fresh_phase_A_ancestor(
        member_capacity=roster_env.TRAIN_CAPACITY,
        initialization_seed=seeds["initialization"],
    )
    phase_A_initial_digest = source._actor_digest(phase_A_model)
    phase_A_records: list[dict[str, object]] = []
    phase_A_updates = int(configuration["phase_A_updates"])
    for update_index in range(phase_A_updates):
        first = update_index * source.NUM_ENVS
        trajectory = _collect_phase_A(
            phase_A_model,
            episode_ids=tuple(range(first, first + source.NUM_ENVS)),
            ledger_seed=(
                seeds["phase_A_gradient_probe"]
                if update_index == 0
                else seeds["phase_A_ledger"]
            ),
            action_seed=(
                seeds["phase_A_gradient_probe"]
                if update_index == 0
                else seeds["phase_A_action"]
            ),
        )
        phase_A_records.append(
            source.optimize_phase_A_update(
                phase_A_model,
                phase_A_optimizer,
                trajectory,
                update_index=update_index,
            )
        )
    expected_boundary_step = phase_A_updates * source.PPO_PASSES
    source.snapshot_actor_adam_state(
        phase_A_model, phase_A_optimizer, expected_step=expected_boundary_step
    )
    models, optimizers, boundary = source.project_phase_B_arms(
        phase_A_model,
        phase_A_optimizer,
        completed_phase_A_updates=phase_A_updates,
        expected_step=expected_boundary_step,
    )
    if source._actor_digest(models[source.RESET_ARM]) != source._actor_digest(
        models[source.CARRY_ARM]
    ):
        raise RuntimeError("G52 pre-boundary arm drift")

    phase_B_updates = int(configuration["phase_B_updates_per_arm"])
    first_batch = _collect_phase_B(
        models[source.RESET_ARM],
        episode_ids=tuple(range(source.NUM_ENVS)),
        ledger_seed=seeds["phase_B_gradient_probe"],
        action_seed=seeds["phase_B_gradient_probe"],
    )
    first_update, activation = source.execute_first_phase_B_update(
        models,
        optimizers,
        first_batch,
        carry_install_evidence=boundary["CARRY_install"],  # type: ignore[arg-type]
    )
    phase_B_records: list[dict[str, object]] = [first_update]
    for update_index in range(1, phase_B_updates):
        first = update_index * source.NUM_ENVS
        episode_ids = tuple(range(first, first + source.NUM_ENVS))
        trajectories = {
            arm: source.g47._actor_only_trajectory_view(
                _collect_phase_B(
                    models[arm],
                    episode_ids=episode_ids,
                    ledger_seed=seeds["phase_B_ledger"],
                    action_seed=seeds["phase_B_action"],
                )
            )
            for arm in source.ARMS
        }
        phase_B_records.append(
            source.optimize_phase_B_update(
                models,
                optimizers,
                trajectories,
                update_index=update_index,
            )
        )
    checkpoints = {
        arm: source.build_final_checkpoint(
            model=models[arm],
            optimizer=optimizers[arm],
            source_commit=str(configuration["source_commit"]),
            formal=formal,
            replicate=replicate,
            arm=arm,
            completed_phase_A_updates=phase_A_updates,
            completed_phase_B_updates=phase_B_updates,
            configuration={
                key: value for key, value in configuration.items() if key != "source_commit"
            },
            seeds=seeds,
            boundary_evidence=boundary,
            activation_certificate=activation,
        )
        for arm in source.ARMS
    }
    return {
        "replicate": replicate,
        "seeds": seeds,
        "fresh_initialization_count": 1,
        "common_phase_A_ancestor_count": 1,
        "phase_A_initial_actor_digest": phase_A_initial_digest,
        "phase_A_final_actor_digest": boundary["ancestor_actor_digest"],
        "phase_A_update_records": phase_A_records,
        "phase_boundary_evidence": boundary,
        "first_phase_B_activation_certificate": activation,
        "phase_B_update_records": phase_B_records,
        "later_arm_specific_on_policy_collection": phase_B_updates > 1,
        "paired_exogenous_assignments": True,
        "forced_common_post_first_step_trajectories": False,
        "checkpoints": checkpoints,
        "proof_activity": {
            "diagnostic_real_transitions": 0,
            "diagnostic_optimizer_steps": 0,
            "bootstrap_resamples": 0,
        },
    }


def _training_replicate_worker(task: Mapping[str, object]) -> dict[str, object]:
    _activate_single_thread_worker()
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G52 training worker output path is not fresh")
    started = time.perf_counter()
    row = _train_replicate(
        formal=bool(task["formal"]),
        replicate=int(task["replicate"]),
        configuration=dict(task["configuration"]),  # type: ignore[arg-type]
    )
    payload = {
        "index": int(task["index"]),
        "row": row,
        "pid": os.getpid(),
        "wall_time_seconds": time.perf_counter() - started,
        "thread_environment": {name: os.environ.get(name) for name in _THREAD_ENV_NAMES},
        "torch_intraop_threads": torch.get_num_threads(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, output_path)
    return {
        "index": int(task["index"]),
        "output_path": str(output_path),
        "output_digest": _artifact_digest(output_path),
    }


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None = None,
    preflight_root: Path | None = None,
    alignment_disposition: str | None = None,
    aligned_source_commit: str | None = None,
    alignment_stage_commit: str | None = None,
    implementation_handoff_sha256: str | None = None,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    if not _valid_commit(source_commit):
        raise ValueError("G52 train requires a lowercase integrated source commit")
    root = _fresh_root(run_root)
    admission: dict[str, object] | None = None
    if formal:
        admission = validate_formal_admission(
            source_commit=source_commit,
            authorization_token=authorization_token,
            preflight_root=preflight_root,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
            alignment_stage_commit=alignment_stage_commit,
            implementation_handoff_sha256=implementation_handoff_sha256,
            cpu_budget=cpu_budget,
            process_workers=process_workers,
        )
        if admission["admitted"] is not True:
            raise ValueError("G52 formal admission failed: " + "|".join(admission["errors"]))  # type: ignore[arg-type]
    elif any(
        value is not None
        for value in (
            authorization_token,
            preflight_root,
            alignment_disposition,
            aligned_source_commit,
            alignment_stage_commit,
            implementation_handoff_sha256,
        )
    ):
        raise ValueError("G52 nonformal train cannot carry formal authority")

    started = time.perf_counter()
    cpu = _configure_cpu_execution(cpu_budget, process_workers)
    configuration = _configuration(
        formal=formal,
        cpu_budget=int(cpu["cpu_budget"]),
        process_workers=int(cpu["process_workers"]),
    )
    worker_configuration = {**configuration, "source_commit": source_commit}
    native_backend = _backend._native_backend_identity()
    root.mkdir(parents=True, exist_ok=True)
    (root / CHECKPOINT_DIRECTORY).mkdir(exist_ok=True)
    tasks = [
        {
            "index": replicate,
            "replicate": replicate,
            "formal": formal,
            "configuration": worker_configuration,
            "output_path": str(
                root
                / ".worker_transport"
                / "train"
                / f"replicate_{replicate}"
                / "result.pt"
            ),
        }
        for replicate in range(int(configuration["replicates"]))
    ]
    results = _backend._run_indexed_worker_tasks(
        tasks,
        _training_replicate_worker,
        process_workers=int(configuration["process_workers"]) if formal else 1,
    )
    rows: list[dict[str, Any]] = []
    for result in results:
        path = Path(str(result["output_path"]))
        payload = torch.load(path, map_location="cpu", weights_only=False)
        if payload.get("index") != int(result["index"]):
            raise RuntimeError("G52 training worker identity mismatch")
        row = dict(payload["row"])
        checkpoints = row.pop("checkpoints")
        arm_rows: dict[str, object] = {}
        for arm in source.ARMS:
            reference = _checkpoint_reference(int(row["replicate"]), arm)
            checkpoint_path = root / reference
            torch.save(checkpoints[arm], checkpoint_path)
            arm_rows[arm] = {
                "final_checkpoint": reference,
                "final_checkpoint_sha256": _artifact_digest(checkpoint_path),
                "final_model_state_digest": _checkpoint_model_state_digest(
                    checkpoints[arm]
                ),
                "completed_phase_A_updates": configuration["phase_A_updates"],
                "completed_phase_B_updates": configuration["phase_B_updates_per_arm"],
            }
        row["arms"] = arm_rows
        row["worker_execution"] = {
            "preassigned_index": int(result["index"]),
            "pid": int(payload["pid"]),
            "output_digest": result["output_digest"],
            "wall_time_seconds": payload["wall_time_seconds"],
            "thread_environment": payload["thread_environment"],
            "torch_intraop_threads": payload["torch_intraop_threads"],
        }
        rows.append(row)
        path.unlink()
    activation = {
        "certificate_kind": "G52_FORMAL_ROOT_ACTIVATION_INVENTORY_V1",
        "root_count": len(rows),
        "q_r": [
            row["first_phase_B_activation_certificate"]["norms"]["q_r"] for row in rows
        ],
        "every_root_certificate_structurally_valid": all(
            source.validate_boundary_activation_certificate(
                row["first_phase_B_activation_certificate"]
            )
            for row in rows
        ),
        "every_root_boundary_operationally_valid": all(
            row["first_phase_B_activation_certificate"][
                "boundary_operationally_valid"
            ]
            is True
            for row in rows
        ),
        "every_root_active": all(
            row["first_phase_B_activation_certificate"]["active"] is True for row in rows
        ),
        "every_root_scientifically_valid": all(
            row["first_phase_B_activation_certificate"]["scientifically_valid"]
            is True
            for row in rows
        ),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": formal,
        "formal_statistical_run": formal,
        "scientific_iteration_cost": 1 if formal else 0,
        "source_commit": source_commit,
        "authorization_token": authorization_token,
        "alignment_audit_id": ALIGNMENT_AUDIT_ID if formal else None,
        "alignment_disposition": alignment_disposition,
        "aligned_source_commit": aligned_source_commit,
        "alignment_stage_commit": alignment_stage_commit,
        "implementation_handoff_sha256": IMPLEMENTATION_HANDOFF_SHA256,
        "preflight_root": str(Path(preflight_root).resolve()) if preflight_root else None,
        "preflight_artifact_digests": None if admission is None else admission["preflight_digests"],
        # The accepted backend schema retains this field.  G52 binds it to
        # ``None`` because no predecessor/anchor artifact may initialize or
        # otherwise supply this lifecycle.
        "accepted_anchor_artifact_digests": None,
        "configuration": configuration,
        "source_controls": source_controls(),
        "native_backend": native_backend,
        "cpu_execution": cpu,
        "conclusion_evidence": activation,
        "replicate_results": rows,
        "checkpoint_selection": "final_only",
        "work_accounting": {
            "scientific_real_transitions": configuration["training_real_transitions"],
            "scientific_optimizer_steps": configuration["optimizer_steps"],
            "proof_real_transitions": 0,
            "proof_optimizer_steps": 0,
            "bootstrap_resamples": 0,
        },
        "stage_wall_time_seconds": time.perf_counter() - started,
    }
    _write_json(root / TRAIN_MANIFEST, manifest)
    return manifest


def _load_checkpoint_payload(
    path: Path,
    *,
    training: Mapping[str, Any],
    replicate: int,
    arm: str,
) -> Mapping[str, Any]:
    value = torch.load(path, map_location="cpu", weights_only=False)
    if (
        not source.validate_final_checkpoint(value)
        or value.get("source_commit") != training.get("source_commit")
        or value.get("formal") is not training.get("formal")
        or value.get("replicate") != replicate
        or value.get("arm") != arm
        or value.get("configuration") != training.get("configuration")
        or value.get("seed_block")
        != source.seed_block(replicate, formal=bool(training["formal"]))
    ):
        raise ValueError("G52 final checkpoint identity/schema mismatch")
    return value


def _load_final_model(
    *,
    run_root: Path,
    training: Mapping[str, Any],
    replicate: int,
    capacity: int,
    arm: str,
) -> source.g50.G50PhaseBProjection:
    reference = training["replicate_results"][replicate]["arms"][arm]["final_checkpoint"]
    checkpoint = _load_checkpoint_payload(
        run_root / reference,
        training=training,
        replicate=replicate,
        arm=arm,
    )
    return source.load_phase_B_checkpoint_model(checkpoint, member_capacity=capacity)


def _expected_checkpoint_files(configuration: Mapping[str, object]) -> set[str]:
    return {
        _checkpoint_reference(replicate, arm)
        for replicate in range(int(configuration["replicates"]))
        for arm in source.ARMS
    }


def _valid_native_backend(value: object) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("kind") == "ContinuousRosterToyBatch_CPU_CPP"
        and value.get("required") is True
        and value.get("python_fallback") is False
        and isinstance(value.get("module"), str)
        and bool(value.get("module"))
        and isinstance(value.get("build_identity"), (str, Mapping))
    )


def _training_errors(run_root: Path, training: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    formal = training.get("formal")
    if formal not in (True, False):
        return ["G52 training formal flag invalid"]
    try:
        configuration = training["configuration"]
        expected = _configuration(
            formal=bool(formal),
            cpu_budget=int(configuration["cpu_budget"]),
            process_workers=int(configuration["process_workers"]),
        )
    except (KeyError, TypeError, ValueError):
        return ["G52 training configuration invalid"]
    conclusion = training.get("conclusion_evidence")
    work = training.get("work_accounting")
    if (
        training.get("schema_version") != SCHEMA_VERSION
        or training.get("algorithm_id") != ALGORITHM_ID
        or training.get("source_id") != SOURCE_ID
        or training.get("stage") != "train"
        or training.get("status") != "COMPLETE"
        or training.get("configuration") != expected
        or training.get("source_controls") != source_controls()
        or not _valid_commit(training.get("source_commit"))
        or training.get("formal_statistical_run") is not formal
        or training.get("scientific_iteration_cost") != (1 if formal else 0)
        or training.get("implementation_handoff_sha256") != IMPLEMENTATION_HANDOFF_SHA256
        or training.get("accepted_anchor_artifact_digests") is not None
        or (
            formal is False
            and any(
                training.get(name) is not None
                for name in (
                    "authorization_token", "alignment_audit_id",
                    "alignment_disposition", "aligned_source_commit",
                    "alignment_stage_commit", "preflight_root",
                    "preflight_artifact_digests",
                )
            )
        )
        or (
            formal is True
            and (
                training.get("authorization_token") != AUTHORIZATION_TOKEN
                or training.get("alignment_audit_id") != ALIGNMENT_AUDIT_ID
                or training.get("alignment_disposition") != "ALIGNED"
                or training.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
                or training.get("alignment_stage_commit") != ALIGNMENT_STAGE_COMMIT
                or not isinstance(training.get("preflight_root"), str)
                or not isinstance(training.get("preflight_artifact_digests"), Mapping)
            )
        )
        or training.get("checkpoint_selection") != "final_only"
        or not isinstance(conclusion, Mapping)
        or conclusion.get("every_root_certificate_structurally_valid") is not True
        or not isinstance(work, Mapping)
        or work.get("scientific_real_transitions")
        != expected["training_real_transitions"]
        or work.get("scientific_optimizer_steps") != expected["optimizer_steps"]
        or work.get("proof_real_transitions") != 0
        or work.get("proof_optimizer_steps") != 0
        or work.get("bootstrap_resamples") != 0
        or not _valid_cpu_execution_record(training.get("cpu_execution"), expected)
        or not _valid_native_backend(training.get("native_backend"))
        or not isinstance(training.get("stage_wall_time_seconds"), (int, float))
        or isinstance(training.get("stage_wall_time_seconds"), bool)
        or not math.isfinite(float(training["stage_wall_time_seconds"]))
        or not 0.0 <= float(training["stage_wall_time_seconds"]) <= float(expected["wall_clock_cap_seconds"])
    ):
        errors.append("G52 training manifest identity/configuration/activation mismatch")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(expected["replicates"]):
        errors.append("G52 training replicate inventory mismatch")
        return errors
    actual_files = {
        str(path.relative_to(run_root)).replace("\\", "/")
        for path in (run_root / CHECKPOINT_DIRECTORY).glob("*.pt")
    }
    if actual_files != _expected_checkpoint_files(expected):
        errors.append("G52 final checkpoint inventory mismatch")
    seen_pids: set[int] = set()
    for replicate, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("replicate") != replicate:
            errors.append("G52 replicate identity mismatch")
            continue
        certificate = row.get("first_phase_B_activation_certificate")
        if not source.validate_boundary_activation_certificate(certificate):
            errors.append("G52 boundary activation certificate invalid")
        phase_A_records = row.get("phase_A_update_records")
        phase_B_records = row.get("phase_B_update_records")
        boundary = row.get("phase_boundary_evidence")
        proof = row.get("proof_activity")
        if (
            row.get("fresh_initialization_count") != 1
            or row.get("common_phase_A_ancestor_count") != 1
            or row.get("seeds")
            != source.seed_block(replicate, formal=bool(formal))
            or not isinstance(phase_A_records, list)
            or len(phase_A_records) != int(expected["phase_A_updates"])
            or [record.get("update_index") for record in phase_A_records]
            != list(range(int(expected["phase_A_updates"])))
            or any(
                record.get("PPO_passes") != source.PPO_PASSES
                or record.get("optimizer_steps") != source.PPO_PASSES
                or record.get("passed") is not True
                or not isinstance(record.get("records"), list)
                or len(record["records"]) != source.PPO_PASSES
                or any(
                    pass_row.get("pass_index") != pass_index
                    or pass_row.get("optimizer_step")
                    != int(record["update_index"]) * source.PPO_PASSES + pass_index + 1
                    or not _valid_digest(pass_row.get("target_digest"))
                    or not _valid_digest(pass_row.get("normalized_target_digest"))
                    or not _valid_digest(pass_row.get("assigned_gradient_digest"))
                    for pass_index, pass_row in enumerate(record["records"])
                )
                for record in phase_A_records
            )
            or not _valid_digest(row.get("phase_A_initial_actor_digest"))
            or row.get("phase_A_final_actor_digest") != boundary.get("ancestor_actor_digest")
            or not isinstance(boundary, Mapping)
            or boundary.get("passed") is not True
            or boundary.get("completed_phase_A_updates")
            != expected["phase_A_updates"]
            or boundary.get("expected_boundary_step")
            != int(expected["phase_A_updates"]) * source.PPO_PASSES
            or boundary.get("RESET_empty_Adam") is not True
            or not isinstance(boundary.get("CARRY_install"), Mapping)
            or boundary["CARRY_install"].get("passed") is not True
            or not isinstance(certificate, Mapping)
            or certificate.get("pre_step_actor_digest")
            != boundary.get("ancestor_actor_digest")
            or boundary.get("projected_actor_digests")
            != {arm: boundary.get("ancestor_actor_digest") for arm in source.ARMS}
            or certificate.get("CARRY_installed_Adam_digest")
            != boundary["CARRY_install"].get("installed_state_digest")
            or certificate.get("CARRY_boundary_step")
            != boundary.get("expected_boundary_step")
            or not isinstance(phase_B_records, list)
            or len(phase_B_records) != int(expected["phase_B_updates_per_arm"])
            or [record.get("update_index") for record in phase_B_records]
            != list(range(int(expected["phase_B_updates_per_arm"])))
            or phase_B_records[0].get("first_step_certificate") != certificate
            or phase_B_records[0].get("optimizer_steps_per_arm")
            != source.PPO_PASSES
            or phase_B_records[0].get("PPO_passes_per_arm") != source.PPO_PASSES
            or phase_B_records[0].get("passed") is not True
            or phase_B_records[0].get("certificate_structurally_valid") is not True
            or phase_B_records[0].get("first_batch_materialized_before_either_step") is not True
            or phase_B_records[0].get("both_first_step_plans_materialized_before_either_step") is not True
            or phase_B_records[0].get("first_step_actor_batch_target_gradient_equal") is not True
            or phase_B_records[0].get("boundary_operationally_valid")
            is not certificate.get("boundary_operationally_valid")
            or phase_B_records[0].get("treatment_active") is not certificate.get("active")
            or any(
                record.get("separate_on_policy_collection") is not True
                or record.get("paired_exogenous_assignments_only") is not True
                or record.get("forced_common_actions_or_trajectories") is not False
                or record.get("optimizer_steps_per_arm") != source.PPO_PASSES
                or record.get("PPO_passes_per_arm") != source.PPO_PASSES
                or record.get("passed") is not True
                or not isinstance(record.get("records"), list)
                or len(record["records"]) != source.PPO_PASSES
                or any(
                    pass_row.get("pass_index") != pass_index
                    or pass_row.get("plans_materialized_before_either_step") is not True
                    or set(pass_row.get("arm_specific_trajectory_digests", {})) != set(source.ARMS)
                    or set(pass_row.get("arm_specific_target_digests", {})) != set(source.ARMS)
                    or any(not _valid_digest(value) for value in pass_row.get("arm_specific_trajectory_digests", {}).values())
                    or any(not _valid_digest(value) for value in pass_row.get("arm_specific_target_digests", {}).values())
                    for pass_index, pass_row in enumerate(record["records"])
                )
                for record in phase_B_records[1:]
            )
            or row.get("later_arm_specific_on_policy_collection")
            is not (int(expected["phase_B_updates_per_arm"]) > 1)
            or row.get("paired_exogenous_assignments") is not True
            or row.get("forced_common_post_first_step_trajectories") is not False
            or proof
            != {
                "diagnostic_real_transitions": 0,
                "diagnostic_optimizer_steps": 0,
                "bootstrap_resamples": 0,
            }
        ):
            errors.append("G52 replicate lifecycle/count/proof inventory mismatch")
        worker = row.get("worker_execution")
        if (
            not isinstance(worker, Mapping)
            or worker.get("preassigned_index") != replicate
            or worker.get("torch_intraop_threads") != 1
            or worker.get("thread_environment") != dict(WORKER_THREAD_ENV)
            or not isinstance(worker.get("pid"), int)
            or isinstance(worker.get("pid"), bool)
            or int(worker["pid"]) <= 0
            or not isinstance(worker.get("output_digest"), str)
            or re.fullmatch(r"[0-9a-f]{64}", worker["output_digest"]) is None
            or not isinstance(worker.get("wall_time_seconds"), (int, float))
            or isinstance(worker.get("wall_time_seconds"), bool)
            or not math.isfinite(float(worker["wall_time_seconds"]))
            or float(worker["wall_time_seconds"]) < 0.0
        ):
            errors.append("G52 worker preassigned-index mismatch")
        else:
            seen_pids.add(int(worker["pid"]))
        arms = row.get("arms")
        if not isinstance(arms, Mapping) or set(arms) != set(source.ARMS):
            errors.append("G52 checkpoint arm inventory mismatch")
            continue
        for arm in source.ARMS:
            reference = _checkpoint_reference(replicate, arm)
            path = run_root / reference
            try:
                if (
                    arms[arm].get("final_checkpoint") != reference
                    or arms[arm].get("final_checkpoint_sha256") != _artifact_digest(path)
                ):
                    raise ValueError
                checkpoint = _load_checkpoint_payload(
                    path,
                    training=training,
                    replicate=replicate,
                    arm=arm,
                )
                if (
                    arms[arm].get("final_model_state_digest")
                    != _checkpoint_model_state_digest(checkpoint)
                    or arms[arm].get("completed_phase_A_updates")
                    != expected["phase_A_updates"]
                    or arms[arm].get("completed_phase_B_updates")
                    != expected["phase_B_updates_per_arm"]
                ):
                    raise ValueError
            except (FileNotFoundError, KeyError, TypeError, ValueError):
                errors.append("G52 checkpoint digest/reload mismatch")
    certificates = [row.get("first_phase_B_activation_certificate") for row in rows]
    if (
        not isinstance(conclusion, Mapping)
        or conclusion.get("certificate_kind")
        != "G52_FORMAL_ROOT_ACTIVATION_INVENTORY_V1"
        or conclusion.get("root_count") != len(rows)
        or conclusion.get("q_r")
        != [
            certificate.get("norms", {}).get("q_r")
            if isinstance(certificate, Mapping)
            else None
            for certificate in certificates
        ]
        or conclusion.get("every_root_certificate_structurally_valid")
        is not all(source.validate_boundary_activation_certificate(certificate) for certificate in certificates)
        or conclusion.get("every_root_boundary_operationally_valid")
        is not all(
            isinstance(certificate, Mapping)
            and certificate.get("boundary_operationally_valid") is True
            for certificate in certificates
        )
        or conclusion.get("every_root_active")
        is not all(
            isinstance(certificate, Mapping) and certificate.get("active") is True
            for certificate in certificates
        )
        or conclusion.get("every_root_scientifically_valid")
        is not all(
            isinstance(certificate, Mapping)
            and certificate.get("scientifically_valid") is True
            for certificate in certificates
        )
    ):
        errors.append("G52 conclusion/certificate inventory mismatch")
    if formal is True and len(seen_pids) < min(
        int(expected["replicates"]), int(expected["process_workers"])
    ):
        errors.append("G52 formal roots were not process isolated")
    return errors


def _evaluation_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> list[str]:
    errors = _training_errors(run_root, training)
    configuration = training.get("configuration")
    if not isinstance(configuration, Mapping):
        return errors + ["G52 evaluation has no bound training configuration"]
    if (
        evaluation.get("schema_version") != SCHEMA_VERSION
        or evaluation.get("algorithm") != ALGORITHM_ID
        or evaluation.get("source_id") != SOURCE_ID
        or evaluation.get("stage") != "evaluate"
        or evaluation.get("status") != "COMPLETE"
        or evaluation.get("formal") is not training.get("formal")
        or evaluation.get("source_commit") != training.get("source_commit")
        or any(
            evaluation.get(name) != training.get(name)
            for name in (
                "authorization_token", "alignment_audit_id", "alignment_disposition",
                "aligned_source_commit", "alignment_stage_commit",
                "preflight_artifact_digests", "accepted_anchor_artifact_digests",
            )
        )
        or evaluation.get("configuration") != configuration
        or evaluation.get("source_controls") != source_controls()
        or evaluation.get("conclusion_evidence") != training.get("conclusion_evidence")
        or evaluation.get("training_manifest_digest")
        != _artifact_digest(run_root / TRAIN_MANIFEST)
        or evaluation.get("accepted_anchor_artifact_digests") is not None
        or evaluation.get("direct_source_validation") is not True
        or not isinstance(evaluation.get("runtime"), Mapping)
        or not _valid_cpu_execution_record(evaluation.get("cpu_execution"), configuration)
        or not _valid_native_backend(evaluation.get("native_backend"))
        or evaluation.get("native_backend") != training.get("native_backend")
        or not isinstance(evaluation.get("stage_wall_time_seconds"), (int, float))
        or isinstance(evaluation.get("stage_wall_time_seconds"), bool)
        or not math.isfinite(float(evaluation["stage_wall_time_seconds"]))
        or not 0.0 <= float(evaluation["stage_wall_time_seconds"]) <= float(configuration["wall_clock_cap_seconds"])
        or evaluation.get("work_accounting") != {
            "scientific_real_transitions": configuration["evaluation_real_transitions"],
            "scientific_optimizer_steps": 0,
            "proof_real_transitions": 0,
            "proof_optimizer_steps": 0,
            "bootstrap_resamples": 0,
        }
    ):
        errors.append("G52 evaluation identity/source/backend mismatch")

    expected_worker_keys = [
        (replicate, capacity, name)
        for replicate in range(int(configuration["replicates"]))
        for capacity in g34.CAPACITIES
        for name in MODEL_CELLS
    ]
    workers = evaluation.get("worker_execution")
    observed_worker_keys: list[tuple[int, int, str]] = []
    if not isinstance(workers, list) or len(workers) != len(expected_worker_keys):
        errors.append("G52 evaluation worker inventory mismatch")
    else:
        for index, row in enumerate(workers):
            identity = row.get("task_identity") if isinstance(row, Mapping) else None
            if (
                not isinstance(row, Mapping)
                or row.get("index") != index
                or not isinstance(identity, Mapping)
                or set(identity) != {"replicate", "capacity", "cell"}
                or row.get("configured_process_workers") != int(configuration["process_workers"])
                or not isinstance(row.get("output_path"), str)
                or re.fullmatch(r"[0-9a-f]{64}", str(row.get("output_digest"))) is None
                or row.get("output_transport_consumed") is not True
                or not _valid_worker_runtime(row.get("runtime"))
            ):
                errors.append("G52 evaluation worker index/runtime mismatch")
                break
            observed_worker_keys.append((int(identity["replicate"]), int(identity["capacity"]), str(identity["cell"])))
        if observed_worker_keys != expected_worker_keys:
            errors.append("G52 evaluation worker deterministic order mismatch")

    expected_inventories: list[dict[str, object]] = []
    for replicate in range(int(configuration["replicates"])):
        for capacity in g34.CAPACITIES:
            _, inventory = _source_inventory(
                replicate=replicate, capacity=capacity,
                episode_count=int(configuration["episodes_per_cell"]),
                formal=bool(training["formal"]),
            )
            expected_inventories.append(inventory)
    if evaluation.get("source_inventory") != expected_inventories:
        errors.append("G52 evaluation source/process inventory mismatch")
    inventories = {
        (int(row["replicate"]), int(row["capacity"])): row["processes"]
        for row in expected_inventories
    }

    cells = evaluation.get("cells")
    expected_cell_keys = [
        (replicate, capacity, arm, name)
        for replicate in range(int(configuration["replicates"]))
        for capacity in g34.CAPACITIES
        for arm in source.ARMS
        for name in MODEL_CELLS
    ]
    if not isinstance(cells, list) or len(cells) != len(expected_cell_keys):
        return errors + ["G52 evaluation cell inventory mismatch"]
    cell_fields = {
        "replicate", "capacity", "arm", "cell", "checkpoint", "process",
        "deterministic", "optimizer_steps", "state_before", "state_after",
        "lifecycle_valid", "realized_successor_actor_credit_read_count",
        "baseline_evaluation_read_count", "episodes",
    }
    observed_keys: list[tuple[int, int, str, str]] = []
    paired_episode_identity: dict[tuple[int, int, str], list[tuple[object, ...]]] = {}
    for cell in cells:
        try:
            if not isinstance(cell, Mapping) or set(cell) != cell_fields:
                raise ValueError("G52 evaluation cell field set mismatch")
            key = (int(cell["replicate"]), int(cell["capacity"]), str(cell["arm"]), str(cell["cell"]))
            observed_keys.append(key)
            contract = _cell_contract(key[3])
            if any(cell.get(name) != value for name, value in contract.items()):
                raise ValueError("G52 evaluation cell route mismatch")
            expected_digest = training["replicate_results"][key[0]]["arms"][key[2]]["final_model_state_digest"]
            if (
                cell.get("optimizer_steps") != 0
                or cell.get("state_before") != expected_digest
                or cell.get("state_after") != expected_digest
                or cell.get("lifecycle_valid") is not True
                or cell.get("realized_successor_actor_credit_read_count") != 0
                or cell.get("baseline_evaluation_read_count") != 0
            ):
                raise ValueError("G52 evaluation checkpoint/model immutability mismatch")
            episodes = cell.get("episodes")
            if not isinstance(episodes, list) or len(episodes) != int(configuration["episodes_per_cell"]):
                raise ValueError("G52 evaluation episode inventory mismatch")
            expected_rows = inventories[(key[0], key[1])]
            roster_field = "random_expected_roster_sizes" if contract["process"] == "random" else "fixed_expected_roster_sizes"
            identities: list[tuple[object, ...]] = []
            for index, episode in enumerate(episodes):
                if not isinstance(episode, Mapping):
                    raise ValueError("G52 evaluation episode schema mismatch")
                expected_process = expected_rows[index]
                identity = (
                    episode.get("local_episode_id"), episode.get("episode_id"),
                    episode.get("signature"), tuple(episode.get("event_times", ())),
                    tuple(episode.get("event_order", ())),
                )
                identities.append(identity)
                if (
                    identity != (
                        index, expected_process["episode_id"], expected_process["signature"],
                        tuple(expected_process["event_times"]), tuple(expected_process["event_order"]),
                    )
                    or episode.get("roster_sizes_valid") is not True
                ):
                    raise ValueError("G52 paired evaluation episode identity mismatch")
                trace = _backend.g39_runner.g34_runner._trace_evidence(episode)
                if (
                    trace["roster_size_trace"] != tuple(expected_process[roster_field])
                    or not _backend.g39_runner.g34_runner._summary_matches_trace(episode, trace)
                ):
                    raise ValueError("G52 evaluation episode trace mismatch")
            pair_key = (key[0], key[1], key[3])
            if pair_key in paired_episode_identity and paired_episode_identity[pair_key] != identities:
                raise ValueError("G52 paired arm episode identity mismatch")
            paired_episode_identity[pair_key] = identities
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
    if observed_keys != expected_cell_keys or len(set(observed_keys)) != len(expected_cell_keys):
        errors.append("G52 evaluation exact cell-key set/order mismatch")
    return errors


def _balanced_assignments(
    categories: Sequence[object], *, capacity: int, process_seed: int,
    stream: int, count: int,
) -> tuple[object, ...]:
    if len(categories) != 3 or count not in (6, 48) or count % 3:
        raise ValueError("G52 evaluation balance request invalid")
    order = sorted(
        range(count),
        key=lambda episode: (
            int(
                source.g40.g35._process_rng(
                    process_seed, capacity, episode, stream
                ).integers(0, 2**63)
            ),
            episode,
        ),
    )
    assigned: list[object | None] = [None] * count
    width = count // 3
    for category_index, category in enumerate(categories):
        for episode in order[category_index * width : (category_index + 1) * width]:
            assigned[episode] = category
    if any(value is None for value in assigned):
        raise RuntimeError("G52 balanced evaluation assignment did not close")
    return tuple(assigned)  # type: ignore[return-value]


def _source_inventory(
    *, replicate: int, capacity: int, episode_count: int, formal: bool
) -> tuple[tuple[g34.RandomProcessLedger, ...], dict[str, object]]:
    if capacity not in g34.CAPACITIES or episode_count not in (6, 48):
        raise ValueError("G52 evaluation source request outside frozen support")
    seeds = source.seed_block(replicate, formal=formal)
    times = source.g40.g35._time_assignments(
        capacity=capacity, process_seed=seeds["evaluation_process"]
    )[:episode_count]
    orders = _balanced_assignments(
        g34.EVENT_ORDERS,
        capacity=capacity,
        process_seed=seeds["evaluation_process"],
        stream=1,
        count=episode_count,
    )
    if capacity == 6:
        profiles: Sequence[object] = (roster_env.SMALL_CAPACITY_6,) * episode_count
    elif capacity == 12:
        profiles = (roster_env.LARGE_CAPACITY_12,) * episode_count
    else:
        profiles = _balanced_assignments(
            roster_env.TRAIN_PROFILES,
            capacity=capacity,
            process_seed=seeds["evaluation_process"],
            stream=2,
            count=episode_count,
        )
    processes: list[g34.RandomProcessLedger] = []
    for local_episode in range(episode_count):
        base = roster_env.make_ledger(
            g34.episode_address(capacity, local_episode),
            master_seed=seeds["evaluation_ledger"],
            profile=profiles[local_episode],  # type: ignore[arg-type]
        )
        expected, trajectory = g34._expected_roster_schedule(
            base, times[local_episode], orders[local_episode]  # type: ignore[arg-type]
        )
        row = g34.RandomProcessLedger(
            base=base,
            local_episode_id=local_episode,
            event_times=times[local_episode],
            event_order=orders[local_episode],  # type: ignore[arg-type]
            expected_roster_sizes=expected,
            count_trajectory=trajectory,
        )
        row.validate()
        processes.append(row)
    if len({row.signature for row in processes}) != episode_count:
        raise ValueError("G52 evaluation process signatures are not unique")
    inventory = {
        "replicate": replicate,
        "capacity": capacity,
        "seeds": seeds,
        "order_counts": {
            "LRJT": sum(tuple(row.event_order) == tuple(g34.EVENT_ORDERS[0]) for row in processes),
            "LJRT": sum(tuple(row.event_order) == tuple(g34.EVENT_ORDERS[1]) for row in processes),
            "JLRT": sum(tuple(row.event_order) == tuple(g34.EVENT_ORDERS[2]) for row in processes),
        },
        "profile_counts": {
            profile.name: sum(row.profile.name == profile.name for row in processes)
            for profile in roster_env.TRAIN_PROFILES
        } if capacity == 8 else None,
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
    expected = episode_count // 3
    if set(inventory["order_counts"].values()) != {expected}:  # type: ignore[union-attr]
        raise RuntimeError("G52 event-order inventory is not balanced")
    if capacity == 8 and set(inventory["profile_counts"].values()) != {expected}:  # type: ignore[union-attr]
        raise RuntimeError("G52 capacity-8 profile inventory is not balanced")
    return tuple(processes), inventory


def _cell_contract(name: str) -> dict[str, object]:
    contracts = {
        FINAL_FIXED_DET: {"process": "fixed", "deterministic": True},
        FINAL_FIXED_STOCH: {"process": "fixed", "deterministic": False},
        FINAL_RANDOM_DET: {"process": "random", "deterministic": True},
        FINAL_RANDOM_STOCH: {"process": "random", "deterministic": False},
    }
    if name not in contracts:
        raise ValueError("G52 unknown evaluation cell")
    return {"checkpoint": "final", **contracts[name]}


class _G52ActorOnlyEvaluationPolicy:
    __slots__ = ("_projection",)

    def __init__(self, projection: source.g50.G50PhaseBProjection) -> None:
        if projection.phase != "credit_branch" or hasattr(projection, "credit_baselines"):
            raise ValueError("G52 evaluation requires actor-only Phase-B projection")
        self._projection = projection

    @property
    def member_capacity(self) -> int:
        return self._projection.member_capacity

    @property
    def hidden_dim(self) -> int:
        return self._projection.hidden_dim

    def eval(self) -> "_G52ActorOnlyEvaluationPolicy":
        self._projection.eval()
        return self

    def forward_step(self, **arguments: Any) -> Any:
        arguments.pop("critic_state", None)
        return source.g47._actor_only_step(self._projection, **arguments)


def _evaluate_cell(
    *, replicate: int, capacity: int, arm: str, name: str,
    processes: Sequence[g34.RandomProcessLedger], action_seed: int,
    deployed: source.g50.G50PhaseBProjection,
) -> dict[str, object]:
    contract = _cell_contract(name)
    before = _state_digest(deployed)
    episodes, lifecycle = source.g40.evaluate_model(
        _G52ActorOnlyEvaluationPolicy(deployed),  # type: ignore[arg-type]
        processes=processes,
        action_seed=action_seed,
        process_kind=str(contract["process"]),
        deterministic=bool(contract["deterministic"]),
    )
    return {
        "replicate": replicate, "capacity": capacity, "arm": arm, "cell": name,
        **contract, "optimizer_steps": 0, "state_before": before,
        "state_after": _state_digest(deployed), "lifecycle_valid": lifecycle,
        "realized_successor_actor_credit_read_count": 0,
        "baseline_evaluation_read_count": 0, "episodes": list(episodes),
    }


def _evaluation_cell_worker(task: Mapping[str, object]) -> dict[str, object]:
    _activate_single_thread_worker()
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    tracemalloc.start()
    index, replicate, capacity = int(task["index"]), int(task["replicate"]), int(task["capacity"])
    name, formal = str(task["cell"]), bool(task["formal"])
    run_root, output_path = Path(str(task["run_root"])), Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G52 evaluation worker output is not fresh")
    training = _read_json(run_root / TRAIN_MANIFEST)
    if training.get("configuration") != task.get("configuration"):
        raise RuntimeError("G52 evaluation worker configuration mismatch")
    processes, inventory = _source_inventory(
        replicate=replicate, capacity=capacity,
        episode_count=int(training["configuration"]["episodes_per_cell"]), formal=formal,
    )
    seeds = source.seed_block(replicate, formal=formal)
    cells = [
        _evaluate_cell(
            replicate=replicate, capacity=capacity, arm=arm, name=name,
            processes=processes, action_seed=seeds["evaluation_action"],
            deployed=_load_final_model(
                run_root=run_root, training=training, replicate=replicate,
                capacity=capacity, arm=arm,
            ),
        )
        for arm in source.ARMS
    ]
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    payload = {
        "index": index,
        "task_identity": {"replicate": replicate, "capacity": capacity, "cell": name},
        "direct_source_validation": _backend.g38_runner._direct_source_validation(processes),
        "source_inventory": inventory, "cells": cells,
        "worker_runtime": _worker_telemetry(
            started_wall=started_wall, started_cpu=started_cpu, peak_bytes=peak
        ),
    }
    _write_json(output_path, payload)
    return {"index": index, "output_path": str(output_path), "output_digest": _artifact_digest(output_path)}


def _consume_evaluation_worker_results(
    results: Sequence[Mapping[str, object]], tasks: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], bool]:
    cells: list[dict[str, object]] = []
    inventories: dict[tuple[int, int], dict[str, object]] = {}
    workers: list[dict[str, object]] = []
    direct = True
    for expected_index, (task, result) in enumerate(zip(tasks, results, strict=True)):
        path = Path(str(result["output_path"]))
        payload = _read_json(path)
        identity = {"replicate": int(task["replicate"]), "capacity": int(task["capacity"]), "cell": str(task["cell"])}
        if (payload.get("index") != expected_index or payload.get("task_identity") != identity
                or not isinstance(payload.get("cells"), list) or len(payload["cells"]) != len(source.ARMS)):
            raise RuntimeError("G52 evaluation worker payload identity mismatch")
        key = (identity["replicate"], identity["capacity"])
        inventory = dict(payload["source_inventory"])
        if key in inventories and inventories[key] != inventory:
            raise RuntimeError("G52 duplicate evaluation inventory disagrees")
        inventories[key] = inventory
        direct &= payload.get("direct_source_validation") is True
        cells.extend(dict(row) for row in payload["cells"])
        workers.append({
            "index": expected_index, "task_identity": identity,
            "configured_process_workers": int(task["configured_process_workers"]),
            "output_path": str(path), "output_digest": result["output_digest"],
            "output_transport_consumed": True, "runtime": dict(payload["worker_runtime"]),
        })
        path.unlink()
    expected_keys = [(r, c) for r in range(1 + max(int(t["replicate"]) for t in tasks)) for c in g34.CAPACITIES]
    if list(inventories) != expected_keys:
        raise RuntimeError("G52 evaluation inventory merge mismatch")
    arm_order = {arm: index for index, arm in enumerate(source.ARMS)}
    cell_order = {name: index for index, name in enumerate(MODEL_CELLS)}
    cells.sort(key=lambda row: (int(row["replicate"]), int(row["capacity"]), arm_order[str(row["arm"])], cell_order[str(row["cell"])]))
    return cells, list(inventories.values()), workers, direct


def evaluate(
    *, run_root: Path, cpu_budget: int | None = None, process_workers: int | None = None
) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / TRAIN_MANIFEST)
    errors = _training_errors(run_root, training)
    if errors:
        raise ValueError("G52 training artifact invalid: " + " | ".join(errors))
    formal, configuration = bool(training["formal"]), training["configuration"]
    requested = _resolve_cpu_execution(
        int(configuration["cpu_budget"]) if cpu_budget is None else cpu_budget,
        int(configuration["process_workers"]) if process_workers is None else process_workers,
    )
    if requested["cpu_budget"] != configuration["cpu_budget"] or requested["process_workers"] != configuration["process_workers"]:
        raise ValueError("G52 evaluate CPU/process settings differ from training")
    cpu = _configure_cpu_execution(int(configuration["cpu_budget"]), int(configuration["process_workers"]))
    _backend.configure_runtime(source.bootstrap_seed(formal=formal))
    native = _backend._native_backend_identity()
    tasks: list[dict[str, object]] = []
    for replicate in range(int(configuration["replicates"])):
        for capacity in g34.CAPACITIES:
            for name in MODEL_CELLS:
                index = len(tasks)
                tasks.append({
                    "index": index, "replicate": replicate, "capacity": capacity,
                    "cell": name, "formal": formal, "configuration": configuration,
                    "configured_process_workers": int(configuration["process_workers"]),
                    "run_root": str(Path(run_root).resolve()),
                    "output_path": str(Path(run_root).resolve() / ".worker_transport" / "evaluate" / f"task_{index}" / "result.json"),
                })
    results = _backend._run_indexed_worker_tasks(tasks, _evaluation_cell_worker, process_workers=int(configuration["process_workers"]))
    cells, inventories, workers, direct = _consume_evaluation_worker_results(results, tasks)
    manifest = {
        "schema_version": SCHEMA_VERSION, "algorithm": ALGORITHM_ID, "source_id": SOURCE_ID,
        "stage": "evaluate", "status": "COMPLETE", "formal": formal,
        "source_commit": training["source_commit"], "authorization_token": training["authorization_token"],
        "alignment_audit_id": training["alignment_audit_id"], "alignment_disposition": training["alignment_disposition"],
        "aligned_source_commit": training["aligned_source_commit"], "alignment_stage_commit": training["alignment_stage_commit"],
        "preflight_artifact_digests": training["preflight_artifact_digests"],
        "accepted_anchor_artifact_digests": None, "runtime": _runtime_identity(),
        "cpu_execution": cpu, "native_backend": native, "configuration": configuration,
        "source_controls": source_controls(), "conclusion_evidence": training["conclusion_evidence"],
        "training_manifest_digest": _artifact_digest(run_root / TRAIN_MANIFEST),
        "stage_wall_time_seconds": time.perf_counter() - started,
        "direct_source_validation": bool(direct), "source_inventory": inventories,
        "worker_execution": workers, "cells": cells,
        "work_accounting": {
            "scientific_real_transitions": configuration["evaluation_real_transitions"],
            "scientific_optimizer_steps": 0,
            "proof_real_transitions": 0,
            "proof_optimizer_steps": 0,
            "bootstrap_resamples": 0,
        },
    }
    _write_json(run_root / EVALUATION_MANIFEST, manifest)
    return manifest


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
    components: dict[str, object] = {}
    upper_bounds: list[float] = []
    for name, cell, metric, pooled in component_specs:
        delta = _backend._difference(
            _backend._metric_arrays(evaluation, source.RESET_ARM, cell, metric),
            _backend._metric_arrays(evaluation, source.CARRY_ARM, cell, metric),
        )
        if pooled:
            ci = _backend._hierarchical_ci(delta, capacities=g34.CAPACITIES, plan=plan)
            components[name] = ci
            upper_bounds.append(ci[2])
        else:
            rows = {capacity: _backend._hierarchical_ci(delta, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
            components[name] = rows
            upper_bounds.extend(row[2] for row in rows.values())
    transport = _backend._difference(
        _backend._difference(
            _backend._metric_arrays(evaluation, source.RESET_ARM, FINAL_RANDOM_DET, "utility"),
            _backend._metric_arrays(evaluation, source.RESET_ARM, FINAL_FIXED_DET, "utility"),
        ),
        _backend._difference(
            _backend._metric_arrays(evaluation, source.CARRY_ARM, FINAL_RANDOM_DET, "utility"),
            _backend._metric_arrays(evaluation, source.CARRY_ARM, FINAL_FIXED_DET, "utility"),
        ),
    )
    transport_rows = {capacity: _backend._hierarchical_ci(transport, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
    components["random_minus_fixed_transport"] = transport_rows
    upper_bounds.extend(row[2] for row in transport_rows.values())
    primary_values = _backend._difference(
        _backend._metric_arrays(evaluation, source.RESET_ARM, FINAL_RANDOM_DET, "utility"),
        _backend._metric_arrays(evaluation, source.CARRY_ARM, FINAL_RANDOM_DET, "utility"),
    )
    primary = _backend._hierarchical_ci(primary_values, capacities=g34.CAPACITIES, plan=plan)
    capacity_primary = {capacity: _backend._hierarchical_ci(primary_values, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
    noninferior = _backend.g38_runner._inclusive_le(primary[2], MATERIALITY_MARGIN) and all(
        _backend.g38_runner._inclusive_le(value, MATERIALITY_MARGIN) for value in upper_bounds
    )
    material = _backend.g38_runner._strict_gt(primary[0], MATERIALITY_MARGIN) and all(
        _backend.g38_runner._strict_gt(capacity_primary[capacity][0], 0.0) for capacity in g34.CAPACITIES
    )
    return {
        "RESET_minus_CARRY_primary_ci95": primary,
        "RESET_minus_CARRY_capacity_ci95": capacity_primary,
        "RESET_minus_CARRY_component_ci95": components,
        "persistent_Adam_noninferior": bool(noninferior),
        "material_reset_advantage": bool(material),
    }


def _bootstrap_plan(
    *, formal: bool, replicates: int, episodes: int, repetitions: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(source.bootstrap_seed(formal=formal))
    return (
        rng.integers(0, replicates, size=(repetitions, replicates), dtype=np.int16),
        rng.integers(0, episodes, size=(repetitions, replicates, len(g34.CAPACITIES), episodes), dtype=np.int16),
    )


def select_g52_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics.get("operational_valid")) or not bool(
        metrics.get("treatment_activation_valid")
    ):
        return INVALID_BRANCH
    if not bool(metrics.get("source_valid")) or not bool(
        metrics.get("RESET_access_pass")
    ):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics.get("RESET_access_pass"))
        and bool(metrics.get("CARRY_access_pass"))
        and bool(metrics.get("persistent_Adam_noninferior"))
    ):
        return NULL_SUFFICIENT_BRANCH
    if bool(metrics.get("RESET_access_pass")) and (
        bool(metrics.get("CARRY_access_confident_fail"))
        or bool(metrics.get("material_reset_advantage"))
    ):
        return REFERENCE_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def _analysis_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
    analysis: Mapping[str, Any],
) -> list[str]:
    errors = _evaluation_errors(run_root, training, evaluation)
    configuration = training.get("configuration")
    metrics = analysis.get("metrics")
    if not isinstance(configuration, Mapping) or not isinstance(metrics, Mapping):
        return errors + ["G52 analysis configuration/metrics missing"]
    formal = bool(training.get("formal"))
    active = bool(
        isinstance(training.get("conclusion_evidence"), Mapping)
        and training["conclusion_evidence"].get("every_root_scientifically_valid") is True
    )
    expected_branch = (
        INVALID_BRANCH
        if not active
        else select_g52_result_branch(metrics)
        if formal
        else NONFORMAL_BRANCH
    )
    expected_bootstrap = int(configuration["bootstrap_resamples"]) if active else 0
    expected_thresholds = {
        "utility_floor": UTILITY_FLOOR,
        "stochastic_floor": STOCHASTIC_FLOOR,
        "event_floor": EVENT_FLOOR,
        "segment_floor": SEGMENT_FLOOR,
        "random_minus_fixed_floor": PROCESS_MARGIN,
        "minimum_replicate_floor": MINIMUM_REPLICATE_FLOOR,
        "materiality_noninferiority_margin": MATERIALITY_MARGIN,
    }
    if (
        analysis.get("schema_version") != SCHEMA_VERSION
        or analysis.get("algorithm_id") != ALGORITHM_ID
        or analysis.get("source_id") != SOURCE_ID
        or analysis.get("stage") != "analyze"
        or analysis.get("status") != "COMPLETE"
        or analysis.get("formal") is not training.get("formal")
        or analysis.get("source_commit") != training.get("source_commit")
        or analysis.get("operational_valid") is not True
        or analysis.get("operational_errors") != []
        or metrics.get("operational_valid") is not True
        or metrics.get("treatment_activation_valid") is not active
        or analysis.get("primary_estimand") != "Delta_reset=U_RESET-U_CARRY"
        or analysis.get("positive_direction") != "favors_RESET"
        or analysis.get("materiality_and_noninferiority_margin") != MATERIALITY_MARGIN
        or analysis.get("threshold_record") != expected_thresholds
        or analysis.get("first_match_priority") != list(FIRST_MATCH_ORDER)
        or analysis.get("result_branch") != expected_branch
        or analysis.get("claim_ceiling")
        != source.CLAIM_CEILINGS.get(expected_branch, source.CLAIM_CEILINGS["otherwise"])
        or analysis.get("scientific_branch_selected") is not formal
        or analysis.get("terminal_for_registered_treatment_if_formal") is not formal
        or analysis.get("retry_rescue_more_roots_seed_search_or_ablation_authorized") is not False
        or analysis.get("training_manifest_digest") != _artifact_digest(run_root / TRAIN_MANIFEST)
        or analysis.get("evaluation_manifest_digest") != _artifact_digest(run_root / EVALUATION_MANIFEST)
        or analysis.get("work_accounting") != {
            "scientific_real_transitions": 0,
            "scientific_optimizer_steps": 0,
            "proof_real_transitions": 0,
            "proof_optimizer_steps": 0,
            "bootstrap_resamples": expected_bootstrap,
        }
        or not isinstance(analysis.get("stage_wall_time_seconds"), (int, float))
        or isinstance(analysis.get("stage_wall_time_seconds"), bool)
        or not math.isfinite(float(analysis["stage_wall_time_seconds"]))
        or not 0.0 <= float(analysis["stage_wall_time_seconds"]) <= float(configuration["wall_clock_cap_seconds"])
    ):
        errors.append("G52 analysis identity/digest/work/branch mismatch")
    return errors


def analyze(
    *,
    run_root: Path,
    require_formal: bool = False,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / TRAIN_MANIFEST)
    evaluation = _read_json(run_root / EVALUATION_MANIFEST)
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G52 analysis requires formal artifacts")
    configuration = training["configuration"]
    requested = _resolve_cpu_execution(
        int(configuration["cpu_budget"]) if cpu_budget is None else cpu_budget,
        int(configuration["process_workers"])
        if process_workers is None
        else process_workers,
    )
    if (
        requested["cpu_budget"] != configuration["cpu_budget"]
        or requested["process_workers"] != configuration["process_workers"]
    ):
        raise ValueError("G52 analyze CPU/process settings differ from training")
    errors = _evaluation_errors(run_root, training, evaluation)
    conclusion = training.get("conclusion_evidence", {})
    metrics: dict[str, Any] = {
        "operational_valid": not errors,
        "treatment_activation_valid": bool(
            isinstance(conclusion, Mapping)
            and conclusion.get("every_root_scientifically_valid") is True
        ),
    }
    if not errors and metrics["treatment_activation_valid"]:
        plan = _bootstrap_plan(
            formal=formal,
            replicates=int(configuration["replicates"]),
            episodes=int(configuration["evaluation_episodes_per_cell"]),
            repetitions=int(configuration["bootstrap_resamples"]),
        )
        access = {
            arm: _backend._arm_access(evaluation, arm, plan) for arm in source.ARMS
        }
        metrics.update(
            {
                "source_valid": evaluation["direct_source_validation"] is True,
                "arm_access": access,
                "RESET_access_pass": access[source.RESET_ARM]["access_pass"],
                "CARRY_access_pass": access[source.CARRY_ARM]["access_pass"],
                "RESET_access_confident_fail": access[source.RESET_ARM][
                    "access_confident_fail"
                ],
                "CARRY_access_confident_fail": access[source.CARRY_ARM][
                    "access_confident_fail"
                ],
                **_comparison(evaluation, plan),
            }
        )
    branch = INVALID_BRANCH if errors or not metrics["treatment_activation_valid"] else select_g52_result_branch(metrics) if formal else NONFORMAL_BRANCH
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": formal,
        "source_commit": training.get("source_commit"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "metrics": metrics,
        "primary_estimand": "Delta_reset=U_RESET-U_CARRY",
        "positive_direction": "favors_RESET",
        "materiality_and_noninferiority_margin": MATERIALITY_MARGIN,
        "threshold_record": {
            "utility_floor": UTILITY_FLOOR,
            "stochastic_floor": STOCHASTIC_FLOOR,
            "event_floor": EVENT_FLOOR,
            "segment_floor": SEGMENT_FLOOR,
            "random_minus_fixed_floor": PROCESS_MARGIN,
            "minimum_replicate_floor": MINIMUM_REPLICATE_FLOOR,
            "materiality_noninferiority_margin": MATERIALITY_MARGIN,
        },
        "first_match_priority": list(FIRST_MATCH_ORDER),
        "result_branch": branch,
        "scientific_branch_selected": formal,
        "claim_ceiling": source.CLAIM_CEILINGS.get(
            branch, source.CLAIM_CEILINGS["otherwise"]
        ),
        "terminal_for_registered_treatment_if_formal": formal,
        "retry_rescue_more_roots_seed_search_or_ablation_authorized": False,
        "training_manifest_digest": _artifact_digest(run_root / TRAIN_MANIFEST),
        "evaluation_manifest_digest": _artifact_digest(run_root / EVALUATION_MANIFEST),
        "work_accounting": {
            "scientific_real_transitions": 0,
            "scientific_optimizer_steps": 0,
            "proof_real_transitions": 0,
            "proof_optimizer_steps": 0,
            "bootstrap_resamples": int(configuration["bootstrap_resamples"])
            if metrics["treatment_activation_valid"] and not errors
            else 0,
        },
        "stage_wall_time_seconds": time.perf_counter() - started,
    }
    _write_json(run_root / ANALYSIS_RESULT, result)
    return result


def _synthetic_branch_witnesses() -> dict[str, str]:
    base = {
        "operational_valid": True,
        "treatment_activation_valid": True,
        "source_valid": True,
        "RESET_access_pass": True,
        "CARRY_access_pass": True,
        "CARRY_access_confident_fail": False,
        "persistent_Adam_noninferior": False,
        "material_reset_advantage": False,
    }
    witnesses = {
        "invalid": {**base, "treatment_activation_valid": False},
        "source_failure": {**base, "source_valid": False},
        "persistent_sufficient": {**base, "persistent_Adam_noninferior": True},
        "reset_advantage": {
            **base,
            "CARRY_access_pass": False,
            "CARRY_access_confident_fail": True,
        },
        "underpowered": base,
    }
    return {name: select_g52_result_branch(row) for name, row in witnesses.items()}


def readiness_interface_smoke(*, source_commit: str) -> dict[str, object]:
    if not _valid_commit(source_commit):
        raise ValueError("G52 readiness requires an integrated source commit")
    return {
        "algorithm_id": ALGORITHM_ID,
        "source_commit": source_commit,
        "schema_version": SCHEMA_VERSION,
        "formal": False,
        "execution_readiness_proof_only": True,
        "registered_scientific_roots": 0,
        "scientific_iteration_cost": 0,
        "scientific_real_transitions": 0,
        "scientific_optimizer_steps": 0,
        "bootstrap_resamples": 0,
        "scientific_branch_selected": False,
        "interfaces": [
            "train",
            "evaluate",
            "analyze",
            "exercise",
            "readiness-smoke",
            "readiness-train",
            "readiness-validate",
            "readiness-reload",
            "readiness-evaluate",
            "readiness-analyze",
        ],
        "passed": True,
    }


def _readiness_process_worker(task: Mapping[str, object]) -> dict[str, object]:
    _activate_single_thread_worker()
    output_path = Path(str(task["output_path"]))
    payload = {
        "index": int(task["index"]),
        "pid": os.getpid(),
        "thread_environment": {name: os.environ.get(name) for name in _THREAD_ENV_NAMES},
        "torch_intraop_threads": torch.get_num_threads(),
        "configuration_digest": hashlib.sha256(
            json.dumps(
                source.static_configuration_certificate(formal=False), sort_keys=True
            ).encode("utf-8")
        ).hexdigest(),
    }
    _write_json(output_path, payload)
    return {
        "index": int(task["index"]),
        "output_path": str(output_path),
        "output_digest": _artifact_digest(output_path),
    }


def _readiness_process_entry(
    task: Mapping[str, object], ready_event: Any, release_event: Any
) -> None:
    _activate_single_thread_worker()
    ready_event.set()
    if not release_event.wait(timeout=60.0):
        raise RuntimeError("G52 readiness worker barrier timed out")
    _readiness_process_worker(task)


def _run_distinct_readiness_workers(
    tasks: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if [task.get("index") for task in tasks] != [0, 1]:
        raise ValueError("G52 readiness requires exactly two indexed tasks")
    context = multiprocessing.get_context("spawn")
    ready_events = [context.Event() for _ in tasks]
    release_event = context.Event()
    processes = [
        context.Process(
            target=_readiness_process_entry,
            args=(dict(task), ready_event, release_event),
        )
        for task, ready_event in zip(tasks, ready_events, strict=True)
    ]
    try:
        for process in processes:
            process.start()
        for index, ready_event in enumerate(ready_events):
            if not ready_event.wait(timeout=60.0):
                raise RuntimeError(f"G52 readiness worker {index} did not reach barrier")
        if len({process.pid for process in processes}) != 2 or any(
            process.pid is None for process in processes
        ):
            raise RuntimeError("G52 readiness workers are not distinct")
        release_event.set()
        for process in processes:
            process.join(timeout=60.0)
        if any(process.is_alive() or process.exitcode != 0 for process in processes):
            raise RuntimeError("G52 readiness worker failed")
    finally:
        release_event.set()
        for process in processes:
            if process.pid is not None and process.is_alive():
                process.terminate()
        for process in processes:
            if process.pid is not None:
                process.join(timeout=5.0)
    rows = [_read_json(Path(str(task["output_path"]))) for task in tasks]
    if [row.get("index") for row in rows] != [0, 1] or any(
        row.get("pid") != process.pid for row, process in zip(rows, processes, strict=True)
    ):
        raise RuntimeError("G52 readiness process output identity mismatch")
    return rows


def readiness_train(
    *, run_root: Path, source_commit: str
) -> dict[str, object]:
    root = _fresh_root(run_root)
    smoke = readiness_interface_smoke(source_commit=source_commit)
    root.mkdir(parents=True, exist_ok=True)
    _backend.configure_runtime(source.SEED_BASES["phase_B_gradient_probe"])
    phase_A_model, phase_A_optimizer = source.make_fresh_phase_A_ancestor(
        member_capacity=roster_env.TRAIN_CAPACITY,
        initialization_seed=source.SEED_BASES["initialization"],
    )
    source.make_synthetic_boundary_state_for_readiness(
        phase_A_model,
        phase_A_optimizer,
        step=source.EXPECTED_FORMAL_BOUNDARY_STEP,
    )
    models, optimizers, boundary = source.project_phase_B_arms(
        phase_A_model,
        phase_A_optimizer,
        completed_phase_A_updates=source.FORMAL_PHASE_A_UPDATES,
        expected_step=source.EXPECTED_FORMAL_BOUNDARY_STEP,
    )
    proof_trajectory = _collect_phase_B(
        models[source.RESET_ARM],
        episode_ids=tuple(range(source.NUM_ENVS)),
        ledger_seed=source.SEED_BASES["phase_B_gradient_probe"],
        action_seed=source.SEED_BASES["phase_B_gradient_probe"],
    )
    first_update, certificate = source.execute_first_phase_B_update(
        models,
        optimizers,
        proof_trajectory,
        carry_install_evidence=boundary["CARRY_install"],  # type: ignore[arg-type]
    )
    state_payload = {
        "kind": "G52_EXECUTION_READINESS_PROOF_ONLY_V1",
        "source_commit": source_commit,
        "actor_state": {
            arm: {name: value.detach().cpu().clone() for name, value in models[arm].state_dict().items()}
            for arm in source.ARMS
        },
        "boundary_evidence": boundary,
        "activation_certificate": certificate,
    }
    torch.save(state_payload, root / READINESS_STATE)
    tasks = [
        {
            "index": index,
            "output_path": str(root / "process_proof" / f"worker_{index}.json"),
        }
        for index in range(2)
    ]
    process_rows = _run_distinct_readiness_workers(tasks)
    payload = {
        "smoke": smoke,
        "formal": False,
        "execution_readiness_proof_only": True,
        "registered_scientific_roots": 0,
        "scientific_iteration_cost": 0,
        "scientific_real_transitions": 0,
        "scientific_optimizer_steps": 0,
        "bootstrap_resamples": 0,
        "scientific_branch_selected": False,
        "scientific_access_conclusion": None,
        "proof_activity": {
            "fresh_proof_models": 1,
            "proof_real_transitions": source.NORMALIZATION_ROWS,
            "proof_optimizer_steps": len(source.ARMS) * source.PPO_PASSES,
            "synthetic_Adam_state_rows": len(source.ACTOR_PARAMETER_NAMES),
            "bootstrap_resamples": 0,
        },
        "boundary_evidence": boundary,
        "first_update": first_update,
        "activation_certificate": certificate,
        "serialization": {
            "path": READINESS_STATE,
            "sha256": _artifact_digest(root / READINESS_STATE),
        },
        "process_proof": {
            "worker_count": len(process_rows),
            "distinct_processes": len({int(row["pid"]) for row in process_rows}) == 2,
            "deterministic_preassigned_index_merge": [row["index"] for row in process_rows]
            == [0, 1],
            "single_thread_workers": all(
                row["torch_intraop_threads"] == 1
                and all(row["thread_environment"][name] == "1" for name in _THREAD_ENV_NAMES)
                for row in process_rows
            ),
        },
        "passed": True,
    }
    if not source.validate_boundary_activation_certificate(certificate):
        raise RuntimeError("G52 readiness boundary certificate failed")
    if not all(payload["process_proof"].values()):  # type: ignore[union-attr]
        raise RuntimeError("G52 readiness process-isolation proof failed")
    _write_json(root / READINESS_TRAIN, payload)
    return payload


def readiness_validate(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root)
    if (root / READINESS_VALIDATION).exists():
        raise ValueError("G52 readiness validation artifact already exists")
    training = _read_json(root / READINESS_TRAIN)
    state = torch.load(root / READINESS_STATE, map_location="cpu", weights_only=False)
    valid = bool(
        training.get("formal") is False
        and training.get("registered_scientific_roots") == 0
        and training.get("scientific_iteration_cost") == 0
        and training.get("scientific_branch_selected") is False
        and training.get("bootstrap_resamples") == 0
        and _readiness_certificates_match(
            training.get("activation_certificate"),
            state.get("activation_certificate"),
        )
        and state.get("kind") == "G52_EXECUTION_READINESS_PROOF_ONLY_V1"
        and state.get("source_commit") == training["smoke"]["source_commit"]
        and training.get("serialization", {}).get("sha256")
        == _artifact_digest(root / READINESS_STATE)
    )
    payload = {
        "formal": False,
        "registered_scientific_roots": 0,
        "scientific_iteration_cost": 0,
        "bootstrap_resamples": 0,
        "scientific_branch_selected": False,
        "passed": valid,
    }
    _write_json(root / READINESS_VALIDATION, payload)
    if not valid:
        raise RuntimeError("G52 readiness validation failed")
    return payload


def readiness_reload(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root)
    if (root / READINESS_RELOAD).exists():
        raise ValueError("G52 readiness reload artifact already exists")
    validation = _read_json(root / READINESS_VALIDATION)
    if validation.get("passed") is not True:
        raise RuntimeError("G52 readiness validation artifact failed")
    state = torch.load(root / READINESS_STATE, map_location="cpu", weights_only=False)
    models: dict[str, source.g50.G50PhaseBProjection] = {}
    for arm in source.ARMS:
        shell = source.g40.make_model(
            roster_env.TRAIN_CAPACITY,
            initialization_seed=source.SEED_BASES["initialization"],
        )
        model = source.g50.G50PhaseBProjection(shell)
        model.load_state_dict(state["actor_state"][arm], strict=True)
        models[arm] = model
    payload = {
        "formal": False,
        "registered_scientific_roots": 0,
        "scientific_iteration_cost": 0,
        "bootstrap_resamples": 0,
        "scientific_branch_selected": False,
        "actor_digests": {arm: source._actor_digest(models[arm]) for arm in source.ARMS},
        "state_sha256": _artifact_digest(root / READINESS_STATE),
        "passed": True,
    }
    _write_json(root / READINESS_RELOAD, payload)
    return payload


def readiness_evaluate(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root)
    if (root / READINESS_EVALUATION).exists():
        raise ValueError("G52 readiness evaluation artifact already exists")
    reload = _read_json(root / READINESS_RELOAD)
    if reload.get("passed") is not True:
        raise RuntimeError("G52 readiness reload artifact failed")
    state = torch.load(root / READINESS_STATE, map_location="cpu", weights_only=False)
    forward_rows: dict[str, object] = {}
    for arm in source.ARMS:
        shell = source.g40.make_model(
            roster_env.TRAIN_CAPACITY,
            initialization_seed=source.SEED_BASES["initialization"],
        )
        model = source.g50.G50PhaseBProjection(shell)
        model.load_state_dict(state["actor_state"][arm], strict=True)
        actor = model.policy
        step = source.g47._actor_only_step(
            model,
            observations=torch.zeros(
                (1, roster_env.TRAIN_CAPACITY, actor.observation_dim),
                dtype=actor.log_std.dtype,
            ),
            active_mask=torch.ones(
                (1, roster_env.TRAIN_CAPACITY), dtype=torch.bool
            ),
            hidden=torch.zeros(
                (1, roster_env.TRAIN_CAPACITY, actor.hidden_dim),
                dtype=actor.log_std.dtype,
            ),
            deterministic=True,
        )
        forward_rows[arm] = {
            "action_shape": list(step.actions.shape),
            "finite": bool(torch.isfinite(step.actions).all()),
        }
    payload = {
        "formal": False,
        "registered_scientific_roots": 0,
        "scientific_iteration_cost": 0,
        "scientific_real_transitions": 0,
        "evaluation_optimizer_steps": 0,
        "bootstrap_resamples": 0,
        "bootstrap_inference": False,
        "scientific_access_conclusion": None,
        "scientific_branch_selected": False,
        "proof_forward_calls": len(source.ARMS),
        "reload_state_sha256": reload["state_sha256"],
        "forward_rows": forward_rows,
        "passed": all(row["finite"] for row in forward_rows.values()),  # type: ignore[union-attr]
    }
    _write_json(root / READINESS_EVALUATION, payload)
    return payload


def readiness_analyze(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root)
    if (root / READINESS_ANALYSIS).exists():
        raise ValueError("G52 readiness analysis artifact already exists")
    evaluation = _read_json(root / READINESS_EVALUATION)
    if evaluation.get("passed") is not True:
        raise RuntimeError("G52 readiness evaluation artifact failed")
    payload = {
        "formal": False,
        "execution_readiness_proof_only": True,
        "registered_scientific_roots": 0,
        "scientific_iteration_cost": 0,
        "scientific_real_transitions": 0,
        "scientific_optimizer_steps": 0,
        "bootstrap_resamples": 0,
        "bootstrap_inference": False,
        "scientific_access_conclusion": None,
        "scientific_branch_selected": False,
        "result_branch": None,
        "branch_witnesses_exercised_without_selection": _synthetic_branch_witnesses(),
        "evaluation_passed": evaluation["passed"],
        "passed": evaluation["passed"] is True,
    }
    _write_json(root / READINESS_ANALYSIS, payload)
    return payload


def validate_readiness_artifacts(run_root: Path) -> list[str]:
    root = Path(run_root)
    errors: list[str] = []
    for name in READINESS_ARTIFACTS:
        if not (root / name).is_file():
            errors.append(f"missing:{name}")
    if errors:
        return errors
    try:
        analysis = _read_json(root / READINESS_ANALYSIS)
        if (
            analysis.get("passed") is not True
            or analysis.get("formal") is not False
            or analysis.get("registered_scientific_roots") != 0
            or analysis.get("bootstrap_inference") is not False
            or analysis.get("scientific_branch_selected") is not False
            or analysis.get("result_branch") is not None
        ):
            errors.append("readiness_analysis_boundary_invalid")
    except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
        errors.append("readiness_artifact_invalid")
    return errors


def exercise(
    *,
    run_root: Path,
    source_commit: str,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    train(
        run_root=run_root,
        source_commit=source_commit,
        formal=False,
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
            "readiness-validate",
            "readiness-reload",
            "readiness-evaluate",
            "readiness-analyze",
        ),
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--alignment-disposition")
    parser.add_argument("--aligned-source-commit")
    parser.add_argument("--alignment-stage-commit")
    parser.add_argument("--implementation-handoff-sha256")
    parser.add_argument("--cpu-budget", type=int)
    parser.add_argument("--process-workers", type=int)
    args = parser.parse_args()
    if args.stage == "readiness-smoke":
        if args.source_commit is None:
            raise ValueError("G52 readiness smoke requires --source-commit")
        readiness_interface_smoke(source_commit=args.source_commit)
    elif args.stage == "readiness-train":
        if args.source_commit is None:
            raise ValueError("G52 readiness train requires --source-commit")
        readiness_train(run_root=args.run_root, source_commit=args.source_commit)
    elif args.stage == "readiness-validate":
        readiness_validate(run_root=args.run_root)
    elif args.stage == "readiness-reload":
        readiness_reload(run_root=args.run_root)
    elif args.stage == "readiness-evaluate":
        readiness_evaluate(run_root=args.run_root)
    elif args.stage == "readiness-analyze":
        readiness_analyze(run_root=args.run_root)
    elif args.stage == "train":
        if args.source_commit is None:
            raise ValueError("G52 train requires --source-commit")
        train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            preflight_root=args.preflight_root,
            alignment_disposition=args.alignment_disposition,
            aligned_source_commit=args.aligned_source_commit,
            alignment_stage_commit=args.alignment_stage_commit,
            implementation_handoff_sha256=args.implementation_handoff_sha256,
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
        if args.source_commit is None:
            raise ValueError("G52 exercise requires --source-commit")
        exercise(
            run_root=args.run_root,
            source_commit=args.source_commit,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )


if __name__ == "__main__":
    main()
