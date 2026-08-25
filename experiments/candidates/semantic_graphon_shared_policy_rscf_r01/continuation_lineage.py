"""Explicit, fail-closed A-to-B continuation provenance for SGSP RSCF-r01.

The objects in this module are value objects only.  They never discover a
retained root, mint an empirical identity, read a master, or open a result.
The authorized generation-154 bridge is therefore testable with synthetic
bytes without creating an empirical continuation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping


SCIENCE_REVISION = "SGSP-RG2Z-RSCF-SCIENCE-20260821-01"
LINEAGE_SCHEMA = "SGSP_RSCF_R01_CONTINUATION_LINEAGE_V1"
CONTINUATION_IDENTITY_SCHEMA = "SGSP_RSCF_R01_CONTINUATION_IDENTITY_V1"
OWNER_CONTINUATION_AUTHORITY_SCHEMA = "SGSP_RSCF_R01_OWNER_CONTINUATION_AUTHORITY_V1"
CUT_GENERATION = 154
CUT_COMPLETED_UPDATES = 154
NEXT_ATTEMPTED_UPDATE_INDEX = 154
ALLOWED_IMPORT = (
    "ACTOR",
    "CRITIC",
    "OPTIMIZER",
    "COMPLETED_UPDATES",
    "ROLLING_ORIGIN_DIGEST",
    "AUDIT_RECEIPTS",
)


class ContinuationLineageError(ValueError):
    """One lineage fact failed before any destination state was mutated."""


def _plain(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ContinuationLineageError("lineage payload contains a nonfinite float")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ContinuationLineageError(f"unsupported lineage value {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("ascii")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_sha256(name: str, value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ContinuationLineageError(f"{name} must be one lowercase SHA-256")
    return value


@dataclass(frozen=True)
class ContinuationLineage:
    """One separately hashed predecessor-to-continuation cut edge."""

    namespace: str
    lease_lineage_id: str
    predecessor_production_identity_sha256: str
    predecessor_source_binding_sha256: str
    predecessor_master_commitment_sha256: str
    predecessor_coordinate_manifest_sha256: str
    cut_seed_block_index: int
    cut_frontier_sha256: str
    cut_resume_commit_sha256: str
    cut_resume_metadata_sha256: str
    cut_resume_state_sha256: str
    continuation_source_binding_sha256: str
    science_revision: str = SCIENCE_REVISION
    cut_generation: int = CUT_GENERATION
    cut_completed_updates: int = CUT_COMPLETED_UPDATES
    next_attempted_update_index: int = NEXT_ATTEMPTED_UPDATE_INDEX
    allowed_import: tuple[str, ...] = ALLOWED_IMPORT
    width: int = 32
    outer_workers: int = 1
    cpu_cores: int = 1
    native_threads: int = 1
    gpu: bool = False
    seed_blocks: int = 24
    sole_checkpoint_update: int = 512
    quantity_family_size: int = 28
    both_arms_common_cut: bool = True
    atomic_complete_result: bool = True
    evaluable: bool = False
    source_alias: bool = False
    old_artifact_mutation: bool = False
    schema: str = LINEAGE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != LINEAGE_SCHEMA or self.science_revision != SCIENCE_REVISION:
            raise ContinuationLineageError("lineage schema or science revision changed")
        if not self.namespace or not self.lease_lineage_id:
            raise ContinuationLineageError("lineage namespace and lease lineage are required")
        for name in (
            "predecessor_production_identity_sha256",
            "predecessor_source_binding_sha256",
            "predecessor_master_commitment_sha256",
            "predecessor_coordinate_manifest_sha256",
            "cut_frontier_sha256",
            "cut_resume_commit_sha256",
            "cut_resume_metadata_sha256",
            "cut_resume_state_sha256",
            "continuation_source_binding_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        if self.predecessor_source_binding_sha256 == self.continuation_source_binding_sha256:
            raise ContinuationLineageError("predecessor and continuation source digests must be distinct")
        if not 0 <= self.cut_seed_block_index < 24:
            raise ContinuationLineageError("cut seed block is outside the frozen 24-seed panel")
        if (
            self.cut_generation,
            self.cut_completed_updates,
            self.next_attempted_update_index,
        ) != (154, 154, 154):
            raise ContinuationLineageError("lineage cut is not the immutable generation-154 boundary")
        if self.allowed_import != ALLOWED_IMPORT:
            raise ContinuationLineageError("lineage import inventory changed")
        if (
            self.width,
            self.outer_workers,
            self.cpu_cores,
            self.native_threads,
            self.gpu,
            self.seed_blocks,
            self.sole_checkpoint_update,
            self.quantity_family_size,
        ) != (32, 1, 1, 1, False, 24, 512, 28):
            raise ContinuationLineageError("lineage execution or panel law changed")
        if (
            self.both_arms_common_cut is not True
            or self.atomic_complete_result is not True
            or self.evaluable is not False
            or self.source_alias is not False
            or self.old_artifact_mutation is not False
        ):
            raise ContinuationLineageError("lineage relaxed the common-cut, atomicity, or non-alias law")

    @property
    def digest(self) -> str:
        return canonical_sha256(asdict(self))


@dataclass(frozen=True)
class ContinuationIdentity:
    """The B identity; A and the lineage remain separately named objects."""

    namespace: str
    lease_lineage_id: str
    master_commitment_sha256: str
    coordinate_manifest_sha256: str
    continuation_source_binding_sha256: str
    predecessor_production_identity_sha256: str
    lineage_sha256: str
    width: int = 32
    outer_workers: int = 1
    cpu_cores: int = 1
    native_threads: int = 1
    gpu: bool = False
    seed_blocks: int = 24
    sole_checkpoint_update: int = 512
    quantity_family_size: int = 28
    atomic_complete_result: bool = True
    partial_evaluable: bool = False
    schema: str = CONTINUATION_IDENTITY_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != CONTINUATION_IDENTITY_SCHEMA:
            raise ContinuationLineageError("continuation identity schema changed")
        for name in (
            "master_commitment_sha256",
            "coordinate_manifest_sha256",
            "continuation_source_binding_sha256",
            "predecessor_production_identity_sha256",
            "lineage_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        if (
            self.width,
            self.outer_workers,
            self.cpu_cores,
            self.native_threads,
            self.gpu,
            self.seed_blocks,
            self.sole_checkpoint_update,
            self.quantity_family_size,
        ) != (32, 1, 1, 1, False, 24, 512, 28):
            raise ContinuationLineageError("continuation identity execution or panel law changed")
        if self.atomic_complete_result is not True or self.partial_evaluable is not False:
            raise ContinuationLineageError("continuation identity relaxed atomic complete-only evaluation")

    @classmethod
    def bind(cls, lineage: ContinuationLineage) -> "ContinuationIdentity":
        return cls(
            namespace=lineage.namespace,
            lease_lineage_id=lineage.lease_lineage_id,
            master_commitment_sha256=lineage.predecessor_master_commitment_sha256,
            coordinate_manifest_sha256=lineage.predecessor_coordinate_manifest_sha256,
            continuation_source_binding_sha256=lineage.continuation_source_binding_sha256,
            predecessor_production_identity_sha256=lineage.predecessor_production_identity_sha256,
            lineage_sha256=lineage.digest,
        )

    @property
    def digest(self) -> str:
        return canonical_sha256(asdict(self))

    def require_exact_lineage(self, lineage: ContinuationLineage) -> None:
        expected = ContinuationIdentity.bind(lineage)
        if self != expected:
            raise ContinuationLineageError("continuation identity does not bind the exact A-to-B lineage")


def _authenticate_cut_bytes(
    *,
    lineage: ContinuationLineage,
    frontier_bytes: bytes,
    resume_metadata_bytes: bytes,
    resume_commit_bytes: bytes,
    resume_state_bytes: bytes,
    label: str,
) -> Mapping[str, Any]:
    """Authenticate four already-supplied byte objects without discovering paths."""

    observed = {
        "frontier": hashlib.sha256(frontier_bytes).hexdigest(),
        "metadata": hashlib.sha256(resume_metadata_bytes).hexdigest(),
        "commit": hashlib.sha256(resume_commit_bytes).hexdigest(),
        "state": hashlib.sha256(resume_state_bytes).hexdigest(),
    }
    expected = {
        "frontier": lineage.cut_frontier_sha256,
        "metadata": lineage.cut_resume_metadata_sha256,
        "commit": lineage.cut_resume_commit_sha256,
        "state": lineage.cut_resume_state_sha256,
    }
    if observed != expected:
        raise ContinuationLineageError(f"{label} cut byte digest differs from the lineage")
    try:
        frontier_envelope = json.loads(frontier_bytes.decode("ascii"))
        metadata = json.loads(resume_metadata_bytes.decode("ascii"))
        commit = json.loads(resume_commit_bytes.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContinuationLineageError(f"{label} cut metadata is not canonical ASCII JSON") from exc
    for raw, value in (
        (frontier_bytes, frontier_envelope),
        (resume_metadata_bytes, metadata),
        (resume_commit_bytes, commit),
    ):
        if canonical_json_bytes(value) != raw:
            raise ContinuationLineageError(f"{label} cut metadata bytes are noncanonical")
    frontier = frontier_envelope.get("payload")
    if (
        not isinstance(frontier, dict)
        or frontier_envelope.get("schema") != "SGSP_RSCF_R01_PRODUCTION_LIFECYCLE_V1"
        or frontier_envelope.get("payload_sha256") != canonical_sha256(frontier)
        or frontier.get("kind") != "BLINDED_NON_EVALUABLE_SEED_FRONTIER"
    ):
        raise ContinuationLineageError(f"{label} frontier envelope is invalid")
    state_sha = hashlib.sha256(resume_state_bytes).hexdigest()
    frontier_core = dict(frontier)
    frontier_core.pop("kind")
    frontier_sha = canonical_sha256(frontier_core)
    if (
        frontier.get("seed_block_index") != lineage.cut_seed_block_index
        or frontier.get("generation") != 154
        or frontier.get("completed_updates") != 154
        or frontier.get("coordinate_manifest_sha256") != lineage.predecessor_coordinate_manifest_sha256
        or frontier.get("source_binding_sha256") != lineage.predecessor_source_binding_sha256
        or frontier.get("evaluable") is not False
        or metadata.get("kind") != "BLINDED_NON_EVALUABLE_RESUME_STATE"
        or metadata.get("seed_block_index") != lineage.cut_seed_block_index
        or metadata.get("generation") != 154
        or metadata.get("state_sha256") != state_sha
        or metadata.get("frontier_sha256") != frontier_sha
        or metadata.get("evaluable") is not False
        or commit.get("kind") != "ATOMIC_RESUME_GENERATION_COMMIT"
        or commit.get("seed_block_index") != lineage.cut_seed_block_index
        or commit.get("generation") != 154
        or commit.get("state_sha256") != state_sha
        or commit.get("metadata_sha256") != hashlib.sha256(resume_metadata_bytes).hexdigest()
        or commit.get("frontier_sha256") != frontier_sha
    ):
        raise ContinuationLineageError(f"{label} cut relation is inconsistent")
    return frontier_core


@dataclass(frozen=True)
class AuthenticatedContinuationCut:
    """Authenticated TEST-only cut bytes; contains no path or value output."""

    test_only_marker: str
    frontier_bytes: bytes
    resume_metadata_bytes: bytes
    resume_commit_bytes: bytes
    resume_state_bytes: bytes

    def __post_init__(self) -> None:
        if self.test_only_marker != "TEST_ONLY_SYNTHETIC_GENERATION154":
            raise ContinuationLineageError("cut fixture is not explicitly TEST-only")
        if not all(isinstance(item, bytes) and item for item in (
            self.frontier_bytes,
            self.resume_metadata_bytes,
            self.resume_commit_bytes,
            self.resume_state_bytes,
        )):
            raise ContinuationLineageError("synthetic cut requires four nonempty byte objects")

    @property
    def byte_digests(self) -> Mapping[str, str]:
        return {
            "frontier": hashlib.sha256(self.frontier_bytes).hexdigest(),
            "metadata": hashlib.sha256(self.resume_metadata_bytes).hexdigest(),
            "commit": hashlib.sha256(self.resume_commit_bytes).hexdigest(),
            "state": hashlib.sha256(self.resume_state_bytes).hexdigest(),
        }

    def authenticate(self, lineage: ContinuationLineage) -> Mapping[str, Any]:
        return _authenticate_cut_bytes(
            lineage=lineage,
            frontier_bytes=self.frontier_bytes,
            resume_metadata_bytes=self.resume_metadata_bytes,
            resume_commit_bytes=self.resume_commit_bytes,
            resume_state_bytes=self.resume_state_bytes,
            label="synthetic",
        )


_PRODUCTION_CUT_CONSTRUCTION_TOKEN = object()


@dataclass(frozen=True, init=False)
class OwnerAuthenticatedContinuationCut:
    """Owner-authorized production bytes with no path-discovery capability."""

    authority_sha256: str
    frontier_bytes: bytes
    resume_metadata_bytes: bytes
    resume_commit_bytes: bytes
    resume_state_bytes: bytes

    def __init__(
        self,
        authority_sha256: str,
        frontier_bytes: bytes,
        resume_metadata_bytes: bytes,
        resume_commit_bytes: bytes,
        resume_state_bytes: bytes,
        *,
        _construction_token: object | None = None,
    ) -> None:
        if _construction_token is not _PRODUCTION_CUT_CONSTRUCTION_TOKEN:
            raise ContinuationLineageError("production cut requires from_owner_authenticated_bytes")
        object.__setattr__(self, "authority_sha256", _require_sha256("authority_sha256", authority_sha256))
        for name, value in (
            ("frontier_bytes", frontier_bytes),
            ("resume_metadata_bytes", resume_metadata_bytes),
            ("resume_commit_bytes", resume_commit_bytes),
            ("resume_state_bytes", resume_state_bytes),
        ):
            if not isinstance(value, bytes) or not value:
                raise ContinuationLineageError("production cut requires four nonempty byte objects")
            object.__setattr__(self, name, value)

    @classmethod
    def from_owner_authenticated_bytes(
        cls,
        *,
        predecessor_lease: Any,
        continuation_lease: Any,
        lineage: ContinuationLineage,
        continuation_identity: ContinuationIdentity,
        owner_authority: Mapping[str, Any],
        frontier_bytes: bytes,
        resume_metadata_bytes: bytes,
        resume_commit_bytes: bytes,
        resume_state_bytes: bytes,
    ) -> "OwnerAuthenticatedContinuationCut":
        from .production_boundary import ValidatedRootLease

        if type(predecessor_lease) is not ValidatedRootLease or type(continuation_lease) is not ValidatedRootLease:
            raise ContinuationLineageError("production cut requires two exact validated Root leases")
        continuation_identity.require_exact_lineage(lineage)
        byte_digests = {
            "frontier": hashlib.sha256(frontier_bytes).hexdigest(),
            "metadata": hashlib.sha256(resume_metadata_bytes).hexdigest(),
            "commit": hashlib.sha256(resume_commit_bytes).hexdigest(),
            "state": hashlib.sha256(resume_state_bytes).hexdigest(),
        }
        expected_authority = {
            "schema": OWNER_CONTINUATION_AUTHORITY_SCHEMA,
            "authority": "OPERATIONAL_ROOT",
            "state": "ACTIVE",
            "authorization_id": owner_authority.get("authorization_id"),
            "predecessor_lease_payload_sha256": predecessor_lease.lease_payload_sha256,
            "continuation_lease_payload_sha256": continuation_lease.lease_payload_sha256,
            "lineage_sha256": lineage.digest,
            "continuation_identity_sha256": continuation_identity.digest,
            "cut_seed_block_index": lineage.cut_seed_block_index,
            "cut_byte_digests": byte_digests,
        }
        if (
            set(owner_authority) != set(expected_authority)
            or not isinstance(owner_authority.get("authorization_id"), str)
            or not owner_authority["authorization_id"]
            or dict(owner_authority) != expected_authority
        ):
            raise ContinuationLineageError("production cut owner authority is absent or inexact")
        cut = cls(
            canonical_sha256(owner_authority),
            frontier_bytes,
            resume_metadata_bytes,
            resume_commit_bytes,
            resume_state_bytes,
            _construction_token=_PRODUCTION_CUT_CONSTRUCTION_TOKEN,
        )
        cut.authenticate(lineage)
        return cut

    @property
    def byte_digests(self) -> Mapping[str, str]:
        return {
            "frontier": hashlib.sha256(self.frontier_bytes).hexdigest(),
            "metadata": hashlib.sha256(self.resume_metadata_bytes).hexdigest(),
            "commit": hashlib.sha256(self.resume_commit_bytes).hexdigest(),
            "state": hashlib.sha256(self.resume_state_bytes).hexdigest(),
        }

    def authenticate(self, lineage: ContinuationLineage) -> Mapping[str, Any]:
        return _authenticate_cut_bytes(
            lineage=lineage,
            frontier_bytes=self.frontier_bytes,
            resume_metadata_bytes=self.resume_metadata_bytes,
            resume_commit_bytes=self.resume_commit_bytes,
            resume_state_bytes=self.resume_state_bytes,
            label="owner-authenticated production",
        )


def validate_source_epoch_provenance(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema", "predecessor_production_identity_sha256",
        "predecessor_source_binding_sha256", "predecessor_master_commitment_sha256",
        "predecessor_coordinate_manifest_sha256", "predecessor_last_completed_update_index",
        "cut_seed_block_index", "cut_generation", "cut_frontier_sha256",
        "cut_resume_commit_sha256", "cut_resume_metadata_sha256", "cut_resume_state_sha256",
        "continuation_identity_sha256", "continuation_source_binding_sha256",
        "continuation_first_attempted_update_index", "lineage_sha256", "both_arms_common_cut",
    }
    result = dict(value)
    if (
        set(result) != required
        or result.get("schema") != "SGSP_RSCF_R01_SOURCE_EPOCH_PROVENANCE_V1"
        or result.get("predecessor_last_completed_update_index") != 153
        or result.get("cut_generation") != 154
        or result.get("continuation_first_attempted_update_index") != 154
        or result.get("both_arms_common_cut") is not True
        or not isinstance(result.get("cut_seed_block_index"), int)
        or not 0 <= result["cut_seed_block_index"] < 24
        or result.get("predecessor_source_binding_sha256") == result.get("continuation_source_binding_sha256")
    ):
        raise ContinuationLineageError("source-epoch provenance is not exact")
    non_digests = {
        "schema", "predecessor_last_completed_update_index", "cut_seed_block_index",
        "cut_generation", "continuation_first_attempted_update_index", "both_arms_common_cut",
    }
    for name in required - non_digests:
        _require_sha256(name, result[name])
    return result


def source_epoch_provenance(
    lineage: ContinuationLineage,
    continuation_identity: ContinuationIdentity,
) -> Mapping[str, Any]:
    continuation_identity.require_exact_lineage(lineage)
    return validate_source_epoch_provenance({
        "schema": "SGSP_RSCF_R01_SOURCE_EPOCH_PROVENANCE_V1",
        "predecessor_production_identity_sha256": lineage.predecessor_production_identity_sha256,
        "predecessor_source_binding_sha256": lineage.predecessor_source_binding_sha256,
        "predecessor_master_commitment_sha256": lineage.predecessor_master_commitment_sha256,
        "predecessor_coordinate_manifest_sha256": lineage.predecessor_coordinate_manifest_sha256,
        "predecessor_last_completed_update_index": 153,
        "cut_seed_block_index": lineage.cut_seed_block_index,
        "cut_generation": 154,
        "cut_frontier_sha256": lineage.cut_frontier_sha256,
        "cut_resume_commit_sha256": lineage.cut_resume_commit_sha256,
        "cut_resume_metadata_sha256": lineage.cut_resume_metadata_sha256,
        "cut_resume_state_sha256": lineage.cut_resume_state_sha256,
        "continuation_identity_sha256": continuation_identity.digest,
        "continuation_source_binding_sha256": lineage.continuation_source_binding_sha256,
        "continuation_first_attempted_update_index": 154,
        "lineage_sha256": lineage.digest,
        "both_arms_common_cut": True,
    })
