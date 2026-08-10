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
    ):
        assert required in contract
    for required in (
        "workflow_design_manager_workflow_design_authority=exclusive",
        "root_canonical_state_physical_write_authority=accepted_proposals_only",
        "root_final_git_integration_authority=accepted_paths_only",
        "root_cross_owner_relay_authority=exclusive",
    ):
        assert required in router
    assert "compatibility_path_semantics=stable_role_locator_not_live_session_thread_or_admission_identity" in contract
    assert "task_scope=fresh_cli_root_task|exact_assignment" in contract
    assert "designing an assignment/interface" in router
    assert "native_child_brief_content=" not in router
    assert "hmasd-writing-agent-assignments" in router


def test_assignment_writing_preserves_semantic_context_over_file_only_anchors() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    router = " ".join(_text("AGENTS.md").split())
    assert "hmasd-writing-agent-assignments" in router
    assert "self-contained brief" in contract
    assert "workflow_assignment_identity=workflow_assignment_id|owned_paths|wdm_session_workspace" in contract
    assert "does not replace the semantic assignment" in contract
    assert "returns its conclusion to the parent" in contract
    assert "Root retains canonical writes, Git, helper lifecycle/receipt control and cross-owner routing" in contract
    assert "Manager proposals may be kept in an assignment-specific temporary state-proposal file, but a proposal is not canonical state until Root accepts and writes it" in router
    assert "workflow_root_reload=fresh_root_task_canonical_reload" in contract
    assert "workflow_root_reload_brief=current_commit|accepted_stable_change|real_unfinished_item|next_user_goal|next_map_or_interface" in contract
    assert "workflow_thread_registry=forbidden" in contract
    assert "agentify_transport_assignment_locators=batch_path|results_path" in contract
    assert "agentify_transport_result_locator=results_path" in contract
    assert "agentify_transport_result_path_guard=.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py" in contract
    assert "agentify_transport_result_guard_inputs=repo|expected_results_path|returned_results_path" in contract
    assert "agentify_transport_result_guard_timing=child_after_write_before_COMPLETE|requester_after_terminal_before_read" in contract
    assert "agentify_transport_result_guard_scope=strict_assignment_descendant_no_root_generic" in contract
    assert "agentify_transport_result_guard_error=ERROR_empty_results_path_actual_error" in contract
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
        "A task may edit only its own role record and common records whose `owner_role` is that role",
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
    for required in (
        "task_scope=fresh_cli_root_task|exact_assignment",
        "workflow_root_reload=fresh_root_task_canonical_reload",
        "workflow_thread_registry=forbidden",
    ):
        assert required in normalized
    assert "rotation_boundary=integrated_batch_completion" in normalized_wdm_session
    assert "This record contains only WDM workflow-control-plane identity and status" in normalized_wdm_session
    assert "owner_role=workflow_design_manager" in wdm_common


def test_cpm_action_bearing_technical_treatment_view_is_projection_only() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    role = " ".join(_text(".agents/roles/CODE_PROJECT_MANAGER.md").split())
    agile = " ".join(_text(".agents/skills/hmasd-agile-research-development/SKILL.md").split())
    canonical = " ".join(_text("docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md").split())
    surfaces = " ".join((contract, role, agile))
    for required in (
        "docs/project/current-work/common/explorer_project_validation.md",
        "owner-local",
        "pointer/view only",
        "canonical contract remains the sole detailed source",
        "not a second semantic source",
        "not a schema, queue, scheduler, process monitor, runtime-capacity source, admission source or acceptance source",
        "`active_assignment_id` remains only the foreground pointer",
    ):
        assert required in surfaces

    for required in (
        "status-only token never supplies an action",
        "never infers an action from a status-only token",
        "`parked` is Explorer-local",
        "ordinary engineering gaps belong to CPM",
        "asks one exact clarification",
        "continues unrelated work",
    ):
        assert required in surfaces

    for required in (
        "Status-only text is insufficient",
        "## Explorer scientific dispositions and action map",
        "Direction | current scientific question",
        "CPM Technical Treatment View at",
    ):
        assert required in canonical

    for forbidden in (
        "Direction/treatment",
        "Explorer request and handoff locator",
        "current technical phase in full prose",
        "runtime class/units and current admission reason",
        "dependency/path/resource conflict",
        "`parked` is an Explorer-local scientific disposition only when no scientifically complete frozen CPM successor exists",
        "A parked direction reactivates only when its recorded prospective condition is met",
        "`retired` is a separate explicit terminal disposition",
    ):
        assert forbidden not in surfaces

    assert "runtime_capacity_pool_units=3" in role
    assert "three-unit" in agile
    assert "independent_admitted_treatment_execution=parallel_first_within_capacity" in role
    assert "runtime_admission_judgment=admit|up-class|pending_runtime_capacity" in role
    assert "event-driven continuation" in agile
    assert "no clock-driven scheduler or polling" in agile


def test_durable_and_temporary_workspaces_remain_separate() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    router = _text("AGENTS.md")
    normalized = " ".join(contract.split())
    normalized_router = " ".join(router.split())
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
    assert "Root-managed worktree" in normalized_router
    assert "tracked writer" in normalized_router
    assert "mixed tracked and ignored assignment is still a tracked writer" in normalized_router
    for exemption in ("read-only", "ignored-only", "temporary-only"):
        assert exemption in normalized_router
    assert "mandatory_ticket_identity=forbidden_for_subagent_authority" in normalized_router
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
        "ACTION_BEARING_STATUS_ONLY_HANDOFF_GAP",
        "accepted-contract/CLOSED",
        "science/runtime effect=none",
    ):
        assert required in queue


def test_non_workflow_role_ownership_is_preserved() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    normalized = " ".join(contract.split())
    assert "Workflow-design, code, runtime and research authority remain with the owner Roles and the router" in normalized
    assert "No role, task, compatibility label or workspace path grants Git integration or push authority" in normalized


def test_explorer_research_and_session_artifacts_remain_explorer_owned() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    role = _text(".agents/roles/WORKFLOW_DESIGN_MANAGER.md")
    assert "Root alone relays accepted material to another owner, and the receiving owner does not intake directly from a sibling" in contract
    assert "A receiver reads only an assignment-named sender handoff; it does not write another role's workspace" in contract
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
