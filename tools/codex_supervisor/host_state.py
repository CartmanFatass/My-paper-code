"""External supervisor host identity and mechanical readiness records.

These files describe process and App Server lifecycle facts only.  They do not
carry, inspect, or infer repository semantic state.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


PROCESS_RECORD_SCHEMA = "HMASD_SUPERVISOR_PROCESS_V1"
READY_RECORD_SCHEMA = "HMASD_SUPERVISOR_READY_V2"


class HostStateValidationError(ValueError):
    """Raised when an external host-state record is not exactly valid."""


@dataclass(frozen=True)
class SupervisorProcessRecord:
    schema: str
    pid: int
    process_start_time_utc: str
    executable: str
    repo_root: str
    runtime_home: str
    profile: str
    started_at: str
    ready_file: str


@dataclass(frozen=True)
class SupervisorReadyRecord:
    schema: str
    run_id: str
    process_id: int
    initialized_at: str
    watcher_active: bool
    first_reconciliation_completed: bool
    thread_count: int
    runtime_home: str
    profile: str


_PROCESS_FIELDS = frozenset(SupervisorProcessRecord.__dataclass_fields__)
_READY_FIELDS = frozenset(SupervisorReadyRecord.__dataclass_fields__)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Durably replace *path* with one complete JSON object.

    The temporary file is created beside the destination so ``replace`` stays
    on one filesystem.  A failed write or replace removes only that temporary
    file and leaves any previously published record intact.
    """

    destination = Path(path)
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                sort_keys=True,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
        temporary = None
        _fsync_directory(destination.parent)
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def load_process_record(path: Path) -> SupervisorProcessRecord:
    """Load one exact ``SupervisorProcessRecord`` from JSON."""

    payload = _load_json_object(Path(path), "process record")
    _require_exact_fields(payload, _PROCESS_FIELDS, "process record")
    _require_schema(payload, PROCESS_RECORD_SCHEMA, "process record")
    _require_positive_int(payload, "pid", "process record")
    for field in (
        "process_start_time_utc",
        "executable",
        "repo_root",
        "runtime_home",
        "profile",
        "started_at",
        "ready_file",
    ):
        _require_nonempty_string(payload, field, "process record")
    return SupervisorProcessRecord(**payload)


def load_ready_record(path: Path) -> SupervisorReadyRecord:
    """Load one exact ``SupervisorReadyRecord`` from JSON."""

    payload = _load_json_object(Path(path), "ready record")
    _require_exact_fields(payload, _READY_FIELDS, "ready record")
    _require_schema(payload, READY_RECORD_SCHEMA, "ready record")
    _require_string(payload, "run_id", "ready record")
    _require_positive_int(payload, "process_id", "ready record")
    _require_nonempty_string(payload, "initialized_at", "ready record")
    _require_bool(payload, "watcher_active", "ready record")
    _require_bool(payload, "first_reconciliation_completed", "ready record")
    _require_nonnegative_int(payload, "thread_count", "ready record")
    _require_nonempty_string(payload, "runtime_home", "ready record")
    _require_nonempty_string(payload, "profile", "ready record")
    return SupervisorReadyRecord(**payload)


def validate_ready_record(
    process: SupervisorProcessRecord,
    ready: SupervisorReadyRecord | None,
) -> tuple[str, ...]:
    """Return mechanical reasons why *ready* does not prove host readiness."""

    if not isinstance(process, SupervisorProcessRecord):
        raise TypeError("process must be a SupervisorProcessRecord")
    if ready is None:
        return ("ready record is missing",)
    if not isinstance(ready, SupervisorReadyRecord):
        raise TypeError("ready must be a SupervisorReadyRecord or None")

    errors: list[str] = []
    if ready.process_id != process.pid:
        errors.append("process ID does not match")
    if not _same_path(ready.runtime_home, process.runtime_home):
        errors.append("runtime home does not match")
    if ready.profile != process.profile:
        errors.append("profile does not match")
    if not ready.watcher_active:
        errors.append("server-request watcher is not active")
    if not ready.first_reconciliation_completed:
        errors.append("first reconciliation is incomplete")
    if not ready.run_id.strip():
        errors.append("run_id is empty")
    return tuple(errors)


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HostStateValidationError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise HostStateValidationError(f"{label} must be a JSON object")
    return payload


def _require_exact_fields(
    payload: Mapping[str, Any], expected: frozenset[str], label: str
) -> None:
    actual = set(payload)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise HostStateValidationError(
            f"{label} fields differ: missing={missing}, extra={extra}"
        )


def _require_schema(payload: Mapping[str, Any], expected: str, label: str) -> None:
    value = payload["schema"]
    if type(value) is not str:
        raise HostStateValidationError(f"{label}.schema must be a string")
    if value != expected:
        raise HostStateValidationError(f"{label}.schema must equal {expected!r}")


def _require_string(payload: Mapping[str, Any], field: str, label: str) -> None:
    if type(payload[field]) is not str:
        raise HostStateValidationError(f"{label}.{field} must be a string")


def _require_nonempty_string(
    payload: Mapping[str, Any], field: str, label: str
) -> None:
    _require_string(payload, field, label)
    if not payload[field].strip():
        raise HostStateValidationError(f"{label}.{field} must be non-empty")


def _require_positive_int(payload: Mapping[str, Any], field: str, label: str) -> None:
    value = payload[field]
    if type(value) is not int or value <= 0:
        raise HostStateValidationError(f"{label}.{field} must be a positive integer")


def _require_nonnegative_int(
    payload: Mapping[str, Any], field: str, label: str
) -> None:
    value = payload[field]
    if type(value) is not int or value < 0:
        raise HostStateValidationError(
            f"{label}.{field} must be a non-negative integer"
        )


def _require_bool(payload: Mapping[str, Any], field: str, label: str) -> None:
    if type(payload[field]) is not bool:
        raise HostStateValidationError(f"{label}.{field} must be a boolean")


def _same_path(left: str, right: str) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(
        os.path.abspath(right)
    )


def _fsync_directory(directory: Path) -> None:
    """Persist the directory entry where the platform permits directory fsync."""

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        # Windows does not generally allow opening a directory this way.  The
        # file itself was fsynced before the atomic replacement.
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


__all__ = (
    "HostStateValidationError",
    "PROCESS_RECORD_SCHEMA",
    "READY_RECORD_SCHEMA",
    "SupervisorProcessRecord",
    "SupervisorReadyRecord",
    "atomic_write_json",
    "load_process_record",
    "load_ready_record",
    "validate_ready_record",
)
