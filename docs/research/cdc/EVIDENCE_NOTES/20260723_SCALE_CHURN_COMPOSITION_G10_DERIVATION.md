# Scale-by-churn composition G10 derivation

Date: 2026-07-23

## Starting evidence

Formal G8 supports the prefix-normalized policy through active count 40 under
three membership edits. Formal G9 separately supports the same frozen
checkpoints under eight edits through active count 16. Neither result licenses
the conjunction.

`CE-SEPARATE-MARGINAL-ROBUSTNESS` allows the policy to pass each one-factor
stress while failing their cross-product. Large rosters amplify the
autoregressive allocation sequence; frequent leave/rejoin/join operations also
change the prefix and recurrent-state layout. Their errors can interact even
when each marginal evaluation succeeds.

## Smallest separating action

Freeze the same three G8 final checkpoints and perform zero optimizer steps.
Keep Generic-SHORT, horizon, waves, reward, observations, policy, count
coordinate and thresholds unchanged. Evaluate exactly three eight-edit
profiles:

1. moderate scale churn, active count ranging from 12 to 24;
2. far scale churn, active count ranging from 16 to 40;
3. oscillating mixed churn, repeatedly moving between 12 and 40.

All event schedules retain exact lifecycle semantics and a constructive
utility-one controller. The action is conclusion-bearing only after the frozen
formal inventory closes.

## Interpretation boundary

Success supports composition only for the registered count/event profiles.
Failure selects the first failed count/churn domain and motivates either a
training-distribution correction or a representation correction; it does not
relabel G8 or G9. Asynchronous skill lifetime remains frozen.

```text
next_boundary=SCALE_CHURN_COMPOSITION_G10_EXECUTABLE_DEFINITION
training_operation=none_frozen_g8_checkpoint_import
conclusion_bearing_iteration=11
iterations_remaining_before_run=7
```
