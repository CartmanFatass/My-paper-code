"""Closed incident levels and local blast-radius validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IncidentLevel(str, Enum):
    E0_OBSERVATION = "E0_OBSERVATION"
    E1_EXACT_OPERATION_INCIDENT = "E1_EXACT_OPERATION_INCIDENT"
    E2_ASSIGNMENT_RECOVERY = "E2_ASSIGNMENT_RECOVERY"
    E3_DOMAIN_OWNER_DECISION = "E3_DOMAIN_OWNER_DECISION"
    E4_CROSS_OWNER_DECISION = "E4_CROSS_OWNER_DECISION"
    E5_USER_AUTHORITY_REQUIRED = "E5_USER_AUTHORITY_REQUIRED"


@dataclass(frozen=True)
class ImpactEnvelope:
    level: IncidentLevel
    observed_object_kind: str
    observed_object_id: str
    affected_actions: tuple[str, ...]
    unaffected_actions: tuple[str, ...]
    does_not_imply: tuple[str, ...]
    recovery_owner: str
    escalate_to: str
    escalate_when: tuple[str, ...]
    user_question: str | None = None
    technical: bool = False


_ORDER = {level: index for index, level in enumerate(IncidentLevel)}


def validate_impact(envelope: ImpactEnvelope) -> list[str]:
    errors: list[str] = []
    for name in ("observed_object_kind", "observed_object_id", "recovery_owner", "escalate_to"):
        if not str(getattr(envelope, name)).strip():
            errors.append(f"{name} is required")
    if not envelope.affected_actions:
        errors.append("affected_actions must not be empty")
    if not envelope.does_not_imply:
        errors.append("does_not_imply must not be empty")
    if envelope.level == IncidentLevel.E5_USER_AUTHORITY_REQUIRED:
        if not (envelope.user_question and envelope.user_question.strip().endswith("?")):
            errors.append("E5 requires a concrete user question")
    else:
        if envelope.user_question:
            errors.append("user_question is only valid for E5")
    if envelope.level in {IncidentLevel.E1_EXACT_OPERATION_INCIDENT, IncidentLevel.E2_ASSIGNMENT_RECOVERY}:
        forbidden = {"root_session_stopped", "direction_paused", "direction_retired", "portfolio_disposition"}
        if forbidden.intersection(envelope.affected_actions):
            errors.append("E1/E2 cannot claim a broader stop or disposition")
    if envelope.level == IncidentLevel.E3_DOMAIN_OWNER_DECISION and envelope.technical:
        if "scientific_disposition" in envelope.affected_actions:
            errors.append("technical E3 cannot create scientific disposition")
    return errors


def default_route(envelope: ImpactEnvelope) -> str:
    routes = {
        IncidentLevel.E0_OBSERVATION: "CURRENT_EXECUTOR",
        IncidentLevel.E1_EXACT_OPERATION_INCIDENT: envelope.recovery_owner or "OPERATOR_OR_TRANSPORT",
        IncidentLevel.E2_ASSIGNMENT_RECOVERY: envelope.recovery_owner or "CM_OR_WORKFLOW_RECOVERY_MANAGER",
        IncidentLevel.E3_DOMAIN_OWNER_DECISION: envelope.escalate_to or "DOMAIN_OWNER",
        IncidentLevel.E4_CROSS_OWNER_DECISION: envelope.escalate_to or "ROOT_OR_PORTFOLIO",
        IncidentLevel.E5_USER_AUTHORITY_REQUIRED: "USER",
    }
    return routes[envelope.level]


def may_escalate(envelope: ImpactEnvelope, target_level: IncidentLevel) -> bool:
    if validate_impact(envelope):
        return False
    if target_level == IncidentLevel.E5_USER_AUTHORITY_REQUIRED:
        return envelope.level == IncidentLevel.E5_USER_AUTHORITY_REQUIRED
    return _ORDER[target_level] >= _ORDER[envelope.level]
