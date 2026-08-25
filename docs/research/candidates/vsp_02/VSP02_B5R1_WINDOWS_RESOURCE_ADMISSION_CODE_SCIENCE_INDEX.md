# VSP02-B5R1 Windows resource-admission code-science index

This is an implementation-intent and readiness index, not a registered-full
result or an acceptance record. The reserved repository result remains absent.

```text
direction=CAND-VSP-02
candidate=CAND-VSP-02@adversarial-revision-v10
treatment=VSP02-B5R1-FULL-ADAM-STATE-CONTINUITY
registered_full=VSP02-B5R1-REGISTERED-FULL-01
implementation_base=204af1e02372686e9e51eb592ea60897076237ed
freeze_publication_commit=204af1e02372686e9e51eb592ea60897076237ed
freeze_handoff=C:/Projects/HMASD/temp/handoffs/explorer_to_code_manager/2026-08-11_vsp02_b5r1_windows_resource_admission_implementation.md
freeze_handoff_sha256=86e2327e1895be8a9a7ced0304b62c9b4833e82943bfba0012c4398ae16be0f8
units=VSP02-B5R1-U01..VSP02-B5R1-U05
roots=22051001..22051005
seed_prefix=VSP02-B5R1-V1\0
evidence_complexity=H=4|K_search=0|hypothetical_transitions=0
caps=one full|30 CPU minutes|2 GiB|57400 transitions|10200 training episodes|1280 evaluation episodes|1275 optimizer steps|10 checkpoints
reserved_result=docs/research/candidates/vsp_02/VSP02_B5R1_WINDOWS_RESOURCE_ADMISSION_RESULT.json
```

| claim_id | frozen_assertion_path_and_section | code_path::symbol | observable_invariant | focused_test::test_name | alternate_explanation_excluded |
|---|---|---|---|---|---|
| B5R1-C01 | Freeze packet, “Fresh candidate and unchanged science” | `vsp02_b5r1_windows_resource_admission.py::B5R1_UNITS`, `b5r1_seed`, `B5R1AddressTape`, `seed_and_tape_report` | Fresh identities, five roots, six seed streams, address-indexed tape, and no predecessor reuse or silent reseed | `test_fresh_exact_namespace_roots_streams_and_no_predecessor_collision`; `test_fresh_address_tape_is_pure_immutable_and_reproducible` | B1-B5/G52 root, seed, tape, checkpoint, batch, model, optimizer, or result reuse |
| B5R1-C02 | Freeze packet, “Fresh candidate and unchanged science” | `vsp02_b5r1_windows_resource_admission.py::_clone_post_update0`, `adam_state_report`, `_train_unit` | The arms remain exactly `ADAM_CARRY` and `ADAM_RESET`, with complete post-update-0 Adam state as the sole intervention | `test_complete_adam_fork_reset_update1_and_q_are_proven_for_every_root` | Component reset, hyperparameter drift, or mutation of parameters, recurrent state, counters, RNG, schedule, or tape position |
| B5R1-C03 | Freeze packet, “Fresh candidate and unchanged science” | `vsp02_b5r1_windows_resource_admission.py::_one_boundary_proof`, `_prepare_update`, `_train_unit` barrier receipts | One common update 0 precedes a byte-identical update-1 batch, forward values, loss, raw/clipped gradients, norm and factor; every root has positive finite q; updates 2-127 are unmatched descendants | `test_update1_equality_covers_forward_loss_raw_and_clipped_gradients_norm_factor`; `test_common_update0_and_later_fixed_order_noninterference_with_immutable_batches` | Data, gradient, ordering, cross-arm contamination, inactive intervention, or later matching explains the contrast |
| B5R1-C04 | Freeze packet, “Fresh candidate and unchanged science” | `vsp02_b5r1_windows_resource_admission.py::B5R1LifecycleHost`, `_loss_terms`, `_collect_batch`, `_evaluation_panel`, `_derive_retained_evaluation_metric` | Host, oracle-sign actor/critic loss, behavior mixture, immutable batches, fixed order, held-out 64/64 panels, and exact no-tie endpoint are unchanged | `test_source_uses_only_stable_b1_a1_primitives_and_defines_fresh_host_and_tape`; `test_oracle_firewall_sign_magnitude_detach_and_no_direct_label_loss`; `test_retained_evaluation_metric_recomputes_exact_panel_and_rejects_row_or_summary_tampering`; `test_predecessor_b5_protected_semantics_equivalence_excluding_fresh_identity_and_admission_delta` | Host, loss, behavior, evaluation, direct-label, checkpoint-selection, or summary-trust drift creates the outcome |
| B5R1-C05 | Freeze packet, six ordered branch literals | `vsp02_b5r1_windows_resource_admission.py::B5R1_BRANCH_PRECEDENCE`, `classify_b5r1` | All six exact B5 branch literals retain first-match order and narrow finite-panel meanings | `test_six_branch_first_match_precedence_is_total` | Overlapping, reordered, scalar-selected, or post-result-repaired branch meaning |
| B5R1-C06 | Freeze packet, registered counts and caps | `vsp02_b5r1_windows_resource_admission.py::B5R1_CAPS`, `build_manifest`, `analyze_registered_full`, `validate_result` | Exact counts are 1,275 optimizer steps, 10,200 training episodes, 1,280 evaluation episodes, 10 checkpoints, at most 57,400 transitions, one pool unit/full, 30 CPU minutes, 2 GiB, and zero retry/rescue/sweep/extra root/checkpoint/threshold/boundary | `test_manifest_freezes_counts_caps_complexity_no_retry_and_nonclaims`; `test_retained_validators_have_no_runtime_call_surface` | Hidden activity, replay, extra evidence, cap extension, or validator runtime changes the result |
| B5R1-C07 | Corrected handoff, “Sole implementation delta and admission proof” | `vsp02_b5r1_windows_resource_admission.py::_peak_process_rss_bytes` | Windows helper uses local callable bindings, pointer-width process handle, typed memory-counter pointer/DWORD arguments, BOOL return, and raises `OSError` on false BOOL | `test_windows_ctypes_signature_contract_and_false_bool_failure` | Implicit ctypes defaults, truncated handle, or ignored false BOOL supplies a misleading RSS |
| B5R1-C08 | Freeze packet, “Sole admission delta” | `vsp02_b5r1_windows_resource_admission.py::resource_admission_receipt`, `validate_resource_admission_receipt` | Production admission fails closed unless real Windows RSS is a positive non-bool int within 2 GiB and binding, process, CPU, cap, freshness, and exact zero-start metadata are valid | `test_real_windows_resource_admission_receipt_is_positive_finite_and_zero_activity`; `test_resource_admission_fails_closed_on_invalid_rss_and_metadata` | Fallback, skip, synthetic, inferred, stale, non-Windows, malformed, or over-cap RSS passes admission |
| B5R1-C09 | Freeze packet, “Sole admission delta” and “Execution and review gate” | `run_vsp02_b5r1_windows_resource_admission.py::_readiness_command`, `_require_bounded_readiness` | Bounded readiness calls the real helper and retains exact receipt fields; validation/reload bind digest and byte stability; all six readiness phases remain zero activity and full-only | `test_runner_write_once_claim_source_binding_and_zero_runtime_readiness` | Fixture-only RSS, phase collapse, retained-byte drift, or readiness training/evaluation produces evidence |
| B5R1-C10 | Freeze packet, preclaim receipt requirement | `run_vsp02_b5r1_windows_resource_admission.py::_registered_full_command`; `vsp02_b5r1_windows_resource_admission.py::run_treatment`, `validate_result` | Registered-full obtains and validates admission before exclusive claim; claim and later result retain and cross-validate the same receipt; failed admission creates neither claim nor runtime; tampering is rejected | `test_registered_full_admission_precedes_claim_and_result_retains_exact_receipt`; `test_failed_admission_never_creates_exclusive_claim_or_starts_runtime`; `test_result_admission_receipt_tamper_is_rejected` | Postclaim measurement, runtime-before-admission, receipt substitution, or retained-field tampering is accepted |
| B5R1-C11 | Freeze packet, “Sole admission delta” and reserved-result gate | `vsp02_b5r1_windows_resource_admission.py::build_manifest`; `run_vsp02_b5r1_windows_resource_admission.py::_expect_full_only_rejection`, `RESULT_NAME` | No fallback, skip, synthetic substitute, inferred RSS, training/evaluation during readiness, or reserved result creation is permitted | `test_runner_write_once_claim_source_binding_and_zero_runtime_readiness`; `test_failed_admission_never_creates_exclusive_claim_or_starts_runtime`; `test_reserved_repo_result_remains_absent` | A technical-only path consumes a scientific iteration or creates a result artifact |
| B5R1-C12 | Corrected handoff, “Scientific contract retained verbatim” | `vsp02_b5r1_windows_resource_admission.py::build_manifest::nonclaims`, `scientific_freeze` | Disposition is `REPAIR_FRESH_CANDIDATE`, scientific literal change remains none, and all B5 nonclaims remain exact: no population, sufficiency, necessity, superiority, equivalence, component, mediator, transfer, B4-explanation, or generic Adam/self-feedback claim | `test_manifest_freezes_counts_caps_complexity_no_retry_and_nonclaims`; `test_predecessor_b5_protected_semantics_equivalence_excluding_fresh_identity_and_admission_delta` | The Windows repair is reinterpreted as a scientific change, widened claim, promotion, or B5 retry |

The six readiness phases remain distinct: interface smoke, bounded exercise,
artifact validation, artifact reload, evaluate entry, and analyze entry. Only
bounded exercise performs the real Windows RSS sample. All readiness activity
fields are exactly zero, and evaluate/analyze readiness reaches only the
production full-only rejection guards.

The sole scientific-neutral delta from the accepted B5 package is the Windows
resource-admission path and its retained receipt. No full, science, evaluation,
or result action is authorized by this index.
