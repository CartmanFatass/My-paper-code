# Unconstrained anchored delayed residual G21 derivation

Date: 2026-07-24

## Accepted evidence

G19 and G20 both preserve the frozen G17 actor exactly but fail to improve the
delayed battery source. G19 permits common-mode action residuals but removes
batch-global conflict through parameter projection. G20 removes that
projection but structurally deletes every active-set common-mode residual.
Because the two candidates constrain different axes, neither establishes that
an ordinary frozen-anchor residual lacks delayed access.

G20 is especially separating: its residual is nonzero, numerical centering is
closed, and G18 utility, gain and spike service remain unchanged. The next test
must restore common-mode freedom without simultaneously changing the residual
optimizer, credit estimator, budget or gates.

## Counterexamples

### CE-ZERO-MEAN-PRE-SQUASH-CANNOT-CHANGE-COMMON-EFFORT

If every active residual coordinate sums to zero, the residual cannot directly
raise or lower the active-set pre-squash action mean. A delayed solution may
need a simultaneous effort reduction during charging or increase during the
spike in addition to member redistribution. G17 behavioral gates, rather than
zero-sum algebra, are the correct protection for the immediate task.

### CE-G19-DOES-NOT-TEST-UNPROJECTED-COMMON-MODE

G19's common-mode head was subject to the batch-global immediate-gradient
projection on every delayed pass. Its failure therefore cannot be used as the
unprojected-control counterexample. G21 must remove both G19 projection and G20
centering while changing nothing else.

### CE-OPTIMIZER-CHANGE-CONFOUNDS-GEOMETRY

Moving directly to Adam could turn a geometry test into an optimizer test.
Unpreconditioned SGD is retained for one screen. Adaptive optimization is a
later discriminator only if unrestricted residual geometry still fails.

## Smallest new algorithm

`UNCONSTRAINED_ANCHORED_DELAYED_RESIDUAL_G21` reuses the G19 fast-trained and
frozen actor, exact-zero source-neutral residual head, state-only critics and
two-phase schedule. During the delayed phase it applies only the successor PPO
loss to residual parameters with SGD. There is no immediate-gradient
projection and no active-set centering. The residual may express both anonymous
member redistribution and common-mode action changes; the unchanged G17 gates
decide whether those changes preserve immediate service.

## Necessary invariants

1. Zero residual exactly reproduces sampled, deterministic and teacher-replay
   anchor execution.
2. Fast actor and exploration parameters remain bitwise fixed during delayed
   training.
3. Inactive actions and likelihood rows remain exact zero.
4. Only successor-value actor loss reaches residual parameters; state-only
   critic losses reach neither actor.
5. Residual features remain source-neutral and use no slot identity, future
   state or environment-specific field.
6. Replay, lifecycle and source controls retain their registered bounds.
7. G17 compatibility remains the first scientific gate before G18 access and
   mechanism gates.

## Cheapest separating action

Reuse the G19 policy and G20 successor-only update core with centering audit
disabled. Add only a thin G21 implementation/runner and proof-sized tests for
unprojected residual ownership, exact anchor identity and frozen precedence.
Use the G19/G20 budgets and thresholds with fresh seeds:

```text
g17_model=2819000
g17_train_ledger=2829000
g17_action=2839000
g17_evaluation_ledger=2849000
g17_evaluation_action=2859000
g18_model=2919000
g18_action=2939000
```

Passing the paired screen licenses a fresh formal executable definition.
Failure retires the exact unrestricted-SGD residual and makes optimizer/credit
the next question. No formal or UAV run is scheduled.

```text
next_boundary=UNCONSTRAINED_ANCHORED_DELAYED_RESIDUAL_G21_PROTOTYPE
formal_compute=not_scheduled
conclusion_bearing_iteration_cost=0
iterations_remaining=8
```
