# VSP05-B0 support-map code/science index

This package is the frozen candidate-independent evidence-level-A support map.
It is an experiment-stage, nonintervening real-runtime probe.  It neither
trains nor evaluates a learner and makes no prevalence, selection, promotion,
retirement, utility, or generalization claim.

| Protected assertion | Exact implementation symbols | Observable invariant | Focused test | Excluded alternate explanation |
|---|---|---|---|---|
| All six cells are fixed before outcomes | `CELLS`, `SupportCell`, `build_episode_roster` | Exact order, dynamics, geometry, roots, counts and prebuilt episode roster | `test_frozen_cells_roots_counts_and_namespace_are_exact` | Adaptive search, best-cell selection, B1 namespace reuse |
| Threshold labels are symmetric and inclusive | `classify_support_receipt`, `SupportCell.__post_init__` | Truth label 0, alias label 1, unresolved `None`; valid strict threshold ordering | `test_receipt_geometry_is_symmetric_inclusive_and_ordered` | One-sided receipt rule or threshold tuning |
| Only the local physical process recurrence changes | `CellCleanProcessDynamicRosterEnv._advance_process`, `CellCleanProcessDynamicRosterEventEnv.reset_event_runtime` | Requested damping/drive/step are applied while inherited roster, observations, reward and action support remain identical | `test_candidate_local_dynamics_change_only_requested_process_factors` | Shared-environment edits or candidate-owned reward/roster |
| Every transition uses the real executor and lifecycle core | `SupportMapVectorRuntime.create_cell`, `SupportMapVectorRuntime.advance_one` | Environment, supplied-executor and lifecycle-transaction calls equal the real transition count | `test_smoke_uses_real_runtime_and_emits_complete_zero_filled_grid` | Synthetic receipt table or inferred call counts |
| Proposal calls include joins while joins are not different-successor opportunities | `SupportMapVectorRuntime._oracle_teacher_actions`, `_category` | Proposal count is dynamic per frontier key; genuine joins start at skill 2; JOIN/REJOIN/SURVIVOR remain separate | `test_smoke_uses_real_runtime_and_emits_complete_zero_filled_grid` | Treating a join as a different-successor learner example |
| The result retains every zero support stratum | `_empty_bucket`, `_bucket_payload`, `run_support_map` | Complete cell/seed/proposed-skill/lifecycle Cartesian grid with zero rows and all membership delta kinds | `test_smoke_uses_real_runtime_and_emits_complete_zero_filled_grid` | Dropping zeros or reporting only favorable cells |
| The evidence is deterministic and nonselective | `run_support_map`, `write_result` | Canonical JSON equality on repeat; `K_search=0`; learner/trainer/update calls are zero; no best-cell field | `test_smoke_is_canonical_and_has_no_adaptive_or_best_cell_field` | Learner training, learned veto, reject tuning, cell selection, B1/C/Pro action |

## Accepted full result

CPM technically accepted the fixed full run from source commit
`27c45eb399bce9de0f706ee65ec51a37c53d87ce`. The canonical compact result is
`VSP05_B0_SUPPORT_MAP_RESULT.json`; the raw evidence remains under
`logs/vsp05_b0_support_map_27c45eb3_r1/`.

All six cells and all zero strata were retained. Across 432 episodes and
34,560 real transitions, the map observed 141 gated examples, all of them
alias, and zero strict-truth examples. No cell was two-sided. This is a
mechanical descriptive observation only; `scientific_disposition` remains
null and the run licenses no learner comparison, C treatment, External Pro
review, or change to the queued EOCIV-B5 decision.
