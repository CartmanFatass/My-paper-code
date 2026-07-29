# Scientific ruling — D7.S source-assignment correction

**Stage reviewed:** `9cb7974563cb7de3371b1d22f3691fc00e02744d`

## Overall disposition

# **FREEZE AFTER MODIFICATION**

The six-object correction is scientifically sound in direction. The selected assignment semantics remain:

* the executable duty assignment is a partial injection;
* physical coverage is determined by action-bearing execution rather than raw map membership;
* R5 acts only on executably covered incumbents;
* invalid assignment states fail closed;
* and the historical R4 artifact remains immutable but scientifically invalid.

One section should be narrowed before freeze:

> **Select (b1), strengthened by a batch-level postcondition.**
> Preserve the current LEAVE rematching semantics. Prevent any REJOINing UAV that already holds a duty after the LEAVE phase from receiving another duty, process multiple rejoiners deterministically, and assert injectivity after the complete transition batch.

Do **not** select the proposed full atomic rebatch in which every transition batch globally removes, preserves and rematches all assignments. The new measurement localizes the observed defect to the REJOIN phase; a full rebatch would change additional source-controller behavior without evidence that those changes are necessary.

The semantic correction does not need a second standalone test suite separate from the repair. It does require a **predeclared, paired-negative conformance suite implemented with the repair**, with the old code demonstrably red before the correction and the corrected code green afterward.

---

# 1. Accept or amend, freeze by freeze

## Freeze 1 — partial-injection semantics

# **ACCEPT**

Freeze the executable assignment as:

[
m_t^{\mathrm{exec}}:D_t\rightharpoonup U_t
]

with:

[
m_t^{\mathrm{exec}}(d_1)=m_t^{\mathrm{exec}}(d_2)
\Longrightarrow d_1=d_2.
]

The representation emits one physical action per UAV. Its current action generator obtains a single duty per UAV through an inverse map, so a UAV assigned two duties cannot execute the claimed state; one duty is silently discarded by dictionary overwrite.

A non-injective source would require a different executor—such as an explicit multi-target allocation or composite action—and would constitute a new source model. No such executor exists in the reviewed implementation.

### Amendment to notation

Use the partial-map symbol explicitly:

[
m_t^{\mathrm{exec}}:D_t\rightharpoonup U_t.
]

The current textual “`m_t : D_t -> U_t partial`” is understandable but unnecessarily ambiguous.

---

## Freeze 2 — executable coverage

# **ACCEPT WITH A PROVENANCE AMENDMENT**

The distinction among:

* `m_raw`;
* `m_exec`;
* (C_t=\operatorname{dom}(m_t^{\mathrm{exec}}));

is necessary and should be frozen. A phantom duty is uncovered.

However, `m_exec` should not be reconstructed after the fact by inspecting raw map keys or inferring which target an action “looks like” it follows. Freeze an explicit action-provenance object:

```text
action_source[u] ∈ {
    DUTY(d),
    CHARGING,
    STATION_RETURN,
    FOCAL_OVERRIDE,
    IDLE_OR_OTHER
}
```

Then:

[
m_t^{\mathrm{exec}}
===================

{(d,u):\operatorname{action_source}_t(u)=\mathrm{DUTY}(d)}.
]

This follows the actual action precedence:

1. focal override;
2. charging behavior;
3. station-return behavior;
4. ordinary duty-directed action.

The current action function already has exactly those precedence branches.

### Important distinction

A non-action-bearing raw ledger entry is not automatically a second executable duty. It may remain ownership metadata, but:

* it is outside `m_exec`;
* it is outside (C_t);
* it is outside R5’s treatment domain;
* and no metric or branch may call it covered.

If any code interprets such raw membership as coverage, that is an invalid source-control realization.

A **non-injective raw map**, by contrast, must fail before inversion. The source has selected one-duty-per-UAV semantics; it may not silently choose one duplicated duty by insertion order.

---

## Freeze 3 — atomic lifecycle transitions

# **AMEND**

Retain the outcome-level invariant:

```text
After a lifecycle transition batch, the assignment over the final
action-capable UAV set is a partial injection.
```

Do not freeze the current five-step text as a mandatory global rebatching algorithm. In particular, this line is too strong:

```text
rematch the remaining duties one-to-one over the remaining UAVs
```

if it is read as requiring a full rematch on every transition batch.

The reviewed development measurement found:

```text
dup_after_leaves = False  in all 249 simultaneous batches
dup_out          = True   in all 249 simultaneous batches
```

including all eight duplication onsets. Thus the existing LEAVE phase produced an injective intermediate map every time, and REJOIN recreated the duplicate every time.

The code agrees with that localization:

* the LEAVE branch clears unlocked assignments and assigns each survivor at most once by removing it from `pool`;
* the REJOIN branch assigns the rejoining UAV an uncovered duty without checking whether it already appears in the map.

### Revised frozen transition semantics

Use this minimum batch-aware procedure:

1. Detect the complete LEAVE and REJOIN sets and the final action-capable UAV set.
2. Apply the existing LEAVE rematch semantics, including locked-incumbent preservation.
3. Form the set of holders already assigned after all LEAVE processing.
4. Process REJOINers in a frozen canonical order—ascending physical UAV index is the existing deterministic order:

   * if a rejoiner is already a holder, it receives no second duty;
   * otherwise, if an uncovered duty exists, assign at most one under the existing nearest-uncovered-duty rule;
   * otherwise leave it unassigned.
5. Assert:

   * every holder is action-capable;
   * every holder appears at most once;
   * the resulting map is a partial injection.

The current transition dispatcher already constructs LEAVE and REJOIN lists in ascending UAV-index order and processes all LEAVEs before all REJOINs.

### Why this is preferable to full rebatching

A full rebatch would potentially change:

* incumbent preservation outside the implicated REJOIN path;
* which duty is left uncovered;
* transit assignments on REJOIN-only steps;
* and behavior on batches that already satisfy the invariant.

The evidence identifies no need for those changes. The scientific object is the injective batch output, not a requirement to replace all current lifecycle assignment logic.

---

## Freeze 4 — R5 treatment domain

# **ACCEPT WITH TEMPORAL PRECISION**

Freeze R5’s domain at each shared **pre-action** check, after:

1. lifecycle state visible at that boundary has been processed;
2. the source assignment has passed injectivity validation;
3. action provenance has established which incumbents are genuinely duty-directed.

Then:

[
D_e
===

{d\in C_t:m_t^{\mathrm{exec}}(d)\in U_e},
]

where (U_e) is the already frozen six-condition eligible set.

R5 must not derange:

* raw-map phantoms;
* charging or absent holders;
* station-return-overridden holders;
* failed or non-acting holders;
* or holder–duty tokens that duplicate one physical action authority.

The correction’s present treatment-domain statement is otherwise right.

---

## Freeze 5 — fail-closed handling

# **ACCEPT WITH A SCOPE CLARIFICATION**

Retain:

```text
noninjective executable assignment
lossy assignment inversion
coverage asserted without an action-bearing holder
    -> INVALID SOURCE-CONTROL REALIZATION
    -> no matching
    -> no effect estimate
    -> no synthetic zero
```

Clarify that the second line means:

> **An assignment inversion is forbidden unless injectivity has already been established.**

Once the map is validated as injective, building a reverse lookup is lossless and acceptable.

Also distinguish:

* a raw ownership entry whose holder is temporarily non-duty-directed, which may remain metadata but is not covered;
* from an artifact or controller that counts that entry as covered, which is invalid.

### Aggregation scope

This is an implementation/conformance failure, not stochastic source support. It must never be converted into:

* an event support miss;
* an excluded inconvenient episode;
* or a zero effect.

For a conclusion-bearing instrument, any such violation on its source-control path must route to the formal invalid-audit branch. The exact run/topology abort scope belongs in the eventual R5 result contract, but the classification is already fixed: **invalid realization, not source absence**.

---

## Freeze 6 — R4 disposition

# **ACCEPT**

Keep the historical JSON unchanged:

```text
PART_A_CONTRADICTION
```

Attach the authoritative scientific disposition:

```text
INVALID_R4_REALIZATION:
DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED
```

The correction accurately records that the defect affected more than the physical trajectories:

* stable-candidate construction iterated raw duty-map entries, allowing one UAV to appear as multiple candidates;
* flex-survivor construction keyed by UAV and collapsed duplicate entries;
* therefore the conditioning set and focal identity were also changed.

This is an implementation-level invalidation, not evidence against R30, D7.3, D8 or the broader variable-lifetime hypothesis. That is the narrow update required by the project’s result semantics.

---

# 2. Scope of “repair the development source controller”

# **Select (b1), with a universal postcondition**

The minimum repair is sufficient for the identified defect:

```text
When processing a REJOIN, do not assign an uncovered duty if that UAV
already appears as a holder in the map produced by the preceding LEAVE phase.
```

It should be written against the current map state, not merely against a separate “assigned earlier in this batch” flag:

```text
if rejoining_uav in new_map.values():
    do not assign a second duty
```

That catches:

* assignment received during the current LEAVE phase;
* any unexpected pre-existing assignment;
* and future code paths reaching REJOIN with an already assigned UAV.

Then assert the final partial-injection invariant.

## The LEAVE branch

The correct claim is:

> **No semantic change to the LEAVE rematching algorithm is justified for this defect, provided its input map is valid and its output remains subject to the universal injectivity assertion.**

The stronger unqualified statement “the LEAVE branch needs no change” would exceed the evidence. The development measurement covers the current transition patterns on one topology, and the code structurally removes each assigned survivor from its pool, but future changes to locks, transition batching or input validity remain re-review triggers.

## Absorbing versus continuously recreated

Both descriptions are true at different observational surfaces:

* at ordinary step/check boundaries, each affected episode enters a duplicated state and remains duplicated;
* inside every simultaneous lifecycle batch, LEAVE transiently repairs the map and REJOIN immediately recreates the duplicate.

The latter localizes the repair. It does not make the former whole-step observation false.

## Why not (b2)?

Full atomic rebatching remains a live fallback if the targeted repair later fails one of these conditions:

* multiple simultaneous rejoiners produce ambiguous or non-injective output;
* locked incumbents conflict with the final action-capable set;
* an uncovered duty cannot be allocated deterministically;
* or another lifecycle path generates ownership/execution divergence.

No such contradiction is currently established. Selecting b2 now would broaden the intervention rather than repair the observed defect.

## Why not `u → z_u` now?

Making UAV-to-target assignment the primary representation remains a strong simpler alternative because it is injective by physical construction. It should remain parked as the next abstraction if the repaired `duty → UAV` representation continues to diverge from execution.

At this boundary, replacing the representation would change substantially more source logic than the localized REJOIN repair.

---

# 3. Paired-negative suite

## Ruling

# **The correction rides on the repair’s suite—but that suite must be frozen before the repair and must demonstrate red-to-green behavior**

A prose semantics document has no independent executable mechanism to test. A separate “correction suite” and a “repair suite” would either:

* duplicate the same assertions;
* or test two copies of one definition against each other.

Instead:

1. freeze the conformance cases now;
2. run them against the old implementation and record the expected failures;
3. land the controller repair and the suite atomically;
4. require the same cases to pass without weakening their predicates.

The existing strict xfail is a valuable first negative: it directly asserts that REJOIN must never give an already assigned UAV a second duty. It does not cover the complete correction.

## Mandatory positive witnesses

The repair suite must include:

1. **Unassigned REJOINer:** an unassigned rejoiner fills one nearest uncovered duty.
2. **Already assigned REJOINer:** a rejoiner assigned by the LEAVE phase receives no second duty.
3. **Simultaneous LEAVE+REJOIN:** the complete batch ends injective.
4. **Multiple REJOINers:** canonical processing produces a deterministic injective result.
5. **LEAVE regression:** the current reduced-fleet rematch and locked-incumbent behavior remain unchanged on representative valid inputs.
6. **Executable coverage:** every duty counted in (C_t) has exactly one `DUTY(d)` action-provenance record.

The existing positive REJOIN test uses an empty incoming map, so it proves only that an unassigned rejoiner can fill an uncovered duty; it cannot exercise the duplicate-holder defect.

## Mandatory paired negatives

Each of the following must independently make the relevant guard fail:

1. the old REJOIN behavior that assigns a second duty;
2. a raw non-injective map passed to the action generator;
3. a reverse lookup performed before injectivity validation;
4. a raw duty key whose holder’s action source is `CHARGING` or `STATION_RETURN`, while the artifact calls it covered;
5. a phantom raw duty with no `DUTY(d)` provenance;
6. simultaneous transitions whose final map contains a duplicate holder;
7. a deliberately removed final injection assertion;
8. an implementation that silently drops one duplicate duty and continues.

The suite must test both:

* map-level injectivity;
* action-provenance/executable-coverage consistency.

Testing only `len(values) == len(set(values))` would close the duplicate-holder defect but leave the historical charging/stale-holder mismatch invisible.

---

# 4. Assessment of the post-fence measurement

## Supported

The development measurement supports the following narrow statement:

> On the eight development episodes and 249 observed simultaneous LEAVE+REJOIN batches, the map was injective after the LEAVE phase and non-injective after the REJOIN phase; all eight duplication onsets followed that same route.

This is strong enough to select the targeted REJOIN repair over a full rebatch as the next realization.

## Not supported

It does not prove:

* that LEAVE can never violate injectivity under another topology or future lock configuration;
* that REJOIN is the only possible future source of non-injectivity;
* that the targeted repair guarantees all aspects of executable coverage;
* or that no UAV-to-target representation change will eventually be needed.

The question itself correctly avoids those generalizations.

## One wording correction

The phrase:

> “Duplication is continuously re-created, not persistent state”

should be qualified. At the externally visible step-boundary state it is persistent after onset; at the internal phase boundary it is repaired and immediately recreated. The distinction matters because:

* the former explains how many downstream checks and events were contaminated;
* the latter identifies the minimal repair location.

---

# 5. Consequences for A, B and C

The source-assignment correction does not close these obligations by itself.

## Obligation A

After the controller repair:

* rerun A1–A4 against the corrected source assignment;
* prove that every admitted `m_exec` is a partial injection;
* derive (D_e) from `m_exec`;
* require one unique incumbent duty per eligible UAV.

A3 is then rescued:

[
|U_e|=|D_e|
]

because the corrected executable relation is injective.

The solver, canonical tie-break, sparse-graph and Hall-witness lemmas remain retained.

## Obligation B

The prior `1200/1200` is not rehabilitated by the new localization. It was computed through the lossy one-duty-per-UAV view and must be repeated on trajectories generated by the corrected source controller. The source trajectory itself may change after the REJOIN fix.

## Obligation C

C must begin with these preconditions:

```text
incoming raw map injective;
incoming executable map injective;
outgoing executable map injective;
every claimed covered duty has one duty-directed action;
no action-bearing UAV represents more than one covered duty.
```

Its mutation set must include a duplicate-holder and a raw-map/action-provenance disagreement. The existing `UNCONSTRUCTIBLE` handling was honest but did not prove witness completeness.

D–F remain open behind the corrected A–C sequence.

---

# 6. Fresh-panel rule

The panel **size of eight** remains unchanged.

One terminology correction is warranted in `D7_S_R5_OBLIGATION_G_FRESH_PANEL_RULE.md`:

> A deterministic rule that uniquely names `20260742…20260749` is a **preselection without observation**, not “no selection.”

That is scientifically acceptable as preregistration, provided:

* none of those topologies is constructed, inspected or probed before A–F close;
* the block is not inserted into a conclusion-bearing driver;
* and the final R5 contract binds the exact panel and namespace before use.

The document’s claim that the panel rule is purely a PM implementation choice is too broad. Topology is the highest inferential unit, so the resulting panel is part of the scientific population contract. The mechanical “next contiguous block” rule may be PM-derived; the resulting population binding must still appear in the final protected freeze.

No panel has been consumed merely by writing the rule. It must remain sealed and uninstantiated.

---

# 7. Revised sequence

| Order | Action                                                                    | Status after this ruling         |
| ----: | ------------------------------------------------------------------------- | -------------------------------- |
|     0 | Supersede the source-assignment correction with the amendments above      | Selected                         |
|     1 | Freeze the repair/conformance test matrix; demonstrate old-code negatives | Required                         |
|     2 | Apply the targeted REJOIN fix and final batch injectivity assertion       | Ordinary implementation boundary |
|     3 | Add action-source provenance and executable-coverage validation           | Required with repair             |
|     4 | Rerun A1–A4 and B on the repaired source                                  | Required                         |
|     5 | Revise and rerun C with injectivity and coverage preconditions            | Required                         |
|     6 | Resume D, E and F                                                         | Still gated                      |
|     7 | Activate and fully freeze G’s untouched eight-topology population         | Only after A–F                   |

No full atomic rebatch, new representation, topology selection/inspection or formal source run is selected now.

---

# 8. Retained portfolio

| Route                                                     | Status                   | Raising or lowering evidence                                                                                    |
| --------------------------------------------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Targeted REJOIN exclusion + final injection assertion** | **Selected**             | Raised by red-to-green transition tests and repaired A–C; lowered by any remaining lifecycle ownership mismatch |
| Full atomic transition rebatch                            | Parked                   | Raise only if the targeted repair fails on multiple transitions, locks or totality                              |
| UAV-to-target executable state as primary representation  | Live simpler alternative | Raise if duty-ledger and execution continue to diverge after repair                                             |
| Explicit multi-duty controller                            | Not selected             | Requires a new composite action model and changes the source                                                    |
| Move to a tenure-native source                            | Retained fallback        | Raise if S7-S3’s assignment abstraction remains non-identifying                                                 |

## Smallest refuted unit

The new evidence refutes:

> The source controller must globally rebatch every simultaneous lifecycle transition in order to eliminate the observed duplicate-holder defect.

It supports the narrower correction:

> The observed defect is created by assigning an uncovered duty to a rejoiner already assigned during the preceding LEAVE phase.

It does not yet prove that the targeted repair makes the entire source assignment realization scientifically valid.

---

# Final disposition

The source-assignment correction may be frozen after:

1. replacing the mandatory full-rematch resolution order with the targeted batch-aware REJOIN semantics;
2. adding explicit action-source provenance to executable coverage;
3. clarifying fail-closed scope;
4. preserving the accepted R4 invalid-realization disposition;
5. binding the paired-negative suite to the repair.

**The selected repair is (b1) plus a universal final injectivity assertion—not (b2).**

`D7.3` and `D8` remain blocked. This review authorizes neither implementation nor compute.
