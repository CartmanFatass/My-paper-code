# PM reconciliation — contract-grill mechanism

Date: 2026-07-25

```text
round=20260725_contract_grill_design
stage_commit=a859bc4ac535fc91d5e618b2934d83e189051336
raw=21_PRO_OPEN_RAW.md
verdict=CHANGES_REQUIRED
adopted=in_full
authority=external_pro
compute_authorized=none
science_status=FROZEN
```

Adopted in full. The direction is supported, the division of labour is sound and
the three-gate split is confirmed correct. The mechanism is **not closable** and
operates as an **advisory experimental reader** until the ten changes in the
final disposition are incorporated and V2 passes.

## What was wrong with my design, in order of importance

Four structural gaps, each of which I had left as a discretionary judgement:

1. **No non-discretionary gate-closing predicate.** I built three gates and no
   pass criterion for any of them.
2. **No lossless reader-to-Pro evidence channel.** I sat between the reader and
   Pro with no rule on what I could drop.
3. **No independently governed validation and grading.** I ceded thresholds but
   would still have graded the matches.
4. **No technique-validity boundary** for a method correctly specified and
   faithfully implemented but wrong for the estimand.

One premise of mine is also retired: I framed the fable reader as taking over
discovery. **Pro's own unmediated primary-evidence read is mandatory**, not
optional, and the architecture must retain three channels — primary reader,
fresh grill-the-grill, and Pro's independent read. The evidence Pro cites is our
own: fable found the tolerance and clustering defects, Pro found the
conditioning-history failure.

## Q1 — archetypes

**Retain all sixteen. Cut none.** Superficially similar pairs protect different
surfaces (2 vs 10, 7 vs 9, 10 vs 13, 1 vs 12, 11 vs 12). Archetype 13's
separation from 10 is confirmed: the G20 zero fixed point was an algebraic
absorbing state independent of noise, threshold, capacity, seed and budget, so no
threshold-reachability check could have caught it.

**Add archetype 17 — claim identifiability and branch interpretation.** Does the
branch license only the smallest supported or refuted unit? Distinct from 3: 3
asks whether evidence distinguishes FAIL from UNRESOLVED; 17 asks whether even a
perfectly resolved result would answer the claimed question.

**Burden is controlled by applicability predicates, not deletion.** Archetypes 4,
11, 15 and 16 are conditional — but a skipped one must be marked
`NOT_APPLICABLE` with a falsifiable reason and **may not silently disappear**.

**Coverage matrix.** The thirteen rows are insufficient. Add
*registration, authority provenance and executable binding*. Broaden the
natural-policy-transport row into the full **claim ladder**: access → statistical
identification → intervention-sensitive behaviour → natural-policy use →
held-out transport → integration claim. The Technique grill gets its own row and
must not be marked covered by Gate A's estimator/null row.

## Q2 — gate assignment

**Most archetypes have both a design limb and a realization limb.** Assigning
each exclusively to one gate would recreate the very gap between a correct
sentence and an incorrect executable meaning. Pro supplied a full 17 × 3 matrix;
it is adopted verbatim into the skill.

Gate A is **not** reduced by deleting universal classes. Twelve are universal
core; 4, 10, 11, 15, 16 are triggered-but-mandatory. If burden is too high,
reduce the *depth* of irrelevant triggered modules, never the core.

Gate B-core is specified as **twelve observables**, not module requirements — so
refactoring can neither satisfy nor violate the ruling by renaming files. This
also resolves my Q2b, which had wrongly asked Pro to bless a module list.

Gate B-delta stays separate and is **diff-scoped**.

## Q3 — what closes a gate

The largest change. **A gate closes only on a mechanical predicate** over the
ledger, coverage matrix, reader evidence, Pro rulings and bound artifacts.
Neither the reader nor I may close one by asserting enough has been checked.

The ledger's single ruling field is **overloaded and must be split three ways**:

| Axis | Values |
|---|---|
| Authority route | `PROTECTED_PRO`, `PM_ENGINEERING` |
| Workflow state | `DISCOVERED_UNTRIAGED`, `AWAITING_PRO_RULING`, `DECIDED`, `DEFERRED_OUT_OF_SCOPE`, `BLOCKED_UNRESOLVED`, `SUPERSEDED` |
| Ruling | `ACCEPTED`, `MODIFIED`, `REJECTED` |

A PM engineering decision is `PM_ENGINEERING + DECIDED` — **never recorded as a
Pro acceptance**. Every entry carries authority route, state, ruling source,
ruling artifact and revision.

**No generic open entry may remain.** Implementation may begin past a deferral
only when it is `DEFERRED_OUT_OF_SCOPE`, has no implementation binding on the
current path, cannot change the current claim, and has an explicit re-review
trigger. Always blocking: unresolved estimand, probability or credit
factorization, branch meaning, threshold, support, measure, comparator, data
split, snapshot, or source identifiability.

**I may not waive a missing coverage row or reinterpret silence as
`NOT_APPLICABLE`.** Pro states a bounded formula rather than a completeness
claim: *"within the reviewed evidence and declared coverage scope, I find no
remaining unresolved protected decision."*

**Certificate voiding**: my Pro-only rule was too narrow. **Any change by any
actor** to a protected decision, its implementation binding, or a bound evidence
artifact voids the affected certificate — including my own amendment to a
nominally engineering choice when it changes a bound runtime observable. Add
`depends_on`, `affects`, `certificate_scope`, `re_review_trigger`; invalidate the
transitive dependency closure; **fail closed** when impact cannot be localized.

## Q4 — the channel to Pro

Reader and grill-the-grill raw outputs are **sealed evidence artifacts named in
the question's allow-list**. I may organize; I may not make findings disappear.

A **finding-disposition manifest** records every finding ID as
`FORWARDED_AS_DECISION`, `MERGED_WITH`, `EXACT_DUPLICATE_OF`, `PM_ENGINEERING`,
`FACTUALLY_UNSUPPORTED`, or `OUT_OF_SCOPE`. Nothing is omitted, and **uncertainty
defaults to forwarding**. Merges must preserve all source IDs and may not join
two findings whose reversal affects different quantities or branches.

I may drop from the decision tree only an exact duplicate, a demonstrable factual
error, or a pure layout/naming matter — and it remains visible in the manifest so
Pro can overrule the classification. Explicitly **not** grounds to drop: that I
think the concern mistaken, the fix inconvenient, another test seems to cover it,
or that it would raise Pro's burden.

## Q5 — validation, now independently governed

**V1 proves wiring only. V2 is the adoption gate. V3 is required for specificity
and burden.**

| Tier | Requirement |
|---|---|
| V1 | 100% critical recall; 100% on directly encoded critical instances. A miss is a wiring or instruction failure. Does not establish transfer even at 100%. |
| V2 | ≥2 contracts from distinct failure families; **100% critical recall**; ≥80% material recall; **no contract rescued by aggregate recall from the other**. One critical miss → advisory only. |
| V3 | Zero fabricated critical blockers; ≤1 noncritical false escalation per contract; zero authority violations. |

Both V1 and V2: evidence-grounded rate 100%, authority violations 0, duplicates
≤15%, precision ≥70%, and **burden ratio ≤1.5** (deduplicated Pro ruling nodes
per confirmed actionable finding). My own "fifteen of nineteen via fifty
questions" example fails on both counts — 30% precision, ratio ≈3.33.

**Neither I nor the reader may grade.** A blinded independent adjudicator maps
findings to frozen ground-truth IDs; Pro resolves disputes, novel claims, and
anything whose resolution changes pass/fail. A match requires **all three**: same
violated invariant, same smallest consequence, and an independently established
evidence path. Language similarity is neither necessary nor sufficient — which
also retires the auto-void-on-similar-wording rule I had proposed.

**V2 selection must be frozen before V1 output is read.** Objective eligible pool
of stage commits not used to build the casebook, frozen exclusions, deterministic
seeded selection or an independent selector. I may assemble the pool; I may not
choose contracts after seeing V1 performance. An independent curator builds the
defect inventory blinded; Pro seals criticality before V2 runs.

**Tuning versus abandonment.** Mechanical invalidation (contamination, forbidden
-path access, broken harness, failed containment) may be repaired and rerun.
A **conceptual miss may not be tuned on the same holdout** — adding the missed
instance to the casebook and rerunning there is not validation, and a redesign
needs a fresh holdout. If two independently constructed versions fail on separate
V2 sets, **abandon the single-reader architecture** rather than enlarging the
casebook.

**Metamorphic pair** is mandatory V3 evidence but not a complete substitute for a
negative control. If no contract can honestly be presumed clean, V3 is labelled
`METAMORPHIC_SPECIFICITY` and other findings are adjudicated rather than assumed
false — which answers the wrinkle I raised.

## Q6 — authority boundary

The facts-yes / rulings-no line is confirmed. Two limits added:

The griller **may not silently choose the semantics of its own diagnostic** when
that choice affects the conclusion — probe distribution, null construction,
clustering unit, tolerance, policy snapshot, action support. It may say *"under
diagnostic choice X, I observed Y"*; it may not say *"X is the correct protected
choice."* That is a Pro question.

Pre-digestion is not the hazard; **lossy** digestion is. Pro receives raw
evidence whenever the ruling may turn on distribution shape, cluster dependence,
outlier sensitivity, exact reachability, numerical cancellation, or competing
causal explanations. **A single scalar may not replace raw samples.**

The five-field item shape stands, plus metadata: `finding_id`, coverage row,
authority classification, evidence confidence, raw-evidence path, merge ancestry.
The **conditional decision tree is built separately from the factual finding
inventory**, so a compact tree never becomes the only record of what was observed.

## Q7 — six residual classes, and what they imply

1. **A wrong numerical method faithfully implementing a coherent contract** — the
   most important residual, and the reason the Technique grill is separate.
2. **Regime- or scale-dependent runtime failure** — the bounded screen must keep
   an operational-invalid branch and exact runtime provenance. Engineering
   outcomes, not scientific negatives.
3. **A benchmark that does not separate the mechanism** — remains the job of
   source controls, matched reductions, comparator equivalence, intervention
   tests and held-out natural execution.
4. **Shared epistemic blind spots** — the mechanism reduces correlated omission
   and cannot prove absence of unknown unknowns. Mitigations are empirical only.
5. **Drift outside tracked code** — certificates must bind runtime configuration,
   source commit, environment identity and conclusion-bearing command arguments,
   not only source files.
6. **Correct evidence, incorrect final interpretation** — the result grill stays
   distinct.

## What I now own

1. Add archetype 17 and the separate Technique-grill class and trigger.
2. Add the registration/authority/binding coverage row; broaden transport into
   the claim ladder; give Technique its own row.
3. Adopt the 17 × 3 gate matrix and the twelve Gate B-core observables.
4. Build the three-axis decision ledger and the mechanical gate-close predicate.
5. Build the finding-disposition manifest and seal reader raws into the allow-list.
6. Add Pro's standing unmediated-read instruction to every Gate A round.
7. Freeze V1–V3 thresholds, selector, pool, ground truth, matcher and grader —
   **all before V1 runs**, and the V2 selection before V1 output is *read*.
8. Rewrite certificate voiding to any-actor, with dependency closure and
   fail-closed scoping.

## Consequences for the frozen G20R2 rework

It may use the experimental reader **only under the existing full Pro review
path**. Every protected decision must still be ruled directly by Pro. The reader's
silence licenses nothing.

If V2 later fails: experimental certificates expire, Pro's existing rulings remain
authoritative, and any contract that relied on the reader's silence must be
regrilled before a bounded screen.

## Honest note on cost

The mechanism is now substantially larger than what I proposed, and most of the
additions are governance rather than discovery. That is the correct trade only if
it is actually cheaper than another cycle like the one that produced it — 5,700
lines built against a contract that then required changes. The burden ratio of
≤1.5 is the number that will tell us, and it is now a pass/fail criterion rather
than an aspiration.

No compute is authorized. Science remains frozen.
