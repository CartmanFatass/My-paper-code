+++
decision_id = "ADR-0005"
title = "Normal workflow uses low-intrusion artifact-first control"
owner = "operational_root"
scope = "shared:codex-context-control-plane"
status = "accepted"
decision_date = "2026-08-22"
supersedes = []
canonical_sources = [
  "docs/project/LOW_INTRUSION_CONTROL_PLANE.md",
  "docs/project/PROJECT_REQUIREMENTS.toml",
  "docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md"
]
revisit_conditions = [
  "A measured live workflow demonstrates that artifact-first boundaries cannot provide required liveness without behavioral hooks."
]
+++

# ADR-0005 Normal workflow uses low-intrusion artifact-first control

Behavioral lifecycle Hooks are not part of normal workflow. Native
auto-compaction is unchanged. Assignments/results and owner intake contain
drift. This ADR does not forbid explicit App Server runtime control.
