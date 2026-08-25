# G52 Phase-B Adam reset attribution: code-science index

```text
candidate_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_BOUNDARY_ADAM_RESET_ATTRIBUTION_G52
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_BOUNDARY_ADAM_RESET_ATTRIBUTION_G52_P0
scope=direction:g52-adam-boundary
loop=loop_03
handoff_sha256=c94ae40590c79959943e9624b124c1649d990e82a81c4266de8c551e590f782c
implementation_base=7293ff85a8b386488718388582896f3dd93689a3
evidence_complexity=O(H*K_search),H=48,K_search=0
hypothetical_trajectories=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
```

## Frozen question and ancestry

G52 asks whether the actor-Adam reset at the accepted update-100 Phase-A/Phase-B
boundary is removable. It compares one fresh common baseline-free Phase-A
ancestor against two storage-disjoint Phase-B projections. `RESET` receives a
fresh empty Adam. `CARRY` receives exact clones of the ancestor's `step`,
`exp_avg`, and `exp_avg_sq`. Nothing else is a treatment.

The frozen ancestry is `G49_P0@8ecb01f -> G50_P0@b829069 ->
G51_P0@ce6ed86 -> G52_P0`. Those predecessors supply accepted objective and
provenance meaning only. No predecessor checkpoint, optimizer state,
trajectory, manifest, analysis, result root, or run root initializes G52.

## Critical implementation points

| Scientific invariant | Production binding | Focused evidence |
|---|---|---|
| One fresh G51-reduced G50-null ancestor, no Phase-A baseline package | `make_fresh_phase_A_ancestor`, `optimize_phase_A_update` in `ha_ctse_process/continuous_roster_native_six_g31_phase_boundary_adam_reset_attribution_g52.py` | `test_identity_ancestry_inventory_and_common_ancestor` constructs the ancestor and both projections and checks the live objects |
| Exact 17-name actor/`log_std` order | `ACTOR_PARAMETER_NAMES`, `actor_parameters` | identity/inventory test |
| Complete boundary state with expected step 200 in the formal treatment | `snapshot_actor_adam_state`, `_validate_state_row` | exact carry and rejection-mode test |
| Exact name/order/shape/dtype/device bijection, same Adam class/hyperparameters/flags, finite state, no foreign/extra/shared state | `install_carried_adam_state`, `optimizer_hyperparameters` | missing, extra, reordered, shape, dtype, device, foreign, shared, malformed, nonfinite, wrong-step, dirty-destination and hyperparameter rejection witnesses |
| Projection/install consume zero RNG and take zero optimizer steps | `project_phase_B_arms`, `install_carried_adam_state` | common-ancestor and carry-install tests |
| RESET empty, CARRY exact and storage-disjoint | `project_phase_B_arms` | boundary tests |
| Both first plans exist before either step; actor, realized batch, normalized target and assigned gradients are identical | `execute_first_phase_B_update` | `test_actual_adam_first_step_delta_certificate_and_tamper` executes the registered first-step path and checks its realized bindings |
| Complete post-first-step RESET/CARRY Adam states, including retained inventory, state digests, RESET step 1, CARRY boundary+1, finiteness and storage separation | `inspect_post_step_adam_state`, boundary certificate | `test_actual_adam_first_step_delta_certificate_and_tamper` executes both steps and checks both complete post-step records |
| Actual float64 delta certificate and exact q edge rules | `activation_ratio`, `build_boundary_activation_certificate`, `validate_boundary_activation_certificate` | `test_q_r_edge_rules_and_inactive_branch_predicate`, `test_post_step_nonfinite_adam_state_is_sealed_scientific_invalidity`, and the active actual-step tamper witnesses execute the math and seal validators |
| Activation means finite `q_r>0` and different post-step actor bytes; inactive or invalid treatment remains a structurally valid artifact | boundary certificate, runner root activation inventory and `select_g52_result_branch` | `test_post_step_nonfinite_adam_state_is_sealed_scientific_invalidity` and `test_sealed_q_zero_reaches_exact_invalid_branch_without_generic_error` execute the sealed-invalid path through analysis |
| Composite intervention cannot identify an individual state component | `composite_state_only_no_component_attribution`, `CLAIM_CEILINGS` | cost/claim-limit test |
| After the first step, arms collect separately on-policy under paired exogenous assignments | `optimize_phase_B_update`; runner `_train_replicate` loop begins at Phase-B update 1 | `test_later_updates_are_arm_specific_and_no_forced_trajectory_equality` executes different arm trajectories and verifies distinct realized trajectory/target digests |
| G49 single-immediate objective, two PPO passes per update | G51 `_reduced_plan`/`_apply_reduced_pass` in Phase A; G49 `_single_probe`/`_apply_pass` in Phase B | `test_actual_adam_first_step_delta_certificate_and_tamper` and `test_later_updates_are_arm_specific_and_no_forced_trajectory_equality` execute two optimizer passes |
| Final-only checkpoints, strict reload and evaluation with zero optimizer steps | `build_final_checkpoint`, `validate_final_checkpoint`, `load_phase_B_checkpoint_model`; runner `_load_checkpoint_payload`, `_load_final_model`, `evaluate` | `test_final_only_checkpoint_reload_and_tamper_rejection` executes save-schema/reload validation; `test_evaluation_validation_rejects_route_source_state_worker_pairing_and_backend_tamper` executes final-state and zero-step validation |
| Evaluation has the exact unique ordered cell-key set, source/process inventory, immutable checkpoint-bound model state, valid lifecycle, paired episode identity, native backend and worker/thread evidence | G52-owned `_evaluation_cell_worker`, `_consume_evaluation_worker_results`, `_evaluation_errors` | `test_evaluation_validation_rejects_route_source_state_worker_pairing_and_backend_tamper` starts from a complete valid artifact then executes tamper witnesses for every material family |
| G52 evaluation never mutates predecessor orchestration modules | G52-owned non-mutating evaluation adapter | `test_g52_import_and_adapter_use_do_not_mutate_g50_or_g48_backends` executes a fresh import/use subprocess and compares G50/G48 source objects, callables, identities and constants |
| Native backend, spawned process isolation, preassigned-index merge, one thread per worker | runner `_resolve_cpu_execution`, `_training_replicate_worker`, `_run_indexed_worker_tasks` call contract | `test_evaluation_validation_rejects_route_source_state_worker_pairing_and_backend_tamper` executes worker/order/thread/backend admission and rejection; exact configuration test checks the frozen ceilings |
| Formal admission requires candidate/alignment bindings and one exact complete same-source preflight | runner `validate_formal_admission`, `_valid_nonformal_preflight` | `test_formal_admission_and_nonformal_authority_fail_closed` and `test_same_source_preflight_rejects_incomplete_and_accepts_complete_fixture` execute incomplete rejection, complete acceptance, cross-digest tamper rejection and authority closure |
| Readiness is candidate-bound proof only and cannot select a scientific branch | runner `readiness_interface_smoke`, six readiness entries, `validate_readiness_artifacts` | readiness interface/boundary test; later clean-candidate Verifier receipt required |

## Exact costs and independent units

The independent unit is one fresh initialization plus its whole common Phase-A
history. A Phase-B fork, environment, episode, member, timestep, PPO pass,
evaluation cell, or bootstrap draw is not independent.

| Scope | Ancestor roots | Phase A | Phase B per arm | Training transitions | Evaluation transitions | Total | Optimizer steps | Bootstrap | Wall cap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| nonformal preflight | 1 | 10 | 10 | 11,136 | 6,912 | 18,048 | 60 | 250 | 1,200 s |
| formal | 3 | 100 | 100 | 344,448 | 165,888 | 510,336 | 1,800 | 10,000 | 28,800 s |

The nonformal hard ceilings are 22,272 total real transitions, 80 optimizer
steps, 250 bootstrap resamples and 1,200 seconds. The formal ceilings are
626,688, 2,400, 10,000 and 28,800 seconds respectively.

Training real transitions count realized environment batches, not per-arm
exposure. Per independent root the exact count is
`(A + 2*B - 1) * 8 * 48`: Phase-B update 0 is one batch materialized once and
reused by both arms, so exactly one batch is subtracted from the two-arm
exposure count. Optimizer accounting remains per arm and therefore unchanged.
`test_training_real_transition_formula_subtracts_one_shared_phase_b_batch_per_root`
executes this formula for both configurations, explicitly contrasts the old
double-count, and checks that both-arm optimizer-step accounting is retained.

## Estimand, branches, and claims

The primary estimand is `Delta_reset = U_RESET - U_CARRY`; positive favors
RESET. The materiality/noninferiority margin is `0.05`. Evaluation retains the
G50 capacity-equal paired whole-episode construction over the G34-P0
fixed/random capacity-6/8/12 family, four cells per capacity, and the frozen
absolute access gates.

First match is exact:

1. `INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_BOUNDARY_ADAM_RESET_ATTRIBUTION_G52`
2. `SOURCE_OR_REFERENCE_ACCESS_FAILURE_G52`
3. `PERSISTENT_ADAM_CONTINUOUS_TRAINING_SUFFICIENT_G52`
4. `PHASE_BOUNDARY_ADAM_RESET_FINITE_BUDGET_ADVANTAGE_G52`
5. `MIXED_UNDERPOWERED_PHASE_BOUNDARY_ADAM_RESET_ATTRIBUTION_G52`

Sufficiency requires both access gates and the primary plus every registered
component RESET-minus-CARRY 95% upper bound at or below `0.05`. Reset advantage
requires valid source and activation, RESET access, and either confidently
failed CARRY access or a primary 95% lower bound strictly above `0.05` with
every capacity-specific lower bound strictly above zero.

A sufficiency result says only that this exact update-100 reset is removable in
G52-P0. A reset-advantage result says only that this exact composite reset has a
source-local finite-budget advantage. It does not identify `step`, `exp_avg`,
or `exp_avg_sq` separately and supports no universal optimizer, horizon,
capacity, recurrence, UAV, transport, or deployment claim. Invalid,
source-failure, inactive, and mixed outcomes rank neither arm.

## Runtime and readiness separation

This implementation does not authorize or perform readiness or scientific
runtime. After Root creates a clean candidate commit, the registered Verifier
must execute exactly `readiness-smoke`, `readiness-train`,
`readiness-validate`, `readiness-reload`, `readiness-evaluate`, and
`readiness-analyze` through the readiness wrapper. Readiness is `formal=false`,
has zero registered scientific roots and zero scientific-iteration cost, uses
separate proof-only artifacts, performs no bootstrap inference or access
conclusion, and selects none of the five branches. It cannot initialize or
satisfy nonformal/formal execution.

Formal execution remains fail-closed until the exact clean implementation and
alignment commits are bound and the complete same-source nonformal preflight is
present. There is at most one nonformal preflight and one conclusion-bearing
formal run. No branch authorizes retry, rescue, extra roots, a margin change,
seed search, component ablation, or a second formal execution.
