# Randomized roster-process G13

Status: executable definition and implementation accepted; bounded nonformal
exercise operationally valid; formal iteration 14 ready.

## Frozen algorithm

```text
algorithm=RANDOMIZED_ROSTER_PROCESS_G13
checkpoint_run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
checkpoint_source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
checkpoint_result=USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
checkpoints=3_final_update_250
training_operation=none_frozen_g8_checkpoint_import
optimizer_steps=0
policy_representation=sum_log1p_count_active_fraction_prefix
```

G8--G12 remain closed. G13 changes only the evaluation ledger distribution and
source-control inventory. It changes no policy parameter, task, reward,
observation, action, wave, horizon, lifecycle ownership, PPO or action RNG.

## Episode-random process

Each episode samples a distinct initial roster and 12 events from a dedicated
ledger stream. The event pattern repeats three times:

```text
temporary_leave(random active keys, random positive batch)
rejoin(the same temporarily absent keys)
terminal_leave(random active keys, random positive batch)
join(random never-seen keys, random positive batch)
```

Removal-time windows are `[4,8]`, `[14,23]`, `[29,31]`, `[37,39]`, `[44,48]`
and `[54,63]`; the paired rejoin/join times are 9, 24, 32, 40, 49 and 64.
These intervals are random where wave safety permits and never remove a member
during an open wave. The four operation types, keys and batch magnitudes vary
per episode.

```text
random_moderate: capacity=48, initial_N=[12,32], allowed_N=[4,40], max_batch=8
random_wide:     capacity=96, initial_N=[24,56], allowed_N=[8,64], max_batch=12
mixed_churn:     capacity=96, initial_N=[40,72], allowed_N=[12,80], max_batch=16
```

Every generated profile validates its lifecycle transitions. Formal source
controls cover all 48 episode processes in each domain, require unique profile
names, exact event signatures/counts/schedules/wave demand, all four operation
types, constructive utility one and lifecycle freeze/restore.

## Formal execution

```text
authorization_token=AUTHORIZE_RANDOMIZED_ROSTER_PROCESS_G13_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=48
evaluation_cells=18
utility_values=864
source_control_rows=144
bootstrap_repetitions=10000
random_moderate_ledger_seed=3481000
random_wide_ledger_seed=3481100
mixed_churn_ledger_seed=3481200
action_seed_base=3581000
bootstrap_seed=3681013
```

## Gates and first match

- random-moderate deterministic utility CI95 LCB `>=0.90`;
- random-wide deterministic utility CI95 LCB `>=0.90`;
- random-ultra deterministic utility CI95 LCB `>=0.90`;
- minimum random-ultra deterministic replicate mean `>=0.85`;
- random-ultra stochastic mean `>=0.80`.

After operational validity, first match is:

1. `NO_RANDOM_MODERATE_ACCESS_G13`;
2. `NO_RANDOM_WIDE_ACCESS_G13`;
3. `NO_RANDOM_ULTRA_ACCESS_G13`;
4. `UNSTABLE_RANDOM_ROSTER_G13`;
5. `ROBUST_RANDOMIZED_ROSTER_PROCESS_G13`.

Invalid evidence returns `INVALID_RANDOMIZED_ROSTER_PROCESS_G13` and consumes
no iteration. Nonformal evidence returns
`NONFORMAL_RANDOMIZED_ROSTER_G13_EXERCISE_COMPLETE`.
