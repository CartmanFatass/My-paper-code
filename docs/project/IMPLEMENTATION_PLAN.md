# Beyond-declared-count G7 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hashes are
> disabled.

```text
active_implementation=BEYOND_DECLARED_COUNT_G7
implementation_status=FORMAL_CLOSED_NO_MODERATE_BEYOND_COUNT_G7
design=docs/research/designs/BEYOND_DECLARED_COUNT_G7.md
backend=cpu
torch_threads=1
training_operation=none_frozen_g5_checkpoint_import
active_line_policy=replace_archived_g6_runner_with_g7
formal_iteration=8
chain_iterations_remaining_after_run=9
```

## Goal

Measure the frozen G5 checkpoint beyond its declared N=16 observation range
before introducing any scale-free algorithm repair. Separate moderate, far and
joint scale failure.

## Task 1 - Replace the closed G6 active runner

Git history and the G6 source commit archive its exact implementation. Remove
the G6-specific module, runner and test from the active line and replace them
with G7 equivalents. Reuse the direct evaluator and Generic-SHORT core; do not
add compatibility imports or readers.

Focused proof: no G6 code path remains active, G5 source files are unchanged,
and the new profile validator admits exactly the registered range through 40
without modifying the inherited count feature.

## Task 2 - Preserve zero-training provenance

Carry forward the repaired exact G5 intake: source, formal authorization token,
result, runtime, counts, manifest seeds, checkpoint-embedded RNG constants and
strict final loads. Materialize three finals into a fresh root and record zero
optimizer steps.

Focused proof: exact intake succeeds; missing/wrong token and one independent
source/checkpoint field fail; model state is finite and unchanged.

## Task 3 - Evaluate the three beyond-limit domains

Produce 18 final-checkpoint cells with full 128-episode arrays in formal mode.
Source controls reconstruct actual-wave demand and lifecycle changes. Analyzer
validates exact inventory, CPU one-thread runtime, finite domains, model
immutability and first-match boundaries.

Focused proof: constructive controls and padding invariance pass through N=40;
the reduced full-path exercise is operationally valid but rejected as formal;
exact thresholds pass and `nextafter` below each threshold fails.

## Acceptance and launch

Run the new focused test plus one bounded nonformal exercise. One advisory
review is permitted only if a conclusion-bearing risk appears. After PM
acceptance and Git integration, assign one exact formal foreground pipeline to
the fixed Luna-low operator. A valid result consumes iteration 8 and leaves
nine rounds.

Acceptance is complete. The G7-specific suite passes `7/7`, the combined G7/G5
suite passes `12/12`, and the nonformal full path at
`logs/nonformal_open_roster_beyond_count_g7_20260723_g7impl_r1` is operationally
valid with zero optimizer steps, exact model immutability and finite count
features through N=40. Old G6 active files are absent and G7 replacements are
present. The package is formal-ready after Git integration.

## Formal closure and successor

The exact source `19ea4d915ee4bdd03e81c913570d66f0ad00974d`
completed all 18 formal cells with zero parameter drift and returned
`NO_MODERATE_BEYOND_COUNT_G7`. The moderate deterministic CI95 lower bound is
`0.8590299`, below the frozen `0.90` floor. G7 is closed without rescue.

The active implementation boundary is now zero-compute
`SCALE_NORMALIZED_OPEN_ROSTER_G8_DERIVATION`. No G8 formal contract or run is
frozen by this G7 plan.
