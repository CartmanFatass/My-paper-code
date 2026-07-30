# D7.S world-manifest persistence and replay

Status: **implemented at schema 2, not wired in, no compute authorized by it.**
Selected repair family per the Pro ruling of 2026-07-30,
`docs/external-review/rounds/20260730_d7_s_provenance_correction_result/`.

This document makes the ruling's requirements executable and nothing more. It
adds no scientific decision. Where it makes a choice the ruling left open, that is
marked **[PM binding]** and is disclosed rather than presented as Pro's.

## The problem it removes

A registered episode key -- contract namespace, topology-coordinate hash, block,
episode index, `user_world_seed` -- does not identify one world. Two cloud runs at
identical keys and hard-pinned dependencies produced different initial worlds on 3
of 8 topologies. The ruling's requirement:

> A registered episode key must identify either one reproducible world or one
> validated probability law.

Route A is selected: fixed-world reconstruction. It preserves the actual generated
bytes and makes those bytes -- not an unreliable promise about regeneration -- the
authoritative evidence input.

## AMENDMENT (round 2): an initial manifest is not the whole repair

The round-1 version of this document said trig portability stops mattering because
the trig is never re-executed. **That is false for any horizon longer than zero
steps**, and the correction is the most consequential thing in the round-2 ruling.

Verified in source at `envs/pettingzoo/scenario_base.py`:

```text
_initialize_user_waypoints_rpgm  :2512   calls three trig helpers and then
                                          OVERWRITES user_velocities at :2539
_update_user_positions_rpgm      :2320   re-enters the waypoint generators
_update_cluster_centers_rpgm     :2372   re-enters _generate_new_cluster_target_rpgm
_generate_intra_cluster_waypoint :2470   np.cos / np.sin
_generate_inter_cluster_waypoint :2498   np.cos / np.sin
_generate_new_cluster_target_rpgm:2444   np.cos / np.sin
_initialize_cluster_migration_rpgm:2557  np.cos / np.sin
```

R4 measures 139 or 550 steps after the event. So the repair family must be stated
as the ruling states it:

> **Manifest-defined initial evidence population, plus a registered execution rule
> preventing unregistered runtime variation from changing the exogenous world
> process after initialization.**

### The three sub-realizations, and which is frozen

```text
A1  manifest + one frozen registered runtime class     LIVE, simplest
A2  exogenous-process / random-tape replay             LIVE, stronger
A3  portable user-motion implementation                NOT SELECTED -- overlaps
                                                       Route B, changes dynamics
```

**A1 versus A2 is a PROTECTED choice and is NOT frozen here.** The measurement
that decides it is the full-horizon exercise in the replay gate below: if A1's
horizon equality holds across independently provisioned runners, A1 suffices; if
later RPGM transitions diverge under A1, A2 is required. The measurement comes
first.

## The manifest, schema 2

```text
schema_version                  int, bumped on ANY layout change
contract_id                     the population namespace
topology_seed
pinned_coordinate_hash
block                           calibration | audit
episode_index
user_world_seed
generator_version               [PM binding] see below
n_users, n_clusters
arrays                          exactly WORLD_COMPONENT_ORDER, all nine, no skips
component_digests               one SHA-256 per array, same bytes as the fingerprint
component_shapes                per array, checked on load
component_dtypes                per array, checked on load
payload_hash                    one hash over the nine component digests
```

**Storage.** `.npz` per episode plus a JSON sidecar, under
`<contract_id>/<topology_seed>/<block>/<episode_index>`, **create-once**. Plus one
`inventory.json` per manifest root binding every episode key, identity, component
digest set, payload hash and a `set_hash` over the whole population.

`payload_hash` is derived from the component digests, **not** from `world.npz`. A
zip carries timestamps and member ordering, so hashing the file would report two
byte-identical worlds as different and make the inventory useless for exactly the
comparison it exists for.

**Bit-exactness is the whole point.** No tolerance anywhere in this path -- a
tolerance here would re-admit exactly the drift the manifest exists to exclude.
The paired negative perturbs by one ULP, because `user_positions` differing in the
last bit is the actual failure mode.

## The five schema-1 defects the round-2 ruling found

Each of them is a manifest that verifies perfectly against **itself** and is not
the registered world. That is the family; schema 1 admitted it five ways.

```text
B1  load compared only schema_version. The other nine identity fields were read
    and never checked, and four of them came FROM the path -- so a manifest copied
    into a plausible directory verified against its own sidecar and was accepted.
    FIX: load requires an INDEPENDENTLY supplied expected identity, and compares
    every field plus shapes and dtypes.

B2  an absent component was skipped on capture, and verification compared the
    array set against the digest set -- consistent, and short by one.
    FIX: capture refuses an absent component; verification requires the set to
    equal WORLD_COMPONENT_ORDER.

B3  generator_version hashed five hand-listed functions. Measured: the transitive
    closure is EIGHT. The three missing are _initialize_cluster_migration_rpgm,
    _generate_intra_cluster_waypoint and _generate_inter_cluster_waypoint --
    exactly the trig helpers that overwrite the array that diverged.
    FIX: the closure is DERIVED from the AST, never listed. So is configuration:
    constructor signatures across the MRO, union every attribute the closure
    reads. An env whose closure is EMPTY is refused rather than versioned.

B4  apply installed the arrays and stopped. THE ONLY BLOCKER THAT FAILS ON THE
    HAPPY PATH: a correct manifest still left connections, channel state and
    routing belonging to the world just replaced.
    FIX: apply runs DERIVED_STATE_REBUILD, and a test compares that constant
    against what regenerate_user_world actually calls.

B5  save overwrote in silence and nothing bound the population together.
    FIX: create-once (idempotent for identical bytes), plus the set-hashed
    inventory. A deleted episode leaves every remaining manifest verifying
    perfectly; only the set hash notices.
```

## [PM binding] generator_version

The ruling requires the version to cover *every reachable writer and every source
parameter*. Binding: a content hash over the transitive call closure's source from
the five generation entry points, plus every constructor parameter across the MRO
unioned with every attribute that closure reads, excluding the nine world
components themselves (they are the generator's output).

Rationale, and the alternative rejected: a hand-maintained integer fails the way
every hand-maintained version fails. So does a hand-maintained *list* -- that is
precisely how B3 happened. The cost is that a whitespace-only edit invalidates
existing manifests; that is the correct direction to err, because a wrongly
invalidated manifest is regenerated while a wrongly accepted one is a false result.

## [PM binding] the derived-state postcondition

`apply_world_manifest` must reproduce the complete post-`regenerate_user_world`
transition: `_reset_connection_baseline`, `_update_channel_state`,
`_update_uav_connections`, `_compute_routing_paths`, in that order.

**Measured before asserting it, not after:** 35 functions are reachable from those
four calls and **none** of them touches `np_random`. So "the rebuild consumes no
registered continuation randomness" is a satisfiable assertion rather than an
aspiration, and any future edit that breaks it is a real finding.

## The Route A acceptance gate

`d7_s_world_conformance_gate.py` compares independently **generated**
`episode_world_provenance` records. It is a useful generator diagnostic, keeps its
three outcomes, and **is not this gate**.

`scripts/d7_s_manifest_replay_probe.py` produces one runner's evidence;
`scripts/d7_s_manifest_replay_gate.py` compares two. Split because the comparison
must run anywhere, on artifacts from machines that never met.

```text
a1  sidecar identity equals the independently expected identity
a2  the complete nine-component set, shapes and dtypes
a3  payload and component digests match before application
a4  post-application readback matches exactly
a5  post-world-replacement derived state matches the canonical postcondition
a6  the complete pre-step environment identity matches
a7  the load and rebuild consume no registered continuation randomness
a8  a full registered stable AND flex horizon executed from the same manifest and
    streams, comparing exogenous trajectories, event and candidate identity,
    primary-G component series, and branch-relevant quantities
```

a1-a7 are local to a probe; **a8 is a cross-runner equality**, so the probe records
the digests and the gate does the comparing.

### The runtime rule, reversed from what this project wrote

For manifest **replay**, two independently provisioned runners using the same
immutable bytes are meaningful evidence **even if their CPU model strings match**.
`RUNTIME_DISCRIMINATORS` belongs to the generator-portability question; carrying it
across would make a homogeneous hosted fleet produce a permanent `UNTESTED` for a
byte-replay mechanism -- an unfalsifiable gate that reads like caution.

Independence is established from the **job**: run id, run attempt, job, runner
name, hostname, pid. **There is no `--allow-same-runtime` and there must never be.**

### One extra condition the ruling did not name, added here

The gate returns `UNTESTED` if applying the manifest replaced **no** component.
The probe deliberately builds its env with `user_world_seed=None`, so the world it
starts from is the non-identifying construction-time state the manifest exists to
replace. If the readback agrees with a world that was already there, it tested
nothing. **[PM binding]**, and the same failure shape as the generator gate's
`UNTESTED`.

## What this design does NOT do

- It does not decide A1 versus A2. That is protected and waits on the measurement.
- It does not make world generation bit-portable. Route B is parked as a **change
  to the registered draw**, not a refactor.
- It does not select, generate or inspect a confirmatory population. The probe
  **refuses** any topology in the frozen R4 set, because a probe run over an R4
  seed would inspect a confirmatory world while looking like apparatus work.
- It does not touch any threshold, result branch, or historical JSON.
- It does not authorize compute.

## Sequencing

```text
0  cloud-fleet cause recorded UNRESOLVED, platform surface retained   DECIDED
1  amend the Route A contract for runtime user-motion consequences    THIS DOC
2  close B1-B5                                                        DONE
3  build the separate manifest-replay gate                            DONE
4  run it on DEVELOPMENT manifests over a full registered horizon     IN PROGRESS
5  freeze the fresh-population selection rule and result contract     PARALLEL
6  apply the frozen rule, generate an immutable inventory             HELD
7  route any new formal run through separate compute authority        HELD
```
