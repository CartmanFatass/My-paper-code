"""Immutable control-plane models for the repository-local semantic MVP."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .actor_models import ActorContext, ActorKind, ActorState


class ReturnKind(str, Enum):
    COMPLETED_ASSIGNMENT = "COMPLETED_ASSIGNMENT"
    PARTIAL_EVIDENCE = "PARTIAL_EVIDENCE"
    LOCAL_AUTHORITY_BOUNDARY = "LOCAL_AUTHORITY_BOUNDARY"
    MECHANICAL_INCIDENT = "MECHANICAL_INCIDENT"


class IntakeKind(str, Enum):
    INTEGRATE = "INTEGRATE"
    FOLLOWUP = "FOLLOWUP"
    ROUTE_OWNER = "ROUTE_OWNER"
    CANCEL_AUTHORIZED = "CANCEL_AUTHORIZED"
    ESCALATE_USER = "ESCALATE_USER"


class ObligationKind(str, Enum):
    REPORT_INTAKE_REQUIRED = "REPORT_INTAKE_REQUIRED"
    UNBOUND_SUBAGENT_INTAKE_REQUIRED = "UNBOUND_SUBAGENT_INTAKE_REQUIRED"
    OWNER_ROUTING_REQUIRED = "OWNER_ROUTING_REQUIRED"
    FOLLOWUP_DECISION_REQUIRED = "FOLLOWUP_DECISION_REQUIRED"
    PORTFOLIO_REVIEW_REQUIRED = "PORTFOLIO_REVIEW_REQUIRED"
    USER_DECISION_REQUIRED = "USER_DECISION_REQUIRED"
    CONTEXT_REANCHOR_REQUIRED = "CONTEXT_REANCHOR_REQUIRED"
    PACKET_INTAKE_REQUIRED = "PACKET_INTAKE_REQUIRED"
    PROMOTION_REVIEW_REQUIRED = "PROMOTION_REVIEW_REQUIRED"
    RESPONSIBILITY_HANDOFF_REQUIRED = "RESPONSIBILITY_HANDOFF_REQUIRED"
    # Persisted alias only. New writes use REPORT_INTAKE_REQUIRED.
    ROOT_INTAKE_REQUIRED = "ROOT_INTAKE_REQUIRED"


def normalize_obligation_kind(kind: str | ObligationKind) -> str:
    value = kind.value if isinstance(kind, ObligationKind) else str(kind)
    if value == ObligationKind.ROOT_INTAKE_REQUIRED.value:
        return ObligationKind.REPORT_INTAKE_REQUIRED.value
    return value


@dataclass(frozen=True)
class ResearchFrontier:
    current_question: str
    strongest_live_alternative: str
    claim_ceiling: str
    next_discriminator: str | None
    exploration_debt: tuple[str, ...]


@dataclass(frozen=True)
class ObservedFact:
    object: str
    predicate: str
    value: Any
    evidence_ref: str


@dataclass(frozen=True)
class SuggestedNextAction:
    owner: str
    action: str


@dataclass(frozen=True)
class SubagentReturnPacket:
    schema_version: str
    packet_kind: str
    workflow_id: str
    task_id: str
    return_kind: ReturnKind
    observed_facts: tuple[ObservedFact, ...]
    interpretive_claims: tuple[str, ...]
    remaining_unknowns: tuple[str, ...]
    suggested_next_actions: tuple[SuggestedNextAction, ...]
    research_frontier: ResearchFrontier | None
    global_disposition: str


@dataclass(frozen=True)
class RootIntakePacket:
    report_id: str
    intake_kind: IntakeKind
    translation: dict[str, str]
    next_action: SuggestedNextAction
    note: str
