---
name: hmasd-marl-experiment-design
description: Use when an HMASD MARL direction must choose or bound an experiment before requesting a result-bearing train, evaluate, or analyze run.
---

# HMASD MARL Experiment Design

Produce a direction-local design note inside one scientific assignment. Use
only supplied evidence and allowed direction paths; workflow documents are not
scientific evidence, and missing facts stay unbound. Do not execute, route,
create tasks, define envelope fields, or choose sessions.

## Design note contract

Write seven short sections:

1. **Bound question** — cite the supplied direction-level scientific authority. Mark any metric,
   baseline, threshold, seed count, or claim choice that is not yet bound; do
   not silently choose it.
2. **Evidence class** — name one primary class for each proposed command:
   correctness, performance, or scientific evidence. One class cannot stand in
   for another.
3. **Discriminator** — state the observation and the different next action for
   each possible outcome. If an observation cannot change the next action, omit
   that probe.
4. **Independent unit and estimand** — identify the repeated unit, pairing or
   blocking, metric, aggregation, population, common-random-number scope, and
   incomplete-unit handling. Usually the unit is a seed/configuration; episodes,
   timesteps, vector lanes, agents, and checkpoints are nested observations.
5. **Numerical semantics** — preserve the project dtype and algorithm semantics
   unless frozen authority or observed instability supports a change. Every
   tolerance needs a cited existing contract, measurement-derived rationale, or
   explicit unbound status. More bits are not evidence of greater rigor.
6. **Execution projection** — use observed timing, memory, and the actual
   CLI/manifest surface. Name the batched axis and invariants it must preserve.
   Every wall-time allocation needs an observed estimate or derivation. Never
   invent a flag, speedup, or runner mode; inspect the existing command before
   freezing argv.
7. **Stop, scale, and claim ceiling** — connect each stop/scale condition to the
   discriminator and the predeclared analysis population. Require balance only
   when the frozen design requires it; predeclare failed/incomplete-unit handling.

## Smallest useful evidence

| Unknown | Smallest useful next evidence |
| --- | --- |
| Implementation correctness | One focused reproducer for the disputed semantic path |
| Vectorization benefit | Measured serial and small-vector throughput on a justified representative workload |
| Precision sensitivity | Probe after a named mismatch, observed instability, or bound requirement; preference alone triggers no probe |
| Missing implementation | A bounded description of the missing source, test, CLI, or instrumentation surface |
| Scientific comparison | A frozen design with exact inputs and an analysis population; execution is outside this skill |

Do not turn a probe into an all-algorithm/all-topology qualification matrix.
Expand coverage only when the preceding observation changes the named decision.

## Common mistakes

- Inventing a threshold, tolerance, flag, speedup, or runner mode.
- Treating a toy pass as throughput evidence or nested observations as seeds.
- Verifying every path before naming the discriminator.
