"""Compact structural-audit surfaces for RSCF Gate B.

Audits retain booleans, counters and digests only.  They are designed to make
the protected coupling and lifecycle invariants inspectable without retaining
Q vectors, branch trajectories, private branch state, or private returns.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from .lifecycle import (
    LifecycleContractError,
    canonical_sha256,
    reject_private_persistence,
    validate_test_namespace,
)


AUDIT_SCHEMA_VERSION = "SGSP_RSCF_AUDIT_CERTIFICATE_V1"


class AuditName(str, Enum):
    ONE_ORIGIN_PER_ROLE = "one_origin_per_role"
    SELECTOR_ARM_IDENTITY = "selector_arm_identity"
    ANTITHETIC_SLOT_PAIRING = "antithetic_slot_pairing"
    Q_ENTRY_COUNT = "all_legal_q_entry_count"
    FACTUAL_REUSE_COUNT = "factual_return_reuse_count"
    ALTERNATIVE_COUNT = "alternative_continuation_count"
    IMMUTABLE_PARAMETERS = "immutable_parameter_identity"
    FOCAL_ONLY_INTERVENTION = "focal_only_current_action_intervention"
    FACTUAL_TEAMMATES = "factual_teammate_action_identity"
    CLOSED_LOOP_RECURRENCE = "closed_loop_next_slot_recurrence"
    COMMON_TAPE = "common_future_tape"
    BRANCH_ORDER_INDEPENDENCE = "branch_order_independence"
    FACTUAL_RETURN_IDENTITY = "factual_suffix_return_identity"
    STOPPED_TARGETS = "stopped_targets_and_advantages"
    COMPARATOR_MATCHING = "comparator_information_work_optimizer_checkpoint_matching"
    NO_LEAKAGE = "no_private_branch_leakage"
    UPDATE_512_ONLY = "update_512_only_evaluation"
    ATOMIC_COMPLETE_SEED = "atomic_complete_seed_lifecycle"


REQUIRED_AUDITS = frozenset(AuditName)


@dataclass(frozen=True)
class AuditEvidence:
    name: AuditName
    passed: bool
    evidence_sha256: str
    observed_count: int | None = None
    expected_count: int | None = None
    detail_code: str = ""

    def __post_init__(self) -> None:
        if len(self.evidence_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.evidence_sha256):
            raise LifecycleContractError(f"audit {self.name.value} has invalid evidence digest")
        for label, value in (("observed_count", self.observed_count), ("expected_count", self.expected_count)):
            if value is not None and (not isinstance(value, int) or value < 0):
                raise LifecycleContractError(f"audit {self.name.value} {label} must be nonnegative")
        if (self.observed_count is None) != (self.expected_count is None):
            raise LifecycleContractError("audit count comparison requires both observed and expected")
        if self.observed_count is not None and self.passed != (self.observed_count == self.expected_count):
            raise LifecycleContractError("audit pass flag disagrees with its compact count comparison")
        if len(self.detail_code) > 96:
            raise LifecycleContractError("audit detail_code must remain compact")
        reject_private_persistence(asdict(self))

    @classmethod
    def digest_match(
        cls,
        name: AuditName,
        left_digest: str,
        right_digest: str,
        *,
        detail_code: str = "DIGEST_MATCH",
    ) -> "AuditEvidence":
        material = {"name": name.value, "left": left_digest, "right": right_digest}
        return cls(
            name=name,
            passed=left_digest == right_digest,
            evidence_sha256=canonical_sha256(material),
            detail_code=detail_code,
        )

    @classmethod
    def count_match(
        cls,
        name: AuditName,
        observed: int,
        expected: int,
        *,
        provenance_digest: str,
        detail_code: str = "COUNT_MATCH",
    ) -> "AuditEvidence":
        return cls(
            name=name,
            passed=observed == expected,
            evidence_sha256=canonical_sha256(
                {"name": name.value, "observed": observed, "expected": expected, "provenance": provenance_digest}
            ),
            observed_count=observed,
            expected_count=expected,
            detail_code=detail_code,
        )


@dataclass(frozen=True)
class AtomicLifecycleCounters:
    expected_origins: int
    completed_origins: int
    duplicate_origins: int
    replacement_origins: int
    resampled_origins: int
    partial_rows: int
    checkpoint_update: int

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not isinstance(value, int) or value < 0:
                raise LifecycleContractError(f"lifecycle counter {name} must be nonnegative")

    @property
    def complete_and_atomic(self) -> bool:
        return (
            self.expected_origins > 0
            and self.completed_origins == self.expected_origins
            and self.duplicate_origins == 0
            and self.replacement_origins == 0
            and self.resampled_origins == 0
            and self.partial_rows == 0
            and self.checkpoint_update == 512
        )

    def to_audit(self, provenance_digest: str) -> AuditEvidence:
        return AuditEvidence(
            name=AuditName.ATOMIC_COMPLETE_SEED,
            passed=self.complete_and_atomic,
            evidence_sha256=canonical_sha256({"counters": asdict(self), "provenance": provenance_digest}),
            detail_code="ATOMIC_COMPLETE_NO_DUPLICATE_RESAMPLE_REPLACEMENT_OR_PARTIAL_ROW",
        )


@dataclass(frozen=True)
class AuditCertificate:
    namespace: str
    test_seed_block_id: str
    evidence: tuple[AuditEvidence, ...]
    schema_version: str = AUDIT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_test_namespace(self.namespace)
        if not self.test_seed_block_id.startswith("TEST_"):
            raise LifecycleContractError("audit seed-block identity must be explicitly TEST-only")
        if self.schema_version != AUDIT_SCHEMA_VERSION:
            raise LifecycleContractError("audit schema mismatch")
        names = [entry.name for entry in self.evidence]
        if len(names) != len(set(names)):
            raise LifecycleContractError("audit certificate contains duplicate audit names")
        missing = REQUIRED_AUDITS - set(names)
        extra = set(names) - REQUIRED_AUDITS
        if missing or extra:
            raise LifecycleContractError(
                f"audit certificate suite mismatch; missing={sorted(item.value for item in missing)}, "
                f"extra={sorted(item.value for item in extra)}"
            )
        reject_private_persistence(self.to_compact_payload())

    @property
    def structural_valid(self) -> bool:
        return all(entry.passed for entry in self.evidence)

    @property
    def failed_names(self) -> tuple[str, ...]:
        return tuple(sorted(entry.name.value for entry in self.evidence if not entry.passed))

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_compact_payload())

    def to_compact_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": "COMPACT_TEST_AUDIT_CERTIFICATE",
            "namespace": self.namespace,
            "test_seed_block_id": self.test_seed_block_id,
            "structural_valid": self.structural_valid,
            "evidence": [
                {
                    **asdict(entry),
                    "name": entry.name.value,
                }
                for entry in sorted(self.evidence, key=lambda item: item.name.value)
            ],
        }


class AuditBuilder:
    """Collect one evidence item per required surface and seal once complete."""

    def __init__(self, namespace: str, test_seed_block_id: str) -> None:
        self.namespace = validate_test_namespace(namespace)
        if not test_seed_block_id.startswith("TEST_"):
            raise LifecycleContractError("audit seed-block identity must be explicitly TEST-only")
        self.test_seed_block_id = test_seed_block_id
        self._evidence: dict[AuditName, AuditEvidence] = {}

    def add(self, evidence: AuditEvidence) -> None:
        if evidence.name in self._evidence:
            raise LifecycleContractError(f"audit {evidence.name.value} is write-once within a certificate")
        self._evidence[evidence.name] = evidence

    def add_boolean(
        self,
        name: AuditName,
        passed: bool,
        *,
        compact_facts: Mapping[str, str | int | bool],
        detail_code: str,
    ) -> None:
        reject_private_persistence(compact_facts)
        self.add(
            AuditEvidence(
                name=name,
                passed=passed,
                evidence_sha256=canonical_sha256({"name": name.value, "facts": compact_facts}),
                detail_code=detail_code,
            )
        )

    def seal(self) -> AuditCertificate:
        return AuditCertificate(
            namespace=self.namespace,
            test_seed_block_id=self.test_seed_block_id,
            evidence=tuple(self._evidence.values()),
        )


def build_complete_test_audit_certificate(
    namespace: str,
    test_seed_block_id: str,
    evidence: Iterable[AuditEvidence],
) -> AuditCertificate:
    """Convenience constructor which remains fail-closed on an incomplete suite."""
    return AuditCertificate(namespace, test_seed_block_id, tuple(evidence))
