# VSP05-A1 truth-reachability decomposition code/science index

This package prepares the single fixed recovery trace for
`VSP05-A1-TRUTH-REACHABILITY-DECOMPOSITION`. It is an evidence-level-A,
nonintervening real-runtime observation of `CAND-VSP-05@adversarial-revision-v7`.
It does not train a learner, modify the proposal or environment, advance a
hypothetical transition, select a cell, or make a direction decision. The
registered full pass is intentionally unexecuted in this implementation
package; CPM owns its later dispatch and technical acceptance.

| Protected assertion | Exact implementation symbols | Observable invariant | Focused test | Excluded alternate explanation |
|---|---|---|---|---|
| The recovery pass reuses the complete frozen B0 roster | `FULL_CONFIG`, `SMOKE_CONFIG`, `build_episode_roster`, `_episode_index_from_id` | Six cells, roots 68101–68103, 24 episodes per cell/seed, horizon 80, 432 episodes, 34,560 transitions and the B0 episode namespace are unchanged | `test_registered_configuration_and_namespace_are_exact_b0_reuse` | Adaptive cell/seed search, favorable selection, namespace drift |
| Every real row is captured after membership commit and before policy/current primitive stepping | `TruthReachabilityVectorRuntime._oracle_teacher_actions`, `TruthReachabilityVectorRuntime._capture_preframe`, `CAPTURE_BOUNDARY` | Bound transaction is consumed once; committed records exist; environment, core, transaction and completed-transition clocks all equal the current step | `test_capture_is_after_membership_commit_and_before_current_primitive_step` | Pre-commit classification, post-action state, hypothetical state reconstruction |
| Joins remain visible but are never incumbent-bearing opportunities | `_category`, `TruthReachabilityVectorRuntime._capture_preframe` | JOIN rows have committed records, semantic incumbent absent, and `different_successor=false`; REJOIN/SURVIVOR require a committed active skill | `test_capture_is_after_membership_commit_and_before_current_primitive_step` | Treating the newly created join record as an incumbent |
| Lifecycle event ranks retain B0's exact counter and are not advanced by the hook | `TruthReachabilityVectorRuntime._oracle_teacher_actions`, `TruthReachabilityVectorRuntime._capture_preframe` | Each episode/key sequence is exactly `1..n`; the hook only snapshots the already-incremented B0 counter | `test_event_ranks_are_exact_per_key_and_never_double_incremented` | Double-ranked events or a second trace-owned counter |
| Gate and strict truth are classified for every skill at the same real physical state | `classify_support_receipt`, `TruthReachabilityVectorRuntime._capture_preframe` | Skills 0, 1 and 2 exactly match the existing cell classifier; strict truth always implies gate | `test_all_skill_classification_matches_existing_frozen_classifier` | Candidate-local threshold reinterpretation or per-skill state drift |
| The evidence retains a complete simultaneous mask and every tied semantic failure | `MASK_FIELDS`, `semantic_missing_predicates`, `semantic_near_miss_class`, `_mask_code` | Eight mask fields are bound together; all false semantic predicates are returned; failed gate is not double-counted when actual strict truth is false | `test_complete_mask_and_missing_set_are_simultaneous_not_first_blocker` | Check-order “first blocker” or gate/truth double counting |
| Zero strata remain auditable | `_complete_tables`, `_marginal_table`, `NEAR_MISS_DOMAIN`, `TRUTH_SET_DOMAIN` | All 256 masks and 64 tied near-miss classes are emitted including zeros, with zero-retaining cell, seed, cell/seed, lifecycle, incumbent, proposal and truth-set marginals | `test_zero_retaining_mask_and_stratified_tables_are_complete` | Dropped zeros or favorable-stratum reporting |
| Hypothetical incumbent compatibility is static bookkeeping only | `_static_row`, `_static_tables` | Every real row has exactly three incumbent classifications, each marked `static=true`, `reachable_evidence=false`, with zero hypothetical environment transitions | `test_static_compatibility_is_complete_and_never_real_reachability` | Counterfactual rows counted as physical/lifecycle reachability |
| Runtime activity is real and prohibited learning/search activity remains zero | `run_truth_reachability_decomposition`, `TruthReachabilityVectorRuntime.advance_one` | Real environment, supplied executor and lifecycle calls equal registered transitions; proposal calls equal real frontier rows; learner/trainer/optimizer/hypothetical-transition calls are zero | `test_smoke_real_activity_and_protected_zero_calls_are_exact` | Synthetic-only analysis, hidden learner call, post-outcome extension |
| The read-only hook is behaviorally nonintervening | `run_differential_nonintervention_smoke`, `_deep_equal` | Same-root A1 and B0 runs have identical primitive actions, rewards, decisions, membership evidence, lifecycle audit and transition/proposal counts | `test_differential_smoke_proves_nonintervention_on_real_runtime` | RNG, action, reward or lifecycle perturbation from logging |
| Serialization and finite branch mapping are deterministic | `_decision_branch`, `write_result`, `run_truth_reachability_decomposition` | Repeated smoke payloads and canonical JSON are identical; exactly one frozen finite-evidence branch is emitted while underlying tables remain present | `test_smoke_is_deterministic_and_json_canonical` | Result-aware branch selection, global impossibility, scientific disposition |

## Result lifecycle

The runner writes raw real frontier rows, all static compatibility rows,
zero-filled tables, exact activity counts and one finite-evidence decision-map
branch. A later CPM-owned full run may publish a compact public result while
retaining its raw output under the frozen run identity. Until that run is
technically accepted, this index records implementation/readiness claims only;
it licenses no B learner comparison, C treatment, External Pro review,
promotion, retirement, global reachability claim, or sibling/portfolio claim.
