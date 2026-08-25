# G18 delayed battery roster information-gate evidence

Date: 2026-07-24

The fresh toy gate in `DELAYED_BATTERY_ROSTER_G18.md` passed all four focused
tests on the registered CPU interpreter. It contains no training or random
draws and consumes no conclusion-bearing iteration.

```text
branch=PASS_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18
constructive_utilities=[1.0,1.0,1.0]
myopic_utilities=[0.8333333333,0.8333333333,0.8333333333]
minimum_constructive_minus_myopic=0.1666666667
immediate_service_equal=true
next_persistent_battery_delta=0.25
natural_utility=1.0
intervened_utility=0.9583333333
intervened_future_service_deficit=0.5
slot_permutation_invariant=true
roster_sizes=[4,4,4,4,4,4,2,2,2,2,4,4]
formal=false
iteration_consumed=false
```

This is stronger than a “battery diversity exists” observation: an exact
same-service sequence intervention changes a persisted next-state component
and later external service under the same continuation. The equal-demand
myopic controller is a simpler explanation that fails specifically because it
ignores announced lifecycle rotation.

No claim is made about learned access, PPO, UAV transport, station scheduling
or long-horizon robustness. The next admissible evidence action is the bounded
`FAST_SLOW_SEPARATED_CREDIT_G18_ALGEBRA_PROTOTYPE`.
