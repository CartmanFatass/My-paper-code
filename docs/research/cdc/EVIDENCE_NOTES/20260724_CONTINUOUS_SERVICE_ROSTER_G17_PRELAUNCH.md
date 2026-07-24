# Continuous service roster G17 prelaunch

Date: 2026-07-24

## Accepted source and contract

The formal runner and frozen evidence contract were integrated and pushed at
source commit `8efedec5a23465fa9d701198dd0095f4730ad0f8`. The active algorithm is
`CURRENT_OBSERVATION_RESIDUAL_ONE_STEP_CREDIT_G17`; all checkpoints are fresh,
credit uses `gamma=0`, and the current-observation residual is enabled.

This is a CPU-only, one-thread toy-source boundary. It imports no spatial, G8
or UAV checkpoint and changes no completed G0-G16 result.

## Proof-sized acceptance

```text
focused_g17_plus_shared_uav_policy_tests=22_passed
bounded_run=logs/nonformal_continuous_service_roster_g17_formal_path_20260724_8efedec_pm1
train_exit=0
evaluate_exit=0
analyze_exit=0
train_status=COMPLETE
evaluate_status=COMPLETE
analysis_status=COMPLETE
formal=false
operational_valid=true
branch=NONFORMAL_CONTINUOUS_SERVICE_G17_EXERCISE_COMPLETE
maximum_replay_error=0.0
lifecycle_contract_valid=true
source_schedules_exact=true
constructive_access_valid=true
formal_validator_rejection=ValueError_formal_analysis_requires_formal_artifacts
```

The exercise used one update only, so its low utility and conditional mapping
are deliberately non-conclusion-bearing. Its role is to prove artifact closure,
not to predict the formal result.

A broader legacy UAV runner suite returned 45 passes and one failure where a
duplicate-checkpoint negative reached a different fail-closed error earlier
than its expected message. Neither affected runner/test is modified by G17;
the actual shared policy surface passed. This message-order issue is recorded
as non-blocking and is not converted into unrelated repair work.

## Launch disposition

The frozen train/evaluate/analyze path is operationally executable. Formal
Iteration 18 may run under the standing ten-iteration CPU grant with token
`AUTHORIZE_CONTINUOUS_SERVICE_ROSTER_G17_FORMAL_CPU_V1`. Only a complete valid
formal analysis consumes an iteration. No UAV promotion is implied.
