# VSP-04 Sequence 10 code-science evidence index

## Scope and traceability

- Candidate: `CAND-VSP-04-MATCHED-BOUNDARY-REQUEST-TRIAD@adversarial-revision-v8`
- Treatment: `VSP-04-STACKED-FINITE-CELL-KNOCKOFF-CERT-D0`
- Implementation: `experiments/candidates/vsp_04/matched_boundary_rational_certificate.py`
- Proof-sized tests: `tests/experiments/candidates/vsp_04/test_matched_boundary_rational_certificate.py`
- Frozen literal-table result: the 13-row `PRIMARY_ROWS` matrix is set-theoretically infeasible. The exact sparse separator OR ACK risk minus IND ACK risk still has `A^T y=0`, `y^T b=1/8`, box RHS `0`, and margin `1/8`; it is an algebraic certificate for the literal stack, not evidence of a cross-mode shared-K obstruction.

The smaller common-raw-plus-OR subsystem is already infeasible. Its path/raw rows force `q=(1/2,1/2,1/2)`, while `OR.risk.ACK` forces `q1=3/4`. Conversely, deleting `OR.risk.ACK` leaves all other 12 rows feasible at `q=(1/2,1/2,1/2)`. Thus neither IND nor SOFT is needed for the observed literal-table contradiction.

`PRIMARY_ROWS` is a declared finite table. It is not mechanically generated or marginally validated by the loss/interface/policy/recurrent/shadow/ledger objects. This artifact does not establish lower-level path/risk provenance, cellwise H/W/U ancestry, matched-carrier independence, or generator-safe semantic binding.

The separately named feasible and infeasible engineering units are solver checks only. The feasible unit retains its exhaustive paired equality and zero-residual checks; neither engineering unit repairs coherence or provenance, nor establishes exact Bernoulli calibration.

## Exact raw CLI binding

The following UTF-8 line, including its terminal newline, is the exact deterministic stdout of the candidate entry point:

```json
{"candidate_id":"CAND-VSP-04-MATCHED-BOUNDARY-REQUEST-TRIAD@adversarial-revision-v8","certificate":{"forcing_modes":["IND","OR"],"forcing_rows":["IND.risk.ACK","OR.risk.ACK"],"lhs":"1/8","margin":"1/8","rhs":"0","y_sparse":{"IND.risk.ACK":"-1","OR.risk.ACK":"1"}},"checks":{"declared_object_scope_only":true,"excluded_u_absent_from_g":true,"frozen_policy_recurrent_shadow_tables":true,"no_post_result_feature_adaptation":true,"support_floor":"1/4"},"conclusion":"literal stacked PRIMARY_ROWS matrix is set-theoretically infeasible","engineering_units":{"does_not_repair":["coherence","provenance","exact Bernoulli calibration"],"feasible":{"paired":{"a0_u_independent":true,"comparisons":72,"delta_tk":"0","finite_tape_size":4},"witness":["1/2","1/2","1/2"]},"infeasible":{"margin":"1/2","witness":null},"scope":"solver_checks_only"},"literal_subsystems":{"common_raw_plus_or":{"infeasible":true,"or_ack_forced_q1":"3/4","path_raw_forced_q":["1/2","1/2","1/2"]},"delete_or_risk_ack":{"remaining_rows":12,"witness":["1/2","1/2","1/2"]}},"nonclaims":["authentic-request value","causality","cellwise H/W/U ancestry","coherent IND/OR/SOFT matched-boundary triad","cross-mode shared-K obstruction","deployment","exact Bernoulli calibration","generator-safe semantic binding","lower-level path/risk provenance","matched-carrier independence","return","training benefit","universal impossibility"],"primary":{"cells":["w0","w1","w2"],"omega":["1/4","1/2","1/4"],"p_h":"1/2","row_inventory":{"action_risk":{"IND":2,"OR":2,"SOFT":2},"path":{"IND":2,"OR":2,"SOFT":2},"raw":1,"total":13},"table_scope":{"declared_finite_table":true,"marginally_validated_by_lower_level_objects":false,"mechanically_generated_from_lower_level_objects":false},"witness":null},"treatment":"VSP-04-STACKED-FINITE-CELL-KNOCKOFF-CERT-D0"}
```

## VSP04-A1 declared-table certificate acceptance

- Action treatment: `VSP04-A1-DECLARED-TABLE-RATIONAL-CERTIFICATE-ACCEPTANCE`.
- Solver payload treatment: `VSP-04-STACKED-FINITE-CELL-KNOCKOFF-CERT-D0`. This is the external technical-acceptance alias for the already frozen solver payload; it does not change any solver literal.
- Commit-bound package anchor: `1236cdc096fe913d7854892275284c652d7df00b`.
- Action-level technical branch: `A1_LITERAL_DECLARED_TABLE_CERTIFICATE_ACCEPTED`.
- Public result: `docs/research/candidates/vsp_04/VSP04_A1_DECLARED_TABLE_CERTIFICATE_ACCEPTANCE_RESULT.json`.
- Source and proof-sized test: `experiments/candidates/vsp_04/matched_boundary_rational_certificate.py`; `tests/experiments/candidates/vsp_04/test_matched_boundary_rational_certificate.py` (17 passed in the A1 focused receipt).
- Accepted action boundary: only the declared 13-row table is infeasible under `IND.risk.ACK=-1`, `OR.risk.ACK=+1`, with `A^T y=0`, lhs/margin `1/8`, and RHS `0`; deleting `OR.risk.ACK` leaves 12 rows and witness `(1/2,1/2,1/2)`.
- This action is a declared-table/solver-check-only acceptance. It makes no lower-level H/W/U generation, provenance, causality, value, natural-instance relevance, matched-carrier, semantic-binding, universal-impossibility, or deployment claim.

## Narrow nonclaims

This isolated exact finite-cell contradiction does not establish a cross-mode shared-K obstruction or a coherent IND/OR/SOFT matched-boundary triad. It also does not establish lower-level path/risk provenance, cellwise H/W/U ancestry, matched-carrier independence, generator-safe semantic binding, exact Bernoulli calibration, authentic-request value, training benefit, return, causality, deployment validity, or universal impossibility. The declared-object checks do not bind those objects semantically to `PRIMARY_ROWS`; they only check their own registered constants.
