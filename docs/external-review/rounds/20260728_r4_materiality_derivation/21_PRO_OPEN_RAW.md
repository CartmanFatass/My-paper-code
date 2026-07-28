# Scientific ruling — R4 materiality derivation

**Stage reviewed:** `214553620e97085060a485d527ead3d85679ca2b`

## Overall disposition

# **SELECT ANCHOR E; R4-A IS DERIVABLE; RETAIN S7-S3 CONDITIONALLY**

Freeze the R4 focal materiality unit as:

[
\boxed{
\delta_{\mathrm{stable}}
========================

# \delta_{\mathrm{flex}}

5\ \text{primary-}G\text{ units}
}
]

Five (G)-units should be described as **one service-cutoff-equivalent external-task consequence**, not as a requirement that an actual cutoff event occur.

R4 may therefore continue on S7-S3. The source is not retired at this boundary.

However, the full R4 result contract cannot inherit the R3 branch system verbatim. In addition to replacing the two focal gates, it must:

1. rebind branch 3 to the focal KEEP/SET component audit;
2. replace branch 4’s (0.05B_{\mathrm{stable}}) equivalence margin with an absolute task-unit margin;
3. replace the R3 expansion predicate, which depends on (B_m) and (T_m);
4. preserve flex-only positive evidence rather than lose it in the asymmetric R3 branch table.

No environment compute is authorized by this ruling.

---

# 1. ANCHOR

## Decision: Anchor E

Use:

[
\delta_E = 5.
]

The R4 gates are:

[
\boxed{
\operatorname{UCB}*{95}
\left(
U^**{\mathrm{stable}}
\right)
<
-5
}
]

and

[
\boxed{
\operatorname{LCB}*{95}
\left(
U^**{\mathrm{flex}}
\right)

>

+5.
}
]

Because

[
U^*_m
=====

## V_{\mathrm{SET},m}

V_{\mathrm{KEEP},m},
]

the interpretation is:

* stable clearance: KEEP is better than the best legal focal SET by more than one cutoff-equivalent;
* flex clearance: the best legal focal SET is better than KEEP by more than one cutoff-equivalent.

The R2 estimand is already a difference of cumulative external return over the mechanism-specific horizon, and the frozen primary objective assigns a weight of (-5) to one new service-cutoff event.

## Why the same five-unit bar is correct for both horizons

The source question is about the **total task consequence of one renewal decision**, not its average effect per primitive step.

The two horizons differ because the relevant physical consequences unfold over different causal windows:

[
H_{\mathrm{stable}}=139,
\qquad
H_{\mathrm{flex}}=550.
]

A service cutoff is a discrete task consequence. Its external value does not become one quarter as important merely because the evaluator must observe the flex process for roughly four times as long. The fact that five units correspond to:

* about (3.60%) sustained QoS loss over 139 steps;
* about (0.91%) sustained QoS loss over 550 steps,

is therefore not an unfairness in the gate. It is the expected consequence of evaluating **cumulative task value** over different causal horizons.

Selecting an equal per-step bar would define a different proposition:

> the renewal decision must produce the same average effect rate over its entire downstream observation window.

That is not the registered source-necessity proposition.

## What “cutoff-equivalent” means

The result need not be carried by an observed cutoff. Five (G)-units may arise from any registered combination of:

* QoS differences;
* capped return-cost differences;
* cutoff events;
* depletion events.

The frozen objective has already declared those exchange rates. The anchor provides an interpretable task unit; it does not require a particular component to realize the margin.

This also explains why the cutoff coefficient is preferable to selecting one QoS step or one return-cost step:

* QoS and return cost are rate-like, continuously valued quantities whose one-step interpretation depends on the simulation clock;
* a new cutoff is a discrete, window-local, task-semantic event;
* five is the smallest nonzero coefficient attached to such a discrete safety event in the registered objective.

The anchor is not mathematically unique, but it is non-post-hoc, externally interpretable and fixed by pre-existing task semantics. That is sufficient for the requested R4 derivation.

## Anchor Q

Do not select Anchor Q.

The form

[
\delta_m=q^*H_m
]

is mathematically valid for an average-rate proposition, but the level (q^*) is not identified by:

* the primary-(G) weights;
* the horizons;
* (\Delta);
* or the source semantics.

Choosing it would introduce a free materiality parameter after observing the R3 line. The question correctly identifies that defect.

Per-step normalized quantities such as

[
U^*_m/H_m
]

may be reported descriptively in R4, but they must not determine the branch.

## Third-anchor candidate

A possible third anchor is one full check interval of complete QoS loss,

[
\delta=\Delta=10.
]

It is also treatment-independent and focal-clock-matched. It is not selected because it encodes a substantially harsher criterion—ten full system-wide QoS-step units—without a registered reason to prefer that task event over one service cutoff. It remains a speculative sensitivity interpretation, not a conclusion-bearing candidate.

---

# 2. DERIVABLE

# **R4-A is derivable**

The (q^*) gap does not force source retirement because Anchor E supplies a valid absolute task-unit margin.

S7-S3 remains the carrier candidate because the prior evidence established:

* sufficient event support;
* legal focal interventions;
* no identified opposite stable/flex direction;
* and no structural contradiction showing that the source cannot express the proposition.

The preceding autopsy ruled that the R3 normalizer’s relevance was not demonstrated, while leaving the source proposition unjudged.

## What R4 deletes, retains and adds

### Deletes

* (B_{\mathrm{stable}}) and (B_{\mathrm{flex}}) as materiality denominators;
* the per-limb requirement
  [
  \operatorname{LCB}_{95}(B_m)>0;
  ]
* the normalizer-driven half of `PRIMARY_G_DEGENERATE`;
* the R3 expansion predicate based on (B_m) and (T_m).

### Retains

* the event definition;
* stable and flex certification;
* legal focal SET alternatives;
* (U^**m=V*{\mathrm{SET},m}-V_{\mathrm{KEEP},m});
* primary (G);
* (H_{\mathrm{stable}}=139);
* (H_{\mathrm{flex}}=550);
* CRN pairing;
* topology-level inference;
* the `2/2` empirical-maximization floor;
* the mandatory component persistence audit.

### Adds or modifies

* the fixed five-unit absolute margins;
* a focal-arm component-separation predicate;
* a five-unit Part-A equivalence margin;
* an R4-specific expansion rule;
* symmetric partial-result semantics.

## Fresh evidence is mandatory

The R3 artifact cannot be rethresholded at (\pm5) and reported as an R4 result.

The previous ruling selected a fresh, untouched evidence population for any new R4 measurement. The old artifact may inform design and precision planning, but it cannot confirm the newly chosen margin.

## Part-A branch must be rederived

The claim that “calibration is no longer conclusion-bearing” is too broad.

The **normalizer calibration** disappears. But branch 4 presently uses:

[
D_A
===

## G(\texttt{full_sync_SET})

G(\texttt{constructive_mixed})
]

and tests equivalence against

[
\pm0.05B_{\mathrm{stable}}.
]

The current implementation and frozen R2 contract both make that (B_{\mathrm{stable}})-dependent control conclusion-bearing.

Under R4, replace it with the same absolute task anchor:

[
-5<D_A<+5.
]

The corresponding Part-A rules should be:

### Return-equivalence contradiction

Both one-sided tests establish:

[
\operatorname{LCB}_{95}(D_A+5)>0
]

and

[
\operatorname{LCB}_{95}(5-D_A)>0.
]

Then emit:

```text
PART_A_CONTRADICTION
```

### Full-sync materially worse

Require:

[
\operatorname{UCB}_{95}(D_A+5)<0.
]

### Otherwise

```text
PART_A_CONFORMANCE_UNRESOLVED
```

Thus a disjoint Part-A contradiction-control block remains conclusion-bearing, even though (B_m) calibration does not.

## The R3 expansion rule cannot carry forward

R3 permits expansion only when:

* (B_m) points are positive;
* (T_m) points have the intended directions;
* one or more confidence bounds remain unresolved.

Those quantities no longer exist under R4.

Before an R4 run, either:

* freeze an R4-specific one-expansion rule based on the absolute-margin point directions and unresolved bounds; or
* freeze no expansion.

The R3 expansion set is not automatically authorized for the new measurement.

## Preserve flex-only positive evidence

The R3 branch map has no authoritative top-level outcome for:

* flex clears;
* stable does not clear.

Its branch table preserves stable-only positive evidence but not the symmetric flex-only case.

R4 must record independent per-limb states:

```text
MATERIAL
AFFIRMATIVE_NONMATERIAL
UNRESOLVED
COMPONENT_INVARIANT
```

and must preserve at least these two additional combined results:

```text
MATERIAL_FLEX_RENEWAL_IDENTIFIED
FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE
```

A valid flex positive may not be hidden under a stable-negative or generic unresolved branch.

---

# 3. BRANCH_3_UNDER_R4

# **Retain branch 3, but bind it solely to exact focal-arm component invariance**

The normalizer half of branch 3 is retired.

Under R4, branch 3 should mean:

> On the registered focal action support, primary (G)’s four component sequences were exactly invariant between KEEP and every legal paired SET continuation on both limbs.

## R4 pair set

For limb (m), let (\mathcal P_m^{R4}) contain every complete, CRN-paired evaluation comparison:

[
(\mathrm{KEEP},\mathrm{SET}(z))
]

for:

* every qualifying event;
* every legal (z);
* every registered evaluation replicate.

Do not use the R3 calibration pair

[
(\texttt{constructive_mixed},\texttt{null})
]

for branch 3. That pair was relevant because it defined (B_m). R4 has no (B_m), so the earlier calibration-pair aggregation ruling is R3-specific. Under R3, that ruling explicitly tied component separation to the normalizer source controls.

## Per-limb aggregation

For each limb:

[
\mathrm{components_invariant}_m
===============================

\bigwedge_{p\in\mathcal P_m^{R4}}
\mathrm{exact_paired_sequence_equal}(p),
]

[
\mathrm{components_separate}_m
==============================

\neg\mathrm{components_invariant}_m.
]

One unequal complete pair is sufficient to refute **exact** component invariance.

No fraction threshold is permitted. A 10%, 50% or 95% rule would turn an exact non-degeneracy assertion into another unregistered materiality threshold.

## Global branch-3 predicate

Use the disjunctive partial-evidence principle:

[
\boxed{
\mathrm{primary_g_degenerate}
=============================

\neg
\left(
\mathrm{components_separate}*{\mathrm{stable}}
\lor
\mathrm{components_separate}*{\mathrm{flex}}
\right)
}
]

Thus branch 3 fires only when **neither limb** contains any observed focal component separation.

If one limb separates and the other is invariant:

* do not emit global branch 3;
* record the invariant limb explicitly;
* allow only the separated limb’s materiality state to contribute to a positive claim.

## Missing audit versus exact invariance

These are different outcomes.

### Component audit missing or incomplete

Emit:

```text
INVALID_EVENT_ALIGNED_AUDIT
reason = MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING
```

The required completeness conditions remain:

* every qualifying event represented;
* every legal candidate represented;
* both members of every CRN pair present;
* all four sequences present at the registered horizon;
* no invalidated pair;
* serialized and in-memory pair counts agree.

A missing pair is neither equal nor unequal.

### Audit complete and all focal pairs invariant

Emit:

```text
PRIMARY_G_DEGENERATE
reason = FOCAL_KEEP_SET_COMPONENTS_EXACTLY_INVARIANT
```

That is a valid non-affirmative source/measurement result, not an implementation invalidity.

### Audit complete and at least one pair differs

Proceed to the absolute (U^*) materiality gates.

The current script’s fail-closed default is appropriate until this aggregation is actually wired. Its tri-state logic already distinguishes a missing mandatory audit from a concluded degeneracy.

---

# 4. R3_CITABILITY

# **The proposed ratio/linear divergence does not establish a new R3 design defect**

There are two independent corrections.

## Correction 1 — the frozen contract registers the linear gate

Within the listed evidence, the authoritative R2/R3 contract freezes:

[
T_{\mathrm{stable}}
===================

U^**{\mathrm{stable}}
+
0.10B*{\mathrm{stable}},
]

[
T_{\mathrm{flex}}
=================

## U^*_{\mathrm{flex}}

0.10B_{\mathrm{flex}},
]

together with the explicit per-limb requirement:

[
\operatorname{LCB}_{95}(B_m)>0.
]

R3 carries those gate and branch semantics forward unchanged.

The frozen files do not independently register an unconditional ratio gate that may be interpreted when (B_m\le0).

Even if one reads the linear expression as a realization of

[
U^*/B\le-0.10,
]

the two are equivalent on the registered admissible domain (B>0). The separate positive-(B_m) requirement is precisely what protects that equivalence.

The hypothetical (B=-1) case lies outside the registered interpretation domain. It would fail the (B_m) gate and terminate before the linear materiality contrast was interpreted.

Therefore:

> The worked counterexample correctly shows why positivity is necessary, but does not show that R3 applied the linear gate outside the domain in which it represented the intended comparison.

## Correction 2 — the stable sign description is reversed

The question states:

```text
U*_stable = -3
SET is 3 G-units BETTER than KEEP
```

But:

[
U^*_{\mathrm{stable}}
=====================

## V_{\mathrm{SET}}

V_{\mathrm{KEEP}}.
]

Therefore (U^*_{\mathrm{stable}}=-3) means:

> SET is three (G)-units **worse** than KEEP.

That is why it points toward stable persistence.

The later conclusion—that (-3) does not clear a (-5) R4 margin—is correct. The prose explanation of its sign is not.

## The artifact did not identify a negative population normalizer

The artifact-derived point estimates were positive:

[
B_{\mathrm{stable}}=+0.180,
\qquad
B_{\mathrm{flex}}=+4.289,
]

while their lower bounds were non-positive. Some individual topology estimates were negative, but the registered population point was not.

The correct reading remains:

> A positive population normalizer was not established.

It is not:

> The population normalizer was proved negative.

## What R3 remains citable for

Within its previously accepted conditional execution scope, the R3 artifact may still be cited for:

1. the executed matched scalar observations;
2. the registered topology and event-support record;
3. the artifact-derived (B_m) and (U^*_m) distributions;
4. failure to establish a positive (B_m) lower bound on either limb;
5. retirement of the signed global-rotation normalizer as the R3 materiality scale;
6. the design risk that the global-rotation comparator is not demonstrated to be relevant to the focal effect.

## What it may not be cited for

It may not support:

* an R4 five-unit source result obtained by rethresholding the old data;
* persistence necessity;
* absence of persistence necessity;
* flexible-renewal necessity;
* an identified negative (B_m);
* an identified ratio inversion;
* primary-(G) component cancellation;
* natural-policy or algorithmic claims about R30 or D8.

The previous result semantics and portfolio update therefore stand. No additional R3 retraction is required.

---

# 5. CHALLENGES

## 1. Anchor E is not uniquely forced, but it is admissible

The primary objective does not prove that one cutoff-equivalent is the only possible materiality unit. It makes it a task-semantic, non-post-hoc choice with no fitted parameter. That is enough to freeze a confirmatory criterion.

## 2. The unequal per-step bars are not a flaw

Anchor E deliberately tests total external consequence. Anchor Q would test average-rate consequence. These are different scientific questions, not two normalizations of one unquestioned estimand.

## 3. Anchor Q remains underived

The form (q^*H_m) is available, but its level is not. It is therefore not a legal conclusion-bearing alternative in this round.

## 4. The R4-B failure is not a proof of impossibility

No positive pre-treatment opportunity scale was found. That route remains parked, but R4-A makes source retirement unnecessary.

## 5. “Calibration disappears” is false if branch 4 remains

Normalizer calibration disappears. A Part-A contradiction control remains conclusion-bearing and must receive a new absolute equivalence margin.

## 6. “Branches 4–10 keep unchanged” is false

At least four branch-system changes are necessary:

* branch 3 changes its causal pair set;
* branch 4 loses (B_{\mathrm{stable}});
* the expansion rule loses (B_m/T_m);
* flex-only positive evidence needs an explicit disposition.

## 7. The proposed R3 inversion is outside the registered gate domain

The positive-normalizer requirement was not merely a power preference; it was also the domain condition under which ratio language and the linear contrast agree. But because that requirement was explicit and first-match branch 3 preempted later interpretation, the hypothetical negative-(B) example does not reveal a new executed-design defect.

---

# Final portfolio

| Route                                              | Status                        | Rejection or reactivation condition                                                                                                 |
| -------------------------------------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **R4-A: five-unit cutoff-equivalent focal margin** | **Selected**                  | Reject only if a pre-run task-semantic argument shows one cutoff-equivalent is not a meaningful minimum consequence                 |
| **R4-Q: equal per-step QoS rate**                  | Parked                        | Reactivate only if an external (q^*) is supplied independently of R3                                                                |
| **R4-B: positive pre-treatment scale**             | Parked                        | Reactivate if a sign-fixed focal-commensurate scale is derived without treatment returns                                            |
| **S7-S3 carrier retirement**                       | Conditional fallback          | Select only if the full R4 contract cannot be frozen without post-hoc choices, or a valid R4 result later identifies source failure |
| **New source with inherent materiality unit**      | Retained alternative          | Raise if S7-S3 fails R4 or Part-A remains non-identifying                                                                           |
| **R3 global-rotation normalizer**                  | Retired for focal materiality | Reopen only after a prior analytical relation to focal (U^*) is proved                                                              |

## Scheduled action

**Freeze the full R4 contract around the five-unit absolute focal margin, including:**

* focal-arm component-invariance branch 3;
* the five-unit Part-A equivalence test;
* symmetric per-limb result semantics;
* a fresh evidence population;
* and an R4-specific expansion or no-expansion rule.

No implementation or environment compute is authorized by this review. D7.3 and D8 remain blocked pending a valid R4 result.
