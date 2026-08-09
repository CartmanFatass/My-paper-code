# Workflow Design Manager current work

```text
document_kind=current_work_session
schema_version=2
session_owner_role=workflow_design_manager
session_owner_id=workflow_design_manager
workstream_ids=workflow_control_plane
status=CENTRAL_WORKFLOW_AUTHORITY_ACTIVE
continuity=role_based_successor_tasks
rotation_boundary=integrated_batch_completion
next_boundary=role_reload_receipts
```

This record contains only WDM workflow-control-plane identity and status. It
does not copy project operation, science, runtime or review state.
