# Optimizer-realized tangent full actor G29

```text
status=DESIGN_FROZEN_IMPLEMENTATION_NEXT
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen algorithm delta

Reuse the G28 two-phase full actor, independently normalized immediate and
successor channels, equal channel weights, state-only critics and exact-zero
residual. Remove the pre-Adam raw-gradient projection. Apply the clipped raw
equal combined actor gradient to Adam exactly once, compute the realized
descent displacement `d = theta_before - theta_adam`, and leave it unchanged
when `dot(g_i, d) >= 0`. Otherwise project only `d` to the closest
immediate-tangent boundary and write `theta_before - d'` to the actor.

Adam moments and step counters always reflect the clipped unprojected equal
combined gradient; projected actor parameters and those moments jointly define
checkpoint state. There is no optimizer rollback, second step, coefficient,
learned gate, tolerance relaxation or raw-gradient constraint.

## Screen contract

- G17 fast/realized-tangent updates: `100/100`; G18: `100/300`.
- Eight environments, two PPO passes, Adam `1e-3`, CPU one thread.
- G17 evaluation uses 48 IID and 48 held-out episodes; G18 uses all three
  registered slot layouts.
- Fresh seeds: G17 model/ledger/action/evaluation-ledger/evaluation-action
  `5119000/5129000/5139000/5149000/5159000`; G18 model/action
  `5219000/5239000`.
- Replay `<=1e-6`; realized-displacement immediate dot `>=-1e-7`; exact
  applied-parameter identity `<=1e-7`; lifecycle, optimizer state/step count,
  ownership, inactive rows and zero residual fail closed.
- Behavioral thresholds and first-match order remain exactly G28: invalid,
  no G17 compatibility, no G18 access, no G18 mechanism, promising.

## Protected semantics

Sources, observations, rewards, factorization, recurrent/lifecycle state, RNG,
PPO clipping, channel normalization, critics, budgets, thresholds and result
precedence are frozen. Actor optimizer state meaning changes only as explicitly
defined above; critic optimizer and every old result remain unchanged. There is
no oracle input, future reference, formal mode or UAV promotion.

## Proof-sized acceptance

1. A momentum/preconditioning counterexample separates raw-gradient and actual
   displacement dots, and G29 closes only the latter.
2. A non-conflicting ordinary Adam step leaves parameters and complete optimizer
   state bitwise unchanged; a conflict advances Adam state exactly once.
3. Float64 plus one-coordinate lattice closure retains the first closed
   float32 displacement without relaxing `1e-7`.
4. Applied parameter identity, full actor/critic/residual ownership and
   checkpoint state meaning fail closed under tampering or nonfinite values.
5. One G17 and one G18 trajectory retain exact replay/lifecycle behavior and
   the integrated paired screen is the only next evidence action.
