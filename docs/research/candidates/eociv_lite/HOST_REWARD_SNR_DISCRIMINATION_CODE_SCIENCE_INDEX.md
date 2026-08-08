# EOCIV-B5 host-reward SNR code/science index

This index binds the frozen IID-versus-balanced estimator question to code
observables. It is a code package index, not a scientific result or a license
for C treatment.

| Protected assertion | Exact implementation symbol | Observable invariant | Focused evidence | Alternate explanation excluded |
|---|---|---|---|---|
| Equal-size four-episode updates | `ExperimentPlan`, `_train_block` | Four complete 48-step episodes, one block loss, one backward, one clip and one Adam step | `test_registered_plans_counts_namespaces_and_block_order_are_exact`, `test_one_block_uses_exactly_one_optimizer_step_and_clip_and_preserves_b4_gae` | Update-count or batch-size difference |
| IID critical shocks are frozen pre-outcome | `iid_critical_tuple`, `shock_tuples_for_block` | Candidate-local deterministic tape keyed only by seed/profile/root/position; repeats allowed | `test_balanced_order_and_iid_tape_are_frozen_with_repeats_allowed` | Outcome-adaptive or favorable shock selection |
| Balanced estimator is exact natural-prior enumeration | `CRITICAL_TUPLES`, `shock_tuples_for_block` | Fixed `(A,A),(A,B),(B,A),(B,B)` order, with event 24 always `NONE` | `test_balanced_order_and_iid_tape_are_frozen_with_repeats_allowed`, smoke `matching_proof.balanced_expected_ordinary_prior_exact` | Reward shaping or changed expected objective |
| Treatment changes only training hidden shocks | `_make_env`, `public_world_digest`, `episode_id` | Same ledger/profile/root, lifecycle and action-noise tape within blocks and across conditions; condition and position absent from episode id | `test_explicit_training_shock_changes_only_hidden_tuple_not_public_root_or_tape`, smoke matching proof | Different public world, roster, load, lifecycle or exploration tape |
| Actor sees only the legitimate receipt body | `_make_runner` using B4 `RetentionPolicy` and `RetentionEpisodeRunner` | Fixed `SEGMENT_LATCH_RNN`, receipt validation before latch write, no condition/oracle/reward preview input | block/evaluation matching predicates and inherited B4 runner evidence | Semantic or oracle observation augmentation |
| Learner is the same B4 normalized terminal GAE | `_episode_loss_tensors` | `gamma=.99`, `lambda=.95`, detached normalized advantages and detached lambda-return value target | `test_one_block_uses_exactly_one_optimizer_step_and_clip_and_preserves_b4_gae` | Auxiliary loss, altered credit rule or reward transformation |
| Diagnostic gradients do not become optimizer gradients | `_gradient_moments` | `torch.autograd.grad(..., allow_unused=True)` with missing contributions treated as zero; `.grad` remains `None` before block backward | `test_autograd_moments_leave_grad_untouched_and_zero_missing_contributions`, `_train_block` fail-closed checks | Extra gradient accumulation or episode-wise update |
| SNR uses the registered pre-clip moment definition | `_gradient_moments`, `gradient_moments_from_vectors` | `signal_sq=||mean g||²`, `noise_sq=mean||g||²-signal_sq`, `snr=signal_sq/max(noise_sq,1e-12)` | `test_hand_checkable_four_vector_gradient_moments_are_exact` | Post-clip or concatenation-dependent diagnostic |
| Actor and critic contributions match the update | `_train_block` | Actor uses `grad(actor_loss_j)`; critic uses `grad(0.5*critic_loss_j)`; block loss is `mean(actor)+0.5*mean(critic)` | one-block focused test and per-block serialized moments | Critic scaling mismatch |
| Evaluation remains natural-prior and three-arm matched | `_evaluate_checkpoint` | No forced `shock_states`; `CORRECT`, `SWAPPED`, `NATIVE_NEUTRAL` share root, shock tuple, lifecycle, hidden/latch initialization and noise | `test_registered_smoke_is_real_matched_complete_and_canonical` | Balanced evaluation distribution or unmatched arm roots |
| All semantic cells and unfavorable/null rows survive | `_evaluation_summaries` | MID/FINAL minus INIT, every seed/profile paired FINAL-minus-INIT cell, aggregate means and sign counts | smoke artifact shape assertions | Favorable seed/cell selection |
| SNR, clipping, critic and late retention diagnostics are visible | `_snr_summaries`, `gradient_and_critic_summary`, `_final_late_lag_confirmation` | Per-condition seed/profile actor/critic SNR; pre-clip/clip/critic summaries; FINAL lags 4–11 | deterministic smoke artifact assertions | A contrast change caused by lost retention or hidden clipping |
| Real-runtime budget is exact and bounded | `ExperimentPlan`, `run_experiment` | Full: 27,648 train + 31,104 evaluation = 58,752 transitions/policy calls; 576 learner episodes, 144 blocks/optimizer updates, 648 evaluation episodes | exact plan and deterministic smoke tests | Tests-only substitute or unbounded evidence search |

## Frozen interpretation boundary

The output keeps `scientific_disposition=null` and C unlicensed. It cannot be
extended into a rescue, second B5, favorable-seed selection, reward shaping,
valve, auxiliary loss, model widening, VSP learner comparison, External Pro
request or C treatment. The Code Project Manager owns integration, full-run
execution, result interpretation and technical acceptance.
