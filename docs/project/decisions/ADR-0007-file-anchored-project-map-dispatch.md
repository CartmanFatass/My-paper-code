+++
decision_id = "ADR-0007"
title = "Nontrivial code dispatch is file-anchored and PROJECT_MAP-grounded"
owner = "operational_root"
scope = "shared:codex-assignment-control"
status = "accepted"
decision_date = "2026-08-22"
supersedes = []
canonical_sources = [
  "docs/project/PROJECT_MAP.md",
  "docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md"
]
revisit_conditions = [
  "A later sole repository architecture map replaces PROJECT_MAP.md by explicit owner decision."
]
+++

# ADR-0007 Nontrivial code dispatch is file-anchored and PROJECT_MAP-grounded

Abstract labels do not establish scope. Implementation/review assignments name
exact files or bounded discovery roots, PROJECT_MAP anchor, state owner, and
direct consumer.
