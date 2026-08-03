#!/usr/bin/env python3
"""Run and verify proof-sized HMASD code execution-readiness receipts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 2
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
EXECUTION_SUPPORT_PATHS = (
    ".agents/skills/hmasd-agile-research-development/scripts/hmasd_execution_readiness.py",
    "tests/hmasd_code_project_manager_contract_test.ps1",
)
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class ReadinessError(RuntimeError):
    pass


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="strict")


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    if completed.returncode != 0:
        raise ReadinessError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def _git_predicate(repo: Path, *args: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    if completed.returncode not in (0, 1):
        raise ReadinessError(completed.stderr.strip() or "git predicate failed")
    return completed.returncode == 0


def _repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    root = _git(start, "rev-parse", "--show-toplevel")
    return Path(root).resolve()


def _safe_relative_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReadinessError(f"{field} must be a non-empty repository-relative path")
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts:
        raise ReadinessError(f"{field} must stay inside the repository")
    return pure.as_posix()


def _receipt_dir(repo: Path) -> Path:
    git_path = _git(repo, "rev-parse", "--git-path", "hmasd/execution-readiness")
    path = Path(git_path)
    if not path.is_absolute():
        path = repo / path
    return path.resolve()


def _receipt_path(repo: Path, commit: str) -> Path:
    if not COMMIT_RE.fullmatch(commit):
        raise ReadinessError("commit must be a 40-character lowercase SHA")
    return _receipt_dir(repo) / f"{commit}.json"


def _code_pm_session(repo: Path) -> str:
    try:
        role = (repo / ".agents/roles/CODE_PROJECT_MANAGER.md").read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        raise ReadinessError(f"cannot read Code PM role: {exc}") from exc
    matches = re.findall(r"(?m)^session_owner_id=([^\s]+)$", role)
    if len(matches) != 1:
        raise ReadinessError("Code PM role must contain exactly one session owner")
    return matches[0]


def _validate_execution_binding(
    repo: Path,
    source_commit: str,
    execution_commit: str,
    exact_paths: list[str],
    execution_support_paths: list[str],
) -> None:
    for field, commit in (
        ("source_commit", source_commit),
        ("execution_commit", execution_commit),
    ):
        try:
            resolved = _git(repo, "rev-parse", "--verify", f"{commit}^{{commit}}")
        except ReadinessError as exc:
            raise ReadinessError(f"{field} does not identify a Git commit") from exc
        if resolved != commit:
            raise ReadinessError(f"{field} does not identify the exact Git commit")
    if _git(repo, "rev-parse", "HEAD") != execution_commit:
        raise ReadinessError("execution_commit does not equal current HEAD")
    if execution_support_paths != list(EXECUTION_SUPPORT_PATHS):
        raise ReadinessError("execution_support_paths do not equal the approved readiness bridge")
    if source_commit == execution_commit:
        raise ReadinessError(
            "source_commit and execution_commit must be distinct and joined by the nonempty approved readiness bridge"
        )
    if set(exact_paths).intersection(execution_support_paths):
        raise ReadinessError("accepted paths overlap execution_support_paths")
    if not _git_predicate(repo, "merge-base", "--is-ancestor", source_commit, execution_commit):
        raise ReadinessError("source_commit is not an ancestor of execution_commit")
    observed_delta = [
        item
        for item in _git(
            repo, "diff", "--name-only", source_commit, execution_commit, "--"
        ).splitlines()
        if item
    ]
    if observed_delta != execution_support_paths:
        raise ReadinessError("source-to-execution path delta does not match execution_support_paths")
    dirty = _git(
        repo,
        "status",
        "--porcelain=v1",
        "--",
        *exact_paths,
        *execution_support_paths,
    )
    if dirty:
        raise ReadinessError("accepted or execution-support paths contain uncommitted changes")


def _load_spec(
    path: Path, repo: Path, *, require_fresh_exercise_root: bool
) -> dict[str, Any]:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"invalid readiness spec: {exc}") from exc
    if not isinstance(spec, dict) or spec.get("schema_version") != SCHEMA_VERSION:
        raise ReadinessError(f"schema_version must equal {SCHEMA_VERSION}")
    source_commit = spec.get("source_commit")
    if not isinstance(source_commit, str) or not COMMIT_RE.fullmatch(source_commit):
        raise ReadinessError("source_commit must be a 40-character lowercase SHA")
    execution_commit = spec.get("execution_commit")
    if not isinstance(execution_commit, str) or not COMMIT_RE.fullmatch(execution_commit):
        raise ReadinessError("execution_commit must be a 40-character lowercase SHA")
    if spec.get("formal") is not False or spec.get("scientific_iteration_cost") != 0:
        raise ReadinessError("readiness must be nonformal and cost zero scientific iterations")
    if not isinstance(spec.get("trigger"), str) or not spec["trigger"].strip():
        raise ReadinessError("trigger must be a non-empty string")

    exact_paths = spec.get("exact_paths")
    if not isinstance(exact_paths, list) or not exact_paths:
        raise ReadinessError("exact_paths must be a non-empty list")
    normalized_paths = [_safe_relative_path(item, "exact_paths") for item in exact_paths]
    if len(set(normalized_paths)) != len(normalized_paths):
        raise ReadinessError("exact_paths contains duplicates")

    support_paths = spec.get("execution_support_paths")
    if not isinstance(support_paths, list) or not support_paths:
        raise ReadinessError("execution_support_paths must be a non-empty list")
    normalized_support_paths = [
        _safe_relative_path(item, "execution_support_paths") for item in support_paths
    ]
    if len(set(normalized_support_paths)) != len(normalized_support_paths):
        raise ReadinessError("execution_support_paths contains duplicates")
    _validate_execution_binding(
        repo,
        source_commit,
        execution_commit,
        normalized_paths,
        normalized_support_paths,
    )

    exercise_root = spec.get("exercise_root")
    if not isinstance(exercise_root, str) or not exercise_root.strip():
        raise ReadinessError("exercise_root must be a non-empty path")
    exercise_path = _resolve_artifact(repo, exercise_root)
    if require_fresh_exercise_root and exercise_path.exists() and (
        not exercise_path.is_dir() or any(exercise_path.iterdir())
    ):
        raise ReadinessError("exercise_root must be absent or empty before readiness starts")
    if not require_fresh_exercise_root and not exercise_path.is_dir():
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

    phase_specs = spec.get("phases")
    if not isinstance(phase_specs, dict) or set(phase_specs) != set(PHASES):
        raise ReadinessError("phases must contain exactly the six readiness phases")
    total_timeout = 0
    for phase in PHASES:
        phase_spec = phase_specs[phase]
        if not isinstance(phase_spec, dict):
            raise ReadinessError(f"{phase} must be an object")
        argv = phase_spec.get("argv")
        timeout = phase_spec.get("timeout_seconds")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ReadinessError(f"{phase}.argv must be a non-empty string array")
        normalized_argv = [item.strip().lower() for item in argv]
        if any(item == "--formal" or item.startswith("--formal=") or item == "formal=true" for item in normalized_argv):
            raise ReadinessError(f"{phase}.argv crosses the nonformal boundary")
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
            raise ReadinessError(f"{phase}.timeout_seconds must be a positive integer")
        if phase == "interface_smoke" and timeout > MAX_SMOKE_SECONDS:
            raise ReadinessError(f"interface_smoke timeout exceeds {MAX_SMOKE_SECONDS} seconds")
        total_timeout += timeout
    if total_timeout > MAX_TOTAL_SECONDS:
        raise ReadinessError(f"combined phase timeout exceeds {MAX_TOTAL_SECONDS} seconds")

    spec["exact_paths"] = normalized_paths
    spec["execution_support_paths"] = normalized_support_paths
    return spec


def _run_phase(repo: Path, name: str, phase_spec: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            phase_spec["argv"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            timeout=phase_spec["timeout_seconds"],
            shell=False,
        )
        return {
            "name": name,
            "status": "PASSED" if completed.returncode == 0 else "FAILED",
            "argv": phase_spec["argv"],
            "timeout_seconds": phase_spec["timeout_seconds"],
            "duration_seconds": round(time.monotonic() - started, 3),
            "exit_code": completed.returncode,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "status": "FAILED",
            "argv": phase_spec["argv"],
            "timeout_seconds": phase_spec["timeout_seconds"],
            "duration_seconds": round(time.monotonic() - started, 3),
            "exit_code": None,
            "stdout_tail": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": "phase timed out",
        }


def _resolve_artifact(repo: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (repo / path).resolve()


def _candidate_receipt_path(repo: Path, spec: dict[str, Any]) -> Path:
    return _resolve_artifact(repo, spec["exercise_root"]) / ".hmasd-readiness-candidate.json"


def _artifact_states(repo: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"path": item, "present": _resolve_artifact(repo, item).is_file()}
        for item in spec["expected_artifacts"]
    ]


def _validate_candidate_receipt(
    repo: Path, spec: dict[str, Any], receipt: dict[str, Any]
) -> None:
    expected_header = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASSED",
        "source_commit": spec["source_commit"],
        "execution_commit": spec["execution_commit"],
        "execution_support_paths": spec["execution_support_paths"],
        "trigger": spec["trigger"],
        "exact_paths": spec["exact_paths"],
        "formal": False,
        "scientific_iteration_cost": 0,
        "exercise_root": spec["exercise_root"],
    }
    for key, value in expected_header.items():
        if receipt.get(key) != value:
            raise ReadinessError(
                f"candidate receipt {key} mismatch: "
                f"expected={value!r} observed={receipt.get(key)!r}"
            )

    results = receipt.get("phases")
    if not isinstance(results, list) or [item.get("name") for item in results] != list(PHASES):
        raise ReadinessError("candidate receipt phase set mismatch")
    for result, phase in zip(results, PHASES, strict=True):
        phase_spec = spec["phases"][phase]
        if result.get("status") != "PASSED" or result.get("exit_code") != 0:
            raise ReadinessError(f"candidate receipt {phase} is not successful")
        if result.get("argv") != phase_spec["argv"]:
            raise ReadinessError(f"candidate receipt {phase} argv mismatch")
        if result.get("timeout_seconds") != phase_spec["timeout_seconds"]:
            raise ReadinessError(f"candidate receipt {phase} timeout mismatch")

    current_artifacts = _artifact_states(repo, spec)
    if receipt.get("artifacts") != current_artifacts or not all(
        item["present"] for item in current_artifacts
    ):
        raise ReadinessError("candidate receipt artifact set mismatch")


def run_spec(spec_path: Path) -> int:
    repo = _repo_root()
    spec = _load_spec(spec_path.resolve(), repo, require_fresh_exercise_root=True)
    results: list[dict[str, Any]] = []
    for phase in PHASES:
        result = _run_phase(repo, phase, spec["phases"][phase])
        results.append(result)
        if result["status"] != "PASSED":
            print(json.dumps({"status": "FAILED", "phase": phase, "result": result}, ensure_ascii=False))
            return 1

    artifact_states = _artifact_states(repo, spec)
    if not all(item["present"] for item in artifact_states):
        print(json.dumps({"status": "FAILED", "phase": "expected_artifacts", "artifacts": artifact_states}))
        return 1

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASSED",
        "source_commit": spec["source_commit"],
        "execution_commit": spec["execution_commit"],
        "execution_support_paths": spec["execution_support_paths"],
        "trigger": spec["trigger"],
        "exact_paths": spec["exact_paths"],
        "formal": False,
        "scientific_iteration_cost": 0,
        "exercise_root": spec["exercise_root"],
        "phases": results,
        "artifacts": artifact_states,
    }
    path = _candidate_receipt_path(repo, spec)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("HMASD_EXECUTION_READINESS_PHASES_OK")
    print(
        json.dumps(
            {
                "candidate_receipt": str(path),
                "source_commit": spec["source_commit"],
                "execution_commit": spec["execution_commit"],
            },
            ensure_ascii=True,
        )
    )
    return 0


def finalize_spec(spec_path: Path) -> int:
    repo = _repo_root()
    spec = _load_spec(spec_path.resolve(), repo, require_fresh_exercise_root=False)
    candidate_path = _candidate_receipt_path(repo, spec)
    try:
        receipt = json.loads(candidate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"missing or invalid candidate receipt: {exc}") from exc
    if not isinstance(receipt, dict):
        raise ReadinessError("candidate receipt must be an object")
    _validate_candidate_receipt(repo, spec, receipt)

    path = _receipt_path(repo, spec["source_commit"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("HMASD_EXECUTION_READINESS_OK")
    print(
        json.dumps(
            {
                "receipt": str(path),
                "source_commit": spec["source_commit"],
                "execution_commit": spec["execution_commit"],
            },
            ensure_ascii=True,
        )
    )
    return 0


def _read_receipt(repo: Path, commit: str) -> dict[str, Any]:
    path = _receipt_path(repo, commit)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"missing or invalid readiness receipt: {exc}") from exc
    if receipt.get("schema_version") != SCHEMA_VERSION or receipt.get("status") != "PASSED":
        raise ReadinessError("readiness receipt is not successful")
    if receipt.get("source_commit") != commit:
        raise ReadinessError("readiness receipt commit mismatch")
    execution_commit = receipt.get("execution_commit")
    if not isinstance(execution_commit, str) or not COMMIT_RE.fullmatch(execution_commit):
        raise ReadinessError("readiness receipt execution_commit mismatch")
    exact_paths = receipt.get("exact_paths")
    if not isinstance(exact_paths, list) or not exact_paths:
        raise ReadinessError("readiness receipt exact_paths mismatch")
    normalized_exact_paths = [
        _safe_relative_path(item, "receipt exact_paths") for item in exact_paths
    ]
    if normalized_exact_paths != exact_paths or len(set(exact_paths)) != len(exact_paths):
        raise ReadinessError("readiness receipt exact_paths mismatch")
    execution_support_paths = receipt.get("execution_support_paths")
    if not isinstance(execution_support_paths, list) or not execution_support_paths:
        raise ReadinessError("readiness receipt execution_support_paths mismatch")
    normalized_support_paths = [
        _safe_relative_path(item, "receipt execution_support_paths")
        for item in execution_support_paths
    ]
    if (
        normalized_support_paths != execution_support_paths
        or len(set(execution_support_paths)) != len(execution_support_paths)
    ):
        raise ReadinessError("readiness receipt execution_support_paths mismatch")
    _validate_execution_binding(
        repo, commit, execution_commit, exact_paths, execution_support_paths
    )
    if receipt.get("formal") is not False or receipt.get("scientific_iteration_cost") != 0:
        raise ReadinessError("readiness receipt crosses the nonformal boundary")
    phases = receipt.get("phases")
    if not isinstance(phases, list) or [item.get("name") for item in phases] != list(PHASES):
        raise ReadinessError("readiness receipt phase set mismatch")
    if any(item.get("status") != "PASSED" for item in phases):
        raise ReadinessError("readiness receipt contains a failed phase")
    if not receipt.get("artifacts") or any(not item.get("present") for item in receipt["artifacts"]):
        raise ReadinessError("readiness receipt has missing artifacts")
    return receipt


def check_receipt(commit: str) -> int:
    repo = _repo_root()
    _read_receipt(repo, commit)
    print("HMASD_EXECUTION_READINESS_RECEIPT_OK")
    return 0


def _message_field(message: str, name: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(name)}=(.*)$", message)
    return match.group(1).strip() if match else None


def _hook_feedback(reason: str, already_active: bool) -> dict[str, Any]:
    if already_active:
        return {
            "continue": False,
            "stopReason": "invalid_code_acceptance",
            "systemMessage": reason,
        }
    return {
        "decision": "block",
        "reason": reason + " Run the Skill script or return CODE_ACCEPTANCE_BLOCKED.",
    }


def hook_stop() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    try:
        repo = _repo_root()
        code_pm_session = _code_pm_session(repo)
    except ReadinessError:
        return 0
    if payload.get("session_id") != code_pm_session:
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
    if not commit or not COMMIT_RE.fullmatch(commit):
        print(json.dumps(_hook_feedback("CODE_ACCEPTED has no exact 40-character commit.", already_active)))
        return 0
    if not exact_paths:
        print(json.dumps(_hook_feedback("CODE_ACCEPTED has no exact_paths.", already_active)))
        return 0
    if readiness == "not_triggered":
        if _git(repo, "rev-parse", "HEAD") != commit:
            print(json.dumps(_hook_feedback("CODE_ACCEPTED commit is not current HEAD.", already_active)))
            return 0
        if not reason or reason in {"none", "not-triggered", "not_triggered"}:
            print(json.dumps(_hook_feedback("Untriggered execution readiness needs a bounded reason.", already_active)))
        return 0
    if readiness != "passed":
        print(json.dumps(_hook_feedback("CODE_ACCEPTED has no passed execution_readiness state.", already_active)))
        return 0
    try:
        receipt = _read_receipt(repo, commit)
        expected_receipt_path = _receipt_path(repo, commit)
        if not receipt_field or Path(receipt_field).resolve() != expected_receipt_path:
            raise ReadinessError("CODE_ACCEPTED does not name the exact readiness receipt")
        returned_paths = [item for item in exact_paths.split("|") if item]
        if receipt.get("exact_paths") != returned_paths:
            raise ReadinessError("receipt exact_paths do not match CODE_ACCEPTED")
    except ReadinessError as exc:
        print(json.dumps(_hook_feedback(str(exc), already_active)))
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
    check_parser.add_argument("--commit", required=True)
    subparsers.add_parser("hook-stop")
    args = parser.parse_args()
    try:
        if args.command == "run":
            return run_spec(args.spec)
        if args.command == "finalize":
            return finalize_spec(args.spec)
        if args.command == "check":
            return check_receipt(args.commit)
        return hook_stop()
    except ReadinessError as exc:
        print(f"HMASD_EXECUTION_READINESS_ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
