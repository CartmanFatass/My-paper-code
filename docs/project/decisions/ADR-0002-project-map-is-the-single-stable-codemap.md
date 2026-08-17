+++
decision_id = "ADR-0002"
title = "PROJECT_MAP is the single stable codemap"
owner = "operational_root"
scope = "shared:codex-context-control-plane"
status = "accepted"
decision_date = "2026-08-17"
supersedes = []
canonical_sources = ["docs/project/PROJECT_MAP.md"]
revisit_conditions = ["A later repository-wide architecture map replaces PROJECT_MAP.md by explicit owner decision."]
+++

# ADR-0002 PROJECT_MAP is the single stable codemap

`docs/project/PROJECT_MAP.md` is the single stable codemap.
Do not create a competing `CODEMAP.md`.

## Consequences

- Positive: navigation stays in one CM-owned map.
- Costs: control-plane additions must update PROJECT_MAP, not a second map.
- Non-goals: this ADR does not record current work or scientific meaning.

## Revisit

Supersedes nothing. Revisit only if an explicit owner decision replaces
PROJECT_MAP with a new sole map.
