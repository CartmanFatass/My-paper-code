# G31 formal result and UAV charge-rotation realization plan

> Use `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work, workflow hashes and review stacks are disabled.

```text
last_nonformal=RETURN_TO_GO_DIRECTION_BALANCED_G31_BOUNDED_SCREEN
last_nonformal_result=NONFORMAL_RETURN_TO_GO_DIRECTION_BALANCED_PROMISING_G31
active_source=UAV_CHARGE_ROTATION_ROSTER_G2
source_gate=FROZEN_G2_CHARGE_ROTATION_IDENTIFICATION
active_implementation=UAV_CHARGE_ROTATION_ROSTER_G2_FORMAL_PRELAUNCH
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal_iteration=22_complete
iterations_remaining=5
formal_compute=G2_AUTHORIZED_AFTER_PM_ACCEPTANCE_PENDING_SOURCE_COMMIT
algebra_status=G31_PAIRED_TOY_USABLE_UAV_G1_SOURCE_NON_IDENTIFIABLE
screen_contract=docs/research/designs/RETURN_TO_GO_DIRECTION_BALANCED_G31.md
next_boundary=UAV_CHARGE_ROTATION_ROSTER_G2_FORMAL_ITERATION_23
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

The first integrated G26 artifact is not accepted scientifically: changing the
residual parameter count advanced the global RNG before credit-baseline
construction, and the resulting fast anchor differed from G25. The bounded
repair constructs the G25 reference from the same incoming RNG state, copies
every non-residual tensor, restores the exact G25 post-construction RNG state,
and proves both identities. Rerun once from a fresh root after focused tests;
the invalid artifact consumes no iteration and cannot select a branch.

The repaired G26 probe exactly pairs the G25 anchor but still closes as
`NO_POINTWISE_PREFIX_CONTEXTUAL_FIT_G26`: MSE `1.43119 -> 0.34146` misses both
gates, while closed-loop utility/spike reach only `0.92811`/`0.88163`. The
frozen-anchor additive residual family is retired without more inputs or fit.

G27 restores full actor capacity and changes one optimization rule relative to
the closed formal G18 path. After the fast phase, compute immediate and
successor actor gradients separately, project only a conflicting successor
gradient into the immediate tangent half-space, and apply their exact equal
average. Keep state-only critics separate and every residual exact zero.
Implement one thin optimizer module, rename the active runner/test, and close
actor inventory, projection algebra, replay/lifecycle and first-match proofs
before one paired nonformal screen. No formal or UAV run is scheduled.

The G27 implementation is accepted for that screen. The tangent phase owns the
complete environment-neutral actor and a separate Adam optimizer; the slow
value and two state-only baselines use their disjoint critic optimizer, while
the old core critic and delayed residual remain frozen. Six focused tests prove
the exact inventory, aligned/conflicting projection formula, exact applied
gradient identity, critic isolation, actor-only movement, zero residual,
G17/G18 replay and first-match precedence. Together with retained G17/G18/G19
proofs, 36 tests pass on CPU with one thread. The G26 module, runner, test and
now-unused routed-hook arguments are removed from the active line. The only
next action is the integrated paired G27 screen; formal and UAV compute remain
unscheduled unless its promising branch is selected.

The first integrated screen produced no admissible scientific branch because
float32 casting left the mathematically zero conflict-projection dot at
`-1.64565e-6`, below the frozen `-1e-7` runtime bound. Finite updates, replay,
lifecycle, optimizer ownership and zero residual all passed. Repair only the
CPU numerical realization: form the projection in float64, cast to actor dtype,
then use the minimum one-coordinate float-lattice correction if casting lands
outside the closed half-space. Keep the bound, gradient weights, budgets,
seeds, gates and branch order unchanged; add the exact reproducer and rerun the
same bounded screen from a fresh integrated source. The invalid artifact costs
zero conclusion-bearing iterations.

The fixed-seed 100-coordinate reproducer confirms that the old float32
realization leaves a negative dot below `-1e-7`, while the repaired projection
returns to the closed half-space with a positive, minimal lattice correction.
Seven focused and 37 combined G17/G18/G19/G27 tests pass on CPU with one thread.
The exact next action is one fresh integrated rerun; no gate or scientific
parameter changed.

The repaired G27 screen is operationally valid and closes as
`NONFORMAL_NO_DELAYED_ACCESS_TANGENT_FULL_ACTOR_G27`. G17 passes all gates, but
G18 gain is only `0.02515` and spike utility is zero. Strictly requiring the
successor gradient itself to be non-conflicting is therefore retired.

G28 changes only that excessive constraint. Preserve the full actor, equal
channel weights and all screen semantics, but allow successor conflict while
the equal combined gradient remains an immediate-loss descent direction. The
closed-form boundary has no tunable coefficient. Implement the projection,
rename the active runner/test, retain the accepted float-lattice realization,
and run proof-sized tests before one integrated bounded screen. No formal or
UAV compute is scheduled.

The G28 implementation is accepted for that screen. The active G27
module/runner/test were renamed instead of duplicated. Algebra tests prove that
tolerable successor conflict is unchanged, excess conflict reaches the exact
combined-descent boundary, and a fixed float32 counterexample receives only the
minimum representable closure. Actor/critic/residual ownership, G17/G18 replay,
zero residual and first-match precedence remain intact. Seven focused and 37
combined tests pass on CPU with one thread. The only next action is the fresh
integrated paired screen; formal and UAV compute remain unscheduled.

The first G28 screen terminated before producing `result.json`: one
high-dimensional actor update remained outside the closed half-space after the
single analytical float64 correction and one float32 `nextafter`. This is an
operational realization failure, not a scientific branch, and consumes no
iteration. Seed 73 with 1,000 coordinates reproduces the same two-step
undershoot. Keep the frozen zero boundary and equal channel weights; repeatedly
apply the exact float64 residual on the same maximum-magnitude immediate
coordinate, then walk back to the first closed float32 lattice point. Eight
focused and 38 combined tests now pass. Run the same bounded G28 screen once
from a fresh integrated source; no other restart, formal run or UAV promotion
is scheduled.

The repaired G28 screen is operationally valid and closes as
`NONFORMAL_NO_DELAYED_ACCESS_NET_DESCENT_G28`. G17 held-out utility remains
`0.95179`; G18 reaches `0.96328` utility, `0.37994` gain and `0.86963` rotating
share, but spike utility `0.88983` remains below the frozen `0.90` access floor.
The first-match result is not rescued by the stronger lower-precedence metrics.

G29 changes one geometric owner. Remove the raw-gradient projection, send the
clipped equal combined gradient through Adam once, and constrain only the
realized actor displacement against the immediate gradient. Non-conflicting
Adam steps remain bitwise ordinary Adam; conflicting parameter displacement is
projected to the closest tangent boundary with float64/float-lattice closure.
Adam moments record the unprojected combined gradient and advance exactly once,
while projected parameters plus those moments are the explicit new checkpoint
semantics. Rename the closed G28 active module/runner/test, add displacement and
optimizer-state proofs, then run one paired bounded screen. Formal and UAV
compute remain unscheduled.

Independently, the shared trainer no longer computes a no-grad replay and then
immediately repeats it for the first PPO pass before any mutation. G17, G18,
G19, G28 and UAV now reuse the first gradient-bearing replay for both audit and
first loss, invalidating it at the first optimizer step. Fifty-five focused
tests pass; a ten-pair alternating CPU benchmark reduces median G17 two-pass
update time from `1.11708s` to `0.89023s` (`20.3074%`) with exact metrics and
zero parameter difference. This is execution-only and changes no scientific
contract.

The G29 implementation is accepted for its paired screen. The closed G28
module, runner and test were renamed rather than retained as a parallel active
line. A momentum counterexample proves that a positive raw combined-gradient
dot can still produce a conflicting Adam displacement. The new helper advances
Adam exactly once, leaves non-conflicting parameters and complete optimizer
state bitwise identical to ordinary Adam, and moves only a conflicting realized
parameter displacement to the first closed float32 lattice point. Actor,
critic, residual and core-critic ownership remain disjoint; G17/G18 replay and
lifecycle behavior are unchanged. Eight focused and 55 combined tests pass on
CPU with one thread. The only next evidence action is one integrated bounded
G29 screen from a fresh source commit.

The first G29 attempt reached result aggregation but emitted no `result.json`:
the inherited G19 metric reducer still requires its internal
`minimum_projection_post_dot` input, while the G29 source row exposes only the
new realized-displacement name. This is an operational schema-adapter failure,
not a scientific branch, and consumes no iteration. Supply the legacy name only
in a temporary copy passed to the shared reducer, then delete the reducer's
legacy output before building the G29 artifact. Keep the G29 source rows,
external telemetry, gates and algorithm free of the old projection label. Add
one regression and rerun once from a fresh integrated source.

The repaired G29 screen is operationally valid and closes as
`NONFORMAL_NO_DELAYED_ACCESS_REALIZED_TANGENT_G29`. G17 remains strong, but G18
falls below its anchor (`0.51679` final, `-0.06654` gain, zero spike). The
realized constraint fires on 234/600 G18 actor passes and limits actor movement
to `0.08077`, so it is retired as more restrictive in practice than G28.

G30 returns to a pre-Adam algebraic guarantee while changing one different
axis: discard the two raw global gradient magnitudes and equally combine their
unit directions. The unit half-sum always has nonnegative raw immediate dot by
Cauchy--Schwarz and preserves the complete successor direction. Define exact
zero-channel branches, use float64 norms without epsilon, retain the existing
`0.5` gradient clip, and introduce no global rescale or projection. Rename the
closed G29 module/runner/test, prove direction/zero/opposite/Adam ownership and
run one paired bounded screen. Formal and UAV compute remain unscheduled.

The active-line G30 implementation is now PM-accepted. It replaces the retired
G29 module, runner and tests rather than retaining an adapter. Fourteen focused
checks close the algebraic edge cases, float32 near-opposite bound, ordinary
Adam state transition, ownership and first-match contract; the 48-test
G17/G18/G19/G30 shared-core set passes. The bounded paired screen is the next
action and consumes no conclusion-bearing iteration.

The bounded G30 screen is operationally valid and selects the sole promising
branch. G17 compatibility remains strong while G18 reaches `0.98515` utility,
`0.40181` anchor gain, `0.95544` spike utility and `0.95311` rotating share.
Freeze a three-replicate paired formal runner with fresh seeds, the same two
phase budgets and the inherited CI/first-match gates. First close a one-update
per phase nonformal path exercise and reject it under formal-required analysis;
then the integrated source may launch conclusion-bearing iteration 20.

The G30 formal runner is PM-accepted after 18 focused and 52 shared-core tests.
It binds zero/final checkpoints to phase counts, configuration, source and
replicate; closes exact training/evaluation inventories; recomputes the frozen
hierarchical intervals; and fails closed on token, checkpoint and cell tamper.
The next action is its bounded nonformal exercise from an integrated source.

The integrated formal-path exercise closes with the registered nonformal
branch, exact checkpoint/cell inventories, zero replay error and explicit
formal-required rejection. No result gate changed. G30 is prelaunch-ready for
one three-replicate conclusion-bearing CPU run under its frozen token.

Formal G30 is operationally valid and closes at the delayed-access branch. G17
compatibility, G18 total utility/gain, rotating mechanism and replicate utility
stability pass, but spike-utility CI95 lower bound is `0.87611`, below `0.90`.
Do not rerun or tune G30. The next zero-compute boundary isolates why broad
delayed utility is learned while load-bearing spike allocation remains
seed-unstable, then freezes at most one proof-sized G31 discriminator.

G31 freezes the smallest environment-neutral target correction. Keep G30's
actor geometry, but replace `gamma*V(s_(t+1))` in the successor actor/baseline
channel with the detached realized discounted future tail excluding `r_t`.
Retain the full-return slow critic, exact terminal zero, current active mask and
all paired screen budgets/gates. Implement a shared direction-update entrypoint,
prove tail algebra and run one fresh-seed nonformal screen only.

The G31 active implementation is PM-accepted after 20 focused checks including
the G30 refactor regression and 58 shared-core checks. Exact tail algebra,
mid-trajectory terminal reset, detached targets, unchanged checkpoint shape,
first-replay reuse, actor/critic/residual ownership and first-match precedence
close. The next action is the one frozen bounded paired screen.

The G31 screen is operationally valid and selects
`NONFORMAL_RETURN_TO_GO_DIRECTION_BALANCED_PROMISING_G31`. It preserves G17
while reaching G18 utility `0.994996`, spike utility `0.997803` and rotating
share `0.998296`, with exact replay, composition and terminal-tail closure.
Freeze a three-replicate formal runner with fresh seeds and the unchanged G30
budgets, bootstrap, behavioral gates and first-match order. Replace the closed
G30 formal runner/test in the active line, close a one-update nonformal path
exercise, then launch conclusion-bearing iteration 21.

The G31 formal runner is PM-accepted without duplicating the closed G30 active
line. It binds fresh G31 identity, seeds, return-to-go exposure, checkpoints,
exact evaluation inventory and all inherited first-match gates; it additionally
fails closed on non-finite/zero future-tail support or any nonzero terminal
tail. Twelve focused and 60 relevant shared checks pass on CPU with one thread.
The next action is one integrated nonformal formal-path exercise.

The integrated G31 formal-path exercise completes train/evaluate/analyze with
two exact training rows, seven evaluation cells, four checkpoints, zero replay
and terminal-tail error, and the registered nonformal branch. Formal-required
analysis rejects it. The next action is one frozen three-replicate formal CPU
iteration 21; no parameter, seed, threshold, budget or source selection remains
open.

Formal G31 is operationally valid and selects
`USABLE_RETURN_TO_GO_DIRECTION_BALANCED_G31`. All G17 compatibility and G18
delayed access/mechanism/stability gates pass across fresh seeds, including a
spike-utility LCB of `0.95969`. Close the paired toy package. The next boundary
is a proof-sized UAV promotion definition that preserves the exact G31
environment-neutral credit and direction geometry; no heavy formal UAV run is
scheduled until its bounded path passes.

The UAV promotion audit selects an earlier prerequisite: close the already
frozen G1 source predicate before writing a G31-UAV adapter. Read-only Scouts
found no control-ledger or paired-execution defect, but the representative
no-reallocation controller leaves at most `0.032166` headroom, well below the
frozen `0.10` source margin. The learned G1 modes also exposed one operational
defect: both routing labels used the same anonymous-content order. FIXED now
uses active-first physical-slot order while OPEN retains anonymous-content
order; parameters, observations, reward, source, budget, seeds and gates are
unchanged. Forty-one focused core/runner checks pass. Launch one fresh
control-first formal iteration 22; if source identification fails, accept the
registered second branch with zero learned training and do not use G31 to
rescue it.

Formal UAV G1 closes exactly at that registered second branch. The complete
three-replicate control screen has constructive `J_event` CI95
`[0.84811,0.85662,0.86524]` and constructive-minus-no-reallocation CI95
`[-0.11816,-0.10589,-0.09209]`; both source predicates fail. The validator and
independent first-match recomputation pass with 192 chunks, 6,144 rows, zero
training rows and zero checkpoints. Close G1 without rescue. The valid
non-`INVALID` terminal satisfies the frozen prerequisite for UAV charge-rotation
G2. Implement that design as the next active line, retain source-first pruning,
and require focused tests plus one bounded nonformal CPU exercise before any
formal G2 launch.

The G2 executable realization is now PM-accepted. The active core implements
the frozen IID/LOW_ENERGY/SYNCHRONIZED_PRESSURE ledgers, dynamic
ACTIVE/CHARGE_ABSENT/TERMINAL roster, anonymous current-only actor and full
current critic, matched FIXED/OPEN policy arms, replay/GAE/PPO, constructive
and no-proactive source controls, source-first pruning, seven-branch analysis,
and identity-bound resumable journals. RESET and every REJOIN retain an
immutable projection audit; initial pressure is taken only from RESET, every
audit must pass, and existing absent station commitments survive replanning.
Parse-truncated authority records are recoverable, while valid-but-wrong or
tampered evidence remains fail-closed.

Twenty-two core and twenty runner tests pass together as 42 focused CPU
one-thread checks. A fresh bounded run at
`logs/nonformal_uav_charge_rotation_g2_cpu_20260724_pm2` completed
train/evaluate/analyze/validate as
`NONFORMAL_UAV_CHARGE_ROTATION_G2_EXERCISE_COMPLETE`, with
`operational_valid=true`, `formal=false` and `conclusion_bearing=false`. The
closed G1 runtime and tests are deleted rather than retained behind adapters.
This consumes zero conclusion-bearing iterations. After exact-path Git
integration, launch the frozen formal CPU iteration 23 without changing any
source, budget, seed, threshold or result precedence.
