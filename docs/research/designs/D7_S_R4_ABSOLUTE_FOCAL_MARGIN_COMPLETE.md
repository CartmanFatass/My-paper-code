# D7.S R4 — absolute focal task-unit margin — complete frozen contract

```text
id=D7.S-R4
status=FROZEN_R4_COMPLETE
freeze_date=2026-07-28
expansion=NONE
topology_population=20260734..20260741
population_namespace=D7_S_R4_ABSOLUTE_FOCAL_MARGIN
supersedes=D7_S_R4_ABSOLUTE_FOCAL_MARGIN.md (the partial freeze, left immutable as its own record)
authority=rounds/20260728_r4_contract_freeze/21_PRO_OPEN_RAW.md
prior_authority=rounds/20260728_r4_materiality_derivation/21_PRO_OPEN_RAW.md
authorizes_implementation=false
authorizes_compute=false
```

**Relationship to R3.** R4 supersedes R3's **conclusion-bearing measurement and
result layer**. R3's environment, event, focal estimand, horizons, legal support,
CRN, snapshot, component-recording, and hierarchical-inference machinery carry
forward unless expressly amended here. (The partial freeze said "materiality
scale only", which was too narrow — R4 also changes branch 3's causal pair set,
Part-A equivalence, expansion semantics, the topology population, and the
combined result mapping.)

This contract authorizes neither implementation nor compute.

## §1. The materiality gate

```text
stable clears  iff  UCB95(U*_stable) < -5.0
flex clears    iff  LCB95(U*_flex)   > +5.0

U*_m = V_SET,m - V_KEEP,m,  window-summed primary G over H_m
delta_stable = delta_flex = 5.0 G-units      H_stable = 139   H_flex = 550
```

Five is the smallest nonzero coefficient on a **discrete, window-local,
task-semantic** safety event in the frozen objective
(`G_t = qos − 2·return_cost − 5·cutoff − 10·depletion`), fixed from the weights
alone and never from an observed `U*`. "Cutoff-equivalent" does not require a
cutoff — five units may be realized by any registered combination of components.

The same margin applies to both horizons deliberately: the proposition is the
**total task consequence of one renewal decision**, not its per-step rate. The
anchor is **not mathematically unique**; it is non-post-hoc and externally
interpretable, which is what was required.

**Strict inequalities. Equality at the threshold is UNRESOLVED.**

## §2. Expansion — NONE

There is no expansion path. Not "a rule that rarely fires" — none.

The scientific reasons, recorded because a weaker justification was offered and
corrected: a **fixed confirmatory population**; no optional-stopping correction
required; no power rescue available; lower complexity; and **the legitimacy of an
unresolved result**. That R3's expansion predicate was never evaluable is an
implementation lesson, *not* the reason.

No expansion does **not** predetermine source retirement. An unresolved fixed R4
result means the registered evidence did not identify the proposition, and its
disposition still requires a smallest-unit analysis over measurement precision,
source heterogeneity, source non-identification, or carrier replacement.

## §3. Population — fresh at the highest inferential unit

```text
TOPOLOGY_SEEDS_R4 = (20260734, 20260735, 20260736, 20260737,
                     20260738, 20260739, 20260740, 20260741)
development topology = 20260725   (no scientific reading)
```

R2 registered these as the only possible second block but never authorized their
use absent its expansion predicate. This contract **repurposes them as R4's
initial fixed population**; they are *not* inherited through R3 expansion
authority.

**Why not new episodes under the R3 topologies.** Topology is the upper
inferential unit (`T ~ P_T`, `W ~ P(W|T)`) and the top-level bootstrap unit. New
user worlds under the same eight topologies are fresh *conditional* observations
but not a fresh population for the registered topology-population claim — those
eight have been measured, autopsied, inspected topology by topology, and used to
motivate R4 itself.

### Frozen nested draws

Per R4 topology: **Part-A control block, episode indices 0–7**; **focal audit
block, episode indices 0–7**. The blocks stay disjoint through their block
namespace, episode seeds, energy-permutation seeds, user-world seeds and
continuation-stream seeds. R4 uses its own population/seed namespace
`D7_S_R4_ABSOLUTE_FOCAL_MARGIN` while retaining the existing hash field structure
and CRN relationships — disjoint randomness at every conclusion-bearing layer,
not merely a topology change.

### The claim

> An equal-topology-weighted result over eight untouched draws from the same
> registered S7-S3 topology-generating procedure, with topology-conditioned
> episode worlds and the `heldout_low` energy profile.

It is **not** conditional on the R3 panel, **not** a balanced four-quadrant
claim, and **not** a claim that every topology individually exhibits the effect.
Topologies must not be replaced or rebalanced after their layouts or event
support are observed; BS-quadrant composition is reported descriptively only.

### Freshness sentinel — fail closed unless

1. the exact seed list is `20260734–20260741`;
2. none overlaps the R3 initial set;
3. the artifact identifies the R4 contract and population namespace;
4. each topology has the required Part-A and focal-audit block identities;
5. no R3 topology unit is accepted by the R4 pooler;
6. no arbitrary CLI topology override can produce a conclusion-bearing artifact.

If repository provenance ever shows a proposed R4 topology was previously used
for a result-bearing or design-informing measurement, **reopen the contract** — a
replacement seed must not be selected silently.

A later run on `20260726–20260733` with new episodes may be retained as
`R4_ORIGINAL_PANEL_CONDITIONAL_REPLICATION`. It **must not** be pooled with the
primary R4 population or substituted for it.

## §4. Branch 3 — focal-arm component invariance only

`P_m^R4` contains every complete, CRN-paired evaluation comparison
`(KEEP, SET(z))` for every qualifying event, every legal `z`, every registered
evaluation replicate. **Not** the R3 calibration pair — that rule was R3-specific
because it tied component separation to the normalizer source controls.

```text
components_invariant_m = AND over p in P_m^R4 of exact_paired_sequence_equal(p)
components_separate_m  = NOT components_invariant_m
primary_g_degenerate   = NOT (components_separate_stable OR components_separate_flex)
```

One unequal complete pair refutes exact invariance. **No fraction threshold.**

```text
audit missing/incomplete -> INVALID_EVENT_ALIGNED_AUDIT
                            reason = MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING
audit complete, all invariant -> PRIMARY_G_DEGENERATE
                            reason = FOCAL_KEEP_SET_COMPONENTS_EXACTLY_INVARIANT
audit complete, >=1 differs -> proceed to the absolute U* gates
```

Completeness: every qualifying event and legal candidate represented; both CRN
members present; all four sequences at the registered horizon; no invalidated
pair; serialized and in-memory pair counts agree. **A missing pair is neither
equal nor unequal.**

## §5. Per-limb result states — frozen predicates

### Stable limb

```text
COMPONENT_INVARIANT       complete focal audit AND every stable KEEP/SET(z) pair exactly invariant
MATERIAL                  components separate AND UCB95(U*_stable) < -5
AFFIRMATIVE_NONMATERIAL   components separate AND LCB95(U*_stable) > -5
UNRESOLVED                components separate AND neither bound condition holds
```

### Flex limb

```text
COMPONENT_INVARIANT       complete focal audit AND every flex KEEP/SET(z) pair exactly invariant
MATERIAL                  components separate AND LCB95(U*_flex) > +5
AFFIRMATIVE_NONMATERIAL   components separate AND UCB95(U*_flex) < +5
UNRESOLVED                components separate AND neither bound condition holds
```

## §6. Combined result mapping

| Stable | Flex | Combined |
|---|---|---|
| `MATERIAL` | `MATERIAL` | `PERSISTENCE_NECESSARY_SOURCE` |
| `MATERIAL` | `AFFIRMATIVE_NONMATERIAL` or `COMPONENT_INVARIANT` | `STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL` |
| `MATERIAL` | `UNRESOLVED` | `MATERIAL_STABLE_PERSISTENCE_IDENTIFIED` |
| `AFFIRMATIVE_NONMATERIAL` or `COMPONENT_INVARIANT` | `MATERIAL` | `FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE` |
| `UNRESOLVED` | `MATERIAL` | `MATERIAL_FLEX_RENEWAL_IDENTIFIED` |
| both nonmaterial/invariant, except both invariant | — | `NO_MATERIAL_SOURCE_NECESSITY_IDENTIFIED` |
| `AFFIRMATIVE_NONMATERIAL` or `COMPONENT_INVARIANT` | `UNRESOLVED` | `NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED` |
| `UNRESOLVED` | `AFFIRMATIVE_NONMATERIAL` or `COMPONENT_INVARIANT` | `NO_MATERIAL_FLEX_RENEWAL_IDENTIFIED` |
| `UNRESOLVED` | `UNRESOLVED` | `SOURCE_NECESSITY_UNRESOLVED` |

Both limbs `COMPONENT_INVARIANT` → global branch 3 fires first.

**The independent limb states must always remain in the payload**, so a top-level
name can never erase whether the non-material limb was affirmatively nonmaterial,
exactly invariant, or merely unresolved. This is what R3 could not express, and
it is why a valid flex positive can no longer be hidden.

## §7. First-match precedence

```text
1. INVALID_EVENT_ALIGNED_AUDIT
2. SOURCE_EVENT_SUPPORT_INSUFFICIENT
3. PRIMARY_G_DEGENERATE
4. PART_A_CONTRADICTION
5. combined result from the two per-limb states
```

`PART_A_CONFORMANCE_UNRESOLVED` remains diagnostic and does not suppress an
otherwise valid focal result.

## §8. `PART_A_CONTROL` — not an R3 calibration block

Eight episodes per topology, comparing **only** `full_sync_SET` against
`constructive_mixed` on the stable event class over `H_stable = 139`:

```text
D_A = G(full_sync_SET) - G(constructive_mixed)

PART_A_CONTRADICTION        iff  LCB95(D_A + 5) > 0  AND  LCB95(5 - D_A) > 0
full-sync materially worse  iff  UCB95(D_A + 5) < 0
otherwise                        PART_A_CONFORMANCE_UNRESOLVED
```

**The `null` arm and both `B_m` quantities have no conclusion-bearing role in R4
and are deleted from the R4 path** — not retained as decorative legacy apparatus.
Replacement before accumulation.

The focal-audit block remains eight disjoint episodes per topology.

## §9. Support does not carry over

R3 support justifies retaining S7-S3 as a *candidate*. It does **not** let R4
inherit a support pass. The new topologies must independently satisfy the
existing minimum-support rule before any focal margin is read. On failure:
`SOURCE_EVENT_SUPPORT_INSUFFICIENT`, **with no topology substitution and no
expansion.**

## §10. What R4 retains and replaces

**Reuse:** event construction; live-event snapshotting; legal SET enumeration;
CRN; the `2/2` empirical-maximization floor; component-series persistence; the
hierarchical topology/episode bootstrap.

**Replace:** `B_m`/`T_m` inference; R3 branch selection; the R3 expansion guard;
the R3 topology list; the R3 calibration/null block.

## §11. Gates before any formal R4 run

**Realization conformance** — verify all ten: the formal path accepts only the
exact R4 topology set; no R3 topology or artifact can enter the R4 pool; Part-A
uses `D_A ± 5` and not `B_stable`; branch 3 aggregates focal pairs; every
per-limb state and combined result has a reachable witness; incomplete component
records fail closed; both flex-only positive branches are reachable; there is no
expansion path; the run cannot override episode counts or topology seeds; R3
results cannot be rethresholded through the R4 assembler.

**Proof-sized assembled-path exercise** on development topology `20260725` only,
no scientific interpretation, exercising: invalid audit; support failure;
both-limb invariance; Part-A contradiction; both material; stable-only material;
flex-only material; affirmative nonmaterial; unresolved.

Only after those close may the fixed R4 run return to the separate
conclusion-bearing compute-authorization path.

**Guard closure is a PM-owned technical premise, not an adjudicated scientific
fact.** The mutation-sweep and pooler closure claims were not independently
reviewed and must be checked at that gate rather than assumed.

`D7.3` and `D8` remain blocked pending a valid fresh-population R4 result.
