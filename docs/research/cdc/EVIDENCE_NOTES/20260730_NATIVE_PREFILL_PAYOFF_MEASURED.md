# The native prefill buys 1.04x, not 1.6x, and the projection was invalid arithmetic

Date: 2026-07-30
Subject: `envs/pettingzoo/scenario_base.py::_prefill_access_path_loss_natively`

## Measured

Interleaved off/on/off/on, 5 samples each, quiet box, `--dev` topology 20260725,
40 steps per sample after one untimed warm-up step. The fast path was asserted
active before timing (`240` matrix entries prefilled), so this is not a benchmark
of a backend that silently declined.

```text
flag OFF   96.82 ms/step   spread +/-6.8%   best 91.18
flag ON    92.76 ms/step   spread +/-4.9%   best 88.75

speedup mean 1.044x
speedup best 1.027x
```

**The gain is inside the off-side noise band.** Treat it as "no measurable
improvement" rather than as 4%.

## The projection was wrong, and wrong in a specific way

`CURRENT_WORK` carried this claim:

> path loss is 17.5% of a 0.0937 s/step scenario7 step, but the CACHE machinery
> around it is another 24%, so one native call per step retires both.

Both numbers were **cumulative** profiler shares, and cumulative time
double-counts nested calls. Adding them was invalid. A self-time (`tottime`)
profile over 20 steps, total 63.4 ms/step:

```text
                                              tottime   cumtime   calls
{method 'reduce' of 'numpy.ufunc'}              0.150             147145
_compute_distance                               0.122     0.311    68192
_compute_air_to_ground_path_loss                0.058     0.116     7298
_current_step_communication_cache               0.049     0.302    21049
_compute_uav_to_user_sinr                       0.048     0.296     4897
_is_uav_unavailable                             0.034     0.090    31014
_communication_config_signature                 0.033     0.054    16269
_compute_air_to_air_path_loss                   0.025     0.092    13867
                                       (total profiled 1.268 s)
```

Two corrections fall out:

1. **The kernel's target is ~9% of a step, not 17.5%.**
   `_compute_air_to_ground_path_loss` is `0.116 / 1.268` cumulative = 9.2%, and
   only 4.6% of self time.
2. **The prefill does not retire the cache machinery at all.** The 24% is
   `_current_step_communication_cache`, which is the cache *validity check* --
   `_communication_config_signature` plus `np.array_equal` over positions -- and it
   runs on **every lookup regardless**. The prefill converts misses into hits; it
   does not remove the lookup. Claiming one native call retires both was false.

So the addressable share was ~9% and the ceiling was ~1.10x. Measured 1.04x, the
gap being the prefill's own cost: one native call, array conversions, and 240 dict
writes per step.

## Same error family as this round's refuted claims

A real measurement (17.5% cumulative) reported as supporting a broader claim (40%
retired) than its scope allows. Identical shape to reading
`rejoin_events = 0` as "the branch never executed". The fix is the same discipline:
check what the number covers before building on it -- and for profiler output
specifically, **never add two cumulative shares.**

## Disposition of the integration

**Keep it, default off, and stop citing a payoff.** It is bit-exact (flag-on and
flag-off produce identical SINR, connections and serving assignment over real
steps), it is off by default, no production path calls it, and the oracle behind it
still holds at max_ulp 0. It costs nothing to leave in place and it is the wiring a
future batched or fully-native step would build on.

What it is **not** is a speedup worth reporting. Any claim that the native kernel
accelerates scenario 7 must be re-earned against a larger native surface.

## Where the time actually is, if acceleration is revisited

By self time, the real targets are:

- **`_compute_distance` -- 68,192 calls over 20 steps (3,410 per step), 0.122 s
  self / 0.311 s cumulative.** The single biggest identifiable consumer.
- **The cache validity machinery -- `_current_step_communication_cache` 21,049
  calls (1,052 per step) at 0.302 s cumulative, with
  `_communication_config_signature` rebuilt 16,269 times (813 per step).** The
  check is re-derived per lookup rather than invalidated on write.
- `_is_uav_unavailable`, 31,014 calls (1,551 per step).

These are call-count problems, not arithmetic problems, so the payoff route is
fewer crossings of the Python boundary -- a dirty-flag cache validity check, or one
native call that computes the whole SINR matrix rather than one path-loss matrix.
Neither is attempted here, and neither is claimed.

## ADDENDUM, same day: the shim gives back what the kernel saves

`scenario_base.py:2781-2784`, inside the prefill:

```python
geometry = uav_cpp_backend.step_geometry_batch(...)   # one native call, whole matrix
access = np.asarray(geometry.access_path_loss)[0]
store = cache["user_path_loss"]
for i in range(access.shape[0]):
    row = access[i]
    for j in range(row.shape[0]):
        store[(i, j)] = float(row[j])                 # a float(), a tuple key, a dict insert
```

The native call returns a matrix and the shim immediately marshals it back into a
per-element Python dict, with an iteration count equal to the loop it replaced. The
mature backend this kernel came from is fast because it crosses the boundary once
per step and keeps arrays as arrays; the variant implemented here is the one that
violates both. That is a defect in the consumer, not in the kernel.

Arithmetic check, so the point is not overstated: `_compute_air_to_ground_path_loss`
costs ~15.9 us per call and 365 calls/step = 5.8 ms, while 240 dict inserts cost
well under 0.1 ms. The shim does **not** consume the whole saving -- ~9% was
available and ~4% arrived. So the shim is part of the gap, not all of it, and the
bigger part remains that only 9% was ever addressable.

## The real target, resolved to its callers

`_current_step_communication_cache` runs **1,028 times per step**, but the 240 calls
from `_compute_sinr` are already short-circuited by `_channel_update_cache_active`.
The **788 that run the full check** are:

```text
_get_link_capacity   (scenario_base.py:4357)   534 per step
_cached_link_sinr    (scenario_base.py:2826)   254 per step
                                              ---
                                              788 per step
```

and that matches `_communication_config_signature` at **789 per step** exactly --
each full check rebuilds a 13-field tuple, including a generator over `mcs_table`,
and runs four `np.array_equal` calls.

**This is the dominant cost, and it is larger than the path loss the kernel
replaces.** `_get_link_capacity` alone has nine call sites across the routing code,
each inside a loop, so threading `step_cache` through is invasive.

## Why the obvious fix is NOT attempted here

The tempting change is to stamp the cache with a per-step counter and compare
integers instead of arrays -- exactly what `_channel_update_cache_active` already
does for the channel-update window. It would remove nearly all of the 788 full
checks.

It is not attempted because it converts a guard that *verifies* inputs are unchanged
into one that *assumes* it, and correctness then depends on nothing mutating
positions, unavailability or config between the cache's creation and its last use
**within** a step. That ordering has not been traced, and this session has already
produced three claims that were true of a narrower scope than they were asserted
over. Tracing every mutation site is the prerequisite, and it is the same shape of
work as the "identify every writer" step the provenance ruling ordered.

Recorded so the next attempt starts from the caller table above rather than from a
guess about where the time is.

No threshold, contract, population or result is touched by any of this. The
integration remains default-off and outside every R4 path.
