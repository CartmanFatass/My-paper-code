# G26 prefix-contextual residual expressivity implementation plan

> Use `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work, workflow hashes and review stacks are disabled.

```text
last_nonformal=FROZEN_ANCHOR_LOCAL_RESIDUAL_EXPRESSIVITY_G25
last_nonformal_result=NO_POINTWISE_LOCAL_RESIDUAL_FIT_G25
active_source=DELAYED_BATTERY_ROSTER_G18
source_gate=PASS_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18
active_implementation=PREFIX_CONTEXTUAL_RESIDUAL_EXPRESSIVITY_G26_BOUNDED_PROBE
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal_iteration=19_complete
iterations_remaining=8
formal_compute=not_scheduled_for_g26
algebra_status=PROTOTYPE_ACCEPTED_BOUNDED_PROBE_NEXT
screen_contract=docs/research/designs/PREFIX_CONTEXTUAL_RESIDUAL_EXPRESSIVITY_G26.md
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

The G22 prototype is accepted for that screen. The active G21 runner/test were
renamed rather than duplicated, and the only algorithmic edit is the delayed
residual optimizer constructor. Six focused tests close Adam defaults, fresh
state, exact residual-only ownership, zero-output/common-mode policy behavior,
replay, anchor identity and precedence; 36 focused-plus-retained tests pass on
CPU with one thread. The only next action is the frozen paired screen from an
integrated commit.

That screen is now closed as
`NONFORMAL_NO_DELAYED_ACCESS_ADAPTIVE_RESIDUAL_G22`. Adam strongly exercises
the residual but collapses G18 utility to `0.01025`; G17 and the frozen anchor
remain valid. Optimizer conditioning is therefore closed without a sweep.

G23 changes only the residual actor objective to the exact equal average of
independently normalized immediate and successor PPO channels. Adam remains
residual-only; the fast anchor, critics, budgets, gates and evaluation are
unchanged with fresh seeds. Replace the active optimizer function, rename the
runner/test, prove channel weights and gradient ownership, then run one paired
nonformal screen.

The G23 prototype is accepted for that screen. The active module, runner and
test were renamed rather than duplicated. The delayed residual loss records and
checks the exact equal average of separately normalized immediate and successor
channels; Adam remains residual-only and delayed entropy remains zero. Six
focused and 36 focused-plus-retained tests close loss identity, optimizer and
gradient ownership, zero-output/common-mode behavior, replay, anchor identity
and precedence on CPU with one thread. The only next action is the integrated
paired screen.

That screen is now closed as
`NONFORMAL_NO_DELAYED_ACCESS_DUAL_CHANNEL_RESIDUAL_G23`. G17 passes and G18
utility, gain and rotating share pass, but spike utility `0.85332` misses the
frozen `0.90` floor. The exact local residual is retired without rescue.

G24 changes only residual representation: compute an unrestricted proposal
directly from actor-side member encoding, active-set context, current hidden
state and observation. Dual-channel Adam, frozen fast actor, budgets, gates and
evaluation remain unchanged with fresh seeds. Reintroduce the proven optional
step hook, use the injectable anchor core, rename the active module/runner/test,
and close permutation/padding/inactive plus retained loss/ownership proofs
before one paired screen.

The G24 prototype is accepted for that screen. The prior proven step-residual
hook is restored with `None` as the base path; the G24 policy computes an
unrestricted actor-contextual proposal and masks inactive rows exactly. Seven
focused tests close zero-output equivalence, common-mode freedom,
permutation/padding error at most `1e-7`, inactive exact zero, dual-channel loss,
residual-only Adam, replay and anchor identity. Together with retained proofs,
37 tests pass on CPU with one thread. The only next action is the integrated
paired screen.

That screen is now closed as
`NONFORMAL_NO_DELAYED_ACCESS_CONTEXTUAL_RESIDUAL_G24`. It is operationally
valid and preserves G17, but G18 returns to utility `0.58333`, gain `0.06322`
and zero spike service. This is a strict regression from G23, so direct
actor-set contextual widening is retired without rescue.

G25 is a diagnostic-only expressivity gate on the better G23 local residual.
Reuse the unchanged G18 fast-anchor phase, build the exact 36-row constructive
dataset, optimize only the local residual for the frozen 200-step active-action
MSE fit, and separately evaluate deterministic closed-loop realization. Add
one focused runner test covering dataset semantics, residual-only ownership,
bitwise anchor preservation and first-match precedence. Remove the closed G24
module/runner/test and its now-unused generic contextual hook in the same
accepted implementation boundary. One integrated bounded CPU probe follows;
no formal iteration or UAV run is scheduled.

The G25 implementation is accepted for that one probe. The runner keeps the
constructive teacher diagnostic-only, reuses the source-neutral local residual,
and exposes no formal mode. Four focused tests close all 36 source rows,
inactive targets/actions, residual-only Adam ownership, residual movement,
bitwise frozen state and first-match precedence. Together with retained
G17/G18/G19 proofs, 25 tests pass on CPU with one thread. G24's module, runner,
test and contextual hook are deleted from the active line. The only next
action is the integrated bounded G25 diagnostic.

That diagnostic is now closed as `NO_POINTWISE_LOCAL_RESIDUAL_FIT_G25`. It is
operationally valid, but MSE `1.43119 -> 0.37358` misses both frozen gates and
closed-loop utility falls below the anchor. The local residual receives no
retry, extra steps, optimizer change or threshold rescue.

G26 changes one representation axis. Add a routed residual hook that combines
G24's direct actor-set context with G23's live autoregressive prefix, while
retaining G25's exact fast anchor, dataset, optimizer, fit budget, seeds and
gates. Rename the active diagnostic runner/test rather than retain duplicate
execution lines. Prove zero-output equivalence, live-prefix sensitivity,
permutation/padding/inactive behavior, residual-only ownership and precedence
before one paired bounded CPU diagnostic. No PPO or formal run is scheduled.

The G26 prototype is accepted for the paired probe. The source-neutral routed
head reads direct member/set/hidden fields plus the live prefix, while the base
hook ignores those extra arguments. Nine focused tests close exact zero-output
execution, independent context/prefix sensitivity, permutation/padding within
`1e-7`, inactive exact zero, residual-only mutation, bitwise anchor identity,
dataset semantics and precedence. With retained G17/G18/G19 proofs, 30 tests
pass on CPU with one thread. The only next action is the integrated paired G26
diagnostic; no delayed PPO or formal compute is scheduled.
