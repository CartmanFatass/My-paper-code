# UAV G0 Readiness Performance Contract

```text
document_kind=execution_readiness_performance_contract
request_id=UAV_G0_READINESS_PERFORMANCE_CONTRACT_V3
selected_option=B_EVIDENCE_BACKED_TIMEOUT_REVISION
candidate_identity=checked_out_clean_HEAD
source_execution_bridge=forbidden
execution_support_delta=forbidden
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
unchanged_clean_candidate_rule=up_to_three_fresh_attempts_under_this_contract
full_six_phase_candidate_bound_receipt=required
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
accepts nor changes that work. CM binds each focused observation to the exact
source and scientific configuration it inspected. A pushed commit, fresh root,
attempt identity or retry budget is not required for local evidence or
unchanged-science repair; Root publication remains later integration work when
a downstream consumer actually needs it.

Code Project Manager retains the exact thirteen-path implementation boundary:

```text
ha_ctse_process/uav_episode_schema.py
ha_ctse_process/uav_episode_serialization.py
ha_ctse_process/uav_g0_geometry.py
ha_ctse_process/uav_g0_statistics.py
ha_ctse_process/uav_g0_oracle_evidence.py
ha_ctse_process/uav_g0_controllers.py
ha_ctse_process/uav_g0_environment.py
ha_ctse_process/uav_source_identifiability_g0.py
scripts/uav_g0_artifact_io.py
scripts/run_uav_source_identifiability_g0.py
tests/ha_ctse_process_uav_source_identifiability_g0_test.py
tests/run_uav_source_identifiability_g0_test.py
docs/research/designs/UAV_SOURCE_IDENTIFIABILITY_G0_CODE_SCIENCE_INDEX.md
```

No proof-inventory reduction, production-entry bypass, validator weakening,
artifact-claim change or scientific-identity change is authorized.

## Ordered phase gates

The registered verifier executes one wrapper run on one clean candidate `HEAD`,
one exact spec and one fresh absent root. Phases are serial and a phase starts
only after its predecessor succeeds:

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
120-second limit, reruns no phase and must revalidate the exact candidate `HEAD`,
paths, spec, artifacts and candidate receipt before emitting the Git-private
receipt.

Focused candidate checks remain separate from these phases and do not pre-run
or replay a phase. Technical acceptance requires every expected artifact, all
six successful phase records and the matching finalized receipt.

## Fresh-root and failure semantics

The r2 failed root is terminal and cannot be used as acceptance evidence,
reused, resumed or repaired in place. One unchanged clean candidate may make at most
three attempts under this unchanged contract. Every attempt has one exact
spec, one new root that must be absent before the wrapper starts and one wrapper
run. A failed root remains terminal regardless of failure class.

A root in which any readiness phase started is a failed attempt and consumes one
of the three unchanged-candidate attempts. A pure zero-compute finalizer retry
after a successful `run` starts no phase, creates no new scientific evidence and
does not consume another attempt; it may only repeat the same candidate receipt
write with identical content.

- A phase timeout is `READINESS_PHASE_TIMEOUT`: technical readiness evidence,
  zero scientific iterations, no scientific disposition and no receipt.
- A nonzero command exit, missing artifact, validator rejection, reload
  mismatch or identity mismatch is reported as the exact observed technical
  fact. Later independent safe observations may continue when they can add
  evidence; no status token or phase order controls scientific work.
- A check that cannot satisfy its operational observation bound returns the
  measured fact and remaining unknown to CM. It is not `BLOCKED` and cannot
  pause the scientific direction.
- Finalizer failure means only that its optional receipt was not produced. It
  grants or removes no readiness, technical acceptance or scientific validity.

Environment, launcher, path, operating-system, code, validator and artifact
failures return as evidence to Code Project Manager. CM chooses
semantics-preserving repair and fresh verification without a fixed retry budget,
pushed-candidate prerequisite or attempt identity. A higher operational timeout
or another resource slice is a CM/Root scheduling decision; changing the frozen
scientific boundary or weakening evidence remains science-bearing and returns
to EM.

The runtime workflow continues when Code Project Manager has enough focused
technical evidence for the exact changed risk. No pushed candidate, status
token, fixed six-phase receipt or formal admission state is required. Git and
optional receipts document accepted work for downstream consumers; they never
admit or terminate scientific execution.
