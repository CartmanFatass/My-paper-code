# Fast-policy-anchored delayed residual G19 derivation

Date: 2026-07-24

## Accepted evidence

Formal G17 remains a closed success for immediate continuous service with
objective-aligned one-step credit. Formal G18 is a valid first-match failure:
its delayed battery-roster gates pass strongly, but the shared actor loses G17
compatibility on fresh seeds even after the slow critic is isolated from actor
representation.

The supported diagnosis is narrower than generic catastrophic forgetting. The
slow value loss no longer reaches actor parameters, yet successor-channel PPO
gradients still update the same action-producing parameters as immediate
credit. Separating critics and normalizing losses therefore does not separate
control authority.

## Counterexamples to tempting repairs

### CE-FROZEN-BASE-IS-NOT-PRESERVED-BEHAVIOR

Freezing a base actor while adding an unrestricted residual does not preserve
the base policy. The total action mean is still changed by the residual, and an
autoregressive residual action also changes later prefix inputs. Parameter
immutability alone is not a behavior guarantee.

### CE-KL-WEIGHT-IS-A-NEW-TUNING-AXIS

Adding an arbitrary KL or imitation coefficient merely trades delayed gain
against immediate damage. A small average KL can still cross a sensitive
conditional-control boundary, while a large coefficient can suppress the
needed battery allocation. Selecting that coefficient after observing G18
would be a tuned retry rather than the smallest separating test.

### CE-SOURCE-LABEL-ROUTING

Selecting an immediate or delayed head from the environment name, battery
field, demand phase or rotating-member flag would solve the registered pair by
hand. It would not be an environment-neutral MARL credit algorithm and would
not support UAV transport.

## Smallest new algorithm

The new candidate is
`FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_G19`.

For each source, training has two fixed phases:

1. train the ordinary continuous-roster actor with immediate reward residual
   only;
2. freeze every fast actor parameter and its exploration scale, attach an
   exactly zero-initialized residual mean head, and train only that residual
   with centered successor-value credit plus independent state-only critics.

The deployed mean is

```text
mu_total(o,h,p) = stopgrad(mu_fast(o,h,p)) + mu_delayed(o,h,p)
mu_delayed at phase transition = 0 exactly
```

The residual uses only the same current actor features, current observation and
normalized action prefix. It receives no source identity or environment field
outside the registered observation.

Freezing the anchor prevents parameter overwrite but not residual behavioral
interference. Therefore each residual PPO step applies a parameter-space
lexicographic projection. Let `g_fast` be the residual-parameter gradient of
the frozen immediate-reward PPO loss and `g_delayed` the gradient of the
successor-value PPO loss. The applied gradient is

```text
if dot(g_delayed, g_fast) >= 0:
    g_applied = g_delayed
else:
    g_applied = g_delayed
        - dot(g_delayed, g_fast) / ||g_fast||^2 * g_fast
```

For a minimization step, this makes the first-order change of the immediate
loss non-positive. If the immediate gradient is exactly zero, the delayed
gradient is unchanged. This rule has no learned source switch, loss weight,
threshold or post-result hyperparameter choice.

## Necessary invariants

1. The zero residual reproduces anchor action means, sampled actions,
   log-probabilities, recurrent state and autoregressive prefixes exactly under
   identical draws.
2. Fast actor parameters and exploration scale remain bitwise unchanged during
   the delayed phase.
3. Residual gradients contain only the delayed PPO actor objective; slow value
   and baseline losses update state-only critics and cannot reach either actor.
4. The projected gradient is finite and has nonnegative dot product with the
   immediate gradient up to numerical tolerance.
5. Inactive lifecycle rows retain exactly zero actions and likelihood; replay,
   RNG ownership, slot anonymity and lifecycle schedules remain unchanged.
6. The implementation imports no G17/G18/UAV source into the generic policy or
   projection algebra. Source-specific collection remains in the runner.
7. Absolute G17 gates retain first precedence. Strong delayed evidence cannot
   rescue an immediate-controller failure.

## Cheapest separating action

Implement only the residual hook, phase transition, projected-gradient helper
and paired one-seed screen in the existing toy sources. Proof-sized tests cover
the seven invariants above. The bounded screen uses the already accepted G17
absolute compatibility thresholds, followed by G18 delayed access and
mechanism thresholds. It records anchor-to-final paired deltas but does not add
an arbitrary preservation margin.

Passing licenses a fresh formal executable definition. Failure retires this
exact anchored/projected residual without changing seeds, budgets, projection,
thresholds or source. The derivation and bounded screen consume zero
conclusion-bearing iterations. UAV promotion remains forbidden until a formal
toy result passes the full first-match contract.

```text
next_boundary=FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_G19_PROTOTYPE
formal_compute=not_scheduled
conclusion_bearing_iteration_cost=0
iterations_remaining=8
```

## Prototype disposition

The source-neutral implementation and runner now close the derivation. A
single hook avoids copying the autoregressive policy loop; zero residual output
is exact under sampled, deterministic and teacher-replay execution. The fast
anchor is bitwise unchanged after delayed updates on both toy sources, while
the residual output layer moves. Projected-gradient post-dots are nonnegative
within `1e-7`, replay remains exact and all lifecycle/inactive-row checks pass.

Eight focused G19 tests and 22 retained G17/G18 shared proofs pass. The next
action is the frozen one-seed paired screen from the integrated source. No
formal or conclusion-bearing claim is licensed yet.
