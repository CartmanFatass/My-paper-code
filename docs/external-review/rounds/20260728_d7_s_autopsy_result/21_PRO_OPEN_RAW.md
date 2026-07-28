# Scientific ruling — D7.S normalizer autopsy result

**Stage reviewed:** `6430ef968498bf8be0533cb27eb865cecba8a519`

## Overall disposition

**SELECT AN R4 MEASUREMENT DERIVATION; DO NOT RETIRE S7-S3 YET.**

The autopsy does not establish that (B_m) is empirically “unrelated” to (U_m^*). With eight topologies, the association intervals are far too broad and the leave-one-topology-out estimates too unstable for that conclusion. It establishes the narrower result that:

> **The completed artifact provides no positive evidence that the global `constructive_mixed − null` contrast is a useful scale for the focal one-(\Delta) SET-versus-KEEP effect.**

That finding matters because the two quantities already differ causally:

[
B_m
===

G(\texttt{constructive_mixed})-G(\texttt{null})
]

measures a global proactive-rotation intervention, while

[
U_m^*
=====

V_{\mathrm{SET},m}-V_{\mathrm{KEEP},m}
]

measures one focal reassignment for (\Delta=10) steps under reoptimized continuation. The R2 contract defines those as different interventions.

The portfolio should therefore move toward a treatment-independent, focal-contrast-compatible R4 materiality criterion. The source itself remains scientifically live because neither standalone (U^*) direction was identified and no structural contradiction shows that S7-S3 cannot carry the proposition.

---

# 1. SMALLEST_UNIT

## What the autopsy supports

The four artifact-derived distributions are all broad and include zero:

[
B_{\mathrm{stable}}
===================

0.180,\qquad
90%\text{ interval }[-0.077,0.416],
]

[
B_{\mathrm{flex}}
=================

4.289,\qquad
[-8.649,14.103],
]

[
U^*_{\mathrm{stable}}
=====================

1.254,\qquad
[-2.204,7.186],
]

[
U^*_{\mathrm{flex}}
===================

-4.122,\qquad
[-13.828,3.371].
]

The per-topology signs also vary substantially: (U^**{\mathrm{stable}}) is split (4/4), while (U^**{\mathrm{flex}}) is split (3/5).

Consequently, the autopsy supports three narrow conclusions:

1. **Neither focal source direction is identified.** There is no resolved evidence that SET is harmful on the stable class or beneficial on the flex class.
2. **The positive-normalizer failure was not merely caused by one obviously negative population mean.** Both (B_m) point estimates are positive, but their topology and within-topology variation prevent a positive lower bound.
3. **The empirical relevance of (B_m) to (U_m^*) is not demonstrated.**

The last statement is the correct empirical form of N5.

## What N5 does—and does not—establish

The point associations are nearly zero:

* stable: Pearson (0.038), rank (-0.180);
* flex: Pearson (0.022), rank (-0.333).

But their 90% bootstrap intervals are extremely wide:

* stable Pearson: approximately ([-0.600,0.551]);
* flex Pearson: approximately ([-0.688,0.738]).

The flex leave-one-topology-out Pearson estimate ranges from roughly (-0.887) to (+0.568).

Therefore:

> **N5 is raised as a design risk, not identified as a scientific fact.**

The eight-topology result cannot distinguish:

* a genuinely irrelevant normalizer;
* attenuation caused by noisy (B_m) and (U_m^*) estimates;
* instability from the minimally replicated action maximization;
* or heterogeneous causal relationships across topologies.

The evidence-note title, “the normalizer is unrelated to the effect,” is too strong. Its body correctly acknowledges the small sample and instability, but “unrelated” sounds like an established null relationship.

A defensible durable statement is:

> `GLOBAL_ROTATION_NORMALIZER_RELEVANCE_NOT_DEMONSTRATED`

## Smallest portfolio move

The autopsy adds **no broader retirement** beyond the already retired R3 measurement unit:

```text
primary G
× constructive_mixed-versus-null calibration pair
× signed B_m denominator
× registered topology population
```

It does strengthen one design constraint:

> A future measurement may not use a global source-control contrast to scale a focal renewal effect merely because both are measured in (G). It must either use an arm-independent task scale or establish analytically—before data—that the proposed normalizer is commensurate with the focal one-(\Delta) intervention.

The status table is therefore:

| Object                             | Disposition                                        |
| ---------------------------------- | -------------------------------------------------- |
| R3 signed (B_m) materiality scale  | **Retired; not reopened**                          |
| N5 comparator-scale mismatch       | **Prioritized design risk; not proven**            |
| N1 signed-normalizer explanation   | **Autopsy classification invalid; see Challenges** |
| N2 opposite source direction       | Not resolved                                       |
| N3 component cancellation          | Undiscriminated                                    |
| N4 topology effect                 | Limited evidence; no regime                        |
| S7-S3 source-necessity proposition | Unjudged                                           |
| R30 carrier                        | Unchanged                                          |
| D7.3 / D8                          | Blocked                                            |

This follows the project rule that a non-identifying measurement updates the measurement or benchmark–comparator pair, not the entire algorithmic proposition.

---

# 2. NEXT_ACTION

# **Select the R4 route, beginning with a zero-compute materiality derivation**

Do not retire S7-S3 at this boundary.

The source provided:

* qualifying events across all eight registered topologies;
* a reproducible artifact;
* legal focal interventions;
* and no resolved evidence that the underlying stable/flex proposition points in the opposite direction.

What failed was the scale used to interpret those interventions, not source support or a demonstrated causal consequence. Retiring the source now would therefore be broader than the evidence permits.

## Preferred R4 form: an absolute external-task-unit gate

The preferred replacement removes the empirical denominator entirely:

[
\operatorname{UCB}*{95}
\left(
U^**{\mathrm{stable}}
\right)
<
-\delta_{\mathrm{stable}},
]

[
\operatorname{LCB}*{95}
\left(
U^**{\mathrm{flex}}
\right)

>

+\delta_{\mathrm{flex}}.
]

Here (\delta_{\mathrm{stable}}>0) and (\delta_{\mathrm{flex}}>0) must be derived from external-task semantics before any new result is observed. They may differ because the stable and flex horizons are 139 and 550 steps.

Acceptable derivations include a fixed, interpretable primary-(G) consequence such as:

* a predeclared QoS-service loss budget;
* a fixed cutoff- or depletion-equivalent task consequence;
* or another externally justified (G)-unit margin.

They may not be selected by inspecting the R3 (U^*) magnitudes.

This form is preferable because it tests the focal effect directly and removes the need to prove that a separate controller contrast is a meaningful denominator.

## Acceptable alternative: a positive pre-treatment scale

A ratio may be retained only if its scale (S_m(h)):

1. is positive by construction;
2. is determined solely from the pre-intervention state, the frozen horizon, and fixed source semantics;
3. does not depend on the realized return of KEEP, SET, `constructive_mixed`, or `null`;
4. cannot change sign;
5. is commensurate with the focal one-(\Delta) causal consequence.

Then the gate could take the form

[
U^**{\mathrm{stable}}/S*{\mathrm{stable}}
\le -\eta,
\qquad
U^**{\mathrm{flex}}/S*{\mathrm{flex}}
\ge+\eta.
]

A second global-rotation contrast is not acceptable merely under a new name.

## Does N5 require focal matching?

**Yes, with one qualification.**

The scale must either:

* be matched to the focal action support, history and horizon; or
* be an arm-independent task-unit scale for which “matching an intervention” is unnecessary.

A global source-control contrast may be reused only after a zero-data derivation establishes a monotone or otherwise decision-relevant relationship to the focal effect. The current correlation estimates cannot supply that proof.

## The selected evidence action

The next action is one zero-compute R4 design assertion:

> Derive one non-arbitrary absolute task-unit margin or one positive pre-treatment scale; construct its zero-denominator and sign counterexamples; freeze its branch semantics; and decide whether it is scientifically meaningful before any implementation or environment run.

That action ends in one of two outcomes:

### R4 derivable

Freeze a new measurement on a fresh, untouched evidence population. The R3 artifact may motivate the design but cannot become the confirmatory R4 result.

### R4 not derivable without using observed effects or arbitrary task tuning

Retire S7-S3 as the carrier of this source-necessity proposition and move the carrier-capacity question to a source with a naturally identified materiality unit.

No expansion, rerun, threshold adjustment, (|B_m|), sign flip, or clipping is authorized.

## Retained alternatives

| Candidate                                          | Status          | Raising observation                                                                       |
| -------------------------------------------------- | --------------- | ----------------------------------------------------------------------------------------- |
| **R4-A: absolute (G)-unit focal margins**          | **Preferred**   | A task-semantic (\delta_m) can be derived without reference to R3 outcomes                |
| **R4-B: positive pre-treatment opportunity scale** | Live            | A scale based only on (h), (H_m), and source semantics is shown commensurate with (U_m^*) |
| **New source with inherent unit**                  | Parked fallback | Neither R4-A nor R4-B can be defined non-arbitrarily                                      |
| **Another global-rotation denominator**            | Disfavored      | Reactivate only after an analytical relation to focal SET/KEEP is proved                  |

---

# 3. AGGREGATION_RULE

## The first two proposed rules are logically identical

The question offers:

* “not separate only if every pair is equal”;
* “separate if any pair differs.”

These are the same rule by De Morgan’s law:

[
\neg\left(\bigwedge_j E_j\right)
================================

\bigvee_j\neg E_j.
]

There is no substantive choice between them.

## Binding rule

For each limb (m), let (\mathcal P_m) be the complete set of qualifying **calibration source-control pairs**:

[
(\texttt{constructive_mixed},\texttt{null})
]

for that limb.

Define:

[
\text{components_invariant}_m
=============================

\bigwedge_{p\in\mathcal P_m}
\text{exact_paired_sequence_equal}(p),
]

[
\boxed{
\text{components_separate}_m
============================

# \neg\text{components_invariant}_m

\bigvee_{p\in\mathcal P_m}
\neg\text{exact_paired_sequence_equal}(p)
}
]

Thus:

> A limb is component-invariant only if every complete paired source-control continuation has exactly equal QoS, capped return-cost, cutoff-transition and depletion-transition sequences. One unequal pair is sufficient to refute **exact** invariance.

No fraction threshold is permitted.

A proportion such as 10%, 50%, or 95% would silently turn an exact structural-degeneracy check into a new statistical materiality gate. R2 already assigns materiality and population uncertainty to the (B_m) confidence bound; the component-invariance limb is only the exact-degeneracy check.

## Which pairs enter the branch input?

For branch 3, use the calibration source-control pairs only.

The branch meaning is that primary (G) cannot separate the source controls, and (B_m) is defined from `constructive_mixed − null`. The implementation now computes exact component equality for that precise pair while both series are in memory.

The audit block’s KEEP-versus-each-SET equality records remain mandatory evidence for:

* future component-cancellation analysis;
* focal-intervention diagnostics;
* and verification of the recorded (U^*) arms.

They do not define whether the **normalizer source controls** are component-separable. The code records these focal pairwise equalities separately.

## Completeness is load-bearing

Before `component_invariance_evaluated=True`, require:

1. one calibration equality record for every qualifying calibration event and each limb;
2. both members of every CRN pair present;
3. all four sequences present at their registered horizon;
4. no invalidated pair;
5. serialized and in-memory pair counts agree;
6. the focal audit component records are also complete, because their persistence is mandatory prospectively even though they are not the branch-3 aggregation input.

A missing record is not “equal” and not “separate.” It means the mandatory component audit was not evaluated and the run remains fail-closed.

## Branch logic

Use:

```text
normalizer_forces_degenerate =
    not (stable_b_identified or flex_b_identified)

if normalizer_forces_degenerate:
    PRIMARY_G_DEGENERATE
    reason = NO_POSITIVE_NORMALIZER_ON_EITHER_LIMB

elif not component_audit_complete:
    INVALID_EVENT_ALIGNED_AUDIT
    reason = MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING

else:
    stable_measurement_valid =
        stable_b_identified and stable_components_separate

    flex_measurement_valid =
        flex_b_identified and flex_components_separate

    primary_g_degenerate =
        not (stable_measurement_valid or flex_measurement_valid)
```

There is also a useful consistency assertion:

> If (B_m) has a strictly positive lower bound but every associated source-control component sequence is exactly equal, the artifact is internally inconsistent and should be invalidated rather than interpreted as an ordinary branch-3 result.

An exactly equal component sequence implies exactly equal (G), so it cannot coexist coherently with an identified positive (B_m) computed from the same pairs.

## Activation timing

The rule is now scientifically decided. It should be wired as part of the R4 instrument closure.

Do not rerun R3 merely because branches 4–10 become reachable. R3’s normalizer route is already retired.

---

# 4. SELECTION_FLOOR

# **`2/2` remains admissible; selection instability remains a material qualifier, not an invalidation**

The autopsy reports:

* stable: 39% of events have leading-candidate frequency below 0.60; 67% below 0.75;
* flex: 37% below 0.60; 59% below 0.75.

Median normalized selection entropy is about 0.42 on both limbs.

This makes it plausible that `n_select=2` contributes to the width of the (U^*) distributions. It does not establish how much of that width is due to:

* candidate selection;
* evaluation noise;
* event heterogeneity;
* or topology variation.

The diagnostic’s entropy-to-(|U^*|) associations are near zero for stable and modestly negative for flex, and they repeat one topology-level (U^*) value across multiple event observations. They should remain descriptive rather than being used as a variance decomposition.

## Why `2/2` does not explain the normalizer failure

(B_m) comes from the calibration `constructive_mixed − null` pair. It does not contain the legal-candidate argmax whose instability is controlled by `n_select`.

Therefore selection instability cannot explain why neither (B_m) lower bound was positive. It can only qualify the focal (U^*) side and consequently the reliability of the N5 association.

## Why the floor remains valid

R2 explicitly froze `2/2` as the minimum non-degenerate volume and stated that candidate instability should widen or prevent resolution rather than invalidate a correctly propagated interval. It also prohibited interpreting the result as a precise candidate ranking.

The registered bootstrap resamples each candidate’s selection streams, reruns the argmax, and carries the uncertainty into (U^*). Thus the measurement did not hide selection instability.

The correct status is:

> `2/2` is implicated as a plausible contributor to low precision, but not implicated as an estimand defect.

## R4 consequence

Do not automatically increase the volume.

R4 must freeze its replicate volume before its new evidence is observed. A larger selection volume may be chosen prospectively only if:

* the R4 precision requirement is stated first;
* an analytic or proof-sized cost/variance calculation shows that selection uncertainty would otherwise dominate;
* and the change is part of the new contract rather than described as rescuing R3.

The current “moderate,” not “high,” instability is insufficient by itself to mandate the old `4/8` confirmatory route.

---

# 5. CHALLENGES

## 1. “The normalizer is unrelated to the effect” is not established

The association point estimates are close to zero, but their intervals encompass strong negative and positive relationships, and leave-one-topology-out estimates are unstable. The supported statement is “relevance not demonstrated,” not “unrelated.”

N5 moves the portfolio by prioritizing focal-compatible scale design. It does not independently retire a comparator.

## 2. The N1 evidence-matrix row is not valid as implemented

The script constructs N1 by concatenating the stable and flex topology values:

```text
B_stable points + B_flex points
U*_stable points + U*_flex points
```

but then evaluates that combined vector using only the `U*_stable` pooled interval and stable leave-one-out points.

This mixes:

* two different horizons;
* two different causal classes;
* differently scaled (B_m) distributions;
* and two different (U^*) directions.

The reported `N1 = compatible (moderate)` must be discarded. N1 must be evaluated separately by limb. This error does not change the four standalone distributions or the R4 decision.

## 3. N4 “material” is overstated

Only (B_{\mathrm{stable}}) has nonzero adjusted topology ratio:

[
R_{\mathrm{topology}}\approx0.122.
]

The other three quantities have (R_{\mathrm{topology}}=0) because their estimated within-topology variance exceeds their between-topology point variance.

The script calls any positive maximum “material,” using a threshold it explicitly identifies as its own interpretive choice.

A more accurate result is:

> Limited topology contribution is detected for artifact-derived (B_{\mathrm{stable}}); topology-dominant variation is not established for any quantity.

The non-binding recommendation to stratify or expand by topology should not be selected. R3 expansion remains forbidden, and eight post hoc topologies cannot identify a transportable regime.

## 4. The N2 classifier is prospectively too conjunctive

The prior ruling stated that either:

* positively resolved (U^*_{\mathrm{stable}}); or
* negatively resolved (U^*_{\mathrm{flex}})

would raise N2 directly.

The script reserves `resolved` for both legs and calls one resolved leg merely `compatible`.

Neither leg resolves here, so the current `not resolved` result is unchanged. Future output should report the two legs separately rather than collapse them into one AND predicate.

## 5. “N5 raised” is a hypothesis status, not an acceptance test

The classifier labels a weak, unstable, or negative association as `raised`, including any negative rank point even when its interval is broad.

That vocabulary is acceptable only when read as:

> the comparator-mismatch explanation remains important enough to affect design.

It must not be quoted as a statistically identified mismatch.

## 6. The two aggregation candidates are not different

“All pairs equal implies invariant” and “any unequal pair implies separate” are exact complements. A fraction rule would be the only genuinely different candidate, and it is rejected because it invents an unregistered threshold.

## 7. The instrument’s safe stop is appropriate

The current default `component_invariance_evaluated=False` prevents branches 4–10 from firing unless the mandatory component audit is explicitly supplied. That is the correct fail-closed state.

The aggregation ruling above closes the semantic choice. It does not retroactively alter the R3 artifact or authorize another R3 run.

---

## Final portfolio

| Route                                             | Status                      | Reactivation or rejection condition                                          |
| ------------------------------------------------- | --------------------------- | ---------------------------------------------------------------------------- |
| **R4 absolute focal task-unit margin**            | **Selected for derivation** | Retain if a non-arbitrary (\delta_m) follows from task semantics             |
| **R4 positive pre-treatment scale**               | Live alternative            | Retain if it is sign-fixed and focal-commensurate without treatment outcomes |
| **S7-S3 carrier retirement**                      | Conditional fallback        | Select if neither R4 scale can be derived without post hoc tuning            |
| **Global `constructive_mixed − null` normalizer** | Retired for this claim      | Reopen only with a prior analytical relation to focal (U^*)                  |
| **Topology stratification**                       | Not selected                | Requires independent, pre-registered regime evidence                         |
| **Higher selection volume**                       | Parked                      | Reconsider only prospectively under an R4 precision contract                 |

## Scheduled action

**Derive and pre-freeze the R4 absolute task-unit or positive pre-treatment materiality criterion.**

No environment compute, expanded topology set, or R3 rerun is selected by this ruling. D7.3 and D8 remain blocked.
