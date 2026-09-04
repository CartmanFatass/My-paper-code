"""Independent create-once quarantine lock and no-polarity terminal facts."""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping


class QuarantineError(RuntimeError):
    pass


def quarantine_lock_path(root: str | Path) -> Path:
    value = Path(root).resolve(strict=False)
    return value.with_name(f".{value.name}.quarantine-lock.json")


def _canonical(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _atomic_create(path: Path, value: Mapping[str, object]) -> None:
    if path.exists():
        raise QuarantineError("quarantine artifact is create-only")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    except FileExistsError as error:
        raise QuarantineError("quarantine artifact is create-only") from error
    finally:
        temporary.unlink(missing_ok=True)


def _lock_value(root: Path, mode: str) -> dict[str, object]:
    return {
        "schema": "SCDMP_MF_RS_MK_B01_QUARANTINE_LOCK_V1",
        "resolved_root": str(root.resolve(strict=False)),
        "mode": mode,
        "status": "QUARANTINED_INCOMPLETE_ATTEMPT",
        "scientific_polarity": None,
        "resume_allowed": False,
    }


def ensure_quarantine_lock(root: str | Path, *, mode: str) -> Path:
    value_root = Path(root).resolve(strict=False)
    path = quarantine_lock_path(value_root)
    expected = _canonical(_lock_value(value_root, mode))
    if path.exists():
        try:
            observed = path.read_bytes()
        except OSError as error:
            raise QuarantineError("quarantine lock cannot be read") from error
        if observed != expected:
            raise QuarantineError("quarantine lock binding differs")
        return path
    _atomic_create(path, _lock_value(value_root, mode))
    return path


def write_no_polarity_terminal(
    root: str | Path,
    *,
    mode: str,
    stage: str,
    error_type: str,
    telemetry: object | None,
    active_gate_binding: Mapping[str, object] | None = None,
) -> Path:
    value_root = Path(root).resolve(strict=False)
    if (value_root / "published-result.json").exists() or (value_root / "assessment.json").exists():
        raise QuarantineError("published artifact forbids a quarantine terminal")
    ensure_quarantine_lock(value_root, mode=mode)
    value_root.mkdir(parents=True, exist_ok=True)
    path = value_root / "terminal-no-polarity.json"
    telemetry_value = asdict(telemetry) if telemetry is not None else None
    _atomic_create(path, {
        "schema": "SCDMP_MF_RS_MK_B01_NO_POLARITY_V1",
        "mode": mode,
        "stage": stage,
        "status": "QUARANTINED_INCOMPLETE_ATTEMPT",
        "scientific_polarity": None,
        "ordered_branch": None,
        "error_type": error_type,
        "telemetry": telemetry_value,
        "quarantine_lock": str(quarantine_lock_path(value_root)),
        "active_invocation_gate": None if active_gate_binding is None else dict(active_gate_binding),
    })
    return path


def raise_after_quarantine(
    root: str | Path,
    *,
    mode: str,
    stage: str,
    original: BaseException,
    telemetry: object | None,
    active_gate_binding: Mapping[str, object] | None = None,
) -> None:
    try:
        ensure_quarantine_lock(root, mode=mode)
    except BaseException as lock_error:
        try:
            setattr(original, "quarantine_lock_error", lock_error)
        except BaseException:
            pass
        raise original
    try:
        write_no_polarity_terminal(
            root, mode=mode, stage=stage, error_type=type(original).__name__, telemetry=telemetry,
            active_gate_binding=active_gate_binding,
        )
    except BaseException:
        # The independently persisted lock is already sufficient to reject
        # every future resume; preserve the exact primary failure.
        pass
    raise original


def validate_quarantine_lock(root: str | Path, *, mode: str) -> bool:
    path = quarantine_lock_path(root)
    if not path.exists():
        return False
    ensure_quarantine_lock(root, mode=mode)
    return True


__all__ = [
    "QuarantineError", "ensure_quarantine_lock", "quarantine_lock_path",
    "raise_after_quarantine", "validate_quarantine_lock", "write_no_polarity_terminal",
]
