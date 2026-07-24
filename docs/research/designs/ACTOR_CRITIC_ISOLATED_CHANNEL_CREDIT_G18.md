# Actor/critic-isolated channel credit G18

```text
status=ALGEBRA_ACCEPTED_NONFORMAL_SCREEN_FROZEN
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Single algorithmic delta

The candidate retains the channel-normalized fast/successor PPO losses from
`CHANNEL_NORMALIZED_SEPARATED_CREDIT_G18.md`. It replaces the actor-shared slow
value path with a state-only critic:

```text
V_slow = MLP([critic_state, active_mask])
grad(V_slow loss, actor parameters) = 0
```

The unused core critic is frozen. Immediate and successor baselines already use
their own state-only parameter block. Actor observations, recurrent state,
autoregressive factorization, action distribution, reward, sources and credit
targets are unchanged.

Twelve focused tests prove the slow value gradient reaches its critic while
remaining absent from actor representation and heads. They also retain the
previous scale-invariance, replay, lifecycle, inactive-row, terminal/bootstrap,
gradient, slot-permutation, precedence and checkpoint proofs.

## Bounded paired screen

The exact sources, seeds, 38,400/28,800 environment-step budgets, PPO settings,
source controls, thresholds and first-match order are unchanged. The registered
branches are:

1. `INVALID_ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_CRITIC_ISOLATED_G18`;
3. `NONFORMAL_NO_DELAYED_ACCESS_CRITIC_ISOLATED_G18`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_CRITIC_ISOLATED_G18`; or
5. `NONFORMAL_ACTOR_CRITIC_ISOLATED_CREDIT_PROMISING_G18`.

Only branch 5 licenses a formal executable definition. Any other valid branch
retires this exact candidate. This screen consumes zero conclusion-bearing
iterations.

Implementation: `ha_ctse_process/separated_credit_g18.py`.
Runner: `scripts/screen_fast_slow_separated_credit_g18.py`.
