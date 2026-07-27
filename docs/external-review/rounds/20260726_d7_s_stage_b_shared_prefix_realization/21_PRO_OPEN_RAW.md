# Scientific ruling — D7.S Stage B shared-prefix realization

**Stage reviewed:** `4d4a623f250decd9376afbb0b3f16e74aee813ee`

## Overall verdict

# **MISMATCH**

The shared-prefix architecture is the correct direction and should be retained. The current realization does **not**, however, instantiate the frozen R2 fixed-history contract.

The decisive problem is stronger than the failed clone-versus-replay test:

> The event is certified in one user world, but `materialize_event_snapshot()` reconstructs the “canonical” snapshot through a fresh environment whose user and cluster state can belong to a different world. The narrow state hash then certifies only the subset that happened to remain equal.

The disclosed measurements establish that fresh environments using the same reset seed differ by kilometres in user positions and that independent prefix replays differ in user, cluster, SINR, connection and other state. The hash omits precisely those fields. fileciteturn293file0L21-L46

Accordingly:

- the prior replay-every-replicate route was invalid;
- shared-prefix cloning fixes arm-to-arm comparability **after** the snapshot has been created;
- but the present code does not establish that the snapshot is the evaluator-certified history;
- and the current condition-2/condition-5 tests do not establish complete-state isolation or restoration because they reuse the same incomplete hash.

The audit must not launch as implemented.

---

# Q1 — Stage B questions

## 1. Does the code instantiate the frozen R2 contract?

**No — `MISMATCH`.**

The frozen contract requires:

1. a canonical prefix state verified against the evaluator-certified history;
2. a snapshot containing all state capable of affecting the continuation, including user and cluster motion state, channel/routing state, caches and RNG;
3. complete-state restoration and clone isolation. fileciteturn292file0L61-L124

The code instead does the following:

- `materialize_event_snapshot()` calls `replay_prefix()`;
- `replay_prefix()` creates a fresh Scenario-7 environment;
- the environment’s construction-time user population can differ from the one in which the event was certified;
- verification uses `compute_state_hash()`, which contains UAV position, battery, charging, station state, lifecycle mask and duty map, but no user, cluster, channel or routing state. fileciteturn302file0L20-L37 fileciteturn302file0L73-L150

Thus the realized sequence is:

\[
\text{certify event in world }W_1
\longrightarrow
\text{replay actions in world }W_2
\longrightarrow
\text{accept because }h_{\mathrm{narrow}}(W_1)=h_{\mathrm{narrow}}(W_2).
\]

That does not instantiate “the same pre-intervention history.”

It can additionally create a hybrid continuation:

- focal identities, legal targets, duty map and service centroids come from \(W_1\);
- environment users, clusters and channels come from \(W_2\).

Because those quantities affect \(G\), source-control behavior and possibly candidate ordering, this is conclusion-bearing.

---

## 2. Could a test pass through the wrong mechanism?

**Yes.**

The focused condition-1 test replaces `replay_prefix()` with a deterministic fake environment. It therefore proves that clone and replay agree **when the reference replay is artificially deterministic**, not that the real Scenario-7 reference is valid. fileciteturn304file0L220-L248

The condition-2 and condition-5 checks similarly reuse the narrow state hash. They mutate UAV position and battery and verify those fields, but do not test:

- user positions;
- user velocities and waypoints;
- cluster assignments, centres, velocities, waypoints and pause state;
- connection, SINR and routing state;
- relevant counters and caches;
- or other continuation-sensitive fields named by the contract. fileciteturn304file0L150-L216

The real-environment conformance script consequently reports conditions 2–5 as passing while the measured independent replays differ on 24 attributes. fileciteturn294file0L142-L172 fileciteturn293file0L26-L46

A high test count therefore does not close this defect: the tests and implementation share the same incomplete definition of state.

---

## 3. Could an alternate implementation explanation change the registered conclusion?

**Yes.**

Two implementations currently described as realizations of the same contract can evaluate different quantities:

### Realization A — current code

Certify the event in one environment, reconstruct a fresh environment, verify a partial hash, and fork from the reconstructed world.

### Realization B — semantically correct realization

Capture the actual live evaluator environment at the moment the event is certified and fork all continuations from that exact state.

These can produce different:

- legal SET alternatives;
- maximizing candidate;
- stable-target displacement;
- user service and routing state;
- \(B_m\);
- \(U^\*_{m,\mathrm{src}}\);
- \(T_m\);
- and final result branch.

That is not an engineering-only equivalence question.

---

## Two additional Stage B mismatches

These are independent of the disclosed replay defect and must also be corrected before launch.

### A. `full_sync_SET` runs every primitive step, not every check

The contract defines `full_sync_SET` as reassigning every duty at each check. fileciteturn291file0L148-L155

The implementation recomputes the complete duty map whenever `step_once()` is called, explicitly “every step.” fileciteturn321file0L1-L20

Because `full_sync_SET` determines the Part-A equivalence contrast \(D_A\), changing its cadence can change whether `PART_A_CONTRADICTION` fires.

It must operate only at the registered shared check boundaries, every \(\Delta=10\) primitive steps.

### B. The stable limb freezes a non-focal flexible duty

The contract states that non-focal duties are not frozen and are reoptimized under `constructive_mixed`. fileciteturn291file0L68-L72

The event builder constructs a lock for the flex focal’s incumbent duty and supplies it as the `stable` limb’s `locked_duties`; the continuation then applies that lock during the focal stable intervention. fileciteturn299file0L233-L251 fileciteturn300file0L109-L134

This restricts the stable SET joint continuation relative to the registered maximization and can make SET look artificially costly—a claim-favouring error for stable persistence.

For the flex limb, preserving a genuinely certified stable incumbent can follow `constructive_mixed` semantics. For the stable limb, the non-focal flexible duty may not be locked merely to preserve the paired-history narrative.

---

# Q2(a) — Replacement for condition 1

## Ruling: choose **(iii)** — direct event-state capture, incorporating the valid part of option (i)

Replacing the test with clone-versus-clone equality is necessary but not sufficient. The source snapshot itself must first be the history that was actually certified.

## Correct fixed-history realization

At the qualified event:

1. Roll the one real evaluator/source-control environment to \(t_e\).
2. Certify stable and flex on that live environment.
3. Before installing any continuation-specific RNG stream, capture an immutable snapshot **directly from that live environment**.
4. Store the auxiliary source-controller state with it:
   - duty map;
   - duty positions;
   - service centroids;
   - lifecycle state;
   - event record;
   - legal candidate sets.
5. Fork every calibration, KEEP, SET, selection and evaluation continuation from that snapshot.
6. Do not reconstruct the event through a second fresh-environment prefix replay.

The conclusion-bearing path should no longer use `replay_prefix()` as an oracle. It may remain as a historical diagnostic or as a future test of a separately repaired deterministic reconstruction route.

## Revised condition 1

Condition 1 becomes three assertions.

### 1A. Same snapshot, same stream

Two independent clones of the same event snapshot, assigned the same `stream_seed` and the same arm semantics, must produce exactly the same:

- primary-\(G\) component series;
- total \(G\);
- duty-map evolution;
- lifecycle transitions;
- and relevant physical trajectory.

### 1B. Stream isolation

Two clones assigned different continuation streams must:

- have identical non-RNG state immediately before stream installation;
- differ immediately afterward only in the registered RNG state;
- and have any later divergence causally downstream of that stream.

They need not be forced to produce unequal trajectories. A stochastic stream may be unused, or two draws may happen to yield the same behavior.

### 1C. Event identity

The snapshot’s full-state fingerprint must equal the fingerprint recorded at certification. There is no “replay approximation” between the two.

This replaces the unsatisfiable comparison to a nondeterministic independent route.

---

## Complete-state fingerprint

The existing narrow hash may remain as a quick subset assertion, but it cannot carry fixed-history validity.

The load-bearing event fingerprint must include, at minimum:

- primitive step and episode counters;
- UAV positions and actual velocities;
- user positions and velocities;
- user cluster assignments;
- cluster centres, velocities, waypoints and pause timers;
- user waypoints and pause timers;
- battery, charging, station, queue and docking state;
- cutoff/depletion and event-latch state;
- connection matrices, SINR state, routing paths and reusable channel/radio caches;
- handover and service-set state where it can affect the continuation;
- environment RNG state;
- duty map, duty targets and service centroids;
- lifecycle/service mask;
- source-controller scheduling state;
- topology coordinates and hash.

A canonical recursive digest or exact deep comparison can realize this; the scientific requirement is coverage of every continuation-sensitive state surface, not a particular serialization technique.

---

## Cross-limb equivalence

**Yes, it must be demonstrated.**

The contract states that one snapshot serves both limbs. The conformance evidence must show:

1. stable and flex obtain clones with the same complete event fingerprint;
2. neither limb adapter mutates the immutable source;
3. before the focal/lock/horizon-specific semantics are applied, their starting states are identical.

The strongest compact witness is a neutral, no-focal-intervention continuation through both limb call paths:

- same snapshot;
- same stream;
- same common horizon;
- no limb-specific locks or override.

It must produce identical state and \(G\) sequences. Actual stable and flex interventions are not expected to agree.

---

# Q2(b) — Is topology still the comparability unit?

## Ruling: choose **(iii), strengthened**

**Topology identity remains the ground-BS and charging-station geometry. The user world is a nested episode-level random factor, not part of topology identity.**

The frozen inference already treats topology as the upper unit and resamples episodes/events within topology. Pinning one user layout to each topology would collapse topology and episode variation and reduce the intended population to eight infrastructure-plus-user fixtures. fileciteturn291file0L227-L235 fileciteturn292file0L135-L167

The eight registered topology seeds therefore retain their identity and require no re-registration.

However, option (i)—doing nothing—is not acceptable. Construction-time OS entropy is not adequate evidence provenance.

## Required episode-world provenance

Each calibration or audit episode must have:

### A registered user-world seed

Derive a separate `user_world_seed` from the existing episode provenance under a disjoint namespace. That seed controls construction of:

- initial user positions;
- cluster assignments and centres;
- user/cluster waypoints;
- initial motion and pause state.

This is separate from:

- topology seed;
- energy-permutation seed;
- continuation stream seed.

The statistical distribution remains the registered random-user distribution; it merely becomes reproducible.

### An episode-world fingerprint

Record after environment initialization:

- initial user and cluster state;
- relevant initial motion state;
- the user-world seed;
- and a canonical fingerprint.

### An event-history fingerprint

At \(t_e\), record the complete fixed-history fingerprint defined above.

This permits verification that:

- all arms of one event share one world;
- different episodes remain legitimate independent episode draws;
- and an artifact can be reconstructed later.

The hierarchical bootstrap remains unchanged: topology is the top-level unit and user worlds contribute through within-topology episode variation.

---

# Q2(c) — Prior closed Scenario-7 results

## Ruling: choose **(ii)** for the named ep64 diagnostic; use audit-on-reuse for the wider repository

The ep64 single-topology artifact must be explicitly rescoped now because its arm differences are actively quoted in the portfolio.

The following readings are retired:

- its paired `constructive − null` \(B_H\);
- its paired `set_stable − keep_stable` contrast;
- its paired `set_flex − keep_flex` contrast;
- the paired bootstrap intervals around those quantities;
- any causal interpretation of the normalized margins.

The arms were not paired on one user history, and the unrecorded construction-time worlds cannot now be reconstructed. The apparent episode index pairing does not restore CRN pairing. fileciteturn290file0L123-L142 fileciteturn293file0L54-L65

## What survives from ep64

Preserve the artifact as a historical implementation record supporting only noncomparative facts such as:

- the superseded instrument ran;
- energy and charging dynamics were active;
- the measured runtime and fork-cost evidence;
- raw per-arm outputs under their separately realized worlds.

Even the raw arm means are descriptive, not matched causal estimates. No unpaired reanalysis should be performed because the user-world samples and their provenance were not recorded.

## Wider Scenario-7 history

Adopt the existing audit-on-reuse rule:

> Any prior result used again as a causal comparator or paper-level premise must establish that compared arms shared the complete episode world, not merely the same coordinate topology.

No repository-wide retrospective audit is required before D7.S. The corrected D7.S path does not rely on those historical arm contrasts.

Part A’s structural non-transferability argument is unaffected because it is based on transition-state structure rather than the ep64 paired returns.

---

# Q3 — Does D7.S launch?

## Ruling: **No, not as currently implemented**

The wall-clock projection is not the blocker. The current policy explicitly removes the formal-run cap: formal scientific runs may take longer than eight hours, while the cost projection is informational. The 20-minute limit remains only for smokes, probes and verification apparatus. fileciteturn314file0L23-L65

The measured projection of roughly 4.3 hours at eight-way sharding is therefore acceptable scheduling information.

## Blocking conditions before launch

### 1. Supersede R2 with the fixed-history amendment

The new immutable contract should record:

- direct capture of the live evaluator-certified event state;
- revised clone-to-clone condition 1;
- complete event-state fingerprint;
- cross-limb snapshot conformance;
- episode-world seed and fingerprint;
- topology identity unchanged;
- current cost policy: projection informational, no eight-hour launch gate.

The existing R2 section 12 is now stale because it still declares the eight-hour bound a launch condition. fileciteturn292file0L204-L235

This round supplies the scientific ruling; no separate open-design freeze round is needed. The repository should supersede rather than edit R2.

### 2. Correct the conclusion-bearing code path

The formal driver must:

- snapshot the live event environment directly;
- stop using fresh-environment `replay_prefix()` to materialize the event;
- use the full fingerprint for source integrity, clone restoration and mutation isolation;
- implement the revised same-seed/different-seed conformance;
- demonstrate the same snapshot across stable and flex.

### 3. Correct the two independent realization mismatches

- `full_sync_SET` must reassign at shared checks, not every primitive step;
- the stable limb must not freeze the non-focal flex duty contrary to the registered joint maximization.

### 4. Update tests and the real-environment conformance check

The focused suite must no longer prove condition 1 by monkeypatching a deterministic replay oracle.

It must contain:

- same-live-snapshot, same-stream equality;
- different-stream isolation;
- complete-state mutation detection, including a user/cluster field;
- cross-limb starting-state equality;
- a witness that `full_sync_SET` changes only at check boundaries;
- a witness that the stable limb does not impose the prohibited flex-duty lock.

This is code-science alignment, not another evidence experiment.

### 5. Rescope the ep64 record in the active ledger

The invalid paired contrasts must not remain active premises when the new D7.S result is interpreted.

---

## Launch boundary after repair

After those items close:

- the `2/2` scientific floor remains unchanged;
- topology seeds, episode counts, horizons, thresholds, bootstrap and `stream_seed` semantics remain unchanged;
- the cost projection is recorded but does not gate launch;
- the D7.S joint held-out-topology audit becomes eligible for the project’s separate conclusion-bearing compute authorization.

This response does not itself provide that authorization.

---

# Smallest scientific updates

## Refuted

1. **Fresh Scenario-7 construction plus `reset(seed=S)` reconstructs the same user world.**
2. **The existing narrow state hash establishes fixed pre-intervention history.**
3. **Independent replay is a valid reference oracle for clone equivalence.**
4. **The ep64 arm-level paired contrasts are valid causal comparisons.**
5. **The implemented every-step `full_sync_SET` realizes the registered every-check control.**

## Retained

1. Shared-prefix cloning is the correct realization family.
2. `copy.deepcopy` remains a plausible and inexpensive snapshot mechanism; what failed is its conformance criterion, not cloning itself.
3. `n_select=2`, `n_eval=2` remains the scientific minimum.
4. The eight topology seeds and hierarchical topology/episode inference remain appropriate.
5. D7.S source necessity remains live.
6. Part A’s structural finding remains live.
7. No evidence here updates R30, D7.3 or D8.

---

# Retained realization portfolio

| Route | Status | Strongest issue | Reactivation condition |
|---|---|---|---|
| **Direct live-event snapshot** | **Selected** | Complete-state coverage must be demonstrated | Full fingerprint, clone isolation and cross-limb conformance pass |
| **Fully deterministic whole-world replay** | Retained fallback | Requires explicit reconstruction of all construction-time user/cluster state | Reactivate only if direct snapshots prove technically unusable |
| **Fresh-env replay with narrow hash** | Retired | Certifies a different user world as the same history | None without complete world pinning and full-state verification |
| **Historical ep64 paired contrast** | Retired as causal evidence | Compared unrecorded, different user worlds | Cannot be recovered from existing artifact |

## Scheduled next action

The next action is the **minimal corrected Stage-B realization closure**, not another scientific audit:

1. supersede the contract under this ruling;
2. correct the direct-snapshot, full-state, cadence and lock semantics;
3. run focused code tests and the minimal real-environment conformance path;
4. record the informational cost projection;
5. then route the conclusion-bearing D7.S launch through its normal authority boundary.

**D7.3 and D8 remain blocked until D7.S produces `PERSISTENCE_NECESSARY_SOURCE`. This review authorizes neither implementation nor compute.**