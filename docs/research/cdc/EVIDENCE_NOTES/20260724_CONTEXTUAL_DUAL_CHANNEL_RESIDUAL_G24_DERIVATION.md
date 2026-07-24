# Contextual dual-channel residual G24 derivation

Date: 2026-07-24

## Accepted evidence

G23 proves that equal normalized immediate/successor credit over a frozen
residual can preserve G17 and learn most of the delayed battery mechanism. It
passes G18 utility, gain and rotating-effort gates but reaches spike utility
only `0.85332` against the frozen `0.90` floor.

The remaining candidate bottleneck is representation. G23's residual sees the
fast actor's post-RNN candidate, current prefix and raw observation. The fast
encoder/context/RNN are frozen after an immediate-service phase, so their
candidate may discard set-level information useful at a delayed roster
transition. The residual should read the current active-set representation
directly rather than require that information to survive the frozen fast
bottleneck.

## Counterexamples

### CE-RAW-OBSERVATION-PLUS-FROZEN-CANDIDATE-IS-NOT-DIRECT-SET-CONTEXT

Raw member fields identify battery, role and time, but the desired action also
depends on the current anonymous peer set. A frozen candidate can be sufficient
for immediate allocation while compressing peer context needed for the spike.

### CE-CONTEXTUAL-RESIDUAL-DOES-NOT-REQUIRE-CENTERING

G20's contextual proposal failed under active-set centering, successor-only
credit and SGD. That result does not test an unrestricted contextual proposal
with G23 dual-channel Adam. G24 restores no centering constraint.

### CE-SET-CONTEXT-IS-NOT-CRITIC-STATE-LEAKAGE

The residual may read only actor-side member encodings, anonymous active-set
context, current actor hidden state and current observations. It may not read
central critic state, slot identity, future state or source labels.

## Smallest new algorithm

`CONTEXTUAL_DUAL_CHANNEL_RESIDUAL_G24` keeps G23's frozen fast actor,
residual-only Adam and exact dual-channel loss. It replaces the owner-local
residual head with one zero-output proposal head computed once per step from:

```text
[member_encoding_i, active_set_context, hidden_i, observation_i]
```

The proposal is unrestricted and added to the pre-squash mean of the matching
member. It is permutation equivariant, padding independent and exact zero for
inactive rows. The base autoregressive routing and prefix factorization remain
unchanged; the residual itself does not consume the prefix.

## Necessary invariants

1. Zero residual exactly reproduces sampled, deterministic and teacher-replay
   anchor execution.
2. Residual proposals are permutation equivariant, padding independent and
   inactive exact zero.
3. No active-set centering or critic/source field enters the residual.
4. Dual-channel weights/loss identity and residual-only Adam remain exact.
5. Fast actor and exploration scale remain bitwise fixed.
6. Replay, lifecycle and source controls retain their bounds.
7. G17 compatibility remains the first result gate.

## Cheapest separating action

Reintroduce the previously proven optional step residual hook, implement the
unrestricted contextual policy through the existing injectable anchor wrapper,
rename the active module/runner/test and use fresh seeds:

```text
g17_model=3419000
g17_train_ledger=3429000
g17_action=3439000
g17_evaluation_ledger=3449000
g17_evaluation_action=3459000
g18_model=3519000
g18_action=3539000
```

Keep G23 budgets, optimizer, credit, thresholds and branch order. Only a
promising screen licenses formal definition.

```text
next_boundary=CONTEXTUAL_DUAL_CHANNEL_RESIDUAL_G24_PROTOTYPE
formal_compute=not_scheduled
conclusion_bearing_iteration_cost=0
iterations_remaining=8
```
