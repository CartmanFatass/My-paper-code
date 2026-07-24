# Randomized roster-process G13 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hashes are
> disabled.

```text
active_implementation=RANDOMIZED_ROSTER_PROCESS_G13
implementation_status=FORMAL_CLOSED_ROBUST_RANDOM_PROCESS
design=docs/research/designs/RANDOMIZED_ROSTER_PROCESS_G13.md
backend=cpu
torch_threads=1
formal_iteration=14
chain_iterations_remaining_after_run=3
```

## Goal

Separate genuine roster-process robustness from success on a few fixed count
schedules by drawing a fresh, fully recorded valid membership process for every
evaluation episode.

## Task 1 - Generate identifiable random processes

Sample initial count/keys, safe event times, affected keys and positive batch
magnitudes from an episode-owned seed. Use 12 operations containing three
leave/rejoin and terminal/join motifs. Keep declared count bounds and prohibit
lifecycle reuse.

Focused proof: reproducibility, profile uniqueness, schedule diversity, all
operation types, transition validity and exact count bounds.

## Task 2 - Close every source instance

Generalize the active frozen-checkpoint evaluator from one source-control row
per domain to one row per domain/episode. Record exact event signatures,
schedules, wave demand and constructive outcomes. Recompute every row during
analysis and retain one shared lifecycle-state proof per domain.

Focused proof: tampered event signatures fail closed; nonformal records cannot
be promoted to formal; all generated source rows attain utility one.

## Task 3 - Evaluate the frozen algorithm

Import the exact three G8 finals with zero optimizer steps. Evaluate all three
random-process domains under deterministic and stochastic action modes for 48
episodes per cell. Preserve exact model state, CPU runtime, G8 provenance and
the predeclared first-match access/stability gates.

## Acceptance and launch

The focused suite passes 6/6 and the G13 plus shared G5 suite passes 11/11. The
official bounded nonformal pipeline at
`logs/nonformal_random_roster_g13_20260723_pm1` is operationally valid with 12
unique source rows, six cells, zero optimizer steps, exact checkpoint copy,
immutable model state and every source/lifecycle control true.

The first failing probe localized an invalid mid-wave removal support and was
repaired at the source generator; it neither changed policy nor weakened a
gate. The exact formal result is `ROBUST_RANDOMIZED_ROSTER_PROCESS_G13`: every
deterministic LCB exceeds 0.9249, random-ultra minimum replicate mean is 0.9284
and stochastic mean is 0.8893. Iteration 14 is closed with three iterations
remaining. The next boundary is `ATOMIC_COHORT_REPLACEMENT_G14`.
