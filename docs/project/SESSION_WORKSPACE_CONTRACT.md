# HMASD Session Workspace Contract

```text
document_kind=session_workspace_contract
workflow_child_parent=workflow_design_manager
durable_workspace_root=docs/session-workspaces/<role_id>/
temporary_workspace_root=temp/sessions/<role_id>/
child_assignment_brief=temp/sessions/<parent_role>/assignments/<assignment_id>.md
child_assignment_format=self_contained_natural_language_not_schema_admission
child_forked_context=background_only
workflow_assignment_identity=workflow_assignment_id|owned_paths|wdm_session_workspace
workflow_session_identity=stable_role_plus_assignment_scoped_owner_task
workflow_session_owner_id=workflow_design_manager
workflow_successor_rotation=integrated_batch_completion
workflow_successor_brief=current_commit|accepted_stable_change|real_unfinished_item|next_user_goal|next_map_or_interface
workflow_thread_registry=forbidden_except_scheduler_active_assignment_locators
same_file_concurrent_writes=forbidden
research_scheduler_kind=user_owned_persistent_desktop_task
research_scheduler_registered_child=false
research_scheduler_profile_path=none
research_scheduler_owner=user
research_scheduler_authority=task_lifecycle_and_resource_conflict_routing_only
research_scheduler_forbidden_authority=science|code|technical_acceptance|git|runtime_execution|semantic_relay|sibling_preload
research_scheduler_owner_task_modes=explorer_direction|explorer_portfolio|cpm_treatment|cpm_integration
research_scheduler_owner_task_depth=1
research_scheduler_live_roster=temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md
research_scheduler_binding_directory=temp/sessions/research_scheduler/bindings/
research_scheduler_binding_keys=assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active
research_scheduler_binding_purpose=mutation_boundary_identity_only
research_scheduler_identity_observation_directory=temp/sessions/research_scheduler/identity_observations/
research_scheduler_identity_observation_path=temp/sessions/research_scheduler/identity_observations/<assignment_id>.json
research_scheduler_identity_observation_keys=assignment_id|thread_id|host_id|session_id
research_scheduler_identity_observation_purpose=observation_only_not_activation_or_task_context
research_scheduler_binding_task_context=false
research_scheduler_binding_queue=false
research_scheduler_procedure_pointer=.agents/skills/hmasd-research-scheduler/SKILL.md
research_scheduler_resource_policy_pointer=.agents/skills/hmasd-research-scheduler/SKILL.md
public_current_work_partition_status=active_index_and_partitions
public_current_work_index=docs/project/CURRENT_WORK.md
public_current_work_index_owner=workflow_design_manager
workflow_incident_log=docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md
workspace_boundary_guard=fail_closed_for_recognized_pretooluse_cases
authoritative_write_boundary=tool_os_sandbox|verified_ticket_identity|git_visible_checks
workspace_ticket_retirement=registered_clean_detached_worktree_only
agentify_transport_workspace=temp/sessions/agentify_transport_operator/
agentify_transport_assignment=AGENTIFY_REVIEW_BATCH_ASSIGNMENT
agentify_transport_assignment_locators=batch_path|results_path
agentify_transport_batch_locators=context_path|question_paths
agentify_transport_result=AGENTIFY_REVIEW_BATCH_RESULT
agentify_transport_result_locator=results_path
cpm_mechanical_assignment=CPM_MECHANICAL_TASK_ASSIGNMENT
cpm_mechanical_assignment_locators=spec_path|result_path
cpm_mechanical_result=CPM_MECHANICAL_TASK_RESULT
cpm_mechanical_result_locator=result_path
cpm_treatment_write_scope_count=2
cpm_treatment_write_scopes=ticket_local_paths_inside_one_registered_worktree|one_exact_strict_descendant_main_checkout_transport_path
cpm_treatment_reverse_handoff_root=temp/handoffs/code_manager_to_explorer/
cpm_treatment_reverse_handoff_locator=assignment_named_exact_strict_descendant
cpm_treatment_main_checkout_mutation=apply_patch_only_reverse_handoff_no_git
cpm_treatment_canonical_result=assignment_named_treatment_artifact_evidence_acceptance_record
cpm_integration_main_checkout_semantics=unchanged_shared_mainline_integration_only
```

## Ownership model

Workflow-design, code, runtime and research authority remain with the owner
Roles and the router. This contract defines only workspace roots, sender/receiver
byte storage, owner write partitions and current-work links.

## Assignment and write boundaries

The parent writes one self-contained brief at `child_assignment_brief` (or
passes the same natural-language model natively when no workspace is granted).
`workflow_assignment_identity` locates the owned paths and workspace; it does
not replace the semantic assignment. A receiver reads only the named bytes,
writes only its owned paths and returns its conclusion to the parent. Acceptance,
Git and cross-task routing remain with the owner Role.

## Durable and temporary files

`docs/session-workspaces/<role_id>/` is tracked durable material for that
session's plans and compact receipts. `temp/sessions/<role_id>/` is ignored
scratch and handoff material owned by that session. Neither replaces canonical
science, code, runtime evidence or review archives. A receiver reads only an
assignment-named sender handoff; it does not write or clean another role's
workspace. No hash, byte count or digest is required for a handoff.

The Scheduler durable pointer is
`docs/session-workspaces/research_scheduler/README.md`. Its active roster and
bindings are temporary only; no tracked live state is created. The roster is a
human-readable locator, identity observations use the declared temporary
directory and four keys, and each binding contains only the six identity keys
in `research_scheduler_binding_keys`. Identity observations are not activation,
task context, queue, registry, ledger, semantic result or acceptance state.

## File-backed transport locators

Agentify raw responses live under `agentify_transport_workspace`. A named
`AGENTIFY_REVIEW_BATCH_ASSIGNMENT` locates `batch_path|results_path`, and the
batch locates `context_path|question_paths`; the parent reads only that result.
Concurrent batches use distinct assignment-specific result paths. No polling,
queue or inferred path scan is part of this contract.

The CPM mechanical lane uses the same file-only boundary: its assignment
locates `spec_path|result_path`, and its result locates
`status|result_path|error`. The Explorer mechanical lane is native and carries
no result file or workspace; its parent returns the response directly.

## Desktop Research Scheduler boundary

The Research Scheduler is a single persistent, user-visible Desktop task
owned by the user. It creates same-level ephemeral Explorer or CPM owner tasks;
those owner tasks retain their existing registered children and `max_depth=1`.
The Scheduler is not a registered child and has no `.codex` profile or
configuration. It owns lifecycle and resource-conflict routing only, with no
science, code, technical acceptance, Git, runtime execution, semantic relay or
sibling-preload authority.

The frozen Desktop lifecycle, initial-prompt guard and ambiguous-action
fallback are defined once by `research_scheduler_procedure_pointer`; this
workspace contract does not repeat command-level procedure.

The human-readable live roster is
`temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md` and remains ignored
temporary state. The machine record is
`temp/sessions/research_scheduler/bindings/<assignment_id>.json` with exactly
`assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active`.
This binding is mutation-boundary identity only; it is not task context, queue
state or a result ledger.

Resource-conflict policy and its exclusions are defined once by
`research_scheduler_resource_policy_pointer`; this contract stores the
workspace and identity boundary only.

## Shared temporary semantic handoffs

`docs/project/handoffs/README.md` is the tracked contract; ignored
`temp/handoffs/` is the live exchange, not a state store. Explorer owns the
`explorer_to_code_manager/` direction and CPM owns
`code_manager_to_explorer/`; each receiver is read-only. For a CPM
`owner_mode=treatment` assignment, the binding names exactly two physical write
scopes: ticket-local paths inside one registered worktree and one exact
strict-descendant main-checkout transport path under
`temp/handoffs/code_manager_to_explorer/`. The descendant is the only allowed
main-checkout treatment write; the root and sibling paths are never granted.
WDM owns only the contract text.

Handoffs are self-contained human/model-readable briefs. Formats and suggested
sections aid understanding but never become admission gates. The receiver uses
judgment and bounded safe read-only reconnaissance, stopping only for a
materially missing authority, scientific choice or concrete input object. An
ordered manifest organizes candidate-specific work without queue state.
Concurrent treatments use assignment-specific direction/treatment handoff files,
role temporary paths and runtime roots; they never share a writable file,
checkpoint or mutable trainer state. Manifest order does not allocate runtime
capacity or establish scientific priority.
The sender removes the temporary exchange copy after intake. It is never staged,
committed or pushed; canonical owner records remain outside the exchange.

The CPM treatment reverse handoff is disposable transport only. It points to the
exact assignment-named treatment artifact, evidence and technical-acceptance
record; it is not that canonical result, an acceptance record, result ledger,
queue, Scheduler semantic relay or Git object. Treatment Git and shell mutation
remain ticket-worktree-scoped, while the one named main-checkout handoff file is
written with `apply_patch` only and has no Git authority. Explorer reads only the
exact named handoff/technical locators and performs exactly one scientific
intake. Scheduler routes/checks locators mechanically and does not interpret the
result. `owner_mode=integration` retains its existing shared-mainline semantics
and does not repeat treatment runtime or acceptance.

## Public current work

`docs/project/CURRENT_WORK.md` is a WDM-owned link/schema index only. It names session records
under `docs/project/current-work/sessions/<role_id>.md` and common records under
`docs/project/current-work/common/<record-id>.md`; active state is not duplicated in the
index.

The user-owned Scheduler pointer is
`docs/project/current-work/sessions/research_scheduler.md`; it records only the
role/workspace locator and stable status links. Live owner assignments remain
under the ignored Scheduler roster and binding paths above.

Registered persistent control tasks and assignment-scoped owner tasks may read
only index records relevant to their assignment. An owner may edit only its
named owner record and common records whose `owner_role` matches its authority.
WDM owns
`workflow_control_plane`; CPM owns project operational common records; Explorer
owns only its research pointer when registered. Shared records have one owner,
and concurrent writes to one file are forbidden.

A session may edit only its own session record. Assignment-scoped Explorer and
CPM owner tasks do not acquire a public session-record partition; their
lifecycle locators remain Scheduler-owned as defined above.

The WDM session record is
`docs/project/current-work/sessions/workflow_design_manager.md`; its common
record is `docs/project/current-work/common/workflow_control_plane.md`. Both
use `session_owner_id=workflow_design_manager` as the stable role identity and
retain only fenced identity/status headers plus links. Continuity details are
loaded only when the router trigger requires them; canonical science, code,
runtime and review evidence remain in their owner paths.

## Git boundary

WDM may fetch and push accepted workflow-control-plane paths. Other sessions may
push only their owned non-workflow durable paths; live temporary handoffs never
enter Git. Every commit uses an exact owned path set,
preserves disjoint edits and leaves unrelated index entries untouched.
