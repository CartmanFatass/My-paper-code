---
name: hmasd-portfolio-task
description: Use when the top-level HMASD Portfolio task receives a bounded priority, investment, lifecycle, capacity, fusion, separation, or new-direction decision.
---

# HMASD Portfolio Task

Read `docs/project/WORKFLOW_PROTOCOL.md` and `docs/research/portfolio/PORTFOLIO.md` completely before deciding. Portfolio owns current cross-direction judgment; it does not implement, run experiments, or contact EM/CM directly.

## Decision turn

1. Read the bounded `[WORK]`, current portfolio table, and cited direction authorities.
2. Compare only evidence that can change investment, lifecycle, priority, capacity, fusion, or separation.
3. Make the decision in the main session. Use `hmasd-general-leaf` for weakly coupled inventories, table preparation, reference collection, or formatting—not for the judgment itself.
4. Atomically update the one current table in `PORTFOLIO.md`. Only `REGISTERED | ACTIVE | PARKED | CLOSED` are valid lifecycle values.
5. Return `[RESULT]` to Clerk with explicit `Outcome`, `Next`, summary, refs, blocker, and reentry facts.

## Rules

- `PORTFOLIO.md` is the only current lifecycle/priority/capacity authority; do not create JSON registries, revisions, DAGs, CAS, receipts, or transition files.
- ACTIVE cannot return `Next: NONE`. PARKED normally has no heartbeat. CLOSED may use NONE.
- A material Portfolio reevaluation may request EM to open a new research cycle; Portfolio does not perform External Pro calls itself.
- Major investment/closure rationale may be a historical Markdown decision note, clearly labeled as non-current state.
