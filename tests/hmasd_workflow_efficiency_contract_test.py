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

    assert _fields(contract, "workflow_auditor_policy") == {
        "high_risk_authority_topology_cross_owner_shared_contract_requires_Auditor",
        "low_risk_one_file_wording_or_test_only_may_skip_new_Auditor_with_WDM_rationale",
    }
    assert (
        "workflow_auditor_decision="
        "high_risk_requires_Auditor|low_risk_one_file_wording_or_test_only_may_skip_with_concrete_rationale"
    ) in manager
    assert _fields(manager, "workflow_auditor_decision") == {
        "high_risk_requires_Auditor",
        "low_risk_one_file_wording_or_test_only_may_skip_with_concrete_rationale",
    }
    assert "concrete rationale" in manager

    assert _field(contract, "workflow_integrated_review") == (
        "exactly_one_advisory_Reviewer_after_TESTS_COMPLETE_and_REVIEW_READY"
    )
    assert _field(contract, "workflow_integrated_review_followup") == (
        "one_pass_no_second_review"
    )
    assert _field(contract, "workflow_reviewer_authority") == "advice_only_no_acceptance"
    assert _field(manager, "workflow_integration_review_authority") == (
        "one_advisory_Reviewer_read_only_then_WDM_union_acceptance"
    )


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
