# EOCIV-A1 headroom-reference inventory — result evidence

- Object: `EOCIV-A1-HEADROOM-REFERENCE-INVENTORY-R01`
- Direction: `eociv_lite`
- Evidence class / claim ceiling: **A/RECON**, presence or absence of a matched headroom pair in
  the committed EOCIV evidence only
- Status: `VALID_COMPLETE_READ_ONLY`
- Result branch: **`A1-GENERIC-COMPARATOR-WIN-WITHOUT-UPPER`**
- Observation date: 2026-09-04

## 1. Activity, integrity and receipts

The inventory read eleven object records: B1--B7, A8, B9, B9R1 and B10. Every named tracked
source was readable. Required cited endpoints were finite. B7 and A8 retained their recorded
invalid/unidentified terminals; B9 retained its zero-activity invalid terminal. They were not
silently promoted to scientific results.

A1 created zero environment episodes, transitions, policy calls, learner/trainer/optimiser calls,
model initialisations, stochastic draws, checkpoints or result roots. It invoked no scientific
runner and therefore has no resource-admission, process or publication receipt. The evidence is
the cited committed source set plus this read-only classification. No historical artifact was
rewritten.

## 2. Inventory

| record | frozen comparison and direct observation | qualifying tuned generic baseline | matched same-information native-return upper reference | raw `H = Y_upper - Y_generic` |
| --- | --- | --- | --- | --- |
| B1 real valve | Learned-versus-exact-rate control difference-in-differences `tau_B1 = -0.000007465733177634326`; the control side exceeds the learned side by `0.000007465733177634326` on that estimand. | The fixed exact-rate control is a within-object generic comparator candidate. | **No.** No feasible/exact upper-return arm is present on the B1 panel. | **not identified** |
| B2 payload representation | Overall RAW minus content-separating is `+0.0369146054446664` for CORRECT-minus-SWAPPED and `+0.0242169758361389` for CORRECT-minus-NATIVE_NEUTRAL. RAW is not a tuned upper reference, and the representation intervention changes the representation path. | No prospectively tuned generic endpoint paired to an upper reference. | **No.** The result explicitly reports no untrained three-arm outcome baseline, and no exact/native upper. | **not identified** |
| B3 reward credit | `MC_RETURN` versus `GAE_NORM`; GAE's paired change was larger in 8/9 cells, but both are learned credit estimators. | No generic baseline meeting the pair rule. | **No.** Neither estimator is an upper reference. | **not identified** |
| B4 retention | `EPHEMERAL_RNN` versus `SEGMENT_LATCH_RNN`; heterogeneous paired semantic changes. | No tuned generic paired endpoint. | **No.** Neither retention condition is an upper reference. | **not identified** |
| B5 shock balance | `IID_SHOCK_BLOCK` versus `BALANCED_SHOCK_BLOCK`; balancing did not improve registered SNR or semantic consistency. | No tuned generic paired endpoint. | **No.** Training-schedule conditions are not return upper references. | **not identified** |
| B6 clip/root cross | `JOINT_GLOBAL_CLIP` versus `ACTOR_ANCHORED_CRITIC_CLIP`; branch `UNIDENTIFIED`, with no stable dominance. | No tuned generic paired endpoint. | **No.** Both are adaptive learner treatments. | **not identified** |
| B7 | Terminal `B7_INVALID_OR_UNIDENTIFIED` after the exact-fidelity witness failed. | none | none | unavailable; invalid attempt |
| A8 | Source-only audit, terminal `A8_INVALID_SOURCE_OR_ACTIVITY_CONTRACT`, zero return activity. | none | none | unavailable; no return observation |
| B9 | Zero-activity invalid terminal; no scientific result. | none | none | unavailable; invalid attempt |
| B9R1 | Receiver `R`, authenticated-source `S`, and unchanged `theta_0` on one matched panel. Global `Delta_R=-0.00019334158620836717`; anchor-over-receiver semantic contrast is therefore `0.00019334158620836717`. Global `R-v0=-0.00039827717195504791`; anchor-over-receiver CORRECT difference is `0.00039827717195504791`. The recorded generic gain is itself negative (`-0.00030160637885086404`); the disjunctive branch name does not show a generic-gain win. | The source control is same-information but not a tuned generic optimum; the unchanged endpoint is a baseline, not a tuned upper. | **No.** The `0.006814690014960328` value is an Adam L2 displacement bound, not a return reference. | **not identified**; neither `-Delta_R` nor `-(R-v0)` is `H` |
| B10 | Same frozen trajectories/tensor with receiver/source gradients, unchanged endpoint and `m=1,4,16`. At `m=16`, global `Delta_R=-0.0022498171590474747`, so anchor-over-receiver semantic contrast is `0.0022498171590474747`; `R16-v0=-0.006511830807355812`, so anchor-over-receiver CORRECT difference is `0.006511830807355812`. Positive `J_16=0.0049095035863372955` and `R16-vS=0.00179746069486719` coexist with source harm `S16-v0=-0.008309291502223003`. | The source branch is a same-information control and the unchanged endpoint is a baseline; neither is a prospectively tuned generic upper. | **No.** The `0.006814690014960328*m` triangle is a parameter-displacement bound, not a native-return upper reference. | **not identified**; negative `Delta_R` records treatment loss to the anchor only |

The records use different populations, seeds, histories, interventions and sometimes return
coordinates. None can supply a missing upper endpoint for another record. No cross-object
subtraction is admissible.

## 3. Raw gap and the exact missing terms

For the requested headroom estimand,

```text
Y_upper          = MISSING in every qualified same-host/same-information pair
Y_tuned_generic  = not paired with any Y_upper on the same frozen return coordinate
H                = Y_upper - Y_tuned_generic = NOT IDENTIFIED
```

The missing evidence is not a confidence interval or a larger learner budget. It is the absence of
a prospectively specified, feasible same-information upper-return reference evaluated beside a
competent tuned generic baseline on one identical host population and native-return coordinate.

The strongest raw relative gaps that must remain separate are:

- B1 control-over-learned difference-in-differences: `+0.000007465733177634326`;
- B9R1 unchanged-anchor over receiver semantic contrast: `+0.00019334158620836717`;
- B9R1 unchanged-anchor over receiver CORRECT difference: `+0.00039827717195504791`;
- B10 `m=16` unchanged-anchor over receiver semantic contrast: `+0.0022498171590474747`; and
- B10 `m=16` unchanged-anchor over receiver CORRECT difference: `+0.006511830807355812`.

These are comparator/treatment gaps. None is a distance from the generic baseline to a feasible
upper return.

## 4. Frozen rule applied verbatim

1. `A1-INVENTORY-INCOMPLETE` does not apply: all named records were readable and assignable from
   their own cards/results; invalid historical attempts stayed invalid.
2. `A1-MATCHED-HEADROOM-IDENTIFIED` does not apply: no record contains a qualified numeric
   `(Y_upper, Y_generic)` pair.
3. `A1-GENERIC-COMPARATOR-WIN-WITHOUT-UPPER` applies: B1 directly records the exact-rate generic
   control side above the learned side on its frozen difference-in-differences, B2 records RAW
   means above the content-separating means on both overall native contrasts, and B9R1/B10 record
   unchanged-baseline wins over receiver treatment on their global endpoints, while every
   qualifying native-return upper reference is absent.
4. Branch 4 is therefore not reached.

## 5. Bounded reading

Direct observation: current EOCIV evidence contains several treatment-versus-control or
treatment-versus-anchor losses, but no matched upper-reference-minus-tuned-generic headroom value.

Inference bounded by that observation: the negative B9R1/B10 `Delta_R` values cannot distinguish
host saturation from unused achievable value. B10 still validly says that its frozen fixed-vector
exposure range did not rescue receiver-addressed credit; A1 adds only that this negative result is
not a headroom measurement.

Strongest support for a generic/control explanation is the repeated absence of robust treatment
benefit and the direct B1/B2/baseline wins above. Strongest contradiction to any saturation claim
is the total absence of a qualified return upper reference. The surviving alternatives are an
already-saturated host, unused headroom inaccessible to these treatments, and comparator-specific
harm. A1 cannot choose among them.

There is no MEI, materiality threshold, lifecycle inference, Portfolio change, B authorization or
Transport action.

## 6. Evidence references

- Science card: `docs/research/candidates/eociv_lite/EOCIV_A1_HEADROOM_REFERENCE_INVENTORY_SCIENCE_CARD_20260904.md`
- B1--B6 public result JSON and adjacent code/science indexes in this direction directory
- `docs/research/candidates/eociv_lite/EOCIV_B7_ONE_STEP_ROOT_PARTITION_FROZEN_HISTORY_RESULT.json`
- `docs/research/candidates/eociv_lite/EOCIV_A8_EXACT_DYADIC_LEDGER_IDENTIFIABILITY_PROOF_RESULT.json`
- `docs/research/candidates/eociv_lite/EOCIV_B9_RECEIVER_ADDRESSED_CREDIT_EDGE_RESULT.json`
- `docs/research/candidates/eociv_lite/EOCIV_B9R1_RECEIVER_ADDRESSED_CREDIT_RESULT_EVIDENCE_20260904.md`
- `docs/research/candidates/eociv_lite/EOCIV_B10_RECEIVER_CREDIT_FROZEN_SCORE_EXPOSURE_CURVE_RESULT_EVIDENCE_20260904.md`
