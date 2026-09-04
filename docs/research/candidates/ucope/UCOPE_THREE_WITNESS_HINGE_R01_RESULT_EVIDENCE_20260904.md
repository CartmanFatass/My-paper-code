# UCOPE-B-EXPLORE-THREE-WITNESS-HINGE-R01 — result evidence

- Direction: `ucope`
- Evidence class: **B/EXPLORE**
- Frozen card: `UCOPE_THREE_WITNESS_HINGE_R01_CARD_20260904.md`
- Launch SHA: `71f693ae1f1634e3e9c45461cc3c6d61c18394b8`
- Result root:
  `temp/directions/ucope/exp/three_witness_hinge_r01_20260904/`
- Summary: `summary.json`, format `UCOPE_THREE_WITNESS_HINGE_R01_SUMMARY_V1`, `complete=true`
- Published branch: **`TW-B — COVERAGE_CLOSES_TAIL_ONLY`**

## 1. Bounded result

On the six frozen policies and the reused offset-`2,000,000` rows, the oracle-signed
`THREE-WITNESS` tail reached the `19/20` held-out agreement gate in **6 of 6** policies. The live
same-data, same-information, equal-total-dose `DOSE-MATCHED-SINGLE` comparator reached it in **4 of
6**, and every comparator pass remained a treatment pass. This satisfies the card's `TW-B` branch.

The tail closure did **not** improve the full competence count: `C_even` remained **3 of 6 for both
arms**. In the two policies whose tail failures were repaired, the treatment instead made the root
pay at `LINKED-p17_20-c7_50`, where the oracle refuses because net acquisition is `-0.028563`.
Coverage therefore closed the observed tail obstruction beyond equal hinge dose and translated its
two residual failures into paired root false positives on this panel. It did not close competence.

Claim ceiling: a preliminary, deterministic six-policy mechanism observation about this
oracle-signed intervention on this draw. It is not stable superiority, a seed-population result, a
deployable training objective, paid-acquisition or COUNT/RAW polarity, or a generic UCOPE/MARL,
transfer, safety, flight, energy, or deployment claim.

## 2. Launch and engineering conformance

The card was committed and pushed as `fdc6068e3` before implementation. CM accepted the bounded
implementation at `71f693ae1`: 596 new research-code lines excluding tests, a 61-line runner,
orchestration below the 30-percent budget, and no engineering-scope §4 machinery. The focused
post-edit run was `13 passed in 4.03 s`; the independent pre-launch review found no material issue
and produced the permitted second and final focused run, `13 passed in 3.95 s`. No test was run a
third time.

The fresh central admission immediately before the detached launch records:

| field | observed |
| --- | ---: |
| captured / assessed | `2026-09-04T09:55:01.112362Z` / `09:55:01.146056Z` |
| physical available | `12,701,573,120` bytes |
| effective available | `12,701,573,120` bytes |
| required floor | `4,294,967,296` bytes |
| physical / effective / overall pass | `true / true / true` |

The operator accepted exactly one hidden detached process, PID `28892`, at
`2026-09-04T09:55:12.5270942Z`. It terminated after publishing exactly one complete summary at the
launch SHA; stdout contains the `TW-B` map and stderr is empty. The detached PowerShell process
object was not retained across commands, so its Windows exit code is unavailable. No second process
was started.

## 3. Frozen assignment and actual work

The arm order was comparator then treatment. Both arms used the same three named seeds, both folds,
40,960 episodes per context at offset `2,000,000`, odd training support `{1,3,5,7,9}`, even held-out
support `{2,4,6,8}`, FP32 AdamW, `lr=0.003`, batch 256, 1,600 tail updates, 3,200 root updates, and
one intra-op thread. Root targets were rebuilt from each arm's own learned tail.

| quantity | actual |
| --- | ---: |
| environment episodes / transitions | `983,040 / 4,915,200` |
| tail optimizer updates / example exposures | `19,200 / 4,915,200` |
| root optimizer updates / example exposures | `38,400 / 9,830,400` |
| exact policy evaluations | `144` |
| sampled evaluation episodes / transitions | `9,216 / 25,344` |
| nonfinite learner events | `0` |

Every required learner, update, and evaluation count is nonzero. The exact reference was evaluated
on each paired seed/fold and never entered either arm or the branch rule.

## 4. The deciding observations

The table reports `min_forced_PROBE_tail_agreement`; bold entries pass `>=0.95`.

| seed / fold | dose-matched single | three-witness | exact reference |
| --- | ---: | ---: | ---: |
| 00 / 0 | **1.000000** | **1.000000** | **1.000000** |
| 00 / 1 | 0.788446 | **1.000000** | 0.611559 |
| 01 / 0 | 0.788446 | **1.000000** | 0.611559 |
| 01 / 1 | **1.000000** | **1.000000** | **1.000000** |
| 02 / 0 | **1.000000** | **1.000000** | **1.000000** |
| 02 / 1 | **1.000000** | **1.000000** | 0.611559 |
| **pass count** | **4 / 6** | **6 / 6** | **3 / 6** |

The comparator pass set is a strict subset of the treatment pass set. Thus `N_T-N_C=2` and no
comparator pass regressed. Tripling the one-witness dose did not close the two directions: its
agreement flags are the same `[T,F,F,T,T,T]` as the accepted one-witness weight-1 predecessor on
these rows. Covering the missing directions did.

## 5. Witness and held-out direction measurements

At the final parameters every treatment witness row clears the frozen `0.024022` signed margin:

| treatment witness | minimum over all policies and training rows | final active rows |
| --- | ---: | ---: |
| `(1,5)` | `0.024701` | `0` |
| `(3,7)` | `0.031795` | `0` |
| `(5,9)` | `0.028142` | `0` |

The comparator's sole `(5,9)` witness has global minimum `0.029619` and zero active final rows.
Both arms therefore received enough final margin on what they constrained; the result is not a
failure of the dose-matched null to satisfy its own hinge.

Across all contexts, counts, and policies, the treatment's minimum oracle-signed held-out gaps are
positive on every direction: `(2,4) = 0.012351`, `(4,6) = 0.015897`, `(6,8) = 0.014071`. The
comparator has exactly the two localized failures the card targeted:

- seed 00 / fold 1: two negative `(2,4)` cells, minimum `-0.006196`;
- seed 01 / fold 0: two negative `(4,6)` cells, minimum `-0.003161`.

It has no other negative held-out direction cell. The three-witness treatment turns all four of
those cells positive and introduces no negative cell elsewhere. This is the direct mechanism-level
support for coverage rather than total dose.

## 6. Full competence and native root consequence

| arm | agreement gate | `C_root` | `C_even` |
| --- | ---: | ---: | ---: |
| `DOSE-MATCHED-SINGLE` | `4/6` | `5/6` | `3/6` |
| `THREE-WITNESS` | `6/6` | `3/6` | `3/6` |
| exact reference | `3/6` | `6/6` | `3/6` |

The two repaired tail policies expose a matched downstream tradeoff:

| policy | comparator | three-witness | native consequence |
| --- | --- | --- | --- |
| 00 / 1 | tail fail; oracle root; regret `0` | tail pass; extra PROBE at `LINKED-p17_20-c7_50`; regret `0.028562899` | buys information where its net value is negative |
| 01 / 0 | tail fail; oracle root; regret `0` | tail pass; extra PROBE at `LINKED-p17_20-c7_50`; regret `0.028562899` | same false-positive root action |

Seed 02 / fold 1 remains the chain's other root residual in both live arms: it refuses the unique
profitable target `LINKED-p17_20-c9_100`, with regret `0.021437101`. Hence the treatment has three
root failures and three `C_even` failures, while the comparator has two tail failures plus that one
root failure. The exact reference has the oracle root vector in all six policies but tail agreement
in only three, showing that the finite-row least-squares optimum itself does not close this tail
criterion on the draw.

Direct observation: the only paired arm change is the distribution of equal total hinge dose, and
the root targets are native consequences of each learned tail. Inference boundary: the summary does
not evaluate the exact root optimum induced by each learned tail, so it cannot separate shifted
root targets from residual root optimization as the cause of the two false positives.

## 7. Fit cost and exposure

The tail training-MSE ratio to each policy's own exact solve is small in both arms:

| arm | min / median / max ratio | tail clipping | root clipping |
| --- | --- | ---: | ---: |
| dose-matched single | `1.000375 / 1.002974 / 1.005250` | `878 / 9,600` | `1,046 / 19,200` |
| three-witness | `1.000392 / 1.001560 / 1.004150` | `847 / 9,600` | `1,045 / 19,200` |

The treatment therefore did not buy coverage through a gross deterioration of training fit. Its
maximum excess ratio is lower than the comparator's, although that does not make it a better value
estimator.

Machine-generated exposure, maximum absolute raw-coordinate move and L2 displacement relative to
initial L2 scale:

| arm / stage | move min / median / max | displacement/initial min / median / max |
| --- | --- | --- |
| dose / tail | `1.425719 / 1.864066 / 2.150794` | `1.085299 / 1.954651 / 2.593696` |
| dose / root | `0.902591 / 1.145171 / 1.808278` | `1.062975 / 1.443512 / 1.870757` |
| three / tail | `1.439629 / 1.883676 / 2.122606` | `1.094598 / 1.914543 / 2.579949` |
| three / root | `0.902564 / 1.145185 / 1.808285` | `1.062623 / 1.454748 / 1.884986` |

Every optimized row moved nonzero. The learner could move in its budget; lack of exposure cannot
explain a nonpass.

## 8. Cost and resource record

The runner's carded projection was `185.481 s` per arm against a `600 s` per-arm cap. Charging the
full `45.162 s` shared generation to each arm, measured charged wall was `62.506 s` for the
comparator and `62.641 s` for the treatment, both below the cap. Total summary wall was
`84.843 s`.

Peak RSS capture returned `null`, so the result is marked **`resources_unmeasured`**. Under the
owner's telemetry rule this does not annul a non-resource claim. Admission, learner measurements,
counts, and scientific observables are complete.

## 9. Frozen rule applied verbatim

The first card branch asks:

> `TW-A`: `N_T=6`, `N_C<6`, and `THREE-WITNESS C_even=6/6`.

The first two terms hold (`6`, `4`), but `C_even=3/6`, so `TW-A` is false.

The second asks:

> `TW-B`: `N_T=6`, `N_C<6`, and `THREE-WITNESS C_even<6/6`.

All terms hold: `6=6`, `4<6`, and `3<6`. Therefore the published branch is
**`TW-B — COVERAGE_CLOSES_TAIL_ONLY`**. Later branches are not reached.

## 10. Predictions on record

The DM predicted `TW-B`, `N_T=6`, `N_C=4`, and treatment `C_even` at 4 or 5 of 6. The branch and both
agreement counts are borne out exactly. The competence-level prediction is not: observed `C_even`
is 3 of 6 because both repaired tail policies become root false positives. The mechanism prediction
was right and the downstream-cost prediction was too optimistic.

Owner prediction: `not taken (unattended)`.

## 11. Deviations, limits, and validity

Deviations from the frozen scientific assignment: **none identified**. The arms, signs, margin,
weights, draw, order, learner, seeds, folds, updates, precision, evaluator, rule, projection, and
single-invocation stop all match the card.

Recorded execution limitations:

1. Peak RSS is unmeasured; wall time is measured. This is a telemetry downgrade, not a scientific
   invalidity.
2. The detached process exit code is unavailable after termination. The complete launch-SHA-bound
   summary, one stdout branch record, empty stderr, and absence of a second launch are directly
   observed; no claim depends on the process exit code.
3. The draw was deliberately reused to isolate the observed residual. A fresh draw, other seeds,
   another host, other margins/weights, and a non-oracle-signed objective were not run.
4. This is one machine and one invocation. B/EXPLORE has no consumption state and no reproduction
   claim.
5. Paid acquisition and COUNT/RAW were not evaluated. Their locks and recorded PA-B status are
   unchanged.

The result is a valid complete B/EXPLORE observation. A negative or tradeoff closes at most this
oracle-signed intervention on this observed draw; it does not close the mechanism family or
direction.
