"""Run the bounded G49 duplicated-immediate single-channel collapse proof."""

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
    continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49
    as source,
)
from scripts import (
    run_continuous_roster_native_six_g31_realized_successor_channel_attribution_g48
    as g48_runner,
)


SCHEMA_VERSION = 1
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_"
    "SINGLE_CHANNEL_COLLAPSE_G49_FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_"
    "SINGLE_CHANNEL_COLLAPSE_CODE_SCIENCE_ALIGNMENT_AUDIT"
)

# Formal admission is intentionally closed until an independent G49 alignment.
ALIGNED_IMPLEMENTATION_COMMIT: str | None = None
ALIGNMENT_STAGE_COMMIT: str | None = None

ACCEPTED_ANCHOR_ROOT_RELATIVE = g48_runner.ACCEPTED_ANCHOR_ROOT_RELATIVE
DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 1
MAX_CPU_BUDGET = 6
MAX_PROCESS_WORKERS = 1
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}
WALL_CLOCK_CAP_SECONDS = 1_200.0

INVALID_BRANCH = (
    "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_"
    "SINGLE_CHANNEL_COLLAPSE_G49"
)
COUPLING_BRANCH = "UNREGISTERED_DUPLICATED_IMMEDIATE_COUPLING_G49"
REMOVABLE_BRANCH = "DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_EXACTLY_COLLAPSIBLE_G49"
UNRESOLVED_BRANCH = (
    "NUMERICALLY_UNRESOLVED_DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_COLLAPSE_G49"
)
PROOF_COMPLETE_BRANCH = (
    "PROOF_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_"
    "SINGLE_CHANNEL_COLLAPSE_G49_COMPLETE"
)

TRAIN_MANIFEST = "train_manifest.json"
EVALUATION_MANIFEST = "evaluation_manifest.json"
ANALYSIS_RESULT = "analysis_result.json"
CHECKPOINT_DIRECTORY = "checkpoints"
CHECKPOINT_FILES = {
    source.REFERENCE_ARM: "duplicated_immediate_reference_final.pt",
    source.REDUCED_ARM: "single_immediate_reduced_final.pt",
}
SHARED_TRAJECTORY_REFERENCE = "proof_inputs/shared_trajectory.pt"
TWO_PROCESS_REPORT_REFERENCE = "parallel_proof/two_process_equivalence.json"


def _activate_single_thread_runtime(seed: int) -> None:
    for name in _THREAD_ENV_NAMES:
        os.environ[name] = "1"
    g48_runner.configure_runtime(int(seed))
    torch.set_num_threads(1)


def _resolve_cpu_execution(
    cpu_budget: int | None, process_workers: int | None
) -> dict[str, object]:
    cpu = DEFAULT_CPU_BUDGET if cpu_budget is None else cpu_budget
    workers = DEFAULT_PROCESS_WORKERS if process_workers is None else process_workers
    if isinstance(cpu, bool) or not isinstance(cpu, int) or not 1 <= cpu <= MAX_CPU_BUDGET:
        raise ValueError("G49 cpu_budget must be an integer in 1..6")
    if (
        isinstance(workers, bool)
        or not isinstance(workers, int)
        or workers != 1
    ):
        raise ValueError(
            "G49 production proof has one branch start and requires process_workers=1"
        )
    if workers > cpu:
        raise ValueError("G49 process_workers exceeds cpu_budget")
    return {
        "cpu_budget": cpu,
        "process_workers": workers,
        "supported_cpu_budget_ceiling": MAX_CPU_BUDGET,
        "supported_process_worker_ceiling": MAX_PROCESS_WORKERS,
        "cpu_parallelism_fixed_at_launch": True,
        "cpu_continuous_adaptation": False,
        "worker_start_method": "spawn",
        "deterministic_merge": "preassigned_index_not_completion_order",
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
        raise TypeError("G49 formal scope must be bool")
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
        "bootstrap_resamples": 0,
        "arms": list(source.ARMS),
        "branch_update_order": list(source.ARMS),
        "same_stored_trajectory_for_both_paths": True,
        "common_anchor_training": "none_read_only_accepted_G40_anchor",
        "accepted_g48_formal_source_commit": source.ACCEPTED_G48_FORMAL_SOURCE_COMMIT,
        "accepted_g48_aligned_implementation_commit": source.ACCEPTED_G48_ALIGNED_IMPLEMENTATION_COMMIT,
        "accepted_g48_alignment_stage_commit": source.ACCEPTED_G48_ALIGNMENT_STAGE_COMMIT,
        "accepted_g48_formal_branch": source.ACCEPTED_G48_FORMAL_BRANCH,
        "aligned_g49_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0,amsgrad=false)",
        "learning_rate": 1e-3,
        "gradient_clipping": False,
        "minibatches": False,
        "optimizer_reset": False,
        "baseline_module": "absent",
        "standalone_slow_critic": "absent",
        "reference_channel_count": 2,
        "reduced_channel_count": 1,
        "common_entropy_additions_per_pass": 1,
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
        "parent_source_id": source.g48.SOURCE_ID,
        "design_stage_commit": source.DESIGN_STAGE_COMMIT,
        "design_disposition": source.DESIGN_DISPOSITION,
        "accepted_g40_manifest": source.g41.ACCEPTED_G40_MANIFEST,
        "accepted_g48_formal_source_commit": source.ACCEPTED_G48_FORMAL_SOURCE_COMMIT,
        "accepted_g48_aligned_implementation_commit": source.ACCEPTED_G48_ALIGNED_IMPLEMENTATION_COMMIT,
        "accepted_g48_alignment_stage_commit": source.ACCEPTED_G48_ALIGNMENT_STAGE_COMMIT,
        "accepted_g48_formal_branch": source.ACCEPTED_G48_FORMAL_BRANCH,
        "seed_bases": dict(g48_runner.SEED_BASES),
        "bootstrap_seed": g48_runner.BOOTSTRAP_SEED,
        "nonformal_seed_offset": g48_runner.NONFORMAL_SEED_OFFSET,
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_backend_python_fallback": False,
        "arms": list(source.ARMS),
        "result_type": "exact_functional_and_optimizer_equivalence",
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
        raise ValueError(f"G49 JSON artifact is not an object: {path}")
    return value


def _artifact_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _semantic_digest(value: object) -> str:
    digest = hashlib.sha256()

    def visit(row: object) -> None:
        if isinstance(row, torch.Tensor):
            tensor = row.detach().cpu().contiguous()
            digest.update(b"tensor")
            digest.update(str(tensor.dtype).encode("ascii"))
            digest.update(json.dumps(list(tensor.shape)).encode("ascii"))
            digest.update(tensor.numpy().tobytes())
        elif isinstance(row, Mapping):
            digest.update(b"mapping")
            for key in sorted(row, key=lambda item: str(item)):
                digest.update(str(key).encode("utf-8"))
                visit(row[key])
        elif isinstance(row, (list, tuple)):
            digest.update(b"sequence")
            for item in row:
                visit(item)
        else:
            digest.update(type(row).__name__.encode("ascii"))
            digest.update(repr(row).encode("utf-8"))

    visit(value)
    return digest.hexdigest()


def _native_backend_identity() -> dict[str, object]:
    return g48_runner._native_backend_identity()


def _seed_block(*, formal: bool) -> dict[str, int]:
    # The exact G48 seed ledger is inherited; this proof uses replicate zero.
    return g48_runner.seed_block(0, formal=formal)


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
        raise ValueError("G49 checkpoint arm is not registered")
    return run_root / CHECKPOINT_DIRECTORY / CHECKPOINT_FILES[arm]


def _save_checkpoint(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(dict(value), path)


def _load_checkpoint(path: Path) -> dict[str, object]:
    value = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(value, dict):
        raise ValueError(f"G49 checkpoint is not an object: {path}")
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
        errors.append("G49 formal execution requires an independently ALIGNED source")
        return errors
    if alignment_disposition != "ALIGNED":
        errors.append("G49 formal alignment disposition is not ALIGNED")
    if aligned_source_commit != ALIGNED_IMPLEMENTATION_COMMIT:
        errors.append("G49 formal aligned source identity mismatch")
    if alignment_stage_commit != ALIGNMENT_STAGE_COMMIT:
        errors.append("G49 formal alignment stage identity mismatch")
    if authorization_token != AUTHORIZATION_TOKEN:
        errors.append("G49 formal authorization token mismatch")
    if preflight_root is None:
        errors.append("G49 formal execution requires a same-source preflight")
    else:
        try:
            preflight = reload_artifacts(preflight_root)
            if preflight["training"].get("formal") is not False:
                errors.append("G49 preflight is not proof-only nonformal scope")
            if preflight["training"].get("source_commit") != source_commit:
                errors.append("G49 preflight source commit mismatch")
            if preflight["analysis"].get("result_branch") != REMOVABLE_BRANCH:
                errors.append("G49 preflight did not close exact removability")
        except (FileNotFoundError, RuntimeError, TypeError, ValueError) as error:
            errors.append(f"G49 preflight artifact validation failed: {error}")
    return errors


def _load_anchor(accepted_anchor_root: Path) -> source.g40.G40NativeSixPolicy:
    root = g48_runner._bind_anchor_root(Path(accepted_anchor_root))
    g48_runner._validate_anchor_manifest(root)
    return g48_runner._load_accepted_anchor(root, 0)


def _prepare_models(
    accepted_anchor_root: Path,
) -> tuple[
    dict[str, source.G49Model],
    dict[str, torch.optim.Adam],
    dict[str, object],
]:
    anchor = _load_anchor(accepted_anchor_root)
    models = source.project_g49_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = source.make_g49_optimizers(models)
    certificate = source.reconstruct_static_certificate(models, optimizers)
    if not source.validate_static_certificate(certificate):
        raise RuntimeError("G49 static certificate failed before trajectory use")
    return models, optimizers, certificate


def _collect_shared_trajectory(
    model: source.G49Model, *, formal: bool
) -> source.AnchoredRosterTrajectory:
    seeds = _seed_block(formal=formal)
    return g48_runner._collect_trajectory(
        model,
        episode_ids=tuple(range(source.NUM_ENVS)),
        ledger_seed=seeds["branch_ledger"],
        action_seed=seeds["branch_action"],
    )


def _fresh_root(root: Path) -> Path:
    resolved = Path(root).resolve()
    if resolved.exists() and (not resolved.is_dir() or any(resolved.iterdir())):
        raise ValueError("G49 run root must be absent or empty")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


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
    _execution_readiness_proof: bool = False,
) -> dict[str, object]:
    if not _valid_commit(source_commit):
        raise ValueError("G49 train requires a lowercase 40-character source commit")
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
        raise ValueError("G49 proof-only scope forbids formal admission fields")
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
            "return_schema": "G49_train_manifest_v1",
            "scientific_iteration_cost": 0,
            "passed": True,
        }
    root = _fresh_root(run_root)
    started = time.perf_counter()
    trajectory = _collect_shared_trajectory(models[source.REFERENCE_ARM], formal=formal)
    trajectory_path = root / SHARED_TRAJECTORY_REFERENCE
    trajectory_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(trajectory, trajectory_path)
    evidence = source.optimize_duplicated_immediate_single_channel_update(
        models, optimizers, trajectory, update_index=0
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
        "execution_readiness_proof_only": _execution_readiness_proof,
        "scientific_iteration_cost": 0,
        "configuration": configuration,
        "source_controls": source_controls(),
        "seed_block": seeds,
        "environment_backend": backend,
        "cpu_execution": _runtime_record(configuration),
        "static_certificate": static,
        "dynamic_equivalence": evidence,
        "shared_trajectory": {
            "path": SHARED_TRAJECTORY_REFERENCE,
            "sha256": _artifact_digest(trajectory_path),
            "real_transitions": source.MAX_REAL_TRANSITIONS,
            "used_by_both_paths": True,
        },
        "checkpoint_inventory": checkpoint_inventory,
        "checkpoint_selection": "final_only",
        "wall_clock_seconds": wall,
        "wall_clock_cap_seconds": WALL_CLOCK_CAP_SECONDS,
        "two_process_equivalence": None,
        "two_process_equivalence_artifact": None,
        "passed": bool(
            wall <= WALL_CLOCK_CAP_SECONDS
            and source.validate_static_certificate(static)
            and source.validate_update_evidence(evidence)
            and source.validate_checkpoint_pair(checkpoints)
        ),
    }
    if manifest["passed"] is not True:
        raise RuntimeError("G49 train evidence failed before manifest write")
    _write_json(root / TRAIN_MANIFEST, manifest)
    validate_training_artifacts(root, expected_source_commit=source_commit)
    return manifest


def _activate_worker() -> None:
    for name in _THREAD_ENV_NAMES:
        os.environ[name] = "1"
    torch.set_num_threads(1)


def _two_process_worker(task: Mapping[str, object]) -> dict[str, object]:
    _activate_worker()
    index = int(task["index"])
    anchor_root = Path(str(task["accepted_anchor_root"]))
    trajectory_path = Path(str(task["trajectory_path"]))
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G49 two-process worker output path is not fresh")
    trajectory = torch.load(trajectory_path, map_location="cpu", weights_only=False)
    models, optimizers, static = _prepare_models(anchor_root)
    evidence = source.optimize_duplicated_immediate_single_channel_update(
        models, optimizers, trajectory, update_index=0
    )
    checkpoints = source.build_final_checkpoints(models, optimizers, evidence)
    semantic = {
        "static_sha256": hashlib.sha256(
            source.serialize_diagnostics(static).encode("utf-8")
        ).hexdigest(),
        "evidence_sha256": hashlib.sha256(
            source.serialize_diagnostics(evidence).encode("utf-8")
        ).hexdigest(),
        "model_state_digests": {
            arm: source.g47._state_digest(source.g48._actor_state(models[arm]))
            for arm in source.ARMS
        },
        "adam_state_digests": {
            arm: source.g47._optimizer_state_digest(
                source.g47._optimizer_state_by_name(optimizers[arm], models[arm])
            )
            for arm in source.ARMS
        },
        "checkpoint_projection_digest": {
            arm: _semantic_digest(source.canonical_actor_projection(checkpoints[arm]))
            for arm in source.ARMS
        },
        "D_SC": evidence["D_SC"],
        "passed": evidence["passed"],
    }
    payload = {
        "index": index,
        "pid": os.getpid(),
        "thread_environment": {
            name: os.environ.get(name) for name in _THREAD_ENV_NAMES
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


def prove_two_process_equivalence(
    *,
    proof_root: Path,
    accepted_anchor_root: Path,
    trajectory_path: Path,
) -> dict[str, object]:
    root = Path(proof_root).resolve()
    tasks = [
        {
            "index": index,
            "accepted_anchor_root": str(Path(accepted_anchor_root).resolve()),
            "trajectory_path": str(Path(trajectory_path).resolve()),
            "output_path": str(root / f"worker_{index}" / "result.json"),
        }
        for index in range(2)
    ]
    results = g48_runner._run_indexed_worker_tasks(
        tasks, _two_process_worker, process_workers=2
    )
    payloads = [_read_json(Path(str(result["output_path"]))) for result in results]
    equivalent = payloads[0]["semantic"] == payloads[1]["semantic"]
    distinct = len({int(payload["pid"]) for payload in payloads}) == 2
    threads = all(
        payload["torch_intraop_threads"] == 1
        and all(
            payload["thread_environment"].get(name) == "1"
            for name in _THREAD_ENV_NAMES
        )
        for payload in payloads
    )
    report = {
        "proof_kind": "two_process_g49_exact_collapse_equivalence",
        "worker_count": 2,
        "distinct_processes": distinct,
        "single_thread_workers": threads,
        "deterministic_preassigned_index_merge": [
            payload["index"] for payload in payloads
        ]
        == [0, 1],
        "shared_stored_trajectory_path": str(Path(trajectory_path).resolve()),
        "duplicated_environment_interaction": False,
        "real_transitions": source.MAX_REAL_TRANSITIONS,
        "parameters_Adam_evidence_checkpoint_bitwise_equivalent": equivalent,
        "semantic": payloads[0]["semantic"] if equivalent else None,
        "formal": False,
        "formal_statistical_run": False,
        "scientific_iteration_cost": 0,
        "passed": bool(equivalent and distinct and threads),
    }
    _write_json(root / "two_process_equivalence.json", report)
    if report["passed"] is not True:
        raise RuntimeError("G49 two-process equivalence failed")
    return report


def validate_training_artifacts(
    run_root: Path, *, expected_source_commit: str | None = None
) -> dict[str, object]:
    root = Path(run_root).resolve()
    manifest = _read_json(root / TRAIN_MANIFEST)
    source_commit = manifest.get("source_commit")
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("algorithm_id") != ALGORITHM_ID
        or manifest.get("source_id") != source.SOURCE_ID
        or not _valid_commit(source_commit)
        or (expected_source_commit is not None and source_commit != expected_source_commit)
        or not isinstance(manifest.get("formal"), bool)
        or manifest.get("formal_statistical_run") is not False
        or manifest.get("scientific_iteration_cost") != 0
        or manifest.get("checkpoint_selection") != "final_only"
        or manifest.get("passed") is not True
        or not source.validate_static_certificate(manifest.get("static_certificate"))
        or not source.validate_update_evidence(manifest.get("dynamic_equivalence"))
    ):
        raise ValueError("G49 train manifest invariant mismatch")
    configuration = manifest.get("configuration")
    if not isinstance(configuration, Mapping) or dict(configuration) != _configuration(
        formal=bool(manifest["formal"]),
        cpu_budget=int(configuration.get("cpu_budget", 0)),
        process_workers=int(configuration.get("process_workers", 0)),
    ):
        raise ValueError("G49 serialized configuration mismatch")
    backend = manifest.get("environment_backend")
    if (
        not isinstance(backend, Mapping)
        or backend.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
        or backend.get("required") is not True
        or backend.get("python_fallback") is not False
    ):
        raise ValueError("G49 C++ backend identity mismatch")
    shared = manifest.get("shared_trajectory")
    if not isinstance(shared, Mapping):
        raise ValueError("G49 shared trajectory record missing")
    trajectory_path = root / str(shared.get("path"))
    if (
        shared.get("path") != SHARED_TRAJECTORY_REFERENCE
        or shared.get("real_transitions") != source.MAX_REAL_TRANSITIONS
        or shared.get("used_by_both_paths") is not True
        or not trajectory_path.is_file()
        or shared.get("sha256") != _artifact_digest(trajectory_path)
    ):
        raise ValueError("G49 shared trajectory identity mismatch")
    inventory = manifest.get("checkpoint_inventory")
    if not isinstance(inventory, Mapping) or set(inventory) != set(source.ARMS):
        raise ValueError("G49 final checkpoint inventory mismatch")
    checkpoints: dict[str, dict[str, object]] = {}
    for arm in source.ARMS:
        row = inventory.get(arm)
        expected = f"{CHECKPOINT_DIRECTORY}/{CHECKPOINT_FILES[arm]}"
        if (
            not isinstance(row, Mapping)
            or row.get("kind") != "final_only"
            or row.get("path") != expected
        ):
            raise ValueError("G49 checkpoint inventory row mismatch")
        path = root / expected
        if not path.is_file() or row.get("sha256") != _artifact_digest(path):
            raise ValueError("G49 checkpoint digest mismatch")
        checkpoints[arm] = _load_checkpoint(path)
    if not source.validate_checkpoint_pair(checkpoints):
        raise ValueError("G49 checkpoint reload validation failed")
    readiness = manifest.get("execution_readiness_proof_only") is True
    report_reference = manifest.get("two_process_equivalence_artifact")
    if readiness:
        if report_reference != TWO_PROCESS_REPORT_REFERENCE:
            raise ValueError("G49 readiness process-proof reference mismatch")
        report = _read_json(root / str(report_reference))
        if (
            report != manifest.get("two_process_equivalence")
            or report.get("passed") is not True
            or report.get("worker_count") != 2
            or report.get("distinct_processes") is not True
            or report.get("single_thread_workers") is not True
            or report.get("deterministic_preassigned_index_merge") is not True
            or report.get("duplicated_environment_interaction") is not False
            or report.get("real_transitions") != source.MAX_REAL_TRANSITIONS
            or report.get("parameters_Adam_evidence_checkpoint_bitwise_equivalent") is not True
        ):
            raise ValueError("G49 readiness two-process proof mismatch")
    elif report_reference is not None or manifest.get("two_process_equivalence") is not None:
        raise ValueError("G49 ordinary artifact contains readiness-only process proof")
    return manifest


def evaluate(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    training = validate_training_artifacts(root)
    checkpoints = {
        arm: _load_checkpoint(_checkpoint_path(root, arm)) for arm in source.ARMS
    }
    if not source.validate_checkpoint_pair(checkpoints):
        raise RuntimeError("G49 evaluate checkpoint reload mismatch")
    canonical_equal = source._canonical_values_equal(
        source.canonical_actor_projection(checkpoints[source.REFERENCE_ARM]),
        source.canonical_actor_projection(checkpoints[source.REDUCED_ARM]),
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_commit": training["source_commit"],
        "formal": training["formal"],
        "formal_statistical_run": False,
        "scientific_iteration_cost": 0,
        "evaluation_optimizer_steps": 0,
        "environment_transitions": 0,
        "canonical_final_checkpoint_projection_equal": canonical_equal,
        "D_SC": 0.0 if canonical_equal else float("inf"),
        "passed": canonical_equal,
    }
    if result["passed"] is not True:
        raise RuntimeError("G49 evaluation exact projection mismatch")
    _write_json(root / EVALUATION_MANIFEST, result)
    return result


def validate_evaluation_artifacts(run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    training = validate_training_artifacts(root)
    value = _read_json(root / EVALUATION_MANIFEST)
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("algorithm_id") != ALGORITHM_ID
        or value.get("source_commit") != training.get("source_commit")
        or value.get("formal") != training.get("formal")
        or value.get("formal_statistical_run") is not False
        or value.get("scientific_iteration_cost") != 0
        or value.get("evaluation_optimizer_steps") != 0
        or value.get("environment_transitions") != 0
        or value.get("canonical_final_checkpoint_projection_equal") is not True
        or value.get("D_SC") != 0.0
        or value.get("passed") is not True
    ):
        raise ValueError("G49 evaluation artifact invariant mismatch")
    return value


def select_g49_result_branch(metrics: Mapping[str, object]) -> str:
    if metrics.get("valid") is not True:
        return INVALID_BRANCH
    if metrics.get("static_factorization") is not True:
        return COUPLING_BRANCH
    if metrics.get("D_SC") == 0.0 and metrics.get("canonical_projection_equal") is True:
        return REMOVABLE_BRANCH
    return UNRESOLVED_BRANCH


def analyze(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    training = validate_training_artifacts(root)
    evaluation = validate_evaluation_artifacts(root)
    metrics = {
        "valid": bool(
            source.validate_static_certificate(training["static_certificate"])
            and source.validate_update_evidence(training["dynamic_equivalence"])
            and evaluation["passed"] is True
        ),
        "static_factorization": training["static_certificate"]["passed"],
        "D_SC": evaluation["D_SC"],
        "canonical_projection_equal": evaluation[
            "canonical_final_checkpoint_projection_equal"
        ],
    }
    branch = select_g49_result_branch(metrics)
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_commit": training["source_commit"],
        "formal": training["formal"],
        "formal_statistical_run": False,
        "scientific_iteration_cost": 0,
        "metrics": metrics,
        "first_match_priority": [
            INVALID_BRANCH,
            COUPLING_BRANCH,
            REMOVABLE_BRANCH,
            UNRESOLVED_BRANCH,
        ],
        "result_branch": branch,
        "claim_ceiling": (
            "structural_removability_of_duplicate_immediate_package_inside_exact_G48_route_only"
        ),
        "passed": branch == REMOVABLE_BRANCH,
    }
    if result["passed"] is not True:
        raise RuntimeError(f"G49 exact collapse unresolved: {branch}")
    _write_json(root / ANALYSIS_RESULT, result)
    return result


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
        or value.get("formal_statistical_run") is not False
        or value.get("scientific_iteration_cost") != 0
        or not isinstance(metrics, Mapping)
        or value.get("result_branch") != select_g49_result_branch(metrics)
        or value.get("result_branch") != REMOVABLE_BRANCH
        or value.get("passed") is not True
        or evaluation.get("D_SC") != metrics.get("D_SC")
    ):
        raise ValueError("G49 analysis artifact invariant mismatch")
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
        _execution_readiness_proof=True,
    )
    if row.get("return_schema") != "G49_train_manifest_v1":
        raise RuntimeError("G49 production-entry smoke schema mismatch")
    return row


def readiness_train(
    *, run_root: Path, source_commit: str, accepted_anchor_root: Path
) -> dict[str, object]:
    root = Path(run_root).resolve()
    manifest = train(
        run_root=root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        accepted_anchor_root=accepted_anchor_root,
        cpu_budget=DEFAULT_CPU_BUDGET,
        process_workers=DEFAULT_PROCESS_WORKERS,
        _execution_readiness_proof=True,
    )
    report = prove_two_process_equivalence(
        proof_root=root / "parallel_proof",
        accepted_anchor_root=accepted_anchor_root,
        trajectory_path=root / SHARED_TRAJECTORY_REFERENCE,
    )
    manifest["two_process_equivalence"] = report
    manifest["two_process_equivalence_artifact"] = TWO_PROCESS_REPORT_REFERENCE
    _write_json(root / TRAIN_MANIFEST, manifest)
    validate_training_artifacts(root, expected_source_commit=source_commit)
    return manifest


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
    if not source.validate_checkpoint_pair(checkpoints):
        raise RuntimeError("G49 artifact reload failed")
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
    train(
        run_root=run_root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        accepted_anchor_root=accepted_anchor_root,
    )
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


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
        raise ValueError("G49 entry requires source commit and accepted anchor root")
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
