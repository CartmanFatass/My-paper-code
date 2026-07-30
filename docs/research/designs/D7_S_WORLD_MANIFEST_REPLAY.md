# D7.S world-manifest persistence and replay

Status: **design only. Not implemented, not frozen, no compute authorized by it.**
Selected repair family per the Pro ruling of 2026-07-30,
`docs/external-review/rounds/20260730_d7_s_r4_rerun_disposition/`, §6.2.

This document makes the ruling's five requirements executable and nothing more. It
adds no scientific decision. Where it makes a choice the ruling left open, that is
marked **[PM binding]** and is disclosed rather than presented as Pro's.

## The problem it removes

A registered episode key -- contract namespace, topology-coordinate hash, block,
episode index, `user_world_seed` -- does not identify one world. Two cloud runs at
identical keys and hard-pinned dependencies produced different initial worlds on 3
of 8 topologies. The ruling's requirement:

> A registered episode key must identify either one reproducible world or one
> validated probability law.

Route A is selected: fixed-world reconstruction. Manifest replay achieves it
**without** requiring that world generation be made bit-portable, which is why it
is the reversible choice -- it works whatever the root cause turns out to be.

## Requirements, quoted

From §6.2, verbatim:

1. Generate the episode world once under a registered generator.
2. Persist the complete initial user/cluster manifest, not only its hash.
3. Make every formal episode load that manifest.
4. Verify its canonical digest before stepping.
5. Separate manifest identity, episode/continuation RNG, topology identity, and
   energy permutation.

## The manifest

**Contents.** Exactly the nine arrays `episode_world_fingerprint` hashes, in its
generation order, plus the identity needed to bind the manifest to its episode:

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
arrays        user_positions, user_velocities, user_waypoints, user_pause_times,
              user_cluster_assignments, cluster_centers_history,
              cluster_velocities, cluster_waypoints, cluster_pause_times
component_digests               one SHA-256 per array, same bytes as the fingerprint
fingerprint                     the combined SHA-256, unchanged in definition
```

**Storage.** `.npz` per episode plus a JSON sidecar carrying identity and digests,
under a manifest root keyed by
`<contract_id>/<topology_seed>/<block>/<episode_index>`. Arrays go in the `.npz`
because they are float64 and must round-trip bit-exactly; identity goes in JSON
because it must be readable without numpy.

**Bit-exactness is the whole point.** Arrays are written with `np.savez` from
`np.ascontiguousarray(...)` and reloaded with `allow_pickle=False`. Loading must
reproduce `component_digests` byte-for-byte or the episode fails closed. No
tolerance anywhere in this path -- a tolerance here would re-admit exactly the
drift the manifest exists to exclude.

## Requirement 4, and the trap in it

"Verify its canonical digest before stepping" must be a **refusal**, not a log
line. The check runs after loading and before the first `env.step`, and on
mismatch raises a named error that aborts the episode.

The trap this line has already fallen into twice: a check that cannot fail reads
as coverage forever. So the gate needs a paired negative that corrupts one array
by one ULP and watches the load refuse. A ULP, not a large perturbation --
`user_positions` differing in the last bit is the actual failure mode, and a gate
tuned to catch gross corruption would pass the real thing.

## Requirement 5 -- the four things that must not share a stream

```text
manifest identity     what world this is. A digest. Consumes no randomness.
world generation      draws the manifest ONCE, under generator_version.
episode/continuation  the arm streams: prefix roll, forks, bootstrap replicates.
energy permutation    draw_energy_permutation(energy_seed=...)
```

`regenerate_user_world` already restores `self.np_random` after drawing the world,
so the world does not consume from the arm streams today, and that property must
survive. A manifest LOAD consumes no randomness at all, which strictly improves
the separation: after this change the arm streams cannot be perturbed by anything
the world generator does or does not draw.

## [PM binding] generator_version

The ruling requires the tuple to include a world-generator version but does not
say how to derive it. Binding: a content hash over the source of the functions
that produce the nine arrays --
`_generate_user_positions`, `_generate_forced_relay_cluster_positions`,
`_generate_coverage_hole_positions`, `_init_user_velocities`,
`_initialize_user_waypoints_rpgm` -- plus `n_users`, `n_clusters` and
`cluster_std`.

Rationale, and the alternative rejected: a hand-maintained integer is the obvious
choice and it fails the way every hand-maintained version fails -- someone edits
the generator and forgets to bump it, and then two different worlds share a
version string. A source hash cannot be forgotten. Its cost is that a
whitespace-only edit to those functions invalidates existing manifests; that is
the correct direction to err, because a manifest that is wrongly invalidated is
regenerated, while a manifest that is wrongly accepted is a false result.

This is an implementation binding, disclosed here, not a scientific decision.

## What this design does NOT do

- It does not make world generation bit-portable across machines. Manifests are
  generated once, on one machine, and replayed. Whether the generator should ALSO
  be made deterministic is the live alternative in the ruling (§6.3) and is not
  decided here.
- It does not select a fresh confirmatory population. §6.5 is explicit that H and
  the current re-run must not be relabelled, and that no population is selected
  by that ruling.
- It does not touch any threshold, the R4 topology set, any result branch, or any
  historical JSON.
- It does not authorize compute.

## Sequencing

This is step 3 of the ordered five. Steps 1 and 2 -- localizing the first
differing array and identifying its writers -- are **not** prerequisites for the
manifest being correct, because replay is cause-agnostic. They are prerequisites
for the step 4 conformance gate knowing what to assert, and for the ruling's own
requirement that a cause not be frozen before it is named.

Step 4's gate must run **cross-process and cross-machine**. A single-machine check
is worthless here for a measured reason: one machine is exactly where the current
generator looks stable.
