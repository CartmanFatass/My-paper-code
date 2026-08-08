# HMASD Session Workspace Contract

```text
document_kind=session_workspace_contract
shared_workflow_surface_owner=workflow_design_manager
shared_workflow_design_authority=exclusive
shared_workflow_acceptance_authority=exclusive
shared_workflow_git_authority=exclusive
workflow_collaboration_skill=hmasd-collaborative-workflow-design
workflow_audit_skill=hmasd-workflow-change-audit
assignment_writing_skill=hmasd-writing-agent-assignments
workflow_child_parent=workflow_design_manager
workflow_child_acceptance_authority=none
durable_workspace_root=docs/session-workspaces/<role_id>/
temporary_workspace_root=temp/sessions/<role_id>/
child_assignment_brief=temp/sessions/<parent_role>/assignments/<assignment_id>.md
child_assignment_format=self_contained_natural_language_not_schema_admission
child_forked_context=background_only
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
workflow_router_consistency_check=required_for_every_workflow_change
workflow_implementer_parallelism=file_family_adaptive
workspace_boundary_guard=fail_closed_for_recognized_pretooluse_cases
authoritative_write_boundary=tool_os_sandbox|verified_ticket_identity|git_visible_checks
workspace_ticket_retirement=registered_clean_detached_worktree_only
agentify_transport_child=hmasd-agentify-transport
agentify_transport_child_parent=code_project_manager|independent_research_explorer
agentify_transport_assignment=AGENTIFY_REVIEW_BATCH_ASSIGNMENT
agentify_transport_assignment_fields=batch_path|results_path
agentify_transport_batch_file_fields=provider|question_paths
agentify_transport_result=AGENTIFY_REVIEW_BATCH_RESULT
agentify_transport_result_fields=status|results_path|error
agentify_transport_terminal_status=COMPLETE|ERROR
agentify_transport_wait_visibility=silent_until_terminal_native_final
cpm_mechanical_child=hmasd-cpm-mechanical
cpm_mechanical_parent=code_project_manager
cpm_mechanical_assignment=CPM_MECHANICAL_TASK_ASSIGNMENT
cpm_mechanical_assignment_fields=spec_path|result_path
cpm_mechanical_result=CPM_MECHANICAL_TASK_RESULT
cpm_mechanical_result_fields=status|result_path|error
cpm_mechanical_terminal_status=COMPLETE|ERROR
cpm_mechanical_wait_visibility=silent_until_terminal_native_final
cpm_mechanical_write_scope=assignment_named_temporary_outputs_only
cpm_mechanical_acceptance_authority=none
cpm_mechanical_git_authority=none
cpm_mechanical_scientific_authority=none
cpm_mechanical_runtime_authority=no_experiment_no_readiness_no_agentify
cpm_mechanical_finalize_owner=code_project_manager
cpm_mechanical_activation=after_fresh_profile_reload
cpm_mechanical_active_research_state_effect=none
```

## Ownership model

Workflow Design Manager is the sole owner of the router, workflow roles and
profiles, workflow Skills, hooks, registries, workflow contracts and their
tests. It plans, verifies, accepts, stages, commits and pushes those surfaces.
All workflow-design requests and defects route to WDM; CPM and Explorer do not
edit or accept workflow surfaces.

Code Project Manager keeps exclusive authority for code, technical acceptance,
runtime and project operational records. Independent Research Explorer keeps
exclusive authority for advisory research and its research artifacts. CPM or
Explorer may request the registered Agentify transport child, which keeps
exclusive batch-scoped authority for transport mechanics and writes only its
temporary workspace. Those role-local authorities do not include workflow
design, workflow acceptance or workflow Git.

The CPM mechanical child is a CPM-only, file-bound capability. CPM remains the
sole technical acceptance, source/Git and canonical-state owner; the child
receives one exact temporary `CPM_MECHANICAL_TASK_ASSIGNMENT` and returns one
typed temporary `CPM_MECHANICAL_TASK_RESULT`. Its interface is registered by
`spec_path|result_path`, remains silent until one native terminal return, and
does not grant experiment, readiness, Agentify, science, Git or acceptance
authority. Activation requires a fresh profile reload and has no active
research-state effect.

The Explorer remains the sole owner of its research plans, continuity notes,
candidate and scientific research artifacts, and all temporary/session research
artifacts under its durable and temporary workspace. WDM is the single
acceptance owner for the explicitly listed Explorer workflow artifacts; that
acceptance does not grant workspace cleanup or write authority.

WDM workflow children are advisory or mechanical only. Every assignment names:

```text
workflow_assignment_id=<locked assignment>
owned_paths=<exact nonoverlapping paths>
wdm_session_workspace=docs/session-workspaces/workflow_design_manager|temp/sessions/workflow_design_manager
```

Children return to WDM and never accept, stage, commit, push or route results.
WDM resolves semantic junctions and performs final Git integration.

The PreToolUse workspace guard fails closed for the mutation forms it recognizes
and preserves all existing denials. It is a bounded syntactic preflight, not an
arbitrary shell-semantics proof and not a replacement for tool/OS sandboxing,
registered ticket identity or Git-visible pre/post checks. After integration,
WDM retires a ticket only through the registered ticket script when its exact
worktree is detached, at the expected HEAD and free of Git-visible changes.
Retirement never uses force or discards work; a mismatch leaves both worktree
and ticket intact.

Before designing or dispatching any registered child or cross-session task,
its parent invokes `hmasd-writing-agent-assignments`, the single
assignment-writing contract, and writes the exact user-readable brief beneath
its own temporary `assignments/` directory. File-only transport carries this
rich natural-language brief so the child can understand the owned outcome,
intent, protected boundaries, necessary observations, permitted actions,
role-local judgment, bounded recovery and completion evidence. Paths, statuses
and schema fields are anchors, not meaning; they never substitute for the
semantic outcome or the child's judgment. Suggested headings aid communication
but never become required fields or an admission gate. Forked turns are
background only; the brief controls task scope and completion. A child uses
bounded reconnaissance to resolve ordinary omissions and escalates only a
material outcome, authority or path change.

Workflow reports from other sessions are advisory inputs. WDM appends typed
defect reports to its chronological incident log. The log preserves order but
does not serialize unrelated work, create an active state or block an operating
owner's local recovery. Autonomous repair is limited to restoring an accepted stable contract;
a material authority, policy, science, runtime or external-effect change moves
to the user-confirmed change lane.

## Durable and temporary files

`docs/session-workspaces/<role_id>/` is tracked durable material for that
session's plans and compact receipts. `temp/sessions/<role_id>/` is ignored
scratch and handoff material owned by that session. Neither replaces canonical
science, code, runtime evidence or review archives. A receiver reads only an
assignment-named sender handoff; it does not write or clean another role's
workspace. No hash, byte count or digest is required for a handoff.

The registered Agentify transport child uses
`temp/sessions/agentify_transport_operator/` for raw response handoffs. CPM or
Explorer writes one exact `AGENTIFY_REVIEW_BATCH_ASSIGNMENT` naming
`batch_path|results_path`, then reads only that named result after the child's
single native terminal return. Concurrent batches use distinct assignment-
specific result paths; no parent polling, queue, monitor or inferred scan is
allowed. CPM or Explorer copies the named result into its own canonical archive
and performs its own scientific or mechanical intake.

The CPM mechanical child uses the same file-only boundary: CPM writes one exact
`spec_path` and names one exact `result_path` under its temporary workspace;
the child writes only assignment-named temporary outputs and returns
`status|result_path|error` with terminal status `COMPLETE|ERROR`. CPM alone
finalizes, accepts and records the result. No queue, monitor, inferred path
scan, experiment/readiness execution or active research-state transition is
introduced.

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
ordered manifest organizes one-candidate-at-a-time work without queue state.
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
use `session_owner_id=workflow_design_manager` as the stable role identity.
Batch completion is the preferred successor-task rotation boundary. A compact
successor brief may name the current workflow commit, accepted stable changes,
any real unfinished item, the next user goal and the next map/interface section
to load. The workspace contract creates no task and stores no thread registry.
Canonical science, code, runtime and review evidence remain in their existing
owner paths and are linked rather than copied.

## Git boundary

WDM may fetch and push accepted workflow-control-plane paths. Other sessions may
push only their owned non-workflow durable paths; live temporary handoffs never
enter Git. Every commit uses an exact owned path set,
preserves disjoint edits and leaves unrelated index entries untouched.
