# Fast/slow separated-credit G18 bounded screen

Date: 2026-07-24

```text
source_commit=963ac812fe856d08c9865b04c4a4c7af03f1783a
run=logs/nonformal_fast_slow_separated_credit_g18_20260724_963ac81_pm1
formal=false
backend=cpu
torch=2.7.0+cpu
torch_threads=1
operational_valid=true
maximum_replay_error=0.0
branch=NONFORMAL_NO_G17_COMPATIBILITY_SEPARATED_CREDIT_G18
iteration_consumed=false
iterations_remaining=9
```

## Result

The frozen first-match branch rejects the candidate at G17 compatibility:

```text
g17_iid_mean=0.6288764992
g17_heldout_mean=0.6319945907
g17_gain_mean=0.1108817022
g17_minimum_episode=0.5400426948
g17_effort_correlation=-0.2371373388
g17_mix_correlation=0.0415913115
g17_effort_mae=0.1629728466
g17_mix_mae=0.1563781196
```

The candidate moved parameters, remained finite and learned a positive mean
gain, but it destroyed the already established conditional immediate-service
mapping. The exact sum of unscaled immediate and successor residuals is retired
without seed, exposure, threshold or optimizer rescue.

G18 is lower precedence and cannot relabel that decision. It independently
shows that the candidate did not acquire the delayed allocation mechanism:

```text
g18_utility_mean=0.8363923608
g18_minimum_slot_utility=0.8348188959
g18_gain_mean=0.1007894218
g18_minimum_spike_utility=0.5044566877
g18_minimum_rotating_effort_share=0.4338866365
```

The score is close to the frozen myopic comparator utility `0.8333333333`, and
the low-phase effort share did not move toward the announced rotating members.
Thus the positive gain is not evidence of delayed battery mediation.

## Smallest correction

The failure identifies channel-scale interference before it identifies a need
for more environment detail. The next prototype retains the same detached
immediate and successor residuals but normalizes each actor-advantage channel
separately before equal-weight loss composition. This preserves both channel
identities through the PPO objective and adds no environment field, horizon,
seed, budget or tunable mixing coefficient.

The next boundary is
`CHANNEL_NORMALIZED_SEPARATED_CREDIT_G18_ALGEBRA_PROTOTYPE`, followed only on
algebra acceptance by the same fixed dual-source screen. It is a new algorithm
candidate, not a rerun or rescue of the retired raw-sum candidate.
