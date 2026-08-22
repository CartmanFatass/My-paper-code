# Project Requirements

Generated from `PROJECT_REQUIREMENTS.toml`. Do not edit manually.

## ACTIVE USER REQUIREMENTS

### `UR-EXEC-001`

Use a semantics-preserving C++ backend for experiment-critical result-bearing execution.

- Authority: `P0_USER`; owner: `OPERATIONAL_ROOT`
- Scope: `experiment.result_bearing, code.performance_critical`
- Source: `user:2026-08-22`; enforced at: `assignment, technical_acceptance, experiment_manifest`
- Does not imply: `rewrite_every_tool_in_cpp, change_frozen_science`

### `UR-EXEC-002`

Use parallel execution for result-bearing experiment execution; select the worker/environment count from a current CPU/memory resource preflight for the exact host and route. No fixed width is implied.

- Authority: `P0_USER`; owner: `OPERATIONAL_ROOT`
- Scope: `experiment.result_bearing`
- Source: `user:2026-08-22`; enforced at: `assignment, experiment_manifest, operator_dispatch`
- Does not imply: `fixed_worker_count, worker_count_cap, portfolio_direction_cap, neighbor_count_ceiling`

### `UR-PERF-001`

A runtime claim that affects routing must be measured or transparently extrapolated from measured evidence.

- Authority: `P0_USER`; owner: `CODE_PROJECT_MANAGER`
- Scope: `performance_estimate, experiment_runtime`
- Source: `user:2026-08-22`; enforced at: `result, technical_acceptance, resource_escalation`
- Does not imply: `hard_wall_clock_stop`

### `UR-RECOVERY-001`

Route scope-local problems to the smallest recovery owner before requesting user authority.

- Authority: `P0_USER`; owner: `OPERATIONAL_ROOT`
- Scope: `subagent_incident, workflow_recovery`
- Source: `user:2026-08-22`; enforced at: `impact_envelope, root_intake`
- Does not imply: `hide_real_user_decisions`

### `UR-RESOURCE-001`

Before experiment launch, inspect current CPU and memory resources and record the CM-selected concurrency for the exact host, backend and route.

- Authority: `P0_USER`; owner: `CODE_PROJECT_MANAGER`
- Scope: `experiment.prelaunch, experiment.resource_selection`
- Source: `user:2026-08-22`; enforced at: `resource_preflight, experiment_manifest, operator_dispatch`
- Does not imply: `fixed_worker_default, fixed_worker_cap, scientific_stop`

## ACTIVE PROJECT INVARIANTS

_(none)_

## ACTIVE DEFAULTS

_(none)_

## ACTIVE NONREQUIREMENTS

### `NR-COMPACTION-HOOKS-001`

Native auto-compaction remains untouched; no custom compaction Hook, automatic checkpoint, or automatic reanchor is required.

- Authority: `P0_USER`; owner: `OPERATIONAL_ROOT`
- Scope: `compaction`
- Source: `user:2026-08-22`; enforced at: `config, control_plane_review`
- Does not imply: `delete_explicit_recovery_tools`

### `NR-DIRECTION-CAP-001`

No fixed direction-count cap is authorized.

- Authority: `P0_USER`; owner: `PORTFOLIO`
- Scope: `portfolio`
- Source: `user:2026-08-22`; enforced at: `portfolio_plan, constraint_lint`
- Does not imply: `unlimited_compute, no_priority_judgment`

### `NR-HASH-HANDOFF-001`

Internal repository file handoffs do not require SHA-256 and hashes never establish semantic validity or owner authority.

- Authority: `P0_USER`; owner: `OPERATIONAL_ROOT`
- Scope: `internal_handoff, repository_artifact`
- Source: `user:2026-08-22`; enforced at: `assignment, handoff, constraint_lint`
- Does not imply: `transport_integrity_checks_for_untrusted_bytes`

### `NR-HIGH_FREQUENCY_HOOKS-001`

Do not use high-frequency lifecycle Hooks as semantic-drift prompts or workflow-wide audit triggers.

- Authority: `P0_USER`; owner: `OPERATIONAL_ROOT`
- Scope: `control_plane`
- Source: `user:2026-08-22`; enforced at: `config, control_plane_review`
- Does not imply: `remove_explicit_supervisor`

### `NR-WORKER-LIMIT-001`

No project-wide default or hard upper limit for worker/environment count is authorized; every launch width is selected from the current resource preflight.

- Authority: `P0_USER`; owner: `OPERATIONAL_ROOT`
- Scope: `experiment.worker_count, experiment.parallelism`
- Source: `user:2026-08-22`; enforced at: `assignment, resource_preflight, experiment_manifest, constraint_lint`
- Does not imply: `serial_execution, unbounded_resource_use, ignore_host_capacity`

## SUPERSEDED

_(none)_
