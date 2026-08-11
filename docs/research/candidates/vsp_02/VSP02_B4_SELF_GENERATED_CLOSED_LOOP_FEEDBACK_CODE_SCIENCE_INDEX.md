# VSP02-B4 code–science index

This is a commit-bound source/configuration intent record for the frozen
ordinary-B treatment `VSP02-B4-SELF-GENERATED-CLOSED-LOOP-FEEDBACK`. It does
not contain a registered-full result, technical acceptance, or a scientific
success claim. The source revision is bound at manifest creation and a
registered full additionally requires all runtime paths to be tracked and
clean at that exact `HEAD`.

```text
treatment=VSP02-B4-SELF-GENERATED-CLOSED-LOOP-FEEDBACK
direction=CAND-VSP-02
candidate=CAND-VSP-02@adversarial-revision-v8
registered_full=VSP02-B4-REGISTERED-FULL-01
freeze_handoff=C:/Projects/HMASD/temp/handoffs/explorer_to_code_manager/2026-08-11_vsp02_b4_self_generated_closed_loop_feedback.md
freeze_handoff_sha256=bd9aac55ec4f8aaa8adb88f8d20f3dc2fb2f45e7a0e17d01d7ef23caf63ac245
freeze_publication_commit=de5f2427662de2dc28fe20793086c0763d725018
source=experiments/candidates/vsp_02/self_generated_closed_loop_feedback.py
runner=scripts/run_vsp02_b4_self_generated_closed_loop_feedback.py
tests=tests/experiments/candidates/vsp_02/test_self_generated_closed_loop_feedback.py
index=docs/research/candidates/vsp_02/VSP02_B4_SELF_GENERATED_CLOSED_LOOP_FEEDBACK_CODE_SCIENCE_INDEX.md
canonical_run_root=temp/sessions/code_project_manager/vsp02_b4_self_generated_closed_loop_feedback/
arms=RL_ORIGINAL_GENERATOR|CREDIT_SIGN_SHADOW|CREDIT_SIGN_SELF_FEEDBACK
units=VSP02-B4-U01:22040001|VSP02-B4-U02:22040002|VSP02-B4-U03:22040003|VSP02-B4-U04:22040004|VSP02-B4-U05:22040005
budget=10240 real training episodes|1920 optimizer updates|1920 evaluation episodes|15 final checkpoints
caps=one result-bearing full|30 CPU minutes|2 GiB|145348 real environment transitions
retry_rescue_sweep_extra_arm_seed_checkpoint=0
```

The frozen stream family is literal: parameter initialization, optimizer
initialization, address-indexed training tapes, per-arm learner stochasticity,
minibatch order, and held-out evaluation tapes. The retained state/observable
family is likewise literal: complete initial and first-oracle-successor state;
collector source and pre-update snapshot; tape addresses; row and batch
digests; barrier, noninterference, oracle-firewall, mask, correctness-class,
actual-sign-change, coefficient, zero/nonzero, loss, actor/critic/entropy and
combined-gradient, pre-clip, clip, Adam, parameter/optimizer, occupancy,
return, target, advantage, credit-density, divergence, count, panel, tie,
finite-logit, and final-hash receipts. These are observables or mediators, not
added branch conditions, except that retained resource-cap violations are
branch-bearing validity failures. Retained evaluation is row-derived and all
zero-activity admission preflight must pass before exclusive claim creation.

| claim_id | frozen_assertion_path_and_section | code_path::symbol | observable_invariant | focused_test::test_name | alternate_explanation_excluded |
|---|---|---|---|---|---|
| B4-C01 | Freeze handoff: Roots, seeds, streams, and fixed budget | `self_generated_closed_loop_feedback.py::B4_UNITS`, `seed_and_tape_report`; `run_vsp02_b4_self_generated_closed_loop_feedback.py::_require_frozen_handoff` | U01..U05 map exactly to 22040001..22040005; B4 namespace is collision-free and no reseed path exists | `test_fresh_seed_namespace_and_predecessor_collision_fail_closed` | a reused predecessor root, identity, tape, or silent replacement seed |
| B4-C02 | Freeze handoff: Exact three arms | `self_generated_closed_loop_feedback.py::B4_ARMS`, `_new_learners` | exactly three byte-identically initialized arms in manifest order | `test_complete_three_arm_initialization_is_byte_identical` | initial parameter, Adam, recurrent, or carried-state asymmetry |
| B4-C03 | Freeze handoff: Address-indexed tape and dual-collector phase barrier | `self_generated_closed_loop_feedback.py::AddressTape`, `b4_seed`, `_update_tape_receipt` | parameter/optimizer initialization, training-tape, per-arm learner stochasticity, minibatch, and evaluation streams are immutable pure address reads; no shared mutable RNG | `test_address_tape_is_immutable_deterministic_and_stream_complete` | collector order or mutable RNG consumption changes exogenous inputs |
| B4-C04 | Freeze handoff: Address-indexed tape and dual-collector phase barrier | `self_generated_closed_loop_feedback.py::_collect_batch`, `_synthetic_barrier_proof`, `_train_unit` | both complete batches freeze before every update; frozen rows/order/masks/metadata/digests do not change | `test_dual_collection_freeze_barrier_and_batch_immutability` | an update or collector retroactively changes a training row |
| B4-C05 | Freeze handoff: Address-indexed tape and dual-collector phase barrier | `self_generated_closed_loop_feedback.py::_collect_batch`, `_train_unit` | update-zero generator and self collector batches, including ordered rows, are byte-identical | `test_first_collector_batches_are_byte_identical` | pre-treatment batch/input mismatch explains later behavior |
| B4-C06 | Freeze handoff: Address-indexed tape and dual-collector phase barrier | `self_generated_closed_loop_feedback.py::_synthetic_barrier_proof`, `_train_unit` | the first shadow and self oracle-sign complete successor states are byte-identical | `test_first_oracle_successors_have_complete_state_identity` | a hidden first oracle-sign route, optimizer, or learner-RNG difference |
| B4-C07 | Freeze handoff: Exact three arms | `self_generated_closed_loop_feedback.py::FIXED_UPDATE_ORDER`, `_train_unit` | generator updates its batch, shadow consumes exact generator bytes/order, then self consumes its own frozen bytes/order | `test_shadow_batch_bytes_and_order_match_generator_exactly` | the comparator received a different or reordered dataset |
| B4-C08 | Freeze handoff: Address-indexed tape and dual-collector phase barrier | `self_generated_closed_loop_feedback.py::_train_unit`, `validate_result` | collector, optimizer, tape, batch, RNG, and cross-arm successor-state receipts prove noninterference | `test_per_update_noninterference_receipts_preserve_all_other_arms` | one arm's mutation leaks into another arm or collector |
| B4-C09 | Freeze handoff: Feedback activity and required observables | `self_generated_closed_loop_feedback.py::_train_unit`, `validate_result` | every unit has post-first original/oracle collector divergence and at least one later action or transition-row divergence | `test_every_unit_realizes_later_feedback_exposure_without_effect_threshold` | the feedback edge never actually changes future generated data |
| B4-C10 | Freeze handoff: Frozen architecture, optimizer, and evaluator | `self_generated_closed_loop_feedback.py::_loss_terms`, `_optimizer_step`, `B4LifecycleHost`, `_evaluate_arm_unit`; `vsp02_b3_lifecycle_credit_sign_bridge.py::ORIGINAL_ACTOR_ROUTE` | B3 actor, critic, GRU, history, mask, return, entropy, Adam, clip, reduction, and evaluator routes stay literal-preserved; retained common-panel evaluation projections are recomputed from rows | `test_b3_loss_firewall_and_evaluation_routes_are_preserved`<br>`test_b3_actor_loss_reduction_gradients_and_one_step_successor_are_exact`<br>`test_retained_evaluation_rows_recompute_every_projection_and_common_panel` | a second change to loss, host, optimizer, clipping, evaluator, loss reduction, gradient route, successor, or evaluation-row projection caused the contrast |
| B4-C11 | Freeze handoff: Exact three arms | `self_generated_closed_loop_feedback.py::correctness_sign`, `_loss_terms` | oracle enters only scalar `c_i * detach(abs(G_i-b(h_i)))`; original generator has no oracle coefficient | `test_oracle_scalar_firewall_sign_and_magnitude_contract` | labels/cues alter observations, targets, sampling, rewards, masks, or the nuisance arm |
| B4-C12 | Freeze handoff: Roots, seeds, streams, and fixed budget | `self_generated_closed_loop_feedback.py::build_manifest`, `validate_manifest`, `B4_CAPS`, `validate_result` | fixed three arms, five units, 128 updates, 8 collector episodes/update at 4/4, 128 evaluation episodes at 64/64, 15 checkpoints, and all retained/recomputed caps are branch-bearing | `test_manifest_has_exact_counts_caps_and_no_extra_activity`<br>`test_resource_caps_are_branch_bearing_and_retained_recomputed_without_full` | a budget, arm, seed, checkpoint, cap, or retained activity projection variation affects the outcome |
| B4-C13 | Freeze handoff: Frozen result branches | `self_generated_closed_loop_feedback.py::B4_BRANCH_PRECEDENCE`, `classify_b4`, `validate_result` | invalidity is first, including a retained resource-cap violation; only the two specified exact patterns may receive non-invalid branch labels | `test_branch_precedence_and_frozen_nonclaims`<br>`test_resource_caps_are_branch_bearing_and_retained_recomputed_without_full` | scalar ranking, mediator direction, cap failure, post-result thresholding, or reinterpretation selects a branch |
| B4-C14 | Freeze handoff: Interpretation boundary and nonclaims | `self_generated_closed_loop_feedback.py::build_manifest`, `run_treatment`, `validate_result` | mediators are logged but never branch conditions; no B3 reopening, pooling, rescue, or general/on-policy claim is encoded | `test_mediator_records_and_nonclaims_cannot_expand_branch_meaning` | a descendant mediator or B3 result becomes a separately identified cause |
| B4-C15 | Freeze handoff: Fresh implementation outputs and technical readiness | `self_generated_closed_loop_feedback.py::validate_result`, `_arm_aggregate` | retained validation is pure; all evaluation and resource-cap projections are row-derived/recomputed without a full and do not invoke trainer, host, model, optimizer, or evaluator | `test_retained_validation_is_pure_and_source_bound`<br>`test_resource_caps_are_branch_bearing_and_retained_recomputed_without_full`<br>`test_retained_evaluation_rows_recompute_every_projection_and_common_panel` | validation itself creates fresh runtime activity, hides source drift, or trusts an unrecomputed evaluation/cap summary |
| B4-C16 | Freeze handoff: Fresh implementation outputs and technical readiness | `run_vsp02_b4_self_generated_closed_loop_feedback.py::_require_root`, `_require_bound_manifest`, `_require_clean_claim_sources`, `_require_publication_ancestry`, `preflight_report`, `_write_once`, `_exclusive_claim` | canonical source checkout/root and manifest are accepted only after every zero-activity admission/preflight gate passes; only then is the write-once sole full claim exclusively created | `test_runner_is_write_once_source_bound_and_exclusive`<br>`test_runner_preflight_precedes_claim_and_failed_preflight_consumes_nothing` | a sibling root, dirty/untracked source, manifest/ancestry/preflight drift, failed admission consuming the claim, overwrite, retry, or second full is accepted |

## Artifact boundary

The runner exposes only `manifest`, `technical-proof`, `registered-full`, and
`validate`. `registered-full` is deliberately the only result-bearing path;
every zero-activity admission and preflight gate passes before its exclusive
claim is created immediately before the one treatment invocation; there is no
catch, retry, rescue, sweep, or corrected-full route. This index does not
create a result JSON and does not authorize executing that subcommand.
