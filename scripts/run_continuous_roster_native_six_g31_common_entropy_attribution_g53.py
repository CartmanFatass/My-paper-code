"""Run the frozen fresh G53 common-entropy attribution package."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import re
import shutil
import sys
import time
from typing import Any, Mapping, Sequence

_THREAD_ENV_NAMES = (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"
)
for _name in _THREAD_ENV_NAMES:
    os.environ[_name] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import (
    continuous_roster_native_six_g31_common_entropy_attribution_g53 as source,
)
from envs.continuous_roster import runtime_capacity as roster_env


SCHEMA_VERSION = source.SCHEMA_VERSION
ALGORITHM_ID = source.ALGORITHM_ID
INVALID_BRANCH = source.INVALID_BRANCH
NONFORMAL_BRANCH = source.NONFORMAL_BRANCH
PHASES = (
    "train", "evaluate", "analyze", "exercise", "readiness-smoke",
    "readiness-train", "readiness-validate", "readiness-reload",
    "readiness-evaluate", "readiness-analyze",
)
MODEL_CELLS = (
    "final_fixed_deterministic", "final_fixed_stochastic",
    "final_random_deterministic", "final_random_stochastic",
)
TRAIN_MANIFEST = "train_manifest.json"
EVALUATION_MANIFEST = "evaluation_manifest.json"
ANALYSIS_RESULT = "analysis_result.json"
CHECKPOINT_DIRECTORY = "checkpoints"
TRANSIENT_DIRECTORY = ".worker_transport"
DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 2
MAX_AGGREGATE_RSS_BYTES = 2_147_483_648
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}


def _valid_commit(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"G53 artifact is not an object: {path}")
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fresh_root(root: Path) -> Path:
    resolved = Path(root).resolve()
    if resolved.exists() and any(resolved.iterdir()):
        raise ValueError("G53 run root must be fresh")
    return resolved


def _activate_worker() -> None:
    for name in _THREAD_ENV_NAMES:
        os.environ[name] = "1"
    torch.set_num_threads(1)


def _peak_rss_bytes() -> int:
    """Read this Windows worker's peak working set without an extra package."""

    class _Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    counters = _Counters(); counters.cb = ctypes.sizeof(counters)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise OSError("G53 could not read worker RSS")
    return int(counters.PeakWorkingSetSize)


def _cpu_configuration(cpu_budget: int | None, process_workers: int | None) -> dict[str, object]:
    cpu = DEFAULT_CPU_BUDGET if cpu_budget is None else int(cpu_budget)
    workers = DEFAULT_PROCESS_WORKERS if process_workers is None else int(process_workers)
    if cpu != 2 or workers != 2:
        raise ValueError("G53 CPU/process budget is frozen at 2/2")
    return {
        "cpu_budget": 2,
        "process_workers": 2,
        "worker_start_method": "spawn",
        "worker_thread_controls": dict(WORKER_THREAD_ENV),
        "torch_intraop_threads": 1,
        "aggregate_RSS_cap_bytes": MAX_AGGREGATE_RSS_BYTES,
        "wall_clock_cap_seconds": NONFORMAL_WALL_CLOCK_CAP_SECONDS,
    }


def configuration(
    *, formal: bool = False, cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, object]:
    if formal:
        raise ValueError("G53 formal runtime is not authorized")
    return {
        **source.static_configuration_certificate(formal=False),
        **_cpu_configuration(cpu_budget, process_workers),
        "training_capacity": 8,
        "cells_per_arm_capacity": 4,
        "evaluation_optimizer_steps": 0,
        "physical_training_collection_count": 39,
        "arm_update_exposures": 40,
        "training_parallelism": "one_spawned_root_worker",
        "evaluation_parallelism": "two_spawned_cell_workers",
        "deterministic_merge": "preassigned_index_not_completion_order",
    }


def source_controls() -> dict[str, object]:
    return {
        "source_id": source.SOURCE_ID,
        "claim_identity": source.CLAIM_IDENTITY,
        "estimand": source.ESTIMAND,
        "positive_direction": "favors_common_entropy",
        "primary_utility": "capacity_equal_final_random_process_deterministic_action_utility_capacity_6_8_12",
        "margin": source.PRIMARY_MARGIN,
        "G50_provenance_objective_authority_only": True,
        "G51_provenance_projection_authority_only": True,
        "predecessor_artifact_initialization_count": 0,
        "G52_dependency_state_artifact_result_count": 0,
        "training_source": "G32_capacity8_fixed_process",
        "evaluation_source": "G34_P0_fixed_and_random_capacity_6_8_12",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "python_fallback": False,
        "actor_input_coordinates": [
            "capability[0]", "capability[1]", "presentation_priority", "load",
            "target_mix", "log1p(active_count)",
        ],
        "action_dimension": 2,
        "reward_signal": "x_I=r_t",
        "normalization": "one_384_row_float64_center_population_RMS_per_realized_batch",
        "zero_scale_result": "exact_zero",
        "paired_exogenous_roles": ["episode_ID", "ledger", "action_noise"],
        "post_treatment_trajectory_sharing": False,
    }


def _native_backend_identity() -> dict[str, object]:
    backend = source.g40.toy_cpp
    module = backend.load_continuous_roster_toy_cpp_backend()
    return {
        "name": "ContinuousRosterToyBatch_CPU_CPP_required",
        "python_fallback": False,
        "extension_available": True,
        "module": str(module.__name__),
        "build_identity": backend._build_identity(),
    }


def _actor_trajectory(
    model: source.G53PhaseAModel | source.G53PhaseBModel,
    *, episode_ids: Sequence[int], ledger_seed: int, action_seed: int,
) -> source.g47.G47ActorTrajectory:
    ids = tuple(int(value) for value in episode_ids)
    if len(ids) != source.NUM_ENVS or model.member_capacity != roster_env.TRAIN_CAPACITY:
        raise ValueError("G53 collection requires exactly eight capacity-8 episodes")
    ledgers = tuple(
        roster_env.make_ledger(
            episode, master_seed=int(ledger_seed),
            profile=roster_env.TRAIN_PROFILES[episode % len(roster_env.TRAIN_PROFILES)],
        )
        for episode in ids
    )
    envs = tuple(roster_env.RuntimeCapacityRosterEnv(row) for row in ledgers)
    env_batch = source.g40.toy_cpp.ContinuousRosterToyBatch(envs)
    noise = roster_env.make_action_noise(ids, action_seed=int(action_seed), member_capacity=8)
    hidden = torch.zeros((len(ids), 8, model.hidden_dim))
    rows: dict[str, list[torch.Tensor]] = {
        name: [] for name in (
            "observations", "active_mask", "rewards", "hidden_before",
            "terminal_hidden_reset_mask", "pre_tanh_actions", "actions", "old_log_probs",
        )
    }
    model.eval()
    with torch.no_grad():
        for step in range(source.HORIZON):
            views = env_batch.observe_six()
            terminal = torch.zeros((len(ids), 8), dtype=torch.bool)
            for batch_index, view in enumerate(views):
                if view.membership_change.terminally_left:
                    terminal[batch_index, list(view.membership_change.terminally_left)] = True
            source.g40.g39.g32._delete_terminal_hidden(hidden, views)
            observations = torch.as_tensor(np.stack([row.observations for row in views]))
            active = torch.as_tensor(np.stack([row.active_mask for row in views]))
            before = hidden.clone()
            output = source.g47._actor_only_step(
                model, observations=observations, active_mask=active, hidden=hidden,
                sampling_noise=torch.as_tensor(noise[step]),
            )
            rewards = env_batch.advance(
                views, np.ascontiguousarray(output.actions.cpu().numpy(), dtype=np.float32)
            )
            values = {
                "observations": observations,
                "active_mask": active,
                "rewards": torch.as_tensor(np.asarray(rewards, dtype=np.float32)),
                "hidden_before": before,
                "terminal_hidden_reset_mask": terminal,
                "pre_tanh_actions": output.pre_tanh_actions,
                "actions": output.actions,
                "old_log_probs": output.token_log_probs,
            }
            for name, value in values.items():
                rows[name].append(value.detach().cpu())
            hidden = output.next_hidden
    return source.g47.G47ActorTrajectory(**{name: torch.stack(values) for name, values in rows.items()})


def _summarize_update(value: Mapping[str, object]) -> dict[str, object]:
    return {
        "phase": value["phase"], "update_index": value["update_index"],
        "shared_pretreatment_physical_collection_count": value["shared_pretreatment_physical_collection_count"],
        "arm_exposures": value["arm_exposures"],
        "paired_episode_IDs": value["paired_episode_IDs"],
        "post_treatment_arm_local_on_policy": value["post_treatment_arm_local_on_policy"],
        "pass_records": value["pass_records"],
        "first_batch_activation_certificate": value["first_batch_activation_certificate"],
        "optimizer_steps_per_arm": value["optimizer_steps_per_arm"],
        "passed": value["passed"],
    }


def _train_root(source_commit: str) -> dict[str, object]:
    seeds = source.seed_block(0, formal=False)
    torch.manual_seed(seeds["phase_A_gradient_probe"])
    models = source.make_phase_A_models(member_capacity=8, initialization_seed=seeds["initialization"])
    optimizers = source.make_phase_A_optimizers(models)
    boundary = source.phase_A_boundary_audit(models, optimizers)
    if boundary["passed"] is not True:
        raise RuntimeError("G53 phase-A boundary invalid")
    records: list[dict[str, object]] = []
    for update in range(source.PHASE_A_UPDATES):
        ids = tuple(range(update * source.NUM_ENVS, (update + 1) * source.NUM_ENVS))
        ledger = seeds["phase_A_gradient_probe"] if update == 0 else seeds["phase_A_ledger"]
        action = seeds["phase_A_gradient_probe"] if update == 0 else seeds["phase_A_action"]
        if update == 0:
            trajectory = _actor_trajectory(models[source.REFERENCE_ARM], episode_ids=ids, ledger_seed=ledger, action_seed=action)
            trajectories = {arm: trajectory for arm in source.ARMS}
        else:
            trajectories = {
                arm: _actor_trajectory(models[arm], episode_ids=ids, ledger_seed=ledger, action_seed=action)
                for arm in source.ARMS
            }
        record = source.optimize_phase_A_update(
            models, optimizers, trajectories, update_index=update,
            episode_ids={arm: ids for arm in source.ARMS},
        )
        records.append(_summarize_update(record))
    phase_B_models, phase_boundary = source.project_phase_B_models(
        models, completed_phase_A_updates=source.PHASE_A_UPDATES
    )
    del optimizers, models
    phase_B_optimizers = source.make_phase_B_optimizers(phase_B_models)
    phase_B_fresh = all(not optimizer.state for optimizer in phase_B_optimizers.values())
    for update in range(source.PHASE_B_UPDATES):
        ids = tuple(range(update * source.NUM_ENVS, (update + 1) * source.NUM_ENVS))
        ledger = seeds["phase_B_gradient_probe"] if update == 0 else seeds["phase_B_ledger"]
        action = seeds["phase_B_gradient_probe"] if update == 0 else seeds["phase_B_action"]
        trajectories = {
            arm: _actor_trajectory(phase_B_models[arm], episode_ids=ids, ledger_seed=ledger, action_seed=action)
            for arm in source.ARMS
        }
        record = source.optimize_phase_B_update(
            phase_B_models, phase_B_optimizers, trajectories, update_index=update,
            episode_ids={arm: ids for arm in source.ARMS},
        )
        records.append(_summarize_update(record))
    checkpoints = {
        arm: source.build_final_checkpoint(
            model=phase_B_models[arm], optimizer=phase_B_optimizers[arm],
            source_commit=source_commit, arm=arm,
            phase_boundary_certificate=phase_boundary[arm],
        )
        for arm in source.ARMS
    }
    first = records[0]["first_batch_activation_certificate"]
    return {
        "replicate": 0,
        "seeds": seeds,
        "phase_A_boundary": boundary,
        "phase_B_boundary": phase_boundary,
        "phase_B_fresh_empty_Adam": phase_B_fresh,
        "update_records": records,
        "first_batch_activation_certificate": first,
        "physical_collection_count": 39,
        "shared_pretreatment_batch_count": 1,
        "post_treatment_arm_local_physical_collections_per_root": 38,
        "arm_update_exposures": 40,
        "optimizer_step_count": 80,
        "checkpoints": checkpoints,
    }


def _training_worker(task: Mapping[str, object]) -> None:
    _activate_worker()
    output = Path(str(task["output_path"]))
    if output.exists():
        raise RuntimeError("G53 transient worker payload already exists")
    started = time.perf_counter()
    payload = {
        "row": _train_root(str(task["source_commit"])),
        "pid": os.getpid(),
        "wall_time_seconds": time.perf_counter() - started,
        "thread_environment": {name: os.environ.get(name) for name in _THREAD_ENV_NAMES},
        "torch_intraop_threads": torch.get_num_threads(),
        "peak_RSS_bytes": _peak_rss_bytes(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, output)


def _spawn_one(target: Any, task: Mapping[str, object]) -> None:
    context = multiprocessing.get_context("spawn")
    process = context.Process(target=target, args=(task,))
    process.start()
    process.join()
    if process.exitcode != 0:
        raise RuntimeError(f"G53 spawned worker failed with exit code {process.exitcode}")


def train(
    *, run_root: Path, source_commit: str, formal: bool = False,
    cpu_budget: int | None = None, process_workers: int | None = None,
    **formal_authority: object,
) -> dict[str, Any]:
    if formal or any(value is not None for value in formal_authority.values()):
        raise ValueError("G53 formal CLI/runtime authority fails closed")
    if not _valid_commit(source_commit):
        raise ValueError("G53 requires a lowercase 40-character integrated source commit")
    root = _fresh_root(run_root)
    config = configuration(formal=False, cpu_budget=cpu_budget, process_workers=process_workers)
    static = source.reconstruct_static_certificate()
    if not source.validate_static_certificate(static):
        raise RuntimeError("G53 static certificate invalid")
    native = _native_backend_identity()
    if native["extension_available"] is not True or native["python_fallback"] is not False:
        raise RuntimeError("G53 required native backend unavailable")
    started = time.perf_counter()
    root.mkdir(parents=True)
    (root / CHECKPOINT_DIRECTORY).mkdir()
    transient = root / TRANSIENT_DIRECTORY / "train" / "root_0.pt"
    _spawn_one(_training_worker, {"output_path": str(transient), "source_commit": source_commit})
    worker = torch.load(transient, map_location="cpu", weights_only=False)
    row = dict(worker["row"])
    checkpoints = row.pop("checkpoints")
    checkpoint_rows: dict[str, object] = {}
    for arm in source.ARMS:
        relative = f"checkpoints/{arm.lower()}_final.pt"
        path = root / relative
        torch.save(checkpoints[arm], path)
        checkpoint_rows[arm] = {"path": relative, "sha256": _digest(path)}
    row["checkpoints"] = checkpoint_rows
    row["worker"] = {
        "pid": worker["pid"], "wall_time_seconds": worker["wall_time_seconds"],
        "thread_environment": worker["thread_environment"],
        "torch_intraop_threads": worker["torch_intraop_threads"],
        "peak_RSS_bytes": worker["peak_RSS_bytes"],
        "start_method": "spawn",
    }
    transient.unlink()
    shutil.rmtree(root / TRANSIENT_DIRECTORY)
    elapsed = time.perf_counter() - started
    if elapsed > NONFORMAL_WALL_CLOCK_CAP_SECONDS:
        raise RuntimeError("G53 training exceeded the frozen wall-clock cap")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "train", "status": "COMPLETE", "formal": False,
        "source_commit": source_commit,
        "configuration": config,
        "source_controls": source_controls(),
        "static_certificate": static,
        "native_backend": native,
        "replicate_results": [row],
        "transient_worker_payloads_removed": True,
        "stage_wall_time_seconds": elapsed,
    }
    _write_json(root / TRAIN_MANIFEST, manifest)
    return manifest


def _checkpoint_path(training: Mapping[str, Any], arm: str) -> str:
    return str(training["replicate_results"][0]["checkpoints"][arm]["path"])


_UPDATE_KEYS = {
    "phase", "update_index", "shared_pretreatment_physical_collection_count",
    "arm_exposures", "paired_episode_IDs", "post_treatment_arm_local_on_policy",
    "pass_records", "first_batch_activation_certificate", "optimizer_steps_per_arm",
    "passed",
}
_PASS_KEYS = {
    "pass_index", "plans_prepared_before_either_step",
    "reverse_preparation_preserved_model_optimizer_gradient_and_RNG",
    "coefficient_read_audit", "coefficient_call_count_per_arm", "coefficient_hex",
    "raw_entropy_gradient_digest", "scaled_entropy_gradient_digest",
    "normalization_rows", "physical_normalization_instances",
    "normalization_exposures", "optimizer_steps_per_arm",
}
_ACTIVATION_KEYS = {
    "same_stored_trajectory_object", "model_mask_RNG_actor_metadata_Adam_equal",
    "stored_trajectory_digest",
    "replay_old_logprob_target_centered_normalized_policy_gradient_equal",
    "raw_entropy_scalar_equal_finite", "raw_entropy_gradient_equal_finite",
    "raw_entropy_gradient_support", "null_scaled_gradient_finite_bytewise_zero",
    "reference_scaled_gradient_support", "reference_scaled_gradient_positive_norm",
    "coefficient_is_sole_graph_delta", "post_step_actor_or_Adam_state_differs",
    "activation",
}


def _hex_digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _strict_activation(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != _ACTIVATION_KEYS:
        return False
    trajectory = value.get("stored_trajectory_digest")
    activation = value.get("activation")
    if not isinstance(trajectory, Mapping) or set(trajectory) != {
        "observations", "active_mask", "rewards", "hidden_before",
        "terminal_hidden_reset_mask", "pre_tanh_actions", "actions", "old_log_probs",
    } or not all(_hex_digest(row) for row in trajectory.values()):
        return False
    if not isinstance(activation, Mapping) or set(activation) != {
        "reference_scaled_entropy_gradient_norm64", "null_scaled_entropy_gradient_norm64",
        "difference_norm64", "q_H", "active_iff_q_H_gt_0",
    }:
        return False
    numeric = [activation[name] for name in (
        "reference_scaled_entropy_gradient_norm64", "null_scaled_entropy_gradient_norm64",
        "difference_norm64", "q_H",
    )]
    return bool(
        all(isinstance(row, (int, float)) and not isinstance(row, bool) and np.isfinite(row) for row in numeric)
        and float(activation["reference_scaled_entropy_gradient_norm64"]) > 0.0
        and float(activation["null_scaled_entropy_gradient_norm64"]) == 0.0
        and float(activation["difference_norm64"]) > 0.0
        and float(activation["q_H"]) > 0.0
        and activation.get("active_iff_q_H_gt_0") is True
        and value.get("raw_entropy_gradient_support") == ["policy.log_std"]
        and value.get("reference_scaled_gradient_support") == ["policy.log_std"]
        and all(value.get(name) is True for name in (
            "same_stored_trajectory_object", "model_mask_RNG_actor_metadata_Adam_equal",
            "replay_old_logprob_target_centered_normalized_policy_gradient_equal",
            "raw_entropy_scalar_equal_finite", "raw_entropy_gradient_equal_finite",
            "null_scaled_gradient_finite_bytewise_zero",
            "reference_scaled_gradient_positive_norm", "coefficient_is_sole_graph_delta",
            "post_step_actor_or_Adam_state_differs",
        ))
    )


def _strict_update_record(value: object, *, ordinal: int) -> bool:
    if not isinstance(value, Mapping) or set(value) != _UPDATE_KEYS:
        return False
    phase = "A" if ordinal < 10 else "B"
    update_index = ordinal if ordinal < 10 else ordinal - 10
    shared = ordinal == 0
    records = value.get("pass_records")
    if not isinstance(records, list) or len(records) != 2:
        return False
    for pass_index, record in enumerate(records):
        if not isinstance(record, Mapping) or set(record) != _PASS_KEYS:
            return False
        expected_audit = [[phase, arm] for arm in source.ARMS]
        expected_hex = {
            arm: source.ENTROPY_COEFFICIENTS[arm].hex() for arm in source.ARMS
        }
        if not (
            record.get("pass_index") == pass_index
            and record.get("plans_prepared_before_either_step") is True
            and record.get("reverse_preparation_preserved_model_optimizer_gradient_and_RNG") is True
            and record.get("coefficient_read_audit") == expected_audit
            and record.get("coefficient_call_count_per_arm") == {arm: 1 for arm in source.ARMS}
            and record.get("coefficient_hex") == expected_hex
            and isinstance(record.get("raw_entropy_gradient_digest"), Mapping)
            and tuple(record["raw_entropy_gradient_digest"]) == source.ARMS
            and all(_hex_digest(record["raw_entropy_gradient_digest"][arm]) for arm in source.ARMS)
            and isinstance(record.get("scaled_entropy_gradient_digest"), Mapping)
            and tuple(record["scaled_entropy_gradient_digest"]) == source.ARMS
            and all(_hex_digest(record["scaled_entropy_gradient_digest"][arm]) for arm in source.ARMS)
            and record.get("normalization_rows") == 384
            and record.get("physical_normalization_instances") == (1 if shared else 2)
            and record.get("normalization_exposures") == 2
            and record.get("optimizer_steps_per_arm") == 1
        ):
            return False
    return bool(
        value.get("phase") == phase
        and value.get("update_index") == update_index
        and value.get("shared_pretreatment_physical_collection_count") == (1 if shared else 0)
        and value.get("arm_exposures") == 2
        and value.get("paired_episode_IDs") is True
        and value.get("post_treatment_arm_local_on_policy") is (not shared)
        and value.get("first_batch_activation_certificate")
        == (value.get("first_batch_activation_certificate") if shared else None)
        and (_strict_activation(value.get("first_batch_activation_certificate")) if shared else value.get("first_batch_activation_certificate") is None)
        and value.get("optimizer_steps_per_arm") == 2
        and value.get("passed") is True
    )


def _strict_phase_boundaries(row: Mapping[str, object]) -> bool:
    phase_A = row.get("phase_A_boundary")
    phase_B = row.get("phase_B_boundary")
    if not isinstance(phase_A, Mapping) or set(phase_A) != {
        "fresh_G50_null_source_count", "G51_NoBaselinePhaseAProjection_count",
        "G51_make_phase_A_models_call_count", "baseline_free_before_trajectory_or_optimizer",
        "model_state_bytes_equal", "actor_parameter_names", "actor_parameter_order_equal",
        "optimizer_parameter_order_equal", "Adam_states_empty",
        "slow_critic_state_bytes_equal_and_unexposed", "shared_storage_count",
        "projection_RNG_consumption", "G52_CARRY_state_count", "passed",
    }:
        return False
    if not (
        phase_A.get("fresh_G50_null_source_count") == 1
        and phase_A.get("G51_NoBaselinePhaseAProjection_count") == 1
        and phase_A.get("G51_make_phase_A_models_call_count") == 0
        and phase_A.get("shared_storage_count") == 0
        and phase_A.get("projection_RNG_consumption") == 0
        and phase_A.get("G52_CARRY_state_count") == 0
        and len(phase_A.get("actor_parameter_names", [])) == 17
        and all(phase_A.get(name) is True for name in (
            "baseline_free_before_trajectory_or_optimizer", "model_state_bytes_equal",
            "actor_parameter_order_equal", "optimizer_parameter_order_equal",
            "Adam_states_empty", "slow_critic_state_bytes_equal_and_unexposed", "passed",
        ))
    ):
        return False
    if not isinstance(phase_B, Mapping) or tuple(phase_B) != source.ARMS:
        return False
    for arm in source.ARMS:
        boundary = phase_B[arm]
        if not isinstance(boundary, Mapping) or set(boundary) != {
            "completed_phase_A_updates", "retained_actor_and_log_std_bytes_equal",
            "slow_critic_deleted_at_common_boundary", "baseline_absent",
            "forbidden_state_keys", "phase_A_optimizer_disposed",
            "projection_optimizer_steps", "projection_RNG_consumption", "passed",
        } or not (
            boundary.get("completed_phase_A_updates") == 10
            and boundary.get("forbidden_state_keys") == []
            and boundary.get("projection_optimizer_steps") == 0
            and boundary.get("projection_RNG_consumption") == 0
            and all(boundary.get(name) is True for name in (
                "retained_actor_and_log_std_bytes_equal",
                "slow_critic_deleted_at_common_boundary", "baseline_absent",
                "phase_A_optimizer_disposed", "passed",
            ))
        ):
            return False
    return True


def _strict_training_row(row: object) -> bool:
    if not isinstance(row, Mapping) or set(row) != {
        "replicate", "seeds", "phase_A_boundary", "phase_B_boundary",
        "phase_B_fresh_empty_Adam", "update_records",
        "first_batch_activation_certificate", "physical_collection_count",
        "shared_pretreatment_batch_count",
        "post_treatment_arm_local_physical_collections_per_root",
        "arm_update_exposures", "optimizer_step_count", "checkpoints", "worker",
    }:
        return False
    updates = row.get("update_records")
    return bool(
        row.get("replicate") == 0
        and row.get("seeds") == source.seed_block(0, formal=False)
        and _strict_phase_boundaries(row)
        and row.get("phase_B_fresh_empty_Adam") is True
        and isinstance(updates, list) and len(updates) == 20
        and all(_strict_update_record(update, ordinal=index) for index, update in enumerate(updates))
        and row.get("first_batch_activation_certificate") == updates[0].get("first_batch_activation_certificate")
        and _strict_activation(row.get("first_batch_activation_certificate"))
        and row.get("physical_collection_count") == 39
        and row.get("shared_pretreatment_batch_count") == 1
        and row.get("post_treatment_arm_local_physical_collections_per_root") == 38
        and row.get("arm_update_exposures") == 40
        and row.get("optimizer_step_count") == 80
    )


def validate_training_artifacts(run_root: Path) -> dict[str, object]:
    errors: list[str] = []
    try:
        training = _read_json(Path(run_root) / TRAIN_MANIFEST)
        expected = configuration(formal=False, cpu_budget=2, process_workers=2)
        if set(training) != {
            "schema_version", "algorithm_id", "source_id", "stage", "status", "formal",
            "source_commit", "configuration", "source_controls", "static_certificate",
            "native_backend", "replicate_results", "transient_worker_payloads_removed",
            "stage_wall_time_seconds",
        }:
            errors.append("train_schema")
        if training.get("configuration") != expected or training.get("source_controls") != source_controls():
            errors.append("train_configuration")
        if (
            training.get("schema_version") != SCHEMA_VERSION
            or training.get("algorithm_id") != ALGORITHM_ID
            or training.get("source_id") != source.SOURCE_ID
            or training.get("stage") != "train"
            or training.get("status") != "COMPLETE"
            or training.get("formal") is not False
            or not _valid_commit(training.get("source_commit"))
            or training.get("transient_worker_payloads_removed") is not True
        ):
            errors.append("train_identity")
        if not source.validate_static_certificate(training.get("static_certificate")):
            errors.append("static_certificate")
        native = training.get("native_backend")
        if not (
            isinstance(native, Mapping)
            and set(native) == {
                "name", "python_fallback", "extension_available", "module", "build_identity"
            }
            and native.get("name") == "ContinuousRosterToyBatch_CPU_CPP_required"
            and native.get("python_fallback") is False
            and native.get("extension_available") is True
            and isinstance(native.get("module"), str) and bool(native["module"])
            and isinstance(native.get("build_identity"), str)
            and re.fullmatch(r"[0-9a-f]{20}", native["build_identity"]) is not None
        ):
            errors.append("native_backend")
        if not (
            isinstance(training.get("stage_wall_time_seconds"), (int, float))
            and not isinstance(training.get("stage_wall_time_seconds"), bool)
            and np.isfinite(training["stage_wall_time_seconds"])
            and 0.0 <= training["stage_wall_time_seconds"] <= NONFORMAL_WALL_CLOCK_CAP_SECONDS
        ):
            errors.append("training_wall_time")
        rows = training.get("replicate_results")
        if not isinstance(rows, list) or len(rows) != 1:
            errors.append("root_inventory")
        else:
            row = rows[0]
            if not _strict_training_row(row):
                errors.append("nested_training_evidence")
            worker = row.get("worker")
            if (
                not isinstance(worker, Mapping)
                or set(worker) != {
                    "pid", "wall_time_seconds", "thread_environment",
                    "torch_intraop_threads", "peak_RSS_bytes", "start_method",
                }
                or not isinstance(worker.get("pid"), int)
                or not isinstance(worker.get("wall_time_seconds"), (int, float))
                or not np.isfinite(worker["wall_time_seconds"])
                or worker["wall_time_seconds"] < 0.0
                or worker.get("start_method") != "spawn"
                or worker.get("thread_environment") != WORKER_THREAD_ENV
                or worker.get("torch_intraop_threads") != 1
                or not isinstance(worker.get("peak_RSS_bytes"), int)
                or worker["peak_RSS_bytes"] > MAX_AGGREGATE_RSS_BYTES
            ): errors.append("training_worker_resources")
            checkpoints = row.get("checkpoints")
            if not isinstance(checkpoints, Mapping) or tuple(checkpoints) != source.ARMS:
                errors.append("checkpoint_inventory")
                checkpoints = {}
            for arm in source.ARMS:
                record = checkpoints.get(arm)
                if not isinstance(record, Mapping) or set(record) != {"path", "sha256"}:
                    errors.append(f"checkpoint_record:{arm}")
                    continue
                relative = f"checkpoints/{arm.lower()}_final.pt"
                path = Path(run_root) / relative
                if record.get("sha256") != _digest(path):
                    errors.append(f"checkpoint_digest:{arm}")
                    continue
                if record.get("path") != relative:
                    errors.append(f"checkpoint_path:{arm}")
                payload = torch.load(path, map_location="cpu", weights_only=False)
                if (
                    not source.validate_final_checkpoint(payload)
                    or payload.get("arm") != arm
                    or payload.get("source_commit") != training.get("source_commit")
                    or payload.get("phase_boundary_certificate")
                    != row["phase_B_boundary"][arm]
                ):
                    errors.append(f"checkpoint_schema:{arm}")
        observed = {str(path.relative_to(run_root)).replace("\\", "/") for path in (Path(run_root) / CHECKPOINT_DIRECTORY).glob("*.pt")}
        expected_files = {_checkpoint_path(training, arm) for arm in source.ARMS}
        if observed != expected_files or (Path(run_root) / TRANSIENT_DIRECTORY).exists():
            errors.append("artifact_inventory")
    except (AttributeError, EOFError, FileNotFoundError, KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        errors.append(type(error).__name__)
    return {"valid": not errors, "errors": errors}


class _EvaluationPolicy:
    def __init__(self, model: source.G53PhaseBModel) -> None:
        self.model = model
    @property
    def member_capacity(self) -> int:
        return self.model.member_capacity
    @property
    def hidden_dim(self) -> int:
        return self.model.hidden_dim
    def eval(self) -> "_EvaluationPolicy":
        self.model.eval(); return self
    def forward_step(self, **arguments: Any) -> Any:
        arguments.pop("critic_state", None)
        return source.g47._actor_only_step(self.model, **arguments)


def _processes(*, capacity: int, count: int, seeds: Mapping[str, int]) -> tuple[g34.RandomProcessLedger, ...]:
    times = source.g40.g35._time_assignments(capacity=capacity, process_seed=seeds["evaluation_process"])
    orders = source.g40.g39._balanced_64_assignments(
        g34.EVENT_ORDERS, replicate=0, capacity=capacity,
        process_seed=seeds["evaluation_process"], stream=1,
    )
    if capacity == 6:
        profiles = (roster_env.SMALL_CAPACITY_6,) * 64
    elif capacity == 12:
        profiles = (roster_env.LARGE_CAPACITY_12,) * 64
    else:
        profiles = source.g40.g39._balanced_64_assignments(
            roster_env.TRAIN_PROFILES, replicate=0, capacity=capacity,
            process_seed=seeds["evaluation_process"], stream=2,
        )
    output = []
    for episode in range(count):
        base = roster_env.make_ledger(
            g34.episode_address(capacity, episode), master_seed=seeds["evaluation_ledger"],
            profile=profiles[episode],
        )
        expected, trajectory = g34._expected_roster_schedule(base, times[episode], orders[episode])
        row = g34.RandomProcessLedger(
            base=base, local_episode_id=episode, event_times=times[episode],
            event_order=orders[episode], expected_roster_sizes=expected,
            count_trajectory=trajectory,
        )
        row.validate(); output.append(row)
    return tuple(output)


def _evaluate_task(task: Mapping[str, object]) -> None:
    _activate_worker()
    checkpoint = torch.load(Path(str(task["checkpoint"])), map_location="cpu", weights_only=False)
    model = source.load_final_checkpoint_model(checkpoint, member_capacity=int(task["capacity"]))
    processes = _processes(
        capacity=int(task["capacity"]), count=source.EVALUATION_EPISODES_PER_CELL,
        seeds=dict(task["seeds"]),  # type: ignore[arg-type]
    )
    cell = str(task["cell"])
    process_kind = "fixed" if "fixed" in cell else "random"
    deterministic = cell.endswith("deterministic")
    episodes, lifecycle = source.g40.evaluate_model(
        _EvaluationPolicy(model), processes=processes,
        action_seed=int(task["action_seed"]), process_kind=process_kind,
        deterministic=deterministic,
    )
    payload = {
        "index": int(task["index"]), "arm": task["arm"], "capacity": int(task["capacity"]),
        "cell": cell, "process": process_kind, "deterministic": deterministic,
        "process_schedule_source": (
            "base.fixed_expected_roster_sizes"
            if process_kind == "fixed"
            else "G34.random_expected_roster_sizes"
        ),
        "lifecycle_valid": lifecycle, "optimizer_steps": 0,
        "baseline_actor_read_count": 0, "coefficient_read_count": 0,
        "episodes": list(episodes), "worker_pid": os.getpid(),
        "thread_environment": {name: os.environ.get(name) for name in _THREAD_ENV_NAMES},
        "torch_intraop_threads": torch.get_num_threads(),
        "peak_RSS_bytes": _peak_rss_bytes(),
    }
    path = Path(str(task["output_path"])); path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)


def evaluate(
    *, run_root: Path, cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    root = Path(run_root).resolve()
    validation = validate_training_artifacts(root)
    if validation["valid"] is not True:
        raise ValueError("G53 training artifact invalid: " + "|".join(validation["errors"]))
    training = _read_json(root / TRAIN_MANIFEST)
    config = configuration(formal=False, cpu_budget=cpu_budget, process_workers=process_workers)
    if config != training["configuration"]:
        raise ValueError("G53 evaluation configuration differs from training")
    started = time.perf_counter()
    seeds = source.seed_block(0, formal=False)
    tasks = []
    index = 0
    for arm in source.ARMS:
        for capacity in source.EVALUATION_CAPACITIES:
            for cell_index, cell in enumerate(MODEL_CELLS):
                tasks.append({
                    "index": index, "arm": arm, "capacity": capacity, "cell": cell,
                    "checkpoint": str(root / _checkpoint_path(training, arm)),
                    "seeds": seeds,
                    "action_seed": seeds["evaluation_action"] + cell_index,
                    "output_path": str(root / TRANSIENT_DIRECTORY / "evaluate" / f"cell_{index}.pt"),
                }); index += 1
    # Bounded two-process spawned execution, deterministically merged by index.
    context = multiprocessing.get_context("spawn")
    active: list[multiprocessing.Process] = []
    for task in tasks:
        process = context.Process(target=_evaluate_task, args=(task,)); process.start(); active.append(process)
        if len(active) == 2:
            for row in active:
                row.join()
                if row.exitcode != 0: raise RuntimeError("G53 evaluation worker failed")
            active = []
    for row in active:
        row.join()
        if row.exitcode != 0: raise RuntimeError("G53 evaluation worker failed")
    cells = []
    worker_pids = set()
    for task in tasks:
        path = Path(str(task["output_path"])); payload = torch.load(path, map_location="cpu", weights_only=False)
        cells.append(payload)
        worker_pids.add(payload["worker_pid"]); path.unlink()
    shutil.rmtree(root / TRANSIENT_DIRECTORY)
    elapsed = time.perf_counter() - started
    if float(training["stage_wall_time_seconds"]) + elapsed > NONFORMAL_WALL_CLOCK_CAP_SECONDS:
        raise RuntimeError("G53 train+evaluate exceeded the frozen wall-clock cap")
    manifest = {
        "schema_version": SCHEMA_VERSION, "algorithm_id": ALGORITHM_ID,
        "source_id": source.SOURCE_ID, "stage": "evaluate", "status": "COMPLETE",
        "formal": False, "source_commit": training["source_commit"],
        "configuration": config, "training_manifest_sha256": _digest(root / TRAIN_MANIFEST),
        "cells": cells, "evaluation_transition_count": source.EVALUATION_TRANSITIONS,
        "optimizer_steps": 0, "distinct_worker_pid_count": len(worker_pids),
        "transient_worker_payloads_removed": True,
        "stage_wall_time_seconds": elapsed,
    }
    _write_json(root / EVALUATION_MANIFEST, manifest)
    return manifest


def validate_evaluation_artifacts(run_root: Path) -> dict[str, object]:
    errors = list(validate_training_artifacts(run_root)["errors"])
    try:
        root = Path(run_root); training = _read_json(root / TRAIN_MANIFEST); evaluation = _read_json(root / EVALUATION_MANIFEST)
        if set(evaluation) != {
            "schema_version", "algorithm_id", "source_id", "stage", "status", "formal",
            "source_commit", "configuration", "training_manifest_sha256", "cells",
            "evaluation_transition_count", "optimizer_steps", "distinct_worker_pid_count",
            "transient_worker_payloads_removed", "stage_wall_time_seconds",
        }:
            errors.append("evaluation_schema")
        if evaluation.get("training_manifest_sha256") != _digest(root / TRAIN_MANIFEST): errors.append("train_digest")
        if (
            evaluation.get("schema_version") != SCHEMA_VERSION
            or evaluation.get("algorithm_id") != ALGORITHM_ID
            or evaluation.get("source_id") != source.SOURCE_ID
            or evaluation.get("stage") != "evaluate"
            or evaluation.get("status") != "COMPLETE"
            or evaluation.get("formal") is not False
            or evaluation.get("source_commit") != training.get("source_commit")
            or evaluation.get("configuration") != training.get("configuration")
            or evaluation.get("transient_worker_payloads_removed") is not True
        ): errors.append("evaluation_identity")
        cells = evaluation.get("cells")
        expected_cells = [
            (index, arm, capacity, cell)
            for index, (arm, capacity, cell) in enumerate(
                (arm, capacity, cell)
                for arm in source.ARMS
                for capacity in source.EVALUATION_CAPACITIES
                for cell in MODEL_CELLS
            )
        ]
        cell_keys = {
            "index", "arm", "capacity", "cell", "process", "deterministic",
            "process_schedule_source", "lifecycle_valid", "optimizer_steps",
            "baseline_actor_read_count", "coefficient_read_count", "episodes",
            "worker_pid", "thread_environment", "torch_intraop_threads", "peak_RSS_bytes",
        }
        episode_keys = {
            "local_episode_id", "episode_id", "profile", "event_times", "event_order",
            "count_trajectory", "signature", "utility", "minimum_step_utility",
            "minimum_event_window_utility", "minimum_process_segment_utility",
            "event_window_utility", "process_segment_utility", "reward_trace",
            "roster_size_trace", "roster_sizes_valid",
        }
        if not isinstance(cells, list) or len(cells) != 24:
            errors.append("cell_inventory")
        else:
            for row, (index, arm, capacity, cell) in zip(cells, expected_cells):
                process = "fixed" if "fixed" in cell else "random"
                deterministic = cell.endswith("deterministic")
                expected_schedule = (
                    "base.fixed_expected_roster_sizes"
                    if process == "fixed" else "G34.random_expected_roster_sizes"
                )
                episodes = row.get("episodes") if isinstance(row, Mapping) else None
                episode_valid = bool(
                    isinstance(episodes, list) and len(episodes) == 6
                    and all(
                        isinstance(episode, Mapping)
                        and set(episode) == episode_keys
                        and episode.get("local_episode_id") == local_episode
                        and episode.get("episode_id") == g34.episode_address(capacity, local_episode)
                        and isinstance(episode.get("profile"), str)
                        and isinstance(episode.get("event_times"), list)
                        and len(episode["event_times"]) == 4
                        and all(isinstance(value, int) for value in episode["event_times"])
                        and isinstance(episode.get("event_order"), list)
                        and tuple(episode["event_order"]) in g34.EVENT_ORDERS
                        and isinstance(episode.get("count_trajectory"), list)
                        and len(episode["count_trajectory"]) == 48
                        and all(isinstance(value, int) and value > 0 for value in episode["count_trajectory"])
                        and isinstance(episode.get("event_window_utility"), Mapping)
                        and set(episode["event_window_utility"]) == set(episode["event_order"])
                        and all(np.isfinite(value) for value in episode["event_window_utility"].values())
                        and isinstance(episode.get("process_segment_utility"), list)
                        and len(episode["process_segment_utility"]) == 5
                        and all(np.isfinite(value) for value in episode["process_segment_utility"])
                        and isinstance(episode.get("reward_trace"), list)
                        and len(episode["reward_trace"]) == 48
                        and all(np.isfinite(value) for value in episode["reward_trace"])
                        and isinstance(episode.get("roster_size_trace"), list)
                        and len(episode["roster_size_trace"]) == 48
                        and all(isinstance(value, int) and value > 0 for value in episode["roster_size_trace"])
                        and episode.get("roster_sizes_valid") is True
                        and all(
                            isinstance(episode.get(name), (int, float))
                            and not isinstance(episode.get(name), bool)
                            and np.isfinite(episode[name])
                            for name in (
                                "utility", "minimum_step_utility",
                                "minimum_event_window_utility",
                                "minimum_process_segment_utility",
                            )
                        )
                        for local_episode, episode in enumerate(episodes)
                    )
                )
                if not (
                    isinstance(row, Mapping) and set(row) == cell_keys
                    and (row.get("index"), row.get("arm"), row.get("capacity"), row.get("cell"))
                    == (index, arm, capacity, cell)
                    and row.get("process") == process
                    and row.get("deterministic") is deterministic
                    and row.get("process_schedule_source") == expected_schedule
                    and row.get("lifecycle_valid") is True
                    and row.get("optimizer_steps") == 0
                    and row.get("baseline_actor_read_count") == 0
                    and row.get("coefficient_read_count") == 0
                    and episode_valid
                    and isinstance(row.get("worker_pid"), int)
                    and row.get("thread_environment") == WORKER_THREAD_ENV
                    and row.get("torch_intraop_threads") == 1
                    and isinstance(row.get("peak_RSS_bytes"), int)
                    and 0 < row["peak_RSS_bytes"] <= MAX_AGGREGATE_RSS_BYTES
                ):
                    errors.append(f"cell_contract:{index}")
            if any(
                sum(int(row["peak_RSS_bytes"]) for row in cells[start:start + 2])
                > MAX_AGGREGATE_RSS_BYTES
                for start in range(0, len(cells), 2)
            ):
                errors.append("aggregate_RSS")
            pids = {row["worker_pid"] for row in cells if isinstance(row, Mapping) and isinstance(row.get("worker_pid"), int)}
            if evaluation.get("distinct_worker_pid_count") != len(pids) or not 1 <= len(pids) <= 24:
                errors.append("worker_pid_inventory")
        if evaluation.get("evaluation_transition_count") != 6912 or evaluation.get("optimizer_steps") != 0: errors.append("evaluation_counts")
        if not (
            isinstance(evaluation.get("stage_wall_time_seconds"), (int, float))
            and not isinstance(evaluation.get("stage_wall_time_seconds"), bool)
            and np.isfinite(evaluation["stage_wall_time_seconds"])
            and 0.0 <= evaluation["stage_wall_time_seconds"]
            and float(training.get("stage_wall_time_seconds", float("inf")))
            + float(evaluation["stage_wall_time_seconds"])
            <= NONFORMAL_WALL_CLOCK_CAP_SECONDS
            and not (root / TRANSIENT_DIRECTORY).exists()
        ):
            errors.append("evaluation_resources")
    except (AttributeError, EOFError, FileNotFoundError, KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        errors.append(type(error).__name__)
    return {"valid": not errors, "errors": errors}


def _episode_metric(episode: Mapping[str, object], name: str) -> float:
    value = episode.get(name)
    if isinstance(value, (int, float)) and np.isfinite(value): return float(value)
    raise ValueError(f"G53 episode metric unavailable: {name}")


def _primary_values(evaluation: Mapping[str, Any], arm: str) -> np.ndarray:
    values = []
    for capacity in source.EVALUATION_CAPACITIES:
        row = next(
            item for item in evaluation["cells"]
            if item["arm"] == arm and item["capacity"] == capacity
            and item["cell"] == "final_random_deterministic"
        )
        values.append([_episode_metric(episode, "utility") for episode in row["episodes"]])
    return np.asarray(values, dtype=np.float64)


def select_result_branch(metrics: Mapping[str, object]) -> str:
    return NONFORMAL_BRANCH if all(
        metrics.get(name) is True for name in (
            "operational_valid", "source_valid", "pairing_valid",
            "G52_isolation_valid", "activation_valid", "exact_completion",
        )
    ) else INVALID_BRANCH


def _expected_analysis_metrics(
    training: Mapping[str, Any], evaluation: Mapping[str, Any], *, operational_valid: bool
) -> dict[str, object]:
    rows = training.get("replicate_results")
    nested_valid = bool(
        isinstance(rows, list) and len(rows) == 1 and _strict_training_row(rows[0])
    )
    controls = training.get("source_controls")
    static = training.get("static_certificate")
    controls = controls if isinstance(controls, Mapping) else {}
    static = static if isinstance(static, Mapping) else {}
    metrics: dict[str, object] = {
        "operational_valid": operational_valid,
        "source_valid": bool(
            evaluation.get("evaluation_transition_count") == 6912
            and evaluation.get("optimizer_steps") == 0
        ),
        "pairing_valid": nested_valid,
        "G52_isolation_valid": bool(
            controls.get("G52_dependency_state_artifact_result_count") == 0
            and static.get("G52_import_or_carry_count") == 0
        ),
        "activation_valid": bool(
            nested_valid and _strict_activation(rows[0].get("first_batch_activation_certificate"))
        ),
        "exact_completion": bool(
            nested_valid
            and rows[0].get("optimizer_step_count") == 80
            and evaluation.get("evaluation_transition_count") == 6912
        ),
    }
    if operational_valid:
        ref = _primary_values(evaluation, source.REFERENCE_ARM)
        null = _primary_values(evaluation, source.NULL_ARM)
        delta = float(ref.mean() - null.mean())
        rng = np.random.default_rng(source.bootstrap_seed(formal=False))
        samples = np.empty(source.BOOTSTRAP_RESAMPLES, dtype=np.float64)
        for index in range(source.BOOTSTRAP_RESAMPLES):
            draw = rng.integers(0, ref.size, size=ref.size)
            samples[index] = float((ref.ravel()[draw] - null.ravel()[draw]).mean())
        metrics.update({
            "Delta_entropy": delta,
            "Delta_entropy_ci95": [
                float(np.quantile(samples, 0.025)), float(np.median(samples)),
                float(np.quantile(samples, 0.975)),
            ],
            "positive_direction_favors_common_entropy": True,
            "conditional_single_root_only": True,
        })
    return metrics


def analyze(
    *, run_root: Path, require_formal: bool = False,
    cpu_budget: int | None = None, process_workers: int | None = None,
) -> dict[str, Any]:
    if require_formal:
        raise ValueError("G53 formal analysis is not authorized")
    root = Path(run_root).resolve(); started = time.perf_counter()
    validation = validate_evaluation_artifacts(root)
    training = _read_json(root / TRAIN_MANIFEST); evaluation = _read_json(root / EVALUATION_MANIFEST)
    if configuration(formal=False, cpu_budget=cpu_budget, process_workers=process_workers) != training["configuration"]:
        raise ValueError("G53 analyze configuration differs from training")
    metrics = _expected_analysis_metrics(
        training, evaluation, operational_valid=bool(validation["valid"])
    )
    branch = select_result_branch(metrics)
    elapsed = time.perf_counter() - started
    cumulative = (
        float(training["stage_wall_time_seconds"])
        + float(evaluation["stage_wall_time_seconds"])
        + elapsed
    )
    if cumulative > NONFORMAL_WALL_CLOCK_CAP_SECONDS:
        raise RuntimeError("G53 exercise exceeded the frozen wall-clock cap")
    result = {
        "schema_version": SCHEMA_VERSION, "algorithm_id": ALGORITHM_ID,
        "source_id": source.SOURCE_ID, "stage": "analyze", "status": "COMPLETE",
        "formal": False, "source_commit": training["source_commit"],
        "configuration": training["configuration"],
        "train_manifest_sha256": _digest(root / TRAIN_MANIFEST),
        "evaluation_manifest_sha256": _digest(root / EVALUATION_MANIFEST),
        "metrics": metrics, "validation_errors": validation["errors"],
        "result_branch": branch,
        "scientific_branch_selected": False,
        "terminal_for_registered_treatment_if_formal": False,
        "arm_ranking_authorized": False,
        "retry_rescue_authorized": False,
        "future_claim_branches_selected": [],
        "claim_ceiling": "one_root_conditional_nonformal_exercise_only",
        "stage_wall_time_seconds": elapsed,
        "cumulative_wall_time_seconds": cumulative,
    }
    _write_json(root / ANALYSIS_RESULT, result)
    return result


def validate_analysis_artifacts(run_root: Path) -> dict[str, object]:
    evaluation_validation = validate_evaluation_artifacts(run_root)
    errors = list(evaluation_validation["errors"])
    try:
        root = Path(run_root); result = _read_json(root / ANALYSIS_RESULT)
        if set(result) != {
            "schema_version", "algorithm_id", "source_id", "stage", "status", "formal",
            "source_commit", "configuration", "train_manifest_sha256",
            "evaluation_manifest_sha256", "metrics", "validation_errors", "result_branch",
            "scientific_branch_selected", "terminal_for_registered_treatment_if_formal",
            "arm_ranking_authorized", "retry_rescue_authorized", "future_claim_branches_selected",
            "claim_ceiling", "stage_wall_time_seconds",
            "cumulative_wall_time_seconds",
        }: errors.append("analysis_schema")
        if result.get("train_manifest_sha256") != _digest(root / TRAIN_MANIFEST) or result.get("evaluation_manifest_sha256") != _digest(root / EVALUATION_MANIFEST): errors.append("analysis_digest")
        training = _read_json(root / TRAIN_MANIFEST)
        evaluation = _read_json(root / EVALUATION_MANIFEST)
        if (
            result.get("schema_version") != SCHEMA_VERSION
            or result.get("algorithm_id") != ALGORITHM_ID
            or result.get("source_id") != source.SOURCE_ID
            or result.get("stage") != "analyze"
            or result.get("status") != "COMPLETE"
            or result.get("formal") is not False
            or result.get("source_commit") != training.get("source_commit")
            or result.get("configuration") != training.get("configuration")
        ): errors.append("analysis_identity")
        expected_metrics = _expected_analysis_metrics(
            training, evaluation,
            operational_valid=bool(evaluation_validation["valid"]),
        )
        if result.get("metrics") != expected_metrics:
            errors.append("analysis_metrics")
        if result.get("validation_errors") != evaluation_validation["errors"]:
            errors.append("analysis_validation_errors")
        if result.get("result_branch") != select_result_branch(expected_metrics):
            errors.append("branch")
        if not (
            result.get("scientific_branch_selected") is False
            and result.get("terminal_for_registered_treatment_if_formal") is False
            and result.get("arm_ranking_authorized") is False
            and result.get("retry_rescue_authorized") is False
            and result.get("future_claim_branches_selected") == []
            and result.get("claim_ceiling") == "one_root_conditional_nonformal_exercise_only"
            and isinstance(result.get("stage_wall_time_seconds"), (int, float))
            and np.isfinite(result["stage_wall_time_seconds"])
            and result["stage_wall_time_seconds"] >= 0.0
            and isinstance(result.get("cumulative_wall_time_seconds"), (int, float))
            and np.isfinite(result["cumulative_wall_time_seconds"])
            and result["cumulative_wall_time_seconds"]
            == float(training["stage_wall_time_seconds"])
            + float(evaluation["stage_wall_time_seconds"])
            + float(result["stage_wall_time_seconds"])
            and result["cumulative_wall_time_seconds"] <= NONFORMAL_WALL_CLOCK_CAP_SECONDS
        ):
            errors.append("claim_ceiling")
    except (AttributeError, EOFError, FileNotFoundError, KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        errors.append(type(error).__name__)
    return {"valid": not errors, "errors": errors}


def reload_artifacts(run_root: Path) -> dict[str, object]:
    return {
        "train": validate_training_artifacts(run_root),
        "evaluate": validate_evaluation_artifacts(run_root),
        "analyze": validate_analysis_artifacts(run_root),
    }


def readiness_interface_smoke(*, source_commit: str) -> dict[str, object]:
    if not _valid_commit(source_commit): raise ValueError("G53 readiness requires source commit identity")
    static = source.reconstruct_static_certificate()
    return {
        "phase": "readiness-smoke", "source_commit": source_commit,
        "static_certificate": static,
        "formal_CLI_fail_closed": True,
        "scientific_roots": 0, "scientific_transitions": 0,
        "optimizer_steps": 0, "bootstrap_resamples": 0,
        "initializes_nonformal": False,
        "passed": source.validate_static_certificate(static),
    }


_READINESS_TRAIN_KEYS = {
    "schema_version", "algorithm_id", "source_id", "phase", "source_commit",
    "formal", "static_certificate", "formal_CLI_fail_closed",
    "scientific_roots", "scientific_transitions", "optimizer_steps",
    "bootstrap_resamples", "initializes_nonformal", "proof_only", "passed",
}


def _strict_readiness_train(value: object) -> bool:
    return bool(
        isinstance(value, Mapping) and set(value) == _READINESS_TRAIN_KEYS
        and value.get("schema_version") == SCHEMA_VERSION
        and value.get("algorithm_id") == ALGORITHM_ID
        and value.get("source_id") == source.SOURCE_ID
        and value.get("phase") == "readiness-train"
        and _valid_commit(value.get("source_commit"))
        and value.get("formal") is False
        and source.validate_static_certificate(value.get("static_certificate"))
        and value.get("formal_CLI_fail_closed") is True
        and value.get("scientific_roots") == 0
        and value.get("scientific_transitions") == 0
        and value.get("optimizer_steps") == 0
        and value.get("bootstrap_resamples") == 0
        and value.get("initializes_nonformal") is False
        and value.get("proof_only") is True
        and value.get("passed") is True
    )


def _load_readiness_train(run_root: Path) -> tuple[dict[str, Any], str]:
    path = Path(run_root) / "readiness_train.json"
    value = _read_json(path)
    if not _strict_readiness_train(value):
        raise ValueError("G53 readiness-train evidence failed strict validation")
    return value, _digest(path)


def _readiness_record(
    phase: str, *, source_commit: str, train_digest: str, predicate: bool,
    **extra: object,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION, "algorithm_id": ALGORITHM_ID,
        "source_id": source.SOURCE_ID, "phase": phase,
        "source_commit": source_commit, "formal": False,
        "readiness_train_sha256": train_digest,
        "scientific_roots": 0, "scientific_transitions": 0,
        "optimizer_steps": 0, "bootstrap_resamples": 0,
        "initializes_nonformal": False, "proof_only": True,
        "passed": bool(predicate), **extra,
    }


def readiness_train(*, run_root: Path, source_commit: str) -> dict[str, object]:
    if not _valid_commit(source_commit):
        raise ValueError("G53 readiness-train requires a valid source commit")
    root = _fresh_root(run_root); root.mkdir(parents=True)
    static = source.reconstruct_static_certificate()
    record = {
        "schema_version": SCHEMA_VERSION, "algorithm_id": ALGORITHM_ID,
        "source_id": source.SOURCE_ID, "phase": "readiness-train",
        "source_commit": source_commit, "formal": False,
        "static_certificate": static, "formal_CLI_fail_closed": True,
        "scientific_roots": 0, "scientific_transitions": 0,
        "optimizer_steps": 0, "bootstrap_resamples": 0,
        "initializes_nonformal": False, "proof_only": True,
        "passed": source.validate_static_certificate(static),
    }
    if not _strict_readiness_train(record):
        raise RuntimeError("G53 readiness-train evidence did not close")
    _write_json(root / "readiness_train.json", record); return record


def readiness_validate(*, run_root: Path) -> dict[str, object]:
    prior, digest = _load_readiness_train(run_root)
    return _readiness_record(
        "readiness-validate", source_commit=prior["source_commit"],
        train_digest=digest, predicate=_strict_readiness_train(prior),
        prior_strictly_valid=True,
    )


def readiness_reload(*, run_root: Path) -> dict[str, object]:
    prior, digest = _load_readiness_train(run_root)
    return _readiness_record(
        "readiness-reload", source_commit=prior["source_commit"],
        train_digest=digest, predicate=True,
        artifact_reloaded=True, reload_digest_verified=True,
    )


def readiness_evaluate(*, run_root: Path) -> dict[str, object]:
    prior, digest = _load_readiness_train(run_root)
    return _readiness_record(
        "readiness-evaluate", source_commit=prior["source_commit"],
        train_digest=digest, predicate=True, evaluation_cells=0,
    )


def readiness_analyze(*, run_root: Path) -> dict[str, object]:
    prior, digest = _load_readiness_train(run_root)
    return _readiness_record(
        "readiness-analyze", source_commit=prior["source_commit"],
        train_digest=digest, predicate=True, scientific_branch_selected=False,
    )


def exercise(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    train(run_root=run_root, source_commit=source_commit, formal=False)
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def _reject_formal(args: argparse.Namespace) -> None:
    if getattr(args, "formal", False) or any(
        getattr(args, name, None) is not None
        for name in ("authorization_token", "preflight_root", "alignment_disposition", "aligned_source_commit", "alignment_stage_commit")
    ):
        raise SystemExit("G53 formal runtime is not authorized; CLI fails closed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=PHASES)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--source-commit", default="0" * 40)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--cpu-budget", type=int, default=2)
    parser.add_argument("--process-workers", type=int, default=2)
    for name in ("authorization-token", "preflight-root", "alignment-disposition", "aligned-source-commit", "alignment-stage-commit"):
        parser.add_argument(f"--{name}")
    args = parser.parse_args(); _reject_formal(args)
    if args.phase == "readiness-smoke": result = readiness_interface_smoke(source_commit=args.source_commit)
    elif args.run_root is None: parser.error("--run-root is required")
    elif args.phase == "train": result = train(run_root=args.run_root, source_commit=args.source_commit, cpu_budget=args.cpu_budget, process_workers=args.process_workers)
    elif args.phase == "evaluate": result = evaluate(run_root=args.run_root, cpu_budget=args.cpu_budget, process_workers=args.process_workers)
    elif args.phase == "analyze": result = analyze(run_root=args.run_root, cpu_budget=args.cpu_budget, process_workers=args.process_workers)
    elif args.phase == "exercise": result = exercise(run_root=args.run_root, source_commit=args.source_commit)
    elif args.phase == "readiness-train": result = readiness_train(run_root=args.run_root, source_commit=args.source_commit)
    elif args.phase == "readiness-validate": result = readiness_validate(run_root=args.run_root)
    elif args.phase == "readiness-reload": result = readiness_reload(run_root=args.run_root)
    elif args.phase == "readiness-evaluate": result = readiness_evaluate(run_root=args.run_root)
    else: result = readiness_analyze(run_root=args.run_root)
    print(json.dumps(result, sort_keys=True, indent=2, default=str))


if __name__ == "__main__":
    main()
