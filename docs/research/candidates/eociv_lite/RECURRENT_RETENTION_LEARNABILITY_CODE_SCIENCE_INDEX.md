# EOCIV-B4 recurrent-retention learnability code/science index

`EOCIV-B4-RECURRENT-RETENTION-LEARNABILITY` is a new result-aware matched B
experiment. It is neither a B3 rerun/rescue nor a C-level confirmation. The
only scientific delta is boundary-only external slot use versus parameter-free
policy-local retention of a validated delivered slot block until replacement.

## Frozen implementation boundary

- Both conditions use the existing real `EocivSiblingRosterEnv`, LR always-real
  actuation route, content-separating recurrent actor/value network, B3
  `GAE_NORM`, ordinary external team reward, Adam `3e-4`, gamma `0.99`, lambda
  `0.95`, complete-episode normalization, detached advantages/value target,
  gradient cap `0.5`, and one update per episode.
- `EPHEMERAL_RNN` supplies the verified external slot only at t=12/24/36 and
  supplies zero on every non-boundary step.
- `SEGMENT_LATCH_RNN` adds no trainable parameter. After base receipt
  validation and before the boundary forward, it replaces the entire float32
  latch with the delivered block. It retains that internal block without new
  actuation, receipt, or ingestion; zeros inactive rows permanently; replaces
  the whole block at the next boundary; and zeros at episode end.
- The latch consumes only validated slot bytes and the active mask. It cannot
  consume time, event/shock/A-B/arm/route/reward/future/oracle/valve or
  supervised labels.
- H=48, event times are 12/24/36, segments contain 12 steps, `K_search=0`, and
  hypothetical transitions are zero.

## Fixed plans and evidence

The full plan has seeds 86031/86032/86033, three registered profiles, 96
root-major profile-interleaved episodes per condition/seed, INIT/MID/FINAL at
0/48/96 updates, and four evaluation roots per checkpoint/profile with
CORRECT/SWAPPED/NATIVE_NEUTRAL. Counts are 576 training episodes/updates,
27,648 training transitions, 648 evaluation episodes, 31,104 evaluation
transitions, and 58,752 total real environment transitions/policy calls.

The smoke keeps both conditions, one seed, all profiles/checkpoints/arms, two
training episodes per profile, MID=3, and one evaluation root. Counts are 12
training episodes/updates, 54 evaluation episodes, and 3,168 total real
transitions. IDs use condition-absent bases 10,000,000 (train), 11,000,000
(INIT), 12,000,000 (MID), and 13,000,000 (FINAL).

Raw output retains every training row and evaluation root/arm, bounded focal
lag evidence for t=12 and t=36, paired per-root lag distances/differences,
root distributions, checkpoint changes, nine paired condition cells,
early/late reward absolute mass and shares, state digests, matching proof,
counts, and real-call booleans. `scientific_disposition` stays null and the C
license stays false regardless of observed signs.

## Traceability matrix

| Explorer brief section | Frozen claim | Exact code symbol | Focused proof | Alternate explanations excluded |
|---|---|---|---|---|
| Exact `SEGMENT_LATCH_RNN` semantics | Receipt verification precedes whole-block latch replacement; boundary effective slot equals delivery | `RetentionPolicy.accept_verified_slot`, `RetentionEpisodeRunner.bound_step` | `test_actual_runner_validates_before_accepting_exact_boundaries_and_latches_neutral` | Re-publication, unverified bytes, route/arm label access, neutral-as-zero |
| Inactive-row and lifecycle rules | Start/end zero, per-step inactive clearing, no stale reactivation, whole-block replacement | `RetentionPolicy.initial_state`, `RetentionPolicy.forward`, `RetentionPolicy.end_episode` | `test_parameter_free_latch_starts_and_ends_zero_without_actor_delta`, `test_latch_retains_replaces_whole_block_and_never_reactivates_stale_row` | Recurrent leakage across episodes, partial overwrite, inactive-row resurrection |
| Pre-run matched-material freeze | Conditions share initialization, roots, order, noise, host, architecture, optimizer and checkpoints | `episode_id`, `_train_actor`, `_evaluate_checkpoint`, `run_experiment` matching proof | `test_registered_plans_counts_and_nonoverlapping_matched_ids_are_exact`, `test_registered_smoke_is_real_matched_complete_and_canonical` | Root/order/noise/host/parameter confounding |
| Fixed budget ceiling | Exact full and smoke episode/update/transition counts with one real policy call per transition | `ExperimentPlan`, `FULL_PLAN`, `SMOKE_PLAN`, `run_experiment` count assertions | `test_registered_plans_counts_and_nonoverlapping_matched_ids_are_exact`, `test_registered_smoke_is_real_matched_complete_and_canonical` | Budget drift, hidden hypothetical search, serial rescue budget |
| Checkpoint three-arm evaluation | All arms retain actual delivered content and unchanged real routes/receipts/costs | `_make_runner`, `_arm_record`, `_evaluate_checkpoint` | `test_actual_runner_validates_before_accepting_exact_boundaries_and_latches_neutral` | Neutral zero-vector substitution, receipt-count or ingestion-cost changes |
| Required discriminating evidence | Focal 24-step raw traces, paired lag metrics, root distributions, checkpoint and paired-condition changes | `_lag_evidence`, `_paired_lag_rows`, `_condition_summaries`, `_paired_condition_changes`, `_lag_summaries` | `test_lag_schema_and_early_late_mass_math_are_exact`, `test_registered_smoke_is_real_matched_complete_and_canonical` | Favorable-only filtering, full-capacity trace expansion, early/late aggregation ambiguity |
| Interpretation rule and boundary | Mechanical completion never encodes a scientific gate or direction | `run_experiment` result envelope and `interpretation_boundary` | `test_registered_smoke_is_real_matched_complete_and_canonical` | Promotion/retirement/C licensing inferred from sign |

## Accepted exploratory result

The one full accepted run is
`eociv_b4_recurrent_retention_learnability_508bdf40_r2`; its public compact
record is `RECURRENT_RETENTION_LEARNABILITY_RESULT.json`, and its ignored raw
evidence root is
`logs/eociv_b4_recurrent_retention_learnability_508bdf40_r2`. The preceding
`r1` attempt failed before import or scientific execution and remains
preserved with scientific iteration cost zero.

The matched result is mechanically complete and numerically finite. At FINAL,
the segment latch moved the absolute reward-difference mass into lags 4--11,
but its paired FINAL-minus-INIT direction was heterogeneous across the two
registered contrasts and nine seed/profile cells. This is a nonterminal B
diagnosis only: scientific disposition remains null and the registered C
license remains false.

## Interpretation limit

The implementation can establish only that the frozen matched experiment ran
and that its requested evidence was retained. Positive, negative, zero, or
heterogeneous outcomes remain nonterminal B diagnostics. No result from this
package selects a successor, alters the direction, tunes a valve, licenses C,
or supports deployment/generalization.
