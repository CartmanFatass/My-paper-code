---
name: hmasd-portfolio-control
description: Select and reconcile active research directions from the Portfolio authority.
---

# HMASD Portfolio Control

## Purpose

Own cross-direction lifecycle, ranking, synthesis, and resource attention without
copying scientific goals into workflow JSON. Portfolio is a long-lived logical
manager revived by Root, not a permission gate or an inference loop.

## Inputs

- `docs/research/portfolio/PORTFOLIO.md` as the sole source of the persistent
  scientific goal, ranking, synthesis, and lifecycle reasons.
- `docs/research/portfolio/workflow/registry.json` as the sole lifecycle and
  dependency authority.
- Candidate `DIRECTION.md` references and their SHA-256 values.
- Existing EM logical identities, generations, completion envelopes, and Root's
  bounded assignment.

## Bounded cycle

1. Read and mechanically validate the registry, then resolve each referenced
   Portfolio and direction path and SHA before scientific ranking.
2. Rank eligible directions from `PORTFOLIO.md`; qualify active work by value and
   dependencies. Target 2–8 active directions only when they qualify; zero is a
   valid `IDLE` outcome.
3. Write one lifecycle decision (create, activate, park, merge, close, or
   reactivate) with its scientific reason in `PORTFOLIO.md`, then replace the
   registry through the state CLI using the expected revision.
4. Reuse or revive one stable `EM-<direction>` identity per selected direction;
   dispatch at most the required non-blocking turns and send only material
   transitions.
5. Perform one bounded reassessment. Return `IDLE` rather than activating a
   low-value direction to satisfy cardinality. Ordinary worker target is 28,
   preserving four advisory slots.

There is no continuous poller. A parent wake-up, Hub completion, process exit,
or explicit observed file change starts the next bounded cycle.

## State writes

- Write lifecycle reasons and portfolio synthesis only to `PORTFOLIO.md`.
- Write lifecycle/dependency records only to `registry.json` through
  `scripts/hmasd_state.py` with expected-revision CAS.
- Update no `DIRECTION.md`, research state, engineering state, Agentify ledger,
  run manifest, or Git integration state.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-portfolio"`, logical identity
`Portfolio`, and payload:

```json
{
  "kind": "portfolio",
  "direction_actions": [],
  "portfolio_ref": "docs/research/portfolio/PORTFOLIO.md",
  "registry_revision": 1
}
```

`summary`, `status`, `materiality`, changed paths, state references, checkpoint
SHA, decision requests, and next action describe only observed work. A valid
zero-qualified result is `status: "COMPLETED"`, `materiality: "PORTFOLIO"`, and
`next_action: "IDLE"`.

## Failure handling

If a registry path, SHA, schema, or expected revision is invalid, stop before a
scientific decision and return the exact conflict. Never invent a lifecycle
state, duplicate the goal in JSON, activate a weak direction for quota, or
replay an EM result whose direction checkpoint is newer. A missing specialist
or Advisor is an evidence gap and does not block ordinary lifecycle work.

## Deletion condition

Delete this Skill when a reviewed replacement owns Portfolio goal, ranking,
lifecycle, dependencies, and EM revival with one source of truth and equivalent
bounded `IDLE` behavior.
