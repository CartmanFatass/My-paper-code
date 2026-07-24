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

## Nonformal screen disposition

The exact screen at source commit `95c5d1266cb2ecc0e9de8993e8e60cc55e35ff5f`
completed with zero replay error and selected
`NONFORMAL_ACTOR_CRITIC_ISOLATED_CREDIT_PROMISING_G18`. It passed every frozen
G17 and G18 threshold and therefore licenses this formal definition without
changing the algorithm.

## Formal executable definition

```text
authorization_token=AUTHORIZE_ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18_FORMAL_CPU_V1
formal_replicates=3
g17_updates_per_replicate=100
g18_updates_per_replicate=300
num_envs=8
ppo_passes=2
g17_eval_episodes_per_domain_per_replicate=128
g18_slot_permutations_per_replicate=3
bootstrap_repetitions=10000
total_g17_environment_steps=115200
total_g18_environment_steps=86400
backend=cpu
torch_threads=1
```

Formal seeds are fresh and replicate-indexed from these bases:

```text
g17_model=2218000
g17_train_ledger=2228000
g17_action=2238000
g17_evaluation_ledger=2248000
g17_evaluation_action=2258000
g18_model=2318000
g18_action=2338000
bootstrap=2368018
```

Replicate `r` adds `r` to every source seed. Checkpoints bind algorithm,
formal identity, source commit, replicate, completed updates and the complete
configuration. Training must be finite, move parameters, retain exact replay
within `1e-6`, preserve lifecycle schedules and keep inactive actions exact
zero.

G17 IID/held-out utility and held-out gain use hierarchical 95% CIs over
replicate and episode. G18 utility, paired zero-checkpoint gain, spike utility
and rotating-member effort share use the same registered bootstrap over
replicate and slot layout. First-match outcomes are:

1. `INVALID_ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18` on operational failure;
2. `NO_G17_COMPATIBILITY_CRITIC_ISOLATED_G18` unless G17 IID/held-out LCBs are
   at least `0.90`, gain LCB at least `0.10`, every episode at least `0.80`,
   both minimum mapping correlations at least `0.90`, and both maximum MAEs at
   most `0.05`;
3. `NO_DELAYED_ACCESS_CRITIC_ISOLATED_G18` unless G18 utility LCB is at least
   `0.95`, paired gain LCB at least `0.10`, and spike-utility LCB at least
   `0.90`;
4. `NO_DELAYED_MECHANISM_CRITIC_ISOLATED_G18` unless rotating-effort-share LCB
   is at least `0.75`;
5. `UNSTABLE_ACTOR_CRITIC_ISOLATED_CREDIT_G18` unless every replicate's mean
   G18 utility is at least `0.90`; or
6. `USABLE_DELAYED_DYNAMIC_ROSTER_CREDIT_G18`.

Only branch 6 supports a usable delayed-effect toy algorithm. No result here
supports UAV radio, motion, charging-station geometry or deployment claims.
One valid formal analysis consumes conclusion-bearing iteration 19.

Before launch, the same runner must close a bounded nonformal path exercise:
one replicate, one update per source, two environments, four G17 evaluation
episodes and one PPO pass. Its only valid branch is
`NONFORMAL_CRITIC_ISOLATED_FORMAL_PATH_EXERCISE_COMPLETE`, and formal analysis
must reject it.

The exercise completed operationally with exact replay and the registered
nonformal branch; the explicit formal-analysis attempt rejected it. Formal
iteration 19 is therefore prelaunch-ready without any contract change.
