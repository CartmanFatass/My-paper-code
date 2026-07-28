# D7.S R4 — absolute focal task-unit margin — frozen contract

```text
id=D7.S-R4
status=FROZEN_2026-07-28
supersedes=D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md (materiality scale only)
authority=rounds/20260728_r4_materiality_derivation/21_PRO_OPEN_RAW.md
prior_authority=rounds/20260728_d7_s_autopsy_result/21_PRO_OPEN_RAW.md
freeze_scope=materiality_scale|part_a_margin|branch_3_semantics|per_limb_result_states|expansion_rule|evidence_population
authorizes_implementation=false
authorizes_compute=false
```

**This contract authorizes neither implementation nor compute.** It records
External Pro's decision at freeze and is not edited afterwards; supersede it with
a new file.

## §0. Why R4 exists

R3's materiality scale was the signed empirical normalizer
`B_m = G(constructive_mixed) − G(null)`. The first formal run failed to establish
a positive `B_m` lower bound on either limb, and the artifact-only autopsy found
no positive evidence that the global rotation contrast is a useful scale for the
focal one-Δ SET-versus-KEEP effect. Status recorded:
`GLOBAL_ROTATION_NORMALIZER_RELEVANCE_NOT_DEMONSTRATED`.

**What failed was the scale, not source support and not a demonstrated causal
consequence.** S7-S3 is retained as the carrier because the prior evidence
established sufficient event support, legal focal interventions, no identified
opposite stable/flex direction, and no structural contradiction showing the
source cannot express the proposition.

## §1. The materiality gate — absolute, no denominator

```text
stable clears  iff  UCB95(U*_stable) < -5.0
flex clears    iff  LCB95(U*_flex)   > +5.0

U*_m = V_SET,m - V_KEEP,m,  a difference of window-summed primary G over H_m
delta_stable = delta_flex = 5.0 G-units
```

### The derivation of 5.0, recorded so it is auditable

Anchor E, the **cutoff-equivalent** margin. Primary `G` already declares its
exchange rates:

```text
G_t = qos_satisfaction_ratio - 2*return_constraint_cost - 5*new_cutoff - 10*new_depletion
```

Five is the smallest nonzero coefficient attached to a **discrete, window-local,
task-semantic** safety event. QoS and capped return cost are rate-like and their
one-step interpretation depends on the simulation clock; a new cutoff is a
discrete task consequence. The margin was fixed from the frozen weights alone and
**not** by inspecting any R3 `U*` magnitude.

**"Cutoff-equivalent" does not require a cutoff.** Five G-units may be realized by
any registered combination of QoS, capped return-cost, cutoff and depletion
differences. The anchor supplies an interpretable unit; it does not mandate which
component carries it.

**The same five units apply to both horizons, deliberately.** The proposition is
the *total task consequence of one renewal decision*, not its average rate. A
service cutoff does not become one quarter as important because the flex process
must be observed roughly four times as long. That five units is ≈3.60% sustained
QoS loss over `H_stable = 139` and ≈0.91% over `H_flex = 550` is the expected
consequence of evaluating cumulative task value over different causal windows,
**not an unfairness in the gate**. An equal per-step bar would define a different
proposition and is rejected.

The anchor is **not mathematically unique**. It is non-post-hoc, externally
interpretable, and fixed by pre-existing task semantics, which is what the
derivation required.

## §2. What R4 deletes, retains, adds

**Deletes.** `B_stable` and `B_flex` as materiality denominators; the per-limb
`LCB95(B_m) > 0` requirement; the normalizer-driven half of
`PRIMARY_G_DEGENERATE`; the R3 expansion predicate based on `B_m` and `T_m`.

**Retains.** The event definition; stable and flex certification; legal focal SET
alternatives; `U*_m = V_SET,m − V_KEEP,m`; primary `G`; `H_stable = 139`;
`H_flex = 550`; CRN pairing; topology-level inference; the `2/2` empirical-
maximization floor; the mandatory component persistence audit.

**Adds or modifies.** The fixed five-unit absolute margins; a focal-arm
component-separation predicate; a five-unit Part-A equivalence margin; an
R4-specific expansion rule; symmetric partial-result semantics.

## §3. Part-A must be rederived at the same anchor

"Calibration is no longer conclusion-bearing" is **too broad**. The *normalizer*
calibration disappears; the Part-A contradiction control does not.

`D_A = G(full_sync_SET) − G(constructive_mixed)` was tested against `±0.05·B_stable`,
which made a `B_stable`-dependent control conclusion-bearing. Under R4 it is
tested against the same absolute anchor:

```text
-5 < D_A < +5

PART_A_CONTRADICTION        iff  LCB95(D_A + 5) > 0  AND  LCB95(5 - D_A) > 0
full-sync materially worse  iff  UCB95(D_A + 5) < 0
otherwise                        PART_A_CONFORMANCE_UNRESOLVED
```

A disjoint Part-A contradiction-control block therefore remains
conclusion-bearing even though `B_m` calibration does not.

## §4. Branch 3 under R4 — focal-arm component invariance only

The normalizer half of branch 3 is retired. Branch 3 now means:

> On the registered focal action support, primary `G`'s four component sequences
> were exactly invariant between KEEP and every legal paired SET continuation on
> both limbs.

### The pair set — changed from R3, deliberately

For limb `m`, `P_m^R4` contains **every complete, CRN-paired evaluation
comparison** `(KEEP, SET(z))` for every qualifying event, every legal `z`, and
every registered evaluation replicate.

**Do not use the R3 calibration pair `(constructive_mixed, null)` for branch 3.**
That pair mattered because it defined `B_m`. R4 has no `B_m`, so the earlier
calibration-pair aggregation ruling is **R3-specific and does not carry
forward.** This supersedes the aggregation rule frozen on 2026-07-28 in the
autopsy-result round, which tied component separation to the normalizer source
controls.

### Aggregation and the global predicate

```text
components_invariant_m = AND over p in P_m^R4 of exact_paired_sequence_equal(p)
components_separate_m  = NOT components_invariant_m

primary_g_degenerate = NOT (components_separate_stable OR components_separate_flex)
```

One unequal complete pair refutes exact invariance. **No fraction threshold is
permitted** — 10%, 50% or 95% would turn an exact non-degeneracy assertion into
another unregistered materiality threshold.

Branch 3 fires only when **neither limb** contains any observed focal component
separation. If one limb separates and the other is invariant: do not emit global
branch 3, record the invariant limb explicitly, and allow only the separated
limb's materiality state to contribute to a positive claim.

### Missing audit and exact invariance are different outcomes

```text
audit missing or incomplete  -> INVALID_EVENT_ALIGNED_AUDIT
                                reason = MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING

audit complete, all pairs invariant -> PRIMARY_G_DEGENERATE
                                reason = FOCAL_KEEP_SET_COMPONENTS_EXACTLY_INVARIANT

audit complete, >=1 pair differs -> proceed to the absolute U* gates
```

The second is a **valid non-affirmative source/measurement result**, not an
implementation invalidity. A missing pair is neither equal nor unequal.

Completeness conditions: every qualifying event represented; every legal
candidate represented; both members of every CRN pair present; all four sequences
present at the registered horizon; no invalidated pair; serialized and in-memory
pair counts agree.

## §5. Symmetric per-limb result semantics

R3's branch map preserved stable-only positive evidence but had no authoritative
top-level outcome for *flex clears, stable does not*. R4 records **independent
per-limb states**:

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

**A valid flex positive may not be hidden under a stable-negative or generic
unresolved branch.**

## §6. Expansion

The R3 expansion predicate keyed on `B_m` points, `T_m` point directions and
unresolved bounds. **Those quantities no longer exist.** The R3 expansion set is
**not** automatically authorized for the new measurement.

Before any R4 run, either freeze an R4-specific one-expansion rule based on the
absolute-margin point directions and unresolved bounds, **or freeze no
expansion.** This contract does not yet choose between them; that choice must be
frozen before a run.

## §7. Evidence population — fresh, and mandatory

**The R3 artifact cannot be rethresholded at ±5 and reported as an R4 result.**
A fresh, untouched evidence population is required. The old artifact may inform
design and precision planning; it cannot confirm the newly chosen margin.

## §8. Launch preconditions

Carried forward and still binding:

1. The seven guard areas closed with paired negatives before any environment run
   — done as of `ccf162e0`, and the pooler reconstruction as of `5b91c398`.
2. The component audit aggregation of §4 wired, with the fail-closed default
   retained until it is. The current tri-state already distinguishes a missing
   mandatory audit from a concluded degeneracy, which Pro confirmed appropriate.
3. §6's expansion choice frozen.
4. A fresh evidence population identified.

`D7.3` and `D8` remain blocked pending a valid R4 result.
