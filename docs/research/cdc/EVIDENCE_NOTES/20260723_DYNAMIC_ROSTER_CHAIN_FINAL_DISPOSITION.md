# Dynamic-roster chain final disposition

Date: 2026-07-23

## Accepted algorithm test version

The accepted baseline is the G8 prefix-normalized direct recurrent open-roster
policy:

```text
algorithm=PREFIX_NORMALIZED_OPEN_ROSTER_G8
active_set_aggregation=sum
count_coordinate=log1p_active_count
actor_prefix=active_fraction_prefix
hidden_state=lifecycle_owned_per_member_recurrence
parameter_shape_independent_of_roster_capacity=true
```

G16 is the terminal deployment-mixture evidence package for this policy, not a
new trained model.

## Twelve-iteration evidence sequence

- G5 establishes a directly usable dynamic-roster MVP.
- G6 establishes zero-training count/time transport through N=16.
- G7 finds a valid failure above the original count-feature range.
- G8 repairs that failure with active-fraction action prefixes and retrains once.
- G9 establishes high-frequency membership churn.
- G10 composes scale and churn through N=40.
- G11 establishes exact slot-layout invariance.
- G12 extends zero-training transport through N=80.
- G13 replaces fixed schedules with episode-random processes.
- G14 establishes count-invisible atomic cohort replacement.
- G15 composes atomic identity replacement with large count shocks.
- G16 confirms a fresh-seed balanced deployment mixture of the three strongest
  supported process modes.

The final registered branch is `USABLE_DYNAMIC_ROSTER_DEPLOYMENT_G16`; all
formal evidence is CPU-only with one thread and the terminal G16 evaluation
uses zero optimizer steps.

## Claim boundary

Supported: one usable algorithm test version for runtime-variable team
membership and active count across the registered family through N=80.

Not supported: universal arbitrary-roster robustness, N>80, asynchronous skill
lifetime, intrinsic-reward benefit, sample-efficiency or performance advantage
over competing algorithms. These remain optional future research directions.

```text
grant_status=EXHAUSTED_COMPLETE
conclusion_bearing_iterations_consumed=17
iterations_remaining=0
successor_status=none_without_new_user_direction
```
