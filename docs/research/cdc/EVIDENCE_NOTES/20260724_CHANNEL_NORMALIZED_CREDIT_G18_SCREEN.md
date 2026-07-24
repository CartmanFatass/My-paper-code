# Channel-normalized separated-credit G18 screen

Date: 2026-07-24

```text
source_commit=f704d4d9a7410b367271b9afeee864cad8f639fe
run=logs/nonformal_channel_normalized_credit_g18_20260724_f704d4d_pm1
formal=false
backend=cpu
torch=2.7.0+cpu
torch_threads=1
operational_valid=true
maximum_replay_error=0.0
branch=NONFORMAL_NO_G17_COMPATIBILITY_CHANNEL_NORMALIZED_G18
iteration_consumed=false
iterations_remaining=9
```

Independent channel normalization materially improved the paired result over
the raw-sum candidate:

```text
g17_heldout_mean=0.7417511859
g17_gain_mean=0.2206382974
g17_effort_correlation=0.3697880598
g17_mix_correlation=0.8340003329
g17_effort_mae=0.1083222998
g17_mix_mae=0.0905667029
g18_utility_mean=0.8441312388
g18_minimum_spike_utility=0.5276296344
g18_minimum_rotating_effort_share=0.4585884280
```

This supports channel-scale interference as one contributor, but the frozen
first-match branch still rejects G17 compatibility. G18 remains close to the
myopic source baseline and does not learn rotation-directed effort. The exact
channel-normalized shared-critic candidate is retired without tuning.

The remaining smallest implementation-level confound is value-gradient
sharing: the slow discounted-return critic currently backpropagates through the
same member/context encoders as the immediate actor. The next candidate gives
the slow critic a state-only parameter block and freezes the unused core critic,
while leaving actor heads, credit channels, sources, seeds, budgets and gates
unchanged. This tests representation interference rather than a new source or
more compute.
