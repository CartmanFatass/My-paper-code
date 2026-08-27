---
name: hmasd-marl-result-analysis
description: Use when an HMASD MARL direction must aggregate multi-seed results, compare paired algorithms, or interpret learning curves and failed runs after data collection.
---

# HMASD MARL Result Analysis

Produce a direction-local analysis note inside one scientific assignment. Use
only supplied evidence and allowed direction paths; accept explicit,
non-conflicting observations and leave other facts unbound. Workflow documents
are not scientific evidence. Do not execute, install, route, or define a claim
registry, manifest, directory tree, or new schema.

## Analysis note contract

Write six short sections:

1. **Analysis basis** — cite the supplied direction-level scientific authority
   and frozen design. Name the primary metric, contrast, independent unit,
   pairing/blocking, analysis population, and confirmatory versus exploratory
   status. Do not choose them after seeing results.
2. **Sample accounting** — report planned, completed, failed, and partial
   seed/configuration units by reason. Separate endpoint eligibility from curve
   availability. Preserve failures; follow the frozen incomplete-unit rule and
   state when missingness may be informative.
3. **Estimate and uncertainty** — aggregate nested episodes within each
   seed/configuration before cross-seed inference. For common-random-number A/B
   comparisons, analyze paired seed-level contrasts such as
   `d_s = mean_e(B_s,e) - mean_e(A_s,e)`. Report the effect, uncertainty interval,
   effective seed count, and any predeclared test or multiplicity rule. A
   p-value alone is not a result; non-significance does not prove equality.
4. **Curves and figures** — retain raw seed traces when feasible. Declare any
   smoothing as display-only, apply it consistently per seed, and never
   interpolate or extrapolate across missing runs. Compute uncertainty over
   seed-level values, show `n(t)`, and label pointwise intervals. Timesteps,
   episodes, agents, and vector lanes are not independent seeds.
5. **Failures and claim ceiling** — disclose OOM, non-finite, timeout, partial,
   and excluded runs in the main analysis summary. Distinguish a complete-panel
   claim from a complete-case or descriptive subset, and limit interpretation
   to the frozen environment, configurations, seeds, metric, and checkpoint.
6. **Computation specification** — name existing inputs, transformations,
   outputs, and an exact command only when a real runnable surface is supplied.
   Otherwise leave it unbound. Use the installed project stack.

## Quick reference

| Observed structure | Analysis treatment |
| --- | --- |
| Many episodes from one trained seed | Aggregate within seed; do not inflate `n` |
| A/B share seed/configuration | Preserve pairing and analyze seed-level contrasts |
| OOM or partial run | Retain, classify, disclose, and apply the frozen eligibility rule |
| Unequal curve lengths | Use observed points, report `n(t)`, no silent fill |
| Smoothed learning curve | Display aid only; inference uses declared seed-level quantities |
| Missing library or runner | Mark an implementation need; do not install or invent an API |

Without an owned output location or schema, provide note content only.

## Common mistakes

- Treating nested episodes or timesteps as independent seeds.
- Hiding failures or describing survivors as the planned population.
- Selecting a metric, checkpoint, smoother, test, or new ledger after results.
