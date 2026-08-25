# Immediate-tangent protected full actor G27

```text
status=OPERATIONAL_REPAIR_ACCEPTED_RERUN_NEXT
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen delta

G27 reuses the G19 two-phase wrapper but freezes every delayed residual at exact
zero. After the fast phase it updates the full environment-neutral actor with
the equal average of the immediate gradient and the successor gradient after
one-way projection against immediate conflict. Slow value and both channel
baselines remain state-only and use a separate critic optimizer.

Full actor ownership includes member/context encoders, GRU, action mean,
current-observation residual and `log_std`. It excludes the unused core critic,
slow critic, credit baselines and all delayed residual parameters.

## Protected semantics

- G17/G18 sources, observations, rewards, action factorization and lifecycle;
- PPO ratio/clipping, independently normalized channel advantages, terminal
  and bootstrap semantics;
- RNG streams, replay, inactive rows, seeds, budgets, gates and branch order;
- CPU-only one-thread runtime and `formal=false` screen artifact.

No oracle labels, source identifiers, critic features or future references
enter the actor. This is not a rerun or relabeling of formal G18 because the
one-way full-actor gradient projection is a new optimization rule.

## Proof-sized acceptance

1. Actor inventory is exact and disjoint from every critic/residual parameter.
2. Non-conflicting successor gradients are unchanged; conflicting gradients
   have post-projection dot at least `-1e-7` and match the formula.
3. The applied actor gradient is exactly `0.5*(g_i+g_s')`; critic gradients do
   not reach actor tensors.
4. Residual output remains exact zero while full actor parameters move.
5. Replay/lifecycle/inactive and first-match result semantics are retained.

The CPU realization evaluates projection dot products and norms in float64.
After casting the mathematically projected rows to the actor gradient dtype, a
negative rounding remnant receives the minimum one-coordinate representable
correction needed to re-enter the closed tangent half-space. This is an
execution-only realization of the same projection; it does not relax the
`-1e-7` acceptance bound or change either channel's scientific weight.

After focused acceptance, run one integrated paired nonformal screen. Formal
compute remains unscheduled unless the promising branch is selected.
