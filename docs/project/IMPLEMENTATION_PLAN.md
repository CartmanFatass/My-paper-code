# Atomic cohort-replacement G14 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hashes are
> disabled.

```text
active_implementation=ATOMIC_COUNT_SHOCK_G15_DERIVATION
implementation_status=G14_FORMAL_CLOSED_G15_NOT_YET_FROZEN
design=docs/research/designs/ATOMIC_COHORT_REPLACEMENT_G14.md
backend=cpu
torch_threads=1
formal_iteration=16
chain_iterations_remaining_before_run=2
```

## Goal

Test count-invisible identity turnover: terminate a large active cohort and join
an equal cold-start cohort in one transaction while holding active N constant.

## Task 1 - Generate atomic replacement ledgers

Sample one constant N and random initial physical keys per episode. At six
registered wave boundaries, sample a positive active cohort and an equal-size
never-seen cohort, then encode both terminal leave and join in the same event.

Focused proof: deterministic diversity, no key reuse, exact equal cohort sizes,
constant roster schedules and bounded capacity/count support.

## Task 2 - Validate cold-start semantics

Require terminal members to remain inactive with frozen hidden state and every
new member to begin from zero hidden state at the atomic transaction. Recompute
every event signature, schedule, wave demand and constructive outcome.

Focused proof: lifecycle trajectory, constructive utility one, tamper rejection
and complete per-episode source-control inventory.

## Task 3 - Evaluate frozen G8 finals

Import three exact G8 finals with no optimizer. Evaluate moderate, wide and
ultra atomic replacement distributions under deterministic and stochastic
actions for 32 episodes per cell. Preserve CPU-only runtime, model immutability,
absolute gates and first-match precedence.

## Acceptance and launch

The focused suite passes 6/6 and the G14 plus shared G5 suite passes 11/11. The
official bounded nonformal pipeline at
`logs/nonformal_atomic_replacement_g14_20260723_pm1` is operationally valid with
12 unique atomic source rows, six cells, zero optimizer steps, exact checkpoint
copy, immutable model state and every source/lifecycle control true.

No additional review is selected because focused evidence closes the only new
shared-core switch and no anomaly remains. Integrate and launch the exact formal
commands through the fixed operator.

## Formal closure and next boundary

Formal iteration 15 completed from source
`b709fd5fc9cb423110d5edc24067e0030e05cbab` as
`ROBUST_ATOMIC_COHORT_REPLACEMENT_G14`. All registered gates passed with exact
source and lifecycle closure, zero optimizer steps and unchanged G8 model
state. G14 is closed without rerun, tuning or relabeling.

The next bounded action is `ATOMIC_COUNT_SHOCK_G15_DERIVATION`: define atomic
transactions whose terminal and fresh-join cohort sizes differ, so identity
turnover and an abrupt low/high active-count transition occur together. No G15
source, budget or result contract is frozen by this closure paragraph.
