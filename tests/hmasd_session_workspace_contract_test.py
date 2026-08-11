from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split()).lower()


def test_wdm_is_the_semantic_owner_for_each_scoped_workflow_slice() -> None:
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
    assert "scope-key" in router.lower()
    assert "(role, scope_key)" in router
    assert "unique per root tree" in router.lower()
    assert "multiple active wdms" in router.lower()
    assert "disjoint frozen scopes" in router.lower()


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


def test_plain_language_rule_is_universal_in_router_and_detailed_in_its_sources() -> None:
    router = _normalized("AGENTS.md")
    skill = _normalized(".agents/skills/hmasd-writing-agent-assignments/SKILL.md")
    contract = _normalized("docs/project/SESSION_WORKSPACE_CONTRACT.md")

    assert any(cue in router for cue in ("plain-language", "plain language", "ordinary-language"))
    assert "hmasd-writing-agent-assignments" in router
    assert "session_workspace_contract" in router
    assert "root↔l1" in contract
    assert "l1↔l2" in contract
    for detail_group in (
        ("concrete objects", "concrete files, objects or decisions"),
        ("their relationship", "how they relate", "causal relationship"),
        ("responsible owner", "owner of the relevant action", "who owns each action"),
        ("consequence", "what breaks"),
        (
            "paths, fields, abbreviations, commands, statuses, or evidence",
            "fields, paths, abbreviations, commands or evidence",
            "fields, paths, abbreviations, commands, statuses or evidence",
            "paths, commands, statuses and evidence",
        ),
    ):
        assert any(detail in skill or detail in contract for detail in detail_group), detail_group
        # AGENTS.md may state the small universal semantic rule; only its
        # detailed factual-tail wording belongs exclusively in the sources.
        if detail_group[0].startswith("paths, fields,"):
            assert not any(detail in router for detail in detail_group), detail_group


def test_plain_language_messages_append_only_the_smallest_relevant_factual_tail() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    normalized = " ".join(contract.split()).lower()
    start = normalized.index("## plain-language-first cross-owner messages")
    end = normalized.index("## workflow validation and progress vocabulary", start)
    section = normalized[start:end]
    assert "assignment, progress report and terminal result" in section
    assert section.index("states the request") < section.index("then append the relevant factual tail")
    assert section.index("then append the relevant factual tail") < section.index("technical detail after")
    for cue_group in (
        ("assignment", "scope", "owned paths"),
        ("files", "objects", "decisions", "artifact"),
        ("action", "status", "outcome"),
        ("commands", "evidence", "paths"),
        ("unresolved", "next", "owner"),
    ):
        assert any(cue in section for cue in cue_group), cue_group
    assert "preserves technical detail after the explanation" in section
    assert "not a message schema" in section


def test_progress_and_terminal_meanings_remain_wdm_status_only_and_not_acceptance() -> None:
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    normalized = " ".join(contract.split()).lower()
    assert "workflow_progress_event_owner=WDM" in contract
    assert (
        _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
        .count("workflow_progress_event_names=DISPATCHED|WRITES_COMPLETE|TESTS_COMPLETE|REVIEW_READY|TERMINAL")
        == 1
    )
    for cue_group in (
        ("status-only observations",),
        ("not scheduler", "not_scheduler", "not scheduling"),
        ("not queue", "not_queue", "not queuing"),
        ("not ledger", "not_ledger"),
        ("not acceptance token", "not_acceptance_token", "not acceptance"),
        ("terminal does not mean accepted", "terminal` does not mean accepted"),
        ("necessary but insufficient for root's final response",),
        ("accepted-path record",),
        ("canonical reload",),
        ("runtime smoke",),
    ):
        assert any(cue in normalized for cue in cue_group), cue_group
    assert "workflow_progress_event_emission=each_relevant_event_at_most_once|adjacent_observations_may_share_one_report" in contract


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
    assert "This pointer-only record contains WDM workflow-control-plane identity, status" in normalized_wdm_session
    assert "owner_role=workflow_design_manager" in wdm_common


def test_cpm_action_bearing_technical_treatment_view_is_projection_only() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    role = " ".join(_text(".agents/roles/CODE_PROJECT_MANAGER.md").split())
    agile = " ".join(_text(".agents/skills/hmasd-agile-research-development/SKILL.md").split())
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

    for required in (
        "runtime_unit_accounting=none",
        "runtime_pool=none",
        "runtime_class_quota=none",
        "runtime_reservation=none",
        "runtime_admission_ledger=none",
        "runtime_observation_owner=root_mechanical",
        "runtime_observation_facts=live_processes|cpu|memory|concrete_resource_conflicts",
        "runtime_judgment_owner=code_project_manager_scope_local",
        "high_cost_runtime_authorization=explicit_user_task_via_root",
        "max_threads=20",
        "max_threads_semantics=agent_concurrency_ceiling_only",
        "max_threads_runtime_authorization=none",
        "parallelism_runtime_authorization=none",
    ):
        assert required in role
    for required in (
        "actual live processes, CPU, memory and concrete resource conflicts",
        "runtime_unit_accounting=none",
        "runtime_pool=none",
        "runtime_reservation=none",
        "runtime_admission_ledger=none",
        "High-cost runtime requires an explicit user task routed through Root",
        "`max_threads=20` is an agent-concurrency ceiling only",
        "No runtime or costly execution is authorized by this Skill alone",
    ):
        assert required in agile


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
    assert "tracked_writer_workspace=root_managed_worktree_required" in normalized_router
    assert "tracked_writer_mixed_write_classification=tracked_writer" in normalized_router
    for exemption in ("read-only", "ignored-only", "temporary-only"):
        assert exemption in normalized_router
    assert "mandatory_ticket_identity=forbidden_for_subagent_authority" in normalized_router
    assert "child_forked_context=background_only" in normalized
    assert "managed worktree/receipt" in normalized_router.lower()
    assert "root alone provisions, records, integrates, releases or retains it and owns" in normalized_router.lower()
    assert "children never invoke helper or git lifecycle" in normalized_router.lower()
    assert "one writable l1 assignment" in normalized_router.lower()
    assert "one root-managed worktree" in normalized_router.lower()
    assert "parallel implementers" in normalized_router.lower()
    assert "same frozen base" in normalized_router.lower()
    assert "exact disjoint paths" in normalized_router.lower()
    assert "one l1 slice candidate" in normalized_router.lower()
    assert "root commits/records only after all children complete" in normalized_router.lower()
    assert "independent candidate/release lifecycle means a new l1" in normalized_router.lower()
    assert "distinct concurrent wdm/cpm l1 assignments" in normalized_router.lower()
    assert "root_managed_worktree_union_convergence=separate_worktree_for_multi_candidate_union_only" in normalized_router.lower()
    assert "disjoint l2 writers share one l1 worktree" in normalized_router.lower()
    assert "l2 never has its own worktree lifecycle" in normalized_router.lower()
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


def test_singleton_package_acceptance_precedes_root_integration_and_union_is_conditional() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split()).lower()
    router = " ".join(_text("AGENTS.md").split()).lower()
    role = " ".join(_text(".agents/roles/WORKFLOW_DESIGN_MANAGER.md").split()).lower()
    surfaces = " ".join((contract, router, role))
    for required in (
        "workflow_slice_result=wdm_accepts_exact_slice_then_returns_candidate_ready_packet",
        "workflow_candidate_integration=root_records_and_integrates_candidate_set_after_all_children_finish",
        "workflow_singleton_package=one_writable_wdm_l1_exact_final_frozen_bytes_reviewed_together",
        "workflow_singleton_acceptance=one_advisory_reviewer_then_same_wdm_package_acceptance_before_root_integration",
        "workflow_multi_candidate_convergence_trigger=two_or_more_independently_reviewed_wdm_candidates|actual_union_differs_from_every_reviewed_package",
        "workflow_union_convergence=conditional_on_workflow_multi_candidate_convergence_trigger",
        "workflow_reviewer_authority=advice_only_no_acceptance",
        "read-only advisory reviewer",
    ):
        assert required in surfaces, required
    assert "fresh convergence wdm is required only when root combines" in surfaces


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


def test_reverse_intake_patch_locator_and_candidate_copy_boundary() -> None:
    contract = " ".join(_text("docs/project/SESSION_WORKSPACE_CONTRACT.md").split())
    for required in (
        "explorer_reverse_intake_patch_root=temp/sessions/independent_research_explorer/<root-assignment>/state-proposals/",
        "explorer_reverse_intake_patch_locator=<patch-root>/<proposal>.patch",
        "explorer_reverse_intake_payload=small_self_contained_semantic_delta",
        "explorer_reverse_intake_writer_check=exact_destination|payload_presence|UTF-8/LF",
        "explorer_reverse_intake_full_map_transport=forbidden",
        "explorer_reverse_intake_root_install=exact_path_and_git_revision_check_then_exact_copy",
        "explorer_reverse_intake_retry=one_concrete_delta_clarification_only",
        "explorer_reverse_intake_retry_state_queue_receipt_validator=forbidden",
        "not canonical state",
        "task-scoped candidate copy once",
        "exact-copy installation only after the EM's full-read row/delta acceptance",
    ):
        assert required in contract, required


def test_workflow_defect_queue_received_order_is_chronological_evidence_only() -> None:
    queue = _text("docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md")
    received_order = [
        int(match.group(1))
        for line in queue.splitlines()
        if (match := re.match(r"\|\s*(\d+)\s*\|", line))
    ]
    assert received_order == sorted(received_order)
    assert received_order == list(range(1, len(received_order) + 1))
    assert "scheduler=false" in queue
    assert "reverse_intake_queue_role=evidence_log_only_not_dispatcher_or_scheduler" in queue
