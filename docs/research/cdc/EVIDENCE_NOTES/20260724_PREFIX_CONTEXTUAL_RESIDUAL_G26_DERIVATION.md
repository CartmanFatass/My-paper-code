# Prefix-contextual residual G26 derivation

Date: 2026-07-24

## Accepted evidence

G23's local residual has the autoregressive prefix and reaches G18 spike utility
`0.85332`, but G25 shows that its frozen-candidate representation cannot fit
the constructive mapping. G24 supplies direct anonymous set context but omits
the prefix and collapses to zero spike service. Neither result tests their
one-axis composition.

## Counterexamples

### CE-SET-CONTEXT-WITHOUT-PREFIX-CANNOT-COORDINATE-EXCLUSIVITY

At a routed member, direct peer context says which roles and resources exist,
but not how much active-set effort preceding members have already proposed.
Independent contextual outputs can duplicate effort and destroy later battery
availability. This is the G24 failure mode.

### CE-PREFIX-WITH-COMPRESSED-SET-CANNOT-RECOVER-DISCARDED-ROLE-STRUCTURE

The prefix reports earlier actions, but G23 obtains peer context only after the
fast immediate-service encoder/RNN. G25 shows that the local head cannot fit the
constructive delayed map under the accepted measurement.

### CE-SUPERVISED-PASS-IS-STILL-DIAGNOSTIC

Constructive labels remain runner-only. Even a pass licenses only a subsequent
PPO candidate using the same source-neutral representation; it never licenses
oracle loss or source fields in the algorithm.

## Smallest representation delta

`PREFIX_CONTEXTUAL_RESIDUAL_EXPRESSIVITY_G26` adds one routed residual hook. For
the current member it concatenates:

```text
[member_encoding_i, active_set_context, current_hidden_i,
 current_prefix_fraction, current_observation_i]
```

The residual is an unrestricted zero-output MLP. The direct actor-side set
context is anonymous and permutation-compatible; the prefix is the existing
causal action prefix. No critic state, source label, future reference, slot
identity or environment-specific field enters policy code.

## Paired diagnostic contract

G26 reuses G25's source, 100-update fast anchor, 36 constructive rows, 200 Adam
fit steps, `1e-3` learning rate, batch size 36, gradient clip `1.0`, MSE gates,
closed-loop G18 gates, CPU runtime and exact seeds. Reusing them makes this a
paired representation comparison, not a retry of the closed local head. Only
the residual feature map changes.

First match:

1. `INVALID_PREFIX_CONTEXTUAL_RESIDUAL_EXPRESSIVITY_G26`;
2. `NO_POINTWISE_PREFIX_CONTEXTUAL_FIT_G26`;
3. `NO_CLOSED_LOOP_PREFIX_CONTEXTUAL_REALIZATION_G26`;
4. `PASS_PREFIX_CONTEXTUAL_RESIDUAL_EXPRESSIVITY_G26`.

A pass licenses one dual-channel PPO prototype using this representation. A
pointwise failure retires the frozen-anchor residual representation family. A
pointwise pass with closed-loop failure isolates autoregressive rollout/state
realization. No outcome is formal, conclusion-bearing or UAV evidence.
