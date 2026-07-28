# Scientific convergence ruling — D7.S normalizer autopsy plan

**Stage reviewed:** `f1d79b17334e485708e4a457701c808605a08c7b`

## 1. CONVERGENCE_DECISION

# **APPROVED WITH MODIFICATIONS**

The next scientific action remains the proposed **artifact-only normalizer-identifiability autopsy**. It may run locally against the byte-unchanged pooled artifact. There is no authorization for:

* a new environment run;
* expansion topologies;
* additional continuation replicates;
* a changed threshold;
* or a reinterpretation of R3 as an identified source-necessity result.

This is the appropriate next action because accepted-evidence reanalysis is cheaper and more reversible than another experiment, and the prior disposition specifically selected an artifact-only autopsy rather than more power.

The plan must incorporate six modifications.

### Modification 1 — name the output correctly

The autopsy analyzes:

> **the scalar quantities recorded by the executed R3 code**, conditional on the correctness of that execution path.

It is not itself a second validation of the environment trajectories. The output should consistently use wording such as:

```text
artifact-derived B_stable
artifact-derived B_flex
artifact-derived U*_stable
artifact-derived U*_flex
```

rather than laundering the reanalysis into a new source-level result.

### Modification 2 — add an input-and-semantics sentinel

Before emitting any autopsy statistic, the new script must fail closed unless it verifies:

1. the input artifact hash;
2. contract ID and procedure version;
3. the exact initial topology set `20260726–20260733`;
4. `smoke=False`;
5. the four expected `topology_units` collections;
6. exact reproduction of all six registered R3 bounds to the frozen numerical tolerance already demonstrated manually.

The plan’s manual reproduction to better than (10^{-12}) is strong evidence that the mapping is correct, but it must become an executable precondition of the autopsy rather than remain an external assertion. The current artifact’s recorded bounds are the reference values.

### Modification 3 — preserve the actual bootstrap factorization

The four standalone distributions should use the registered outer topology resampling stream. Within a selected topology, however:

* calibration episodes for (B_m);
* and audit events for (U_m^*)

must still be resampled independently, because they are disjoint data blocks.

“Shared resampling” means that the same topology indices are used across primary quantities. It does **not** mean forcing the calibration and audit blocks to use the same within-topology draws. The frozen design explicitly requires common topology resampling while independently resampling calibration episodes and audit events.

### Modification 4 — treat the explanation set as overlapping

N1, N2, N4, and the additional explanation introduced below are not mutually exclusive. The script should emit an **evidence vector**, not select a winning cause.

For example, it is entirely possible that:

* (B_m) changes sign across topologies;
* (U_m^*) points opposite to the original proposition;
* and the two quantities are poorly aligned because the normalizer comparator measures a different causal object.

### Modification 5 — N4 may establish heterogeneity, not “reproducible regimes”

With only eight already-observed topologies and no permitted expansion, the autopsy may establish that between-topology variation is large relative to within-topology uncertainty. It cannot, without a pre-existing partition and independent validation data, establish reproducible topology regimes.

Any grouping by BS quadrant, coordinate pattern, charging-station geometry, or a post hoc cluster is exploratory. It may generate an R4 hypothesis but cannot close N4 as a discovered regime.

### Modification 6 — the autopsy may nominate, but not silently freeze, R4

The output may recommend:

* a treatment-independent positive scale;
* an absolute task-unit materiality threshold;
* a redefined source control with analytically ordered semantics;
* or retirement of S7-S3 as this proposition’s carrier.

The final R4 freeze or carrier retirement remains a scientific disposition at the next review boundary. The script itself does not decide it.

Subject to these changes, the plan has converged and may be implemented.

---

## 2. VERDICT_N3

# **Select option 3, with option 1 as the mandatory historical report**

No new environment run is authorized.

For this artifact:

```text
N3 = UNDISCRIMINATED_FROM_STORED_ARTIFACT
```

The pooled artifact preserves scalar continuation totals in `topology_units`, but not the QoS, return-cost, cutoff, depletion, or nondegeneracy records needed to decompose those totals.

The production path computes a `nondegeneracy_report` containing QoS, return-cost, event-incidence, total-(G), saturation, and secondary-metric fields.  It also retains those reports transiently inside each calibration continuation result.  But the serialized per-topology unit carries only the bootstrap inputs and episode-world provenance; it does not carry the component reports.  Audit-event serialization similarly stores only each continuation’s scalar `g_total` in `select`, `eval_set`, and `eval_keep`.

Therefore N3 cannot be reconstructed honestly.

## Prospective component persistence

The future instrument must persist more than the existing summary means. To support both component cancellation analysis and the frozen exact-invariance clause, it should retain, per paired continuation:

* QoS component series or a lossless canonical representation;
* capped return-cost series;
* window-local cutoff transition series;
* window-local depletion transition series;
* component window totals;
* total (G);
* user-step QoS saturation;
* the paired arm identity, topology, event, limb, and continuation replicate.

At minimum, exact paired-sequence equality must be computed before serialization and recorded separately from component totals. Persisting only the current `nondegeneracy_report` would allow coarse decomposition but would not establish whether the four sequences were exactly arm-invariant, which R2 made a distinct degeneracy condition.

This prospective repair does not make N3 answerable for run `30289161086`. It only prevents the same blind spot in a future measurement.

---

## 3. DISCRIMINATORS

## A. Standalone distributions — approved

Compute artifact-derived points and two-sided 90% percentile intervals for:

[
B_{\mathrm{stable}},\quad
B_{\mathrm{flex}},\quad
U^**{\mathrm{stable}},\quad
U^**{\mathrm{flex}}.
]

The 5th–95th percentile interval is the appropriate two-sided presentation of the same bootstrap distribution from which R3 took its one-sided 95% bounds. Report:

* equal-topology-weighted point;
* interval;
* eight per-topology point values;
* minimum and maximum;
* sign counts;
* leave-one-topology-out point and interval sensitivity.

The leave-one-topology-out analysis is necessary because one topology can have substantial leverage when the top-level sample size is eight.

## B. N1 — valid after sharpening

The proposed N1 discriminator is directionally right, but “(U^*) holds a coherent direction” must be frozen before looking at the output.

Use this evidence hierarchy:

1. **Strong N1 evidence:** (B_m) has both positive and negative topology values, while the standalone pooled (U_m^*) interval excludes zero and its leave-one-topology-out direction does not reverse.
2. **Moderate N1 evidence:** (B_m) crosses zero, while most topology-level (U_m^*) values share one sign but the pooled interval still includes zero.
3. **No resolved N1:** both (B_m) and (U_m^*) change direction materially.

Sign frequency alone is descriptive and must not be promoted into an inferential branch.

## C. N2 — approved and decision-relevant

Standalone (U^*) intervals are the cleanest available discriminator.

* If (U^*_{\mathrm{stable}}) is positively resolved, then under the registered primary (G), the best focal SET is better than KEEP on the purported stable class.
* If (U^*_{\mathrm{flex}}) is negatively resolved, then under that same objective, focal renewal is worse than KEEP on the purported flex class.

That would raise N2 directly. It would not require a positive (B_m) because it is a sign diagnosis of the unnormalized intervention contrast, not an R3 materiality claim.

It remains diagnostic rather than a retroactive branch of R3, because the frozen branch system stopped before margin interpretation once its scale was unidentified. The prior disposition explicitly selected recovery of these standalone distributions for that diagnostic purpose.

## D. N3 — live but not discriminated

Do not score N3 as false, absent, or lowered merely because the artifact cannot test it.

The output must state:

> Primary-(G) component cancellation remains compatible with every scalar pattern observed in this autopsy.

A resolved N2 may coexist with N3: component cancellation could explain why the registered primary objective gives a direction opposite to the intended source narrative. N3 would then be an explanation of the N2 result, not an alternative that negates it.

## E. N4 — modify substantially

“Between-topology spread versus within-topology event spread” is not yet a complete discriminator.

Report:

[
s^2_{\text{between}}
====================

\operatorname{Var}_t(\hat\theta_t),
]

and an estimated average within-topology uncertainty derived by independently resampling events inside each topology. A useful descriptive ratio is:

[
R_{\text{topology}}
===================

\frac{\max(0,,
s^2_{\text{between}}-\bar s^2_{\text{within}})}
{\max(0,,
s^2_{\text{between}}-\bar s^2_{\text{within}})
+\bar s^2_{\text{within}}}.
]

This may raise:

> `TOPOLOGY_HETEROGENEITY_DOMINANT`

It does not establish a regime.

Also report values against already-recorded topology attributes such as BS quadrant, but mark all such partitions exploratory. The registered set is small and was not selected to validate a discovered partition.

## F. Add N5 — normalizer relevance or comparator mismatch

This explanation is missing from the plan.

[
B_m
===

G(\texttt{constructive_mixed})-
G(\texttt{null})
]

measures the benefit of global proactive rotation relative to no proactive rotation. In contrast,

[
U_m^*
=====

V_{\mathrm{SET},m}-V_{\mathrm{KEEP},m}
]

measures a focal, one-(\Delta) reassignment under reoptimized continuation. These are not the same intervention. The normalizer may be measured correctly and still be a poor scale for the focal renewal effect. The frozen definitions make this causal mismatch visible.

Use the already-planned (B_m)–(U_m^*) association to diagnose N5, but compute it correctly:

1. form one paired point ((B_{m,t},U^*_{m,t})) per topology;
2. report Pearson and rank association descriptively;
3. resample topologies jointly;
4. resample calibration and audit observations independently within each topology;
5. report leave-one-topology-out association.

With eight topologies, no association test should be used as a sharp acceptance gate. A weak, unstable, or negative relation raises N5; it does not prove it.

## G. Add a selection-instability diagnostic

This is not a fifth causal explanation for (B_m), but it is a necessary qualifier on N2.

At the `2/2` floor, the selected SET alternative can be unstable. R2 therefore required point winners, bootstrap selection frequencies, legal-set size, and concentration or entropy for every event.

The autopsy should summarize by limb and topology:

* median and range of normalized selection entropy;
* fraction of events whose leading candidate has frequency below 0.60;
* fraction below 0.75;
* association between candidate instability and (|U^*_m|) or topology-level uncertainty.

The registered bootstrap already propagates this uncertainty. The diagnostic explains why an (U^*) estimate may remain broad; it must not be used to remove events or select a more favorable candidate.

## Overall discriminator verdict

The plan is sufficient after adding N5, the selection-instability qualifier, and the stricter N4 interpretation.

The explanations should be reported as an evidence matrix:

| Explanation                  | Status vocabulary                     |
| ---------------------------- | ------------------------------------- |
| N1 signed-normalizer failure | raised / compatible / lowered         |
| N2 opposite source direction | resolved / compatible / not resolved  |
| N3 component cancellation    | undiscriminated                       |
| N4 topology heterogeneity    | dominant / material / not established |
| N5 comparator-scale mismatch | raised / compatible / lowered         |
| Selection instability        | high / moderate / low                 |

Do not force exactly one explanation to win.

---

## 4. APPARATUS_LEMMA

# **The lemma survives only in a narrower form**

The following remains supported:

> The run instantiated the frozen eight-topology sampling frame, reached the registered event-support floor, recorded seed-controlled user-world provenance, preserved per-topology bootstrap units, and produced an artifact that can be deterministically reanalyzed.

The artifact used the frozen eight topology seeds, and the run reports qualifying calibration and audit support across all eight.  The R3 provenance contract defines topology-conditioned user-world seeds and event-history fingerprints, while preserving topology as the upper inferential unit.

The following broader reading is withdrawn:

> The entire support, conformance, provenance, clone, and primary-(G) apparatus has been independently demonstrated to detect all conclusion-changing faults.

The back-half sweep showed that the existing tests did not object when:

* every `g_total` was halved;
* condition 5 was disabled;
* the (B_{\mathrm{stable}}) treatment/baseline order was reversed;
* `all_seed_controlled` was fabricated;
* or qualifying-event construction was made unreachable.

It also found that clone conditions 2, 3, and 5 could be removed with the suite still green, and that the two functions generating every `g_total` had no direct test.

The revised retained lemma is therefore:

> **The artifact preserves the intended eight-topology data and provenance structure well enough for conditional artifact analysis. The current test suite did not independently certify every guard or numeric transformation on the path that produced it.**

## Does “valid matched observation” survive?

Not without qualification.

The strongest justified phrase is:

> **A provenance-recorded, CRN-paired, executed-code observation that remains admissible for diagnostic reanalysis, but is not independently validated at every conclusion-bearing transformation.**

Why it remains usable:

* no concrete defect in the production calculation used by the run has been identified;
* the current source code computes (G) from the registered QoS, capped return-cost, cutoff, and depletion terms and sums that series into `g_total`;
* calibration arms share their continuation stream and compute (B_m) from paired `constructive_mixed` and `null` totals;
* audit SET and KEEP evaluation streams are paired before their scalar totals enter the stored units.
* the stored units reproduce the registered bootstrap output.

Why the adjective “validated” is too strong:

* the suite’s inability to detect large mutations means the mechanical certificates provide less independent assurance than their names imply;
* the old artifact contains no raw component data from which the scalar totals can be independently reconstructed.

Adding guard tests now would improve future reliability, but it could not retroactively reconstruct the missing component series. Therefore instrumenting the guards **instead of** running the autopsy would not solve the historical evidentiary limitation.

The autopsy remains the correct next action, but every conclusion inherits this conditional scope. It may design the next measurement; it cannot turn R3 into a fully validated source result.

Before any future environment run, the guard gaps affecting:

* `window_g_from_step_metrics`;
* baseline masks;
* calibration arm ordering;
* audit-limb assignment;
* seed-controlled provenance;
* qualifying-event construction;
* clone conditions 2, 3, and 5

must be closed with paired negative tests or another independent conformance mechanism.

---

## 5. COMPONENT_INVARIANCE

# **Neither binary option is correct**

Recording:

```text
component_invariance_evaluated = False
```

is correct for the historical artifact.

It is not sufficient as the permanent prospective treatment.

At the same time, branch 3 must **not** be prohibited from firing when normalizer failure alone logically establishes degeneracy.

Use tri-state logic.

## Historical and normalizer-forced case

Define:

```text
normalizer_forces_degenerate =
    not (stable_b_identified or flex_b_identified)
```

When this is true, branch 3 fires regardless of whether component invariance was evaluated:

```text
PRIMARY_G_DEGENERATE
reason = NO_POSITIVE_NORMALIZER_ON_EITHER_LIMB
component_invariance_evaluated = False
```

That is the current run. Neither component result could restore a valid (B_m), so the missing component input cannot change its branch.

The present implementation correctly applies the disjunctive normalizer rule and records both limb statuses and the missing component evaluation.

## Prospective case with at least one identified normalizer

When either normalizer is identified, the instrument may not silently proceed while component separation remains unknown.

Use:

```text
if normalizer_forces_degenerate:
    branch = PRIMARY_G_DEGENERATE
    reason = NO_POSITIVE_NORMALIZER_ON_EITHER_LIMB

elif not component_invariance_evaluated:
    result = INVALID_EVENT_ALIGNED_AUDIT
    reason = MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING

else:
    stable_measurement_valid =
        stable_b_identified and stable_components_separate

    flex_measurement_valid =
        flex_b_identified and flex_components_separate

    primary_g_degenerate =
        not (stable_measurement_valid or flex_measurement_valid)
```

Under the frozen R3 branch vocabulary, the missing mandatory component audit is an implementation/measurement invalidity and belongs under branch 1, not under branch 10. R2 explicitly made the component record and nondegeneracy audit mandatory.

Thus:

* branch 3 remains reachable through the independently sufficient normalizer condition;
* component invariance is not fabricated;
* later branches cannot fire on a future run whose mandatory component audit is missing.

Because R3’s normalizer route is already retired and no R3 rerun is authorized, this prospective logic mainly binds the R4 instrument.

---

## 6. CHALLENGES

### Claims checked and accepted

1. **N3 is not recoverable from the pooled artifact.**
2. **The zero-new-data boundary should remain.**
3. **The technical branch-3 repair correctly uses disjunctive limb identification for the current result.**
4. **The point-estimate addition can be made without perturbing the previously registered bounds.**
5. **The §9 expansion guard must evaluate the initial eight topologies rather than allow the extra topologies to justify themselves.**

### Claims checked and modified

1. **“Everything else is executable as written” is too strong.**
   N4 lacks a criterion that distinguishes topology heterogeneity from reproducible regimes, and the proposed (B_m)–(U^*_m) association needs paired outer-topology but independent inner-block resampling.

2. **The four explanations are not exhaustive.**
   The plan omitted normalizer relevance/comparator mismatch: the global `constructive_mixed − null` contrast may simply be the wrong scale for a focal SET-versus-KEEP effect.

3. **The explanations are not mutually exclusive.**
   N2 and N3 can both be true; N1 and N4 can coexist; N5 can coexist with all of them.

4. **The apparatus lemma was stated too broadly.**
   The data/provenance structure survives. A general claim that the apparatus was independently fault-detecting does not.

5. **The phrase “valid matched observation” needs downgrading.**
   The observation remains diagnostically usable, but “valid” without qualification overstates the guard evidence uncovered by the mutation sweep.

6. **Guard hardening is not a substitute for the autopsy.**
   New tests can prevent recurrence but cannot reconstruct component series absent from the historical artifact.

7. **`component_invariance_evaluated=False` is not a complete prospective design.**
   It is correct for this historical disposition, but any future non-normalizer result must fail closed if the mandatory component audit is absent.

8. **The autopsy must not automatically decide R4.**
   It may narrow the portfolio and recommend a measurement, but N3 remains live and the final scale or carrier choice requires a subsequent scientific disposition.

---

## Converged execution order

1. Implement the deterministic artifact-only autopsy with the modifications above.
2. Abort unless its input sentinel reproduces the six frozen R3 bounds.
3. Emit standalone distributions and the N1/N2/N4/N5/selection evidence matrix.
4. Record N3 as `UNDISCRIMINATED_FROM_STORED_ARTIFACT`.
5. Add prospective component persistence and fail-closed component-audit semantics, without rerunning R3.
6. Return the autopsy artifact for the R4-scale-versus-source-retirement decision.

No environment compute is selected by this ruling.
