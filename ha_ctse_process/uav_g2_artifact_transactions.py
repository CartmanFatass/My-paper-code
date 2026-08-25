"""Immutable artifact transactions for UAV charge-rotation G2."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


COMMIT_SCHEMA = "hmasd.uav_charge_rotation_g2.immutable_commit.v1"


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_json_immutable(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path} must contain one JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = json.loads(line)
        if type(value) is not dict:
            raise ValueError(f"{path}:{line_number} must contain one JSON object")
        rows.append(value)
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _commit_artifact(root: Path, reference: str, schema: str) -> dict[str, str]:
    artifact = root / reference
    marker_reference = f"{reference}.complete.json"
    marker = root / marker_reference
    payload = {
        "schema": COMMIT_SCHEMA,
        "artifact_schema": schema,
        "artifact_reference": reference,
        "artifact_sha256": _sha256_file(artifact),
    }
    _write_json_immutable(marker, payload)
    return {
        "reference": reference,
        "complete_reference": marker_reference,
        "sha256": payload["artifact_sha256"],
    }


def _validate_committed_artifact(
    root: Path, binding: Mapping[str, Any], *, schema: str
) -> Path:
    reference = binding.get("reference")
    complete_reference = binding.get("complete_reference")
    digest = binding.get("sha256")
    if (
        type(reference) is not str
        or type(complete_reference) is not str
        or complete_reference != f"{reference}.complete.json"
        or type(digest) is not str
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
    ):
        raise ValueError("artifact binding is malformed")
    artifact = (root / reference).resolve()
    marker_path = (root / complete_reference).resolve()
    try:
        artifact.relative_to(root.resolve())
        marker_path.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError("artifact binding escapes run root") from error
    if not artifact.is_file() or not marker_path.is_file():
        raise ValueError("artifact binding references a missing file")
    marker = _read_json(marker_path)
    expected = {
        "schema": COMMIT_SCHEMA,
        "artifact_schema": schema,
        "artifact_reference": reference,
        "artifact_sha256": digest,
    }
    if marker != expected or _sha256_file(artifact) != digest:
        raise ValueError("artifact binding SHA-256 mismatch")
    return artifact


def _recover_binding(root: Path, reference: str, *, schema: str) -> dict[str, str] | None:
    artifact = root / reference
    marker = root / f"{reference}.complete.json"
    if not artifact.exists() and not marker.exists():
        return None
    if artifact.is_file() and not marker.exists():
        artifact.unlink()
        return None
    if not artifact.is_file() or not marker.is_file():
        raise ValueError("committed artifact recovery encountered a split pair")
    try:
        value = _read_json(marker)
    except (json.JSONDecodeError, UnicodeError):
        marker.unlink()
        artifact.unlink()
        return None
    binding = {
        "reference": reference,
        "complete_reference": f"{reference}.complete.json",
        "sha256": value.get("artifact_sha256"),
    }
    _validate_committed_artifact(root, binding, schema=schema)
    return binding


def _read_binding_or_truncated(path: Path) -> dict[str, Any] | None:
    try:
        return _read_json(path)
    except (json.JSONDecodeError, UnicodeError):
        return None


def _terminal_binding(
    root: Path,
    binding_path: Path,
    *,
    reference: str,
    schema: str,
) -> dict[str, Any] | None:
    if binding_path.exists():
        binding = _read_binding_or_truncated(binding_path)
        if binding is not None:
            return binding
        binding_path.unlink()
    recovered = _recover_binding(root, reference, schema=schema)
    if recovered is not None:
        _write_json_immutable(binding_path, recovered)
    return recovered


def _recover_attempt_binding(
    root: Path,
    *,
    directory: Path,
    artifact_pattern: str,
    artifact_name_pattern: str,
    schema: str,
) -> dict[str, str] | None:
    candidates: list[tuple[int, dict[str, str]]] = []
    if not directory.exists():
        return None
    for artifact in directory.glob(artifact_pattern):
        match = re.fullmatch(artifact_name_pattern, artifact.name)
        if match is None:
            continue
        marker = Path(f"{artifact}.complete.json")
        if not marker.exists():
            continue
        try:
            marker_value = _read_json(marker)
        except (json.JSONDecodeError, UnicodeError):
            continue
        reference = artifact.relative_to(root).as_posix()
        binding = {
            "reference": reference,
            "complete_reference": f"{reference}.complete.json",
            "sha256": marker_value.get("artifact_sha256"),
        }
        _validate_committed_artifact(root, binding, schema=schema)
        candidates.append((int(match.group(1)), binding))
    return max(candidates, key=lambda row: row[0])[1] if candidates else None
