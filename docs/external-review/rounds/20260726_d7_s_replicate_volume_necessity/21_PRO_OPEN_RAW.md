# Scientific ruling — D7.S replicate-volume necessity

**Stage reviewed:** `d0b89815563b9e5d907f4a446df8d4a8211c420f`

## Overall disposition

**MODIFY THE REPLICATE VOLUME; ACCEPT SHARED-PREFIX FORKING; DO NOT LAUNCH UNTIL THE REVISED DESIGN PASSES THE EIGHT-HOUR COST GATE.**

My rulings are:

1. **Reject `n_select=1, n_eval=2` for the frozen max-over-\(z\) inference.**
2. **Freeze the scientific minimum at `n_select=2, n_eval=2`.**
3. **Accept one canonical prefix replay followed by independent full-state continuation forks.**
4. The original `4/8` volume is **not** scientifically indispensable. The source-necessity predicate itself **is** indispensable to the current paper thesis.
5. The supplied cost evidence does not yet establish that the minimally valid `2/2` realization fits the eight-hour cap. Therefore:
   - if a post-diff cost bound establishes `≤8 h`, the audit may proceed under the amended contract;
   - otherwise it remains `NON_EXECUTABLE_EVIDENCE_DESIGN` and waits for different compute or a user-named exception.
6. Do **not** downscope the scientific claim on the basis of the existing Part-A and single-topology evidence.
7. The contract amendments are ruled in this round and may refreeze directly. No further scientific freeze round is required.

The previous run was correctly stopped: the hard policy requires a prelaunch upper bound, classifies an over-cap design as non-executable rather than scientifically negative, and directs the Project Manager to seek the cheapest bounded realization that preserves the predicate. fileciteturn273file0L22-L53

---

# Q1(a) — Minimal replicate volume

## Ruling: `n_select = 2`, `n_eval = 2`

The frozen `4/8` values were not derived as a minimum required by the estimand. They were a realization choice inside an eight-topology, sixteen-episode-per-topology design. fileciteturn272file0L18-L33 They may therefore be reduced if the reduction preserves:

- independent selection and evaluation;
- uncertainty from candidate selection;
- paired SET-versus-KEEP evaluation;
- and the topology-population gate.

## Why `n_select=1` is below the scientific floor

The current Section-8 bootstrap explicitly resamples every candidate’s selection stream and **reruns the argmax inside every bootstrap iteration**. With a singleton selection array, resampling always returns the same observation. The candidate winner is then fixed across all inner bootstrap iterations, so the required selection-uncertainty propagation becomes algebraically inert. fileciteturn288file0L102-L170

That is not merely a power reduction. It changes what is being inferred.

With one selection draw per candidate, the independent evaluation estimates the return of a **one-draw candidate-selection procedure**, not the frozen quantity

\[
\max_{z\in\mathcal Z(h)} V(\mathrm{SET}(z)).
\]

This distinction is especially dangerous for the stable limb:

- selecting the wrong, poor SET alternative can make SET look more costly;
- that error favors a false conclusion that persistence is necessary;
- independent evaluation removes winner’s-curse optimism, but it does not repair failure to select the true best legal alternative.

For the flex limb, poor selection mostly reduces power. For the stable limb, it can be claim-favoring. Therefore `n_select=1` cannot carry the two-sided source-necessity gate.

## Why `n_select=2` is the minimum

At two selection streams per candidate:

- the inner bootstrap is non-degenerate;
- the selected candidate can vary across resamples;
- candidate-selection uncertainty reaches the topology-level \(T_m\) distribution;
- selection remains disjoint from evaluation.

Two is not precision-grade candidate optimization. It is the smallest admissible finite-sample realization of the already accepted split-selection procedure.

Its interpretation must therefore remain narrow:

> The audit tests a material source margin under a minimally replicated empirical maximization over the complete legal alternative set; it does not estimate a precise oracle value or establish a stable ranking among individual alternatives.

The result artifact must report:

- point-level selected \(z\) for each event;
- bootstrap selection frequencies for every legal \(z\);
- number of legal alternatives;
- and candidate-selection concentration or entropy as a diagnostic.

Candidate instability widens or prevents the gate from resolving. It does not invalidate a correctly propagated interval and must not be hidden by reporting only the point winner.

## Why `n_eval=2` is the minimum

With one evaluation pair, the paired SET–KEEP evaluation resampling is itself degenerate. Two independent paired continuation streams are the smallest volume that permits:

- a nontrivial paired empirical difference;
- inner resampling of evaluation noise;
- and independent evaluation after selection.

The primary independent units remain topologies and qualifying episodes. The two continuation pairs are not being treated as two independent source histories.

## What `2/2` may and may not support

If the complete hierarchical bounds clear, `2/2` can support the frozen source-level branch because:

- every legal candidate is still represented;
- maximization is still selection/evaluation split;
- the maximizing candidate is rerun inside the bootstrap;
- SET and KEEP remain CRN-paired;
- and topology is still the top-level population unit.

It cannot support:

- candidate-specific superiority;
- a reliable ordering of alternative duties;
- a precise effect-size estimate;
- or a claim that two continuation samples are generally sufficient outside this bounded source gate.

A wider interval is the correct consequence. A branch that remains unresolved remains unresolved; no tuning rescue follows.

---

# Q1(b) — Shared-prefix realization

## Ruling: accepted, with a complete-state cloning obligation

A single evaluator-certified prefix replay followed by independent continuation forks preserves the scientific predicate.

The pre-intervention history is intentionally common to all arms. Rewalking it separately is not part of the estimand; it is an expensive implementation method for obtaining the same state. The current implementation recreates a fresh environment and replays the entire prefix inside every KEEP, selection and evaluation replicate. fileciteturn287file0L5-L18 fileciteturn287file0L25-L54

Deduplicating that identical work does not reduce replication of the conclusion-bearing continuation randomness.

## Exact semantic contract

For each qualifying episode/event:

1. Perform one canonical prefix replay from reset.
2. Verify the prefix against the evaluator-certified event history.
3. Take one immutable post-replay snapshot before setting any continuation-specific RNG stream.
4. For every limb, candidate, phase and replicate:
   - instantiate an independent clone from that immutable snapshot;
   - assign the unchanged registered `stream_seed`;
   - execute only that continuation;
   - discard the clone after use.
5. Never run multiple continuations sequentially on one mutated clone.

The same canonical event snapshot may serve both stable and flex limbs because they begin at the same registered joint event. Their focal intervention, locked-duty set and horizon remain limb-specific.

## What the snapshot must contain

A clone must preserve all source state capable of changing the continuation, including at least:

- environment step and episode counters;
- UAV and user positions;
- user/cluster pause and motion state;
- battery, charging, dock-request, target-station, queue and occupancy state;
- cutoff/depletion and window-baseline masks;
- routing, connection and channel state and any reusable caches;
- environment RNG state;
- duty map, duty targets and service centroids;
- lifecycle/service mask;
- the source-controller schedule state;
- topology coordinates and hash.

The current prefix hash intentionally covers a narrower fixed-history surface—positions, battery, charging, station/queue state, lifecycle mask and duty map. fileciteturn283file0L59-L80 That remains a useful scientific assertion, but it is not by itself proof that an object clone includes every hidden mutable field.

## Stage-B requirements for the realization diff

Before launch, the code-science alignment check must establish:

1. **Clone equivalence:** one continuation from a clone is byte- or exact-numerically identical to one continuation obtained by the previous independent replay route under the same continuation seed.
2. **Mutation isolation:** mutating one clone changes neither the immutable source snapshot nor another clone.
3. **RNG isolation:** clone construction consumes no registered continuation random numbers.
4. **Topology preservation:** every clone retains the same coordinate hash.
5. **Complete-state restoration:** current step, users, routing/channel caches, energy latches, duty geometry and source-controller state agree.
6. **Failure semantics:** failure of the one canonical replay invalidates the whole event; a clone-equivalence or isolation failure emits `INVALID_EVENT_ALIGNED_AUDIT`.

The current contract’s requirement is equality of the history before forking, not repeated physical replay as an end in itself. fileciteturn270file0L230-L235

Thus shared-prefix realization is an implementation optimization with a conformance obligation, not a new scientific design.

---

# Cost consequence of the `2/2` floor

The supplied cost model establishes that shared-prefix plus `1/2` is expected to land near the six-to-eight-hour boundary. fileciteturn269file0L24-L42 Moving from `1/2` to `2/2` increases continuation forks from

\[
2(2+3|\mathcal Z|)
\]

to

\[
2(2+4|\mathcal Z|),
\]

an increase of roughly 27–31% for the observed legal-set sizes.

Therefore, on the evidence currently available:

> **The eight-hour upper bound for `2/2` has not been established.**

The contract may refreeze scientifically at `2/2`, but the conclusion-bearing audit may not launch merely because the scientific volume is now defined.

Before launch, the Project Manager must apply the existing cost policy to the shared-prefix realization. A single policy-permitted microbenchmark of at most twenty minutes may establish the shared-prefix continuation rate. The resulting calculation must be an upper bound for:

- eight topology shards;
- calibration and audit blocks;
- observed or conservatively bounded legal-set sizes;
- `n_select=2`, `n_eval=2`;
- event search;
- continuation forks;
- pooling and bootstrap overhead.

If that bound is above eight hours, the result is:

```text
NON_EXECUTABLE_EVIDENCE_DESIGN
```

and no audit starts.

This cost check is not another scientific review round and cannot renegotiate `2/2`.

---

# Q1(c) versus Q1(d)

## The frozen `4/8` volume is not indispensable

I do **not** rule that `4/8` itself is scientifically necessary. The scientifically necessary minimum is `2/2`.

A future `4/8` audit remains a useful confirmatory realization if:

- the minimal audit is boundary-adjacent;
- candidate selection is highly unstable;
- or stronger compute becomes available.

It is not the minimum admission requirement.

## The source-necessity predicate is indispensable

If `2/2` plus shared-prefix cannot satisfy the hard cap, the correct consequence is operationally the one described in branch (c):

- the joint audit does not run on this machine;
- it waits for a user-named exception, different compute, or a newly demonstrated bounded realization that preserves the same predicate;
- D7.3 and D8 remain blocked.

This is not because the original replicate constants are sacred. It is because source-level heterogeneous renewal urgency is a prerequisite for the present thesis. `RESEARCH_GOAL.md` places both source heterogeneity and the learned low-cardinality renewal advantage on the critical path. fileciteturn275file0L164-L176

## Downscope is not selected

Part A plus the existing single-topology diagnostic can support only a restricted statement:

> Role exchange is structurally non-free in the Scenario-7 dynamics, and one previously tested fixed exchange protocol was costly on one pinned topology.

They do not establish:

- material flexible renewal;
- the max-over-legal-SET stable margin;
- event-aligned one-\(\Delta\) effects;
- or a topology-population source claim.

Downscoping to that statement would remove the source prerequisite needed to justify D7.3 and D8, while leaving the paper’s advertised heterogeneous-urgency thesis unchanged. That is not a valid shortcut.

A stable-persistence-only paper is a possible separate project direction, but adopting it would require explicit user-level thesis revision rather than an evidence-cost convenience decision.

---

# Q2 — Contract amendment and refreeze

## Ruling: amend and refreeze in this round

No separate freeze round is required.

The frozen contract should be superseded with these changes:

### Section 8 constants

```text
n_select = 2
n_eval   = 2
```

Add:

> `n_select=2` is the minimum non-degenerate selection-bootstrap volume; `n_eval=2` is the minimum non-degenerate paired-evaluation volume. These constants support only the source-level materiality branches, not candidate-specific ranking or precision effect estimation.

### Selection diagnostic

Require the result artifact to report:

- each event’s point-selected candidate;
- candidate selection frequency across bootstrap iterations;
- legal-set size;
- and candidate-selection concentration.

### Fixed-history realization

Replace “fresh prefix replay for every continuation” with:

> One canonical evaluator-certified prefix replay per qualifying event may be materialized as an immutable complete-state snapshot. Every continuation is executed on an independently instantiated clone receiving its unchanged registered continuation stream. Clone equivalence, mutation isolation, RNG isolation and full-state restoration are Stage-B blocking conditions.

### Cost status

Add:

> The scientific contract is frozen at `2/2`, but remains non-executable until the shared-prefix realization has a prelaunch wall-clock upper bound of at most eight hours at the registered sharding width.

The topology seeds, episode counts, bootstrap, thresholds, branch semantics and one-expansion rule remain unchanged.

The contract’s original `4/8` design and branch system are explicitly recorded in the repository. fileciteturn270file0L212-L228 fileciteturn271file0L18-L36 The amendment changes evidence resolution and realization cost, not the scientific proposition.

---

# Retained portfolio

| Route | Status | What would raise or lower it |
|---|---|---|
| **A. `2/2` + shared-prefix snapshot** | **Selected minimum** | Raise if Stage B proves clone equivalence and the cost bound is ≤8 h; lower if either fails |
| **B. Original `4/8` on stronger compute** | Retained confirmatory route | Reactivate for boundary-adjacent `2/2`, unstable candidate selection, or user-provided compute |
| **C. Existing-evidence stable-only claim** | Parked, not selected | Reactivate only if the user changes the paper thesis away from heterogeneous renewal urgency |
| **D. Retire this Scenario-7 source predicate** | Not supported | Reactivate only after an identified negative or proof that no bounded valid audit can distinguish its source classes |

## Smallest refuted unit

The current cost result refutes:

> The frozen `4/8`, replay-every-prefix realization is an executable evidence design on the registered CPU under the user’s eight-hour policy.

It does not refute:

- the D7.S source predicate;
- event-aligned source auditing;
- hierarchical topology inference;
- or the R30 variable-lifetime research line.

## Scheduled next boundary

The next boundary is:

1. refreeze at `2/2` with shared-prefix semantics;
2. perform the Stage-B realization-conformance check;
3. produce the policy-required prelaunch cost upper bound;
4. launch only if that bound is at most eight hours.

If the bound exceeds eight hours, stop with `NON_EXECUTABLE_EVIDENCE_DESIGN`; do not substitute `1/2`, do not reinterpret the existing evidence, and do not advance D7.3 or D8.

**This review amends the scientific contract. It does not itself authorize implementation or compute.**