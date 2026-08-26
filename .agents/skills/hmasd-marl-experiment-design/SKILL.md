---
name: hmasd-marl-experiment-design
description: Use when an HMASD MARL direction must choose or bound an experiment before requesting a result-bearing train, evaluate, or analyze run.
---

# HMASD MARL Experiment Design

Use this method inside one exact Root or EM scientific slice. It is not a task,
gate, packet, authority, or execution workflow. Cross-session work uses the
public Work Packet and `run-chain` seams; an exact result command uses the
existing `hmasd_run.py` capability. This skill does not restate that workflow.

## Plan contract

Return seven short items:

1. **Bound question** — cite the frozen question/authority. Mark any metric,
   baseline, threshold, seed count, or claim choice that is not yet bound; do
   not silently choose it.
2. **Evidence class** — name one primary class for each proposed command:
   correctness, performance, or scientific evidence. One class cannot stand in
   for another.
3. **Discriminator** — state the observation and the different next action for
   each possible outcome. If an observation cannot change the next action, omit
   that probe.
4. **Independent unit** — identify the randomized/replicated unit and the
   pairing or blocking structure. Episodes, timesteps, vector lanes, agents,
   and checkpoints are not independent repetitions unless the design actually
   randomizes at that level.
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
| Missing implementation | One bounded engineering request through an exact Work Packet |
| Scientific comparison | A frozen design; CM assigns each exact result command to one Operator through `hmasd_run.py` |

Do not turn a probe into an all-algorithm/all-topology qualification matrix.
Expand coverage only when the preceding observation changes the named decision.

## Common mistakes

- Inventing `1e-5`, five percentage points, or another plausible threshold.
- Treating a passed toy environment as throughput evidence.
- Counting evaluation episodes or vector lanes as training replicates.
- Verifying every code path before the actual discriminator is known.
- Emitting placeholder or imagined CLI flags as an exact command.

Example: “vector width 8 because 12× is expected” is unbound; measure the
existing runner before choosing.
