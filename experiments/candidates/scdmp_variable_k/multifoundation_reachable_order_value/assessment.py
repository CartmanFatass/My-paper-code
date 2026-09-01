"""Create-once A/RECON performance assessment for the real B01 data path."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import shutil
import time
from typing import Callable, Mapping, Sequence

import torch

from .orchestration import (
    AttemptError,
    WORKER_TOPOLOGY,
    atomic_create_bytes,
    atomic_create_json,
)
from .contracts import RESOURCE_CAPS
from .preflight import PreflightReceipt, admission_receipt_passed, preflight_run
from .resources import (
    ContinuousResourceMonitor, ResourceLimits, ResourceTelemetry, foreground_io_snapshot,
    tree_bytes,
)
from .rng import CounterRNG
from .foundation import materialize_foundation
from .training import ExactAdamW
from .source_identity import validate_source_identity_gate, write_source_identity_gate
from .quarantine import raise_after_quarantine, validate_quarantine_lock, write_no_polarity_terminal
from .active_gate import ActiveInvocationGate
from .technical_checkpoint import (
    cold_validate_technical_checkpoint_grid, inventory_technical_checkpoint_grid,
    write_technical_checkpoint_grid,
)
from .workload import (
    evaluate_foundation_missions,
    execute_representative_twin_work,
    execute_training_update,
)


ASSESS_SCHEMA = "SCDMP_MF_RS_MK_B01_A_RECON_V1"
ASSESS_ID = "SCDMP-MF-RS-MK-B01-A-RECON"
ASSESS_COUNTS = {
    "training_updates": 1,
    "optimizer_steps": 12,
    "training_missions": 12,
    "evaluator_missions": 32,
    "source_missions": 1,
    "development_missions": 36,
    "heldout_missions": 6,
    "allocated_primitive_slots": 87 * 364,
    "technical_checkpoint_files": 322,
}
FULL_STAGE_MISSIONS = {
    "foundation_training": 3_840,
    "foundation_evaluator": 832,
    "source_scan": 48,
    "development": 3_456,
    "heldout": 1_152,
    "checkpoint_serialize": 322,
    "checkpoint_cold_validate": 322,
    "checkpoint_inventory": 322,
    "publication_preview": 1,
}
PROJECTION_SAFETY_FACTOR = 2.0
PROJECTION_FIXED_OVERHEAD_SECONDS = 60.0


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _tree_bytes(path: Path) -> int:
    return tree_bytes(path)


@dataclass(frozen=True, slots=True)
class AssessAttempt:
    root: Path
    admission: PreflightReceipt
    frozen_argv: tuple[str, ...]
    frozen_cwd: Path


def _manifest(root: Path, argv: tuple[str, ...], cwd: Path) -> dict[str, object]:
    return {
        "schema": ASSESS_SCHEMA,
        "assessment_id": ASSESS_ID,
        "resolved_assess_root": str(root),
        "frozen_argv": list(argv),
        "frozen_cwd": str(cwd),
        "resource_caps": asdict(ResourceLimits()),
        "worker_topology": dict(WORKER_TOPOLOGY),
        "representative_work": dict(ASSESS_COUNTS),
        "science_exclusions": [
            "RUN-01 result root",
            "RUN-01 master",
            "RUN-01 q draw",
            "RUN-01 raw returns",
            "RUN-01 ordered branch",
        ],
    }


def prepare_assess_attempt(
    *,
    assess_root: str | Path,
    admission_receipt: str | Path,
    command_runner: Callable[..., object],
    argv: Sequence[str],
    cwd: str | Path,
) -> AssessAttempt:
    """Admit memory before creating the non-scientific A/RECON root."""

    root = Path(assess_root).resolve(strict=False)
    receipt = Path(admission_receipt).resolve(strict=False)
    resolved_cwd = Path(cwd).resolve(strict=True)
    exact_argv = tuple(argv)
    if not exact_argv or not all(isinstance(item, str) and item for item in exact_argv):
        raise AttemptError("A/RECON exact argv is required")
    try:
        receipt.relative_to(root)
    except ValueError:
        pass
    else:
        raise AttemptError("fresh A/RECON admission receipt must precede its root")
    admission = preflight_run(receipt, command_runner=command_runner)
    if root.exists():
        validate_source_identity_gate(root / "source-identity.json")
        raise AttemptError("A/RECON root is create-once")
    source_gate = receipt.with_name(receipt.name + ".source-identity.json")
    write_source_identity_gate(source_gate)
    staging = root.with_name(f".{root.name}.initializing")
    if staging.exists():
        raise AttemptError("incomplete A/RECON initialization requires quarantine")
    staging.mkdir(parents=True, exist_ok=False)
    atomic_create_json(staging / "manifest.json", _manifest(root, exact_argv, resolved_cwd))
    shutil.move(str(source_gate), staging / "source-identity.json")
    admissions = staging / "admissions"
    admissions.mkdir()
    shutil.move(str(receipt), admissions / "invocation-000000.json")
    if root.exists():
        raise AttemptError("A/RECON root appeared during create-once initialization")
    staging.rename(root)
    return AssessAttempt(root, admission, exact_argv, resolved_cwd)


def finalize_assess_success(
    root: str | Path,
    *,
    telemetry: ResourceTelemetry,
    counts: Mapping[str, int],
    stage_observations: Mapping[str, Mapping[str, float | int]],
    scratch_root: str | Path | None = None,
    final_committer: Callable[[Path, Path], None] = os.rename,
) -> Path:
    result_root = Path(root)
    if (result_root / "assessment.json").exists():
        raise AttemptError("A/RECON assessment is create-only")
    if (result_root / "terminal-no-polarity.json").exists() or validate_quarantine_lock(
        result_root, mode="A/RECON"
    ):
        raise AttemptError("quarantined A/RECON cannot publish readiness")
    if (
        not isinstance(telemetry, ResourceTelemetry)
        or not telemetry.passed
        or dict(counts) != ASSESS_COUNTS
        or set(stage_observations) != set(FULL_STAGE_MISSIONS)
    ):
        raise AttemptError("A/RECON publication requires passing complete direct telemetry")
    stage_projection = {}
    projected_work_seconds = 0.0
    for stage, full_missions in FULL_STAGE_MISSIONS.items():
        row = stage_observations[stage]
        measured = row.get("measured_missions")
        wall = row.get("wall_seconds")
        if (
            isinstance(measured, bool) or not isinstance(measured, int) or measured <= 0
            or isinstance(wall, bool) or not isinstance(wall, (int, float))
            or not math.isfinite(float(wall)) or float(wall) <= 0.0
        ):
            raise AttemptError("A/RECON stage observation is not direct positive work")
        throughput = measured / float(wall)
        projected = float(wall) * (full_missions / measured) * PROJECTION_SAFETY_FACTOR
        projected_work_seconds += projected
        stage_projection[stage] = {
            "measured_missions": measured,
            "measured_wall_seconds": float(wall),
            "measured_missions_per_second": throughput,
            "fixed_full_missions": full_missions,
            "linear_scale_ratio": full_missions / measured,
            "safety_factor": PROJECTION_SAFETY_FACTOR,
            "conservative_projected_seconds": projected,
            "measured_io_read_bytes": int(row.get("io_read_bytes", 0)),
            "measured_io_write_bytes": int(row.get("io_write_bytes", 0)),
        }
    projected_total = projected_work_seconds + PROJECTION_FIXED_OVERHEAD_SECONDS
    telemetry_path = result_root / "telemetry.json"
    path = result_root / "assessment.json"
    assessment = {
        "schema": ASSESS_SCHEMA,
        "assessment_id": ASSESS_ID,
        "status": "PERFORMANCE_OBSERVATION_COMPLETE",
        "performance_readiness": "REVIEW_REQUIRED",
        "counts": dict(counts),
        "stage_coverage": stage_projection,
        "projection": {
            "formula": "sum(measured_stage_wall * fixed_full_missions / measured_missions * 2.0) + 60.0",
            "assumptions": [
                "representative stage throughput remains no worse than half the observed rate",
                "fixed artifact, resume, and publication overhead fits within 60 seconds",
                "measured process-tree RSS and storage high waters remain bounded under streamed full work",
                "projection is reviewer evidence and is not a RUN-01 admission or pass decision",
            ],
            "projected_work_seconds": projected_work_seconds,
            "fixed_overhead_seconds": PROJECTION_FIXED_OVERHEAD_SECONDS,
            "conservative_projected_total_seconds": projected_total,
            "margin_to_1800_seconds": 1_800.0 - projected_total,
        },
        "telemetry_file": telemetry_path.name,
        "scientific_polarity": None,
        "ordered_branch": None,
    }
    prepublication = _tree_bytes(result_root)
    accounting: dict[str, object] = {}
    telemetry_value: dict[str, object] = {}
    telemetry_bytes = b""
    assessment_bytes = b""
    for _ in range(12):
        telemetry_value = {
            "schema": "SCDMP_MF_RS_MK_B01_A_RESOURCE_V1",
            "telemetry": asdict(telemetry),
            "final_tail_accounting": accounting,
        }
        assessment["final_tail_accounting"] = accounting
        telemetry_bytes = _canonical_bytes(telemetry_value)
        assessment_bytes = _canonical_bytes(assessment)
        next_accounting = {
            "prepublication_durable_bytes": prepublication,
            "telemetry_exact_bytes": len(telemetry_bytes),
            "assessment_exact_bytes": len(assessment_bytes),
            "exact_tail_bytes": len(telemetry_bytes) + len(assessment_bytes),
            "predicted_final_durable_bytes": prepublication + len(telemetry_bytes) + len(assessment_bytes),
            "durable_cap_bytes": RESOURCE_CAPS["durable_bytes"],
        }
        if next_accounting == accounting:
            break
        accounting = next_accounting
    else:
        raise AttemptError("A/RECON final-tail byte accounting did not converge")
    predicted = prepublication + len(telemetry_bytes) + len(assessment_bytes)
    if predicted != accounting["predicted_final_durable_bytes"]:
        raise AttemptError("A/RECON final-tail byte accounting differs")
    if predicted > RESOURCE_CAPS["durable_bytes"]:
        raise AttemptError("A/RECON predicted final durable output exceeds 256 MiB")
    scratch_base = (
        Path(scratch_root) if scratch_root is not None
        else result_root.with_name(f".{result_root.name}.assessment-tail-scratch")
    )
    staged = scratch_base / "assessment-final-tail"
    staged.mkdir(parents=True, exist_ok=False)
    staged_telemetry = staged / "telemetry.json"
    staged_assessment = staged / "assessment.json"
    atomic_create_bytes(staged_telemetry, telemetry_bytes)
    atomic_create_bytes(staged_assessment, assessment_bytes)
    if (
        staged_telemetry.read_bytes() != telemetry_bytes
        or staged_assessment.read_bytes() != assessment_bytes
        or _tree_bytes(scratch_base) > RESOURCE_CAPS["scratch_bytes"]
    ):
        raise AttemptError("A/RECON staged final-tail bytes or scratch cap differ")
    os.rename(staged_telemetry, telemetry_path)
    if telemetry_path.read_bytes() != telemetry_bytes:
        raise AttemptError("A/RECON telemetry direct bytes differ before commit")
    if _tree_bytes(result_root) + len(assessment_bytes) != predicted:
        raise AttemptError("A/RECON precommit durable size differs from exact prediction")
    # Unique final commit point: the fsynced/verified staged payload is moved
    # into its create-only coordinate and no cleanup/read/assert follows.
    final_committer(staged_assessment, path)
    return path


def run_assess(
    *,
    assess_root: str | Path,
    admission_receipt: str | Path,
    command_runner: Callable[..., object],
    argv: Sequence[str],
    cwd: str | Path,
    monitor_factory: Callable[..., ContinuousResourceMonitor] = ContinuousResourceMonitor,
) -> Path:
    """Execute one real scaled native/PPO/evaluator performance observation."""

    requested_root = Path(assess_root).resolve(strict=False)
    staging = requested_root.with_name(f".{requested_root.name}.initializing")
    source_gate = Path(admission_receipt).resolve(strict=False).with_name(
        Path(admission_receipt).name + ".source-identity.json"
    )
    attempt: AssessAttempt | None = None
    monitor: ContinuousResourceMonitor | None = None
    active_gate = ActiveInvocationGate(requested_root, mode="A/RECON")
    active_gate.acquire()
    telemetry: ResourceTelemetry | None = None
    stage = "admission-and-source-identity"
    try:
        attempt = prepare_assess_attempt(
            assess_root=requested_root,
            admission_receipt=admission_receipt,
            command_runner=command_runner,
            argv=argv,
            cwd=cwd,
        )
        stage = "scratch-and-monitor-initialization"
        scratch = attempt.root.with_name(f".{attempt.root.name}.scratch")
        scratch.mkdir(exist_ok=False)
        monitor = monitor_factory(
            scratch_root=scratch,
            durable_root=attempt.root,
            limits=ResourceLimits(),
        )
        stage = "real-native-training"
        torch.set_num_threads(1)
        source = CounterRNG(1709)
        model = materialize_foundation(source)
        optimizer = ExactAdamW(tuple(model.named_parameters()))
        stage_started = time.perf_counter()
        training = execute_training_update(model, optimizer, source, update=1)
        training_wall = time.perf_counter() - stage_started
        stage = "real-native-evaluator"
        stage_started = time.perf_counter()
        endpoints = evaluate_foundation_missions(
            model, source, stage="CURVE", update=1, missions_per_cell=8,
        )
        evaluator_wall = time.perf_counter() - stage_started
        stage = "real-native-source-development-heldout"
        twin_work = execute_representative_twin_work(model, source)
        second_source = CounterRNG(2903)
        second_model = materialize_foundation(second_source)
        second_optimizer = ExactAdamW(tuple(second_model.named_parameters()))
        checkpoint_root = attempt.root / "technical-checkpoints"
        source_identity_path = attempt.root / "source-identity.json"

        stage = "technical-checkpoint-serialize"
        io_start = foreground_io_snapshot()
        stage_started = time.perf_counter()
        technical_paths = write_technical_checkpoint_grid(
            checkpoint_root,
            models={1709: model, 2903: second_model},
            optimizers={1709: optimizer, 2903: second_optimizer},
            source_identity_path=source_identity_path,
            scratch_observer=monitor.observe_scratch_path,
        )
        serialize_wall = time.perf_counter() - stage_started
        io_end = foreground_io_snapshot()
        serialize_io = {
            "io_read_bytes": max(0, io_end["foreground_io_read_bytes"] - io_start["foreground_io_read_bytes"]),
            "io_write_bytes": max(0, io_end["foreground_io_write_bytes"] - io_start["foreground_io_write_bytes"]),
        }

        stage = "technical-checkpoint-cold-validate"
        io_start = foreground_io_snapshot()
        stage_started = time.perf_counter()
        cold_validate_technical_checkpoint_grid(
            technical_paths, source_identity_path=source_identity_path,
        )
        cold_wall = time.perf_counter() - stage_started
        io_end = foreground_io_snapshot()
        cold_io = {
            "io_read_bytes": max(0, io_end["foreground_io_read_bytes"] - io_start["foreground_io_read_bytes"]),
            "io_write_bytes": max(0, io_end["foreground_io_write_bytes"] - io_start["foreground_io_write_bytes"]),
        }

        stage = "technical-checkpoint-inventory"
        io_start = foreground_io_snapshot()
        stage_started = time.perf_counter()
        technical_inventory = inventory_technical_checkpoint_grid(technical_paths)
        inventory_wall = time.perf_counter() - stage_started
        io_end = foreground_io_snapshot()
        inventory_io = {
            "io_read_bytes": max(0, io_end["foreground_io_read_bytes"] - io_start["foreground_io_read_bytes"]),
            "io_write_bytes": max(0, io_end["foreground_io_write_bytes"] - io_start["foreground_io_write_bytes"]),
        }

        stage = "technical-publication-preview"
        io_start = foreground_io_snapshot()
        stage_started = time.perf_counter()
        atomic_create_json(attempt.root / "technical-publication-preview.json", {
            "schema": ASSESS_SCHEMA,
            "source_identity_file": "source-identity.json",
            "checkpoint_files": len(technical_inventory),
            "checkpoint_direct_bytes": sum(int(row["direct_size_bytes"]) for row in technical_inventory),
            "inventory": list(technical_inventory),
            "scientific_polarity": None,
            "ordered_branch": None,
        }, scratch_observer=monitor.observe_scratch_path)
        publication_wall = time.perf_counter() - stage_started
        io_end = foreground_io_snapshot()
        publication_io = {
            "io_read_bytes": max(0, io_end["foreground_io_read_bytes"] - io_start["foreground_io_read_bytes"]),
            "io_write_bytes": max(0, io_end["foreground_io_write_bytes"] - io_start["foreground_io_write_bytes"]),
        }
        counts = {
            "training_updates": 1,
            "optimizer_steps": training.receipt.optimizer_step,
            "training_missions": training.missions,
            "evaluator_missions": len(endpoints),
            "source_missions": twin_work.source_missions,
            "development_missions": twin_work.development_missions,
            "heldout_missions": twin_work.heldout_missions,
            "allocated_primitive_slots": (
                training.allocated_slots + len(endpoints) * 364 + twin_work.allocated_slots
            ),
            "technical_checkpoint_files": len(technical_paths),
        }
        stage_observations = {
            "foundation_training": {"measured_missions": training.missions, "wall_seconds": training_wall},
            "foundation_evaluator": {"measured_missions": len(endpoints), "wall_seconds": evaluator_wall},
            "source_scan": {
                "measured_missions": twin_work.source_missions,
                "wall_seconds": twin_work.source_wall_seconds,
            },
            "development": {
                "measured_missions": twin_work.development_missions,
                "wall_seconds": twin_work.development_wall_seconds,
            },
            "heldout": {
                "measured_missions": twin_work.heldout_missions,
                "wall_seconds": twin_work.heldout_wall_seconds,
            },
            "checkpoint_serialize": {
                "measured_missions": len(technical_paths), "wall_seconds": serialize_wall,
                **serialize_io,
            },
            "checkpoint_cold_validate": {
                "measured_missions": len(technical_paths), "wall_seconds": cold_wall,
                **cold_io,
            },
            "checkpoint_inventory": {
                "measured_missions": len(technical_inventory), "wall_seconds": inventory_wall,
                **inventory_io,
            },
            "publication_preview": {
                "measured_missions": 1, "wall_seconds": publication_wall,
                **publication_io,
            },
        }
        atomic_create_json(attempt.root / "stage-coverage.json", {
            "schema": ASSESS_SCHEMA,
            "counts": counts,
            "stage_observations": stage_observations,
            "native_transitions": training.transitions + sum(row.transitions for row in endpoints)
            + twin_work.transitions,
            "policy_queries": training.policy_queries + sum(row.policy_queries for row in endpoints)
            + twin_work.policy_queries,
            "scientific_polarity": None,
            "ordered_branch": None,
        }, scratch_observer=monitor.observe_scratch_path)
        telemetry = monitor.finalize(exit_status=0)
        stage = "telemetry-publication"
        active_gate.assert_owner()
        active_gate.retain_until_process_exit()
        return finalize_assess_success(
            attempt.root, telemetry=telemetry, counts=counts,
            stage_observations=stage_observations, scratch_root=scratch,
        )
    except BaseException as error:
        if (
            isinstance(error, AttemptError)
            and str(error) == "A/RECON root is create-once"
            and (requested_root / "assessment.json").is_file()
        ):
            try:
                active_gate.release()
            except BaseException as gate_error:
                setattr(error, "active_gate_release_error", gate_error)
            raise
        if telemetry is None and monitor is not None:
            telemetry = monitor.finalize(exit_status=1)
        if requested_root.is_dir():
            quarantine_root = requested_root
        elif staging.exists():
            quarantine_root = staging
        elif source_gate.exists() or admission_receipt_passed(admission_receipt):
            quarantine_root = requested_root.with_name(f".{requested_root.name}.initialization-failure")
        else:
            # Admission refusal occurred before any source/result transaction.
            try:
                active_gate.release()
            except BaseException as gate_error:
                setattr(error, "active_gate_release_error", gate_error)
            raise
        try:
            try:
                active_binding = active_gate.binding()
            except BaseException as gate_error:
                setattr(error, "active_gate_ownership_error", gate_error)
                active_binding = None
            raise_after_quarantine(
                quarantine_root, mode="A/RECON", stage=stage, original=error, telemetry=telemetry,
                active_gate_binding=active_binding,
            )
        finally:
            try:
                if validate_quarantine_lock(quarantine_root, mode="A/RECON"):
                    active_gate.release()
            except BaseException as gate_error:
                setattr(error, "active_gate_release_error", gate_error)


__all__ = [
    "ASSESS_COUNTS", "ASSESS_ID", "ASSESS_SCHEMA", "AssessAttempt",
    "finalize_assess_success", "prepare_assess_attempt", "run_assess",
    "raise_after_quarantine", "write_no_polarity_terminal",
]
