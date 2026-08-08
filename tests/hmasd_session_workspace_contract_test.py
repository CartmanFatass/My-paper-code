from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_wdm_is_the_single_workflow_owner() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    router = _text("AGENTS.md")
    for required in (
        "shared_workflow_surface_owner=workflow_design_manager",
        "shared_workflow_design_authority=exclusive",
        "shared_workflow_acceptance_authority=exclusive",
        "shared_workflow_git_authority=exclusive",
        "workflow_child_parent=workflow_design_manager",
        "workflow_child_acceptance_authority=none",
        "workflow_router_consistency_check=required_for_every_workflow_change",
        "workflow_implementer_parallelism=file_family_adaptive",
        "assignment_writing_skill=hmasd-writing-agent-assignments",
        "child_assignment_brief=temp/sessions/<parent_role>/assignments/<assignment_id>.md",
        "child_assignment_format=self_contained_natural_language_not_schema_admission",
        "child_forked_context=background_only",
        "Workflow Design Manager is the sole owner",
    ):
        assert required in contract
    assert "workflow_design_manager_workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces" in router
    assert "persistent_session_workflow_design_authority=none" in router
    assert "workflow_assignment_writing_skill=hmasd-writing-agent-assignments" in router
    assert "native_child_brief_content=" not in router
    assert "Before designing, dispatching or materially revising any subagent or cross-session assignment/interface" in " ".join(router.split())


def test_assignment_writing_preserves_semantic_context_over_file_only_anchors() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    router = " ".join(_text("AGENTS.md").split())
    assert "hmasd-writing-agent-assignments" in contract
    assert "hmasd-writing-agent-assignments" in router
    assert "single assignment-writing contract" in contract
    assert "rich natural-language brief" in contract
    assert "Before designing or dispatching any registered child or cross-session task" in contract
    for capability in (
        "owned outcome",
        "necessary observations",
        "permitted actions",
        "role-local judgment",
        "bounded recovery",
        "completion evidence",
    ):
        assert capability in contract
    contract_lower = contract.lower()
    assert "paths, statuses and schema fields are anchors, not meaning" in contract_lower
    assert "never substitute for the semantic outcome or the child's judgment" in contract_lower


def test_public_current_work_is_partitioned_and_owned() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    index = _text("docs/project/CURRENT_WORK.md")
    wdm_session = _text("docs/project/current-work/sessions/workflow_design_manager.md")
    wdm_common = _text("docs/project/current-work/common/workflow_control_plane.md")
    normalized = " ".join(contract.split())
    normalized_wdm_session = " ".join(wdm_session.split())
    for required in (
        "public_current_work_partition_status=active_index_and_partitions",
        "docs/project/current-work/common/",
        "docs/project/current-work/sessions/",
        "A session may edit only its own session record",
        "workflow_control_plane",
    ):
        assert required in normalized
    for required in (
        "session_record_ids=code_project_manager|workflow_design_manager",
        "index_owner=workflow_design_manager",
        "workflow_control_plane",
        "current-work/sessions/workflow_design_manager.md",
    ):
        assert required in index
    assert "workflow_index_owner=" not in index
    assert "session_owner_id=workflow_design_manager" in wdm_session
    assert "continuity=role_based_successor_tasks" in wdm_session
    assert "Continuity is attached to the stable WDM role" in normalized_wdm_session
    assert "not to a historical thread" in normalized_wdm_session
    assert "owner_role=workflow_design_manager" in wdm_common


def test_durable_and_temporary_workspaces_remain_separate() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    normalized = " ".join(contract.split())
    readme = _text("docs/session-workspaces/workflow_design_manager/README.md")
    for required in (
        "docs/session-workspaces/<role_id>/",
        "temp/sessions/<role_id>/",
        "same_file_concurrent_writes=forbidden",
        "No hash, byte count or digest is required",
    ):
        assert required in contract
    for required in (
        "Suggested headings aid communication but never become required fields or an admission gate",
        "Forked turns are background only",
    ):
        assert required in normalized
    assert "workflow_surface_owner=true" in readme


def test_wdm_defect_reports_are_logged_without_becoming_a_scheduler() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    normalized = " ".join(contract.split())
    queue = _text("docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md")
    for required in (
        "workflow_incident_log=docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md",
        "chronological incident log",
        "does not serialize unrelated work",
        "advisory inputs",
    ):
        assert required in normalized
    for required in (
        "ordering=chronological",
        "scheduler=false",
        "global_blocker=false",
        "report_authority=advisory_only",
        "hash_identity=forbidden",
    ):
        assert required in queue


def test_non_workflow_role_ownership_is_preserved() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    normalized = " ".join(contract.split())
    assert "Code Project Manager keeps exclusive authority for code" in normalized
    assert "Independent Research Explorer keeps exclusive authority for advisory research" in normalized
    assert "Those role-local authorities do not include workflow" in normalized
    assert "push only their owned non-workflow durable paths" in normalized


def test_explorer_research_and_session_artifacts_remain_explorer_owned() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    role = _text(".agents/roles/WORKFLOW_DESIGN_MANAGER.md")
    for required in (
        "Explorer remains the sole owner of its research plans, continuity notes",
        "all temporary/session research artifacts under its durable and temporary workspace",
        "WDM is the single acceptance owner for the explicitly listed Explorer workflow artifacts",
        "acceptance does not grant workspace cleanup or write authority",
    ):
        assert required in contract
    assert "workflow_acceptance_authority=exclusive" in role
    assert "centralized_explorer_workspace_cleanup_write_authority=none" in role
