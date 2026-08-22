## Impact envelope

```toml hmasd-impact
schema_version = 1
incident_level = "E1_EXACT_OPERATION_INCIDENT"
observed_object_kind = "agentify_operation"
observed_object_id = "op_<id>"
affected_actions = ["<exact action>"]
unaffected_actions = ["<authorized continuation>"]
does_not_imply = ["root_session_stopped", "direction_paused", "user_authority_required"]
recovery_owner = "WORKFLOW_RECOVERY_MANAGER"
escalate_to = "OPERATIONAL_ROOT"
escalate_when = ["<concrete condition>"]
```
