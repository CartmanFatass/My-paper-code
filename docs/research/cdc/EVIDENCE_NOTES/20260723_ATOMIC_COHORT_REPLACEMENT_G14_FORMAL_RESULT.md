# Atomic cohort-replacement G14 formal result

Date: 2026-07-23

The exact source `b709fd5fc9cb423110d5edc24067e0030e05cbab`
completed at `logs/formal_atomic_replacement_g14_cpu_20260723_b709fd5_r1`.

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_g8_replicates=3
optimizer_steps=0
evaluation_cells=18
utility_values=576
source_control_rows=96
operational_valid=true
operational_errors=[]
branch=ROBUST_ATOMIC_COHORT_REPLACEMENT_G14
```

All 96 source rows are unique and contain six exact atomic transactions. Every
transaction has positive, equal-size terminal and fresh-join cohorts, no
temporary/rejoin operation, and a constant active-count schedule. Constructive
utility, wave demand, terminal persistence and cold-start hidden state close.
All three G8 checkpoint copies and 18 behavior cells remain exact with zero
optimizer steps and 576 complete values.

```text
atomic_moderate_deterministic_utility_ci95=[0.923095703125,0.95166015625,1.0]
atomic_wide_deterministic_utility_ci95=[0.92578125,0.9525405421401515,0.9999556107954546]
atomic_ultra_deterministic_utility_ci95=[0.92919921875,0.9541193627781976,0.9998092602095928]
atomic_ultra_replicate_means=[0.92919921875,0.9998092602095928,0.933349609375]
atomic_ultra_min_replicate_mean=0.92919921875
atomic_ultra_stochastic_mean=0.8951629449054547
```

Independent first-match evaluation reproduced
`ROBUST_ATOMIC_COHORT_REPLACEMENT_G14`. The current policy handles large
same-transaction identity turnover even when log-count and active-count signals
do not change.

The result does not cover an atomic transaction where terminal and join cohort
sizes differ, creating an abrupt count shock at the same moment as lifecycle
replacement. That composition is the next closest dynamic-roster boundary.

```text
next_boundary=ATOMIC_COUNT_SHOCK_G15_DERIVATION
conclusion_bearing_iteration=15
iterations_remaining_after_run=2
```
