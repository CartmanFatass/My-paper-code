# Continuous-roster native-six G42 formal result (mechanical evidence)

```text
status=FORMAL_COMPLETE
operational_valid=true
scientific_disposition=EXTERNAL_PRO_PENDING
iteration_cost_pending_external_pro=true
source_commit=a6c3c2971ee74e76a453995c3a7c12627bb8f02c
aligned_source_commit=6b8ea82d8fdbc76c14a414ff2b042a126f945dfb
alignment_stage_commit=309858dca06af66f13857f94773bcef37527d821
formal_run=logs/formal_continuous_roster_native_six_g31_direction_balance_attribution_g42_cpu_20260727_a6c3c29_r1
registered_authorization_token=CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_FORMAL_AUTHORIZATION_V1
registered_branch=EXTERNAL_PRO_PENDING
```

The fresh formal train, evaluate and analyze commands all exited zero. The
three required manifests are present and report `status=COMPLETE`,
`formal=true`, and the exact execution source commit. The analysis manifest
reports `operational_valid=true` with no operational errors.

The manifests record the required CPU-only C++ backend
`ContinuousRosterToyBatch_CPU_CPP`, with `required=true` and
`python_fallback=false`, torch `2.7.0+cpu`, and one torch thread. The frozen
inventory is three replicates, two arms, 100 branch updates per arm, two PPO
passes, 230400 training transitions, 165888 evaluation transitions, 396288
total real transitions, 1200 optimizer steps, 72 evaluation cells, 48
episodes per cell, and 10000 bootstrap resamples. No intrinsic K search or
hypothetical transitions are recorded. Checkpoint selection is final-only.

This note records transport and runtime facts only. It does not interpret the
scientific metrics or consume the valid iteration; External Pro disposition is
required before CDC, ledger, portfolio, or successor-state changes.

## External Pro disposition (mechanically recorded)

The exact archived response records `valid_result_disposition=CONTINUE`,
`conclusion_bearing_iterations_consumed=32`, `iterations_remaining=5`, and
the next scheduled action
`CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_DESIGN_ASSERTION_AUDIT`.
The exact raw response and transport intake are in the round paths named in
`CURRENT_WORK.md`.
