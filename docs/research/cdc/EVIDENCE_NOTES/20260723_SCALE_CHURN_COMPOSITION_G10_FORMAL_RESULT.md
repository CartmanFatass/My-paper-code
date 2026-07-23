# Scale-by-churn composition G10 formal result

Date: 2026-07-23

The exact source `e66a202673ea91711d9d122d1807e9597e3dba43`
completed at `logs/formal_scale_churn_g10_cpu_20260723_e66a202_r1`.

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_g8_replicates=3
optimizer_steps=0
evaluation_cells=18
utility_values=2304
operational_valid=true
operational_errors=[]
branch=ROBUST_SCALE_CHURN_COMPOSITION_G10
```

All checkpoints, cells, serialized means, source schedules, wave requirements
and lifecycle controls closed exactly. Reapplication of the frozen first-match
order reproduced the reported branch.

```text
moderate_scale_churn_ci95=[0.92962646484375,0.9544881184895834,1.0]
far_scale_churn_ci95=[0.924560546875,0.95159912109375,1.0]
mixed_churn_ci95=[0.92724609375,0.9527860201322116,0.9994103064903846]
mixed_replicate_means=[0.92724609375,0.9994103064903846,0.93170166015625]
mixed_min_replicate_mean=0.92724609375
mixed_stochastic_mean=0.8963305038060897
```

The same frozen policy is usable when active counts through 40 and eight
membership edits occur together. This closes `CE-SEPARATE-MARGINAL-ROBUSTNESS`
for the registered cross-product; it does not establish arbitrary scale or
arbitrary event schedules.

The smallest next structural counterexample is slot-layout dependence: dense
low-numbered keys and capacity close to active N could conceal a fixed-layout
policy despite shared parameters. Test paired sparse/permuted lifecycle keys and
larger padding with the frozen checkpoints before increasing N again.

```text
next_boundary=SLOT_LAYOUT_INVARIANCE_G11_DERIVATION
conclusion_bearing_iteration=11
iterations_remaining_after_run=6
```
