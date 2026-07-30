# G51 Phase-A Shadow-Baseline Module Reduction Code–Science Index

## Frozen boundary

```text
algorithm_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51_P0
schema_version=1
design_round=20260729_g31_phase_a_shadow_baseline_module_reduction_g51_design_assertion_audit
design_stage_commit=fb16a412841ad69912d927262dae8f694ea5471a
design_disposition=PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51
accepted_predecessor_source_commit=044d9690fa19aa07b8e68bf5cbb2a159c19be8c1
accepted_G50_formal_source_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
accepted_G50_execution_code_commit=23af6bf7c80a4b73c09cf0423f9f539972b1b55d
accepted_G50_alignment_stage_commit=4df41063d077ace7e0c9212e0cbadbf56e1be4b7
accepted_G50_formal_branch=FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50
reference_arm=G50_FRESH_SINGLE_IMMEDIATE_WITH_PHASE_A_SHADOW_BASELINE
reduced_arm=G50_FRESH_SINGLE_IMMEDIATE_WITHOUT_PHASE_A_BASELINE_MODULE
implementation_commit=the_Git_commit_containing_this_index_and_all_four_G51_code_test_paths
alignment_audit_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51_CODE_SCIENCE_ALIGNMENT_AUDIT
alignment_correction_recheck_round=20260729_g31_phase_a_shadow_baseline_module_reduction_g51_code_science_alignment_correction_recheck
alignment_disposition=ALIGNED
aligned_implementation_commit=188b210975a0f243ae34318d658fbf943d1d63ab
alignment_stage_commit=aa756dcd06a2ea622c155f2983a89bb5d76e9d80
formal_authorization_token=none
formal_admission=FAIL_CLOSED_UNTIL_SEPARATE_AUTHORIZATION_TOKEN_AND_EXECUTION_INTERFACE
formal_compute_started=false
nonformal_compute_started=false
scientific_iteration_cost=zero
```

G51 changes one thing only: before phase-A trajectory use and optimizer
construction, it physically deletes the G50 null arm's `credit_baselines`
module and every baseline-only input, target, forward, loss, gradient, Adam,
diagnostic, liveness, checkpoint, compatibility and dummy path from the reduced
arm. It preserves the G50 single-immediate actor objective, common entropy,
actor and `log_std` parameter order, source, action law, phase boundary, fresh
phase-B Adam, G49 phase-B route and final-only actor projection.

## Owned implementation paths

| Role | Path |
|---|---|
| Algorithm and exact evidence | `ha_ctse_process/continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51.py` |
| Result-bearing proof runner | `scripts/run_continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51.py` |
| Focused algorithm proof | `tests/ha_ctse_process_continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51_test.py` |
| Focused runner and artifact proof | `tests/run_continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51_test.py` |
| Contract-to-code-to-test binding | this file |

No G47, G49, G50, runtime, review, CDC, `CURRENT_WORK`, workflow or authority
path is part of this implementation diff.

## Exact construction and proof inventory

`make_phase_A_models` creates one complete fresh G50 single-immediate null
initialization, then produces two deep storage-disjoint arms. The reference
retains the phase-A shadow baseline package. The reduced arm uses
`G51NoBaselinePhaseAProjection` and deletes exactly `credit_baselines` before
any trajectory collection or optimizer construction. It preserves the accepted
G50 `slow_critic` as storage-disjoint, optimizer-unexposed phase-A state until
the ordinary common phase boundary removes it from both arms.
`phase_A_boundary_audit` requires actor/`log_std` and slow-critic bytes, names,
shapes, order and masks to match while projection consumes zero RNG and zero
optimizer steps.

`make_phase_A_optimizers` retains the accepted actor-then-baseline G50 order in
the reference and the exact actor/`log_std` prefix in the reduced arm. The
actual Adam class, hyperparameters, retained parameter order, per-parameter
step, `exp_avg` and `exp_avg_sq` are reconstructed; whole optimizer-state
equality is intentionally not required because the reference owns baseline-only
entries.

The mandatory static proof uses no trajectory. Exact classification also
requires the proof-sized actual-kernel witness to close the Adam
tensor-list/kernel call-surface risk:

```text
accepted_G50_fresh_initializations=1
shared_stored_phase_A_batches=1
episodes=8
H=48
real_transitions=384
PPO_passes_per_arm=2
actor_optimizer_steps_per_arm=2
reference_baseline_parameter_Adam_exposures=2
reduced_baseline_parameter_Adam_exposures=0
total_optimizer_steps=4
bootstrap_resamples=0
formal_statistical_run=false
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
wall_clock_cap_seconds=1200
```

The runner collects the shared stored batch once from the common reference
actor and passes that exact object to both source paths. It does not collect a
second environment batch. `optimize_phase_A_update` invokes the actual accepted
backward and Adam kernels for both PPO passes and validates every registered
gradient, actor/`log_std`, Adam, action/log-probability and source/lifecycle
difference as exactly zero. Artifact validation reloads the saved object as the
exact `AnchoredRosterTrajectory` type, checks every time-major tensor as 48x8,
and independently reconstructs the source/lifecycle digest record for exact
comparison with the serialized phase-A evidence.

The inherited G50 seed block remains role-separated: runtime configuration may
use `phase_A_gradient_probe`, while the stored witness collection uses exactly
`phase_A_ledger` for lifecycle/source generation and `phase_A_action` for
action noise. The manifest serializes the complete replicate-zero nonformal
seed block and the validator reconstructs it from `source.seed_block`.

The serialized configuration and source controls bind the inherited runtime
contract as `ContinuousRosterToyBatch_CPU_CPP_required` with
`environment_python_fallback=false`; the proof runner cannot relabel a Python
fallback as accepted backend evidence. The train manifest additionally records
the exact five-field result of inherited
`g50_runner._backend._native_backend_identity()`, including its loaded module
and build identity, and every reload validates it against the live interface.

`project_phase_B_models` then deletes phase-A state in both arms and constructs
fresh empty actor-only phase-B Adam instances. The witness takes zero phase-B
optimizer steps: the common G49 phase-B transition and its per-parameter
factorization are registered by `build_phase_B_zero_step_certificate` against
the actual G49 single-channel probe/apply callables, actor parameter order,
fresh disjoint Adam state, unchanged RNG/model/gradient slots and exact assigned
gradient/actor traces. `build_inductive_equality_certificate` binds the phase-A
evidence, phase-boundary evidence, zero-step phase-B certificate and both
final-only proof checkpoints into the exact `D_G51` reconstruction.

`assess_structural_witness` is the only terminal assessment boundary. The exact
path retains the strict witness and two final checkpoints. It catches only the
four registered `G51InvariantError` reasons for static pre-step invalidity,
pre-step semantic coupling, coupling-free pre-step numerical difference and
post-paired numerical mismatch. Semantic coupling is reconstructed only from
cross-gradients, RNG/buffer/hook effects, shared storage, forbidden reads or
another registered side-effect predicate; a failed policy-loss, assigned-gradient,
action, pre-tanh or log-probability equality with all such predicates zero is
numerically unresolved. The independently
validated optimizer ledger requires equal reference/reduced completed actor
steps, no step after detection and zero phase-B steps; partial reference-only
updates, unknown exceptions or malformed evidence remain operational errors.
For a valid adverse assessment, the runner writes a branch-discriminated train
manifest with no placeholder checkpoints, then zero-transition/zero-optimizer
evaluation and analysis manifests. Thus every frozen first-match token can be
durably reconstructed without converting an adverse scientific result into a
technical failure or a positive claim.

## Contract mapping

| claim_id | frozen_assertion_path_and_section | code_path::symbol | observable_invariant | focused_test::test_name | alternate_explanation_excluded |
|---|---|---|---|---|---|
| G51-PROVENANCE-01 | Design raw `IDENTIFICATION_AND_DEPENDENCY_RESULT / Exact provenance and arm construction` | source `::make_phase_A_models`; `::phase_A_boundary_audit`; runner `::source_controls` | G51 binds design `fb16a412...`, predecessor `044d9690...`, accepted G50 formal source `b8290699...`, execution code `23af6bf7...`, corrected alignment stage `4df41063...` and branch `FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50`. One full initialization precedes both storage-disjoint arms. | source provenance/boundary proof; runner `::test_configuration_provenance_and_formal_admission_are_fail_closed` | A historical fast-anchor arm, separately initialized reduced model, caller-selected predecessor, stale G50 stage or shared tensor storage cannot define G51. |
| G51-DELETION-02 | Design raw `EXECUTABLE_BOUNDARY / Required reduced callable boundary` | source `::G51NoBaselinePhaseAProjection`; `::make_phase_A_models` | Reduced phase A has no baseline module, true-state-only argument/accessor, target, forward, loss, gradient, optimizer member, diagnostic, liveness gate, artifact field, compatibility route or dummy value. | source exact projection and read-trap proof; runner recursive reduced-checkpoint tamper guard | Output disconnection with a dormant module, frozen head, zero filler, legacy key or readable `critic_state` cannot pass as deletion. |
| G51-STATIC-03 | Design raw `IDENTIFICATION_AND_DEPENDENCY_RESULT / Static dependency certificate` | source `::reconstruct_static_certificate`; `::validate_static_certificate` | Actual module, parameter/storage, autograd, optimizer, action, RNG, lifecycle, checkpoint, evaluation and result dependency graphs are reconstructed. Every registered baseline-to-actor and diagnostic-side-effect count is zero. | source static-certificate proof and tamper rejection; runner nested certificate tamper guard | Caller-authored booleans, declared zero counters or output-only disconnection cannot conceal a baseline dependency. |
| G51-ADAM-04 | Design raw `IDENTIFICATION_AND_DEPENDENCY_RESULT / Per-parameter Adam factorization` | source `::make_phase_A_optimizers`; `::reconstruct_static_certificate`; `::optimize_phase_A_update` | Reference actor parameters form the exact retained prefix; reduced owns that prefix only. No clipping, joint normalization, loss-count/group-size scaling, global step/scheduler or cross-parameter reduction exists. Actual assigned actor gradients and retained Adam states are byte-equal after each pass. | source optimizer-factorization and actual-kernel proof | Parameter deletion cannot alter actor arithmetic through ordinal remapping, global norm/scaling, scheduler state, fused replacement or a simplified optimizer. |
| G51-SIDE-EFFECT-05 | Design raw `COUNTEREXAMPLES_AND_CLAIM_CEILING / Backward and diagnostic counterexample` | source `::reconstruct_static_certificate`; `::optimize_phase_A_update` | Baseline forward/backward owns no dropout, RNG, mutable actor buffer, actor hook, gradient-slot ordering, trainable-mask, optimizer-order, source, checkpoint or branch side effect. | source static and phase-A update tamper proofs | A mathematically disconnected loss with operational side effects cannot select exact removability. |
| G51-PHASE-06 | Design raw `IDENTIFICATION_AND_DEPENDENCY_RESULT / Exact inductive equality` | source `::project_phase_B_models`; `::make_phase_B_optimizers`; `::build_phase_B_zero_step_certificate`; `::build_inductive_equality_certificate` | Equal actor bytes reach the phase boundary, phase-A state is deleted, fresh empty actor-only phase-B Adam is created in exact order, and the actual G49 single-channel callables, assigned gradients, actor traces and per-parameter factorization preserve equality with zero phase-B steps. | source phase-boundary/fresh-Adam, phase-B zero-step and inductive-certificate proof | Retained baseline state, reused Adam, actor-order drift, caller-authored phase-B success or a hidden compatibility module cannot pass. |
| G51-DIFF-07 | Design raw `IDENTIFICATION_AND_DEPENDENCY_RESULT / D_G51` | source `::build_inductive_equality_certificate`; `::validate_inductive_equality_certificate` | The registered vector covers actor gradients, actor/`log_std`, actor Adam, pre-tanh/action/log-probability, reward/roster/lifecycle, phase boundary, phase-B actor/Adam and canonical final checkpoint; every component and `D_G51` are exactly zero. | source inductive reconstruction and tamper proof; runner lifecycle `::test_readiness_lifecycle_is_exact_reloadable_and_zero_additional_science` | Tolerance-based equality, one final-weight comparison, missing Adam/provenance or a stored favorable label cannot establish the result. |
| G51-ARTIFACT-08 | Design raw `COUNTEREXAMPLES_AND_CLAIM_CEILING / Checkpoint-schema counterexample` | source `::build_final_checkpoints`; `::validate_checkpoint_pair`; `::canonical_actor_projection`; runner `::validate_training_artifacts`; `::validate_evaluation_artifacts`; `::validate_analysis_artifacts` | Reference and reduced full schemas intentionally differ, while canonical actor/`log_std`/Adam/update/provenance/final-only projections are exact. Every assessment, runner envelope, nested source certificate, trajectory row, checkpoint inventory row, process report, evaluation and analysis schema is exact and rejects recursive extras; checkpoint source provenance and phase-boundary records have exact nested schemas and reject innocuous extra keys. The reduced checkpoint omits baseline-bearing comparison labels and rejects every baseline identity recursively in keys and free-form string values. | source checkpoint round-trip/tamper proof; runner `::test_recursive_artifact_and_checkpoint_tamper_guards_fail_closed` | Full-file equality, synthesized reduced defaults, extra legacy keys, forbidden string values, digest-only trust or incomplete canonical projection cannot pass. |
| G51-WITNESS-09 | Design raw `EVIDENCE_AND_COMPLEXITY_DISPOSITION / Optional proof-sized numerical witness` | runner `::_configuration`; `::_materialize_source_bundle`; `::train` | One initialization, one shared 8×48 batch and exactly two passes per arm invoke the actual source kernel within four actor steps, zero bootstrap and the hard complexity ceiling. Collection binds ledger=`phase_A_ledger` and action=`phase_A_action`, while the gradient-probe seed is runtime-only. Fresh-root admission occurs before materialization. | runner configuration, stale-root, seed and lifecycle tests | Duplicate collection, seed-role collapse, compute before root admission, statistical inference, a replacement optimizer, hidden evaluation steps or expanded search cannot enter. |
| G51-OUTCOME-10 | Design raw `EVIDENCE_AND_COMPLEXITY_DISPOSITION / Ordered result classes` | source `::optimize_phase_A_update`; `::_pre_step_semantic_coupling_detected`; `::_pre_step_numeric_difference_detected`; `::assess_structural_witness`; `::validate_structural_assessment`; runner `::record_terminal_assessment`; `::select_g51_result_branch`; `::analyze` | First match is exactly invalid, reconstructed semantic coupling, exact removability, then numerical unresolved. Pre-step coupling and numeric reasons are disjoint: zero coupling predicates plus a failed registered equality selects unresolved with zero actor steps. Source and runner independently reconstruct the branch from diagnostics and optimizer ledger. | source assessment/branch proof; runner `::test_frozen_first_match_order_and_tokens_are_exact`; `::test_source_assessed_adverse_lifecycles_are_terminal_and_zero_extra_work`; `::test_zero_coupling_pre_step_numeric_difference_is_unresolved_with_zero_steps`; partial/unknown failure rejection | Failure-reason text, a favorable stored branch or `D_G51` cannot manufacture coupling or exactness; partial updates, unknown errors and malformed evidence cannot be relabeled as scientific outcomes. |
| G51-READINESS-11 | Code-PM execution-readiness contract | runner `::readiness_interface_smoke`; `::readiness_train`; `::readiness_validate`; `::readiness_reload`; `::readiness_evaluate`; `::readiness_analyze`; `::_run_distinct_proof_workers` | Smoke constructs the real pre-trajectory boundary with zero transitions/steps. Bounded exercise alone runs the authorized witness. Later phases add no optimizer steps or transitions. Two dedicated concurrently live spawn processes independently reload and validate the same artifacts; they do not rerun collection or optimization. | runner lifecycle, smoke and `::test_two_process_attestation_is_dedicated_spawn_and_not_a_second_witness` | A reused pool PID, a second scientific witness, phase replay, manual artifact trust or lower-level projection-only smoke cannot satisfy readiness. |
| G51-AUTHORITY-12 | Formal-interface alignment-binding assignment; router formal authority | runner `::AUTHORIZATION_TOKEN`; `::ALIGNED_IMPLEMENTATION_COMMIT`; `::ALIGNMENT_STAGE_COMMIT`; `::source_controls`; `::_formal_admission_errors`; `::train` | The runner binds exactly the independently ALIGNED correction target `188b2109...` and correction-recheck stage `aa756dcd...`. The scientific contract supplies no formal authorization token, so every formal request still fails before run-root creation, model construction, trajectory collection or optimizer work; nonformal/proof-only CLI rejects every formal field. | runner `::test_configuration_provenance_and_formal_admission_are_fail_closed`; CLI formal-field guard | A caller-selected target/stage, package/archive commit, invented token, preflight path or this index cannot self-authorize formal execution. |
| G51-ISOLATION-13 | Assignment protected predecessor semantics | source/runner read-only `g50` dependency | G51 adds new paths and does not mutate G47, G49 or G50 arm names, source identities, optimizers, RNG, artifacts, formal gates or accepted results. | runner `::test_g51_import_leaves_g50_identity_unchanged`; protected predecessor checks | Global monkey-patching or cross-direction identity leakage cannot alter the supported G50 line. |

Because the accepted PyTorch backward/Adam kernel is exercised by this
candidate, exact removability requires the registered 8x48 witness to be
present and all-zero. A caller-authored `D_G51=0` or a static-only record is
classified as numerical unresolved rather than exact.

## Result branches and claim ceiling

The exact first-match order is:

1. `INVALID_G50_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51`
2. `UNREGISTERED_PHASE_A_SHADOW_BASELINE_COUPLING_G51`
3. `PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51`
4. `NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51`

A positive result means only that, in the exact G50-P0 fresh two-phase
single-immediate route, the phase-A shadow-baseline module, true-state input,
target-fitting loss, parameters, gradients, Adam entries, diagnostics and
artifact fields are structurally removable without changing the registered
actor/Adam trajectory, behavior traces or canonical final actor checkpoint.

It does not establish arbitrary critic redundancy; removal of immediate
centering, RMS normalization or entropy; removal of the phase boundary or Adam
reset; uninterrupted 200-update sufficiency; optimizer-independent equality;
arbitrary process/capacity/horizon transport; UAV deployment; global
memorylessness; or TEAM-GAE1 sufficiency. A coupling or numerical failure does
not restore the historical common-fast-anchor actor-credit treatment or alter
the accepted G50 formal result.

## Next boundary

```text
CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51_FORMAL_EXECUTION_INTERFACE
```

The independently ALIGNED implementation and stage are now bound. Formal
admission remains closed because neither the frozen G51 contract nor this
binding assignment supplies an authorization token or a conclusion-bearing
same-source preflight interface. This implementation, its tests, its mandatory
proof-sized actual-kernel witness and this index cannot supply that authority.
