from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SESSION_CONTRACT = REPO / "docs/project/SESSION_WORKSPACE_CONTRACT.md"
MANAGER_ROLE = REPO / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md"


def _field(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}=(.+)$", text)
    assert match, f"missing keyed contract field: {name}"
    return match.group(1)


def _fields(text: str, name: str) -> set[str]:
    return set(_field(text, name).split("|"))


def test_validation_layers_and_writer_scope_are_structural() -> None:
    contract = SESSION_CONTRACT.read_text(encoding="utf-8")

    assert _fields(contract, "workflow_validation_layers") == {
        "slice_local",
        "integration_cross_slice",
        "runtime_fresh_smoke_after_root_integration_reload",
    }
    assert _field(
        contract, "workflow_validation_ownership"
    ) == (
        "slice_local:writer|integration_cross_slice:WDM|"
        "runtime_fresh_smoke_after_root_integration_reload:Root"
    )
    assert _field(contract, "workflow_writer_validation_scope") == (
        "owned_paths|smallest_affected_contracts"
    )
    assert _field(contract, "workflow_writer_full_suite") == "forbidden"
    assert _field(contract, "control_plane_document_routes") == (
        "docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md"
    )
    assert _field(contract, "workflow_change_risk_tiers") == (
        "high|bounded_contract|low_causal_repair"
    )
    assert _field(contract, "workflow_route_table_policy") == (
        "clear_route_loads_defining_source_direct_consumers_focused_tests|"
        "missing_ambiguous_conflicting_or_authority_crossing_route_requires_Auditor"
    )
    assert _field(contract, "workflow_singleton_package") == (
        "one_writable_WDM_L1_exact_final_frozen_bytes_reviewed_together"
    )
    assert _field(contract, "workflow_singleton_acceptance") == (
        "one_advisory_Reviewer_then_same_WDM_package_acceptance_before_Root_integration"
    )
    assert _field(contract, "workflow_multi_candidate_convergence_trigger") == (
        "two_or_more_independently_reviewed_WDM_candidates|"
        "actual_union_differs_from_every_reviewed_package"
    )
    assert _field(contract, "workflow_causal_check_timing") == (
        "when_all_consumed_bytes_are_frozen_before_package_acceptance"
    )
    assert _field(contract, "workflow_progress_event_emission") == (
        "each_relevant_event_at_most_once|adjacent_observations_may_share_one_report"
    )


def test_dependency_observation_repair_and_preflight_contract_is_session_defined() -> None:
    contract = SESSION_CONTRACT.read_text(encoding="utf-8")
    manager = MANAGER_ROLE.read_text(encoding="utf-8")

    assert _field(contract, "workflow_consumer_finalization") == (
        "all_direct_producer_bytes_frozen_before_final_consumer_write_or_run|"
        "independent_producers_parallel"
    )
    assert _field(contract, "workflow_causal_observation_before_repair") == (
        "all_independently_runnable_focused_causal_commands_terminal_before_product_repair_dispatch|"
        "environment_or_parse_blocker_repair_same_layer_then_continue_observation"
    )
    assert _field(contract, "workflow_product_repair_dispatch") == (
        "complete_observed_product_failures_grouped_by_exact_nonoverlapping_owned_paths|"
        "minimal_repair_dispatches|not_stale_literal_serial_dispatch"
    )
    assert _field(contract, "workflow_validation_layer_preflight") == (
        "once_per_layer_before_product_evidence|"
        "lightweight_short_basetemp_parent_and_actual_command_host|"
        "not_doctor_or_global_health_check_or_acceptance_gate"
    )
    assert _field(manager, "workflow_dependency_validation_authority") == (
        "producer_consumer_dependency_ordering|causal_failure_aggregation|"
        "validation_layer_execution"
    )
    assert _field(manager, "workflow_dependency_validation_contract") == (
        "docs/project/SESSION_WORKSPACE_CONTRACT.md|"
        ".agents/skills/hmasd-workflow-change-audit/SKILL.md"
    )


def test_progress_vocabulary_is_exactly_status_only_and_nonaccepting() -> None:
    contract = SESSION_CONTRACT.read_text(encoding="utf-8")
    manager = MANAGER_ROLE.read_text(encoding="utf-8")

    event_names = _fields(contract, "workflow_progress_event_names")
    assert event_names == {
        "DISPATCHED",
        "WRITES_COMPLETE",
        "TESTS_COMPLETE",
        "REVIEW_READY",
        "TERMINAL",
    }
    assert _field(manager, "workflow_progress_event_vocabulary") == _field(
        contract, "workflow_progress_event_names"
    )
    assert _field(contract, "workflow_progress_event_owner") == "WDM"
    assert _fields(contract, "workflow_progress_event_semantics") == {
        "status_observations_only",
        "not_scheduler",
        "not_queue",
        "not_ledger",
        "not_background_callback",
        "not_retry_state",
        "not_admission",
        "not_acceptance_token",
    }
    assert _field(contract, "workflow_terminal_event_not_acceptance") == "true"


def test_auditor_risk_tiers_and_integrated_review_are_keyed() -> None:
    contract = SESSION_CONTRACT.read_text(encoding="utf-8")
    manager = MANAGER_ROLE.read_text(encoding="utf-8")

    assert _field(manager, "workflow_change_risk_tiers") == (
        "high|bounded_contract|low_causal_repair"
    )
    assert _field(manager, "workflow_high_risk_requires_auditor") == (
        "authority|topology|cross_owner|shared_contract"
    )
    assert _field(manager, "workflow_auditor_skip") == (
        "route_resolved_bounded_single_owner_contract|"
        "low_causal_repair_with_concrete_WDM_rationale"
    )
    assert _field(manager, "workflow_auditor_required") == (
        "missing|ambiguous|conflicting|authority_crossing_route"
    )
    assert _field(contract, "workflow_auditor_policy") == (
        "high_requires_Auditor|bounded_contract_clear_route_may_skip_with_WDM_rationale|"
        "low_causal_repair_may_skip_with_WDM_rationale|"
        "missing_ambiguous_conflicting_or_authority_crossing_route_requires_Auditor"
    )
    assert _field(contract, "workflow_auditor_skip_evidence") == (
        "concrete_WDM_rationale|focused_causal_evidence_on_all_frozen_consumed_bytes"
    )
    assert _field(contract, "workflow_integrated_review") == (
        "exactly_one_advisory_Reviewer_after_TESTS_COMPLETE_and_REVIEW_READY"
    )
    assert _field(contract, "workflow_integrated_review_followup") == (
        "one_pass_no_second_review"
    )
    assert _field(contract, "workflow_reviewer_authority") == "advice_only_no_acceptance"
    assert _field(manager, "workflow_integration_review_authority") == (
        "one_registered_read_only_advisory_Reviewer_then_WDM_package_or_union_acceptance"
    )


def test_control_plane_route_table_is_six_rows_and_path_backed() -> None:
    route_path = SESSION_CONTRACT.parent / "CONTROL_PLANE_DOCUMENT_ROUTES.md"
    route_text = route_path.read_text(encoding="utf-8")
    assert _field(route_text, "control_plane_document_routes") == (
        "docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md"
    )
    assert _field(route_text, "control_plane_document_routes_not") == (
        "task_state|history|hash|receipt|queue|admission|acceptance"
    )
    assert _field(route_text, "workflow_route_table_policy") == (
        "clear_route_loads_defining_source_direct_consumers_focused_tests|"
        "missing_ambiguous_conflicting_or_authority_crossing_route_requires_Auditor"
    )
    assert _field(route_text, "workflow_route_table_auditor_priority") == (
        "authority|topology|cross_owner|shared_contract=>"
        "high_requires_registered_Workflow_Auditor_regardless_of_route_clarity|"
        "skip_evidence_only_after_WDM_non-high_bounded_contract_or_low_causal_repair_classification"
    )

    table_lines = [
        line.strip()
        for line in route_text.splitlines()
        if line.strip().startswith("|")
    ]
    assert len(table_lines) == 8  # header, separator and six compact route rows
    header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    assert header == [
        "Trigger",
        "Defining source",
        "Direct consumers",
        "Focused tests",
        "Auditor escalation",
    ]
    rows = [
        [cell.strip() for cell in line.strip("|").split("|")]
        for line in table_lines[2:]
    ]
    assert len(rows) == 6
    assert len({row[0] for row in rows}) == 6
    assert all(len(row) == 5 and all(row) for row in rows)

    authority_escalation = next(
        row[4].lower() for row in rows if row[0] == "Authority and topology"
    )
    assert re.search(
        r"`high`:\s*auditor required for authority, topology, cross-owner or shared-contract work"
        r" regardless of route clarity;\s*missing, ambiguous, conflicting or authority-crossing routes also require auditor",
        authority_escalation,
    )

    rows_by_trigger = {row[0]: row for row in rows}
    for trigger in (
        "Authority and topology",
        "Session, worktree and lifecycle",
        "Risk, delegation and review",
    ):
        assert re.search(r"`high`.*auditor required", rows_by_trigger[trigger][4].lower())

    # A clear route never authorizes an Auditor skip by itself. Skip evidence
    # appears only after WDM has classified the change as non-high.
    for trigger in (
        "WDM planning and confirmation",
        "Risk, delegation and review",
        "L1 startup and context",
        "Assignment and message contract",
    ):
        escalation = rows_by_trigger[trigger][4].lower()
        assert "after wdm classifies the change as non-high" in escalation
        assert "`workflow_auditor_skip_evidence`" in escalation
    assert "clear plan route may skip only with" not in rows_by_trigger[
        "WDM planning and confirmation"
    ][4].lower()
    assert "clear assignment route may skip only with" not in rows_by_trigger[
        "Assignment and message contract"
    ][4].lower()

    expected_consumers = {
        "Authority and topology": {
            "AGENTS.md",
            ".codex/agents/hmasd-workflow-design-manager.toml",
            ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
            ".codex/agents/hmasd-workflow-implementer.toml",
            ".agents/roles/WORKFLOW_IMPLEMENTER.md",
            ".codex/agents/hmasd-workflow-auditor.toml",
            ".agents/roles/WORKFLOW_AUDITOR.md",
            ".codex/agents/hmasd-workflow-reviewer.toml",
            ".agents/roles/WORKFLOW_REVIEWER.md",
        },
        "Assignment and message contract": {
            "AGENTS.md",
            ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
            ".agents/roles/WORKFLOW_AUDITOR.md",
            ".agents/roles/WORKFLOW_IMPLEMENTER.md",
            ".agents/roles/WORKFLOW_REVIEWER.md",
            ".agents/roles/CODE_PROJECT_MANAGER.md",
            ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md",
        },
    }
    for trigger, consumers in expected_consumers.items():
        actual = set(re.findall(r"`([^`]+)`", rows_by_trigger[trigger][2]))
        assert actual == consumers
        for path in consumers:
            assert (REPO / path).is_file(), path
    assert "docs/project/current-work/sessions/workflow_design_manager.md" not in (
        rows_by_trigger["Assignment and message contract"][2]
    )

    # Every repo-relative backticked source/consumer/test path is live. The
    # prose and keyed negatives intentionally remain non-path relationship data.
    for row in rows:
        for cell in row[1:4]:
            for value in re.findall(r"`([^`]+)`", cell):
                assert not value.startswith(("http://", "https://"))
                assert (SESSION_CONTRACT.parents[2] / value).is_file(), value

    normalized = " ".join(route_text.split()).lower()
    for forbidden in (
        "task_state",
        "task log",
        "history",
        "hash",
        "receipt",
        "queue",
        "admission",
        "acceptance record",
    ):
        assert forbidden in normalized
    assert not re.search(
        r"(?m)^(?:assignment|history|hash|receipt|queue|admission|acceptance)(?:_|[a-z])*\s*=",
        route_text,
    )


def test_wdm_current_work_routes_and_map_owner_meaning_are_resolved() -> None:
    route_path = SESSION_CONTRACT.parent / "CONTROL_PLANE_DOCUMENT_ROUTES.md"
    route_text = route_path.read_text(encoding="utf-8")
    table_lines = [
        line.strip()
        for line in route_text.splitlines()
        if line.strip().startswith("|")
    ]
    rows = [
        [cell.strip() for cell in line.strip("|").split("|")]
        for line in table_lines[2:]
    ]
    triggers = {row[0] for row in rows}
    expected_route = "docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md"
    expected_active_trigger = "WDM planning and confirmation"
    expected_boundary_trigger = "Risk, delegation and review"

    for record_path in (
        REPO / "docs/project/current-work/common/workflow_control_plane.md",
        REPO / "docs/project/current-work/sessions/workflow_design_manager.md",
    ):
        record = record_path.read_text(encoding="utf-8")
        assert _field(record, "active_wdm_route") == expected_route
        assert _field(record, "next_boundary") == expected_route
        assert _field(record, "active_wdm_route_trigger") == expected_active_trigger
        assert _field(record, "next_boundary_trigger") == expected_boundary_trigger
        assert _field(record, "active_wdm_route_trigger") in triggers
        assert _field(record, "next_boundary_trigger") in triggers

    workflow_map = (REPO / "docs/project/WORKFLOW_MAP.md").read_text(encoding="utf-8")
    wdm_rows = [
        line.strip()
        for line in workflow_map.splitlines()
        if line.strip().startswith("| Workflow Design Manager (WDM) |")
    ]
    assert len(wdm_rows) == 1
    wdm_row = wdm_rows[0].lower()
    assert "singleton frozen-package acceptance" in wdm_row
    assert "conditional true multi-candidate union acceptance" in wdm_row
    assert "package/conditional-convergence packets" in wdm_row


def test_start_guidance_basetemp_and_failure_classes_are_bounded() -> None:
    contract = SESSION_CONTRACT.read_text(encoding="utf-8")

    assert _field(contract, "workflow_root_l1_start_guidance") == (
        "useful_owned_work_and_useful_action_or_matching_leaf_capacity"
    )
    assert _fields(contract, "workflow_root_l1_start_guidance_not") == {
        "quota",
        "reservation",
        "scheduler",
        "admission_gate",
        "pool",
        "runtime_authorization",
    }
    assert _field(contract, "workflow_windows_basetemp") == (
        "short_absolute_assignment_specific_under_root_controlled_parent"
    )
    assert _field(contract, "workflow_windows_integration_basetemp") == (
        r"C:\Projects\ht\<assignment-run>"
    )
    assert _fields(contract, "workflow_validation_failure_classes") == {
        "environment_setup",
        "product_assertion",
    }
    assert _field(contract, "workflow_environment_setup_recovery") == (
        "same_layer_rerun_without_retry_state"
    )
    assert _field(contract, "workflow_product_failure_recovery") == (
        "repair_causal_contract_or_implementation"
    )


def test_root_smoke_and_concurrency_boundaries_remain_explicit() -> None:
    contract = SESSION_CONTRACT.read_text(encoding="utf-8")

    assert _field(contract, "workflow_root_runtime_smoke") == (
        "Root_only_after_integration_and_canonical_reload"
    )
    assert "pending until Root's post-integration action" in " ".join(contract.split())
    assert _field(contract, "owner_l1_multiplicity") == (
        "role_defined_scope_keyed_within_root_tree"
    )
    assert _field(contract, "owner_scope_key_uniqueness") == (
        "one_l1_per(role,role_defined_scope_key)_within_root_tree"
    )
    assert _field(contract, "workflow_l1_parallelism") == (
        "disjoint_frozen_workflow_scopes_only"
    )
    assert _field(contract, "managed_worktree_allocation") == (
        "one_writable_l1_assignment_one_root_managed_worktree"
    )
    assert _field(contract, "shared_l1_worktree_conditions") == (
        "same_frozen_base|exact_disjoint_paths|no_l2_git|"
        "one_shared_l1_slice_candidate|Root_records_after_all_children_finish"
    )
    assert _field(contract, "l2_worktree_lifecycle") == "forbidden"
    assert _field(contract, "root_managed_worktree_authority") == "root_only"
    assert _field(contract, "runtime_invariants") == "max_threads=20|max_depth=2"
    assert _field(contract, "workflow_max_threads_semantics") == (
        "20_agent_tree_ceiling_only_not_runtime_authorization"
    )
    assert _field(contract, "workflow_runtime_pool") == "forbidden"


def test_root_turn_progress_wait_and_final_response_are_keyed() -> None:
    contract = SESSION_CONTRACT.read_text(encoding="utf-8")

    # These three values are the literal control-plane definitions. Keep the
    # exact-value assertions here so wording drift cannot broaden Root's turn.
    assert _field(contract, "root_progress_response_channel") == (
        "commentary_while_required_dependencies_or_root_post_actions_remain"
    )
    assert _field(contract, "root_final_response_precondition") == (
        "all_required_owner_terminal_conclusions_received_and_root_authorized_post_actions_complete_or_explicitly_reported_blocked"
    )
    assert _field(contract, "subagent_terminal_delivery") == (
        "mailbox_update_requires_active_root_wait_or_later_user_turn;"
        "does_not_reactivate_ended_root_turn"
    )

    assert _field(contract, "root_wait_policy") == (
        "bounded_wait_agent_while_safe_required_work_remains"
    )
    assert _field(contract, "root_progress_question_behavior") == (
        "commentary_without_yielding_active_root_turn"
    )
    assert _field(contract, "root_wdm_terminal_requirement") == (
        "depended_upon_WDM_TERMINAL_necessary_but_insufficient_for_Root_final"
    )
    assert _field(contract, "root_post_action_scope") == (
        "accepted_path_record|integrate|canonical_reload|runtime_smoke|"
        "release_or_retain_as_applicable"
    )
    assert _fields(contract, "root_final_exceptions") == {
        "genuinely_blocked_on_new_user_authority_or_decision",
        "user_explicitly_replaces_or_cancels",
    }
    assert _field(contract, "root_final_unfinished_work") == "explicit_report_required"
    assert _fields(contract, "root_continuation_forbidden") == {
        "background_callback",
        "scheduler",
        "watcher",
        "automatic_continuation",
        "busy_polling",
    }


def test_root_turn_lifecycle_prose_preserves_dependency_and_exception_edges() -> None:
    contract = " ".join(SESSION_CONTRACT.read_text(encoding="utf-8").split()).lower()

    # Structural windows tolerate line wrapping while preserving causal edges.
    assert re.search(
        r"safe required work remains.{0,100}bounded.{0,10}wait_agent",
        contract,
    )
    assert re.search(
        r"progress questions.{0,100}commentary.{0,100}without yielding",
        contract,
    )
    assert re.search(
        r"depended-upon wdm.{0,20}terminal.{0,100}necessary but insufficient",
        contract,
    )
    assert re.search(
        r"terminal.{0,180}(?:completes|explicitly reports blocked).{0,180}"
        r"applicable (?:accepted-path )?record",
        contract,
    )
    assert re.search(
        r"final response with unfinished work.{0,220}"
        r"genuinely blocked.{0,220}replaces or cancels",
        contract,
    )
    assert re.search(r"blocked actions and unfinished work.{0,80}reported", contract)
    assert re.search(
        r"mailbox terminal updates.{0,120}active root wait.{0,120}"
        r"later user turn.{0,120}never reactivate",
        contract,
    )
    assert re.search(
        r"background callbacks?, schedulers?, watchers?, automatic continuation"
        r" and busy polling are forbidden",
        contract,
    )
