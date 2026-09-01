"""Create-only complete-result and incident publication for OMRC B0."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
from typing import Any, Mapping, Sequence
import uuid


RESULT_SCHEMA = "cbsc_omrc_b01_b_explore_result_v1"
INCIDENT_SCHEMA = "cbsc_omrc_b01_b_explore_incident_v1"
B0_RUN_NAME = "CBSC-OMRC-B0-INSTRUMENT"
OBJECT_ID = "CBSC-OMRC-B01"
CLARIFICATION_ID = "cbsc-online-b-innovator-20260901-02"
PINNED_EVIDENCE_REF = "f198cedf8b0bb2c06b6e79ed3415e08b6e197477"
NO_SCIENCE_CLAIM = "B0_INSTRUMENTATION_ONLY_NO_SCIENTIFIC_BRANCH"


class ArtifactError(ValueError):
    """An artifact is incomplete, noncanonical, or violates create-only publication."""


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise ArtifactError("artifact contains nonfinite or noncanonical JSON") from exc


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _write_fsync(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def directory_size(root: Path) -> int:
    total = 0
    if not root.exists():
        return 0
    for path in root.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            continue
    return total


def ensure_confined(path: Path, allowed_root: Path) -> Path:
    resolved = path.resolve(strict=False)
    root = allowed_root.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ArtifactError(f"path is outside the confined direction root: {resolved}") from exc
    return resolved


def create_staging_directory(final_path: Path, *, allowed_root: Path) -> Path:
    final = ensure_confined(final_path, allowed_root)
    if final.exists():
        raise FileExistsError(f"create-only final artifact already exists: {final}")
    final.parent.mkdir(parents=True, exist_ok=True)
    staging = final.parent / f".{final.name}.partial-{uuid.uuid4().hex}"
    staging.mkdir(mode=0o700)
    return staging


def _all_finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_all_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_all_finite(item) for item in value)
    return True


def validate_b0_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    manifest = dict(value)
    required = {
        "schema",
        "object_id",
        "clarification_id",
        "run_name",
        "implementation_commit",
        "source_conformance",
        "pinned_evidence_ref",
        "configuration_sha256",
        "arms",
        "seeds",
        "checkpoint_identities",
        "counts",
        "arm_records",
        "parity_audits",
        "resource_caps",
        "resource_admissions",
        "telemetry",
        "numerical_finiteness_audit",
        "incident_references",
        "scientific_branch",
        "claim_ceiling",
        "performance_disposition",
    }
    missing = required - set(manifest)
    if missing:
        raise ArtifactError(f"B0 manifest fields are missing: {sorted(missing)}")
    if (
        manifest["schema"] != RESULT_SCHEMA
        or manifest["object_id"] != OBJECT_ID
        or manifest["clarification_id"] != CLARIFICATION_ID
        or manifest["run_name"] != B0_RUN_NAME
    ):
        raise ArtifactError("B0 artifact identity differs")
    if manifest["seeds"] != [21001]:
        raise ArtifactError("B0 seed identity differs")
    if manifest["scientific_branch"] is not None:
        raise ArtifactError("B0 must not contain a scientific branch")
    if manifest["claim_ceiling"] != NO_SCIENCE_CLAIM:
        raise ArtifactError("B0 claim ceiling differs")
    if manifest["performance_disposition"] != "PILOT_ONLY":
        raise ArtifactError("B0 remains PILOT_ONLY until real telemetry is accepted by CM")
    if manifest["numerical_finiteness_audit"] is not True or not _all_finite(manifest):
        raise ArtifactError("B0 artifact contains nonfinite or unaudited numerical data")
    if not isinstance(manifest["incident_references"], list):
        raise ArtifactError("incident_references must be a list")
    canonical_json_bytes(manifest)
    return manifest


def publish_complete(
    staging: Path,
    final_path: Path,
    manifest: Mapping[str, Any],
    *,
    allowed_root: Path,
) -> Path:
    """Validate, fsync, then atomically claim the absent final directory."""

    staging = ensure_confined(staging, allowed_root)
    final = ensure_confined(final_path, allowed_root)
    if staging.parent != final.parent or not staging.is_dir():
        raise ArtifactError("staging must be an existing sibling of the final path")
    if final.exists():
        raise FileExistsError(f"create-only final artifact already exists: {final}")
    validated = validate_b0_manifest(manifest)
    manifest_path = staging / "manifest.json"
    if manifest_path.exists():
        raise ArtifactError("staging manifest already exists")
    _write_fsync(manifest_path, canonical_json_bytes(validated) + b"\n")
    for path in staging.rglob("*"):
        if path.is_file() and path != manifest_path:
            # Windows' CRT rejects fsync on a read-only descriptor.  Opening
            # without truncation as r+b preserves bytes while making the
            # durability barrier portable.
            with path.open("r+b") as stream:
                os.fsync(stream.fileno())
    _fsync_directory(staging)
    if final.exists():
        raise FileExistsError(f"create-only final artifact appeared: {final}")
    os.rename(staging, final)
    _fsync_directory(final.parent)
    return final


def publish_incident(
    *,
    incident_root: Path,
    allowed_root: Path,
    attempt_id: str,
    run_name: str,
    category: str,
    detail: str,
    completed_arms: Sequence[str],
) -> Path:
    """Publish one create-only engineering incident with no science surface."""

    root = ensure_confined(incident_root, allowed_root)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{attempt_id}-{uuid.uuid4().hex}.json"
    payload = {
        "schema": INCIDENT_SCHEMA,
        "object_id": OBJECT_ID,
        "run_name": run_name,
        "attempt_id": attempt_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "detail": detail,
        "completed_arms": list(completed_arms),
        "scientific_branch": None,
        "scientific_object_consumed": False,
        "claim_ceiling": "ENGINEERING_INCIDENT_ONLY",
    }
    _write_fsync(destination, canonical_json_bytes(payload) + b"\n")
    _fsync_directory(root)
    return destination


def publish_incident_bundle(
    *,
    staging: Path,
    incident_root: Path,
    allowed_root: Path,
    attempt_id: str,
    run_name: str,
    category: str,
    detail: str,
    completed_arms: Sequence[str],
) -> Path:
    """Atomically preserve a failed private attempt and every produced byte."""

    source = ensure_confined(staging, allowed_root)
    root = ensure_confined(incident_root, allowed_root)
    if ".partial-" not in source.name or not source.is_dir():
        raise ArtifactError("incident source must be an existing private partial directory")
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{attempt_id}-{uuid.uuid4().hex}"
    if destination.exists():
        raise FileExistsError(f"create-only incident bundle already exists: {destination}")
    payload = {
        "schema": INCIDENT_SCHEMA,
        "object_id": OBJECT_ID,
        "run_name": run_name,
        "attempt_id": attempt_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "detail": detail,
        "completed_arms": list(completed_arms),
        "preserved_evidence_relative_root": ".",
        "scientific_branch": None,
        "scientific_object_consumed": False,
        "claim_ceiling": "ENGINEERING_INCIDENT_ONLY",
    }
    _write_fsync(source / "incident.json", canonical_json_bytes(payload) + b"\n")
    _fsync_directory(source)
    os.rename(source, destination)
    _fsync_directory(root)
    return destination


def discard_staging(staging: Path, *, allowed_root: Path) -> None:
    """Remove only a verified private partial tree after incident publication."""

    path = ensure_confined(staging, allowed_root)
    if ".partial-" not in path.name:
        raise ArtifactError("refusing to discard a non-partial directory")
    if path.exists():
        shutil.rmtree(path)


__all__ = [
    "ArtifactError",
    "B0_RUN_NAME",
    "CLARIFICATION_ID",
    "INCIDENT_SCHEMA",
    "NO_SCIENCE_CLAIM",
    "OBJECT_ID",
    "PINNED_EVIDENCE_REF",
    "RESULT_SCHEMA",
    "canonical_json_bytes",
    "create_staging_directory",
    "directory_size",
    "discard_staging",
    "ensure_confined",
    "publish_complete",
    "publish_incident",
    "publish_incident_bundle",
    "sha256_json",
    "validate_b0_manifest",
]
