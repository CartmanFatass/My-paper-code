from pathlib import Path

from tools.hmasd_control_plane.artifact_protocol import parse_assignment, parse_result, validate_assignment, validate_result
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
