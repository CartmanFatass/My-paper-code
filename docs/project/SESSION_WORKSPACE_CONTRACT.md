# HMASD Session Workspace Contract

```text
document_kind=session_workspace_contract
shared_workflow_surface_owner=workflow_design_manager
shared_workflow_design_authority=exclusive
shared_workflow_acceptance_authority=exclusive
shared_workflow_git_authority=exclusive
workflow_collaboration_skill=hmasd-collaborative-workflow-design
workflow_audit_skill=hmasd-workflow-change-audit
workflow_child_parent=workflow_design_manager
workflow_child_acceptance_authority=none
durable_workspace_root=docs/session-workspaces/<role_id>/
temporary_workspace_root=temp/sessions/<role_id>/
same_file_concurrent_writes=forbidden
public_current_work_partition_status=active_index_and_partitions
public_current_work_index=docs/project/CURRENT_WORK.md
public_current_work_index_owner=workflow_design_manager
workflow_incident_log=docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md
workflow_router_consistency_check=required_for_every_workflow_change
workflow_implementer_parallelism=file_family_adaptive
```

## Ownership model

Workflow Design Manager is the sole owner of the router, workflow roles and
profiles, workflow Skills, hooks, registries, workflow contracts and their
tests. It plans, verifies, accepts, stages, commits and pushes those surfaces.
All workflow-design requests and defects route to WDM; CPM and Explorer do not
edit or accept workflow surfaces.

Code Project Manager keeps exclusive authority for code, technical acceptance,
runtime and project operational records. Independent Research Explorer keeps
exclusive authority for advisory research and its research artifacts. Agentify
Transport Operator keeps exclusive authority for transport mechanics and writes
only its temporary workspace. Those role-local authorities do not include
workflow design, workflow acceptance or workflow Git.

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

The Agentify operator uses `temp/sessions/agentify_transport_operator/` for raw
response handoffs. CPM or Explorer reads the named result, copies it into its
own canonical archive, and performs its own scientific or mechanical intake.

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
record is `docs/project/current-work/common/workflow_control_plane.md`.
Canonical science, code, runtime and review evidence remain in their existing
owner paths and are linked rather than copied.

## Git boundary

WDM may fetch and push accepted workflow-control-plane paths. CPM, Explorer and
other sessions may fetch and push only their non-workflow code, science,
runtime, review and workspace paths. Every commit uses an exact owned path set,
preserves disjoint edits and leaves unrelated index entries untouched.
