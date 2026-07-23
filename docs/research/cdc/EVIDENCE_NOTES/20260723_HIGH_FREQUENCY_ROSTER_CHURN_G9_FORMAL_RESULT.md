# High-frequency roster churn G9 formal result

Date: 2026-07-23

## Evidence closure

The exact committed source
`ff7461fd2b0f3cfb7ad13a5f6f2730eb6bac3d99` completed the registered CPU-only
pipeline at
`logs/formal_high_frequency_churn_g9_cpu_20260723_ff7461f_r1`.

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_g8_replicates=3
optimizer_steps=0
evaluation_cells=18
evaluation_episodes_per_cell=128
utility_values=2304
operational_valid=true
operational_errors=[]
branch=ROBUST_HIGH_FREQUENCY_CHURN_G9
```

All imported checkpoint copies were bitwise exact. Every evaluation cell left
the model unchanged, all constructive/source/lifecycle controls passed, and the
serialized cell means were independently reproduced. The Project Manager
reapplied the frozen first-match order and obtained the reported branch.

## Registered metrics

```text
repeated_rejoin_deterministic_utility_ci95=[0.93096923828125,0.95562744140625,1.0]
load_proximal_deterministic_utility_ci95=[0.929443359375,0.9545491536458334,1.0]
mixed_churn_deterministic_utility_ci95=[0.929931640625,0.9543050130208334,1.0]
mixed_churn_replicate_means=[0.929931640625,1.0,0.9329833984375]
mixed_churn_min_replicate_mean=0.929931640625
mixed_churn_stochastic_mean=0.9099933159413526
```

## Scientific disposition

The frozen G8 policy remains usable under eight membership edits, repeated
leave/rejoin cycles, genuine joins, terminal leaves and edits at short-wave
boundaries for the registered N<=16 profiles. G8 and G9 are both closed
successes; neither is rerun or retuned.

This does not establish that count-scale transport through N=40 and
high-frequency churn compose in the same episode. The smallest next separating
action freezes the same G8 finals and evaluates that cross-product with zero
optimizer steps.

```text
next_boundary=SCALE_CHURN_COMPOSITION_G10_DERIVATION
conclusion_bearing_iteration=10
iterations_remaining_after_run=7
```
