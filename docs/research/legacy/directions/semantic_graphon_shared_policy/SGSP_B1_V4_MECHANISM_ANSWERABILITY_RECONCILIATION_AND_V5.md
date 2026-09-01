# SGSP B1 revision-04 mechanism-answerability reconciliation and revision 05

```text
direction=semantic_graphon_shared_policy
superseded_revision=SGSP-B1-SCIENCE-20260813-04
successor_revision=SGSP-B1-SCIENCE-20260813-05
trigger=revision_04_same_conversation_Pro_REVISION_REQUIRED
scientific_activity_started=false
science_bearing_change=true
new_arm=false
new_stochastic_object=false
new_endpoint=false
new_threshold=false
new_compute=false
```

## Decision

The Pro defects are correct and decision-changing. Revision 04 could route an
impossible mechanism pass to its mechanism-failure branch because its support
flags did not use the same `min_N`-within-seed aggregation as the registered
mechanism estimands. This is not safely handled by the existing claim ceiling:
it changes whether observed nonattenuation/action-insensitivity may be stated.
The smallest complete correction is revision 05.

## Frozen replacements

For each seed, with held-out `N={6,16}` and regime `OPPOSED`, define

```text
R_CAP_s = min_N [Rbar_s^{SGSP,intact}(N) - L_s(N)]
TV_CAP_s = min_N Vmax_s(N)
```

and freeze

```text
CUT_RETURN_DROP_AVAILABLE iff mean_s R_CAP_s > 0.075
CUT_ACTION_TV_AVAILABLE iff mean_s TV_CAP_s > 0.10.
```

For `B in {EDGE,ALT}`, define

```text
d_s^{GB}(N) = Rbar_s^{SGSP,intact}(N) - Rbar_s^{B,intact}(N)
I_CAP_s^{GB}(N) = d_s^{GB}(N) + U_s(N) - L_s(N)
```

and freeze

```text
GE_ATTENUATION_AVAILABLE iff mean_s min_N I_CAP_s^{GE}(N) > 0.015
GA_ATTENUATION_AVAILABLE iff mean_s min_N I_CAP_s^{GA}(N) > 0.015.
```

These are arithmetic support/headroom checks, not efficacy confidence bounds.
They use only already registered seed packets, intact returns, action tapes, and
support envelopes. Sender reassociation and center swap share the return/TV
flags because both preserve the same epsilon-soft legal support. The two
attenuation flags remain family-specific.

## Branch consequences

Promotion requires both matched two-sided flags, anonymous-positive
availability, both common cut flags, both attenuation flags, both SGSP-material
direct labels, `SGSP_BEATS_ANON`, and all six observed mechanism bounds.

The narrower mechanism-failure branch requires both matched two-sided flags,
both common cut flags, both attenuation flags, and both SGSP-material direct
labels before an observed mechanism-bound failure can be interpreted. It still
does not require `ANON_POSITIVE_AVAILABLE`, because it remains a matched-
comparator mechanism reading rather than an anonymous-compression claim.

If a required mechanism flag is unavailable, the affected gate is saturated
or unanswerable. It cannot authorize equivalence, family deletion, observed
nonattenuation, or mechanism failure. Earlier independently identifying direct
adverse or interaction branches retain their own predicates; otherwise the
packet reaches failed availability or bounded nonidentification.

## Retained object and ceiling

Revision 05 changes no treatment, comparator, control, action, intervention,
estimand, margin, confidence law, multiplicity law, seed, world, checkpoint,
counter address, optimizer, work/communication budget, activity boundary,
second surface, or UAV mapping. It retains revision 04's maximum claim exactly:
correct-center finite-budget value relative only to the registered wider edge
family and one opposite-association equal-width center on the frozen finite
toy, with both action-sensitive mechanism families passing. Other centers,
target-table alignment, cell-specific conditioning, arbitrary `N`/topology,
graph mismatch, churn, continuous geometry, and UAV efficacy remain excluded.
