#!/usr/bin/env python3
"""Run and verify proof-sized HMASD execution-readiness receipts.

The readiness wrapper is intentionally mechanical.  Candidate validators own
the meaning of a phase and of an artifact; this module only runs the frozen
commands, records their observable result, and checks the candidate identity.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 3
PHASES = (
    "interface_smoke",
    "bounded_exercise",
    "artifact_validation",
    "artifact_reload",
    "evaluate_entry",
    "analyze_entry",
)
MAX_SMOKE_SECONDS = 60
MAX_TOTAL_SECONDS = 2460
TAIL_CHARS = 2000
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ATTEMPT_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class ReadinessError(RuntimeError):
    """A mechanical readiness contract or execution error."""


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise ReadinessError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def _repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    return Path(_git(start, "rev-parse", "--show-toplevel")).resolve()


def _repo_state(repo: Path) -> tuple[str, str]:
    return (
        _git(repo, "rev-parse", "HEAD"),
        _git(repo, "status", "--porcelain=v1", "--untracked-files=all"),
    )


def _require_clean_state(repo: Path, expected_head: str | None = None) -> tuple[str, str]:
    head, status = _repo_state(repo)
    if expected_head is not None and head != expected_head:
        raise ReadinessError("candidate_commit does not equal the checked-out HEAD")
    if status:
        raise ReadinessError("Git-visible tracked or nonignored-untracked changes are present")
    return head, status


def _require_unchanged(repo: Path, baseline: tuple[str, str], where: str) -> None:
    current = _repo_state(repo)
    if current != baseline:
        raise ReadinessError(f"git_visible_mutation after {where}")


def _safe_relative_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReadinessError(f"{field} must be a non-empty repository-relative path")
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts:
        raise ReadinessError(f"{field} must stay inside the repository")
    return pure.as_posix()


def _safe_attempt(value: Any) -> str:
    if not isinstance(value, str) or not ATTEMPT_RE.fullmatch(value):
        raise ReadinessError("attempt_id must contain only letters, digits, '.', '_' or '-'")
    return value


def _resolve_artifact(repo: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (repo / path).resolve()


def _receipt_root(repo: Path) -> Path:
    git_path = _git(repo, "rev-parse", "--git-path", "hmasd/execution-readiness")
    path = Path(git_path)
    if not path.is_absolute():
        path = repo / path
    return path.resolve()


def _final_receipt_path(repo: Path, candidate: str, attempt: str) -> Path:
    if not COMMIT_RE.fullmatch(candidate):
        raise ReadinessError("candidate_commit must be a 40-character lowercase SHA")
    return _receipt_root(repo) / candidate / f"{attempt}.json"


def _candidate_receipt_path(repo: Path, spec: dict[str, Any]) -> Path:
    return _resolve_artifact(repo, spec["exercise_root"]) / ".hmasd-readiness-candidate.json"


def _load_spec(path: Path, repo: Path, *, fresh: bool, require_current_head: bool) -> dict[str, Any]:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"invalid readiness spec: {exc}") from exc
    if not isinstance(spec, dict) or spec.get("schema_version") != SCHEMA_VERSION:
        raise ReadinessError(f"schema_version must equal {SCHEMA_VERSION}")

    candidate = spec.get("candidate_commit")
    if not isinstance(candidate, str) or not COMMIT_RE.fullmatch(candidate):
        raise ReadinessError("candidate_commit must be a 40-character lowercase SHA")
    attempt = _safe_attempt(spec.get("attempt_id"))
    if require_current_head:
        _require_clean_state(repo, candidate)
    else:
        _git(repo, "rev-parse", "--verify", f"{candidate}^{{commit}}")

    if spec.get("formal") is not False or spec.get("scientific_iteration_cost") != 0:
        raise ReadinessError("readiness must be nonformal and cost zero scientific iterations")
    if not isinstance(spec.get("trigger"), str) or not spec["trigger"].strip():
        raise ReadinessError("trigger must be a non-empty string")

    exact = spec.get("exact_paths")
    if not isinstance(exact, list) or not exact:
        raise ReadinessError("exact_paths must be a non-empty list")
    exact_paths = [_safe_relative_path(item, "exact_paths") for item in exact]
    if len(set(exact_paths)) != len(exact_paths):
        raise ReadinessError("exact_paths contains duplicates")

    exercise_root = spec.get("exercise_root")
    if not isinstance(exercise_root, str) or not exercise_root.strip():
        raise ReadinessError("exercise_root must be a non-empty path")
    exercise_path = _resolve_artifact(repo, exercise_root)
    if fresh and exercise_path.exists() and (not exercise_path.is_dir() or any(exercise_path.iterdir())):
        raise ReadinessError("exercise_root must be absent or empty before readiness starts")
    if not fresh and not exercise_path.is_dir():
        raise ReadinessError("exercise_root must exist before receipt finalization")

    artifacts = spec.get("expected_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ReadinessError("expected_artifacts must be a non-empty list")
    for artifact in artifacts:
        if not isinstance(artifact, str) or not artifact:
            raise ReadinessError("expected_artifacts entries must be non-empty strings")
        try:
            _resolve_artifact(repo, artifact).relative_to(exercise_path)
        except ValueError as exc:
            raise ReadinessError("expected_artifacts must stay inside exercise_root") from exc

    phases = spec.get("phases")
    if not isinstance(phases, dict) or set(phases) != set(PHASES):
        raise ReadinessError("phases must contain exactly the six readiness phases")
    total = 0
    for phase in PHASES:
        phase_spec = phases[phase]
        if not isinstance(phase_spec, dict):
            raise ReadinessError(f"{phase} must be an object")
        argv = phase_spec.get("argv")
        timeout = phase_spec.get("timeout_seconds")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ReadinessError(f"{phase}.argv must be a non-empty string array")
        lowered = [item.strip().lower() for item in argv]
        if any(item == "--formal" or item.startswith("--formal=") or item == "formal=true" for item in lowered):
            raise ReadinessError(f"{phase}.argv crosses the nonformal boundary")
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
            raise ReadinessError(f"{phase}.timeout_seconds must be a positive integer")
        if phase == "interface_smoke" and timeout > MAX_SMOKE_SECONDS:
            raise ReadinessError(f"interface_smoke timeout exceeds {MAX_SMOKE_SECONDS} seconds")
        total += timeout
    if total > MAX_TOTAL_SECONDS:
        raise ReadinessError(f"combined phase timeout exceeds {MAX_TOTAL_SECONDS} seconds")

    spec["candidate_commit"] = candidate
    spec["attempt_id"] = attempt
    spec["exact_paths"] = exact_paths
    return spec


class _StreamPump(threading.Thread):
    def __init__(self, source: Any, target: Path) -> None:
        super().__init__(daemon=True)
        self.source = source
        self.target = target
        self.tail: deque[bytes] = deque()
        self.size = 0
        self.error: BaseException | None = None

    def run(self) -> None:
        try:
            with self.target.open("wb") as output:
                while True:
                    chunk = self.source.read(65536)
                    if not chunk:
                        break
                    output.write(chunk)
                    self.tail.append(chunk)
                    self.size += len(chunk)
                    while self.size > 65536 and self.tail:
                        self.size -= len(self.tail.popleft())
                output.flush()
        except BaseException as exc:  # typed by caller, never escapes wrapper
            self.error = exc

    def decoded_tail(self) -> str:
        return b"".join(self.tail).decode("utf-8", errors="replace")[-TAIL_CHARS:]


def _terminate_tree(process: subprocess.Popen[bytes]) -> bool:
    try:
        if os.name == "nt":
            was_running = process.poll() is None
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                capture_output=True,
                timeout=10,
            )
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # taskkill can report success before the Python handle is
                # signalled.  Kill the direct handle as a bounded fallback.
                process.kill()
                process.wait(timeout=5)
            # A failed taskkill followed by a direct-handle kill cannot prove
            # that descendants are gone, so report that conservatively.
            return process.poll() is not None and (completed.returncode == 0 or not was_running)
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        return process.poll() is not None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        try:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return process.poll() is not None


def _run_phase(repo: Path, exercise_path: Path, name: str, phase_spec: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    log_dir = exercise_path / ".hmasd-readiness-logs"
    stdout_path = log_dir / f"{name}.stdout"
    stderr_path = log_dir / f"{name}.stderr"
    base: dict[str, Any] = {
        "name": name,
        "argv": phase_spec.get("argv"),
        "timeout_seconds": phase_spec.get("timeout_seconds"),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
    }
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return {
            **base,
            "status": "FAILED",
            "failure_kind": "log_path_error",
            "process_tree_terminated": False,
            "exit_code": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }
    try:
        kwargs: dict[str, Any] = {
            "cwd": repo,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "shell": False,
        }
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            kwargs["start_new_session"] = True
        process = subprocess.Popen(phase_spec["argv"], **kwargs)
    except (OSError, ValueError, TypeError) as exc:
        stdout_path.write_bytes(b"")
        stderr_path.write_text(str(exc), encoding="utf-8", errors="replace")
        return {
            **base,
            "status": "FAILED",
            "failure_kind": "launch_error",
            "process_tree_terminated": False,
            "exit_code": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }

    stdout_pump = _StreamPump(process.stdout, stdout_path)
    stderr_pump = _StreamPump(process.stderr, stderr_path)
    stdout_pump.start()
    stderr_pump.start()
    timed_out = False
    terminated = True
    try:
        process.wait(timeout=phase_spec["timeout_seconds"])
    except subprocess.TimeoutExpired:
        timed_out = True
        terminated = _terminate_tree(process)
    except (OSError, ValueError) as exc:
        terminated = _terminate_tree(process)
        stdout_pump.join(timeout=10)
        stderr_pump.join(timeout=10)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        return {
            **base,
            "status": "FAILED",
            "failure_kind": "wait_error",
            "process_tree_terminated": terminated,
            "exit_code": process.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": stdout_pump.decoded_tail(),
            "stderr_tail": (stderr_pump.decoded_tail() + "\n" + str(exc))[-TAIL_CHARS:],
        }
    stdout_pump.join(timeout=10)
    stderr_pump.join(timeout=10)
    if process.stdout is not None:
        process.stdout.close()
    if process.stderr is not None:
        process.stderr.close()
    streams_drained = not stdout_pump.is_alive() and not stderr_pump.is_alive()
    if not streams_drained:
        terminated = False
    if stdout_pump.error is not None or stderr_pump.error is not None:
        terminated = False
    if timed_out and not terminated:
        failure_kind = "process_tree_termination_failed"
    elif timed_out:
        failure_kind = "timeout"
    elif process.returncode != 0:
        failure_kind = "nonzero_exit"
    elif not streams_drained:
        failure_kind = "stream_drain_failed"
    elif stdout_pump.error is not None or stderr_pump.error is not None:
        failure_kind = "log_write_error"
    else:
        failure_kind = None
    result = {
        **base,
        "status": "PASSED" if failure_kind is None else "FAILED",
        "failure_kind": failure_kind,
        "process_tree_terminated": terminated,
        "exit_code": process.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout_tail": stdout_pump.decoded_tail(),
        "stderr_tail": stderr_pump.decoded_tail(),
    }
    return result


def _artifact_states(repo: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"path": item, "present": _resolve_artifact(repo, item).is_file()}
        for item in spec["expected_artifacts"]
    ]


def _candidate_header(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASSED",
        "candidate_commit": spec["candidate_commit"],
        "attempt_id": spec["attempt_id"],
        "trigger": spec["trigger"],
        "exact_paths": spec["exact_paths"],
        "formal": False,
        "scientific_iteration_cost": 0,
        "exercise_root": spec["exercise_root"],
    }


def _validate_candidate_receipt(repo: Path, spec: dict[str, Any], receipt: dict[str, Any]) -> None:
    for key, value in _candidate_header(spec).items():
        if receipt.get(key) != value:
            raise ReadinessError(f"candidate receipt {key} mismatch")
    phases = receipt.get("phases")
    if not isinstance(phases, list) or [item.get("name") for item in phases] != list(PHASES):
        raise ReadinessError("candidate receipt phase set mismatch")
    for result, phase in zip(phases, PHASES, strict=True):
        phase_spec = spec["phases"][phase]
        if result.get("status") != "PASSED" or result.get("exit_code") != 0:
            raise ReadinessError(f"candidate receipt {phase} is not successful")
        if result.get("argv") != phase_spec["argv"] or result.get("timeout_seconds") != phase_spec["timeout_seconds"]:
            raise ReadinessError(f"candidate receipt {phase} command mismatch")
    current_artifacts = _artifact_states(repo, spec)
    if receipt.get("artifacts") != current_artifacts or not all(item["present"] for item in current_artifacts):
        raise ReadinessError("candidate receipt artifact set mismatch")


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def run_spec(spec_path: Path) -> int:
    _configure_utf8_stdio()
    repo = _repo_root()
    spec = _load_spec(spec_path.resolve(), repo, fresh=True, require_current_head=True)
    baseline = _repo_state(repo)
    exercise_path = _resolve_artifact(repo, spec["exercise_root"])
    exercise_path.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for phase in PHASES:
        try:
            _require_unchanged(repo, baseline, f"before {phase}")
        except ReadinessError as exc:
            result = {"name": phase, "status": "FAILED", "failure_kind": "git_visible_mutation", "error": str(exc)}
            print(json.dumps({"status": "FAILED", "phase": phase, "result": result}, ensure_ascii=False))
            return 1
        result = _run_phase(repo, exercise_path, phase, spec["phases"][phase])
        results.append(result)
        try:
            _require_unchanged(repo, baseline, f"{phase}")
        except ReadinessError as exc:
            result.update({"status": "FAILED", "failure_kind": "git_visible_mutation", "error": str(exc)})
        if result["status"] != "PASSED":
            print(json.dumps({"status": "FAILED", "phase": phase, "result": result}, ensure_ascii=False))
            return 1

    artifacts = _artifact_states(repo, spec)
    if not all(item["present"] for item in artifacts):
        print(json.dumps({"status": "FAILED", "phase": "expected_artifacts", "artifacts": artifacts}, ensure_ascii=False))
        return 1
    try:
        _require_unchanged(repo, baseline, "candidate receipt publication")
    except ReadinessError as exc:
        print(json.dumps({"status": "FAILED", "phase": "candidate_receipt", "failure_kind": "git_visible_mutation", "error": str(exc)}, ensure_ascii=False))
        return 1
    receipt = {**_candidate_header(spec), "phases": results, "artifacts": artifacts}
    path = _candidate_receipt_path(repo, spec)
    _atomic_write_json(path, receipt)
    print("HMASD_EXECUTION_READINESS_PHASES_OK")
    print(json.dumps({"candidate_receipt": str(path), "candidate_commit": spec["candidate_commit"], "attempt_id": spec["attempt_id"]}, ensure_ascii=True))
    return 0


def finalize_spec(spec_path: Path) -> int:
    _configure_utf8_stdio()
    repo = _repo_root()
    spec = _load_spec(spec_path.resolve(), repo, fresh=False, require_current_head=True)
    baseline = _require_clean_state(repo, spec["candidate_commit"])
    candidate_path = _candidate_receipt_path(repo, spec)
    try:
        receipt = json.loads(candidate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"missing or invalid candidate receipt: {exc}") from exc
    if not isinstance(receipt, dict):
        raise ReadinessError("candidate receipt must be an object")
    _validate_candidate_receipt(repo, spec, receipt)
    _require_unchanged(repo, baseline, "finalization")
    path = _final_receipt_path(repo, spec["candidate_commit"], spec["attempt_id"])
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReadinessError(f"invalid existing final receipt: {exc}") from exc
        if existing != receipt:
            raise ReadinessError("conflicting final receipt already exists")
    else:
        _atomic_write_json(path, receipt)
    print("HMASD_EXECUTION_READINESS_OK")
    print(json.dumps({"receipt": str(path), "candidate_commit": spec["candidate_commit"], "attempt_id": spec["attempt_id"]}, ensure_ascii=True))
    return 0


def _validate_historical_receipt(receipt: dict[str, Any]) -> None:
    if receipt.get("schema_version") != SCHEMA_VERSION or receipt.get("status") != "PASSED":
        raise ReadinessError("readiness receipt is not successful")
    candidate = receipt.get("candidate_commit")
    if not isinstance(candidate, str) or not COMMIT_RE.fullmatch(candidate):
        raise ReadinessError("readiness receipt candidate_commit mismatch")
    _safe_attempt(receipt.get("attempt_id"))
    exact = receipt.get("exact_paths")
    if not isinstance(exact, list) or not exact or [_safe_relative_path(x, "receipt exact_paths") for x in exact] != exact:
        raise ReadinessError("readiness receipt exact_paths mismatch")
    if receipt.get("formal") is not False or receipt.get("scientific_iteration_cost") != 0:
        raise ReadinessError("readiness receipt crosses the nonformal boundary")
    phases = receipt.get("phases")
    if not isinstance(phases, list) or [item.get("name") for item in phases] != list(PHASES) or any(item.get("status") != "PASSED" for item in phases):
        raise ReadinessError("readiness receipt phase set mismatch")
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts or any(not item.get("present") for item in artifacts):
        raise ReadinessError("readiness receipt has missing artifacts")


def check_receipt(receipt_path: Path) -> int:
    _configure_utf8_stdio()
    try:
        receipt = json.loads(receipt_path.resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"missing or invalid readiness receipt: {exc}") from exc
    if not isinstance(receipt, dict):
        raise ReadinessError("readiness receipt must be an object")
    _validate_historical_receipt(receipt)
    print("HMASD_EXECUTION_READINESS_RECEIPT_OK")
    return 0


def _code_pm_session(repo: Path) -> str:
    role = (repo / ".agents/roles/CODE_PROJECT_MANAGER.md").read_text(encoding="utf-8")
    matches = re.findall(r"(?m)^session_owner_id=([^\s]+)$", role)
    if len(matches) != 1:
        raise ReadinessError("Code PM role must contain exactly one session owner")
    return matches[0]


def _message_field(message: str, name: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(name)}=(.*)$", message)
    return match.group(1).strip() if match else None


def _hook_feedback(reason: str, already_active: bool) -> dict[str, Any]:
    if already_active:
        return {"continue": False, "stopReason": "invalid_code_acceptance", "systemMessage": reason}
    return {"decision": "block", "reason": reason + " Run the Skill script or return CODE_ACCEPTANCE_BLOCKED."}


def hook_stop() -> int:
    _configure_utf8_stdio()
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0
    try:
        repo = _repo_root()
        session = _code_pm_session(repo)
    except (ReadinessError, OSError):
        return 0
    if payload.get("session_id") != session:
        return 0
    message = payload.get("last_assistant_message") or ""
    if not re.search(r"(?m)^CODE_ACCEPTED\s*$", message):
        return 0
    already_active = payload.get("stop_hook_active") is True
    commit = _message_field(message, "commit")
    exact_paths = _message_field(message, "exact_paths")
    readiness = _message_field(message, "execution_readiness")
    receipt_field = _message_field(message, "execution_readiness_receipt")
    reason = _message_field(message, "execution_readiness_reason")
    try:
        current = _git(repo, "rev-parse", "HEAD")
        if not commit or not COMMIT_RE.fullmatch(commit):
            raise ReadinessError("CODE_ACCEPTED has no exact 40-character commit.")
        if current != commit:
            raise ReadinessError("CODE_ACCEPTED commit is not current HEAD.")
        if not exact_paths:
            raise ReadinessError("CODE_ACCEPTED has no exact_paths.")
        if readiness == "not_triggered":
            if not reason or reason in {"none", "not-triggered", "not_triggered"}:
                raise ReadinessError("Untriggered execution readiness needs a bounded reason.")
        elif readiness == "passed":
            if not receipt_field:
                raise ReadinessError("CODE_ACCEPTED does not name the exact readiness receipt")
            receipt = json.loads(Path(receipt_field).resolve().read_text(encoding="utf-8"))
            _validate_historical_receipt(receipt)
            if receipt.get("candidate_commit") != commit:
                raise ReadinessError("receipt candidate identity does not match CODE_ACCEPTED")
            if receipt.get("exact_paths") != [item for item in exact_paths.split("|") if item]:
                raise ReadinessError("receipt exact_paths do not match CODE_ACCEPTED")
        else:
            raise ReadinessError("CODE_ACCEPTED has no passed execution_readiness state.")
    except (ReadinessError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps(_hook_feedback(str(exc), already_active), ensure_ascii=False))
    return 0


def main() -> int:
    _configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--spec", type=Path, required=True)
    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--spec", type=Path, required=True)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--receipt", type=Path, required=True)
    subparsers.add_parser("hook-stop")
    args = parser.parse_args()
    try:
        if args.command == "run":
            return run_spec(args.spec)
        if args.command == "finalize":
            return finalize_spec(args.spec)
        if args.command == "check":
            return check_receipt(args.receipt)
        return hook_stop()
    except ReadinessError as exc:
        print(f"HMASD_EXECUTION_READINESS_ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
