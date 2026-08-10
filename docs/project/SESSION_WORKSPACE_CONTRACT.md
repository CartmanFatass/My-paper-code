# HMASD Session Workspace Contract

```text
document_kind=session_workspace_contract
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
workflow_role_label=workflow_design_manager
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
```

## Ownership model

Workflow-design, code, runtime and research authority remain with the owner
Roles and the router. This contract defines only workspace roots, sender/receiver
byte storage, owner write partitions, current-work links and the Root-managed
worktree boundary. Root alone relays user requests and owner results across
lanes, controls task lifecycle, provisions/records/integrates/releases or
retains managed worktrees, and physically writes canonical state only after the
owning L1 accepts a proposal. The helper is a Root-controlled lifecycle tool,
not a child identity, ticket, Git authority or admission substitute.

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
operations.

The Root-controlled lifecycle keeps at most one nonterminal receipt per
assignment. A local helper failure is recorded as nonterminal so Root can retry
or park that assignment while unrelated work continues. Existing legacy
worktrees remain isolated and untouched; they are not adopted, migrated or
released by the managed lifecycle.

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
