# Scientific ruling — D7.S duty-map injectivity

**Stage reviewed:** `db7ad266394657300b2463e78fc8a5bd06c7e0ad`

## Overall disposition

# **SELECT (a1): THE DOUBLE HOLD IS A REALIZATION DEFECT**

The current source-control abstraction requires `duty_map` to be a **partial injection** from executable duties to physical UAVs:

[
m_t:D_t\rightharpoonup U_t,
\qquad
m_t(d_1)=m_t(d_2)\Rightarrow d_1=d_2.
]

A UAV may hold at most one executable duty because the source controller emits exactly one physical action per UAV and obtains that action by inverting `duty_map` into one `uav_to_duty` entry. When the map is non-injective, one duty is discarded by dictionary overwrite and has no corresponding action. That is not a legitimate multi-duty state; it is an internally inconsistent controller state.

The treatment domain for R5 must therefore be the **injective, action-bearing assignment relation**, not:

* raw `duty_map.keys()`;
* a multiset of holder–duty pairs;
* or the lossy inverse currently consumed by the action generator.

A phantom duty is **uncovered**. A map key is only an assignment claim; coverage requires an executable action-bearing incumbent.

Consequences:

* obligation A is reopened at A1–A4, while its solver and Hall-witness lemmas remain;
* obligation B’s `1200/1200` result is retired as feasibility evidence and must be repeated after the assignment semantics are repaired;
* obligation C was never closed and its witness needs an injectivity/executable-coverage precondition;
* the R4 JSON remains immutable, but it no longer carries a valid R4 scientific result. Its authoritative disposition becomes an invalid realization of both named Part-A arms, not merely a non-identifying control arm.

`D7.3` and `D8` remain blocked.

---

# 1. Branch (a): defect or legitimate state?

## 1.1 Why the double hold is not legitimate

`constructive_mixed_update` is written as a one-to-one reassignment mechanism:

* during LEAVE, each survivor is removed from the assignment pool after receiving one duty;
* when fewer UAVs than duties are available, one duty is deliberately left uncovered;
* the intended interpretation is explicitly that one duty receives one live incumbent.

The REJOIN branch violates that representation. It assigns the rejoining UAV to an uncovered duty without testing whether that UAV already appears in `new_map.values()`.

The defect becomes physically consequential because the action layer cannot execute two duties. It constructs:

```python
uav_to_duty = {u: d for d, u in duty_map.items()}
```

and therefore retains only the last duty encountered for a duplicate holder. The other duty disappears from execution.

The focused test now correctly records this as a strict known failure, while its paired positive confirms that `full_sync_set_update` is injective because each chosen UAV is removed from the remaining pool.

A legitimate multi-duty source would require a different executable model, such as:

* a composite action that jointly serves several duty targets;
* an explicit allocation of capacity among several duties;
* or a defined aggregation rule from a duty set to one physical trajectory.

None exists here. Reinterpreting the duplicate as legitimate would therefore create a new source/controller rather than clarify the existing one.

## 1.2 Correct lifecycle semantics

The minimal invariant is:

```text
after every lifecycle update:
    every duty has at most one holder;
    every UAV holds at most one duty.
```

For the measured simultaneous LEAVE+REJOIN case, the correct outcome is not to reject the REJOIN lifecycle event. It is to prevent the rejoining UAV from receiving a second duty.

More generally, simultaneous lifecycle changes should be resolved atomically:

1. determine the final action-capable UAV set after all LEAVE and REJOIN edges;
2. remove assignments belonging to leaving or non-action-bearing UAVs;
3. preserve any valid locked incumbents;
4. rematch the remaining duties one-to-one over the remaining UAVs;
5. ensure the result is a partial injection.

In the worked example, seven UAVs are action-capable after one leaves and another rejoins. At most seven duties can therefore be executably covered. The map with eight keys and UAV 5 appearing twice falsely claims an eighth covered duty. The measured same-step ordering—LEAVEs first, then REJOINs—explains how this state is created.

A local implementation may realize the invariant by refusing a second assignment in the REJOIN branch, but the frozen scientific object should be the injective post-transition map, not one particular conditional statement.

---

# 2. The R5 treatment object

## 2.1 Separate ownership claims from executable assignments

The current workflow has conflated at least three objects:

1. **Raw assignment ledger**
   [
   m^{\mathrm{raw}}_t
   ]
   —what the dictionary claims.

2. **Executable assignment**
   [
   m^{\mathrm{exec}}_t
   ]
   —pairs whose holder is present, action-capable, and whose action is actually generated from that duty target.

3. **Covered-duty set**
   [
   C_t=\operatorname{dom}(m^{\mathrm{exec}}_t).
   ]

Freeze:

[
m^{\mathrm{exec}}_t
===================

\left{
(d,u)\in m^{\mathrm{raw}}_t:
\begin{array}{l}
u\text{ is present and action-capable},\
u\text{ is not charging or otherwise overridden},\
\text{the scripted action for }u\text{ is generated from }d
\end{array}
\right}.
]

`m_exec` must be injective.

This retains an optional ownership ledger if the controller needs one for lifecycle history, but prevents that ledger from being mistaken for physical coverage or R5 treatment support.

## 2.2 The derangement domain

Let (U_e) be the eligible action-bearing incumbents under the already frozen six conditions, and define:

[
D_e
===

{d\in\operatorname{dom}(m^{\mathrm{exec}}_t):
m^{\mathrm{exec}}_t(d)\in U_e}.
]

The R5 control solves:

[
a:U_e\rightarrow D_e
]

as a bijection, with:

[
a(u)\ne d_0(u),
]

and with all target-equivalent alternatives excluded under the registered geometric tolerance.

Because `m_exec` is injective:

[
|U_e|=|D_e|.
]

This restores A3 after the source assignment invariant is repaired. There is no need to replace A3 with a multiset or holder–duty-pair formulation.

## 2.3 Why holder–duty pairs are the wrong object

Under the current defective map, treating:

```text
(UAV 5, duty 5)
(UAV 5, duty 7)
```

as two distinct commitment tokens would duplicate one physical action authority. The derangement could appear bijective over tokens while still asking one UAV to execute two targets.

That would validate bookkeeping rather than individual renewal. It is precisely the kind of surface-semantic substitution the project principles prohibit. Evidence must establish executable behavior, not labels or assignments that the executor cannot realize.

---

# 3. Branch (b): is a phantom duty covered?

# **No. A phantom duty is uncovered.**

Use the following vocabulary:

| State                 | Meaning                                                                         |
| --------------------- | ------------------------------------------------------------------------------- |
| `CLAIMED`             | duty appears as a key in the raw map                                            |
| `ASSIGNED_EXECUTABLY` | exactly one action-bearing UAV receives that duty as its actual target          |
| `COVERED_BY_CONTROL`  | executably assigned under the source-control semantics                          |
| `TASK_SERVED`         | environment-level QoS or task outcome; determined separately by the environment |

The duplicate-holder phantom is:

```text
CLAIMED = yes
ASSIGNED_EXECUTABLY = no
COVERED_BY_CONTROL = no
```

Whether the environment happens incidentally to serve users near that location does not transform the phantom into a valid duty assignment.

The same distinction applies to the mirror case in `full_sync_SET`: a charging UAV may remain in the raw map between check boundaries, but the charging branch of `scripted_source_actions` does not fly it toward that duty. The duty is therefore not executably covered during that period.

The two defects should not be collapsed into one implementation diagnosis:

* `constructive_mixed`: **non-injective assignment**, followed by lossy inversion;
* `full_sync_SET`: **stale inactive-holder assignment** between check boundaries.

Both can produce a duty that the raw map calls assigned but no UAV’s duty-directed action serves. Their corrective mechanisms differ.

## Treatment consequence

Every future support, exposure, same-support and coverage assertion must be computed from `m_exec`, not from:

```python
set(duty_map.keys())
```

or from a lossy inversion of a non-injective map.

If raw-map injectivity fails, the instrument must fail closed. It must not select one duty by insertion order, silently drop another, or choose a canonical survivor post hoc.

---

# 4. Branch (c): obligations A and B

## 4.1 Obligation A

# **A is reopened, but not erased wholesale**

### Reopened

* **A1:** its domain was defined using raw covered duties rather than executably covered duties.
* **A2:** “noneligible pairs remain fixed” is undefined when one physical holder appears in multiple pairs.
* **A3:** the source-side injectivity premise was false.
* **A4:** “one forbidden incumbent edge per eligible agent” requires one uniquely defined incumbent duty.

The 2,000 randomized checks cannot validate A3 because their generator created injective maps by construction. They checked a consequence of the premise rather than whether the source satisfied the premise.

### Retained

The following mathematical lemmas survive once the corrected bipartite graph is supplied:

* canonical minimum-distance matching;
* explicit lexicographic tie resolution;
* sparse-graph feasibility;
* Hall-witness support;
* logical exclusion of forbidden edges.

The sparse feasible/infeasible checks and Hall-witness correspondence concern a well-defined graph and are independent of the source’s defective map construction.

### New A closure condition

A closes again only after proving:

1. `m_exec` is a partial injection at every admitted boundary;
2. (D_e) is derived from `m_exec`, not the raw map;
3. every eligible UAV has exactly one incumbent duty;
4. every eligible duty has exactly one holder;
5. the solver graph is built from those exact sets;
6. an injectivity violation fails before matching begins.

The strict xfail in the focused suite is the correct current posture; it should not be removed until that invariant is realized and the result semantics are reconciled.

---

## 4.2 Obligation B

# **B’s closed status is revoked**

The reported `1200/1200` feasibility count was computed through:

```python
uav_to_duty = {u: d for d, u in duty_map.items()}
```

and therefore omitted one duty whenever a UAV held two. The current B source explicitly acknowledges that the view was lossy on roughly one third of the development check boundaries.

The result may be preserved as:

> Feasibility of derangement over the one-duty-per-UAV view actually consumed by the defective action executor, on development topology `20260725`.

It does not establish feasibility of the corrected R5 treatment domain.

B must be repeated after:

* source-map injectivity is repaired;
* executable coverage is defined;
* simultaneous lifecycle transitions are corrected;
* and the same corrected source trajectory is used by the feasibility probe.

The source trajectory itself can change after the repair, so the old rows cannot simply be reinterpreted through a new domain.

## 4.3 Obligation C and later obligations

C had not closed; its reported `450/450` same-support passes do not become evidence.

The witness currently checks, among other things:

```python
set(m1.values()) == set(m0.values())
```

which discards multiplicity and cannot establish injectivity. It must add explicit fail-closed predicates for:

```text
incoming executable map injective
outgoing executable map injective
one action-bearing duty per UAV
raw claimed duties == executably represented duties, where coverage is asserted
```

The “noneligible incumbent moved” negative becoming unconstructible was not merely an inconvenient source state. It exposed that the witness’s treatment object was undefined. The existing negative correctly stayed red, but a new duplicate-holder negative is now mandatory.

D, E, F and G remain open. None is newly invalidated because none had closed.

---

# 5. R4 artifact disposition

## 5.1 Historical artifact

The historical JSON and its emitted string remain immutable:

```text
PART_A_CONTRADICTION
```

Do not rewrite the artifact.

## 5.2 Authoritative scientific status

# **R4 is no longer a valid R4 source-necessity measurement**

The previous disposition identified one defect in the Part-A control: incumbent retention was permitted and unmeasured. The present evidence identifies an independent defect in the `constructive_mixed` arm:

* the duty map can become non-injective;
* action generation silently chooses one of the duplicated duties;
* the claimed coverage and executed action diverge.

The formal run did not persist an injectivity/executable-coverage witness capable of establishing that its trajectories avoided this state. Development evidence shows the path is common and structurally reachable, but it does not measure its prevalence on the R4 topology panel. The appropriate fail-closed conclusion is therefore:

> The R4 artifact cannot demonstrate that either named Part-A arm instantiated its registered semantics.

The previous interpretive label:

```text
PART_A_CONTROL_NON_IDENTIFYING_FOR_FORCED_INDIVIDUAL_RENEWAL
```

is superseded by the stronger local disposition:

```text
INVALID_R4_REALIZATION:
DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED
```

This is not a new branch written into the old artifact. It is its scientific disposition under newly established implementation evidence.

## 5.3 What remains citable

The artifact remains citable only as:

> A descriptive external-return observation produced by the exact historical code paths, including their noninjective/stale assignment behavior.

It cannot support:

* Part-A equivalence;
* persistence necessity or non-necessity;
* `constructive_mixed` versus true full renewal;
* or the masked focal stable/flex states.

The masked focal measurements are also affected. The map does not enter results only through physical actions: it also enters event certification, focal selection, survivor construction, legal-target construction and the event snapshot. `_stable_candidates_at` iterates every raw `(d,u)` entry and can therefore treat one UAV as more than one candidate; `_flex_survivors_at` collapses entries by UAV; the selected map and focal identities then enter the event estimand.

Thus the claim in §4 that the defect reaches registered quantities **only** through the actions flown is false. It also changes the conditioning set and focal-action identity.

Under the project’s result semantics, an invalid realization updates the implementation rather than the whole algorithm family.

No conclusion about R30, D7.3, D8 or the broader variable-lifetime thesis follows.

---

# 6. Challenges to §§3–4

## 6.1 The measured development prevalence is local

The `33.33%` check-boundary rate is a valid development-topology observation, not a population estimate. It establishes that the defect is recurrent rather than a constructed corner case on `20260725`; it does not establish the rate on the R4 panel.

## 6.2 “Every onset is same-step LEAVE+REJOIN” is locally supported

The measured onset classification and the code ordering agree:

* `airborne_positions` uses the post-step charging mask;

* all LEAVEs are processed before all REJOINs;

* the rejoiner can therefore enter the LEAVE rematch and then receive another duty in the REJOIN loop.

This explains the observed development defect. It should not be generalized as the only possible future route to noninjectivity once the controller changes.

## 6.3 The two arms do not have the same phantom mechanism

The phrase “both arms emit phantom duties” is acceptable only at the high-level meaning:

> the raw map claims an assignment for which no duty-directed action is executed.

At the representation level they are different:

* duplicate-holder overwrite;
* inactive-holder staleness.

The direct phantom census detects only the former, which the evidence note correctly acknowledges.

## 6.4 A3 is rescuable

The claim that A3 needs replacing outright is too strong.

It cannot survive over the current raw map, but it follows immediately once the treatment domain is changed to the injective executable assignment relation. The correct response is:

* repair the source invariant;
* redefine coverage;
* rerun the integration proof.

It is not necessary to invent a derangement over duplicate holder–duty tokens.

## 6.5 C’s witness has an untested precondition

The current C witness may correctly detect its existing mutations while still accepting a noninjective starting map. Its `UNCONSTRUCTIBLE` bucket is honest, but that does not establish witness completeness. A new injectivity and executable-coverage precondition is required before C can close.

---

# 7. Revised semantics to freeze

Before any further R5 realization, freeze these statements.

## Assignment invariant

```text
The executable duty assignment is a partial injection:
each executable duty has at most one holder,
and each action-bearing UAV holds at most one executable duty.
```

## Coverage

```text
A duty is covered by the controller iff exactly one action-bearing UAV's
scripted action is generated from that duty target.

Raw map membership alone does not establish coverage.
```

## Lifecycle update

```text
Simultaneous LEAVE/REJOIN transitions produce one injective post-transition
assignment over the final action-capable UAV set.

A rejoining UAV already assigned during the same transition batch cannot
receive a second duty.
```

## R5 domain

```text
R5 deranges eligible incumbents over the executably covered duty set.

Non-action-bearing, charging, failed, overridden or phantom assignments
are outside the treatment domain.
```

## Failure semantics

```text
noninjective executable map
lossy assignment inversion
claimed coverage without an action-bearing holder
    -> INVALID SOURCE-CONTROL REALIZATION
    -> no matching, no effect estimate, no synthetic zero
```

---

# 8. Retained portfolio

| Route                                                                      | Status                   | Causal role                                                                         | Strongest limitation                                                               |
| -------------------------------------------------------------------------- | ------------------------ | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **Injective executable `duty → UAV` relation**                             | **Selected**             | Preserves stable duty identity while making one-agent/one-action semantics explicit | Requires repairing lifecycle batching and repeating A–C                            |
| **Canonical `UAV → physical target` assignment as primary representation** | Live simpler alternative | Matches the executor by construction and makes duplicate holders impossible         | Stable duty identity and uncovered-duty bookkeeping must be represented separately |
| **Explicit multi-duty UAV controller**                                     | Parked / not selected    | Could make one UAV legitimately own several duties                                  | Requires a new composite executor and changes the source proposition               |
| **Abandon S7-S3 for a tenure-native source**                               | Retained fallback        | Avoids brittle duty-map abstraction entirely                                        | Changes the benchmark carrier                                                      |

The strongest simpler alternative is to make the authoritative control state:

[
u\mapsto z_u
]

rather than:

[
d\mapsto u.
]

One physical UAV then has one physical target by construction. Duty IDs can remain metadata for persistence tracking, but cannot overrule the executable assignment. This route should be raised if the repaired duty-map abstraction continues producing ownership/execution mismatches.

---

# 9. Scheduled next action

The next scientific artifact should be a **zero-compute source-assignment correction**, freezing:

1. partial-injection semantics;
2. executable coverage;
3. atomic lifecycle transition behavior;
4. R5’s revised treatment domain;
5. fail-closed handling of noninjective maps;
6. the R4 invalid-realization disposition.

After that correction is accepted through the ordinary implementation boundary:

* repair the development source controller;
* add direct injectivity and phantom-coverage negatives;
* rerun A1–A4 and B;
* revise and rerun C;
* then resume D–F.

No fresh confirmatory topology panel should be selected before those development obligations close.

**`D7.3` and `D8` remain blocked. This review authorizes neither implementation nor compute.**
