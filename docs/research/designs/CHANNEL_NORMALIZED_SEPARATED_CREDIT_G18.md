# Channel-normalized separated credit G18

```text
status=ALGEBRA_ACCEPTED_NONFORMAL_SCREEN_FROZEN
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Single algorithmic delta

The candidate retains the accepted fast/slow residual definitions, detached
targets, three critics, active masks, sources and PPO clipping from
`FAST_SLOW_SEPARATED_CREDIT_G18.md`. It changes only actor-loss composition:

```text
a_fast = normalize(r_t - b_fast(s_t))
a_slow = normalize(gamma * V_slow(s_(t+1)) - b_successor(s_t))
L_actor = 0.5 * PPO(a_fast) + 0.5 * PPO(a_slow)
```

Each channel is normalized before composition, so a change in the scale of one
cannot erase the other. Equal weight is fixed, not tuned. No battery, roster
role, demand phase, slot identity, UAV field or future reference enters the
credit rule.

Eleven focused tests close scale invariance, terminal/bootstrap algebra,
detached targets, finite gradients, exact replay, inactive action zero,
lifecycle schedules, slot permutations, result precedence and checkpoint
round-trip.

## Bounded screen

The screen reuses the exact paired protocol, seeds, budgets, source controls,
thresholds and first-match ordering of the retired raw-sum screen. This is a
new algorithm comparison, not a seed/budget/threshold retry. Branch names are:

1. `INVALID_CHANNEL_NORMALIZED_SEPARATED_CREDIT_G18`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_CHANNEL_NORMALIZED_G18`;
3. `NONFORMAL_NO_DELAYED_ACCESS_CHANNEL_NORMALIZED_G18`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_CHANNEL_NORMALIZED_G18`; or
5. `NONFORMAL_CHANNEL_NORMALIZED_SEPARATED_CREDIT_PROMISING_G18`.

Only branch 5 licenses a formal executable definition. Any other valid branch
retires this exact candidate. The run is nonformal and consumes no scientific
iteration.

Implementation: `ha_ctse_process/separated_credit_g18.py`.
Runner: `scripts/screen_fast_slow_separated_credit_g18.py`.

## Screen disposition

The exact screen at source commit `f704d4d9a7410b367271b9afeee864cad8f639fe`
completed operationally with zero replay error and selected
`NONFORMAL_NO_G17_COMPATIBILITY_CHANNEL_NORMALIZED_G18`. It improved both source
scores but did not cross the frozen gates, so this shared-critic candidate is
retired without tuning.
