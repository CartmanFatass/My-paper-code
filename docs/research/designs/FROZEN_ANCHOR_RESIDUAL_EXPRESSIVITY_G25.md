# Frozen-anchor local residual expressivity G25

```text
status=NONFORMAL_CLOSED_NO_POINTWISE_FIT
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Purpose

This is a diagnostic gate, not a candidate algorithm. It asks whether G23's
frozen-anchor local residual can fit and realize the existing constructive G18
controller when PPO credit is removed. Oracle labels remain in the runner and
never enter policy code or a successor algorithm.

## Executable contract

- train the unchanged G18 fast anchor for `100` updates, `8` environments and
  `2` PPO passes;
- freeze the complete anchor and enable only the initially zero local residual;
- build exactly `36` constructive-manifold state rows from the three registered
  slot permutations and twelve source steps;
- optimize active-row action-space MSE for `200` Adam steps at `1e-3`, batch
  size `36`, gradient clip `1.0`;
- report initial/final MSE, ratio, exact anchor difference, parameter ownership,
  inactive-row checks, source coverage, residual movement, and deterministic
  closed-loop G18 metrics;
- apply the four first-match branches frozen in the derivation.

The probe may reuse the current source, fast-anchor optimizer, evaluation and
runtime helpers. It may not call the delayed PPO optimizer, alter reward,
observation, lifecycle, RNG ownership, source dynamics, budgets or thresholds,
or claim held-out generalization from the three slot permutations.

## Proof-sized acceptance

1. The constructive dataset has exact row, phase, slot-order and inactive
   semantics.
2. The optimizer owns exactly the local residual parameters.
3. One update moves the residual while leaving the anchor bitwise unchanged.
4. Result precedence rejects invalid, failed pointwise and failed closed-loop
   payloads in order.
5. A formal analyzer or formal claim cannot consume the diagnostic artifact.

Only one integrated bounded CPU run is permitted after focused acceptance.

## Implementation acceptance

The active runner is
`scripts/probe_frozen_anchor_residual_expressivity_g25.py`. Constructive labels
remain in that diagnostic boundary; the policy is the existing source-neutral
`FastAnchoredResidualPolicy`. The runner closes the exact 36-row dataset,
trains the unchanged fast anchor, enables only the local residual, records
pointwise and closed-loop evidence separately, and has no formal mode.

Four focused tests and 25 focused-plus-retained G17/G18/G19 tests pass on the
registered CPU one-thread runtime. They prove dataset coverage and inactive
semantics, exact residual optimizer ownership, a moving residual with bitwise
frozen non-residual state, and fail-closed result precedence. Closed G24 code
and its now-unused generic contextual hook are removed from the active line.
This accepts only the single bounded diagnostic run.

## Bounded probe disposition

The integrated probe is operationally valid and closes all dataset, source,
runtime, optimizer-ownership, inactive-row, replay and anchor invariants. Active
action MSE falls from `1.43119` to `0.37358`, a ratio of `0.26103`, so it misses
both frozen pointwise gates. Deterministic closed-loop utility also changes from
the fast anchor's `0.66679` to `0.64357`; spike utility reaches `0.82401` but
does not compensate for the first-match pointwise failure. The exact branch is
`NO_POINTWISE_LOCAL_RESIDUAL_FIT_G25`.

The G23 local residual representation is closed under this accepted probe. No
extra fit steps, optimizer change, threshold relaxation or UAV promotion is
permitted. The next paired diagnostic adds direct actor-set context while
retaining the autoregressive prefix; it does not rerun or rescue G25.
