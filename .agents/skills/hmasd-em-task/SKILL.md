---
name: hmasd-em-task
description: Use when a top-level HMASD EM direction task receives a bounded scientific question, mechanism, comparator, evidence interpretation, claim, or discriminator slice.
---

# HMASD EM Task

Read `docs/project/WORKFLOW_PROTOCOL.md`, the native WORK/CONTROL history, the direction authority, and the current research state if it exists. EM makes the scientific judgment in its main session.

## Direct work

Freeze the question, inputs, comparators, criteria, Effects, assumptions, claim ceiling, and next discriminator. Directly perform mechanism design, innovation, principles analysis, synthesis, revision, evidence interpretation, and durable research writing.

Use `hmasd-general-leaf` for weakly coupled chores such as exact paper/PDF downloads, metadata normalization, file organization, fixture preparation, or mechanical extraction. Give exact sources, destination paths, allowed Effects, output shape, and stop condition. Use Research Scout instead when the task requires external primary-evidence discovery, multi-source appraisal, or broad evidence acquisition.

## Material cycle

Open a new cycle only for a new direction/mechanism/comparator/discriminator, possible material claim rise, a result overturning a core assumption, or Portfolio reevaluation.

1. Write `SCOPE_FROZEN` state.
2. Complete necessary Scout evidence.
3. Call `hmasd-external-pro-transport` once with `Mode: INNOVATOR` and archive path.
4. Synthesize and write `SYNTHESIS_READY`.
5. Call the same transport once with `Mode: CONVERGENCE`; require independent adversarial review.
6. Resolve objections and write `REVIEW_RESOLVED`.
7. Write `HANDOFF_READY` when the next responsibility is frozen.

No automatic re-review within the same cycle. Unknown external send commitment is observed, never resent. A local Research Critic is exceptional: material Pro objection, EM rejection of a core Pro recommendation, shared scientific core, or explicit user request.

## Milestone and return

Update state only when losing context would repeat costly work or change a material judgment. A leaf result, lookup, tool success, or file write is not a milestone. Material tool evidence is a concise Markdown note written by EM, not a typed sidecar pipeline.

Return `[RESULT]` to Clerk with explicit `Outcome` and `Next`. EM never directly sends to CM or Portfolio and never delegates durable scientific judgment.
