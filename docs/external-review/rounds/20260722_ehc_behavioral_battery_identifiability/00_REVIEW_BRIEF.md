# Focused Review Brief — EHC Behavioral-Battery Identifiability

## Purpose

This is a focused continuation of the already selected
`EVENT_HELD_COMMITMENT_LINK_G0` source. It does not reopen the wider portfolio,
authorize implementation or authorize compute. It asks whether the corrected
behavioral battery can distinguish learned event-held commitment from a useful
low-frequency representation with arbitrary or random renewal timing.

The concern was raised before any formal result existed. All formal attempts
were operationally aborted and provide no scientific evidence. The primary
mechanism-matched estimand
`G = U_EHC - U_DUM` remains unchanged and is not under challenge.

## Prior correction

The 2026-07-21 GPT-5.6 Pro response found the original battery insufficient:

- KEEP/RENEW rates were support checks, not learned-use evidence;
- physical lifetime `T` mixed learned decisions with exogenous opportunity gaps;
- `CV(T)` and physical-time bins could reward random timing and penalize crisp
  deterministic timing;
- `||W_z(z-z_perm)||` measured a parameter path, not an executable action-law
  consequence.

It proposed the minimal replacement now present in the implementation:

1. KEEP and RENEW minimum eligible counts are estimability checks only.
2. Opportunity-count lifetime support uses `K==1`, `K==2`, `K>=3` bins.
3. Primitive-action dependence uses same-state total variation under a
   lifecycle-stratified `z` derangement.
4. Natural KEEP and RENEW rows use exact-snapshot, common-random-number
   counterfactual continuations and require positive external-utility advantage
   for the action naturally selected by the policy.

## Focused ambiguity

The unresolved question is whether this replacement is actually identifying.
A random nondegenerate event head can still pass support and K-spread. Action TV
can be positive for a useful mark representation even when renewal timing is
arbitrary. The two natural counterfactual advantages are intended to close that
gap, but they must be audited for conditioning, selection, support, branch
semantics, utility attribution and whether both signs jointly establish learned
context-sensitive timing rather than representation-only value.

The tracked design document still displays the superseded physical-time and
logit-norm gates. Treat that as a repository inconsistency to be corrected only
after the scientific decision; audit the implemented replacement rather than
silently treating the stale prose as the active battery.

## Decision required

Determine which of these outcomes is justified before launch:

- `BATTERY_IDENTIFIABLE_AS_IMPLEMENTED`;
- `BATTERY_REQUIRES_MINIMAL_CORRECTION`, with the smallest exact correction;
- `BATTERY_CANNOT_IDENTIFY_COMMITMENT_UNDER_THIS_SOURCE`.

Preserve plural live explanations where evidence permits them. Select only one
next evidence action by information gain, cost and reversibility. One scheduled
action does not make other legal explanations illegal.

## Hard boundaries

- No formal result exists; aborted runs are operational evidence only.
- Do not change `G`, external reward, arms, budget, seeds or the mechanism-
  matched ordinary/capacity comparison.
- Do not convert support, entropy, label prediction or parameter magnitude into
  useful-skill evidence.
- Intrinsic reward remains environment-agnostic.
- Do not write an implementation plan or authorize implementation/compute.
- If a correction is needed, change the smallest refuted measurement unit and
  preserve every still-valid invariant.
