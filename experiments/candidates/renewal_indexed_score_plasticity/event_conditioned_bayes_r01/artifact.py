"""Canonical, no-overwrite, complete-only artifact publication."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from .contract import (
    COMPLETE_RESULT_SCHEMA,
    MAX_DURABLE_BYTES,
    RESULT_NAME,
    canonical_json_bytes,
    validate_schema_instance,
)


class ArtifactError(RuntimeError):
    """Artifact validation or atomic publication failed."""


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_once(path: Path, value: object) -> int:
    """Publish canonical JSON through an exclusive hard-link boundary."""

    payload = canonical_json_bytes(value)
    if len(payload) > MAX_DURABLE_BYTES:
        raise ArtifactError("canonical artifact exceeds the durable-output ceiling")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ArtifactError(f"refusing to overwrite existing artifact: {path}")
    temporary = path.with_name(f".{path.name}.pending-{os.getpid()}")
    if temporary.exists():
        raise ArtifactError(f"pending artifact already exists: {temporary}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except OSError as error:
            raise ArtifactError(f"atomic no-overwrite publication failed: {path}") from error
        with path.open("a+b") as handle:
            os.fsync(handle.fileno())
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()
    return len(payload)


def _validate_complete_result(value: object) -> Mapping[str, object]:
    try:
        from .analysis import validate_complete_result

        return validate_complete_result(value)
    except (RuntimeError, ValueError) as error:
        raise ArtifactError(f"complete-result validation failed: {error}") from error


def publish_complete_result(output_root: Path, value: object) -> Path:
    """Publish one fully staged result directory and never overwrite a root."""

    result = _validate_complete_result(value)
    output_root = Path(output_root)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    if output_root.exists():
        raise ArtifactError(f"refusing to overwrite existing output root: {output_root}")
    staging = output_root.with_name(f".{output_root.name}.pending-{os.getpid()}")
    if staging.exists():
        raise ArtifactError(f"pending output root already exists: {staging}")
    staging.mkdir()
    staged_result = staging / RESULT_NAME
    try:
        size = atomic_write_once(staged_result, result)
        if size > MAX_DURABLE_BYTES:
            raise ArtifactError("complete result exceeds durable-output ceiling")
        _fsync_directory(staging)
        if output_root.exists():
            raise ArtifactError("output root appeared during staging")
        try:
            os.rename(staging, output_root)
        except OSError as error:
            raise ArtifactError("atomic complete-root publication failed") from error
        _fsync_directory(output_root.parent)
    finally:
        if staging.exists():
            if staged_result.exists():
                staged_result.unlink()
            staging.rmdir()
    return output_root / RESULT_NAME


__all__ = ["ArtifactError", "atomic_write_once", "publish_complete_result"]
