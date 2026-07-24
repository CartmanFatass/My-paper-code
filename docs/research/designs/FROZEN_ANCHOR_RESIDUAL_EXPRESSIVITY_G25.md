# Frozen-anchor local residual expressivity G25

```text
status=DESIGN_FROZEN_IMPLEMENTATION_NEXT
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
