# Actor/critic-isolated channel credit G18 formal result

Date: 2026-07-24

The exact source `3bf6a2efa6b18219448147abe55683181582a4de`
completed at
`logs/formal_critic_isolated_channel_credit_g18_cpu_20260724_3bf6a2e_r1`.

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
replicates=3
g17_updates_per_replicate=100
g18_updates_per_replicate=300
environments_per_update=8
ppo_passes=2
checkpoint_references=12/12_present
training_source_results=6
evaluation_cells=21
g17_evaluation_cells=15
g18_evaluation_cells=6
maximum_replay_error=0.0
lifecycle_contracts_exact=true
source_controls_valid=true
operational_valid=true
operational_errors=[]
branch=NO_G17_COMPATIBILITY_CRITIC_ISOLATED_G18
wall_seconds=611.0372916
```

The Project Manager independently closed source, algorithm, runtime and formal
identity across all three artifacts, checked every checkpoint reference and
the exact six-source-result/21-cell inventory, verified finite updates,
lifecycle schedules and both source controls, and recomputed the frozen
first-match branch from the recorded metrics. The recomputed branch exactly
matches the analyzer.

## Registered evidence

```text
g17_iid_utility_ci95=[0.8812917574808976,0.9127691902557385,0.9298359068296792]
g17_heldout_utility_ci95=[0.8702532855621111,0.903785594367426,0.9231117381312345]
g17_gain_ci95=[0.2679349005405369,0.48644528832409467,0.6474909372602162]
g17_minimum_episode=0.7775857223021645
g17_minimum_effort_correlation=0.8428963697794755
g17_minimum_mix_correlation=0.9345449178977188
g17_maximum_effort_mae=0.057457305107770175
g17_maximum_mix_mae=0.04352848184741257
g18_utility_ci95=[0.9880695493408926,0.9925694558079596,0.9957698753310574]
g18_gain_ci95=[0.20736764316205625,0.23294120209222324,0.2542207492409674]
g18_spike_utility_ci95=[0.9642086480226781,0.9777083674238788,0.9872763525280688]
g18_rotating_effort_share_ci95=[0.9624205843137186,0.9765774358028041,0.9878195576953781]
g18_minimum_replicate_utility=0.9880081771148576
```

The first-match G17 compatibility gate fails independently on IID and held-out
utility lower bounds, minimum episode utility, minimum effort correlation and
maximum effort MAE. Positive G17 gain and the later G18 gates cannot relabel
that result.

The lower-precedence G18 evidence is nevertheless highly informative: all
registered delayed-access, sequence-mechanism and replicate-stability
thresholds would pass. Thus actor/slow-critic isolation is sufficient to learn
the delayed battery-roster mechanism, but the shared actor update is not a
stable dual-source algorithm because it damages the already accepted G17
immediate controller on fresh seeds.

## Smallest scientific update

The exact G18 package is closed without rerun, seed selection, budget increase,
threshold change or result rescue. It does not advance to UAV.

The next zero-compute boundary is
`FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_G19_DERIVATION`: preserve the accepted
G17 immediate policy as an explicit fast anchor and ask whether a
zero-initialized delayed residual can add successor-state control without
allowing slow credit to overwrite immediate behavior. This is a new algorithm
family, not a tuned retry of G18.

```text
conclusion_bearing_iteration=19
toy_first_chain_iterations_consumed=2
iterations_remaining_after_run=8
next_boundary=FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_G19_DERIVATION
```
