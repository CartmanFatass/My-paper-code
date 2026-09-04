"""Result-blind preactivity identity collection for TBVUUS r03.

Native compilation/loading is intentionally outside this module.  The caller
supplies an already observed native identity; this module authenticates that it
is full-host C++, has no Python production fallback, and seals only source,
configuration, schema, and unbound-coordinate facts.
"""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import re
from typing import Mapping

from .contracts import (
    PREACTIVITY_SCHEMA,
    SOURCE_MANIFEST_SCHEMA,
    SERIALIZER_ID,
    ContractError,
    canonical_json_bytes,
    coordinate_proposal,
    document_sha256,
    frozen_identity,
    prospective_schema_contract,
    validate_coordinate_proposal,
)


_SHA256 = re.compile(r"[0-9a-f]{64}")
_FORBIDDEN_KEYS = frozenset(
    {
        "coordinate",
        "coordinates",
        "coordinate_rows",
        "random_word",
        "random_words",
        "action_word",
        "action_words",
        "trajectory",
        "trajectories",
        "controller_tick",
        "controller_ticks",
        "result",
        "results",
        "endpoint_values",
    }
)


class PreactivityError(ContractError):
    pass


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise PreactivityError(f"{label} must be lowercase SHA-256")
    return value


def _validate_unmaterialized_tree(value: object, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise PreactivityError(f"{path} contains a non-string key")
            normalized = key.lower().replace("-", "_")
            if normalized in _FORBIDDEN_KEYS:
                raise PreactivityError(f"{path}.{key} contains production material")
            _validate_unmaterialized_tree(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_unmaterialized_tree(item, path=f"{path}[{index}]")
    else:
        # Canonical serialization also rejects non-finite/unsupported leaves.
        canonical_json_bytes(value)


def canonical_source_identity(paths: Mapping[str, str | Path]) -> dict[str, object]:
    """Hash a named source set; relative labels cannot escape their scope."""

    if not paths:
        raise PreactivityError("source identity requires at least one source")
    files: dict[str, object] = {}
    for label, source in sorted(paths.items()):
        if not isinstance(label, str) or not label:
            raise PreactivityError("source labels must be nonempty strings")
        logical = PurePosixPath(label.replace("\\", "/"))
        if logical.is_absolute() or "." in logical.parts or ".." in logical.parts:
            raise PreactivityError(f"source label escapes its scope: {label!r}")
        resolved = Path(source).resolve(strict=True)
        payload = resolved.read_bytes()
        files[logical.as_posix()] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    body = {"files": files, "ordering": "logical path byte order"}
    return {**body, "source_set_sha256": document_sha256(body)}


def validate_source_identity(value: Mapping[str, object]) -> dict[str, object]:
    if set(value) != {"files", "ordering", "source_set_sha256"}:
        raise PreactivityError("source identity schema differs")
    if value["ordering"] != "logical path byte order":
        raise PreactivityError("source identity ordering differs")
    files = value["files"]
    if not isinstance(files, Mapping) or not files:
        raise PreactivityError("source identity has no files")
    for label, item in files.items():
        logical = PurePosixPath(str(label))
        if logical.is_absolute() or "." in logical.parts or ".." in logical.parts:
            raise PreactivityError("source identity contains an escaping logical path")
        if not isinstance(item, Mapping) or set(item) != {"bytes", "sha256"}:
            raise PreactivityError("source file identity schema differs")
        if isinstance(item["bytes"], bool) or not isinstance(item["bytes"], int) or item["bytes"] < 0:
            raise PreactivityError("source byte count is invalid")
        _require_sha256(item["sha256"], "source file")
    body = {"files": dict(files), "ordering": value["ordering"]}
    if value["source_set_sha256"] != document_sha256(body):
        raise PreactivityError("source-set digest differs")
    return dict(value)


def canonical_schema_identity() -> dict[str, object]:
    body = {
        "serializer": SERIALIZER_ID,
        "prospective": prospective_schema_contract(),
    }
    return {**body, "schema_sha256": document_sha256(body)}


def canonical_native_identity(
    *,
    toolchain_identity: Mapping[str, object],
    artifact_identity: Mapping[str, object],
) -> dict[str, object]:
    """Normalize the sibling native adapter's observations into this contract."""

    flags = toolchain_identity.get("compile_flags")
    if not isinstance(flags, list) or "/fp:strict" not in flags:
        raise PreactivityError("native toolchain is not frozen to /fp:strict")
    abi = artifact_identity.get("abi")
    if not isinstance(abi, Mapping) or not abi:
        raise PreactivityError("native artifact ABI identity is absent")
    value = {
        "backend": "cpp",
        "python_fallback": False,
        "full_reset_step_cpp": True,
        "abi_version": str(abi.get("abi_version", "")),
        "source_sha256": artifact_identity.get("source_sha256"),
        "artifact_sha256": artifact_identity.get("sha256"),
        "toolchain": dict(toolchain_identity),
    }
    return validate_native_identity(value)


def validate_native_identity(value: Mapping[str, object]) -> dict[str, object]:
    """Admit only an exact-stage full-reset/full-step C++ artifact identity."""

    required = {
        "backend",
        "python_fallback",
        "full_reset_step_cpp",
        "abi_version",
        "source_sha256",
        "artifact_sha256",
        "toolchain",
    }
    if set(value) != required:
        raise PreactivityError("native identity schema differs")
    if (
        value["backend"] != "cpp"
        or value["python_fallback"] is not False
        or value["full_reset_step_cpp"] is not True
    ):
        raise PreactivityError("native identity is not full-host C++ without fallback")
    _require_sha256(value["source_sha256"], "native source")
    _require_sha256(value["artifact_sha256"], "native artifact")
    if not isinstance(value["abi_version"], str) or not value["abi_version"]:
        raise PreactivityError("native ABI version is absent")
    if not isinstance(value["toolchain"], Mapping) or not value["toolchain"]:
        raise PreactivityError("native toolchain identity is absent")
    canonical_json_bytes(dict(value))
    return dict(value)


def collect_preactivity_identity(
    *,
    source_paths: Mapping[str, str | Path],
    config_facts: Mapping[str, object],
    native_identity: Mapping[str, object],
) -> dict[str, object]:
    """Seal construction facts while proving that no activity object is present."""

    if not config_facts:
        raise PreactivityError("config facts must be nonempty")
    _validate_unmaterialized_tree(config_facts, path="config_facts")
    proposal = coordinate_proposal()
    validate_coordinate_proposal(proposal)
    identity = {
        "schema": PREACTIVITY_SCHEMA,
        "frozen": frozen_identity(),
        "source": canonical_source_identity(source_paths),
        "config": dict(config_facts),
        "config_sha256": document_sha256(dict(config_facts)),
        "schema_identity": canonical_schema_identity(),
        "native": validate_native_identity(native_identity),
        "coordinate_proposal": proposal,
        "activity_boundary": {
            "preactivity_only": True,
            "coordinate_binding_present": False,
            "coordinate_rows_present": False,
            "production_words_materialized": False,
            "action_word_domain_present": False,
            "controller_ticks_executed": False,
            "scientific_results_present": False,
        },
    }
    return {"identity": identity, "identity_sha256": document_sha256(identity)}


def validate_preactivity_identity(value: Mapping[str, object]) -> dict[str, object]:
    if set(value) != {"identity", "identity_sha256"}:
        raise PreactivityError("preactivity envelope schema differs")
    identity = value["identity"]
    if not isinstance(identity, Mapping):
        raise PreactivityError("preactivity identity must be an object")
    if value["identity_sha256"] != document_sha256(dict(identity)):
        raise PreactivityError("preactivity identity digest differs")
    if identity.get("schema") != PREACTIVITY_SCHEMA:
        raise PreactivityError("preactivity schema identity differs")
    if identity.get("frozen") != frozen_identity():
        raise PreactivityError("frozen science/stage identity differs")
    source = identity.get("source")
    if not isinstance(source, Mapping):
        raise PreactivityError("source identity is absent")
    validate_source_identity(source)
    config = identity.get("config")
    if not isinstance(config, Mapping) or not config:
        raise PreactivityError("config identity is absent")
    _validate_unmaterialized_tree(config, path="config")
    if identity.get("config_sha256") != document_sha256(dict(config)):
        raise PreactivityError("config digest differs")
    if identity.get("schema_identity") != canonical_schema_identity():
        raise PreactivityError("prospective schema identity differs")
    validate_coordinate_proposal(identity.get("coordinate_proposal", {}))  # type: ignore[arg-type]
    native = identity.get("native")
    if not isinstance(native, Mapping):
        raise PreactivityError("native identity is absent")
    validate_native_identity(native)
    activity = identity.get("activity_boundary")
    expected_activity = {
        "preactivity_only": True,
        "coordinate_binding_present": False,
        "coordinate_rows_present": False,
        "production_words_materialized": False,
        "action_word_domain_present": False,
        "controller_ticks_executed": False,
        "scientific_results_present": False,
    }
    if activity != expected_activity:
        raise PreactivityError("preactivity boundary differs")
    return dict(value)


def build_source_manifest(
    package_root: Path, logical_paths: tuple[str, ...]
) -> dict[str, object]:
    """Build a non-self-referential manifest for a stable candidate source set."""

    root = Path(package_root).resolve(strict=True)
    if not logical_paths or len(set(logical_paths)) != len(logical_paths):
        raise PreactivityError("source-manifest paths must be unique and nonempty")
    files: dict[str, object] = {}
    for logical_name in sorted(logical_paths):
        logical = PurePosixPath(logical_name.replace("\\", "/"))
        if logical.is_absolute() or "." in logical.parts or ".." in logical.parts:
            raise PreactivityError("source-manifest path escapes its package")
        path = (root / Path(*logical.parts)).resolve(strict=True)
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise PreactivityError("source-manifest path escapes its package") from exc
        payload = path.read_bytes()
        if path.suffix.lower() in {".cpp", ".hpp", ".json", ".md", ".py"}:
            payload = payload.replace(b"\r\n", b"\n")
        files[logical.as_posix()] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    body = {
        "schema": SOURCE_MANIFEST_SCHEMA,
        "ordering": "logical path byte order",
        "files": files,
    }
    return {**body, "source_set_sha256": document_sha256(body)}


def validate_live_source_manifest(
    manifest: Mapping[str, object], package_root: Path
) -> dict[str, object]:
    if set(manifest) != {"schema", "ordering", "files", "source_set_sha256"}:
        raise PreactivityError("source manifest schema differs")
    if manifest["schema"] != SOURCE_MANIFEST_SCHEMA:
        raise PreactivityError("source manifest revision differs")
    files = manifest["files"]
    if not isinstance(files, Mapping) or not files:
        raise PreactivityError("source manifest contains no files")
    rebuilt = build_source_manifest(Path(package_root), tuple(str(name) for name in files))
    if dict(manifest) != rebuilt:
        raise PreactivityError("live candidate source differs from FINAL manifest")
    return rebuilt
