# G20 active-set-centered delayed-residual implementation plan

> Use `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work, workflow hashes and review stacks are disabled.

```text
last_nonformal=FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_G19
last_nonformal_result=NONFORMAL_NO_DELAYED_ACCESS_FAST_ANCHOR_G19
active_source=DELAYED_BATTERY_ROSTER_G18
source_gate=PASS_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18
active_implementation=ACTIVE_SET_CENTERED_DELAYED_RESIDUAL_G20_DERIVATION
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal_iteration=19_complete
iterations_remaining=8
formal_compute=not_scheduled_for_g19
algebra_status=ZERO_COMPUTE_DERIVATION_REQUIRED
screen_contract=none_until_g20_derivation
```

## Accepted active line

1. The exact TD(0), raw-sum, channel-normalized and actor/critic-isolated G18
   candidates are closed without retry or tuning. They remain only as frozen
   evidence and focused regression surfaces.
2. Formal G18 proves that the delayed battery source is learnable: every
   delayed-access, mechanism and replicate-stability threshold passed. It also
   proves that a shared actor update does not reliably preserve the accepted
   G17 immediate controller across fresh seeds.
3. G17 remains the accepted fast immediate-service algorithm. G18 does not
   relabel or weaken that result and does not advance to UAV.
4. The next derivation must isolate one new algorithmic degree of freedom: an
   explicit fast-policy anchor plus a zero-initialized delayed residual whose
   optimization cannot overwrite the fast path. It must remain environment
   neutral and may not read battery, demand phase or lifecycle role directly.
5. The G19 derivation now freezes that boundary. Implement one generic mean
   hook, an exactly zero residual, phase-specific parameter ownership and the
   parameter-space conflict projection. Then run the proof-sized tests and one
   bounded paired nonformal screen; no formal compute is scheduled.

## Prototype acceptance

- `ContinuousRosterPolicy` now exposes one action-mean hook; its base behavior
  is unchanged and existing G17/G18 shared tests pass.
- `anchored_residual_g19.py` contains no G17, G18 or UAV source import. It owns
  the zero residual, phase transition, source-neutral credit and projected SGD
  step only.
- Exact sampled, deterministic and teacher-replay equivalence holds at the
  zero-residual boundary. Both source paths retain exact replay and lifecycle
  behavior, and one update in each phase is finite.
- After delayed updates, every fast policy tensor including `log_std` remains
  bitwise unchanged; the residual output layer moves and every projected
  gradient has nonnegative fast-gradient dot product within `1e-7`.
- Eight G19-focused tests plus the retained G17/G18 shared proofs total 30
  passing tests on CPU with one thread.

The integrated G19 screen closed operationally and preserves every G17 gate,
but G18 remains at utility `0.66667` with zero spike service and zero gain over
the anchor. G19 is retired without tuning. The next action is a zero-compute
derivation of an active-set-centered residual that exposes per-step anonymous
redistribution directions before any implementation or compute.
