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
workflow_session_identity=role_based
workflow_session_owner_id=workflow_design_manager
workflow_successor_rotation=integrated_batch_completion
workflow_successor_brief=current_commit|accepted_stable_change|real_unfinished_item|next_user_goal|next_map_or_interface
workflow_thread_registry=forbidden
same_file_concurrent_writes=forbidden
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

## Shared temporary semantic handoffs

`docs/project/handoffs/README.md` is the tracked contract; ignored
`temp/handoffs/` is the live exchange, not a state store. Explorer owns the
`explorer_to_code_manager/` direction and CPM owns
`code_manager_to_explorer/`; each receiver is read-only. WDM owns only the
contract text.

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

## Public current work

`docs/project/CURRENT_WORK.md` is a WDM-owned link/schema index only. It names session records
under `docs/project/current-work/sessions/<role_id>.md` and common records under
`docs/project/current-work/common/<record-id>.md`; active state is not duplicated in the
index.

All registered persistent sessions may read the index and the records relevant
to their assignment. A session may edit only its own session record and common
records whose `owner_role` is that session. WDM owns
`workflow_control_plane`; CPM owns project operational common records; Explorer
owns only its research pointer when registered. Shared records have one owner,
and concurrent writes to one file are forbidden.

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
