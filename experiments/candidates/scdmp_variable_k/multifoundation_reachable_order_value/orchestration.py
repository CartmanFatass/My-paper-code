"""Create-once RUN-01 identity, resume, workload, and publication orchestration.

This module owns the production control seam for the isolated B01 package.  It
does not import the consumed FCEOV implementation and it never launches work
at import time.
"""

from __future__ import annotations

from dataclasses import dataclass
import base64
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import tempfile
from typing import Callable, Mapping, Sequence

import torch
from torch import Tensor

from .contracts import Q_COUNTER_ADDRESS, RunManifest, WORKLOADS, build_run_manifest
from .foundation import FoundationActorCritic, materialize_foundation
from .preflight import PreflightReceipt, preflight_run
from .rng import CounterRNG
from .source_identity import validate_source_identity_gate, write_source_identity_gate
from .quarantine import raise_after_quarantine, validate_quarantine_lock
from .training import ExactAdamW, UpdateReceipt


ATTEMPT_SCHEMA = "SCDMP_MF_RS_MK_B01_ATTEMPT_V1"
WORKER_TOPOLOGY = {
    "foreground_processes": 1,
    "telemetry_threads": 1,
    "torch_intraop_threads": 1,
    "native_training_batch_width": 12,
    "native_evaluator_batch_width": 32,
    "native_twin_batch_width": 2,
}
CHECKPOINT_SCHEMA = "SCDMP_MF_RS_MK_B01_FOUNDATION_CHECKPOINT_V1"


@dataclass(frozen=True, slots=True)
class WorkObservation:
    missions: int
    allocated_slots: int
    transitions: int
    policy_queries: int
    optimizer_steps: int
    evaluator_calls: int


class WorkLedger:
    """Typed declared/actual ledger; source scanning retains its 48-slot ceiling."""

    _EXPECTED_MISSIONS = {
        "foundation_training": 3_840,
        "fixed_learning_curves": 576,
        "final_competence": 256,
        "development": 3_456,
        "heldout": 1_152,
    }

    def __init__(self) -> None:
        self._rows: dict[str, WorkObservation] = {}

    @property
    def rows(self) -> tuple[tuple[str, WorkObservation], ...]:
        return tuple(self._rows.items())

    def record(
        self,
        stage: str,
        *,
        missions: int,
        allocated_slots: int,
        transitions: int,
        policy_queries: int,
        optimizer_steps: int,
        evaluator_calls: int,
    ) -> None:
        values = (
            missions, allocated_slots, transitions, policy_queries, optimizer_steps,
            evaluator_calls,
        )
        if (
            stage not in {*self._EXPECTED_MISSIONS, "reachable_state_source_scans"}
            or stage in self._rows
            or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values)
        ):
            raise AttemptError("work ledger stage or nonnegative count differs")
        self._rows[stage] = WorkObservation(*values)

    def reconcile_for_publication(self, *, source_states: int, ppo_updates: int) -> dict[str, int]:
        required = {*self._EXPECTED_MISSIONS, "reachable_state_source_scans"}
        source = self._rows.get("reachable_state_source_scans")
        fixed_ok = all(
            self._rows.get(name) is not None and self._rows[name].missions == expected
            for name, expected in self._EXPECTED_MISSIONS.items()
        )
        allocated = sum(row.allocated_slots for row in self._rows.values())
        optimizer_steps = sum(row.optimizer_steps for row in self._rows.values())
        if (
            set(self._rows) != required
            or not fixed_ok
            or source is None
            or not 6 <= source.missions <= WORKLOADS["reachable_state_source_scans"]
            or source.allocated_slots != WORKLOADS["reachable_state_source_scans"] * 364
            or source_states != 6
            or ppo_updates != WORKLOADS["ppo_updates"]
            or optimizer_steps != WORKLOADS["adamw_steps"]
            or allocated != WORKLOADS["allocated_primitive_slots"]
        ):
            raise AttemptError("complete RUN-01 count reconciliation failed")
        actual = sum(row.missions for row in self._rows.values())
        return {
            "declared_total_missions": WORKLOADS["total_missions_rollouts"],
            "actual_executed_missions": actual,
            "source_scan_ceiling_unexecuted": WORKLOADS["reachable_state_source_scans"] - source.missions,
            "allocated_primitive_slots": allocated,
            "actual_transitions": sum(row.transitions for row in self._rows.values()),
            "policy_queries": sum(row.policy_queries for row in self._rows.values()),
            "optimizer_steps": optimizer_steps,
            "ppo_updates": ppo_updates,
            "native_evaluator_calls": sum(row.evaluator_calls for row in self._rows.values()),
        }

    def reconcile_for_branch(
        self, *, branch: str, source_states: int, ppo_updates: int,
    ) -> dict[str, int | str]:
        stage_order = (
            "foundation_training", "fixed_learning_curves", "final_competence",
            "reachable_state_source_scans", "development", "heldout",
        )
        branch_frontier = {
            "FOUNDATION_COMPETENCE_NOT_ESTABLISHED": 3,
            "REACHABLE_STATE_PANEL_NOT_ESTABLISHED": 4,
            "ACTION_CONSTRUCTION_NONDISCRIMINATING": 5,
            "PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL": 6,
            "GENERIC_ACTION_OR_RECOVERY_EXPLANATION": 6,
            "ORDER_ASSOCIATION_NOT_OBSERVED_IN_RUN_01": 6,
            "FOUNDATION_STATE_OR_SELECTOR_HETEROGENEITY": 6,
        }
        frontier = branch_frontier.get(branch)
        expected_stages = set(stage_order[:frontier]) if frontier is not None else set()
        source = self._rows.get("reachable_state_source_scans")
        fixed_expected = {
            "foundation_training": 3_840,
            "fixed_learning_curves": 576,
            "final_competence": 256,
            "development": 3_456,
            "heldout": 1_152,
        }
        allocated_expected = {
            "foundation_training": 3_840 * 364,
            "fixed_learning_curves": 576 * 364,
            "final_competence": 256 * 364,
            "reachable_state_source_scans": 48 * 364,
            "development": 3_456 * 364,
            "heldout": 1_152 * 364,
        }
        if (
            frontier is None
            or set(self._rows) != expected_stages
            or ppo_updates != 320
            or sum(row.optimizer_steps for row in self._rows.values()) != 3_840
            or any(
                self._rows[name].missions != expected
                for name, expected in fixed_expected.items() if name in expected_stages
            )
            or any(
                self._rows[name].allocated_slots != allocated_expected[name]
                for name in expected_stages
            )
            or (
                "reachable_state_source_scans" in expected_stages and (
                    source is None or not 1 <= source.missions <= 48
                    or not 0 <= source_states <= 6
                )
            )
            or (
                "reachable_state_source_scans" not in expected_stages and source_states != 0
            )
            or (frontier >= 5 and source_states != 6)
        ):
            raise AttemptError("branch-specific RUN-01 count reconciliation failed")
        actual = sum(row.missions for row in self._rows.values())
        return {
            "branch": branch,
            "declared_total_missions": WORKLOADS["total_missions_rollouts"],
            "actual_executed_missions": actual,
            "declared_not_executed_missions": WORKLOADS["total_missions_rollouts"] - actual,
            "allocated_primitive_slots": sum(row.allocated_slots for row in self._rows.values()),
            "actual_transitions": sum(row.transitions for row in self._rows.values()),
            "policy_queries": sum(row.policy_queries for row in self._rows.values()),
            "optimizer_steps": 3_840,
            "ppo_updates": 320,
            "source_states_established": source_states,
            "native_evaluator_calls": sum(row.evaluator_calls for row in self._rows.values()),
        }


class AttemptError(RuntimeError):
    """The requested operation is not a legal continuation of this run."""


@dataclass(frozen=True, slots=True)
class Attempt:
    root: Path
    fresh: bool
    run_manifest: RunManifest
    admission: PreflightReceipt
    invocation_index: int
    frozen_argv: tuple[str, ...]
    frozen_cwd: Path


def _tensor_value(name: str, value: Tensor) -> dict[str, object]:
    if (
        not isinstance(name, str) or not name
        or not isinstance(value, Tensor)
        or value.dtype != torch.float32
        or not bool(torch.isfinite(value).all())
    ):
        raise AttemptError("checkpoint tensors must be named finite float32 values")
    direct = value.detach().cpu().contiguous().numpy().tobytes()
    return {
        "name": name,
        "dtype": "torch.float32",
        "shape": list(value.shape),
        "length_bytes": len(direct),
        "direct_bytes_b64": base64.b64encode(direct).decode("ascii"),
    }


def _decode_tensor(value: object, *, expected_name: str, expected_shape: tuple[int, ...]) -> Tensor:
    if not isinstance(value, dict) or set(value) != {
        "name", "dtype", "shape", "length_bytes", "direct_bytes_b64",
    }:
        raise AttemptError("checkpoint tensor fields differ")
    encoded = value.get("direct_bytes_b64")
    try:
        direct = base64.b64decode(str(encoded).encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as error:
        raise AttemptError("checkpoint tensor direct bytes cannot be decoded") from error
    expected_bytes = torch.empty(expected_shape, dtype=torch.float32).numel() * 4
    if (
        value.get("name") != expected_name
        or value.get("dtype") != "torch.float32"
        or value.get("shape") != list(expected_shape)
        or value.get("length_bytes") != len(direct)
        or len(direct) != expected_bytes
        or base64.b64encode(direct).decode("ascii") != encoded
    ):
        raise AttemptError("checkpoint tensor identity, shape, or direct length differs")
    tensor = torch.frombuffer(bytearray(direct), dtype=torch.float32).clone().reshape(expected_shape)
    if not bool(torch.isfinite(tensor).all()):
        raise AttemptError("checkpoint tensor is nonfinite")
    return tensor


def write_foundation_checkpoint(
    path: str | Path,
    *,
    model: FoundationActorCritic,
    optimizer: ExactAdamW,
    update: int,
    run_manifest: RunManifest,
    training_receipt: UpdateReceipt | None = None,
    scratch_observer: Callable[[Path], None] | None = None,
) -> None:
    """Persist full model parameters and AdamW moments at one legal frontier."""

    if (
        not isinstance(model, FoundationActorCritic)
        or not isinstance(optimizer, ExactAdamW)
        or not optimizer.matches(tuple(model.named_parameters()))
        or isinstance(update, bool) or not isinstance(update, int) or not 0 <= update <= 160
        or optimizer.step_index != update * 12
        or not isinstance(run_manifest, RunManifest)
        or (update == 0 and training_receipt is not None)
        or (
            update > 0 and (
                not isinstance(training_receipt, UpdateReceipt)
                or training_receipt.update != update
                or training_receipt.episodes_complete != 12
                or training_receipt.optimizer_step != optimizer.step_index
            )
        )
    ):
        raise AttemptError("foundation checkpoint frontier differs from RUN-01")
    run_manifest.validate()
    parameters = tuple(model.named_parameters())
    payload = {
        "schema": CHECKPOINT_SCHEMA,
        "run_binding": run_manifest.to_dict(),
        "seed": model.foundation_seed,
        "update": update,
        "optimizer_step": optimizer.step_index,
        "training_receipt": None if training_receipt is None else {
            "update": training_receipt.update,
            "episodes_complete": training_receipt.episodes_complete,
            "records": training_receipt.records,
            "transitions": training_receipt.transitions,
            "optimizer_step": training_receipt.optimizer_step,
            "mean_loss": training_receipt.mean_loss,
        },
        "parameters": [_tensor_value(name, value) for name, value in parameters],
        "optimizer_names": list(optimizer.names),
        "optimizer_first": [
            _tensor_value(name, value) for name, value in zip(optimizer.names, optimizer.first)
        ],
        "optimizer_second": [
            _tensor_value(name, value) for name, value in zip(optimizer.names, optimizer.second)
        ],
    }
    atomic_create_json(path, payload, scratch_observer=scratch_observer)


def load_foundation_checkpoint(
    path: str | Path,
    *,
    expected_seed: int,
    run_manifest: RunManifest,
) -> tuple[FoundationActorCritic, ExactAdamW]:
    """Restore a seed-bound checkpoint after validating all direct tensors."""

    run_manifest.validate()
    value = _read_canonical_json(Path(path))
    required = {
        "schema", "run_binding", "seed", "update", "optimizer_step", "training_receipt", "parameters",
        "optimizer_names", "optimizer_first", "optimizer_second",
    }
    update = value.get("update")
    if (
        set(value) != required
        or value.get("schema") != CHECKPOINT_SCHEMA
        or value.get("run_binding") != run_manifest.to_dict()
        or value.get("seed") != expected_seed
        or isinstance(update, bool) or not isinstance(update, int) or not 0 <= update <= 160
        or value.get("optimizer_step") != update * 12
        or (
            update == 0 and value.get("training_receipt") is not None
        )
        or (
            update > 0 and not _valid_training_receipt(value.get("training_receipt"), update)
        )
    ):
        raise AttemptError("foundation checkpoint run, seed, or frontier binding differs")
    model = materialize_foundation(CounterRNG(expected_seed))
    optimizer = ExactAdamW(tuple(model.named_parameters()))
    parameter_rows = value.get("parameters")
    first_rows = value.get("optimizer_first")
    second_rows = value.get("optimizer_second")
    if (
        not isinstance(parameter_rows, list)
        or not isinstance(first_rows, list)
        or not isinstance(second_rows, list)
        or value.get("optimizer_names") != list(optimizer.names)
        or not (len(parameter_rows) == len(first_rows) == len(second_rows) == len(optimizer.names))
    ):
        raise AttemptError("foundation checkpoint tensor inventory differs")
    with torch.no_grad():
        for (name, target), row in zip(model.named_parameters(), parameter_rows):
            target.copy_(_decode_tensor(row, expected_name=name, expected_shape=tuple(target.shape)))
        for name, target, row in zip(optimizer.names, optimizer.first, first_rows):
            target.copy_(_decode_tensor(row, expected_name=name, expected_shape=tuple(target.shape)))
        for name, target, row in zip(optimizer.names, optimizer.second, second_rows):
            decoded = _decode_tensor(row, expected_name=name, expected_shape=tuple(target.shape))
            if bool(torch.any(decoded < 0)):
                raise AttemptError("AdamW second moment is negative")
            target.copy_(decoded)
    optimizer.step_index = int(value["optimizer_step"])
    return model, optimizer


def _valid_training_receipt(value: object, update: int) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "update", "episodes_complete", "records", "transitions", "optimizer_step", "mean_loss",
    }:
        return False
    mean_loss = value.get("mean_loss")
    return (
        value.get("update") == update
        and value.get("episodes_complete") == 12
        and isinstance(value.get("records"), int) and not isinstance(value.get("records"), bool)
        and value["records"] > 0
        and isinstance(value.get("transitions"), int) and not isinstance(value.get("transitions"), bool)
        and value["transitions"] > 0
        and value.get("optimizer_step") == update * 12
        and isinstance(mean_loss, (int, float)) and not isinstance(mean_loss, bool)
        and math.isfinite(float(mean_loss))
    )


def load_checkpoint_training_receipt(path: str | Path) -> dict[str, object] | None:
    value = _read_canonical_json(Path(path))
    update = value.get("update")
    receipt = value.get("training_receipt")
    if update == 0 and receipt is None:
        return None
    if not isinstance(update, int) or not _valid_training_receipt(receipt, update):
        raise AttemptError("checkpoint training receipt differs")
    assert isinstance(receipt, dict)
    return dict(receipt)


def _canonical_json(value: Mapping[str, object]) -> bytes:
    try:
        return (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise AttemptError("attempt artifact is not finite canonical JSON") from error


def atomic_create_bytes(
    path: str | Path,
    payload: bytes,
    *,
    scratch_observer: Callable[[Path], None] | None = None,
) -> None:
    """Create one durable file without an overwrite window."""

    destination = Path(path)
    if not isinstance(payload, bytes):
        raise TypeError("atomic artifact payload must be bytes")
    if destination.exists():
        raise AttemptError(f"create-only artifact already exists: {destination.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if scratch_observer is not None:
            scratch_observer(temporary)
        os.link(temporary, destination)
    except FileExistsError as error:
        raise AttemptError(f"create-only artifact already exists: {destination.name}") from error
    finally:
        temporary.unlink(missing_ok=True)


def atomic_create_json(
    path: str | Path,
    value: Mapping[str, object],
    *,
    scratch_observer: Callable[[Path], None] | None = None,
) -> None:
    atomic_create_bytes(path, _canonical_json(value), scratch_observer=scratch_observer)


def _read_canonical_json(path: Path) -> dict[str, object]:
    try:
        encoded = path.read_bytes()
        value = json.loads(encoded.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AttemptError(f"attempt artifact is missing or unreadable: {path.name}") from error
    if not isinstance(value, dict) or encoded != _canonical_json(value):
        raise AttemptError(f"attempt artifact is not canonical direct JSON: {path.name}")
    return value


def _resolved_root(path: str | Path) -> Path:
    root = Path(path).resolve(strict=False)
    normalized = str(root).replace("\\", "/").lower()
    if "foundation_conditioned_event_order_value" in normalized or "2026-08-31." in normalized:
        raise AttemptError("old FCEOV coordinates are isolated from B01")
    return root


def _manifest_value(
    run_manifest: RunManifest,
    *,
    root: Path,
    argv: tuple[str, ...],
    cwd: Path,
) -> dict[str, object]:
    return {
        "schema": ATTEMPT_SCHEMA,
        "run_identity": run_manifest.static.schema,
        "resolved_result_root": str(root),
        "frozen_argv": list(argv),
        "frozen_cwd": str(cwd),
        "run_manifest": run_manifest.to_dict(),
        "worker_topology": dict(WORKER_TOPOLOGY),
    }


def _q_audit_value(run_manifest: RunManifest) -> dict[str, object]:
    return {
        "schema": "SCDMP_MF_RS_MK_B01_REALIZED_Q_AUDIT_V1",
        "run_binding": run_manifest.to_dict(),
        "counter_address": list(Q_COUNTER_ADDRESS),
        "q_counter_u64": run_manifest.q_counter_u64,
        "q_pattern_index": run_manifest.q_pattern_index,
        "q_by_cell": [
            {"cell": state.cell, "q_pre": run_manifest.q_by_cell[index]}
            for index, state in enumerate(run_manifest.static.states)
        ],
        "draw_count": 1,
        "redraw_allowed": False,
    }


def _invocation_value(
    *, index: int, argv: tuple[str, ...], cwd: Path, root: Path,
    resume: bool, admission_file: str,
) -> dict[str, object]:
    return {
        "schema": "SCDMP_MF_RS_MK_B01_INVOCATION_V1",
        "invocation_index": index,
        "exact_argv": list(argv),
        "exact_cwd": str(cwd),
        "resolved_result_root": str(root),
        "technical_resume": resume,
        "admission_file": admission_file,
    }


def _validate_manifest(root: Path, master: bytes) -> tuple[RunManifest, dict[str, object]]:
    if len(master) != 32:
        raise AttemptError("persisted RUN-01 master must contain exactly 32 bytes")
    run_manifest = build_run_manifest(master)
    value = _read_canonical_json(root / "manifest.json")
    required = {
        "schema", "run_identity", "resolved_result_root", "frozen_argv", "frozen_cwd",
        "run_manifest", "worker_topology",
    }
    if (
        set(value) != required
        or value.get("schema") != ATTEMPT_SCHEMA
        or value.get("run_identity") != run_manifest.static.schema
        or value.get("resolved_result_root") != str(root)
        or value.get("run_manifest") != run_manifest.to_dict()
        or value.get("worker_topology") != WORKER_TOPOLOGY
        or not isinstance(value.get("frozen_argv"), list)
        or not all(isinstance(item, str) for item in value["frozen_argv"])
        or not isinstance(value.get("frozen_cwd"), str)
    ):
        raise AttemptError("persisted manifest differs from the sealed RUN-01 identity")
    if _read_canonical_json(root / "realized-q-audit.json") != _q_audit_value(run_manifest):
        raise AttemptError("persisted realized-q audit differs from the sealed RUN-01 identity")
    validate_source_identity_gate(root / "source-identity.json")
    return run_manifest, value


def _fresh_attempt(
    *,
    root: Path,
    admission_receipt: Path,
    command_runner: Callable[..., object],
    master_source: Callable[[], bytes],
    argv: tuple[str, ...],
    cwd: Path,
) -> Attempt:
    if root.exists():
        raise AttemptError("existing RUN-01 root requires explicit technical resume")
    try:
        admission_receipt.resolve(strict=False).relative_to(root)
    except ValueError:
        pass
    else:
        raise AttemptError("fresh admission receipt must be outside the not-yet-created result root")
    admission = preflight_run(admission_receipt, command_runner=command_runner)
    source_gate = admission_receipt.with_name(admission_receipt.name + ".source-identity.json")
    write_source_identity_gate(source_gate)
    master = master_source()
    if not isinstance(master, bytes) or len(master) != 32:
        raise AttemptError("RUN-01 master source must return exactly 32 fresh bytes")
    run_manifest = build_run_manifest(master)
    staging = root.with_name(f".{root.name}.initializing")
    if staging.exists():
        raise AttemptError("incomplete initialization staging root requires quarantine")
    staging.mkdir(parents=True, exist_ok=False)
    try:
        atomic_create_bytes(staging / "run-master.bin", master)
        atomic_create_json(
            staging / "manifest.json",
            _manifest_value(run_manifest, root=root, argv=argv, cwd=cwd),
        )
        atomic_create_json(staging / "realized-q-audit.json", _q_audit_value(run_manifest))
        shutil.move(str(source_gate), staging / "source-identity.json")
        admissions = staging / "admissions"
        admissions.mkdir()
        shutil.move(str(admission_receipt), admissions / "invocation-000000.json")
        atomic_create_json(staging / "invocations" / "invocation-000000.json", _invocation_value(
            index=0, argv=argv, cwd=cwd, root=root, resume=False,
            admission_file="admissions/invocation-000000.json",
        ))
        if root.exists():
            raise AttemptError("RUN-01 root appeared during create-once initialization")
        staging.rename(root)
    except Exception:
        # A partially initialized staging directory is deliberately retained.
        # It contains no published result root and is not eligible for resume.
        raise
    persisted_master = (root / "run-master.bin").read_bytes()
    observed, value = _validate_manifest(root, persisted_master)
    if observed != run_manifest or tuple(value["frozen_argv"]) != argv:
        raise AttemptError("fresh RUN-01 identity changed during publication")
    return Attempt(root, True, observed, admission, 0, argv, cwd)


def _resume_attempt(
    *,
    root: Path,
    admission_receipt: Path,
    command_runner: Callable[..., object],
    argv: tuple[str, ...],
    cwd: Path,
) -> Attempt:
    if not root.is_dir():
        raise AttemptError("technical resume requires an existing RUN-01 directory")
    if (root / "published-result.json").exists():
        raise AttemptError("published RUN-01 result is immutable and cannot be resumed")
    if (root / "terminal-no-polarity.json").exists():
        raise AttemptError("quarantined RUN-01 attempt cannot be resumed")
    if validate_quarantine_lock(root, mode="RUN-01"):
        raise AttemptError("quarantine lock forbids RUN-01 resume")
    master = (root / "run-master.bin").read_bytes()
    run_manifest, value = _validate_manifest(root, master)
    frozen_cwd = Path(str(value["frozen_cwd"])).resolve(strict=False)
    if cwd != frozen_cwd:
        raise AttemptError("technical resume cwd differs from the frozen RUN-01 cwd")
    admissions = root / "admissions"
    expected_index = len(tuple(admissions.glob("invocation-*.json")))
    expected_path = admissions / f"invocation-{expected_index:06d}.json"
    if admission_receipt.resolve(strict=False) != expected_path.resolve(strict=False):
        raise AttemptError("resume admission receipt must use the next create-only invocation slot")
    admission = preflight_run(expected_path, command_runner=command_runner)
    atomic_create_json(
        root / "invocations" / f"invocation-{expected_index:06d}.json",
        _invocation_value(
            index=expected_index, argv=argv, cwd=cwd, root=root, resume=True,
            admission_file=f"admissions/invocation-{expected_index:06d}.json",
        ),
    )
    return Attempt(
        root, False, run_manifest, admission, expected_index, tuple(value["frozen_argv"]), frozen_cwd,
    )


def initialize_or_resume_attempt(
    *,
    result_root: str | Path,
    admission_receipt: str | Path,
    command_runner: Callable[..., object],
    master_source: Callable[[], bytes] = lambda: secrets.token_bytes(32),
    argv: Sequence[str],
    cwd: str | Path,
    resume: bool,
) -> Attempt:
    """Admit memory, then create or validate exactly one RUN-01 identity."""

    root = _resolved_root(result_root)
    receipt = Path(admission_receipt).resolve(strict=False)
    materialized_argv = tuple(argv)
    resolved_cwd = Path(cwd).resolve(strict=True)
    if not materialized_argv or not all(isinstance(item, str) and item for item in materialized_argv):
        raise AttemptError("exact invocation argv must be a nonempty string sequence")
    if resume:
        try:
            return _resume_attempt(
                root=root, admission_receipt=receipt, command_runner=command_runner,
                argv=materialized_argv, cwd=resolved_cwd,
            )
        except BaseException as error:
            if root.is_dir():
                raise_after_quarantine(
                    root, mode="RUN-01", stage="resume-source-or-initialization-gate",
                    original=error, telemetry=None,
                )
            raise
    return _fresh_attempt(
        root=root, admission_receipt=receipt, command_runner=command_runner,
        master_source=master_source, argv=materialized_argv, cwd=resolved_cwd,
    )


__all__ = [
    "ATTEMPT_SCHEMA", "Attempt", "AttemptError", "WORKER_TOPOLOGY",
    "atomic_create_bytes", "atomic_create_json", "initialize_or_resume_attempt",
]
