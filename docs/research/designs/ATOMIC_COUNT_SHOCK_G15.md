# Atomic count-shock G15

Status: formal iteration 16 closed as `ROBUST_ATOMIC_COUNT_SHOCK_G15`; no
rerun, tuning, threshold change or relabeling is admissible.

## Frozen algorithm

```text
algorithm=ATOMIC_COUNT_SHOCK_G15
checkpoint_run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
checkpoint_source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
checkpoint_result=USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
checkpoints=3_final_update_250
training_operation=none_frozen_g8_checkpoint_import
optimizer_steps=0
policy_representation=sum_log1p_count_active_fraction_prefix
```

G5--G14 remain closed. G15 changes only the evaluation membership transaction
distribution and slot capacity. It changes no policy, task, reward,
observation, action, wave, horizon, lifecycle ownership, PPO, checkpoint or
action RNG semantics.

## Atomic count-shock process

Each seed-derived profile starts in its low-count band and has six transactions
at `9, 24, 32, 40, 49, 64`. Targets alternate between the high and low bands.
Every transaction has:

```text
terminally_left=random_active_cohort
joined=random_never_seen_cohort
len(terminally_left)>0
len(joined)>0
len(terminally_left)!=len(joined)
post_event_active_count=sampled_alternating_band_target
```

The smaller cohort contains a positive turnover baseline; the larger adds the
exact count delta. No temporary leave, rejoin or lifecycle-key reuse is legal.

```text
shock_moderate: capacity=128, low=[12,16], high=[24,32], turnover=[2,4]
shock_wide:     capacity=192, low=[28,32], high=[52,64], turnover=[4,6]
shock_ultra:    capacity=224, low=[40,48], high=[72,80], turnover=[6,8]
```

## Formal execution

```text
authorization_token=AUTHORIZE_ATOMIC_COUNT_SHOCK_G15_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=24
evaluation_cells=18
utility_values=432
source_control_rows=72
bootstrap_repetitions=10000
shock_moderate_ledger_seed=4181000
shock_wide_ledger_seed=4181100
shock_ultra_ledger_seed=4181200
action_seed_base=4281000
bootstrap_seed=4381015
```

Source controls require 72 unique profile names, six exact transactions per
profile, alternating low/high count trajectories, constructive utility one,
exact wave demand, terminal persistence and cold-start lifecycle validity.
All imported checkpoints and evaluated models must remain exactly unchanged.

## Gates and first match

- shock-moderate deterministic utility CI95 LCB `>=0.90`;
- shock-wide deterministic utility CI95 LCB `>=0.90`;
- shock-ultra deterministic utility CI95 LCB `>=0.90`;
- minimum shock-ultra deterministic replicate mean `>=0.85`;
- shock-ultra stochastic mean `>=0.80`.

After operational validity, first match is:

1. `NO_ATOMIC_SHOCK_MODERATE_ACCESS_G15`;
2. `NO_ATOMIC_SHOCK_WIDE_ACCESS_G15`;
3. `NO_ATOMIC_SHOCK_ULTRA_ACCESS_G15`;
4. `UNSTABLE_ATOMIC_COUNT_SHOCK_G15`;
5. `ROBUST_ATOMIC_COUNT_SHOCK_G15`.

Invalid evidence returns `INVALID_ATOMIC_COUNT_SHOCK_G15` and consumes no
iteration. Nonformal evidence returns
`NONFORMAL_ATOMIC_COUNT_SHOCK_G15_EXERCISE_COMPLETE`.

## Closed formal result

The exact source `68fa0d6e3f45596e108d858fb7c7a4d1df8e95fe` completed at
`logs/formal_atomic_count_shock_g15_cpu_20260723_68fa0d6_r1`.

```text
branch=ROBUST_ATOMIC_COUNT_SHOCK_G15
operational_valid=true
shock_moderate_deterministic_utility_ci95=[0.9188948796948356,0.9496082486464861,0.9992658037446224]
shock_wide_deterministic_utility_ci95=[0.9166666666666666,0.9487374207165274,0.9995325746495825]
shock_ultra_deterministic_utility_ci95=[0.9225260416666666,0.951754607967718,0.9994695530698207]
shock_ultra_min_replicate_mean=0.9225260416666666
shock_ultra_stochastic_mean=0.8936154854921216
```

This closes the registered composition of large count transport and atomic
cold-start identity turnover. A fresh-seed heterogeneous deployment mixture is
the final confirmation boundary; arbitrary roster processes remain outside the
claim.
