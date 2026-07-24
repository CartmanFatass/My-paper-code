# Net-immediate-descent full actor G28

```text
status=DESIGN_FROZEN_IMPLEMENTATION_NEXT
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen algorithm delta

Reuse the G27 two-phase full-actor policy, equal independently normalized
immediate/successor channels, state-only critics and exact-zero residual. Replace
only the successor half-space: protect the equal-weight *combined* gradient,
not the successor gradient alone. If `dot(g_i, g_s) < -||g_i||^2`, add the
minimum multiple of `g_i` that makes
`dot(g_i, 0.5*(g_i+g_s')) >= 0`; otherwise leave `g_s` unchanged.

## Screen contract

- G17 fast/tolerant updates: `100/100`; G18: `100/300`.
- Eight environments, two PPO passes, Adam `1e-3`, CPU one thread.
- G17 evaluation: 48 episodes in IID and held-out domains; G18 uses all three
  registered slot layouts.
- Fresh seeds: G17 model/ledger/action/evaluation-ledger/evaluation-action
  `4119000/4129000/4139000/4149000/4159000`; G18 model/action
  `4219000/4239000`.
- Replay `<=1e-6`; net-immediate post dot and applied-gradient identity
  `>=-1e-7` and `<=1e-7`; lifecycle, ownership, inactive rows and zero residual
  fail closed.
- Behavioral thresholds and branch order are exactly G27: invalid, no G17
  compatibility, no G18 access, no G18 mechanism, promising.

## Protected semantics

Sources, observations, rewards, factorization, recurrent/lifecycle state, RNG,
PPO clipping, channel normalization, critics, optimizers, budgets, seeds,
thresholds and first-match precedence are frozen except for the listed fresh
seed identities. There is no oracle input, source identity, future reference,
formal mode or UAV promotion.

## Proof-sized acceptance

1. Non-conflicting and tolerable-conflict successor gradients are unchanged.
2. Excess conflict maps to the exact combined-descent boundary in scalar and
   multi-parameter cases, including the float32 reproducer.
3. Applied gradient remains the exact equal average; actor/critic/residual
   ownership is unchanged from G27.
4. One G17 and one G18 trajectory retain exact replay/lifecycle behavior.
5. One integrated bounded screen is the only conclusion-bearing next action.
