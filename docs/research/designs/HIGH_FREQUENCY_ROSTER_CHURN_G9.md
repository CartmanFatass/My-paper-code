# High-frequency roster churn G9

Status: executable definition frozen; focused implementation checks complete;
bounded nonformal exercise pending.

## Frozen source and policy

```text
algorithm=HIGH_FREQUENCY_ROSTER_CHURN_G9
checkpoint_run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
checkpoint_source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
checkpoint_result=USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
checkpoints=3_final_update_250
training_operation=none_frozen_g8_checkpoint_import
optimizer_steps=0
policy_representation=sum_log1p_count_active_fraction_prefix
```

G8 and its checkpoints remain closed. G9 changes no model parameter, reward,
observation, action, wave, horizon, count coordinate or PPO semantics.

## Event profiles

All profiles have capacity 20, eight membership edits and maximum active count
at most 16. Event time applies before a wave opening at the same time.

`repeated_rejoin`, initial keys 0--7:

```text
t9  temp_leave(6,7)
t13 rejoin(6,7)
t24 temp_leave(6,7)
t28 rejoin(6,7)
t40 temp_leave(6,7)
t44 rejoin(6,7) + join(8,9)
t64 terminal_leave(0,1)
t68 join(10,11)
```

`load_proximal`, initial keys 0--11:

```text
t9  temp_leave(8,9,10,11)
t13 rejoin(8,9,10,11)
t24 terminal_leave(0,1)
t28 join(12,13,14,15)
t40 temp_leave(10,11,12,13)
t44 rejoin(10,11,12,13)
t64 terminal_leave(2,3,4,5)
t68 join(16,17)
```

`mixed_churn`, initial keys 0--9:

```text
t6  temp_leave(8,9)
t10 rejoin(8,9)
t24 terminal_leave(0,1)
t28 join(10,11,12,13)
t40 temp_leave(6,7,8,9)
t44 rejoin(6,7,8,9)
t60 terminal_leave(2,3,4,5)
t64 join(14,15,16,17)
```

Profile validation simulates every lifecycle transition, rejects reuse after
terminal leave, requires nonempty active sets, and computes wave demand from
the post-event count. Source controls require exact schedules, membership
deltas, finite observations and constructive utility one.

## Formal execution

```text
authorization_token=AUTHORIZE_HIGH_FREQUENCY_ROSTER_CHURN_G9_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=128
evaluation_cells=18
bootstrap_repetitions=10000
repeated_rejoin_ledger_seed=1981000
load_proximal_ledger_seed=1981100
mixed_churn_ledger_seed=1981200
action_seed_base=2081000
bootstrap_seed=2181009
```

The fixed operator runs ordered `train(import) -> evaluate -> analyze` once.
G8 source, token, result, representation, runtime, counts and update-250 finals
must match exactly. Models remain bitwise unchanged.

## Gates and first match

- repeated-rejoin deterministic CI95 LCB `>=0.90`;
- load-proximal deterministic CI95 LCB `>=0.90`;
- mixed-churn deterministic CI95 LCB `>=0.90`;
- minimum mixed-churn replicate mean `>=0.85`;
- mixed-churn stochastic mean `>=0.80`.

After operational validity, first match is:

1. `NO_REPEATED_REJOIN_ACCESS_G9`;
2. `NO_LOAD_PROXIMAL_CHURN_ACCESS_G9`;
3. `NO_MIXED_CHURN_ACCESS_G9`;
4. `UNSTABLE_HIGH_FREQUENCY_CHURN_G9`;
5. `ROBUST_HIGH_FREQUENCY_CHURN_G9`.

Invalid evidence returns `INVALID_HIGH_FREQUENCY_CHURN_G9` and costs no
iteration. Nonformal evidence returns
`NONFORMAL_HIGH_FREQUENCY_CHURN_G9_EXERCISE_COMPLETE`.
