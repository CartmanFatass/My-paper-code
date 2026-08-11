# Workflow Design Manager current work

```text
document_kind=current_work_session
schema_version=2
session_owner_role=workflow_design_manager
session_owner_id=workflow_design_manager
workstream_ids=workflow_control_plane
status=WDM_SLICE_ACCEPTED_PENDING_ROOT_CANDIDATE_RECORD_AND_INTEGRATION
control_plane_document_routes=docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md
active_wdm_route=docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md
active_wdm_route_trigger=WDM planning and confirmation
active_wdm_convergence=docs/project/SESSION_WORKSPACE_CONTRACT.md#frozen-package-and-convergence
continuity=role_based_successor_tasks
rotation_boundary=integrated_batch_completion
workflow_scope_key=core_parallel_control
worktree_allocation=one_writable_l1_assignment_one_root_managed_worktree
l2_worktree_lifecycle=forbidden_new_l1_for_independent_candidate_or_release
slice_status=exact_owned_document_slice_wdm_accepted
next_boundary=docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md
next_boundary_trigger=Risk, delegation and review
```

This pointer-only record contains WDM workflow-control-plane identity, status,
the active route and the next boundary. It is not an active-instance registry
and does not claim Root candidate record/integration, commit, Reviewer advice
or singleton/multi-candidate acceptance. It does not copy procedure, project
operation, science, runtime or review state.
