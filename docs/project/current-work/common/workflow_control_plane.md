# Workflow control plane

```text
document_kind=current_work_common_record
schema_version=2
record_id=workflow_control_plane
record_kind=workflow_surface
owner_role=workflow_design_manager
status=CENTRALIZED_ACTIVE
authority=workflow_design_manager_exclusive
workflow_runtime_authority=none
session_owner_id=workflow_design_manager
continuity=role_based_successor_tasks
rotation_boundary=integrated_batch_completion
next_boundary=all_registered_sessions_reload_role_and_skill
```

This record names the active control-plane owner and next reload boundary only.
It also records the stable role identity used when a successor task reloads
the workflow. A compact successor brief may identify the current workflow
commit, accepted stable change, real unfinished item, next user goal and next
map/interface section; no thread registry or automatic task creation exists.
It contains no scientific conclusion, runtime state, code result or review
response.
