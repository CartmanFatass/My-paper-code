# Step 2: every writer and random source for the diverging array

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
| `_initialize_user_waypoints_rpgm` | `user_waypoints`, `user_velocities` (overwrites) | `np_random.random`, `np_random.uniform` | `np.linalg.norm` -> `sqrt` |

## The single non-portable operation

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

`user_cluster_assignments` is an `int` array written at line 790 from float
comparisons, so it cannot drift numerically but a near-tie can flip. That remains a
plausible downstream consequence, not an established one.

## Consequence for the repair choice, which is the useful part

The ruling left two routes live. This finding separates them sharply.

**Route A -- persist and replay the complete manifest (selected).** Generation
happens once, on one machine, and every formal episode loads those bytes. Trig
portability stops mattering entirely, because the trig is never re-executed. **Step
2's finding does not threaten Route A; it explains why Route A was the right
selection.**

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
