---
name: hmasd-portfolio-task
description: Use when the top-level HMASD Portfolio task receives a bounded priority, investment, lifecycle, capacity, fusion, separation, or new-direction decision.
---

# HMASD Portfolio Task

Read `docs/project/WORKFLOW_PROTOCOL.md` and `docs/research/portfolio/PORTFOLIO.md` completely before deciding. Portfolio owns current cross-direction judgment; it does not implement or run experiments.

## Decision turn

1. Confirm the composer uses `Custom (config.toml)` with no live permission override; project config
   must resolve this top-level task to `danger-full-access` with `approval_policy = never`. Otherwise
   perform no write, Git, external send, launch, or read-only leaf spawn; return `WAITING` and resume
   the same WORK only after this task is switched to Custom mode.
2. Read the bounded `[WORK]`, current portfolio table, and cited direction authorities.
3. Apply the scientific quality floor first: clear question/non-goals, traceable evidence, an
   interpretable discriminator, distinguishable scientific versus execution failure, and a claim
   no stronger than the evidence.
4. Compare only evidence that can change investment, lifecycle, priority, capacity, fusion, or
   separation. Explicitly identify complementarity, substitution, shared assumptions, common
   failure risk, decision leverage, cost/time, reversibility, and option value. Do not invent a
   numeric VOI, aggregate score, Elo, or vote.
5. Make the decision in the main session. Use `hmasd-general-leaf` for weakly coupled inventories, table preparation, reference collection, or formatting—not for the judgment itself.
6. Atomically update the one current table in `PORTFOLIO.md`. Only `REGISTERED | ACTIVE | PARKED | CLOSED` are valid lifecycle values.
7. Return `[RESULT]` directly to the `Return task` with outcome, summary, refs, blocker, and reentry
   facts. For user-direct input, answer the user in the current task without inventing a return ID.
8. When the accepted decision opens a separate scientific WORK, first close the current inbound
   WORK, confirm the exact direction EM has no unfinished WORK, then send the complete new brief.
   Portfolio, not the recipient or an intermediary, owns that brief.

## Rules

- `PORTFOLIO.md` is the only current lifecycle/priority/capacity authority; do not create JSON registries, revisions, DAGs, CAS, receipts, or transition files.
- An ACTIVE direction has a current `Direction owner`; a temporary CM slice does not change that
  Portfolio projection. PARKED and CLOSED use `NONE`.
- A material Portfolio reevaluation may request EM to open a new research cycle; Portfolio does not perform External Pro calls itself.
- Major investment/closure rationale may be a historical Markdown decision note, clearly labeled as non-current state.
- A comparative Portfolio WORK may fan out to several distinct idle EM tasks. Each brief shares the
  same decision context but freezes a differentiated direction lens/discriminator. Portfolio must
  join every sent EM to terminal, or CANCEL each outstanding EM to terminal, before returning its
  own terminal RESULT. Initial independent directions do not see one another's favored result.
- Continue/narrow/PARK/CLOSE/fuse/spinoff are decision actions, not new lifecycle values. Fusion
  opens a scientific synthesis question and preserves explicit source-direction dispositions;
  spinoff registers a new direction before its EM establishes science.
