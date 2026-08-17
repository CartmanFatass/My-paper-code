+++
decision_id = "ADR-0004"
title = "Controlled forgetting excludes without deleting"
owner = "operational_root"
scope = "shared:codex-context-control-plane"
status = "accepted"
decision_date = "2026-08-17"
supersedes = []
canonical_sources = ["docs/project/CONTEXT_RETENTION_POLICY.md"]
revisit_conditions = ["A later version authorizes destructive deletion of audit-only rows."]
+++

# ADR-0004 Controlled forgetting excludes without deleting

Controlled forgetting removes stale objects from active working sets without
automatic physical deletion.

## Consequences

- Positive: capsules stay bounded while history remains queryable.
- Costs: operators must mark archive candidates instead of deleting rows.
- Non-goals: this ADR does not retire scientific directions or actors.

## Revisit

Supersedes nothing. Revisit only if a later version authorizes destructive
deletion of audit-only rows.
