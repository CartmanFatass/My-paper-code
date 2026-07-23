# Slot-layout invariance G11 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hashes are
> disabled.

```text
active_implementation=SLOT_LAYOUT_INVARIANCE_G11
implementation_status=PRELAUNCH_ACCEPTED_FORMAL_READY
design=docs/research/designs/SLOT_LAYOUT_INVARIANCE_G11.md
backend=cpu
torch_threads=1
formal_iteration=12
chain_iterations_remaining_before_run=6
```

## Goal

Separate true active-set behavior from dependence on dense lifecycle keys or a
nearby fixed padding capacity, using paired isomorphic episodes at N<=40.

## Task 1 - Build exact layout isomorphisms

Map the G10 oscillating logical ledger into dense, reversed, sparse-96 and
affine-scattered-128 layouts. Remap every membership key and every priority
column; provide the same transform for stochastic uniform tables.

Focused proof: mappings are injective and in range; wave arrivals, logical
priority columns, roster schedules, demand, constructive utility and lifecycle
state are exact in all layouts.

## Task 2 - Pair frozen-checkpoint evaluations

Import the exact three G8 finals with zero optimizer steps. For each replicate,
evaluate all four layouts under deterministic and matched-stochastic modes.
Record strict episode/profile inventories and immutable model state.

The shared frozen-checkpoint validator now distinguishes the source G8
128-episode provenance from a successor's own evaluation count. This is a
validator field separation only; G8 source evidence is unchanged.

## Task 3 - Freeze paired outcomes

Count an episode mismatch when any persistent, short or utility value differs
from its dense pair. Require zero mismatches per transformed layout and retain
the absolute access/stability floors from the design. Threshold equality passes
and the immediately lower value fails.

## Acceptance and formal launch

The G11 focused suite passes `6/6`; G11 plus shared G5 regression passes
`11/11`. The official bounded nonformal full path at
`logs/nonformal_slot_layout_g11_20260723_pm2` is operationally valid. It records
zero optimizer steps, eight immutable cells, exact source controls and zero
paired mismatch for every transformed layout.

No additional advisory review is triggered. Integrate this package and assign
the exact formal commands in the prelaunch note. A valid result consumes
iteration 12 and leaves five authorized iterations.
