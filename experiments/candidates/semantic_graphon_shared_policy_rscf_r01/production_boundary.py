"""Fail-closed production boundary for the frozen SGSP RSCF-r01 panel.

This module is deliberately a lifecycle/metadata boundary.  It does not step
RIDGEGATE-2Z in Python and it has no Python rollout fallback.  The factual,
shadow and full-suffix hot paths remain the source-keyed C++ ABI V3 host.  A
production master, coordinate plan or parameter tensor can only be materialized
from a current, exact Operational-Root lease.

The sealed preflight at the bottom of the module uses an unrelated TEST-only
secret and a disposable probe directory.  It cannot construct any of the
production classes guarded by :class:`ValidatedRootLease`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import argparse
import base64
import hashlib
import hmac
import io
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
import torch

from .analysis import QUANTITY_NAMES, SUPPORT_SLACK_CLARIFICATION_PATH
from .contracts import (
    PAIRS_PER_TRAIN_ROSTER,
    RESERVED_SCIENTIFIC_NAMESPACE,
    SCIENCE_REVISION,
    SEED_BLOCK_COUNT,
    TRAIN_ROSTERS,
    UPDATES,
)
from .native_contract import ABI_VERSION, HOST_KIND, NATIVE_THREADS
from .native_loader import load_native_host
from .policy import ACTOR_PARAMETER_SHAPES, CRITIC_PARAMETER_SHAPES
from .continuation_lineage import (
    ContinuationLineageError,
    validate_source_epoch_provenance,
)


PRODUCTION_BOUNDARY_SCHEMA = "SGSP_RSCF_R01_PRODUCTION_BOUNDARY_V1"
ROOT_LEASE_SCHEMA = "SGSP_RSCF_R01_OPERATIONAL_ROOT_LEASE_V1"
ROOT_LEASE_AUTHORITY = "OPERATIONAL_ROOT"
COORDINATE_SCHEMA = "SGSP_RSCF_R01_ARM_INDEPENDENT_COORDINATES_V1"
LIFECYCLE_SCHEMA = "SGSP_RSCF_R01_PRODUCTION_LIFECYCLE_V1"
PREFLIGHT_SCHEMA = "SGSP_RSCF_R01_SEALED_TEST_PREFLIGHT_V1"
PREFLIGHT_ARTIFACT_SCHEMA = "SGSP_RSCF_R01_EXTENDED_TEST_PREFLIGHT_ARTIFACT_V1"

WIDTH = 32
OUTER_WORKERS = 1
CPU_CORES = 1
GPU = False
RSS_CEILING_BYTES = 7_718_343_680
MINIMUM_AVAILABLE_MEMORY_BYTES = 12_013_310_976
MINIMUM_SYSTEM_RESERVE_BYTES = 4_294_967_296
RETAINED_STORAGE_CEILING_BYTES = 8_589_934_592
MINIMUM_FREE_STORAGE_BYTES = 17_179_869_184
PROJECTED_PANEL_WALL_SECONDS = 744_938.572103712
LEASE_FINALIZATION_MARGIN_SECONDS = 21_600
EXPECTED_ORIGINS_PER_SEED = 196_608
EXPECTED_ARM_INDEPENDENT_ORIGINS_PER_SEED = 98_304
EXPECTED_ARM_INDEPENDENT_ORIGINS_PANEL = 2_359_296
EXPECTED_ARM_ORIGINS_PANEL = 4_718_592
SOLE_EVALUABLE_UPDATE = 512
ARMS = ("PHY-TRUST", "EDGE-FLEX")

EXPECTED_COMBINED_SOURCE_SHA256 = "48d50b61b972f8471619ca762731c567edae791fdd0b34a99301663ba0734548"
EXPECTED_RUNNER_SHA256 = "6208674617e71102f11c0a4ab346857cbcbb048a4b7302acd678f661b85c3857"
EXPECTED_NATIVE_SOURCE_SHA256 = "014b7246c677f1bd12539a808c551fa7a80379e0312a7706b84020ee5e6dd5c0"
EXPECTED_NATIVE_SOURCE_KEY = "014b7246c677f1bd"
EXPECTED_NATIVE_BUILD_SHA256 = "0c14c2f7b3fa5840fe53a01ca7c9e219ba9309907533af2f971fa66f590cd5c9"
EXPECTED_NATIVE_ARTIFACT_SHA256 = "4a09f6e71eff77333e00aa30f0adcafc162485279a41a7fa79e9dec851d53962"
EXPECTED_NATIVE_ARTIFACT_SIZE = 249_344

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_SOURCE_PATHS = (
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/contracts.py",
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/native_contract.py",
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/native_loader.py",
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/native/rscf_r01_full_suffix_host.cpp",
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/policy.py",
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/training.py",
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/snapshot.py",
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/runner.py",
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/analysis.py",
    "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/continuation_lineage.py",
    "tools/benchmarks/benchmark_sgsp_rscf_gate_b.py",
    "tools/benchmarks/benchmark_sgsp_rscf_update_audit.py",
    SUPPORT_SLACK_CLARIFICATION_PATH,
)


class ProductionBoundaryError(ValueError):
    """A production-boundary object failed closed before scientific activity."""


class LeaseValidationError(ProductionBoundaryError):
    """The supplied lease is absent, stale, noncanonical or scope-inexact."""


class IntegrityError(ProductionBoundaryError):
    """A write-once lifecycle object is incomplete, inconsistent or changed."""


class WriteOnceConflictError(FileExistsError):
    """A production lifecycle destination already exists."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _plain(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        raise IntegrityError("canonical payload contains a nonfinite float")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise IntegrityError(f"unsupported canonical payload type {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("ascii")


def canonical_sha256(value: Any) -> str:
    return _sha256_bytes(canonical_json_bytes(value))


def _require_sha256(name: str, value: object) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ProductionBoundaryError(f"{name} must be a lowercase SHA-256")
    return value


def _parse_utc(name: str, value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise LeaseValidationError(f"{name} must be an RFC3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise LeaseValidationError(f"{name} is not a valid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise LeaseValidationError(f"{name} must be UTC")
    return parsed


@dataclass(frozen=True)
class ExactSourceBinding:
    combined_source_sha256: str
    runner_sha256: str
    native_abi: str
    native_host_kind: str
    native_source_sha256: str
    native_source_key: str
    native_build_key_sha256: str
    native_artifact_sha256: str
    native_artifact_size_bytes: int
    native_threads: int
    production_package_sha256: str

    @property
    def digest(self) -> str:
        return canonical_sha256(asdict(self))


def current_exact_source_binding(*, load_native: bool = True) -> ExactSourceBinding:
    """Recompute every frozen Gate-B source/ABI field and reject any drift."""

    combined = hashlib.sha256()
    file_hashes: dict[str, str] = {}
    for relative in _SOURCE_PATHS:
        path = _REPOSITORY_ROOT / relative
        payload = path.read_bytes()
        file_hashes[relative] = _sha256_bytes(payload)
        combined.update(relative.encode("utf-8"))
        combined.update(payload)
    combined_digest = combined.hexdigest()
    runner_digest = file_hashes[
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/runner.py"
    ]
    production_digest = hashlib.sha256()
    for relative in (
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/production_boundary.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/production_runner.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/production_launcher.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/production_preflight.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/continuation_lineage.py",
    ):
        payload = (_REPOSITORY_ROOT / relative).read_bytes()
        production_digest.update(relative.encode("utf-8"))
        production_digest.update(payload)
    production_package_sha256 = production_digest.hexdigest()
    if combined_digest != EXPECTED_COMBINED_SOURCE_SHA256:
        raise IntegrityError("Gate-B combined source identity drifted")
    if runner_digest != EXPECTED_RUNNER_SHA256:
        raise IntegrityError("Gate-B runner source identity drifted")

    if load_native:
        native = load_native_host()
        binding = ExactSourceBinding(
            combined_source_sha256=combined_digest,
            runner_sha256=runner_digest,
            native_abi=native.abi_version,
            native_host_kind=native.host_kind,
            native_source_sha256=native.source_sha256,
            native_source_key=native.source_key,
            native_build_key_sha256=native.build_key_sha256,
            native_artifact_sha256=native.artifact_sha256,
            native_artifact_size_bytes=native.artifact_size_bytes,
            native_threads=native.native_threads,
            production_package_sha256=production_package_sha256,
        )
    else:
        native_source = _REPOSITORY_ROOT / _SOURCE_PATHS[3]
        binding = ExactSourceBinding(
            combined_source_sha256=combined_digest,
            runner_sha256=runner_digest,
            native_abi=ABI_VERSION,
            native_host_kind=HOST_KIND,
            native_source_sha256=_sha256_file(native_source),
            native_source_key=_sha256_file(native_source)[:16],
            native_build_key_sha256=EXPECTED_NATIVE_BUILD_SHA256,
            native_artifact_sha256=EXPECTED_NATIVE_ARTIFACT_SHA256,
            native_artifact_size_bytes=EXPECTED_NATIVE_ARTIFACT_SIZE,
            native_threads=NATIVE_THREADS,
            production_package_sha256=production_package_sha256,
        )
    expected = ExactSourceBinding(
        EXPECTED_COMBINED_SOURCE_SHA256,
        EXPECTED_RUNNER_SHA256,
        ABI_VERSION,
        HOST_KIND,
        EXPECTED_NATIVE_SOURCE_SHA256,
        EXPECTED_NATIVE_SOURCE_KEY,
        EXPECTED_NATIVE_BUILD_SHA256,
        EXPECTED_NATIVE_ARTIFACT_SHA256,
        EXPECTED_NATIVE_ARTIFACT_SIZE,
        1,
        production_package_sha256,
    )
    if binding != expected:
        raise IntegrityError("loaded width-32 native source/ABI/build/artifact tuple drifted")
    return binding


_LEASE_FIELDS = frozenset({
    "lease_id", "lease_lineage_id", "authority", "direction_id", "science_revision", "namespace",
    "master_source", "master_record_relative_path", "outer_workers", "cpu_cores", "native_threads",
    "width", "gpu", "process_rss_ceiling_bytes", "minimum_available_memory_bytes",
    "minimum_system_reserve_bytes", "retained_root", "valid_from_utc",
    "valid_until_utc", "source_binding_sha256", "retained_storage_ceiling_bytes",
    "minimum_free_storage_bytes", "projected_wall_seconds", "production_preflight_sha256",
    "production_preflight_artifact_path", "production_preflight_artifact_file_sha256",
    "stage_boundary", "state",
})


@dataclass(frozen=True)
class ValidatedRootLease:
    lease_path: Path
    lease_payload: Mapping[str, Any]
    lease_payload_sha256: str
    source_binding: ExactSourceBinding
    retained_root: Path
    valid_until: datetime

    @property
    def lease_id(self) -> str:
        return str(self.lease_payload["lease_id"])

    @property
    def lease_lineage_id(self) -> str:
        return str(self.lease_payload["lease_lineage_id"])


def expected_production_preflight_artifact_path(source_binding_sha256: str) -> Path:
    _require_sha256("source_binding_sha256", source_binding_sha256)
    return (
        _REPOSITORY_ROOT
        / "artifacts"
        / "semantic_graphon_shared_policy"
        / "preflight"
        / f"SGSP_RG2Z_RSCF_R01_{source_binding_sha256}.json"
    ).resolve(strict=False)


def validate_production_preflight_artifact(
    path: Path | str,
    *,
    artifact_file_sha256: str,
    production_preflight_sha256: str,
    projected_wall_seconds: float,
    source_binding: ExactSourceBinding,
    require_exact_retained_path: bool = True,
) -> Mapping[str, Any]:
    """Authenticate the exact sealed preflight evidence used by a Root lease."""

    artifact_path = Path(path).resolve(strict=True)
    if require_exact_retained_path and artifact_path != expected_production_preflight_artifact_path(source_binding.digest):
        raise LeaseValidationError("production preflight artifact path is not the exact retained source-bound path")
    expected_file_sha = _require_sha256("production_preflight_artifact_file_sha256", artifact_file_sha256)
    raw = artifact_path.read_bytes()
    if _sha256_bytes(raw) != expected_file_sha:
        raise LeaseValidationError("production preflight artifact file digest mismatch")
    try:
        envelope = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LeaseValidationError("production preflight artifact is not canonical ASCII JSON") from exc
    if canonical_json_bytes(envelope) != raw:
        raise LeaseValidationError("production preflight artifact bytes are not canonical")
    if not isinstance(envelope, dict) or set(envelope) != {"schema", "report_sha256", "report"}:
        raise LeaseValidationError("production preflight artifact envelope is not exact")
    report = envelope["report"]
    if envelope["schema"] != PREFLIGHT_ARTIFACT_SCHEMA or not isinstance(report, dict):
        raise LeaseValidationError("production preflight artifact schema changed")
    if report.get("production_preflight_sha256") != production_preflight_sha256:
        raise LeaseValidationError("Root lease preflight digest differs from the retained artifact")
    report_core = dict(report)
    report_digest = report_core.pop("production_preflight_sha256", None)
    if (
        _require_sha256("production_preflight_sha256", report_digest) != canonical_sha256(report_core)
        or envelope["report_sha256"] != report_digest
    ):
        raise LeaseValidationError("production preflight report digest mismatch")
    if (
        report.get("source_binding_sha256") != source_binding.digest
        or report.get("schema") != "SGSP_RSCF_R01_EXTENDED_TEST_ONLY_PRODUCTION_PREFLIGHT_V1"
        or report.get("formal_activity") is not False
        or report.get("empirical_objects_created") != 0
        or report.get("probe_cleanup_complete") is not True
        or report.get("exact_coordinate_adapter_class") != (
            "experiments.candidates.semantic_graphon_shared_policy_rscf_r01."
            "production_boundary.EmpiricalCoordinateAdapter"
        )
        or report.get("exact_coordinate_adapter_test_only") is not True
    ):
        raise LeaseValidationError("production preflight artifact is not exact, source-current, and TEST-only")
    if (
        isinstance(projected_wall_seconds, bool)
        or not isinstance(projected_wall_seconds, (int, float))
        or report.get("production_projected_wall_seconds") != projected_wall_seconds
        or report.get("required_lease_remaining_seconds")
        != math.ceil(float(projected_wall_seconds) + LEASE_FINALIZATION_MARGIN_SECONDS)
    ):
        raise LeaseValidationError("Root lease projection differs from the retained preflight")
    return report


def validate_root_lease(
    path: Path | str,
    *,
    now_utc: datetime | None = None,
    available_memory_bytes: int | None = None,
    load_native: bool = True,
    require_full_projection: bool = True,
) -> ValidatedRootLease:
    """Validate one canonical Root lease before accepting a production master."""

    lease_path = Path(path).resolve(strict=True)
    raw = lease_path.read_bytes()
    try:
        envelope = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LeaseValidationError("lease is not canonical ASCII JSON") from exc
    if canonical_json_bytes(envelope) != raw:
        raise LeaseValidationError("lease bytes are not canonical")
    if not isinstance(envelope, dict) or set(envelope) != {"schema", "payload_sha256", "payload"}:
        raise LeaseValidationError("lease envelope schema is not exact")
    if envelope["schema"] != ROOT_LEASE_SCHEMA or not isinstance(envelope["payload"], dict):
        raise LeaseValidationError("lease schema is not SGSP RSCF-r01")
    payload = envelope["payload"]
    if set(payload) != _LEASE_FIELDS:
        raise LeaseValidationError("lease payload field inventory is not exact")
    payload_sha = canonical_sha256(payload)
    if envelope["payload_sha256"] != payload_sha:
        raise LeaseValidationError("lease payload digest mismatch")

    exact = {
        "authority": ROOT_LEASE_AUTHORITY,
        "direction_id": "semantic_graphon_shared_policy",
        "science_revision": SCIENCE_REVISION,
        "namespace": RESERVED_SCIENTIFIC_NAMESPACE,
        "master_source": "OS_CSPRNG_256_ONE_SHOT_AFTER_LEASE_DPAPI_SEALED",
        "master_record_relative_path": "control/master.json",
        "outer_workers": OUTER_WORKERS,
        "cpu_cores": CPU_CORES,
        "native_threads": NATIVE_THREADS,
        "width": WIDTH,
        "gpu": GPU,
        "process_rss_ceiling_bytes": RSS_CEILING_BYTES,
        "minimum_available_memory_bytes": MINIMUM_AVAILABLE_MEMORY_BYTES,
        "minimum_system_reserve_bytes": MINIMUM_SYSTEM_RESERVE_BYTES,
        "retained_storage_ceiling_bytes": RETAINED_STORAGE_CEILING_BYTES,
        "minimum_free_storage_bytes": MINIMUM_FREE_STORAGE_BYTES,
        "stage_boundary": "ONE_EXACT_COMPLETE_PANEL",
        "state": "ISSUED",
    }
    for name, expected in exact.items():
        if payload[name] != expected:
            raise LeaseValidationError(f"lease field {name} differs from the accepted mode-one envelope")
    projected_wall = payload["projected_wall_seconds"]
    if (
        isinstance(projected_wall, bool)
        or not isinstance(projected_wall, (int, float))
        or not math.isfinite(float(projected_wall))
        or float(projected_wall) < PROJECTED_PANEL_WALL_SECONDS
    ):
        raise LeaseValidationError("projected_wall_seconds must include the measured production overhead")
    try:
        _require_sha256("production_preflight_sha256", payload["production_preflight_sha256"])
    except ProductionBoundaryError as exc:
        raise LeaseValidationError(str(exc)) from exc
    if not isinstance(payload["lease_id"], str) or not payload["lease_id"].startswith("SGSP-RG2Z-RSCF-R01-ROOT-"):
        raise LeaseValidationError("lease_id is not Root SGSP RSCF-r01 scoped")
    if not isinstance(payload["lease_lineage_id"], str) or not payload["lease_lineage_id"].startswith("SGSP-RG2Z-RSCF-R01-LINEAGE-"):
        raise LeaseValidationError("lease_lineage_id is not SGSP RSCF-r01 scoped")
    binding = current_exact_source_binding(load_native=load_native)
    if payload["source_binding_sha256"] != binding.digest:
        raise LeaseValidationError("lease is not bound to the current exact width-32 source/ABI tuple")
    validate_production_preflight_artifact(
        payload["production_preflight_artifact_path"],
        artifact_file_sha256=payload["production_preflight_artifact_file_sha256"],
        production_preflight_sha256=payload["production_preflight_sha256"],
        projected_wall_seconds=float(projected_wall),
        source_binding=binding,
    )
    retained_root = Path(payload["retained_root"])
    if not retained_root.is_absolute():
        raise LeaseValidationError("retained_root must be absolute")
    retained_root = retained_root.resolve(strict=False)
    expected_retained_root = (
        _REPOSITORY_ROOT
        / "artifacts"
        / "semantic_graphon_shared_policy"
        / "empirical"
        / str(payload["lease_lineage_id"])
    ).resolve(strict=False)
    if retained_root != expected_retained_root:
        raise LeaseValidationError("retained_root must be the exact lineage-stable SGSP empirical path")
    storage_probe = retained_root
    while not storage_probe.exists() and storage_probe != storage_probe.parent:
        storage_probe = storage_probe.parent
    if shutil.disk_usage(storage_probe).free < MINIMUM_FREE_STORAGE_BYTES:
        raise LeaseValidationError("retained volume free storage is below the exact launch threshold")
    start = _parse_utc("valid_from_utc", payload["valid_from_utc"])
    end = _parse_utc("valid_until_utc", payload["valid_until_utc"])
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise LeaseValidationError("validation clock must be timezone-aware")
    if not start <= now.astimezone(timezone.utc) < end:
        raise LeaseValidationError("lease is not currently valid")
    remaining = (end - now.astimezone(timezone.utc)).total_seconds()
    required_remaining = math.ceil(float(projected_wall) + LEASE_FINALIZATION_MARGIN_SECONDS)
    if require_full_projection and remaining < required_remaining:
        raise LeaseValidationError("lease does not cover projected mode-one panel wall plus finalization margin")
    if available_memory_bytes is not None and available_memory_bytes < MINIMUM_AVAILABLE_MEMORY_BYTES:
        raise LeaseValidationError("system available memory is below the exact launch threshold")
    return ValidatedRootLease(lease_path, payload, payload_sha, binding, retained_root, end)


class BoundEmpiricalMaster:
    """Redacted master capability constructible only from a validated Root lease."""

    __slots__ = ("_secret", "lease_lineage_id", "current_lease_payload_sha256", "commitment_sha256")

    def __init__(self, lease: ValidatedRootLease, secret: bytes) -> None:
        if len(secret) != 32:
            raise LeaseValidationError("empirical master token must contain exactly 256 bits")
        commitment = _sha256_bytes(b"SGSP_RSCF_R01_MASTER_V1|" + secret)
        self._secret = secret
        self.lease_lineage_id = lease.lease_lineage_id
        self.current_lease_payload_sha256 = lease.lease_payload_sha256
        self.commitment_sha256 = commitment

    def __repr__(self) -> str:
        return "BoundEmpiricalMaster(<redacted>)"


def _dpapi_protect(plaintext: bytes, entropy: bytes) -> bytes:
    if os.name != "nt":
        raise IntegrityError("Windows same-user DPAPI is required; no master-seal fallback exists")
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    def blob(value: bytes):
        buffer = ctypes.create_string_buffer(value)
        return DATA_BLOB(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer

    source, source_buffer = blob(plaintext)
    optional_entropy, entropy_buffer = blob(entropy)
    destination = DATA_BLOB()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), wintypes.LPCWSTR, ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL
    if not crypt32.CryptProtectData(
        ctypes.byref(source), "SGSP RSCF-r01 empirical master",
        ctypes.byref(optional_entropy), None, None, 0x1,
        ctypes.byref(destination),
    ):
        raise OSError(ctypes.get_last_error(), "CryptProtectData failed")
    del source_buffer, entropy_buffer
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(destination.pbData)


def _dpapi_unprotect(ciphertext: bytes, entropy: bytes) -> bytes:
    if os.name != "nt":
        raise IntegrityError("Windows same-user DPAPI is required; no master-seal fallback exists")
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    def blob(value: bytes):
        buffer = ctypes.create_string_buffer(value)
        return DATA_BLOB(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer

    source, source_buffer = blob(ciphertext)
    optional_entropy, entropy_buffer = blob(entropy)
    destination = DATA_BLOB()
    description = wintypes.LPWSTR()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), ctypes.POINTER(wintypes.LPWSTR), ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source), ctypes.byref(description), ctypes.byref(optional_entropy),
        None, None, 0x1, ctypes.byref(destination),
    ):
        raise OSError(ctypes.get_last_error(), "CryptUnprotectData failed")
    del source_buffer, entropy_buffer
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        if description:
            kernel32.LocalFree(description)
        kernel32.LocalFree(destination.pbData)


def _master_dpapi_entropy(lease: ValidatedRootLease) -> bytes:
    return (
        f"{SCIENCE_REVISION}|{lease.lease_lineage_id}|SGSP_RSCF_R01_MASTER_DPAPI_V1"
    ).encode("ascii")


def mint_or_resume_empirical_master(lease: ValidatedRootLease) -> BoundEmpiricalMaster:
    """Create exactly one master after lease admission, or resume that exact one.

    The canonical record is installed with an exclusive atomic link beneath the
    lease-owned retained root.  The lease contains no master or commitment, so
    validating it cannot cross the scientific-activity boundary.
    """

    relative = Path(str(lease.lease_payload["master_record_relative_path"]))
    if relative.is_absolute() or ".." in relative.parts:
        raise LeaseValidationError("master record path escaped the lease root")
    path = lease.retained_root / relative
    if path.exists():
        raw = path.read_bytes()
        try:
            record = json.loads(raw.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntegrityError("persisted master record is unreadable") from exc
        if canonical_json_bytes(record) != raw or set(record) != {
            "schema", "lease_lineage_id", "source_binding_sha256",
            "ciphertext_b64", "commitment_sha256"
        }:
            raise IntegrityError("persisted master record is noncanonical")
        if (
            record["schema"] != "SGSP_RSCF_R01_MASTER_RECORD_V2_DPAPI"
            or record["lease_lineage_id"] != lease.lease_lineage_id
            or record["source_binding_sha256"] != lease.source_binding.digest
        ):
            raise IntegrityError("persisted master record belongs to another lineage or source binding")
        try:
            ciphertext = base64.b64decode(record["ciphertext_b64"], validate=True)
        except (TypeError, ValueError) as exc:
            raise IntegrityError("persisted DPAPI master ciphertext is malformed") from exc
        secret = _dpapi_unprotect(ciphertext, _master_dpapi_entropy(lease))
        master = BoundEmpiricalMaster(lease, secret)
        if not hmac.compare_digest(master.commitment_sha256, record["commitment_sha256"]):
            raise IntegrityError("persisted master commitment mismatch")
        return master
    secret = os.urandom(32)
    master = BoundEmpiricalMaster(lease, secret)
    ciphertext = _dpapi_protect(secret, _master_dpapi_entropy(lease))
    record = {
        "schema": "SGSP_RSCF_R01_MASTER_RECORD_V2_DPAPI",
        "lease_lineage_id": lease.lease_lineage_id,
        "source_binding_sha256": lease.source_binding.digest,
        "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
        "commitment_sha256": master.commitment_sha256,
    }
    try:
        _atomic_write_once(path, canonical_json_bytes(record))
    except WriteOnceConflictError:
        # A simultaneous process won.  Discard this secret and admit only the
        # exact write-once record now on disk.
        return mint_or_resume_empirical_master(lease)
    return master


def resume_empirical_master_through_lineage(
    predecessor_lease: ValidatedRootLease,
    continuation_lease: ValidatedRootLease,
    lineage: Any,
    continuation_identity: Any,
) -> BoundEmpiricalMaster:
    """Authenticate A's write-once master and bind the same secret to B.

    Ordinary restore remains source-strict in :func:`mint_or_resume_empirical_master`.
    This separate operation accepts only the exact, separately hashed lineage.
    """

    if (
        predecessor_lease.retained_root != continuation_lease.retained_root
        or predecessor_lease.lease_lineage_id != continuation_lease.lease_lineage_id
        or predecessor_lease.lease_payload.get("master_record_relative_path")
        != continuation_lease.lease_payload.get("master_record_relative_path")
        or predecessor_lease.source_binding.digest != lineage.predecessor_source_binding_sha256
        or continuation_lease.source_binding.digest != lineage.continuation_source_binding_sha256
        or predecessor_lease.source_binding.digest == continuation_lease.source_binding.digest
        or lineage.lease_lineage_id != predecessor_lease.lease_lineage_id
    ):
        raise IntegrityError("master continuation leases differ from the exact A-to-B lineage")
    try:
        continuation_identity.require_exact_lineage(lineage)
    except ValueError as exc:
        raise IntegrityError("continuation identity does not authenticate the lineage") from exc
    before_path = predecessor_lease.retained_root / Path(
        str(predecessor_lease.lease_payload["master_record_relative_path"])
    )
    before = before_path.read_bytes()
    predecessor_master = mint_or_resume_empirical_master(predecessor_lease)
    after = before_path.read_bytes()
    if before != after:
        raise IntegrityError("predecessor master record changed during lineage authentication")
    if predecessor_master.commitment_sha256 != lineage.predecessor_master_commitment_sha256:
        raise IntegrityError("predecessor master commitment differs from the lineage")
    continuation_master = BoundEmpiricalMaster(
        continuation_lease, predecessor_master._secret
    )
    if continuation_master.commitment_sha256 != predecessor_master.commitment_sha256:
        raise IntegrityError("continuation master commitment changed")
    return continuation_master


def _address_word(secret: bytes, payload: Mapping[str, Any], counter: int = 0) -> int:
    material = canonical_json_bytes({"payload": payload, "counter": counter})
    return int.from_bytes(hmac.new(secret, material, hashlib.sha256).digest()[:8], "big")


def _uniform_below(secret: bytes, payload: Mapping[str, Any], upper: int) -> int:
    if upper <= 0:
        raise ProductionBoundaryError("uniform support must be positive")
    limit = (1 << 64) - ((1 << 64) % upper)
    counter = 0
    while True:
        word = _address_word(secret, payload, counter)
        if word < limit:
            return word % upper
        counter += 1


_COORDINATE_KIND_CODES = {
    "event_time": 1,
    "detection_uniform": 2,
    "base_uniform": 3,
    "action_uniform": 4,
    "uplink_uniform": 5,
    "base_slot": 6,
    "local_index": 7,
}


def _mix64_word(value: int) -> int:
    mask = (1 << 64) - 1
    value = (value + 0x9E3779B97F4A7C15) & mask
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & mask
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
    return (value ^ (value >> 31)) & mask


def _coordinate_word(
    key: int,
    *,
    kind_code: int,
    phase_code: int,
    roster_size: int,
    update_index: int,
    episode_index: int,
    coordinate_0: int,
    coordinate_1: int,
    coordinate_2: int,
    counter: int = 0,
) -> int:
    mask = (1 << 64) - 1
    value = key & mask
    for factor, constant in (
        (kind_code, 0xD6E8FEB86659FD93),
        (phase_code, 0xA5A35625AA5A3563),
        (roster_size, 0x9E3779B185EBCA87),
        (update_index + 1, 0xC2B2AE3D27D4EB4F),
        (episode_index, 0x165667B19E3779F9),
        (coordinate_0, 0x85EBCA77C2B2AE63),
        (coordinate_1, 0x27D4EB2F165667C5),
        (coordinate_2, 0x94D049BB133111EB),
        (counter, 0xDB4F0B9175AE2165),
    ):
        value ^= (factor * constant) & mask
    return _mix64_word(value)


def _coordinate_uniform_below(key: int, upper: int, **address: int) -> int:
    limit = (1 << 64) - ((1 << 64) % upper)
    counter = 0
    while True:
        word = _coordinate_word(key, counter=counter, **address)
        if word < limit:
            return word % upper
        counter += 1


@dataclass(frozen=True)
class SeedBlockBinding:
    index: int
    seed_block_id: str
    seed_commitment_sha256: str


@dataclass(frozen=True)
class ArmIndependentOrigin:
    seed_block_index: int
    update_index: int
    roster_size: int
    pair_index: int
    side: int
    role_index: int
    base_slot: int
    selected_slot: int
    role_local_index: int
    address_sha256: str

    @property
    def arm_keys(self) -> tuple[tuple[str, str], ...]:
        return tuple((arm, self.address_sha256) for arm in ARMS)


@dataclass(frozen=True)
class ArmIndependentPotential:
    """One addressed task/action potential with arm structurally unavailable."""

    seed_block_index: int
    phase: str
    roster_size: int
    episode_index: int
    random_variable_kind: str
    address_sha256: str
    uniform_01: float


class EmpiricalCoordinateAdapter:
    """Lazy counter-addressed coordinate plan; no arm enters selector addresses."""

    def __init__(self, lease: ValidatedRootLease, master: BoundEmpiricalMaster) -> None:
        if master.lease_lineage_id != lease.lease_lineage_id:
            raise ProductionBoundaryError("master and lease lineage differ")
        self._lease_lineage_id = lease.lease_lineage_id
        self._master = master
        self.namespace = RESERVED_SCIENTIFIC_NAMESPACE
        self._test_only = False
        self._bind_seed_manifest()

    def _bind_seed_manifest(self) -> None:
        blocks = []
        for index in range(SEED_BLOCK_COUNT):
            secret = hmac.new(
                self._master._secret,
                f"{SCIENCE_REVISION}|seed-block|{index:02d}".encode("ascii"),
                hashlib.sha256,
            ).digest()
            blocks.append(SeedBlockBinding(index, f"SB{index:02d}", _sha256_bytes(secret)))
        self.seed_blocks = tuple(blocks)
        self.manifest_sha256 = canonical_sha256({
            "schema": COORDINATE_SCHEMA,
            "namespace": self.namespace,
            "seed_commitments": [asdict(item) for item in self.seed_blocks],
            "training_rosters": TRAIN_ROSTERS,
            "updates": UPDATES,
            "pairs_per_roster": PAIRS_PER_TRAIN_ROSTER,
            "sides": 2,
            "roles": 3,
            "arm_independent_origins": EXPECTED_ARM_INDEPENDENT_ORIGINS_PANEL,
            "arm_origins": EXPECTED_ARM_ORIGINS_PANEL,
            "arms": ARMS,
            "address_omits_arm": True,
        })

    @classmethod
    def for_sealed_test_preflight(
        cls, *, namespace: str, secret: bytes
    ) -> "EmpiricalCoordinateAdapter":
        """Create the exact adapter under a capability that cannot enter production."""

        if not namespace.startswith("TEST_ONLY|"):
            raise ProductionBoundaryError("sealed coordinate capability requires a TEST_ONLY namespace")
        if len(secret) != 32 or not secret.startswith(b"TEST_ONLY|"):
            raise ProductionBoundaryError("sealed coordinate capability requires an exact TEST_ONLY secret")

        class _TestOnlyMasterCapability:
            __slots__ = ("_secret",)

            def __init__(self, value: bytes) -> None:
                self._secret = value

        adapter = cls.__new__(cls)
        adapter._lease_lineage_id = namespace
        adapter._master = _TestOnlyMasterCapability(secret)
        adapter.namespace = namespace
        adapter._test_only = True
        adapter._bind_seed_manifest()
        return adapter

    def _seed_secret(self, index: int) -> bytes:
        if type(index) is not int or not 0 <= index < SEED_BLOCK_COUNT:
            raise ProductionBoundaryError("seed block index must be in [0,23]")
        return hmac.new(
            self._master._secret,
            f"{SCIENCE_REVISION}|seed-block|{index:02d}".encode("ascii"),
            hashlib.sha256,
        ).digest()

    def origin(
        self, *, seed_block_index: int, update_index: int, roster_size: int,
        pair_index: int, side: int, role_index: int,
    ) -> ArmIndependentOrigin:
        if not 0 <= update_index < UPDATES or roster_size not in TRAIN_ROSTERS:
            raise ProductionBoundaryError("origin update/roster is outside the frozen panel")
        if not 0 <= pair_index < PAIRS_PER_TRAIN_ROSTER or side not in (0, 1) or not 0 <= role_index < 3:
            raise ProductionBoundaryError("origin pair/side/role is outside the frozen schedule")
        key = int.from_bytes(self._seed_secret(seed_block_index)[:8], "little")
        common = {
            "schema": COORDINATE_SCHEMA,
            "namespace": self.namespace,
            "seed_block": f"SB{seed_block_index:02d}",
            "phase": "TRAINING",
            "update": update_index,
            "roster": roster_size,
            "pair": pair_index,
            "role": role_index,
        }
        base_payload = {**common, "kind": "base_slot"}
        base = _coordinate_uniform_below(
            key, 12, kind_code=_COORDINATE_KIND_CODES["base_slot"],
            phase_code=1, roster_size=roster_size, update_index=update_index,
            episode_index=pair_index, coordinate_0=role_index,
            coordinate_1=0, coordinate_2=0,
        )
        local_payload = {**common, "side": side, "kind": "local_index"}
        local = _coordinate_uniform_below(
            key, roster_size // 3, kind_code=_COORDINATE_KIND_CODES["local_index"],
            phase_code=1, roster_size=roster_size, update_index=update_index,
            episode_index=pair_index, coordinate_0=role_index,
            coordinate_1=side, coordinate_2=0,
        )
        address = {**common, "side": side, "base_slot": base, "local_index": local}
        return ArmIndependentOrigin(
            seed_block_index, update_index, roster_size, pair_index, side,
            role_index, base, base if side == 0 else 11 - base, local,
            canonical_sha256(address),
        )

    def iter_update(self, seed_block_index: int, update_index: int) -> Iterator[ArmIndependentOrigin]:
        for roster in TRAIN_ROSTERS:
            for pair in range(PAIRS_PER_TRAIN_ROSTER):
                for side in (0, 1):
                    for role in range(3):
                        yield self.origin(
                            seed_block_index=seed_block_index, update_index=update_index,
                            roster_size=roster, pair_index=pair, side=side,
                            role_index=role,
                        )

    def potential(
        self,
        *,
        seed_block_index: int,
        phase: str,
        roster_size: int,
        episode_index: int,
        random_variable_kind: str,
        update_index: int | None = None,
        basin: int | None = None,
        event_ordinal: int | None = None,
        slot: int | None = None,
        public_role: int | None = None,
        role_local_index: int | None = None,
        sender: int | None = None,
        receiver: int | None = None,
    ) -> ArmIndependentPotential:
        """Address every task/action potential without a sequential RNG stream.

        The exact domains cover event times, detection, packet/uplink, base
        delivery and inverse-CDF action uniforms for training and evaluation.
        Optional semantic coordinates are always present in canonical form;
        callers cannot supply an arm, model state, action outcome or branch.
        """

        allowed_kinds = set(_COORDINATE_KIND_CODES) - {"base_slot", "local_index"}
        if random_variable_kind not in allowed_kinds:
            raise ProductionBoundaryError("potential kind is outside the frozen task/action domains")
        if phase not in ("TRAINING", "EVALUATION"):
            raise ProductionBoundaryError("potential phase must be TRAINING or EVALUATION")
        allowed_rosters = TRAIN_ROSTERS if phase == "TRAINING" else (9, 15, 6, 21)
        if roster_size not in allowed_rosters:
            raise ProductionBoundaryError("potential roster is outside the phase population")
        if phase == "TRAINING":
            if update_index is None or not 0 <= update_index < 512 or not 0 <= episode_index < 32:
                raise ProductionBoundaryError("training potential update/episode is invalid")
        elif update_index is not None or not 0 <= episode_index < 256:
            raise ProductionBoundaryError("evaluation potential update/episode is invalid")
        bounded = {
            "basin": (basin, 2), "event_ordinal": (event_ordinal, 3),
            "slot": (slot, 12), "public_role": (public_role, 3),
            "role_local_index": (role_local_index, roster_size // 3),
            "sender": (sender, roster_size), "receiver": (receiver, roster_size),
        }
        for name, (value, upper) in bounded.items():
            if value is not None and (type(value) is not int or not 0 <= value < upper):
                raise ProductionBoundaryError(f"potential coordinate {name} is invalid")
        if random_variable_kind == "event_time" and (basin is None or event_ordinal is None):
            raise ProductionBoundaryError("event-time potential requires basin and event ordinal")
        if random_variable_kind != "event_time" and slot is None:
            raise ProductionBoundaryError("slot-indexed potential requires a slot")
        if random_variable_kind in {"detection_uniform", "base_uniform", "action_uniform", "uplink_uniform"} and sender is None and (public_role is None or role_local_index is None):
            raise ProductionBoundaryError("agent potential requires sender or public-role/local coordinates")
        if random_variable_kind == "uplink_uniform" and receiver is None:
            raise ProductionBoundaryError("uplink potential requires receiver")
        payload = {
            "schema": COORDINATE_SCHEMA,
            "namespace": self.namespace,
            "seed_block": f"SB{seed_block_index:02d}",
            "phase": phase,
            "update": update_index,
            "roster": roster_size,
            "episode": episode_index,
            "basin": basin,
            "event_ordinal": event_ordinal,
            "slot": slot,
            "public_role": public_role,
            "role_local_index": role_local_index,
            "sender": sender,
            "receiver": receiver,
            "kind": random_variable_kind,
        }
        coordinate_0 = event_ordinal if random_variable_kind == "event_time" else (slot or 0)
        if sender is not None:
            coordinate_1 = sender
        elif public_role is not None and role_local_index is not None:
            coordinate_1 = public_role * (roster_size // 3) + role_local_index
        else:
            coordinate_1 = basin or 0
        coordinate_2 = receiver or 0
        word = _coordinate_word(
            int.from_bytes(self._seed_secret(seed_block_index)[:8], "little"),
            kind_code=_COORDINATE_KIND_CODES[random_variable_kind],
            phase_code=1 if phase == "TRAINING" else 2,
            roster_size=roster_size,
            update_index=update_index if update_index is not None else -1,
            episode_index=episode_index,
            coordinate_0=coordinate_0,
            coordinate_1=coordinate_1,
            coordinate_2=coordinate_2,
        )
        return ArmIndependentPotential(
            seed_block_index, phase, roster_size, episode_index,
            random_variable_kind, canonical_sha256(payload),
            float(np.float32((word >> 11) * (1.0 / (1 << 53)))),
        )

    def uniform_grid(
        self,
        *,
        seed_block_index: int,
        phase: str,
        roster_size: int,
        update_index: int,
        random_variable_kind: str,
        episode_indices: np.ndarray,
        slot_indices: np.ndarray,
        sender_indices: np.ndarray,
        receiver_indices: np.ndarray,
    ) -> np.ndarray:
        """Vectorize the same arm-free task/action address domain for ABI tapes."""

        kinds = {name: code for name, code in _COORDINATE_KIND_CODES.items() if name not in ("base_slot", "local_index")}
        if random_variable_kind not in kinds or phase not in ("TRAINING", "EVALUATION"):
            raise ProductionBoundaryError("uniform grid kind/phase is outside the frozen coordinate domain")
        if phase == "TRAINING" and roster_size not in TRAIN_ROSTERS:
            raise ProductionBoundaryError("training uniform grid roster changed")
        if phase == "EVALUATION" and roster_size not in (9, 15, 6, 21):
            raise ProductionBoundaryError("evaluation uniform grid roster changed")
        key = int.from_bytes(self._seed_secret(seed_block_index)[:8], "little")
        shape = np.broadcast_shapes(
            episode_indices.shape, slot_indices.shape,
            sender_indices.shape, receiver_indices.shape,
        )
        value = np.full(shape, np.uint64(key), dtype=np.uint64)
        mask = (1 << 64) - 1
        phase_code = 1 if phase == "TRAINING" else 2
        for factor, constant in (
            (kinds[random_variable_kind], 0xD6E8FEB86659FD93),
            (phase_code, 0xA5A35625AA5A3563),
            (roster_size, 0x9E3779B185EBCA87),
            (update_index + 1, 0xC2B2AE3D27D4EB4F),
        ):
            value ^= np.uint64((factor * constant) & mask)
        value ^= episode_indices.astype(np.uint64) * np.uint64(0x165667B19E3779F9)
        value ^= slot_indices.astype(np.uint64) * np.uint64(0x85EBCA77C2B2AE63)
        value ^= sender_indices.astype(np.uint64) * np.uint64(0x27D4EB2F165667C5)
        value ^= receiver_indices.astype(np.uint64) * np.uint64(0x94D049BB133111EB)
        value = value + np.uint64(0x9E3779B97F4A7C15)
        value = (value ^ (value >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        value = (value ^ (value >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        words = value ^ (value >> np.uint64(31))
        return ((words >> np.uint64(11)).astype(np.float32)) * (1.0 / (1 << 53))

    def event_times(
        self,
        *,
        seed_block_index: int,
        phase: str,
        roster_size: int,
        update_index: int,
        episode_index: int,
        basin: int,
    ) -> tuple[int, int, int]:
        if basin not in (0, 1):
            raise ProductionBoundaryError("event basin is invalid")
        key = int.from_bytes(self._seed_secret(seed_block_index)[:8], "little")
        selected: list[int] = []
        for ordinal in range(3):
            counter = 0
            while True:
                word = _coordinate_word(
                    key,
                    kind_code=_COORDINATE_KIND_CODES["event_time"],
                    phase_code=1 if phase == "TRAINING" else 2,
                    roster_size=roster_size,
                    update_index=update_index,
                    episode_index=episode_index,
                    coordinate_0=ordinal,
                    coordinate_1=basin,
                    coordinate_2=0,
                    counter=counter,
                )
                candidate = word % 8
                if candidate not in selected:
                    selected.append(candidate)
                    break
                counter += 1
        return tuple(selected)  # type: ignore[return-value]


@dataclass(frozen=True)
class ParameterInitialization:
    seed_block_index: int
    coordinate_manifest_sha256: str
    actor_parameters: Mapping[str, torch.Tensor]
    critic_parameters: Mapping[str, torch.Tensor]
    initialization_sha256: str
    arms_bitwise_equal: bool


def initialize_one_worker_parameters(
    lease: ValidatedRootLease,
    master: BoundEmpiricalMaster,
    coordinates: EmpiricalCoordinateAdapter,
    *, seed_block_index: int,
) -> ParameterInitialization:
    """Materialize the frozen initializer only after lease and coordinate bind."""

    if master.lease_lineage_id != lease.lease_lineage_id:
        raise ProductionBoundaryError("initializer master was not admitted by this lease lineage")
    if coordinates._lease_lineage_id != lease.lease_lineage_id:
        raise ProductionBoundaryError("initializer coordinate plan was not bound by this lease lineage")
    secret = coordinates._seed_secret(seed_block_index)

    def uniforms(name: str, shape: tuple[int, ...], gain: float) -> torch.Tensor:
        fan_out, fan_in = shape
        # The frozen initializer is part of the FP32 model boundary.  Keep the
        # addressed integer draws unchanged, but evaluate its continuous
        # transforms in Torch FP32 rather than Python's binary64 scalars.
        bound = torch.tensor(gain, dtype=torch.float32) * torch.sqrt(
            torch.tensor(6.0 / (fan_in + fan_out), dtype=torch.float32)
        )
        count = math.prod(shape)
        values = [
            ((_address_word(secret, {"kind": "init-uniform", "tensor": name, "index": i}) + 0.5) / (1 << 64))
            for i in range(count)
        ]
        return ((torch.tensor(values, dtype=torch.float32) * 2.0 - 1.0) * bound).to(torch.float32).reshape(shape).contiguous()

    def normals(name: str, count: int) -> torch.Tensor:
        values: list[float] = []
        pair = 0
        while len(values) < count:
            u1 = (_address_word(secret, {"kind": "init-normal", "tensor": name, "pair": pair, "part": 0}) + 1.0) / ((1 << 64) + 1.0)
            u2 = (_address_word(secret, {"kind": "init-normal", "tensor": name, "pair": pair, "part": 1}) + 0.5) / (1 << 64)
            radius = torch.sqrt(-2.0 * torch.log(torch.tensor(u1, dtype=torch.float32)))
            angle = torch.tensor(2.0 * math.pi * u2, dtype=torch.float32)
            values.extend((
                float(radius * torch.cos(angle)),
                float(radius * torch.sin(angle)),
            ))
            pair += 1
        return torch.tensor(values[:count], dtype=torch.float32)

    actor: dict[str, torch.Tensor] = {}
    critic: dict[str, torch.Tensor] = {}
    zero_actor = {"encoder_b1", "encoder_b2", "b_z", "b_r", "b_n", "actor_b", "beta"}
    zero_critic = {"critic_b1", "critic_b2", "critic_b3"}
    gain_001 = {"actor_w"}
    recurrent = {"u_z", "u_r", "u_n"}
    for name, shape in ACTOR_PARAMETER_SHAPES.items():
        if name in zero_actor:
            actor[name] = torch.zeros(shape, dtype=torch.float32)
        elif name in recurrent:
            matrix = normals(name, 64 * 64).reshape(64, 64)
            q, r = torch.linalg.qr(matrix)
            signs = torch.where(torch.diag(r) < 0, -torch.ones(64), torch.ones(64))
            actor[name] = (q * signs).contiguous()
        else:
            actor[name] = uniforms(name, shape, 0.01 if name in gain_001 else 1.0)
    for name, shape in CRITIC_PARAMETER_SHAPES.items():
        critic[name] = torch.zeros(shape, dtype=torch.float32) if name in zero_critic else uniforms(name, shape, 1.0)
    digest = canonical_sha256({
        "actor": {name: _sha256_bytes(value.numpy().tobytes()) for name, value in sorted(actor.items())},
        "critic": {name: _sha256_bytes(value.numpy().tobytes()) for name, value in sorted(critic.items())},
        "seed_block": seed_block_index,
        "manifest": coordinates.manifest_sha256,
    })
    # Both arms receive distinct tensor copies of this one bitwise identity.
    equal = all(torch.equal(value, value.clone()) for value in (*actor.values(), *critic.values()))
    return ParameterInitialization(seed_block_index, coordinates.manifest_sha256, actor, critic, digest, equal)


def _atomic_write_once(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".pending", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short atomic write")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise WriteOnceConflictError(str(path)) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
    return _sha256_bytes(data)


def _atomic_replace(path: Path, data: bytes) -> str:
    """Durably replace one non-evaluable resume image with no partial window."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".pending", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short atomic resume write")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
    return _sha256_bytes(data)


def _write_json_once(path: Path, payload: Mapping[str, Any]) -> str:
    body = dict(payload)
    envelope = {
        "schema": LIFECYCLE_SCHEMA,
        "payload_sha256": canonical_sha256(body),
        "payload": body,
    }
    return _atomic_write_once(path, canonical_json_bytes(envelope))


def _read_json_exact(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        envelope = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrityError("lifecycle object is not canonical JSON") from exc
    if canonical_json_bytes(envelope) != raw or envelope.get("schema") != LIFECYCLE_SCHEMA:
        raise IntegrityError("lifecycle envelope changed")
    payload = envelope.get("payload")
    if not isinstance(payload, dict) or envelope.get("payload_sha256") != canonical_sha256(payload):
        raise IntegrityError("lifecycle payload digest mismatch")
    return payload


@dataclass(frozen=True)
class BlindedSeedFrontier:
    seed_block_index: int
    generation: int
    completed_updates: int
    completed_origin_count: int
    completed_origin_set_sha256: str
    coordinate_manifest_sha256: str
    source_binding_sha256: str
    evaluable: bool = False
    continuation_identity_sha256: str | None = None
    lineage_sha256: str | None = None
    predecessor_source_binding_sha256: str | None = None
    cut_generation: int | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.seed_block_index < 24 or self.generation < 0:
            raise IntegrityError("frontier seed/generation is invalid")
        if not 0 <= self.completed_updates <= 512:
            raise IntegrityError("frontier update count is invalid")
        expected = self.completed_updates * 384
        if self.completed_origin_count != expected or self.completed_origin_count > EXPECTED_ORIGINS_PER_SEED:
            raise IntegrityError("frontier origin count is not an atomic update boundary")
        _require_sha256("completed_origin_set_sha256", self.completed_origin_set_sha256)
        _require_sha256("coordinate_manifest_sha256", self.coordinate_manifest_sha256)
        _require_sha256("source_binding_sha256", self.source_binding_sha256)
        if self.evaluable is not False:
            raise IntegrityError("a per-seed frontier is never evaluable")
        provenance = (
            self.continuation_identity_sha256,
            self.lineage_sha256,
            self.predecessor_source_binding_sha256,
            self.cut_generation,
        )
        if any(value is not None for value in provenance):
            if not all(value is not None for value in provenance):
                raise IntegrityError("continuation frontier provenance is partial")
            for name in (
                "continuation_identity_sha256",
                "lineage_sha256",
                "predecessor_source_binding_sha256",
            ):
                _require_sha256(name, getattr(self, name))
            if self.cut_generation != 154 or self.source_binding_sha256 == self.predecessor_source_binding_sha256:
                raise IntegrityError("continuation frontier source epochs or cut changed")

    def require_successor_of(self, previous: "BlindedSeedFrontier") -> None:
        if (
            self.seed_block_index != previous.seed_block_index
            or self.coordinate_manifest_sha256 != previous.coordinate_manifest_sha256
            or self.source_binding_sha256 != previous.source_binding_sha256
            or self.generation != previous.generation + 1
            or self.completed_updates < previous.completed_updates
        ):
            raise IntegrityError("frontier is not an exact atomic resume successor")
        if self.completed_updates == previous.completed_updates and self.completed_origin_set_sha256 != previous.completed_origin_set_sha256:
            raise IntegrityError("frontier replaced work without advancing")

    def require_lineage_successor_of(
        self,
        previous: "BlindedSeedFrontier",
        *,
        continuation_identity_sha256: str,
        lineage_sha256: str,
        predecessor_source_binding_sha256: str,
    ) -> None:
        """Admit the one source-changing edge without relaxing ordinary restore."""

        if (
            previous.generation != 154
            or previous.completed_updates != 154
            or self.seed_block_index != previous.seed_block_index
            or self.coordinate_manifest_sha256 != previous.coordinate_manifest_sha256
            or self.completed_updates < previous.completed_updates
            or self.generation != previous.generation + 1
            or self.continuation_identity_sha256 != continuation_identity_sha256
            or self.lineage_sha256 != lineage_sha256
            or self.predecessor_source_binding_sha256 != predecessor_source_binding_sha256
            or previous.source_binding_sha256 != predecessor_source_binding_sha256
            or self.cut_generation != 154
            or self.source_binding_sha256 == previous.source_binding_sha256
        ):
            raise IntegrityError("frontier is not the exact one-time lineage successor")


@dataclass(frozen=True)
class Update512CheckpointRef:
    seed_block_index: int
    checkpoint_sha256: str
    byte_count: int
    coordinate_manifest_sha256: str
    source_binding_sha256: str
    update: int = 512
    continuation_identity_sha256: str | None = None
    lineage_sha256: str | None = None
    predecessor_source_binding_sha256: str | None = None
    cut_generation: int | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.seed_block_index < 24 or self.update != 512 or self.byte_count <= 0:
            raise IntegrityError("checkpoint reference is not one complete update-512 seed")
        for name in ("checkpoint_sha256", "coordinate_manifest_sha256", "source_binding_sha256"):
            _require_sha256(name, getattr(self, name))
        provenance = (
            self.continuation_identity_sha256,
            self.lineage_sha256,
            self.predecessor_source_binding_sha256,
            self.cut_generation,
        )
        if any(value is not None for value in provenance):
            if not all(value is not None for value in provenance) or self.cut_generation != 154:
                raise IntegrityError("checkpoint continuation provenance is partial or changed")
            for name in (
                "continuation_identity_sha256",
                "lineage_sha256",
                "predecessor_source_binding_sha256",
            ):
                _require_sha256(name, getattr(self, name))
            if self.predecessor_source_binding_sha256 == self.source_binding_sha256:
                raise IntegrityError("checkpoint source epochs are aliased")


@dataclass(frozen=True)
class SealedSeedResultRef:
    seed_block_index: int
    payload_sha256: str
    byte_count: int
    quantity_names_sha256: str
    structurally_valid: bool
    partial_evaluable: bool = False
    continuation_identity_sha256: str | None = None
    lineage_sha256: str | None = None
    source_epoch_provenance: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.seed_block_index < 24 or self.byte_count <= 0:
            raise IntegrityError("sealed seed result reference is invalid")
        _require_sha256("payload_sha256", self.payload_sha256)
        _require_sha256("quantity_names_sha256", self.quantity_names_sha256)
        if self.structurally_valid is not True or self.partial_evaluable is not False:
            raise IntegrityError("sealed seed result is invalid or partially evaluable")
        if (self.continuation_identity_sha256 is None) != (self.lineage_sha256 is None):
            raise IntegrityError("sealed result continuation provenance is partial")
        for name in ("continuation_identity_sha256", "lineage_sha256"):
            value = getattr(self, name)
            if value is not None:
                _require_sha256(name, value)
        if self.continuation_identity_sha256 is None:
            if self.source_epoch_provenance is not None:
                raise IntegrityError("ordinary sealed result acquired continuation provenance")
        else:
            if self.source_epoch_provenance is None:
                raise IntegrityError("sealed result lacks the full source-epoch tuple")
            try:
                provenance = validate_source_epoch_provenance(self.source_epoch_provenance)
            except ContinuationLineageError as exc:
                raise IntegrityError(str(exc)) from exc
            if (
                provenance["continuation_identity_sha256"] != self.continuation_identity_sha256
                or provenance["lineage_sha256"] != self.lineage_sha256
            ):
                raise IntegrityError("sealed result source-epoch cross-digest changed")


@dataclass(frozen=True)
class NonValueConformanceDiagnostic:
    """A bounded failure receipt that cannot carry an action, value, or result."""

    seed_block_index: int
    attempted_update_index: int
    completed_updates: int
    leaf_identifiers: tuple[str, ...]
    leaf_passed: Mapping[str, bool]
    max_probability_abs_error: float
    generation_advanced: bool = False
    evaluable: bool = False
    schema: str = "SGSP_RSCF_R01_NONVALUE_CONFORMANCE_DIAGNOSTIC_V1"

    def __post_init__(self) -> None:
        allowed = {
            "Q_TARGET_DETACHED",
            "PRIVATE_TARGET_ISOLATED",
            "TORCH_NATIVE_ACTION_IDENTITY",
            "TORCH_NATIVE_PROBABILITY_TOLERANCE",
        }
        if (
            not 0 <= self.seed_block_index < 24
            or not 0 <= self.attempted_update_index < 512
            or self.completed_updates != self.attempted_update_index
            or set(self.leaf_identifiers) - allowed
            or set(self.leaf_passed) != set(self.leaf_identifiers)
            or any(type(value) is not bool for value in self.leaf_passed.values())
            or not math.isfinite(self.max_probability_abs_error)
            or not 0.0 <= self.max_probability_abs_error <= 1.0
            or self.generation_advanced is not False
            or self.evaluable is not False
        ):
            raise IntegrityError("non-value conformance diagnostic is invalid")


class ProductionLifecycleStore:
    """Write-only partial lifecycle and one strict complete-panel publication."""

    def __init__(
        self,
        lease: ValidatedRootLease,
        coordinates: EmpiricalCoordinateAdapter,
        *,
        source_epoch_provenance: Mapping[str, Any] | None = None,
    ) -> None:
        if coordinates._lease_lineage_id != lease.lease_lineage_id:
            raise IntegrityError("store coordinate plan is outside the validated lease lineage")
        self.root = lease.retained_root
        self.lease = lease
        self.coordinates = coordinates
        self.source_epoch_provenance = (
            None if source_epoch_provenance is None else dict(source_epoch_provenance)
        )
        if self.source_epoch_provenance is not None:
            try:
                self.source_epoch_provenance = validate_source_epoch_provenance(
                    self.source_epoch_provenance
                )
            except ContinuationLineageError as exc:
                raise IntegrityError(str(exc)) from exc
            if (
                self.source_epoch_provenance["continuation_source_binding_sha256"]
                != lease.source_binding.digest
            ):
                raise IntegrityError("lifecycle continuation source differs from its lease")

    def _provenance_fields(self) -> dict[str, Any]:
        if self.source_epoch_provenance is None:
            return {
                "continuation_identity_sha256": None,
                "lineage_sha256": None,
                "predecessor_source_binding_sha256": None,
                "cut_generation": None,
            }
        return {
            "continuation_identity_sha256": self.source_epoch_provenance["continuation_identity_sha256"],
            "lineage_sha256": self.source_epoch_provenance["lineage_sha256"],
            "predecessor_source_binding_sha256": self.source_epoch_provenance["predecessor_source_binding_sha256"],
            "cut_generation": self.source_epoch_provenance["cut_generation"],
        }

    def retained_bytes(self) -> int:
        if not self.root.exists():
            return 0
        return sum(path.stat().st_size for path in self.root.rglob("*") if path.is_file())

    def _guard_storage(self, additional_bytes: int) -> None:
        if additional_bytes < 0:
            raise IntegrityError("storage guard received a negative write size")
        retained = self.retained_bytes()
        if retained + additional_bytes > RETAINED_STORAGE_CEILING_BYTES:
            raise IntegrityError("retained-root byte ceiling would be exceeded")
        probe = self.root
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        free = shutil.disk_usage(probe).free
        if free - additional_bytes < RETAINED_STORAGE_CEILING_BYTES:
            raise IntegrityError("retained volume would lose the reserved free-space envelope")

    def write_frontier(self, frontier: BlindedSeedFrontier) -> str:
        if frontier.coordinate_manifest_sha256 != self.coordinates.manifest_sha256:
            raise IntegrityError("frontier coordinate identity mismatch")
        if frontier.source_binding_sha256 != self.lease.source_binding.digest:
            raise IntegrityError("frontier source identity mismatch")
        if {
            "continuation_identity_sha256": frontier.continuation_identity_sha256,
            "lineage_sha256": frontier.lineage_sha256,
            "predecessor_source_binding_sha256": frontier.predecessor_source_binding_sha256,
            "cut_generation": frontier.cut_generation,
        } != self._provenance_fields():
            raise IntegrityError("frontier continuation provenance differs from its lifecycle")
        path = self.root / "frontier" / f"SB{frontier.seed_block_index:02d}" / f"g{frontier.generation:06d}.json"
        if path.exists():
            observed = self.read_frontier(frontier.seed_block_index, frontier.generation)
            if observed != frontier:
                raise IntegrityError("existing frontier differs from the exact resume generation")
            return _sha256_file(path)
        self._guard_storage(4096)
        return _write_json_once(path, {"kind": "BLINDED_NON_EVALUABLE_SEED_FRONTIER", **asdict(frontier)})

    def read_frontier(self, seed_block_index: int, generation: int) -> BlindedSeedFrontier:
        payload = _read_json_exact(self.root / "frontier" / f"SB{seed_block_index:02d}" / f"g{generation:06d}.json")
        if payload.pop("kind", None) != "BLINDED_NON_EVALUABLE_SEED_FRONTIER":
            raise IntegrityError("frontier kind changed")
        return BlindedSeedFrontier(**payload)

    def install_update512_checkpoint(self, seed_block_index: int, data: bytes, frontier: BlindedSeedFrontier) -> Update512CheckpointRef:
        if frontier.seed_block_index != seed_block_index or frontier.completed_updates != 512:
            raise IntegrityError("checkpoint requires this seed's complete update-512 frontier")
        digest = _sha256_bytes(data)
        directory = self.root / "checkpoint" / f"SB{seed_block_index:02d}"
        path = directory / f"{digest}.pt"
        if path.exists() and path.read_bytes() != data:
            raise IntegrityError("checkpoint content-address collision")
        if not path.exists():
            self._guard_storage(2 * len(data))
            _atomic_write_once(path, data)
        ref = Update512CheckpointRef(
            seed_block_index,
            digest,
            len(data),
            self.coordinates.manifest_sha256,
            self.lease.source_binding.digest,
            **self._provenance_fields(),
        )
        metadata_path = directory / f"{digest}.json"
        metadata = {"kind": "SOLE_UPDATE_512_CHECKPOINT", **asdict(ref)}
        if metadata_path.exists():
            if _read_json_exact(metadata_path) != metadata:
                raise IntegrityError("checkpoint metadata differs from its content address")
        else:
            self._guard_storage(8192)
            _write_json_once(metadata_path, metadata)
        commit_path = directory / "COMMITTED.json"
        commit = {
            "kind": "ATOMIC_UPDATE512_CHECKPOINT_COMMIT",
            "seed_block_index": seed_block_index,
            "checkpoint_sha256": digest,
            "metadata_sha256": _sha256_file(metadata_path),
            "frontier_sha256": canonical_sha256(asdict(frontier)),
        }
        if commit_path.exists():
            observed = _read_json_exact(commit_path)
            if observed != commit:
                raise IntegrityError("committed update-512 checkpoint differs from resumed state")
        else:
            self._guard_storage(8192)
            _write_json_once(commit_path, commit)
        return self.read_update512_checkpoint_ref(seed_block_index)

    def _require_immutable_predecessor_cut(self) -> None:
        """Pin A's four generation-154 objects while B advances."""

        provenance = self.source_epoch_provenance
        if provenance is None:
            return
        seed = int(provenance["cut_seed_block_index"])
        generation = int(provenance["cut_generation"])
        directory = self.root / "resume" / f"SB{seed:02d}"
        commit_path = directory / f"g{generation:06d}.commit"
        frontier_path = self.root / "frontier" / f"SB{seed:02d}" / f"g{generation:06d}.json"
        try:
            commit_bytes = commit_path.read_bytes()
            commit = json.loads(commit_bytes.decode("ascii"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntegrityError("immutable predecessor cut commit is absent or invalid") from exc
        if (
            canonical_json_bytes(commit) != commit_bytes
            or _sha256_bytes(commit_bytes) != provenance["cut_resume_commit_sha256"]
            or _sha256_file(frontier_path) != provenance["cut_frontier_sha256"]
            or commit.get("seed_block_index") != seed
            or commit.get("generation") != generation
        ):
            raise IntegrityError("immutable predecessor cut commit/frontier changed")
        state_path = directory / str(commit.get("state_name"))
        metadata_path = directory / str(commit.get("metadata_name"))
        if (
            state_path.parent != directory
            or metadata_path.parent != directory
            or _sha256_file(state_path) != provenance["cut_resume_state_sha256"]
            or _sha256_file(metadata_path) != provenance["cut_resume_metadata_sha256"]
        ):
            raise IntegrityError("immutable predecessor cut state/metadata changed")

    def write_resume_state(self, seed_block_index: int, generation: int, data: bytes, frontier: BlindedSeedFrontier) -> str:
        if (
            frontier.seed_block_index != seed_block_index
            or frontier.generation != generation
            or frontier.evaluable
            or frontier.coordinate_manifest_sha256 != self.coordinates.manifest_sha256
        ):
            raise IntegrityError("resume image/frontier identity mismatch")
        self._require_immutable_predecessor_cut()
        digest = _sha256_bytes(data)
        directory = self.root / "resume" / f"SB{seed_block_index:02d}"
        state_path = directory / f"g{generation:06d}-{digest}.pt"
        if state_path.exists() and state_path.read_bytes() != data:
            raise IntegrityError("resume content-address collision")
        if not state_path.exists():
            self._guard_storage(2 * len(data))
            _atomic_write_once(state_path, data)
        metadata = {
            "kind": "BLINDED_NON_EVALUABLE_RESUME_STATE",
            "seed_block_index": seed_block_index,
            "generation": generation,
            "state_sha256": digest,
            "byte_count": len(data),
            "frontier_sha256": canonical_sha256(asdict(frontier)),
            "evaluable": False,
        }
        metadata_path = directory / f"g{generation:06d}-{digest}.json"
        if metadata_path.exists():
            observed = json.loads(metadata_path.read_text(encoding="ascii"))
            if canonical_json_bytes(observed) != metadata_path.read_bytes() or observed != metadata:
                raise IntegrityError("resume metadata differs from its content address")
        else:
            self._guard_storage(8192)
            _atomic_write_once(metadata_path, canonical_json_bytes(metadata))
        commit_path = directory / f"g{generation:06d}.commit"
        commit = {
            "kind": "ATOMIC_RESUME_GENERATION_COMMIT",
            "seed_block_index": seed_block_index,
            "generation": generation,
            "state_sha256": digest,
            "state_name": state_path.name,
            "metadata_name": metadata_path.name,
            "metadata_sha256": _sha256_file(metadata_path),
            "frontier_sha256": canonical_sha256(asdict(frontier)),
        }
        if commit_path.exists():
            observed_commit = json.loads(commit_path.read_text(encoding="ascii"))
            if canonical_json_bytes(observed_commit) != commit_path.read_bytes() or observed_commit != commit:
                raise IntegrityError("resume generation was already committed to different state")
        else:
            self._guard_storage(8192)
            _atomic_write_once(commit_path, canonical_json_bytes(commit))
        self._require_immutable_predecessor_cut()
        # The new generation is fully committed.  Retain it and one immediate
        # rollback generation; older state/metadata/commit triples are now
        # redundant, except the separately hashed generation-154 A cut.  Its
        # four byte objects remain immutable for the entire B epoch.  Blinded
        # frontier JSON remains append-only.
        for old_commit_path in sorted(directory.glob("g*.commit")):
            try:
                old_generation = int(old_commit_path.stem[1:])
            except ValueError as exc:
                raise IntegrityError("resume commit marker name is invalid") from exc
            if old_generation >= generation - 1:
                continue
            if (
                self.source_epoch_provenance is not None
                and seed_block_index == self.source_epoch_provenance["cut_seed_block_index"]
                and old_generation == self.source_epoch_provenance["cut_generation"]
            ):
                continue
            old_commit = json.loads(old_commit_path.read_text(encoding="ascii"))
            for name in (old_commit.get("state_name"), old_commit.get("metadata_name")):
                candidate = directory / str(name)
                if candidate.parent != directory or not candidate.name.startswith(f"g{old_generation:06d}-"):
                    raise IntegrityError("old resume cleanup target escaped its generation")
                candidate.unlink(missing_ok=True)
            old_commit_path.unlink(missing_ok=True)
        self._require_immutable_predecessor_cut()
        return digest

    def read_resume_state(self, seed_block_index: int, frontier: BlindedSeedFrontier) -> bytes:
        directory = self.root / "resume" / f"SB{seed_block_index:02d}"
        commit_path = directory / f"g{frontier.generation:06d}.commit"
        try:
            commit = json.loads(commit_path.read_text(encoding="ascii"))
        except (OSError, json.JSONDecodeError) as exc:
            raise IntegrityError("resume commit marker is absent or invalid") from exc
        if canonical_json_bytes(commit) != commit_path.read_bytes():
            raise IntegrityError("resume commit marker is noncanonical")
        state_path = directory / str(commit.get("state_name"))
        metadata_path = directory / str(commit.get("metadata_name"))
        try:
            metadata = json.loads(metadata_path.read_text(encoding="ascii"))
        except (OSError, json.JSONDecodeError) as exc:
            raise IntegrityError("committed resume metadata is absent or invalid") from exc
        if canonical_json_bytes(metadata) != metadata_path.read_bytes() or commit.get("metadata_sha256") != _sha256_file(metadata_path):
            raise IntegrityError("committed resume metadata changed")
        data = state_path.read_bytes()
        if (
            commit.get("kind") != "ATOMIC_RESUME_GENERATION_COMMIT"
            or commit.get("seed_block_index") != seed_block_index
            or commit.get("generation") != frontier.generation
            or commit.get("frontier_sha256") != canonical_sha256(asdict(frontier))
            or
            metadata.get("kind") != "BLINDED_NON_EVALUABLE_RESUME_STATE"
            or metadata.get("seed_block_index") != seed_block_index
            or metadata.get("generation") != frontier.generation
            or metadata.get("state_sha256") != _sha256_bytes(data)
            or commit.get("state_sha256") != metadata.get("state_sha256")
            or metadata.get("frontier_sha256") != canonical_sha256(asdict(frontier))
            or metadata.get("evaluable") is not False
        ):
            raise IntegrityError("resume state does not match the atomic frontier")
        return data

    def latest_resume_frontier(self, seed_block_index: int) -> BlindedSeedFrontier | None:
        directory = self.root / "resume" / f"SB{seed_block_index:02d}"
        commits = sorted(directory.glob("g*.commit")) if directory.exists() else []
        if not commits:
            return None
        try:
            generation = int(commits[-1].stem[1:])
        except ValueError as exc:
            raise IntegrityError("resume commit marker name is invalid") from exc
        frontier = self.read_frontier(seed_block_index, generation)
        self.read_resume_state(seed_block_index, frontier)
        return frontier

    def read_update512_checkpoint_ref(self, seed_block_index: int) -> Update512CheckpointRef:
        directory = self.root / "checkpoint" / f"SB{seed_block_index:02d}"
        commit = _read_json_exact(directory / "COMMITTED.json")
        if commit.get("kind") != "ATOMIC_UPDATE512_CHECKPOINT_COMMIT" or commit.get("seed_block_index") != seed_block_index:
            raise IntegrityError("checkpoint commit marker changed")
        digest = str(commit.get("checkpoint_sha256"))
        metadata_path = directory / f"{digest}.json"
        if commit.get("metadata_sha256") != _sha256_file(metadata_path):
            raise IntegrityError("checkpoint committed metadata changed")
        payload = _read_json_exact(metadata_path)
        if payload.pop("kind", None) != "SOLE_UPDATE_512_CHECKPOINT":
            raise IntegrityError("checkpoint reference kind changed")
        reference = Update512CheckpointRef(**payload)
        checkpoint_path = directory / f"{digest}.pt"
        data = checkpoint_path.read_bytes()
        if _sha256_bytes(data) != reference.checkpoint_sha256 or len(data) != reference.byte_count:
            raise IntegrityError("update-512 checkpoint bytes changed")
        return reference

    @staticmethod
    def _seed_result_keystream(master: BoundEmpiricalMaster, seed_block_index: int, length: int) -> bytes:
        result = bytearray()
        counter = 0
        while len(result) < length:
            result.extend(hmac.new(
                master._secret,
                f"SGSP_RSCF_R01_SEALED_RESULT|{seed_block_index:02d}|{counter}".encode("ascii"),
                hashlib.sha256,
            ).digest())
            counter += 1
        return bytes(result[:length])

    def install_sealed_seed_result(
        self,
        seed_block_index: int,
        payload: Mapping[str, Any],
        master: BoundEmpiricalMaster,
    ) -> SealedSeedResultRef:
        if master.lease_lineage_id != self.lease.lease_lineage_id:
            raise IntegrityError("sealed seed result master belongs to another lease lineage")
        if not 0 <= seed_block_index < 24 or payload.get("seed_block_index") != seed_block_index:
            raise IntegrityError("sealed seed result identity mismatch")
        vector = payload.get("quantity_vector")
        values = vector.get("values") if isinstance(vector, Mapping) else None
        if not isinstance(values, Mapping) or set(values) != set(QUANTITY_NAMES):
            raise IntegrityError("sealed seed result lacks the exact 28-quantity family")
        plaintext = canonical_json_bytes(payload)
        stream = self._seed_result_keystream(master, seed_block_index, len(plaintext))
        ciphertext = bytes(left ^ right for left, right in zip(plaintext, stream))
        path = self.root / "sealed" / f"SB{seed_block_index:02d}.bin"
        ciphertext_sha256 = _sha256_bytes(ciphertext)
        quantity_names_sha256 = canonical_sha256(list(QUANTITY_NAMES))
        manifest_core = {
            "kind": "AUTHENTICATED_NON_EVALUABLE_SEED_RESULT",
            "lease_lineage_id": self.lease.lease_lineage_id,
            "seed_block_index": seed_block_index,
            "ciphertext_sha256": ciphertext_sha256,
            "byte_count": len(ciphertext),
            "quantity_names_sha256": quantity_names_sha256,
            "structurally_valid": True,
            "partial_evaluable": False,
            "continuation_identity_sha256": (
                None if self.source_epoch_provenance is None
                else self.source_epoch_provenance["continuation_identity_sha256"]
            ),
            "lineage_sha256": (
                None if self.source_epoch_provenance is None
                else self.source_epoch_provenance["lineage_sha256"]
            ),
            "source_epoch_provenance": self.source_epoch_provenance,
        }
        authentication_key = hmac.new(
            master._secret,
            f"SGSP_RSCF_R01_SEED_RESULT_AUTH_KEY|{self.lease.lease_lineage_id}|{seed_block_index:02d}".encode("ascii"),
            hashlib.sha256,
        ).digest()
        manifest = {
            **manifest_core,
            "authentication_hmac_sha256": hmac.new(
                authentication_key, canonical_json_bytes(manifest_core), hashlib.sha256
            ).hexdigest(),
        }
        if path.exists():
            existing = path.read_bytes()
            if existing != ciphertext:
                raise IntegrityError("existing sealed seed result differs from resumed completion")
        else:
            self._guard_storage(2 * len(ciphertext))
            _atomic_write_once(path, ciphertext)
        manifest_path = path.with_suffix(".json")
        if manifest_path.exists():
            if _read_json_exact(manifest_path) != manifest:
                raise IntegrityError("existing seed-result authentication manifest changed")
        else:
            self._guard_storage(8192)
            _write_json_once(manifest_path, manifest)
        return self.read_sealed_seed_result_ref(seed_block_index, master)

    def read_sealed_seed_result_ref(
        self,
        seed_block_index: int,
        master: BoundEmpiricalMaster,
    ) -> SealedSeedResultRef:
        if master.lease_lineage_id != self.lease.lease_lineage_id:
            raise IntegrityError("seed-result authenticator belongs to another lease lineage")
        path = self.root / "sealed" / f"SB{seed_block_index:02d}.bin"
        manifest = _read_json_exact(path.with_suffix(".json"))
        required = {
            "kind", "lease_lineage_id", "seed_block_index",
            "ciphertext_sha256", "byte_count", "quantity_names_sha256",
            "structurally_valid", "partial_evaluable",
            "authentication_hmac_sha256",
            "continuation_identity_sha256", "lineage_sha256",
            "source_epoch_provenance",
        }
        if set(manifest) != required:
            raise IntegrityError("seed-result authentication manifest field inventory changed")
        tag = manifest.pop("authentication_hmac_sha256")
        if (
            manifest.get("kind") != "AUTHENTICATED_NON_EVALUABLE_SEED_RESULT"
            or manifest.get("lease_lineage_id") != self.lease.lease_lineage_id
            or manifest.get("seed_block_index") != seed_block_index
            or manifest.get("quantity_names_sha256") != canonical_sha256(list(QUANTITY_NAMES))
            or manifest.get("source_epoch_provenance") != self.source_epoch_provenance
        ):
            raise IntegrityError("seed-result authentication identity changed")
        authentication_key = hmac.new(
            master._secret,
            f"SGSP_RSCF_R01_SEED_RESULT_AUTH_KEY|{self.lease.lease_lineage_id}|{seed_block_index:02d}".encode("ascii"),
            hashlib.sha256,
        ).digest()
        expected_tag = hmac.new(
            authentication_key, canonical_json_bytes(manifest), hashlib.sha256
        ).hexdigest()
        if not isinstance(tag, str) or not hmac.compare_digest(tag, expected_tag):
            raise IntegrityError("seed-result authentication HMAC mismatch")
        ciphertext = path.read_bytes()
        if (
            _sha256_bytes(ciphertext) != manifest["ciphertext_sha256"]
            or len(ciphertext) != manifest["byte_count"]
        ):
            raise IntegrityError("authenticated seed-result ciphertext changed")
        return SealedSeedResultRef(
            seed_block_index=seed_block_index,
            payload_sha256=str(manifest["ciphertext_sha256"]),
            byte_count=int(manifest["byte_count"]),
            quantity_names_sha256=str(manifest["quantity_names_sha256"]),
            structurally_valid=bool(manifest["structurally_valid"]),
            partial_evaluable=bool(manifest["partial_evaluable"]),
            continuation_identity_sha256=(
                None if manifest["continuation_identity_sha256"] is None
                else str(manifest["continuation_identity_sha256"])
            ),
            lineage_sha256=(
                None if manifest["lineage_sha256"] is None
                else str(manifest["lineage_sha256"])
            ),
            source_epoch_provenance=manifest["source_epoch_provenance"],
        )

    def write_nonvalue_conformance_diagnostic(
        self, diagnostic: NonValueConformanceDiagnostic
    ) -> str:
        """Write one non-evaluable receipt without creating any next generation."""

        if diagnostic.completed_updates != diagnostic.attempted_update_index:
            raise IntegrityError("diagnostic is not bound to the failed attempted update")
        path = (
            self.root
            / "diagnostic"
            / f"SB{diagnostic.seed_block_index:02d}"
            / f"u{diagnostic.attempted_update_index:06d}.json"
        )
        return _write_json_once(path, {
            "kind": "BLINDED_NONVALUE_CONFORMANCE_DIAGNOSTIC",
            **asdict(diagnostic),
        })

    def read_nonvalue_conformance_diagnostic(
        self, seed_block_index: int, attempted_update_index: int
    ) -> NonValueConformanceDiagnostic:
        payload = _read_json_exact(
            self.root
            / "diagnostic"
            / f"SB{seed_block_index:02d}"
            / f"u{attempted_update_index:06d}.json"
        )
        if payload.pop("kind", None) != "BLINDED_NONVALUE_CONFORMANCE_DIAGNOSTIC":
            raise IntegrityError("diagnostic kind changed")
        payload["leaf_identifiers"] = tuple(payload["leaf_identifiers"])
        return NonValueConformanceDiagnostic(**payload)

    def read_sealed_seed_result(
        self,
        reference: SealedSeedResultRef,
        master: BoundEmpiricalMaster,
    ) -> dict[str, Any]:
        authenticated_reference = self.read_sealed_seed_result_ref(
            reference.seed_block_index, master
        )
        if authenticated_reference != reference:
            raise IntegrityError("caller seed-result reference differs from authenticated manifest")
        path = self.root / "sealed" / f"SB{reference.seed_block_index:02d}.bin"
        ciphertext = path.read_bytes()
        if _sha256_bytes(ciphertext) != reference.payload_sha256 or len(ciphertext) != reference.byte_count:
            raise IntegrityError("sealed seed result ciphertext changed")
        stream = self._seed_result_keystream(master, reference.seed_block_index, len(ciphertext))
        plaintext = bytes(left ^ right for left, right in zip(ciphertext, stream))
        try:
            payload = json.loads(plaintext.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntegrityError("sealed seed result cannot be opened") from exc
        if canonical_json_bytes(payload) != plaintext:
            raise IntegrityError("sealed seed result plaintext is noncanonical")
        return payload

    def install_complete_result(
        self,
        complete_payload: Mapping[str, Any],
        *,
        checkpoints: Sequence[Update512CheckpointRef],
        seed_results: Sequence[SealedSeedResultRef],
        master: BoundEmpiricalMaster,
    ) -> str:
        expected_indices = set(range(24))
        if {item.seed_block_index for item in checkpoints} != expected_indices or len(checkpoints) != 24:
            raise IntegrityError("complete result requires exactly one update-512 checkpoint per seed")
        if {item.seed_block_index for item in seed_results} != expected_indices or len(seed_results) != 24:
            raise IntegrityError("complete result requires exactly one sealed result per seed")
        quantity_digest = canonical_sha256(list(QUANTITY_NAMES))
        for checkpoint in checkpoints:
            if checkpoint.update != 512 or checkpoint.coordinate_manifest_sha256 != self.coordinates.manifest_sha256 or checkpoint.source_binding_sha256 != self.lease.source_binding.digest:
                raise IntegrityError("checkpoint inventory is not exact")
            if {
                "continuation_identity_sha256": checkpoint.continuation_identity_sha256,
                "lineage_sha256": checkpoint.lineage_sha256,
                "predecessor_source_binding_sha256": checkpoint.predecessor_source_binding_sha256,
                "cut_generation": checkpoint.cut_generation,
            } != self._provenance_fields():
                raise IntegrityError("checkpoint source-epoch provenance changed")
        for result in seed_results:
            if not result.structurally_valid or result.partial_evaluable or result.quantity_names_sha256 != quantity_digest:
                raise IntegrityError("seed result is incomplete, evaluable early, or has a changed 28-family")
            if self.read_sealed_seed_result_ref(result.seed_block_index, master) != result:
                raise IntegrityError("seed result reference differs from authenticated retained manifest")
            if result.source_epoch_provenance != self.source_epoch_provenance:
                raise IntegrityError("seed result full source-epoch provenance changed")
        if set(complete_payload) != {"kind", "science_revision", "seed_rows", "analysis"}:
            raise IntegrityError("complete result payload field inventory is not exact")
        if complete_payload["kind"] != "ATOMIC_COMPLETE_24_SEED_PANEL" or complete_payload["science_revision"] != SCIENCE_REVISION:
            raise IntegrityError("complete result identity changed")
        rows = complete_payload["seed_rows"]
        if not isinstance(rows, list) or len(rows) != 24 or {row.get("seed_block_index") for row in rows if isinstance(row, dict)} != expected_indices:
            raise IntegrityError("complete result does not contain exactly 24 seed rows")
        if any(set(row.get("quantities", {})) != set(QUANTITY_NAMES) for row in rows):
            raise IntegrityError("complete seed row does not contain the exact 28 quantities")
        envelope = {
            "kind": "ATOMIC_COMPLETE_EVALUABLE_PANEL",
            "evaluable": True,
            "lease_lineage_id": self.lease.lease_lineage_id,
            "coordinate_manifest_sha256": self.coordinates.manifest_sha256,
            "source_binding_sha256": self.lease.source_binding.digest,
            "source_epoch_provenance": self.source_epoch_provenance,
            "checkpoint_refs": [asdict(item) for item in sorted(checkpoints, key=lambda item: item.seed_block_index)],
            "seed_result_refs": [asdict(item) for item in sorted(seed_results, key=lambda item: item.seed_block_index)],
            "complete_payload": complete_payload,
        }
        path = self.root / "complete" / "SGSP_RG2Z_RSCF_R01_PANEL.json"
        if path.exists():
            if _read_json_exact(path) != envelope:
                raise IntegrityError("existing complete panel differs from exact resumed completion")
            return _sha256_file(path)
        self._guard_storage(2 * len(canonical_json_bytes(envelope)) + 8192)
        return _write_json_once(path, envelope)


@dataclass(frozen=True)
class SealedPreflightReport:
    schema: str
    source_binding_sha256: str
    exact_launch_module: str
    width: int
    outer_workers: int
    native_threads: int
    coordinate_count: int
    seed_block_count: int
    arm_independent: bool
    atomic_resume_validated: bool
    write_once_conflict_validated: bool
    retained_probe_bytes: int
    resume_generation_bytes: int
    update512_checkpoint_bytes: int
    projected_complete_retained_bytes: int
    lifecycle_io_wall_seconds: float
    lifecycle_io_cpu_seconds: float
    retained_storage_ceiling_bytes: int
    storage_headroom_valid: bool
    available_storage_bytes: int
    wall_seconds: float
    process_cpu_seconds: float
    peak_rss_bytes: int | None
    empirical_objects_created: int
    probe_cleanup_complete: bool


def _working_set_bytes() -> int | None:
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(Counters),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        if psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return int(counters.WorkingSetSize)
    except (AttributeError, OSError):
        return None
    return None


def run_sealed_test_preflight(root: Path | str) -> SealedPreflightReport:
    """Validate launch-boundary mechanics without a lease or empirical object."""

    preflight_root = Path(root).resolve(strict=True)
    before = {item.name for item in preflight_root.iterdir()}
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    rss_before = _working_set_bytes()
    binding = current_exact_source_binding(load_native=True)
    test_secret = hashlib.sha256(b"TEST_ONLY|SGSP_RSCF_R01|SEALED_PREFLIGHT").digest()
    # Exercise the exact counter-address form with a TEST-only namespace.  No
    # ProductionMaster, ValidatedRootLease, empirical coordinate or model exists.
    keys = []
    for roster in TRAIN_ROSTERS:
        for pair in range(PAIRS_PER_TRAIN_ROSTER):
            for role in range(3):
                common = {"schema": COORDINATE_SCHEMA, "namespace": "TEST_ONLY|SGSP-RSCF-PREFLIGHT", "seed": "TEST_BLOCK", "phase": "TEST", "update": 0, "roster": roster, "pair": pair, "role": role}
                base = _uniform_below(test_secret, {**common, "kind": "base_slot"}, 12)
                for side in (0, 1):
                    local = _uniform_below(test_secret, {**common, "side": side, "kind": "local_index"}, roster // 3)
                    keys.append(canonical_sha256({**common, "side": side, "slot": base if side == 0 else 11 - base, "local": local}))
    if len(keys) != 192 or len(set(keys)) != 192:
        raise IntegrityError("sealed preflight coordinate inventory is not exact or arm-independent")

    probe_bytes = 0
    resume_generation_bytes = 0
    update512_checkpoint_bytes = 0
    lifecycle_io_wall_seconds = 0.0
    lifecycle_io_cpu_seconds = 0.0
    conflict = False
    with tempfile.TemporaryDirectory(prefix="TEST_ONLY_SGSP_RSCF_PREFLIGHT_", dir=preflight_root) as temporary_name:
        temporary = Path(temporary_name)
        first = temporary / "atomic" / "frontier.json"
        payload = {"kind": "TEST_ONLY_NON_EVALUABLE_FRONTIER", "evaluable": False, "completed": 192, "identity": canonical_sha256(keys)}
        probe_bytes += len(canonical_json_bytes(payload))
        _write_json_once(first, payload)
        observed = _read_json_exact(first)
        if observed != payload:
            raise IntegrityError("sealed preflight atomic resume readback changed")
        try:
            _write_json_once(first, payload)
        except WriteOnceConflictError:
            conflict = True
        if not conflict:
            raise IntegrityError("sealed preflight write-once conflict was not enforced")
        successor = temporary / "atomic" / "frontier-successor.json"
        successor_payload = {**payload, "completed": 384, "prior_sha256": canonical_sha256(payload)}
        probe_bytes += len(canonical_json_bytes(successor_payload))
        _write_json_once(successor, successor_payload)
        if _read_json_exact(successor).get("prior_sha256") != canonical_sha256(payload):
            raise IntegrityError("sealed preflight resume successor identity changed")
        # Full-shaped TEST-only state dictionaries: parameter and Adam tensor
        # shapes are exact, but no actor, critic, optimizer or model object is
        # instantiated and no scientific initialization value exists.
        test_arm_state: dict[str, Any] = {}
        for arm in ("TEST_PHY_SHAPE", "TEST_EDGE_SHAPE"):
            parameter_shapes = {**ACTOR_PARAMETER_SHAPES, **{f"critic.{name}": shape for name, shape in CRITIC_PARAMETER_SHAPES.items()}}
            parameters = {
                name: torch.zeros(shape, dtype=torch.float32)
                for name, shape in parameter_shapes.items()
            }
            optimizer = {
                name: {
                    "step": torch.zeros((), dtype=torch.float32),
                    "exp_avg": torch.zeros(shape, dtype=torch.float32),
                    "exp_avg_sq": torch.zeros(shape, dtype=torch.float32),
                }
                for name, shape in parameter_shapes.items()
            }
            test_arm_state[arm] = {"parameters": parameters, "adam": optimizer}
        resume_payload = {
            "schema": "TEST_ONLY_SGSP_RSCF_FULL_SHAPED_RESUME_V1",
            "arms": test_arm_state,
            "completed_updates": 1,
            "evaluable": False,
        }
        checkpoint_payload = {
            "schema": "TEST_ONLY_SGSP_RSCF_FULL_SHAPED_UPDATE512_CHECKPOINT_V1",
            "arms": test_arm_state,
            "update": 512,
            "synthetic_test_only": True,
        }
        resume_buffer = io.BytesIO()
        checkpoint_buffer = io.BytesIO()
        torch.save(resume_payload, resume_buffer)
        torch.save(checkpoint_payload, checkpoint_buffer)
        resume_data = resume_buffer.getvalue()
        checkpoint_data = checkpoint_buffer.getvalue()
        resume_generation_bytes = len(resume_data)
        update512_checkpoint_bytes = len(checkpoint_data)
        io_wall_started = time.perf_counter()
        io_cpu_started = time.process_time()
        resume_path = temporary / "full-shaped" / "TEST_ONLY_RESUME.pt"
        checkpoint_path = temporary / "full-shaped" / "TEST_ONLY_UPDATE512.pt"
        _atomic_write_once(resume_path, resume_data)
        _atomic_write_once(checkpoint_path, checkpoint_data)
        if resume_path.read_bytes() != resume_data or checkpoint_path.read_bytes() != checkpoint_data:
            raise IntegrityError("full-shaped TEST-only lifecycle serialization changed on readback")
        lifecycle_io_wall_seconds = time.perf_counter() - io_wall_started
        lifecycle_io_cpu_seconds = time.process_time() - io_cpu_started
        probe_bytes += resume_generation_bytes + update512_checkpoint_bytes
        if any(RESERVED_SCIENTIFIC_NAMESPACE.encode("ascii") in path.read_bytes() for path in temporary.rglob("*") if path.is_file()):
            raise IntegrityError("sealed preflight leaked the reserved empirical namespace")
    after = {item.name for item in preflight_root.iterdir()}
    cleanup = before == after
    if not cleanup:
        raise IntegrityError("sealed preflight did not clean its TEST-only probe directory")
    rss_after = _working_set_bytes()
    available_storage = shutil.disk_usage(preflight_root).free
    projected_retained = 2 * (
        24 * (resume_generation_bytes + update512_checkpoint_bytes)
        + 24 * 512 * 2048
        + 24 * 65_536
        + 1_048_576
    )
    return SealedPreflightReport(
        PREFLIGHT_SCHEMA,
        binding.digest,
        "experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher",
        WIDTH,
        OUTER_WORKERS,
        NATIVE_THREADS,
        EXPECTED_ARM_INDEPENDENT_ORIGINS_PANEL,
        SEED_BLOCK_COUNT,
        True,
        True,
        conflict,
        probe_bytes,
        resume_generation_bytes,
        update512_checkpoint_bytes,
        projected_retained,
        lifecycle_io_wall_seconds,
        lifecycle_io_cpu_seconds,
        RETAINED_STORAGE_CEILING_BYTES,
        projected_retained <= RETAINED_STORAGE_CEILING_BYTES and available_storage >= MINIMUM_FREE_STORAGE_BYTES,
        available_storage,
        time.perf_counter() - wall_started,
        time.process_time() - cpu_started,
        max(value for value in (rss_before, rss_after) if value is not None) if any(value is not None for value in (rss_before, rss_after)) else None,
        0,
        cleanup,
    )


def exact_future_launch_contract() -> dict[str, Any]:
    """Return the exact preflight and Root-lease production command contract."""

    return {
        "python": "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
        "module": "experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher",
        "preflight_command": "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher --preflight-only --preflight-root <TEST_ONLY_ABSOLUTE_DIRECTORY> --preflight-artifact C:/Projects/HMASD/artifacts/semantic_graphon_shared_policy/preflight/SGSP_RG2Z_RSCF_R01_<CURRENT_SOURCE_BINDING_SHA256>.json",
        "boundary_entrypoint": "validate_root_lease -> mint_or_resume_empirical_master -> EmpiricalCoordinateAdapter -> initialize_one_worker_parameters -> ProductionLifecycleStore -> ProductionSeedEngine -> ProductionPanelLauncher",
        "production_launch_command": "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher --lease <EXACT_ROOT_LEASE_JSON>",
        "production_launch_status": "IMPLEMENTED_REQUIRES_ROOT_LEASE_AND_CM_ACCEPTANCE",
        "root_lease_schema": ROOT_LEASE_SCHEMA,
        "root_lease_exact_resources": {
            "width": WIDTH,
            "outer_workers": OUTER_WORKERS,
            "cpu_cores": CPU_CORES,
            "native_threads": NATIVE_THREADS,
            "gpu": GPU,
            "process_rss_ceiling_bytes": RSS_CEILING_BYTES,
            "minimum_available_memory_bytes": MINIMUM_AVAILABLE_MEMORY_BYTES,
            "minimum_system_reserve_bytes": MINIMUM_SYSTEM_RESERVE_BYTES,
            "retained_storage_ceiling_bytes": RETAINED_STORAGE_CEILING_BYTES,
            "minimum_free_storage_bytes": MINIMUM_FREE_STORAGE_BYTES,
            "master_source": "OS_CSPRNG_256_ONE_SHOT_AFTER_LEASE_DPAPI_SEALED",
            "master_record_relative_path": "control/master.json",
            "accepted_base_projected_wall_seconds": PROJECTED_PANEL_WALL_SECONDS,
            "lease_finalization_margin_seconds": LEASE_FINALIZATION_MARGIN_SECONDS,
            "minimum_lease_remaining_rule": "ceil(projected_wall_seconds + lease_finalization_margin_seconds)",
            "production_preflight_binding": "production_preflight_sha256 from the immediately preceding sealed TEST-only extended preflight",
            "production_preflight_artifact_rule": "exact source-binding-named retained artifact plus canonical file SHA-256",
            "successor_lease_rule": "same lease_lineage_id, exact retained_root, source binding and DPAPI master commitment",
        },
        "root_lease_payload_fields": tuple(sorted(_LEASE_FIELDS)),
        "lease_required_before": ("master", "coordinates", "parameters", "frontier", "checkpoint", "result"),
        "width": 32,
        "outer_workers": 1,
        "native_threads": 1,
        "panel_seed_blocks": 24,
        "sole_checkpoint_update": 512,
        "partial_evaluable": False,
        "native_environment_rollout_fallback": None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SGSP RSCF-r01 sealed production-boundary preflight")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--preflight-root", type=Path)
    args = parser.parse_args(argv)
    if not args.preflight_only or args.preflight_root is None:
        parser.error("production execution is exposed by production_launcher --lease; this module accepts only sealed --preflight-only")
    report = run_sealed_test_preflight(args.preflight_root)
    print(canonical_json_bytes(asdict(report)).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
