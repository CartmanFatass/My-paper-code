"""Deterministic dispatcher for one bounded CPM mechanical assignment.

The dispatcher is intentionally small and file-oriented.  A native child is
started with ``run --spec <json> --result <json>`` and emits one terminal line
after writing the result atomically.  The spec is the complete authority for
the operation; this module never creates a queue, retries a failed task, or
interprets scientific meaning.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = 1
REGISTERED_INTERPRETER = Path(
    r"C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
TICKET_SCRIPT = REPOSITORY_ROOT / "scripts" / "hmasd_workspace_ticket.py"
TASK_CLASSES = {
    "inspect_identity",
    "run_focused_checks",
    "verify_result",
    "assemble_handoff",
    "render_state",
    "ticket_prepare",
}
RETRY_CLASSES = {"INVOCATION", "TIMEOUT", "CHECK", "NONE"}
COMMON_SPEC_FIELDS = (
    "schema_version",
    "assignment_id",
    "task_class",
    "attempt_id",
    "working_directory",
    "allowed_read_paths",
    "allowed_write_paths",
    "result_path",
    "task",
)


class MechanicalError(RuntimeError):
    """A deterministic, mechanical assignment failure."""

    def __init__(self, code: str, path: str, message: str, retry_class: str = "CHECK"):
        super().__init__(message)
        self.code = code
        self.path = path
        self.message = message
        self.retry_class = retry_class
        self.observations: Any = {}
        self.output_paths: list[str] = []
        self.log_paths: list[str] = []


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise MechanicalError("INVALID_SPEC", field, f"{field} must be a non-empty string")
    return value


def _path_key(path: Path) -> str:
    return os.path.normcase(str(path.resolve(strict=False)))


def _same_path(left: Path, right: Path) -> bool:
    return _path_key(left) == _path_key(right)


def _canonical_root(raw: Any, *, field: str, must_exist: bool = True) -> Path:
    value = _text(raw, field=field)
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        raise MechanicalError("INVALID_SPEC", field, f"{field} must be absolute")
    try:
        resolved = candidate.resolve(strict=must_exist)
    except OSError as exc:
        raise MechanicalError("IDENTITY_MISMATCH", field, f"{field} does not resolve: {exc}") from exc
    return resolved


def _relative_name(raw: Any, *, field: str) -> str:
    value = _text(raw, field=field).replace("\\", "/")
    candidate = PurePosixPath(value)
    if (
        candidate.is_absolute()
        or not value
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or ":" in candidate.parts[0]
    ):
        raise MechanicalError("PATH_NOT_ALLOWED", field, f"unsafe relative path: {value!r}")
    return candidate.as_posix()


def _path_list(raw: Any, *, field: str) -> list[str]:
    if not isinstance(raw, list):
        raise MechanicalError("INVALID_SPEC", field, f"{field} must be a list")
    paths: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(raw):
        name = _relative_name(value, field=f"{field}[{index}]")
        if name in seen:
            raise MechanicalError("PATH_NOT_ALLOWED", field, f"duplicate path: {name}")
        seen.add(name)
        paths.append(name)
    return paths


def _under(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _allowed(candidate: Path, root: Path, allow: Iterable[str]) -> bool:
    relative = candidate.relative_to(root).as_posix()
    return any(relative == name or relative.startswith(name + "/") for name in allow)


def _resolve_path(
    raw: Any,
    *,
    root: Path,
    allow: list[str],
    field: str,
    write: bool = False,
    must_exist: bool = False,
    allow_root: bool = False,
) -> Path:
    value = _text(raw, field=field)
    candidate = Path(value)
    if candidate.is_absolute():
        joined = candidate
    else:
        joined = root / _relative_name(value, field=field)
    try:
        resolved = joined.resolve(strict=must_exist)
    except OSError as exc:
        code = "UNREADABLE_ARTIFACT" if not write else "PATH_NOT_ALLOWED"
        raise MechanicalError(code, field, f"cannot resolve path: {exc}") from exc
    if not _under(resolved, root) or (not _allowed(resolved, root, allow) and not (allow_root and _same_path(resolved, root))):
        raise MechanicalError("PATH_NOT_ALLOWED", field, f"path is not allow-listed: {value}")
    if write and resolved.exists() and resolved.is_dir():
        raise MechanicalError("PATH_NOT_ALLOWED", field, f"write target is a directory: {value}")
    return resolved


def _atomic_write(path: Path, data: str) -> None:
    """Write *data* beside *path* and replace it in one filesystem operation."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent), text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _captured_text(value: str | bytes | None) -> str:
    """Normalize subprocess output, including TimeoutExpired byte streams."""

    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _json_load(path: Path, *, code: str = "INVALID_JSON") -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise MechanicalError("UNREADABLE_ARTIFACT", str(path), str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise MechanicalError(code, str(path), str(exc)) from exc


def _field_value(value: Any, path: str) -> Any:
    current = value
    if not path:
        return current
    for part in path.split("."):
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            raise KeyError(path)
    return current


def _validate_common(spec: Mapping[str, Any]) -> tuple[Path, list[str], list[str], Path]:
    missing = [field for field in COMMON_SPEC_FIELDS if field not in spec]
    if missing:
        raise MechanicalError("INVALID_SPEC", "spec", "missing fields: " + ", ".join(missing))
    if spec.get("schema_version") != SCHEMA_VERSION:
        raise MechanicalError("INVALID_SPEC", "schema_version", "unsupported schema_version")
    _text(spec.get("assignment_id"), field="assignment_id")
    task_class = _text(spec.get("task_class"), field="task_class")
    if task_class not in TASK_CLASSES:
        raise MechanicalError("INVALID_SPEC", "task_class", f"unsupported task class: {task_class}")
    _text(spec.get("attempt_id"), field="attempt_id")
    root = _canonical_root(spec.get("working_directory"), field="working_directory")
    reads = _path_list(spec.get("allowed_read_paths"), field="allowed_read_paths")
    writes = _path_list(spec.get("allowed_write_paths"), field="allowed_write_paths")
    result = _resolve_path(
        spec.get("result_path"), root=root, allow=writes, field="result_path", write=True
    )
    if not isinstance(spec.get("task"), Mapping):
        raise MechanicalError("INVALID_SPEC", "task", "task must be an object")
    return root, reads, writes, result


def _ensure_registered_interpreter() -> None:
    expected = _path_key(REGISTERED_INTERPRETER)
    actual = _path_key(Path(sys.executable))
    if actual != expected:
        raise MechanicalError(
            "IDENTITY_MISMATCH",
            "interpreter",
            f"registered interpreter mismatch: expected {REGISTERED_INTERPRETER}, got {sys.executable}",
            retry_class="INVOCATION",
        )


def _task_inspect_identity(spec: Mapping[str, Any], root: Path, reads: list[str], writes: list[str]) -> dict[str, Any]:
    task = spec["task"]
    identity: dict[str, Any] = {
        "assignment_id": spec["assignment_id"],
        "attempt_id": spec["attempt_id"],
        "task_class": spec["task_class"],
        "working_directory": str(root),
        "interpreter": str(Path(sys.executable).resolve(strict=False)),
        "allowed_read_paths": list(reads),
        "allowed_write_paths": list(writes),
    }
    expected = task.get("expected_identity", task.get("expected", {}))
    if expected:
        if not isinstance(expected, Mapping):
            raise MechanicalError("INVALID_SPEC", "task.expected_identity", "expected identity must be an object")
        for key, value in expected.items():
            if identity.get(key) != value:
                raise MechanicalError("IDENTITY_MISMATCH", str(key), f"identity mismatch for {key}")
    return {"identity": identity}


def _check_log_path(task: Mapping[str, Any], index: int, root: Path, writes: list[str]) -> Path:
    raw = task.get("log_path")
    if raw is None:
        raw = task.get("log")
    if raw is None:
        raise MechanicalError("INVALID_SPEC", f"task.checks[{index}].log_path", "each check needs a log_path")
    return _resolve_path(raw, root=root, allow=writes, field=f"task.checks[{index}].log_path", write=True)


def _task_run_focused_checks(spec: Mapping[str, Any], root: Path, reads: list[str], writes: list[str]) -> tuple[dict[str, Any], list[str], list[str]]:
    task = spec["task"]
    checks = task.get("checks", task.get("commands"))
    if not isinstance(checks, list) or not checks:
        raise MechanicalError("INVALID_SPEC", "task.checks", "checks must be a non-empty list")
    observations: list[dict[str, Any]] = []
    log_paths: list[str] = []
    for index, raw_check in enumerate(checks):
        if not isinstance(raw_check, Mapping):
            raise MechanicalError("INVALID_SPEC", f"task.checks[{index}]", "check must be an object")
        argv = raw_check.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(value, str) for value in argv):
            raise MechanicalError("INVALID_SPEC", f"task.checks[{index}].argv", "argv must be a non-empty string array")
        if _path_key(Path(argv[0])) != _path_key(REGISTERED_INTERPRETER):
            raise MechanicalError("INVOCATION_NOT_ALLOWED", f"task.checks[{index}].argv", "checks must use the registered interpreter", "INVOCATION")
        lowered = " ".join(argv).lower()
        if any(token in lowered for token in ("py_compile", "compileall", "-m compile", ".pyc")):
            raise MechanicalError("BYTECODE_NOT_ALLOWED", f"task.checks[{index}].argv", "bytecode-producing checks are forbidden")
        timeout = raw_check.get("timeout_sec", raw_check.get("timeout"))
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise MechanicalError("INVALID_SPEC", f"task.checks[{index}].timeout_sec", "timeout_sec must be positive")
        cwd_raw = raw_check.get("cwd")
        cwd = root if cwd_raw is None else _resolve_path(
            cwd_raw, root=root, allow=reads, field=f"task.checks[{index}].cwd", must_exist=True, allow_root=True
        )
        if not cwd.is_dir():
            raise MechanicalError("PATH_NOT_ALLOWED", f"task.checks[{index}].cwd", "cwd must be a directory")
        log_path = _check_log_path(raw_check, index, root, writes)
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            completed = subprocess.run(
                argv,
                cwd=str(cwd),
                env=env,
                shell=False,
                capture_output=True,
                text=True,
                timeout=float(timeout),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            output = _captured_text(exc.stdout) + _captured_text(exc.stderr)
            _atomic_write(log_path, output)
            log_paths.append(str(log_path))
            failure = MechanicalError("CHECK_TIMEOUT", str(log_path), f"check timed out after {timeout}s", "TIMEOUT")
            failure.observations = {"checks": observations}
            failure.log_paths = list(log_paths)
            raise failure from exc
        except OSError as exc:
            failure = MechanicalError("INVOCATION_ERROR", str(log_path), str(exc), "INVOCATION")
            failure.observations = {"checks": observations}
            failure.log_paths = list(log_paths)
            raise failure from exc
        output = (completed.stdout or "") + (completed.stderr or "")
        _atomic_write(log_path, output)
        log_paths.append(str(log_path))
        observation = {"index": index, "argv": list(argv), "exit_code": completed.returncode, "log_path": str(log_path)}
        observations.append(observation)
        if completed.returncode != 0:
            failure = MechanicalError("CHECK_FAILED", str(log_path), f"focused check exited {completed.returncode}", "CHECK")
            failure.observations = {"checks": observations}
            failure.log_paths = list(log_paths)
            raise failure
    return {"checks": observations}, [], log_paths


def _required_artifacts(task: Mapping[str, Any]) -> list[Any]:
    value = task.get("required_artifacts", task.get("artifacts", []))
    if not isinstance(value, list):
        raise MechanicalError("INVALID_SPEC", "task.required_artifacts", "required_artifacts must be a list")
    return value


def _load_artifact(raw: Any, index: int, root: Path, reads: list[str]) -> tuple[str, Path, Any | None]:
    if isinstance(raw, str):
        name = raw
        json_required = False
    elif isinstance(raw, Mapping):
        name = raw.get("path", raw.get("artifact"))
        json_required = bool(raw.get("json", False))
    else:
        raise MechanicalError("INVALID_SPEC", f"task.required_artifacts[{index}]", "artifact must be a path or object")
    path = _resolve_path(name, root=root, allow=reads, field=f"task.required_artifacts[{index}].path", must_exist=True)
    if not path.is_file():
        raise MechanicalError("MISSING_ARTIFACT", str(path), "required artifact is not a file")
    try:
        encoding = "utf-8-sig" if json_required or path.suffix.lower() == ".json" else "utf-8"
        content = path.read_text(encoding=encoding)
    except (OSError, UnicodeError) as exc:
        raise MechanicalError("UNREADABLE_ARTIFACT", str(path), str(exc)) from exc
    parsed: Any | None = None
    if json_required or path.suffix.lower() == ".json":
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise MechanicalError("INVALID_JSON", str(path), str(exc)) from exc
    return str(path), path, parsed


def _task_verify_result(spec: Mapping[str, Any], root: Path, reads: list[str], writes: list[str]) -> dict[str, Any]:
    task = spec["task"]
    artifacts: dict[str, Any] = {}
    output_paths: list[str] = []
    for index, raw in enumerate(_required_artifacts(task)):
        name, _path, parsed = _load_artifact(raw, index, root, reads)
        artifacts[name] = parsed
        output_paths.append(name)

    required_fields = task.get("required_json_fields", task.get("json_fields", {}))
    if required_fields and not isinstance(required_fields, Mapping):
        raise MechanicalError("INVALID_SPEC", "task.required_json_fields", "required_json_fields must be an object")
    for raw_name, fields in (required_fields.items() if isinstance(required_fields, Mapping) else []):
        name = str(_resolve_path(raw_name, root=root, allow=reads, field="task.required_json_fields.path", must_exist=True))
        parsed = artifacts.get(name)
        if parsed is None:
            # Accept the caller's relative spelling as a lookup key as well.
            parsed = artifacts.get(str(root / _relative_name(raw_name, field="task.required_json_fields.path")))
        if parsed is None:
            raise MechanicalError("INVALID_JSON", raw_name, "JSON artifact was not loaded")
        if not isinstance(fields, list):
            raise MechanicalError("INVALID_SPEC", raw_name, "required fields must be a list")
        for field in fields:
            try:
                _field_value(parsed, str(field))
            except KeyError as exc:
                raise MechanicalError("MISSING_JSON_FIELD", f"{raw_name}.{field}", "required JSON field is absent") from exc

    declared_identity = task.get("identity")
    if declared_identity is not None:
        if not isinstance(declared_identity, Mapping):
            raise MechanicalError("INVALID_SPEC", "task.identity", "identity must be an object")
        for key, expected in declared_identity.items():
            if spec.get(key) != expected:
                raise MechanicalError("IDENTITY_MISMATCH", str(key), f"assignment identity mismatch for {key}")

    exact = task.get("exact_equals", task.get("expected_identity", {}))
    if isinstance(exact, Mapping) and all(key in spec for key in exact):
        for key, expected in exact.items():
            if spec.get(key) != expected:
                raise MechanicalError("IDENTITY_MISMATCH", str(key), f"assignment identity mismatch for {key}")
        exact = {}
    exact_entries: list[tuple[str, Any, str]] = []
    if isinstance(exact, Mapping):
        for raw_name, expected in exact.items():
            if isinstance(expected, Mapping) and raw_name in artifacts:
                for field, value in expected.items():
                    exact_entries.append((raw_name, value, str(field)))
            else:
                exact_entries.append((str(raw_name), expected, ""))
    elif isinstance(exact, list):
        for item in exact:
            if not isinstance(item, Mapping):
                raise MechanicalError("INVALID_SPEC", "task.exact_equals", "exact_equals entries must be objects")
            exact_entries.append((str(item.get("artifact", item.get("path"))), item.get("expected"), str(item.get("field", ""))))
    elif exact:
        raise MechanicalError("INVALID_SPEC", "task.exact_equals", "exact_equals must be an object or list")
    for raw_name, expected, field in exact_entries:
        key = str(_resolve_path(raw_name, root=root, allow=reads, field="task.exact_equals.path", must_exist=True))
        actual = artifacts.get(key)
        if field:
            try:
                actual = _field_value(actual, field)
            except KeyError as exc:
                raise MechanicalError("MISSING_JSON_FIELD", f"{raw_name}.{field}", "exact-equality field is absent") from exc
        if actual != expected:
            raise MechanicalError("IDENTITY_MISMATCH", f"{raw_name}.{field}" if field else raw_name, "exact equality check failed")

    extractions: dict[str, Any] = {}
    extraction_specs = task.get("extractions", [])
    if not isinstance(extraction_specs, list):
        raise MechanicalError("INVALID_SPEC", "task.extractions", "extractions must be a list")
    for index, item in enumerate(extraction_specs):
        if not isinstance(item, Mapping):
            raise MechanicalError("INVALID_SPEC", f"task.extractions[{index}]", "extraction must be an object")
        raw_name = item.get("artifact", item.get("path"))
        field = str(item.get("field", ""))
        key = str(_resolve_path(raw_name, root=root, allow=reads, field=f"task.extractions[{index}].artifact", must_exist=True))
        try:
            value = _field_value(artifacts[key], field)
        except KeyError as exc:
            raise MechanicalError("MISSING_JSON_FIELD", f"{raw_name}.{field}", "extraction field is absent") from exc
        extractions[str(item.get("name", field or raw_name))] = value

    constraints = task.get("numeric_constraints", [])
    if not isinstance(constraints, list):
        raise MechanicalError("INVALID_SPEC", "task.numeric_constraints", "numeric_constraints must be a list")
    for index, item in enumerate(constraints):
        if not isinstance(item, Mapping):
            raise MechanicalError("INVALID_SPEC", f"task.numeric_constraints[{index}]", "constraint must be an object")
        raw_name = item.get("artifact", item.get("path"))
        field = str(item.get("field", ""))
        key = str(_resolve_path(raw_name, root=root, allow=reads, field=f"task.numeric_constraints[{index}].artifact", must_exist=True))
        try:
            value = _field_value(artifacts[key], field)
        except KeyError as exc:
            raise MechanicalError("MISSING_JSON_FIELD", f"{raw_name}.{field}", "numeric field is absent") from exc
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MechanicalError("NUMERIC_CONSTRAINT", f"{raw_name}.{field}", "value is not numeric")
        if "equals" in item and value != item["equals"]:
            raise MechanicalError("NUMERIC_CONSTRAINT", f"{raw_name}.{field}", "numeric equality failed")
        if "minimum" in item and value < item["minimum"]:
            raise MechanicalError("NUMERIC_CONSTRAINT", f"{raw_name}.{field}", "value is below minimum")
        if "maximum" in item and value > item["maximum"]:
            raise MechanicalError("NUMERIC_CONSTRAINT", f"{raw_name}.{field}", "value exceeds maximum")
        if item.get("integer") and int(value) != value:
            raise MechanicalError("NUMERIC_CONSTRAINT", f"{raw_name}.{field}", "value is not an integer")
        extractions[str(item.get("name", field or raw_name))] = value

    return {"artifacts": output_paths, "extractions": extractions}


def _task_assemble_handoff(spec: Mapping[str, Any], root: Path, reads: list[str], writes: list[str]) -> tuple[dict[str, Any], list[str], list[str]]:
    task = spec["task"]
    evidence_specs = task.get("evidence", task.get("artifacts", []))
    if not isinstance(evidence_specs, list):
        raise MechanicalError("INVALID_SPEC", "task.evidence", "evidence must be a list")
    evidence: list[dict[str, Any]] = []
    for index, raw in enumerate(evidence_specs):
        name, path, parsed = _load_artifact(raw, index, root, reads)
        evidence.append({"path": name, "readable": True, "json": parsed is not None})
    output_raw = task.get("output_path", task.get("handoff_path"))
    output = _resolve_path(output_raw, root=root, allow=writes, field="task.output_path", write=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "kind": "CPM_MECHANICAL_HANDOFF",
        "assignment_id": spec["assignment_id"],
        "attempt_id": spec["attempt_id"],
        "evidence": evidence,
    }
    _atomic_write(output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return {"handoff_path": str(output), "evidence": evidence}, [str(output)], []


def _temporary_owner_path(path: Path, root: Path) -> bool:
    relative = path.relative_to(root).as_posix()
    return relative == "temp" or relative.startswith("temp/")


def _task_render_state(spec: Mapping[str, Any], root: Path, reads: list[str], writes: list[str]) -> tuple[dict[str, Any], list[str], list[str]]:
    task = spec["task"]
    files = task.get("proposed_files", task.get("files", []))
    if not isinstance(files, list) or not files:
        raise MechanicalError("INVALID_SPEC", "task.proposed_files", "proposed_files must be a non-empty list")
    rendered: list[str] = []
    for index, item in enumerate(files):
        if not isinstance(item, Mapping):
            raise MechanicalError("INVALID_SPEC", f"task.proposed_files[{index}]", "file must be an object")
        path = _resolve_path(item.get("path"), root=root, allow=writes, field=f"task.proposed_files[{index}].path", write=True)
        if not _temporary_owner_path(path, root):
            raise MechanicalError("OWNER_FILE_NOT_TEMPORARY", str(path), "render_state writes only proposed temp owner files")
        content = item.get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content, indent=2, sort_keys=True) + "\n"
        _atomic_write(path, content)
        rendered.append(str(path))
    return {"rendered_paths": rendered}, rendered, []


def _task_ticket_prepare(spec: Mapping[str, Any], root: Path, reads: list[str], writes: list[str]) -> tuple[dict[str, Any], list[str], list[str]]:
    task = spec["task"]
    timeout = task.get("timeout_sec", task.get("timeout", 30))
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise MechanicalError("INVALID_SPEC", "task.timeout_sec", "timeout_sec must be positive")
    raw_argv = task.get("argv")
    if raw_argv is None:
        raise MechanicalError(
            "INVALID_SPEC",
            "task.argv",
            "ticket_prepare requires the complete prepare-integrate argv",
        )
    if not isinstance(raw_argv, list) or not raw_argv or any(not isinstance(value, str) for value in raw_argv):
        raise MechanicalError("INVALID_SPEC", "task.argv", "ticket argv must be a string array")
    if len(raw_argv) < 3 or _path_key(Path(raw_argv[0])) != _path_key(REGISTERED_INTERPRETER):
        raise MechanicalError("INVOCATION_NOT_ALLOWED", "task.argv", "ticket_prepare must use registered interpreter", "INVOCATION")
    if _path_key(Path(raw_argv[1])) != _path_key(TICKET_SCRIPT) or raw_argv[2] != "prepare-integrate":
        raise MechanicalError("INVOCATION_NOT_ALLOWED", "task.argv", "only the exact prepare-integrate ticket command is allowed", "INVOCATION")
    if len(raw_argv) != 11 or raw_argv[3::2] != [
        "--ticket",
        "--assignment-id",
        "--target-repo",
        "--receipt",
    ]:
        raise MechanicalError(
            "INVOCATION_NOT_ALLOWED",
            "task.argv",
            "ticket_prepare requires the exact ticket, assignment, target and receipt arguments",
            "INVOCATION",
        )
    _resolve_path(raw_argv[4], root=root, allow=reads, field="task.argv.ticket", must_exist=True)
    if raw_argv[6] != spec["assignment_id"]:
        raise MechanicalError("IDENTITY_MISMATCH", "task.argv.assignment_id", "ticket assignment identity mismatch")
    target_repo = Path(raw_argv[8]).expanduser().resolve(strict=True)
    if not _same_path(target_repo, root):
        raise MechanicalError("PATH_NOT_ALLOWED", "task.argv.target_repo", "ticket target must be the assigned working directory")
    _resolve_path(raw_argv[10], root=root, allow=writes, field="task.argv.receipt", write=True)
    log_path_raw = task.get("log_path", task.get("log"))
    log_path = None
    if log_path_raw is not None:
        log_path = _resolve_path(log_path_raw, root=root, allow=writes, field="task.log_path", write=True)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            raw_argv,
            cwd=str(root),
            env=env,
            shell=False,
            capture_output=True,
            text=True,
            timeout=float(timeout),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        if log_path:
            _atomic_write(log_path, _captured_text(exc.stdout) + _captured_text(exc.stderr))
        failure = MechanicalError("CHECK_TIMEOUT", str(log_path or TICKET_SCRIPT), f"ticket prepare timed out after {timeout}s", "TIMEOUT")
        failure.log_paths = [] if log_path is None else [str(log_path)]
        raise failure from exc
    except OSError as exc:
        raise MechanicalError("INVOCATION_ERROR", str(TICKET_SCRIPT), str(exc), "INVOCATION") from exc
    output = (completed.stdout or "") + (completed.stderr or "")
    log_paths: list[str] = []
    if log_path:
        _atomic_write(log_path, output)
        log_paths.append(str(log_path))
    if completed.returncode != 0:
        failure = MechanicalError("CHECK_FAILED", str(log_path or TICKET_SCRIPT), f"prepare-integrate exited {completed.returncode}", "CHECK")
        failure.log_paths = list(log_paths)
        raise failure
    return {"argv": list(raw_argv), "exit_code": completed.returncode}, [], log_paths


def _execute_task(spec: Mapping[str, Any], root: Path, reads: list[str], writes: list[str]) -> tuple[dict[str, Any], list[str], list[str]]:
    task_class = spec["task_class"]
    if task_class == "inspect_identity":
        return _task_inspect_identity(spec, root, reads, writes), [], []
    if task_class == "run_focused_checks":
        return _task_run_focused_checks(spec, root, reads, writes)
    if task_class == "verify_result":
        return _task_verify_result(spec, root, reads, writes), [], []
    if task_class == "assemble_handoff":
        return _task_assemble_handoff(spec, root, reads, writes)
    if task_class == "render_state":
        return _task_render_state(spec, root, reads, writes)
    if task_class == "ticket_prepare":
        return _task_ticket_prepare(spec, root, reads, writes)
    raise MechanicalError("INVALID_SPEC", "task_class", f"unsupported task class: {task_class}")


def _base_result(spec: Mapping[str, Any], *, status: str, observations: Any, output_paths: list[str], log_paths: list[str], failure: MechanicalError | None, exit_code: int) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "assignment_id": spec.get("assignment_id"),
        "task_class": spec.get("task_class"),
        "attempt_id": spec.get("attempt_id"),
        "observations": observations,
        "output_paths": output_paths,
        "log_paths": log_paths,
        "first_failure": None if failure is None else {"code": failure.code, "path": failure.path, "message": failure.message},
        "retry_class": "NONE" if failure is None else failure.retry_class,
        "exit_code": exit_code,
    }


def _terminal(status: str, result_path: str, error: str | None = None) -> str:
    def ascii_safe(value: str) -> str:
        return value.encode("ascii", "backslashreplace").decode("ascii")

    error_text = "none" if error is None else ascii_safe(error)
    return f"CPM_MECHANICAL_TASK_RESULT status={status} result_path={ascii_safe(result_path)} error={error_text}"


def run(spec_path: Path, result_arg: Path) -> int:
    spec: dict[str, Any] = {}
    try:
        loaded = _json_load(spec_path)
        if not isinstance(loaded, dict):
            raise MechanicalError("INVALID_SPEC", str(spec_path), "spec must be a JSON object")
        spec = loaded
        declared = spec.get("result_path")
        if not isinstance(declared, str):
            raise MechanicalError("INVALID_SPEC", "result_path", "result_path must be a string")
        declared_path = Path(declared).expanduser()
        if not declared_path.is_absolute():
            declared_path = spec_path.parent / declared_path
        if not _same_path(declared_path, result_arg):
            raise MechanicalError("RESULT_PATH_MISMATCH", "result_path", "--result must exactly match spec result_path")
        _ensure_registered_interpreter()
        root, reads, writes, result_path = _validate_common(spec)
        if not _same_path(result_path, result_arg):
            raise MechanicalError("RESULT_PATH_MISMATCH", "result_path", "--result must resolve to spec result_path")
        observations, output_paths, log_paths = _execute_task(spec, root, reads, writes)
        result = _base_result(spec, status="COMPLETE", observations=observations, output_paths=output_paths, log_paths=log_paths, failure=None, exit_code=0)
        _atomic_write(result_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(_terminal("COMPLETE", str(result_path)))
        return 0
    except MechanicalError as exc:
        target = result_arg
        if isinstance(spec.get("result_path"), str):
            candidate = Path(spec["result_path"])
            if not candidate.is_absolute():
                candidate = spec_path.parent / candidate
            target = candidate
        result = _base_result(spec, status="ERROR", observations=exc.observations, output_paths=exc.output_paths, log_paths=exc.log_paths, failure=exc, exit_code=1)
        if exc.code != "RESULT_PATH_MISMATCH":
            try:
                _atomic_write(target, json.dumps(result, indent=2, sort_keys=True) + "\n")
            except OSError:
                pass
        print(_terminal("ERROR", str(target), exc.message))
        return 1
    except (OSError, ValueError, TypeError) as exc:
        failure = MechanicalError("INVOCATION_ERROR", str(spec_path), str(exc), "INVOCATION")
        result = _base_result(spec, status="ERROR", observations={}, output_paths=[], log_paths=[], failure=failure, exit_code=1)
        try:
            _atomic_write(result_arg, json.dumps(result, indent=2, sort_keys=True) + "\n")
        except OSError:
            pass
        print(_terminal("ERROR", str(result_arg), str(exc)))
        return 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--spec", type=Path, required=True)
    run_parser.add_argument("--result", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "run":
        return run(args.spec, args.result)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
