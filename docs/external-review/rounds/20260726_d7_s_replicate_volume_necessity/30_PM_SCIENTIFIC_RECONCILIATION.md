# PM scientific reconciliation — 20260726_d7_s_replicate_volume_necessity

Source of record: `21_PRO_OPEN_RAW.md` (hash-verified, see
`50_MECHANICAL_INTAKE_RECORD.md`). Transport facts are not repeated here.

Disposition: **MODIFY THE REPLICATE VOLUME; ACCEPT SHARED-PREFIX FORKING; DO NOT
LAUNCH UNTIL THE REVISED DESIGN PASSES THE EIGHT-HOUR COST GATE.**

## What was asked and what was ruled

| Ask | Ruling |
|---|---|
| Q1(a) minimal `(n_select, n_eval)` | `n_select=2, n_eval=2`. `n_select=1` is **below the scientific floor** and rejected |
| Q1(b) shared-prefix realization | **Accepted**, with a complete-state cloning obligation and six Stage-B blocking conditions |
| Q1(c) frozen `4/8` indispensable | **No.** `4/8` is not the minimum admission requirement; retained only as a confirmatory route |
| Q1(c) predicate indispensable | **Yes.** Source-level heterogeneous renewal urgency is a prerequisite for the present thesis |
| Q1(d) downscope | **Not selected.** Part A + ep64 support only a restricted statement that removes the D7.3/D8 prerequisite |
| Q2 amend and refreeze in-round | **Confirmed.** No separate freeze round |

## The load-bearing argument, in one paragraph

`n_select=1` was rejected on a mechanism, not on power. The Section-8 bootstrap
resamples each candidate's selection stream and reruns the argmax inside every
bootstrap iteration; with a singleton selection array the resample always returns
the same observation, the candidate winner is fixed across all inner iterations,
and selection-uncertainty propagation becomes **algebraically inert**. That
changes the estimand — it would estimate the return of a one-draw selection
procedure rather than the frozen `max_z V(SET(z))`. The asymmetry matters: for
the stable limb, selecting a poor SET alternative makes SET look costly and
therefore **favors the claim that persistence is necessary**. A claim-favoring
failure mode cannot sit under a two-sided source-necessity gate. `n_select=2` is
the smallest volume at which the inner bootstrap is non-degenerate; `n_eval=2` is
the smallest at which the paired SET–KEEP evaluation resampling is non-degenerate.

## Contract amendments to apply (Q2 authorizes these directly)

Against `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md`:

1. **Section 8 constants** — `n_select = 2`, `n_eval = 2`, plus the interpretation
   note that these support only source-level materiality branches, never
   candidate-specific ranking or precision effect estimation.
2. **Selection diagnostic (new reporting requirement)** — the result artifact must
   report, per event: point-selected candidate; candidate selection frequency
   across bootstrap iterations; legal-set size; candidate-selection concentration
   or entropy. Candidate instability must widen or fail to resolve the gate, never
   be hidden by reporting only the point winner.
3. **Fixed-history realization** — replace "fresh prefix replay for every
   continuation" with one canonical evaluator-certified replay per qualifying
   event, materialized as an immutable complete-state snapshot; every continuation
   runs on an independently instantiated clone carrying its unchanged registered
   `stream_seed`.
4. **Cost status** — the contract is frozen at `2/2` but **non-executable** until a
   prelaunch wall-clock upper bound of at most eight hours exists at the
   registered sharding width.

Unchanged: topology seeds, episode counts, bootstrap procedure, thresholds,
branch semantics, the one-expansion rule, and `stream_seed` semantics.

## Stage-B conditions — blocking, and named by the ruling

Stage B is **mandatory** on the realization diff. Six conditions must be
established before launch:

1. **Clone equivalence** — a continuation from a clone is exactly numerically
   identical to one from the previous independent-replay route under the same
   continuation seed.
2. **Mutation isolation** — mutating one clone changes neither the immutable
   snapshot nor any other clone.
3. **RNG isolation** — clone construction consumes no registered continuation
   random numbers.
4. **Topology preservation** — every clone retains the same coordinate hash.
5. **Complete-state restoration** — step counter, users, routing/channel caches,
   energy latches, duty geometry and source-controller state all agree.
6. **Failure semantics** — failure of the canonical replay invalidates the whole
   event; a clone-equivalence or isolation failure emits
   `INVALID_EVENT_ALIGNED_AUDIT`.

The ruling explicitly warns that the existing prefix hash covers a **narrower**
surface (positions, battery, charging, station/queue, lifecycle mask, duty map)
than the snapshot must preserve, and is therefore not by itself proof that a
clone captures every hidden mutable field. The snapshot obligation lists env step
and episode counters, user/cluster pause and motion state, dock-request and
target-station state, cutoff/depletion and window-baseline masks, routing and
channel caches, environment RNG state, duty targets and service centroids,
lifecycle mask, source-controller schedule state, and topology hash.

## Cost gate — what the ruling actually permits

The eight-hour bound for `2/2` is **not** established by existing evidence. Moving
from `1/2` to `2/2` raises forks per event from `2(2+3|Z|)` to `2(2+4|Z|)`,
roughly **+27–31%** at observed legal-set sizes, against a `1/2` projection that
already landed near the six-to-eight-hour boundary.

The ruling permits **one microbenchmark of at most twenty minutes** to establish
the shared-prefix continuation rate. *(This corrects the restart handoff's
"zero-compute" summary, which was tighter than the ruling.)* The resulting
calculation must be an upper bound covering eight topology shards, calibration and
audit blocks, observed or conservatively bounded legal-set sizes, `n_select=2`,
`n_eval=2`, event search, continuation forks, and pooling and bootstrap overhead.

If that bound exceeds eight hours: emit `NON_EXECUTABLE_EVIDENCE_DESIGN`, do not
substitute `1/2`, do not reinterpret existing evidence, do not advance D7.3 or D8.
The cost check is explicitly **not** another scientific round and cannot
renegotiate `2/2`.

## Smallest refuted unit

Refuted: *the frozen `4/8`, replay-every-prefix realization is an executable
evidence design on the registered CPU under the eight-hour policy.*

Not refuted: the D7.S source predicate; event-aligned source auditing;
hierarchical topology inference; the R30 variable-lifetime line.

## Portfolio effect

| Route | Status |
|---|---|
| A. `2/2` + shared-prefix snapshot | **Selected minimum** |
| B. Original `4/8` on stronger compute | Retained confirmatory route |
| C. Existing-evidence stable-only claim | Parked — reactivation requires a user-level thesis change |
| D. Retire the Scenario-7 source predicate | Not supported |

Route C is explicitly **not** a PM-available shortcut: adopting it would require
user-level thesis revision, not an evidence-cost convenience decision.

## Execution order this ruling sets

1. Refreeze the contract with the four amendments above (this round, no new round).
2. Implement the shared-prefix realization in
   `scripts/audit_d7_s_event_aligned.py`; PM diff-read and focused tests.
3. Stage B on the realization diff — mandatory, six conditions.
4. Produce the prelaunch cost upper bound (≤20 min microbenchmark permitted).
5. Launch only if that bound is ≤8 h; otherwise `NON_EXECUTABLE_EVIDENCE_DESIGN`.

## PM inference — marked as inference, not result

The following are this conversation's engineering reads and carry no scientific
authority:

- *(inference)* Condition 1 (clone equivalence) is the expensive one to satisfy,
  because it requires keeping the old replay path executable as a reference
  oracle at least for the conformance test. Deleting the replay-every-prefix path
  in the same diff would remove the only means of proving equivalence.
- *(inference)* The snapshot obligation is broader than a naive `copy.deepcopy`
  guarantee only if the environment holds references to module-level or cached
  state; the enumerated field list is the actionable checklist and should be
  turned into an explicit assertion set rather than trusted to deep-copy
  semantics.
- *(inference)* The +27–31% fork increase applies to continuation forks only.
  Prefix replay collapses from once-per-replicate to once-per-event under (b),
  so the net change against the *measured* `1/2` projection is expected to be
  dominated by the shared-prefix saving rather than the volume increase. This is
  an expectation, not a bound, and does not substitute for step 4.
