"""Owner-gated result intake and incident routing."""

from __future__ import annotations

from dataclasses import dataclass

from .artifact_protocol import AssignmentArtifact, ResultArtifact
from .incident_scope import IncidentLevel, validate_impact
from .requirements_registry import Requirement


@dataclass(frozen=True)
class IntakeDecision:
    incident_level: str
    route_to: str
    root_action: str
    user_question: str | None
    continuation_allowed: bool
    disposition_created: bool


def route_result(assignment: AssignmentArtifact, result: ResultArtifact, registry: dict[str, Requirement]) -> IntakeDecision:
    if result.assignment_id != assignment.assignment_id:
        raise ValueError("assignment/result identity mismatch")
    if result.impact is None:
        return IntakeDecision("E0_OBSERVATION", "OWNER_INTAKE", "NO_DECISION", None, True, False)
    errors = validate_impact(result.impact)
    if errors:
        raise ValueError("invalid impact envelope: " + "; ".join(errors))
    level = result.impact.level
    forbidden = set(result.impact.affected_actions)
    if level == IncidentLevel.E1_EXACT_OPERATION_INCIDENT and ("root_session_stopped" in forbidden or "user_authority_required" in forbidden):
        raise ValueError("E1 cannot claim root stop or user authority")
    if level == IncidentLevel.E2_ASSIGNMENT_RECOVERY and {"direction_retired", "direction_paused"}.intersection(forbidden):
        raise ValueError("E2 cannot create direction disposition")
    if level == IncidentLevel.E3_DOMAIN_OWNER_DECISION and result.impact.technical and "scientific_disposition" in forbidden:
        raise ValueError("technical E3 cannot create scientific disposition")
    routes = {
        IncidentLevel.E1_EXACT_OPERATION_INCIDENT: result.impact.recovery_owner,
        IncidentLevel.E2_ASSIGNMENT_RECOVERY: result.impact.recovery_owner,
        IncidentLevel.E3_DOMAIN_OWNER_DECISION: result.impact.escalate_to,
        IncidentLevel.E4_CROSS_OWNER_DECISION: result.impact.escalate_to,
        IncidentLevel.E5_USER_AUTHORITY_REQUIRED: "USER",
    }
    return IntakeDecision(
        level.value,
        routes[level],
        "USER_QUESTION_REQUIRED" if level == IncidentLevel.E5_USER_AUTHORITY_REQUIRED else "ROUTE_SCOPE_LOCAL",
        result.impact.user_question,
        level != IncidentLevel.E5_USER_AUTHORITY_REQUIRED,
        False,
    )
