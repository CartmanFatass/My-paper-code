# EC4G-R1 execution-digest censuses: code-science index

Candidate: `CAND-VAP-EC4G-R1@adversarial-revision-v7`

Project treatment: zero-runtime deterministic
`EC4G-A1-EXECUTION-DIGEST-CENSUS`

Predecessor treatment: proof-sized deterministic synthetic conformance unit
`EC4G-EXECUTION-DIGEST-CENSUS-D1/x0`.

These are separate evidence surfaces. The synthetic x0 cell below is retained
only as a legacy action-map/conformance unit and is never a row, support fact,
mass declaration, or contract object for the registered A1 project census.

This tracked index is self-contained so an external reviewer can inspect the
exact pushed revision without access to temporary cross-role handoff files. It
does not claim that an empirical project EC4G cell exists or that EC4G has
operational value.

## Registered A1 project-binding census

The A1 source adds a pure validator/analyzer and a thin one-shot runner. The
project census requires independently bound identities for the objective,
ordered decision-cell and receipt registries, coherent seven-arm joint moments,
costs, immutable decision parameters and both total maps, fallback programs,
payload-preserving donor operation, canonical execution compiler, prospective
support and deployed mass, and the source/order freeze manifest. Missing,
unfrozen, non-total, or incoherent objects return `INCOMPLETE_CONTRACT` with an
exact object witness. Missing objects are not converted into empty registries,
zero mass, synthetic rows, or vacuous support.

At the implementation revision, the project package contains no complete
prospective binding for those objects. In particular, the synthetic x0
`executor_measure=1` is not a prospective deployed-mass registry. Therefore
`build_registered_project_binding` binds no fabricated rows and records every
required object as absent. The unique registered invocation can naturally and
technically return `INCOMPLETE_CONTRACT`; `D_A` remains undefined in that
branch.

For a complete future binding supplied without changing the frozen analyzer,
the terminal precedence is:

1. `INCOMPLETE_CONTRACT` for any global or row-bound contract failure;
2. `SUPPORTED_POSITIVE_MASS_BEHAVIORAL_DISCORDANCE` when the exact active
   discordance mass `D_A` is positive;
3. `LABEL_ONLY_DIFFERENCE` when `D_A=0` and an active literal label differs;
4. `EXECUTION_EQUIVALENT` otherwise, with `vacuous_active_domain=true` only
   when a nonempty complete registry has no supported positive-mass row. An
   empty decision-cell registry is an incomplete contract, and its deployed
   mass total of zero separately fails the exact normalization check.

Program equality compares every literal receipt/donor execution branch. The
stored SHA-256 digest is audit evidence only: an equal digest never makes
unequal complete programs equivalent. Unsupported and zero-mass differences
remain full row witnesses but cannot promote the terminal branch.

The one-shot runner requires the declared lowercase 40-hex source revision to
equal checkout `HEAD`. It rejects an existing result path before binding or
analyzing any project object, then uses exclusive `xb` creation as the atomic
write guard. The
result schema carries the frozen source revision and run identity, complete
missing-object evidence, complete row programs for every admitted row, exact
decimal masses/cross-tabs, and activity counters. It invokes no environment,
policy, learner, trainer, optimizer, return evaluator, model fit, or RNG.

### A1 traceability

| Assertion | Implementation | Focused proof |
|---|---|---|
| Synthetic x0 cannot enter the project census; every absent project object is an explicit fail-closed witness | `experiments/candidates/ec4g_r1/execution_digest_census.py::build_registered_project_binding`; `::run_project_census` | `tests/experiments/candidates/ec4g_r1/test_execution_digest_census.py::test_registered_project_binding_fails_closed_with_exact_missing_objects` |
| Exact terminal precedence, exact decimal `D_A`, label-only and vacuous handling, and audit-only unsupported differences | `::run_project_census`; `::_validate_project_binding` | `::test_project_terminal_precedence_and_exact_discordance_mass`; `::test_label_only_execution_equivalent_and_vacuous_branches` |
| Complete execution programs, not supplied digests, determine equality | `CanonicalExecutionProgram.execution_equal` | `::test_complete_program_equality_overrides_a_supplied_digest_collision` |
| Source revision is frozen and result creation is one-shot | `scripts/run_ec4g_a1_execution_digest_census.py::_require_source_revision`; `::_write_new` | `::test_runner_source_freeze_and_one_shot_output_are_fail_closed` |
| Empty registries and zero total deployed mass fail closed; existing output aborts before analyzer activity | `::_validate_project_binding`; `scripts/run_ec4g_a1_execution_digest_census.py::main` | `::test_empty_declared_registry_is_incomplete_not_vacuously_equivalent`; `::test_runner_existing_output_preflight_never_constructs_or_analyzes` |

A1 nonclaims: `INCOMPLETE_CONTRACT` establishes neither equivalence nor
discordance. A positive discordance in a complete contract would establish
only supported positive-mass program difference, not positive return, causal
benefit, receipt-content value, executor invariance, transfer, promotion,
retirement, B/C readiness, External Pro need, or formal-compute readiness.

## Legacy synthetic conformance unit

## Frozen object

The ordered arms are `R0,RV,RB,RS,PV,PB,PS`. For one registered cell,
`nu_j = measured_mean_j - external_cost_j`; cost is subtracted exactly once.
All contrasts use one full seven-arm covariance matrix and one simultaneous
critical value:

```text
tau_T = nu_RV - nu_R0
tau_B = nu_RB - nu_R0
tau_A = nu_RS - nu_RB
tau_C = nu_RV - nu_RS
tau_V = nu_RV - nu_RB
L_q = tau_q - kappa*s_q
U_q = tau_q + kappa*s_q
```

The fixed maps receive the identical immutable cell statistic:

```text
g_E:
  unsupported                                      -> A
  L_T > max(0,U_F)+delta_T and L_C>delta_C
      and L_V>delta_V                              -> P
  U_T<=0 and U_F<=0                                -> N
  otherwise                                        -> A

g_D:
  unsupported                                      -> A
  L_T > max(0,U_F)+delta_T                         -> P
  U_T<=0 and U_F<=0                                -> N
  otherwise                                        -> A
```

Every expected row must satisfy the full support conjunction and have strictly
positive finite executor mass. A single failing row returns
`INCOMPLETE_CONTRACT` before either map is classified; the census never drops a
row and classifies a filtered subset.

The candidate-local immutable receipt registry fixes schema
`synthetic.receipt.v1`, executor `synthetic-executor`, source/version
`synthetic-source/v1`, latency `fixed-one-tick`, integer-tick timestamps,
channel `synthetic-channel`, four-byte payload support, public envelope
`public-envelope-v1`, and the exact safe-action-mask digest. It also fixes
`RV=GOOD`, `RB=00000000`, and `RS=SWAP`, hidden assignment, and the registered
strictly pre-outcome cross-event/cross-trajectory donor. Same-length substitute
bytes, invalid/collapsed blinds, donor changes, and non-finite donor time are
contract failures rather than admissible receipts.

Complete behavior comprises execution path (`probe`, `no-probe`, or
`fallback`), receipt variant, delivery channel, envelope identity and bytes,
body bytes, and external cost. The continuation digest binds all those fields.
The action label is deliberately excluded from behavior identity, so distinct
labels are label-only only when every complete behavior field is identical;
matching only body and cost is insufficient. Its only terminal values are
`INCOMPLETE_CONTRACT`, `EQUIVALENCE`, `LABEL_ONLY_DIFFERENCE`, and
`BEHAVIORAL_DISCORDANCE`.

## Exact synthetic witness

```text
cell_id=x0; support=1; executor_measure=1
fallback=R0; [L_F,U_F]=[0,0]
delta_T=delta_C=delta_V=0; kappa=1
nu=(R0=0,RV=.10,RB=.12,RS=.14,PV=0,PB=0,PS=0)
diag(Sigma)=(.0003,.0001,.000125,.0003,0,0,0)
```

Expected intervals are `T=[.08,.12]`, `C=[-.06,-.02]`, and
`V=[-.035,-.005]`; therefore `g_D=P`, `g_E=A`. The probe and fallback
continuations have different full execution digests, so the synthetic cell is
supported behavioral discordance. Its point difference is `-.10` and the
confidence-region upper bound is `-.08`.

## Traceability

| Assertion | Implementation | Focused proof |
|---|---|---|
| Immutable exact receipt registry: schema, executor/source/version, latency/timestamp/channel, envelope, support/length/safe-mask, RV/RB/RS bytes, hidden assignment and donor relation | `experiments/candidates/ec4g_r1/execution_digest_census.py::_REGISTERED_RECEIPT`; `::_validate_receipts` | `tests/experiments/candidates/ec4g_r1/test_execution_digest_census.py::test_exact_receipt_registry_rejects_each_mismatch` |
| Seven-arm means, one-time external cost, PSD covariance, named support conjunction, executor measure, fallback and P/N/A continuations | `experiments/candidates/ec4g_r1/execution_digest_census.py::_validate_cell` | `::test_cost_is_subtracted_once_and_pseudo_arms_are_report_only`; `::test_continuation_digest_binds_cost_and_bytes_and_fallback_binding` |
| Fixed EC4G and Direct-tau maps share one immutable object | `experiments/candidates/ec4g_r1/execution_digest_census.py::ec4g_gate`; `::direct_tau_gate`; `::run_census` | `::test_same_cell_object_reaches_both_maps_and_output_is_byte_stable`; `::test_both_gate_branch_tables_cover_unsupported_probe_no_probe_and_abstain` |
| Exact witness intervals, identities, actions, digests, point difference and upper bound | `experiments/candidates/ec4g_r1/execution_digest_census.py::build_synthetic_witness`; `::compute_contrasts` | `::test_exact_single_cell_witness_is_supported_behavioral_discordance` |
| Complete behavior identity and digest exclude labels but include path, receipt, channel, envelope, body and cost | `experiments/candidates/ec4g_r1/execution_digest_census.py::continuation_digest`; `Comparison.behavior_equal` | `::test_census_returns_all_four_and_only_four_terminal_classes`; `::test_body_and_cost_only_clone_is_still_behaviorally_different`; `::test_continuation_digest_binds_cost_and_bytes_and_fallback_binding` |
| Whole-domain admission and exactly four terminal classifications | `experiments/candidates/ec4g_r1/execution_digest_census.py::_validate_cell`; `::run_census` | `::test_every_expected_row_must_be_supported_with_positive_finite_mass`; `::test_whole_positive_domain_classifies_all_rows_without_filtering` |

## Bounded execution receipt

Deterministic command:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -c "from experiments.candidates.ec4g_r1.execution_digest_census import build_synthetic_witness,run_census; print(run_census(build_synthetic_witness()).to_bytes().decode('utf-8'))"
```

Raw canonical output:

```json
{"cells":[{"behavior_equal":false,"cell_id":"x0","confidence_upper_bound":-0.08,"contrasts":{"tau_A":{"estimate":0.02,"lower":-0.000615528128,"standard_error":0.020615528128,"upper":0.040615528128},"tau_B":{"estimate":0.12,"lower":0.099384471872,"standard_error":0.020615528128,"upper":0.140615528128},"tau_C":{"estimate":-0.04,"lower":-0.06,"standard_error":0.02,"upper":-0.02},"tau_T":{"estimate":0.1,"lower":0.08,"standard_error":0.02,"upper":0.12},"tau_V":{"estimate":-0.02,"lower":-0.035,"standard_error":0.015,"upper":-0.005}},"direct_tau":{"action":"P","body_hex":"70726f62652d6f6e63652d7468656e2d66726f7a656e2d636f6e74696e756174696f6e","continuation_digest":"0a2cf7bd4bb4790cd81322daf0a62e73bd629cff7d2a1e50400ca1d9532d03b0","delivery_channel":"synthetic-channel","envelope_bytes_hex":"474f4f44","envelope_id":"public-envelope-v1","execution_path":"probe","external_cost":0.0,"receipt_variant":"RV"},"ec4g":{"action":"A","body_hex":"66616c6c6261636b2d72302d66726f7a656e2d636f6e74696e756174696f6e","continuation_digest":"78f2b3900f99b2a716dd58d3caa5064018006f8c1a6c113147e88c6b0a24752c","delivery_channel":"synthetic-channel","envelope_bytes_hex":"53574150","envelope_id":"public-envelope-v1","execution_path":"fallback","external_cost":0.0,"receipt_variant":"RS"},"executor_measure":1.0,"label_equal":false,"nu":[0.0,0.1,0.12,0.14,0.0,0.0,0.0],"point_value_difference":-0.1,"support":true}],"classification":"BEHAVIORAL_DISCORDANCE","issues":[]}
```

Focused validation:

```text
35 passed in 0.23s
```

Mechanical disposition: `PASS_SYNTHETIC_ACTION_MAP_AND_CENSUS_CONFORMANCE`.
The run used one immutable cell, zero environment transitions, zero training
updates, and zero return-bearing rollout. The accepted revision is the exact
Git commit containing this index, source, and mirrored test; its public
commit-pinned URLs are returned to Explorer after push.

Narrow nonclaims: this proves synthetic contract and action-map conformance
only. It does not establish an empirical EC4G cell, natural receipt
availability, positive deployed executor mass, transport safety, causal effect,
or operational value.
