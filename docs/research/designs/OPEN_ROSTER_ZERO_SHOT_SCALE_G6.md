# Open-roster zero-shot scale G6

Status: formally complete and closed as `ROBUST_ZERO_SHOT_OPEN_ROSTER_G6`.

## Question

Do the three closed G5 final checkpoints retain absolute usability under far
unseen roster counts, unseen membership-event times, and their composition,
without any new training?

This is iteration 7 and the second conclusion-bearing action in the user-
authorized twelve-round dynamic-agent chain. It is not a rerun or rescue of G5.
G5 remains `USABLE_OPEN_ROSTER_DIRECT_G5` regardless of this result.

## Frozen checkpoint provenance

```text
g5_run=logs/formal_open_roster_direct_g5_cpu_20260723_4b38eae_r1
g5_source_commit=4b38eae5abbaeccbab6d53e3eb8f50bd28b957a9
g5_result=USABLE_OPEN_ROSTER_DIRECT_G5
g5_replicates=3
g5_completed_updates=250
g6_training_operation=none_frozen_g5_checkpoint_import
g6_optimizer_steps=0
```

The G6 import stage must fail closed unless the G5 train and analysis manifests
are formal and complete, CPU one-thread, source-identical, operationally valid
and carry the exact branch above. It strictly loads each final checkpoint and
materializes it under the fresh G6 run root. Manifest replicate seeds and the
checkpoint-embedded RNG-contract constants are distinct evidence fields.

## Stress source

All profiles use the G5 80-step Generic-SHORT environment, primitive action
space, terminal external utility, wave windows, observation schema, lifecycle
rules and exact count feature `log1p(N)/log1p(16)`.

`count_scale`, capacity 20, event times 20/40/60:

- `8 -> 4 -> 12 -> 6`;
- `10 -> 6 -> 14 -> 8`;
- `12 -> 8 -> 16 -> 10`.

`event_time`, capacity 12:

- `6 -> 2 -> 8 -> 4` at 15/38/58;
- `7 -> 4 -> 9 -> 6` at 18/46/62.

`joint`, capacity 20:

- `8 -> 4 -> 12 -> 6` at 15/38/58;
- `10 -> 6 -> 14 -> 8` at 18/46/62;
- `12 -> 8 -> 16 -> 10` at 21/45/70.

Expected short demand is computed from the actual wave arrivals and active
membership at those arrivals. Every profile must have constructive utility one.
Temporary leave freezes hidden state, rejoin restores it, genuine join starts
at zero and terminal leave removes the lifecycle. No skill or event hierarchy
is introduced.

## Formal execution

```text
algorithm=OPEN_ROSTER_ZERO_SHOT_SCALE_G6
authorization_token=AUTHORIZE_OPEN_ROSTER_ZERO_SHOT_SCALE_G6_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=128
evaluation_cells=18
bootstrap_repetitions=10000
count_ledger_seed=1061000
event_time_ledger_seed=1061100
joint_ledger_seed=1061200
action_seed_base=1161000
bootstrap_seed=1261006
```

The registered experiment operator still executes three ordered commands. The
`train` command is explicitly a zero-training provenance/import stage, followed
by evaluate and analyze. Only final checkpoints are evaluated across three
domains and deterministic/stochastic modes. Model parameters must remain
bitwise unchanged.

## Gates and first-match result

Absolute usability retains the G5 thresholds:

- count-scale deterministic replicate-bootstrap CI95 LCB `>=0.90`;
- event-time deterministic CI95 LCB `>=0.90`;
- joint deterministic CI95 LCB `>=0.90`;
- minimum joint replicate mean `>=0.85`;
- pooled joint stochastic mean `>=0.80`.

First match after operational validity:

1. `NO_COUNT_SCALE_TRANSPORT_G6`;
2. `NO_EVENT_TIME_TRANSPORT_G6`;
3. `NO_JOINT_SCALE_TIME_TRANSPORT_G6`;
4. `UNSTABLE_ZERO_SHOT_TRANSPORT_G6`;
5. `ROBUST_ZERO_SHOT_OPEN_ROSTER_G6`.

Operational invalidity returns `INVALID_OPEN_ROSTER_ZERO_SHOT_G6` and consumes
no iteration. A nonformal exercise returns
`NONFORMAL_OPEN_ROSTER_G6_EXERCISE_COMPLETE` and cannot bear a conclusion.

## Protected interpretation

Success supports zero-shot transport only on the exact count/time range. It is
not arbitrary-N generalization or algorithmic advantage. Failure does not
relabel G5; it selects the corresponding smallest independent G7 repair. Skill
selection, asynchronous skill lifetime, EHC and intrinsic reward remain frozen.

## Formal disposition

The exact CPU one-thread run at source
`909ced01ee58e2690fd7cd0ec2da214e99203af5` is operationally valid with zero
optimizer steps and exact model immutability. Count-scale, event-time and joint
CI95 lower bounds are `0.9294811`, `0.9854642` and `0.9358802`; the registered
first match is `ROBUST_ZERO_SHOT_OPEN_ROSTER_G6`.

The result rejects the three registered counterexamples through N=16 but does
not cross the declared count-feature limit. G6 is closed without tuning or
relabeling; beyond-limit transport is independent G7 evidence.
