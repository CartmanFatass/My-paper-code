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
