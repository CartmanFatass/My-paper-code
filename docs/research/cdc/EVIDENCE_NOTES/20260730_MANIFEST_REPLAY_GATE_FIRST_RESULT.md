# The replay gate's first result: replay works, and assertion 6 fails for another reason

> **REFUTED 2026-07-30 by the Pro ruling in
> `docs/external-review/rounds/20260730_d7_s_manifest_replay_gate_result/21_PRO_OPEN_RAW.md`,
> §5.1 and §5.2.** The characterization of the six differing attributes is
> incorrect. Two specific claims are dead:
>
> 1. **The six fields are not all station-distance-derived.** The two
>    `last_min_station_distance_*` caches are station-distance-derived, and the
>    return threshold/margin arrays are downstream of station distance and battery.
>    But `current_graph_potential` is a graph-service potential computed from
>    communication, user/UAV geometry, and backhaul capacity. `state` is a
>    composite cache containing base state, energy state, station state, and stage
>    identity. The evidence establishes AT LEAST TWO stale initialization families:
>    station/return-energy-derived state; and topology/world/radio-derived potential
>    and public state.
> 2. **Replay is not exonerated as a complete evidence-population reconstruction
>    mechanism.** The manifest payload does not create these values, but the
>    current manifest application path fails to canonicalize or replace
>    construction-derived state that remains live at the pre-step boundary. Replay
>    is exonerated as the source of the original bytes. It is not exonerated as a
>    complete evidence-population reconstruction mechanism.
>
> What survives: Manifest replay reproduced the episode, the post-roll world,
> event identity, and both limbs' units across independent executions. The
> pre-step divergence is construction-borne (six of 273 attributes), and one
> carrier is a provably stale distance cache. The measurements are correct; only
> the characterisation of them was wrong.

Date: 2026-07-30
Instruments: `scripts/d7_s_manifest_replay_probe.py`, `scripts/d7_s_manifest_replay_gate.py`
Topology: `TOPOLOGY_SEED_DEV = 20260725`. **No R4 topology was constructed** -- the
probe refuses them, because a support probe over a candidate is inspection.

## The verdict, and why it is not the verdict it looks like

```text
MANIFEST_REPLAY_FAIL:pre_step_state_fingerprint
independent executions: True -- pid differs
compared 1 episode key
```

Everything else agreed, across two independent executions of a full registered
horizon:

```text
manifest_payload_hash          EQUAL
episode_world_fingerprint      EQUAL   (all nine world arrays)
post_roll_world_digests        EQUAL   (after the prefix roll -- every RPGM
                                        waypoint regeneration folded in)
event_conformance_digest       EQUAL
duty_map_at_te_digest          EQUAL
snapshot_state_hash            EQUAL
unit_stable_digest             EQUAL   (H_STABLE = 139)
unit_flex_digest               EQUAL   (H_FLEX  = 550)
local assertions a1-a7         PASS on both sides
replaced_a_different_world     True on both sides
```

**Manifest replay reproduced the episode.** The nine arrays, the post-roll world,
the event and candidate identity, and both limbs' primary-`G` units are
byte-identical between two executions that each started from a *different*
construction-time world -- `replaced_a_different_world=True` proves the manifest
overwrote something else rather than agreeing with a world that was already there.

The one failing assertion is 6, "the complete pre-step environment identity
matches", and the measurements below show it fails for a reason that has nothing
to do with replay.

## Isolation: the divergence exists without a manifest anywhere

Two `build_pinned_env` calls in ONE process, identical seeds, **no manifest**:

```text
                          two constructions equal?
episode_world_fingerprint          True
full_state_fingerprint             False       <- with AND without a user_world_seed
episode_graph_pbrs_sum             True  (0.0 on both)
station_occupancy / station_queue  True
coordinate_hash                    True
```

So the failing surface differs between two plain constructions. ~~**Replay is
exonerated by measurement, not by argument.**~~ **UNQUALIFIED — Replay is exonerated
as the source of the original bytes, but not as a complete evidence-population
reconstruction mechanism** (see refutation banner for full correction).

This also **refutes the explanation `full_state_fingerprint`'s own docstring
gives.** It blames station-relative logistics and says the residue lives in
`episode_graph_pbrs_sum` -- and that sum is `0.0` on both sides, as are station
occupancy and queue. The docstring names a carrier that is measurably identical.

## Naming the surface, from the fingerprint rather than from a hypothesis

`full_state_fingerprint` is include-by-default, so the differing attributes can be
read off directly. Of **273** fingerprinted attributes, **6** differ:

```text
last_min_station_distance_before
last_min_station_distance_after
uav_return_energy_margins
uav_return_threshold_ratios
current_graph_potential
state                              (the 306-dim observation, which embeds them)
```

~~All station-distance-derived~~ **NOT ALL station-distance-derived** -- while the charging-station coordinates **and** the
UAV positions both compare byte-equal. (Refutation recorded in banner above.)

## Proving it is a stale cache, by making it converge

Two of the six clear themselves on the path the audit already takes:

```text
as built                          7 surfaces differ (incl. full_state_fingerprint)
after apply_energy_profile        5   -- uav_return_energy_margins and
                                       uav_return_threshold_ratios converge
after a second explicit refresh   5   -- no further change
```

The remaining distance cache converges when it is recomputed from the **current**
inputs:

```text
BEFORE   uav_positions equal=True   charging_station_positions equal=True
         last_min_station_distance_before/after   equal=False

AFTER recomputing from the current station coordinates
         last_min_station_distance_before/after   equal=True
```

Both inputs are identical, so a differing output can only have been computed when
one of them was different. `scenario7_energy_aware.py:487-488` computes it at
`reset()`; `build_pinned_env` restores the registered coordinates **after** that
reset and nothing recomputes it. **Stale cache, proven by recomputation rather
than asserted from reading the call order.**

`current_graph_potential` does **not** converge under that recompute, so the
residue has at least two carriers and only one of them is localized. Recorded as
open rather than folded into the same sentence.

## What this means for the ruling's assertion 6

Assertion 6 as written -- *the complete pre-step environment identity matches* --
**cannot pass on this codebase**, for a reason a manifest cannot fix. The
environment carries construction-time state derived from unseeded OS entropy
(`scenario_base.py:328`), and a manifest defines the user world, not the whole
environment.

This is exactly the reactivation condition the parked item names in
`CURRENT_WORK.md`:

> the OS-entropy construction seed is ruled **parked** -- reactivate the
> station-logistics reorder only if [...] a result must reproduce the whole event
> state from registered seeds

Assertion 6 *is* that requirement. **The trigger has fired.**

**The assertion was not weakened to make the gate green.** Narrowing it to the
surfaces a manifest can determine would be repairing the check instead of the
defect, and the residue reaches `state` -- the observation vector -- which is not
obviously outside the claim even though it did not reach the units here.

The gate now names the differing attributes instead of reporting two hashes, so
the next reader does not have to redo this.

## What is measured, and what is not

**Measured.** Replay reproduces the world, the post-roll world, event identity and
both limbs' units across independent executions. The pre-step divergence is
construction-borne, is six of 273 attributes, and one carrier is a provably stale
distance cache.

**NOT established.** That the residue is harmless. The units agreed *in this
episode*, which is one episode on one topology; that is evidence, not a theorem.
`state` differs, and any path that consumed observations would see it.

**NOT established.** Cross-MACHINE replay. Both executions were local processes,
so this is cross-PROCESS evidence. The gate reports independence from `pid`, which
is honest about what it proved and is not the same as two provisioned runners.

**NOT established.** That A1 suffices. Horizon equality held here between two
processes on one machine and one runtime; the question A1-vs-A2 asks is whether it
holds across runtimes, and that needs the cloud vehicle.

## One prediction of mine that was wrong

I recorded that the other line's 667-line change to `scenario_base.py` would move
`generator_version` and invalidate the development manifests. Measured across the
rebase: `generator_version` is **unchanged** (`478ecb5b8ac60dec2444...`) and the
payload hash is identical. The derived closure is precise enough to be unmoved by
an edit to the same file that does not touch the world generators -- which is the
behaviour the derivation was for, and I predicted the opposite.
