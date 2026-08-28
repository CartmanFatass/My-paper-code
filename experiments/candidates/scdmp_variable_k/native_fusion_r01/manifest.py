"""Current-byte S0 source manifest with read-only predecessor provenance."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Final, Mapping

from .contract import REVISION, S0_SLICE


MANIFEST_SCHEMA: Final[str] = "SCDMP_NATIVE_FUSION_R01_S0_SOURCE_MANIFEST_V1"
PACKAGE_PATH: Final[str] = "experiments/candidates/scdmp_variable_k/native_fusion_r01"
TEST_PATH: Final[str] = (
    "tests/experiments/candidates/scdmp_variable_k/test_native_fusion_r01_s0.py"
)
AUTHORITY_PATH: Final[str] = (
    "docs/research/candidates/semigroup_consistent_duration_model_policy/"
    "SCDMP_NATIVE_FUSION_SCIENCE_AUTHORITY_R01_20260827.md"
)
AUTHORITY_SHA256: Final[str] = (
    "c8091b15293f2cdeae4fc00a42bdfc1a0ae165d930fc152bca86610979e0c47c"
)
READ_ONLY_MANIFEST_PATH: Final[str] = (
    "experiments/candidates/scdmp_variable_k/uav_suspended_payload_order_value/"
    "empirical_source_manifest.json"
)
_FORBIDDEN_IMPORT: Final[str] = (
    "experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value"
)


class SourceManifestError(ValueError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def source_manifest_path(repository_root: Path) -> Path:
    return Path(repository_root) / PACKAGE_PATH / "source_manifest.json"


def discover_source_paths(repository_root: Path) -> tuple[str, ...]:
    root = Path(repository_root).resolve()
    package = root / PACKAGE_PATH
    if not package.is_dir():
        raise SourceManifestError("S0 source package is absent")
    rows = [
        path.relative_to(root).as_posix()
        for path in package.rglob("*.py")
        if "__pycache__" not in path.parts
    ]
    rows.append(TEST_PATH)
    paths = tuple(sorted(set(rows)))
    if not paths or any(not (root / path).is_file() for path in paths):
        raise SourceManifestError("S0 source inventory is incomplete")
    return paths


def _validate_import_isolation(root: Path, paths: tuple[str, ...]) -> None:
    for relative in paths:
        if not relative.startswith(PACKAGE_PATH + "/"):
            continue
        tree = ast.parse((root / relative).read_text(encoding="utf-8"), filename=relative)
        for node in ast.walk(tree):
            names: tuple[str, ...] = ()
            if isinstance(node, ast.Import):
                names = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = (node.module,)
            if any(name.startswith(_FORBIDDEN_IMPORT) for name in names):
                raise SourceManifestError("S0 source imports the read-only predecessor")


def build_source_manifest(repository_root: Path) -> dict[str, object]:
    root = Path(repository_root).resolve()
    paths = discover_source_paths(root)
    _validate_import_isolation(root, paths)
    authority = root / AUTHORITY_PATH
    predecessor = root / READ_ONLY_MANIFEST_PATH
    if _sha(authority) != AUTHORITY_SHA256:
        raise SourceManifestError("CLOSED R01 authority bytes changed")
    if not predecessor.is_file():
        raise SourceManifestError("read-only predecessor manifest is absent")
    return {
        "schema": MANIFEST_SCHEMA,
        "status": "S0_TECHNICALLY_ACCEPTED",
        "revision": REVISION,
        "slice": S0_SLICE,
        "files": [{"path": path, "sha256": _sha(root / path)} for path in paths],
        "authority_ref": {"path": AUTHORITY_PATH, "sha256": AUTHORITY_SHA256},
        "read_only_conformance_input": {
            "path": READ_ONLY_MANIFEST_PATH,
            "sha256": _sha(predecessor),
            "imported": False,
            "mutated": False,
        },
        "effect_refs": [],
        "activity_authorized": False,
    }


def manifest_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def emit_source_manifest(repository_root: Path) -> Path:
    """Atomically create the canonical current-byte manifest exactly once."""

    target = source_manifest_path(repository_root)
    if target.exists():
        raise FileExistsError(target)
    payload = canonical_json_bytes(build_source_manifest(repository_root))
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def load_and_validate_source_manifest(path: Path, repository_root: Path) -> dict[str, object]:
    raw = Path(path).read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SourceManifestError("source manifest is not canonical ASCII JSON") from error
    if not isinstance(value, dict) or raw != canonical_json_bytes(value):
        raise SourceManifestError("source manifest bytes are not canonical")
    expected = build_source_manifest(repository_root)
    if value != expected:
        raise SourceManifestError("source manifest does not bind current S0 bytes")
    return value
