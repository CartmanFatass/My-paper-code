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
child_assignment_brief=temp/sessions/<parent_role>/assignments/<assignment_id>.md
child_assignment_format=self_contained_natural_language_not_schema_admission
child_forked_context=background_only
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

Before spawning an Implementer, Reviewer or Verifier, WDM or Code Project
Manager writes the exact user-readable natural-language assignment beneath its
own temporary `assignments/` directory. The brief explains outcome, intent,
protected boundaries, local judgment and completion evidence. Suggested
headings aid communication but never become required fields or an admission
gate. Forked turns are background only; the brief controls task scope and
completion. A child uses bounded reconnaissance to resolve ordinary omissions
and escalates only a material outcome, authority or path change.

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
record is `docs/project/current-work/common/workflow_control_plane.md`.
Canonical science, code, runtime and review evidence remain in their existing
owner paths and are linked rather than copied.

## Git boundary

WDM may fetch and push accepted workflow-control-plane paths. Other sessions may
push only their owned non-workflow durable paths; live temporary handoffs never
enter Git. Every commit uses an exact owned path set,
preserves disjoint edits and leaves unrelated index entries untouched.
