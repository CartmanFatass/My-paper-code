from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


SPEC_SCHEMA = "HMASD_LONG_EFFECT_V1"
OBSERVATION_SCHEMA = "HMASD_LONG_EFFECT_OBSERVATION_V1"
RUN_FILE_NAMES = (
    "experiment.json",
    "owner.json",
    "stdout.log",
    "stderr.log",
    "terminal.json",
)


class LongEffectError(RuntimeError):
    """Base error for the minimal file-backed process recorder."""


class SpecValidationError(LongEffectError, ValueError):
    """The supplied experiment specification is not valid."""


class RunRootConflict(LongEffectError, FileExistsError):
    """The requested run root has already been claimed or populated."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise SpecValidationError(f"{label} keys differ: missing={missing}, extra={extra}")


def _validate_refs(value: Any, label: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise SpecValidationError(f"{label} must be a list")
    result: list[dict[str, str]] = []
    names: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise SpecValidationError(f"{label}[{index}] must be an object")
        _require_exact_keys(item, {"name", "path"}, f"{label}[{index}]")
        name = item["name"]
        path = item["path"]
        if not isinstance(name, str) or not name:
            raise SpecValidationError(f"{label}[{index}].name must be a non-empty string")
        if name in names:
            raise SpecValidationError(f"{label} contains duplicate name {name!r}")
        if not isinstance(path, str) or not path:
            raise SpecValidationError(f"{label}[{index}].path must be a non-empty string")
        names.add(name)
        result.append({"name": name, "path": path})
    return result


def validate_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a detached, JSON-compatible copy of a process spec."""

    if not isinstance(spec, Mapping):
        raise SpecValidationError("spec must be an object")
    _require_exact_keys(
        spec,
        {
            "schema",
            "experiment_id",
            "component",
            "working_directory",
            "argv",
            "input_refs",
            "output_refs",
            "metadata",
        },
        "spec",
    )
    if spec["schema"] != SPEC_SCHEMA:
        raise SpecValidationError(f"schema must equal {SPEC_SCHEMA!r}")
    experiment_id = spec["experiment_id"]
    if not isinstance(experiment_id, str):
        raise SpecValidationError("experiment_id must be a UUID string")
    try:
        parsed_id = uuid.UUID(experiment_id)
    except (ValueError, AttributeError) as exc:
        raise SpecValidationError("experiment_id must be a UUID string") from exc
    if str(parsed_id) != experiment_id.lower():
        raise SpecValidationError("experiment_id must use canonical UUID spelling")
    component = spec["component"]
    if not isinstance(component, str) or not component:
        raise SpecValidationError("component must be a non-empty string")
    working_directory = spec["working_directory"]
    if not isinstance(working_directory, str) or not working_directory:
        raise SpecValidationError("working_directory must be a non-empty string")
    work_path = Path(working_directory)
    if not work_path.is_absolute():
        raise SpecValidationError("working_directory must be absolute")
    argv = spec["argv"]
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(part, str) or not part for part in argv)
    ):
        raise SpecValidationError("argv must be a non-empty list of non-empty strings")
    metadata = spec["metadata"]
    if not isinstance(metadata, Mapping):
        raise SpecValidationError("metadata must be an object")
    _require_exact_keys(metadata, {"direction_id", "stage", "effect_id"}, "metadata")
    for key, value in metadata.items():
        if value is not None and not isinstance(value, str):
            raise SpecValidationError(f"metadata.{key} must be a string or null")
    normalized = {
        "schema": SPEC_SCHEMA,
        "experiment_id": experiment_id.lower(),
        "component": component,
        "working_directory": str(work_path),
        "argv": list(argv),
        "input_refs": _validate_refs(spec["input_refs"], "input_refs"),
        "output_refs": _validate_refs(spec["output_refs"], "output_refs"),
        "metadata": dict(metadata),
    }
    try:
        json.dumps(normalized, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise SpecValidationError("spec must contain only finite JSON values") from exc
    return normalized


def load_spec(path: str | os.PathLike[str]) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        raw = json.load(stream)
    return validate_spec(raw)


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _publish_json_no_overwrite(path: Path, value: Mapping[str, Any]) -> None:
    payload = _json_bytes(value)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    published = False
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise RunRootConflict(f"record already exists: {path}") from exc
        published = True
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    if not published:
        raise LongEffectError(f"record was not published: {path}")


def _create_log(path: Path):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return os.fdopen(descriptor, "wb", buffering=0)


def _flush_log(stream: Any) -> None:
    stream.flush()
    os.fsync(stream.fileno())


def _load_json_record(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except FileNotFoundError:
        return None, None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, type(exc).__name__
    if not isinstance(value, dict):
        return None, "RecordNotObject"
    return value, None


def _resolve_spec(spec: Mapping[str, Any] | str | os.PathLike[str]) -> dict[str, Any]:
    if isinstance(spec, Mapping):
        return validate_spec(spec)
    return load_spec(spec)


def run_long_effect(
    spec: Mapping[str, Any] | str | os.PathLike[str],
    run_root: str | os.PathLike[str],
) -> dict[str, Any]:
    """Run one child synchronously while recording one immutable file envelope."""

    normalized = _resolve_spec(spec)
    root = Path(run_root).absolute()
    try:
        root.mkdir(parents=False, exist_ok=False)
    except FileExistsError as exc:
        raise RunRootConflict(f"run root must be fresh: {root}") from exc

    _publish_json_no_overwrite(root / "experiment.json", normalized)
    stdout_stream = _create_log(root / "stdout.log")
    try:
        stderr_stream = _create_log(root / "stderr.log")
    except BaseException:
        stdout_stream.close()
        raise

    owner = {
        "owner_pid": os.getpid(),
        "acquired_at": _utc_now(),
        "experiment_id": normalized["experiment_id"],
    }
    try:
        _publish_json_no_overwrite(root / "owner.json", owner)
    except BaseException:
        stdout_stream.close()
        stderr_stream.close()
        raise

    started_at = _utc_now()
    child: subprocess.Popen[bytes] | None = None
    terminal: dict[str, Any]
    try:
        try:
            child = subprocess.Popen(
                normalized["argv"],
                cwd=normalized["working_directory"],
                stdout=stdout_stream,
                stderr=stderr_stream,
                shell=False,
            )
        except Exception as exc:
            terminal = {
                "phase": "PRE_CHILD_ERROR",
                "pid": None,
                "started_at": started_at,
                "finished_at": _utc_now(),
                "exit_code": None,
                "exception_category": type(exc).__name__,
            }
        else:
            try:
                exit_code = child.wait()
            except Exception as exc:
                terminal = {
                    "phase": "POST_CHILD_ERROR",
                    "pid": child.pid,
                    "started_at": started_at,
                    "finished_at": _utc_now(),
                    "exit_code": child.returncode,
                    "exception_category": type(exc).__name__,
                }
            except BaseException:
                # Operator/process-control interrupts are not terminal child
                # outcomes and must not be converted into a successful wrapper
                # return.  Keep the sole owner synchronous until the child has
                # exited, then propagate the interrupt.  The intentionally
                # absent terminal remains a directly observable recovery fact.
                child.wait()
                raise
            else:
                terminal = {
                    "phase": "CHILD_EXITED",
                    "pid": child.pid,
                    "started_at": started_at,
                    "finished_at": _utc_now(),
                    "exit_code": exit_code,
                    "exception_category": None,
                }
    finally:
        try:
            _flush_log(stdout_stream)
        finally:
            stdout_stream.close()
        try:
            _flush_log(stderr_stream)
        finally:
            stderr_stream.close()

    _publish_json_no_overwrite(root / "terminal.json", terminal)
    return terminal


def observe_long_effect(run_root: str | os.PathLike[str]) -> dict[str, Any]:
    """Read record metadata without reading process logs or declared outputs."""

    root = Path(run_root).absolute()
    experiment, experiment_error = _load_json_record(root / "experiment.json")
    owner, owner_error = _load_json_record(root / "owner.json")
    terminal, terminal_error = _load_json_record(root / "terminal.json")
    files = {name: (root / name).is_file() for name in RUN_FILE_NAMES}
    record_errors = {
        name: error
        for name, error in (
            ("experiment.json", experiment_error),
            ("owner.json", owner_error),
            ("terminal.json", terminal_error),
        )
        if error is not None
    }
    public_experiment = None
    if experiment is not None:
        public_experiment = {
            key: experiment.get(key)
            for key in ("schema", "experiment_id", "component", "metadata")
        }
    return {
        "schema": OBSERVATION_SCHEMA,
        "run_root": str(root),
        "files": files,
        "experiment": public_experiment,
        "owner": owner,
        "terminal": terminal,
        "owner_without_terminal": owner is not None and terminal is None,
        "record_errors": record_errors,
    }


def run_effect(spec_path: Path, run_root: Path) -> dict[str, Any]:
    """Stable CLI-facing adapter for a file-backed specification."""

    return run_long_effect(spec_path, run_root)


def observe_run(run_root: Path) -> dict[str, Any]:
    """Stable CLI-facing adapter for metadata-only observation."""

    return observe_long_effect(run_root)


__all__: Sequence[str] = (
    "LongEffectError",
    "OBSERVATION_SCHEMA",
    "RUN_FILE_NAMES",
    "RunRootConflict",
    "SPEC_SCHEMA",
    "SpecValidationError",
    "load_spec",
    "observe_long_effect",
    "observe_run",
    "run_effect",
    "run_long_effect",
    "validate_spec",
)
