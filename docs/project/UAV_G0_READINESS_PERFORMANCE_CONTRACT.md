# UAV G0 Readiness Performance Contract

```text
document_kind=execution_readiness_performance_contract
request_id=UAV_G0_READINESS_PERFORMANCE_CONTRACT_V2
selected_option=B_EVIDENCE_BACKED_TIMEOUT_REVISION
observed_timeout_candidate_commit=379726e325236a02c3a45bf7049bedaaa90d4e31
scientific_contract_stage_commit=8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc
scientific_contract_disposition=G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=READY_FOR_CODE_CONTRACT
interface_smoke_timeout_seconds=60
bounded_exercise_timeout_seconds=1200
artifact_validation_timeout_seconds=300
artifact_reload_timeout_seconds=300
evaluate_entry_timeout_seconds=300
analyze_entry_timeout_seconds=300
phase_success_duration=recorded_and_strictly_below_its_timeout
outer_run_timeout_seconds=2520
finalize_timeout_seconds=120
failed_root=logs/execution_readiness_uav_source_identifiability_g0_379726e_r2
failed_root_reuse=forbidden
candidate_attempt_limit=3
fresh_absent_root_required=true
candidate_commit_rule=new_commit_required_for_any_code_change
unchanged_clean_candidate_rule=operational_retry_budget_under_unchanged_v2_contract
full_six_phase_commit_bound_receipt=required
current_oracle_reproduction=continues_under_code_project_manager
formal_compute=forbidden
nonformal_scientific_compute=forbidden
scientific_iteration_cost=zero
duplicate_pro_review=forbidden
current_work_mutation=forbidden
evidence_weakening=forbidden
automatic_timeout_increase=forbidden
automatic_retry=operational_only_within_unchanged_candidate_and_contract
```

## Frozen boundary

This contract revises only the proof-sized readiness time budget for the UAV
native environment and safety ledger. It preserves the accepted G0 source
contract, geometry, `R=273`, `O(H*K_search)`, RNG and seed identities, pairing,
controls, oracle, metrics, estimator, first-match order and independent replay.
It also preserves the real production entry, proof inventory, artifact schema,
canonical validators and reload requirements. A readiness attempt remains
`formal=false`, consumes zero scientific iterations and produces no scientific
disposition.

The Code Project Manager's current Oracle `EVENT`/`NO_EVENT` reproduction and
repair continues independently. This contract neither cancels, preempts,
accepts nor changes that work. If it changes code, the readiness candidate must
be its new clean pushed commit. An unchanged clean candidate may use only the
bounded operational retry budget defined below. Every attempt requires a new
exact spec and a fresh absent root.

Code Project Manager retains the same five-path implementation boundary:

```text
ha_ctse_process/uav_source_identifiability_g0.py
scripts/run_uav_source_identifiability_g0.py
tests/ha_ctse_process_uav_source_identifiability_g0_test.py
tests/run_uav_source_identifiability_g0_test.py
docs/research/designs/UAV_SOURCE_IDENTIFIABILITY_G0_CODE_SCIENCE_INDEX.md
```

No proof-inventory reduction, production-entry bypass, validator weakening,
artifact-claim change or scientific-identity change is authorized.

## Ordered phase gates

The registered verifier executes one wrapper run on one clean candidate, one
exact spec and one fresh absent root. Phases are serial and a phase starts only
after its predecessor succeeds:

| Phase | Timeout | Success gate |
|---|---:|---|
| `interface_smoke` | 60 s | Production configuration, entry method, argument shapes and return schema complete successfully. |
| `bounded_exercise` | 1200 s | The real proof-sized training entry completes and produces its required proof artifacts without changing the frozen inventory. |
| `artifact_validation` | 300 s | Canonical validation accepts the complete produced artifact set. |
| `artifact_reload` | 300 s | Canonical reload reconstructs the required identities and evidence. |
| `evaluate_entry` | 300 s | The minimal real evaluation entry completes with zero optimizer and scientific-disposition authority. |
| `analyze_entry` | 300 s | The minimal real analysis entry completes without formal admission or a scientific conclusion. |

Every successful phase records a duration strictly below its own timeout. The
outer `run --spec` timeout is 2520 seconds: the sum of the six phase timeouts
plus 60 seconds. After all six phases succeed, `finalize --spec` has a separate
120-second limit, reruns no phase and must revalidate the exact candidate,
paths, spec, artifacts and candidate receipt before emitting the Git-private
commit-bound receipt.

Focused candidate checks remain separate from these phases and do not pre-run
or replay a phase. Technical acceptance requires every expected artifact, all
six successful phase records and the matching finalized receipt.

## Fresh-root and failure semantics

The r2 failed root is terminal and cannot be used as acceptance evidence,
reused, resumed or repaired in place. One unchanged clean candidate may make at most
three attempts under this unchanged v2 contract. Every attempt has one exact
spec, one new root that must be absent before the wrapper starts and one wrapper
run. A failed root remains terminal regardless of failure class.

- A phase timeout is `READINESS_PHASE_TIMEOUT`: technical readiness evidence,
  zero scientific iterations, no scientific disposition and no receipt.
- A nonzero command exit, missing artifact, validator rejection, reload
  mismatch or identity mismatch is `READINESS_TECHNICAL_FAILURE`: the first
  causal phase is reported and later phases plus finalization do not run.
- A phase that cannot satisfy its v2 cap without changing the frozen boundary
  returns `READINESS_PERFORMANCE_BLOCKED`.
- Finalizer failure is `READINESS_FINALIZATION_FAILURE`; it reruns no phase and
  produces no successful receipt.

Only a transient environment, launcher, path or operating-system failure may
use the remaining operational retry budget automatically. A code defect,
validator rejection or reproducible artifact mismatch returns to Code Project
Manager and requires a new clean pushed candidate before another attempt. No
outcome authorizes a higher timeout, evidence weakening or scientific
abandonment. Changing a timeout, the frozen boundary or the evidence contract
requires a new explicit workflow contract.

The runtime workflow may resume only after Code Project Manager returns a
pushed `CODE_ACCEPTED` candidate with its exact changed path subset, focused
verification and matching full six-phase execution-readiness receipt. Research
Operations Manager then applies the existing same-source preflight and formal
admission rules. This contract authorizes no preflight, nonformal scientific
execution or formal execution.
