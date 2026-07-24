# G22 adaptive anchored delayed-residual implementation plan

> Use `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work, workflow hashes and review stacks are disabled.

```text
last_nonformal=UNCONSTRAINED_ANCHORED_DELAYED_RESIDUAL_G21
last_nonformal_result=NONFORMAL_NO_DELAYED_ACCESS_UNCONSTRAINED_RESIDUAL_G21
active_source=DELAYED_BATTERY_ROSTER_G18
source_gate=PASS_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18
active_implementation=ADAPTIVE_ANCHORED_DELAYED_RESIDUAL_G22_PROTOTYPE
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal_iteration=19_complete
iterations_remaining=8
formal_compute=not_scheduled_for_g22
algebra_status=DERIVATION_FROZEN_IMPLEMENTATION_PENDING
screen_contract=docs/research/designs/ADAPTIVE_ANCHORED_DELAYED_RESIDUAL_G22.md
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

The G20 derivation now freezes that single delta. Implement one optional
step-level mean-residual hook, active-only centering, residual-only successor
optimization and the focused invariants. Then run one bounded paired screen
from an integrated source; no formal compute is scheduled.

The G20 prototype is accepted for that screen. The optional hook is `None` on
every prior policy, while the G20 core computes one proposal tensor per step,
centers only active rows and adds it before the existing tanh-Gaussian path.
The G19 wrapper now accepts a policy class so G20 reuses the frozen-anchor
mechanics without a discarded initialization or extra RNG draws. Six focused
tests and the retained G17/G18/G19 proofs total 36 passing tests on CPU with one
thread. Zero-output sampled, deterministic and teacher replay are exact;
inactive rows are exact zero; centering is permutation equivariant and padding
independent; delayed updates leave the anchor bitwise unchanged. The only next
action is the already-frozen paired nonformal screen from an integrated commit.

That screen is now closed as
`NONFORMAL_NO_DELAYED_ACCESS_CENTERED_RESIDUAL_G20`. It is operationally valid,
keeps G17 above every gate and exercises a numerically centered residual, but
G18 gain and spike service remain zero. The exact G20 candidate is retired.

G21 changes one algorithmic axis: remove active-set centering and use the
ordinary source-neutral delayed residual without G19's gradient projection.
Keep SGD, successor credit, frozen anchor, budgets, thresholds and evaluation
unchanged with fresh seeds. Implement only the thin optimizer/runner boundary,
reuse existing trajectory and policy mechanics, and run the proof-sized tests
before one integrated paired nonformal screen.

The G21 prototype is accepted for that screen. It reuses the frozen-anchor
policy and adds a successor-only, unprojected SGD update; no centering or
immediate-gradient projection remains. Five focused tests prove exact
zero-output equivalence, available common-mode control, inactive exact zero,
source-pair replay, residual exercise, anchor identity and first-match order.
Together with retained G17/G18/G19 proofs, 35 tests pass on CPU with one thread.
The closed G20 module, runner, test and now-unused generic mean hook are removed
from the active line; their integrated commit remains the reproduction source.
The only next action is the frozen paired nonformal G21 screen.

That screen is now closed as
`NONFORMAL_NO_DELAYED_ACCESS_UNCONSTRAINED_RESIDUAL_G21`: G17 remains strong,
but G18 gains only `0.004` and spike utility remains zero despite exercised
common-mode residuals. The exact SGD candidate is retired.

G22 changes only the delayed residual optimizer to Adam with the same `1e-3`
learning rate and registered defaults. The policy, credit, fast anchor, critics,
budgets, gates and evaluation remain unchanged with fresh seeds. Mechanically
rename the active runner/test, prove exact residual-only optimizer ownership,
then run one integrated paired nonformal screen.
