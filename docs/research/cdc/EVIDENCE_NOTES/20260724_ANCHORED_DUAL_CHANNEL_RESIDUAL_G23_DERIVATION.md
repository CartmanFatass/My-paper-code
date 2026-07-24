# Anchored dual-channel residual G23 derivation

Date: 2026-07-24

## Accepted evidence

G22 keeps G17 compatible but drives G18 utility from `0.66667` to `0.01025`
under an exercised Adam residual. This turns the G21 ambiguity into a credit
diagnosis: the residual can optimize, but the successor-only actor objective
does not retain the immediate-service signal needed to stay on a useful action
manifold.

The earlier actor/critic-isolated G18 candidate learned the delayed source with
two independently normalized PPO channels averaged at equal weight. Its formal
failure came from sharing those actor gradients with the G17 fast policy. The
frozen-anchor residual separates these mechanisms: dual-channel credit can be
restored without allowing any fast-parameter mutation.

## Counterexamples

### CE-SUCCESSOR-ONLY-CAN-DESTROY-THE-BOOTSTRAP-MANIFOLD

Successor targets are estimated under trajectories produced by the current
policy. A large residual update can leave the action region where those targets
are informative and collapse current service before delayed benefit appears.
G22 is a direct example.

### CE-UNNORMALIZED-CHANNEL-SUM-LETS-SCALE-SELECT-THE-ALGORITHM

Immediate and successor residuals have different scales. Summing raw values
would let source-dependent variance choose their effective weights. Each
channel must retain its own normalization before a frozen equal-weight average.

### CE-DUAL-CHANNEL-RESIDUAL-IS-NOT-FAST-ACTOR-TRAINING

The immediate channel may update the residual but cannot change the trained
fast actor or exploration scale. Behavioral compatibility remains empirical
because the residual still changes executed actions.

## Smallest new algorithm

`ANCHORED_DUAL_CHANNEL_RESIDUAL_G23` is G22 except for the residual actor loss:

```text
L_residual = 0.5 * (L_PPO(normalize(A_immediate))
                    + L_PPO(normalize(A_successor)))
```

Both advantages and their baselines are the already-registered anchored credit
channels. Adam remains residual-only with the G22 defaults. No entropy term is
added to the delayed residual step, so channel composition is the sole delta.
Critic losses, frozen fast actor, sources, budgets, observations, recurrent
state and first-match gates remain unchanged.

## Necessary invariants

1. Each actor channel is normalized independently and enters with exact weight
   `0.5`.
2. Only residual parameters receive the combined actor gradient.
3. Fast actor and exploration scale remain bitwise fixed.
4. State-only critic losses reach neither actor.
5. Zero-output/common-mode, replay, inactive-row, lifecycle and source proofs
   remain closed.
6. Adam state is fresh and residual-local.
7. G17 compatibility remains the first result gate.

## Cheapest separating action

Replace the active successor-only optimizer function with the dual-channel
residual loss, mechanically rename the active runner/test, and use fresh seeds:

```text
g17_model=3219000
g17_train_ledger=3229000
g17_action=3239000
g17_evaluation_ledger=3249000
g17_evaluation_action=3259000
g18_model=3319000
g18_action=3339000
```

Keep the same budgets and thresholds. Only a promising paired screen licenses
formal definition; any valid failure closes this exact credit composition.

```text
next_boundary=ANCHORED_DUAL_CHANNEL_RESIDUAL_G23_PROTOTYPE
formal_compute=not_scheduled
conclusion_bearing_iteration_cost=0
iterations_remaining=8
```
