# Scale-by-churn composition G10 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hashes are
> disabled.

```text
active_implementation=SCALE_CHURN_COMPOSITION_G10
implementation_status=FOCUSED_CHECKS_COMPLETE_NONFORMAL_EXERCISE_PENDING
design=docs/research/designs/SCALE_CHURN_COMPOSITION_G10.md
backend=cpu
torch_threads=1
formal_iteration=11
chain_iterations_remaining_before_run=7
```

## Goal

Test whether the separately supported G8 count-scale and G9 high-churn
properties compose in one episode. Freeze the same G8 finals, train nothing and
place eight roster edits across active counts through 40.

## Task 1 - Parameterize the accepted churn source

Retain the G9 event, lifecycle, ledger and environment machinery as the shared
active core. Parameterize each profile with its capacity and maximum active
count without changing the exact G9 profile values. Add only the three G10
large-count profiles.

Focused proof: simulate every transition, reject event collisions, lifecycle
reuse and understated count bounds, and require exact count ranges, post-event
wave demand and constructive utility one.

## Task 2 - Reuse one frozen-checkpoint evaluator

Reuse the G9 import/evaluate/analyze implementation by configuring an explicit
G10 contract: algorithm identity, domains, seeds, thresholds and terminal
branches. Do not duplicate checkpoint or artifact validation. Each process has
one activated contract; the formal G9 source remains preserved by its commit
and artifacts and is never rerun.

Focused proof: G10 identity reaches manifests and branches; imported G8 state
is exact; optimizer steps remain zero; lifecycle freeze/restore and evaluation
immutability hold at capacities 32 and 48.

## Task 3 - Freeze result semantics

Evaluate deterministic and stochastic behavior across the three registered
domains, exactly 18 formal cells. Retain the 0.90 deterministic LCB, 0.85
minimum mixed replicate and 0.80 mixed stochastic gates. Test equality and the
next lower floating-point value under the frozen first-match order.

## Current acceptance boundary

The G10 focused suite passes `6/6`; the combined G10 plus shared G5 regression
passes `11/11`. One official bounded nonformal CPU full-path exercise is the
remaining prelaunch check. A valid formal result will consume iteration 11 and
leave six authorized iterations; operationally invalid evidence consumes none.
