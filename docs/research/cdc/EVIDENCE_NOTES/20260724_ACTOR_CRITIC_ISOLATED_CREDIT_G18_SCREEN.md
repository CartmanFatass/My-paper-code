# Actor/critic-isolated channel-credit G18 screen

Date: 2026-07-24

```text
source_commit=95c5d1266cb2ecc0e9de8993e8e60cc55e35ff5f
run=logs/nonformal_critic_isolated_credit_g18_20260724_95c5d12_pm1
formal=false
backend=cpu
torch=2.7.0+cpu
torch_threads=1
operational_valid=true
maximum_replay_error=0.0
branch=NONFORMAL_ACTOR_CRITIC_ISOLATED_CREDIT_PROMISING_G18
iteration_consumed=false
iterations_remaining=9
```

The isolated slow critic is the first G18 candidate to pass both frozen source
families:

```text
g17_iid_mean=0.9453568418
g17_heldout_mean=0.9251236627
g17_gain_mean=0.4040107742
g17_minimum_episode=0.8777376407
g17_effort_correlation=0.9584054023
g17_mix_correlation=0.9867246513
g17_effort_mae=0.0302234460
g17_mix_mae=0.0188922964
g18_utility_mean=0.9725569358
g18_gain_mean=0.2369539968
g18_minimum_spike_utility=0.9165745489
g18_minimum_rotating_effort_share=0.9128468315
```

All updates were finite, both source contracts closed, parameters moved and
every replay field had exact zero error. The contrast with the otherwise
unchanged shared-critic candidate supports value-gradient interference as the
decisive implementation mechanism at this source.

This is only a bounded screen. It licenses the frozen three-replicate formal
dual-source contract in `ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18.md`; it does
not itself establish a usable algorithm or any UAV result.
