# Scale-by-churn composition G10

Status: formal closed as `ROBUST_SCALE_CHURN_COMPOSITION_G10`; no rerun, tuning
or relabeling.

## Frozen policy and source

```text
algorithm=SCALE_CHURN_COMPOSITION_G10
checkpoint_run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
checkpoint_source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
checkpoint_result=USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
checkpoints=3_final_update_250
training_operation=none_frozen_g8_checkpoint_import
optimizer_steps=0
policy_representation=sum_log1p_count_active_fraction_prefix
```

G8 and G9 remain closed. G10 changes only the evaluation membership schedules;
it changes no model parameter, reward, observation, action, wave, horizon,
lifecycle ownership, PPO or RNG semantics.

## Exact profiles

`moderate_scale_churn`, capacity 32, initial keys 0--15:

```text
t9  temp_leave(8..11)       N=12
t13 rejoin(8..11)           N=16
t24 terminal_leave(0..3)    N=12
t28 join(16..23)            N=20
t40 temp_leave(12..15)      N=16
t44 rejoin(12..15)+join(24..27) N=24
t64 terminal_leave(4..11)   N=16
t68 join(28..31)            N=20
```

`far_scale_churn`, capacity 48, initial keys 0--23:

```text
t9  temp_leave(16..23)      N=16
t13 rejoin(16..23)          N=24
t24 terminal_leave(0..7)    N=16
t28 join(24..39)            N=32
t40 temp_leave(8..15)       N=24
t44 rejoin(8..15)+join(40..47) N=40
t64 terminal_leave(16..31)  N=24
t68 terminal_leave(32..39)  N=16
```

`mixed_churn`, capacity 48, initial keys 0--19:

```text
t6  temp_leave(12..19)      N=12
t10 rejoin(12..19)          N=20
t24 terminal_leave(0..7)    N=12
t28 join(20..35)            N=28
t40 temp_leave(8..19)       N=16
t44 rejoin(8..19)+join(36..47) N=40
t60 temp_leave(12..19)      N=32
t64 rejoin(12..19)          N=40
```

Events apply before a wave opening at the same time. Validation simulates every
transition, forbids lifecycle reuse and requires the exact post-event active
count. Source controls require exact schedules, post-event wave demand,
finite observations, hidden-state freeze/restore and constructive utility one.

## Formal execution

```text
authorization_token=AUTHORIZE_SCALE_CHURN_COMPOSITION_G10_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=128
evaluation_cells=18
bootstrap_repetitions=10000
moderate_scale_churn_ledger_seed=2381000
far_scale_churn_ledger_seed=2381100
mixed_churn_ledger_seed=2381200
action_seed_base=2481000
bootstrap_seed=2581010
```

## Gates and first match

- moderate scale-churn deterministic CI95 LCB `>=0.90`;
- far scale-churn deterministic CI95 LCB `>=0.90`;
- mixed scale-churn deterministic CI95 LCB `>=0.90`;
- minimum mixed replicate mean `>=0.85`;
- mixed stochastic mean `>=0.80`.

After operational validity, first match is:

1. `NO_MODERATE_SCALE_CHURN_ACCESS_G10`;
2. `NO_FAR_SCALE_CHURN_ACCESS_G10`;
3. `NO_MIXED_SCALE_CHURN_ACCESS_G10`;
4. `UNSTABLE_SCALE_CHURN_COMPOSITION_G10`;
5. `ROBUST_SCALE_CHURN_COMPOSITION_G10`.

Invalid evidence returns `INVALID_SCALE_CHURN_COMPOSITION_G10` and consumes no
iteration. Nonformal evidence returns
`NONFORMAL_SCALE_CHURN_G10_EXERCISE_COMPLETE`.
