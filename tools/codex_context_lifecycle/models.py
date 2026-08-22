"""Context-source and load-policy models.

These types classify repository context. They do not load file contents and
do not create owner authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ContextSourceKind(str, Enum):
    USER_AUTHORITY = "USER_AUTHORITY"
    ROUTER = "ROUTER"
    ROLE_CONTRACT = "ROLE_CONTRACT"
    STAGE_OR_PORTFOLIO_CONTRACT = "STAGE_OR_PORTFOLIO_CONTRACT"
    CANONICAL_OWNER_ARTIFACT = "CANONICAL_OWNER_ARTIFACT"
    ADVISORY_OBJECT_COST_CONTEXT = "ADVISORY_OBJECT_COST_CONTEXT"
    EXPLICIT_USER_CONTROL_PLANE_CORRECTION = "EXPLICIT_USER_CONTROL_PLANE_CORRECTION"
    PLAN_EPOCH = "PLAN_EPOCH"
    SEMANTIC_COMMIT = "SEMANTIC_COMMIT"
    TYPED_PACKET = "TYPED_PACKET"
    TYPED_REPORT = "TYPED_REPORT"
    RAW_CONVERSATION = "RAW_CONVERSATION"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    COMPACTION_SUMMARY = "COMPACTION_SUMMARY"
    AUTOMATIC_MEMORY = "AUTOMATIC_MEMORY"
    NAVIGATION = "NAVIGATION"
    PROCEDURE = "PROCEDURE"
    HISTORY = "HISTORY"


class LoadPolicy(str, Enum):
    AUTO_ROUTER = "AUTO_ROUTER"
    ROLE_REQUIRED = "ROLE_REQUIRED"
    ON_DEMAND = "ON_DEMAND"
    ASSIGNMENT_ONLY = "ASSIGNMENT_ONLY"
    ASSIGNMENT_REFERENCED = "ASSIGNMENT_REFERENCED"
    EPOCH_REFERENCED = "EPOCH_REFERENCED"


class PromotionKind(str, Enum):
    EPHEMERAL = "EPHEMERAL"
    AUTHORITY_RULE = "AUTHORITY_RULE"
    ROLE_CONTRACT = "ROLE_CONTRACT"
    PROCEDURE = "PROCEDURE"
    REPOSITORY_NAVIGATION = "REPOSITORY_NAVIGATION"
    SHARED_ARCHITECTURE_DECISION = "SHARED_ARCHITECTURE_DECISION"
    SCIENTIFIC_ARTIFACT = "SCIENTIFIC_ARTIFACT"
    TECHNICAL_ARTIFACT = "TECHNICAL_ARTIFACT"
    PORTFOLIO_ARTIFACT = "PORTFOLIO_ARTIFACT"
    CURRENT_WORK_POINTER = "CURRENT_WORK_POINTER"


class PromotionState(str, Enum):
    PROPOSED = "PROPOSED"
    OWNER_ACCEPTED = "OWNER_ACCEPTED"
    OWNER_REJECTED = "OWNER_REJECTED"
    APPLIED = "APPLIED"
    CARRIED_FORWARD = "CARRIED_FORWARD"


class RolloverState(str, Enum):
    PREPARED = "PREPARED"
    OWNER_CONFIRMED = "OWNER_CONFIRMED"
    APPLIED = "APPLIED"
    CANCELLED = "CANCELLED"


class RetentionClass(str, Enum):
    ACTIVE_WORKING_SET = "ACTIVE_WORKING_SET"
    CANONICAL_REFERENCE = "CANONICAL_REFERENCE"
    AUDIT_ONLY = "AUDIT_ONLY"
    ARCHIVE_CANDIDATE = "ARCHIVE_CANDIDATE"
    RAW_EVIDENCE_RETAINED = "RAW_EVIDENCE_RETAINED"


class GcMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    MARK_ARCHIVED = "MARK_ARCHIVED"


@dataclass(frozen=True)
class PrecedenceLayer:
    name: str
    rank: int


PrecedenceLayer.P0_USER_AUTHORITY = PrecedenceLayer("P0_USER_AUTHORITY", 0)
PrecedenceLayer.P1_ROUTER_AND_ROLE = PrecedenceLayer("P1_ROUTER_AND_ROLE", 1)
PrecedenceLayer.P2_STAGE_OR_PORTFOLIO_CONTRACT = PrecedenceLayer(
    "P2_STAGE_OR_PORTFOLIO_CONTRACT", 2
)
PrecedenceLayer.P3_CANONICAL_OWNER_ARTIFACT = PrecedenceLayer(
    "P3_CANONICAL_OWNER_ARTIFACT", 3
)
PrecedenceLayer.P4_PLAN_EPOCH = PrecedenceLayer("P4_PLAN_EPOCH", 4)
PrecedenceLayer.P5_SEMANTIC_COMMIT = PrecedenceLayer("P5_SEMANTIC_COMMIT", 5)
PrecedenceLayer.P6_TYPED_PACKET = PrecedenceLayer("P6_TYPED_PACKET", 6)
PrecedenceLayer.P7_RAW_CONTEXT = PrecedenceLayer("P7_RAW_CONTEXT", 7)
PrecedenceLayer.P8_COMPACTION_SUMMARY = PrecedenceLayer("P8_COMPACTION_SUMMARY", 8)
PrecedenceLayer.P9_AUTOMATIC_MEMORY = PrecedenceLayer("P9_AUTOMATIC_MEMORY", 9)
PrecedenceLayer.NAVIGATION = PrecedenceLayer("NAVIGATION", 7)
PrecedenceLayer.PROCEDURE = PrecedenceLayer("PROCEDURE", 7)
PrecedenceLayer.HISTORY = PrecedenceLayer("HISTORY", 7)


@dataclass(frozen=True)
class ContextSource:
    id: str
    path: str
    kind: ContextSourceKind
    owner: str
    actors: tuple[str, ...]
    load_policy: LoadPolicy
    canonical: bool
    direction_id: str | None = None
    scope_key: str | None = None


@dataclass(frozen=True)
class ContextSourceRegistry:
    schema_version: int
    registry_revision: int
    sources: tuple[ContextSource, ...]


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    title: str
    owner: str
    scope: str
    status: str
    decision_date: str
    supersedes: tuple[str, ...]
    canonical_sources: tuple[str, ...]
    revisit_conditions: tuple[str, ...]
    path: str


@dataclass(frozen=True)
class PromotionProposal:
    promotion_id: str
    actor_context_id: str
    epoch_id: str
    promotion_kind: PromotionKind
    target_ref: str | None
    summary: str
    rationale: str
    source_refs: tuple[str, ...]
    owner_actor_context_id: str
    state: PromotionState
    disposition: dict[str, object] | None = None
    canonical_ref: str | None = None
    source_kind: ContextSourceKind | None = None
    writer_actor_context_id: str | None = None
    carried_to_epoch_id: str | None = None


@dataclass(frozen=True)
class WorkingSet:
    actor_context_id: str
    actor_kind: str
    epoch_id: str | None
    semantic_commit_id: str | None
    checkpoint_id: str | None
    open_obligation_ids: tuple[str, ...]
    unintaken_report_ids: tuple[str, ...]
    active_packet_ids: tuple[str, ...]
    navigation_refs: tuple[str, ...]
    procedure_refs: tuple[str, ...]
    canonical_refs: tuple[str, ...]
    promotion_ids: tuple[str, ...]
    rollover_id: str | None
    excluded_object_ids: tuple[str, ...]
