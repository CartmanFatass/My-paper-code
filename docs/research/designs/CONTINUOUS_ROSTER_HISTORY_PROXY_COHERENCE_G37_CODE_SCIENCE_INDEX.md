# G37 code-science critical-point index

```text
algorithm_id=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37
source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_P0
scientific_contract=docs/external-review/rounds/20260726_continuous_roster_history_proxy_coherence_g37_design_assertion_audit/21_PRO_OPEN_RAW.md
implementation_commit=bound_by_git_identity
review_mode=CODE_SCIENCE_ALIGNMENT_AUDIT
```

| claim_id | frozen_assertion_path_and_section | code_path::symbol | observable_invariant | focused_test::test_name | alternate_explanation_excluded |
|---|---|---|---|---|---|
| G37-C1 | `21_PRO_OPEN_RAW.md` §2.1--2.5 | `ha_ctse_process/continuous_roster_history_proxy_coherence_g37.py::G37FactorizedHistoryProxyTape` | each active coordinate is an exact independently addressed selected/permuted column from the byte-identical G36 active-count bank; inactive rows are zero | `tests/ha_ctse_process_continuous_roster_history_proxy_coherence_g37_test.py::test_factorized_tape_uses_exact_independent_column_streams` | one shared snapshot/permutation, scalar constants, distinct-draw rejection, post-selection clipping or donor reweighting |
| G37-C2 | `21_PRO_OPEN_RAW.md` §2.6 | `ha_ctse_process/continuous_roster_history_proxy_coherence_g37.py::evaluate_g37_factorized_history_proxy` -> `continuous_roster_history_proxy_free_cs_g36.py::build_g36_actor_input_without_history` | actor source coordinates 6:10 are never materialized; only active proxy rows are written; critic is unchanged | `tests/ha_ctse_process_continuous_roster_history_proxy_free_cs_g36_test.py::test_evaluator_never_copies_source_history_before_substitution` | target-history leakage, critic intervention or inactive-row filler |
| G37-C3 | `21_PRO_OPEN_RAW.md` §3.1--3.3 | `scripts/run_continuous_roster_history_proxy_coherence_g37.py::_g36_reference` | exact G36 source/branch/evaluation and analysis digests, G35 package/checkpoints, full traces and recomputed metrics validate before G37 use | `tests/run_continuous_roster_history_proxy_coherence_g37_test.py::test_bootstrap_seed_and_dedicated_authority_are_frozen` | rerun or substituted G36 baseline, checkpoint drift, summary-only trust or source mismatch |
| G37-C4 | `21_PRO_OPEN_RAW.md` §3.2--3.4, §5 | `scripts/run_continuous_roster_history_proxy_coherence_g37.py::evaluate` and `_evaluation_errors` | one tape is reused across mode and matching fixed/random count traces; exact G36 member-owned action-noise digests pair every joint/factorized cell | `tests/ha_ctse_process_continuous_roster_history_proxy_coherence_g37_test.py::test_nonformal_offset_and_inactive_rows_are_exact` | process-conditioned factorization, mode-specific proxy redraw or unpaired stochastic action noise |
| G37-C5 | `21_PRO_OPEN_RAW.md` §4--§7 | `scripts/run_continuous_roster_history_proxy_coherence_g37.py::_access_and_noninferiority` and `select_g37_result_branch` | inherited access gates, joint-minus-factorized 0.05 intervals and exact first-match order use one paired whole-episode plan | `tests/run_continuous_roster_history_proxy_coherence_g37_test.py::test_first_match_truth_table_is_exact` | threshold rescue, reversed contrast, per-metric resampling or diagnostic relabeling |
| G37-C6 | `21_PRO_OPEN_RAW.md` §8 | `scripts/run_continuous_roster_history_proxy_coherence_g37.py::_configuration`, `_validate_formal_preflight` and `evaluate` | nonformal is 4,608 and formal at most 221,184 real transitions, zero optimizer steps, `K_search=0`, projected within 28,800 seconds and gated by the dedicated token | `tests/run_continuous_roster_history_proxy_coherence_g37_test.py::test_configuration_freezes_inventory_and_zero_training` | training, hypothetical search, oversized evidence, cross-commit preflight or ungated formal run |

File names, array storage, vectorization, serialization, telemetry and batching
are implementation-only. Every row above maps only a Pro-frozen field or the
smallest observable proof that excludes its named alternate explanation.
