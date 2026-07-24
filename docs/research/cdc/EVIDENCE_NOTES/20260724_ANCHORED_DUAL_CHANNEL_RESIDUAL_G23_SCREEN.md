# Anchored dual-channel residual G23 screen

Date: 2026-07-24

The exact integrated source
`b1efaf3e831ba2ae0c2aaab30f8eff97589fd42f` completed the bounded screen at
`logs/nonformal_anchored_dual_channel_residual_g23_20260724_b1efaf3_pm1`.

```text
formal=false
backend=cpu
torch=2.7.0+cpu
torch_threads=1
status=COMPLETE
operational_valid=true
maximum_replay_error=0.0
maximum_anchor_difference=0.0
maximum_channel_loss_identity_error=1.1641532182693481e-10
source_controls_valid=true
branch=NONFORMAL_NO_DELAYED_ACCESS_DUAL_CHANNEL_RESIDUAL_G23
wall_seconds=479.8357199
```

Project Manager independently closed source/runtime identity, exact channel
weights, loss identity, replay, anchor identity, source/lifecycle controls and
the first-match branch.

## Evidence

Every G17 compatibility gate passes:

```text
g17_anchor_iid_utility=0.9448683479
g17_final_iid_utility=0.9516865538
g17_anchor_heldout_utility=0.9366705623
g17_final_heldout_utility=0.9398994887
g17_gain_over_zero=0.3459580906
g17_minimum_episode=0.9136435199
g17_effort_correlation=0.9823891876
g17_mix_correlation=0.9925808767
g17_effort_mae=0.0225434805
g17_mix_mae=0.0142752100
```

Dual-channel residual credit nearly closes G18:

```text
g18_anchor_utility=0.7002783284
g18_final_utility=0.9511069287
g18_gain_over_anchor=0.2508286003
g18_spike_utility=0.8533207861
g18_rotating_effort_share=0.8499289361
g18_minimum_step_utility=0.4810895622
g18_residual_output_max_abs=0.2816999555
```

Utility, gain and rotating-mechanism gates pass, but the registered spike floor
is `0.90`. Lower-precedence successes cannot relabel that failure.

## Disposition

G23 supports dual-channel credit as a useful correction but closes the exact
local residual representation as insufficient for spike access. It is retired
without threshold, weight, optimizer, budget or seed rescue and does not
advance to formal compute or UAV.

The fast actor's recurrent candidate is frozen for immediate service. G23's
residual reads that candidate, the autoregressive prefix and raw observation;
it reaches high average delayed utility but may inherit a representation
bottleneck at the roster transition. The smallest next discriminator replaces
only the residual representation with a direct active-set contextual proposal,
without centering, while retaining G23 credit and optimization.

```text
conclusion_bearing_iteration_cost=0
iterations_remaining=8
next_boundary=CONTEXTUAL_DUAL_CHANNEL_RESIDUAL_G24_DERIVATION
```
