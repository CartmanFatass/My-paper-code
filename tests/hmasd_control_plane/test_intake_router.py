from dataclasses import replace

import pytest

from tools.hmasd_control_plane.artifact_protocol import (
    AssignmentArtifact,
    ResultArtifact,
    parse_result,
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


def test_parent_cannot_upgrade_unobserved_recovery():
    decision = route_result(wrm_assignment(), unobserved_recovery_result(), {})
    assert decision.disposition_created is False
    assert decision.root_action == "ROUTE_SCOPE_LOCAL"


def test_incomplete_wrm_non_recovery_e4_keeps_disposition():
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
    result = replace(unobserved_recovery_result(), impact=impact)
    decision = route_result(wrm_assignment(), result, {})
    assert decision.disposition_created is True
    assert decision.root_action == "ROUTE_SCOPE_LOCAL"


def test_recovery_disposition_requires_nonblank_assignment_outcome():
    result = replace(
        unobserved_recovery_result(),
        result_kind="COMPLETED",
        acceptance_observed="TRUE",
        acceptance_evidence=("docs/session/runtime-boundary.md",),
    )
    legacy_assignment = replace(wrm_assignment(), acceptance_outcome="")
    decision = route_result(legacy_assignment, result, {})
    assert decision.disposition_created is False
    assert decision.root_action == "ROUTE_SCOPE_LOCAL"


def test_recovered_claim_in_prose_has_no_intake_effect(tmp_path):
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
    result = parse_result(path)
    assert result.acceptance_observed == "UNKNOWN"
    decision = route_result(wrm_assignment(), result, {})
    assert decision.disposition_created is False
    assert decision.root_action == "ROUTE_SCOPE_LOCAL"
