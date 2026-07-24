# Prefix-contextual residual expressivity G26

```text
status=NONFORMAL_CLOSED_NO_POINTWISE_FIT
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen delta

G26 retains the complete G25 diagnostic and replaces only the local residual
features. The routed zero-output MLP reads direct member encoding, anonymous
active-set context, current hidden state, current autoregressive prefix and
current observation. The base policy hook returns no residual. G26 is the only
active implementation of the hook.

## Preserved contract

- unchanged G18 source, constructive dataset and fast-anchor training;
- bitwise identical G25 non-residual initialization and post-construction RNG
  state, plus identical seeds, fit budget, optimizer, loss, gates and branch
  order;
- residual-only mutation and bitwise frozen non-residual state;
- inactive exact zero, finite CPU execution and exact source/lifecycle rows;
- no critic/source/future/slot input and no PPO delayed update;
- fixed `formal=false` artifact with zero iteration cost.

## Proof-sized acceptance

1. Exact zero residual reproduces the anchor in sampled, deterministic and
   teacher-replay execution.
2. Direct set context and the live prefix both change the routed proposal in a
   focused counterexample; no cached prior-step prefix is used.
3. Permuting active rows permutes outputs within `1e-7`; padding and inactive
   rows remain exact.
4. The optimizer owns only the new residual and leaves every other tensor
   bitwise unchanged.
5. First-match precedence retains invalid, pointwise, closed-loop and pass
   outcomes.

After focused acceptance, run exactly one integrated bounded CPU diagnostic.

## Implementation acceptance

The active source-neutral representation is
`ha_ctse_process/prefix_contextual_residual_g26.py`. The generic routed hook now
passes direct actor fields and the current prefix to the active policy; the base
path ignores them. The diagnostic runner/test are renamed from G25, so no
duplicate executable line remains.

Ten focused and 31 focused-plus-retained G17/G18/G19 tests pass on the
registered CPU one-thread runtime. They prove exact zero-output behavior in all
execution modes, independent sensitivity to direct context and live prefix,
full routed permutation plus proposal/padding behavior within `1e-7`, inactive exact zero,
residual-only mutation, bitwise frozen state, exact dataset coverage and
fail-closed precedence. This accepts only the paired G26 bounded probe.

The first integrated attempt exposed that the larger residual consumed extra
constructor RNG before the credit baselines, so its fast anchor was not paired
with G25. That artifact is operationally invalid for this question. The repair
constructs the G25 local reference from the same incoming RNG state, copies
every non-residual tensor bitwise, restores the exact G25 post-construction RNG
state, and adds a regression proving both identities before a fresh-root rerun.

## Repaired probe disposition

The fresh-root repair exactly reproduces G25's fast-anchor utility `0.666788`
and retains zero replay and frozen-state error. Pointwise MSE falls from
`1.43119` to `0.34146`, a ratio of `0.23859`; both gates still fail. Closed-loop
utility `0.92811`, spike utility `0.88163`, gain `0.26132` and rotating share
`0.85982` show useful partial structure but cannot bypass the pointwise branch.
The exact valid result is `NO_POINTWISE_PREFIX_CONTEXTUAL_FIT_G26`.

G25 and G26 jointly retire the frozen-anchor additive residual representation
family under this measurement. No further input stacking, fit-budget increase,
optimizer change, threshold rescue, formal run or UAV promotion is selected.
