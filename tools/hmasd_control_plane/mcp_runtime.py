"""Runtime-only lifecycle evidence for local HMASD MCP stdio processes.

The registry is intentionally not a singleton lease, heartbeat, or scheduler.
Each process publishes one immutable start record and, on an ordinary return,
one immutable terminal record.  Readers combine PID liveness with the OS
process creation identity so PID reuse cannot be mistaken for the old server.
"""

from __future__ import annotations

import ctypes
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


INSTANCE_SCHEMA = "HMASD_MCP_INSTANCE_V1"
TERMINAL_SCHEMA = "HMASD_MCP_INSTANCE_TERMINAL_V1"
INDEX_SCHEMA = "HMASD_MCP_INSTANCE_INDEX_V1"
DEFAULT_INSTANCE_REL = Path("runtime/hmasd-control-plane/mcp-instances")


class MCPRuntimeRecordError(RuntimeError):
    """Raised when an immutable MCP runtime record cannot be published."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _publish_json_no_overwrite(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise MCPRuntimeRecordError(f"runtime record already exists: {path}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _filetime_to_iso(ticks: int) -> str:
    # Windows FILETIME counts 100ns intervals since 1601-01-01 UTC.
    unix_seconds = (ticks - 116_444_736_000_000_000) / 10_000_000
    return datetime.fromtimestamp(unix_seconds, timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


def _windows_process_identity(pid: int) -> dict[str, Any]:
    from ctypes import wintypes

    process_query_limited_information = 0x1000
    error_invalid_parameter = 87

    class FileTime(ctypes.Structure):
        _fields_ = (("low", wintypes.DWORD), ("high", wintypes.DWORD))

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetProcessTimes.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(FileTime),
        ctypes.POINTER(FileTime),
        ctypes.POINTER(FileTime),
        ctypes.POINTER(FileTime),
    )
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL

    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        return {
            "probe_state": "NOT_FOUND" if error == error_invalid_parameter else "UNKNOWN",
            "process_start_token": None,
            "process_started_at": None,
            "probe_error": f"WinError:{error}",
        }
    try:
        created = FileTime()
        exited = FileTime()
        kernel = FileTime()
        user = FileTime()
        if not kernel32.GetProcessTimes(
            handle,
            ctypes.byref(created),
            ctypes.byref(exited),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            return {
                "probe_state": "UNKNOWN",
                "process_start_token": None,
                "process_started_at": None,
                "probe_error": f"WinError:{ctypes.get_last_error()}",
            }
        ticks = (int(created.high) << 32) | int(created.low)
        return {
            "probe_state": "RUNNING",
            "process_start_token": f"win-filetime:{ticks}",
            "process_started_at": _filetime_to_iso(ticks),
            "probe_error": None,
        }
    finally:
        kernel32.CloseHandle(handle)


def _proc_process_identity(pid: int) -> dict[str, Any]:
    stat_path = Path(f"/proc/{pid}/stat")
    try:
        fields = stat_path.read_text(encoding="utf-8").split()
    except FileNotFoundError:
        return {
            "probe_state": "NOT_FOUND",
            "process_start_token": None,
            "process_started_at": None,
            "probe_error": "FileNotFoundError",
        }
    except (OSError, UnicodeError) as exc:
        return {
            "probe_state": "UNKNOWN",
            "process_start_token": None,
            "process_started_at": None,
            "probe_error": type(exc).__name__,
        }
    if len(fields) < 22:
        return {
            "probe_state": "UNKNOWN",
            "process_start_token": None,
            "process_started_at": None,
            "probe_error": "MalformedProcStat",
        }
    start_ticks = int(fields[21])
    started_at = None
    try:
        boot_line = next(
            line for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines()
            if line.startswith("btime ")
        )
        boot_seconds = int(boot_line.split()[1])
        clock_ticks = int(os.sysconf("SC_CLK_TCK"))
        started_at = datetime.fromtimestamp(
            boot_seconds + start_ticks / clock_ticks, timezone.utc
        ).isoformat(timespec="microseconds").replace("+00:00", "Z")
    except (OSError, StopIteration, ValueError):
        pass
    return {
        "probe_state": "RUNNING",
        "process_start_token": f"proc-startticks:{start_ticks}",
        "process_started_at": started_at,
        "probe_error": None,
    }


def process_identity(pid: int) -> dict[str, Any]:
    """Return a non-secret OS identity probe for one PID."""

    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return {
            "probe_state": "UNKNOWN",
            "process_start_token": None,
            "process_started_at": None,
            "probe_error": "InvalidPid",
        }
    if os.name == "nt":
        return _windows_process_identity(pid)
    if Path("/proc").is_dir():
        return _proc_process_identity(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        state, error = "NOT_FOUND", "ProcessLookupError"
    except (PermissionError, OSError) as exc:
        state, error = "UNKNOWN", type(exc).__name__
    else:
        state, error = "RUNNING", None
    return {
        "probe_state": state,
        "process_start_token": None,
        "process_started_at": None,
        "probe_error": error,
    }


@dataclass(frozen=True)
class MCPInstanceRegistration:
    instance_id: str
    instance_root: Path
    start: dict[str, Any]

    def close(self) -> dict[str, Any]:
        terminal = {
            "schema": TERMINAL_SCHEMA,
            "instance_id": self.instance_id,
            "pid": int(self.start["pid"]),
            "finished_at": _now_iso(),
            "exit_kind": "NORMAL",
        }
        _publish_json_no_overwrite(self.instance_root / "terminal.json", terminal)
        return terminal


def begin_mcp_instance(
    repo_root: str | os.PathLike[str],
    *,
    server_name: str,
    profile: str,
    state_path: str | os.PathLike[str] | None = None,
) -> MCPInstanceRegistration:
    """Publish one fresh MCP start record and return its close handle."""

    root = Path(repo_root).resolve()
    instance_id = f"mcp_{uuid.uuid4().hex}"
    instance_root = root / DEFAULT_INSTANCE_REL / instance_id
    instance_root.mkdir(parents=True, exist_ok=False)
    identity = process_identity(os.getpid())
    start = {
        "schema": INSTANCE_SCHEMA,
        "instance_id": instance_id,
        "server_name": str(server_name),
        "profile": str(profile),
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "process_start_token": identity["process_start_token"],
        "process_started_at": identity["process_started_at"],
        "transport": "stdio",
        "repo_root": str(root),
        "state_path": str(Path(state_path).resolve()) if state_path else None,
        "started_at": _now_iso(),
    }
    _publish_json_no_overwrite(instance_root / "start.json", start)
    return MCPInstanceRegistration(instance_id, instance_root, start)


def _load_record(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, type(exc).__name__
    if not isinstance(value, dict):
        return None, "RecordNotObject"
    return value, None


def inspect_mcp_instances(repo_root: str | os.PathLike[str]) -> dict[str, Any]:
    """Read the runtime registry without modifying or cleaning it."""

    root = Path(repo_root).resolve()
    registry = root / DEFAULT_INSTANCE_REL
    instances: list[dict[str, Any]] = []
    if not registry.exists():
        return {
            "schema": INDEX_SCHEMA,
            "registry_root": str(registry),
            "registry_exists": False,
            "instances": [],
            "record_errors": [],
        }
    errors: list[dict[str, str]] = []
    try:
        entries = sorted(path for path in registry.iterdir() if path.is_dir())
    except OSError as exc:
        return {
            "schema": INDEX_SCHEMA,
            "registry_root": str(registry),
            "registry_exists": True,
            "instances": [],
            "record_errors": [
                {"path": str(registry), "error": type(exc).__name__}
            ],
        }
    for entry in entries:
        start_path = entry / "start.json"
        terminal_path = entry / "terminal.json"
        start, start_error = _load_record(start_path)
        terminal, terminal_error = _load_record(terminal_path)
        if start_error or start is None:
            errors.append(
                {
                    "path": str(start_path),
                    "error": start_error or "MissingStartRecord",
                }
            )
            instances.append(
                {
                    "instance_id": entry.name,
                    "server_name": None,
                    "profile": None,
                    "pid": None,
                    "status": "UNKNOWN",
                    "started_at": None,
                    "finished_at": terminal.get("finished_at") if terminal else None,
                    "evidence_refs": [str(start_path), str(terminal_path)],
                    "reason": start_error or "MissingStartRecord",
                }
            )
            continue
        start_validation_error = None
        if start.get("schema") != INSTANCE_SCHEMA:
            start_validation_error = "UnexpectedStartSchema"
        elif str(start.get("instance_id") or "") != entry.name:
            start_validation_error = "InstanceIdConflict"
        elif not isinstance(start.get("pid"), int) or isinstance(start.get("pid"), bool):
            start_validation_error = "InvalidStartPid"
        elif not str(start.get("server_name") or ""):
            start_validation_error = "MissingServerName"
        if start_validation_error:
            errors.append({"path": str(start_path), "error": start_validation_error})
        if terminal_error:
            errors.append({"path": str(terminal_path), "error": terminal_error})
        terminal_validation_error = None
        if terminal is not None and terminal_error is None:
            if terminal.get("schema") != TERMINAL_SCHEMA:
                terminal_validation_error = "UnexpectedTerminalSchema"
            elif terminal.get("instance_id") != start.get("instance_id"):
                terminal_validation_error = "TerminalInstanceConflict"
            elif terminal.get("pid") != start.get("pid"):
                terminal_validation_error = "TerminalPidConflict"
            if terminal_validation_error:
                errors.append(
                    {"path": str(terminal_path), "error": terminal_validation_error}
                )
        if start_validation_error or terminal_validation_error or terminal_error:
            status = "UNKNOWN"
            reason = start_validation_error or terminal_validation_error or terminal_error
        elif terminal is not None:
            status, reason = "CLOSED", "terminal_present"
        else:
            probe = process_identity(int(start.get("pid") or 0))
            if probe["probe_state"] == "NOT_FOUND":
                status, reason = "STALE", "pid_not_found_without_terminal"
            elif probe["probe_state"] != "RUNNING":
                status, reason = "UNKNOWN", str(probe.get("probe_error") or "probe_unknown")
            elif not start.get("process_start_token") or not probe.get("process_start_token"):
                status, reason = "UNKNOWN", "process_creation_identity_unavailable"
            elif start["process_start_token"] != probe["process_start_token"]:
                status, reason = "STALE", "pid_reused"
            else:
                status, reason = "ACTIVE", "pid_and_creation_identity_match"
        instances.append(
            {
                "instance_id": str(start.get("instance_id") or entry.name),
                "server_name": start.get("server_name"),
                "profile": start.get("profile"),
                "pid": start.get("pid"),
                "parent_pid": start.get("parent_pid"),
                "process_started_at": start.get("process_started_at"),
                "started_at": start.get("started_at"),
                "finished_at": terminal.get("finished_at") if terminal else None,
                "status": status,
                "reason": reason,
                "evidence_refs": [str(start_path), str(terminal_path)],
            }
        )
    return {
        "schema": INDEX_SCHEMA,
        "registry_root": str(registry),
        "registry_exists": True,
        "instances": instances,
        "record_errors": errors,
    }


__all__ = (
    "DEFAULT_INSTANCE_REL",
    "INDEX_SCHEMA",
    "INSTANCE_SCHEMA",
    "MCPInstanceRegistration",
    "MCPRuntimeRecordError",
    "TERMINAL_SCHEMA",
    "begin_mcp_instance",
    "inspect_mcp_instances",
    "process_identity",
)
