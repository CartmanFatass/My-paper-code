# Unconstrained anchored delayed residual G21 screen

Date: 2026-07-24

The exact integrated source
`6db3a29b71e1ad2ab583930fdab5c0b38c80b5ad` completed the bounded screen at
`logs/nonformal_unconstrained_anchored_residual_g21_20260724_6db3a29_pm1`.

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
branch=NONFORMAL_NO_DELAYED_ACCESS_UNCONSTRAINED_RESIDUAL_G21
wall_seconds=472.5730666
```

Project Manager independently closed source/runtime identity, exact replay,
anchor immutability, lifecycle/source controls and first-match recomputation.

## Evidence

The unrestricted residual preserves every G17 gate:

```text
g17_anchor_iid_utility=0.9551750402
g17_final_iid_utility=0.9547477800
g17_anchor_heldout_utility=0.9526466023
g17_final_heldout_utility=0.9525348427
g17_gain_over_zero=0.4504753645
g17_minimum_episode=0.9363541103
g17_effort_correlation=0.9803443244
g17_mix_correlation=0.9935389034
g17_effort_mae=0.0196435911
g17_mix_mae=0.0145530100
```

Common-mode freedom produces only a negligible G18 change:

```text
g18_anchor_utility=0.5793338691
g18_final_utility=0.5833333333
g18_gain_over_anchor=0.0039994642
g18_spike_utility=0.0
g18_rotating_effort_share=0.4945366841
g18_minimum_step_utility=0.0
g18_residual_output_max_abs=0.0131500429
```

The residual is exercised and can express common-mode action changes, so the
failure is not zero-gradient, centering, projection or anchor mutation.

## Disposition

G21 closes the geometry discriminator: an unprojected, unrestricted residual
trained with unpreconditioned SGD still does not acquire delayed access. The
exact candidate is retired without learning-rate, budget, seed or threshold
tuning and does not advance to formal compute or UAV.

The successful actor/critic-isolated G18 path used Adam at the same registered
learning rate. The smallest next discriminator changes only the residual
optimizer from SGD to Adam while keeping the G21 policy, successor credit,
anchor, sources, budgets, thresholds and first-match order unchanged.

```text
conclusion_bearing_iteration_cost=0
iterations_remaining=8
next_boundary=ADAPTIVE_ANCHORED_DELAYED_RESIDUAL_G22_DERIVATION
```
