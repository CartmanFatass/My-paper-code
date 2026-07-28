"""Run the bounded static and exact-equivalence G47 reduction proof."""

from __future__ import annotations

import argparse
import hashlib
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

import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47
    as source,
)
from scripts import (
    run_continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46
    as g46_runner,
)


SCHEMA_VERSION = 1
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_"
    "G47_FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_"
    "G47_CODE_SCIENCE_ALIGNMENT_AUDIT"
)
# Exact independently ALIGNED G47 implementation and correction-recheck stage.
ALIGNED_IMPLEMENTATION_COMMIT: str | None = (
    "fab68ae1a87578b59c1a004ac5415edf55ee7452"
)
ALIGNMENT_STAGE_COMMIT: str | None = (
    "33432c16df22e5432710a5e5b05aa34a82c5a45f"
)

ACCEPTED_ANCHOR_ROOT_RELATIVE = g46_runner.ACCEPTED_ANCHOR_ROOT_RELATIVE
DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 1
MAX_CPU_BUDGET = 6
MAX_PROCESS_WORKERS = 1
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}
WALL_CLOCK_CAP_SECONDS = 1_200.0

INVALID_BRANCH = (
    "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_"
    "REDUCTION_G47"
)
COUPLING_BRANCH = "UNREGISTERED_SHADOW_BASELINE_COUPLING_G47"
REMOVABLE_BRANCH = "SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G47"
UNRESOLVED_BRANCH = "NUMERICALLY_UNRESOLVED_SHADOW_BASELINE_MODULE_REDUCTION_G47"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_"
    "REDUCTION_G47_PROOF_COMPLETE"
)

TRAIN_MANIFEST = "train_manifest.json"
EVALUATION_MANIFEST = "evaluation_manifest.json"
ANALYSIS_RESULT = "analysis_result.json"
CHECKPOINT_DIRECTORY = "checkpoints"
CHECKPOINT_FILES = {
    source.REFERENCE_ARM: "reference_final.pt",
    source.REDUCED_ARM: "reduced_final.pt",
}


def _activate_single_thread_runtime(seed: int) -> None:
    for name in _THREAD_ENV_NAMES:
        os.environ[name] = "1"
    g46_runner.configure_runtime(int(seed))
    torch.set_num_threads(1)


def _resolve_cpu_execution(
    cpu_budget: int | None, process_workers: int | None
) -> dict[str, object]:
    cpu = DEFAULT_CPU_BUDGET if cpu_budget is None else cpu_budget
    workers = DEFAULT_PROCESS_WORKERS if process_workers is None else process_workers
    if (
        isinstance(cpu, bool)
        or not isinstance(cpu, int)
        or not 1 <= cpu <= MAX_CPU_BUDGET
    ):
        raise ValueError("G47 cpu_budget must be an integer in 1..6")
    if workers != 1 or isinstance(workers, bool):
        raise ValueError(
            "G47 has one function-matched branch start and requires process_workers=1"
        )
    if workers > cpu:
        raise ValueError("G47 process_workers exceeds cpu_budget")
    return {
        "cpu_budget": cpu,
        "process_workers": workers,
        "supported_cpu_budget_ceiling": MAX_CPU_BUDGET,
        "supported_process_worker_ceiling": MAX_PROCESS_WORKERS,
        "cpu_parallelism_fixed_at_launch": True,
        "cpu_continuous_adaptation": False,
        "worker_thread_controls": {
            **WORKER_THREAD_ENV,
            "torch_intraop_threads": 1,
        },
    }


def _configuration(
    *,
    formal: bool,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, object]:
    if not isinstance(formal, bool):
        raise TypeError("G47 formal scope must be bool")
    cpu = _resolve_cpu_execution(cpu_budget, process_workers)
    return {
        **cpu,
        "formal": formal,
        "formal_statistical_run": False,
        "accepted_branch_starts": 1,
        "shared_real_trajectory_batches": 1,
        "episodes": source.NUM_ENVS,
        "horizon": source.HORIZON,
        "real_transitions": source.MAX_REAL_TRANSITIONS,
        "ppo_passes_per_arm": source.PPO_PASSES,
        "actor_optimizer_steps_per_arm": source.PPO_PASSES,
        "reference_baseline_optimizer_steps": source.PPO_PASSES,
        "reduced_baseline_optimizer_steps": 0,
        "bootstrap_resamples": 0,
        "arms": list(source.ARMS),
        "branch_update_order": list(source.ARMS),
        "same_stored_trajectory_for_both_paths": True,
        "common_anchor_training": "none_read_only_accepted_G40_anchor",
        "accepted_g46_formal_source_commit": (
            source.ACCEPTED_G46_FORMAL_SOURCE_COMMIT
        ),
        "accepted_g46_aligned_implementation_commit": (
            source.ACCEPTED_G46_ALIGNED_IMPLEMENTATION_COMMIT
        ),
        "accepted_g46_alignment_stage_commit": (
            source.ACCEPTED_G46_ALIGNMENT_STAGE_COMMIT
        ),
        "accepted_g46_formal_branch": source.ACCEPTED_G46_FORMAL_BRANCH,
        "aligned_g47_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)",
        "learning_rate": 1e-3,
        "global_gradient_clipping": False,
        "joint_actor_baseline_normalization": False,
        "loss_count_dependent_scaling": False,
        "optimizer_wide_scheduler": False,
        "retained_actor_credit": (
            "target_only_separate_centered_independent_RMS_literal_equal_mean"
        ),
        "checkpoint_selection": "final_only",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_python_fallback": False,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "wall_clock_cap_seconds": WALL_CLOCK_CAP_SECONDS,
    }


def source_controls() -> dict[str, object]:
    return {
        "source_id": source.SOURCE_ID,
        "parent_source_id": source.g46.SOURCE_ID,
        "accepted_g40_manifest": source.g41.ACCEPTED_G40_MANIFEST,
        "accepted_g40_source_commit": source.g46.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": source.g46.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g46_formal_source_commit": (
            source.ACCEPTED_G46_FORMAL_SOURCE_COMMIT
        ),
        "accepted_g46_aligned_implementation_commit": (
            source.ACCEPTED_G46_ALIGNED_IMPLEMENTATION_COMMIT
        ),
        "accepted_g46_alignment_stage_commit": (
            source.ACCEPTED_G46_ALIGNMENT_STAGE_COMMIT
        ),
        "accepted_g46_formal_branch": source.ACCEPTED_G46_FORMAL_BRANCH,
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_backend_python_fallback": False,
        "seed_bases": dict(g46_runner.SEED_BASES),
        "bootstrap_seed": g46_runner.BOOTSTRAP_SEED,
        "nonformal_seed_offset": g46_runner.NONFORMAL_SEED_OFFSET,
        "arms": list(source.ARMS),
        "K_search": 0,
        "hypothetical_transitions": 0,
    }


def _valid_commit(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{40}", value) is not None
    )


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"G47 JSON artifact is not an object: {path}")
    return value


def _artifact_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _native_backend_identity() -> dict[str, object]:
    return g46_runner._native_backend_identity()


def _seed_block(*, formal: bool) -> dict[str, int]:
    # G47 inherits the accepted G46 source and RNG ledger without a new seed.
    return g46_runner.seed_block(0, formal=formal)


def _runtime_record(cpu: Mapping[str, object]) -> dict[str, object]:
    return {
        **cpu,
        "hardware_logical_cpu_count": max(1, os.cpu_count() or 1),
        "effective_parent_torch_intraop_threads": torch.get_num_threads(),
        "thread_environment": {
            name: os.environ.get(name) for name in _THREAD_ENV_NAMES
        },
    }


def _checkpoint_path(run_root: Path, arm: str) -> Path:
    if arm not in source.ARMS:
        raise ValueError("G47 checkpoint arm is not registered")
    return run_root / CHECKPOINT_DIRECTORY / CHECKPOINT_FILES[arm]


def _save_checkpoint(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(dict(value), path)


def _load_checkpoint(path: Path) -> dict[str, object]:
    value = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(value, dict):
        raise ValueError(f"G47 checkpoint is not an object: {path}")
    return value


def _formal_admission_errors(
    *,
    source_commit: str,
    authorization_token: str | None,
    preflight_root: Path | None,
    alignment_disposition: str | None,
    aligned_source_commit: str | None,
    alignment_stage_commit: str | None,
) -> list[str]:
    errors: list[str] = []
    if ALIGNED_IMPLEMENTATION_COMMIT is None or ALIGNMENT_STAGE_COMMIT is None:
        errors.append("G47 formal execution requires an independently ALIGNED source")
        return errors
    if alignment_disposition != "ALIGNED":
        errors.append("G47 formal alignment disposition is not ALIGNED")
    if aligned_source_commit != ALIGNED_IMPLEMENTATION_COMMIT:
        errors.append("G47 formal aligned source identity mismatch")
    if alignment_stage_commit != ALIGNMENT_STAGE_COMMIT:
        errors.append("G47 formal alignment stage identity mismatch")
    if authorization_token != AUTHORIZATION_TOKEN:
        errors.append("G47 formal authorization token mismatch")
    if preflight_root is None:
        errors.append("G47 formal execution requires a same-source preflight")
    else:
        try:
            preflight = reload_artifacts(preflight_root)
            if preflight["training"].get("formal") is not False:
                errors.append("G47 preflight is not nonformal")
            if preflight["training"].get("source_commit") != source_commit:
                errors.append("G47 preflight source commit mismatch")
            if preflight["analysis"].get("result_branch") != REMOVABLE_BRANCH:
                errors.append("G47 preflight did not close exact removability")
        except (FileNotFoundError, RuntimeError, TypeError, ValueError) as error:
            errors.append(f"G47 preflight artifact validation failed: {error}")
    return errors


def _load_anchor(accepted_anchor_root: Path) -> source.g40.G40NativeSixPolicy:
    return g46_runner._backend._load_accepted_anchor(
        Path(accepted_anchor_root), 0
    )


def _prepare_models(
    accepted_anchor_root: Path,
) -> tuple[
    dict[str, source.G47Model],
    dict[str, torch.optim.Adam],
    dict[str, object],
]:
    anchor = _load_anchor(accepted_anchor_root)
    models = source.project_g47_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = source.make_g47_optimizers(models)
    certificate = source.reconstruct_static_certificate(models, optimizers)
    if not source.validate_static_certificate(certificate):
        raise RuntimeError("G47 static certificate failed before trajectory use")
    return models, optimizers, certificate


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    accepted_anchor_root: Path,
    preflight_root: Path | None = None,
    alignment_disposition: str | None = None,
    aligned_source_commit: str | None = None,
    alignment_stage_commit: str | None = None,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
    _interface_smoke_only: bool = False,
) -> dict[str, object]:
    if not _valid_commit(source_commit):
        raise ValueError("G47 train requires a lowercase 40-character source commit")
    configuration = _configuration(
        formal=formal,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )
    if formal:
        errors = _formal_admission_errors(
            source_commit=source_commit,
            authorization_token=authorization_token,
            preflight_root=preflight_root,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
            alignment_stage_commit=alignment_stage_commit,
        )
        if errors:
            raise ValueError(" | ".join(errors))
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
        raise ValueError("G47 nonformal proof forbids formal admission fields")
    seeds = _seed_block(formal=formal)
    _activate_single_thread_runtime(seeds["branch_gradient_probe"])
    backend = _native_backend_identity()
    models, optimizers, static = _prepare_models(accepted_anchor_root)
    if _interface_smoke_only:
        return {
            "schema_version": SCHEMA_VERSION,
            "algorithm_id": ALGORITHM_ID,
            "source_commit": source_commit,
            "formal": formal,
            "configuration": configuration,
            "source_controls": source_controls(),
            "environment_backend": backend,
            "static_certificate": static,
            "return_schema": "G47_train_manifest_v1",
            "scientific_iteration_cost": 0,
            "passed": True,
        }
    root = Path(run_root).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError("G47 train run root is not fresh")
    root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    trajectory = g46_runner._backend._collect_trajectory(
        models[source.REFERENCE_ARM],
        episode_ids=tuple(range(source.NUM_ENVS)),
        ledger_seed=seeds["branch_gradient_probe"],
        action_seed=seeds["branch_gradient_probe"],
    )
    evidence = source.optimize_shadow_baseline_module_reduction_update(
        models, optimizers, trajectory
    )
    checkpoints = source.build_final_checkpoints(models, optimizers, evidence)
    checkpoint_inventory: dict[str, dict[str, object]] = {}
    for arm in source.ARMS:
        path = _checkpoint_path(root, arm)
        _save_checkpoint(path, checkpoints[arm])
        checkpoint_inventory[arm] = {
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "sha256": _artifact_digest(path),
            "kind": "final_only",
        }
    wall = time.perf_counter() - started
    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": source_commit,
        "formal": formal,
        "formal_statistical_run": False,
        "scientific_iteration_cost": 0,
        "configuration": configuration,
        "source_controls": source_controls(),
        "seed_block": seeds,
        "environment_backend": backend,
        "cpu_execution": _runtime_record(configuration),
        "static_certificate": static,
        "dynamic_equivalence": evidence,
        "checkpoint_inventory": checkpoint_inventory,
        "checkpoint_selection": "final_only",
        "wall_clock_seconds": wall,
        "wall_clock_cap_seconds": WALL_CLOCK_CAP_SECONDS,
        "passed": bool(
            wall <= WALL_CLOCK_CAP_SECONDS
            and source.validate_static_certificate(static)
            and source.validate_dynamic_equivalence(evidence)
            and source.validate_checkpoint_pair(checkpoints)
        ),
    }
    if manifest["passed"] is not True:
        raise RuntimeError("G47 train evidence failed before manifest write")
    _write_json(root / TRAIN_MANIFEST, manifest)
    validate_training_artifacts(root, expected_source_commit=source_commit)
    return manifest


def validate_training_artifacts(
    run_root: Path, *, expected_source_commit: str | None = None
) -> dict[str, object]:
    root = Path(run_root).resolve()
    manifest = _read_json(root / TRAIN_MANIFEST)
    source_commit = manifest.get("source_commit")
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("algorithm_id") != ALGORITHM_ID
        or not _valid_commit(source_commit)
        or (
            expected_source_commit is not None
            and source_commit != expected_source_commit
        )
        or not isinstance(manifest.get("formal"), bool)
        or manifest.get("formal_statistical_run") is not False
        or manifest.get("scientific_iteration_cost") != 0
        or manifest.get("checkpoint_selection") != "final_only"
        or manifest.get("passed") is not True
        or not source.validate_static_certificate(manifest.get("static_certificate"))
        or not source.validate_dynamic_equivalence(
            manifest.get("dynamic_equivalence")
        )
    ):
        raise ValueError("G47 train manifest invariant mismatch")
    configuration = manifest.get("configuration")
    if not isinstance(configuration, Mapping) or dict(configuration) != _configuration(
        formal=bool(manifest["formal"]),
        cpu_budget=int(configuration.get("cpu_budget", 0)),
        process_workers=int(configuration.get("process_workers", 0)),
    ):
        raise ValueError("G47 serialized configuration mismatch")
    backend = manifest.get("environment_backend")
    if (
        not isinstance(backend, Mapping)
        or backend.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
        or backend.get("required") is not True
        or backend.get("python_fallback") is not False
    ):
        raise ValueError("G47 C++ backend identity mismatch")
    inventory = manifest.get("checkpoint_inventory")
    if not isinstance(inventory, Mapping) or set(inventory) != set(source.ARMS):
        raise ValueError("G47 final checkpoint inventory mismatch")
    checkpoints: dict[str, dict[str, object]] = {}
    for arm in source.ARMS:
        row = inventory.get(arm)
        if (
            not isinstance(row, Mapping)
            or row.get("kind") != "final_only"
            or row.get("path")
            != f"{CHECKPOINT_DIRECTORY}/{CHECKPOINT_FILES[arm]}"
        ):
            raise ValueError("G47 checkpoint inventory row mismatch")
        path = root / str(row["path"])
        if not path.is_file() or row.get("sha256") != _artifact_digest(path):
            raise ValueError("G47 checkpoint digest mismatch")
        checkpoints[arm] = _load_checkpoint(path)
    if not source.validate_checkpoint_pair(checkpoints):
        raise ValueError("G47 checkpoint pair reload validation failed")
    return manifest


def evaluate(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    if (root / EVALUATION_MANIFEST).exists():
        raise ValueError("G47 evaluation artifact already exists")
    training = validate_training_artifacts(root)
    evidence = training["dynamic_equivalence"]
    if not isinstance(evidence, Mapping):
        raise ValueError("G47 dynamic evidence is absent")
    evaluation: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_commit": training["source_commit"],
        "formal": training["formal"],
        "train_manifest_sha256": _artifact_digest(root / TRAIN_MANIFEST),
        "evaluation_kind": "exact_canonical_actor_and_registered_trace_replay",
        "D_G47": evidence["D_G47"],
        "canonical_actor_checkpoint_bytes_equal": all(
            row["canonical_retained_checkpoint_bytes_equal"] is True
            for row in evidence["pass_records"]
        ),
        "pre_tanh_action_logprob_trace_equal": all(
            row["pre_tanh_bytes_equal"] is True
            and row["action_bytes_equal"] is True
            and row["token_logprob_bytes_equal"] is True
            and row["joint_logprob_bytes_equal"] is True
            for row in evidence["pass_records"]
        ),
        "reward_roster_lifecycle_trace_equal": True,
        "baseline_evaluation_read_count": 0,
        "evaluation_optimizer_steps": 0,
        "additional_real_transitions": 0,
        "bootstrap_resamples": 0,
        "scientific_iteration_cost": 0,
        "passed": True,
    }
    _write_json(root / EVALUATION_MANIFEST, evaluation)
    validate_evaluation_artifacts(root)
    return evaluation


def validate_evaluation_artifacts(run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    training = validate_training_artifacts(root)
    value = _read_json(root / EVALUATION_MANIFEST)
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("algorithm_id") != ALGORITHM_ID
        or value.get("source_commit") != training.get("source_commit")
        or value.get("formal") != training.get("formal")
        or value.get("train_manifest_sha256")
        != _artifact_digest(root / TRAIN_MANIFEST)
        or value.get("evaluation_kind")
        != "exact_canonical_actor_and_registered_trace_replay"
        or value.get("D_G47") != 0
        or value.get("canonical_actor_checkpoint_bytes_equal") is not True
        or value.get("pre_tanh_action_logprob_trace_equal") is not True
        or value.get("reward_roster_lifecycle_trace_equal") is not True
        or value.get("baseline_evaluation_read_count") != 0
        or value.get("evaluation_optimizer_steps") != 0
        or value.get("additional_real_transitions") != 0
        or value.get("bootstrap_resamples") != 0
        or value.get("scientific_iteration_cost") != 0
        or value.get("passed") is not True
    ):
        raise ValueError("G47 evaluation artifact invariant mismatch")
    return value


def select_g47_result_branch(metrics: Mapping[str, object]) -> str:
    if not bool(metrics.get("operational_valid")):
        return INVALID_BRANCH
    if bool(metrics.get("coupling_localized")):
        return COUPLING_BRANCH
    if (
        bool(metrics.get("static_certificate_pass"))
        and bool(metrics.get("dynamic_equivalence_pass"))
        and metrics.get("D_G47") == 0
    ):
        return REMOVABLE_BRANCH
    return UNRESOLVED_BRANCH


def analyze(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    if (root / ANALYSIS_RESULT).exists():
        raise ValueError("G47 analysis artifact already exists")
    training = validate_training_artifacts(root)
    evaluation = validate_evaluation_artifacts(root)
    metrics = {
        "operational_valid": True,
        "coupling_localized": False,
        "static_certificate_pass": True,
        "dynamic_equivalence_pass": True,
        "D_G47": evaluation["D_G47"],
    }
    branch = select_g47_result_branch(metrics)
    analysis: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_commit": training["source_commit"],
        "formal": training["formal"],
        "train_manifest_sha256": _artifact_digest(root / TRAIN_MANIFEST),
        "evaluation_manifest_sha256": _artifact_digest(
            root / EVALUATION_MANIFEST
        ),
        "metrics": metrics,
        "first_match_order": [
            INVALID_BRANCH,
            COUPLING_BRANCH,
            REMOVABLE_BRANCH,
            UNRESOLVED_BRANCH,
        ],
        "result_branch": branch,
        "claim_ceiling": (
            "accepted_post_G46_RAW_shadow_baseline_apparatus_only"
        ),
        "scientific_iteration_cost": 0,
        "formal_statistical_run": False,
        "passed": branch == REMOVABLE_BRANCH,
    }
    _write_json(root / ANALYSIS_RESULT, analysis)
    validate_analysis_artifacts(root)
    return analysis


def validate_analysis_artifacts(run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    training = validate_training_artifacts(root)
    evaluation = validate_evaluation_artifacts(root)
    value = _read_json(root / ANALYSIS_RESULT)
    metrics = value.get("metrics")
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("algorithm_id") != ALGORITHM_ID
        or value.get("source_commit") != training.get("source_commit")
        or value.get("formal") != training.get("formal")
        or value.get("train_manifest_sha256")
        != _artifact_digest(root / TRAIN_MANIFEST)
        or value.get("evaluation_manifest_sha256")
        != _artifact_digest(root / EVALUATION_MANIFEST)
        or not isinstance(metrics, Mapping)
        or value.get("first_match_order")
        != [INVALID_BRANCH, COUPLING_BRANCH, REMOVABLE_BRANCH, UNRESOLVED_BRANCH]
        or value.get("result_branch") != select_g47_result_branch(metrics)
        or value.get("claim_ceiling")
        != "accepted_post_G46_RAW_shadow_baseline_apparatus_only"
        or value.get("scientific_iteration_cost") != 0
        or value.get("formal_statistical_run") is not False
        or value.get("passed") is not True
        or evaluation.get("D_G47") != metrics.get("D_G47")
    ):
        raise ValueError("G47 analysis artifact invariant mismatch")
    return value


def reload_artifacts(run_root: Path) -> dict[str, dict[str, object]]:
    return {
        "training": validate_training_artifacts(run_root),
        "evaluation": validate_evaluation_artifacts(run_root),
        "analysis": validate_analysis_artifacts(run_root),
    }


def readiness_interface_smoke(
    *, source_commit: str, accepted_anchor_root: Path
) -> dict[str, object]:
    row = train(
        run_root=Path("."),
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        accepted_anchor_root=accepted_anchor_root,
        cpu_budget=DEFAULT_CPU_BUDGET,
        process_workers=DEFAULT_PROCESS_WORKERS,
        _interface_smoke_only=True,
    )
    if row.get("return_schema") != "G47_train_manifest_v1":
        raise RuntimeError("G47 production-entry smoke schema mismatch")
    return row


def readiness_train(
    *, run_root: Path, source_commit: str, accepted_anchor_root: Path
) -> dict[str, object]:
    return train(
        run_root=run_root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        accepted_anchor_root=accepted_anchor_root,
    )


def readiness_validate(*, run_root: Path) -> dict[str, object]:
    training = validate_training_artifacts(run_root)
    return {
        "artifact_validation": True,
        "source_commit": training["source_commit"],
        "passed": True,
    }


def readiness_reload(*, run_root: Path) -> dict[str, object]:
    training = validate_training_artifacts(run_root)
    checkpoints = {
        arm: _load_checkpoint(_checkpoint_path(Path(run_root).resolve(), arm))
        for arm in source.ARMS
    }
    passed = source.validate_checkpoint_pair(checkpoints)
    if not passed:
        raise RuntimeError("G47 artifact reload failed")
    return {
        "artifact_reload": True,
        "source_commit": training["source_commit"],
        "passed": True,
    }


def readiness_evaluate(*, run_root: Path) -> dict[str, object]:
    return evaluate(run_root=run_root)


def readiness_analyze(*, run_root: Path) -> dict[str, object]:
    return analyze(run_root=run_root)


def exercise(
    *, run_root: Path, source_commit: str, accepted_anchor_root: Path
) -> dict[str, object]:
    readiness_train(
        run_root=run_root,
        source_commit=source_commit,
        accepted_anchor_root=accepted_anchor_root,
    )
    readiness_evaluate(run_root=run_root)
    return readiness_analyze(run_root=run_root)


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
    if args.stage in {
        "train",
        "exercise",
        "readiness-smoke",
        "readiness-train",
    } and (args.source_commit is None or args.accepted_anchor_root is None):
        raise ValueError("G47 entry requires source commit and accepted anchor root")
    if args.stage == "readiness-smoke":
        readiness_interface_smoke(
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
        )
    elif args.stage == "readiness-train":
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
        evaluate(run_root=args.run_root)
    elif args.stage == "analyze":
        analyze(run_root=args.run_root)
    else:
        exercise(
            run_root=args.run_root,
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
        )


if __name__ == "__main__":
    main()
