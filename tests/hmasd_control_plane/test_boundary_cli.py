import json

from tools.hmasd_control_plane import boundary_cli
from tools.hmasd_control_plane.intake_router import IntakeDecision


def _write_incident_artifacts(tmp_path, *, assignment_id="asg_cli", author_role="hmasd-implementer"):
    (tmp_path / "docs/project").mkdir(parents=True)
    (tmp_path / "docs/project/PROJECT_MAP.md").write_text(
        "## Route\n", encoding="utf-8"
    )
    (tmp_path / "docs/project/PROJECT_REQUIREMENTS.toml").write_text(
        "requirements = []\n", encoding="utf-8"
    )
    (tmp_path / "consumer.py").write_text("", encoding="utf-8")
    (tmp_path / "input.py").write_text("", encoding="utf-8")
    assignment_path = tmp_path / "assignment.md"
    assignment_path.write_text(
        f"""```toml hmasd-assignment
schema_version=2
assignment_id='{assignment_id}'
assignment_mode='IMPLEMENTATION'
semantic_owner='CM:x'
executor_role='hmasd-implementer'
return_to='CM:x'
strictness_profile='R1_ROUTINE_ENGINEERING'
evidence_class='B'
result_bearing=false
runtime_profile=''
requirement_ids=[]
nonrequirement_ids=[]
recovery_owner='CM:x'
result_path='result.md'
project_map_anchor='Route'
architecture_role='ENTRYPOINT'
affected_files=['consumer.py']
create_files=[]
affected_symbols=['f']
search_roots=[]
direct_consumers=['consumer.py']
upstream_inputs=['input.py']
state_owner='f'
non_target_surfaces=['science']
```

## Outcome

The consumer receives the value.
""",
        encoding="utf-8",
    )
    result_path = tmp_path / "result.md"
    result_path.write_text(
        f"""```toml hmasd-result
schema_version=2
assignment_id='{assignment_id}'
result_kind='INCIDENT'
author_role='{author_role}'
owner_return='CM:x'
project_map_anchor='Route'
files_observed=['consumer.py']
files_changed=[]
symbols_changed=[]
direct_consumer_checked='consumer.py'
```

```toml hmasd-impact
incident_level='E1_EXACT_OPERATION_INCIDENT'
observed_object_kind='runtime'
observed_object_id='run-1'
affected_actions=['retry_exact_operation']
unaffected_actions=['continue_other_work']
does_not_imply=['direction_paused']
recovery_owner='CM:x'
escalate_to='ROOT'
escalate_when=[]
```
""",
        encoding="utf-8",
    )
    return assignment_path, result_path


def _run_incident(tmp_path, assignment_path, result_path):
    return boundary_cli.main(
        [
            "incident",
            str(result_path),
            "--assignment",
            str(assignment_path),
            "--requirements",
            str(tmp_path / "docs/project/PROJECT_REQUIREMENTS.toml"),
        ]
    )


def test_incident_rejects_invalid_assignment_without_routing(
    monkeypatch, capsys, tmp_path
):
    assignment_path, result_path = _write_incident_artifacts(
        tmp_path, assignment_id="invalid"
    )
    monkeypatch.setattr(
        boundary_cli,
        "route_result",
        lambda *_: (_ for _ in ()).throw(AssertionError("route_result called")),
    )

    exit_code = _run_incident(tmp_path, assignment_path, result_path)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["valid"] is False
    assert payload["errors"]["assignment"]
    assert payload["errors"]["result"] == []


def test_incident_rejects_invalid_result_without_routing(monkeypatch, capsys, tmp_path):
    assignment_path, result_path = _write_incident_artifacts(
        tmp_path, author_role="hmasd-reviewer"
    )
    monkeypatch.setattr(
        boundary_cli,
        "route_result",
        lambda *_: (_ for _ in ()).throw(AssertionError("route_result called")),
    )

    exit_code = _run_incident(tmp_path, assignment_path, result_path)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["valid"] is False
    assert payload["errors"]["assignment"] == []
    assert "author_role does not match assignment executor_role" in payload["errors"]["result"]


def test_incident_routes_only_after_complete_validation(monkeypatch, capsys, tmp_path):
    assignment_path, result_path = _write_incident_artifacts(tmp_path)
    calls = []

    def route(assignment, result, requirements):
        calls.append((assignment, result, requirements))
        return IntakeDecision(
            "E1_EXACT_OPERATION_INCIDENT",
            "CM:x",
            "ROUTE_SCOPE_LOCAL",
            None,
            True,
            False,
        )

    monkeypatch.setattr(boundary_cli, "route_result", route)

    exit_code = _run_incident(tmp_path, assignment_path, result_path)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["route_to"] == "CM:x"
    assert len(calls) == 1
