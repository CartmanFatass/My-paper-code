# Assignment: Constraint lint boundary

```toml hmasd-assignment
schema_version = 2
assignment_id = "asg_constraint_lint_seed"
assignment_mode = "IMPLEMENTATION"
semantic_owner = "CM:control-plane"
executor_role = "hmasd-implementer"
return_to = "CM:control-plane"
strictness_profile = "R1_ROUTINE_ENGINEERING"
evidence_class = "B"
result_bearing = false
runtime_profile = ""
requirement_ids = ["UR-RECOVERY-001"]
nonrequirement_ids = ["NR-HASH-HANDOFF-001"]
recovery_owner = "CM:control-plane"
result_path = "docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/results/RESULT_asg_constraint_lint_seed.md"
project_map_anchor = "Low-intrusion control-plane route"
architecture_role = "CONTROL_PLANE"
affected_files = ["tools/hmasd_control_plane/constraint_lint.py"]
create_files = []
affected_symbols = ["lint_repository"]
search_roots = []
direct_consumers = ["tools/hmasd_control_plane/boundary_cli.py"]
upstream_inputs = ["docs/project/PROJECT_REQUIREMENTS.toml"]
state_owner = "lint_repository"
non_target_surfaces = ["scientific treatment", "portfolio state"]
```

## Outcome

The boundary CLI returns unregistered-constraint findings to the CM consumer.

## Allowed actions

Inspect and improve the named lint module only.

## Prohibited actions

Do not change scientific policies or worker selection.
