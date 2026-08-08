# VSP05-A2 lifecycle-phase support discrimination — code/science index

This package implements the single frozen A2 treatment for
`CAND-VSP-05@adversarial-revision-v7`. It is an A-level real-runtime instance
discriminator. It does not contain a learner, optimizer, search, hypothetical
transition, schedule tuning, or a second treatment.

## Frozen scientific delta

The immutable accepted A1 full trace is the historical control. Its raw file
must hash to
`d4ba7e00ae65c4f0cfd6f84b37c300e9e580868c42bd3c3f02eff20b0b3a3f2e`,
its implementation revision must be
`1a09bccf9bd64c756865531bc55a871afa286dd3`, and its public result revision is
`9f3c57f809a0c0ee11868e025adbeea762832a46`.

The treatment changes exactly two temporary leaves per episode from physical
time 20 to time 19. Time-40 rejoin and every other membership event remain
unchanged. The full roster remains six frozen cells, seeds 68101/68102/68103,
24 episodes per seed/cell, horizon 80: 432 episodes and 34,560 new real
transitions. This compiles to 864 leave shifts and 864 unchanged rejoins.

## Claim-to-code map

| Frozen claim or observable | Production symbol | Focused evidence |
|---|---|---|
| Exact accepted-control file/SHA and identity are mandatory | `load_accepted_control` | `test_exact_accepted_control_binding_and_known_t19_lineage`, `test_raw_validation_rejects_namespace_activity_and_protected_count_drift` |
| Source/configuration/run identity is frozen before outcomes | `_config_identity`, `_frozen_identity` | `test_frozen_identity_binds_config_and_rejects_unfrozen_full_source` |
| Only leave time changes 20→19; rejoin stays 40 | `LifecyclePhaseCellEnv._apply_membership`, `_schedule_rows` | `test_registered_full_configuration_and_schedule_are_exact` |
| Real environment, supplied executor and lifecycle core remain in use | `LifecyclePhaseEventEnv`, `LifecyclePhaseVectorRuntime.create_cell` | `test_smoke_uses_real_runtime_and_only_the_declared_schedule_delta`, CLI equivalence smoke |
| A1 post-membership/pre-policy capture and full all-skill mask are reused | `LifecyclePhaseVectorRuntime` inherits `TruthReachabilityVectorRuntime` | `test_complete_masks_and_zero_tables_are_retained` |
| Equality through t18 and exogenous ledger identity | `run_equivalence_smoke`, `analyze_treatment` pre-treatment join | `test_cli_entrypoint_and_exact_82_transition_equivalence_smoke` |
| Each treated key is incumbent-bearing, skips one primitive, stays physically frozen while absent, and retains incumbent at t40 | `LifecyclePhaseVectorRuntime._capture_preframe` lineage audit | `test_lineage_audit_proves_skip_absence_and_no_rejoin_reset` |
| Schedule collisions, incomplete lineage or missing rejoin rows fail closed | `_schedule_rows`, `_capture_preframe`, `analyze_treatment` | `test_registered_full_configuration_and_schedule_are_exact`, `test_smoke_analysis_has_exact_pairing_and_distinguishes_skips_from_proposals` |
| Exact paired time-40 table retains state, incumbent, proposal, truth set and complete mask | `analyze_treatment` → `paired_t40_rejoin_rows` | `test_smoke_analysis_has_exact_pairing_and_distinguishes_skips_from_proposals` |
| Primitive skips are distinct from actually suppressed t19 proposals | `analyze_treatment` → `lineage_receipt` and `suppressed_t19_control_frontiers` | same test; full analysis additionally requires exactly 864 versus 88 |
| Known `STEP_HIGH/68102/20401022/key1` gated-alias lineage is explicit | full-only known-lineage assertion in `analyze_treatment` | `test_exact_accepted_control_binding_and_known_t19_lineage` |
| Favorable support on a suppression-created incumbent mismatch cannot open clean support | `classify_terminal_label`, `mismatch_lineages` | `test_mismatch_only_favorable_evidence_fails_closed_and_join_cannot_open` |
| JOIN never counts as a different-successor learner opportunity | inherited A1 mask construction plus `classify_terminal_label` | same test |
| Both clean eligible strict truth and a real gated alias are required | `classify_terminal_label` | `test_clean_two_sided_label_requires_both_real_classes_and_clean_lineage` |
| Complete masks and zero-retaining stratifications survive | inherited `_complete_tables` | `test_complete_masks_and_zero_tables_are_retained` |
| Learner/trainer/optimizer/hypothetical calls and `K_search` stay zero | `run_treatment_probe`, `_validate_raw` | `test_smoke_uses_real_runtime_and_only_the_declared_schedule_delta`, raw-drift test |
| Smoke/equivalence artifacts are technical-only and cannot emit any five-label result or route disposition | `analyze_treatment`, `evaluate_treatment`, `run_equivalence_smoke` | `test_zero_episode_smoke_cannot_emit_any_scientific_terminal`, technical smoke analysis/evaluation tests |
| Five-label classification is inaccessible without an exact validated FULL_CONFIG admission | `_ValidatedRawAdmission`, `_FullTerminalAdmission`, `_make_full_terminal_admission`, `classify_terminal_label` | classifier admission tests and full drift regression |
| Full admission binds exact configuration, 432/34,560 counts, roster, 864 schedule/paired rows, lineage coverage, known t19 row, zero counts and 82-transition equivalence | `_validate_exact_raw_contract`, `_validate_lineage_coverage`, `_validate_equivalence_receipt`, `_make_full_terminal_admission` | `test_full_config_count_roster_schedule_and_lineage_drift_fail_closed`, `test_full_equivalence_receipt_is_mandatory_and_fail_closed` |

## Runtime phases

The thin entry point is
`scripts/run_vsp05_a2_lifecycle_phase_support.py`.

- `--phase train` and `--phase probe` are identical no-learning acquisition
  aliases. Acquisition requires an explicit `--config`; there is no silent
  smoke default. They bind the accepted control first, freeze identity, then
  run the requested registered treatment configuration and write raw evidence.
- `--phase evaluate` validates and pairs raw evidence, applies the frozen
  decision map, and writes a compact evaluation receipt.
- `--phase analyze` writes the complete result, including all treatment real
  frontier rows, zero tables, 864-row rejoin table and t19 lineage audit.
- `--phase equivalence-smoke` is the sole paired control/treatment technical
  path. It executes exactly 41 control plus 41 treatment transitions (82 total)
  through the time-40 rejoin and never contributes scientific counts.

Smoke acquisition, evaluation and analysis emit only `TECHNICAL_ONLY`
artifacts. They contain no terminal label, open/park disposition,
clean-two-sided conclusion, scientific decision boundary, or historical-control
reuse-pass claim. A malformed zero-episode smoke fails before analysis rather
than mapping to `NONSEPARATING_SHIFT`.

The full acquisition requires an exact 40-hex treatment source revision, an
explicit pre-outcome run ID, and the successful separately written
82-transition equivalence receipt. Evaluation and analysis bind the same
accepted A1 SHA again and reject any full configuration, activity, namespace,
roster, 864-row schedule, lineage, membership, mask-table, known-lineage,
pairing, equivalence, or protected-zero drift before terminal classification.

## Terminal map and claim boundary

Only an exact validated full artifact can obtain the private terminal-admission
receipt consumed by `classify_terminal_label`; partial, smoke and malformed
artifacts raise before classification. The admitted classifier returns exactly
one of the five pre-registered labels. `CLEAN_TWO_SIDED_SUPPORT_OPENS` only establishes support feasibility.
Every other label parks this exact toy learner route. No label establishes
prevalence, learner value, utility, return, generalization, superiority, C
authorization, global impossibility, sibling-direction status, or portfolio
status. Scientific intake remains Explorer-owned; technical acceptance,
runtime, Git, and result publication remain CPM-owned.
