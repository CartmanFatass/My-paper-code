# Scientific ruling — D7.S R5 derangement control

**Stage reviewed:** `72a41fab3146c10caf4b802ff7635042de4ed056`

## Overall disposition

# **MODIFY BEFORE FREEZE**

An exposure-certified derangement is the correct family of successor controls, but the present derivation is not yet a valid two-sided test of individual-persistence necessity.

The central distinction is:

\[
\Pi_{\neg P}
=
\{\text{policies that forbid incumbent retention at every eligible check}\},
\]

\[
V_{\neg P}^{*}
=
\sup_{\pi\in\Pi_{\neg P}}V(\pi).
\]

The proposed minimum-distance derangement is one member,

\[
\pi_{\mathrm{der}}\in\Pi_{\neg P},
\]

not the optimizer of external return over that policy class. Therefore:

- if \(\pi_{\mathrm{der}}\) is equivalent to `constructive_mixed`, it supplies a valid counterexample to the necessity of individual persistence;
- if \(\pi_{\mathrm{der}}\) is materially worse, it proves only that this particular least-distance derangement is worse—not that every no-persistence policy is worse.

The successor Part-A control is thus admissible as a **one-sided falsification control**. It is not yet an oracle positive control that can certify persistence necessity.

There are also three required definition corrections:

1. Derange the **currently covered duty set**, not all eight source duties.
2. Define eligibility by whether an incumbent’s duty actually controls its action at that check, not merely by `not charging`.
3. Strengthen `EXPOSURE_OK` beyond map retention: different duty IDs with identical targets or identical executed action trajectories do not establish physical renewal.

The phase repair is a correction to the intended check-boundary semantics, but because it changes the executed intervention, it belongs in a new R5 contract and fresh population.

For infeasibility, use different rules before and after intervention begins:

- pre-intervention infeasibility is an event/episode support miss;
- infeasibility reached after an R5 continuation starts aborts that topology’s Part-A instrument rather than permitting selective episode deletion.

`D7.3` and `D8` remain blocked.

---

# 1. 4a — comparator validity

## 1.1 Is incumbent exclusion itself an invalid confound?

**No. It is the treatment definition.**

The scientific counterfactual is:

> What is lost when active individual commitments are prohibited from persisting across a renewal opportunity?

Forbidding the incumbent edge is how the no-persistence policy class is operationalized. Any unavoidable transit, reassignment, energy, QoS or safety cost caused by that prohibition is a **mediator of the value of persistence**, not an external confound.

The comparison remains matched when both arms retain:

- the same physical duty targets;
- the same number of covered duties;
- the same active UAV set;
- the same information;
- the same energy/charging controller;
- the same check clock;
- the same external objective;
- and CRN-matched continuation randomness.

The project’s evidence principles require a temporal comparator to match the lifetime claim and require a positive control to make the target behavior necessary rather than merely permitted. fileciteturn90file0L126-L163

The problem is not that exclusion has a cost. The problem is whether the proposed controller is the **strongest no-persistence alternative**.

---

## 1.2 What can minimum-cost derangement identify?

Let \(V_C\) denote the value of `constructive_mixed`, and \(V_D\) the value of the minimum-distance derangement.

Because

\[
V_D\le V_{\neg P}^{*},
\]

the two possible findings are asymmetric.

### Equivalence or superiority

If

\[
V_D\ge V_C-5
\]

with the registered equivalence inference, then at least one exposure-certified no-persistence controller matches the persistent controller within the task-semantic margin.

That is enough to refute:

> Individual persistence is necessary on this source at the five-\(G\)-unit scale.

This result would carry genuine benchmark/mechanism weight.

### Materially worse

If

\[
V_D<V_C-5,
\]

that does **not** establish

\[
V_{\neg P}^{*}<V_C-5.
\]

Another no-persistence controller could:

- use a different full derangement;
- sacrifice a different duty;
- anticipate future user movement;
- choose assignments by expected \(G\), rather than distance;
- or coordinate future derangements to offset the immediate transit cost.

Therefore a materially worse result supports only:

> The minimum-distance exposure-certified derangement is materially worse than `constructive_mixed`.

It cannot close the source-necessity prerequisite and cannot unblock D7.3.

## Required R5 Part-A semantics

The successor should have these interpretations:

| Observation | Smallest conclusion |
|---|---|
| Exposure-certified derangement equivalent within \(\pm5\) | Valid counterexample to individual-persistence necessity |
| Derangement materially worse | Comparator-specific negative; source necessity remains unresolved |
| Statistical interval overlaps both regions | Unresolved |
| Exposure or support fails | No mechanistic result |

Do not retain an R4-style rule in which “full-sync materially worse” automatically makes Part A pass.

A two-sided necessity test would require one of:

1. an identified approximation to \(V_{\neg P}^{*}\);
2. a structural proof that the minimum-distance derangement upper-bounds every other no-persistence controller in \(G\);
3. a task-dynamic lower bound showing that every legal derangement necessarily loses more than five units;
4. multiple structurally different strong no-persistence controls that all fail, with the remaining policy-class gap explicitly bounded.

None is currently established.

---

## 1.3 The optimization domain is wrong as written

The derivation defines a map over the full duty set \(D\):

\[
m:D\rightarrow U
\]

with \(m\) injective. But the registered source normally has eight duties and, after one charging LEAVE, seven airborne UAVs. The existing `constructive_mixed` realization explicitly leaves exactly one unlocked duty uncovered when the fleet has one fewer body than duties. fileciteturn92file0L3-L9

Thus the statement that “fewer airborne UAVs than duties” makes derangement infeasible is an artifact of the proposed formulation, not a property of the source. The present unconstrained full-sync implementation already maps as many duties as there are airborne UAVs and leaves the remainder uncovered. fileciteturn92file0L94-L112

### Correct matched formulation

Let the incoming partial assignment be

\[
m_0:D\rightharpoonup U.
\]

Let \(U_e\) be the eligible action-bearing incumbents, and let

\[
D_e=\{d:m_0(d)\in U_e\}.
\]

Hold every noneligible incumbent pair fixed. Solve a bijection

\[
a:U_e\rightarrow D_e
\]

that minimizes

\[
\sum_{u\in U_e}
\left\|p_u-z_{a(u)}\right\|
\]

subject to

\[
a(u)\ne d_0(u)
\quad\forall u\in U_e,
\]

where \(d_0(u)\) is the incumbent duty of \(u\).

This preserves:

- the same covered-duty set;
- the same number of assignments;
- the same duty targets;
- the same noneligible incumbents.

Only eligible agent-to-duty ownership changes.

That is substantially better matched than allowing the derangement arm to choose a different uncovered duty. The latter would combine:

1. elimination of persistence; and
2. a different team duty-composition decision.

---

## 1.4 Eligibility sub-branch

The proposed definition—airborne, non-charging and holding a duty—is necessary but insufficient.

`scripted_source_actions` can ignore an airborne UAV’s duty because the energy controller sends it to a charging station. Charging UAVs are also controlled by charging logic rather than their duty assignment. fileciteturn76file0L21-L74

Freeze an eligible incumbent as an agent satisfying all of:

1. present and active at the pre-action check boundary;
2. airborne and not currently charging;
3. not failed, terminal or otherwise non-acting;
4. appears as an incumbent in the incoming duty map;
5. its duty target—not a station-return or other override—determines the scripted action at that check;
6. has at least one legal, geometrically distinct non-incumbent target in the retained covered-duty set.

Charging or absent UAVs are correctly excluded because they carry no executable active commitment.

A newly rejoined agent that has not yet acquired an incumbent is not counted in the retention denominator. The lifecycle/update logic should first establish the incoming assignment; derangement is then applied to the resulting incumbents at the check boundary.

Record per check:

- number of active UAVs;
- number holding duties;
- number action-bearing;
- number eligible;
- exclusions by reason;
- size of the matching graph.

An event with fewer than two eligible incumbents cannot instantiate full derangement and is a support miss.

---

## 1.5 `EXPOSURE_OK` is currently too weak

The proposed predicate is:

```text
retained_eligible_incumbents == 0
```

But the same design also acknowledges that:

- a different duty ID can denote a geometrically identical target;
- bookkeeping reassignment need not change the physical action. fileciteturn86file0L60-L86

Those statements are inconsistent if retention count alone is load-bearing.

Freeze exposure as the conjunction:

```text
map_exposure_ok:
    retained eligible incumbents == 0

target_exposure_ok:
    every eligible incumbent receives a target differing
    from its incumbent target by more than the registered 1e-6 tolerance

physical_exposure_ok:
    for every uncensored eligible incumbent, its executed action sequence
    differs from constructive_mixed at least once during the Δ-step interval

lifetime_exposure_ok:
    every uncensored eligible assignment run lasts exactly one check
```

Then:

```text
EXPOSURE_OK =
    map_exposure_ok
    AND target_exposure_ok
    AND physical_exposure_ok
    AND lifetime_exposure_ok
```

“Run lengths concentrated at one check” is too weak. For uncensored eligible commitments, the requirement is exact. Lifecycle-truncated runs must be reported separately as censored rather than counted as either a pass or failure.

The action comparison can use exact deterministic action-array inequality over the \(\Delta\)-step interval; no new empirical fraction threshold is needed.

---

# 2. 4b — cadence correction or new intervention?

## Scientific ruling

**It is a correction to the intended cadence, but it must be registered as a new R5 intervention.**

The intended phrase “reassign every duty at each shared check” refers to a pre-action decision at that check. The current implementation synthesizes and executes the action from the incoming map, then recomputes the map. The new assignment consequently governs the following interval with a uniform one-step phase lag. fileciteturn87file0L45-L67

The corrected ordering is:

1. arrive at a shared pre-action boundary;
2. process lifecycle state already visible at that boundary;
3. establish the incoming duty map;
4. solve the exposure-certified derangement;
5. verify exposure feasibility;
6. synthesize that boundary’s action from the new map;
7. carry the assignment until the next shared check, subject to lifecycle censoring.

This preserves:

- \(\Delta=10\);
- the same shared check clock;
- the same renewal frequency;
- the same horizon.

So it is not a new clock or a new cadence.

But it is a different executed intervention from R4, and the difference is conclusion-bearing. Therefore it cannot be treated as a silent code correction to the historical R4 result. R5 must register:

```text
derangement applied before action synthesis at every shared check
```

The R4 artifact remains a valid result for:

> lagged greedy reassignment recomputed after the boundary action.

It does not become evidence for the repaired arm.

## R4’s control was doubly non-identifying

The question’s characterization is correct:

1. incumbent retention was allowed and unmeasured;
2. the recomputed map took effect one primitive step late.

The first defect is sufficient to make the control non-identifying. The second independently shows that its physical timing did not instantiate the intended boundary intervention.

---

# 3. 4c — infeasibility scope

## Ruling: distinguish pre-treatment support from post-start instrument failure

A single rule for all infeasibility would conflate two scientifically different situations.

## 3.1 Infeasible before the intervention begins

At candidate-event certification, construct the matching graph.

If no full derangement exists:

- the event is ineligible;
- continue to the next candidate event within that episode;
- if no candidate qualifies, the episode is a Part-A support miss.

This is a pre-treatment support decision and may be handled at episode level.

Typical reasons include:

- fewer than two eligible incumbents;
- no geometrically distinct alternative;
- failure of the matching graph’s Hall condition.

It must not be reported as zero effect and must not invoke a greedy or partial fallback.

## 3.2 Infeasible after an R5 continuation has begun

Once an episode has been admitted and the derangement policy is running, later infeasibility must **not** cause that one episode to be quietly dropped while retaining the other completed episodes from the same topology.

That would condition the Part-A estimate on a post-treatment event and could preferentially preserve trajectories on which forced renewal was easiest.

Instead:

- abort the Part-A instrument for that topology;
- discard all of that topology’s Part-A \(D_A\) units;
- record `DERANGEMENT_CONTROL_NOT_TOTAL_ON_TOPOLOGY`;
- do not retry the episode or substitute another one.

The final contract may let the overall population continue only through a separately frozen topology-support rule. The aborted topology contributes no Part-A estimate.

## 3.3 Solver or exposure failure is not mathematical infeasibility

Distinguish:

### Structural infeasibility

The matching problem has no legal solution. This updates source/control support.

### Solver or conformance failure

A legal matching exists, but the implementation:

- reports infeasible;
- retains an incumbent;
- assigns duplicate UAVs;
- changes the covered-duty set;
- violates the pre-action phase;
- or fails one of the exact exposure predicates.

That is:

```text
INVALID_EVENT_ALIGNED_AUDIT
```

with zero tolerance, not a source-support outcome.

A development-time structural derivation should make routine post-start infeasibility impossible on the registered fleet states. If it cannot, the comparator is not yet a total policy and no confirmatory panel should be frozen.

---

# 4. Challenges to §§2–3

## 4.1 “Retention is geometrically favoured” is plausible, not established

The source facts establish only that retention is permitted. The stronger statement is an inference.

Reasons it may often hold:

- UAVs are driven toward their incumbent duty;
- nearest assignment therefore often favours the incumbent. fileciteturn87file0L31-L43

Reasons it need not hold:

- service centroids move with users;
- a LEAVE/REJOIN can have just rematched incumbents;
- another UAV can be nearer after motion;
- an airborne UAV may be travelling toward a station rather than its duty;
- nearest-duty geometry can change between checks.

No incumbent-retention data were serialized, so this explanation of \(D_A\approx0\) is unmeasured. The durable reason R4 is non-identifying is:

> retention was neither prohibited nor recorded.

That conclusion does not depend on asserting that retention was frequent.

## 4.2 The all-duty formulation is false for the registered source

The source normally has more duties than airborne UAVs after a LEAVE, and `constructive_mixed` deliberately leaves one duty uncovered. fileciteturn92file0L3-L9

Therefore:

> “fewer airborne UAVs than duties” is not by itself derangement infeasibility.

It becomes infeasibility only if the control wrongly insists on assigning every duty. The correct control permutes incumbents over the currently covered-duty set.

## 4.3 Minimum distance is not external-return optimality

The derivation calls the assignment a constrained optimum, but it is optimal only for transit distance. It is not proven optimal for cumulative primary \(G\).

That distinction must appear in the contract and branch meanings. Otherwise a worse result will again be overread as a source theorem.

## 4.4 Zero retention alone does not prove executable renewal

The design already records target displacement and action divergence because map identity is insufficient. Those quantities must enter exposure validity, not remain optional diagnostics.

## 4.5 Same physical support must be explicit

To isolate ownership persistence, R5 must keep the same covered-duty set as the incoming `constructive_mixed` map. Permitting the derangement arm to choose a different uncovered duty would add a separate coverage-allocation intervention.

---

# 5. Development obligations before freezing a confirmatory panel

No new topology panel should be selected until the following zero-compute and proof-sized conditions close.

## A. Mathematical support derivation

Prove for the registered event state:

1. the assignment domain is the current covered-duty set;
2. noneligible incumbent pairs are fixed;
3. eligible agents and eligible duties have equal cardinality;
4. every forbidden incumbent edge is absent;
5. the matching solver returns a full derangement when one exists;
6. a failed matching includes an explicit Hall-condition or equivalent infeasibility witness.

For small synthetic cardinalities, enumerate all legal assignments and verify that the selected solution is the true minimum-distance derangement with the registered tie-break.

## B. Real source-state feasibility

On development topology `20260725`, record at every relevant check:

- total duties;
- covered duties;
- airborne UAVs;
- action-bearing incumbents;
- eligible matching size;
- whether a full derangement exists;
- reason for every exclusion.

The exercise must show that the comparator is routinely executable on the source rather than passing one hand-selected state.

## C. Same-support witness

For each tested check, verify:

```text
covered duty set under derangement
    ==
covered duty set entering the check

number of assigned active UAVs unchanged

energy/charging decisions unchanged

only eligible agent-to-duty ownership is forced to change
```

## D. Pre-action cadence witness

At every check:

- the deranged map exists before action synthesis;
- the first action of the interval uses that map;
- the map is carried for the intended interval.

Include the deliberately delayed R4 ordering as a paired negative and show that the phase guard rejects it.

## E. Exact exposure witness

For every uncensored eligible incumbent:

- zero incumbent retention;
- geometrically distinct target;
- non-identical action trajectory during \(\Delta\);
- assignment run length exactly one check.

Include at least these paired negatives:

1. one permitted incumbent retention;
2. a different duty ID at the same geometric target;
3. post-action rather than pre-action recomputation;
4. a partial derangement;
5. a one-eligible-agent infeasible state.

Each must make the relevant guard go red.

## F. Branch-semantic witness

Exercise all three statistically meaningful Part-A outcomes:

```text
exposure-certified equivalence
    -> counterexample to persistence necessity

minimum-distance derangement materially worse
    -> comparator-specific negative only

unresolved interval
    -> unresolved
```

No branch may turn a worse heuristic result into `PERSISTENCE_NECESSARY_SOURCE`.

## G. Fresh-population procedure

Only after A–F pass:

- choose the untouched topology panel by a deterministic, predeclared rule;
- freeze its seed namespace and episode blocks;
- prohibit reuse or pooling of R4 topologies;
- retain the five-unit margin unchanged.

A same-R4-topology exercise may be used for diagnostic development only and must remain labelled conditional.

---

# 6. Retained portfolio

| Route | Status | Causal role | Raising or lowering observation |
|---|---|---|---|
| **Minimum-distance full derangement** | **Selected as one-sided falsification control** | Supplies an explicit no-persistence counterexample if equivalent | Raised by exact exposure and equivalence; a worse result does not establish necessity |
| **External-\(G\)-optimal constrained derangement** | Live, stronger | Approximates \(V_{\neg P}^{*}\), allowing a two-sided necessity test | Raised if a tractable, pre-registered optimizer or valid upper bound can be derived |
| **Portfolio of strong no-persistence controllers** | Live | Reduces dependence on one heuristic comparator | Raised if several information-matched controls agree on a negative consequence |
| **Tenure/non-transferable-state source** | Retained fallback | Makes persistence necessity structurally identifiable | Raised if S7-S3 cannot support a total, strong no-persistence comparator |
| Current greedy recompute-every-check controller | Retained ordinary reduction | Tests frequent replanning without guaranteed renewal | Never again labelled forced individual renewal |

---

# Smallest scientific update

The R5 derivation establishes a valid way to **force exposure**, but not yet a valid way to infer necessity from a worse return.

The reusable principle is:

> A constrained intervention’s unavoidable natural cost is part of its causal effect; the inferential defect arises when one heuristic member of the constrained policy class is treated as the class optimum.

The next action is the proof-sized feasibility and exposure exercise above, after the derivation is amended. It is not a conclusion-bearing source run.

**D7.3 and D8 remain blocked. This review authorizes neither implementation nor compute.**