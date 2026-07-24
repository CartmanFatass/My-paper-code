# G27 immediate-tangent full-actor bounded result

```text
status=COMPLETE
formal=false
iteration_consumed=false
accepted_source_commit=9a60621614c03f1f3bad9040360e0b2b20fdad33
accepted_run=logs/nonformal_immediate_tangent_full_actor_g27_20260724_9a60621_pm2
branch=NONFORMAL_NO_DELAYED_ACCESS_TANGENT_FULL_ACTOR_G27
iterations_remaining=8
```

## Evidence closure

The repaired CPU one-thread artifact is operationally valid. Replay error and
applied-gradient identity error are exact zero, lifecycle and optimizer
ownership pass, the delayed residual stays exact zero, and the minimum
post-projection inner product is `4.7303654e-13`. The largest representable
half-space correction is `3.7252903e-08`.

The first artifact at source `99730224a171db4ddd67f4528c98807d89994d97`
is retained only as an operational reproducer. Its float32 projection remnant
was `-1.645647e-6`, below the frozen `-1e-7` bound, so it selected INVALID and
cannot support a scientific conclusion.

## Registered result

G17 passes every first behavioral gate after the tangent phase: IID utility is
`0.9567011`, held-out utility `0.9507994`, minimum episode `0.9191451`, effort
and mix correlations `0.9878585`/`0.9933416`, and both mapping errors remain
below their ceilings.

G18 does not access the delayed source. Utility moves only from the fast anchor
`0.6415180` to `0.6666667`; gain is `0.0251487`, spike utility is exact zero,
and rotating effort share is `0.4935985`. The registered first-match branch is
therefore `NONFORMAL_NO_DELAYED_ACCESS_TANGENT_FULL_ACTOR_G27`.

## Scientific disposition

Full actor capacity is sufficient to retain G17 under strict immediate-tangent
protection, but requiring the successor gradient itself to be non-conflicting
removes the useful delayed update. G27 is closed without tuning, threshold,
budget, seed, optimizer or UAV rescue. It does not consume a conclusion-bearing
iteration and does not license formal compute.

The next smallest discriminator relaxes only the excessive algebraic
constraint: require the *combined* equal-weight actor gradient to remain an
immediate-loss descent direction. This permits successor conflict up to the
amount cancelled by the immediate gradient itself while preserving a direct
first-order compatibility guarantee.
