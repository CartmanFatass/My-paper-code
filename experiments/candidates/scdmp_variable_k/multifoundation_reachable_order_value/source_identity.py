"""Create-once direct source/native identity gate for SCDMP B01 invocations."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Final

import torch

from .native_backend import native_abi_identity


SOURCE_IDENTITY_SCHEMA: Final[str] = "SCDMP_MF_RS_MK_B01_SOURCE_IDENTITY_V1"
ASSIGNED_BASE_COMMIT: Final[str] = "dbd85cbe98bc8705cc5dc0ea72eb20480551e167"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
OWNED_PRODUCTION_PATHS: Final[tuple[str, ...]] = tuple(sorted((
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/__init__.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/analysis.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/active_gate.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/artifacts.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/assessment.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/contracts.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/foundation.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/native/mf_rs_native.cpp",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/native_backend.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/native_state.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/orchestration.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/performance_readiness.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/preflight.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/production.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/quarantine.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/resources.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/rng.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/runner.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/selection.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/source_identity.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/technical_checkpoint.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/training.py",
    "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/workload.py",
    "scripts/hmasd_platform.py",
    "scripts/hmasd_resource_preflight.py",
    "scripts/run_scdmp_mf_rs_mk_b01.py",
)))


class SourceIdentityError(RuntimeError):
    pass


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: dict[str, object]) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise SourceIdentityError("source identity is not finite canonical JSON") from error


def _run_git(arguments: list[str]) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *arguments], cwd=_REPOSITORY_ROOT, capture_output=True, check=False,
        )
    except OSError as error:
        raise SourceIdentityError("source identity cannot execute Git") from error
    if completed.returncode != 0:
        raise SourceIdentityError(
            "source identity Git measurement failed: "
            + completed.stderr.decode("utf-8", errors="replace").strip()
        )
    return bytes(completed.stdout)


def _owned_inventory() -> list[dict[str, object]]:
    rows = []
    for relative in OWNED_PRODUCTION_PATHS:
        path = (_REPOSITORY_ROOT / relative).resolve(strict=True)
        try:
            path.relative_to(_REPOSITORY_ROOT.resolve(strict=True))
            direct = path.read_bytes()
        except (OSError, ValueError) as error:
            raise SourceIdentityError(f"owned source path cannot be measured: {relative}") from error
        if not path.is_file():
            raise SourceIdentityError(f"owned source path is not a file: {relative}")
        rows.append({"relative_path": relative, "byte_size": len(direct), "sha256": _sha256(direct)})
    return rows


def compute_source_identity() -> dict[str, object]:
    """Recompute all owned source, Git-diff, runtime, binary, and ABI facts."""

    resolved_base = _run_git(["rev-parse", f"{ASSIGNED_BASE_COMMIT}^{{commit}}"]).decode("ascii").strip()
    if resolved_base != ASSIGNED_BASE_COMMIT:
        raise SourceIdentityError("assigned base commit does not resolve exactly")
    inventory = _owned_inventory()
    inventory_bytes = _canonical_json({"owned_source_inventory": inventory})
    diff_command = ["git", "diff", "--binary", ASSIGNED_BASE_COMMIT, "--", *OWNED_PRODUCTION_PATHS]
    diff_bytes = _run_git(diff_command[1:])
    abi = native_abi_identity()
    build_binding = abi.get("build_binding")
    if not isinstance(build_binding, dict):
        raise SourceIdentityError("native build receipt binding is unavailable")
    library_value = abi.get("compiled_library_resolved_path")
    if not isinstance(library_value, str):
        raise SourceIdentityError("loaded native library path is unavailable")
    try:
        library = Path(library_value).resolve(strict=True)
        library_bytes = library.read_bytes()
    except OSError as error:
        raise SourceIdentityError("loaded native library cannot be measured") from error
    native_source = _REPOSITORY_ROOT / (
        "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/native/"
        "mf_rs_native.cpp"
    )
    native_source_bytes = native_source.read_bytes()
    executable = Path(sys.executable).resolve(strict=True)
    return {
        "schema": SOURCE_IDENTITY_SCHEMA,
        "assigned_base_commit": ASSIGNED_BASE_COMMIT,
        "owned_production_paths": list(OWNED_PRODUCTION_PATHS),
        "owned_source_inventory": inventory,
        "owned_tree_aggregate_sha256": _sha256(inventory_bytes),
        "git_diff_command": diff_command,
        "git_diff_byte_size": len(diff_bytes),
        "git_diff_sha256": _sha256(diff_bytes),
        "python": {
            "resolved_executable": str(executable),
            "version": sys.version,
            "version_info": list(sys.version_info[:5]),
        },
        "torch_version": str(torch.__version__),
        "native_cpp_source": {
            "relative_path": native_source.relative_to(_REPOSITORY_ROOT).as_posix(),
            "byte_size": len(native_source_bytes),
            "sha256": _sha256(native_source_bytes),
        },
        "compiled_native_library": {
            "resolved_path": str(library),
            "byte_size": len(library_bytes),
            "sha256": _sha256(library_bytes),
        },
        "native_build_receipt": build_binding,
        "native_abi_identity": abi,
    }


def compute_source_identity_bytes() -> bytes:
    return _canonical_json(compute_source_identity())


def _atomic_create(path: Path, payload: bytes) -> None:
    if path.exists():
        raise SourceIdentityError("source identity gate is create-only")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    except FileExistsError as error:
        raise SourceIdentityError("source identity gate is create-only") from error
    finally:
        temporary.unlink(missing_ok=True)


def write_source_identity_gate(path: str | Path) -> bytes:
    encoded = compute_source_identity_bytes()
    _atomic_create(Path(path), encoded)
    if Path(path).read_bytes() != encoded:
        raise SourceIdentityError("source identity bytes changed during create-once publication")
    return encoded


def validate_source_identity_bytes(persisted: bytes, recomputed: bytes) -> dict[str, object]:
    if not isinstance(persisted, bytes) or not isinstance(recomputed, bytes) or persisted != recomputed:
        raise SourceIdentityError("persisted source identity differs from direct recomputation")
    try:
        value = json.loads(persisted.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SourceIdentityError("persisted source identity is unreadable") from error
    if not isinstance(value, dict) or _canonical_json(value) != persisted:
        raise SourceIdentityError("persisted source identity is not canonical direct JSON")
    return value


def validate_source_identity_gate(path: str | Path) -> dict[str, object]:
    try:
        persisted = Path(path).read_bytes()
    except OSError as error:
        raise SourceIdentityError("persisted source identity gate is unavailable") from error
    return validate_source_identity_bytes(persisted, compute_source_identity_bytes())


__all__ = [
    "ASSIGNED_BASE_COMMIT", "OWNED_PRODUCTION_PATHS", "SOURCE_IDENTITY_SCHEMA",
    "SourceIdentityError", "compute_source_identity", "compute_source_identity_bytes",
    "validate_source_identity_bytes", "validate_source_identity_gate", "write_source_identity_gate",
]
