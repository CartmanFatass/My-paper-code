from dataclasses import replace

import pytest

from tools.hmasd_control_plane.artifact_protocol import (
    AssignmentArtifact,
    ResultArtifact,
    parse_result,
    validate_result,
)
from tools.hmasd_control_plane.incident_scope import ImpactEnvelope, IncidentLevel
from tools.hmasd_control_plane.intake_router import route_result


def assignment():
    return AssignmentArtifact("asg_x", "OPERATION", "CM:x", "hmasd-implementer", "CM:x", "R1_ROUTINE_ENGINEERING", "B", False, None, (), (), "CM:x", "result.md", "Route", "ENTRYPOINT", (), (), (), (), ("consumer.py",), (), "state", ("science",))


def wrm_assignment():
    return replace(
        assignment(),
        executor_role="hmasd-workflow-recovery-manager",
        acceptance_outcome="The original operation succeeds end to end.",
    )


def unobserved_recovery_result():
    impact = ImpactEnvelope(
        IncidentLevel.E3_DOMAIN_OWNER_DECISION,
        "runtime",
        "run-1",
        ("accept_recovery",),
        ("continue_scope_local_repair",),
        ("recovery_completed",),
        "CM:x",
        "ROOT",
        (),
    )
    return ResultArtifact(
        "asg_x",
        "PARTIAL",
        "hmasd-workflow-recovery-manager",
        "CM:x",
        "Route",
        (),
        (),
        (),
        "consumer.py",
        impact,
        acceptance_observed="FALSE",
        acceptance_evidence=("docs/session/runtime-boundary.md",),
    )


def test_e1_does_not_request_user(tmp_path):
    assigned = repository_assignment(tmp_path)
    impact = ImpactEnvelope(IncidentLevel.E1_EXACT_OPERATION_INCIDENT, "agentify_operation", "op-1", ("resend_exact_operation",), ("inspect_existing_provider_state",), ("direction_paused", "root_session_stopped"), "WORKFLOW_RECOVERY_MANAGER", "OPERATIONAL_ROOT", ())
    result = repository_result(assigned, impact=impact)
    decision = route_result(assigned, result, {})
    assert decision.route_to == "WORKFLOW_RECOVERY_MANAGER"
    assert decision.user_question is None
    assert decision.continuation_allowed


def test_invalid_e2_direction_stop_is_rejected(tmp_path):
    assigned = repository_assignment(tmp_path)
    impact = ImpactEnvelope(IncidentLevel.E2_ASSIGNMENT_RECOVERY, "runtime", "run-1", ("direction_retired",), (), ("user_authority_required",), "CM:x", "ROOT", ())
    result = repository_result(assigned, impact=impact)
    with pytest.raises(ValueError):
        route_result(assigned, result, {})


def test_parent_cannot_upgrade_unobserved_recovery(tmp_path):
    assigned = repository_assignment(tmp_path, recovery=True)
    result = repository_result(
        assigned,
        impact=unobserved_recovery_result().impact,
        result_kind="PARTIAL",
        acceptance_observed="FALSE",
        acceptance_evidence=("docs/session/runtime-boundary.md",),
    )
    decision = route_result(assigned, result, {})
    assert decision.disposition_created is False
    assert decision.root_action == "ROUTE_SCOPE_LOCAL"


def test_incomplete_wrm_non_recovery_e4_keeps_disposition(tmp_path):
    assigned = repository_assignment(tmp_path, recovery=True)
    impact = ImpactEnvelope(
        IncidentLevel.E4_CROSS_OWNER_DECISION,
        "cross_owner_dependency",
        "handoff-1",
        ("coordinate_cross_owner_dependency",),
        ("continue_scope_local_repair",),
        ("recovery_completed",),
        "CM:x",
        "ROOT",
        (),
    )
    result = repository_result(
        assigned,
        impact=impact,
        result_kind="PARTIAL",
        acceptance_observed="FALSE",
        acceptance_evidence=("docs/session/runtime-boundary.md",),
    )
    decision = route_result(assigned, result, {})
    assert decision.disposition_created is True
    assert decision.root_action == "ROUTE_SCOPE_LOCAL"


def test_recovery_disposition_requires_nonblank_assignment_outcome(tmp_path):
    assigned = replace(
        repository_assignment(tmp_path, recovery=True), acceptance_outcome=""
    )
    result = repository_result(
        assigned,
        impact=unobserved_recovery_result().impact,
        result_kind="COMPLETED",
        acceptance_observed="TRUE",
        acceptance_evidence=("docs/session/runtime-boundary.md",),
    )

    with pytest.raises(ValueError, match="assignment validation failed"):
        route_result(assigned, result, {})


def test_recovered_claim_in_prose_has_no_intake_effect(tmp_path):
    assigned = repository_assignment(tmp_path, recovery=True)
    path = tmp_path / "result.md"
    path.write_text(
        """```toml hmasd-result
schema_version=2
assignment_id='asg_x'
result_kind='PARTIAL'
author_role='hmasd-workflow-recovery-manager'
owner_return='CM:x'
project_map_anchor='Route'
files_observed=[]
files_changed=[]
symbols_changed=[]
direct_consumer_checked='consumer.py'
```

```toml hmasd-impact
incident_level='E3_DOMAIN_OWNER_DECISION'
observed_object_kind='runtime'
observed_object_id='run-1'
affected_actions=['accept_recovery']
unaffected_actions=['continue_scope_local_repair']
does_not_imply=['recovery_completed']
recovery_owner='CM:x'
escalate_to='ROOT'
escalate_when=[]
```

## Conclusion

RECOVERED: the parent should accept this recovery.
""",
        encoding="utf-8",
    )
    result = replace(parse_result(path), assignment_id=assigned.assignment_id)
    assert result.acceptance_observed == "UNKNOWN"
    decision = route_result(assigned, result, {})
    assert decision.disposition_created is False
    assert decision.root_action == "ROUTE_SCOPE_LOCAL"


def test_recovery_disposition_rejects_unvalidated_evidence_reference(tmp_path):
    assigned = repository_assignment(tmp_path, recovery=True)
    result = repository_result(
        assigned,
        impact=unobserved_recovery_result().impact,
        result_kind="COMPLETED",
        acceptance_observed="TRUE",
        acceptance_evidence=("docs/session/missing.json",),
        files_observed=("docs/session/missing.json",),
    )

    with pytest.raises(ValueError, match="result validation failed"):
        route_result(assigned, result, {})


def test_recovery_disposition_accepts_existing_observed_evidence_reference(tmp_path):
    assigned = repository_assignment(tmp_path, recovery=True)
    evidence = tmp_path / "docs/session/runtime-boundary.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("{}\n", encoding="utf-8")
    result = repository_result(
        assigned,
        impact=unobserved_recovery_result().impact,
        result_kind="COMPLETED",
        acceptance_observed="TRUE",
        acceptance_evidence=("docs/session/runtime-boundary.json",),
        files_observed=("docs/session/runtime-boundary.json",),
    )

    decision = route_result(assigned, result, {})

    assert decision.disposition_created is True


def repository_assignment(tmp_path, *, recovery=False, requirement_ids=()):
    (tmp_path / "docs/project").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/project/PROJECT_MAP.md").write_text(
        "## Route\n", encoding="utf-8"
    )
    (tmp_path / "consumer.py").write_text("", encoding="utf-8")
    (tmp_path / "input.py").write_text("", encoding="utf-8")
    assignment_path = tmp_path / "assignment.md"
    assignment_path.write_text("assignment\n", encoding="utf-8")
    return AssignmentArtifact(
        "asg_route",
        "OPERATION",
        "CM:x",
        "hmasd-workflow-recovery-manager" if recovery else "hmasd-implementer",
        "CM:x",
        "R1_ROUTINE_ENGINEERING",
        "B",
        False,
        None,
        requirement_ids,
        (),
        "CM:x",
        "result.md",
        "Route",
        "ENTRYPOINT",
        ("consumer.py",),
        (),
        ("f",),
        (),
        ("consumer.py",),
        ("input.py",),
        "f",
        ("science",),
        outcome="The consumer receives the value.",
        source_path=str(assignment_path),
        acceptance_outcome=(
            "The original operation succeeds end to end." if recovery else ""
        ),
    )


def repository_result(assigned, *, impact=None, **changes):
    result = ResultArtifact(
        assigned.assignment_id,
        "INCIDENT" if impact else "COMPLETED",
        assigned.executor_role,
        assigned.return_to,
        assigned.project_map_anchor,
        ("consumer.py",),
        (),
        (),
        "consumer.py",
        impact,
    )
    return replace(result, **changes)


def test_direct_route_rejects_unknown_assignment_requirement(tmp_path):
    assigned = repository_assignment(
        tmp_path, requirement_ids=("req_unknown",)
    )
    result = repository_result(assigned)

    with pytest.raises(ValueError, match="assignment validation failed"):
        route_result(assigned, result, {})


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("author_role", "hmasd-reviewer"),
        ("owner_return", "ROOT"),
        ("project_map_anchor", "Different anchor"),
    ),
)
def test_direct_route_rejects_result_identity_contract_violations(
    tmp_path, field, value
):
    assigned = repository_assignment(tmp_path)
    result = repository_result(assigned, **{field: value})

    with pytest.raises(ValueError, match="result validation failed"):
        route_result(assigned, result, {})


def test_direct_route_rejects_non_wrm_completed_result_with_impact(tmp_path):
    assigned = repository_assignment(tmp_path)
    impact = ImpactEnvelope(
        IncidentLevel.E3_DOMAIN_OWNER_DECISION,
        "runtime",
        "run-1",
        ("accept_recovery",),
        ("continue_other_work",),
        ("direction_paused",),
        "CM:x",
        "ROOT",
        (),
    )
    result = repository_result(assigned, impact=impact, result_kind="COMPLETED")

    with pytest.raises(ValueError, match="result validation failed"):
        route_result(assigned, result, {})


def test_direct_route_rejects_unknown_result_kind(tmp_path):
    assigned = repository_assignment(tmp_path)
    result = repository_result(assigned, result_kind="UNREGISTERED")

    with pytest.raises(ValueError, match="result validation failed"):
        route_result(assigned, result, {})


def test_direct_route_accepts_narrow_valid_wrm_completed_recovery_claim(tmp_path):
    assigned = repository_assignment(tmp_path, recovery=True)
    evidence = tmp_path / "docs/session/runtime-boundary.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("{}\n", encoding="utf-8")
    impact = ImpactEnvelope(
        IncidentLevel.E3_DOMAIN_OWNER_DECISION,
        "runtime",
        "run-1",
        ("accept_recovery",),
        ("continue_other_work",),
        ("direction_paused",),
        "CM:x",
        "ROOT",
        (),
    )
    result = repository_result(
        assigned,
        impact=impact,
        result_kind="COMPLETED",
        files_observed=("consumer.py", "docs/session/runtime-boundary.json"),
        acceptance_observed="TRUE",
        acceptance_evidence=("docs/session/runtime-boundary.json",),
    )

    assert validate_result(result, assigned) == []
    decision = route_result(assigned, result, {})

    assert decision.disposition_created is True
    assert decision.route_to == "ROOT"


@pytest.mark.parametrize(
    "extra_action",
    ("direction_retired", "coordinate_cross_owner_dependency"),
)
def test_direct_route_rejects_wrm_recovery_claim_with_extra_action(
    tmp_path, extra_action
):
    assigned = repository_assignment(tmp_path, recovery=True)
    evidence = tmp_path / "docs/session/runtime-boundary.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("{}\n", encoding="utf-8")
    impact = ImpactEnvelope(
        IncidentLevel.E3_DOMAIN_OWNER_DECISION,
        "runtime",
        "run-1",
        ("accept_recovery", extra_action),
        ("continue_other_work",),
        ("direction_paused",),
        "CM:x",
        "ROOT",
        (),
    )
    result = repository_result(
        assigned,
        impact=impact,
        result_kind="COMPLETED",
        files_observed=("consumer.py", "docs/session/runtime-boundary.json"),
        acceptance_observed="TRUE",
        acceptance_evidence=("docs/session/runtime-boundary.json",),
    )

    with pytest.raises(ValueError, match="result validation failed"):
        route_result(assigned, result, {})


def test_direct_route_preserves_valid_legacy_non_recovery_incident(tmp_path):
    assigned = repository_assignment(tmp_path)
    impact = ImpactEnvelope(
        IncidentLevel.E1_EXACT_OPERATION_INCIDENT,
        "runtime",
        "run-1",
        ("retry_exact_operation",),
        ("continue_other_work",),
        ("direction_paused",),
        "CM:x",
        "ROOT",
        (),
    )
    result = repository_result(assigned, impact=impact)

    decision = route_result(assigned, result, {})

    assert decision.route_to == "CM:x"
    assert decision.disposition_created is False
