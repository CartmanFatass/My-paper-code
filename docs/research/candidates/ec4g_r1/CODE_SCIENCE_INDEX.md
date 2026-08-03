# EC4G-R1 execution-digest census: code-science index

Candidate: `CAND-VAP-EC4G-R1@adversarial-revision-v7`

Treatment: proof-sized deterministic `EC4G-EXECUTION-DIGEST-CENSUS-D1`

Status of this evidence: synthetic implementation conformance only.

This tracked index is self-contained so an external reviewer can inspect the
exact pushed revision without access to temporary cross-role handoff files. It
does not claim that an empirical project EC4G cell exists or that EC4G has
operational value.

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

The census compares continuation bytes, external cost, and the digest binding
both—not action labels alone. Its only terminal values are
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
| Exact receipt schema, authorization, executor/source/version, envelope, payload-support, safe-mask, pre-outcome donor, no same-event/trajectory donor, no assignment leak | `experiments/candidates/ec4g_r1/execution_digest_census.py::_validate_receipts` | `tests/experiments/candidates/ec4g_r1/test_execution_digest_census.py::test_contract_and_donor_failures_return_incomplete_contract` |
| Seven-arm means, one-time external cost, PSD covariance, named support conjunction, executor measure, fallback and P/N/A continuations | `experiments/candidates/ec4g_r1/execution_digest_census.py::_validate_cell` | `::test_cost_is_subtracted_once_and_pseudo_arms_are_report_only`; `::test_continuation_digest_binds_cost_and_bytes_and_fallback_binding` |
| Fixed EC4G and Direct-tau maps share one immutable object | `experiments/candidates/ec4g_r1/execution_digest_census.py::ec4g_gate`; `::direct_tau_gate`; `::run_census` | `::test_same_cell_object_reaches_both_maps_and_output_is_byte_stable`; `::test_both_gate_branch_tables_cover_unsupported_probe_no_probe_and_abstain` |
| Exact witness intervals, identities, actions, digests, point difference and upper bound | `experiments/candidates/ec4g_r1/execution_digest_census.py::build_synthetic_witness`; `::compute_contrasts` | `::test_exact_single_cell_witness_is_supported_behavioral_discordance` |
| Exactly four terminal classifications; label-only is not behavioral | `experiments/candidates/ec4g_r1/execution_digest_census.py::run_census` | `::test_census_returns_all_four_and_only_four_terminal_classes` |

## Bounded execution receipt

Deterministic command:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -c "from experiments.candidates.ec4g_r1.execution_digest_census import build_synthetic_witness,run_census; print(run_census(build_synthetic_witness()).to_bytes().decode('utf-8'))"
```

Raw canonical output:

```json
{"cells":[{"behavior_equal":false,"cell_id":"x0","confidence_upper_bound":-0.08,"contrasts":{"tau_A":{"estimate":0.02,"lower":-0.000615528128,"standard_error":0.020615528128,"upper":0.040615528128},"tau_B":{"estimate":0.12,"lower":0.099384471872,"standard_error":0.020615528128,"upper":0.140615528128},"tau_C":{"estimate":-0.04,"lower":-0.06,"standard_error":0.02,"upper":-0.02},"tau_T":{"estimate":0.1,"lower":0.08,"standard_error":0.02,"upper":0.12},"tau_V":{"estimate":-0.02,"lower":-0.035,"standard_error":0.015,"upper":-0.005}},"direct_tau":{"action":"P","continuation_digest":"502fefe74d3ce22c5f87468b44c418d0c585b675ec525367f06e0f6978e4614e","external_cost":0.0},"ec4g":{"action":"A","continuation_digest":"4232fd86d314ea3413f6aafeabd1b4548e6cf75d083d5766c688646a13135b99","external_cost":0.0},"executor_measure":1.0,"label_equal":false,"nu":[0.0,0.1,0.12,0.14,0.0,0.0,0.0],"point_value_difference":-0.1,"support":true}],"classification":"BEHAVIORAL_DISCORDANCE","issues":[]}
```

Focused validation:

```text
14 passed in 0.16s
```

Mechanical disposition: `PASS_SYNTHETIC_ACTION_MAP_AND_CENSUS_CONFORMANCE`.
The run used one immutable cell, zero environment transitions, zero training
updates, and zero return-bearing rollout. The accepted revision is the exact
Git commit containing this index, source, and mirrored test; its public
commit-pinned URLs are returned to Explorer after push.
