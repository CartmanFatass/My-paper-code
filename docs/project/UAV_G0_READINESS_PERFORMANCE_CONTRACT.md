# UAV G0 Readiness Performance Contract

```text
document_kind=execution_readiness_performance_contract
request_id=UAV_G0_READINESS_PERFORMANCE_CONTRACT
selected_option=A
baseline_candidate_commit=379726e325236a02c3a45bf7049bedaaa90d4e31
scientific_contract_stage_commit=8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc
scientific_contract_disposition=G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=READY_FOR_CODE_CONTRACT
bounded_exercise_timeout_seconds=300
bounded_exercise_success_duration_seconds=<300
timeout_revision=forbidden
other_phase_timeout_values=unchanged
outer_run_timeout=sum_of_six_phase_timeouts_plus_60_seconds
failed_root=logs/execution_readiness_uav_source_identifiability_g0_379726e_r2
failed_root_reuse=forbidden
candidate_commit_rule=new_commit_required_for_any_code_change
unchanged_candidate_reexecution=forbidden
fresh_absent_root_required=true
full_six_phase_commit_bound_receipt=required
formal_compute=forbidden
nonformal_scientific_compute=forbidden
scientific_iteration_cost=zero
duplicate_pro_review=forbidden
current_work_mutation=forbidden
evidence_weakening=forbidden
option_b_automatic_fallback=forbidden
```

## Frozen boundary

The repair may improve only the technical execution of the proof-sized
`readiness-train` path. It preserves the accepted G0 source identity and every
frozen scientific property: geometry, RNG and seed identities, pairing,
controls, oracle, metrics, estimator, first-match order and complexity. It also
preserves the real production entry, proof inventory, artifact schema and all
canonical validation and reload requirements.

Code Project Manager may change only these five paths:

```text
ha_ctse_process/uav_source_identifiability_g0.py
scripts/run_uav_source_identifiability_g0.py
tests/ha_ctse_process_uav_source_identifiability_g0_test.py
tests/run_uav_source_identifiability_g0_test.py
docs/research/designs/UAV_SOURCE_IDENTIFIABILITY_G0_CODE_SCIENCE_INDEX.md
```

The implementation choice is owned by Code Project Manager. It must be a
semantics-preserving performance repair inside that path set. Reducing the
proof inventory, bypassing the production entry, weakening a validator,
changing an artifact claim or changing any frozen scientific identity is not a
performance repair under this contract.

## Technical acceptance

Any code change produces a new pushed candidate commit. Focused evidence must
cover the changed performance risk and demonstrate deterministic equivalence
of frozen inputs, critical outputs, counts and artifact schema. Prior scientific
results are not an oracle.

The new candidate receives one fresh execution-readiness spec with a new,
absent proof root. The `bounded_exercise` phase retains its 300-second timeout
and must complete naturally with a recorded duration strictly below 300
seconds. Every other phase timeout remains unchanged, and the outer `run`
timeout remains the sum of all six phase timeouts plus 60 seconds.

The registered verifier then executes the unchanged ordered six-phase wrapper
once:

```text
interface_smoke -> bounded_exercise -> artifact_validation -> artifact_reload -> evaluate_entry -> analyze_entry
```

Technical acceptance requires all six phases, their expected artifacts and a
successful Git-private receipt finalized against the same clean candidate
commit and exact accepted path set. A partial phase record, the failed root, a
replayed phase, or a receipt from another candidate does not satisfy this
contract.

## Failure and resume boundary

If the 300-second bound cannot be met without changing the frozen boundary,
Code Project Manager returns `READINESS_PERFORMANCE_BLOCKED`. It does not raise
the timeout, switch to Option B, replay the unchanged candidate or weaken the
evidence.

The runtime workflow may resume only after Code Project Manager returns a new
pushed `CODE_ACCEPTED` candidate with its exact changed path subset, focused
verification, deterministic-equivalence evidence and matching full six-phase
execution-readiness receipt. Research Operations Manager then applies its
existing same-source preflight and formal-admission rules. This contract itself
authorizes no preflight, nonformal scientific execution or formal execution.
