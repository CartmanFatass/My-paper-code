# Adaptive anchored delayed residual G22 derivation

Date: 2026-07-24

## Accepted evidence

G19 rejects batch-global conflict projection, G20 rejects active-set-zero-mean
geometry, and G21 rejects their absence under unpreconditioned SGD. Across all
three, the frozen fast actor is exact and G17 remains compatible. In G21 the
G18 residual output moves to `0.01315`, yet gain is only `0.004` and spike
service remains zero.

The earlier learnable actor/critic-isolated G18 candidate used Adam at learning
rate `1e-3`. Its formal failure was G17 interference through shared actor
parameters, not lack of G18 access. Freezing the fast actor removes that
parameter-overwrite mechanism. This makes residual preconditioning the
smallest remaining reusable discriminator before changing credit semantics.

## Counterexamples

### CE-NONZERO-SGD-STEP-IS-NOT-EFFECTIVE-RESIDUAL-OPTIMIZATION

A nonzero output layer proves gradient flow but not useful conditioning. The
zero-initialized residual's hidden layers and output layer have sharply
different early gradient scales; plain SGD can leave the policy near its
anchor throughout the fixed budget.

### CE-ADAM-ON-RESIDUAL-IS-NOT-SHARED-ACTOR-OVERWRITE

G18's shared Adam actor can damage G17, but Adam restricted to residual
parameters cannot mutate the frozen fast actor or exploration scale. G17
behavior may still change through the residual, so the unchanged behavioral
gates remain necessary and first.

### CE-OPTIMIZER-SUCCESS-IS-NOT-CREDIT-PROOF

If Adam succeeds, the result supports an adaptive residual realization, not a
claim that successor credit is uniquely correct. If it fails, the next question
is credit/trajectory representation rather than more optimizer tuning.

## Smallest new algorithm

`ADAPTIVE_ANCHORED_DELAYED_RESIDUAL_G22` is exactly G21 except that delayed
residual parameters use Adam with the registered defaults:

```text
learning_rate=0.001
betas=[0.9,0.999]
eps=1e-8
weight_decay=0
amsgrad=false
```

Fast-anchor and critic optimizers remain Adam as before. No reward,
observation, source, recurrent state, routing, probability factorization,
credit target, budget, threshold or lifecycle change is allowed.

## Necessary invariants

1. The G21 zero-output and common-mode policy proofs remain exact.
2. Only residual parameters are registered in the delayed actor optimizer.
3. Fast actor and exploration scale remain bitwise fixed.
4. State-only critic losses reach neither actor.
5. Replay, inactive rows, lifecycle and source controls retain their bounds.
6. G17 compatibility remains the first scientific gate.
7. Optimizer state is fresh, source-local and never shared across phases.

## Cheapest separating action

Mechanically rename the active G21 runner/test to G22, replace only the delayed
residual optimizer constructor and freeze fresh seeds:

```text
g17_model=3019000
g17_train_ledger=3029000
g17_action=3039000
g17_evaluation_ledger=3049000
g17_evaluation_action=3059000
g18_model=3119000
g18_action=3139000
```

Use the same paired screen and first-match thresholds. Only a promising branch
licenses formal definition; any valid failure closes this exact Adam residual
without optimizer sweep or same-package retry.

```text
next_boundary=ADAPTIVE_ANCHORED_DELAYED_RESIDUAL_G22_PROTOTYPE
formal_compute=not_scheduled
conclusion_bearing_iteration_cost=0
iterations_remaining=8
```
