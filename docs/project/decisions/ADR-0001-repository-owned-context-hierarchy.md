+++
decision_id = "ADR-0001"
title = "Repository-owned context hierarchy"
owner = "operational_root"
scope = "shared:codex-context-control-plane"
status = "accepted"
decision_date = "2026-08-17"
supersedes = []
canonical_sources = ["docs/project/CONTEXT_PRECEDENCE.md"]
revisit_conditions = ["A new official Codex context authority model replaces repository ownership."]
+++

# ADR-0001 Repository-owned context hierarchy

Use repository-managed explicit context layers instead of automatic Memory as
project authority.

## Layers

```text
AGENTS/Roles
Skills
PROJECT_MAP
CURRENT_WORK
owner artifacts
ADRs
Plan Epoch
semantic commit/checkpoint
typed packets
Git
```

## Consequences

- Positive: authority remains owner-authored and inspectable.
- Costs: actors must attach navigation/procedure refs explicitly.
- Non-goals: this ADR does not decide science, technical acceptance, or
  portfolio allocation.

## Revisit

Supersedes nothing. Revisit if a later official Codex context authority model
replaces repository ownership.
