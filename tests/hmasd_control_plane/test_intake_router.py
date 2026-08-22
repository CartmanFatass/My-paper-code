import pytest

from tools.hmasd_control_plane.artifact_protocol import AssignmentArtifact, ResultArtifact
from tools.hmasd_control_plane.incident_scope import ImpactEnvelope, IncidentLevel
from tools.hmasd_control_plane.intake_router import route_result


def assignment():
    return AssignmentArtifact("asg_x", "OPERATION", "CM:x", "hmasd-implementer", "CM:x", "R1_ROUTINE_ENGINEERING", "B", False, None, (), (), "CM:x", "result.md", "Route", "ENTRYPOINT", (), (), (), (), ("consumer.py",), (), "state", ("science",))


def test_e1_does_not_request_user():
    impact = ImpactEnvelope(IncidentLevel.E1_EXACT_OPERATION_INCIDENT, "agentify_operation", "op-1", ("resend_exact_operation",), ("inspect_existing_provider_state",), ("direction_paused", "root_session_stopped"), "WORKFLOW_RECOVERY_MANAGER", "OPERATIONAL_ROOT", ())
    result = ResultArtifact("asg_x", "INCIDENT", "hmasd-implementer", "CM:x", "Route", (), (), (), "consumer.py", impact)
    decision = route_result(assignment(), result, {})
    assert decision.route_to == "WORKFLOW_RECOVERY_MANAGER"
    assert decision.user_question is None
    assert decision.continuation_allowed


def test_invalid_e2_direction_stop_is_rejected():
    impact = ImpactEnvelope(IncidentLevel.E2_ASSIGNMENT_RECOVERY, "runtime", "run-1", ("direction_retired",), (), ("user_authority_required",), "CM:x", "ROOT", ())
    result = ResultArtifact("asg_x", "INCIDENT", "hmasd-implementer", "CM:x", "Route", (), (), (), "consumer.py", impact)
    with pytest.raises(ValueError):
        route_result(assignment(), result, {})
