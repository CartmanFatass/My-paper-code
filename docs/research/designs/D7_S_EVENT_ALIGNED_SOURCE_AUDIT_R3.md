# D7.S event-aligned source audit — frozen contract (R3, fixed-history amendment)

```text
id=D7.S
status=FROZEN_2026-07-26_R3
supersedes=D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md
authority=rounds/20260726_d7_s_stage_b_shared_prefix_realization/21_PRO_OPEN_RAW.md
verdict_that_forced_it=MISMATCH
amendment_scope=fixed_history_realization|condition_1|complete_state_fingerprint|cross_limb_conformance|episode_world_provenance|full_sync_cadence|stable_limb_lock|cost_status
unchanged=replicate_volume_2_2|topology_seeds|episode_counts|horizons|thresholds|bootstrap|stream_seed_semantics|branch_semantics|one_expansion_rule
wording_amendment_20260727=section_E_probability_model_only|no_new_freeze_round|rounds/20260727_d7_s_stage_b_crn_and_user_world/21_PRO_OPEN_RAW.md
```

**Carry-forward.** Every section of R2 not amended below remains binding
verbatim: the environment instance (§0), estimand (§1), event definition and
certification (§2), horizons (§3), controllers (§4), normalizers (§5), legal SET
alternatives (§6), primary `G` and its measurement (§7), the gate and
hierarchical bootstrap and Part-A conformance (§8 except as amended), topology
population and the one expansion (§9), and the ten result branches (§10). R2 is
superseded, not deleted, and is never edited.

**Why R3 exists.** R2's shared-prefix realization was correct in direction and
wrong in provenance. Stage B returned `MISMATCH`: the event is certified in one
world, and `materialize_event_snapshot()` rebuilt the "canonical" snapshot
through a fresh environment whose user and cluster population can belong to a
different world, accepted because a narrow UAV-only hash agreed. Cloning made
all arms share that second world consistently; it did not make it the certified
one. This contract removes the reconstruction step.

## A. Fixed-history realization — direct live-event capture

Replaces R2 §8's "one canonical evaluator-certified prefix replay materialized
as an immutable snapshot".

At the qualified event:

1. Roll the one real evaluator/source-control environment to `t_e`.
2. Certify stable and flex **on that live environment**.
3. **Before** installing any continuation-specific RNG stream, capture an
   immutable snapshot **directly from that live environment**.
4. Store the auxiliary source-controller state with it: duty map, duty
   positions, service centroids, lifecycle state, event record, legal candidate
   sets.
5. Fork every calibration, KEEP, SET, selection and evaluation continuation from
   that snapshot.
6. **Do not reconstruct the event through a second fresh-environment prefix
   replay.**

`replay_prefix` leaves the conclusion-bearing path. It is retained only as a
historical diagnostic, or as a future test of a separately repaired
deterministic reconstruction route.

## B. Condition 1 — replaced, not patched

R2's condition 1 compared a clone continuation to one from an independent
replay. The reference route is nondeterministic across constructions, so the
condition asked the correct mechanism to reproduce the broken one. It is
unsatisfiable and inverted, and is deleted along with any deterministic-oracle
test double that made it appear to pass.

- **1A — same snapshot, same stream.** Two independent clones of one event
  snapshot, given the same `stream_seed` and the same arm semantics, must
  produce exactly the same primary-`G` component series, total `G`, duty-map
  evolution, lifecycle transitions and physical trajectory.
- **1B — stream isolation.** Two clones given different continuation streams
  must have identical non-RNG state immediately before stream installation,
  differ immediately afterwards only in the registered RNG state, and have any
  later divergence causally downstream of that stream. They are **not** required
  to produce unequal trajectories: a stochastic stream may be unused, or two
  draws may coincide.
- **1C — event identity.** The snapshot's complete-state fingerprint must equal
  the fingerprint recorded at certification. There is no replay approximation
  between the two.

Conditions 2 (mutation isolation), 3 (RNG isolation), 4 (topology preservation),
5 (complete-state restoration) and 6 (failure semantics) carry forward from R2,
with 2 and 5 now evaluated against the complete fingerprint below rather than
the narrow hash.

## C. Complete-state fingerprint

**What this clause freezes, and what it does not.** Ruled 2026-07-27, Stage B
round `20260727_d7_s_stage_b_fingerprint_closure`, after two identically-seeded
`build_pinned_env` calls were measured to fingerprint differently. Three
statements, and no fourth:

| Claim | Status |
|---|---|
| **User-world reconstruction** from topology plus `user_world_seed` | supported |
| **Concrete event-state identity** via `full_state_fingerprint` | supported |
| **Complete seed-to-environment reconstruction** | **not supported** |

This clause freezes *identity of the concrete event state* — that certification,
the immutable source snapshot and every continuation clone refer to the same
concrete state, verified process-portably. It does **not** assert that
`build_pinned_env` is a seed-to-state reconstruction function. `reset()` derives
station-relative logistics before the registered coordinates are restored, so a
construction-dependent offset survives in `episode_graph_pbrs_sum`; it lies
outside primary `G` and cancels before treatment. The reorder that would remove
it is a **parked** environment correction and must not enter the frozen run.

The narrow state hash may remain as a quick subset assertion. **It cannot carry
fixed-history validity.** The load-bearing fingerprint must cover every
continuation-sensitive surface, at minimum:

primitive step and episode counters; UAV positions and actual velocities; user
positions and velocities; user cluster assignments; cluster centres, velocities,
waypoints and pause timers; user waypoints and pause timers; battery, charging,
station, queue and docking state; cutoff/depletion and event-latch state;
connection matrices, SINR state, routing paths and reusable channel/radio
caches; handover and service-set state where it can affect the continuation;
environment RNG state; duty map, duty targets and service centroids;
lifecycle/service mask; source-controller scheduling state; topology coordinates
and hash.

A canonical recursive digest or exact deep comparison may realize this. The
scientific requirement is **coverage**, not a serialization technique.

*Realization note, binding for this contract:* the digest includes every array
and numeric attribute **by default**, with a short reviewed exclusion list. The
defect being repaired was a guard over a hand-picked subset, so a field nobody
considered fell outside it. Include-by-default inverts that failure mode: a
newly added mutable field joins the fingerprint automatically, and each
exclusion must be argued for in writing.

## D. Cross-limb conformance

One snapshot serves both limbs, so the conformance evidence must demonstrate:

1. stable and flex obtain clones with the same complete event fingerprint;
2. neither limb adapter mutates the immutable source;
3. before focal/lock/horizon-specific semantics are applied, their starting
   states are identical.

The registered compact witness is a neutral, no-focal-intervention continuation
through both limb call paths — same snapshot, same stream, same common horizon,
no limb-specific locks or overrides — producing identical state and `G`
sequences. Actual stable and flex interventions are not expected to agree.

## E. Episode-world provenance

*Amendment (2026-07-27), ruled without a further freeze round:*
`docs/external-review/rounds/20260727_d7_s_stage_b_crn_and_user_world/21_PRO_OPEN_RAW.md`
(Q3(a)) corrected two sentences of this section, quoted verbatim below. The
causal estimand and the bootstrap hierarchy are unaffected; only the
probability-model wording changes, from "user worlds contribute through
within-topology episode variation" to a factorization that names the
topology-conditioned remote-cluster corner explicitly:
`T ~ P_T, W ~ P(W|T)`.

Topology identity is **unchanged**: it remains the ground-BS and
charging-station geometry. The user world is a nested **episode-level random
factor**, not part of topology identity — pinning one user layout per topology
would collapse topology and episode variation and reduce the intended
population to eight infrastructure-plus-user fixtures. The eight registered
topology seeds retain their identity and require no re-registration.

Doing nothing is **not** acceptable: construction-time OS entropy is not
adequate evidence provenance. Each calibration or audit episode must therefore
carry:

- **a registered `user_world_seed`**, derived from existing episode provenance
  under a **disjoint namespace**, controlling initial user positions, cluster
  assignments and centres, user/cluster waypoints, and initial motion and pause
  state. Separate from the topology seed, the energy-permutation seed and the
  continuation stream seed. The generator routines and continuous parameters
  are unchanged, and the draw becomes reproducible — but because the
  remote-cluster corner is a function of the pinned topology's BS quadrant
  rather than of construction-time OS entropy, the effective joint
  distribution and its topology/episode variance decomposition are not simply
  "the same distribution, now reproducible." Saying so would be too broad:
  see the corrected factorization below.
- **an episode-world fingerprint**, recorded after environment initialization:
  initial user and cluster state, relevant initial motion state, the
  `user_world_seed`, and a canonical fingerprint.
- **an event-history fingerprint** at `t_e`: the complete fixed-history
  fingerprint of section C.

This permits verifying that all arms of one event share one world, that
different episodes remain legitimate independent draws, and that an artifact can
be reconstructed later. The hierarchical bootstrap is unchanged: topology
remains the top-level unit. User worlds are **topology-conditioned episode
draws**: `T ~ P_T`, `W ~ P(W|T)` — topology-determined geometric factors (the
remote-cluster corner, fixed by the pinned BS quadrant) contribute at the
topology level, while residual user/cluster geometry, motion, waypoints and
pauses contribute through within-topology episode variation.

## F. Two independent realization corrections

**F1 — `full_sync_SET` cadence.** The control reassigns every duty **at each
shared check**, every `Δ = 10` primitive steps — never on every primitive step.
It supplies the Part-A contrast `D_A`, so its cadence can decide whether
`PART_A_CONTRADICTION` fires. Between checks the duty map is carried forward
unchanged.

**F2 — the stable limb locks nothing.** §1 states that non-focal duties are
never frozen; for every candidate `z` all other airborne assignments are
reoptimized one-to-one under `constructive_mixed`. The stable limb must not
receive the flex focal's incumbent duty as a lock: doing so restricts the stable
SET joint continuation relative to the registered maximization and makes SET
look artificially costly — a **claim-favouring** error for stable persistence.
The flex limb may keep the certified stable incumbent's duty, because preserving
an active stable incumbent between lifecycle events is `constructive_mixed`
semantics rather than an added constraint.

## G. Cost status — supersedes R2 §12 entirely

R2 §12 is stale. There is **no eight-hour launch gate**. The user removed the
formal wall-clock cap on 2026-07-26; formal scientific runs may take longer than
eight hours. The 20-minute cap remains for smokes, probes and verification
apparatus, and audit-stage proliferation and audit-driven verification
experiments remain forbidden (`EVIDENCE_COMPLEXITY_POLICY.md`).

The prelaunch cost projection remains **required and informational** — so the
run's cost is known and scheduled, not so it can be refused. The measured
projection of roughly 4.3 hours at eight-way sharding is acceptable scheduling
information.

## H. Launch boundary

After sections A–F close, the `2/2` scientific floor, topology seeds, episode
counts, horizons, thresholds, bootstrap and `stream_seed` semantics all remain
unchanged, and the joint held-out-topology audit becomes **eligible for the
project's separate conclusion-bearing compute authorization**.

This contract authorizes neither implementation nor compute.

## I. Retired by the ruling that produced this contract

Refuted smallest units:

1. Fresh Scenario-7 construction plus `reset(seed=S)` reconstructs the same user world.
2. The narrow state hash establishes fixed pre-intervention history.
3. Independent replay is a valid reference oracle for clone equivalence.
4. The ep64 arm-level paired contrasts are valid causal comparisons.
5. The implemented every-step `full_sync_SET` realizes the registered every-check control.

Retained: shared-prefix cloning as the correct realization family;
`copy.deepcopy` as a plausible, inexpensive snapshot mechanism — what failed was
its conformance criterion, not cloning; `n_select=2, n_eval=2`; the eight
topology seeds and the hierarchical topology/episode inference; D7.S source
necessity live; Part A's structural finding live; no update to R30, D7.3 or D8.
