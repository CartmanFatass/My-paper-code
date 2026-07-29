# D7.S R5 — the exposure-certified Part-A control

**Status: DERIVATION, amended to Pro's ruling of 2026-07-29
(`MODIFY BEFORE FREEZE`).** Still not a frozen contract. Ruling and
reconciliation:
`docs/external-review/rounds/20260729_d7_s_r5_derangement_control/`.

## Why the old control has to go

`full_sync_SET` was supposed to remove individual persistence. It removes only
explicit incumbent *protection*: `full_sync_set_update`
(`scripts/audit_d7_s_event_aligned.py:941`) never receives an incumbent map, so
it cannot exclude one. Verified against source in
`docs/research/cdc/EVIDENCE_NOTES/20260729_D7_S_THE_FULL_SYNC_ARM_CAN_HAND_A_DUTY_BACK.md`.

Pro's ruling: the control was **doubly** non-identifying — retention permitted
and unmeasured, and the recomputed map applied one primitive step late. The
first defect alone suffices.

## What this control can and cannot conclude — read this before the mechanism

The no-persistence policy class and its optimum:

```text
Pi_notP = policies forbidding incumbent retention at every eligible check
V*_notP = sup over Pi_notP
pi_der  = minimum-distance derangement,  pi_der in Pi_notP,  V_D <= V*_notP
```

`pi_der` is a **member**, not the optimizer. So this is a **one-sided
falsification control**, never an oracle positive control:

| Observation | Smallest conclusion |
|---|---|
| Exposure-certified derangement equivalent within ±5 | Valid counterexample to individual-persistence necessity |
| Derangement materially worse | Comparator-specific negative; source necessity **unresolved** |
| Interval overlaps both regions | Unresolved |
| Exposure or support fails | No mechanistic result |

**The R4-style rule in which "full-sync materially worse" makes Part A pass is
not retained.** A worse result cannot reach `PERSISTENCE_NECESSARY_SOURCE`,
because another no-persistence controller could use a different derangement,
sacrifice a different duty, anticipate user motion, choose by expected `G`
rather than distance, or coordinate future derangements to offset transit cost.

A two-sided necessity test would need one of: an identified approximation to
`V*_notP`; a structural proof that min-distance upper-bounds every no-persistence
controller in `G`; a task-dynamic lower bound; or several structurally different
strong controls all failing with the residual gap bounded. **None is
established.**

Note also, and carry it into the contract: the assignment is optimal for
**transit distance only**, not for cumulative primary `G`. Calling it "the
constrained optimum" without that qualifier is how a worse result gets overread
as a source theorem.

## The control — matched formulation

At every shared check boundary (`DELTA = 10`, unchanged), permute **eligible
incumbents over the currently covered duty set**, holding every non-eligible
incumbent pair fixed:

```text
m0 : D -> U          incoming PARTIAL assignment
U_e                  eligible action-bearing incumbents
D_e = { d : m0(d) in U_e }
solve bijection a : U_e -> D_e
minimising  sum_{u in U_e} || p_u - z_{a(u)} ||
subject to  a(u) != d0(u)   for all u in U_e     (d0(u) = incumbent duty of u)
```

**An earlier version of this file mapped the full duty set, and that was false
for this source.** The registered source normally has eight duties and, after one
charging LEAVE, seven airborne UAVs, and `constructive_mixed` deliberately leaves
one unlocked duty uncovered. "Fewer airborne UAVs than duties" is the *normal
state*, not infeasibility — it becomes infeasibility only if the control insists
on covering every duty.

The matched form preserves the covered-duty set, the assignment count, the duty
targets and the non-eligible incumbents. **Only eligible agent-to-duty ownership
changes.** Letting the derangement arm pick a different *uncovered* duty would
bundle a coverage-allocation intervention on top of the persistence
intervention.

### Held fixed from R4

`DELTA = 10`; `H_STABLE = 139`; `MATERIALITY_MARGIN = 5.0`; the duty set; the
controller's information; the energy and charging policy; the shared check clock;
CRN continuation and the paired-contrast stream discipline; the stable-limb-only
scope of the Part-A block.

## Eligibility — frozen definition, six conditions

Not an implementation binding. An eligible active incumbent satisfies **all** of:

1. present and active at the pre-action check boundary;
2. airborne and not currently charging;
3. not failed, terminal or otherwise non-acting;
4. appears as an incumbent in the incoming duty map;
5. **its duty target — not a station-return or other override — determines the
   scripted action at that check**;
6. has at least one legal, geometrically distinct non-incumbent target in the
   retained covered-duty set.

Condition 5 is the one an earlier draft missed: `scripted_source_actions` can
ignore an airborne UAV's duty entirely when the energy controller sends it to a
station, so "airborne and not charging" is necessary but insufficient.

A newly rejoined agent that has not yet acquired an incumbent is **not** in the
retention denominator. Lifecycle logic establishes the incoming assignment first;
derangement then applies to the resulting incumbents.

An event with fewer than two eligible incumbents cannot instantiate full
derangement and is a **support miss**.

**That cardinality test is a pre-filter, not the support rule.** Obligation A
showed `n ≥ 2` is necessary but not sufficient: condition 6 removes edges, and
Hall's condition can fail at any size. Witness at `n = 3` with
`allowed = [{2}, {2}, {0,1}]` — two incumbents whose only geometrically distinct
alternative is the same duty cannot both be deranged. **The support decision is
"no full derangement exists, with a Hall witness", tested per event.** A contract
gating on cardinality alone would silently admit structurally infeasible events.

Recorded per check: active UAVs; number holding duties; number action-bearing;
number eligible; exclusions by reason; matching-graph size.

## Exposure — a conjunction, not a count

```text
EXPOSURE_OK = map_exposure_ok AND target_exposure_ok
              AND physical_exposure_ok AND lifetime_exposure_ok

map_exposure_ok       retained eligible incumbents == 0
target_exposure_ok    every eligible incumbent receives a target differing from
                      its incumbent target by more than the registered 1e-6 tolerance
physical_exposure_ok  every uncensored eligible incumbent's executed action sequence
                      differs from constructive_mixed at least once during the
                      DELTA-step interval
lifetime_exposure_ok  every uncensored eligible assignment run lasts EXACTLY one check
```

Retention count alone was load-bearing in the earlier draft while the same draft
acknowledged that a different duty ID can denote a geometrically identical target
and that bookkeeping reassignment need not change the physical action. Those
cannot both stand.

"Run lengths concentrated at one check" is too weak: for uncensored commitments
the requirement is exact. **Lifecycle-truncated runs are reported separately as
censored** — never counted as pass or fail. Action comparison uses exact
deterministic action-array inequality over the `DELTA`-step interval. No
empirical fraction threshold appears anywhere.

## Cadence — corrected semantics, registered as a new intervention

Frozen pre-action ordering:

1. arrive at a shared pre-action boundary;
2. process lifecycle state already visible at that boundary;
3. establish the incoming duty map;
4. solve the exposure-certified derangement;
5. verify exposure feasibility;
6. synthesize that boundary's action **from the new map**;
7. carry the assignment to the next shared check, subject to lifecycle censoring.

This keeps `DELTA = 10`, the same clock, the same renewal frequency and the same
horizon — so it is not a new cadence. **But it is a different executed
intervention and it is conclusion-bearing**, so it is registered explicitly:

```text
derangement applied before action synthesis at every shared check
```

It is never a silent code correction to the historical result. **The R4 artifact
remains valid for what it measured** — lagged greedy reassignment recomputed
after the boundary action — and never becomes evidence for the repaired arm.

## Infeasibility — three cases, not one

**Before the intervention begins.** Build the matching graph at candidate-event
certification and **test feasibility, not cardinality**. No full derangement →
the event is ineligible; continue to the next candidate in that episode; if none
qualifies, the episode is a Part-A **support miss**, and the recorded reason
carries the Hall witness `(S, N(S))`. Typical causes: fewer than two eligible
incumbents; no geometrically distinct alternative; Hall-condition failure at
larger sizes. Never reported as zero effect, never a greedy or partial fallback.

**After an R5 continuation has begun.** The episode must **not** be quietly
dropped while its siblings are retained — that conditions the estimate on a
post-treatment event and preferentially preserves trajectories where forced
renewal was easiest. Instead: abort the Part-A instrument for that topology,
discard all of that topology's `D_A` units, record
`DERANGEMENT_CONTROL_NOT_TOTAL_ON_TOPOLOGY`, and neither retry the episode nor
substitute another.

**Solver or conformance failure is not infeasibility.** A legal matching exists
but the implementation reports infeasible, retains an incumbent, duplicates a
UAV, changes the covered-duty set, violates the pre-action phase, or fails an
exposure predicate → `INVALID_EVENT_ALIGNED_AUDIT`, zero tolerance.

A development-time structural derivation should make routine post-start
infeasibility impossible on registered fleet states. If it cannot, the comparator
is not a total policy and **no confirmatory panel is frozen.**

## Population

The eight R4 topologies may not carry the successor's confirmatory result. A
conclusion-bearing successor needs a newly frozen, untouched panel chosen by a
deterministic, predeclared rule, with the five-unit margin unchanged. A
same-R4-topology exercise is diagnostic development only and stays labelled
conditional.

## Development obligations A–G — all zero-compute, all before any panel

Full text in the ruling. Summary:

- **A. Mathematical support derivation** — assignment domain is the covered set;
  non-eligible pairs fixed; equal cardinality of eligible agents and duties;
  every forbidden incumbent edge absent; solver returns a full derangement when
  one exists; a failed matching carries an explicit Hall-condition witness. For
  small synthetic cardinalities, enumerate all legal assignments and verify the
  selected one is the true minimum-distance derangement under the registered
  tie-break.
- **B. Real source-state feasibility** on development topology `20260725`,
  recording per check: total duties, covered duties, airborne UAVs,
  action-bearing incumbents, eligible matching size, whether a full derangement
  exists, and the reason for every exclusion. It must show the comparator is
  *routinely* executable, not that one hand-picked state passes.
- **C. Same-support witness** — covered set unchanged, assigned-UAV count
  unchanged, energy/charging decisions unchanged, only eligible ownership forced
  to change.
- **D. Pre-action cadence witness** — the deranged map exists before action
  synthesis, the interval's first action uses it, the map is carried for the
  intended interval. **Include the deliberately delayed R4 ordering as a paired
  negative and show the phase guard rejects it.**
- **E. Exact exposure witness**, with these five paired negatives, each of which
  must make the relevant guard go red: one permitted incumbent retention; a
  different duty ID at the same geometric target; post-action rather than
  pre-action recomputation; a partial derangement; a one-eligible-agent
  infeasible state.
- **F. Branch-semantic witness** — exercise all three statistically meaningful
  outcomes. **No branch may turn a worse heuristic result into
  `PERSISTENCE_NECESSARY_SOURCE`.**
- **G. Fresh-population procedure** — only after A–F pass.

## Implementation bindings — PM-decided, disclosed, none claim-defining

1. **Solver.** Rectangular linear assignment with forbidden cells at `+inf`,
   over `U_e × D_e`. Deterministic given inputs.
2. **Tie-break.** Lexicographic by `(duty_id, uav_id)` among optimal solutions,
   **produced by an explicit canonicalisation pass, not by the solver.**
   Obligation A found that `linear_sum_assignment` does not honour this
   tie-break: on the symmetric ring at `n = 4`, where every single-rotation
   derangement costs `56.568542` exactly, it returns an optimal assignment that
   is not the lexicographically smallest. The binding named a property the tool
   does not provide.

   The canonicalisation: take the optimal cost, then walk duties ascending and
   fix the smallest agent id whose forced completion still attains it. Verified
   against exhaustive enumeration on constructed ties (rings `n = 3…7`, integer
   lattices) and 200 random cases, plus 20 repeated solves of one tied input
   returning a single distinct result.
   `scripts/d7_s_r5_obligation_a_proof.py`,
   `docs/research/designs/D7_S_R5_OBLIGATION_A_SUPPORT_DERIVATION.md`.

   Ties are measure-zero in continuous positions, which is why random trials
   never surfaced this and the counterexample had to be constructed.

Eligibility was binding 3 in the earlier draft. It is now a frozen definition
above, on Pro's ruling — which is where I had flagged I was least sure it
belonged.

## The reusable principle

> A constrained intervention's unavoidable natural cost is part of its causal
> effect; the inferential defect arises when one heuristic member of the
> constrained policy class is treated as the class optimum.
