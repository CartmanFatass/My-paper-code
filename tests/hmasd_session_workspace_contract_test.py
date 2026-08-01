from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_shared_workflow_design_is_session_scoped() -> None:
    router = _text("AGENTS.md")
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    for required in (
        "persistent_session_role_local_workflow_design_authority=exclusive_for_owned_surfaces",
        "persistent_session_role_local_workflow_acceptance_authority=exclusive_for_owned_surfaces",
        "persistent_session_workflow_assignment_fields=session_owner_role|session_owner_id|owned_paths|session_workspace",
        "workflow_child_parent=assigning_persistent_session",
        "workflow_child_acceptance_authority=none",
        "session_workspace_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md",
    ):
        assert required in router
    for required in (
        "shared_workflow_surface_owner=workflow_design_manager",
        "role_local_workflow_surface_owner=exact_persistent_session",
        "session_owner_role=<locked persistent role>",
        "session_owner_id=<locked session id>",
        "owned_paths=<exact nonoverlapping paths>",
        "WDM is not an approval gate",
    ):
        assert required in contract


def test_session_workspaces_are_owned_and_partitioned() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    normalized = " ".join(contract.split())
    readme = _text("docs/session-workspaces/workflow_design_manager/README.md")
    ignore = _text(".gitignore")
    for required in (
        "docs/session-workspaces/<role_id>/",
        "temp/sessions/<role_id>/",
        "docs/project/current-work/common/<record-id>.md",
        "docs/project/current-work/sessions/<role_id>.md",
        "same_file_concurrent_writes=forbidden",
        "public_current_work_partition_status=phase_two_role_adoption_required",
        "public_current_work_partition_authority=none_in_phase_one",
        "grants no public-entry or partition read/write authority",
        "only that role's access",
        "may edit only its own session file",
    ):
        assert required in normalized
    assert "After activation, all registered persistent sessions may read" not in normalized
    assert "session_owner_role=workflow_design_manager" in readme
    assert "!docs/session-workspaces/**/*.md" in ignore
    assert "!/temp/README.md" in ignore


def test_shared_children_are_owner_neutral_and_advisory() -> None:
    for name in (
        "WORKFLOW_AUDITOR.md",
        "WORKFLOW_IMPLEMENTER.md",
        "WORKFLOW_REVIEWER.md",
        "WORKFLOW_COST_REVIEWER.md",
    ):
        role = _text(f".agents/roles/{name}")
        assert "parent=assigning_persistent_session" in role
        assert "session_owner_role" in role
        assert "session_owner_id" in role
        assert "owned_paths" in role
        assert "session_workspace" in role
        assert "acceptance_authority=none" in role or "workflow_acceptance_authority=none" in role


def test_role_local_git_grants_do_not_expand_research_artifact_authority() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    assert (
        "independent_research_role_local_workflow_git_authority=direct_for_owned_surfaces"
        in contract
    )
    assert "does not extend to `local_research/`" in contract
    assert "another session's files" in " ".join(contract.split())
