# UAV Source Identifiability G0 — Code/Science Index

```text
algorithm_id=UAV_SOURCE_IDENTIFIABILITY_G0
source_id=UAV_SOURCE_IDENTIFIABILITY_G0_P0
schema_version=1
design_round=20260730_uav_g0_executable_contract_addendum_v2
design_disposition=G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=READY_FOR_CODE_CONTRACT
package_stage_commit=8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc
design_archive_commit=9c1566e1c6adefcd500facb1bb50d5a7428eae9c
evidence_source_commit=45385faa81197bdb90c14f849eee17b999ca2f57
oracle_safety_round=20260730_uav_g0_oracle_safety_information_contract_clarification
behavioral_replay_round=20260730_uav_g0_behavioral_replay_contract_clarification
return_ready_step_round=20260730_uav_g0_return_ready_step_contract_clarification
return_ready_step_disposition=G0_RETURN_READY_STEP_DISPOSITION=KEEP_CAUSAL_R_273
branchpoint_transducer_repair_assignment=UAV_SOURCE_IDENTIFIABILITY_G0_BRANCHPOINT_AND_TRANSDUCER_EVIDENCE_REPAIR
readiness_performance_contract=UAV_G0_READINESS_PERFORMANCE_CONTRACT_V2
readiness_performance_option=B_EVIDENCE_BACKED_TIMEOUT_REVISION
readiness_performance_workflow_commit=069b0a65f0b7b8d6af62707fbf1d5d1b5a62afad
bounded_exercise_timeout_seconds=1200
outer_readiness_timeout_seconds=2520
finalize_timeout_seconds=120
automatic_timeout_revision=forbidden
code_science_alignment_audit_round=20260730_uav_source_identifiability_g0_code_science_alignment_audit
code_science_alignment_audit_stage_commit=ae1e01c64643b816fd15534fbfd46d16d3bf2f17
code_science_alignment_audit_disposition=MISMATCH
formal_interface_contract_round=20260730_uav_source_identifiability_g0_formal_interface_contract_clarification_v2
formal_interface_contract_id=UAV_SOURCE_IDENTIFIABILITY_G0_FORMAL_INTERFACE_V2
formal_interface_reconstruction_carrier_round=20260731_uav_source_identifiability_g0_formal_interface_reconstruction_carrier_clarification
formal_interface_reconstruction_carrier_stage_commit=d77710ec87e06d345cc1cdfc94d77645d8673de8
formal_interface_reconstruction_rule=SOURCE_RECONSTRUCTION_ALLOWED
oracle_replay_certificate_rule=SEPARATE_CERTIFICATE_COMPARISON_ALLOWED
runtime_carrier_rule=EXPLICIT_WRAPPER_FIELDS_REQUIRED
formal_interface_next_action=NEW_SOURCE_CANDIDATE_AND_ALIGNMENT
historical_accepted_g0_source_commit=9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43
frozen_v2_scientific_source_blob_sha=0bfaca5c0e2be428c6c9a15cd41c83f4bf7d1f5a
aligned_implementation_commit=unbound_pending_new_alignment
aligned_scientific_source_blob_sha=unbound_pending_new_alignment
claim_scope=SOURCE_IDENTIFIABILITY_G0_ONLY
formal_execution_authorized=false
learning=false
optimizer=false
checkpoint=false
G51_merge=false
```

This index maps the frozen UAV G0 source-identifiability contract to the new
source, proof-only runner, independent validators and focused tests.  It does
not record a scientific result and does not authorize the registered
`128 × 6 × 500` source evaluation.

## Exact path boundary

| Role | Path |
|---|---|
| Source/control/statistics | `ha_ctse_process/uav_source_identifiability_g0.py` |
| Proof-only runner and closed scientific entries | `scripts/run_uav_source_identifiability_g0.py` |
| Source focused tests | `tests/ha_ctse_process_uav_source_identifiability_g0_test.py` |
| Runner/artifact focused tests | `tests/run_uav_source_identifiability_g0_test.py` |
| Clause/evidence map | this file |

All G31–G51 code, runtime, review, workflow and `CURRENT_WORK` surfaces remain
outside this implementation boundary.

## Source geometry and paired authority

| Frozen clause | Implementing symbols | Reconstructed evidence | Focused guard |
|---|---|---|---|
| H=500; 8 UAV; 30 users; one centered BS; S7-S1; fixed altitude; battery/charging/failure/terminal-loss off | `PHYSICAL_HORIZON`, `UAVSourceIdentifiabilityEnv.__init__`, `step_dense` | exact inventory, map, backend flags, zero vertical actions and before/after altitude | `test_source_geometry_rng_assignment_and_support_are_exact`, `test_environment_leave_and_rejoin_are_pre_action_epoch_boundaries` |
| Uniform `phi`; three `.300L` hotspot centers; ten radius-uniform `.040L` users per hotspot | `_frozen_geometry_arrays`, `G0Geometry.__post_init__` | every array regenerated from episode ID and compared bitwise | source tamper test |
| Six tangent primaries, two `.050L` stages, inward `.060L` gates, independent `.002L` perturbations | `_frozen_geometry_arrays`, `make_episode_source` | exact target/gate/initial arrays; no clipping/redraw | source geometry test |
| Complete support inside `MAP` for every `phi in [0,2*pi)`, including hotspot/user disks, primary perturbation disks, staging perturbation disks and all gates | `geometry_support_certificate`, `G0Geometry.__post_init__`, `build_episode_validity_record` | analytic radial bounds and inward map-axis margins are reconstructed independently; sampled-phi success cannot authorize the source | universal-support and certificate-tamper tests; runner source-proof reconstruction |
| Uniform storage-only 8! permutation | `make_episode_source`, `G0Geometry`, `minimum_cost_target_assignment` | physical rows equal target-owned rows indexed by the registered permutation | assignment permutation test |
| Independent phi/users/perturbation/permutation/channel/owner/onset/duration namespaces | `_NAMESPACE_CODES`, `_rng`, `channel_seed_word` | exact namespace inventory and controller-independent, step-addressed channel word | source RNG test |
| One primary leave, O in 180..220, D in 80..100; paired NO_EVENT only disables leave/rejoin | `G0EventLedger`, `_active_mask_for_step`, `_synchronize_service_mask` | event fields regenerated; one source digest is shared by both cells | environment boundary test; result-time `build_episode_validity_record` |
| Leave/rejoin before action; absent hold/zero velocity/no action; fresh opaque epoch | `LifecycleBoundaryEvent`, `current_rows`, `step_dense`, `replacement_lifecycle_handle`, `run_g0_episode` | exact event times/count, inactive mask/action/velocity and changed handle | environment boundary test; `_validate_run_primitives` |

`G0Geometry`, `G0EventLedger` and `G0EpisodeSource` do not accept a favorable
summary flag.  Each independently reconstructs its RNG-owned primitives and
the exhaustive anonymous assignment.

## Anonymous ownership and common tracker

| Frozen clause | Symbols/evidence | Guard |
|---|---|---|
| Canonical physical rows `(x,y,vx,vy)`, canonical targets `(x,y)`, exact minimum squared cost, lexicographic coordinate tie | `minimum_cost_target_assignment`, `AssignmentCertificate` | permutation test and bitwise-identical-row rejection |
| Exactly two primaries per hotspot and two stages | assignment reconstruction in `G0EpisodeSource.__post_init__` | source/assignment tamper test |
| Opaque handles are ownership-only; no slot/epoch decision input | `AnonymousLifecycleRow`, `initial_lifecycle_handles`, `target_map_to_dense` | controller evidence zero-read fields and permutation test |
| Byte-identical accepted-G1 target transducer | `actions_toward_targets`, `ACCEPTED_G1_TRACKER_SOURCE_SHA256` | source digest equals the immutable historical digest |
| Same S7 action conversion/backhaul safety methods | `shared_action_method_digests`, `ACCEPTED_G1_SHARED_ACTION_METHOD_SHA256` | exact method digests plus actual `_prepare_energy_actions` projection |
| Raw and executed permutation equivariance, deterministic equality, inactive zero, action support | `qualify_common_tracker` | `test_accepted_g1_tracker_and_shared_correction_are_qualified`; runner reconstructs the full proof object |

The qualification interface has no caller-supplied projection.  It binds the
actual S7 shared action conversion and rejects any current method or accepted
G1 tracker digest drift.

## Controllers and oracle

### Same-information controller

`SameInformationController` reads only the current anonymous roster, current
positions/velocities/service, registered world geometry and opaque ownership
handles.  At the first seven-active pre-action boundary it ranks the two
reserves by squared physical distance, anonymous physical content and stage
coordinates.  Survivors retain targets.  On rejoin, the fresh lifecycle owns
the vacant primary and the reserve targets its inward gate.  Only after one
complete primary step and current weakest-hotspot service `>=0.90` does the
reserve return to its original stage. `ACTIVE_AT_PRIMARY_PRE` is reconstructed
only from service activity and ownership of the vacant-primary target through
the lifecycle-owner to target-owned-internal-row mapping; position coincidence,
tolerance and storage-row indexing are forbidden. The focused rejoin test
covers the primary → gate → stage state sequence.

### No-reallocation controller

`NoReallocationController` receives the same boundary inputs but freezes all
pre-event targets.  It changes neither reserve nor survivor targets; the new
lifecycle reacquires the vacant primary.  Its focused test proves no deficit-
or active-count-driven target change.

### Mechanically qualified oracle

| Obligation | Evidence |
|---|---|
| exactly two candidates, fixed `stage[-1]` and `stage[+1]` | `OracleQualificationCertificate.candidates`, `candidate_count=2` |
| minimum common-tracker travel to gate and latest departure | `_minimum_tracker_travel_steps`, per-candidate departure/arrival/error bound |
| exact stage/gate/primary/gate-until-ready schedule | `_oracle_schedule_label`, independently compared target rows |
| no future channel/service candidate-selection read | exact zero counters |
| unchanged common dynamics/action/safety source | immutable shared-method digest record |
| moving an unaffected primary would create another vacancy | reconstructed unique ownership of all five unaffected primary labels |
| lexicographic winner | exact rank `(violation_count, gate_arrival_step, event_tracking_error, path_length, stage_x, stage_y)`: violations count hard physical/safety/real-guard deviations; arrival is the first bitwise gate-equal pre-action row between latest departure and `O`, else `H+1`; event error is squared XY post-transition error summed only over `O..O+D-1`; path length is Euclidean XY post-minus-pre distance summed over `0..H-1` |
| `O(H*K_search)`, no nested rollout/replanning/tree/beam/MCTS/adaptive candidates | literal certificate fields and `K_search=2` |
| actual safety deviation fails qualification | `run_g0_episode` folds any backhaul-guard block into oracle qualification failures |

`validate_oracle_qualification` rebuilds the complete certificate.  A stored
`passed=true` or selected-winner label cannot self-authorize the oracle.

### Branch-aware behavioral replay and causal RETURN_READY

The two prebehavior candidate traces remain immutable, service-blind traces.
After their fixed ranking selects one reserve, the selected behavioral branch
is executed and independently replayed. `validate_oracle_branch_aware_replay`
requires complete P/B byte identity for every step before causal `R`, identical
pre-action branchpoint state at `R`, an unchanged shared exogenous ledger for
all steps, and byte-exact self-replay within each post-`R` branch.

`_reconstruct_controller_trace` reconstructs the Oracle controller's base
evidence without silently dropping result-bearing data. The registered
`behavioral_replay_certificate` is extracted only for Oracle rows, required to
be an exact mapping, and compared separately against the independently rerun
Oracle EVENT/NO_EVENT certificate by `_authoritative_replay_errors`. Missing or
altered certificates fail as `environment_replay_certificate`; every other
controller field remains under exact base-evidence equality. Non-Oracle rows
receive no certificate exception, so injected certificate residue fails as
ordinary controller-evidence drift.

Every safety step now serializes an exact-schema `pre_action_context`: all eight
opaque lifecycle handles, epochs, target-owned internal rows and ownership;
the event and reserve owners; the six unaffected survivor ownership rows; the
complete eight-entry service-active mask in target-owned internal order; the
explicit empty controller-RNG inventory; content-addressed bindings to every
full environment `RandomState` in the immutable common prestate; and the empty
channel-tape cursor. `_expected_pre_action_context` reconstructs the
same object from the immutable source and registered common prestate. Missing,
stale, reordered, self-authored or jointly tampered P/B evidence therefore
cannot be rescued by a favorable `branchpoint_identity_ok` summary.

Each step also binds `current_service_mask` to the exact executed action mask
and carries canonical target-owned `common_transducer_evidence`: physical
positions, targets, active mask, accepted-G1 transducer source digest and raw
output. The validator reruns the real common transducer and binds its target
input to the registered candidate schedule or behavioral target schedule.
Attaching a stage-switch schedule beside unchanged gate-target actions is
rejected; a coincident raw action remains valid only when the recomputed output
is byte-identical.

`_derive_return_ready_step` resolves the rejoined lifecycle owner through the
environment's target-owned internal order. The sampled physical storage row is
used only by serialized target schedules and cannot index an internal-order
safety record. For registered episode 0 this reconstructs `onset=191`,
`rejoin=272`, selected `stage/+1`, and `R=273`: step 272 is the completed active
primary step, `S_pre(273)=1.0`, and the gate-to-original-stage target change
occurs before raw-action construction at step 273. No delay, smoothing,
confirmation window, future-service read, reranking, or first-differing-byte
heuristic is present. The selected raw action may remain accidentally
byte-identical at the branchpoint; target identity and causal `R`, not the first
different action byte, certify the switch.

## Primitive result reconstruction

`EpisodeRunEvidence` retains the delivered-rate rows, target rows, raw action
rows, executed velocities, full positions, active masks, lifecycle events and
controller evidence, in addition to their digests.  `_validate_run_primitives`
recomputes:

- weakest-hotspot service from all 30 delivered-rate rows;
- `J`, `Q`, `M`, `A`, `B`, and catastrophe from that primitive service row;
- accepted-G1 actions from positions, targets and active masks;
- exact event mask, leave/rejoin times, inactive authority and epoch change;
- every trace digest and oracle qualification.

`build_episode_validity_record` consumes all six actual control/cell traces for
one episode.  It reconstructs paired source authority, complete NO_EVENT
same-information/no-reallocation identity, survivor continuity and every
validity counter.  The conclusion-bearing `build_analysis_evidence` accepts
only the 128 episode sources plus six ordered primitive run inventories; it
does not accept caller-authored metric or validity summaries.

## Metrics and confidence

| Clause | Implementation |
|---|---|
| `rho_z=(1/10) sum 1[rate>=1 Mbps]`; `S=min_z rho_z` | `weakest_hotspot_service_row`, `weakest_hotspot_service` |
| EVENT `W={O..O+D+59}`, normalized deficit, `J`, outside-window `Q`, minimum `M`, `A=min(J/.90,Q/.90)`, access and 10-step catastrophe | `compute_episode_metrics`, `_has_catastrophic_streak` |
| NO_EVENT `J=1`, whole-row `Q/M`, `A=Q/.90`, access, no catastrophe | `compute_episode_metrics`, `EpisodeMetrics.__post_init__` reconstruction |
| paired deltas same-information minus no-reallocation | `build_analysis_evidence` |
| exactly one `numpy Generator(PCG64(2026072901))` and one `10000×128` integer index matrix generated once and reused for every continuous metric and paired delta | `make_bootstrap_index_plan` |
| sorted no-interpolation `x_(500)`, `x_(9500)` | `bootstrap_bounds` uses zero-indexed `[499]`, `[9499]` |
| one-sided 95% Clopper–Pearson | `clopper_pearson_one_sided` |

Continuous output contains `A/J/Q/M` summaries for every control/cell and
`Delta_A/Delta_J/Delta_M`.  The same bootstrap plan is passed to every
continuous summary.

## Frozen gates and first match

`_build_analysis_from_reconstructed_rows` implements the exact ORACLE,
SAMEINFO and CAUSAL pass/fail/open predicates.  Exact physical impossibility
has FAIL precedence over statistically favorable oracle rows.  Equality laws
are literal: access lower-bound equality passes; catastrophe upper-bound .05
passes; no-reallocation upper bound 1 and binary upper .90 do not pass causal;
`Delta_J` and `Delta_M` confidence improvements remain strict while the
`Delta_M` mean threshold is inclusive.

`select_result_branch` uses only this order and stops at the first match:

1. `INVALID_UAV_G0_REALIZATION`
2. `INFEASIBLE_UAV_G0_SOURCE`
3. `ORACLE_ONLY_UAV_G0_SOURCE`
4. `NON_CAUSAL_UAV_G0_SOURCE`
5. `UNDERPOWERED_UAV_G0_SOURCE`
6. `IDENTIFIED_UAV_G0_SOURCE`

Unread lower-priority statuses are serialized as `null`: INVALID reads no
scientific status, ORACLE FAIL reads neither SAMEINFO nor CAUSAL, SAMEINFO FAIL
reads no CAUSAL, and each OPEN boundary leaves its lower statuses unread. No
reward, throughput, distance, collision, effort or prior toy result enters
these gates.

## Result-bearing interface and proof-only readiness closure

The runner now exposes the frozen `train`, `evaluate` and `analyze` interface,
but the candidate intentionally leaves `ALIGNED_IMPLEMENTATION_COMMIT`,
`ALIGNMENT_STAGE_COMMIT` and `ALIGNMENT_DISPOSITION` unbound. Therefore result-bearing entry fails before
either preflight or formal root creation until this new source candidate has a
fresh independent code-science alignment and a later exact binding commit.
The admission token remains an identity gate, not user authorization.
The frozen CLI field `accepted_g0_source_commit=9239e3e...` remains historical
accepted provenance; it is intentionally distinct from the future new aligned
candidate. The old `0bfaca5...` blob remains the immutable V2 contract record,
while the active aligned source blob is separately unbound until that candidate
has been committed and independently aligned.

Every result-bearing invocation must explicitly carry the external user-grant
reference, the prebound absolute formal root, the failed-root identity and
schema, the source/execution identities, the exact token, 16 workers and
`spawn`. Preflight freezes these fields before root mutation. The formal gate
requires the exact runtime-binding and nested-carrier key sets, then matches the
carrier, Python/runtime environment and same-source four-file preflight. It
validates the terminal digest chain and operational-pass projection without
parsing the episode bundle or re-executing its six rows; preflight evidence is
visible to formal only by identity and operational pass fields. No environment,
root-name, extra authority-looking field or default fallback can author these
fields.

The nonformal preflight terminal inventory is exactly four files:

```text
preflight_contract.json
episodes/episode_000.json
preflight_result.json
terminal_manifest.json
```

It executes six primary episode-0 control/cell rows plus six authoritative
validation replays, records `R_EVENT=273` and `R_NO_EVENT=null`, evaluates no
metric gate or first-match branch, and serializes no conclusion. A later formal
train performs no preflight replay and writes 128 fresh episode bundles (exactly
768 control/cell rows and 384000 steps, not 774/387000); evaluate and
analyze each perform exactly one independent 768-run replay pass. Analyze
captures the 128 reconstructed validity records and all metric rows from its
single `build_analysis_evidence` pass, generates one PCG64 matrix and reuses that
same matrix for source-side plan validation, and requires exact equality with evaluate,
preventing both replay doubling and favorable summary substitution. Successful
formal closure compares the exact registered 132-name preterminal set and exact
133-name terminal set, rather than accepting a same-count substitution; no
checkpoint exists. A terminal created by a failing current self-check is removed
before `failed_root.json` is written, while a terminal from a prior invocation
remains immutable.

The six executable candidate-bound readiness phases remain proof-only:

1. `readiness-smoke`
2. `readiness-train`
3. `readiness-validate`
4. `readiness-reload`
5. `readiness-evaluate`
6. `readiness-analyze`

They produce exactly:

```text
source_manifest.json
evaluation_manifest.json
analysis_result.json
proof/episode_0_source.json
proof/oracle_qualification.json
proof/common_tracker_qualification.json
proof/oracle_safety_ledger.json
proof/oracle_behavioral_replay.json
```

These artifacts are structural/synthetic technical evidence only:

```text
formal=false
scientific_iteration_cost=0
real_environment_transitions=0
learning_enabled=false
optimizer_enabled=false
checkpoint_enabled=false
scientific_conclusion=null
result_branch=null
```

The source manifest exact schema binds the v2 round, stage commit, archive
commit and disposition; the corrected PCG64 generator/seed; the universal
geometry-support certificate; exact oracle ranking arithmetic; ownership-only
RETURN_READY; target-owned context-mask ordering; and strict lazy first-match
closure. Manifest references are exact root-local paths with SHA-256 containment
checks. Validators independently reconstruct the source, full oracle and
full tracker proofs, metric/CP/bootstrap witnesses, branch fixtures and digest
chain.  Absolute paths, `..`, extra artifacts, checkpoints, altered CP rows,
forged proof fields or a stored readiness branch fail validation.

### Readiness performance closure

The registered V2 bounded-exercise ceiling is 1200 seconds; the other phase
caps remain 60/300/300/300/300 seconds, with a 2520-second outer bound and no
automatic timeout revision. Callable source
digests are cached only by the live callable object, so replacing a method
changes the cache key and forces a new digest.  One
`_ValidatedOracleSafetyContext` may be reused only inside its issuing Python
call: it is non-serializable authority, binds the exact source and ledger
objects, recomputes the ledger content digest, and binds both candidate trace
digests plus the independently reconstructed certificate.

Public validators still begin with a complete native two-candidate ledger
reconstruction.  Each readiness phase starts a fresh process and therefore a
fresh reconstruction.  Within that phase, qualification, replay validation,
evaluation and analysis reuse the same bound context rather than rerunning the
identical 2x500 native guard/network proof.  `readiness-train` retains its
independent post-write `validate_source_artifacts` reconstruction.  The two
candidate traces, selected prebehavior replay, behavioral execution and
independent behavioral self-replay are never copied, merged or omitted.

## Technical completion boundary

Technical acceptance requires:

- `py_compile` for both new Python paths;
- all focused source and runner tests;
- protected Scenario-7/S1 regressions selected proportionately;
- exact five-path diff and `git diff --check`;
- pushed candidate identity with local/remote equality;
- six-phase candidate-bound execution-readiness receipt.

Only an independent read-only `UAV_G0_CODE_SCIENCE_ALIGNMENT_AUDIT` may assess
the accepted commit.  Neither this index nor readiness authorizes scientific
execution or supports a UAV paper conclusion.

## Critical-point traceability

| claim_id | frozen_assertion_path_and_section | code_path::symbol | observable_invariant | focused_test::test_name | alternate_explanation_excluded |
|---|---|---|---|---|---|
| G0-ORACLE-LEDGER | G0 oracle-safety clarification, registered ledger | `ha_ctse_process/uav_source_identifiability_g0.py::build_oracle_safety_ledger` | exactly two sealed H=500 traces, immutable rank and real-guard evidence | `test_oracle_safety_ledger_is_real_complete_and_reconstructed` | synthetic ranking flags, service-aware candidate generation, adaptive search |
| G0-V2-GEOMETRY | executable-contract addendum v2 section 1.6 | `ha_ctse_process/uav_source_identifiability_g0.py::geometry_support_certificate` | complete analytic support under every `phi`, with zero clipping/rejection/redraw authority | universal-support and geometry-certificate tamper tests | sampled-angle-only bounds and result-dependent repair |
| G0-V2-RANK | executable-contract addendum v2 sections 2.10 and 2.14 | `ha_ctse_process/uav_source_identifiability_g0.py::validate_oracle_safety_ledger` | bitwise pre-`O` gate arrival, exact event-window squared error, full-H path length and real-guard deviations reconstruct the lexicographic rank | oracle rank arithmetic boundary/tamper tests | tolerance arrival, post-`O` arrival, extended-window error and stored favorable ranks |
| G0-REPLAY | G0 behavioral-replay clarification, branch-aware certificate | `ha_ctse_process/uav_source_identifiability_g0.py::validate_oracle_branch_aware_replay` | pre-R identity, independently reconstructed lifecycle/RNG/channel branchpoint, branch-local self-replay and shared ledger | `test_branch_aware_replay_R_NONE_requires_full_identity`, `test_branchpoint_primitives_are_required_and_independently_reconstructed` | full-episode cross-branch identity, missing primitive evidence and caller-authored replay pass flags |
| G0-TRANSDUCER | G0 branchpoint/transducer evidence repair | `ha_ctse_process/uav_source_identifiability_g0.py::_validate_record_branchpoint_and_transducer` | every target row is an input to a freshly recomputed accepted-G1 action; record output and executed mask match exactly | `test_target_schedule_requires_recomputed_common_transducer_binding`, `test_tampered_common_transducer_input_or_output_fails_closed` | detached target schedules, stale action rows and forged transducer summaries |
| G0-R273 | executable-contract addendum v2 section 2.6 | `ha_ctse_process/uav_source_identifiability_g0.py::_derive_return_ready_step` | episode-0 owner internal row and complete service mask reconstruct causal R=273 without a position test | `test_branch_aware_replay_uses_internal_owner_mapping_and_causal_R_273` | storage-row indexing, positional coincidence, seven-step delay, future service, first-differing-byte selection |
| G0-PRODUCTION-ORACLE | G0 code-science alignment audit plus reconstruction-carrier clarification | `ha_ctse_process/uav_source_identifiability_g0.py::run_g0_episode`, `_reconstruct_controller_trace`, `_authoritative_replay_errors` | every Oracle E/Z step supplies exact ownership, pre-action context and freshly recomputed common-transducer evidence; base controller evidence and the registered replay certificate are independently exact, with episode-0 E at R=273 and Z at R=NONE | `test_production_oracle_event_and_no_event_bind_branch_evidence`, `test_valid_oracle_certificate_is_separate_from_base_controller_evidence`, `test_oracle_behavioral_replay_certificate_fails_closed_separately` | readiness-only helper coverage, silently discarded certificates, detached target schedules, EVENT lifecycle assumptions in NO_EVENT and certificate residue on non-Oracle rows |
| G0-FIRST-MATCH | executable-contract addendum v2 section 5.1 | `ha_ctse_process/uav_source_identifiability_g0.py::_build_analysis_from_reconstructed_rows` | lower scientific statuses are unread and serialized null after INVALID, ORACLE FAIL/OPEN or SAMEINFO FAIL/OPEN | lazy first-match source tests; `test_branch_witnesses_cover_exact_first_match_inventory` | eager lower-gate computation hidden by final branch precedence |
| G0-RUNNER | executable-contract addendum v2 identity and artifact binding | `scripts/run_uav_source_identifiability_g0.py::validate_source_artifacts` | strict manifest binds v2 stage/archive/disposition plus certificate semantics and replay artifact reconstructs R=273 | `test_six_readiness_entries_and_terminal_artifacts`, `test_reference_paths_cp_and_tracker_are_independently_reconstructed` | stale contract identity, altered universal-support certificate and favorable stored certificate |
| G0-FORMAL-CARRIER | formal-interface V2 plus reconstruction-carrier clarification | `scripts/run_uav_source_identifiability_g0.py::FormalRuntimeBinding`, `_validate_binding`, `_validate_preflight`, `_validate_preflight_admission` | explicit user-grant reference, prebound formal root and failed-root identity/schema are frozen before mutation; exact outer/carrier schemas reject extra authority-looking fields; token-only admission, absent new alignment, and rebinding either future identity to the historical accepted commit/blob fail closed; formal admission checks the exact four-file hash chain and operational fields without importing or replaying episode rows | `test_result_bearing_alignment_gate_fails_before_root_creation`, `test_result_bearing_alignment_rejects_historical_identity_rebinding`, `test_result_cli_requires_explicit_wrapper_carriers`, `test_mocked_preflight_writes_exact_four_file_terminal_contract`, `test_failed_root_preserves_prior_terminal_but_replaces_current_invalid_terminal` | repository token treated as user authority, inferred or extra carrier fields, stale historical identity reuse, stale/broken-chain preflight and a failed current self-check left apparently COMPLETE |
| G0-FORMAL-RECONSTRUCTION | formal-interface V2 gates 8-11 | `scripts/run_uav_source_identifiability_g0.py::_authoritative_replay_guard`, `_capture_analysis_reconstruction`, `_reuse_bootstrap_index_plan`, `scientific_evaluate`, `scientific_analyze` | preflight accounts for 6+6 runs and formal train remains exactly 768; evaluate and analyze each use one exact 768-replay pass; analysis compares all reconstructed metric rows, 128 validity records, episode digests and one generated/reused PCG64 plan; terminal inventory uses the exact registered 133 paths | `test_authoritative_replay_counts_are_single_pass_and_guarded`, `test_analysis_reconstruction_rejects_per_episode_validity_tamper`, `test_canonical_sorted_episode_bundle_round_trip_preserves_run_identities`, `test_bootstrap_plan_is_generated_once_and_reused_for_source_validation` | 774-run formal train, doubled analysis replay, per-episode validity substitution, caller-authored bootstrap digest, same-count artifact swaps and favorable stored result branches |
| G0-READINESS-PERFORMANCE | `UAV_G0_READINESS_PERFORMANCE_CONTRACT_V2`, Option B | `ha_ctse_process/uav_source_identifiability_g0.py::_ValidatedOracleSafetyContext`, `_callable_source_digest`; `scripts/run_uav_source_identifiability_g0.py::_ValidatedSourceArtifacts` | every independent phase performs canonical reconstruction while identical within-phase reconstruction is reused; frozen artifacts, counts and R=273 remain unchanged; every phase duration is strictly below its registered V2 cap | `test_callable_source_digests_are_cached_by_callable_identity`, `test_validated_context_rejects_forgery_cross_source_and_nested_ledger_drift`, `test_readiness_train_uses_phase_local_context_and_one_disk_validator`; commit-bound six-phase readiness receipt | automatic timeout increase, cross-phase cache, stale/tampered evidence reuse, copied replay and weakened validation |
