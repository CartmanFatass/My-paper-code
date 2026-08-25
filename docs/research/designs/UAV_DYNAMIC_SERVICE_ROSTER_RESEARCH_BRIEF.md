# UAV dynamic-service-roster research brief

Date: 2026-07-23

Status: external scientific review pending

Conclusion-bearing iteration cost: 0

## User intent

Use the Scenario-7 UAV communication setting to create multiple compact
algorithm tests for:

1. a localized and temporary surge in communication demand that requires
   temporary coverage reallocation;
2. charging rotation that changes how many UAVs are available for service; and
3. robustness when a small number of UAVs temporarily detach from the team or
   fail, followed by either re-entry or terminal loss.

The user authorizes ten automatic conclusion-bearing iterations, including
routine implementation, CPU-only formal execution, result reporting, Git and
successor selection. The Project Manager must write Chinese reports
`ITERATION_18.md` through at most `ITERATION_27.md` as iterations are consumed.

## Verified repository baseline

### Scenario-7 physical source

`Config("S7-S1")` currently fixes:

```text
physical_uavs=8
users=30
ground_base_stations=1
episode_steps=500
per_user_qos_rate_mbps=1.0
qos_target_ratio=0.90
battery_enabled=false
charging_enabled=false
temporary_failure_enabled=false
```

S7-S2/S3 enable 160 Wh batteries, two charging stations with one simultaneous
slot each, and charging. S7-S4 additionally enables temporary failures with a
20--60 step duration while requiring at least six active UAVs.

The current environment keeps all physical UAVs in `possible_agents`.
`uav_charging` and `uav_failed` are observable masks/state fields, and the
adapter retains fixed `(n_uavs, ...)` tensors. There is no independently
registered transient demand-burst process.

### Accepted algorithmic starting point

The previous synthetic chain accepted `PREFIX_NORMALIZED_OPEN_ROSTER_G8` as a
usable test version for runtime-variable anonymous membership through the
registered family up to active N=80. It uses active-set summation, a
`log1p(active_count)` coordinate, an active-fraction actor prefix and
lifecycle-owned recurrence. That result does not establish UAV integration,
sample efficiency, comparative advantage or robustness outside its synthetic
sources.

## Required abstraction

The new benchmark must not equate these two concepts without evidence:

- **physical fleet:** UAV slots/assets that exist in the episode; and
- **service-active roster:** UAV lifecycles currently allowed and capable of
  contributing communication service actions.

The review must decide when return-to-charge, queueing, charging, temporary
failure and temporary detachment cause service LEAVE/REJOIN, which state is
frozen or continues during absence, and which facts are available to actor and
critic. A fixed-agent recurrent policy with correct availability masks is the
strongest simple reduction until a dynamic-roster treatment is shown to add
something identifiable.

## Candidate isolated sources

Names below describe user-requested families, not frozen scientific contracts.

### `UAV_BURST_COVERAGE`

A spatially localized subset of users experiences a temporary QoS-demand
surge. The policy must reallocate coverage while preserving ordinary service
and recover after the burst. The onset signal, affected-user observability,
duration, magnitude and held-out shifts are protected scientific choices.

### `UAV_CHARGE_ROTATION_ROSTER`

Battery and charger capacity force UAVs to leave service, queue or charge, and
later rejoin. The contract must distinguish physical motion/energy dynamics
from service membership and prevent future battery, queue or schedule leakage.

### `UAV_TEMPORARY_LOSS_ROBUSTNESS`

A small subset temporarily detaches or fails. The contract must distinguish
temporary absence from terminal loss, preserve anonymous lifecycle ownership,
and measure degradation and recovery without exposing future failures.

### Composed source

Composition of the three disturbances is a later candidate only. It cannot
replace isolated identifiability checks or be used to rescue a failed isolated
source.

## Protected scientific questions for external review

The review must determine:

1. the exact service-active membership predicate and lifecycle semantics;
2. minimal causal source laws for burst, charging rotation and temporary loss;
3. actor/critic observability needed for a fair, non-oracular task;
4. the smallest source to implement first and the evidence ladder thereafter;
5. primary estimands and matched fixed-agent/recurrent reductions;
6. access, feasibility, recovery, energy-safety and held-out admission gates;
7. mutually exclusive first-match conclusions and their claim limits; and
8. which remaining numeric/engineering choices are implementation-only.

No task-specific field, target, success predicate or external reward may enter
the environment-agnostic intrinsic reward. The existing Scenario-7 physical
and safety semantics should be reused where scientifically compatible, but the
closed synthetic results may not be relabelled as UAV evidence.

## Agile scope guard

Only choices capable of changing the task distribution, information set,
reward/utility, estimand, support predicate, confidence statement, result
branch or held-out claim require external scientific selection. File layout,
serialization, telemetry formatting and proof-sized test realization are PM
engineering choices. The review should provide a minimal executable scientific
contract, not a compatibility specification or exhaustive product schema.
