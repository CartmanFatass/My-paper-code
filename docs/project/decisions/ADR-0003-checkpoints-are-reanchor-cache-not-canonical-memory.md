+++
decision_id = "ADR-0003"
title = "Checkpoints are reanchor cache, not canonical memory"
owner = "operational_root"
scope = "shared:codex-context-control-plane"
status = "accepted"
decision_date = "2026-08-17"
supersedes = []
canonical_sources = ["docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/ACTOR_CONTEXT_AND_COMPACTION_CONTRACT.md"]
revisit_conditions = ["Owner-authored artifacts are replaced by a different canonical store."]
+++

# ADR-0003 Checkpoints are reanchor cache, not canonical memory

Semantic commits and checkpoints are owner-local reanchor cache.
They are not canonical scientific, technical, or portfolio memory.

## Consequences

- Positive: compact/resume can restore IDs without inventing conclusions.
- Costs: owners must still write canonical artifacts for durable truth.
- Non-goals: checkpoints do not accept results or allocate portfolio.

## Revisit

Supersedes nothing. Revisit if owner-authored artifacts are replaced by a
different canonical store.
