# PM scientific reconciliation -- 20260730_d7_s_provenance_correction_result

Ruling: `21_PRO_OPEN_RAW.md`, 22115 chars, stage `b8652fd9`.
Transport facts: `50_MECHANICAL_INTAKE_RECORD.md`.

## The four decisions, as ruled

```text
5a  must cloud-cloud localization finish first   NO -- record the cause UNRESOLVED and proceed
5b  Route A or Route B                            ROUTE A, AMENDED. Route B parked as a
                                                  contract change, not a refactor
5c  may fresh evidence be designed now            YES for the design and the SELECTION RULE.
                                                  NO population may be selected, generated,
                                                  inspected or probed
5d  wire the manifest in now                      NO. Six blockers, then a manifest-SPECIFIC
                                                  development gate
```

`D7.3` and `D8` remain blocked. The ruling authorizes neither implementation nor
conclusion-bearing compute, while naming the next scientific action as *amend and
conformance-test the manifest-replay realization on development-only worlds*.
That is the same ambiguity `CURRENT_WORK.md` already records a Project Manager
reading for, and the reading is unchanged: the closing guard binds the **formal
measurement**, not the repair work the ruling itself schedules as Required.

## What I got wrong, verified in source before recording it

Both of my errors are **the same mistake**: I enumerated the *direct* writers of a
quantity and stopped, without following the calls those writers make. It cost the
step-2 finding and it is also blocker 3.

### 1. `_init_user_velocities` is not the final writer of `user_velocities`

`20260730_STEP2_USER_VELOCITIES_WRITERS.md` lists
`_initialize_user_waypoints_rpgm` as using only `np.linalg.norm` -> `sqrt`. That
row is **false**. Verified at `envs/pettingzoo/scenario_base.py:2512-2541`:

```text
_initialize_user_waypoints_rpgm
  -> _initialize_cluster_migration_rpgm   np.cos/np.sin at :2557-2558
  -> _generate_intra_cluster_waypoint     np.cos/np.sin at :2470
  -> _generate_inter_cluster_waypoint     np.cos/np.sin at :2498
  then OVERWRITES self.user_velocities[i, :2] from the waypoint direction at :2539
```

`regenerate_user_world` calls `_init_user_velocities` and *then*
`_initialize_user_waypoints_rpgm` (`:2269-2271`), so on the configured `rpgm`
path the fingerprinted velocity array is the one written at `:2539`, not the one
written at `:2292-2293`.

The direction of the finding survives -- the array that diverged is still written
through a trigonometric path -- but **the uniqueness claim is dead**, and with it
"scalar trig is the ONLY non-portable operation on this path". That was the claim
I explicitly asked to have attacked, and it did not survive.

### 2. Initial-manifest replay does NOT retire the trig path

Verified at `:2320-2370` and `:2372-2422`: during an episode
`_update_user_positions_rpgm` and `_update_cluster_centers_rpgm` call
`_generate_intra_cluster_waypoint`, `_generate_inter_cluster_waypoint` and
`_generate_new_cluster_target_rpgm` (`np.cos`/`np.sin` at `:2444-2445`) whenever a
user or a cluster centre reaches its waypoint.

So the sentence in my §5b -- *"Route A never re-executes the trig, so portability
stops mattering"* -- is **false for any horizon longer than zero steps**. R4 runs
139 or 550 steps after the event. This is the single most consequential
correction in the ruling: a repair that looked complete was covering only
`t = 0`.

### 3. The `user_cluster_assignments` divergence has no supported explanation

Verified at `:2478-2510`: on the configured path the assignment is written as an
integer, either as `cluster_idx` during generation or by an explicit
`np_random.choice(available_clusters)` at `:2507`. There is **no floating-point
nearest-centre classifier**, so "a float near-tie flipped it" was never available.

I record this as *unexplained*, which is stronger than it sounds. The 80/20
branch and the `choice` are pure RNG draws, and each branch consumes a fixed
number of them, so an aligned stream should produce an identical assignment.
One key differing therefore indicates a different RNG or control-flow state, an
unenumerated writer, or an episode-key alignment problem -- and it is direct
evidence the writer audit is incomplete. It is the loose thread, not a footnote.

## The six blockers, each reproduced by me rather than taken on report

All six are confirmed against `scripts/d7_s_world_manifest.py` at `b8652fd9`.

```text
B1  load_world_manifest checks ONLY schema_version (:218). contract_id,
    topology_seed, block and episode_index come from the PATH, and
    pinned_coordinate_hash, user_world_seed, generator_version, n_users and
    n_clusters are read into `identity` and never compared to anything. A
    mis-copied directory verifies against its own sidecar and is accepted.

B2  world_manifest_from_env SKIPS a None component (:147-148 `continue`), and
    verify_manifest_digests only checks arrays and digests agree WITH EACH OTHER
    (:246-252). A manifest missing one of the nine passes both.

B3  GENERATOR_FUNCTIONS (:46-52) names five functions. It omits
    _initialize_cluster_migration_rpgm, _generate_intra_cluster_waypoint,
    _generate_inter_cluster_waypoint and _generate_new_cluster_target_rpgm --
    exactly the transitive helpers of error 1 above. Two semantically different
    generators can share a generator_version.

B4  apply_world_manifest (:267-296) assigns the arrays, reads them back, and sets
    user_world_seed_applied. regenerate_user_world (:2282-2285) additionally runs
    _reset_connection_baseline, _update_channel_state, _update_uav_connections
    and _compute_routing_paths. Applying a manifest therefore leaves connections,
    routing and service baselines belonging to the world that was just replaced.
    That comment block at :2277-2281 exists because this exact omission once
    booked pre-episode handovers into the D7.S event fingerprint.

B5  save_world_manifest (:177-191) uses makedirs(exist_ok=True) and np.savez,
    both of which overwrite. There is no manifest-set inventory binding the
    expected key set, the identities, the digests and a set hash.

B6  d7_s_world_conformance_gate.py compares independently GENERATED
    episode_world_provenance records. It never loads one manifest on two runners.
    It is a generator diagnostic and keeps its three outcomes; it is not the
    Route A acceptance gate.
```

B4 is the one I would rank first. B1, B2, B3 and B5 admit a *wrong* manifest;
B4 accepts the *right* manifest and still produces a non-identifying hybrid
environment, so it fails on the happy path.

## One ruling I am adopting that reverses my own gate design

For **manifest replay**, two independently provisioned runners using the same
immutable bytes are meaningful evidence even when their CPU model strings match.
`RUNTIME_DISCRIMINATORS` belongs to the generator-portability question and must
not be carried into the replay gate, or a homogeneous hosted fleet creates a
permanent `UNTESTED` for a byte-replay mechanism -- an unfalsifiable gate.

Record distinct workflow job/runner identities instead. `--allow-same-runtime`
must not exist on the conclusion-bearing route at all.

## How step 1 is recorded, verbatim from the ruling

```text
CROSS_PLATFORM_FIRST_DIFFERING_SURFACE:  user_velocities
CLOUD_FLEET_ROOT_CAUSE:                  UNRESOLVED
GITHUB_HOSTED_HETEROGENEITY_TEST:        UNTESTED_ON_OBSERVED_EPYC_7763_PAIR
```

Forbidden: `CLOUD_CAUSE = scalar trig`, and
`WORLD_GENERATOR_PORTABLE_ON_GITHUB_FLEET`.

No further tagging of the homogeneous hosted fleet is required to name the old
cause. The heterogeneous-runtime probe is optional apparatus, not a gate.

## What this round changes about the plan

```text
0  record the cloud cause UNRESOLVED, keep the platform-surface finding   DECIDED
1  amend the Route A contract for runtime user-motion consequences        REQUIRED
2  close B1-B5                                                            REQUIRED
3  build a SEPARATE manifest-replay development gate (8 assertions)       REQUIRED
4  run it on development manifests over a FULL registered horizon         REQUIRED
5  freeze the fresh-population selection rule and result contract         PARALLEL
6  apply the frozen rule, generate an immutable inventory                 HELD
7  route any new formal run through separate compute authority            HELD
```

The A1-versus-A2 choice -- manifest plus one frozen runtime class, versus
persisting the exogenous trajectory or random tape -- is a **protected** decision
and must be frozen before any formal evidence. It is not mine to settle, and it
is the natural subject of the next round: A1 is smaller but binds the formal run
to a runtime class, and step 4's full-horizon exercise is exactly the measurement
that decides whether A1 is sufficient. **The measurement comes first**, so I do
not need to ask before running it.

## Standing correction

`20260730_STEP2_USER_VELOCITIES_WRITERS.md` and
`20260730_WORLD_DIVERGENCE_SCOPE.md` both carry claims this ruling refutes. They
are corrected in place with the refutation recorded, not silently edited -- the
same treatment the R4 re-run note got when Pro refuted my injectivity claim.
