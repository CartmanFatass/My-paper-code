# Dynamic-roster deployment mixture G16 formal result

Date: 2026-07-23

The exact source `1745ab9c155e7a58ba0689380f3a77866b3503b5` completed at
`logs/formal_deployment_mixture_g16_cpu_20260723_1745ab9_r1`.

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_g8_replicates=3
optimizer_steps=0
evaluation_cells=18
utility_values=648
source_control_rows=108
operational_valid=true
operational_errors=[]
branch=USABLE_DYNAMIC_ROSTER_DEPLOYMENT_G16
```

All 108 source profiles are unique. Within each of the three scale domains,
there are exactly 12 serial-random, 12 equal-atomic and 12 shock-atomic
profiles. Mode-specific event counts and operation/count invariants close with
zero mismatches. Constructive utility, exact roster schedules, wave demand,
lifecycle state and all four membership operation types close. Every imported
checkpoint and all 18 evaluation models remain exactly unchanged.

```text
deployment_moderate_deterministic_utility_ci95=[0.9253537984006734,0.9520621491424793,0.9998430656934308]
deployment_wide_deterministic_utility_ci95=[0.9231770833333334,0.9513158464536385,0.9995638588053599]
deployment_ultra_deterministic_utility_ci95=[0.9251302083333334,0.9525272346732843,0.9997258012420754]
deployment_ultra_replicate_means=[0.9251302083333334,0.9997258012420753,0.9327256944444444]
deployment_ultra_min_replicate_mean=0.9251302083333334
deployment_ultra_stochastic_mean=0.8928563785629661
```

Independent first-match evaluation reproduced
`USABLE_DYNAMIC_ROSTER_DEPLOYMENT_G16`. The registered prefix-normalized direct
recurrent policy is therefore accepted as a usable dynamic-agent-count baseline
for the tested family through N=80.

The result does not establish arbitrary roster processes, N above 80,
asynchronous skill lifetime, intrinsic-reward benefit or comparative advantage.
Those are new research grants rather than rescues or implied successors.

```text
conclusion_bearing_iteration=17
iterations_remaining_after_run=0
chain_status=TWELVE_ITERATION_DYNAMIC_ROSTER_CHAIN_COMPLETE
```
