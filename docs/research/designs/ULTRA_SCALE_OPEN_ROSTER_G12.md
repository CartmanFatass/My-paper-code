# Ultra-scale open-roster G12

Status: formal iteration 13 closed as
`ROBUST_ULTRA_SCALE_OPEN_ROSTER_G12`; no rerun, tuning, threshold change or
relabeling is admissible.

## Frozen policy and source semantics

```text
algorithm=ULTRA_SCALE_OPEN_ROSTER_G12
checkpoint_run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
checkpoint_source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
checkpoint_result=USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
checkpoints=3_final_update_250
training_operation=none_frozen_g8_checkpoint_import
optimizer_steps=0
policy_representation=sum_log1p_count_active_fraction_prefix
```

G7--G11 remain closed. G12 changes only evaluation membership schedules and
tensor capacity. It changes no model parameter, task utility, observation,
action, wave, horizon, lifecycle ownership, PPO or RNG semantics.

## Exact profiles

`edge_ultra_scale`, capacity 64:

```text
initial 0..31                 N=32
t6  temp_leave(20..31)       N=20
t10 rejoin(20..31)           N=32
t24 terminal_leave(0..11)    N=20
t28 join(32..55)             N=44
t40 temp_leave(12..23)       N=32
t44 rejoin(12..23)+join(56..59) N=48
t60 terminal_leave(24..35)   N=36
t64 terminal_leave(36..47)   N=24
```

`far_ultra_scale`, capacity 80:

```text
initial 0..39                 N=40
t6  temp_leave(24..39)       N=24
t10 rejoin(24..39)           N=40
t24 terminal_leave(0..15)    N=24
t28 join(40..71)             N=56
t40 temp_leave(16..31)       N=40
t44 rejoin(16..31)+join(72..79) N=64
t60 terminal_leave(32..47)   N=48
t64 terminal_leave(48..63)   N=32
```

`mixed_churn` (the ultra domain), capacity 96:

```text
initial 0..47                 N=48
t6  temp_leave(32..47)       N=32
t10 rejoin(32..47)           N=48
t24 terminal_leave(0..15)    N=32
t28 join(48..79)             N=64
t40 temp_leave(16..31)       N=48
t44 rejoin(16..31)+join(80..95) N=80
t60 terminal_leave(32..47)   N=64
t64 terminal_leave(48..63)   N=48
```

Events apply before any wave opening at the same time. Validation simulates all
transitions, forbids lifecycle reuse, and requires the exact post-event count.
Source controls require exact schedules, actual wave requirements, eight event
transactions, lifecycle freeze/restore and constructive utility one.

## Formal execution

```text
authorization_token=AUTHORIZE_ULTRA_SCALE_OPEN_ROSTER_G12_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=64
evaluation_cells=18
utility_values=1152
bootstrap_repetitions=10000
edge_ultra_scale_ledger_seed=3081000
far_ultra_scale_ledger_seed=3081100
mixed_churn_ledger_seed=3081200
action_seed_base=3181000
bootstrap_seed=3281012
```

## Gates and first match

- N=48 edge deterministic utility CI95 LCB `>=0.90`;
- N=64 far deterministic utility CI95 LCB `>=0.90`;
- N=80 ultra deterministic utility CI95 LCB `>=0.90`;
- minimum N=80 deterministic replicate mean `>=0.85`;
- N=80 stochastic mean `>=0.80`.

After operational validity, first match is:

1. `NO_EDGE_SCALE_ACCESS_G12`;
2. `NO_FAR_SCALE_ACCESS_G12`;
3. `NO_ULTRA_SCALE_ACCESS_G12`;
4. `UNSTABLE_ULTRA_SCALE_G12`;
5. `ROBUST_ULTRA_SCALE_OPEN_ROSTER_G12`.

Invalid evidence returns `INVALID_ULTRA_SCALE_OPEN_ROSTER_G12` and consumes no
iteration. Nonformal evidence returns
`NONFORMAL_ULTRA_SCALE_G12_EXERCISE_COMPLETE`.

## Closed formal result

The exact source `21046fcf9a67cd7503266284c02896ae85dafd62`
completed at `logs/formal_ultra_scale_g12_cpu_20260723_21046fc_r1`.

```text
branch=ROBUST_ULTRA_SCALE_OPEN_ROSTER_G12
operational_valid=true
edge_ultra_scale_deterministic_utility_ci95=[0.9251708984375,0.9513818884408604,0.9996534778225806]
far_ultra_scale_deterministic_utility_ci95=[0.923095703125,0.949975157620614,0.9987291837993421]
mixed_churn_deterministic_utility_ci95=[0.927001953125,0.952321846707433,0.999787805747299]
mixed_churn_min_replicate_mean=0.927001953125
mixed_churn_stochastic_mean=0.8973560290001418
```

This closes the registered zero-training N<=80 question. It does not establish
arbitrary scale or robustness to an episode-random membership process.
