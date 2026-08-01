# Workflow Design Manager workspace

```text
session_owner_role=workflow_design_manager
durable_workspace=docs/session-workspaces/workflow_design_manager/
temporary_workspace=temp/sessions/workflow_design_manager/
shared_surface_owner=true
```

This tracked directory holds compact plans and receipts for shared control-plane
changes. It contains no runtime, science, code acceptance or another session's
state. Temporary material and outgoing handoffs belong under the paired ignored
temporary workspace.

Authority and shared-path ownership come from
`docs/project/SESSION_WORKSPACE_CONTRACT.md`; this README does not duplicate or
expand them.
