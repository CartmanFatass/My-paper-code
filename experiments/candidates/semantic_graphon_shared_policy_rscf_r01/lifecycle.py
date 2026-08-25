"""Write-once TEST-only lifecycle objects for the RSCF runner.

The frontier is deliberately never an evaluation input.  Only a separately
sealed :class:`CompleteSeedPacket` can be paired with the sole update-512
checkpoint by the evaluation consumer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .contracts import (
    RESERVED_SCIENTIFIC_NAMESPACE,
    TEST_NAMESPACE_PREFIX as CONTRACT_TEST_NAMESPACE_PREFIX,
)


SCHEMA_VERSION = "SGSP_RSCF_LIFECYCLE_V1"
TEST_NAMESPACE_PREFIX = CONTRACT_TEST_NAMESPACE_PREFIX
SOLE_EVALUABLE_UPDATE = 512

_FORBIDDEN_NAMESPACE_FRAGMENTS = (
    "PRODUCTION",
    "SCIENTIFIC",
    "EMPIRICAL",
    "SEMANTIC_GRAPHON_SHARED_POLICY|SGSP-RG2Z-RSCF-SCIENCE",
    RESERVED_SCIENTIFIC_NAMESPACE.upper(),
)
_FORBIDDEN_PERSISTED_KEYS = {
    "q",
    "q_value",
    "q_values",
    "q_vector",
    "q_vectors",
    "branch_trace",
    "branch_traces",
    "branch_history",
    "private_branch_state",
    "private_return",
    "private_returns",
    "private_future_return",
    "private_future_returns",
    "raw_episode_returns",
}


class LifecycleContractError(ValueError):
    """Raised when an object would weaken the TEST-only lifecycle contract."""


class WriteOnceConflictError(FileExistsError):
    """Raised when a write-once path already exists."""


def validate_test_namespace(namespace: str) -> str:
    if not isinstance(namespace, str) or not namespace.startswith(TEST_NAMESPACE_PREFIX):
        raise LifecycleContractError(
            f"namespace must start with the unmistakable TEST-only prefix {TEST_NAMESPACE_PREFIX!r}"
        )
    if len(namespace) == len(TEST_NAMESPACE_PREFIX):
        raise LifecycleContractError("TEST-only namespace requires a non-empty local identity")
    upper = namespace.upper()
    if any(fragment in upper for fragment in _FORBIDDEN_NAMESPACE_FRAGMENTS):
        raise LifecycleContractError("namespace resembles a reserved scientific/production identity")
    return namespace


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        raise LifecycleContractError("canonical payload contains a non-finite float")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise LifecycleContractError(f"unsupported canonical payload type: {type(value).__name__}")


def reject_private_persistence(value: Any, *, path: str = "payload") -> None:
    """Reject raw/private branch material recursively before persistence."""
    value = _plain(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in _FORBIDDEN_PERSISTED_KEYS:
                raise LifecycleContractError(f"forbidden persisted field at {path}.{key}")
            reject_private_persistence(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_private_persistence(item, path=f"{path}[{index}]")


def canonical_json_bytes(value: Any) -> bytes:
    plain = _plain(value)
    reject_private_persistence(plain)
    return json.dumps(
        plain,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short write while creating write-once lifecycle object")
        view = view[written:]
    os.fsync(fd)


def write_once_atomic_json(path: Path | str, payload: Mapping[str, Any]) -> str:
    """Publish a canonical envelope atomically without an overwrite window.

    A hard link is the exclusive publish primitive: creation of the destination
    either succeeds exactly once or raises when another writer won the race.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    body = _plain(payload)
    reject_private_persistence(body)
    body_digest = canonical_sha256(body)
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "payload_sha256": body_digest,
        "payload": body,
    }
    data = canonical_json_bytes(envelope)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        _write_all(fd, data)
        os.close(fd)
        fd = -1
        try:
            os.link(temporary, destination)
        except FileExistsError as exc:
            raise WriteOnceConflictError(str(destination)) from exc
        # Make the directory entry durable where the platform permits it.
        if os.name != "nt":
            dir_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        temporary.unlink(missing_ok=True)
    return body_digest


def read_verified_json(path: Path | str) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    try:
        envelope = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LifecycleContractError("lifecycle object is not canonical ASCII JSON") from exc
    if canonical_json_bytes(envelope) != raw:
        raise LifecycleContractError("lifecycle object is not in canonical byte form")
    if envelope.get("schema_version") != SCHEMA_VERSION:
        raise LifecycleContractError("lifecycle schema mismatch")
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise LifecycleContractError("lifecycle payload must be an object")
    if envelope.get("payload_sha256") != canonical_sha256(payload):
        raise LifecycleContractError("lifecycle payload digest mismatch")
    reject_private_persistence(payload)
    return payload


@dataclass(frozen=True)
class ResumeIdentity:
    namespace: str
    test_schedule_id: str
    test_schedule_sha256: str
    runner_identity_sha256: str
    selector_identity_sha256: str

    def __post_init__(self) -> None:
        validate_test_namespace(self.namespace)
        for name in ("test_schedule_id", "test_schedule_sha256", "runner_identity_sha256", "selector_identity_sha256"):
            value = getattr(self, name)
            if not value:
                raise LifecycleContractError(f"resume identity field {name} is empty")
        for name in ("test_schedule_sha256", "runner_identity_sha256", "selector_identity_sha256"):
            value = getattr(self, name)
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise LifecycleContractError(f"resume identity field {name} is not lowercase SHA-256")
        if not self.test_schedule_id.startswith("TEST_"):
            raise LifecycleContractError("schedule identity must be explicitly TEST-only")

    @property
    def digest(self) -> str:
        return canonical_sha256(asdict(self))

    def require_exact_match(self, expected: "ResumeIdentity") -> None:
        if self != expected:
            raise LifecycleContractError(
                "resume identity mismatch; resampling, replacement, or coordinate substitution is forbidden"
            )


@dataclass(frozen=True)
class FrontierRecord:
    resume_identity: ResumeIdentity
    expected_origin_count: int
    completed_origin_count: int
    completed_origin_set_sha256: str
    compact_counters: Mapping[str, int] = field(default_factory=dict)
    audit_digest: str = ""
    duplicate_count: int = 0
    replacement_count: int = 0
    resample_count: int = 0

    def __post_init__(self) -> None:
        if self.expected_origin_count <= 0:
            raise LifecycleContractError("expected origin count must be positive")
        if not 0 <= self.completed_origin_count <= self.expected_origin_count:
            raise LifecycleContractError("completed origin count is outside the registered schedule")
        if len(self.completed_origin_set_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in self.completed_origin_set_sha256
        ):
            raise LifecycleContractError("completed-origin digest is not lowercase SHA-256")
        if self.audit_digest and (
            len(self.audit_digest) != 64 or any(ch not in "0123456789abcdef" for ch in self.audit_digest)
        ):
            raise LifecycleContractError("frontier audit digest is not lowercase SHA-256")
        for key, value in self.compact_counters.items():
            if not isinstance(key, str) or type(value) is not int or value < 0:
                raise LifecycleContractError("frontier compact counters must be nonnegative integers")
        if any((self.duplicate_count, self.replacement_count, self.resample_count)):
            raise LifecycleContractError("frontier records cannot admit duplicate, replacement, or resampled work")
        reject_private_persistence(asdict(self))

    @property
    def evaluable(self) -> bool:
        # A frontier is progress evidence only, including when all work is done.
        return False

    def to_payload(self) -> dict[str, Any]:
        return {"kind": "NON_EVALUABLE_FRONTIER", **asdict(self), "evaluable": False}

    def require_resume_successor_of(self, previous: "FrontierRecord") -> None:
        """Verify a result-blind continuation of the exact frozen TEST schedule."""
        self.resume_identity.require_exact_match(previous.resume_identity)
        if self.expected_origin_count != previous.expected_origin_count:
            raise LifecycleContractError("resume changed the registered schedule cardinality")
        if self.completed_origin_count < previous.completed_origin_count:
            raise LifecycleContractError("resume discarded already completed atomic work")
        if (
            self.completed_origin_count == previous.completed_origin_count
            and self.completed_origin_set_sha256 != previous.completed_origin_set_sha256
        ):
            raise LifecycleContractError("resume replaced work at an unchanged completion frontier")


@dataclass(frozen=True)
class EvaluableCheckpointRef:
    namespace: str
    update: int
    checkpoint_sha256: str
    runner_identity_sha256: str
    synthetic_test_only: bool = True

    def __post_init__(self) -> None:
        validate_test_namespace(self.namespace)
        if self.update != SOLE_EVALUABLE_UPDATE:
            raise LifecycleContractError("only the state immediately after update 512 is evaluable")
        if self.synthetic_test_only is not True:
            raise LifecycleContractError("Gate-B may only construct TEST-only checkpoint references")
        for name in ("checkpoint_sha256", "runner_identity_sha256"):
            value = getattr(self, name)
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise LifecycleContractError(f"{name} is not lowercase SHA-256")

    @property
    def digest(self) -> str:
        return canonical_sha256(asdict(self))


@dataclass(frozen=True)
class CompleteSeedPacket:
    resume_identity: ResumeIdentity
    expected_origin_count: int
    completed_origin_count: int
    completed_origin_set_sha256: str
    audit_certificate_sha256: str
    checkpoint: EvaluableCheckpointRef
    compact_counters: Mapping[str, int]
    duplicate_count: int = 0
    replacement_count: int = 0
    resample_count: int = 0
    partial_row_count: int = 0

    def __post_init__(self) -> None:
        if self.resume_identity.namespace != self.checkpoint.namespace:
            raise LifecycleContractError("packet/checkpoint namespace mismatch")
        if self.resume_identity.runner_identity_sha256 != self.checkpoint.runner_identity_sha256:
            raise LifecycleContractError("packet/checkpoint runner identity mismatch")
        if self.expected_origin_count <= 0 or self.completed_origin_count != self.expected_origin_count:
            raise LifecycleContractError("only a complete selected-origin schedule may be sealed")
        if any((self.duplicate_count, self.replacement_count, self.resample_count, self.partial_row_count)):
            raise LifecycleContractError("atomic packet contains duplicate, replacement, resample, or partial-row evidence")
        for name in ("completed_origin_set_sha256", "audit_certificate_sha256"):
            value = getattr(self, name)
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise LifecycleContractError(f"complete seed packet {name} is not lowercase SHA-256")
        for key, value in self.compact_counters.items():
            if not isinstance(key, str) or type(value) is not int or value < 0:
                raise LifecycleContractError("packet compact counters must be nonnegative integers")
        reject_private_persistence(asdict(self))

    @property
    def evaluable(self) -> bool:
        return True

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        return {"kind": "ATOMIC_COMPLETE_TEST_SEED", **asdict(self), "evaluable": True}


class AtomicFrontierStore:
    """Small write-once store; callers choose distinct frontier generations."""

    def __init__(self, root: Path | str, namespace: str) -> None:
        self.root = Path(root)
        self.namespace = validate_test_namespace(namespace)

    def _path(self, kind: str, object_id: str) -> Path:
        if not object_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for ch in object_id):
            raise LifecycleContractError("lifecycle object id contains unsafe characters")
        return self.root / kind / f"{object_id}.json"

    def write_frontier(self, generation_id: str, record: FrontierRecord) -> str:
        if record.resume_identity.namespace != self.namespace:
            raise LifecycleContractError("frontier store namespace mismatch")
        return write_once_atomic_json(self._path("frontier", generation_id), record.to_payload())

    def read_frontier(self, generation_id: str, expected_identity: ResumeIdentity) -> FrontierRecord:
        payload = read_verified_json(self._path("frontier", generation_id))
        if payload.get("kind") != "NON_EVALUABLE_FRONTIER" or payload.get("evaluable") is not False:
            raise LifecycleContractError("frontier was relabeled as evaluable")
        identity = ResumeIdentity(**payload["resume_identity"])
        identity.require_exact_match(expected_identity)
        return FrontierRecord(
            resume_identity=identity,
            expected_origin_count=payload["expected_origin_count"],
            completed_origin_count=payload["completed_origin_count"],
            completed_origin_set_sha256=payload["completed_origin_set_sha256"],
            compact_counters=payload["compact_counters"],
            audit_digest=payload["audit_digest"],
            duplicate_count=payload.get("duplicate_count", 0),
            replacement_count=payload.get("replacement_count", 0),
            resample_count=payload.get("resample_count", 0),
        )

    def write_complete_packet(self, packet_id: str, packet: CompleteSeedPacket) -> str:
        if packet.resume_identity.namespace != self.namespace:
            raise LifecycleContractError("packet store namespace mismatch")
        return write_once_atomic_json(self._path("complete", packet_id), packet.to_payload())

    def read_complete_packet(self, packet_id: str, expected_identity: ResumeIdentity) -> CompleteSeedPacket:
        payload = read_verified_json(self._path("complete", packet_id))
        if payload.get("kind") != "ATOMIC_COMPLETE_TEST_SEED" or payload.get("evaluable") is not True:
            raise LifecycleContractError("complete packet evaluability marker is invalid")
        identity = ResumeIdentity(**payload["resume_identity"])
        identity.require_exact_match(expected_identity)
        return CompleteSeedPacket(
            resume_identity=identity,
            expected_origin_count=payload["expected_origin_count"],
            completed_origin_count=payload["completed_origin_count"],
            completed_origin_set_sha256=payload["completed_origin_set_sha256"],
            audit_certificate_sha256=payload["audit_certificate_sha256"],
            checkpoint=EvaluableCheckpointRef(**payload["checkpoint"]),
            compact_counters=payload["compact_counters"],
            duplicate_count=payload["duplicate_count"],
            replacement_count=payload["replacement_count"],
            resample_count=payload["resample_count"],
            partial_row_count=payload["partial_row_count"],
        )
