from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_wdm_is_the_single_workflow_owner() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    router = _text("AGENTS.md")
    for required in (
        "workflow_child_parent=workflow_design_manager",
        "child_assignment_brief=temp/sessions/<parent_role>/assignments/<assignment_id>.md",
        "child_assignment_format=self_contained_natural_language_not_schema_admission",
        "child_forked_context=background_only",
        "workflow_assignment_identity=workflow_assignment_id|owned_paths|wdm_session_workspace",
        "public_current_work_index_owner=workflow_design_manager",
        "research_scheduler_kind=user_owned_persistent_desktop_task",
        "research_scheduler_registered_child=false",
        "research_scheduler_desktop_handle=threadId|hostId",
    ):
        assert required in contract
    assert "workflow_design_manager_workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces" in router
    assert "persistent_session_workflow_design_authority=none" in router
    assert "workflow_assignment_writing_skill=hmasd-writing-agent-assignments" in router
    assert "native_child_brief_content=" not in router
    assert "Designing or dispatching a child or cross-session interface" in " ".join(router.split())


def test_assignment_writing_preserves_semantic_context_over_file_only_anchors() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    router = " ".join(_text("AGENTS.md").split())
    assert "hmasd-writing-agent-assignments" in router
    assert "self-contained brief" in contract
    assert "workflow_assignment_identity=workflow_assignment_id|owned_paths|wdm_session_workspace" in contract
    assert "does not replace the semantic assignment" in contract
    assert "returns its conclusion to the parent" in contract
    assert "Acceptance, Git and cross-task routing remain with the owner Role" in contract
    assert "workflow_successor_rotation=integrated_batch_completion" in contract
    assert "workflow_successor_brief=current_commit|accepted_stable_change|real_unfinished_item|next_user_goal|next_map_or_interface" in contract
    assert "workflow_thread_registry=forbidden" in contract
    assert "agentify_transport_assignment_locators=batch_path|results_path" in contract
    assert "agentify_transport_result_locator=results_path" in contract
    assert "cpm_mechanical_assignment_locators=spec_path|result_path" in contract
    assert "cpm_mechanical_result_locator=result_path" in contract
    assert "agentify_transport_result_paths=" not in contract
    assert "cpm_mechanical_result_paths=" not in contract


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
        "session_record_ids=workflow_design_manager|research_scheduler",
        "index_owner=workflow_design_manager",
        "research_scheduler_session=docs/project/current-work/sessions/research_scheduler.md",
        "workflow_control_plane",
        "current-work/sessions/workflow_design_manager.md",
    ):
        assert required in index
    assert "workflow_index_owner=" not in index
    assert "session_owner_id=workflow_design_manager" in wdm_session
    assert "continuity=role_based_successor_tasks" in wdm_session
    assert "rotation_boundary=integrated_batch_completion" in normalized_wdm_session
    assert "This record contains only WDM workflow-control-plane identity and status" in normalized_wdm_session
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
        "assignment-specific direction/treatment handoff files",
        "never share a writable file",
        "checkpoint or mutable trainer state",
        "Manifest order does not allocate runtime capacity or establish scientific priority",
        "No polling, queue or inferred path scan is part of this contract",
    ):
        assert required in normalized
    assert "child_forked_context=background_only" in normalized
    assert "Formats and suggested sections aid understanding but never become admission gates" in normalized
    assert "workflow_surface_owner=true" in readme


def test_wdm_defect_reports_are_logged_without_becoming_a_scheduler() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    normalized = " ".join(contract.split())
    queue = _text("docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md")
    assert "workflow_incident_log=docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md" in normalized
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
    assert "Workflow-design, code, runtime and research authority remain with the owner Roles and the router" in normalized
    assert "push only their owned non-workflow durable paths" in normalized


def test_explorer_research_and_session_artifacts_remain_explorer_owned() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    role = _text(".agents/roles/WORKFLOW_DESIGN_MANAGER.md")
    assert "Explorer owns the `explorer_to_code_manager/` direction and CPM is read-only for that exchange" in contract
    assert "workflow_acceptance_authority=exclusive" in role
    assert "centralized_explorer_workspace_cleanup_write_authority=none" in role


def test_explorer_mechanical_child_keeps_native_no_write_session_boundary() -> None:
    contract_path = ROOT / "docs/project/SESSION_WORKSPACE_CONTRACT.md"
    profile_path = ROOT / ".codex/agents/hmasd-explorer-mechanical.toml"
    role_path = ROOT / ".agents/roles/EXPLORER_MECHANICAL_OPERATOR.md"
    assert profile_path.is_file()
    assert role_path.is_file()

    contract = " ".join(contract_path.read_text(encoding="utf-8").split())
    role = " ".join(role_path.read_text(encoding="utf-8").split())
    assert "Explorer mechanical lane is native" in contract
    assert "role=explorer_mechanical_operator" in role
    assert "write_authority=none" in role
    assert "scientific_authority=none" in role


def test_desktop_scheduler_is_same_level_and_lazy() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    workflow_map = " ".join(_text("docs/project/WORKFLOW_MAP.md").split())
    for required in (
        "same-level ephemeral owner tasks",
        "ACTIVE_ASSIGNMENTS.md",
        "research_scheduler_procedure_pointer=.agents/skills/hmasd-research-scheduler/SKILL.md",
        "research_scheduler_resource_policy_pointer=.agents/skills/hmasd-research-scheduler/SKILL.md",
    ):
        assert required in (contract + " " + workflow_map)
    for command_level in ("create_thread", "wait_threads", "read_thread"):
        assert command_level not in contract
        assert command_level not in workflow_map
