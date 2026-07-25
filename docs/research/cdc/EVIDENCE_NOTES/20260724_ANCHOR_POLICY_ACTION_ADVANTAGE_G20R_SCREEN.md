# Anchor-policy action advantage G20R — bounded screen

Date: 2026-07-24

```text
algorithm=ANCHOR_POLICY_ACTION_ADVANTAGE_G20R
design=docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R.md
run=logs/nonformal_anchor_action_advantage_g20r_20260724_e6390fe_pm1
source_commit=e6390fe3d97ed90b7d64ce902776aa9e70a16e82
branch=NONFORMAL_NON_IDENTIFIED_ACTION_CRITIC_G20R
operational_valid=true
formal=false
iteration_consumed=false
wall_seconds=340.0
```

First match was branch 2, the identification branch added on Pro's instruction
so that a critic which never learned action sensitivity could not be reported as
behavioural absence of delayed access. It fired. **This screen therefore
licenses no update to P2.**

## What the run does establish

**The zero fixed point is gone.** This is the direct behavioural confirmation of
the repair, against the failure that retired the previous package:

| | residual output layer, max abs | optimizer steps |
|---|---|---|
| G20, retired rule | `0.0` — provably, forever | any |
| G20R, g17 | `0.129744` | 600 |
| G20R, g18 | `0.422483` | 1400 |

**The package is operationally clean.** `maximum_replay_error = 0.0`,
`maximum_anchor_difference = 0.0` — the fast anchor survives the delayed phase
bitwise, exactly as the design requires, while the residual moves.

## What fired the branch

The floor is `spread ≥ 0.01 × slow_return_std`, where the spread is the mean
across active tokens of `Q_j`'s variation over the `K = 8` resampled anchor
actions.

| source | spread | floor | |
|---|---|---|---|
| g17 | `0.005004` | `0.094316` | **fail**, short by ~19× |
| g18 | `0.042009` | `0.013658` | pass |

The critic identified action dependence on the **delayed** source and not on the
**immediate** one.

## The floor itself is suspect — Project Manager finding, not a result

`slow_return_std` is `9.431579` on g17 and `1.365788` on g18. That quantity
measures how much the realized return varies across *states*; it says nothing
about how much a single member's action moves it. Normalizing an
action-sensitivity floor by total return variance therefore conflates two
different failures:

- the critic genuinely cannot identify action dependence; and
- the source simply has large state variance relative to any one action's
  marginal effect.

On g17 the second is sufficient to fail the floor regardless of the first. The
threshold as registered cannot distinguish them, which is precisely the
separation the branch exists to provide.

This is a defect in a threshold **I** chose, and the pre-freeze design check
should have caught it. Question 4 of that check asks whether any result branch
can fire for a non-scientific reason; it found and fixed an ordering defect in
the inherited branches, and did not then turn the same question on the new
branch's own threshold. Recorded so the check's blind spot is visible rather
than inferred.

## Reachable-but-not-reached readings, recorded and not claimed

First-match precedence means these did not fire and are **not** results. They are
written down only so that a later round is not re-run to discover them, and they
must not be cited as evidence for or against P2.

- Every G17 compatibility threshold would have passed: iid `0.950439`, held-out
  `0.944830`, gain `0.442770`, minimum episode `0.911817`, effort correlation
  `0.973218`, mix correlation `0.991315`, effort MAE `0.021979`, mix MAE
  `0.015775`. The anchor-relative action credit did not damage the accepted fast
  controller.
- G18 behaviour moved the wrong way: final utility `0.352932` against an anchor
  of `0.666667`, gain `-0.313735`, spike utility `0.0`, rotating-member effort
  share `0.014493` — and this on the source where the critic *did* clear the
  identification floor.

The second is the more interesting one and the reason a threshold repair alone
is not obviously sufficient.

## Source controls

Both passed. G17: all schedules exact, constructive access valid, minimum step
utility `0.99999993`. G18: `PASS_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18`,
immediate service equal, constructive minimum `1.0` against myopic maximum
`0.833333`, slot-permutation invariant.

## Disposition

- No P2 update. No formal contract. No same-package retry and no hyperparameter
  sweep — the design forbids both, and neither would be legitimate on a fired
  identification branch.
- The registered identification floor is retired as a measurement: under the
  result-interpretation table this is *"the estimand cannot identify the target
  proposition"*, which retires **that estimand or measurement** and nothing
  else.
- Thresholds are protected semantics, so redefining the floor is a scientific
  decision rather than a local repair. The next action is a bounded review round
  carrying: the confirmed fixed-point repair, the identification asymmetry, the
  mis-normalized floor, and the un-fired G18 behavioural reading that a repaired
  floor would expose.

Zero compute beyond the 340-second screen. No iteration consumed.
