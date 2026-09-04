# CRTO B1 v4 preactivity hazard-encoding correction

```text
direction=commitment_residual_triggered_options
owner=EM_commitment_residual_triggered_options
superseded_revision=CRTO-B1-SCIENCE-20260812-03
prospective_revision=CRTO-B1-SCIENCE-20260812-04
scientific_activity_started=false
question_relevant_output_exists=false
correction_kind=science_bearing_hazard_hypothesis_class_definition
mathematical_closure=pending_same_conversation_Pro_CLOSED_and_EM_intake
production_authorized=false
```

## Conclusion

The CM-relayed ambiguity is science-bearing and cannot be filled by
implementation discretion. V3 froze a penalized logistic residual-free hazard
with `regime one-hot, and switch direction/phase` but left direction/phase
coordinates undefined. Scalar, categorical, binned, interacted, centered, and
unscaled encodings define different L2-penalized function classes and can change
hazard actions, scored rate balance, `Delta_rate`, and the mechanism branch.

No learned-policy optimizer update or question-relevant output occurred, so v4
prospectively supersedes v3 rather than retrofitting an active treatment. The
landed scalar guess `0=fixed,-1=pre-switch,+1=post-switch` is not evidence and is
not part of v4. CM must not patch or run v3. The complete v4 card, handoff,
provider requesters, and result-blind interpretation map are synchronized and
await same-conversation Pro closure.

## Exact correction packet

The hazard's added temporal/context block is exactly:

```text
regime[4] = one_hot(
  [K8_FIXED,K16_FIXED,SWITCH_4_TO_16,SWITCH_16_TO_4])

direction[3] = one_hot(
  [NO_SWITCH,FOUR_TO_SIXTEEN,SIXTEEN_TO_FOUR])

phase[7] = one_hot(
  [FIXED,PRE_9PLUS,PRE_1_TO_8,AT_SWITCH,
   POST_1_TO_8,POST_9PLUS,FAR_POST])
```

For fixed regimes, direction/phase are always `NO_SWITCH/FIXED`. For a switch
regime define `delta=t-128` at each predecision legal review and bin it as:

```text
delta <= -9     -> PRE_9PLUS
-8 <= delta<=-1 -> PRE_1_TO_8
delta == 0      -> AT_SWITCH
1 <= delta <= 8 -> POST_1_TO_8
9 <= delta<=64  -> POST_9PLUS
delta >= 65     -> FAR_POST.
```

The `t=128` row enters the binary hazard fit only when the existing v4 action
law supplies a legal discretionary review with `KEEP`; its locked CRTO label is
q-only because `b=0`. Immediate forced renewal, no-review, or no-KEEP boundaries
are excluded from fit and support counts.

All fourteen new coordinates remain literal uncentered/unscaled `0/1`. Only
`K/16`, `age/16`, `age/K`, and `cost/4` are centered/unit-scaled over the complete
four-regime hazard-development panel, using scale one for a zero standard
deviation. The model is additive only: no products, interactions, splines,
polynomials, embeddings, reference dropping, or ordinal scalar replacements.
The intercept is unpenalized; every feature slope, including every full-one-hot
slope, receives the existing `1e-3/2` L2 penalty. The penalized deterministic fit
therefore selects the minimum-norm slopes despite full-block collinearity.

## Claim and experiment impact

The correction changes only the previously underdetermined residual-free hazard
hypothesis class, its generated actions, and whether `Delta_rate` can exclude
the registered replanning-exposure alternative. It does not change the physical
DGP; learned CRTO/FULL arms; predictor; calibration; derangement; Q-only or
forced-renewal cuts; evaluation panels; primary utility/robustness estimands;
statistical margins; resource ledger; strongest alternative; claim ceiling; or
warehouse/UAV activation law.

Until v4 receives same-conversation Pro `CLOSED` and EM intake, no prospective
production treatment is mathematically closed. V3's prior closure remains a true
historical disposition of exact v3 but cannot authorize v4 or a guessed hazard
encoding. No result or claim transfers from the preactivity implementation
attempt.

## Exact Root relay

> Treat `CRTO-B1-SCIENCE-20260812-04` as the sole prospective production object.
> Its only v3-to-v4 science delta is the exact 4+3+7 categorical additive hazard
> feature law above, including phase bins, switch-instant eligibility, literal
> binary scaling, full L2 slopes, and no interactions. The scalar
> `0/-1/+1` guess is non-operative. Primary CRTO/FULL science and the 10,715,136-
> step ledger are unchanged, but `Delta_rate` is unavailable under v3 because its
> control was underdefined. Publish the complete owner artifacts, then return the
> exact v4 composite to existing Pro conversation
> `6a7cc6cb-c210-83e8-8d51-0bb7c64ced53` for `CLOSED|REVISION_REQUIRED`. Do not
> release CM construction or production until literal `CLOSED` plus EM intake.
