# Fast/slow separated credit G18

```text
status=ALGEBRA_ACCEPTED_NONFORMAL_SCREEN_FROZEN
source_1=CLOSED_G17_CONTINUOUS_SERVICE_ROSTER
source_2=G18_DELAYED_BATTERY_ROSTER
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Algorithm boundary

The candidate preserves the G17 immediate actor channel and adds only one
environment-neutral successor channel:

```text
immediate_residual_t = r_t - b_fast(s_t)
successor_target_t = 0.99 * (1-terminal_t) * V_slow(s_(t+1))
successor_residual_t = successor_target_t - b_successor(s_t)
actor_advantage_t = immediate_residual_t + successor_residual_t
```

`b_fast`, `b_successor` and `V_slow` are current-state critics. Actor targets
are detached. The slow critic fits the discounted return; the two auxiliary
critics fit current reward and the detached successor target. All three critic
losses have equal weight inside the existing fixed value coefficient. There is
no learned or tuned mixture coefficient and no source-specific field in the
credit rule.

Inactive lifecycle rows retain exactly zero action and likelihood. Terminal
rows receive no bootstrap. The candidate does not read battery, charging role,
demand phase, slot identity, UAV state or future reference data.

## Algebra acceptance

Ten focused tests close:

- exact reduction to immediate credit when the successor residual is centered;
- delayed discrimination when current rewards are equal;
- terminal/bootstrap and discounted-return algebra;
- detached actor targets with finite gradients to all three critics;
- exact G17 and G18 replay, inactive action zero and lifecycle schedules;
- three G18 slot permutations;
- one finite optimizer update and checkpoint round trip; and
- first-match screen-result precedence.

The accepted implementation is
`ha_ctse_process/separated_credit_g18.py`. This acceptance is algebraic and
operational only; it is not evidence that the candidate learns either source.

## Frozen bounded dual-source screen

One fresh nonformal CPU screen trains separate source-shaped policies with the
same credit algorithm. No checkpoint, reward, observation or trajectory is
shared across the sources.

```text
gamma=0.99
hidden_dim=32
learning_rate=1e-3
initial_log_std=-1.0
ppo_passes=2
num_envs=8
g17_updates=100
g18_updates=300
g17_eval_episodes=48
g17_environment_steps=38400
g18_environment_steps=28800
successor_weight=1.0
```

G17 must retain the already accepted immediate-source access: IID and held-out
mean utility at least `0.90`, held-out gain over the zero checkpoint at least
`0.10`, minimum episode at least `0.80`, effort and mix correlations at least
`0.90`, and both MAEs at most `0.05`.

G18 must attain mean and every slot-permutation utility at least `0.95`, gain
over its zero checkpoint at least `0.10`, minimum demand-spike utility at least
`0.90`, and at least `0.75` of low-phase effort on the announced rotating
members. The final condition distinguishes delayed-state use from a high-score
allocation that ignores the load-bearing mechanism.

Both sources require CPU/one-thread identity, finite updates, parameter
movement, exact lifecycle schedules, exact inactive action zero, passed source
controls and replay error at most `1e-6`.

First-match outcomes are:

1. `INVALID_FAST_SLOW_SEPARATED_CREDIT_G18`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_SEPARATED_CREDIT_G18`;
3. `NONFORMAL_NO_DELAYED_ACCESS_SEPARATED_CREDIT_G18`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_SEPARATED_CREDIT_G18`; or
5. `NONFORMAL_FAST_SLOW_SEPARATED_CREDIT_PROMISING_G18`.

Only outcome 5 licenses a formal executable-definition boundary. Any other
valid outcome retires this exact candidate without seed, budget, threshold or
hyperparameter rescue. The screen is not conclusion-bearing and consumes no
iteration.

Runner: `scripts/screen_fast_slow_separated_credit_g18.py`.
