# Step 2: every writer and random source for the diverging array -- WRITER TABLE REFUTED

> **REFUTED 2026-07-30 by the Pro ruling in
> `docs/external-review/rounds/20260730_d7_s_provenance_correction_result/21_PRO_OPEN_RAW.md`,
> §3.1-§3.2, and re-verified in source by the Project Manager.** The table below
> is **incomplete** and its headline conclusion does not hold. Three specific
> claims are dead:
>
> 1. **`_initialize_user_waypoints_rpgm` does not use only `sqrt`.** It calls
>    `_initialize_cluster_migration_rpgm` (`np.cos`/`np.sin` at
>    `scenario_base.py:2557-2558`), `_generate_intra_cluster_waypoint` (`:2470`)
>    and `_generate_inter_cluster_waypoint` (`:2498`), and then **overwrites**
>    `user_velocities` from the waypoint direction at `:2539`. On the `rpgm` path
>    it, not `_init_user_velocities`, is the final writer of the fingerprinted
>    array. So "exactly one non-portable operation" is false, and so is
>    "`_init_user_velocities` is the writer that matters".
> 2. **Replay does not retire the trig path.** `_update_user_positions_rpgm`
>    (`:2320`) and `_update_cluster_centers_rpgm` (`:2372`) re-enter those same
>    trigonometric generators every time a user or cluster centre reaches its
>    waypoint. An initial-state manifest covers `t = 0` only; R4 runs 139 or 550
>    further steps. The §"Consequence for the repair choice" section below is
>    wrong for any horizon longer than zero.
> 3. **The `user_cluster_assignments` near-tie story was never available.** On
>    this path the assignment is an integer written either as `cluster_idx`
>    during generation or by an explicit `np_random.choice` at `:2507`. There is
>    no floating-point nearest-centre classifier to produce a near-tie.
>
> What survives: `user_velocities` is still the earliest differing component
> across the platform boundary, it is still written through a trigonometric path,
> the pre-registered `user_positions`/SVD mechanism is still dead, and Route B is
> still a change to the registered draw. What does not survive is uniqueness --
> which was the load-bearing claim, and the one this round asked to have attacked.
>
> The record of the error is kept rather than edited away. Reconciliation:
> `.../30_PM_SCIENTIFIC_RECONCILIATION.md`.

Date: 2026-07-30
Ordered by the Pro ruling (`20260730_d7_s_r4_rerun_disposition`), step 2 of five:

> identify every writer and random source for that array

Step 1 named the array across a platform boundary: **`user_velocities`**
(`20260730_WORLD_DIVERGENCE_PREREGISTERED_PREDICTION.md`, RESULT section).

## The writers, on the configured path

`user_distribution = "forced_relay_cluster"`, `user_movement_model = "rpgm"`, so
`_generate_coverage_hole_positions` is not reached.

| writer | writes | random source | non-portable operations |
|---|---|---|---|
| `_generate_user_positions` | dispatch only | -- | none |
| `_generate_forced_relay_cluster_positions` | `user_positions`, `cluster_centers_history`, `user_cluster_assignments` (line 790) | `np_random.uniform`, `np_random.multivariate_normal` | `cluster_std**2`; SVD inside `multivariate_normal` |
| `_init_user_velocities` | `user_velocities` | `np_random.uniform` x2 | **`np.cos`, `np.sin`** |
| `_initialize_user_waypoints_rpgm` | `user_waypoints`, `user_velocities` (overwrites) | `np_random.random`, `np_random.uniform` | ~~`np.linalg.norm` -> `sqrt`~~ **WRONG -- also `np.cos`/`np.sin` via three helpers; see the banner** |

## ~~The single non-portable operation~~ -- REFUTED, there is more than one

**IEEE 754 requires `sqrt` to be correctly rounded. It does not require `sin` or
`cos` to be.** Every other operation above is an IEEE-mandated arithmetic
primitive, and `sqrt` via `linalg.norm` is portable for the same reason.

So on this path there is exactly one operation whose result may legitimately differ
between two conforming implementations:

```python
# _init_user_velocities
angle = self.np_random.uniform(0, 2 * np.pi)
self.user_velocities[i, 0] = speed * np.cos(angle)
self.user_velocities[i, 1] = speed * np.sin(angle)
```

And that is precisely the array measured to diverge, while `user_positions` -- which
goes through `multivariate_normal`'s SVD and no transcendentals -- is bit-identical
across the same boundary. The RNG stream is provably shared: identical positions
require identical draws.

~~`user_cluster_assignments` is an `int` array written at line 790 from float
comparisons, so it cannot drift numerically but a near-tie can flip.~~
**REFUTED.** It is written as the integer `cluster_idx` during generation and by
an explicit `np_random.choice` at `scenario_base.py:2507` -- no float comparison
is involved, so no near-tie exists to flip. The one differing key is therefore
**unexplained**, and since both branches consume a fixed number of draws from an
aligned stream, it is evidence that this writer audit is incomplete.

## Consequence for the repair choice -- the Route A half is REFUTED

The ruling left two routes live. This finding separates them sharply.

**Route A -- persist and replay the complete manifest (selected).** ~~Generation
happens once, on one machine, and every formal episode loads those bytes. Trig
portability stops mattering entirely, because the trig is never re-executed.~~
**REFUTED for any horizon longer than zero steps.** An initial-state manifest
fixes `t = 0`; `_update_user_positions_rpgm` and `_update_cluster_centers_rpgm`
re-execute the same trigonometric generators during the episode. Route A is still
selected, but only as **manifest plus a registered execution rule** -- either a
frozen runtime class (A1) or a persisted exogenous-process tape (A2). That choice
is protected and unfrozen.

**Route B -- a deterministic pure seed-to-world generator (live alternative).** To
make generation bit-portable, the `np.cos`/`np.sin` dependency must be removed or
pinned. Every way of doing that **changes the values drawn**:

- replacing trig with a portable direction draw (e.g. rejection sampling on the
  unit disc using only arithmetic) produces different velocities from the same
  stream;
- pinning a specific libm or a software implementation changes the values relative
  to today's;
- rounding the result to fewer bits changes them too.

So Route B is not a refactor -- it is a **change to the registered draw**, and it
invalidates every world any existing artifact recorded. That is a contract change
and a scientific decision, not an implementation binding.

**Recommendation for the next Pro touchpoint, not decided here:** Route A on the
strength of this, with Route B parked unless bit-portable regeneration is needed for
a reason replay cannot serve.

## What is still open

This localization is from the **confounded** local-versus-cloud comparison
(Windows/MSVC/AMD versus Linux/glibc). It is decisive about *that* boundary, and
scalar trig is a complete explanation for it.

It is **not** established for the divergence the ruling is actually about:
cloud-versus-cloud, 3 of 8 R4 topologies, two `ubuntu-latest` runners with identical
pins and presumably the same glibc. If two glibc runners produce different `sin`
results, that needs a different explanation -- a different glibc version, or a
different vectorised code path selected by CPU. `d7s-workers-3` (run
`30518707693`) is the sample that tests it and is still running.

Pro's Challenge 6 continues to bind: nothing here is frozen as *the* cause of the
cloud-versus-cloud divergence.

## PRE-REGISTERED, before `d7s-workers-3` is read

The cloud-versus-cloud divergence needs a mechanism that works with the **same**
glibc on both runners. There is one, and it is the same family as the platform
finding rather than a new one:

**glibc dispatches `sin`/`cos` through ifunc on CPU features.** libm ships multiple
implementations -- notably FMA-using variants -- and selects at load time from what
the CPU reports. Two `ubuntu-latest` runners on different microarchitectures
therefore run *different* `sin` code from the *same* glibc, and FMA changes the
rounding of the intermediate products.

That predicts, for run `30518707693` against run `30516912923`:

```text
first differing component (generation order)   user_velocities
user_positions                                 IDENTICAL
divergence present on SOME episode keys, not all
```

The partial pattern is part of the prediction, not an escape: a dispatch difference
only shows in the last bits for angles where the two implementations disagree, which
is why the R4 population showed 3 of 8 topologies rather than all eight.

**What refutes it:**

- `user_positions` differs. Then the RNG stream or the SVD is implicated after all,
  and the trig story does not cover the cloud case.
- The first differing array is one the platform comparison found identical, with
  `user_velocities` identical. Then cloud-versus-cloud is a genuinely different
  mechanism.
- Every component agrees. Then the two runners were not distinguishable on this
  topology and the comparison tested nothing -- `UNTESTED`, not a pass, and the
  escalated probe job over the R4 seeds becomes necessary.
- The gate reports the runtimes as indistinguishable. Same as above: no evidence
  either way.

Written before reading the artifact, for the same reason as the previous
pre-registration: the last one turned a wrong hypothesis into a marked-dead one
instead of letting it disappear quietly.

## RESULT: the cloud-versus-cloud comparison is UNTESTED, exactly as pre-registered

Run `30518707693` arm `w1` against run `30516912923` arm `w1`, both `ubuntu-latest`,
same commit family, same pins, same invocation, launched **concurrently** so they
could not share a runner.

```text
shared episode keys                6
fingerprints differing             0 of 6
first differing component          none -- all nine arrays agree on every key
runtimes distinguishable           False (audit artifacts record no runtime_identity)

WORLD_CONFORMANCE_UNTESTED         (exit 1)
```

**This neither confirms nor refutes the glibc-ifunc prediction.** It is the third
item on that prediction's own refutation list, quoted before the artifact was read:

> Every component agrees. Then the two runners were not distinguishable on this
> topology and the comparison tested nothing -- `UNTESTED`, not a pass, and the
> escalated probe job over the R4 seeds becomes necessary.

Two explanations remain open and the artifacts cannot separate them:

1. **Development topology 20260725 is simply stable.** The measured divergence is 3
   of 8 *R4* topologies; 20260725 is not an R4 topology at all. The `workers` job is
   the only accessible job that emits component digests, and it runs only this
   topology.
2. **Both runs landed on similar hardware.** Concurrency guarantees different
   runners, not different CPU models, and the `workers` job prints `nproc` and no
   CPU identity.

The gate returning `UNTESTED` rather than `PASS` here is the design working. A
two-outcome gate would have reported six-for-six agreement as a pass and closed step
1 on evidence that establishes nothing.

## The accessible route is now exhausted, with the result recorded

Step 1's clean answer requires component digests from two runs, on **R4 topologies**,
with **runner identity recorded**. Of the three existing workflow jobs, none provides
that: `audit` is the 114-minute formal run, `workers` is the development topology
only, `benchmark` emits no digests. Both attempts at the accessible route were made
and both returned uninformative for reasons stated in advance.

**The escalation stands and is now evidenced rather than predicted:** one job running

```text
python scripts/d7_s_world_digest_probe.py --episodes 2 --out probe.json
```

on `ubuntu-latest`, uploading the JSON. Seconds of compute, the R4 seeds where the
divergence lives, and `platform`/`processor`/`openblas configuration`/CPU-dispatch
recorded inside the artifact so a future agreement is interpretable instead of
ambiguous. Run twice, diff with `d7_s_world_conformance_gate.py`.

Until then the platform-boundary localization (`user_velocities`, scalar trig) is
what step 1 has produced, and it is explicitly *not* the cloud-versus-cloud answer.
