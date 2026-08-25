# Fast-policy-anchored delayed residual G19 screen

Date: 2026-07-24

The exact integrated source
`639a8ddd951376cb4a9497aae205a794c4b977ea` completed the bounded screen at
`logs/nonformal_fast_policy_anchored_residual_g19_20260724_639a8dd_pm1`.

```text
formal=false
backend=cpu
torch=2.7.0+cpu
torch_threads=1
status=COMPLETE
operational_valid=true
maximum_replay_error=0.0
maximum_anchor_difference=0.0
minimum_projection_post_dot=-8.754432201385498e-08
source_controls_valid=true
branch=NONFORMAL_NO_DELAYED_ACCESS_FAST_ANCHOR_G19
wall_seconds=492.0600896
```

Project Manager independently closed source/runtime identity, exact replay,
anchor immutability, source controls and the frozen first-match branch.

## Evidence

The fast anchor and projected residual preserve G17:

```text
g17_anchor_iid_utility=0.9563726731
g17_final_iid_utility=0.9571082567
g17_anchor_heldout_utility=0.9447274378
g17_final_heldout_utility=0.9464109197
g17_gain_over_zero=0.5308483107
g17_minimum_episode=0.9208685443
g17_effort_correlation=0.9793949566
g17_mix_correlation=0.9893718117
g17_effort_mae=0.0180450667
g17_mix_mae=0.0175204718
```

The delayed phase does not acquire G18:

```text
g18_anchor_utility=0.6666666667
g18_final_utility=0.6666666667
g18_gain_over_anchor=0.0
g18_spike_utility=0.0
g18_rotating_effort_share=0.4757144811
g18_minimum_step_utility=0.0
```

The residual output layer moved to maximum absolute value `0.0415042`, so this
is not an unexercised zero-gradient path. The G18 anchor exhausts the service
available for the four-step spike, and the projected residual neither shifts
enough low-phase effort toward soon-charging members nor restores later
service. The global residual-parameter projection encountered conflict on 322
of 600 delayed PPO passes.

## Disposition

G19 confirms one retained lemma: a frozen fast path plus exact-zero residual can
preserve the accepted immediate controller without any fast-parameter drift.
It rejects the stronger claim that a single global parameter-space tangent is
sufficient for delayed member-level redistribution. The projection protects a
batch-level PPO objective, but it does not expose the per-step anonymous
redistribution directions that keep current aggregate service fixed.

The exact candidate is retired without optimizer, learning-rate, budget, seed,
projection or threshold tuning. It consumes no conclusion-bearing iteration
and does not advance to formal compute or UAV.

The smallest new discriminator is
`ACTIVE_SET_CENTERED_DELAYED_RESIDUAL_G20_DERIVATION`: retain the frozen fast
anchor but replace global gradient projection with an active-set-centered
residual whose action-coordinate sum is exactly zero at every step. That
structurally exposes member redistribution while preserving the unweighted
aggregate action mean. G17 absolute gates remain first because weighted service
need not be invariant to such redistribution.

```text
conclusion_bearing_iteration_cost=0
iterations_remaining=8
next_boundary=ACTIVE_SET_CENTERED_DELAYED_RESIDUAL_G20_DERIVATION
```
