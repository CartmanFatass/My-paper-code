# HMASD Session Workspace Contract

```text
document_kind=session_workspace_contract
shared_workflow_surface_owner=workflow_design_manager
role_local_workflow_surface_owner=exact_persistent_session
workflow_collaboration_skill=hmasd-collaborative-workflow-design
workflow_audit_skill=hmasd-workflow-change-audit
workflow_child_parent=assigning_persistent_session
workflow_child_acceptance_authority=none
durable_workspace_root=docs/session-workspaces/<role_id>/
temporary_workspace_root=temp/sessions/<role_id>/
same_file_concurrent_writes=forbidden
independent_research_role_local_workflow_git_authority=direct_for_owned_surfaces
public_current_work_partition_status=phase_two_role_adoption_required
public_current_work_partition_authority=none_in_phase_one
```

## Ownership model

Every persistent session owns its role-local workflow, its durable workspace
and its temporary workspace. It plans, verifies, accepts, commits and pushes
only those paths. The shared Workflow Design Skills grant no authority; the
calling role charter and this contract supply it.

Workflow Design Manager owns the router, shared Workflow Design and routing
Skills, shared child charters and profiles, hooks, registries, shared workflow
contracts and their shared tests. Code Project Manager owns its charter,
code/runtime procedure and focused contracts. Independent Research Explorer
owns its charter, research procedures and focused contracts. Independent
Research Pro Review Operator owns its methodology charter, procedure and
focused contracts. An exact assignment may narrow these defaults but cannot
expand them.

Shared Workflow Auditor, Implementer, Reviewer and Cost Reviewer profiles are
owner-neutral. Every assignment supplies:

```text
session_owner_role=<locked persistent role>
session_owner_id=<locked session id>
owned_paths=<exact nonoverlapping paths>
session_workspace=docs/session-workspaces/<role>|temp/sessions/<role>
```

The child returns only to that assigning session and never accepts, stages,
commits, pushes or routes the result. The assigning session inspects and
accepts the final artifact. WDM is not an approval gate for another session's
owned workflow.

## Durable and temporary files

`docs/session-workspaces/<role_id>/` is tracked durable session material. It may
hold role-local workflow plans, accepted receipts and compact continuity notes.
It does not replace canonical code, science, runtime evidence or public current
work, and it must not copy another session's context.

`temp/sessions/<role_id>/` is ignored scratch owned by that role. Long-text
cross-task payloads are written only beneath the sender's
`temp/sessions/<role_id>/handoffs/`. A receiver may read one assignment-named
payload after verifying the locked source role; it never writes or cleans the
sender's root. The sender alone may clean an acknowledged payload.

## Public current work

The public state entry is currently `docs/project/CURRENT_WORK.md`. The target
partitioned data layout is:

```text
docs/project/current-work/common/<record-id>.md
docs/project/current-work/sessions/<role_id>.md
```

This phase-one contract grants no public-entry or partition read/write
authority. Each persistent role's separate phase-two adoption can establish
only that role's access; existing router and charter restrictions remain
controlling until then. The final shared target may permit all registered
persistent sessions to read the public partitions only after the shared router
and every affected role have adopted that access. A session may edit only its
own session file and common records whose `owner_role` equals that session. Each
common affair is one file, so independent affairs never share a write surface.
Ownership transfer is an explicit update by the current owner; two sessions
never edit the same record concurrently.

In the target layout, the public entry carries schema and links, not duplicated
active state. A session file contains only that session's tasks. A common record
contains only the shared affair it names. Canonical science, code, runtime and
review evidence remain in their existing owner paths and are referenced rather
than copied.

## Git boundary

Each persistent session may fetch and push accepted changes only inside its
owned workflow and durable workspace paths. Independent-research Git authority
does not extend to `local_research/`, code, runtime, formal state or another
session's files. Every commit uses an exact path set, preserves disjoint work,
checks the staged diff and leaves unrelated index entries untouched.
