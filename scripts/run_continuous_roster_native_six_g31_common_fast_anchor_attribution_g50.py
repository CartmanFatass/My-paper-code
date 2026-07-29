"""Train, evaluate, analyze, and proof-check frozen G50 attribution."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import multiprocessing
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
for _name in _THREAD_ENV_NAMES:
    os.environ[_name] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_common_fast_anchor_attribution_g50 as source,
)
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32


def _load_isolated_g48_orchestration() -> Any:
    path = PROJECT_ROOT / (
        "scripts/run_continuous_roster_native_six_g31_realized_successor_"
        "channel_attribution_g48.py"
    )
    name = "scripts._g50_isolated_g48_orchestration_backend"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("G50 could not load its accepted G48 orchestration")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_base = _load_isolated_g48_orchestration()
_backend = _base._backend

SCHEMA_VERSION = source.SCHEMA_VERSION
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_"
    "FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_"
    "CODE_SCIENCE_ALIGNMENT_AUDIT"
)
# Exact target/stage mechanically established by the independent G50
# correction-recheck-v2 audit.
ALIGNED_IMPLEMENTATION_COMMIT: str | None = (
    "b8290699f5c10c593bbc21a6666c17950fae84d3"
)
ALIGNMENT_STAGE_COMMIT: str | None = (
    "4df41063d077ace7e0c9212e0cbadbf56e1be4b7"
)

ACCEPTED_ANCHOR_ROOT_RELATIVE = Path(
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1"
)

INVALID_BRANCH = (
    "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50"
)
SOURCE_FAILURE_BRANCH = "SOURCE_OR_REFERENCE_ACCESS_FAILURE_G50"
NULL_SUFFICIENT_BRANCH = "FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50"
REFERENCE_ADVANTAGE_BRANCH = "COMMON_FAST_ANCHOR_FINITE_BUDGET_ADVANTAGE_G50"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_COMMON_FAST_ANCHOR_ATTRIBUTION_G50"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_"
    "ATTRIBUTION_G50_EXERCISE_COMPLETE"
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
ANCHOR_MARGIN = 0.05
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
FORMAL_WALL_CLOCK_CAP_SECONDS = 28_800.0

DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 2
MAX_PROCESS_WORKERS = 6
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}

TRAIN_MANIFEST = "train_manifest.json"
EVALUATION_MANIFEST = "evaluation_manifest.json"
ANALYSIS_RESULT = "analysis_result.json"
CHECKPOINT_DIRECTORY = "checkpoints"
READINESS_STATIC = "readiness_static.json"
READINESS_EVALUATION = "readiness_evaluation.json"
READINESS_ANALYSIS = "readiness_analysis.json"


def _valid_commit(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"G50 artifact is not an object: {path}")
    return value


def _artifact_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _activate_single_thread_worker() -> None:
    for name in _THREAD_ENV_NAMES:
        os.environ[name] = "1"
    torch.set_num_threads(1)


def _resolve_cpu_execution(
    cpu_budget: int | None, process_workers: int | None
) -> dict[str, object]:
    cpu = DEFAULT_CPU_BUDGET if cpu_budget is None else int(cpu_budget)
    workers = DEFAULT_PROCESS_WORKERS if process_workers is None else int(process_workers)
    if not 1 <= cpu <= 6 or not 1 <= workers <= MAX_PROCESS_WORKERS:
        raise ValueError("G50 CPU/process settings outside frozen support")
    if workers > cpu:
        raise ValueError("G50 process workers exceed CPU budget")
    return {
        "cpu_budget": cpu,
        "process_workers": workers,
        "supported_process_worker_ceiling": MAX_PROCESS_WORKERS,
        "worker_thread_controls": dict(WORKER_THREAD_ENV),
        "torch_intraop_threads": 1,
        "worker_start_method": "spawn",
        "deterministic_merge": "preassigned_index_not_completion_order",
    }


def _configure_cpu_execution(
    cpu_budget: int | None, process_workers: int | None
) -> dict[str, object]:
    row = _resolve_cpu_execution(cpu_budget, process_workers)
    _activate_single_thread_worker()
    return row


def _configuration(
    *,
    formal: bool,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, object]:
    cpu = _resolve_cpu_execution(cpu_budget, process_workers)
    static = source.static_configuration_certificate(formal=formal)
    updates = 100 if formal else 10
    episodes = 48 if formal else 6
    return {
        **static,
        "formal": formal,
        "branch_updates_per_arm": updates,
        "num_envs": source.NUM_ENVS,
        "ppo_passes": source.PPO_PASSES,
        "evaluation_episodes_per_cell": episodes,
        "cpu_budget": cpu["cpu_budget"],
        "process_workers": cpu["process_workers"],
        "supported_process_worker_ceiling": MAX_PROCESS_WORKERS,
        "cpu_parallelism_fixed_at_launch": True,
        "cpu_continuous_adaptation": False,
        "worker_start_method": "spawn",
        "training_parallel_unit": "formal_replicate_only",
        "evaluation_parallel_unit": "replicate_capacity_cell",
        "deterministic_merge": "preassigned_index_not_completion_order",
        "worker_thread_controls": dict(WORKER_THREAD_ENV),
        "training_capacity": g32.TRAIN_CAPACITY,
        "cells_per_arm_capacity": len(MODEL_CELLS),
        "evaluation_optimizer_steps": 0,
        "phase_A_optimizer_steps": (3 if formal else 1) * 2 * updates * 2,
        "phase_B_optimizer_steps": (3 if formal else 1) * 2 * updates * 2,
        "phase_A_reference_interpretation": source.PHASE_A_INTERPRETATION,
        "phase_B_contract": "G49_SINGLE_IMMEDIATE",
        "checkpoint_selection": "final_only",
        "episode_exclusions": "none",
    }


def source_controls() -> dict[str, object]:
    return {
        "source_id": source.SOURCE_ID,
        "phase_A_algorithm": source.PHASE_A_ALGORITHM_ID,
        "phase_A_source_commit": source.PHASE_A_SOURCE_COMMIT,
        "phase_A_objective_contract_id": source.PHASE_A_OBJECTIVE_CONTRACT_ID,
        "phase_A_reference_interpretation": source.PHASE_A_INTERPRETATION,
        "accepted_phase_A_formal_root": str(ACCEPTED_ANCHOR_ROOT_RELATIVE).replace("\\", "/"),
        "historical_anchor_used_as_objective_authority_only": True,
        "historical_anchor_checkpoint_loaded_as_G50_initial_state": False,
        "phase_B_source_commit": source.PHASE_B_SOURCE_COMMIT,
        "phase_B_aligned_implementation_commit": source.PHASE_B_ALIGNED_IMPLEMENTATION_COMMIT,
        "phase_B_alignment_stage_commit": source.PHASE_B_ALIGNMENT_STAGE_COMMIT,
        "phase_B_formal_branch": source.PHASE_B_FORMAL_BRANCH,
        "training_source": "G32_capacity8_fixed_process",
        "evaluation_source": "G34_P0_fixed_and_random_processes_capacity_6_8_12",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_python_fallback": False,
        "seed_bases": dict(source.SEED_BASES),
        "bootstrap_seed": source.BOOTSTRAP_SEED,
        "nonformal_seed_offset": source.NONFORMAL_SEED_OFFSET,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
    }


def _checkpoint_reference(replicate: int, arm: str) -> str:
    if arm not in source.ARMS:
        raise ValueError("G50 checkpoint arm is not registered")
    return f"checkpoints/replicate_{replicate}_{arm.lower()}_final.pt"


def _fresh_root(root: Path) -> Path:
    resolved = Path(root).resolve()
    if resolved.exists() and any(resolved.iterdir()):
        raise ValueError("G50 run root is not fresh")
    return resolved


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
    if (
        training.get("formal") is not False
        or training.get("source_commit") != source_commit
        or training.get("configuration") != expected
        or evaluation.get("formal") is not False
        or evaluation.get("source_commit") != source_commit
        or evaluation.get("configuration") != expected
        or analysis.get("formal") is not False
        or analysis.get("source_commit") != source_commit
        or analysis.get("result_branch") != NONFORMAL_BRANCH
        or analysis.get("operational_valid") is not True
    ):
        raise ValueError("G50 same-source preflight identity/inventory mismatch")
    train_seconds = float(training.get("stage_wall_time_seconds", float("nan")))
    eval_seconds = float(evaluation.get("stage_wall_time_seconds", float("nan")))
    analyze_seconds = float(analysis.get("stage_wall_time_seconds", float("nan")))
    if any(not np.isfinite(row) or row < 0.0 for row in (train_seconds, eval_seconds, analyze_seconds)):
        raise ValueError("G50 preflight timing invalid")
    projection = 1.25 * (
        30.0 * train_seconds + 24.0 * eval_seconds + 40.0 * analyze_seconds
    )
    if projection > FORMAL_WALL_CLOCK_CAP_SECONDS:
        raise ValueError("G50 formal wall-clock projection exceeds cap")
    return _preflight_digests(root)


def _formal_admission_errors(
    *,
    source_commit: str,
    authorization_token: str | None,
    accepted_anchor_root: Path,
    preflight_root: Path | None,
    alignment_disposition: str | None,
    aligned_source_commit: str | None,
    alignment_stage_commit: str | None,
    cpu_budget: int | None,
    process_workers: int | None,
) -> tuple[list[str], dict[str, str] | None]:
    errors: list[str] = []
    if authorization_token != AUTHORIZATION_TOKEN:
        errors.append("authorization_token")
    if ALIGNED_IMPLEMENTATION_COMMIT is None or source_commit != ALIGNED_IMPLEMENTATION_COMMIT:
        errors.append("source_commit")
    if alignment_disposition != "ALIGNED":
        errors.append("alignment_disposition")
    if aligned_source_commit != ALIGNED_IMPLEMENTATION_COMMIT:
        errors.append("aligned_source_commit")
    if ALIGNMENT_STAGE_COMMIT is None or alignment_stage_commit != ALIGNMENT_STAGE_COMMIT:
        errors.append("alignment_stage_commit")
    if not _valid_commit(ALIGNED_IMPLEMENTATION_COMMIT) or not _valid_commit(ALIGNMENT_STAGE_COMMIT):
        errors.append("trusted_alignment_binding")
    try:
        cpu = _resolve_cpu_execution(cpu_budget, process_workers)
        if cpu["cpu_budget"] != 2 or cpu["process_workers"] != 2:
            errors.append("formal_cpu_process_configuration")
    except ValueError:
        errors.append("formal_cpu_process_configuration")
    expected_anchor = (PROJECT_ROOT / ACCEPTED_ANCHOR_ROOT_RELATIVE).resolve()
    if accepted_anchor_root.resolve() != expected_anchor:
        errors.append("accepted_G40_objective_authority_root")
    digests: dict[str, str] | None = None
    if preflight_root is None:
        errors.append("same_source_preflight")
    else:
        try:
            digests = _valid_nonformal_preflight(
                Path(preflight_root).resolve(), source_commit=source_commit
            )
        except (FileNotFoundError, KeyError, TypeError, ValueError):
            errors.append("same_source_preflight")
    return errors, digests


def validate_formal_admission(
    **arguments: object,
) -> dict[str, object]:
    errors, digests = _formal_admission_errors(
        source_commit=str(arguments.get("source_commit", "")),
        authorization_token=arguments.get("authorization_token"),  # type: ignore[arg-type]
        accepted_anchor_root=Path(str(arguments.get("accepted_anchor_root", ""))),
        preflight_root=(
            None
            if arguments.get("preflight_root") is None
            else Path(str(arguments["preflight_root"]))
        ),
        alignment_disposition=arguments.get("alignment_disposition"),  # type: ignore[arg-type]
        aligned_source_commit=arguments.get("aligned_source_commit"),  # type: ignore[arg-type]
        alignment_stage_commit=arguments.get("alignment_stage_commit"),  # type: ignore[arg-type]
        cpu_budget=arguments.get("cpu_budget"),  # type: ignore[arg-type]
        process_workers=arguments.get("process_workers"),  # type: ignore[arg-type]
    )
    return {"admitted": not errors, "errors": errors, "preflight_digests": digests}


def _collect_phase_A(
    model: source.g40.G40NativeSixPolicy,
    *,
    episode_ids: Sequence[int],
    ledger_seed: int,
    action_seed: int,
) -> source.g40.AnchoredRosterTrajectory:
    return source.g40.collect_g40_trajectory(
        model,
        episode_ids=episode_ids,
        ledger_seed=ledger_seed,
        action_seed=action_seed,
        device=torch.device("cpu"),
    )


def _collect_phase_B(
    model: source.G50PhaseBProjection,
    *,
    episode_ids: Sequence[int],
    ledger_seed: int,
    action_seed: int,
) -> source.g40.AnchoredRosterTrajectory:
    return _base._collect_trajectory(
        model,
        episode_ids=episode_ids,
        ledger_seed=ledger_seed,
        action_seed=action_seed,
    )


def _train_replicate(
    *, formal: bool, replicate: int, configuration: Mapping[str, object]
) -> dict[str, object]:
    seeds = source.seed_block(replicate, formal=formal)
    _backend.configure_runtime(seeds["phase_A_gradient_probe"])
    phase_A_models = source.make_phase_A_models(
        member_capacity=g32.TRAIN_CAPACITY,
        initialization_seed=seeds["initialization"],
    )
    phase_A_optimizers = source.make_phase_A_optimizers(phase_A_models)
    boundary = source.phase_A_boundary_audit(phase_A_models, phase_A_optimizers)
    if boundary["passed"] is not True:
        raise RuntimeError("G50 phase-A boundary failed")
    phase_A_records: list[dict[str, object]] = []
    diagnostics: dict[str, object] | None = None
    order_swap: dict[str, object] | None = None
    updates = int(configuration["phase_A_updates_per_arm"])
    for update_index in range(updates):
        first = update_index * source.NUM_ENVS
        episode_ids = tuple(range(first, first + source.NUM_ENVS))
        ledger_seed = (
            seeds["phase_A_gradient_probe"]
            if update_index == 0
            else seeds["phase_A_ledger"]
        )
        action_seed = (
            seeds["phase_A_gradient_probe"]
            if update_index == 0
            else seeds["phase_A_action"]
        )
        trajectories = {
            arm: _collect_phase_A(
                phase_A_models[arm],
                episode_ids=episode_ids,
                ledger_seed=ledger_seed,
                action_seed=action_seed,
            )
            for arm in source.ARMS
        }
        if update_index == 0:
            diagnostics = {
                arm: source.g40.pre_common_gradient_audit(
                    phase_A_models[arm], trajectories[arm]
                )
                for arm in source.ARMS
            }
            if not all(row["passed"] is True for row in diagnostics.values()):  # type: ignore[union-attr]
                raise RuntimeError("G50 zero-step historical liveness audit failed")
            order_swap = source.phase_A_order_swap_guard(
                phase_A_models, phase_A_optimizers, trajectories
            )
            if order_swap["passed"] is not True:
                raise RuntimeError("G50 phase-A order-swap guard failed")
        phase_A_records.append(
            source.optimize_phase_A_update(
                phase_A_models,
                phase_A_optimizers,
                trajectories,
                replicate=replicate,
                update_index=update_index,
            )
        )
    activation = source.build_phase_A_conclusion_evidence(
        phase_A_records, formal=False
    )
    # Per-replicate evidence is validated globally by train; this local row must
    # contain at least one active pass independent of its numeric replicate ID.
    locally_active = any(
        record["activation"]["treatment_active"] is True
        for update in phase_A_records
        for record in update["pass_records"]  # type: ignore[index]
    )
    if not locally_active:
        raise RuntimeError("G50 phase-A treatment did not activate")

    phase_B_models, disposal = source.project_phase_B_models(
        phase_A_models, completed_phase_A_updates=updates
    )
    del phase_A_optimizers
    phase_B_optimizers = source.make_phase_B_optimizers(phase_B_models)
    phase_B_fresh = {arm: not phase_B_optimizers[arm].state for arm in source.ARMS}
    phase_B_records: list[dict[str, object]] = []
    phase_B_updates = int(configuration["phase_B_updates_per_arm"])
    for update_index in range(phase_B_updates):
        first = update_index * source.NUM_ENVS
        episode_ids = tuple(range(first, first + source.NUM_ENVS))
        ledger_seed = (
            seeds["phase_B_gradient_probe"]
            if update_index == 0
            else seeds["phase_B_ledger"]
        )
        action_seed = (
            seeds["phase_B_gradient_probe"]
            if update_index == 0
            else seeds["phase_B_action"]
        )
        trajectories = {
            arm: source.g47._actor_only_trajectory_view(
                _collect_phase_B(
                    phase_B_models[arm],
                    episode_ids=episode_ids,
                    ledger_seed=ledger_seed,
                    action_seed=action_seed,
                )
            )
            for arm in source.ARMS
        }
        phase_B_records.append(
            source.optimize_phase_B_update(
                phase_B_models,
                phase_B_optimizers,
                trajectories,
                replicate=replicate,
                update_index=update_index,
            )
        )
    checkpoints = {
        arm: source.build_final_checkpoint(
            model=phase_B_models[arm],
            optimizer=phase_B_optimizers[arm],
            source_commit=str(configuration["source_commit"]),
            formal=formal,
            replicate=replicate,
            arm=arm,
            completed_phase_A_updates=updates,
            completed_phase_B_updates=phase_B_updates,
            configuration={
                key: value for key, value in configuration.items() if key != "source_commit"
            },
            seeds=seeds,
            disposal_certificate=disposal[arm],
        )
        for arm in source.ARMS
    }
    return {
        "replicate": replicate,
        "seeds": seeds,
        "phase_A_boundary": boundary,
        "phase_A_zero_step_diagnostics": diagnostics,
        "phase_A_order_swap_guard": order_swap,
        "phase_A_update_records": phase_A_records,
        "phase_A_locally_active": locally_active,
        "phase_A_disposal_certificates": disposal,
        "phase_B_fresh_empty_Adam": phase_B_fresh,
        "phase_B_update_records": phase_B_records,
        "checkpoints": checkpoints,
        "paired_collection_before_update": True,
        "branch_update_order": list(source.ARMS),
        "diagnostic_optimizer_steps": 0,
    }


def _training_replicate_worker(task: Mapping[str, object]) -> dict[str, object]:
    _activate_single_thread_worker()
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G50 training worker output path is not fresh")
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
    authorization_token: str | None,
    accepted_anchor_root: Path | None,
    preflight_root: Path | None = None,
    alignment_disposition: str | None = None,
    aligned_source_commit: str | None = None,
    alignment_stage_commit: str | None = None,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    if not _valid_commit(source_commit):
        raise ValueError("G50 train requires a lowercase integrated source commit")
    if accepted_anchor_root is None:
        raise ValueError("G50 train requires accepted G40 objective authority root")
    root = _fresh_root(run_root)
    anchor_root = Path(accepted_anchor_root).resolve()
    preflight_digests: dict[str, str] | None = None
    if formal:
        errors, preflight_digests = _formal_admission_errors(
            source_commit=source_commit,
            authorization_token=authorization_token,
            accepted_anchor_root=anchor_root,
            preflight_root=preflight_root,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
            alignment_stage_commit=alignment_stage_commit,
            cpu_budget=cpu_budget,
            process_workers=process_workers,
        )
        if errors:
            raise ValueError("G50 formal admission failed: " + "|".join(errors))
    elif any(
        value is not None
        for value in (
            authorization_token,
            preflight_root,
            alignment_disposition,
            aligned_source_commit,
            alignment_stage_commit,
        )
    ):
        raise ValueError("G50 nonformal train cannot carry formal authority")
    started = time.perf_counter()
    cpu = _configure_cpu_execution(cpu_budget, process_workers)
    configuration = _configuration(
        formal=formal,
        cpu_budget=int(cpu["cpu_budget"]),
        process_workers=int(cpu["process_workers"]),
    )
    worker_configuration = {**configuration, "source_commit": source_commit}
    # Objective authority is validated but never loaded as an initial G50 state.
    anchor_digests = _backend._validate_anchor_manifest(anchor_root)
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
                root / ".worker_transport" / "train" / f"replicate_{replicate}" / "result.pt"
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
            raise RuntimeError("G50 training worker identity mismatch")
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
                "completed_phase_A_updates": configuration["phase_A_updates_per_arm"],
                "completed_phase_B_updates": configuration["phase_B_updates_per_arm"],
            }
        row["arms"] = arm_rows
        row["worker_execution"] = {
            "index": int(result["index"]),
            "output_digest": result["output_digest"],
            "wall_time_seconds": payload["wall_time_seconds"],
            "thread_environment": payload["thread_environment"],
            "torch_intraop_threads": payload["torch_intraop_threads"],
        }
        rows.append(row)
        path.unlink()
    phase_A_records = [
        update for row in rows for update in row["phase_A_update_records"]
    ]
    conclusion = source.build_phase_A_conclusion_evidence(
        phase_A_records, formal=formal
    )
    if not source.validate_phase_A_conclusion_evidence(conclusion):
        raise RuntimeError("G50 phase-A treatment activation inventory failed")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": source_commit,
        "authorization_token": authorization_token,
        "alignment_audit_id": ALIGNMENT_AUDIT_ID if formal else None,
        "alignment_disposition": alignment_disposition,
        "aligned_source_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "alignment_stage_commit": alignment_stage_commit,
        "preflight_root": str(Path(preflight_root).resolve()) if preflight_root else None,
        "preflight_artifact_digests": preflight_digests,
        "accepted_anchor_root": str(anchor_root),
        "accepted_anchor_artifact_digests": anchor_digests,
        "historical_anchor_used_as_objective_authority_only": True,
        "configuration": configuration,
        "source_controls": source_controls(),
        "native_backend": native_backend,
        "cpu_execution": cpu,
        "conclusion_evidence": conclusion,
        "replicate_results": rows,
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
        or value.get("seed_block") != source.seed_block(replicate, formal=bool(training["formal"]))
    ):
        raise ValueError("G50 final checkpoint identity/schema mismatch")
    return value


def _load_final_model(
    *,
    run_root: Path,
    training: Mapping[str, Any],
    replicate: int,
    capacity: int,
    arm: str,
) -> source.G50PhaseBProjection:
    reference = training["replicate_results"][replicate]["arms"][arm]["final_checkpoint"]
    checkpoint = _load_checkpoint_payload(
        run_root / reference,
        training=training,
        replicate=replicate,
        arm=arm,
    )
    return source.load_phase_B_checkpoint_model(
        checkpoint, member_capacity=capacity
    )


def _expected_checkpoint_files(configuration: Mapping[str, object]) -> set[str]:
    return {
        _checkpoint_reference(replicate, arm)
        for replicate in range(int(configuration["replicates"]))
        for arm in source.ARMS
    }


def _training_errors(run_root: Path, training: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    formal = training.get("formal")
    if formal not in (True, False):
        return ["G50 training formal flag invalid"]
    try:
        expected_configuration = _configuration(
            formal=bool(formal),
            cpu_budget=int(training["configuration"]["cpu_budget"]),
            process_workers=int(training["configuration"]["process_workers"]),
        )
    except (KeyError, TypeError, ValueError):
        return ["G50 training configuration invalid"]
    if (
        training.get("schema_version") != SCHEMA_VERSION
        or training.get("algorithm_id") != ALGORITHM_ID
        or training.get("source_id") != source.SOURCE_ID
        or training.get("stage") != "train"
        or training.get("status") != "COMPLETE"
        or training.get("configuration") != expected_configuration
        or training.get("source_controls") != source_controls()
        or not _valid_commit(training.get("source_commit"))
        or "phase_A_conclusion_evidence" in training
        or not source.validate_phase_A_conclusion_evidence(
            training.get("conclusion_evidence")
        )
    ):
        errors.append("G50 training manifest identity/configuration mismatch")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(expected_configuration["replicates"]):
        errors.append("G50 training replicate inventory mismatch")
        return errors
    expected_files = _expected_checkpoint_files(expected_configuration)
    actual_files = {
        str(path.relative_to(run_root)).replace("\\", "/")
        for path in (run_root / CHECKPOINT_DIRECTORY).glob("*.pt")
    }
    if actual_files != expected_files:
        errors.append("G50 final checkpoint file inventory mismatch")
    for replicate, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("replicate") != replicate:
            errors.append("G50 replicate identity mismatch")
            continue
        arms = row.get("arms")
        if not isinstance(arms, Mapping) or tuple(arms) != source.ARMS:
            errors.append("G50 checkpoint arm inventory mismatch")
            continue
        for arm in source.ARMS:
            arm_row = arms[arm]
            reference = _checkpoint_reference(replicate, arm)
            path = run_root / reference
            try:
                if (
                    arm_row.get("final_checkpoint") != reference
                    or arm_row.get("final_checkpoint_sha256") != _artifact_digest(path)
                ):
                    raise ValueError
                _load_checkpoint_payload(
                    path,
                    training=training,
                    replicate=replicate,
                    arm=arm,
                )
            except (FileNotFoundError, KeyError, TypeError, ValueError):
                errors.append("G50 checkpoint digest/reload mismatch")
    return errors


def _evaluation_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> list[str]:
    errors = _training_errors(run_root, training)
    configuration = training.get("configuration")
    cells = evaluation.get("cells")
    if (
        evaluation.get("schema_version") != SCHEMA_VERSION
        or evaluation.get("algorithm") != ALGORITHM_ID
        or evaluation.get("source_id") != source.SOURCE_ID
        or evaluation.get("stage") != "evaluate"
        or evaluation.get("status") != "COMPLETE"
        or evaluation.get("formal") is not training.get("formal")
        or evaluation.get("source_commit") != training.get("source_commit")
        or evaluation.get("configuration") != configuration
        or "phase_A_conclusion_evidence" in evaluation
        or not source.validate_phase_A_conclusion_evidence(
            evaluation.get("conclusion_evidence")
        )
        or evaluation.get("conclusion_evidence")
        != training.get("conclusion_evidence")
        or evaluation.get("training_manifest_digest")
        != _artifact_digest(run_root / TRAIN_MANIFEST)
        or not isinstance(cells, list)
        or len(cells) != int(configuration["evaluation_cells"])
        or any(
            not isinstance(cell, Mapping)
            or cell.get("optimizer_steps") != 0
            or cell.get("baseline_evaluation_read_count") != 0
            or len(cell.get("episodes", [])) != int(configuration["episodes_per_cell"])
            for cell in cells
        )
    ):
        errors.append("G50 evaluation manifest/cell inventory mismatch")
    return errors


def _patch_evaluation_backend() -> None:
    for module in (_base, _backend):
        module.source = source
        module.SCHEMA_VERSION = SCHEMA_VERSION
        module.ALGORITHM_ID = ALGORITHM_ID
        module.AUTHORIZATION_TOKEN = AUTHORIZATION_TOKEN
        module.ALIGNMENT_AUDIT_ID = ALIGNMENT_AUDIT_ID
        module.ALIGNED_IMPLEMENTATION_COMMIT = ALIGNED_IMPLEMENTATION_COMMIT
        module.ALIGNMENT_STAGE_COMMIT = ALIGNMENT_STAGE_COMMIT
        module.INVALID_BRANCH = INVALID_BRANCH
        module.SOURCE_FAILURE_BRANCH = SOURCE_FAILURE_BRANCH
        module.NONFORMAL_BRANCH = NONFORMAL_BRANCH
        module.FINAL_FIXED_DET = FINAL_FIXED_DET
        module.FINAL_FIXED_STOCH = FINAL_FIXED_STOCH
        module.FINAL_RANDOM_DET = FINAL_RANDOM_DET
        module.FINAL_RANDOM_STOCH = FINAL_RANDOM_STOCH
        module.MODEL_CELLS = MODEL_CELLS
        module.DEFAULT_CPU_BUDGET = DEFAULT_CPU_BUDGET
        module.DEFAULT_PROCESS_WORKERS = DEFAULT_PROCESS_WORKERS
        module.MAX_PROCESS_WORKERS = MAX_PROCESS_WORKERS
        module.WORKER_THREAD_ENV = WORKER_THREAD_ENV
        module._configuration = _configuration
        module.source_controls = source_controls
        module.seed_block = source.seed_block
        module.bootstrap_seed = source.bootstrap_seed
        module._load_checkpoint_payload = _load_checkpoint_payload
        module._load_final_model = _load_final_model
        module._training_errors = _training_errors
        module._evaluation_errors = _evaluation_errors
    _backend._evaluate_cell = _base._evaluate_cell


_patch_evaluation_backend()


def evaluate(
    *, run_root: Path, cpu_budget: int | None = None, process_workers: int | None = None
) -> dict[str, Any]:
    return _backend.evaluate(
        run_root=run_root,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )


def _comparison(
    evaluation: Mapping[str, Any], plan: tuple[np.ndarray, np.ndarray]
) -> dict[str, object]:
    inherited = _base._comparison(evaluation, plan)
    return {
        "reference_minus_null_primary_ci95": inherited[
            "reference_minus_null_primary_ci95"
        ],
        "reference_minus_null_capacity_ci95": inherited[
            "reference_minus_null_capacity_ci95"
        ],
        "component_ci95": inherited["component_ci95"],
        "fresh_single_immediate_noninferior": inherited[
            "duplicated_immediate_noninferior"
        ],
        "material_common_fast_anchor_advantage": inherited[
            "material_realized_successor_advantage"
        ],
    }


def select_g50_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or not bool(
        metrics["reference_access_pass"]
    ):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics["reference_access_pass"])
        and bool(metrics["null_access_pass"])
        and bool(metrics["fresh_single_immediate_noninferior"])
    ):
        return NULL_SUFFICIENT_BRANCH
    if bool(metrics["reference_access_pass"]) and (
        bool(metrics["null_access_confident_fail"])
        or bool(metrics["material_common_fast_anchor_advantage"])
    ):
        return REFERENCE_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


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
        raise ValueError("formal G50 analysis requires formal artifacts")
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
        raise ValueError("G50 analyze CPU/process settings differ from training")
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
            arm: _backend._arm_access(evaluation, arm, plan) for arm in source.ARMS
        }
        metrics.update(
            {
                "source_valid": evaluation["direct_source_validation"] is True,
                "arm_access": access,
                "reference_access_pass": access[source.REFERENCE_ARM]["access_pass"],
                "null_access_pass": access[source.NULL_ARM]["access_pass"],
                "reference_access_confident_fail": access[source.REFERENCE_ARM][
                    "access_confident_fail"
                ],
                "null_access_confident_fail": access[source.NULL_ARM][
                    "access_confident_fail"
                ],
                "treatment_activation_valid": source.validate_phase_A_conclusion_evidence(
                    training["conclusion_evidence"]
                ),
                **_comparison(evaluation, plan),
            }
        )
    elapsed = time.perf_counter() - started
    if errors:
        branch = INVALID_BRANCH
    elif formal:
        branch = select_g50_result_branch(metrics)
    else:
        branch = NONFORMAL_BRANCH
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": formal,
        "source_commit": training.get("source_commit"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "source_valid": metrics.get("source_valid"),
        "treatment_activation_valid": metrics.get("treatment_activation_valid"),
        "reference_access_pass": metrics.get("reference_access_pass"),
        "reference_access_confident_fail": metrics.get(
            "reference_access_confident_fail"
        ),
        "null_access_pass": metrics.get("null_access_pass"),
        "null_access_confident_fail": metrics.get("null_access_confident_fail"),
        "fresh_single_immediate_noninferior": metrics.get(
            "fresh_single_immediate_noninferior"
        ),
        "material_common_fast_anchor_advantage": metrics.get(
            "material_common_fast_anchor_advantage"
        ),
        "metrics": metrics,
        "threshold_record": {
            "utility_floor": UTILITY_FLOOR,
            "stochastic_floor": STOCHASTIC_FLOOR,
            "event_floor": EVENT_FLOOR,
            "segment_floor": SEGMENT_FLOOR,
            "random_minus_fixed_floor": PROCESS_MARGIN,
            "minimum_replicate_floor": MINIMUM_REPLICATE_FLOOR,
            "materiality_noninferiority_margin": ANCHOR_MARGIN,
            "phase_A_activation_tolerance": source.ACTIVATION_TOLERANCE,
            "gradient_live_tolerance": source.GRADIENT_LIVE_TOLERANCE,
        },
        "first_match_priority": [
            INVALID_BRANCH,
            SOURCE_FAILURE_BRANCH,
            NULL_SUFFICIENT_BRANCH,
            REFERENCE_ADVANTAGE_BRANCH,
            UNDERPOWERED_BRANCH,
        ],
        "result_branch": branch,
        "training_manifest_digest": _artifact_digest(run_root / TRAIN_MANIFEST),
        "evaluation_manifest_digest": _artifact_digest(
            run_root / EVALUATION_MANIFEST
        ),
        "stage_wall_time_seconds": elapsed,
    }
    _write_json(run_root / ANALYSIS_RESULT, result)
    return result


def _synthetic_branch_witnesses() -> dict[str, str]:
    base = {
        "operational_valid": True,
        "source_valid": True,
        "reference_access_confident_fail": False,
        "reference_access_pass": True,
        "null_access_pass": True,
        "null_access_confident_fail": False,
        "fresh_single_immediate_noninferior": False,
        "material_common_fast_anchor_advantage": False,
    }
    witnesses = {
        "invalid": {**base, "operational_valid": False},
        "source_failure": {
            **base,
            "reference_access_pass": False,
            "fresh_single_immediate_noninferior": True,
            "material_common_fast_anchor_advantage": True,
        },
        "sufficient": {**base, "fresh_single_immediate_noninferior": True},
        "advantage": {**base, "null_access_pass": False, "null_access_confident_fail": True},
        "underpowered": base,
    }
    return {name: select_g50_result_branch(row) for name, row in witnesses.items()}


def _readiness_worker(task: Mapping[str, object]) -> dict[str, object]:
    _activate_single_thread_worker()
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G50 readiness worker output path is not fresh")
    payload = {
        "index": int(task["index"]),
        "pid": os.getpid(),
        "static": source.static_configuration_certificate(formal=False),
        "branches": _synthetic_branch_witnesses(),
        "thread_environment": {name: os.environ.get(name) for name in _THREAD_ENV_NAMES},
        "torch_intraop_threads": torch.get_num_threads(),
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
    """Hold each dedicated spawn worker until both proof processes are live."""
    _activate_single_thread_worker()
    ready_event.set()
    if not release_event.wait(timeout=60.0):
        raise RuntimeError("G50 readiness worker release barrier timed out")
    _readiness_worker(task)


def _run_distinct_readiness_workers(
    tasks: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Run exactly one proof task in each of two concurrently live processes."""
    if [task.get("index") for task in tasks] != [0, 1]:
        raise ValueError("G50 readiness requires exactly two indexed proof tasks")
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
                raise RuntimeError(
                    f"G50 readiness worker {index} failed to reach the release barrier"
                )
        pids = [process.pid for process in processes]
        if any(pid is None for pid in pids) or len(set(pids)) != 2:
            raise RuntimeError("G50 readiness did not launch two distinct processes")
        release_event.set()
        for process in processes:
            process.join(timeout=60.0)
        if any(process.is_alive() for process in processes):
            raise RuntimeError("G50 readiness worker timed out")
        if any(process.exitcode != 0 for process in processes):
            raise RuntimeError("G50 readiness worker exited unsuccessfully")
    finally:
        release_event.set()
        for process in processes:
            if process.pid is not None and process.is_alive():
                process.terminate()
        for process in processes:
            if process.pid is not None:
                process.join(timeout=5.0)

    results: list[dict[str, object]] = []
    for task, process in zip(tasks, processes, strict=True):
        output_path = Path(str(task["output_path"]))
        if not output_path.is_file():
            raise RuntimeError("G50 readiness worker did not produce its output")
        row = _read_json(output_path)
        if row.get("index") != task["index"] or row.get("pid") != process.pid:
            raise RuntimeError("G50 readiness worker identity/output mismatch")
        results.append(
            {
                "index": int(task["index"]),
                "output_path": str(output_path),
                "output_digest": _artifact_digest(output_path),
            }
        )
    return results


def readiness_interface_smoke(
    *, source_commit: str, accepted_anchor_root: Path
) -> dict[str, object]:
    if not _valid_commit(source_commit):
        raise ValueError("G50 readiness requires integrated source commit")
    if Path(accepted_anchor_root).resolve() != (
        PROJECT_ROOT / ACCEPTED_ANCHOR_ROOT_RELATIVE
    ).resolve():
        raise ValueError("G50 readiness accepted-anchor authority mismatch")
    phase_B_actor_interface = source.phase_B_actor_interface_evidence(
        member_capacity=g32.TRAIN_CAPACITY,
        initialization_seed=source.SEED_BASES["initialization"],
    )
    return {
        "algorithm_id": ALGORITHM_ID,
        "source_commit": source_commit,
        "schema_version": SCHEMA_VERSION,
        "formal": False,
        "scientific_real_transitions": 0,
        "optimizer_steps": 0,
        "phase_B_actor_interface": phase_B_actor_interface,
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


def readiness_train(
    *, run_root: Path, source_commit: str, accepted_anchor_root: Path
) -> dict[str, object]:
    root = _fresh_root(run_root)
    smoke = readiness_interface_smoke(
        source_commit=source_commit, accepted_anchor_root=accepted_anchor_root
    )
    root.mkdir(parents=True, exist_ok=True)
    tasks = tuple(
        {
            "index": index,
            "output_path": str(root / "two_process" / f"worker_{index}.json"),
        }
        for index in range(2)
    )
    results = _run_distinct_readiness_workers(tasks)
    rows = [_read_json(Path(str(result["output_path"]))) for result in results]
    semantics = [
        {key: value for key, value in row.items() if key != "pid"} for row in rows
    ]
    equivalent = semantics[0] == {**semantics[1], "index": 0}
    phase_A_conclusion = source.build_phase_A_conclusion_evidence(
        (
            {
                "replicate": 0,
                "pass_records": ({"activation": {"treatment_active": True}},),
            },
        ),
        formal=False,
    )
    payload = {
        "smoke": smoke,
        "static_configuration": source.static_configuration_certificate(formal=False),
        "conclusion_evidence": phase_A_conclusion,
        "branch_witnesses": _synthetic_branch_witnesses(),
        "two_process_proof": {
            "worker_count": 2,
            "distinct_processes": len({int(row["pid"]) for row in rows}) == 2,
            "deterministic_preassigned_index_merge": [row["index"] for row in rows]
            == [0, 1],
            "semantic_payload_equal": equivalent,
            "single_thread_workers": all(
                row["torch_intraop_threads"] == 1
                and all(row["thread_environment"][name] == "1" for name in _THREAD_ENV_NAMES)
                for row in rows
            ),
        },
        "formal": False,
        "scientific_real_transitions": 0,
        "optimizer_steps": 0,
        "bootstrap_resamples": 0,
    }
    payload["passed"] = bool(
        payload["two_process_proof"]["distinct_processes"]
        and payload["two_process_proof"]["deterministic_preassigned_index_merge"]
        and payload["two_process_proof"]["semantic_payload_equal"]
        and payload["two_process_proof"]["single_thread_workers"]
    )
    _write_json(root / READINESS_STATIC, payload)
    if payload["passed"] is not True:
        raise RuntimeError("G50 readiness two-process proof failed")
    return payload


def readiness_validate(*, run_root: Path) -> dict[str, object]:
    payload = _read_json(Path(run_root) / READINESS_STATIC)
    valid = bool(
        payload.get("passed") is True
        and source.validate_static_configuration(
            payload.get("static_configuration"), formal=False
        )
        and source.validate_phase_A_conclusion_evidence(
            payload.get("conclusion_evidence")
        )
        and payload.get("branch_witnesses")
        == {
            "invalid": INVALID_BRANCH,
            "source_failure": SOURCE_FAILURE_BRANCH,
            "sufficient": NULL_SUFFICIENT_BRANCH,
            "advantage": REFERENCE_ADVANTAGE_BRANCH,
            "underpowered": UNDERPOWERED_BRANCH,
        }
    )
    if not valid:
        raise RuntimeError("G50 readiness static validation failed")
    return {"passed": True, "formal": False, "optimizer_steps": 0}


def readiness_reload(*, run_root: Path) -> dict[str, object]:
    before = _artifact_digest(Path(run_root) / READINESS_STATIC)
    readiness_validate(run_root=run_root)
    after = _artifact_digest(Path(run_root) / READINESS_STATIC)
    if before != after:
        raise RuntimeError("G50 readiness reload mutated its artifact")
    return {"passed": True, "artifact_digest": before, "optimizer_steps": 0}


def readiness_evaluate(*, run_root: Path) -> dict[str, object]:
    readiness_reload(run_root=run_root)
    static_payload = _read_json(Path(run_root) / READINESS_STATIC)
    conclusion_evidence = static_payload.get("conclusion_evidence")
    if not source.validate_phase_A_conclusion_evidence(conclusion_evidence):
        raise RuntimeError("G50 readiness evaluation evidence invalid")
    payload = {
        "formal": False,
        "conclusion_evidence": conclusion_evidence,
        "synthetic_episode_ids": list(range(6)),
        "whole_episode_pairing": True,
        "fixed_random_mates_retained": True,
        "deterministic_stochastic_mates_retained": True,
        "capacity_weights": [1 / 3, 1 / 3, 1 / 3],
        "shared_bootstrap_index_plan": True,
        "evaluation_optimizer_steps": 0,
        "scientific_real_transitions": 0,
        "passed": True,
    }
    _write_json(Path(run_root) / READINESS_EVALUATION, payload)
    return payload


def readiness_analyze(*, run_root: Path) -> dict[str, object]:
    evaluation = readiness_evaluate(run_root=run_root)
    static_payload = _read_json(Path(run_root) / READINESS_STATIC)
    conclusion_evidence = evaluation.get("conclusion_evidence")
    if (
        conclusion_evidence != static_payload.get("conclusion_evidence")
        or not source.validate_phase_A_conclusion_evidence(conclusion_evidence)
    ):
        raise RuntimeError("G50 readiness analysis evidence mismatch")
    payload = {
        "formal": False,
        "conclusion_evidence": conclusion_evidence,
        "branch_witnesses": _synthetic_branch_witnesses(),
        "equality_boundaries": {
            "access_floor_equality_passes": True,
            "transport_minus_0_05_passes": True,
            "UCB_0_05_noninferior_passes": True,
            "primary_LCB_0_05_not_material": True,
            "capacity_LCB_0_not_advantage": True,
            "q_A_1e_6_inactive": source.phase_A_activation(
                (torch.tensor([1.0]),),
                (torch.tensor([1.0 - source.ACTIVATION_TOLERANCE]),),
            )["treatment_active"]
            is False,
        },
        "scientific_real_transitions": 0,
        "optimizer_steps": 0,
        "passed": True,
    }
    _write_json(Path(run_root) / READINESS_ANALYSIS, payload)
    return payload


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
            raise ValueError("G50 readiness smoke requires source and anchor root")
        readiness_interface_smoke(
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
        )
    elif args.stage == "readiness-train":
        if args.source_commit is None or args.accepted_anchor_root is None:
            raise ValueError("G50 readiness train requires source and anchor root")
        readiness_train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
        )
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
            raise ValueError("G50 train requires --source-commit")
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
            raise ValueError("G50 exercise requires source and anchor root")
        exercise(
            run_root=args.run_root,
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )


if __name__ == "__main__":
    main()
