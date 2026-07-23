# Beyond-declared-count G7

Status: executable definition frozen; implementation PM-accepted and formal-
ready after Git integration.

## Question

Do the three successful G5 checkpoints remain absolutely usable when roster
counts exceed the declared N=16 feature limit, without retraining or changing
the count formula?

This is iteration 8. G5 and G6 remain closed successes regardless of G7.

## Frozen checkpoint and algorithm semantics

```text
checkpoint_run=logs/formal_open_roster_direct_g5_cpu_20260723_4b38eae_r1
checkpoint_source_commit=4b38eae5abbaeccbab6d53e3eb8f50bd28b957a9
checkpoint_result=USABLE_OPEN_ROSTER_DIRECT_G5
checkpoints=3_final_update_250
training_operation=none_frozen_g5_checkpoint_import
optimizer_steps=0
count_feature=log1p(N)/log1p(16)
active_context=embedding_sum_plus_count_feature
```

The original formula is intentionally evaluated out of its declared range;
for N>16 its value exceeds 1. No clipping, renormalization, new feature,
parameter update or checkpoint adaptation is allowed.

## Stress profiles

All use the 80-step Generic-SHORT task, the original wave windows, reward,
actions, observations and lifecycle rules.

`moderate_beyond`, capacity 32, events 20/40/60:

- `14 -> 8 -> 20 -> 12`;
- `16 -> 10 -> 24 -> 14`.

`far_beyond`, capacity 48, events 20/40/60:

- `18 -> 10 -> 28 -> 16`;
- `24 -> 12 -> 40 -> 20`.

`joint_beyond`, capacity 48:

- `14 -> 8 -> 20 -> 12` at 15/38/58;
- `18 -> 10 -> 28 -> 16` at 18/46/62;
- `24 -> 12 -> 40 -> 20` at 21/45/70.

Expected short requirement is computed from actual wave arrivals. Source
controls require utility one, exact schedules/events/lifecycle semantics and
finite count features. Inactive padding cannot alter active outputs.

## Formal execution

```text
algorithm=BEYOND_DECLARED_COUNT_G7
authorization_token=AUTHORIZE_BEYOND_DECLARED_COUNT_G7_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_replicates=3
optimizer_steps=0
evaluation_episodes_per_cell=128
evaluation_cells=18
bootstrap_repetitions=10000
moderate_ledger_seed=1071000
far_ledger_seed=1071100
joint_ledger_seed=1071200
action_seed_base=1171000
bootstrap_seed=1271007
```

The registered operator runs ordered `train(import) -> evaluate -> analyze` in
one foreground attempt. Formal intake revalidates the exact G5 source, token,
result, runtime, manifests and checkpoints. Only final checkpoints are used and
model state must remain bitwise unchanged.

## Gates and first match

- moderate deterministic replicate-bootstrap CI95 LCB `>=0.90`;
- far deterministic CI95 LCB `>=0.90`;
- joint deterministic CI95 LCB `>=0.90`;
- minimum joint replicate mean `>=0.85`;
- pooled joint stochastic mean `>=0.80`.

First match after operational validity:

1. `NO_MODERATE_BEYOND_COUNT_G7`;
2. `NO_FAR_BEYOND_COUNT_G7`;
3. `NO_JOINT_BEYOND_COUNT_G7`;
4. `UNSTABLE_BEYOND_COUNT_G7`;
5. `ROBUST_BEYOND_DECLARED_COUNT_G7`.

Invalid evidence returns `INVALID_BEYOND_DECLARED_COUNT_G7` and consumes no
iteration. Nonformal evidence returns
`NONFORMAL_BEYOND_DECLARED_COUNT_G7_EXERCISE_COMPLETE` and cannot bear a
conclusion.

## Protected interpretation

Success supports only the exact range through N=40; it is not arbitrary-N
proof. Failure does not relabel G5/G6 and cannot be rescued by threshold or
checkpoint changes. Skill selection, asynchronous skill lifetime, EHC,
intrinsic reward and comparative advantage remain frozen.

## Formal disposition

The exact CPU one-thread source
`19ea4d915ee4bdd03e81c913570d66f0ad00974d` is operationally valid and returns
`NO_MODERATE_BEYOND_COUNT_G7`. Moderate deterministic utility CI95 is
`[0.8590299, 0.9346962, 0.9864063]`; far is
`[0.8089696, 0.8922767, 0.9669230]`; joint is
`[0.8377266, 0.9154998, 0.9789795]`. All models remain bitwise unchanged.

G7 is closed without rerun, tuning or relabeling. The retained G5/G6 success
through N=16 is unchanged. The next independent boundary is
`SCALE_NORMALIZED_OPEN_ROSTER_G8_DERIVATION`.
