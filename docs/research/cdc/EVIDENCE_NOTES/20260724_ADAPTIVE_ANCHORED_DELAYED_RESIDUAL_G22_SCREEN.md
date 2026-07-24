# Adaptive anchored delayed residual G22 screen

Date: 2026-07-24

The exact integrated source
`6b3b493d83d22a73329cc8fb37770e232c95133d` completed the bounded screen at
`logs/nonformal_adaptive_anchored_residual_g22_20260724_6b3b493_pm1`.

```text
formal=false
backend=cpu
torch=2.7.0+cpu
torch_threads=1
status=COMPLETE
operational_valid=true
maximum_replay_error=0.0
maximum_anchor_difference=0.0
source_controls_valid=true
branch=NONFORMAL_NO_DELAYED_ACCESS_ADAPTIVE_RESIDUAL_G22
wall_seconds=446.8377021
```

Project Manager independently closed source/runtime identity, exact replay,
anchor identity, optimizer configuration, lifecycle/source controls and the
first-match branch.

## Evidence

G17 remains above every compatibility gate:

```text
g17_anchor_iid_utility=0.9573066871
g17_final_iid_utility=0.9517216847
g17_anchor_heldout_utility=0.9477585054
g17_final_heldout_utility=0.9451925081
g17_gain_over_zero=0.3550060528
g17_minimum_episode=0.9191107390
g17_effort_correlation=0.9842192504
g17_mix_correlation=0.9927491252
g17_effort_mae=0.0175106552
g17_mix_mae=0.0185490026
```

Adam strongly moves the G18 residual but collapses service:

```text
g18_anchor_utility=0.6666666667
g18_final_utility=0.0102457996
g18_gain_over_anchor=-0.6564208671
g18_spike_utility=0.0053555481
g18_rotating_effort_share=0.4038051302
g18_minimum_step_utility=0.0052261800
g18_residual_output_max_abs=0.1618446410
```

This is not under-optimization: adaptive residual updates amplify a direction
that is adverse to both current and delayed service while the fast anchor stays
bitwise unchanged.

## Disposition

G22 rejects optimizer conditioning as the sufficient correction. Together with
G21, it shows that successor-only residual credit is either too weak under SGD
or destructive under Adam. No learning-rate, beta, budget, seed or threshold
sweep is admissible. The exact candidate is retired without formal/UAV
promotion.

The smallest next correction restores the successful G18 actor structure:
independently normalize immediate and successor advantages and average their
PPO losses, but apply that dual-channel objective only to the residual while
keeping the fast actor frozen.

```text
conclusion_bearing_iteration_cost=0
iterations_remaining=8
next_boundary=ANCHORED_DUAL_CHANNEL_RESIDUAL_G23_DERIVATION
```
