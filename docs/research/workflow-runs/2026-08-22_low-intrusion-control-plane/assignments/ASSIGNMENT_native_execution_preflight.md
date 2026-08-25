# Assignment: Native execution preflight

```toml hmasd-assignment
schema_version = 2
assignment_id = "asg_native_execution_preflight"
assignment_mode = "OPERATION"
semantic_owner = "CM:continuous-roster"
executor_role = "hmasd-experiment-operator"
return_to = "CM:continuous-roster"
strictness_profile = "R2_EXPERIMENT_EXECUTION"
evidence_class = "B"
result_bearing = true
runtime_profile = "TOY_EXPLORATORY"
requirement_ids = ["UR-EXEC-001", "UR-EXEC-002", "UR-RESOURCE-001", "UR-PERF-001"]
nonrequirement_ids = ["NR-WORKER-LIMIT-001", "NR-DIRECTION-CAP-001", "NR-HASH-HANDOFF-001"]
recovery_owner = "CM:continuous-roster"
result_path = "docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/results/RESULT_asg_native_execution_preflight.md"
project_map_anchor = "Native boundary"
architecture_role = "NATIVE_BOUNDARY"
affected_files = ["envs/continuous_roster/cpp_backend.py", "tools/benchmarks/benchmark_continuous_roster_toy_cpp_backend.py"]
create_files = []
affected_symbols = ["ContinuousRosterCppBackend"]
search_roots = []
direct_consumers = ["tests/ha_ctse_process_continuous_roster_toy_cpp_backend_test.py"]
upstream_inputs = ["docs/project/EXECUTION_BACKEND_REGISTRY.toml"]
state_owner = "ContinuousRosterCppBackend"
non_target_surfaces = ["scientific treatment", "portfolio direction count"]
```

## Outcome

The native benchmark consumer receives a CM-selected parallel C++ execution manifest.

## Allowed actions

Run the current resource preflight and validate the exact manifest.

## Prohibited actions

Do not launch formal training or change scientific treatments.
