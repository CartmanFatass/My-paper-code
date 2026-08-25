"""Write-once construction-manifest lifecycle for Headland-90.

The seal binds source/config/schema/conformance facts only.  It cannot carry
production random words, materialized cells, trajectories, empirical values,
or a scientific-activity transition.  A future empirical runner remains a
separate, unauthorized object and must pass the native C++ production guard.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
from .config import CARD_REVISION, HOST_ID


DIRECTION_ID = "opportunity_normalized_lease_gated_rebinding"
STAGE = "ONLGR-HEADLAND90-UAV-HOST-CONSTRUCTION-AND-CONFORMANCE"
HOST = HOST_ID
SCHEMA_VERSION = "ONLGR-HEADLAND90-CONSTRUCTION-MANIFEST-v1"
FUTURE_PRODUCTION_GUARD = "envs.native.production_backend.require_cpp_batched_production"

_SHA256 = re.compile(r"[0-9a-f]{64}")
_MANIFEST_NAME = re.compile(r"construction-manifest-([0-9a-f]{64})\.json")
_FORBIDDEN_MATERIAL_KEYS = frozenset(
    {
        "production_namespace_words",
        "production_namespace_word",
        "production_random_words",
        "production_random_word",
        "random_words",
        "random_word",
        "prng_words",
        "prng_word",
        "counter_words",
        "counter_word",
        "draws",
        "uniform_values",
        "normal_values",
        "coordinates",
        "coordinate",
        "coordinate_rows",
        "cells",
        "calibration_cells",
        "calibration_cell",
        "held_out_cells",
        "held_out_cell",
        "hold_cells",
        "trajectories",
        "controller_ticks",
        "controller_tick",
        "result",
        "empirical_result",
        "empirical_results",
        "empirical_values",
        "endpoint_values",
        "scientific_activity",
        "scientific_activity_started",
        "activity_started",
        "production_activity",
    }
)
_FORBIDDEN_VALUE_MARKERS = (
    "production random word",
    "production namespace word",
    "scientific activity started",
    "empirical result",
    "calibration cell payload",
    "held out cell payload",
)


class ConstructionManifestError(ValueError):
    """The requested or retained object is outside the construction boundary."""


@dataclass(frozen=True)
class ConstructionSeal:
    artifact_root: Path
    manifest_path: Path
    sha256: str
    manifest_bytes: bytes


def canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ConstructionManifestError("construction facts must be finite JSON values") from exc


def _validate_json_tree(value: object, *, path: str = "facts") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str):
            normalized = " ".join(value.lower().replace("_", " ").replace("-", " ").split())
            if any(marker in normalized for marker in _FORBIDDEN_VALUE_MARKERS):
                raise ConstructionManifestError(f"{path} contains forbidden activity/materialized data")
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ConstructionManifestError(f"{path} contains a non-finite float")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_tree(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ConstructionManifestError(f"{path} contains a non-string JSON key")
            normalized_key = key.lower().replace("-", "_")
            if normalized_key in _FORBIDDEN_MATERIAL_KEYS:
                raise ConstructionManifestError(
                    f"{path}.{key} is forbidden in a construction-only manifest"
                )
            # Schema declarations are permitted; materialized result-like payloads are not.
            if normalized_key == "results" or (
                normalized_key.endswith("_results") and not normalized_key.endswith("_result_schema")
            ):
                raise ConstructionManifestError(
                    f"{path}.{key} cannot seal empirical results"
                )
            _validate_json_tree(item, path=f"{path}.{key}")
        return
    raise ConstructionManifestError(f"{path} contains unsupported type {type(value).__name__}")


def _clean_mapping(value: Mapping[str, object], label: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ConstructionManifestError(f"{label} must be a mapping")
    if not value:
        raise ConstructionManifestError(f"{label} must contain at least one sealed fact")
    copied = json.loads(canonical_json_bytes(dict(value)))
    _validate_json_tree(copied, path=label)
    return copied


def _validate_source_hashes(source_hashes: Mapping[str, str]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    if not source_hashes:
        raise ConstructionManifestError("at least one source hash is required")
    for source, digest in source_hashes.items():
        if not isinstance(source, str) or not source:
            raise ConstructionManifestError("source-hash keys must be nonempty relative paths")
        posix = PurePosixPath(source.replace("\\", "/"))
        if posix.is_absolute() or ".." in posix.parts or "." in posix.parts:
            raise ConstructionManifestError(f"source path escapes the sealed source scope: {source!r}")
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise ConstructionManifestError(f"source hash is not lowercase SHA-256: {source!r}")
        cleaned[posix.as_posix()] = digest
    return dict(sorted(cleaned.items()))


def build_construction_manifest(
    *,
    source_hashes: Mapping[str, str],
    config_facts: Mapping[str, object],
    schema_facts: Mapping[str, object],
    conformance_facts: Mapping[str, object],
) -> dict[str, object]:
    """Build a deterministic manifest with no time, run, coordinate, or result identity."""

    return {
        "artifact_kind": "ONLGR_HEADLAND90_CONSTRUCTION_MANIFEST",
        "schema_version": SCHEMA_VERSION,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "card_revision": CARD_REVISION,
        "host": HOST,
        "sealed_scope": ["source", "config", "schema", "conformance"],
        "source_hashes": _validate_source_hashes(source_hashes),
        "config_facts": _clean_mapping(config_facts, "config_facts"),
        "schema_facts": _clean_mapping(schema_facts, "schema_facts"),
        "conformance_facts": _clean_mapping(conformance_facts, "conformance_facts"),
        "activity_boundary": {
            "construction_only": True,
            "question_relevant_activity_authorized": False,
            "production_random_words_materialized": False,
            "production_controller_ticks_executed": False,
            "calibration_or_held_out_cells_materialized": False,
            "empirical_results_present": False,
        },
        "future_empirical_runner": {
            "present": False,
            "required_preactivity_guard": FUTURE_PRODUCTION_GUARD,
            "guard_invoked_by_this_lifecycle": False,
        },
        "write_once": True,
        "atomic_file_install": True,
    }


def validate_construction_manifest(manifest: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    expected_keys = {
        "artifact_kind",
        "schema_version",
        "direction_id",
        "stage",
        "card_revision",
        "host",
        "sealed_scope",
        "source_hashes",
        "config_facts",
        "schema_facts",
        "conformance_facts",
        "activity_boundary",
        "future_empirical_runner",
        "write_once",
        "atomic_file_install",
    }
    if set(manifest) != expected_keys:
        issues.append("manifest top-level schema differs from the construction-only schema")
        return tuple(issues)
    fixed = {
        "artifact_kind": "ONLGR_HEADLAND90_CONSTRUCTION_MANIFEST",
        "schema_version": SCHEMA_VERSION,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "card_revision": CARD_REVISION,
        "host": HOST,
        "sealed_scope": ["source", "config", "schema", "conformance"],
        "activity_boundary": {
            "construction_only": True,
            "question_relevant_activity_authorized": False,
            "production_random_words_materialized": False,
            "production_controller_ticks_executed": False,
            "calibration_or_held_out_cells_materialized": False,
            "empirical_results_present": False,
        },
        "future_empirical_runner": {
            "present": False,
            "required_preactivity_guard": FUTURE_PRODUCTION_GUARD,
            "guard_invoked_by_this_lifecycle": False,
        },
        "write_once": True,
        "atomic_file_install": True,
    }
    for key, value in fixed.items():
        if manifest.get(key) != value:
            issues.append(f"frozen construction lifecycle field differs: {key}")
    try:
        _validate_source_hashes(manifest["source_hashes"])  # type: ignore[arg-type]
        for key in ("config_facts", "schema_facts", "conformance_facts"):
            _clean_mapping(manifest[key], key)  # type: ignore[arg-type]
    except (ConstructionManifestError, TypeError) as exc:
        issues.append(str(exc))
    return tuple(issues)


def _strict_descendant(path: Path, allowed_root: Path) -> tuple[Path, Path]:
    resolved_root = allowed_root.resolve()
    resolved_path = path.resolve(strict=False)
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ConstructionManifestError("artifact root escapes its authorized parent") from exc
    if not relative.parts:
        raise ConstructionManifestError("artifact root must be a strict child of its authorized parent")
    return resolved_path, resolved_root


def seal_construction_manifest(
    artifact_root: Path,
    *,
    allowed_root: Path,
    source_hashes: Mapping[str, str],
    config_facts: Mapping[str, object],
    schema_facts: Mapping[str, object],
    conformance_facts: Mapping[str, object],
) -> ConstructionSeal:
    """Atomically install one content-addressed manifest into a fresh directory."""

    root, parent = _strict_descendant(Path(artifact_root), Path(allowed_root))
    if root.exists():
        raise FileExistsError(f"refusing to overwrite write-once artifact root: {root}")
    manifest = build_construction_manifest(
        source_hashes=source_hashes,
        config_facts=config_facts,
        schema_facts=schema_facts,
        conformance_facts=conformance_facts,
    )
    issues = validate_construction_manifest(manifest)
    if issues:
        raise ConstructionManifestError("; ".join(issues))
    encoded = canonical_json_bytes(manifest)
    digest = hashlib.sha256(encoded).hexdigest()

    parent.mkdir(parents=True, exist_ok=True)
    try:
        root.mkdir(parents=False, exist_ok=False)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite write-once artifact root: {root}") from exc

    destination = root / f"construction-manifest-{digest}.json"
    temporary = root / ".construction-manifest.tmp"
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        # Flush directory metadata where the platform exposes directory handles.
        if os.name != "nt":
            descriptor = os.open(root, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise
    return ConstructionSeal(root, destination, digest, encoded)


def verify_construction_manifest(
    artifact_root: Path,
    *,
    allowed_root: Path,
    expected_sha256: str | None = None,
) -> dict[str, object]:
    root, _ = _strict_descendant(Path(artifact_root), Path(allowed_root))
    if not root.is_dir():
        raise ConstructionManifestError("construction artifact root is absent")
    files = tuple(sorted(path for path in root.iterdir() if path.is_file()))
    if len(files) != 1:
        raise ConstructionManifestError("construction seal must contain exactly one immutable file")
    match = _MANIFEST_NAME.fullmatch(files[0].name)
    if match is None:
        raise ConstructionManifestError("construction manifest filename is not content-addressed")
    encoded = files[0].read_bytes()
    digest = hashlib.sha256(encoded).hexdigest()
    if digest != match.group(1):
        raise ConstructionManifestError("construction manifest bytes fail filename authentication")
    if expected_sha256 is not None and digest != expected_sha256:
        raise ConstructionManifestError("construction manifest differs from the expected immutable seal")
    try:
        manifest = json.loads(encoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ConstructionManifestError("construction manifest is not valid UTF-8 JSON") from exc
    if canonical_json_bytes(manifest) != encoded:
        raise ConstructionManifestError("construction manifest is not canonical JSON plus LF")
    issues = validate_construction_manifest(manifest)
    if issues:
        raise ConstructionManifestError("; ".join(issues))
    return manifest
