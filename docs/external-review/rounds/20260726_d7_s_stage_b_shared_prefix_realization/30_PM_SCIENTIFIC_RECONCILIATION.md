# PM scientific reconciliation — Stage B, shared-prefix realization

Source of record: `21_PRO_OPEN_RAW.md` (hash-verified, see
`50_MECHANICAL_INTAKE_RECORD.md`).

Verdict: **MISMATCH.** The shared-prefix architecture is retained as the correct
direction; the realization does not instantiate the frozen R2 contract. **The
audit does not launch.**

## The defect the Project Manager did not find

I found that the prefix replay was nondeterministic and concluded that
shared-prefix cloning fixed it, because all arms of an event now fork from one
snapshot. That is true and insufficient, and Pro named the gap precisely:

> The event is certified in one user world, but `materialize_event_snapshot()`
> reconstructs the "canonical" snapshot through a fresh environment whose user
> and cluster state can belong to a different world.

The realized sequence is *certify the event in world W1 → replay the recorded
actions in world W2 → accept because the narrow hash agrees*. Cloning makes all
arms share **W2**, while the focal identities, legal targets, duty map and
service centroids were certified in **W1**. That is a hybrid continuation, and
because those quantities feed `G`, source-control behaviour and possibly
candidate ordering, it is conclusion-bearing.

My error was scoping: I fixed *arm-to-arm* comparability and treated the
snapshot's provenance as already sound, when the snapshot is itself a
reconstruction through the very mechanism I had just shown to be nondeterministic.

## Where my tests let it through

Also correctly identified:

- the condition-1 test monkeypatches `replay_prefix` with a deterministic fake,
  so it proves clone-equals-replay **only when the reference is artificially
  deterministic**;
- conditions 2 and 5 reuse the narrow hash, mutating UAV position and battery
  and checking those same fields, never user, cluster, connection, SINR or
  routing state.

Hence 146 passing tests closed nothing here: *the tests and the implementation
share the same incomplete definition of state.* Test count is not coverage of a
definition.

## Two further mismatches, found by Pro reading the code

Independent of the replay defect, and both claim-bearing:

**A. `full_sync_SET` cadence.** The contract defines it as reassigning every
duty *at each check*; the implementation recomputes the full duty map on every
`step_once` call. It determines the Part-A contrast `D_A`, so cadence can change
whether `PART_A_CONTRADICTION` fires. Must operate only at shared check
boundaries, every `Δ = 10` primitive steps.

**B. Stable limb freezes a non-focal flexible duty.** The event builder locks the
flex focal's incumbent duty and supplies it as the *stable* limb's
`locked_duties`. The contract says non-focal duties are never frozen. This
restricts the stable SET joint continuation relative to the registered
maximization and **makes SET look artificially costly — claim-favouring for
stable persistence**, the same asymmetry that disqualified `n_select=1`.

## Rulings to implement

| Ask | Ruling |
|---|---|
| Q2(a) condition 1 | **(iii)** — direct live-event capture; revised condition 1 becomes 1A/1B/1C; complete-state fingerprint; cross-limb equivalence must be demonstrated |
| Q2(b) comparability | **(iii) strengthened** — topology identity unchanged (BS + station geometry); add a registered `user_world_seed`, an episode-world fingerprint and an event-history fingerprint. Doing nothing is not acceptable |
| Q2(c) ep64 | **(ii)** — retire its paired contrasts as causal evidence now; audit-on-reuse for the wider repository |
| Q3 launch | **No, not as implemented.** Cost is explicitly *not* the blocker; ~4.3 h is acceptable scheduling information |

### Correct fixed-history realization

Roll the one real evaluator environment to `t_e`; certify both limbs on that live
environment; **before** installing any continuation RNG, capture the immutable
snapshot **directly from that live environment**, together with duty map, duty
positions, service centroids, lifecycle state, event record and legal candidate
sets; fork every continuation from it. **Do not reconstruct the event through a
second fresh-environment prefix replay.** `replay_prefix` stops being the
conclusion-bearing oracle and survives only as a historical diagnostic.

### Revised condition 1

- **1A same snapshot, same stream** — two clones with the same `stream_seed` and
  arm semantics produce identical `G` component series, total `G`, duty-map
  evolution, lifecycle transitions and trajectory.
- **1B stream isolation** — two clones with different streams have identical
  non-RNG state before stream installation, differ afterwards only in registered
  RNG state, and any later divergence is causally downstream. They are *not*
  required to produce unequal trajectories.
- **1C event identity** — the snapshot's full-state fingerprint equals the
  fingerprint recorded at certification. No replay approximation between them.

### Complete-state fingerprint

Must cover every continuation-sensitive surface, at minimum: step/episode
counters; UAV positions and velocities; user positions and velocities; cluster
assignments, centres, velocities, waypoints, pause timers; user waypoints and
pause timers; battery, charging, station, queue, docking; cutoff/depletion and
event-latch state; connection matrices, SINR, routing paths and reusable channel
caches; handover/service-set state; environment RNG state; duty map, targets,
service centroids; lifecycle mask; source-controller scheduling state; topology
coordinates and hash. The narrow hash may remain as a quick subset assertion but
cannot carry fixed-history validity.

### Episode-world provenance

A `user_world_seed` derived from existing episode provenance under a **disjoint
namespace**, controlling initial user positions, cluster assignments and centres,
waypoints and initial motion/pause state — separate from topology, energy and
continuation seeds. The distribution is unchanged; it merely becomes
reproducible. Plus an episode-world fingerprint after initialization and an
event-history fingerprint at `t_e`. The hierarchical bootstrap is unchanged:
topology stays the top-level unit and user worlds enter through within-topology
episode variation.

## ep64 — my inference was overridden, correctly

I had established from the estimator that `bootstrap_mean_ci` resamples observed
per-episode differences, so the intervals absorb the unpaired variance rather
than understating it, and I inferred the readings survive as underpowered. I
marked it inference; Pro ruled otherwise and its reasoning is the stronger one:
an honest interval around a **cross-world difference is still not a matched
causal contrast**, and because the construction-time worlds were never recorded,
nothing can reconstruct the pairing afterwards. Estimator validity was the wrong
question.

Retired as causal evidence: paired `B_H`, paired `set_stable − keep_stable`,
paired `set_flex − keep_flex`, the bootstrap intervals around them, and any
causal reading of the normalized margins. Explicitly **no unpaired reanalysis** —
the user-world samples and provenance were not recorded.

Surviving as a historical implementation record only: that the superseded
instrument ran, that energy and charging dynamics were active, the runtime and
fork-cost evidence, and raw per-arm outputs under their separately realized
worlds — descriptive, never matched causal estimates.

Part A's structural finding is unaffected: it rests on transition-state
structure, not on ep64's paired returns.

## Smallest refuted units

1. Fresh Scenario-7 construction plus `reset(seed=S)` reconstructs the same user world.
2. The narrow state hash establishes fixed pre-intervention history.
3. Independent replay is a valid reference oracle for clone equivalence.
4. The ep64 arm-level paired contrasts are valid causal comparisons.
5. The implemented every-step `full_sync_SET` realizes the registered every-check control.

Retained: shared-prefix cloning as the correct family; `copy.deepcopy` as a
plausible, inexpensive snapshot mechanism (its *conformance criterion* failed,
not cloning); `n_select=2, n_eval=2`; the eight topology seeds and the
hierarchical inference; D7.S source necessity live; Part A live; no update to
R30, D7.3 or D8.

## Execution order this ruling sets

Pro's scheduled next action is the **minimal corrected Stage-B realization
closure, not another scientific audit**:

1. supersede R2 with the fixed-history amendment (R2 §12 is stale — it still
   declares the eight-hour bound a launch condition);
2. correct the conclusion-bearing code path to direct live-event snapshot with
   the full fingerprint;
3. correct the `full_sync_SET` cadence and the stable-limb lock;
4. update the focused suite and the real-environment conformance check, ending
   the monkeypatched deterministic oracle;
5. rescope the ep64 record in the active ledger.

Then D7.S becomes eligible for the project's separate conclusion-bearing compute
authorization. This ruling supplies neither implementation nor compute authority.

## PM note — marked as inference

*(inference)* Item 3's stable-limb lock and item A's cadence are both cheap to
fix and both change a registered contrast, which makes them the highest-value
items per unit of work in this list. *(inference)* The full-state fingerprint is
the expensive item, because "every continuation-sensitive surface" is an open
set on this environment; the defensible construction is a canonical recursive
digest over the env's own attribute set with an explicit, reviewed exclusion
list, so that a newly added mutable field is included by default rather than
missed by default. That inverts the failure mode that produced this round.
