# Pre-registered prediction: which world array diverges, and why

Date: 2026-07-30
Status: **written and committed BEFORE reading the cross-machine digests.**

Step 1 of the provenance correction ordered by the Pro ruling
(`docs/external-review/rounds/20260730_d7_s_r4_rerun_disposition/`) is to name the
first differing world array. The comparison is in flight: run `30516912923`
(`d7s-workers-2`, development topology, `--smoke --dev`, no population inference)
against the identical invocation run locally.

This note exists so the mechanism cannot be fitted to the answer afterwards. The
last round's one cheap success was writing a prediction down and letting a
measurement refute it; this repeats that deliberately. Pro's Challenge 6 forbids
freezing a cause before the digest comparison names the surface, so what follows is
a **prediction to be tested, not a conclusion**.

## The prediction

```text
first differing component (generation order)   user_positions
possibly also differing                        cluster_centers_history
predicted NOT differing                        user_pause_times
                                               user_cluster_assignments
                                               cluster_velocities
                                               cluster_waypoints
                                               cluster_pause_times
```

## Why, from source rather than from the data

**1. Five of the nine arrays are structurally incapable of diverging.**
`envs/pettingzoo/scenario_base.py:368-373` initializes `user_cluster_assignments`,
`cluster_velocities`, `cluster_waypoints`, `user_pause_times` and
`cluster_pause_times` to `np.zeros(...)`. The fingerprint is taken immediately
after construction and before any stepping, so at fingerprint time these are
zeros on every machine. Zeros cannot differ.

That leaves four candidates: `user_positions`, `user_velocities`,
`user_waypoints`, `cluster_centers_history` -- exactly the four that
`regenerate_user_world` re-derives from the registered seed.

**2. `user_positions` is generated through a LAPACK call.**
`_generate_forced_relay_cluster_positions` draws its cluster offsets with
`self.np_random.multivariate_normal(...)`, and it also sets
`self.cluster_centers_history = cluster_centers.copy()`. NumPy implements
`multivariate_normal` by factorizing the covariance matrix with an SVD, which is
LAPACK, not a pure RNG stream operation.

**3. This numpy's OpenBLAS dispatches kernels by CPU at runtime.** Measured from
`np.__config__` on the local interpreter, the same pinned `numpy==1.26.3` wheel the
runners install:

```text
blas name              openblas64
openblas configuration USE_64BITINT=1 DYNAMIC_ARCH=1 ... SKYLAKEX MAX_THREADS=2
```

`DYNAMIC_ARCH=1` means one wheel carries many CPU-specific kernels and selects
among them at import/run time from the detected CPU. So pinning the numpy version
pins the *code*, and pins nothing about *which kernel executes*. `ubuntu-latest`
is a heterogeneous fleet, which is how two runs with identical dependency locks
can land on different kernels.

Chain: different CPU -> different OpenBLAS SVD kernel -> different last bits from
the covariance factorization -> different `multivariate_normal` offsets ->
different `user_positions`, and `cluster_centers_history` differs when the changed
draw moves a cluster centre. `user_velocities` and `user_waypoints` are derived
downstream from positions, so they would differ as a *consequence*, which is
exactly why the localizer reports in generation order rather than alphabetically.

**4. It explains the 3-of-8 pattern.** A kernel difference only shows up when the
factorization of that particular covariance actually produces different bits, and
only some topologies' matrices will. A cause that predicted all eight would be the
wrong cause.

## What would refute this

- The first differing array is one of the five predicted-constant ones. Then the
  zeros assumption is wrong and something writes them before the fingerprint.
- The first differing array is `user_velocities` or `user_waypoints` with
  `user_positions` identical. Then the divergence is downstream of positions and
  the SVD story is not it.
- No component differs at all on this key set. That would be **uninformative,
  not exculpatory** -- the effect is known to hit only some topologies, and this
  run uses the development topology rather than an R4 one. A clean result here
  means "not localized yet", and the next step would be to run the comparison on
  R4 keys.
- The two machines turn out to have the same CPU model. Then the experiment did
  not test the hypothesis.

## What this does not claim

It does not claim the cause is established, and it does not license writing
"machine-dependent construction state" into any record as the reason. It also
does not bear on the repair choice: Pro selected complete-manifest persistence and
replay, which removes cross-machine regeneration from the result path **whatever**
the first differing array turns out to be. Localization tells us what to test the
repair against; it is not a precondition for the repair being right.

## RESULT, 2026-07-30: the prediction is REFUTED, and the mechanism is the opposite one

First cross-machine comparison with per-component digests: local probe (dev topology
20260725, 6 shared episode keys) against run `30516912923` arm `w1`.

```text
fingerprints differing            6 of 6
first differing component         user_velocities            5 keys
                                  user_cluster_assignments   1 key
earliest in generation order      user_velocities
```

**Both halves of the prediction are wrong.**

1. **`user_positions` is BIT-IDENTICAL across the platform boundary.** It comes
   before `user_velocities` in generation order, so had it differed it would have
   been named. The predicted chain -- `multivariate_normal` -> SVD -> OpenBLAS
   `DYNAMIC_ARCH` runtime kernel dispatch -> different positions -- **did not
   happen.** LAPACK is portable here.

2. **`user_cluster_assignments` differs on one key**, and it was on the list of five
   arrays I claimed "cannot differ, they are `np.zeros` at fingerprint time". It is
   written at `scenario_base.py:790` inside cluster generation, before the
   fingerprint is taken. The zeros claim was simply false for it.

## The mechanism that fits, from source

`_init_user_velocities`:

```python
speed = self.np_random.uniform(0, self.user_max_speed)
angle = self.np_random.uniform(0, 2 * np.pi)
self.user_velocities[i, 0] = speed * np.cos(angle)
self.user_velocities[i, 1] = speed * np.sin(angle)
```

**Scalar `np.cos` / `np.sin`.** Transcendental functions are not required to be
bit-identical between libm implementations, and MSVC's CRT and glibc are known to
differ in the last bits. That is a far more ordinary explanation than an SVD kernel,
and it matches the data exactly: the RNG stream is identical (positions prove it),
and only the array that passes its draws through trig diverges.

`user_cluster_assignments` is an integer array, so it cannot drift numerically -- but
it is assigned from float comparisons, and a tie or a near-tie can flip. That is a
plausible downstream consequence rather than an independent cause, and it is not
established.

## What this does and does not settle

**Does:** the SVD hypothesis is dead; the zeros-cannot-differ claim is dead;
`user_velocities` is the first differing array across a platform boundary, and scalar
trig is the leading mechanism for it.

**Does NOT:** this is the CONFOUNDED local-versus-cloud comparison. It cannot
establish the cause of the cloud-versus-cloud divergence -- 3 of 8 R4 topologies
between two `ubuntu-latest` runners with identical pins, where libm is presumably the
same glibc on both. Those may be two different mechanisms. The second cloud sample
(`d7s-workers-3`, run `30518707693`) is what tests that, and it is still running.

Pro's Challenge 6 still binds: nothing here is frozen as the cause.

## Why the prediction was worth writing down

It cost one file and it bought a refutation. Had the mechanism been reasoned out
after seeing `user_velocities`, "scalar trig is not portable" would have looked like
an insight rather than a correction, and the dead SVD hypothesis would have quietly
disappeared instead of being marked dead. The refutation list in the section above
named exactly this outcome -- "the first differing array is `user_velocities` ... then
the divergence is downstream of positions and the SVD story is not it."
