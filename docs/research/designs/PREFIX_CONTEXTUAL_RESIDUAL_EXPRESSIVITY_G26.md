# Prefix-contextual residual expressivity G26

```text
status=DESIGN_FROZEN_IMPLEMENTATION_NEXT
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
- identical G25 seeds, fit budget, optimizer, loss, gates and branch order;
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
