# Scientific ruling — R4 contract completion

**Stage reviewed:** `b977e1883c0037e83a39ed46c099ccf6fa2fb7de`

## Overall disposition

# **FREEZE AFTER MODIFICATION**

The substantive R4 choices already recorded are faithful:

* the absolute five-(G)-unit focal margins;
* the removal of (B_m) from materiality;
* the five-unit Part-A equivalence margin;
* focal KEEP-versus-SET component invariance;
* fail-closed component-audit semantics;
* and symmetric preservation of flex-only evidence.

The two deliberately open choices are resolved as follows:

1. **R4 has no adaptive expansion.**
2. **The primary R4 evidence population must use new, previously unobserved topology seeds, not merely new episodes under the eight R3 topologies.**

Freeze the R4 topology set as:

```text
20260734
20260735
20260736
20260737
20260738
20260739
20260740
20260741
```

These were the predeclared but unused R3 expansion seeds. Under R4 they become the **initial and complete** topology population, not an expansion set. The R3 topologies `20260726–20260733` must not enter R4 inference.

The current file is therefore not yet a complete frozen contract despite its header. It must be superseded once this ruling, the complete result mapping, and the exact fresh-population bindings are incorporated.

No implementation or compute is authorized by this review.

---

# 1. EXPANSION

## Decision: **no expansion**

R4 receives exactly one fixed evidence population. There is no conditional second topology block, no episode-count increase, and no replicate-volume increase after any R4 statistic has been read.

The formal design is:

```text
8 fresh topologies

per topology:
    8 Part-A control episodes
    8 focal-audit episodes

n_select = 2
n_eval   = 2

no expansion
```

The R3 one-expansion rule cannot carry forward because its decision variables—(B_m) and (T_m)—were deleted by R4. The previous ruling explicitly required either a newly frozen R4 rule or no expansion.  The current R4 file accurately leaves that choice open.

## Why no expansion is selected

### A. It preserves a fixed confirmatory population

The five-unit margin was chosen after the R3 result, even though it was derived from pre-existing task semantics rather than fitted to R3 magnitudes. A fixed, untouched R4 population gives that new criterion its cleanest confirmatory interpretation.

### B. It avoids an unregistered sequential-inference problem

A rule that inspects the initial point estimates and confidence bounds before deciding whether to add topologies is an adaptive sampling design. Merely pooling sixteen topologies and applying the ordinary final 95% bootstrap bounds would not automatically account for that stopping rule. The R3 design did not contain an alpha-spending or confidence-sequence construction.

It is unnecessary to add that inferential machinery when the scientifically legitimate outcome “R4 remains unresolved on its fixed population” already exists.

### C. It prevents power rescue

The project contract requires mixed and underpowered results to remain unresolved and prohibits rescuing a result through post-result changes to budget, metric, threshold, seed, or model.  A predeclared expansion can sometimes be valid, but here it would add complexity to a measurement whose predecessor already accumulated substantial audit machinery.

### D. More topologies would not directly cure candidate-selection uncertainty

The `2/2` floor carries action-candidate uncertainty through the nested bootstrap. More topologies could narrow population uncertainty but would not directly improve the within-event empirical maximization. R2 explicitly states that instability should widen or prevent resolution rather than invalidate the measurement or trigger automatic tuning.

## Exact operational boundary

The following are **not** expansion:

* restarting a killed or corrupted shard at the same commit with the same topology and episode seeds;
* regenerating a missing artifact from byte-identical completed topology units;
* rerunning a formally invalid operational path before any valid result exists.

The following **are** prohibited additions:

* another topology;
* another episode under a completed topology;
* another selection or evaluation replicate;
* pooling R3 observations with R4;
* replacing an R4 topology after observing that it has poor support or an adverse margin.

If the fixed R4 result is unresolved, it remains unresolved. Any later evidence action requires a new scientific question and cannot be labelled an R4 expansion.

---

# 2. POPULATION

## Decision: fresh means fresh at the highest inferential unit

R3 models the source population hierarchically:

[
T\sim P_T,
\qquad
W\sim P(W\mid T),
]

where topology (T) is the upper inferential unit and user worlds are nested episode-level draws conditional on topology.  R2 likewise resamples topologies as the top-level bootstrap unit and gives them equal weight.

Consequently:

> **New user worlds, energy permutations, and episodes under the same eight R3 topologies would be fresh conditional observations, but not a fresh untouched evidence population for the registered topology-population claim.**

The R3 topologies have already been:

* measured;
* included in the normalizer autopsy;
* inspected topology by topology;
* and used to motivate the transition to R4.

Reusing them would test R4 conditional on an already observed empirical topology panel. That could be a useful later replication, but it cannot carry the primary “fresh population” requirement.

## Frozen R4 topology population

Use exactly:

```text
TOPOLOGY_SEEDS_R4 = (
    20260734,
    20260735,
    20260736,
    20260737,
    20260738,
    20260739,
    20260740,
    20260741,
)
```

R2 registered these as the only possible second block but did not authorize their use absent its expansion predicate.  This ruling explicitly repurposes them as R4’s initial fixed population. They are not inherited through R3 expansion authority.

The development topology remains:

```text
20260725
```

and carries no scientific reading.

## Frozen nested draws

For each R4 topology, use:

```text
Part-A control block:
    episode indices 0–7

focal audit block:
    episode indices 0–7
```

The blocks remain disjoint through their block namespace, episode seeds, energy-permutation seeds, user-world seeds, and continuation-stream seeds.

R4 should have its own evidence-population/seed namespace, for example:

```text
D7_S_R4_ABSOLUTE_FOCAL_MARGIN
```

while retaining the existing hash field structure and CRN relationships. The topology seed, block, episode index, limb, event, candidate, phase, and replicate continue to determine the corresponding streams. The existing implementation derives episode, energy, user-world, selection, and evaluation streams from these registered identifiers.

This gives R4 disjoint randomness at every conclusion-bearing layer rather than relying only on the topology change.

## Population interpretation

The R4 claim is:

> An equal-topology-weighted result over eight untouched draws from the same registered S7-S3 topology-generating procedure, with topology-conditioned episode worlds and the `heldout_low` energy profile.

It is not:

* a claim conditional on the original R3 topology panel;
* a balanced four-quadrant claim;
* or a claim that every topology individually exhibits the effect.

The new topologies must not be replaced or rebalanced after their coordinate layouts or event support are observed. Their BS-quadrant composition is reported descriptively, as R3 already requires, but does not alter inclusion. The implementation already exposes the topology quadrant precisely for this provenance purpose.

## Freshness sentinel

Before conclusion-bearing execution, the R4 contract must fail closed unless:

1. the exact seed list is `20260734–20260741`;
2. none overlaps the R3 initial set;
3. the artifact identifies the R4 contract and population namespace;
4. each topology has the required Part-A and focal-audit block identities;
5. no R3 topology unit is accepted by the R4 pooler;
6. no arbitrary CLI topology override can produce a conclusion-bearing R4 artifact.

If repository provenance establishes that any proposed R4 topology was previously used for a result-bearing or design-informing source measurement, the contract must be reopened. A replacement seed must not be selected silently.

## Status of same-topology/new-episode evidence

A later run on `20260726–20260733` with new episodes may be retained as:

```text
R4_ORIGINAL_PANEL_CONDITIONAL_REPLICATION
```

It would test conditional repeatability on the original topology panel. It must not be pooled with the primary R4 population or substituted for it.

---

# 3. FREEZE_CORRECTIONS

## Correction 1 — the current artifact is only partially frozen

The header says:

```text
status=FROZEN_2026-07-28
freeze_scope=...|expansion_rule|evidence_population
```

while §§6–7 explicitly leave both expansion and population undecided.

That is internally inconsistent.

The existing file should remain immutable as the partial freeze record, then be superseded by a complete file whose header records:

```text
status=FROZEN_R4_COMPLETE
expansion=NONE
topology_population=20260734..20260741
```

## Correction 2 — “supersedes R3 materiality scale only” is too narrow

R4 changes more than the scalar margin. It changes:

* the materiality criterion;
* branch 3’s causal pair set;
* Part-A equivalence;
* expansion semantics;
* the topology population;
* and the combined result mapping.

The header currently says:

```text
supersedes=...R3.md (materiality scale only)
```

while the document itself records all of these additional changes.

Replace that description with:

> R4 supersedes R3’s conclusion-bearing measurement and result layer. R3’s environment, event, focal estimand, horizons, legal support, CRN, snapshot, component-recording, and hierarchical-inference machinery carry forward unless expressly amended.

## Correction 3 — the result-state definitions must be explicit

The four per-limb state names are recorded, but their exact predicates are not.  Freeze them as follows.

### Stable limb

```text
COMPONENT_INVARIANT
    complete focal component audit
    AND every stable KEEP/SET(z) evaluation pair is exactly invariant

MATERIAL
    components separate
    AND UCB95(U*_stable) < -5

AFFIRMATIVE_NONMATERIAL
    components separate
    AND LCB95(U*_stable) > -5

UNRESOLVED
    components separate
    AND neither bound condition above holds
```

### Flex limb

```text
COMPONENT_INVARIANT
    complete focal component audit
    AND every flex KEEP/SET(z) evaluation pair is exactly invariant

MATERIAL
    components separate
    AND LCB95(U*_flex) > +5

AFFIRMATIVE_NONMATERIAL
    components separate
    AND UCB95(U*_flex) < +5

UNRESOLVED
    components separate
    AND neither bound condition above holds
```

Strict inequalities carry forward from the selected five-unit gates. Equality at the threshold remains unresolved.

## Correction 4 — freeze the combined result mapping

After the first-match conformance, support, global component-degeneracy, and Part-A branches, emit both independent limb states and use this mapping:

| Stable state                                       | Flex state                                         | Combined result                                    |
| -------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------- |
| `MATERIAL`                                         | `MATERIAL`                                         | `PERSISTENCE_NECESSARY_SOURCE`                     |
| `MATERIAL`                                         | `AFFIRMATIVE_NONMATERIAL` or `COMPONENT_INVARIANT` | `STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL` |
| `MATERIAL`                                         | `UNRESOLVED`                                       | `MATERIAL_STABLE_PERSISTENCE_IDENTIFIED`           |
| `AFFIRMATIVE_NONMATERIAL` or `COMPONENT_INVARIANT` | `MATERIAL`                                         | `FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE` |
| `UNRESOLVED`                                       | `MATERIAL`                                         | `MATERIAL_FLEX_RENEWAL_IDENTIFIED`                 |
| both nonmaterial/invariant, except both invariant  | `—`                                                | `NO_MATERIAL_SOURCE_NECESSITY_IDENTIFIED`          |
| `AFFIRMATIVE_NONMATERIAL` or `COMPONENT_INVARIANT` | `UNRESOLVED`                                       | `NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED`        |
| `UNRESOLVED`                                       | `AFFIRMATIVE_NONMATERIAL` or `COMPONENT_INVARIANT` | `NO_MATERIAL_FLEX_RENEWAL_IDENTIFIED`              |
| `UNRESOLVED`                                       | `UNRESOLVED`                                       | `SOURCE_NECESSITY_UNRESOLVED`                      |

If both limbs are `COMPONENT_INVARIANT`, global branch 3 fires first:

```text
PRIMARY_G_DEGENERATE
reason = FOCAL_KEEP_SET_COMPONENTS_EXACTLY_INVARIANT
```

The independent limb states must always remain in the payload so that a top-level name cannot erase whether the non-material limb was affirmatively nonmaterial, exactly invariant, or merely unresolved.

## Correction 5 — define the complete first-match precedence

Freeze:

```text
1. INVALID_EVENT_ALIGNED_AUDIT
2. SOURCE_EVENT_SUPPORT_INSUFFICIENT
3. PRIMARY_G_DEGENERATE
4. PART_A_CONTRADICTION
5. combined result from the two per-limb states
```

`PART_A_CONFORMANCE_UNRESOLVED` remains diagnostic and does not suppress an otherwise valid focal result, matching the prior Part-A semantics.

## Correction 6 — the R4 Part-A block is not an R3 calibration block

R4 deletes the normalizer calibration. The fresh disjoint block should be named:

```text
PART_A_CONTROL
```

It retains eight episodes per topology and compares only:

```text
full_sync_SET
constructive_mixed
```

on the stable event class over (H_{\mathrm{stable}}=139), using the five-unit equivalence rules already recorded.

The `null` arm and both (B_m) quantities have no conclusion-bearing role in R4 and should be deleted from the R4 path rather than accumulated as decorative legacy apparatus. This follows the project’s replacement-before-accumulation rule.

The focal-audit block remains eight disjoint episodes per topology.

## Correction 7 — prior R3 support does not pre-pass R4 support

R3 support justifies retaining S7-S3 as a candidate. It does not allow R4 to inherit a support pass.

The new topologies must independently satisfy the existing minimum-support rule before any focal margin is read. If support fails on the fixed R4 population:

```text
SOURCE_EVENT_SUPPORT_INSUFFICIENT
```

fires, with no topology substitution and no expansion.

## Clauses that are correctly transcribed

No correction is needed to:

* the five-unit cutoff-equivalent anchor;
* equal absolute margins across the two causal horizons;
* removal of (B_m);
* the focal KEEP/SET branch-3 pair set;
* exact rather than fractional component invariance;
* missing audit versus valid invariance;
* the five-unit Part-A tests;
* the requirement for fresh confirmatory evidence;
* retention of `n_select=2`, `n_eval=2`.

Those match the previous ruling.

---

# 4. NEXT_ACTION

The next action is **contract and realization closure**, not an environment run.

## A. Supersede the partial freeze

Create a complete immutable R4 contract containing:

* `expansion=NONE`;
* topology seeds `20260734–20260741`;
* the R4 population/seed namespace;
* 8 Part-A control and 8 focal-audit episodes per topology;
* the complete per-limb and combined result mapping;
* deletion of R3 `null`/normalizer apparatus from the R4 path;
* exact formal-run population guards.

## B. Update the decision ledger

Bind at least:

* absolute five-unit margin;
* no-expansion decision;
* fresh-topology population;
* seed namespace;
* Part-A block;
* branch-3 focal pair set;
* limb-state predicates;
* combined branch mapping;
* no-pooling-with-R3 rule.

## C. Implement the smallest R4 delta

The R4 path should reuse the accepted R3 machinery for:

* event construction;
* live-event snapshotting;
* legal SET enumeration;
* CRN;
* `2/2` empirical maximization;
* component-series persistence;
* hierarchical topology/episode bootstrap.

It should replace:

* (B_m/T_m) inference;
* R3 branch selection;
* R3 expansion guard;
* R3 topology list;
* R3 calibration/null block.

## D. Complete realization-conformance review

Before formal compute, verify at least:

1. the formal path accepts only the exact R4 topology set;
2. no R3 topology or artifact can enter the R4 pool;
3. Part-A uses (D_A\pm5), not (B_{\mathrm{stable}});
4. branch 3 aggregates focal pairs, not calibration pairs;
5. every per-limb state and combined result has a reachable witness;
6. incomplete component records fail closed;
7. both flex-only positive branches are reachable;
8. there is no expansion path;
9. the formal run cannot override episode counts or topology seeds;
10. R3 results cannot be rethresholded through the R4 assembler.

## E. Run a proof-sized assembled-path exercise

Use development-only topology `20260725`; no scientific interpretation. Exercise:

* invalid audit;
* support failure;
* both-limb invariance;
* Part-A contradiction;
* both material;
* stable-only material;
* flex-only material;
* affirmative nonmaterial;
* unresolved.

Only after those close may the fixed R4 run return to the project’s separate conclusion-bearing compute-authorization path.

---

# 5. CHALLENGES

## 1. “The contract is frozen” is premature

Its core scientific choices are frozen, but the document itself admits that population and expansion remain open. Those choices determine the data-generating distribution and optional-sampling behavior, so they are not peripheral implementation details.

## 2. Same topology plus new episodes is not the primary fresh population

It would provide new (W\mid T) draws under already observed (T), not new draws from (P_T). Because topology is the highest bootstrap and inferential unit, reuse at that level would weaken the confirmatory separation R4 was required to have.

## 3. The inferential population changes, but the target source does not

Using new topology seeds changes the empirical topology sample, as it should. It does not change:

* the S7-S3 topology generator;
* environment semantics;
* event definition;
* energy profile;
* or intended source population.

R4 estimates the same target over a new untouched sample.

## 4. The PM’s no-expansion preference is accepted, but not because R3’s implementation once failed to record expansion inputs

That historical defect is an implementation lesson. The scientific reasons for no expansion are:

* fixed confirmatory population;
* no optional-stopping correction;
* no power rescue;
* lower complexity;
* and the legitimacy of an unresolved result.

## 5. The guard and pooler closure claims are not independently adjudicated here

The current evidence fence includes the audit implementation but not the full focused tests, mutation reports, or pooler source. Their closure remains a PM-owned technical premise to be checked at Gate B. It should not be promoted into a scientific fact from this round alone.

## 6. No expansion does not predetermine source retirement

An unresolved fixed R4 result would mean the registered evidence did not identify the source proposition. Its next disposition would still require the smallest-unit analysis:

* measurement precision;
* source heterogeneity;
* source non-identification;
* or carrier replacement.

It would not automatically refute R30 or select a new source.

---

# Final disposition

**Freeze the complete R4 contract with:**

```text
expansion             NONE
topology seeds        20260734–20260741
topologies            8, equal weight
Part-A episodes       8 per topology
focal-audit episodes  8 per topology
n_select              2
n_eval                2
R3 data pooling       forbidden
```

The current partial freeze should be superseded, not edited.

**D7.3 and D8 remain blocked pending a valid fresh-population R4 result. This review authorizes neither implementation nor compute.**
