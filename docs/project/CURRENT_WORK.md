# HMASD Current Work Index

```text
document_kind=current_work_index
schema_version=4
index_owner=root
state_updated=2026-08-23
session_record_ids=code_project_manager
common_record_ids=formal_toy_research|uav_validation|explorer_project_validation|independent_research_explorer_pointer
legacy_snapshot=docs/project/archive/CURRENT_WORK_LEGACY_2026-08-01.md
```

This file is a link index. Active state is partitioned so unrelated workstreams
and sessions do not share a write surface.

## Session records

- [Code Project Manager](current-work/sessions/code_project_manager.md)

## Common records

- [Formal toy research](current-work/common/formal_toy_research.md)
- [UAV validation](current-work/common/uav_validation.md)
- [Explorer project validation](current-work/common/explorer_project_validation.md)
- [Independent Research Explorer pointer](current-work/common/independent_research_explorer_pointer.md)

## Stable project pointers

- Scientific principles: `docs/project/ALGORITHM_PRINCIPLES.md`
- Object-level complexity/cost context (advisory, never an admission gate):
  `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- User P0 hidden-limit correction (governance-only; preserves object-local
  fences): `docs/research/workflow-runs/2026-08-11_five-round-research-team/P0_HIDDEN_LIMIT_CONTROL_PLANE_CORRECTION_20260821.md`
- Scientific direction ledger: `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`
- Human-readable 33-direction Portfolio queues, owners and next events:
  `docs/HR/RESEARCH_DIRECTION_DASHBOARD.md`
- Mechanically checked direction/object/evidence/code drill-down:
  `docs/HR/RESEARCH_DIRECTION_REGISTRY.toml`
- Direction projection validator:
  `tools/validate_research_direction_registry.py`
- Runtime facts when assigned: `docs/project/AGENT_CONTEXT.md`
- Stable code map (Code Project Manager-owned): `docs/project/PROJECT_MAP.md`
- Repository context precedence: `docs/project/CONTEXT_PRECEDENCE.md`
- Context source registry: `docs/project/CONTEXT_SOURCE_REGISTRY.toml`
- Stable decisions index: `docs/project/DECISIONS_INDEX.md`
- Promotion policy: `docs/project/CONTEXT_PROMOTION_POLICY.md`
- Retention policy: `docs/project/CONTEXT_RETENTION_POLICY.md`
- Low-intrusion control-plane contract: `docs/project/LOW_INTRUSION_CONTROL_PLANE.md`
- Active requirement registry: `docs/project/PROJECT_REQUIREMENTS.toml`
- Assignment/intake protocol: `docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md`
- Experiment execution policy: `docs/project/EXPERIMENT_EXECUTION_POLICY.md`
- Current resource/manifest boundary tools: `tools/hmasd_control_plane/`
