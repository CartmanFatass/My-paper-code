from tools.hmasd_control_plane.incident_scope import ImpactEnvelope, IncidentLevel, default_route, may_escalate, validate_impact


def envelope(level=IncidentLevel.E1_EXACT_OPERATION_INCIDENT, **kwargs):
    values = dict(affected_actions=("send_exact_turn",), unaffected_actions=("inspect_state",), does_not_imply=("direction_paused",), recovery_owner="CM:scope", escalate_to="ROOT", escalate_when=())
    values.update(kwargs)
    return ImpactEnvelope(level, "operation", "op-1", **values)


def test_e1_stays_below_user():
    item = envelope()
    assert validate_impact(item) == []
    assert default_route(item) == "CM:scope"
    assert not may_escalate(item, IncidentLevel.E5_USER_AUTHORITY_REQUIRED)


def test_e2_cannot_claim_direction_pause():
    item = envelope(IncidentLevel.E2_ASSIGNMENT_RECOVERY, affected_actions=("direction_paused",))
    assert validate_impact(item)


def test_e5_requires_question_and_nonempty_does_not_imply():
    assert validate_impact(envelope(IncidentLevel.E5_USER_AUTHORITY_REQUIRED, user_question="May I continue?")) == []
    assert validate_impact(envelope(IncidentLevel.E5_USER_AUTHORITY_REQUIRED, user_question="May I continue?", does_not_imply=()))
