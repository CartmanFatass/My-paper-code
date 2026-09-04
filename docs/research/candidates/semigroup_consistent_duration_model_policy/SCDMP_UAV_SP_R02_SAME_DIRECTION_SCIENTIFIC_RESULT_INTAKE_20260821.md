# SCDMP UAV suspended-payload order-value r02 scientific result intake

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-UAV-SUSPENDED-PAYLOAD-ORDER-VALUE
revision=SCDMP-UAV-SP-ORDER-VALUE-SCIENCE-20260820-02
owner=EM_semigroup_consistent_duration_model_policy
result_object=SCDMP-UAV-SP-R02-FULL-EMPIRICAL-PANEL
technical_acceptance=complete_atomic_panel
scientific_activity_started=true
question_relevant_output_produced=true
selected_branch=DIRECT-UAV-ORDER-VALUE-NONIDENTIFIED
provisional_before_result_convergence=true
```

## Exact accepted result

The named same-direction CM returned one technically accepted complete atomic
result:

`artifacts/scdmp_uav_sp_r02_full_empirical_20260821/SCDMP_UAV_SP_R02_RESULT.json`.

Its SHA-256 is
`fcf93d1483db443c0b933cfc758d351c49ddc5ab7276af15ae9ca95c26da90a8`.
The result contains all 18 replicate packets and the exact four-controller,
six-regime and support inventories after technical acceptance of all 54 learned
checkpoints. Its stored complete inference equals independent recomputation,
all registered values are finite, `complete_atomic_panel=true`, and
`partial_inspection_permitted=false`. No scientific value was inspected before
the complete technical packet was accepted.

## Validity, task support and action sensitivity

The registered evidence-validity predicate is true and has no invalid reason.
All three support/action qualifications pass their simultaneous one-sided
family:

| Qualification | Mean | Adjusted lower bound | Threshold | State |
| --- | ---: | ---: | ---: | --- |
| `Q_order` | `1.0000000000` | `1.0000000000` | `0.20` | `PASS` |
| `D_order` | `0.2206033069` | `0.2202376044` | `0.05` | `PASS` |
| `D_action` | `1.4348878543` | `1.4347436640` | `0.10` | `PASS` |

Thus the frozen oracle panel establishes order opportunity and action
sensitivity inside this exact simulator/task. It does not by itself establish
that any learned arm was competent or used the order distinction beneficially.

## Learned-controller competence

No learned controller meets the frozen conjunction of all four trained-period
event-order cells plus the pooled threshold. The adjusted competence results
are:

| Controller | Cell | Mean safe delivery | Adjusted lower bound | State |
| --- | --- | ---: | ---: | --- |
| `TREAT` | fixed-4/RG | `0.0000000000` | `0.0000000000` | `UNRESOLVED` |
| `TREAT` | fixed-4/GR | `0.8333333333` | `0.5541702875` | `UNRESOLVED` |
| `TREAT` | fixed-10/RG | `0.0000000000` | `0.0000000000` | `UNRESOLVED` |
| `TREAT` | fixed-10/GR | `0.8888888889` | `0.6534779386` | `PASS` |
| `TREAT` | pooled | `0.4305555556` | `0.3087822869` | `UNRESOLVED` |
| `FREE` | fixed-4/RG | `0.0000000000` | `0.0000000000` | `UNRESOLVED` |
| `FREE` | fixed-4/GR | `0.7777777778` | `0.4663583627` | `UNRESOLVED` |
| `FREE` | fixed-10/RG | `0.0000000000` | `0.0000000000` | `UNRESOLVED` |
| `FREE` | fixed-10/GR | `0.7777777778` | `0.4663583627` | `UNRESOLVED` |
| `FREE` | pooled | `0.3888888889` | `0.2331791813` | `UNRESOLVED` |
| `SET` | fixed-4/RG | `0.0000000000` | `0.0000000000` | `UNRESOLVED` |
| `SET` | fixed-4/GR | `0.8333333333` | `0.5541702875` | `UNRESOLVED` |
| `SET` | fixed-10/RG | `0.0000000000` | `0.0000000000` | `UNRESOLVED` |
| `SET` | fixed-10/GR | `0.8333333333` | `0.5541702875` | `UNRESOLVED` |
| `SET` | pooled | `0.4166666667` | `0.2770851437` | `UNRESOLVED` |

The cell threshold is `0.58` and the pooled threshold is `0.70`, both strict.
Every controller therefore has controller state `UNRESOLVED`. In particular,
all three learned arms have identically zero safe delivery in both registered
RG competence cells. That common failure prevents attribution of the observed
pattern specifically to treatment chronology or its restricted
parameterization.

## Direct mission comparisons

The registered simultaneous direct-family results are:

| Contrast | Mean | Adjusted interval | Registered state |
| --- | ---: | --- | --- |
| `P_T-P_FREE` | `0.0416666667` | `[-0.1028330488,0.1861663822]` | superiority `UNRESOLVED` |
| `P_T-P_REVERSED` | `0.0138888889` | `[-0.0342776829,0.0620554607]` | superiority `UNRESOLVED` |
| `P_T-P_SET` | `0.0138888889` | `[-0.1644307751,0.1922085529]` | superiority `UNRESOLVED` |
| `W_T-W_FREE` | `0.0277777778` | `[-0.1423163056,0.1978718611]` | superiority `UNRESOLVED` |
| `W_T-W_REVERSED` | `0.0000000000` | `[0.0000000000,0.0000000000]` | superiority `FAIL` |
| `W_T-W_SET` | `0.0000000000` | `[-0.1982519741,0.1982519741]` | superiority `UNRESOLVED` |
| `T_T-T_FREE` | `-0.1778819444` | `[-0.7948638988,0.4391000100]` | non-harm `PASS` |
| `E_T-E_FREE` | `0.0208120913` | `[-0.0514681312,0.0930923138]` | non-harm `UNRESOLVED` |

Each of the nine registered cable-overload, swing-envelope and formation-loss
contrasts is exactly zero with interval `[0,0]`, so all nine physical non-harm
requirements pass. The `P` route's `W` noninferiority to `FREE` and the `W`
route's `P` noninferiority to `FREE` are each unresolved. Consequently:

```text
P route = UNRESOLVED
W route = EXCLUDED
```

The `W` route is excluded by the exact failure of superiority over the tied
`REVERSED` control. The `P` route is not excluded; its superiority and
noninferiority intervals, competence qualifications and energy non-harm remain
unresolved.

## Frozen first-true interpretation

The registered first-true map applies exactly:

1. `INVALID-EVIDENCE` is false because the complete atomic evidence is valid;
2. `RETAIN-TAUT-GUST-RISK-TILT` is false because neither route passes;
3. `DECLINE-TAUT-GUST-RISK-TILT` is false because both routes are not excluded
   and the mandatory `FREE` and `SET` competence qualifications do not pass;
4. `DIRECT-UAV-ORDER-VALUE-NONIDENTIFIED` therefore controls.

The provisional direction-local conclusion is:

> In the exact finite `TRI-UAV-SLING-CORRIDOR-36M-v1` panel, the oracle task
> law showed strong order opportunity and action sensitivity, but none of the
> three learned arms established the required competence across event orders.
> The `P` value route remained unresolved and the `W` route was excluded by no
> advantage over tied reversal. The exact `TAUT-GUST-RISK-TILT` package is
> therefore neither retained nor declined: direct UAV order value remains
> nonidentified under the frozen branch law.

This is not evidence that event order is irrelevant: the oracle qualifications
pass decisively. It is also not evidence that the treatment works: no positive
route passes and the competent-comparator precondition is absent.

## Strongest alternatives and claim ceiling

The strongest live alternative is common non-establishment of registered
competence on the RG condition, because `TREAT`, the strictly containing
`FREE-DIRECT`, and `SET-FREE` all have zero safe delivery in both RG competence
cells. This is an unresolved learned-controller pattern, not a failed task-law
qualification: the separate order-support and action-sensitivity families pass.
Finite-budget PPO/AdamW behavior, initialization and optimizer geometry,
reward/risk-surrogate choice, centralized credit and inner stabilization,
numeric-`k` conditioning, post-action damage feedback, the binary last-event
bit, and the simulator-specific cable/damper abstraction remain live and are
not separated by this panel. The exact zero `W` advantage over `REVERSED`
constrains the robustness route but does not isolate which alternative caused
the common competence non-establishment or resolve the `P` route.

The maximum supported result claim is only:

> For the exact planar fixed-three-UAV task, frozen finite training package,
> eighteen paired replicates and registered simultaneous families, the oracle
> panel established task order opportunity and action sensitivity, while all
> three learned arms failed to establish the required across-order competence;
> the treatment's performance route was unresolved and its worst-regime route
> was excluded by no advantage over tied reversal. The controlling result was
> `DIRECT-UAV-ORDER-VALUE-NONIDENTIFIED`.

No positive treatment-value, chronology-use, unique-mechanism, arbitrary-event,
arbitrary-`k`, variable-`N`, other-payload, other-simulator, six-degree-of-
freedom, real-aircraft, safety, deployment or flight claim follows. The exact
zeros in registered harm differences are only comparative facts in this panel,
not evidence of real-world safety. This nonidentified result concerns only the
exact object and does not delete the SCDMP family.

## Next owner and authority boundary

The existing SCDMP ChatGPT Pro conversation must receive one exact result-
convergence request on this complete technically accepted result. Until that
natural response is intaken, this interpretation is provisional.

No source, rerun, new seed, threshold, budget, coordinate, treatment repair,
architecture menu, relation assay, Stage B, second surface, deployment or
flight activity is authorized. The frozen branch opens no in-envelope
scientific successor. After result convergence, Operational Root and the
dedicated Portfolio owner decide whether this exact nonidentified result changes
investment; the EM makes no cross-direction decision.
