# HMASD Session Workspace Contract

```text
document_kind=session_workspace_contract
control_plane_document_routes=docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md
control_plane_document_routes_not=task_state|history|hash|receipt|queue|admission|acceptance
workflow_child_parent=workflow_design_manager
durable_workspace_root=docs/session-workspaces/<role_id>/
temporary_workspace_root=temp/sessions/<role_id>/
compatibility_path_semantics=stable_role_locator_not_live_session_thread_or_admission_identity
task_scope=fresh_cli_root_task|exact_assignment
child_assignment_brief=temp/sessions/<parent_role>/assignments/<assignment_id>.md
child_assignment_format=self_contained_natural_language_not_schema_admission
child_forked_context=background_only
workflow_assignment_identity=workflow_assignment_id|owned_paths|wdm_session_workspace
workflow_assignment_identity_semantics=scope_anchor_only_not_task_meaning_or_completion
l1_user_facing_display_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md
l1_user_facing_display_scope=Root_dispatched_L1_task_name|progress_label|report_label
l1_user_facing_manager_prefixes=workflow_manager:WM_<purpose>|independent_research_explorer_manager:EM_<direction>|code_project_manager:CM_<purpose_or_direction>
l1_user_facing_suffix_rule=short_semantically_informative_purpose_or_direction
l1_internal_task_id_rule=immutable_internal_id_may_differ_from_user_facing_label
l1_wm_display_semantics=workflow_control_plane_only|research_routing_target_allowed|research_execution_not_implied
l1_em_display_semantics=independent_research_execution_for_named_direction
l1_cm_display_semantics=code_project_execution_for_named_purpose_or_direction
l1_em_scope_key_forms=direction:<id>
l1_cm_scope_key_forms=direction:<id>|shared:<component>
l1_scope_key_safe_atom=[a-z0-9][a-z0-9._-]{0,63}
l1_scope_key_reject=empty|extra_colon|separators|whitespace|..
l1_user_facing_clarity_fields=research_execution|science_state_changed
l1_wm_research_routing_defaults=research_execution=false|science_state_changed=false
l1_wm_status_exception=separate_authorized_em_science_result_must_exist_for_any_true_research_or_science_claim
l1_display_name_change_effect=research_execution=false|science_state_changed=false
root_macro_portfolio_owner=Root
root_macro_portfolio_science_authority=cross_direction_compare|rank|pause_continue|dependencies|complete_map_acceptance
root_direction_research_execution_owner=independent_research_explorer(direction:<id>)
root_code_technical_acceptance_owner=code_project_manager(direction:<id>|shared:<component>)
direction_research_execution_owner=EM(direction:<id>)
direction_code_technical_acceptance_owner=CM(direction:<id>|shared:<component>)
root_formal_project_canonical_science_boundary=user_external_pro
workflow_role_label=workflow_design_manager
owner_l1_multiplicity=role_defined_scope_keyed_within_root_tree
owner_scope_key_uniqueness=one_l1_per(role,role_defined_scope_key)_within_root_tree
owner_scope_key_semantics=semantic_ownership_and_concurrency_locator_only
owner_scope_key_not=ticket|session_identity|thread_identity|scheduler|queue|ledger|admission_token|continuity_mechanism
owner_roles_define_scope_key_fields=role_specific_and_future_evolvable
workflow_scope_key_field=workflow_scope_key
workflow_l1_parallelism=disjoint_frozen_workflow_scopes_only
workflow_same_path_or_unfrozen_contract=dependency_order_or_serialization
workflow_root_reload=fresh_root_task_canonical_reload
workflow_root_reload_brief=current_commit|accepted_stable_change|real_unfinished_item|next_user_goal|next_map_or_interface
workflow_thread_registry=forbidden
same_file_concurrent_writes=forbidden
public_current_work_partition_status=active_index_and_partitions
public_current_work_index=docs/project/CURRENT_WORK.md
public_current_work_index_owner=workflow_design_manager
workflow_incident_log=docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md
workspace_boundary_guard=fail_closed_for_recognized_pretooluse_cases
workspace_admission=fresh_cli_root_with_exact_assignment_owned_paths_for_exemptions|root_managed_worktree_for_tracked_writers
workspace_identity_precondition=none
authoritative_write_boundary=assignment_exact_owned_paths|root_accepted_proposal|root_git_integration
tracked_writer_definition=any_assignment_that_may_write_a_tracked_path
tracked_writer_mixed_write_classification=tracked_writer
tracked_writer_exemptions=read_only|ignored_only|temporary_only
root_managed_worktree_authority=root_only
root_managed_worktree_helper=scripts/hmasd_root_managed_worktree.py
root_managed_worktree_lifecycle=root_provision|root_record|root_integrate|root_release_or_retain
root_managed_worktree_receipt=root_controlled_lifecycle_receipt_returned_to_root
root_managed_worktree_one_nonterminal=at_most_one_nonterminal_receipt_per_assignment
root_managed_worktree_local_failure=receipt_local_failure_is_nonterminal_and_root_retries_or_parks
root_managed_worktree_legacy_isolation=legacy_worktrees_are_untouched_and_never_adopted
raw_child_git_worktree=forbidden
hooks={}|disabled_non_authoritative_never_enabled_trusted_or_invoked
runtime_invariants=max_threads=20|max_depth=2
root_to_wdm_caller_action=fork_turns=1
root_to_wdm_forked_context=background_only
wdm_to_registered_implementer_action=fork_turns=none
wdm_disjoint_implementer_dispatch=parallel_when_paths_and_contracts_are_disjoint
completion_order_semantics=no_priority
shared_l1_worktree_conditions=same_frozen_base|exact_disjoint_paths|no_l2_git|one_shared_l1_slice_candidate|Root_records_after_all_children_finish
managed_worktree_allocation=one_writable_l1_assignment_one_root_managed_worktree
l2_worktree_lifecycle=forbidden
independent_candidate_or_release_lifecycle=new_l1_assignment_required
concurrent_wdm_cpm_l1_worktrees=distinct_root_managed_worktrees
convergence_worktree=separate_root_managed_worktree
root_candidate_record_or_commit=after_all_l1_children_finish
workflow_path=direct_orchestration_normal_path_plus_one_bounded_local_recovery
workflow_forbidden_control_surfaces=scheduler|queue|ledger|ticket_registry|hash_admission|digest_admission|fingerprint_admission|polling|recovery_state_machine|new_global_gate
workflow_slice_result=wdm_accepts_exact_slice_then_returns_candidate_ready_packet
workflow_candidate_integration=Root_records_and_integrates_candidate_set_after_all_children_finish
workflow_change_risk_tiers=high|bounded_contract|low_causal_repair
workflow_route_table_policy=clear_route_loads_defining_source_direct_consumers_focused_tests|missing_ambiguous_conflicting_or_authority_crossing_route_requires_Auditor
workflow_singleton_package=one_writable_WDM_L1_exact_final_frozen_bytes_reviewed_together
workflow_singleton_acceptance=one_advisory_Reviewer_then_same_WDM_package_acceptance_before_Root_integration
workflow_multi_candidate_convergence_trigger=two_or_more_independently_reviewed_WDM_candidates|actual_union_differs_from_every_reviewed_package
workflow_union_convergence=conditional_on_workflow_multi_candidate_convergence_trigger
workflow_causal_check_timing=when_all_consumed_bytes_are_frozen_before_package_acceptance
workflow_progress_event_emission=each_relevant_event_at_most_once|adjacent_observations_may_share_one_report
workflow_reviewer_authority=advice_only_no_acceptance
workflow_union_acceptance_not_implied_by=slice_candidate|Root_integration|Reviewer_advice|commit
workflow_convergence_owner=WDM_only_explicit_workflow_convergence
workflow_domain_convergence=forbidden_standing_or_fresh
workflow_extra_union_reviewer=forbidden
direction_shared_slice_acceptance=owning_CM_final_for_slice
direction_shared_root_integration=Root_mechanical_only
direction_shared_union_checks=Root_union_Tests_and_Static
direction_shared_conflict_route=owning_CM_or_temporary_named_shared_CM
direction_shared_forbidden_scopes=portfolio_scope|integration_scope|shared_all
workflow_validation_layers=slice_local|integration_cross_slice|runtime_fresh_smoke_after_root_integration_reload
workflow_validation_ownership=slice_local:writer|integration_cross_slice:WDM|runtime_fresh_smoke_after_root_integration_reload:Root
workflow_writer_validation_scope=owned_paths|smallest_affected_contracts
workflow_writer_full_suite=forbidden
workflow_wdm_integration_suite=exactly_one_after_WRITES_COMPLETE_and_writes_freeze
workflow_root_runtime_smoke=Root_only_after_integration_and_canonical_reload
root_direction_context=compact_direction_packets|lazy_direction_pointers
em_direction_context=one_named_direction_only
cm_direction_context=direct_direction_or_shared_interfaces_only
portfolio_context_preload=forbidden
workflow_validation_failure_classes=environment_setup|product_assertion
workflow_environment_setup_recovery=same_layer_rerun_without_retry_state
workflow_product_failure_recovery=repair_causal_contract_or_implementation
workflow_consumer_finalization=all_direct_producer_bytes_frozen_before_final_consumer_write_or_run|independent_producers_parallel
workflow_causal_observation_before_repair=all_independently_runnable_focused_causal_commands_terminal_before_product_repair_dispatch|environment_or_parse_blocker_repair_same_layer_then_continue_observation
workflow_product_repair_dispatch=complete_observed_product_failures_grouped_by_exact_nonoverlapping_owned_paths|minimal_repair_dispatches|not_stale_literal_serial_dispatch
workflow_validation_layer_preflight=once_per_layer_before_product_evidence|lightweight_short_basetemp_parent_and_actual_command_host|not_doctor_or_global_health_check_or_acceptance_gate
workflow_windows_basetemp=short_absolute_assignment_specific_under_root_controlled_parent
workflow_windows_integration_basetemp=C:\Projects\ht\<assignment-run>
workflow_progress_event_names=DISPATCHED|WRITES_COMPLETE|TESTS_COMPLETE|REVIEW_READY|TERMINAL
workflow_progress_event_owner=WDM
workflow_progress_event_meanings=DISPATCHED:actions_started|WRITES_COMPLETE:all_writers_terminal_and_exact_changed_paths_frozen|TESTS_COMPLETE:required_test_layers_completed_with_evidence|REVIEW_READY:exact_union_and_evidence_frozen_for_one_Reviewer|TERMINAL:terminal_conclusion_returned_to_Root
workflow_progress_event_semantics=status_observations_only|not_scheduler|not_queue|not_ledger|not_background_callback|not_retry_state|not_admission|not_acceptance_token
workflow_progress_event_transport=Root_task_or_report_boundary_only
workflow_progress_event_transport_not=persistent_store|background_callback|queue|ledger
workflow_terminal_event_not_acceptance=true
root_progress_response_channel=commentary_while_required_dependencies_or_root_post_actions_remain
root_final_response_precondition=all_required_owner_terminal_conclusions_received_and_root_authorized_post_actions_complete_or_explicitly_reported_blocked
subagent_terminal_delivery=mailbox_update_requires_active_root_wait_or_later_user_turn;does_not_reactivate_ended_root_turn
root_wait_policy=bounded_wait_agent_while_safe_required_work_remains
root_progress_question_behavior=commentary_without_yielding_active_root_turn
root_wdm_terminal_requirement=depended_upon_WDM_TERMINAL_necessary_but_insufficient_for_Root_final
root_post_action_scope=accepted_path_record|integrate|canonical_reload|runtime_smoke|release_or_retain_as_applicable
root_final_exceptions=genuinely_blocked_on_new_user_authority_or_decision|user_explicitly_replaces_or_cancels
root_final_unfinished_work=explicit_report_required
root_continuation_forbidden=background_callback|scheduler|watcher|automatic_continuation|busy_polling
workflow_integrated_review=exactly_one_advisory_Reviewer_after_TESTS_COMPLETE_and_REVIEW_READY
workflow_integrated_review_followup=one_pass_no_second_review
workflow_auditor_policy=high_requires_Auditor|bounded_contract_clear_route_may_skip_with_WDM_rationale|low_causal_repair_may_skip_with_WDM_rationale|missing_ambiguous_conflicting_or_authority_crossing_route_requires_Auditor
workflow_auditor_skip_evidence=concrete_WDM_rationale|focused_causal_evidence_on_all_frozen_consumed_bytes
workflow_auditor_policy_not=gate|second_acceptance_owner
workflow_root_l1_start_guidance=useful_owned_work_and_useful_action_or_matching_leaf_capacity
workflow_root_l1_start_guidance_not=quota|reservation|scheduler|admission_gate|pool|runtime_authorization
workflow_max_threads_semantics=20_agent_tree_ceiling_only_not_runtime_authorization
workflow_runtime_pool=forbidden
agentify_transport_workspace_code_project_manager=temp/sessions/agentify_transport_operator/code_project_manager/<assignment>/
agentify_transport_workspace_independent_research_explorer=temp/sessions/agentify_transport_operator/independent_research_explorer/<assignment>/
agentify_transport_parent_wdm=forbidden
agentify_transport_assignment=AGENTIFY_REVIEW_BATCH_ASSIGNMENT
agentify_transport_assignment_locators=batch_path|results_path
agentify_transport_batch_locators=context_path|question_paths
agentify_transport_result=AGENTIFY_REVIEW_BATCH_RESULT
agentify_transport_result_locator=results_path
agentify_transport_result_path_guard=.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py
agentify_transport_result_guard_inputs=repo|expected_results_path|returned_results_path
agentify_transport_result_guard_timing=child_after_write_before_COMPLETE|requester_after_terminal_before_read
agentify_transport_result_guard_scope=strict_assignment_descendant_no_root_generic
agentify_transport_result_guard_error=ERROR_empty_results_path_actual_error
cpm_mechanical_assignment=CPM_MECHANICAL_TASK_ASSIGNMENT
cpm_mechanical_assignment_locators=spec_path|result_path
cpm_mechanical_result=CPM_MECHANICAL_TASK_RESULT
cpm_mechanical_result_locator=result_path
explorer_reverse_intake_patch_root=temp/sessions/independent_research_explorer/<root-assignment>/state-proposals/
explorer_reverse_intake_patch_locator=<patch-root>/<proposal>.patch
explorer_reverse_intake_payload=small_self_contained_semantic_delta
explorer_reverse_intake_payload_bindings=canonical_source_locator|candidate_target_locator|git_revision_locator|exact_old_new_text_or_unified_patch|frozen_semantics_and_consequences
explorer_reverse_intake_writer=hmasd-research-artifact-writer
explorer_reverse_intake_writer_check=exact_destination|payload_presence|UTF-8/LF
explorer_reverse_intake_full_map_transport=forbidden
explorer_reverse_intake_root_install=exact_path_and_git_revision_check_then_exact_copy
explorer_reverse_intake_retry=one_concrete_delta_clarification_only
explorer_reverse_intake_retry_state_queue_receipt_validator=forbidden
```

## L1 user-facing display names

Root-dispatched L1 task names, progress labels and report labels use the
prefix for the actual manager lane: `WM_<purpose>` for Workflow Manager,
`EM_<direction>` for the Independent Research Explorer Manager, and
`CM_<purpose_or_direction>` for Code Manager. The suffix is short and
semantically informative. These are user-facing labels; immutable internal task
IDs may differ.

The prefix is part of the meaning, not a rename of a profile or agent type.
`WM_` identifies workflow/control-plane work even when its short purpose names
a research-routing target; research execution belongs under `EM_`. A WM task
that changes research routing reports the clarity fields
`research_execution=false` and `science_state_changed=false`. A separate,
authorized EM science result may provide contrary research or science evidence
only when that result actually exists; the WM routing change and this naming
contract perform no research and change no science state.

## Plain-language-first cross-owner messages

Every assignment, progress report and terminal result crossing Root↔L1 or
L1↔L2 begins with concise outcome-first prose. It states the request or
outcome, why it matters, the concrete files or objects and their relationship,
the responsible owner, the next action and the consequence if work is missed
or unresolved. Define every non-obvious task-local term on first use, and have
a child result mirror the meanings in its assignment instead of silently
renaming them. Then append the relevant factual tail. No named heading or
token is required; an unheaded message is valid and not noteworthy. State the
actual task or event meaning once rather than repeating this communication
guidance as boilerplate. Prefer ordinary words to a new abbreviation; keep an
exact canonical field name only when needed and gloss its meaning once.

An actionable assignment, progress report or terminal result has both layers:
the plain-language explanation above, followed by only the smallest
task-relevant factual tail. As applicable, that tail identifies identity or
scope, paths or artifacts, action or status, commands or observed evidence, an
unresolved blocker and next owner, and residual uncertainty when applicable.
Narrative-only
messages cannot pin work to concrete objects, while fields-only messages omit
the causal meaning; both are insufficient. No irrelevant fields or giant fixed
schema is required, and hashes are not invented: an existing supplied locator
or genuine integrity boundary may still require one under the established
contract.

This is a prose contract for readers without inherited thread context; it
preserves technical detail after the explanation and requires both the
semantic prose and the smallest relevant factual tail. Narrative-only and
fields-only messages are insufficient. It is not a message schema, packet
validator, queue, ledger, admission token or acceptance mechanism. The same
meaning-first order applies to the five WDM status observations, Root
lifecycle/return-reload reports and acceptance reports, while their existing
owners, event meanings and acceptance boundaries remain unchanged.

## Workflow validation and progress vocabulary

The keyed fields above are the single defining source for workflow validation,
failure classification, progress observations and integrated review. Writers
validate only their owned paths and the smallest affected contracts at the
`slice_local` layer; WDM runs exactly one `integration_cross_slice` suite after
writes freeze; and the `runtime_fresh_smoke_after_root_integration_reload`
layer belongs exclusively to Root after Root integrates the accepted paths and
reloads canonical state. That runtime layer is therefore pending until Root's
post-integration action in any in-flight slice.

The progress vocabulary is exactly `DISPATCHED`, `WRITES_COMPLETE`,
`TESTS_COMPLETE`, `REVIEW_READY` and `TERMINAL`. WDM publishes these as
status-only observations with the meanings in the keyed contract fields; they
are not scheduling, queuing, ledger, callback, retry, admission or acceptance
mechanisms, and `TERMINAL` does not mean accepted.

Root lifecycle closure is separate from WDM progress. While safe required work
remains, Root uses bounded `wait_agent`; progress questions receive commentary
without yielding the active Root turn. A depended-upon WDM `TERMINAL` is
necessary but insufficient for Root's final response: Root still completes or
explicitly reports blocked each applicable accepted-path record, integrate,
canonical reload, runtime smoke and release-or-retain action. Mailbox terminal
updates require an active Root wait or a later user turn and never reactivate
an ended Root turn. Root may send a final response with unfinished work only
when genuinely blocked on new user authority or a decision, or when the user
explicitly replaces or cancels the work; the blocked actions and unfinished work
must be reported. Background callbacks, schedulers, watchers, automatic
continuation and busy polling are forbidden.

Windows validation uses a short absolute assignment-specific basetemp below
the Root-controlled parent; the integration verifier's host path is
`C:\Projects\ht\<assignment-run>`. Environment-setup failures stay distinct
from product-assertion failures: setup is repaired and rerun at the same layer
without retry state, while product failures repair the causal contract or
implementation.

Before product evidence at each validation layer, perform one lightweight
preflight of that layer's short basetemp parent and actual command host. It is
not a doctor, global health check or acceptance gate. Independent producers may
run in parallel, but a final consumer write or run waits until all of its
direct producer bytes freeze. Before dispatching a product repair, collect
terminal observations from every independently runnable focused command in the
causal family. Repair an environment or parse blocker at that same layer, then
continue the observations. Group the complete observed product failures by
exact nonoverlapping owned paths into as few repair dispatches as possible;
never serially dispatch stale literal failures one at a time.

## Ownership model

Workflow-design, code, runtime and research authority remain with the owner
Roles and the router. This contract defines only workspace roots, sender/receiver
byte storage, owner write partitions, scope-keyed L1 multiplicity, current-work
links and the Root-managed worktree boundary. Each owner Role defines its own
scope-key field; the generic uniqueness rule is `(role, role-defined scope key)`
within one Root tree. Root alone relays user requests and owner results across
lanes, controls task lifecycle, provisions/records/integrates/releases or
retains managed worktrees, and physically writes canonical state only after the
owning L1 accepts a proposal. A scope key is not a live session, thread,
continuity or admission identity. The helper is a Root-controlled lifecycle
tool, not a child identity, ticket, Git authority or admission substitute.
Root owns the advisory macro/portfolio science surface, including
cross-direction comparison, ranking, pause/continue and dependencies, and
complete-map acceptance. EM receives only one `direction:<id>` and owns that
direction's research execution; CM receives only `direction:<id>` or
`shared:<component>` and owns final acceptance for its slice. Root mechanically
integrates accepted slices and runs union Tests/Static. Semantic conflicts
return to the owning CM(s), or a temporary named shared CM. Formal/project-
canonical science remains at the user/External Pro boundary.

## Assignment and write boundaries

The parent writes one self-contained brief at `child_assignment_brief` (or
passes the same natural-language model natively when no workspace is granted).
`workflow_assignment_identity` locates the owned paths and workspace; it does
not replace the semantic assignment. A receiver reads only the named bytes,
writes only its owned paths and returns its conclusion to the parent. A writer
that may touch a tracked path, including a WDM workflow writer, uses a
Root-provisioned managed worktree. Read-only, ignored-only and temporary-only
assignments do not require one; mixed tracked and ignored writes do. The L1
owner semantically accepts its result or proposal and returns it to Root; Root
retains canonical writes, Git, helper lifecycle/receipt control and cross-owner
routing. Children do not invoke the helper or run raw `git worktree` lifecycle
operations. Within a Root tree, multiple WDM L1s are valid only when their
`workflow_scope_key` values identify disjoint frozen workflow scopes; a shared
writable path or still-unfrozen semantic contract creates a dependency and is
serialized. Root dispatches each WDM with `fork_turns=1`, which carries
background context only. A WDM may dispatch disjoint registered Implementers
with explicit `fork_turns=none`; all such L2 writers share the invoking L1's
Root-provisioned managed worktree only with the same frozen base, exact
disjoint paths, and no L2 Git or helper use. Root creates or records the one
shared L1 slice candidate only after all children finish. An
independent candidate or release lifecycle requires a new L1 assignment; an
L2 never receives, owns or controls a separate worktree lifecycle.
Concurrent WDM/CPM L1 assignments use distinct worktrees, and
integration/convergence uses a separate worktree. Completion order does not
establish priority.

The Root-controlled lifecycle keeps at most one nonterminal receipt per
assignment. A local helper failure is recorded as nonterminal so Root can retry
or park that assignment while unrelated work continues. Existing legacy
worktrees remain isolated and untouched; they are not adopted, migrated or
released by the managed lifecycle. The normal path has one bounded local
recovery; no scheduler, queue, ledger, ticket registry, admission fingerprint,
polling loop, recovery state machine or new global gate is introduced.

For a WDM change, each writer freezes its exact paths and the WDM returns a
candidate-ready packet. If the final bytes come from one writable WDM L1
assignment, the singleton package is reviewed together by exactly one
read-only advisory Reviewer; that same WDM may then semantically accept the
package before Root records and integrates it. A fresh convergence WDM is
required only when Root combines two or more independently reviewed WDM
candidates, or when the actual integrated union differs from every reviewed
package. That convergence WDM receives the exact integrated union, arranges
one integrated advisory review and owns union semantic acceptance. Reviewer
output is advisory and never accepts. A slice candidate, Root integration,
Reviewer advice or a commit does not by itself claim union acceptance.

Focused causal-family checks run once all bytes they consume are frozen and
before package acceptance; their evidence remains valid only while those bytes
stay unchanged. The five WDM observations retain their existing meanings and
are emitted at most once when relevant; adjacent observations may share one
meaning-first Root report without losing event names, owners, evidence or next
action, and without becoming state or acceptance data.

## Frozen package and convergence

The route table is the lazy relationship index for this contract. It names the
defining source, direct consumers, focused checks and Auditor escalation for
each control-plane trigger. A clear route lets WDM load only its row; a missing,
ambiguous, conflicting or authority-crossing route requires a bounded Auditor.
The table is a stable pointer map, never task state, history, a hash, receipt,
queue, admission or acceptance data.

## Durable and temporary files

`docs/session-workspaces/<role_id>/` is a tracked durable compatibility path for
role-associated plans and compact receipts. `temp/sessions/<role_id>/` is an
ignored task-scoped scratch and handoff path. The names retain historical
locators but do not create a live Desktop session, thread, successor or
admission identity; a fresh CLI Root task uses only its exact assignment-owned
bytes. Neither path replaces canonical science, code, runtime evidence or
review archives. A receiver reads only an assignment-named sender handoff; it
does not write another role's workspace. Root controls relay and lifecycle for
temporary bytes. No hash, byte count or digest is required for a handoff.

The Explorer reverse-intake patch is an assignment-specific temporary proposal,
not canonical state. The EM authors and semantically accepts only one small
`direction:<id>` row/delta for its own exact direction assignment. Its brief
carries that delta and the exact locators and old/new text needed to apply it;
the full Direction Action Map is never moved through an agent message or
split/encoded payload. The Writer uses only the exact destination and local
UTF-8/LF checks. Root alone accepts the complete Direction Action Map, its
cross-direction relations, unselected rows, table/map consistency and
portfolio continuity after the affected EM input. Root retains the canonical
source, patches a task-scoped candidate copy once, and performs exact-copy
installation only after the EM's full-read row/delta acceptance and Root's
path/revision check. An anchor failure preserves the original and permits one
concrete clarification only; this contract defines no retry state, queue,
receipt schema, automatic recovery or validator.

## File-backed transport locators

Agentify raw responses live under the requester-specific workspace fields above.
A named
`AGENTIFY_REVIEW_BATCH_ASSIGNMENT` locates `batch_path|results_path`, and the
batch locates `context_path|question_paths`; the parent reads only that result.
Concurrent batches use distinct assignment-specific result paths. No polling,
queue or inferred path scan is part of this contract. Production transport is
partitioned by requester: CPM uses
`temp/sessions/agentify_transport_operator/code_project_manager/<assignment>/`
and Explorer uses
`temp/sessions/agentify_transport_operator/independent_research_explorer/<assignment>/`.
The guard rejects a path outside the requesting partition and assignment
descendant; WDM is not a production transport parent.

The CPM mechanical lane uses the same file-only boundary: its assignment
locates `spec_path|result_path`, and its result locates
`status|result_path|error`. The Explorer mechanical lane is native and carries
no result file or workspace; its parent returns the response directly.

## Shared temporary semantic handoffs

`docs/project/handoffs/README.md` is the tracked contract; ignored
`temp/handoffs/` is a bounded byte relay surface, not a state store or direct
sibling channel. Explorer's Writer L2 may write only assignment-owned bytes in
the `explorer_to_code_manager/` direction and returns its bounded result to
Explorer; CPM's Writer L2 may write only assignment-owned bytes in the
`code_manager_to_explorer/` direction and returns its bounded result to CPM.
Each L1 owner returns its accepted result or proposal to Root; Root alone
relays accepted material to another owner, and the receiving owner does not
intake directly from a sibling. WDM owns only the contract text.

Handoffs are self-contained human/model-readable briefs. Formats and suggested
sections aid understanding but never become admission gates. The receiver uses
judgment and bounded safe read-only reconnaissance, stopping only for a
materially missing authority, scientific choice or concrete input object. An
ordered manifest organizes candidate-specific work without queue state.
Concurrent treatments use assignment-specific direction/treatment handoff files,
role temporary paths and runtime roots; they never share a writable file,
checkpoint or mutable trainer state. Manifest order does not allocate runtime
capacity or establish scientific priority.
Root controls retention and cleanup of the temporary exchange copy after relay.
It is never staged, committed or pushed; canonical owner records remain outside
the exchange.

## Public current work

`docs/project/CURRENT_WORK.md` is a WDM-owned link/schema index only. It names session records
under `docs/project/current-work/sessions/<role_id>.md` and common records under
`docs/project/current-work/common/<record-id>.md`; active state is not duplicated in the
index.

The existing Explorer compatibility pointer is reused for Root's macro/portfolio
surface; there is no portfolio L1. Direction pointers name one `direction:<id>`
EM scope, and current-work/index surfaces remain pointer-only without copying
scientific state or history bytes.

All registered owner tasks may read the index and the records relevant to their
assignment. A task may edit only its own role record and common records whose
`owner_role` is that role. WDM owns
`workflow_control_plane`; CPM owns project operational common records; Explorer
owns only its research pointer when registered. Shared records have one owner,
and concurrent writes to one file are forbidden.

The WDM role record is
`docs/project/current-work/sessions/workflow_design_manager.md`; its common
record is `docs/project/current-work/common/workflow_control_plane.md`. Both
retain `session_owner_id=workflow_design_manager` as a stable role label for
path compatibility, not as a live session or task identity, and retain only
fenced identity/status headers plus links. A fresh Root task loads continuity
only when the router trigger requires it; canonical science, code, runtime and
review evidence remain in their owner paths.

Code Project Manager must maintain the mandatory human-readable Technical
Treatment View on its next owner update at
`docs/project/current-work/common/explorer_project_validation.md`. The view is
allowed as a CPM-owned owner-local projection while this contract preserves the
current-work index, record ownership and pointer semantics. It is a
human-readable view/pointer only, not a schema, queue, scheduler, process
monitor, runtime-capacity source, admission source or acceptance source;
`active_assignment_id` remains only the foreground pointer. The canonical
Explorer↔CPM contract owns its detailed meaning and columns.

## Git boundary

Root is the sole Git integration actor: it may stage, commit, fetch or push an
accepted exact path set after owner acceptance. No role, task, compatibility
label or workspace path grants Git integration or push authority. Live temporary
handoffs never enter Git. Every integration uses an exact accepted path set,
preserves disjoint edits and leaves unrelated index entries untouched. A
managed-worktree receipt records Root lifecycle evidence; it is not a child
acceptance, content-hash or Git-admission token.
