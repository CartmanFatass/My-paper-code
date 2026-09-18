#!/usr/bin/env python3
"""Runner-side admission handshake for result-bearing HMASD entry points.

This is a cooperative launch boundary, not a same-user security sandbox.  A
runner must call :func:`require_admission` before it performs result-bearing
work.  The launch parent binds a short-lived, single-use localhost socket to
the exact interpreter, script, argv, source SHA, direction, and child process.
Arbitrary code running as the same OS user can inspect or interfere with its
own processes, so the protocol is designed to prevent mistakes and replay,
not to defend against a malicious same-UID process.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence


ENVIRONMENT_KEY = "HMASD_ADMISSION_V1"
SCHEMA_VERSION = 1
_MAX_MESSAGE_BYTES = 64 * 1024
_attempted = False


class AdmissionRefused(RuntimeError):
    """The runner was not released by the HMASD launch parent."""


def _normalized_path(value: str | os.PathLike[str]) -> str:
    path = Path(value).resolve(strict=False)
    normalized = os.path.normcase(str(path))
    return normalized.replace("\\", "/")


def command_digest(
    executable: str | os.PathLike[str],
    script: str | os.PathLike[str],
    argv: Sequence[str],
) -> str:
    """Return the stable digest used by both the parent and admitted runner."""

    payload = {
        "executable": _normalized_path(executable),
        "script": _normalized_path(script),
        "argv": [str(value) for value in argv],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_message(stream: Any) -> Mapping[str, Any]:
    raw = stream.readline(_MAX_MESSAGE_BYTES + 1)
    if not raw or len(raw) > _MAX_MESSAGE_BYTES or not raw.endswith(b"\n"):
        raise AdmissionRefused("admission peer returned an invalid message")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdmissionRefused("admission peer returned invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise AdmissionRefused("admission peer message is not an object")
    return value


def _write_message(stream: Any, value: Mapping[str, Any]) -> None:
    rendered = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8") + b"\n"
    if len(rendered) > _MAX_MESSAGE_BYTES:
        raise AdmissionRefused("admission message is too large")
    stream.write(rendered)
    stream.flush()


def _git_head(source_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(source_root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AdmissionRefused(f"cannot verify admitted source HEAD: {exc}") from exc
    value = completed.stdout.strip().lower()
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise AdmissionRefused("admitted source HEAD is not a full SHA")
    return value


def _load_spec() -> Mapping[str, Any]:
    raw = os.environ.pop(ENVIRONMENT_KEY, None)
    if not raw:
        raise AdmissionRefused(
            "missing HMASD admission; start this runner through scripts/hmasd_launch.py"
        )
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdmissionRefused("invalid HMASD admission specification") from exc
    if not isinstance(spec, Mapping) or spec.get("schema_version") != SCHEMA_VERSION:
        raise AdmissionRefused("unsupported HMASD admission specification")
    return spec


def _require_text(spec: Mapping[str, Any], key: str) -> str:
    value = spec.get(key)
    if not isinstance(value, str) or not value:
        raise AdmissionRefused(f"admission specification has no valid {key}")
    return value


def require_admission(
    script_file: str | os.PathLike[str],
    *,
    direction: str,
) -> Mapping[str, Any]:
    """Consume one launch admission bound to this exact runner invocation.

    Call this at the beginning of the runner's ``main`` path, before loading
    checkpoints, creating environments, or starting evaluation/training.
    """

    global _attempted
    if _attempted:
        raise AdmissionRefused("HMASD admission is single-use in each runner process")
    _attempted = True

    spec = _load_spec()
    now = time.time()
    expires_at = spec.get("expires_at")
    if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
        raise AdmissionRefused("admission expiry is invalid")
    if now >= float(expires_at):
        raise AdmissionRefused("HMASD admission expired before the runner accepted it")

    expected_direction = _require_text(spec, "direction")
    if direction != expected_direction:
        raise AdmissionRefused(
            f"admission direction mismatch: expected {expected_direction!r}, got {direction!r}"
        )

    expected_script = _require_text(spec, "runner")
    actual_script = _normalized_path(script_file)
    if actual_script != _normalized_path(expected_script):
        raise AdmissionRefused("admission runner path does not match __file__")

    expected_python = _require_text(spec, "python")
    try:
        same_interpreter = os.path.samefile(sys.executable, expected_python)
    except OSError:
        same_interpreter = _normalized_path(sys.executable) == _normalized_path(expected_python)
    if not same_interpreter:
        raise AdmissionRefused("runner is not using the configured interpreter")

    source_root = Path(_require_text(spec, "source_root")).resolve(strict=True)
    expected_sha = _require_text(spec, "sha").lower()
    if _git_head(source_root) != expected_sha:
        raise AdmissionRefused("source HEAD changed after launch admission was prepared")

    expected_parent = spec.get("parent_pid")
    if isinstance(expected_parent, bool) or not isinstance(expected_parent, int):
        raise AdmissionRefused("admission parent PID is invalid")
    if os.getppid() != expected_parent:
        raise AdmissionRefused("runner is not a direct child of the admitting process")

    actual_digest = command_digest(expected_python, actual_script, sys.argv[1:])
    expected_digest = _require_text(spec, "command_sha256")
    if actual_digest != expected_digest:
        raise AdmissionRefused("runner command does not match the admitted argv")

    endpoint = spec.get("endpoint")
    if (
        not isinstance(endpoint, Sequence)
        or isinstance(endpoint, (str, bytes))
        or len(endpoint) != 2
        or endpoint[0] != "127.0.0.1"
        or isinstance(endpoint[1], bool)
        or not isinstance(endpoint[1], int)
    ):
        raise AdmissionRefused("admission endpoint is invalid")
    nonce = _require_text(spec, "nonce")
    timeout = max(0.05, min(30.0, float(expires_at) - time.time()))

    hello = {
        "schema_version": SCHEMA_VERSION,
        "kind": "hello",
        "nonce": nonce,
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "direction": direction,
        "runner": actual_script,
        "source_root": _normalized_path(source_root),
        "sha": expected_sha,
        "command_sha256": actual_digest,
    }
    try:
        with socket.create_connection((endpoint[0], endpoint[1]), timeout=timeout) as peer:
            peer.settimeout(timeout)
            with peer.makefile("rwb", buffering=0) as stream:
                _write_message(stream, hello)
                response = _read_message(stream)
                if response.get("kind") != "grant" or response.get("nonce") != nonce:
                    reason = response.get("reason")
                    suffix = f": {reason}" if isinstance(reason, str) and reason else ""
                    raise AdmissionRefused(f"launch parent denied admission{suffix}")
                if response.get("pid") != os.getpid():
                    raise AdmissionRefused("launch grant is bound to a different child")
                if time.time() >= float(expires_at):
                    raise AdmissionRefused("HMASD admission expired before grant acceptance")
                _write_message(
                    stream,
                    {
                        "schema_version": SCHEMA_VERSION,
                        "kind": "accepted",
                        "nonce": nonce,
                        "pid": os.getpid(),
                    },
                )
    except AdmissionRefused:
        raise
    except (OSError, ValueError) as exc:
        raise AdmissionRefused(f"cannot complete HMASD admission handshake: {exc}") from exc

    return {
        "schema_version": SCHEMA_VERSION,
        "direction": direction,
        "sha": expected_sha,
        "command_sha256": actual_digest,
        "parent_pid": expected_parent,
        "child_pid": os.getpid(),
        "accepted_at_epoch": time.time(),
    }


__all__ = [
    "AdmissionRefused",
    "ENVIRONMENT_KEY",
    "command_digest",
    "require_admission",
]


def _atomic_write_exit(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=".hmasd-exit-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = stream.name
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def _self_process_identity() -> Mapping[str, Any]:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        created = wintypes.FILETIME()
        exited = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        handle = kernel32.GetCurrentProcess()
        if not kernel32.GetProcessTimes(
            handle,
            ctypes.byref(created),
            ctypes.byref(exited),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            raise OSError("GetProcessTimes failed")
        return {
            "kind": "windows_pid_creation_time",
            "pid": os.getpid(),
            "creation_time_100ns": (
                (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
            ),
        }

    stat_line = Path("/proc/self/stat").read_text(encoding="utf-8")
    fields_after_name = stat_line[stat_line.rfind(")") + 2 :].split()
    return {
        "kind": "linux_pid_start_ticks",
        "pid": os.getpid(),
        "boot_id": Path("/proc/sys/kernel/random/boot_id")
        .read_text(encoding="utf-8")
        .strip(),
        "start_ticks": int(fields_after_name[19]),
        "session_id": os.getsid(0),
    }


def _child_process_identity(process: subprocess.Popen[Any]) -> Mapping[str, Any]:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        created = wintypes.FILETIME()
        exited = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        if not kernel32.GetProcessTimes(
            wintypes.HANDLE(int(getattr(process, "_handle"))),
            ctypes.byref(created),
            ctypes.byref(exited),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            raise OSError("GetProcessTimes failed for runner child")
        return {
            "kind": "windows_pid_creation_time",
            "pid": process.pid,
            "creation_time_100ns": (
                (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
            ),
        }

    stat_line = Path(f"/proc/{process.pid}/stat").read_text(encoding="utf-8")
    fields_after_name = stat_line[stat_line.rfind(")") + 2 :].split()
    return {
        "kind": "linux_pid_start_ticks",
        "pid": process.pid,
        "boot_id": Path("/proc/sys/kernel/random/boot_id")
        .read_text(encoding="utf-8")
        .strip(),
        "start_ticks": int(fields_after_name[19]),
        "session_id": os.getsid(process.pid),
    }


def _run_admitted(argv: Sequence[str]) -> int:
    """Supervise one admitted runner and write its actual OS-process exit."""

    parser = __import__("argparse").ArgumentParser(add_help=False)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("runner_argv", nargs=__import__("argparse").REMAINDER)
    args = parser.parse_args(list(argv))
    if args.runner_argv and args.runner_argv[0] == "--":
        args.runner_argv.pop(0)

    runner = Path(args.runner).resolve(strict=True)
    output = Path(args.output).resolve(strict=False)
    raw_spec = os.environ.get(ENVIRONMENT_KEY)
    if not raw_spec:
        print("hmasd admitted bootstrap refused: missing admission", file=sys.stderr)
        return 125
    try:
        spec = json.loads(raw_spec)
    except json.JSONDecodeError:
        print("hmasd admitted bootstrap refused: invalid admission", file=sys.stderr)
        return 125
    if (
        not isinstance(spec, Mapping)
        or _normalized_path(spec.get("runner", "")) != _normalized_path(runner)
        or _normalized_path(spec.get("output_root", "")) != _normalized_path(output)
    ):
        print("hmasd admitted bootstrap refused: path binding mismatch", file=sys.stderr)
        return 125

    endpoint = spec.get("endpoint")
    expires_at = spec.get("expires_at")
    nonce = spec.get("nonce")
    expected_parent = spec.get("parent_pid")
    if (
        not isinstance(endpoint, Sequence)
        or isinstance(endpoint, (str, bytes))
        or len(endpoint) != 2
        or endpoint[0] != "127.0.0.1"
        or not isinstance(endpoint[1], int)
        or not isinstance(expires_at, (int, float))
        or not isinstance(nonce, str)
        or not isinstance(expected_parent, int)
        or os.getppid() != expected_parent
    ):
        print("hmasd admitted bootstrap refused: supervisor binding mismatch", file=sys.stderr)
        return 125
    remaining = float(expires_at) - time.time()
    if remaining <= 0:
        print("hmasd admitted bootstrap refused: admission expired", file=sys.stderr)
        return 125
    timeout = max(0.05, min(30.0, remaining))

    child: subprocess.Popen[Any] | None = None
    try:
        with socket.create_connection((endpoint[0], endpoint[1]), timeout=timeout) as peer:
            peer.settimeout(timeout)
            with peer.makefile("rwb", buffering=0) as stream:
                _write_message(
                    stream,
                    {
                        "schema_version": SCHEMA_VERSION,
                        "kind": "supervisor",
                        "nonce": nonce,
                        "pid": os.getpid(),
                        "parent_pid": os.getppid(),
                        "process_identity": _self_process_identity(),
                    },
                )
                response = _read_message(stream)
                if response.get("kind") != "prepare_child" or response.get("nonce") != nonce:
                    raise AdmissionRefused("launch parent did not authorize runner creation")
                child_spec = dict(spec)
                child_spec["parent_pid"] = os.getpid()
                child_spec["supervisor_pid"] = os.getpid()
                child_environment = dict(os.environ)
                child_environment[ENVIRONMENT_KEY] = json.dumps(
                    child_spec, sort_keys=True, separators=(",", ":")
                )
                child = subprocess.Popen(
                    [_require_text(spec, "python"), str(runner), *args.runner_argv],
                    cwd=_require_text(spec, "source_root"),
                    env=child_environment,
                    stdin=subprocess.DEVNULL,
                    shell=False,
                )
                child_identity = _child_process_identity(child)
                _write_message(
                    stream,
                    {
                        "schema_version": SCHEMA_VERSION,
                        "kind": "child_started",
                        "nonce": nonce,
                        "supervisor_pid": os.getpid(),
                        "pid": child.pid,
                        "process_identity": child_identity,
                    },
                )
                response = _read_message(stream)
                if response.get("kind") != "child_recorded" or response.get("nonce") != nonce:
                    raise AdmissionRefused("launch parent did not record runner identity")
    except (AdmissionRefused, OSError, ValueError) as exc:
        print(f"hmasd admitted bootstrap failed: {exc}", file=sys.stderr)
        if child is not None:
            try:
                child.wait(timeout=max(0.05, min(30.0, float(expires_at) - time.time())))
            except subprocess.TimeoutExpired:
                pass
        return 125

    assert child is not None
    exit_code = child.wait()

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "exited",
        "exit_code": exit_code,
        "termination": "signal" if exit_code < 0 else "process_exit",
        "pid": child.pid,
        "process_identity": child_identity,
        "supervisor_identity": _self_process_identity(),
        "finished_at_epoch": time.time(),
    }
    try:
        _atomic_write_exit(output / "process-exit.json", payload)
    except OSError as exc:
        print(f"cannot write process exit witness: {exc}", file=sys.stderr)
        return exit_code if exit_code != 0 else 126
    return exit_code


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "_run-admitted":
        raise SystemExit(_run_admitted(sys.argv[2:]))
    raise SystemExit("hmasd_admission.py is a runner library, not a direct entry point")
