# Result: asg_constraint_lint_seed (synthetic E1)

```toml hmasd-result
schema_version = 2
assignment_id = "asg_constraint_lint_seed"
result_kind = "INCIDENT"
author_role = "hmasd-implementer"
owner_return = "CM:control-plane"
project_map_anchor = "Low-intrusion control-plane route"
files_observed = ["tools/hmasd_control_plane/constraint_lint.py"]
files_changed = []
symbols_changed = []
direct_consumer_checked = "tools/hmasd_control_plane/boundary_cli.py"
```

```toml hmasd-impact
schema_version = 1
incident_level = "E1_EXACT_OPERATION_INCIDENT"
observed_object_kind = "agentify_operation"
observed_object_id = "op_synthetic_e1"
affected_actions = ["resend_exact_operation"]
unaffected_actions = ["inspect_existing_provider_state", "continue_local_analysis"]
does_not_imply = ["root_session_stopped", "direction_paused", "user_authority_required"]
recovery_owner = "WORKFLOW_RECOVERY_MANAGER"
escalate_to = "CM:control-plane"
escalate_when = ["new_provider_identity_required"]
```

## Conclusion

Only the synthetic exact operation is fenced; the CM assignment and Root
continuation remain authorized.
