# Direction-balanced full actor G30

```text
status=IMPLEMENTATION_ACCEPTED_BOUNDED_SCREEN_NEXT
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen algorithm delta

Reuse the two-phase full actor, independently normalized immediate/successor
advantages, state-only critics and exact-zero residual. Replace G29's realized
parameter projection with a pre-Adam direction-balanced composition. For each
nonzero global actor gradient divide by its exact float64 norm, take the equal
half-sum, cast once to actor dtype, apply the existing global gradient clip and
advance ordinary Adam once.

Both-zero, immediate-zero and successor-zero branches are exact and contain no
epsilon threshold. No projection, lattice repair, learned gate, raw-norm
rescale, optimizer rollback or second step is allowed. Adam moments receive the
direction-balanced gradient; cross-G28/G29 resume is forbidden.

## Screen contract

- G17 fast/direction-balanced updates: `100/100`; G18: `100/300`.
- Eight environments, two PPO passes, Adam `1e-3`, CPU one thread.
- G17 evaluation uses 48 IID and 48 held-out episodes; G18 uses all three
  registered slot layouts.
- Fresh seeds: G17 model/ledger/action/evaluation-ledger/evaluation-action
  `6119000/6129000/6139000/6149000/6159000`; G18 model/action
  `6219000/6239000`.
- Replay `<=1e-6`; direction-balanced raw immediate dot `>=-1e-7`; exact
  composition identity `<=1e-7`; lifecycle, ownership, inactive rows, finite
  global norms, ordinary Adam step count and zero residual fail closed.
- Behavioral thresholds and first-match order remain exactly G28/G29: invalid,
  no G17 compatibility, no G18 access, no G18 mechanism, promising.

## Protected semantics

Sources, observations, rewards, factorization, recurrent/lifecycle state, RNG,
PPO clipping, advantage normalization, critics, budgets, thresholds and result
precedence are frozen. Only actor-gradient magnitude semantics and its fresh
checkpoint identity change. There is no oracle input, formal mode or UAV
promotion.

## Proof-sized acceptance

1. Aligned, obtuse, exact-opposite, both-zero and either-one-zero cases match
   the closed-form composition and nonnegative float64 raw dot.
2. The output is parallel to the exact unit-direction half-sum; no epsilon,
   projection or hidden rescale is present.
3. Gradient clipping preserves direction, ordinary Adam advances exactly once,
   and checkpoint state receives the composed gradient.
4. A high-dimensional near-opposite float32 case remains finite and inside the
   unchanged `-1e-7` bound.
5. G17/G18 replay, lifecycle, actor/critic/residual ownership and first-match
   semantics pass before one integrated paired screen.
