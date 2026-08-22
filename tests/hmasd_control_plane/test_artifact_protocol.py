from dataclasses import replace
from pathlib import Path
import tempfile

import pytest

from tools.hmasd_control_plane.artifact_protocol import (
    AssignmentArtifact,
    ResultArtifact,
    parse_assignment,
    parse_result,
    validate_assignment,
    validate_result,
)
from tools.hmasd_control_plane.requirements_registry import load_requirements


def make_assignment(root: Path, mode="IMPLEMENTATION"):
    (root / "docs/project").mkdir(parents=True)
    (root / "docs/project/PROJECT_MAP.md").write_text("## Route\n", encoding="utf-8")
    (root / "consumer.py").write_text("", encoding="utf-8")
    (root / "input.py").write_text("", encoding="utf-8")
    return root / "assignment.md"


@pytest.fixture
def valid_assignment(tmp_path):
    path = make_assignment(tmp_path)
    return AssignmentArtifact(
        assignment_id="asg_x",
        assignment_mode="IMPLEMENTATION",
        semantic_owner="CM:x",
        executor_role="hmasd-implementer",
        return_to="CM:x",
        strictness_profile="R1_ROUTINE_ENGINEERING",
        evidence_class="B",
        result_bearing=False,
        runtime_profile=None,
        requirement_ids=(),
        nonrequirement_ids=(),
        recovery_owner="CM:x",
        result_path="result.md",
        project_map_anchor="Route",
        architecture_role="ENTRYPOINT",
        affected_files=("consumer.py",),
        create_files=(),
        affected_symbols=("f",),
        search_roots=(),
        direct_consumers=("consumer.py",),
        upstream_inputs=("input.py",),
        state_owner="f",
        non_target_surfaces=("science",),
        outcome="The consumer receives the produced value.",
        source_path=str(path),
    )


@pytest.fixture
def valid_wrm_assignment(valid_assignment):
    return replace(
        valid_assignment,
        executor_role="hmasd-workflow-recovery-manager",
        acceptance_outcome="The original consumer behavior works end to end.",
    )


@pytest.fixture
def valid_result():
    def make_result(**changes):
        result = ResultArtifact(
            assignment_id="asg_x",
            result_kind="COMPLETED",
            author_role="hmasd-workflow-recovery-manager",
            owner_return="CM:x",
            project_map_anchor="Route",
            files_observed=("consumer.py",),
            files_changed=("consumer.py",),
            symbols_changed=("f",),
            direct_consumer_checked="consumer.py",
            impact=None,
        )
        return replace(result, **changes)

    return make_result


def test_fenced_metadata_and_identity(monkeypatch, tmp_path):
    path = make_assignment(tmp_path)
    path.write_text("""# A\n\n```toml hmasd-assignment\nschema_version=2\nassignment_id='asg_x'\nassignment_mode='IMPLEMENTATION'\nsemantic_owner='CM:x'\nexecutor_role='hmasd-implementer'\nreturn_to='CM:x'\nstrictness_profile='R1_ROUTINE_ENGINEERING'\nevidence_class='B'\nresult_bearing=false\nruntime_profile=''\nrequirement_ids=[]\nnonrequirement_ids=[]\nrecovery_owner='CM:x'\nresult_path='result.md'\nproject_map_anchor='Route'\narchitecture_role='ENTRYPOINT'\naffected_files=['consumer.py']\ncreate_files=[]\naffected_symbols=['f']\nsearch_roots=[]\ndirect_consumers=['consumer.py']\nupstream_inputs=['input.py']\nstate_owner='f'\nnon_target_surfaces=['science']\n```\n\n## Outcome\n\nThe consumer receives the produced value.\n""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assignment = parse_assignment(path)
    assert assignment.acceptance_outcome == ""
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
    assert result.acceptance_observed == "UNKNOWN"
    assert result.acceptance_evidence == ()
    assert not validate_result(result, assignment)


def test_wrm_assignment_requires_acceptance_outcome(valid_assignment):
    assignment = replace(
        valid_assignment,
        executor_role="hmasd-workflow-recovery-manager",
        acceptance_outcome="",
    )
    assert "WRM assignment requires acceptance_outcome" in validate_assignment(
        assignment, {}
    )


def test_reviewer_role_is_registered(valid_assignment):
    assignment = replace(
        valid_assignment,
        assignment_mode="REVIEW",
        executor_role="hmasd-reviewer",
    )

    assert not any(
        error.startswith("unknown executor_role:")
        for error in validate_assignment(assignment, {})
    )


def test_file_empty_review_accepts_real_bounded_search_roots(
    valid_assignment, tmp_path
):
    for search_root in (
        "tools/codex_context_lifecycle",
        "tools/hmasd_control_plane",
    ):
        (tmp_path / search_root).mkdir(parents=True)
    assignment = replace(
        valid_assignment,
        assignment_mode="REVIEW",
        executor_role="hmasd-reviewer",
        affected_files=(),
        create_files=(),
        search_roots=(
            "tools/codex_context_lifecycle",
            "tools/hmasd_control_plane",
            "docs/project",
        ),
    )

    assert validate_assignment(assignment, {}) == []


def test_file_empty_review_requires_search_roots(valid_assignment):
    assignment = replace(
        valid_assignment,
        assignment_mode="REVIEW",
        executor_role="hmasd-reviewer",
        affected_files=(),
        create_files=(),
        search_roots=(),
    )

    assert "REVIEW assignment requires exact files or bounded search_roots" in (
        validate_assignment(assignment, {})
    )


@pytest.mark.parametrize(
    "search_root",
    (
        ".",
        "tools",
        "..",
        "https://example.invalid/review",
        "missing/subtree",
    ),
)
def test_file_empty_review_rejects_unbounded_or_escaping_search_roots(
    valid_assignment, tmp_path, search_root
):
    (tmp_path / "tools").mkdir(exist_ok=True)
    assignment = replace(
        valid_assignment,
        assignment_mode="REVIEW",
        executor_role="hmasd-reviewer",
        affected_files=(),
        create_files=(),
        search_roots=(search_root,),
    )

    errors = validate_assignment(assignment, {})

    assert any("search_roots" in error for error in errors)


def test_file_empty_review_rejects_absolute_search_root(valid_assignment, tmp_path):
    absolute_root = tmp_path / "tools" / "hmasd_control_plane"
    absolute_root.mkdir(parents=True)
    assignment = replace(
        valid_assignment,
        assignment_mode="REVIEW",
        executor_role="hmasd-reviewer",
        affected_files=(),
        create_files=(),
        search_roots=(str(absolute_root),),
    )

    assert any(
        "search_roots" in error for error in validate_assignment(assignment, {})
    )


@pytest.mark.parametrize(
    "search_root",
    (
        ".",
        "tools",
        "..",
        "https://example.invalid/review",
        "<absolute>",
        "missing/subtree",
    ),
)
def test_review_with_affected_files_still_validates_every_search_root(
    valid_assignment, tmp_path, search_root
):
    (tmp_path / "tools").mkdir(exist_ok=True)
    if search_root == "<absolute>":
        absolute_root = tmp_path / "tools" / "hmasd_control_plane"
        absolute_root.mkdir(parents=True)
        search_root = str(absolute_root)
    assignment = replace(
        valid_assignment,
        assignment_mode="REVIEW",
        executor_role="hmasd-reviewer",
        search_roots=(search_root,),
    )

    assert any(
        "search_roots" in error for error in validate_assignment(assignment, {})
    )


def test_review_rejects_search_root_symlink_resolving_outside_repository(
    valid_assignment, tmp_path
):
    link = tmp_path / "tools" / "external_review"
    link.parent.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="hmasd-task11-outside-") as outside:
        try:
            link.symlink_to(Path(outside), target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"host refused directory symlink creation: {exc}")
        assignment = replace(
            valid_assignment,
            assignment_mode="REVIEW",
            executor_role="hmasd-reviewer",
            search_roots=("tools/external_review",),
        )

        assert "search_roots resolves outside repository: tools/external_review" in (
            validate_assignment(assignment, {})
        )


@pytest.mark.parametrize("mode", ("IMPLEMENTATION", "OPERATION"))
def test_non_review_write_modes_still_require_exact_files(
    valid_assignment, tmp_path, mode
):
    (tmp_path / "tools" / "hmasd_control_plane").mkdir(parents=True)
    assignment = replace(
        valid_assignment,
        assignment_mode=mode,
        affected_files=(),
        create_files=(),
        search_roots=("tools/hmasd_control_plane",),
    )

    assert "implementation/review/operation assignment requires exact files" in (
        validate_assignment(assignment, {})
    )


def test_wrm_completed_result_requires_observed_acceptance(
    valid_wrm_assignment, valid_result
):
    result = valid_result(
        result_kind="COMPLETED",
        acceptance_observed="UNKNOWN",
        acceptance_evidence=(),
    )
    assert (
        "WRM COMPLETED requires directly observed acceptance and evidence"
        in validate_result(result, valid_wrm_assignment)
    )


def test_explicit_recovery_fields_are_parsed(tmp_path):
    assignment_path = make_assignment(tmp_path)
    assignment_path.write_text(
        """```toml hmasd-assignment
schema_version=2
assignment_id='asg_x'
assignment_mode='OPERATION'
semantic_owner='CM:x'
executor_role='hmasd-workflow-recovery-manager'
return_to='CM:x'
strictness_profile='R1_ROUTINE_ENGINEERING'
evidence_class='B'
result_bearing=false
runtime_profile=''
requirement_ids=[]
nonrequirement_ids=[]
recovery_owner='CM:x'
acceptance_outcome='The original operation succeeds end to end.'
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
        """```toml hmasd-result
schema_version=2
assignment_id='asg_x'
result_kind='COMPLETED'
author_role='hmasd-workflow-recovery-manager'
owner_return='CM:x'
project_map_anchor='Route'
files_observed=['consumer.py']
files_changed=[]
symbols_changed=[]
direct_consumer_checked='consumer.py'
acceptance_observed='TRUE'
acceptance_evidence=['docs/session/runtime-boundary.md']
```
""",
        encoding="utf-8",
    )
    assignment = parse_assignment(assignment_path)
    result = parse_result(result_path)
    assert assignment.acceptance_outcome == (
        "The original operation succeeds end to end."
    )
    assert result.acceptance_observed == "TRUE"
    assert result.acceptance_evidence == ("docs/session/runtime-boundary.md",)
