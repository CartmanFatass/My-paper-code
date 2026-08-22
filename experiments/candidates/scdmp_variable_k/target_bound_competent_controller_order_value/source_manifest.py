"""Builder/validator for the complete frozen TBCC production source inventory."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Final

import numpy
import torch

from .config import COMPONENT, HOST, NATIVE_ABI_VERSION
from .empirical_contract import (
    CARD_REVISION,
    CARD_SHA256,
    NATIVE_REWARD_TRACE_CONTRACT,
    canonical_json_bytes,
)


MANIFEST_SCHEMA: Final[str] = "SCDMP_TBCC_R02_EMPIRICAL_SOURCE_MANIFEST_V1"
MANIFEST_NAME: Final[str] = "empirical_source_manifest.json"
SHARED_SOURCE_PATH: Final[str] = "envs/native/production_backend.py"
CARD_PATH: Final[str] = (
    "docs/research/candidates/semigroup_consistent_duration_model_policy/"
    "SCDMP_TARGET_BOUND_COMPETENT_CONTROLLER_ORDER_VALUE_SCIENCE_CARD_REVISION_02_20260821.md"
)
PACKAGE_PREFIX: Final[str] = (
    "experiments/candidates/scdmp_variable_k/"
    "target_bound_competent_controller_order_value"
)
ACCEPTED_SHARED_SOURCE_SHA256: Final[str] = (
    "c79a26e4a71678dcde16993a33a01cff735d90116d8ea70b6577232be39939ce"
)
ACCEPTED_NATIVE_SOURCE_SHA256: Final[str] = (
    "ea2149b187ba65c9229f0ada9c3bd55bd0f424ec5a5830de1f454585b488de38"
)
ACCEPTED_NATIVE_BUILD_KEY: Final[str] = (
    "9a9801e94e1b02468df1e3d59e0c0055b85e2d02306c018bb275b69e0f718fe3"
)
ACCEPTED_NATIVE_ARTIFACT_SHA256: Final[str] = (
    "df1097603c3fd2e1f66875e5d3209fcc509609f870569a205efc83c607a7bb9d"
)
ACCEPTED_NATIVE_ARTIFACT_SIZE: Final[int] = 177_664
ACCEPTED_ABI_SIZES: Final[dict[str, int]] = {
    "reset_input": 64,
    "renewal_input": 320,
    "host_output": 336,
    "setup_fixture_input": 24,
    "setup_fixture_output": 24,
    "primitive_fixture_input": 160,
}
_NON_PRODUCTION_FILES = frozenset(("oracle.py", "benchmark.py", "synthetic_resume.py"))


class SourceManifestError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_native_binding(value: Mapping[str, object]) -> dict[str, object]:
    """Drop runtime timing while retaining every source/build/ABI binding."""

    fields = (
        "schema", "component", "host", "artifact_path", "artifact_sha256",
        "artifact_size", "source_path", "source_sha256", "build_key", "toolchain",
        "runtime_abi", "abi_version", "fixture_magic", "max_batch_width",
        "functional_batch_widths", "full_reset_step_cpp", "python_environment_state",
        "python_plant_transition", "python_fallback",
    )
    return {field: value[field] for field in fields if field in value}


def discover_production_source_paths(repository_root: Path) -> tuple[str, ...]:
    """Discover the complete production inventory after all runner files freeze."""

    root = Path(repository_root).resolve()
    package = root / PACKAGE_PREFIX
    if not package.is_dir():
        raise SourceManifestError("TBCC candidate package is absent")
    rows: list[str] = []
    for path in package.rglob("*"):
        if (
            path.is_file()
            and "__pycache__" not in path.parts
            and path.name not in _NON_PRODUCTION_FILES
            and path.name != MANIFEST_NAME
            and path.suffix in (".py", ".cpp", ".hpp")
        ):
            rows.append(path.relative_to(root).as_posix())
    rows.extend((SHARED_SOURCE_PATH, CARD_PATH))
    return tuple(sorted(set(rows)))


def _validate_inventory(root: Path, inventory: Iterable[str]) -> tuple[str, ...]:
    paths = tuple(inventory)
    if not paths or paths != tuple(sorted(set(paths))):
        raise SourceManifestError("source inventory must be a nonempty sorted unique tuple")
    for relative in paths:
        if not isinstance(relative, str) or Path(relative).is_absolute() or "\\" in relative:
            raise SourceManifestError("source inventory paths must be relative POSIX paths")
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise SourceManifestError("source inventory path escapes repository root") from error
        if not candidate.is_file():
            raise SourceManifestError(f"source inventory file is absent: {relative}")
    expected = discover_production_source_paths(root)
    if paths != expected:
        raise SourceManifestError("source inventory is not the complete current production inventory")
    return paths


def build_source_manifest(
    repository_root: Path,
    *,
    source_paths: Iterable[str] | None = None,
    native_identity: Mapping[str, object],
) -> dict[str, object]:
    """Build manifest data in memory; callers decide if/when final bytes persist."""

    root = Path(repository_root).resolve()
    inventory = _validate_inventory(
        root,
        discover_production_source_paths(root) if source_paths is None else source_paths,
    )
    card = root / CARD_PATH
    shared = root / SHARED_SOURCE_PATH
    if _sha(card) != CARD_SHA256:
        raise SourceManifestError("immutable science-card SHA-256 differs")
    if _sha(shared) != ACCEPTED_SHARED_SOURCE_SHA256:
        raise SourceManifestError("accepted shared production source SHA-256 differs")
    native = stable_native_binding(native_identity)
    required_native = {
        "component": COMPONENT,
        "host": HOST,
        "abi_version": NATIVE_ABI_VERSION,
        "source_sha256": ACCEPTED_NATIVE_SOURCE_SHA256,
        "build_key": ACCEPTED_NATIVE_BUILD_KEY,
        "artifact_sha256": ACCEPTED_NATIVE_ARTIFACT_SHA256,
        "artifact_size": ACCEPTED_NATIVE_ARTIFACT_SIZE,
        "full_reset_step_cpp": True,
        "python_fallback": False,
    }
    for key, expected in required_native.items():
        if native.get(key) != expected:
            raise SourceManifestError(f"native binding field {key!r} differs")
    if _sha(root / PACKAGE_PREFIX / "native/tbcc_backend.cpp") != ACCEPTED_NATIVE_SOURCE_SHA256:
        raise SourceManifestError("accepted native C++ source SHA-256 differs")
    runtime_abi = native.get("runtime_abi")
    if not isinstance(runtime_abi, Mapping) or runtime_abi.get("struct_sizes") != ACCEPTED_ABI_SIZES:
        raise SourceManifestError("accepted native ABI struct-size binding differs")
    dependencies = []
    for name, module in (("numpy", numpy), ("torch", torch)):
        module_path = Path(str(module.__file__)).resolve()
        dependencies.append(
            {
                "name": name,
                "version": str(module.__version__),
                "module_path": str(module_path),
                "module_sha256": _sha(module_path),
            }
        )
    return {
        "schema": MANIFEST_SCHEMA,
        "status": "FINAL",
        "card_revision": CARD_REVISION,
        "files": [{"path": relative, "sha256": _sha(root / relative)} for relative in inventory],
        "dependencies": dependencies,
        "immutable": {
            "card_path": CARD_PATH,
            "card_sha256": CARD_SHA256,
            "shared_source_path": SHARED_SOURCE_PATH,
            "shared_source_sha256": ACCEPTED_SHARED_SOURCE_SHA256,
        },
        "native": native,
        "native_reward_trace": dict(NATIVE_REWARD_TRACE_CONTRACT),
        "runtime": {
            "python_executable": "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
            "python_version": platform.python_version(),
            "byteorder": sys.byteorder,
            "cpu_only": True,
        },
        "schemas": [
            "SCDMP_TBCC_R02_COORDINATE_PROPOSAL_V1",
            "SCDMP_TBCC_R02_ROOT_EMPIRICAL_LEASE_V1",
            "SCDMP_TBCC_R02_PREACTIVITY_ACCEPTANCE_V1",
        ],
    }


def manifest_bytes(value: Mapping[str, object]) -> bytes:
    return canonical_json_bytes(dict(value)) + b"\n"


def manifest_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(manifest_bytes(value)).hexdigest()


def validate_source_manifest(
    value: Mapping[str, object],
    repository_root: Path,
    *,
    native_identity: Mapping[str, object],
) -> dict[str, object]:
    root = Path(repository_root).resolve()
    rows = value.get("files") if isinstance(value, Mapping) else None
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise SourceManifestError("source manifest file inventory is malformed")
    paths = tuple(str(row.get("path")) for row in rows)
    rebuilt = build_source_manifest(root, source_paths=paths, native_identity=native_identity)
    if dict(value) != rebuilt:
        raise SourceManifestError("source/dependency/native/shared manifest binding changed")
    return rebuilt


def load_and_validate_source_manifest(
    path: Path, repository_root: Path, *, native_identity: Mapping[str, object]
) -> dict[str, object]:
    target = Path(path)
    try:
        raw = target.read_bytes()
        value = json.loads(raw.decode("ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SourceManifestError("source manifest cannot be read as canonical JSON") from error
    if not isinstance(value, dict) or raw != manifest_bytes(value):
        raise SourceManifestError("source manifest bytes are not canonical")
    return validate_source_manifest(value, repository_root, native_identity=native_identity)
