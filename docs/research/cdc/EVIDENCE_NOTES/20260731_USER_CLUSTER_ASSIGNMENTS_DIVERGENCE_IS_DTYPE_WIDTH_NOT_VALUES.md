# The user_cluster_assignments divergence is dtype width, not values

Date: 2026-07-31
Question: by what mechanism can an integer array differ across the platform
boundary while `user_positions` is bit-identical and the RNG stream is aligned?
Open since the round-2 localization; named STILL OPEN in `CURRENT_WORK.md` until
this note.

Investigated by a dispatched general-purpose child (opus, high effort) at HEAD
`5e25ae1e`; every load-bearing claim below was re-verified mechanically by the
Project Manager before entering this record. What the PM re-ran itself:
`np.zeros(n, dtype=int).dtype` on the registered interpreter, the digest
recomputation at both widths against the committed `manifests/d7s_dev/`
artifacts, the writer grep, and a read of the digest and manifest-application
source. The witness scripts lived in session scratchpad and are ephemeral; the
reproduction recipe below is self-contained and does not depend on them.

## The mechanism

**The divergence is not in the values. It is in the serialized byte width.**

1. `envs/pettingzoo/scenario_base.py:369` creates the array as
   `np.zeros(self.n_users, dtype=int)`. On numpy 1.26.3, `dtype=int` resolves to
   the C `long`: **int32 on Windows, int64 on LP64 Linux** (the Linux half is
   inferred, not executed here — see the falsifiable prediction below). It is
   the only integer-typed component of the nine fingerprinted world arrays; the
   other eight are `float64` on every platform.
2. The component digest at `scripts/audit_d7_s_event_aligned.py:1661-1664`
   hashes `name + str(shape) + tobytes()` and **does not hash dtype**. The same
   30 values serialize to 120 bytes as int32 and 240 bytes as int64, so
   identical values digest differently across the boundary. The digest is not
   blind to the width — it is *only* seeing the width.

Measured on the committed development manifest (topology `20260725`, block
`audit`, episode `0`, 30 values):

```text
stored dtype in world.npz                 int32 (<i4), matching inventory.json
digest as int32   7399fedfba7a6b7f9f8160fa11aa416b09df5e0c76bad9ab82b669192316a5a3
                  == the archived inventory digest, recomputed by the PM
digest as int64   4266e9ee372a9242f925fce1c3e76e50cc91a870aa47d7a9b38030d3d160ea3e
values equal      True        digests equal   False
```

## What the child measured, and the PM's spot checks confirmed

- **Three writers on the D7.S path, not two.** `scenario_base.py:369`
  (creation, `__init__` only — `reset()` never recreates it), `:791`
  (`cluster_idx` during cluster generation), and `:2507`
  (`np_random.choice` result). `:2507` is reachable **during construction** via
  `_initialize_user_waypoints_rpgm`, not only during stepping; it fired for 4 of
  30 users on this topology. The earlier framing that only the `:791` writer
  runs before the fingerprint was incomplete.
- **The fixed-draw-count claim is refuted.** Counting MT19937 buffer words:
  the intra-cluster branch consumes 8 words per user, the inter-cluster branch
  9 (`choice` costs one extra). The claim "both branches consume a fixed number
  of draws" (`20260730_STEP2_USER_VELOCITIES_WRITERS.md`, line 83) is false.
  This refutation does not itself create a divergence — the branch gate is
  portable — but the premise is dead and must not be cited again.
- **No float input can flip a value.** The only float gates feeding the array
  are `np_random.random() < 0.8` (a raw MT19937 double against a constant, no
  libm; minimum observed margin 8.2e-04 over 30 decisions) and
  `distance > 1e-6` (minimum margin 30.25, seven orders above threshold).
  Perturbing every `np.cos`/`np.sin` during construction by 1 ULP, and
  separately by 1e-9 relative, moved `user_velocities` and `user_waypoints`
  while leaving `user_cluster_assignments` values bit-unchanged and
  `user_positions` byte-identical — independently reproducing the round-2
  observation that positions are trig-free.

## The falsifiable prediction, and the exact test

The one unexecuted link is that `ubuntu-latest` numpy 1.26.3 resolves
`dtype=int` to int64. No Linux runtime exists on this workstation (WSL absent),
no archived cloud artifact records `component_dtypes`, and the per-key rows of
the run-`30516912923` comparison were never archived — only the tally survived.

If the mechanism is right, `user_cluster_assignments` appears among the
differing components on **every** Windows-vs-Linux key — all 6 of 6, not 1. It
was reported *first-differing* on only 1 key because it is 5th in component
order and `user_velocities` (2nd, trig-borne) usually differs first. If archived
rows ever showed it differing on only 1 of 6 keys as a component, this mechanism
is wrong.

Direct yes/no test, seconds of compute, rides the already-escalated cloud job
(`docs/project/PROPOSED_WORKFLOW_JOB_MANIFEST_REPLAY.md`): a Linux-side digest
of this array for topology `20260725` / `audit` / `0` under contract
`D7_S_MANIFEST_REPLAY_DEVELOPMENT` equals `4266e9ee...` (mechanism confirmed)
or `7399fed...` (mechanism refuted, Linux default is not int64).

## What this does NOT explain

**The cloud-versus-cloud divergence — 3 of 8 R4 topologies between two
`ubuntu-latest` runners — is untouched.** Two Linux runners share one integer
width, so this mechanism cannot produce it. That divergence remains UNRESOLVED,
exactly as ruled in round 2.

## Action 8 is not threatened by this

Checked because a spurious failure here would have wasted the escalated cloud
run: `apply_world_manifest` (`scripts/d7_s_world_manifest.py:702-736`)
**rebinds** each attribute — `setattr(env, name, np.ascontiguousarray(arr).copy())`
— so the committed int32 arrays keep their dtype on Linux, and it verifies
digests on read-back after assignment, which would catch any coercion. The load
path separately enforces recorded dtypes (`_compare_layout`). Both cloud jobs
will therefore hold and digest the int32 bytes the inventory froze. The dtype
split bites only the *regeneration* path — which is precisely the path the
manifest exists to remove.

## Disclosure owed at the next touchpoint (not changed now)

Whether the instrument should treat width as world-distinguishing is an open
implementation binding: either the component digest canonicalizes dtype, or
`scenario_base.py:369` pins `dtype=np.int64`. Neither edit is made now — the
committed `manifests/d7s_dev/` inventory carries `<i4` digests, the digest
definition feeds the registered fingerprint, and a unilateral change would
re-key committed evidence. Recorded here as a disclosure item alongside the
existing list in `CURRENT_WORK.md`.

## RESULT, 2026-07-31, same day: the prediction is CONFIRMED, 6 of 6

The round-2 cloud artifacts were still downloadable (`gh run download`,
runs `30516912923` / `30518707693`, both `d7s-workers-proof`). The PM ran
`scripts/d7_s_world_digest_probe.py` locally over the same six episode keys
(contract `D7_S_EVENT_ALIGNED_SOURCE_AUDIT`, topology `20260725`), reproduced
the round-2 tally exactly with `scripts/d7_s_world_component_digest_diff.py`
(5 x `user_velocities`, 1 x `user_cluster_assignments`, the latter on
**audit ep0** — the key the round-2 comparison never archived), then rebuilt
each world and compared the cloud digest against the local values cast to both
widths:

```text
key              seeds_match   local_int32==cloud   local_int64==cloud
audit ep0        True          False                True
audit ep1        True          False                True
calibration ep0  True          False                True
calibration ep1  True          False                True
calibration ep2  True          False                True
calibration ep3  True          False                True
```

**6/6 int64 matches.** The inferred link is now measured: `ubuntu-latest`
serializes this array at 8 bytes per element, the values are bit-identical
across the platform boundary on every key, and the array was only *reported*
first-differing on the one key (audit ep0) where the trig-borne
`user_velocities` happened to agree — exactly the ordering artifact the
prediction named. The `user_cluster_assignments` divergence is **closed as a
value question**: no value ever differed.

**Cloud-versus-cloud, same download, new bound.** All four artifacts across the
two runs (`w1`/`w4` arms of both) share one SHA-256
(`4153fb150798b7f6...`), at head SHAs `add28991` and `08a3453c`. Two
independently provisioned `ubuntu-latest` runners agreed byte-for-byte on the
dev vehicle — so the unresolved 3-of-8 R4 cloud-cloud fingerprint divergence
did **not** reproduce here, and whatever causes it did not fire on this
topology/commit pair. That divergence remains open; this narrows where it can
live.

## Reproduction recipe (self-contained)

```python
# registered interpreter: C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
import numpy as np, hashlib
print(np.zeros(5, dtype=int).dtype)              # int32 here, int64 on LP64
d = np.load('manifests/d7s_dev/D7_S_MANIFEST_REPLAY_DEVELOPMENT/20260725/audit/0/world.npz')
arr = d['user_cluster_assignments']
for a in (arr, arr.astype(np.int64)):
    chunk = b''.join((b'user_cluster_assignments', str(a.shape).encode(),
                      np.ascontiguousarray(a).tobytes()))
    print(a.dtype, hashlib.sha256(chunk).hexdigest())
```
