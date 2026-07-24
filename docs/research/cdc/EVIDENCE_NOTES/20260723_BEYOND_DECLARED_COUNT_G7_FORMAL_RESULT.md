# BEYOND_DECLARED_COUNT_G7 formal result

Date: 2026-07-23

```text
source_commit=19ea4d915ee4bdd03e81c913570d66f0ad00974d
run=logs/formal_beyond_declared_count_g7_cpu_20260723_19ea4d9_r1
checkpoint_source_commit=4b38eae5abbaeccbab6d53e3eb8f50bd28b957a9
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
training_operation=none_frozen_g5_checkpoint_import
optimizer_steps=0
result=NO_MODERATE_BEYOND_COUNT_G7
conclusion_bearing_iteration=8
iterations_remaining=9
```

## Evidence closure

The registered Luna-low operator completed the exact import, evaluate and
analyze commands once with all exit codes zero and no restart. Project Manager
then independently closed the three imported update-250 checkpoints, 18 exact
replicate/domain/determinism cells and 2,304 evaluation outcomes.

Every outcome array contains 128 finite values in `[0,1]`; external mean
recomputation differs from the serialized mean by at most `6.67e-16`. Every
model-state difference is exactly zero and every optimizer-step count is zero.
All seven source-control profiles have constructive utility one, exact roster
schedules, actual-wave demand, membership events, lifecycle state and terminal
destruction. The source, G5 provenance, authorization tokens, runtime and count
contracts are exact. `operational_valid=true` and the error list is empty.

## Registered result

| Quantity | Registered value |
|---|---:|
| Moderate deterministic utility CI95 | [0.8590299, 0.9346962, 0.9864063] |
| Far deterministic utility CI95 | [0.8089696, 0.8922767, 0.9669230] |
| Joint deterministic utility CI95 | [0.8377266, 0.9154998, 0.9789795] |
| Joint replicate means | [0.9789795, 0.8377266, 0.9297932] |
| Joint minimum replicate mean | 0.8377266 |
| Joint stochastic utility mean | 0.8873766 |

The moderate lower bound `0.8590299` is already below the registered `0.90`
floor. Independent first-match recomputation therefore exactly returns
`NO_MODERATE_BEYOND_COUNT_G7`; lower-precedence far, joint and stability gates
cannot relabel that outcome.

## Scientific correction

The result rejects robust zero-training extrapolation of the exact G5 feature
mapping beyond its declared N=16 range. It does not reject the closed G5/G6
success through N=16. Mean utility remains high, but replicate 1 falls to
`0.8590299` in the moderate band, `0.8089696` in the far band and `0.8377266`
under joint stress. All deterministic persistent scores remain exactly `1.0`;
the degradation is entirely in short-duty allocation, whose replicate-1 mean
falls from `0.7180599` to `0.6179393` as scale increases.

The evidence is compatible with both active-embedding-sum growth and the
out-of-range `log1p(N)/log1p(16)` count coordinate. G7 does not identify which
one is sufficient. The smallest next action is therefore a bounded
scale-normalized representation derivation and prototype screen, followed by a
freshly trained formal algorithm only after its exact evidence contract is
frozen. No G7 checkpoint, threshold or budget is rescued.

```text
scientific_disposition=closed_failure_no_rerun_tuning_or_relabeling
next_boundary=SCALE_NORMALIZED_OPEN_ROSTER_G8_DERIVATION
iterations_remaining=9
```
