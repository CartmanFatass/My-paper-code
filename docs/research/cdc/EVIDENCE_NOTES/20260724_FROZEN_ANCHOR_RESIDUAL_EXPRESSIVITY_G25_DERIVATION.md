# Frozen-anchor residual expressivity G25 derivation

Date: 2026-07-24

## Accepted evidence

G23 preserves G17 and nearly closes the delayed source, but misses only the
frozen spike floor. G24 widens the residual representation and regresses to
zero spike service. These screens do not distinguish a local-representation
limit from a failure of PPO credit to reach an already representable policy.

The G17 chain previously used a supervised constructive-action fit with exact
active-row MSE gates to separate representation from PPO access. Reusing that
measurement on G18 is the smallest decision-changing action.

## Counterexamples

### CE-NEAR-UTILITY-DOES-NOT-PROVE-REPRESENTABILITY

G23's `0.85332` spike utility may arise from a partial operating point. It does
not prove that the frozen local residual can express the full constructive
sequence.

### CE-SUPERVISED-FIT-IS-NOT-AN-ALGORITHM

The source-side constructive controller may provide labels only to this
diagnostic. Passing the probe does not license oracle labels, source fields, or
supervised loss in the candidate algorithm.

### CE-POINTWISE-FIT-IS-NOT-CLOSED-LOOP-REALIZATION

Low MSE on constructive-manifold states can coexist with rollout drift through
the autoregressive prefix, hidden state, battery dynamics, or lifecycle edits.
The probe therefore records pointwise fit and deterministic closed-loop source
utility as separate first-match outcomes.

## Smallest diagnostic

`FROZEN_ANCHOR_LOCAL_RESIDUAL_EXPRESSIVITY_G25` uses the G23 local residual
representation through `FastAnchoredResidualPolicy` and the unchanged G18
source. It first trains the same immediate fast anchor for 100 updates with
eight environments and two PPO passes. It then freezes every anchor tensor and
optimizes only the zero-initialized local residual against source-side
`constructive_actions` labels.

The fixed dataset contains the 12 constructive trajectory states for each of
the three registered slot permutations (`36` state rows). The candidate policy
receives only generic observations, masks and its actor path; the source name,
critic fields and future state never enter the residual. The pointwise loss is
active-row action-space MSE with zero hidden state, matching the accepted G17
representation measurement. Training uses 200 Adam steps, learning rate
`1e-3`, batch size `36`, gradient clip `1.0`, and a fresh deterministic
minibatch stream. A deterministic closed-loop evaluation follows on all three
registered permutations.

Fresh seeds:

```text
model=3619000
action=3639000
minibatch=3659000
```

## Frozen gates and first-match outcomes

Operational validity requires the G18 information gate, all 36 finite source
rows, exact inactive targets/actions, finite residual-only updates, exact
anchor identity, a moved residual output layer, and the registered CPU
one-thread runtime.

Pointwise representation passes only when final MSE is at most `1e-3` and at
most `0.10` of initial MSE. Closed-loop realization then reuses the existing
G18 floors: utility at least `0.95`, gain over the fast anchor at least `0.10`,
spike utility at least `0.90`, and rotating-effort share at least `0.75`.

First match:

1. `INVALID_FROZEN_ANCHOR_RESIDUAL_EXPRESSIVITY_G25`;
2. `NO_POINTWISE_LOCAL_RESIDUAL_FIT_G25`;
3. `NO_CLOSED_LOOP_LOCAL_RESIDUAL_REALIZATION_G25`;
4. `PASS_FROZEN_ANCHOR_LOCAL_RESIDUAL_EXPRESSIVITY_G25`.

A pass isolates PPO credit/optimization as the next algorithmic boundary. A
pointwise failure retires the local residual representation. A pointwise pass
with closed-loop failure isolates sequential realization. No outcome consumes
a conclusion-bearing iteration or licenses formal/UAV execution.
