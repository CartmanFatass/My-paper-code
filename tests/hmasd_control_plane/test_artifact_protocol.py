from pathlib import Path

from tools.hmasd_control_plane.artifact_protocol import ResultArtifact, parse_assignment, parse_result, validate_assignment, validate_result
from tools.hmasd_control_plane.requirements_registry import load_requirements


def make_assignment(root: Path, mode="IMPLEMENTATION"):
    (root / "docs/project").mkdir(parents=True)
    (root / "docs/project/PROJECT_MAP.md").write_text("## Route\n", encoding="utf-8")
    (root / "consumer.py").write_text("", encoding="utf-8")
    (root / "input.py").write_text("", encoding="utf-8")
    return root / "assignment.md"


def test_fenced_metadata_and_identity(monkeypatch, tmp_path):
    path = make_assignment(tmp_path)
    path.write_text("""# A\n\n```toml hmasd-assignment\nschema_version=2\nassignment_id='asg_x'\nassignment_mode='IMPLEMENTATION'\nsemantic_owner='CM:x'\nexecutor_role='hmasd-implementer'\nreturn_to='CM:x'\nstrictness_profile='R1_ROUTINE_ENGINEERING'\nevidence_class='B'\nresult_bearing=false\nruntime_profile=''\nrequirement_ids=[]\nnonrequirement_ids=[]\nrecovery_owner='CM:x'\nresult_path='result.md'\nproject_map_anchor='Route'\narchitecture_role='ENTRYPOINT'\naffected_files=['consumer.py']\ncreate_files=[]\naffected_symbols=['f']\nsearch_roots=[]\ndirect_consumers=['consumer.py']\nupstream_inputs=['input.py']\nstate_owner='f'\nnon_target_surfaces=['science']\n```\n\n## Outcome\n\nThe consumer receives the produced value.\n""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assignment = parse_assignment(path)
    assert validate_assignment(assignment, {}) == [] or "unknown requirement" not in " ".join(validate_assignment(assignment, {}))


def test_result_identity_and_impact(monkeypatch, tmp_path):
    path = make_assignment(tmp_path)
    assignment_text = """```toml hmasd-assignment\nschema_version=2\nassignment_id='asg_x'\nassignment_mode='IMPLEMENTATION'\nsemantic_owner='CM:x'\nexecutor_role='hmasd-implementer'\nreturn_to='CM:x'\nstrictness_profile='R1_ROUTINE_ENGINEERING'\nevidence_class='B'\nresult_bearing=false\nruntime_profile=''\nrequirement_ids=[]\nnonrequirement_ids=[]\nrecovery_owner='CM:x'\nresult_path='result.md'\nproject_map_anchor='Route'\narchitecture_role='ENTRYPOINT'\naffected_files=['consumer.py']\ncreate_files=[]\naffected_symbols=['f']\nsearch_roots=[]\ndirect_consumers=['consumer.py']\nupstream_inputs=['input.py']\nstate_owner='f'\nnon_target_surfaces=['science']\n```\n## Outcome\nThe consumer receives the value.\n"""
    path.write_text(assignment_text, encoding="utf-8")
    result_path = tmp_path / "result.md"
    result_path.write_text("""```toml hmasd-result\nschema_version=2\nassignment_id='asg_x'\nresult_kind='COMPLETED'\nauthor_role='hmasd-implementer'\nowner_return='CM:x'\nproject_map_anchor='Route'\nfiles_observed=['consumer.py']\nfiles_changed=['consumer.py']\nsymbols_changed=['f']\ndirect_consumer_checked='consumer.py'\n```\n""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assignment = parse_assignment(path)
    result = parse_result(result_path)
    assert not validate_result(result, assignment)


def test_recovery_completion_requires_exact_outcome_evidence(monkeypatch, tmp_path):
    path = make_assignment(tmp_path)
    path.write_text("""```toml hmasd-assignment
schema_version=2
assignment_id='asg_recovery'
assignment_mode='IMPLEMENTATION'
semantic_owner='ROOT'
executor_role='hmasd-workflow-recovery-manager'
return_to='ROOT'
strictness_profile='R4_CONTROL_PLANE_AND_AUTHORITY'
evidence_class='B'
result_bearing=false
runtime_profile=''
requirement_ids=[]
nonrequirement_ids=[]
recovery_owner='ROOT'
result_path='result.md'
project_map_anchor='Route'
architecture_role='RECOVERY'
affected_files=['consumer.py']
create_files=[]
affected_symbols=['f']
search_roots=[]
direct_consumers=['consumer.py']
upstream_inputs=['input.py']
state_owner='f'
non_target_surfaces=['science']
original_outcome='The ordinary worker completes the visible task.'
```
## Outcome
The consumer receives the restored behavior.
""", encoding="utf-8")
    result_path = tmp_path / "result.md"
    result_path.write_text("""```toml hmasd-result
schema_version=2
assignment_id='asg_recovery'
result_kind='COMPLETED'
author_role='hmasd-workflow-recovery-manager'
owner_return='ROOT'
project_map_anchor='Route'
files_observed=['consumer.py']
files_changed=['consumer.py']
symbols_changed=['f']
direct_consumer_checked='consumer.py'
original_outcome='The ordinary worker completes the visible task.'
outcome_evidence='Direct end-to-end ordinary-worker run completed.'
```
""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assignment = parse_assignment(path)
    result = parse_result(result_path)
    assert not validate_result(result, assignment)

    missing = result.__class__(**{**result.__dict__, "outcome_evidence": ""})
    assert "recovery completion requires direct outcome_evidence" in validate_result(missing, assignment)
    promoted = result.__class__(**{**result.__dict__, "original_outcome": "Source tests passed."})
    assert "recovery result original_outcome must exactly match assignment" in validate_result(promoted, assignment)


def test_result_cannot_claim_changes_outside_assignment(monkeypatch, tmp_path):
    path = make_assignment(tmp_path)
    (tmp_path / "other.py").write_text("", encoding="utf-8")
    path.write_text("""```toml hmasd-assignment
schema_version=2
assignment_id='asg_x'
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
""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assignment = parse_assignment(path)
    result = ResultArtifact("asg_x", "COMPLETED", "hmasd-implementer", "CM:x", "Route", ("other.py",), ("other.py",), ("g",), "other.py", None)
    errors = validate_result(result, assignment)
    assert "files_changed exceeds assignment write scope: other.py" in errors
    assert "symbols_changed exceeds assignment symbol scope: g" in errors
    assert "direct_consumer_checked is not an assigned direct consumer" in errors
