#!/usr/bin/env python3
"""Prepare, execute, reconcile, and promote one observed local run.

This helper owns one manifest at a time.  It never invokes a shell, never
replays an interrupted run, and keeps wrapper/refusal outcomes separate from the
child's exact exit status.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as _datetime
import errno
import hashlib
import json
import math
import os
import platform
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

if os.name == "nt":
    from ctypes import wintypes

try:
    from scripts import hmasd_resource_preflight as resource_preflight
    from scripts import hmasd_operator_result, hmasd_platform
except ImportError:
    import hmasd_resource_preflight as resource_preflight
    import hmasd_operator_result
    import hmasd_platform

ROOT = Path(__file__).resolve().parents[1]
STATE_SCRIPT = ROOT / "scripts" / "hmasd_state.py"
SCHEMA_VERSION = 1
RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
SHA_RE = re.compile(r"[0-9a-fA-F]{40,64}\Z")
OUTPUT_NAMES = {
    "stdout": "stdout.log",
    "stderr": "stderr.log",
    "checkpoints": "checkpoints",
    "metrics": "metrics",
    "artifacts": "artifacts",
}
CLAIM_DIRECTORY = ".run-claims"
OPERATOR_RESULT_NAME = "operator-result.json"
TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z\Z"
)
IDENTITY_MATCH = "MATCH"
IDENTITY_DESCENDANTS = "DESCENDANTS"
IDENTITY_GONE = "GONE"
IDENTITY_REUSED = "REUSED"
IDENTITY_UNRECORDED = "UNRECORDED"

# OMP manifests were historically produced in a Linux/WSL checkout.  A
# native Windows runner must never reinterpret those paths as a directory on
# the current drive: doing so turns a useful refusal into a misleading
# CreateProcess ``file not found`` error.  These prefixes cover the Linux
# roots used by the project while leaving native drive and UNC paths intact.
_WINDOWS_WSL_PATH_PREFIXES = (
    "/home/",
    "/mnt/",
    "/opt/",
    "/proc/",
    "/tmp/",
    "/usr/",
    "/var/",
    "/workspace/",
    "/workspaces/",
)


def _looks_like_wsl_absolute(value: str) -> bool:
    if not value:
        return False
    normalized = value.replace("\\", "/")
    return normalized == "/" or normalized.startswith(_WINDOWS_WSL_PATH_PREFIXES)


def _validate_native_command(command: Sequence[str]) -> None:
    """Reject Linux/WSL command forms before changing run state on Windows."""

    if os.name != "nt" or not command:
        return
    first = command[0]
    first_name = Path(first.replace("\\", "/")).name.casefold()
    if re.fullmatch(r"python3(?:\.\d+)?(?:\.exe)?", first_name):
        raise RunInputError(
            "native Windows runs must invoke Python with sys.executable; "
            "the WSL-only python3 command is not an executable here"
        )
    if _looks_like_wsl_absolute(first):
        raise RunInputError(
            f"command uses a WSL/POSIX executable path ({first!r}); "
            "use a native Windows drive or UNC path"
        )
    if first.casefold().endswith(".py"):
        raise RunInputError(
            "native Windows cannot execute a .py file directly; invoke it "
            "through sys.executable"
        )
    for value in command[1:]:
        # Catch both a standalone path argument and common --option=/path
        # forms, without rejecting ordinary switches such as /? or /verbose.
        candidate = value.split("=", 1)[-1] if "=" in value else value
        if _looks_like_wsl_absolute(candidate):
            raise RunInputError(
                f"command argument uses a WSL/POSIX path ({value!r}); "
                "use a native Windows drive or UNC path"
            )


if os.name == "nt":

    def _windows_kernel32() -> Any:
        kernel32 = ctypes.windll.kernel32
        kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateProcess.restype = wintypes.BOOL
        kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        return kernel32


    def _windows_ntdll() -> Any:
        ntdll = ctypes.windll.ntdll
        ntdll.NtQuerySystemInformation.argtypes = [
            wintypes.ULONG,
            wintypes.LPVOID,
            wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG),
        ]
        ntdll.NtQuerySystemInformation.restype = wintypes.LONG
        ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        ntdll.NtResumeProcess.restype = wintypes.LONG
        return ntdll




class RunRefusal(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


class RunInputError(RunRefusal):
    def __init__(self, message: str):
        super().__init__(2, message)


@contextmanager
def _path_lock(path: Path) -> Iterator[None]:
    """Take a short cooperative lock beside a manifest."""

    lock_path = path.with_name(f".{path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        with hmasd_platform.exclusive_file_lock(descriptor):
            yield
    finally:
        os.close(descriptor)


def _utc_now() -> str:
    return (
        _datetime.datetime.now(_datetime.timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _command_digest(command: Sequence[str]) -> str:
    return _sha256_bytes(b"\0".join(os.fsencode(part) for part in command))


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        hmasd_platform.fsync_directory(path.parent)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    rendered = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    _atomic_write_bytes(path, rendered)


def _repo_file_ref(repo: Path, path: Path) -> dict[str, str]:
    try:
        relative = path.relative_to(repo).as_posix()
    except ValueError as exc:
        raise RunRefusal(5, f"operator result ref escapes cwd: {path}") from exc
    return {"path": relative, "sha256": _sha256_file(path)}


def _operator_result_document(
    repo: Path, manifest_path: Path, manifest: Mapping[str, Any]
) -> dict[str, Any]:
    stdout_path = manifest_path.parent / str(manifest["outputs"]["stdout"])
    stderr_path = manifest_path.parent / str(manifest["outputs"]["stderr"])
    manifest_ref = _repo_file_ref(repo, manifest_path)
    stdout_ref = _repo_file_ref(repo, stdout_path)
    stderr_ref = _repo_file_ref(repo, stderr_path)
    result = {
        "schema_version": 2,
        "assignment_message_id": manifest["assignment_id"],
        "run_id": manifest["run_id"],
        "operator_identity": manifest["operator_identity"],
        "manifest_ref": manifest_ref,
        "stdout_ref": stdout_ref,
        "stderr_ref": stderr_ref,
        "terminal_status": manifest["status"],
        "exit_code": manifest["process"]["exit_code"],
    }
    hmasd_operator_result.validate_document(result)
    return result


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunInputError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RunInputError(f"JSON object required at {path}")
    return value


def _safe_resolve(path: Path) -> Path:
    try:
        return path.expanduser().resolve(strict=False)
    except OSError as exc:
        raise RunRefusal(5, f"cannot resolve path {path}: {exc}") from exc


def _assert_no_symlink_components(path: Path, *, stop: Path | None = None) -> None:
    current = path if path.is_absolute() else (Path.cwd() / path)
    current = current.absolute()
    stop_abs = stop.absolute() if stop is not None else None
    parts = current.parts
    cursor = Path(parts[0])
    for part in parts[1:]:
        cursor /= part
        if stop_abs is not None and cursor == stop_abs:
            break
        try:
            if cursor.is_symlink():
                raise RunRefusal(5, f"symlink path component is not allowed: {cursor}")
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise RunRefusal(5, f"cannot inspect path component {cursor}: {exc}") from exc


def _confined_path(root: Path, relative: str | Path, *, allow_root: bool = False) -> Path:
    root_resolved = _safe_resolve(root)
    candidate = Path(relative)
    lexical = candidate if candidate.is_absolute() else root_resolved / candidate
    try:
        if lexical.is_symlink():
            raise RunRefusal(5, f"output path is a symlink: {lexical}")
    except OSError as exc:
        raise RunRefusal(5, f"cannot inspect output path {lexical}: {exc}") from exc
    resolved = _safe_resolve(lexical)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise RunRefusal(5, f"path escapes output root: {relative}") from exc
    if not allow_root and resolved == root_resolved:
        raise RunRefusal(5, "output path must not be the root itself")
    _assert_no_symlink_components(resolved, stop=root_resolved)
    return resolved

def _manifest_root(raw_path: str | Path) -> tuple[Path, Path]:
    manifest = _safe_resolve(Path(raw_path))
    if manifest.name != "manifest.json":
        raise RunInputError("manifest path must end in manifest.json")
    root = manifest.parent
    if root.is_symlink():
        raise RunRefusal(5, "manifest directory must not be a symlink")
    return manifest, root


def _load_manifest(raw_path: str | Path) -> tuple[Path, Path, dict[str, Any]]:
    manifest, root = _manifest_root(raw_path)
    return manifest, root, _read_json(manifest)


def _validate_identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not RUN_ID_RE.fullmatch(value):
        raise RunInputError(f"{name} is invalid")
    return value


def _validate_assignment(value: Any) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value) is None:
        raise RunInputError("assignment is invalid")
    return value


def _validate_sha(value: Any, name: str) -> str:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise RunInputError(f"{name} must be a Git SHA")
    return value.lower()


def _positive_number(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise RunInputError(f"{name} must be positive")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RunInputError(f"{name} must be positive") from exc
    if not math.isfinite(number) or number <= 0:
        raise RunInputError(f"{name} must be positive")
    return number


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise RunInputError(f"{name} must be positive")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise RunInputError(f"{name} must be positive") from exc
    if number <= 0:
        raise RunInputError(f"{name} must be positive")
    return number


def capture_snapshot() -> dict[str, Any]:
    """Indirection kept public so callers can replace host observations in tests."""

    return resource_preflight.capture_snapshot()


def _require_omp_branch(cwd: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(cwd), "symbolic-ref", "--quiet", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise RunRefusal(5, f"cannot inspect Git branch: {exc}") from exc
    branch = completed.stdout.strip()
    if completed.returncode != 0 or not branch.startswith("omp/"):
        raise RunRefusal(5, f"run requires an OMP branch, observed {branch or '<detached>'}")
    return branch


def _git_head(cwd: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--verify", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise RunRefusal(5, f"cannot inspect Git HEAD: {exc}") from exc
    head = completed.stdout.strip().lower()
    if completed.returncode != 0 or SHA_RE.fullmatch(head) is None:
        raise RunRefusal(5, "cannot resolve cwd Git HEAD")
    return head


def _parameters_digest(parameters: Mapping[str, Any]) -> str:
    return _sha256_bytes(_canonical_json(parameters))


def _claim_digest(
    *, direction_id: str, code_sha: str, command_sha256: str
) -> str:
    return _sha256_bytes(
        _canonical_json(
            {
                "direction_id": direction_id,
                "code_sha": code_sha,
                "command_sha256": command_sha256,
            }
        )
    )


def _expected_run_root(cwd: Path, direction_id: str, run_id: str) -> Path:
    return _safe_resolve(cwd) / "temp" / "directions" / direction_id / "exp" / run_id


def _validate_output_root(
    raw_output_root: str | Path, *, cwd: Path, direction_id: str, run_id: str
) -> Path:
    candidate = Path(raw_output_root).expanduser()
    if candidate.exists() and candidate.is_symlink():
        raise RunRefusal(5, "output root must not be a symlink")
    output_root = _safe_resolve(candidate)
    expected = _expected_run_root(cwd, direction_id, run_id)
    if output_root != expected:
        raise RunRefusal(
            5,
            "output root must be "
            f"{Path('temp') / 'directions' / direction_id / 'exp' / run_id} under cwd",
        )
    _assert_no_symlink_components(output_root)
    return output_root


def _reclaim_legacy_unsafe_prepare_root(
    output_root: Path, *, direction_id: str, run_id: str
) -> bool:
    """Remove only the exact partial tree left by the legacy prepare order.

    Older prepare calls created the three artifact directories and wrote an
    unsafe preflight before returning exit 6.  Such a tree contains no launch
    identity and no user/result bytes.  Any extra entry, symlink, non-empty
    directory, valid manifest, or different identity makes reclamation refuse.
    """

    if not output_root.exists():
        return False
    if output_root.is_symlink() or not output_root.is_dir():
        return False
    expected_names = {"preflight.json", "artifacts", "checkpoints", "metrics"}
    try:
        children = {child.name: child for child in output_root.iterdir()}
    except OSError:
        return False
    if set(children) != expected_names:
        return False
    preflight_path = children["preflight.json"]
    if preflight_path.is_symlink() or not preflight_path.is_file():
        return False
    try:
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if (
        not isinstance(preflight, Mapping)
        or preflight.get("schema_version") != SCHEMA_VERSION
        or preflight.get("direction_id") != direction_id
        or preflight.get("run_id") != run_id
        or preflight.get("memory_safe") is not False
    ):
        return False
    directories = [children[name] for name in ("artifacts", "checkpoints", "metrics")]
    for directory in directories:
        if directory.is_symlink() or not directory.is_dir():
            return False
        try:
            if any(directory.iterdir()):
                return False
        except OSError:
            return False
    preflight_path.unlink()
    for directory in directories:
        directory.rmdir()
    output_root.rmdir()
    return True


def _manifest_direction_root(
    manifest_path: Path, manifest: Mapping[str, Any]
) -> Path:
    direction_id = _validate_identifier(manifest.get("direction_id"), "direction_id")
    run_id = _validate_identifier(manifest.get("run_id"), "run_id")
    cwd_raw = manifest.get("cwd")
    if os.name == "nt" and isinstance(cwd_raw, str) and _looks_like_wsl_absolute(cwd_raw):
        raise RunRefusal(
            5,
            f"manifest cwd uses a WSL/POSIX path ({cwd_raw!r}); regenerate the "
            "manifest from the native Windows checkout",
        )
    if not isinstance(cwd_raw, str) or not Path(cwd_raw).is_absolute():
        raise RunRefusal(
            4,
            "manifest cwd is invalid; use a native absolute Windows path when "
            "running from a native Windows checkout",
        )
    if os.name == "nt" and not Path(cwd_raw).is_dir():
        raise RunRefusal(5, f"manifest cwd does not exist on this Windows host: {cwd_raw}")
    expected_root = _expected_run_root(Path(cwd_raw), direction_id, run_id)
    if manifest_path.parent != expected_root:
        raise RunRefusal(5, "manifest path is not owned by its direction and run")
    expected_claim = _claim_digest(
        direction_id=direction_id,
        code_sha=_validate_sha(manifest.get("code_sha"), "code_sha"),
        command_sha256=str(manifest.get("command_sha256")),
    )
    if manifest.get("claim_sha256") != expected_claim:
        raise RunRefusal(4, "manifest launch claim digest is invalid")
    return expected_root.parents[1]


def _claim_path(manifest_path: Path, manifest: Mapping[str, Any]) -> Path:
    direction_root = _manifest_direction_root(manifest_path, manifest)
    return direction_root / CLAIM_DIRECTORY / f"{manifest['claim_sha256']}.json"


def _claim_manifest_ref(manifest: Mapping[str, Any]) -> str:
    return f"exp/{manifest['run_id']}/manifest.json"


def _read_bound_claim(path: Path, manifest: Mapping[str, Any]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    claim = _read_json(path)
    expected = {
        "claim_sha256": manifest["claim_sha256"],
        "direction_id": manifest["direction_id"],
        "code_sha": manifest["code_sha"],
        "command_sha256": manifest["command_sha256"],
    }
    for key, value in expected.items():
        if claim.get(key) != value:
            raise RunRefusal(4, f"direction claim binding changed: {key}")
    if claim.get("manifest_ref") != _claim_manifest_ref(
        {"run_id": str(claim.get("run_id", ""))}
    ):
        raise RunRefusal(4, "direction claim manifest reference is invalid")
    return claim


def _claim_is_for_manifest(
    claim: Mapping[str, Any],
    manifest: Mapping[str, Any],
    execution_token: str | None = None,
) -> bool:
    if claim.get("manifest_ref") != _claim_manifest_ref(manifest):
        return False
    return execution_token is None or claim.get("execution_token") == execution_token


def _write_claim(
    path: Path,
    manifest: Mapping[str, Any],
    *,
    status: str,
    execution_token: str,
) -> None:
    process = manifest.get("process")
    identity = None
    if isinstance(process, Mapping) and isinstance(process.get("pid"), int):
        identity = {
            key: process.get(key)
            for key in (
                "pid",
                "process_group_id",
                "linux_boot_id",
                "proc_start_ticks",
                "identity_persisted_at",
            )
        }
    descendant_identities: list[dict[str, Any]] = []
    if path.exists():
        existing = _read_json(path)
        if _claim_is_for_manifest(existing, manifest, execution_token):
            raw_descendants = existing.get("descendant_identities")
            if isinstance(raw_descendants, list) and all(
                isinstance(value, dict) for value in raw_descendants
            ):
                descendant_identities = [dict(value) for value in raw_descendants]
    _atomic_write_json(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "claim_sha256": manifest["claim_sha256"],
            "direction_id": manifest["direction_id"],
            "run_id": manifest["run_id"],
            "code_sha": manifest["code_sha"],
            "command_sha256": manifest["command_sha256"],
            "manifest_ref": _claim_manifest_ref(manifest),
            "status": status,
            "execution_token": execution_token,
            "process_identity": identity,
            "descendant_identities": descendant_identities,
            "updated_at": _utc_now(),
        },
    )

def _state_input(path: Path, document: Mapping[str, Any]) -> Path:
    descriptor, raw_path = tempfile.mkstemp(prefix=f".{path.name}.input.", suffix=".json", dir=path.parent)
    os.close(descriptor)
    input_path = Path(raw_path)
    _atomic_write_json(input_path, document)
    return input_path


def _state_call(
    operation: str,
    *,
    kind: str,
    path: Path,
    writer: str,
    document: Mapping[str, Any],
    expected_revision: int | None = None,
) -> None:
    if not STATE_SCRIPT.exists():
        raise RunRefusal(1, f"state helper is unavailable: {STATE_SCRIPT}")
    input_path = _state_input(path, document)
    try:
        command = [
            sys.executable,
            str(STATE_SCRIPT),
            operation,
            "--kind",
            kind,
            "--path",
            str(path),
            "--writer",
            writer,
            "--input",
            str(input_path),
        ]
        if expected_revision is not None:
            command.extend(["--expected-revision", str(expected_revision)])
        completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    finally:
        try:
            input_path.unlink()
        except FileNotFoundError:
            pass
    if completed.returncode != 0:
        code = completed.returncode if completed.returncode in {1, 2, 3, 4, 5, 6, 7, 8} else 1
        message = completed.stderr.strip() or completed.stdout.strip() or f"state helper exited {code}"
        raise RunRefusal(code, message)


def _initialize_manifest(path: Path, document: Mapping[str, Any]) -> None:
    _state_call(
        "initialize",
        kind="run_manifest",
        path=path,
        writer=str(document["writer"]),
        document=document,
    )


def _replace_manifest(path: Path, document: Mapping[str, Any], expected_revision: int) -> None:
    _state_call(
        "replace",
        kind="run_manifest",
        path=path,
        writer=str(document["writer"]),
        document=document,
        expected_revision=expected_revision,
    )




def _replace_held(
    path: Path, current: Mapping[str, Any], updated: Mapping[str, Any]
) -> dict[str, Any]:
    replacement = dict(updated)
    revision = int(current.get("revision", 0))
    replacement["revision"] = revision + 1
    replacement["updated_at"] = _utc_now()
    _replace_manifest(path, replacement, revision)
    return replacement


def _validate_estimate(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RunInputError("estimate must be a JSON object")
    wall = _positive_number(raw.get("wall_seconds"), "estimate.wall_seconds")
    peak = _positive_number(raw.get("peak_memory_gib"), "estimate.peak_memory_gib")
    basis = raw.get("basis")
    if not isinstance(basis, str) or not basis.strip():
        raise RunInputError("estimate.basis is required")
    workers = _positive_int(raw.get("workers", 1), "estimate.workers")
    threads = _positive_int(raw.get("threads_per_worker", 1), "estimate.threads_per_worker")
    result: dict[str, Any] = dict(raw)
    result.update(
        {
            "wall_seconds": int(wall) if wall.is_integer() else wall,
            "peak_memory_gib": peak,
            "basis": basis,
            "workers": workers,
            "threads_per_worker": threads,
        }
    )
    return result


def _assess(
    snapshot: Mapping[str, Any],
    *,
    direction_id: str,
    run_id: str,
    estimate: Mapping[str, Any],
) -> dict[str, Any]:
    return resource_preflight.assess_snapshot(
        snapshot,
        direction_id=direction_id,
        run_id=run_id,
        workers=int(estimate["workers"]),
        threads_per_worker=int(estimate["threads_per_worker"]),
        estimated_wall_seconds=estimate["wall_seconds"],
        estimated_peak_gib=estimate["peak_memory_gib"],
        basis=str(estimate["basis"]),
    )


def _make_outputs(root: Path) -> dict[str, str]:
    for name in OUTPUT_NAMES.values():
        target = _confined_path(root, name, allow_root=False)
        if name.endswith(".log"):
            if target.exists() and target.is_symlink():
                raise RunRefusal(5, f"output log is a symlink: {target}")
        else:
            if target.exists() and target.is_symlink():
                raise RunRefusal(5, f"output directory is a symlink: {target}")
            target.mkdir(parents=False, exist_ok=True)
    return dict(OUTPUT_NAMES)


def _make_runner_spec(root: Path, manifest: Mapping[str, Any]) -> str:
    spec = {
        "schema_version": SCHEMA_VERSION,
        "command": manifest["command"],
        "command_sha256": manifest["command_sha256"],
        "cwd": manifest["cwd"],
        "git_branch": manifest.get("_git_branch"),
        "output_root": str(root),
        "outputs": manifest["outputs"],
        "preflight_sha256": manifest.get("_preflight_sha256"),
    }
    path = root / "runner-spec.json"
    _atomic_write_json(path, spec)
    return _sha256_file(path)


def _verify_manifest_provenance(
    manifest_path: Path, root: Path, manifest: Mapping[str, Any]
) -> None:
    _manifest_direction_root(manifest_path, manifest)
    command = manifest.get("command")
    if (
        not isinstance(command, list)
        or not all(isinstance(part, str) for part in command)
        or _command_digest(command) != manifest.get("command_sha256")
    ):
        raise RunRefusal(4, "manifest command digest is invalid")
    _validate_native_command(command)
    parameters = manifest.get("parameters")
    if (
        not isinstance(parameters, Mapping)
        or _parameters_digest(parameters) != manifest.get("parameters_sha256")
    ):
        raise RunRefusal(4, "manifest parameter digest is invalid")
    resources = manifest.get("resources")
    if not isinstance(resources, Mapping) or resources.get("preflight_ref") != "preflight.json":
        raise RunRefusal(4, "manifest resource evidence is invalid")
    preflight_sha = resources.get("preflight_sha256")
    runner_spec_sha = resources.get("runner_spec_sha256")
    if (
        not isinstance(preflight_sha, str)
        or re.fullmatch(r"[0-9a-f]{64}", preflight_sha) is None
        or not isinstance(runner_spec_sha, str)
        or re.fullmatch(r"[0-9a-f]{64}", runner_spec_sha) is None
    ):
        raise RunRefusal(4, "manifest resource evidence hashes are invalid")
    preflight_path = _confined_path(root, "preflight.json")
    runner_spec_path = _confined_path(root, "runner-spec.json")
    if (
        not preflight_path.is_file()
        or _sha256_file(preflight_path) != preflight_sha
        or not runner_spec_path.is_file()
        or _sha256_file(runner_spec_path) != runner_spec_sha
    ):
        raise RunRefusal(4, "run evidence hash does not match the observed files")
    runner_spec = _read_json(runner_spec_path)
    expected = {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "command_sha256": manifest["command_sha256"],
        "cwd": manifest["cwd"],
        "output_root": str(root),
        "outputs": manifest["outputs"],
        "preflight_sha256": preflight_sha,
    }
    for key, value in expected.items():
        if runner_spec.get(key) != value:
            raise RunRefusal(4, f"runner specification changed: {key}")
    branch = runner_spec.get("git_branch")
    if not isinstance(branch, str) or not branch.startswith("omp/"):
        raise RunRefusal(4, "runner specification Git branch is invalid")


def _review_subject(manifest: Mapping[str, Any]) -> dict[str, Any]:
    estimate = dict(manifest["estimate"])
    resources = manifest["resources"]
    estimate["workers"] = resources["workers"]
    estimate["threads_per_worker"] = resources["threads_per_worker"]
    return {
        "schema_version": SCHEMA_VERSION,
        "direction_id": manifest["direction_id"],
        "run_id": manifest["run_id"],
        "assignment_id": manifest["assignment_id"],
        "argv": manifest["command"],
        "code_sha": manifest["code_sha"],
        "parameters": manifest["parameters"],
        "estimate": estimate,
    }


def _validate_review_document(
    review: Mapping[str, Any], manifest: Mapping[str, Any]
) -> None:
    if review.get("schema_version") != SCHEMA_VERSION:
        raise RunRefusal(4, "review evidence schema_version is invalid")
    if review.get("reviewer") != "hmasd-reviewer":
        raise RunRefusal(4, "performance evidence is not from hmasd-reviewer")
    if review.get("assignment_id") != manifest.get("assignment_id"):
        raise RunRefusal(4, "review evidence assignment does not match")
    if review.get("status") not in {"COMPLETED", "FAILED", "UNAVAILABLE"}:
        raise RunRefusal(4, "review evidence status is invalid")
    for key in ("attempt_id", "summary"):
        value = review.get(key)
        if not isinstance(value, str) or not value.strip():
            raise RunRefusal(4, f"review evidence {key} is required")
    observed_at = review.get("observed_at")
    if not isinstance(observed_at, str) or TIMESTAMP_RE.fullmatch(observed_at) is None:
        raise RunRefusal(4, "review evidence observed_at is invalid")
    expected_subject = _sha256_bytes(_canonical_json(_review_subject(manifest)))
    if review.get("subject_sha256") != expected_subject:
        raise RunRefusal(4, "review evidence is not bound to the requested run")


def _read_observed_review(
    raw_path: str | None, manifest: Mapping[str, Any]
) -> tuple[bytes, dict[str, Any]]:
    if raw_path is None:
        raise RunRefusal(4, "observed hmasd-reviewer attempt evidence is required")
    path = _safe_resolve(Path(raw_path))
    if path.is_symlink() or not path.is_file():
        raise RunRefusal(4, "review evidence must be an existing regular file")
    try:
        payload = path.read_bytes()
        review = json.loads(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunRefusal(4, f"review evidence is invalid: {exc}") from exc
    if not isinstance(review, dict):
        raise RunRefusal(4, "review evidence must be a JSON object")
    _validate_review_document(review, manifest)
    return payload, review


def _review_and_request(
    root: Path, manifest: Mapping[str, Any], evidence_path: str | None
) -> None:
    evidence_bytes, review = _read_observed_review(evidence_path, manifest)
    review_path = root / "review-attempt.json"
    _atomic_write_bytes(review_path, evidence_bytes)
    review_sha = _sha256_file(review_path)
    frozen = {
        "schema_version": SCHEMA_VERSION,
        "direction_id": manifest["direction_id"],
        "run_id": manifest["run_id"],
        "argv": manifest["command"],
        "code_sha": manifest["code_sha"],
        "parameters": manifest["parameters"],
        "estimates": manifest["estimate"],
        "evidence_shas": [review_sha],
        "evidence_sha256": review_sha,
    }
    request = dict(frozen)
    request["request_sha256"] = _sha256_bytes(_canonical_json(frozen))
    request["review_attempt"] = {
        "attempted": True,
        "reviewer": "hmasd-reviewer",
        "attempt_id": review["attempt_id"],
        "observed_at": review["observed_at"],
        "status": review["status"],
        "subject_sha256": review["subject_sha256"],
        "evidence_sha256": review_sha,
        "path": "review-attempt.json",
    }
    _atomic_write_json(root / "decision-request.json", request)


def _frozen_request(manifest: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    evidence = request.get("evidence_shas")
    if not isinstance(evidence, list) or not all(isinstance(value, str) for value in evidence):
        raise RunRefusal(4, "decision request evidence is invalid")
    return {
        "schema_version": SCHEMA_VERSION,
        "direction_id": manifest["direction_id"],
        "run_id": manifest["run_id"],
        "argv": manifest["command"],
        "code_sha": manifest["code_sha"],
        "parameters": manifest["parameters"],
        "estimates": manifest["estimate"],
        "evidence_shas": evidence,
        "evidence_sha256": request.get("evidence_sha256"),
    }


def _validate_decision_request(root: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    request = _read_json(root / "decision-request.json")
    frozen = _frozen_request(manifest, request)
    if request.get("request_sha256") != _sha256_bytes(_canonical_json(frozen)):
        raise RunRefusal(4, "frozen decision request changed")
    for key, value in frozen.items():
        if request.get(key) != value:
            raise RunRefusal(4, f"frozen decision request field changed: {key}")
    review_ref = request.get("review_attempt")
    if not isinstance(review_ref, Mapping) or review_ref.get("path") != "review-attempt.json":
        raise RunRefusal(4, "review-attempt evidence reference changed")
    evidence_path = _confined_path(root, review_ref["path"])
    if not evidence_path.is_file():
        raise RunRefusal(4, "review-attempt evidence is missing")
    evidence_sha = _sha256_file(evidence_path)
    if (
        request.get("evidence_sha256") != evidence_sha
        or request.get("evidence_shas") != [evidence_sha]
        or review_ref.get("evidence_sha256") != evidence_sha
    ):
        raise RunRefusal(4, "review-attempt evidence changed")
    try:
        review = _read_json(evidence_path)
    except RunInputError as exc:
        raise RunRefusal(4, str(exc)) from exc
    _validate_review_document(review, manifest)
    for key in (
        "reviewer",
        "attempt_id",
        "observed_at",
        "status",
        "subject_sha256",
    ):
        if review_ref.get(key) != review.get(key):
            raise RunRefusal(4, f"review-attempt observation changed: {key}")
    if review_ref.get("attempted") is not True:
        raise RunRefusal(4, "review-attempt observation is invalid")
    return request


def _validate_approval(
    root: Path, manifest: Mapping[str, Any], approval_path: Path
) -> dict[str, Any]:
    request = _validate_decision_request(root, manifest)
    if approval_path.is_symlink():
        raise RunRefusal(5, "approval path must not be a symlink")
    approval = _read_json(approval_path)
    if approval.get("consumed") is True:
        raise RunRefusal(6, "approval was already consumed")
    if approval.get("approved") is not True:
        raise RunRefusal(8, "explicit approval is required")
    required = (
        "request_sha256",
        "direction_id",
        "run_id",
        "argv",
        "code_sha",
        "parameters",
        "estimates",
        "evidence_sha256",
    )
    for key in required:
        if approval.get(key) != request.get(key):
            raise RunRefusal(4, f"approval does not bind frozen field: {key}")
    if approval.get("evidence_shas", request.get("evidence_shas")) != request.get(
        "evidence_shas"
    ):
        raise RunRefusal(4, "approval evidence differs from frozen evidence")
    return approval


def _consume_approval(root: Path, manifest: Mapping[str, Any], approval_path: Path) -> None:
    approval = _validate_approval(root, manifest, approval_path)
    consumed = dict(approval)
    consumed["consumed"] = True
    consumed["consumed_at"] = _utc_now()
    _atomic_write_json(approval_path, consumed)


def _read_boot_id() -> str | None:
    if os.name == "nt":
        class SYSTEM_TIMEOFDAY_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("boot_time", ctypes.c_longlong),
                ("current_time", ctypes.c_longlong),
                ("time_zone_bias", ctypes.c_longlong),
                ("current_time_zone_id", ctypes.c_ulong),
                ("reserved", ctypes.c_ulong),
                ("boot_time_bias", ctypes.c_ulonglong),
                ("sleep_time_bias", ctypes.c_ulonglong),
            ]

        value = SYSTEM_TIMEOFDAY_INFORMATION()
        status = _windows_ntdll().NtQuerySystemInformation(
            3, ctypes.byref(value), ctypes.sizeof(value), None
        )
        if status != 0:
            return None
        return f"windows:{int(value.boot_time):016x}"
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _proc_start_ticks(pid: int) -> int | None:
    if os.name == "nt":
        process_query_limited_information = 0x1000
        kernel32 = _windows_kernel32()
        handle = kernel32.OpenProcess(
            process_query_limited_information, False, pid
        )
        if not handle:
            return None
        try:
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            if not kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                return None
            return (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
        finally:
            kernel32.CloseHandle(handle)
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    closing = raw.rfind(")")
    if closing < 0:
        return None
    fields = raw[closing + 2 :].split()
    if len(fields) <= 19:
        return None
    try:
        return int(fields[19])
    except ValueError:
        return None


def _proc_command_digest(pid: int) -> str | None:
    if os.name == "nt":
        return None
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return None
    if not raw:
        return None
    values = raw.rstrip(b"\0").split(b"\0")
    return _sha256_bytes(b"\0".join(values))


def _proc_pgid(pid: int) -> int | None:
    if os.name == "nt":
        return pid if _proc_start_ticks(pid) is not None else None
    try:
        return os.getpgid(pid)
    except OSError:
        return None


def _proc_sid(pid: int) -> int | None:
    if os.name == "nt":
        return 0 if _proc_start_ticks(pid) is not None else None
    try:
        return os.getsid(pid)
    except OSError:
        return None


def _group_pids(pgid: int) -> list[int]:
    if os.name == "nt":
        th32cs_snapprocess = 0x00000002
        invalid_handle_value = ctypes.c_void_p(-1).value

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_wchar * 260),
            ]

        kernel32 = _windows_kernel32()
        snapshot = kernel32.CreateToolhelp32Snapshot(
            th32cs_snapprocess, 0
        )
        if snapshot == invalid_handle_value:
            return []
        parents: dict[int, int] = {}
        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(entry)
            kernel32.Process32FirstW.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(PROCESSENTRY32W),
            ]
            kernel32.Process32FirstW.restype = wintypes.BOOL
            kernel32.Process32NextW.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(PROCESSENTRY32W),
            ]
            kernel32.Process32NextW.restype = wintypes.BOOL
            if kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                while True:
                    parents[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
                    if not kernel32.Process32NextW(
                        snapshot, ctypes.byref(entry)
                    ):
                        break
        finally:
            kernel32.CloseHandle(snapshot)

        members = {pgid}
        changed = True
        while changed:
            changed = False
            for pid, parent in parents.items():
                if pid not in members and parent in members:
                    members.add(pid)
                    changed = True
        return sorted(pid for pid in members if pid in parents)

    pids: list[int] = []
    try:
        entries = os.listdir("/proc")
    except OSError:
        return pids
    for entry in entries:
        if not entry.isdigit():
            continue
        pid = int(entry)
        if _proc_pgid(pid) == pgid:
            pids.append(pid)
    return pids


def _claim_descendant_identities(claim: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if claim is None:
        return []
    raw = claim.get("descendant_identities")
    if not isinstance(raw, list):
        return []
    return [dict(value) for value in raw if isinstance(value, Mapping)]


def _capture_descendant_identities(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    process = manifest.get("process")
    if not isinstance(process, Mapping):
        return []
    pid = process.get("pid")
    pgid = process.get("process_group_id")
    start_ticks = process.get("proc_start_ticks")
    boot_id = process.get("linux_boot_id")
    if (
        not isinstance(pid, int)
        or not isinstance(pgid, int)
        or not isinstance(start_ticks, int)
        or not isinstance(boot_id, str)
        or boot_id != _read_boot_id()
        or _proc_start_ticks(pid) != start_ticks
        or (os.name != "nt" and _proc_pgid(pid) != pgid)
        or (
            os.name != "nt"
            and _proc_command_digest(pid) != manifest.get("command_sha256")
        )
    ):
        return []
    captured: list[dict[str, Any]] = []
    for descendant_pid in _group_pids(pgid):
        if descendant_pid == pid:
            continue
        descendant_start = _proc_start_ticks(descendant_pid)
        descendant_sid = _proc_sid(descendant_pid)
        if (
            descendant_start is None
            or descendant_sid is None
            or (os.name != "nt" and _proc_pgid(descendant_pid) != pgid)
        ):
            continue
        captured.append(
            {
                "pid": descendant_pid,
                "process_group_id": pgid,
                "session_id": descendant_sid,
                "linux_boot_id": boot_id,
                "proc_start_ticks": descendant_start,
            }
        )
    return captured


def _merge_descendant_identities(
    existing: Sequence[Mapping[str, Any]],
    captured: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_identity: dict[tuple[int, int], dict[str, Any]] = {}
    for value in (*existing, *captured):
        pid = value.get("pid")
        start_ticks = value.get("proc_start_ticks")
        if isinstance(pid, int) and isinstance(start_ticks, int):
            by_identity[(pid, start_ticks)] = dict(value)
    return [by_identity[key] for key in sorted(by_identity)]


def _persist_descendant_provenance(
    claim_path: Path,
    manifest: Mapping[str, Any],
    execution_token: str,
) -> list[dict[str, Any]]:
    with _path_lock(claim_path):
        claim = _read_bound_claim(claim_path, manifest)
        if (
            claim is None
            or claim.get("status") != "RUNNING"
            or not _claim_is_for_manifest(claim, manifest, execution_token)
        ):
            raise RunRefusal(6, "direction claim changed while recording descendants")
        existing = _claim_descendant_identities(claim)
        merged = _merge_descendant_identities(
            existing, _capture_descendant_identities(manifest)
        )
        if merged != existing:
            claim["descendant_identities"] = merged
            claim["updated_at"] = _utc_now()
            _atomic_write_json(claim_path, claim)
        return merged


def _descendant_group_is_tied(
    manifest: Mapping[str, Any],
    group_pids: Sequence[int],
    descendant_identities: Sequence[Mapping[str, Any]],
) -> bool:
    process = manifest.get("process")
    if not isinstance(process, Mapping):
        return False
    pgid = process.get("process_group_id")
    boot_id = process.get("linux_boot_id")
    if (
        not group_pids
        or not isinstance(pgid, int)
        or not isinstance(boot_id, str)
        or boot_id != _read_boot_id()
    ):
        return False
    by_pid = {
        value.get("pid"): value
        for value in descendant_identities
        if isinstance(value.get("pid"), int)
    }
    for pid in group_pids:
        identity = by_pid.get(pid)
        if (
            identity is None
            or identity.get("linux_boot_id") != boot_id
            or identity.get("process_group_id") != pgid
            or identity.get("proc_start_ticks") != _proc_start_ticks(pid)
            or (os.name != "nt" and identity.get("session_id") != _proc_sid(pid))
            or (os.name != "nt" and _proc_pgid(pid) != pgid)
        ):
            return False
    return True


def _observe_process_identity(
    manifest: Mapping[str, Any],
    descendant_identities: Sequence[Mapping[str, Any]] = (),
) -> tuple[str, bool]:
    process = manifest.get("process")
    if not isinstance(process, Mapping):
        return IDENTITY_UNRECORDED, False
    pid = process.get("pid")
    pgid = process.get("process_group_id")
    start_ticks = process.get("proc_start_ticks")
    if not isinstance(pid, int) or not isinstance(pgid, int) or not isinstance(start_ticks, int):
        return IDENTITY_UNRECORDED, False
    group_pids = _group_pids(pgid)
    group_live = bool(group_pids)
    if process.get("linux_boot_id") != _read_boot_id():
        return IDENTITY_REUSED, group_live
    observed_start = _proc_start_ticks(pid)
    if observed_start is None:
        if not group_live:
            return IDENTITY_GONE, False
        if _descendant_group_is_tied(manifest, group_pids, descendant_identities):
            return IDENTITY_DESCENDANTS, True
        return IDENTITY_REUSED, True
    if observed_start != start_ticks or (os.name != "nt" and _proc_pgid(pid) != pgid):
        return IDENTITY_REUSED, group_live
    digest = _proc_command_digest(pid)
    if digest is not None and digest != manifest.get("command_sha256"):
        return IDENTITY_REUSED, group_live
    return IDENTITY_MATCH, group_live


def _wait_group_quiescent(pgid: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _group_pids(pgid):
            return True
        time.sleep(0.02)
    return not _group_pids(pgid)


def _terminate_windows_pid(pid: int) -> None:
    process_terminate = 0x0001
    kernel32 = _windows_kernel32()
    handle = kernel32.OpenProcess(process_terminate, False, pid)
    if not handle:
        if _proc_start_ticks(pid) is None:
            return
        raise RunRefusal(5, f"cannot open owned Windows process {pid} for termination")
    try:
        if not kernel32.TerminateProcess(handle, 1):
            raise RunRefusal(5, f"cannot terminate owned Windows process {pid}")
    finally:
        kernel32.CloseHandle(handle)


def _terminate_new_group(pgid: int, *, grace: float = 1.0) -> None:
    if os.name == "nt":
        for pid in reversed(_group_pids(pgid)):
            _terminate_windows_pid(pid)
        if not _wait_group_quiescent(pgid):
            raise RunRefusal(5, f"Windows process tree {pgid} did not become quiescent")
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError as exc:
        raise RunRefusal(5, f"cannot terminate process group {pgid}: {exc}") from exc
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline and _group_pids(pgid):
        time.sleep(0.02)
    if _group_pids(pgid):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if not _wait_group_quiescent(pgid):
        raise RunRefusal(5, f"process group {pgid} did not become quiescent")


def _terminate_owned_group(
    manifest: Mapping[str, Any],
    descendant_identities: Sequence[Mapping[str, Any]] = (),
    *,
    grace: float = 1.0,
) -> None:
    process = manifest.get("process")
    if not isinstance(process, Mapping) or not isinstance(process.get("process_group_id"), int):
        raise RunRefusal(6, "running manifest has no process-group identity")
    pgid = int(process["process_group_id"])
    identity, group_live = _observe_process_identity(manifest, descendant_identities)
    if identity == IDENTITY_GONE and not group_live:
        return
    if identity in {IDENTITY_REUSED, IDENTITY_UNRECORDED}:
        raise RunRefusal(6, "process identity was reused or cannot be proven; no signal sent")
    if os.name == "nt":
        captured = _merge_descendant_identities(
            descendant_identities, _capture_descendant_identities(manifest)
        )
        group_pids = _group_pids(pgid)
        descendants = [pid for pid in group_pids if pid != process.get("pid")]
        if descendants and not _descendant_group_is_tied(
            manifest, descendants, captured
        ):
            raise RunRefusal(
                6, "Windows descendant identity cannot be proven; no process was terminated"
            )
        for pid in reversed(group_pids):
            _terminate_windows_pid(pid)
        if not _wait_group_quiescent(pgid):
            raise RunRefusal(5, f"Windows process tree {pgid} did not become quiescent")
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        if _wait_group_quiescent(pgid):
            return
    except PermissionError as exc:
        raise RunRefusal(5, f"cannot terminate process group {pgid}: {exc}") from exc
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline and _group_pids(pgid):
        time.sleep(0.02)
    if _group_pids(pgid):
        identity, _group_live = _observe_process_identity(
            manifest, descendant_identities
        )
        if identity in {IDENTITY_REUSED, IDENTITY_UNRECORDED}:
            raise RunRefusal(6, "process-group identity changed; no further signal sent")
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if not _wait_group_quiescent(pgid):
        raise RunRefusal(5, f"process group {pgid} did not become quiescent")


def _open_output(root: Path, name: str) -> Any:
    path = _confined_path(root, name)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise RunRefusal(5, f"cannot open confined output {path}: {exc}") from exc
    return os.fdopen(descriptor, "wb", closefd=True)


class _WindowsSuspendedGate:
    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        self.process = process


def _spawn_gated_child(
    manifest: Mapping[str, Any], stdout: Any, stderr: Any
) -> tuple[subprocess.Popen[bytes], int | _WindowsSuspendedGate]:
    if os.name == "nt":
        create_suspended = 0x00000004
        child = subprocess.Popen(
            manifest["command"],
            cwd=manifest["cwd"],
            shell=False,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | create_suspended,
            stdout=stdout,
            stderr=stderr,
        )
        return child, _WindowsSuspendedGate(child)

    read_fd, write_fd = os.pipe()
    try:
        child = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "_exec-gate",
                "--gate-fd",
                str(read_fd),
                "--",
                *manifest["command"],
            ],
            cwd=manifest["cwd"],
            shell=False,
            start_new_session=True,
            stdout=stdout,
            stderr=stderr,
            pass_fds=(read_fd,),
        )
    except BaseException:
        os.close(read_fd)
        os.close(write_fd)
        raise
    os.close(read_fd)
    return child, write_fd


def _close_gate(gate: int | _WindowsSuspendedGate) -> None:
    if isinstance(gate, _WindowsSuspendedGate):
        return
    os.close(gate)


def _release_gate(gate: int | _WindowsSuspendedGate, timeout: float = 5.0) -> bool:
    if isinstance(gate, _WindowsSuspendedGate):
        process_handle = int(getattr(gate.process, "_handle"))
        return _windows_ntdll().NtResumeProcess(process_handle) == 0
    os.write(gate, b"\x01")
    return True


def _exec_gate(args: argparse.Namespace) -> int:
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        return 125
    if args.gate_path:
        gate_path = Path(args.gate_path)
        released = b""
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            try:
                released = gate_path.read_bytes()
            except FileNotFoundError:
                return 125
            except OSError:
                return 125
            if released:
                break
            time.sleep(0.01)
        try:
            gate_path.unlink()
        except OSError:
            pass
    else:
        try:
            released = os.read(args.gate_fd, 1)
        except OSError:
            return 125
        finally:
            try:
                os.close(args.gate_fd)
            except OSError:
                pass
    if released != b"\x01":
        return 125
    if os.name == "nt":
        try:
            return subprocess.call(command, shell=False)
        except OSError as exc:
            print(f"hmasd exec gate failed: {exc}", file=sys.stderr)
            return 126
    try:
        os.execvpe(command[0], command, os.environ)
    except OSError as exc:
        print(f"hmasd exec gate failed: {exc}", file=sys.stderr)
        return 126


def _manifest_process_base() -> dict[str, Any]:
    return {
        "execution_token": None,
        "pid": None,
        "process_group_id": None,
        "linux_boot_id": None,
        "proc_start_ticks": None,
        "identity_persisted_at": None,
        "group_quiescent": None,
        "started_at": None,
        "ended_at": None,
        "exit_code": None,
        "terminal_reason": None,
    }


def _prepare(args: argparse.Namespace) -> int:
    direction_id = _validate_identifier(args.direction, "direction")
    run_id = _validate_identifier(args.run_id, "run_id")
    assignment_id = _validate_assignment(args.assignment)
    code_sha = _validate_sha(args.code_sha, "code_sha")
    try:
        parameters = json.loads(args.parameters)
    except json.JSONDecodeError as exc:
        raise RunInputError(f"parameters must be valid JSON: {exc}") from exc
    if not isinstance(parameters, dict):
        raise RunInputError("parameters must be a JSON object")
    cwd = _safe_resolve(Path.cwd())
    branch = _require_omp_branch(cwd)
    observed_head = _git_head(cwd)
    if observed_head != code_sha:
        raise RunRefusal(
            5,
            f"supplied code SHA {code_sha} does not match cwd HEAD {observed_head}",
        )
    try:
        estimate = _validate_estimate(json.loads(args.estimate))
    except json.JSONDecodeError as exc:
        raise RunInputError(f"estimate must be valid JSON: {exc}") from exc
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command or any(not isinstance(part, str) for part in command):
        raise RunInputError("an exact argv is required after --")
    _validate_native_command(command)
    output_root = _validate_output_root(
        args.output_root,
        cwd=cwd,
        direction_id=direction_id,
        run_id=run_id,
    )
    if _reclaim_legacy_unsafe_prepare_root(
        output_root, direction_id=direction_id, run_id=run_id
    ):
        print("reclaimed legacy unsafe prepare root", file=sys.stderr)
    if output_root.exists() and any(output_root.iterdir()):
        raise RunRefusal(6, f"output root is not empty: {output_root}")

    snapshot = capture_snapshot()
    try:
        assessment = _assess(snapshot, direction_id=direction_id, run_id=run_id, estimate=estimate)
    except ValueError as exc:
        raise RunRefusal(6, str(exc)) from exc
    if not assessment["memory_safe"]:
        print(
            "resource preflight refused: unsafe memory plan "
            + _canonical_json(assessment).decode("utf-8"),
            file=sys.stderr,
        )
        return 6

    output_root.mkdir(parents=True, exist_ok=True)
    outputs = _make_outputs(output_root)
    preflight_path = output_root / "preflight.json"
    _atomic_write_json(preflight_path, assessment)
    preflight_sha = _sha256_file(preflight_path)

    command_sha = _command_digest(command)
    writer = f"Operator-{run_id}"
    now = _utc_now()
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "revision": 1,
        "writer": writer,
        "run_id": run_id,
        "direction_id": direction_id,
        "assignment_id": assignment_id,
        "operator_identity": writer,
        "status": "PREPARED",
        "command": command,
        "command_sha256": command_sha,
        "claim_sha256": _claim_digest(
            direction_id=direction_id,
            code_sha=code_sha,
            command_sha256=command_sha,
        ),
        "cwd": str(cwd),
        "parameters": parameters,
        "parameters_sha256": _parameters_digest(parameters),
        "code_sha": code_sha,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.system().lower(),
            "hostname": platform.node(),
            "captured_variables": {},
        },
        "estimate": {
            "wall_seconds": estimate["wall_seconds"],
            "basis": estimate["basis"],
            "peak_memory_gib": estimate["peak_memory_gib"],
        },
        "resources": {
            "preflight_ref": "preflight.json",
            "preflight_sha256": preflight_sha,
            "runner_spec_sha256": "",
            "workers": estimate["workers"],
            "threads_per_worker": estimate["threads_per_worker"],
            "memory_safe": True,
        },
        "process": _manifest_process_base(),
        "outputs": outputs,
        "observed_metrics": {},
        "created_at": now,
        "updated_at": now,
    }
    manifest_for_spec = dict(manifest)
    manifest_for_spec["_preflight_sha256"] = preflight_sha
    manifest_for_spec["_git_branch"] = branch
    runner_spec_sha = _make_runner_spec(output_root, manifest_for_spec)
    manifest["resources"]["runner_spec_sha256"] = runner_spec_sha
    _initialize_manifest(output_root / "manifest.json", manifest)
    if float(estimate["wall_seconds"]) > 7200.0:
        _review_and_request(output_root, manifest, args.review_evidence)
        return 8
    return 0


def _execute(args: argparse.Namespace) -> int:
    manifest_path, root, initial = _load_manifest(args.manifest)
    _verify_manifest_provenance(manifest_path, root, initial)
    claim_path = _claim_path(manifest_path, initial)
    result_path = root / OPERATOR_RESULT_NAME
    approval_path = _safe_resolve(Path(args.approval)) if args.approval else None
    stdout: Any = None
    stderr: Any = None
    child: subprocess.Popen[bytes] | None = None
    gate_write_fd: int | _WindowsSuspendedGate | None = None
    descendant_identities: list[dict[str, Any]] = []
    terminal_recorded = False
    owned_manifest: dict[str, Any] | None = None
    owned_pgid: int | None = None
    cancelled = False
    previous_handlers: dict[int, Any] = {}

    def terminate_for_signal(signum: int, _frame: Any) -> None:
        nonlocal cancelled
        cancelled = True
        if child is not None and child.poll() is None and owned_pgid is not None:
            try:
                if os.name == "nt":
                    child.terminate()
                else:
                    os.killpg(owned_pgid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass

    def running_document(current: Mapping[str, Any], token: str) -> dict[str, Any]:
        running = dict(current)
        running["status"] = "RUNNING"
        running["process"] = dict(
            current["process"],
            execution_token=token,
            started_at=_utc_now(),
            terminal_reason=None,
        )
        return running

    def prestart_failure(
        current: Mapping[str, Any],
        *,
        reason: str,
        memory_safe: bool | None = None,
    ) -> dict[str, Any]:
        failed = dict(current)
        failed["status"] = "FAILED"
        if memory_safe is not None:
            failed["resources"] = dict(current["resources"], memory_safe=memory_safe)
        failed["process"] = dict(
            current["process"],
            ended_at=_utc_now(),
            group_quiescent=True,
            terminal_reason=reason,
        )
        return failed

    try:
        with _path_lock(claim_path):
            with _path_lock(manifest_path):
                manifest = _read_json(manifest_path)
                _verify_manifest_provenance(manifest_path, root, manifest)
                status = manifest.get("status")
                if status != "PREPARED":
                    raise RunRefusal(6, f"manifest is not launchable from status {status!r}")
                if args.emit_operator_result and (
                    os.path.lexists(result_path)
                    or hmasd_platform.is_reparse_or_symlink(result_path)
                ):
                    raise RunRefusal(6, "operator result path already exists")
                existing_claim = _read_bound_claim(claim_path, manifest)
                if existing_claim is not None:
                    claim_status = existing_claim.get("status")
                    if claim_status in {"RUNNING", "UNKNOWN"}:
                        raise RunRefusal(
                            6,
                            "an identical direction/code/argv claim is already "
                            f"{claim_status}",
                        )
                    if claim_status not in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                        raise RunRefusal(4, "direction claim status is invalid")

                estimate_raw = manifest.get("estimate")
                resources = manifest.get("resources")
                if not isinstance(estimate_raw, Mapping) or not isinstance(resources, Mapping):
                    raise RunInputError("manifest estimate/resources are invalid")
                estimate = dict(estimate_raw)
                estimate["workers"] = resources.get("workers")
                estimate["threads_per_worker"] = resources.get("threads_per_worker")
                wall_seconds = _positive_number(
                    estimate.get("wall_seconds"), "estimate.wall_seconds"
                )

                snapshot = capture_snapshot()
                try:
                    assessment = _assess(
                        snapshot,
                        direction_id=str(manifest["direction_id"]),
                        run_id=str(manifest["run_id"]),
                        estimate=estimate,
                    )
                except ValueError as exc:
                    raise RunRefusal(6, str(exc)) from exc
                _atomic_write_json(root / "execute-preflight.json", assessment)

                if not assessment["memory_safe"]:
                    token = secrets.token_urlsafe(32)
                    running = running_document(manifest, token)
                    _write_claim(
                        claim_path,
                        running,
                        status="RUNNING",
                        execution_token=token,
                    )
                    running = _replace_held(manifest_path, manifest, running)
                    failed = _replace_held(
                        manifest_path,
                        running,
                        prestart_failure(
                            running,
                            reason="MEMORY_REFUSED_BEFORE_START",
                            memory_safe=False,
                        ),
                    )
                    _write_claim(
                        claim_path,
                        failed,
                        status="FAILED",
                        execution_token=token,
                    )
                    return 6

                if wall_seconds > 7200.0:
                    _validate_decision_request(root, manifest)
                    if approval_path is None:
                        raise RunRefusal(8, "explicit approval is required for a long run")
                    _validate_approval(root, manifest, approval_path)

                token = secrets.token_urlsafe(32)
                running = running_document(manifest, token)
                _write_claim(
                    claim_path,
                    running,
                    status="RUNNING",
                    execution_token=token,
                )
                running = _replace_held(manifest_path, manifest, running)

                if wall_seconds > 7200.0:
                    assert approval_path is not None
                    _consume_approval(root, manifest, approval_path)

                snapshot = capture_snapshot()
                try:
                    assessment = _assess(
                        snapshot,
                        direction_id=str(manifest["direction_id"]),
                        run_id=str(manifest["run_id"]),
                        estimate=estimate,
                    )
                except ValueError as exc:
                    failed = _replace_held(
                        manifest_path,
                        running,
                        prestart_failure(
                            running,
                            reason="MEMORY_REFUSED_BEFORE_START",
                            memory_safe=False,
                        ),
                    )
                    _write_claim(
                        claim_path,
                        failed,
                        status="FAILED",
                        execution_token=token,
                    )
                    raise RunRefusal(6, str(exc)) from exc
                _atomic_write_json(root / "execute-preflight.json", assessment)
                if not assessment["memory_safe"]:
                    failed = _replace_held(
                        manifest_path,
                        running,
                        prestart_failure(
                            running,
                            reason="MEMORY_REFUSED_BEFORE_START",
                            memory_safe=False,
                        ),
                    )
                    _write_claim(
                        claim_path,
                        failed,
                        status="FAILED",
                        execution_token=token,
                    )
                    return 6

                try:
                    stdout = _open_output(root, manifest["outputs"]["stdout"])
                    stderr = _open_output(root, manifest["outputs"]["stderr"])
                except RunRefusal as exc:
                    failed = _replace_held(
                        manifest_path,
                        running,
                        prestart_failure(running, reason="OUTPUT_PATH_REFUSED"),
                    )
                    _write_claim(
                        claim_path,
                        failed,
                        status="FAILED",
                        execution_token=token,
                    )
                    return exc.code

                for signum in (signal.SIGINT, signal.SIGTERM):
                    previous_handlers[signum] = signal.getsignal(signum)
                    signal.signal(signum, terminate_for_signal)
                try:
                    child, gate_write_fd = _spawn_gated_child(manifest, stdout, stderr)
                except (OSError, ValueError) as exc:
                    failed = _replace_held(
                        manifest_path,
                        running,
                        prestart_failure(running, reason="LAUNCH_FAILED"),
                    )
                    _write_claim(
                        claim_path,
                        failed,
                        status="FAILED",
                        execution_token=token,
                    )
                    raise RunRefusal(1, f"child launch failed: {exc}") from exc

                pid = child.pid
                owned_pgid = _proc_pgid(pid)
                boot_id = _read_boot_id()
                start_ticks = _proc_start_ticks(pid)
                if owned_pgid is None or boot_id is None or start_ticks is None:
                    _close_gate(gate_write_fd)
                    gate_write_fd = None
                    child.wait(timeout=5)
                    if owned_pgid is not None and _group_pids(owned_pgid):
                        _terminate_new_group(owned_pgid)
                    failed = _replace_held(
                        manifest_path,
                        running,
                        prestart_failure(running, reason="IDENTITY_CAPTURE_FAILED"),
                    )
                    _write_claim(
                        claim_path,
                        failed,
                        status="FAILED",
                        execution_token=token,
                    )
                    raise RunRefusal(1, "unable to record child identity")

                identity = {
                    "pid": pid,
                    "process_group_id": owned_pgid,
                    "linux_boot_id": boot_id,
                    "proc_start_ticks": start_ticks,
                    "identity_persisted_at": _utc_now(),
                }
                identified = dict(running)
                identified["process"] = dict(running["process"], **identity)
                owned_manifest = _replace_held(manifest_path, running, identified)
                _write_claim(
                    claim_path,
                    owned_manifest,
                    status="RUNNING",
                    execution_token=token,
                )

                if cancelled:
                    _close_gate(gate_write_fd)
                    gate_write_fd = None
                    if child.poll() is None:
                        _terminate_new_group(owned_pgid)
                    child.wait()
                    cancelled_before_start = dict(owned_manifest)
                    cancelled_before_start["status"] = "CANCELLED"
                    cancelled_before_start["process"] = dict(
                        owned_manifest["process"],
                        ended_at=_utc_now(),
                        group_quiescent=not _group_pids(owned_pgid),
                        terminal_reason="SIGNAL_BEFORE_CHILD_RELEASE",
                    )
                    cancelled_before_start = _replace_held(
                        manifest_path, owned_manifest, cancelled_before_start
                    )
                    _write_claim(
                        claim_path,
                        cancelled_before_start,
                        status="CANCELLED",
                        execution_token=token,
                    )
                    return 1
                try:
                    release_observed = _release_gate(gate_write_fd)
                except OSError as exc:
                    _close_gate(gate_write_fd)
                    gate_write_fd = None
                    if child.poll() is None:
                        _terminate_new_group(owned_pgid)
                    child.wait()
                    failed_release = dict(owned_manifest)
                    failed_release["status"] = "FAILED"
                    failed_release["process"] = dict(
                        owned_manifest["process"],
                        ended_at=_utc_now(),
                        group_quiescent=not _group_pids(owned_pgid),
                        terminal_reason="EXEC_GATE_RELEASE_FAILED",
                    )
                    failed_release = _replace_held(
                        manifest_path, owned_manifest, failed_release
                    )
                    _write_claim(
                        claim_path,
                        failed_release,
                        status="FAILED",
                        execution_token=token,
                    )
                    raise RunRefusal(1, f"child release failed: {exc}") from exc
                else:
                    _close_gate(gate_write_fd)
                    gate_write_fd = None
                transition_observed = release_observed
                if os.name != "nt":
                    deadline = time.monotonic() + 5.0
                    while time.monotonic() < deadline:
                        digest = _proc_command_digest(pid)
                        if digest == manifest["command_sha256"] or child.poll() is not None:
                            transition_observed = True
                            break
                        time.sleep(0.005)
                if not transition_observed:
                    _terminate_new_group(owned_pgid)
                    child.wait(timeout=5)
                    unknown = dict(owned_manifest)
                    unknown["status"] = "UNKNOWN"
                    unknown["process"] = dict(
                        owned_manifest["process"],
                        ended_at=_utc_now(),
                        group_quiescent=True,
                        terminal_reason="EXEC_GATE_TRANSITION_UNOBSERVED",
                    )
                    unknown = _replace_held(manifest_path, owned_manifest, unknown)
                    _write_claim(
                        claim_path,
                        unknown,
                        status="UNKNOWN",
                        execution_token=token,
                    )
                    return 1

        assert child is not None
        assert owned_manifest is not None
        assert owned_pgid is not None
        while child.poll() is None:
            try:
                descendant_identities = _persist_descendant_provenance(
                    claim_path, owned_manifest, token
                )
            except RunRefusal:
                break
            time.sleep(0.02)
        return_code = child.wait()
        quiescence_error: RunRefusal | None = None
        if _group_pids(owned_pgid):
            try:
                _terminate_owned_group(owned_manifest, descendant_identities)
            except RunRefusal as exc:
                quiescence_error = exc
        group_quiescent = not _group_pids(owned_pgid)

        if quiescence_error is not None or not group_quiescent:
            terminal_status = "UNKNOWN"
            terminal_reason = "PROCESS_GROUP_NOT_QUIESCENT"
            wrapper_code = 1
            stored_exit_code = int(return_code) if return_code >= 0 else None
        elif cancelled:
            terminal_status = "CANCELLED"
            terminal_reason = "SIGNAL_TERMINATED"
            wrapper_code = 1
            stored_exit_code = int(return_code) if return_code >= 0 else None
        elif return_code == 0:
            terminal_status = "SUCCEEDED"
            terminal_reason = "CHILD_EXIT_0"
            wrapper_code = 0
            stored_exit_code = 0
        elif return_code < 0:
            terminal_status = "FAILED"
            terminal_reason = f"CHILD_SIGNAL_{-return_code}"
            wrapper_code = 1
            stored_exit_code = None
        else:
            terminal_status = "FAILED"
            terminal_reason = "CHILD_EXIT"
            wrapper_code = 1
            stored_exit_code = int(return_code)

        with _path_lock(claim_path):
            with _path_lock(manifest_path):
                current = _read_json(manifest_path)
                current_process = current.get("process")
                if (
                    not isinstance(current_process, Mapping)
                    or current_process.get("execution_token") != token
                ):
                    raise RunRefusal(4, "execution token changed before terminal observation")
                if current.get("status") != "RUNNING":
                    if current.get("status") == "CANCELLED":
                        return 1
                    raise RunRefusal(
                        6,
                        f"manifest changed to {current.get('status')!r} before terminal observation",
                    )
                terminal = dict(current)
                terminal["status"] = terminal_status
                terminal["process"] = dict(
                    current_process,
                    ended_at=_utc_now(),
                    exit_code=stored_exit_code,
                    group_quiescent=group_quiescent,
                    terminal_reason=terminal_reason,
                )
                terminal = _replace_held(manifest_path, current, terminal)
                _write_claim(
                    claim_path,
                    terminal,
                    status=terminal_status,
                    execution_token=token,
                )
                terminal_recorded = True
        if stdout is not None:
            stdout.close()
            stdout = None
        if stderr is not None:
            stderr.close()
            stderr = None
        if (
            args.emit_operator_result
            and terminal.get("status") == "SUCCEEDED"
            and terminal.get("process", {}).get("exit_code") == 0
            and terminal.get("process", {}).get("group_quiescent") is True
        ):
            try:
                result = _operator_result_document(
                    _safe_resolve(Path(str(terminal["cwd"]))),
                    manifest_path,
                    terminal,
                )
                hmasd_operator_result.publish_document(result_path, result)
            except (
                hmasd_operator_result.OperatorResultError,
                OSError,
                ValueError,
                TypeError,
            ) as exc:
                raise RunRefusal(1, "OPERATOR_RESULT_PUBLISH_FAILED") from exc
        return wrapper_code
    finally:
        if gate_write_fd is not None:
            try:
                _close_gate(gate_write_fd)
            except OSError:
                pass
        if child is not None:
            if child.poll() is None:
                pgid = owned_pgid if owned_pgid is not None else _proc_pgid(child.pid)
                if pgid is not None:
                    _terminate_new_group(pgid)
            child.wait()
            if (
                not terminal_recorded
                and owned_manifest is not None
                and owned_pgid is not None
                and _group_pids(owned_pgid)
            ):
                _terminate_owned_group(owned_manifest, descendant_identities)
        if stdout is not None:
            stdout.close()
        if stderr is not None:
            stderr.close()
        for signum, previous in previous_handlers.items():
            signal.signal(signum, previous)


def _reconcile(args: argparse.Namespace) -> int:
    manifest_path, _root, initial = _load_manifest(args.manifest)
    claim_path = (
        _claim_path(manifest_path, initial)
        if isinstance(initial.get("claim_sha256"), str)
        else None
    )
    with (_path_lock(claim_path) if claim_path is not None else nullcontext()):
        with _path_lock(manifest_path):
            manifest = _read_json(manifest_path)
            process = manifest.get("process")
            token = (
                str(process.get("execution_token"))
                if isinstance(process, Mapping)
                and isinstance(process.get("execution_token"), str)
                else ""
            )
            bound_claim = (
                _read_bound_claim(claim_path, manifest)
                if claim_path is not None
                else None
            )
            if manifest.get("status") == "RUNNING":
                identity, group_live = _observe_process_identity(
                    manifest, _claim_descendant_identities(bound_claim)
                )
                if identity in {IDENTITY_MATCH, IDENTITY_DESCENDANTS} and group_live:
                    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
                    return 0
                unknown = dict(manifest)
                unknown["status"] = "UNKNOWN"
                if identity == IDENTITY_REUSED:
                    reason = "PROCESS_IDENTITY_REUSED"
                    group_quiescent: bool | None = None
                elif identity == IDENTITY_UNRECORDED:
                    reason = "PROCESS_IDENTITY_NOT_PERSISTED"
                    group_quiescent = None
                else:
                    reason = "INTERRUPTED_RUNNING_OBSERVED"
                    group_quiescent = not group_live
                unknown["process"] = dict(
                    process if isinstance(process, Mapping) else {},
                    ended_at=_utc_now(),
                    group_quiescent=group_quiescent,
                    terminal_reason=reason,
                )
                manifest = _replace_held(manifest_path, manifest, unknown)
                if claim_path is not None and (
                    bound_claim is None
                    or _claim_is_for_manifest(bound_claim, manifest, token)
                ):
                    _write_claim(
                        claim_path,
                        manifest,
                        status="UNKNOWN",
                        execution_token=token,
                    )
            elif claim_path is not None:
                claim = bound_claim
                if (
                    claim is not None
                    and claim.get("status") == "RUNNING"
                    and _claim_is_for_manifest(claim, manifest)
                ):
                    if manifest.get("status") in {
                        "SUCCEEDED",
                        "FAILED",
                        "CANCELLED",
                        "UNKNOWN",
                    }:
                        _write_claim(
                            claim_path,
                            manifest,
                            status=str(manifest["status"]),
                            execution_token=token,
                        )
                    elif manifest.get("status") == "PREPARED":
                        claim["status"] = "UNKNOWN"
                        claim["updated_at"] = _utc_now()
                        _atomic_write_json(claim_path, claim)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _cancel(args: argparse.Namespace) -> int:
    manifest_path, _root, initial = _load_manifest(args.manifest)
    claim_path = (
        _claim_path(manifest_path, initial)
        if isinstance(initial.get("claim_sha256"), str)
        else None
    )
    with (_path_lock(claim_path) if claim_path is not None else nullcontext()):
        with _path_lock(manifest_path):
            manifest = _read_json(manifest_path)
            if manifest.get("status") != "RUNNING":
                raise RunRefusal(6, "only a RUNNING manifest can be cancelled")
            process = manifest.get("process")
            if not isinstance(process, Mapping):
                raise RunRefusal(6, "running manifest has no process identity")
            claim: dict[str, Any] | None = None
            if claim_path is not None:
                token = process.get("execution_token")
                if not isinstance(token, str):
                    raise RunRefusal(4, "running manifest execution token is invalid")
                claim = _read_bound_claim(claim_path, manifest)
                if (
                    claim is None
                    or claim.get("status") != "RUNNING"
                    or not _claim_is_for_manifest(claim, manifest, token)
                ):
                    raise RunRefusal(6, "direction claim is not owned by this run")
            descendant_identities = _claim_descendant_identities(claim)
            if claim is not None and claim_path is not None:
                merged = _merge_descendant_identities(
                    descendant_identities, _capture_descendant_identities(manifest)
                )
                if merged != descendant_identities:
                    claim["descendant_identities"] = merged
                    claim["updated_at"] = _utc_now()
                    _atomic_write_json(claim_path, claim)
                descendant_identities = merged
            identity, group_live = _observe_process_identity(
                manifest, descendant_identities
            )
            if identity in {IDENTITY_REUSED, IDENTITY_UNRECORDED}:
                raise RunRefusal(
                    6,
                    "process identity was reused or cannot be proven; reconcile instead",
                )
            if identity == IDENTITY_GONE and not group_live:
                raise RunRefusal(6, "process identity is no longer live; reconcile instead")
            _terminate_owned_group(manifest, descendant_identities)
            pgid = process.get("process_group_id")
            if not isinstance(pgid, int) or _group_pids(pgid):
                raise RunRefusal(5, "process-group quiescence was not proven")
            cancelled = dict(manifest)
            cancelled["status"] = "CANCELLED"
            cancelled["process"] = dict(
                process,
                ended_at=_utc_now(),
                group_quiescent=True,
                terminal_reason="CANCELLED_BY_OPERATOR",
            )
            cancelled = _replace_held(manifest_path, manifest, cancelled)
            if claim_path is not None:
                token = process.get("execution_token")
                if not isinstance(token, str):
                    raise RunRefusal(4, "running manifest execution token is invalid")
                _write_claim(
                    claim_path,
                    cancelled,
                    status="CANCELLED",
                    execution_token=token,
                )
    return 0


def _tracked_result_path(raw: str, *, direction_id: str, root: Path) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        resolved = _safe_resolve(candidate)
    else:
        resolved = _safe_resolve(ROOT / candidate)
    try:
        relative = resolved.relative_to(ROOT)
    except ValueError as exc:
        raise RunRefusal(5, f"result path is outside repository: {raw}") from exc
    expected_prefix = Path("docs/research/candidates") / direction_id / "results"
    try:
        relative.relative_to(expected_prefix)
    except ValueError as exc:
        raise RunRefusal(5, f"result path is outside direction results: {raw}") from exc
    if any(part == ".." for part in candidate.parts) or resolved.is_symlink():
        raise RunRefusal(5, f"result path is not confined: {raw}")
    _assert_no_symlink_components(resolved.parent, stop=ROOT)
    return resolved


def _state_validate(*, kind: str, path: Path) -> None:
    if not STATE_SCRIPT.exists():
        raise RunRefusal(1, f"state helper is unavailable: {STATE_SCRIPT}")
    completed = subprocess.run(
        [
            sys.executable,
            str(STATE_SCRIPT),
            "validate",
            "--kind",
            kind,
            "--path",
            str(path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        code = completed.returncode if completed.returncode in {1, 2, 3, 4, 5, 6, 7, 8} else 1
        message = completed.stderr.strip() or completed.stdout.strip() or f"state helper exited {code}"
        raise RunRefusal(code, message)


def _promote(args: argparse.Namespace) -> int:
    manifest_path, root, manifest = _load_manifest(args.manifest)
    _verify_manifest_provenance(manifest_path, root, manifest)
    if manifest.get("status") != "SUCCEEDED":
        raise RunRefusal(6, "only a successful run can be promoted")
    process = manifest.get("process")
    if not isinstance(process, Mapping) or process.get("group_quiescent") is not True:
        raise RunRefusal(6, "successful run lacks process-group quiescence proof")
    direction_id = _validate_identifier(manifest.get("direction_id"), "direction_id")
    result_json_path = _tracked_result_path(
        args.result_json, direction_id=direction_id, root=root
    )
    result_markdown_path = _tracked_result_path(
        args.result_markdown, direction_id=direction_id, root=root
    )
    if not result_json_path.is_file() or not result_markdown_path.is_file():
        raise RunInputError("promote requires existing EM-authored result files")
    result = _read_json(result_json_path)
    if result.get("direction_id") != direction_id:
        raise RunRefusal(4, "result direction does not match manifest")
    result_id = _validate_identifier(result.get("result_id"), "result_id")
    expected_results = (
        ROOT / "docs" / "research" / "candidates" / direction_id / "results"
    )
    expected_json = _safe_resolve(expected_results / f"{result_id}.json")
    expected_markdown = _safe_resolve(expected_results / f"{result_id}.md")
    if result_json_path != expected_json or result_markdown_path != expected_markdown:
        raise RunRefusal(4, "promote requires the exact result JSON/Markdown pair")
    expected_conclusion = expected_markdown.relative_to(ROOT).as_posix()
    if result.get("conclusion_path") != expected_conclusion:
        raise RunRefusal(4, "result conclusion_path does not identify the supplied Markdown")

    source_run = result.get("source_run")
    if not isinstance(source_run, Mapping):
        raise RunRefusal(4, "result source_run provenance is missing")
    expected_manifest_ref = (
        Path("temp")
        / "directions"
        / direction_id
        / "exp"
        / str(manifest["run_id"])
        / "manifest.json"
    )
    if (
        source_run.get("run_id") != manifest.get("run_id")
        or source_run.get("manifest_path") != expected_manifest_ref.as_posix()
        or _safe_resolve(ROOT / expected_manifest_ref) != manifest_path
        or source_run.get("manifest_sha256") != _sha256_file(manifest_path)
    ):
        raise RunRefusal(4, "result manifest provenance does not match")
    parameters = manifest.get("parameters")
    if not isinstance(parameters, Mapping):
        raise RunRefusal(4, "manifest parameters are invalid")
    parameters_sha = _parameters_digest(parameters)
    if (
        source_run.get("code_sha") != manifest.get("code_sha")
        or source_run.get("parameters") != parameters
        or source_run.get("parameters_sha256") != parameters_sha
        or manifest.get("parameters_sha256") != parameters_sha
    ):
        raise RunRefusal(4, "result code/parameter provenance does not match")
    if result.get("writer") != f"EM-{direction_id}" or result.get("promoted_by") != (
        f"EM-{direction_id}"
    ):
        raise RunRefusal(5, "result must be authored and promoted by its EM")
    try:
        conclusion = result_markdown_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RunInputError(f"result Markdown is unreadable: {exc}") from exc
    if not result.get("metrics") or not conclusion.strip():
        raise RunInputError("result requires selected metric provenance and a conclusion")
    _state_validate(kind="accepted_result", path=result_json_path)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    prepare = modes.add_parser("prepare")
    prepare.add_argument("--direction", required=True)
    prepare.add_argument("--run-id", required=True)
    prepare.add_argument("--assignment", required=True)
    prepare.add_argument("--code-sha", required=True)
    prepare.add_argument("--parameters", required=True)
    prepare.add_argument("--estimate", required=True)
    prepare.add_argument("--output-root", required=True)
    prepare.add_argument("--review-evidence")
    prepare.add_argument("command", nargs=argparse.REMAINDER)
    execute = modes.add_parser("execute")
    execute.add_argument("--manifest", required=True)
    execute.add_argument("--approval")
    execute.add_argument("--emit-operator-result", action="store_true")
    reconcile = modes.add_parser("reconcile")
    reconcile.add_argument("--manifest", required=True)
    cancel = modes.add_parser("cancel")
    cancel.add_argument("--manifest", required=True)
    promote = modes.add_parser("promote")
    promote.add_argument("--manifest", required=True)
    promote.add_argument("--result-json", required=True)
    promote.add_argument("--result-markdown", required=True)
    exec_gate = modes.add_parser("_exec-gate", help=argparse.SUPPRESS)
    gate_source = exec_gate.add_mutually_exclusive_group(required=True)
    gate_source.add_argument("--gate-fd", type=int)
    gate_source.add_argument("--gate-path")
    exec_gate.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.mode == "prepare":
            return _prepare(args)
        if args.mode == "execute":
            return _execute(args)
        if args.mode == "reconcile":
            return _reconcile(args)
        if args.mode == "cancel":
            return _cancel(args)
        if args.mode == "promote":
            return _promote(args)
        if args.mode == "_exec-gate":
            return _exec_gate(args)
        raise RunInputError(f"unknown mode {args.mode}")
    except RunRefusal as exc:
        print(f"hmasd run refused: {exc}", file=sys.stderr)
        return exc.code
    except (OSError, ValueError, TypeError) as exc:
        print(f"hmasd run failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
