# D7.S audit run 2 — scientific disposition

**Stage reviewed:** `76c1ce328b57191f7a1c6f873684de041d12bbc3`

## 1. VERDICT_Q1

# **`PRIMARY_G_DEGENERATE`**

Run `30289161086` is scientifically dispositioned as **`PRIMARY_G_DEGENERATE`**, not as the recorded `SOURCE_NECESSITY_UNRESOLVED`.

R3 carries R2’s primary-(G), gate, expansion, and result-branch semantics forward without modification.  R2 §7 requires branch 3 and termination before margin interpretation whenever (B_m) cannot establish a positive source-control contrast; R2 §8 separately requires each interpreted limb to satisfy

[
\operatorname{LCB}_{95}(B_m)>0.
]

The recorded artifact has:

[
\operatorname{LCB}*{95}(B*{\mathrm{stable}})=-0.0773669869,
]

[
\operatorname{LCB}*{95}(B*{\mathrm{flex}})=-8.6488333493.
]

It nevertheless records branch 10.

That mismatch is explained exactly by the implementation:

* `decide_branch` places `PRIMARY_G_DEGENERATE` at precedence 3;

* every later stable/flex branch requires a positive limb-specific (B_m) lower bound;

* `assemble_audit_result` hardcodes `primary_g_degenerate_flag=False`.

This is **not** `INVALID_EVENT_ALIGNED_AUDIT`. The event histories, pairing, topology provenance, support, and numeric bootstrap outputs remain usable; the defect is in the deterministic post-estimation branch mapping. The pooled evidence is mechanically clean, has zero invalidated pairs, passes support on all eight calibration and audit topologies, and records seed-controlled episode worlds.

The correct preservation rule is:

* leave the historical JSON artifact unchanged;
* record that its emitted branch was mislabelled;
* attach the authoritative scientific disposition `PRIMARY_G_DEGENERATE`;
* do not rerun the experiment merely to rewrite a string.

Applying branch 3 post hoc is not a new result-sensitive choice. It is application of a branch and input condition frozen before the run to bounds that the artifact already contains.

---

## 2. VERDICT_Q2

# **Use the disjunctive definition across limbs**

Define:

[
b_{\mathrm{stable}}^{+}
=======================

\mathbf 1!\left[
\operatorname{LCB}*{95}(B*{\mathrm{stable}})>0
\right],
]

[
b_{\mathrm{flex}}^{+}
=====================

\mathbf 1!\left[
\operatorname{LCB}*{95}(B*{\mathrm{flex}})>0
\right],
]

and wire:

[
\boxed{
b_m_\mathrm{positive_lcb}
=========================

b_{\mathrm{stable}}^{+}
\lor
b_{\mathrm{flex}}^{+}
}
]

Therefore the global branch-3 condition arising from the normalizers is:

[
\neg b_m_\mathrm{positive_lcb}
==============================

\left(
\operatorname{LCB}*{95}(B*{\mathrm{stable}})\le0
\right)
\land
\left(
\operatorname{LCB}*{95}(B*{\mathrm{flex}})\le0
\right).
]

On this run both terms fail, so branch 3 fires under either proposed aggregation. The disjunctive ruling matters prospectively.

## Why not conjunctive?

A conjunctive definition,

[
b_{\mathrm{stable}}^{+}\land b_{\mathrm{flex}}^{+},
]

would make the global degeneracy branch preempt a valid result from one limb merely because the other limb’s normalizer failed.

That would conflict with the frozen partial-result branches:

* branch 7 preserves an identified stable-persistence result while flex remains unresolved;
* branch 8 preserves an identified flex non-materiality result while stable does not clear;
* branch 9 preserves an identified stable non-materiality result.

Each limb’s substantive predicate already protects itself:

* stable clearance or stable affirmative miss requires positive (B_{\mathrm{stable}}) LCB;
* flex clearance or flex affirmative miss requires positive (B_{\mathrm{flex}}) LCB.

Thus disjunction does **not** allow an unnormalized limb to make a claim. It merely prevents the invalid limb from erasing a valid result belonging to the other limb. This follows the project rule to update the smallest implicated unit rather than broaden a failure unnecessarily.

The production payload should record the two statuses separately:

```text
stable_b_identified = b_stable_lcb > 0
flex_b_identified   = b_flex_lcb > 0
```

If one is false and the other limb resolves, the result branch may preserve that valid limb, while the payload explicitly labels the other as `NORMALIZER_NOT_IDENTIFIED` rather than hiding it under a generic “unresolved.”

The same principle should govern the component-invariance limb of branch 3. Conceptually:

```text
stable_measurement_valid =
    stable_components_separate AND stable_b_identified

flex_measurement_valid =
    flex_components_separate AND flex_b_identified

primary_g_degenerate_flag =
    NOT (stable_measurement_valid OR flex_measurement_valid)
```

For the present result, the component-invariance input is immaterial: neither limb establishes a positive normalizer.

---

## 3. VERDICT_Q3

# **Expansion is not admissible**

The Project Manager’s corrected reading is right.

R2 §9 permits the single expansion only when **all** of the following hold:

1. conformance passes;
2. support passes;
3. both relevant (B_m) point estimates are positive;
4. both relevant (T_m) point estimates have their intended signs;
5. one or more required bounds remain unresolved.

It explicitly prohibits expansion on a wrong-direction point.

The reconstructed points are:

[
B_{\mathrm{stable}}=+0.180139,
\qquad
B_{\mathrm{flex}}=+4.288854,
]

so the point-level (B_m) condition passes. But:

[
T_{\mathrm{stable}}
===================

+1.272088
\quad
\text{where the intended sign is negative},
]

[
T_{\mathrm{flex}}
=================

-4.551287
\quad
\text{where the intended sign is positive}.
]

Both point-direction conditions fail. The expansion predicate is therefore false independently of whether the result is labelled branch 3 or branch 10.

The fact that `expansion_allowed()` is dead code is an implementation/governance defect; it does not make the scientific rule optional. The function itself encodes the intended conjunction, but the CLI currently permits a human to bypass it by supplying the expansion seeds.

Accordingly:

* do not run topologies `20260734–20260741`;
* do not add replicates;
* do not reinterpret the expansion as an ordinary power increase;
* do not use the positive (B_m) point estimates to bypass their non-positive lower bounds.

The point estimates are legitimate for applying §9: they are deterministic functions of the recorded `topology_units`, use the registered true-argmax point path and equal topology weighting, and the same unit mapping reproduces all six recorded bootstrap bounds. But they are **expansion diagnostics**, not replacements for confidence-bound result gates.

---

## 4. SMALLEST_UNIT

## What the run supports

The run supports the following narrow proposition:

> On the frozen eight-topology, `heldout_low`, S7-S3 population, the primary-(G) contrast between `constructive_mixed` and `null` did not establish a positive population-level normalizer on either the stable or flex limb.

This is stronger than an operational failure:

* all eight topology shards completed;
* conformance, support, topology identity, CRN pairing, and episode-world provenance passed;
* the failure occurs in the conclusion-bearing calibration quantities themselves.

The run also supports a heterogeneity lemma. The topology-level quantities are not merely all close to one weak mean; they vary widely and change sign, including (B_{\mathrm{flex}}) values from approximately (-17.15) to (+19.03).

## What the run retires

It retires, for this frozen R3 route:

> **The signed empirical normalizer**
>
> [
> B_m
> ===
>
> ## G(\texttt{constructive_mixed})
>
> G(\texttt{null})
> ]
>
> **as an identified positive materiality scale for the joint D7.S source-necessity test on the registered S7-S3 population.**

This is the smallest failed unit:

```text
primary G
× constructive_mixed-versus-null calibration pair
× signed B_m denominator
× registered topology population
```

It does **not** retire primary (G) as the task objective by itself. The observed problem may be caused by:

* a source-control comparator whose ordering changes by topology;
* cancellation between QoS and safety components;
* or the signed contrast being unsuitable as a denominator even though both controllers are meaningful.

Nor does the result establish that primary (G) is arm-invariant. Branch 3 fires here through failure to identify positive (B_m), not through demonstrated equality of all component sequences.

## What the run does not settle

It does **not** support a negative conclusion that:

* stable persistence is unnecessary;
* flexible renewal is unnecessary;
* the S7-S3 source lacks heterogeneous renewal urgency;
* R30 cannot express heterogeneous lifetimes;
* or D8 is algorithmically false.

The wrong-direction (U^*) and (T_m) point estimates are scientifically important diagnostics, but they cannot carry the registered materiality interpretation when the required positive scale has not been identified. A negative lower confidence bound is also not proof that the population (B_m) itself is negative; it says the audit failed to establish that it is positive.

The correct portfolio update is therefore:

| Object                                      | Status                            |
| ------------------------------------------- | --------------------------------- |
| D7.S R3 normalizer/measurement pair         | **Retired for this frozen route** |
| S7-S3 source-necessity proposition          | **Unjudged**                      |
| Primary (G) task objective                  | Retained, under question          |
| R30 carrier                                 | Unchanged                         |
| D7.3                                        | Blocked                           |
| D8                                          | Blocked                           |
| Eight-topology support/provenance apparatus | Retained lemma                    |

This is consistent with the durable result semantics: a valid measurement that cannot identify its intended proposition updates the measurement or benchmark–comparator pair, not the whole algorithm family.

---

## 5. NEXT_ACTION

# **Run one artifact-only normalizer-identifiability autopsy and re-derivation**

The next scientific action is **not** another environment run.

It is a zero-new-data analysis of the completed artifact, followed by a source-level normalizer derivation. It should be frozen as diagnostic rather than retroactively treated as an R3 result.

The action has three predeclared outputs.

### A. Recover the missing standalone distributions

Using the same registered topology/event bootstrap and the stored `topology_units`, compute and report full two-sided intervals—not merely points or the one bound needed by R3—for:

[
B_{\mathrm{stable}},
\quad
B_{\mathrm{flex}},
\quad
U^**{\mathrm{stable}},
\quad
U^**{\mathrm{flex}}.
]

Also report:

* the per-topology values and signs;
* topology sign frequency;
* between-topology spread;
* (B_m)–(U^*_m) association;
* component decomposition from already-recorded fields where available.

This does not create new evidence or rescue R3. It localizes the failure already recorded.

### B. Separate the live causal explanations

| Explanation                                                | What would raise it                                                                                        |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **N1 — signed-normalizer failure**                         | (B_m) crosses zero by topology while (U^*_m) retains a coherent direction                                  |
| **N2 — source proposition points the opposite way**        | standalone (U^**{\mathrm{stable}}) is positively resolved and/or (U^**{\mathrm{flex}}) negatively resolved |
| **N3 — primary-(G) component cancellation**                | constructive improves QoS but worsens return/cutoff/depletion components enough to reverse (B_m)           |
| **N4 — one global topology population is non-identifying** | stable or flex effects form reproducible topology-dependent regimes rather than one population effect      |

### C. End in one of two decisions

1. **Freeze an R4 measurement with a treatment-independent positive scale**, or an unnormalized task-unit materiality criterion whose semantics are derived before another run; or
2. **Retire S7-S3 as the carrier of this source-necessity proposition** and move the carrier-capacity test to a source with a provably ordered or otherwise identified materiality scale.

Candidate replacement scales must be positive by construction and independent of the observed treatment sign. Plausible families include:

* a horizon-specific task-unit range derived from the registered primary-(G) semantics;
* an absolute task-consequence floor stated directly in (G) units, removing the ratio;
* a different source control only if its ordering can be proved before data.

The following are prohibited:

* replacing (B_m) by (|B_m|) after seeing its sign;
* flipping the normalizer sign by limb;
* clipping negative calibration effects to zero;
* changing primary (G) merely to make the existing comparator positive;
* adding the expansion topologies;
* or rerunning R3 with a different threshold.

Changing primary (G) should be reopened only if an independent task-semantic derivation shows that its QoS/safety combination is itself the wrong external objective. Altering it because branch 3 fired would be post-result metric rescue. The project contract permits correction of a definition or measurement while preserving the observation, but forbids rescuing a valid adverse result by changing its metric, threshold, or budget.

The implementation work already scheduled—wiring branch 3, recording point estimates, and enforcing §9—is necessary technical closure. It is not the next scientific evidence action.

---

## 6. CHALLENGES

### Checked and accepted

1. **The recorded branch is mislabelled.** The correct frozen-contract disposition is branch 3.
2. **The result remains quantitatively usable.** The unreachable branch did not corrupt trajectories, pairing, bootstrap units, or recorded bounds.
3. **The expansion is forbidden independently of Q1.** Both (T_m) points have the wrong direction.

### Checked and corrected

1. **The conjunctive aggregation is not the right prospective wiring.** It would allow a failed limb to erase a valid result from the other limb and would undercut branches 7–9. The global flag should use disjunctive limb validity, with per-limb diagnostic statuses preserved.

2. **`PRIMARY_G_DEGENERATE` does not establish that primary (G) itself is defective.** On this run it means the registered primary-(G) source-control contrasts did not establish positive normalizers. The implicated object is the objective–comparator–normalizer measurement pair.

3. **The point estimates do not support an identified negative source-necessity result.** Their wrong signs block expansion and lower the plausibility of the intended source claim, but the frozen materiality gate is undefined as a ratio-scale claim without positively identified (B_m).

4. **A non-positive LCB is not proof that the true (B_m) is non-positive.** The point estimates are positive. The correct statement is “positive calibration contrast not established,” not “constructive is proved no better than null.”

5. **The earlier opposition between the two branch labels was overstated for this run.** Branch 10 would ordinarily preserve a possibility of expansion, but §9 independently rules it out because both (T_m) points have the wrong sign. The label still matters because it localizes the failure and prevents margin interpretation; it does not alter the expansion decision here.

6. **More power is not the next action.** The run has already consumed the only frozen initial population, and the expansion predicate is false. The next decision must concern the normalizer, source-control ordering, or source suitability—not sample size.

The durable smallest conclusion is therefore:

> **D7.S R3 produced a valid matched observation but an unidentifiable materiality scale. The result closes this measurement route, not the heterogeneous-renewal research question.**
