"""Parent-owned spawn-process lifecycle for RCLE TBCFV r04 blocks.

This module is deliberately result blind.  A worker receives one block root,
the immutable source/coordinate identities, and one private scratch root.  It
never receives a canonical frontier or result path.  Workers publish
failure-atomic packets in their private roots; the parent validates every
packet before installing any packet in exact block order.

The production runner consumes this contract only after an exact Root-authored
request and lease bind all four private roots.  TEST-only and protocol-canary
entries exercise spawn, private checkpoint, packet validation and parent
installation without scientific coordinates or values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
from typing import Mapping, Sequence


SCIENCE_REVISION = "RCLE-TBCFV-SCIENCE-20260821-04"
EMPIRICAL_OBJECT = "RCLE-TBCFV-R04-FULL-EMPIRICAL-PANEL"
PRODUCTION_IDENTITY = "RCLE-TBCFV-R04-FULL-PANEL-20260821-01"
COORDINATE_BINDING_SHA256 = "614e4b503a258cff325284376ed8e6f5d65ac713c95a9bb4b8bfd669ad776915"
MASTER_DIGEST = "d35b0f3f3ccb33826e2d3e68d73fad086951ac1cdab7e62e0e38be41e1a626a2"

RESOURCE_SCHEMA = "RCLE_TBCFV_R04_PRIVATE_SCRATCH_PROCESS_RESOURCE_V1"
PAYLOAD_SCHEMA = "RCLE_TBCFV_R04_ONE_BLOCK_SPAWN_PAYLOAD_V1"
PACKET_SCHEMA = "RCLE_TBCFV_R04_COMPLETE_BLOCK_WORKER_PACKET_V1"
TEST_PACKET_SCHEMA = "RCLE_TBCFV_R04_TEST_ONLY_BLOCK_WORKER_PACKET_V1"
TEST_CHECKPOINT_SCHEMA = "RCLE_TBCFV_R04_TEST_ONLY_PRIVATE_CHECKPOINT_V1"
TEST_INSTALL_SCHEMA = "RCLE_TBCFV_R04_TEST_ONLY_PARENT_ORDERED_INSTALL_V1"
WORKER_AUTHORIZATION_SCHEMA = "RCLE_TBCFV_R04_ONE_BLOCK_WORKER_AUTHORIZATION_V1"
PRODUCTION_CONTEXT_SCHEMA = "RCLE_TBCFV_R04_CLOSED_ONE_BLOCK_PRODUCTION_CONTEXT_V1"

CPU_HOURS_CEILING = 32.0
FOUR_PROCESS_WALL_HOURS_CEILING = 8.861
PROCESS_GROUP_RSS_CEILING = 2 * 1024**3
PRIVATE_SCRATCH_COMBINED_CEILING = 12 * 1024**3
CANONICAL_DURABLE_CEILING = 1024**3
CHECKPOINT_READ_CEILING = 4 * 1024**3
CHECKPOINT_WRITE_CEILING = 1024**3
WORKER_COUNT = 4

_HEX = re.compile(r"[0-9a-f]{64}")
_PRIVATE_KEYS = tuple(
    f"lease_scoped_worker_private_scratch_root_{index:02d}"
    for index in range(WORKER_COUNT)
)


class ProcessWorkerError(RuntimeError):
    """The private worker resource, packet, or install contract is invalid."""


@dataclass(frozen=True)
class _PrivateWorkerPermit:
    lease_id: str
    origin_lease_id: str
    predecessor_lease_id: None
    replacement_index: int
    lease_lineage: tuple[str, ...]
    stage_binding_sha256: str
    accepted_binding_sha256: str
    preactivity_certificate_sha256: str
    coordinate_proposal_sha256: str
    paths: Mapping[str, str]
    repair_transition_sha256: None
    expires_at: str

    def require_active(self, *, now: datetime) -> None:
        expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        if now.tzinfo is None or not now < expiry:
            raise ProcessWorkerError("private worker permit expired")


@dataclass(frozen=True)
class _ClosedBlockAuthority:
    certificate: Mapping[str, object]
    block_index: int
    root_digest: str
    expires_at: str

    def require_active(self, *, now: datetime) -> None:
        expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        if now.tzinfo is None or not now < expiry:
            raise ProcessWorkerError("closed block authority expired")

    def block_root_digest(self, block_index: int) -> str:
        if block_index != self.block_index:
            raise ProcessWorkerError("closed block authority crosses block identity")
        return self.root_digest


def canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
            + b"\n"
        )
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ProcessWorkerError("process artifact is not canonical JSON") from exc


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _process_lifetime_peak_rss_bytes() -> int:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class _ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        get_current_process = ctypes.windll.kernel32.GetCurrentProcess
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(_ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        if not get_process_memory_info(
            get_current_process(), ctypes.byref(counters), counters.cb
        ):
            raise ProcessWorkerError("cannot read production worker peak RSS")
        return int(counters.PeakWorkingSetSize)
    import resource

    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def _write_atomic_replace(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".aw-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(6):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(0.01 * (attempt + 1))
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_exclusive(path: Path, payload: bytes) -> None:
    """Publish complete bytes atomically without ever replacing the target."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".exclusive-", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ProcessWorkerError(
                f"create-only process artifact exists: {path.name}"
            ) from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_canonical_mapping(path: Path) -> Mapping[str, object]:
    if not path.is_file() or path.is_symlink():
        raise ProcessWorkerError(f"required regular process artifact is absent: {path}")
    payload = path.read_bytes()
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProcessWorkerError(f"process artifact is malformed: {path}") from exc
    if not isinstance(value, Mapping) or canonical_json_bytes(value) != payload:
        raise ProcessWorkerError(f"process artifact is not a canonical mapping: {path}")
    return value


def _require_hex(value: object, label: str) -> str:
    if not isinstance(value, str) or _HEX.fullmatch(value) is None:
        raise ProcessWorkerError(f"{label} is not a SHA-256 digest")
    return value


def _stable_absolute_path(value: str | os.PathLike[str]) -> Path:
    return Path(os.path.normcase(os.path.abspath(os.fspath(value))))


def _resolve_private_roots(paths: Mapping[str, object], *, canonical_root: Path) -> tuple[Path, ...]:
    if set(paths) != set(_PRIVATE_KEYS):
        raise ProcessWorkerError("private scratch path inventory differs")
    canonical = _stable_absolute_path(canonical_root)
    roots: list[Path] = []
    for key in _PRIVATE_KEYS:
        raw = paths[key]
        if not isinstance(raw, str):
            raise ProcessWorkerError("private scratch path is not a string")
        root = Path(raw)
        if not root.is_absolute():
            raise ProcessWorkerError("private scratch roots must be absolute")
        resolved = _stable_absolute_path(root)
        if resolved == canonical or canonical in resolved.parents or resolved in canonical.parents:
            raise ProcessWorkerError("private scratch root overlaps the canonical result tree")
        if root.exists() and root.is_symlink():
            raise ProcessWorkerError("private scratch root may not be a symlink")
        roots.append(resolved)
    if len(set(roots)) != WORKER_COUNT:
        raise ProcessWorkerError("private scratch roots must be pairwise distinct")
    for index, left in enumerate(roots):
        for right in roots[index + 1 :]:
            if left in right.parents or right in left.parents:
                raise ProcessWorkerError("private scratch roots may not contain one another")
    return tuple(roots)


def _private_root_digests(roots: Sequence[Path]) -> tuple[str, ...]:
    return tuple(_sha256(str(_stable_absolute_path(root)).encode("utf-8")) for root in roots)


def _private_root_set_sha256(roots: Sequence[Path]) -> str:
    return _sha256(canonical_json_bytes(list(_private_root_digests(roots))))


def make_process_resource_object(
    *,
    canonical_result_root: str | os.PathLike[str],
    private_scratch_roots: Sequence[str | os.PathLike[str]],
    source_set_sha256: str,
    native_binding_sha256: str,
) -> dict[str, object]:
    """Create the exact bounded object that a later request/lease must embed."""

    if len(private_scratch_roots) != WORKER_COUNT:
        raise ProcessWorkerError("exactly four private scratch roots are required")
    canonical = _stable_absolute_path(canonical_result_root)
    paths = {
        key: str(_stable_absolute_path(private_scratch_roots[index]))
        for index, key in enumerate(_PRIVATE_KEYS)
    }
    roots = _resolve_private_roots(paths, canonical_root=canonical)
    body: dict[str, object] = {
        "schema": RESOURCE_SCHEMA,
        "direction_id": "roster_consistent_latent_exploration",
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "identity": PRODUCTION_IDENTITY,
        "coordinate_binding_sha256": COORDINATE_BINDING_SHA256,
        "master_digest": MASTER_DIGEST,
        "source_set_sha256": _require_hex(source_set_sha256, "source set"),
        "native_binding_sha256": _require_hex(native_binding_sha256, "native binding"),
        "canonical_result_root": str(canonical),
        "lease_scope": "FUTURE_ROOT_LEASE_REQUIRED",
        "paths": {key: str(roots[index]) for index, key in enumerate(_PRIVATE_KEYS)},
        "private_root_digests": list(_private_root_digests(roots)),
        "private_root_set_sha256": _private_root_set_sha256(roots),
        "limits": {
            "projected_complete_panel_cpu_hours_upper": CPU_HOURS_CEILING,
            "projected_four_process_wall_hours_upper": FOUR_PROCESS_WALL_HOURS_CEILING,
            "max_workers": WORKER_COUNT,
            "spawn_processes": True,
            "one_thread_per_worker": True,
            "process_group_rss_bytes_upper": PROCESS_GROUP_RSS_CEILING,
            "private_scratch_combined_bytes_upper": PRIVATE_SCRATCH_COMBINED_CEILING,
            "canonical_durable_bytes_upper": CANONICAL_DURABLE_CEILING,
            "ordinary_checkpoint_read_bytes_upper": CHECKPOINT_READ_CEILING,
            "ordinary_checkpoint_write_bytes_upper": CHECKPOINT_WRITE_CEILING,
        },
        "result_blind": True,
        "production_activity_authorized": False,
    }
    body["resource_sha256"] = _sha256(canonical_json_bytes(body))
    return body


def validate_process_resource_object(value: Mapping[str, object]) -> dict[str, object]:
    required = {
        "schema", "direction_id", "science_revision", "empirical_object", "identity",
        "coordinate_binding_sha256", "master_digest", "source_set_sha256",
        "native_binding_sha256", "canonical_result_root", "lease_scope", "paths",
        "private_root_digests", "private_root_set_sha256", "limits", "result_blind",
        "production_activity_authorized", "resource_sha256",
    }
    if set(value) != required:
        raise ProcessWorkerError("process resource inventory differs")
    body = {key: value[key] for key in required - {"resource_sha256"}}
    if value["resource_sha256"] != _sha256(canonical_json_bytes(body)):
        raise ProcessWorkerError("process resource digest differs")
    fixed = {
        "schema": RESOURCE_SCHEMA,
        "direction_id": "roster_consistent_latent_exploration",
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "identity": PRODUCTION_IDENTITY,
        "coordinate_binding_sha256": COORDINATE_BINDING_SHA256,
        "master_digest": MASTER_DIGEST,
        "lease_scope": "FUTURE_ROOT_LEASE_REQUIRED",
        "result_blind": True,
        "production_activity_authorized": False,
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise ProcessWorkerError("process resource frozen identity differs")
    _require_hex(value["source_set_sha256"], "source set")
    _require_hex(value["native_binding_sha256"], "native binding")
    canonical_raw = value["canonical_result_root"]
    if not isinstance(canonical_raw, str) or not Path(canonical_raw).is_absolute():
        raise ProcessWorkerError("canonical result root is malformed")
    paths = value["paths"]
    if not isinstance(paths, Mapping):
        raise ProcessWorkerError("private scratch paths are malformed")
    roots = _resolve_private_roots(paths, canonical_root=Path(canonical_raw))
    if value["private_root_digests"] != list(_private_root_digests(roots)):
        raise ProcessWorkerError("private scratch root digest inventory differs")
    if value["private_root_set_sha256"] != _private_root_set_sha256(roots):
        raise ProcessWorkerError("private scratch root-set digest differs")
    expected_limits = {
        "projected_complete_panel_cpu_hours_upper": CPU_HOURS_CEILING,
        "projected_four_process_wall_hours_upper": FOUR_PROCESS_WALL_HOURS_CEILING,
        "max_workers": WORKER_COUNT,
        "spawn_processes": True,
        "one_thread_per_worker": True,
        "process_group_rss_bytes_upper": PROCESS_GROUP_RSS_CEILING,
        "private_scratch_combined_bytes_upper": PRIVATE_SCRATCH_COMBINED_CEILING,
        "canonical_durable_bytes_upper": CANONICAL_DURABLE_CEILING,
        "ordinary_checkpoint_read_bytes_upper": CHECKPOINT_READ_CEILING,
        "ordinary_checkpoint_write_bytes_upper": CHECKPOINT_WRITE_CEILING,
    }
    if value["limits"] != expected_limits:
        raise ProcessWorkerError("process resource limits differ")
    return dict(value)


def make_spawn_payload(
    resource: Mapping[str, object],
    *,
    block_index: int,
    block_root_digest: str,
    native_source_sha256: str,
    native_build_key: str,
    expires_at: str,
    test_only: bool = False,
    test_steps: int = 4,
) -> dict[str, object]:
    accepted = validate_process_resource_object(resource)
    if isinstance(block_index, bool) or not isinstance(block_index, int) or not 0 <= block_index < 20:
        raise ProcessWorkerError("spawn block index is outside 0..19")
    paths = accepted["paths"]
    assert isinstance(paths, Mapping)
    scratch = str(paths[_PRIVATE_KEYS[block_index % WORKER_COUNT]])
    payload: dict[str, object] = {
        "schema": PAYLOAD_SCHEMA,
        "block_index": block_index,
        "identity": PRODUCTION_IDENTITY,
        "coordinate_binding_sha256": COORDINATE_BINDING_SHA256,
        "master_digest": MASTER_DIGEST,
        "source_set_sha256": accepted["source_set_sha256"],
        "native_binding_sha256": accepted["native_binding_sha256"],
        "native_source_sha256": _require_hex(native_source_sha256, "native source"),
        "native_build_key": _require_hex(native_build_key, "native build key"),
        "block_root_digest": _require_hex(block_root_digest, "block root"),
        "resource_sha256": accepted["resource_sha256"],
        "private_root_set_sha256": accepted["private_root_set_sha256"],
        "private_scratch_root": scratch,
        "private_scratch_root_sha256": _sha256(scratch.encode("utf-8")),
        "private_scratch_slot": block_index % WORKER_COUNT,
        "expires_at": expires_at,
        "test_only": bool(test_only),
        "test_steps": int(test_steps),
        "canonical_paths_present": False,
        "result_blind": True,
    }
    payload["payload_sha256"] = _sha256(canonical_json_bytes(payload))
    return payload


def validate_spawn_payload(value: Mapping[str, object]) -> dict[str, object]:
    required = {
        "schema", "block_index", "identity", "coordinate_binding_sha256", "master_digest",
        "source_set_sha256", "native_binding_sha256", "native_source_sha256",
        "native_build_key", "block_root_digest", "resource_sha256",
        "private_root_set_sha256", "private_scratch_root",
        "private_scratch_root_sha256", "private_scratch_slot", "expires_at", "test_only",
        "test_steps", "canonical_paths_present", "result_blind", "payload_sha256",
    }
    if set(value) != required:
        raise ProcessWorkerError("spawn payload inventory differs")
    body = {key: value[key] for key in required - {"payload_sha256"}}
    if value["payload_sha256"] != _sha256(canonical_json_bytes(body)):
        raise ProcessWorkerError("spawn payload digest differs")
    if (
        value["schema"] != PAYLOAD_SCHEMA
        or value["identity"] != PRODUCTION_IDENTITY
        or value["coordinate_binding_sha256"] != COORDINATE_BINDING_SHA256
        or value["master_digest"] != MASTER_DIGEST
        or value["canonical_paths_present"] is not False
        or value["result_blind"] is not True
    ):
        raise ProcessWorkerError("spawn payload frozen identity differs")
    block_index = value["block_index"]
    if isinstance(block_index, bool) or not isinstance(block_index, int) or not 0 <= block_index < 20:
        raise ProcessWorkerError("spawn payload block index differs")
    if value["private_scratch_slot"] != block_index % WORKER_COUNT:
        raise ProcessWorkerError("spawn private scratch slot differs")
    for key in (
        "source_set_sha256", "native_binding_sha256", "native_source_sha256",
        "native_build_key", "block_root_digest", "resource_sha256",
        "private_root_set_sha256", "private_scratch_root_sha256",
    ):
        _require_hex(value[key], key)
    scratch = value["private_scratch_root"]
    if not isinstance(scratch, str) or not Path(scratch).is_absolute():
        raise ProcessWorkerError("spawn private scratch path is malformed")
    if value["private_scratch_root_sha256"] != _sha256(scratch.encode("utf-8")):
        raise ProcessWorkerError("spawn private scratch path digest differs")
    if not isinstance(value["test_only"], bool):
        raise ProcessWorkerError("spawn test-only flag is malformed")
    steps = value["test_steps"]
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 64:
        raise ProcessWorkerError("spawn test step count is malformed")
    try:
        expiry = datetime.fromisoformat(str(value["expires_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProcessWorkerError("spawn expiry is malformed") from exc
    if expiry.tzinfo is None:
        raise ProcessWorkerError("spawn expiry must be timezone-aware")
    return dict(value)


def validate_parent_authorized_spawn_payload(
    value: Mapping[str, object], resource_value: Mapping[str, object]
) -> dict[str, object]:
    payload = validate_spawn_payload(value)
    resource = validate_process_resource_object(resource_value)
    paths = resource["paths"]
    assert isinstance(paths, Mapping)
    expected_scratch = str(paths[_PRIVATE_KEYS[int(payload["private_scratch_slot"])]])
    if (
        payload["resource_sha256"] != resource["resource_sha256"]
        or payload["private_root_set_sha256"] != resource["private_root_set_sha256"]
        or payload["source_set_sha256"] != resource["source_set_sha256"]
        or payload["native_binding_sha256"] != resource["native_binding_sha256"]
        or payload["private_scratch_root"] != expected_scratch
    ):
        raise ProcessWorkerError(
            "spawn private scratch path is not parent-authorized by resource inventory"
        )
    return payload


def validate_production_context(
    value: Mapping[str, object], payload_value: Mapping[str, object]
) -> dict[str, object]:
    required = {
        "schema", "block_index", "identity", "coordinate_binding_sha256",
        "master_digest", "block_root_digest", "source_set_sha256",
        "native_binding_sha256", "native_source_sha256", "native_build_key",
        "native_artifact_sha256", "empirical_bindings", "origin_lease_id",
        "stage_binding_sha256", "accepted_binding_sha256",
        "preactivity_certificate_sha256", "coordinate_proposal_sha256",
        "lease_document_sha256", "lease_validated_at", "expires_at", "one_thread", "gpu_count",
        "canonical_paths_present", "result_blind", "protocol_canary",
        "protocol_canary_failure_once", "context_sha256",
    }
    if set(value) != required:
        raise ProcessWorkerError("production context inventory differs")
    body = {key: value[key] for key in required - {"context_sha256"}}
    if value["context_sha256"] != _sha256(canonical_json_bytes(body)):
        raise ProcessWorkerError("production context digest differs")
    payload = validate_spawn_payload(payload_value)
    if payload["test_only"] is not False:
        raise ProcessWorkerError("production context requires a production payload")
    fixed = {
        "schema": PRODUCTION_CONTEXT_SCHEMA,
        "block_index": payload["block_index"],
        "identity": PRODUCTION_IDENTITY,
        "coordinate_binding_sha256": COORDINATE_BINDING_SHA256,
        "master_digest": MASTER_DIGEST,
        "block_root_digest": payload["block_root_digest"],
        "source_set_sha256": payload["source_set_sha256"],
        "native_binding_sha256": payload["native_binding_sha256"],
        "native_source_sha256": payload["native_source_sha256"],
        "native_build_key": payload["native_build_key"],
        "one_thread": True,
        "gpu_count": 0,
        "canonical_paths_present": False,
        "result_blind": True,
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise ProcessWorkerError("production context frozen one-block binding differs")
    if not isinstance(value["protocol_canary"], bool) or not isinstance(
        value["protocol_canary_failure_once"], bool
    ):
        raise ProcessWorkerError("production context protocol-canary flags are malformed")
    if value["protocol_canary_failure_once"] is True and value["protocol_canary"] is not True:
        raise ProcessWorkerError("failure injection is confined to the protocol canary")
    for key in (
        "native_artifact_sha256", "stage_binding_sha256",
        "accepted_binding_sha256", "preactivity_certificate_sha256",
        "coordinate_proposal_sha256", "lease_document_sha256",
    ):
        _require_hex(value[key], key)
    if not isinstance(value["origin_lease_id"], str) or not value["origin_lease_id"]:
        raise ProcessWorkerError("production context origin lease is malformed")
    try:
        expiry = datetime.fromisoformat(str(value["expires_at"]).replace("Z", "+00:00"))
        validated_at = datetime.fromisoformat(
            str(value["lease_validated_at"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ProcessWorkerError("production context lease time is malformed") from exc
    if expiry.tzinfo is None or validated_at.tzinfo is None or validated_at >= expiry:
        raise ProcessWorkerError("production context lease time differs")
    bindings = value["empirical_bindings"]
    expected_binding_keys = {
        "source_manifest_sha256", "config_sha256", "native_binding_sha256",
        "coordinate_digest", "master_digest", "origin_lease_id", "lease_id",
        "lease_binding_sha256",
    }
    if not isinstance(bindings, Mapping) or set(bindings) != expected_binding_keys:
        raise ProcessWorkerError("production context empirical bindings differ")
    for key in (
        "source_manifest_sha256", "config_sha256", "native_binding_sha256",
        "coordinate_digest", "master_digest", "lease_binding_sha256",
    ):
        _require_hex(bindings[key], f"empirical binding {key}")
    if (
        bindings["source_manifest_sha256"] != payload["source_set_sha256"]
        or bindings["native_binding_sha256"] != payload["native_binding_sha256"]
        or bindings["coordinate_digest"] != COORDINATE_BINDING_SHA256
        or bindings["master_digest"] != MASTER_DIGEST
        or bindings["origin_lease_id"] != value["origin_lease_id"]
        or bindings["lease_id"] != value["origin_lease_id"]
        or bindings["lease_binding_sha256"] != value["stage_binding_sha256"]
    ):
        raise ProcessWorkerError("production context empirical binding values differ")
    return dict(value)


def make_worker_authorization(
    resource_value: Mapping[str, object],
    payload_value: Mapping[str, object],
    *,
    production_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    payload = validate_parent_authorized_spawn_payload(payload_value, resource_value)
    if payload["test_only"] is True:
        if production_context is not None:
            raise ProcessWorkerError("TEST worker authorization cannot carry production context")
        context = None
        production_activity_authorized = False
    else:
        if production_context is None:
            raise ProcessWorkerError("production worker authorization requires closed context")
        context = validate_production_context(production_context, payload)
        production_activity_authorized = context["protocol_canary"] is False
    authorization: dict[str, object] = {
        "schema": WORKER_AUTHORIZATION_SCHEMA,
        "resource_sha256": payload["resource_sha256"],
        "source_set_sha256": payload["source_set_sha256"],
        "native_binding_sha256": payload["native_binding_sha256"],
        "private_root_set_sha256": payload["private_root_set_sha256"],
        "block_index": payload["block_index"],
        "private_scratch_slot": payload["private_scratch_slot"],
        "private_scratch_root": payload["private_scratch_root"],
        "private_scratch_root_sha256": payload["private_scratch_root_sha256"],
        "payload_sha256": payload["payload_sha256"],
        "test_only": payload["test_only"],
        "production_activity_authorized": production_activity_authorized,
        "production_context": context,
        "canonical_paths_present": False,
        "result_blind": True,
    }
    authorization["authorization_sha256"] = _sha256(
        canonical_json_bytes(authorization)
    )
    return authorization


def validate_worker_authorization(
    value: Mapping[str, object], payload_value: Mapping[str, object]
) -> dict[str, object]:
    required = {
        "schema", "resource_sha256", "source_set_sha256", "native_binding_sha256",
        "private_root_set_sha256", "block_index", "private_scratch_slot",
        "private_scratch_root", "private_scratch_root_sha256", "payload_sha256",
        "test_only", "production_activity_authorized", "production_context",
        "canonical_paths_present", "result_blind", "authorization_sha256",
    }
    if set(value) != required:
        raise ProcessWorkerError("worker authorization inventory differs")
    body = {key: value[key] for key in required - {"authorization_sha256"}}
    if value["authorization_sha256"] != _sha256(canonical_json_bytes(body)):
        raise ProcessWorkerError("worker authorization digest differs")
    payload = validate_spawn_payload(payload_value)
    expected = {
        "schema": WORKER_AUTHORIZATION_SCHEMA,
        "resource_sha256": payload["resource_sha256"],
        "source_set_sha256": payload["source_set_sha256"],
        "native_binding_sha256": payload["native_binding_sha256"],
        "private_root_set_sha256": payload["private_root_set_sha256"],
        "block_index": payload["block_index"],
        "private_scratch_slot": payload["private_scratch_slot"],
        "private_scratch_root": payload["private_scratch_root"],
        "private_scratch_root_sha256": payload["private_scratch_root_sha256"],
        "payload_sha256": payload["payload_sha256"],
        "test_only": payload["test_only"],
        "production_activity_authorized": (
            payload["test_only"] is False
            and isinstance(value["production_context"], Mapping)
            and value["production_context"].get("protocol_canary") is False
        ),
        "production_context": value["production_context"],
        "canonical_paths_present": False,
        "result_blind": True,
    }
    if any(value[key] != expected[key] for key in expected):
        raise ProcessWorkerError("worker authorization does not bind exact one-block payload")
    if payload["test_only"] is True:
        if value["production_context"] is not None:
            raise ProcessWorkerError("TEST worker authorization carries production context")
    else:
        context = value["production_context"]
        if not isinstance(context, Mapping):
            raise ProcessWorkerError("production worker authorization context is absent")
        validate_production_context(context, payload)
    return dict(value)


def write_spawn_payload(path: str | os.PathLike[str], value: Mapping[str, object]) -> Path:
    accepted = validate_spawn_payload(value)
    target = Path(path)
    _write_exclusive(target, canonical_json_bytes(accepted))
    return target


def _checkpoint_path(payload: Mapping[str, object]) -> Path:
    return Path(str(payload["private_scratch_root"])) / f"block_{int(payload['block_index']):02d}" / "checkpoint.json"


def run_test_only_spawn_worker(
    payload_path: str,
    worker_authorization: Mapping[str, object],
    *,
    inject_failure_after_step: int | None = None,
) -> dict[str, object]:
    """Spawn-safe deterministic lifecycle canary; it contains no science values."""

    payload = validate_spawn_payload(_read_canonical_mapping(Path(payload_path)))
    validate_worker_authorization(worker_authorization, payload)
    if payload["test_only"] is not True:
        raise ProcessWorkerError("TEST worker refuses a production payload")
    expiry = datetime.fromisoformat(str(payload["expires_at"]).replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expiry:
        raise ProcessWorkerError("spawn payload expired")
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    try:
        import torch

        torch.set_num_threads(1)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
    except ImportError:
        pass
    checkpoint = _checkpoint_path(payload)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    completed = 0
    if checkpoint.exists():
        state = _read_canonical_mapping(checkpoint)
        if set(state) != {"schema", "payload_sha256", "block_index", "steps_completed", "rolling_sha256", "result_blind"}:
            raise ProcessWorkerError("private checkpoint inventory differs")
        if (
            state["schema"] != TEST_CHECKPOINT_SCHEMA
            or state["payload_sha256"] != payload["payload_sha256"]
            or state["block_index"] != payload["block_index"]
            or state["result_blind"] is not True
        ):
            raise ProcessWorkerError("private checkpoint identity differs")
        completed = int(state["steps_completed"])
    steps = int(payload["test_steps"])
    for step in range(completed, steps):
        rolling = _sha256(f"{payload['payload_sha256']}:{step + 1}".encode("ascii"))
        state = {
            "schema": TEST_CHECKPOINT_SCHEMA,
            "payload_sha256": payload["payload_sha256"],
            "block_index": payload["block_index"],
            "steps_completed": step + 1,
            "rolling_sha256": rolling,
            "result_blind": True,
        }
        _write_atomic_replace(checkpoint, canonical_json_bytes(state))
        if inject_failure_after_step == step + 1:
            raise ProcessWorkerError("injected TEST-only worker failure")
    state = _read_canonical_mapping(checkpoint)
    manifest = {
        "schema": TEST_PACKET_SCHEMA,
        "block_index": payload["block_index"],
        "identity": payload["identity"],
        "source_set_sha256": payload["source_set_sha256"],
        "native_binding_sha256": payload["native_binding_sha256"],
        "block_root_digest": payload["block_root_digest"],
        "resource_sha256": payload["resource_sha256"],
        "payload_sha256": payload["payload_sha256"],
        "checkpoint_sha256": _sha256(canonical_json_bytes(state)),
        "steps_completed": steps,
        "one_thread": True,
        "result_blind": True,
        "test_only": True,
    }
    packet_root = checkpoint.parent / "complete_packet"
    if packet_root.exists():
        observed = _read_canonical_mapping(packet_root / "manifest.json")
        if dict(observed) != manifest:
            raise ProcessWorkerError("existing TEST packet differs")
        packet_checkpoint = _read_canonical_mapping(packet_root / "checkpoint.json")
        if (
            canonical_json_bytes(packet_checkpoint) != canonical_json_bytes(state)
            or _sha256(canonical_json_bytes(packet_checkpoint))
            != manifest["checkpoint_sha256"]
        ):
            raise ProcessWorkerError("existing TEST packet checkpoint differs")
    else:
        staging = checkpoint.parent / f".packet-{os.getpid()}"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()
        _write_exclusive(staging / "checkpoint.json", canonical_json_bytes(state))
        _write_exclusive(staging / "manifest.json", canonical_json_bytes(manifest))
        os.rename(staging, packet_root)
    packet_bytes = (
        (packet_root / "manifest.json").read_bytes()
        + (packet_root / "checkpoint.json").read_bytes()
    )
    return {
        "block_index": int(payload["block_index"]),
        "packet_path": str(packet_root),
        "packet_sha256": _sha256(packet_bytes),
        "worker_pid": os.getpid(),
        "private_bytes": sum(path.stat().st_size for path in checkpoint.parent.rglob("*") if path.is_file()),
    }


def _block_file_inventory(block_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(block_root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ProcessWorkerError("production block packet contains a symlink")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ProcessWorkerError("production block packet contains a special entry")
        payload = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(block_root).as_posix(),
                "sha256": _sha256(payload),
                "bytes": len(payload),
            }
        )
    return rows


def run_production_block_worker(
    payload_path: str,
    worker_authorization: Mapping[str, object],
) -> dict[str, object]:
    """Execute one exact block wholly below its sole private scratch root."""

    payload = validate_spawn_payload(_read_canonical_mapping(Path(payload_path)))
    authorization = validate_worker_authorization(worker_authorization, payload)
    if payload["test_only"] is not False:
        raise ProcessWorkerError("production worker requires an authorized production payload")
    context_value = authorization["production_context"]
    assert isinstance(context_value, Mapping)
    context = validate_production_context(context_value, payload)
    protocol_canary = context["protocol_canary"] is True
    if authorization["production_activity_authorized"] is protocol_canary:
        raise ProcessWorkerError("production worker activity/canary authority differs")
    expiry = datetime.fromisoformat(str(context["expires_at"]).replace("Z", "+00:00"))
    if datetime.now(timezone.utc) >= expiry:
        raise ProcessWorkerError("production worker context expired")
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    import torch

    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
        raise ProcessWorkerError("production worker is not exactly one-thread")

    from .empirical_artifacts import AtomicEmpiricalFrontier, EmpiricalBindings
    from .empirical_runner import (
        BLOCK_COUNTS,
        HELDOUT_CELLS,
        LEARNED_PACKAGES,
        OWNER_TOKEN,
        SCRIPTED_PACKAGES,
        SyntheticTestRNG,
        _new_block_runtime,
        _persist_runtime,
        _restore_runtime,
        execute_run_block,
    )

    bindings_value = context["empirical_bindings"]
    assert isinstance(bindings_value, Mapping)
    bindings = EmpiricalBindings(**dict(bindings_value))
    bindings.validate()
    origin = str(context["origin_lease_id"])
    permit = _PrivateWorkerPermit(
        lease_id=origin,
        origin_lease_id=origin,
        predecessor_lease_id=None,
        replacement_index=0,
        lease_lineage=(origin,),
        stage_binding_sha256=str(context["stage_binding_sha256"]),
        accepted_binding_sha256=str(context["accepted_binding_sha256"]),
        preactivity_certificate_sha256=str(context["preactivity_certificate_sha256"]),
        coordinate_proposal_sha256=str(context["coordinate_proposal_sha256"]),
        paths={},
        repair_transition_sha256=None,
        expires_at=str(context["expires_at"]),
    )
    authority = _ClosedBlockAuthority(
        certificate={
            "native": {
                "source_sha256": context["native_source_sha256"],
                "build_key": context["native_build_key"],
                "artifact_sha256": context["native_artifact_sha256"],
            }
        },
        block_index=int(payload["block_index"]),
        root_digest=str(payload["block_root_digest"]),
        expires_at=str(context["expires_at"]),
    )
    block_base = Path(str(payload["private_scratch_root"])) / f"b{int(payload['block_index']):02d}"
    frontier_root = block_base / "f"
    now = datetime.fromisoformat(str(context["lease_validated_at"]).replace("Z", "+00:00"))
    if frontier_root.exists():
        frontier = AtomicEmpiricalFrontier.resume(
            frontier_root,
            bindings,
            owner_token=OWNER_TOKEN,
            permit=permit,
            now=now,
            lease_document_sha256=str(context["lease_document_sha256"]),
        )
    else:
        frontier = AtomicEmpiricalFrontier.create(
            frontier_root,
            bindings,
            owner_token=OWNER_TOKEN,
            permit=permit,
            now=now,
            lease_document_sha256=str(context["lease_document_sha256"]),
        )
    block_index = int(payload["block_index"])
    if protocol_canary:
        runtime = _restore_runtime(frontier, block_index)
        failure_marker = block_base / "PROTOCOL_CANARY_FAILURE_ONCE.json"
        if runtime is None:
            runtime = _new_block_runtime(SyntheticTestRNG())
            if context["protocol_canary_failure_once"] is True:
                _persist_runtime(frontier, block_index, runtime)
                if not failure_marker.exists():
                    _write_exclusive(
                        failure_marker,
                        canonical_json_bytes(
                            {
                                "schema": "RCLE_TBCFV_R04_PROTOCOL_CANARY_FAILURE_ONCE_V1",
                                "block_index": block_index,
                                "payload_sha256": payload["payload_sha256"],
                            }
                        ),
                    )
                    raise ProcessWorkerError("injected production protocol canary failure")
        runtime.phase = "BLOCK_COMPLETE"
        runtime.updates = {arm: 800 for arm in LEARNED_PACKAGES}
        runtime.learned_completed = {
            arm: {cell: 2_048 for cell in HELDOUT_CELLS}
            for arm in LEARNED_PACKAGES
        }
        runtime.scripted_completed = {
            package: {cell: 2_048 for cell in HELDOUT_CELLS}
            for package in SCRIPTED_PACKAGES
        }
        for family in runtime.aggregates.values():
            for owner in family.values():
                for cell in owner.values():
                    cell["episodes"] = 2_048
        runtime.counts = dict(BLOCK_COUNTS)
        _persist_runtime(frontier, block_index, runtime)
        frontier.seal_block(block_index, owner_token=OWNER_TOKEN)
    else:
        execute_run_block(
            frontier, authority, block_index, now=datetime.now(timezone.utc)
        )
    source_block = frontier_root / "blocks" / f"block_{int(payload['block_index']):02d}"
    complete_marker = source_block / "COMPLETE.json"
    if not complete_marker.is_file():
        raise ProcessWorkerError("production worker block did not seal completely")
    packet_root = block_base / "production_complete_packet"
    if not packet_root.exists():
        staging = block_base / f".production-packet-{os.getpid()}"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()
        shutil.copytree(source_block, staging / "block")
        inventory = _block_file_inventory(staging / "block")
        from .empirical_artifacts import BLOCK_COUNTS

        manifest = {
            "schema": PACKET_SCHEMA,
            "block_index": payload["block_index"],
            "identity": payload["identity"],
            "source_set_sha256": payload["source_set_sha256"],
            "native_binding_sha256": payload["native_binding_sha256"],
            "block_root_digest": payload["block_root_digest"],
            "resource_sha256": payload["resource_sha256"],
            "payload_sha256": payload["payload_sha256"],
            "authorization_sha256": authorization["authorization_sha256"],
            "complete_marker_sha256": _sha256(complete_marker.read_bytes()),
            "file_inventory": inventory,
            "counts": dict(BLOCK_COUNTS),
            "one_thread": True,
            "result_blind": True,
            "test_only": False,
        }
        _write_exclusive(staging / "manifest.json", canonical_json_bytes(manifest))
        os.rename(staging, packet_root)
    manifest = validate_production_worker_packet(
        packet_root,
        payload,
        worker_authorization=authorization,
    )
    digest = hashlib.sha256()
    digest.update((packet_root / "manifest.json").read_bytes())
    for row in manifest["file_inventory"]:
        digest.update((packet_root / "block" / Path(str(row["path"]))).read_bytes())
    process_lifetime_peak_rss = _process_lifetime_peak_rss_bytes()
    return {
        "block_index": int(payload["block_index"]),
        "packet_path": str(packet_root),
        "packet_sha256": digest.hexdigest(),
        "worker_pid": os.getpid(),
        "private_bytes": tree_size_bytes(block_base),
        "process_lifetime_peak_rss_bytes": process_lifetime_peak_rss,
    }


def validate_production_worker_packet(
    packet_path: str | os.PathLike[str],
    expected_payload: Mapping[str, object],
    *,
    worker_authorization: Mapping[str, object],
) -> dict[str, object]:
    payload = validate_spawn_payload(expected_payload)
    authorization = validate_worker_authorization(worker_authorization, payload)
    if payload["test_only"] is not False:
        raise ProcessWorkerError("production packet validator refuses TEST payload")
    root = Path(packet_path)
    if not root.is_dir() or root.is_symlink() or {p.name for p in root.iterdir()} != {"block", "manifest.json"}:
        raise ProcessWorkerError("production packet inventory differs")
    manifest = _read_canonical_mapping(root / "manifest.json")
    required = {
        "schema", "block_index", "identity", "source_set_sha256",
        "native_binding_sha256", "block_root_digest", "resource_sha256",
        "payload_sha256", "authorization_sha256", "complete_marker_sha256",
        "file_inventory", "counts", "one_thread", "result_blind", "test_only",
    }
    if set(manifest) != required:
        raise ProcessWorkerError("production packet manifest inventory differs")
    from .empirical_artifacts import BLOCK_COUNTS

    expected = {
        "schema": PACKET_SCHEMA,
        "block_index": payload["block_index"],
        "identity": payload["identity"],
        "source_set_sha256": payload["source_set_sha256"],
        "native_binding_sha256": payload["native_binding_sha256"],
        "block_root_digest": payload["block_root_digest"],
        "resource_sha256": payload["resource_sha256"],
        "payload_sha256": payload["payload_sha256"],
        "authorization_sha256": authorization["authorization_sha256"],
        "counts": dict(BLOCK_COUNTS),
        "one_thread": True,
        "result_blind": True,
        "test_only": False,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ProcessWorkerError("production packet source, identity, digest, or counts differ")
    block_root = root / "block"
    inventory = _block_file_inventory(block_root)
    if manifest["file_inventory"] != inventory:
        raise ProcessWorkerError("production packet file inventory or digest differs")
    marker = block_root / "COMPLETE.json"
    if (
        not marker.is_file()
        or manifest["complete_marker_sha256"] != _sha256(marker.read_bytes())
    ):
        raise ProcessWorkerError("production packet complete marker digest differs")
    return dict(manifest)


def validate_test_worker_packet(
    packet_path: str | os.PathLike[str],
    expected_payload: Mapping[str, object],
    *,
    authorized_resource: Mapping[str, object],
) -> dict[str, object]:
    expected = validate_parent_authorized_spawn_payload(
        expected_payload, authorized_resource
    )
    if expected["test_only"] is not True:
        raise ProcessWorkerError("TEST packet validator refuses production payload")
    root = Path(packet_path)
    if not root.is_dir() or root.is_symlink():
        raise ProcessWorkerError("TEST worker packet root is invalid")
    if {path.name for path in root.iterdir()} != {"checkpoint.json", "manifest.json"}:
        raise ProcessWorkerError("TEST worker packet file inventory differs")
    manifest = _read_canonical_mapping(root / "manifest.json")
    required = {
        "schema", "block_index", "identity", "source_set_sha256", "native_binding_sha256",
        "block_root_digest", "resource_sha256", "payload_sha256", "checkpoint_sha256",
        "steps_completed", "one_thread", "result_blind", "test_only",
    }
    if set(manifest) != required:
        raise ProcessWorkerError("TEST worker packet inventory differs")
    expected_values = {
        "schema": TEST_PACKET_SCHEMA,
        "block_index": expected["block_index"],
        "identity": expected["identity"],
        "source_set_sha256": expected["source_set_sha256"],
        "native_binding_sha256": expected["native_binding_sha256"],
        "block_root_digest": expected["block_root_digest"],
        "resource_sha256": expected["resource_sha256"],
        "payload_sha256": expected["payload_sha256"],
        "steps_completed": expected["test_steps"],
        "one_thread": True,
        "result_blind": True,
        "test_only": True,
    }
    if any(manifest.get(key) != value for key, value in expected_values.items()):
        raise ProcessWorkerError("TEST worker packet identity, source, block, or counts differ")
    _require_hex(manifest["checkpoint_sha256"], "checkpoint")
    checkpoint = _read_canonical_mapping(root / "checkpoint.json")
    if set(checkpoint) != {
        "schema", "payload_sha256", "block_index", "steps_completed",
        "rolling_sha256", "result_blind",
    }:
        raise ProcessWorkerError("TEST packet checkpoint inventory differs")
    if (
        checkpoint["schema"] != TEST_CHECKPOINT_SCHEMA
        or checkpoint["payload_sha256"] != expected["payload_sha256"]
        or checkpoint["block_index"] != expected["block_index"]
        or checkpoint["steps_completed"] != expected["test_steps"]
        or checkpoint["result_blind"] is not True
        or manifest["checkpoint_sha256"]
        != _sha256(canonical_json_bytes(checkpoint))
    ):
        raise ProcessWorkerError("TEST packet checkpoint digest or counts differ")
    _require_hex(checkpoint["rolling_sha256"], "checkpoint rolling state")
    expected_rolling = _sha256(
        f"{expected['payload_sha256']}:{expected['test_steps']}".encode("ascii")
    )
    if checkpoint["rolling_sha256"] != expected_rolling:
        raise ProcessWorkerError("TEST packet final rolling digest differs")
    return dict(manifest)


def parent_install_test_packets(
    canonical_root: str | os.PathLike[str],
    packets: Sequence[tuple[str | os.PathLike[str], Mapping[str, object]]],
    *,
    authorized_resource: Mapping[str, object],
) -> dict[str, object]:
    """Validate all packets first, then install exact block order from the parent."""

    resource = validate_process_resource_object(authorized_resource)
    root = _stable_absolute_path(canonical_root)
    if root != _stable_absolute_path(str(resource["canonical_result_root"])):
        raise ProcessWorkerError("synthetic canonical root is not parent-authorized")
    parent_pid = os.getpid()
    validated = [
        (
            validate_test_worker_packet(
                path, payload, authorized_resource=resource
            ),
            Path(path),
        )
        for path, payload in packets
    ]
    indices = [int(item[0]["block_index"]) for item in validated]
    if len(indices) != len(set(indices)):
        raise ProcessWorkerError("parent received duplicate worker blocks")
    if root.exists():
        raise ProcessWorkerError("synthetic canonical install already exists")
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = root.parent / f".{root.name}.parent-install-{parent_pid}"
    if staging.exists():
        raise ProcessWorkerError("synthetic canonical install staging already exists")
    staging.mkdir()
    installed: list[dict[str, object]] = []
    try:
        for manifest, packet_root in sorted(
            validated, key=lambda item: int(item[0]["block_index"])
        ):
            block_index = int(manifest["block_index"])
            target = staging / f"block_{block_index:02d}"
            target.mkdir()
            manifest_bytes = (packet_root / "manifest.json").read_bytes()
            checkpoint_bytes = (packet_root / "checkpoint.json").read_bytes()
            _write_exclusive(target / "manifest.json", manifest_bytes)
            _write_exclusive(target / "checkpoint.json", checkpoint_bytes)
            installed.append(
                {
                    "block_index": block_index,
                    "packet_sha256": _sha256(manifest_bytes + checkpoint_bytes),
                    "installed_by_pid": parent_pid,
                }
            )
        report = {
            "schema": TEST_INSTALL_SCHEMA,
            "parent_pid": parent_pid,
            "ordered_block_indices": [row["block_index"] for row in installed],
            "installed": installed,
            "all_packets_validated_before_install": True,
            "failure_atomic_parent_tree_install": True,
            "worker_failure_installs_nothing": True,
            "result_blind": True,
            "test_only": True,
        }
        _write_exclusive(
            staging / "PARENT_ORDERED_INSTALL.json", canonical_json_bytes(report)
        )
        os.rename(staging, root)
        return report
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def tree_size_bytes(root: str | os.PathLike[str]) -> int:
    path = Path(root)
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file() and not item.is_symlink())


__all__ = [
    "CANONICAL_DURABLE_CEILING", "CHECKPOINT_READ_CEILING", "CHECKPOINT_WRITE_CEILING",
    "CPU_HOURS_CEILING", "FOUR_PROCESS_WALL_HOURS_CEILING", "PROCESS_GROUP_RSS_CEILING",
    "PRIVATE_SCRATCH_COMBINED_CEILING", "ProcessWorkerError", "make_process_resource_object",
    "make_spawn_payload", "make_worker_authorization", "parent_install_test_packets",
    "run_production_block_worker", "run_test_only_spawn_worker", "tree_size_bytes",
    "validate_production_context", "validate_production_worker_packet",
    "validate_parent_authorized_spawn_payload", "validate_process_resource_object",
    "validate_spawn_payload", "validate_test_worker_packet",
    "validate_worker_authorization", "write_spawn_payload",
]
