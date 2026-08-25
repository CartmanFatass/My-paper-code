# EC4G-A4 code-science index

## Frozen implementation boundary

`EC4G-A4-TWO-PHASE-EXECUTION-MATERIALIZATION-CENSUS` is implemented by
`experiments/candidates/ec4g_r1/two_phase_execution_materialization_census.py`
and its one-shot entry point
`scripts/run_ec4g_a4_two_phase_execution_materialization_census.py`.

The implementation authenticates only the accepted immutable contract at C0
(`c0beef960f5f731f0c994ecd2298a1e889210c7b`, blob
`6d37b33c933ee16f89186a507e67e1080b674ca0`, SHA-256
`0d0c9b6f24ae2bb96fc0a3f542c737557f1cd66be1edbdb72d809dfce9bb0183`)
and its accepted C1 binding record at
`ba9eae5cfc21c014f210e061561fe7b8f47f5592` (SHA-256
`495702d04188a929e62e1e8d178bde84ed156dc83beab10106c67e612a50baef`).
The callable `M_E`, `M_D`, and `Gamma` semantics are derived from those
authenticated literals. Predeclared action predictions, separation metadata,
the prospective prediction object, and predicted `D_RER3` are never read.

Before the first call, `freeze_design` fixes the implementation revision and
entry points, six-row schema, cell-major/map order, three pair order,
compared-field projection and exclusions, exact masses/formula, six terminal
branches, and every hard cap. The runner additionally requires both entry-point
files to be byte-identical to the declared checkout revision.

Evidence complexity is constant: `H` is not used, `K_search=0`, hypothetical
transitions are zero, and work is exactly six map calls, six compilations and
three comparisons. No environment, policy, learner, trainer, optimizer,
evaluation, model fit, RNG, retry, rescue, rescan, repair, or substitution is
present.

## Critical-point traceability

| Frozen assertion | Implementation | Focused wrong-implementation proof |
|---|---|---|
| C0/C1 are exact, non-self-referential, ordered fourteen-role bindings | `authenticate_immutable_inputs` | `test_forbidden_information_flow_precedes_materialization_and_invalidates_all_evidence`; exact immutable fixture authentication in every complete test |
| Maps use support, intervals, fallback and thresholds rather than prediction fields | `map_ec4g`; `map_direct_tau`; `_decision_literals`; `_validate_map_declaration` | `test_maps_ignore_all_prediction_metadata_and_derive_actions_from_decision_literals` |
| `Gamma` binds complete branch behavior, receipt envelope plus RV/RB/RS bodies, budget/cost/reward, post-mask and memory | `compile_gamma`; `_canonical_projection` | missing/default/substitute parameterization in `test_missing_default_or_substituted_rows_fail_before_the_barrier` |
| Phase 1 is exact cell-major/map order and cannot compare or aggregate before six complete rows | `materialize_and_seal_phase1`; `_validate_complete_rows` | `test_complete_census_is_cell_major_exact_and_uses_all_hard_caps`; `test_sixth_compilation_failure_has_no_early_comparison_or_D_and_exact_counts` |
| Six canonical objects/receipts are closed into one content-addressed write-once snapshot and external manifest | `materialize_and_seal_phase1`; `_write_new`; `Phase1Seal` | `test_every_postseal_change_or_import_invalidates_before_comparison`; `test_existing_artifact_root_refuses_overwrite_before_any_map_call` |
| Phase 2 independently enumerates the sealed file set, recomputes snapshot/manifest and six object SHA-256 identities, enforces content-addressed filenames/manifest linkage, and revalidates row/object/receipt order and schema without trusting in-memory bytes, digests, or `canonical_valid`; every object key set must equal the nine compared fields plus two exclusions exactly | `census_sealed_phase2`; `_reopen_and_validate_sealed_artifacts`; `_validate_complete_rows`; `_validate_construction_receipt` | complete call-order proof; snapshot/object/import post-seal mutation parameterization; stale-filename tamper with replaced in-memory expected bytes; digest-consistent extra/missing-excluded/missing-compared key regressions; independent stdlib artifact validator |
| All three fixed pairs are attempted without early stop; equality uses exact canonical compared-field bytes, never supplied hashes | `census_sealed_phase2`; `_canonical_projection` | `test_all_three_pairs_are_attempted_without_early_stop_and_D_is_withheld_on_incomplete`; `test_equality_compares_canonical_fields_not_supplied_hashes` |
| Exact `Fraction` and `Decimal` D exist only after three complete witnesses | `census_sealed_phase2`; `run_two_phase_census`; `CensusResult.payload` | incomplete-compilation and incomplete-witness tests; complete hand-checkable configured-population fixture |
| Six-branch precedence, exact counts, ten digest identities, and no future publication self-reference remain visible | `CensusBranch`; `HARD_CAPS`; `run_two_phase_census`; `CensusResult.payload` | `test_complete_census_is_cell_major_exact_and_uses_all_hard_caps`; `test_result_has_no_future_publication_identity_and_is_byte_stable` |
| Claim and output are one-shot | runner preflight and `_write_new`; Phase-1 exclusive directory/file creation | overwrite-refusal proof above; runner `--help` smoke |

The focused external-consumer proof parses the artifact with Python stdlib
only. It independently checks all ten SHA-256 identities, exact file and row
order/schema, compared projection and exclusions, three witnesses, and exact
`Fraction`/`Decimal` D while mapper, compiler, and module equality helpers are
replaced with fail-fast sentinels.

## Result and authority boundary

The source package does not invoke a registered audit, readiness verifier,
formal compute, publication, Git operation, Operator transport, or technical
acceptance. Component and temporary-fixture tests exercise the phase barrier;
they are not a registered EC4G-A4 result. The result schema therefore leaves
the publication revision unset and records Operator receipt, readiness, and
technical acceptance as CPM-owned pending/not-invoked states.

A complete artifact describes only structural execution-program discordance
for the frozen configured three-cell population. It does not establish an A2
repair, natural prevalence, causal receipt value, reward or return superiority,
learning, B/C evidence, formal-compute need, External Pro need, promotion,
retirement, or an automatic successor.
