# Reconciliation — the autopsy result

Ruling: `21_PRO_OPEN_RAW.md`, stage commit `6430ef96`. Workflow 2 closes here.

## Overall disposition, quoted

> The completed artifact provides no positive evidence that the global
> `constructive_mixed − null` contrast is a useful scale for the focal one-Δ
> SET-versus-KEEP effect.

Registered status: `GLOBAL_ROTATION_NORMALIZER_RELEVANCE_NOT_DEMONSTRATED`. The
global normalizer is **retired for this claim**, reopenable only with a prior
analytical relation to focal `U*`.

## Where Pro corrected this conversation — seven challenges

Recorded because a question's errors are appended, never edited away.

1. **"The normalizer is unrelated to the effect" is not established.** My
   inference. The association intervals encompass strong negative *and* positive
   relationships and the leave-one-out estimates are unstable. The supported
   statement is **"relevance not demonstrated"**, not "unrelated". N5 moves the
   portfolio by prioritising focal-compatible scale design; it does not
   independently retire a comparator. *I marked that reading as inference, which
   is what made it correctable — but I should have written the weaker sentence.*
2. **The N1 row was invalid as implemented, and is discarded.** A genuine code
   defect, verified against source: the call concatenated the stable and flex
   per-topology vectors into one 16-element input, then evaluated it against the
   `U*_stable` interval and stable-only leave-one-out points — mixing two
   horizons, two causal classes, two differently scaled `B_m` distributions and
   two `U*` directions. `N1 = compatible (moderate)` must not be quoted.
3. **N4 "material" was overstated.** Only `B_stable` has a nonzero adjusted
   ratio; the other three are exactly zero because within-topology variance
   exceeds between-topology point variance. The accurate statement is *limited
   topology contribution for artifact-derived `B_stable`; topology-dominant
   variation not established for any quantity*. The stratify-or-expand
   recommendation **is not selected**.
4. **The N2 classifier was prospectively too conjunctive** — it reserved
   `resolved` for both legs where either leg alone raises N2. The `not resolved`
   result here is unchanged; the vocabulary was wrong.
5. **"N5 raised" is a hypothesis status, not an acceptance test.** Readable only
   as *the comparator-mismatch explanation remains important enough to affect
   design*. Never as a statistically identified mismatch.
6. **My two aggregation candidates were not different.** "All pairs equal implies
   invariant" and "any unequal pair implies separate" are exact complements. I
   offered them as alternatives; that was a logical error. A fraction rule was
   the only genuinely distinct candidate, and it is rejected.
7. **The instrument's safe stop is appropriate.** The fail-closed
   `component_invariance_evaluated=False` default — the correction I made against
   the arriving implementation's fail-open `True` — is endorsed as the correct
   state.

**Already repaired in `scripts/d7s_normalizer_autopsy.py`:** challenges 2, 3, 4
and the 5 vocabulary gloss. N1 is now evaluated separately by limb; N4 names
which quantities show limited contribution instead of promoting a maximum to a
global label, and only nominates stratification on genuine dominance; N2 reports
its two legs separately. A corrected re-run is under way — the four standalone
distributions and the R4 decision are unaffected by all three, per the ruling.

## The aggregation rule — the blocker is closed

```text
components_separate_m = OR over p in P_m of NOT exact_paired_sequence_equal(p)
```

where `P_m` is the complete set of qualifying **calibration** source-control
pairs `(constructive_mixed, null)` for limb `m`. A limb is component-invariant
only if **every** complete paired continuation has exactly equal QoS, capped
return-cost, cutoff-transition and depletion-transition sequences; **one unequal
pair refutes exact invariance.** No fraction threshold is permitted — a
proportion would silently turn an exact structural-degeneracy check into a new
statistical materiality gate, and R2 already assigns materiality to the `B_m`
confidence bound.

**Branch-3 input is the calibration pairs only.** The audit block's
KEEP-versus-each-SET equality records stay mandatory evidence for component
cancellation analysis and `U*` arm verification, but they do not define whether
the *normalizer source controls* are component-separable. The implementation
already records the two separately, which turns out to be the right shape.

**Completeness is load-bearing.** Before `component_invariance_evaluated=True`:
one calibration equality record per qualifying calibration event per limb; both
CRN members present; all four sequences at their registered horizon; no
invalidated pair; serialized and in-memory pair counts agreeing; and the focal
audit records complete too. *A missing record is not "equal" and not "separate"
— it means the audit was not evaluated and the run stays fail-closed.*

The branch logic renames the middle gate to `component_audit_complete`, and adds
a consistency assertion: **a strictly positive `B_m` lower bound with every
associated component sequence exactly equal is internally inconsistent and must
be invalidated**, not read as an ordinary branch-3 result — exact sequence
equality implies exactly equal `G`, which cannot coexist with an identified
positive `B_m` from the same pairs.

**Activation timing: wire it as part of the R4 instrument closure. Do not rerun
R3 merely because branches 4–10 become reachable.**

## Selection floor

`2/2` remains admissible. Selection instability is a **material qualifier on
precision, not an estimand defect** — implicated as a plausible contributor to
low precision, not as a reason to invalidate. It does not explain the normalizer
failure.

## Next action, and the portfolio

**Selected: derive and pre-freeze an R4 absolute task-unit materiality
criterion**, or the positive pre-treatment scale as the live alternative. Zero
compute: derive one non-arbitrary margin, construct its zero-denominator and
sign counterexamples, freeze its branch semantics, and decide whether it is
scientifically meaningful **before any implementation or environment run**.

| Route | Status |
|---|---|
| R4 absolute focal task-unit margin | **selected for derivation** |
| R4 positive pre-treatment scale | live alternative |
| S7-S3 carrier retirement | conditional fallback |
| Global `constructive_mixed − null` normalizer | **retired for this claim** |
| Topology stratification | not selected |
| Higher selection volume | parked |

*"No environment compute, expanded topology set, or R3 rerun is selected by this
ruling. D7.3 and D8 remain blocked."*

## The standing constraint this creates

A future measurement **may not** use a global source-control contrast to scale a
focal renewal effect merely because both are measured in `G`. It must either use
an arm-independent task scale, or establish analytically — **before data** — that
the proposed normalizer is commensurate with the focal one-Δ intervention.
