"""Create-once RUN-01 identity, resume, workload, and publication orchestration.

This module owns the production control seam for the isolated B01 package.  It
does not import the consumed FCEOV implementation and it never launches work
at import time.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import stat
import tempfile
from typing import Callable, Mapping, Sequence

import torch
from torch import Tensor

from .contracts import (
    ATTEMPT_ID, NAMED_RUN_ID, Q_COUNTER_ADDRESS, QUARANTINED_NAMED_RUN_ID,
    SCIENCE_CARD_REVISION, STUDY_ID, Manifest, RunManifest, WORKLOADS, build_run_manifest,
)
from .foundation import FoundationActorCritic, materialize_foundation
from .preflight import PreflightReceipt, validate_preflight_receipt_bytes
from .rng import CounterRNG
from .source_identity import (
    compute_source_identity_bytes, validate_source_identity_bytes, write_source_identity_gate,
)
from .quarantine import raise_after_quarantine, validate_quarantine_lock
from .training import ExactAdamW, UpdateReceipt


ATTEMPT_SCHEMA = f"{ATTEMPT_ID}-MANIFEST-V1"
ATTEMPT_HEADER_SCHEMA = f"{ATTEMPT_ID}-HEADER-V1"
WORKER_TOPOLOGY = {
    "foreground_processes": 1,
    "telemetry_threads": 1,
    "torch_intraop_threads": 1,
    "native_training_batch_width": 12,
    "native_evaluator_batch_width": 32,
    "native_twin_batch_width": 2,
}
CHECKPOINT_SCHEMA = "SCDMP_MF_RS_MK_B01_FOUNDATION_CHECKPOINT_V1"
_TELEMETRY_WITNESS_NONCE = object()


@dataclass(frozen=True, slots=True)
class _InitialTelemetryWitness:
    nonce: object
    monitor_identity: int


def _issue_initial_telemetry_witness(monitor: object) -> _InitialTelemetryWitness:
    validator = getattr(monitor, "require_valid_initial_observation", None)
    if not callable(validator):
        raise AttemptError("live telemetry monitor cannot validate its initial observation")
    validator()
    return _InitialTelemetryWitness(_TELEMETRY_WITNESS_NONCE, id(monitor))


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
    sealed_identity_baseline: tuple[bytes, ...] = ()


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
        encoded = _read_regular_bytes(path, label="canonical attempt artifact")
        value = json.loads(encoded.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AttemptError(f"attempt artifact is missing or unreadable: {path.name}") from error
    if not isinstance(value, dict) or encoded != _canonical_json(value):
        raise AttemptError(f"attempt artifact is not canonical direct JSON: {path.name}")
    return value


def _read_regular_bytes(path: Path, *, label: str) -> bytes:
    """Read one exact opened regular-file object without following its leaf."""

    try:
        absolute = Path(os.path.abspath(os.fspath(path)))
        # Reject static parent aliases before opening; the leaf itself is
        # verified atomically through the opened handle below.
        current = Path(absolute.anchor)
        for component in absolute.parts[1:-1]:
            current /= component
            observed = os.lstat(current)
            attributes = int(getattr(observed, "st_file_attributes", 0))
            if stat.S_ISLNK(observed.st_mode) or attributes & 0x400:
                raise AttemptError(f"{label} traverses a symlink, junction, or reparse point")
        return _read_opened_regular_file(absolute, label=label)
    except AttemptError:
        raise
    except OSError as error:
        raise AttemptError(f"{label} is unavailable") from error


def _read_fd_all(descriptor: int) -> bytes:
    chunks = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _read_opened_regular_file(path: Path, *, label: str) -> bytes:
    if os.name != "nt":
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise AttemptError(f"{label} is not an opened regular file")
            return _read_fd_all(descriptor)
        finally:
            os.close(descriptor)

    import ctypes
    import msvcrt
    from ctypes import wintypes

    class _ByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    get_info = kernel32.GetFileInformationByHandle
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ByHandleFileInformation)]
    get_info.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    handle = create_file(
        str(path), 0x80000000, 0x00000001 | 0x00000002 | 0x00000004,
        None, 3, 0x00200000, None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle == invalid_handle:
        raise OSError(ctypes.get_last_error(), f"CreateFileW failed for {label}")
    descriptor = None
    try:
        information = _ByHandleFileInformation()
        if not get_info(handle, ctypes.byref(information)):
            raise OSError(ctypes.get_last_error(), f"GetFileInformationByHandle failed for {label}")
        if information.dwFileAttributes & (0x00000010 | 0x00000400):
            raise AttemptError(f"{label} is a directory or reparse point")
        descriptor = msvcrt.open_osfhandle(
            int(handle), os.O_RDONLY | getattr(os, "O_BINARY", 0),
        )
        handle = None
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise AttemptError(f"{label} is not an opened regular file")
        return _read_fd_all(descriptor)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        elif handle is not None:
            close_handle(handle)


def _require_direct_directory(path: Path, *, label: str) -> None:
    try:
        absolute = Path(os.path.abspath(os.fspath(path)))
        current = Path(absolute.anchor)
        observed = None
        for component in absolute.parts[1:]:
            current /= component
            observed = os.lstat(current)
            attributes = int(getattr(observed, "st_file_attributes", 0))
            if stat.S_ISLNK(observed.st_mode) or attributes & 0x400:
                raise AttemptError(f"{label} traverses a symlink, junction, or reparse point")
        if observed is None or not stat.S_ISDIR(observed.st_mode):
            raise AttemptError(f"{label} is not a direct directory")
    except AttemptError:
        raise
    except OSError as error:
        raise AttemptError(f"{label} is unavailable") from error


def canonical_result_root(path: str | Path) -> Path:
    """Reject every noncanonical coordinate before any filesystem content probe."""

    unprobed = Path(path)
    if unprobed.name != ATTEMPT_ID:
        raise AttemptError(
            f"result root name must be the canonical evidence attempt identity {ATTEMPT_ID}"
        )
    root = Path(os.path.abspath(os.fspath(unprobed)))
    current = Path(root.anchor)
    for component in root.parts[1:]:
        current /= component
        try:
            observed = os.lstat(current)
        except FileNotFoundError:
            break
        except OSError as error:
            raise AttemptError("result coordinate cannot be checked without following aliases") from error
        attributes = int(getattr(observed, "st_file_attributes", 0))
        if stat.S_ISLNK(observed.st_mode) or attributes & 0x400:
            raise AttemptError("result coordinate contains a symlink, junction, or reparse point")
    normalized = str(root).replace("\\", "/").lower()
    if "foundation_conditioned_event_order_value" in normalized or "2026-08-31." in normalized:
        raise AttemptError("old FCEOV coordinates are isolated from B01")
    return root


def _attempt_header_value(*, root: Path, argv: tuple[str, ...], cwd: Path) -> dict[str, object]:
    return {
        "schema": ATTEMPT_HEADER_SCHEMA,
        "study_id": STUDY_ID,
        "named_run_id": NAMED_RUN_ID,
        "attempt_id": ATTEMPT_ID,
        "quarantined_named_run_id": QUARANTINED_NAMED_RUN_ID,
        "resolved_result_root": str(root),
        "science_card_revision": SCIENCE_CARD_REVISION,
        "unchanged_scientific_contract": Manifest().to_dict(),
        "frozen_argv": list(argv),
        "frozen_cwd": str(cwd),
    }


def _manifest_value(
    run_manifest: RunManifest,
    *,
    root: Path,
    argv: tuple[str, ...],
    cwd: Path,
) -> dict[str, object]:
    return {
        "schema": ATTEMPT_SCHEMA,
        "study_id": STUDY_ID,
        "named_run_id": NAMED_RUN_ID,
        "attempt_id": ATTEMPT_ID,
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
        "schema": f"{ATTEMPT_ID}-INVOCATION-V1",
        "named_run_id": NAMED_RUN_ID,
        "attempt_id": ATTEMPT_ID,
        "invocation_index": index,
        "exact_argv": list(argv),
        "exact_cwd": str(cwd),
        "resolved_result_root": str(root),
        "technical_resume": resume,
        "admission_file": admission_file,
    }


def _validate_resume_history(
    root: Path, *, pending_admission: Path | None = None,
    frozen_argv: tuple[str, ...] | None = None, frozen_cwd: str | None = None,
) -> tuple[int, tuple[dict[str, object], ...]]:
    admissions = root / "admissions"
    invocations = root / "invocations"
    _require_direct_directory(admissions, label="admission history directory")
    _require_direct_directory(invocations, label="invocation history directory")
    admission_paths = tuple(sorted(admissions.glob("invocation-*.json")))
    invocation_paths = tuple(sorted(invocations.glob("invocation-*.json")))
    completed = len(invocation_paths)
    expected_invocations = tuple(
        invocations / f"invocation-{index:06d}.json" for index in range(completed)
    )
    expected_admissions = tuple(
        admissions / f"invocation-{index:06d}.json"
        for index in range(completed + (pending_admission is not None))
    )
    if invocation_paths != expected_invocations or admission_paths != expected_admissions:
        raise AttemptError("admission/invocation history is missing, sparse, or extra")
    if pending_admission is not None and (
        not expected_admissions or pending_admission != expected_admissions[-1]
    ):
        raise AttemptError("pending admission is not the next contiguous history slot")
    rows: list[dict[str, object]] = []
    for index, invocation_path in enumerate(invocation_paths):
        admission_path = admissions / f"invocation-{index:06d}.json"
        admission_direct = _read_regular_bytes(admission_path, label="admission history artifact")
        invocation_direct = _read_regular_bytes(invocation_path, label="invocation history artifact")
        admission = validate_preflight_receipt_bytes(admission_direct, path=admission_path)
        invocation = _read_canonical_json(invocation_path)
        required = {
            "schema", "named_run_id", "attempt_id", "invocation_index", "exact_argv",
            "exact_cwd", "resolved_result_root", "technical_resume", "admission_file",
        }
        if (
            set(invocation) != required
            or invocation.get("schema") != f"{ATTEMPT_ID}-INVOCATION-V1"
            or invocation.get("named_run_id") != NAMED_RUN_ID
            or invocation.get("attempt_id") != ATTEMPT_ID
            or invocation.get("invocation_index") != index
            or invocation.get("resolved_result_root") != str(root)
            or invocation.get("technical_resume") is not (index > 0)
            or invocation.get("admission_file") != f"admissions/invocation-{index:06d}.json"
            or not isinstance(invocation.get("exact_argv"), list)
            or not invocation["exact_argv"]
            or not all(isinstance(item, str) and item for item in invocation["exact_argv"])
            or not isinstance(invocation.get("exact_cwd"), str)
            or not invocation["exact_cwd"]
            or (frozen_cwd is not None and invocation.get("exact_cwd") != frozen_cwd)
            or (
                index == 0 and frozen_argv is not None
                and invocation.get("exact_argv") != list(frozen_argv)
            )
            or admission.path != admission_path
        ):
            raise AttemptError("persisted invocation history binding differs")
        rows.append({
            "invocation_index": index,
            "admission_relative_path": admission_path.relative_to(root).as_posix(),
            "invocation_relative_path": invocation_path.relative_to(root).as_posix(),
            "admission_size_bytes": len(admission_direct),
            "admission_sha256": hashlib.sha256(admission_direct).hexdigest(),
            "invocation_size_bytes": len(invocation_direct),
            "invocation_sha256": hashlib.sha256(invocation_direct).hexdigest(),
            "available_physical_bytes": admission.available_physical_bytes,
            "effective_available_bytes": admission.effective_available_bytes,
            "admission_passed": admission.passed,
        })
    if pending_admission is not None:
        pending_direct = _read_regular_bytes(pending_admission, label="pending admission artifact")
        pending = validate_preflight_receipt_bytes(pending_direct, path=pending_admission)
        if pending.path != pending_admission:
            raise AttemptError("pending admission receipt binding differs")
    return completed, tuple(rows)


def _validate_manifest(root: Path, master: bytes) -> tuple[RunManifest, dict[str, object]]:
    if len(master) != 32:
        raise AttemptError("persisted replacement-attempt master must contain exactly 32 bytes")
    run_manifest = build_run_manifest(master)
    header = _read_canonical_json(root / "attempt-header.json")
    value = _read_canonical_json(root / "manifest.json")
    required = {
        "schema", "study_id", "named_run_id", "attempt_id", "run_identity",
        "resolved_result_root", "frozen_argv", "frozen_cwd", "run_manifest", "worker_topology",
    }
    if (
        header != _attempt_header_value(
            root=root,
            argv=tuple(header.get("frozen_argv", ())) if isinstance(header.get("frozen_argv"), list) else (),
            cwd=Path(str(header.get("frozen_cwd", ""))),
        )
        or set(value) != required
        or value.get("schema") != ATTEMPT_SCHEMA
        or value.get("study_id") != STUDY_ID
        or value.get("named_run_id") != NAMED_RUN_ID
        or value.get("attempt_id") != ATTEMPT_ID
        or value.get("run_identity") != run_manifest.static.schema
        or value.get("resolved_result_root") != str(root)
        or header.get("frozen_argv") != value.get("frozen_argv")
        or header.get("frozen_cwd") != value.get("frozen_cwd")
        or value.get("run_manifest") != run_manifest.to_dict()
        or value.get("worker_topology") != WORKER_TOPOLOGY
        or not isinstance(value.get("frozen_argv"), list)
        or not all(isinstance(item, str) for item in value["frozen_argv"])
        or not isinstance(value.get("frozen_cwd"), str)
    ):
        raise AttemptError("persisted manifest differs from the sealed replacement-attempt identity")
    if _read_canonical_json(root / "realized-q-audit.json") != _q_audit_value(run_manifest):
        raise AttemptError("persisted realized-q audit differs from the sealed RUN-01 identity")
    source_identity_path = root / "source-identity.json"
    source_direct = _read_regular_bytes(source_identity_path, label="sealed source identity")
    validate_source_identity_bytes(source_direct, compute_source_identity_bytes())
    return run_manifest, value


def _observe_sealed_identity(attempt: Attempt) -> tuple[dict[str, object], ...]:
    """Observe every sealed identity byte without establishing a new baseline."""

    if not isinstance(attempt, Attempt):
        raise AttemptError("sealed identity validation requires a typed attempt")
    root = canonical_result_root(attempt.root)
    try:
        master = _read_regular_bytes(root / "run-master.bin", label="sealed attempt master")
    except OSError as error:
        raise AttemptError("sealed attempt master is unavailable") from error
    try:
        observed, _manifest = _validate_manifest(root, master)
    except AttemptError:
        raise
    except Exception as error:
        raise AttemptError("sealed source or identity validation failed") from error
    if observed != attempt.run_manifest:
        raise AttemptError("live attempt binding differs from the sealed identity")
    next_index, history = _validate_resume_history(
        root, frozen_argv=tuple(_manifest["frozen_argv"]),
        frozen_cwd=str(_manifest["frozen_cwd"]),
    )
    if next_index != attempt.invocation_index + 1:
        raise AttemptError("attempt invocation index differs from sealed history")
    current_transaction = history[attempt.invocation_index]
    if (
        current_transaction["available_physical_bytes"]
        != attempt.admission.available_physical_bytes
        or current_transaction["effective_available_bytes"]
        != attempt.admission.effective_available_bytes
        or current_transaction["admission_passed"] is not attempt.admission.passed
    ):
        raise AttemptError("current invocation admission fields differ from the attempt binding")
    paths = (
        root / "attempt-header.json",
        root / "manifest.json",
        root / "run-master.bin",
        root / "realized-q-audit.json",
        root / "source-identity.json",
    )
    inventory = []
    for path in paths:
        try:
            direct = _read_regular_bytes(path, label="sealed identity artifact")
        except OSError as error:
            raise AttemptError(f"sealed identity artifact is unavailable: {path.name}") from error
        inventory.append({
            "relative_path": path.relative_to(root).as_posix(),
            "direct_size_bytes": len(direct),
            "sha256": hashlib.sha256(direct).hexdigest(),
        })
    master_row = next(row for row in inventory if row["relative_path"] == "run-master.bin")
    if master_row["sha256"] != attempt.run_manifest.master_commitment:
        raise AttemptError("sealed master direct commitment differs")
    inventory.extend({"transaction": row} for row in history)
    return tuple(inventory)


def validate_sealed_identity(attempt: Attempt) -> tuple[dict[str, object], ...]:
    """Compare the current sealed bytes with the immutable Attempt baseline."""

    if not attempt.sealed_identity_baseline:
        raise AttemptError("attempt has no established sealed identity baseline")
    observed = _observe_sealed_identity(attempt)
    if tuple(_canonical_json(row) for row in observed) != attempt.sealed_identity_baseline:
        raise AttemptError("sealed identity differs from the immutable attempt baseline")
    return observed


def _seal_attempt_identity(attempt: Attempt) -> Attempt:
    if attempt.sealed_identity_baseline:
        raise AttemptError("attempt sealed identity baseline is already established")
    observed = _observe_sealed_identity(attempt)
    return replace(
        attempt,
        sealed_identity_baseline=tuple(_canonical_json(row) for row in observed),
    )


def _fresh_attempt(
    *,
    root: Path,
    admission_receipt: Path,
    admission: PreflightReceipt,
    master_source: Callable[[], bytes],
    argv: tuple[str, ...],
    cwd: Path,
) -> Attempt:
    if root.exists():
        raise AttemptError("existing replacement-attempt root requires explicit technical resume")
    try:
        admission_receipt.resolve(strict=False).relative_to(root)
    except ValueError:
        pass
    else:
        raise AttemptError("fresh admission receipt must be outside the not-yet-created result root")
    if admission.path.resolve(strict=False) != admission_receipt.resolve(strict=False) or not admission.passed:
        raise AttemptError("fresh invocation admission binding differs")
    root.mkdir(parents=True, exist_ok=False)
    atomic_create_json(root / "attempt-header.json", _attempt_header_value(root=root, argv=argv, cwd=cwd))
    write_source_identity_gate(root / "source-identity.json")
    master = master_source()
    if not isinstance(master, bytes) or len(master) != 32:
        raise AttemptError("replacement-attempt master source must return exactly 32 fresh bytes")
    run_manifest = build_run_manifest(master)
    try:
        atomic_create_bytes(root / "run-master.bin", master)
        atomic_create_json(
            root / "manifest.json",
            _manifest_value(run_manifest, root=root, argv=argv, cwd=cwd),
        )
        atomic_create_json(root / "realized-q-audit.json", _q_audit_value(run_manifest))
        admissions = root / "admissions"
        admissions.mkdir()
        shutil.move(str(admission_receipt), admissions / "invocation-000000.json")
        atomic_create_json(root / "invocations" / "invocation-000000.json", _invocation_value(
            index=0, argv=argv, cwd=cwd, root=root, resume=False,
            admission_file="admissions/invocation-000000.json",
        ))
    except Exception:
        # A partially initialized canonical root is retained for fail-closed quarantine.
        raise
    persisted_master = _read_regular_bytes(root / "run-master.bin", label="fresh sealed master")
    observed, value = _validate_manifest(root, persisted_master)
    if observed != run_manifest or tuple(value["frozen_argv"]) != argv:
        raise AttemptError("fresh replacement-attempt identity changed during sealing")
    return _seal_attempt_identity(Attempt(root, True, observed, admission, 0, argv, cwd))


def _resume_attempt(
    *,
    root: Path,
    admission_receipt: Path,
    admission: PreflightReceipt,
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
    master = _read_regular_bytes(root / "run-master.bin", label="resume sealed master")
    run_manifest, value = _validate_manifest(root, master)
    frozen_cwd = Path(str(value["frozen_cwd"])).resolve(strict=False)
    if cwd != frozen_cwd:
        raise AttemptError("technical resume cwd differs from the frozen RUN-01 cwd")
    admissions = root / "admissions"
    invocations = root / "invocations"
    expected_index, _history = _validate_resume_history(
        root, pending_admission=admission_receipt,
        frozen_argv=tuple(value["frozen_argv"]), frozen_cwd=str(value["frozen_cwd"]),
    )
    expected_path = admissions / f"invocation-{expected_index:06d}.json"
    if admission_receipt.resolve(strict=False) != expected_path.resolve(strict=False):
        raise AttemptError("resume admission receipt must use the next create-only invocation slot")
    if admission.path.resolve(strict=False) != expected_path.resolve(strict=False) or not admission.passed:
        raise AttemptError("resume admission receipt differs from the next create-only slot")
    atomic_create_json(
        invocations / f"invocation-{expected_index:06d}.json",
        _invocation_value(
            index=expected_index, argv=argv, cwd=cwd, root=root, resume=True,
            admission_file=f"admissions/invocation-{expected_index:06d}.json",
        ),
    )
    attempt = Attempt(
        root, False, run_manifest, admission, expected_index, tuple(value["frozen_argv"]), frozen_cwd,
    )
    return _seal_attempt_identity(attempt)


def _initialize_or_resume_attempt(
    *,
    result_root: str | Path,
    admission_receipt: str | Path,
    admission: PreflightReceipt,
    master_source: Callable[[], bytes] = lambda: secrets.token_bytes(32),
    argv: Sequence[str],
    cwd: str | Path,
    resume: bool,
    telemetry_witness: _InitialTelemetryWitness,
) -> Attempt:
    """After admission and initial telemetry, create or validate the canonical attempt."""

    root = canonical_result_root(result_root)
    receipt = Path(os.path.abspath(os.fspath(admission_receipt)))
    materialized_argv = tuple(argv)
    resolved_cwd = Path(cwd).resolve(strict=True)
    if (
        not isinstance(telemetry_witness, _InitialTelemetryWitness)
        or telemetry_witness.nonce is not _TELEMETRY_WITNESS_NONCE
    ):
        raise AttemptError("a valid live telemetry observation must precede attempt access")
    if not isinstance(admission, PreflightReceipt) or not admission.passed:
        raise AttemptError("a passing invocation-specific admission is required")
    if not materialized_argv or not all(isinstance(item, str) and item for item in materialized_argv):
        raise AttemptError("exact invocation argv must be a nonempty string sequence")
    if resume:
        try:
            return _resume_attempt(
                root=root, admission_receipt=receipt, admission=admission,
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
        root=root, admission_receipt=receipt, admission=admission,
        master_source=master_source, argv=materialized_argv, cwd=resolved_cwd,
    )


__all__ = [
    "ATTEMPT_SCHEMA", "Attempt", "AttemptError", "WORKER_TOPOLOGY",
    "atomic_create_bytes", "atomic_create_json", "canonical_result_root",
    "validate_sealed_identity",
]
