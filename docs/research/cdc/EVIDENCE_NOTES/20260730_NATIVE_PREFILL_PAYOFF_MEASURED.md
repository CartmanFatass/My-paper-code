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

No threshold, contract, population or result is touched by any of this. The
integration remains default-off and outside every R4 path.
