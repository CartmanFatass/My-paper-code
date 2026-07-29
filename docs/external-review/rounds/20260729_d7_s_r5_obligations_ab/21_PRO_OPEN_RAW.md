# Scientific ruling — D7.S R5 obligations A–B

**Stage reviewed:** `59a221d80bd5d6af6c9459140c46e1cb64e57806`

## Overall disposition

# **A IS SUBSTANTIVELY ACCEPTED WITH TWO REALIZATION CORRECTIONS; B PASSES ONLY THE DEVELOPMENT-TOPOLOGY BAR; C–F ARE SCIENTIFICALLY IN SCOPE BUT REQUIRE ORDINARY IMPLEMENTATION/COMPUTE AUTHORITY**

The durable decisions are:

1. The explicit canonical tie-break stands.
2. Full matching feasibility with a Hall witness—not cardinality—is the correct event-support rule.
3. B establishes that the comparator is routinely feasible along the **observed `constructive_mixed` trajectories on development topology `20260725`**. It does not establish topology-population support or totality under the derangement’s own induced trajectories.
4. A proof-sized development harness applying the derangement is the correct next scientific apparatus for C–F. However, the earlier phrase “A–G are all zero-compute” was wrong:
   - A is zero-environment-compute;
   - B already stepped the environment;
   - C–E require implementation and environment stepping;
   - F can be synthetic;
   - G is design/provenance work.
5. This review defines the permitted scientific scope but does **not itself authorize code or compute**. The Project Manager must route the harness through the repository’s ordinary implementation and development-compute authority. The project principles explicitly separate scientific judgment from implementation authority and state that review output alone is not execution authorization. fileciteturn103file0L100-L107 fileciteturn103file0L217-L222
6. G must freeze its own prospective feasibility and totality gates. It cannot inherit B’s 1200/1200 result.
7. No confirmatory topology panel is frozen. `D7.3` and `D8` remain blocked.

---

# 1. 4a — development-only derangement harness

## Scientific ruling

**Yes: a development-only C–F derangement harness is the correct next scientific apparatus.**

But the precise authority statement is:

> The harness is scientifically admissible within the scheduled R5 development obligations. This reply does not itself authorize its implementation or execution; that remains subject to the repository’s ordinary Project Manager and compute-authorization boundary.

The ambiguity arose because the earlier ruling both selected A–G and ended with “authorizes neither implementation nor compute.” The correct reconciliation is not to call the intervention harness “zero-compute.” It is to distinguish:

- **scientific selection of the next apparatus**, owned here;
- **technical implementation and development execution**, owned elsewhere.

## The permitted boundary

The development apparatus may:

- operate only on development topology `20260725`;
- reuse already observed development episode seeds;
- apply the proposed derangement to cloned or development-only environments;
- step the environment only as needed to establish C, D and E;
- run synthetic branch witnesses for F;
- record raw maps, eligibility sets, assignments, targets, actions, lifecycle censoring and run lengths;
- construct deliberate negative controls;
- stop once each required witness and paired negative has been obtained.

It must:

```text
label every artifact:
    D7_S_R5_DEVELOPMENT_OBLIGATIONS_NOT_A_RESULT

use no confirmatory topology;
use no R4 or future R5 conclusion-bearing population identity;
emit no source-necessity branch;
perform no topology bootstrap or effect-size inference;
perform no training, policy optimization or model update;
select no threshold, seed panel or comparator variant from the observed outputs;
remain outside the conclusion-bearing audit path.
```

A dedicated development-only seed namespace is preferable for provenance, but it carries no inferential status and must be rejected by any future confirmatory pooler.

## Independence requirement

The harness must not merely call an `EXPOSURE_OK` function and then report that the same function returned true. Its witness layer must independently derive from traces:

- incoming and outgoing maps;
- incumbent and assigned targets;
- actual action arrays;
- check boundaries;
- lifecycle censoring;
- assignment run lengths.

The five paired negatives must perturb the production-side behavior while the independent witness remains unchanged. Otherwise the control and its test would again share one narrowed definition of exposure.

## Correction to the question’s provenance claim

The statement that **both** current harnesses are standalone and import nothing from the audit path is false.

Obligation A is standalone. Obligation B explicitly imports `audit_d7_s_event_aligned` and then constructs and steps real environments through that module’s helpers. fileciteturn101file0L3-L10 fileciteturn102file0L30-L46 fileciteturn102file0L142-L168

That does not invalidate B’s local observation. It means B is:

> a probe of feasibility under the current audit/source realization,

not:

> an independent verification that the audit’s source realization is correct.

The second overstatement is that B was “zero-compute.” It ran eight 1500-step episodes and observed 1200 check boundaries. It was non-conclusion-bearing development compute, not zero-compute. fileciteturn99file0L10-L21

---

# 2. 4b — the two obligation-A amendments

## 2.1 Canonical tie-break

# **Accepted**

The registered reproducibility property is:

> Among equal-cost legal derangements, return the lexicographically first assignment by `(duty_id, uav_id)`.

The bare `linear_sum_assignment` result does not provide that property. The symmetric-ring counterexample demonstrates an actual mismatch between the specified binding and the tool’s behavior. The explicit canonicalization pass is therefore the correct repair. fileciteturn98file0L58-L82

This is primarily a **realization correction**, not a new scientific alternative:

- the scientific control remains minimum-transit derangement;
- only selection among exact optima is made deterministic;
- the result branch and causal proposition do not change.

The canonicalization logic—walking duties in ascending order and choosing the smallest agent whose constrained completion preserves the optimum—is consistent with the frozen tie-break. The exhaustive ring, lattice and repeated-solve evidence is appropriate for this technical claim. fileciteturn101file0L54-L94 fileciteturn101file0L147-L166

### Required contract reconciliation

The current derivation document is internally inconsistent:

- the obligation-A harness uses a large **finite** sentinel and explains why `inf` cannot carry infeasibility;
- the amended R5 design still says the implementation uses forbidden cells at `+inf`.

fileciteturn98file0L50-L56 fileciteturn100file0L247-L253

Do not freeze either numerical encoding as the scientific object. Freeze:

> Forbidden edges are logically absent. The implementation must use a representation that preserves the legal optimum and must reject any returned forbidden edge.

A finite sentinel is acceptable only when it is proved larger than every possible legal total cost for the registered geometry. The Hall witness—not the sentinel-valued solver output—owns infeasibility.

## 2.2 Hall-witness support rule

# **Accepted and mandatory**

The support predicate is:

```text
a full derangement exists on the frozen matching graph
```

not:

```text
n_eligible >= 2
```

The latter is only a fast necessary pre-filter. Once geometric legality removes additional edges, Hall’s condition can fail at any cardinality. The `n=3` construction with two agents sharing one available target is a valid counterexample to the cardinality-only rule. fileciteturn98file0L85-L117

A refusal must carry:

```text
S
N(S)
|S|
|N(S)|
```

not merely the size of the neighbourhood.

This is a protected source-support definition, but it is not a newly invented amendment in this round: it is the correct realization of the prior R5 ruling and is already reflected in the amended design. fileciteturn100file0L115-L124

## Is obligation A fully closed?

**Its scientific definition is closed; its realization proof needs one final strengthening.**

The exhaustive cost/tie tests currently use the complete non-incumbent graph. The actual control can contain sparse legal graphs after geometric exclusions. Before A receives a technical certificate, add exhaustive small-\(n\) cases covering:

- feasible sparse graphs;
- infeasible sparse graphs;
- sparse graphs with tied optimal completions;
- comparison between the canonical solver and brute force;
- verification that the reported Hall witness corresponds to the exact graph given to the solver.

This does not reopen the scientific contract.

---

# 3. 4c — does B meet the bar?

## Local ruling

# **Yes, B meets the development-topology “not one hand-picked state” bar**

Across the observed development sample:

```text
8 episodes
1200 shared check boundaries
1200 feasible full derangements
0 infeasibility witnesses
```

The eligible-set distribution ranged from 2 through 8, and the covered-duty count was 7 in 129 checks. That is materially stronger than demonstrating feasibility at one constructed state. fileciteturn99file0L24-L61

It also confirms two load-bearing corrections:

- the treatment domain cannot be the full eight-duty set, because ordinary post-LEAVE states contain only seven covered duties;
- duty-holding and airborne are insufficient for eligibility, because the energy controller overrode the duty action 1170 agent-checks. fileciteturn99file0L49-L76

## Required narrowing

The sentence:

> “The comparator is routinely executable on this source”

is too broad.

The supported statement is:

> The full matching was feasible at every observed pre-action check along eight `constructive_mixed` trajectories on development topology `20260725`.

B does **not** establish:

- feasibility on an unobserved topology;
- feasibility under a fresh population;
- feasibility after the derangement changes future positions and assignments;
- or totality of the derangement policy over its own induced state distribution.

The last point is especially important. B observes states generated by `constructive_mixed`. Once the derangement is applied, the UAV positions, duties and future matching graphs can diverge. A control feasible on the baseline trajectory can become infeasible later on its own trajectory.

Thus B closes:

```text
baseline-state development feasibility
```

but not:

```text
post-treatment policy totality
```

## The 100% must not be generalized

The 1200/1200 is a descriptive liveness witness on one fixed development topology, not an estimate of a source-wide feasibility probability.

The 22 checks at exactly `n_eligible=2` reinforce rather than eliminate the concern: they show that the development realization visits the feasibility boundary, while providing no bound on its frequency elsewhere. The B document itself correctly recognizes this limitation. fileciteturn99file0L85-L100

## One B-harness correction

The B harness repeatedly removes agents whose option set becomes empty after restricting duties to the current eligible pool. That treatment-set pruning is not yet stated as a fixed-point rule in the contract. fileciteturn102file0L73-L103

Before B is used as the conformance oracle for C–E, choose and freeze one interpretation:

1. compute the maximal self-consistent eligible set by iterating the zero-option pruning to a fixed point; then apply Hall to that fixed graph; or
2. freeze the initial eligible set once and classify any later empty adjacency as matching infeasibility.

Do not use an undocumented two-pass approximation.

No such exclusion was reported in the observed 1200 checks, so this correction does not currently overturn the 1200/1200 count. That invariance should be rechecked rather than assumed.

The harness should also explicitly implement or assert every condition in the six-part definition, including failed/terminal/non-acting state, rather than relying on those states being absent implicitly.

---

# 4. G requires its own feasibility precondition

# **Yes**

B cannot pre-pass a future R5 population.

The fresh-panel contract must freeze all of the following before any conclusion-bearing run.

## Event admission

At the candidate check, before treatment:

```text
matching graph constructed under frozen eligibility;
full derangement feasible;
Hall witness absent;
at least two eligible incumbents;
same covered-duty set available.
```

Failure is an event support miss. The episode may continue to its next pre-registered candidate event.

## Post-start totality

At every later shared check in the derangement continuation:

```text
full exposure-certified derangement remains feasible.
```

If it becomes infeasible after treatment begins:

- abort that topology’s Part-A instrument;
- discard all its Part-A units;
- record `DERANGEMENT_CONTROL_NOT_TOTAL_ON_TOPOLOGY`;
- do not silently drop the one adverse episode;
- do not retry or replace it.

This is already the correct distinction in the amended derivation. fileciteturn100file0L179-L204

## Panel-level support

Before selecting seeds, freeze:

- the minimum number of topologies with a total Part-A instrument;
- the minimum number of pre-treatment qualifying episodes per included topology;
- the result branch when those floors are not met.

A support failure must be read as:

```text
DERANGEMENT_CONTROL_SUPPORT_INSUFFICIENT
```

or an equivalent explicitly frozen source/control-pair result—not as equivalence, material inferiority or zero effect.

## No topology replacement

The fresh topology panel must be selected by a deterministic rule before feasibility is observed.

If support fails:

- do not replace the topology;
- do not add episodes;
- do not expand the panel unless such an expansion was frozen independently beforehand;
- do not reuse R4 topologies as confirmatory evidence.

A separate multi-topology development feasibility pilot may reduce operational risk, but it is not a substitute for the confirmatory contract’s own fail-closed support rule.

---

# 5. What closes C–G

I would slightly reorder the remaining obligations by cost and logical dependency.

## Step 0 — residual A/B reconciliation

Before applying the control:

- reconcile `+inf` versus finite/logical forbidden edges;
- add sparse-graph exhaustive A tests;
- freeze the exact eligibility-set construction rather than B’s undocumented two-pass pruning;
- narrow B’s claim to the observed development topology;
- record that B is a dependent development probe, not an independent or zero-compute proof.

No new source run is needed for this step.

---

## Step 1 — F: branch semantics first

Close the result logic synthetically before generating any treatment data.

Required witnesses:

```text
exposure-certified equivalence
    -> COUNTEREXAMPLE_TO_PERSISTENCE_NECESSITY

minimum-distance derangement materially worse
    -> MIN_DISTANCE_DERANGEMENT_WORSE
       source necessity remains unresolved

interval overlaps the equivalence and worse regions
    -> DERANGEMENT_CONTROL_UNRESOLVED

pre-treatment support failure
    -> support outcome, no mechanism result

post-start infeasibility
    -> control-not-total / topology abort

exposure failure
    -> invalid instrument
```

There must be no code path from “minimum-distance derangement materially worse” to:

```text
PERSISTENCE_NECESSARY_SOURCE
```

This preserves the one-sided scientific meaning already frozen in the amended design. fileciteturn100file0L22-L57

Closing F first prevents a development observation from acquiring an interpretation the comparator cannot support.

---

## Step 2 — C: same-support witness

On a captured development check, establish independently:

```text
covered duties after derangement
    == covered duties before derangement

assigned active-UAV count unchanged

noneligible incumbent pairs unchanged

energy/charging decisions unchanged

eligible ownership is the only changed assignment surface
```

Required paired negatives should include:

- allowing the derangement to select a previously uncovered duty;
- moving a noneligible incumbent;
- changing the number of covered duties;
- altering the charging decision.

A pure map-level witness may establish part of C, but the action/controller equality needs the real development environment.

---

## Step 3 — D: pre-action cadence witness

Establish:

1. lifecycle state is processed at the check boundary;
2. the incoming map is established;
3. the derangement is solved;
4. the first primitive action of the new interval is synthesized from the deranged map;
5. the map is carried until the next check unless lifecycle censoring intervenes.

The delayed R4 ordering is the mandatory paired negative:

```text
synthesize first action from old map,
then derange
```

and must fail the phase witness.

The corrected ordering is the same check clock but a newly registered R5 intervention; it is not a retroactive correction to R4. fileciteturn100file0L155-L177

---

## Step 4 — E: exact exposure and totality

For every uncensored eligible incumbent, establish all four conjuncts independently:

```text
map exposure:
    no incumbent duty retained

target exposure:
    target differs by > 1e-6

physical exposure:
    action sequence differs from constructive_mixed
    at least once within DELTA

lifetime exposure:
    assignment run length exactly one check
```

Also verify at **every subsequent check** that a legal full derangement exists under the state generated by the derangement itself. This is what converts B’s baseline feasibility into comparator totality.

Mandatory negatives:

1. one retained incumbent;
2. a different duty ID at the same geometric target;
3. post-action recomputation;
4. partial derangement;
5. one eligible incumbent;
6. a later check becoming infeasible after treatment begins.

The last negative should trigger topology-level control abort, not selective episode deletion.

---

## Step 5 — integrated proof-sized development exercise

After C–F each pass in isolation, run one integrated development-only trace showing:

- same-support preservation;
- pre-action application;
- exact exposure at every uncensored eligible check;
- one-check assignment lifetime;
- no silent fallback;
- correct handling of lifecycle censoring;
- post-start totality over the exercised horizon;
- raw witness serialization sufficient for an independent reader to recompute every guard.

This remains:

```text
DEVELOPMENT_NOT_A_RESULT
```

It emits no \(D_A\) population inference.

---

## Step 6 — G: fresh-population contract

Only then freeze:

- untouched topology seeds;
- the R5 population/stream namespace;
- episode volume;
- event-level feasibility;
- post-start topology-abort semantics;
- panel-level support;
- five-unit equivalence margin;
- CRN and hierarchical inference;
- no-pooling-with-R4 rule;
- one-sided result mapping;
- any expansion rule or an explicit no-expansion decision.

The topology panel must not be chosen until C–F close.

---

# 6. Retained portfolio

| Candidate | Status | What it can establish | Strongest limitation |
|---|---|---|---|
| Minimum-distance full derangement | **Selected development control** | Equivalence supplies a no-persistence counterexample | Inferiority is comparator-specific |
| External-\(G\)-oriented derangement | Live, stronger | Better approximation to \(V_{\neg P}^{*}\) | Harder to derive without outcome-dependent optimization |
| Portfolio of distinct no-persistence controls | Live | Reduces dependence on one heuristic | Still may not bound the full no-persistence policy class |
| Tenure/non-transferable-state source | Retained fallback | Structurally identifies persistence necessity | Changes the benchmark/source |
| Greedy recompute-every-check | Ordinary reduction only | Tests frequent replanning | Does not guarantee individual renewal |

---

# Final disposition

- **4a:** C–F development work is scientifically in scope; this review is not operational implementation or compute authorization.
- **4b:** both amendments stand. Canonicalization is a realization correction; Hall feasibility is the protected support rule. Reconcile the remaining `+inf` contradiction and sparse-graph proof coverage.
- **4c:** B passes the local development-topology liveness bar only. It does not establish fresh-panel support or totality under treatment.
- **Generality:** 1200/1200 must never be quoted as a source-wide probability or as evidence that the applied control will remain feasible.
- **Next sequence:** residual A/B closure → F → C → D → E → integrated development witness → G.
- **Scientific status:** `D7.3` and `D8` remain blocked.

No conclusion-bearing population is selected, and this response authorizes neither implementation nor compute.