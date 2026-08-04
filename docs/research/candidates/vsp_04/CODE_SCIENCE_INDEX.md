# VSP-04 Sequence 10 code-science evidence index

## Scope and traceability

- Candidate: `CAND-VSP-04-MATCHED-BOUNDARY-REQUEST-TRIAD@adversarial-revision-v8`
- Treatment: `VSP-04-STACKED-FINITE-CELL-KNOCKOFF-CERT-D0`
- Implementation: `experiments/candidates/vsp_04/matched_boundary_rational_certificate.py`
- Proof-sized tests: `tests/experiments/candidates/vsp_04/test_matched_boundary_rational_certificate.py`
- Frozen primary result: no common triad K exists under this frozen information contract. The exact separator is OR ACK risk minus IND ACK risk, with `A^T y=0` and margin `3/8-1/4=1/8`.

The implementation stacks the registered raw propensity, complete post-interface path rows, and action-specific joint-risk rows unchanged. It separately exercises a feasible engineering unit (including exhaustive paired T/K and matched-carrier A0 checks) and an infeasible engineering unit. Those units are solver evidence only and are not candidate evidence.

## Exact raw CLI binding

The following UTF-8 line, including its terminal newline, is the exact deterministic stdout of the candidate entry point:

```json
{"candidate_id":"CAND-VSP-04-MATCHED-BOUNDARY-REQUEST-TRIAD@adversarial-revision-v8","certificate":{"forcing_modes":["IND","OR"],"forcing_rows":["IND.risk.ACK","OR.risk.ACK"],"lhs":"1/8","margin":"1/8","rhs":"0","y_sparse":{"IND.risk.ACK":"-1","OR.risk.ACK":"1"}},"checks":{"excluded_u_absent_from_g":true,"frozen_policy_recurrent_shadow_tables":true,"no_post_result_feature_adaptation":true,"support_floor":"1/4"},"conclusion":"no common triad K exists under this frozen information contract","engineering_units":{"feasible":{"paired":{"a0_u_independent":true,"comparisons":72,"delta_tk":"0","finite_tape_size":4},"witness":["1/2","1/2","1/2"]},"infeasible":{"margin":"1/2","witness":null}},"nonclaims":["authentic-request value","causality","deployment","return","training benefit","universal impossibility"],"primary":{"cells":["w0","w1","w2"],"omega":["1/4","1/2","1/4"],"p_h":"1/2","row_inventory":{"action_risk":{"IND":2,"OR":2,"SOFT":2},"path":{"IND":2,"OR":2,"SOFT":2},"raw":1,"total":13},"witness":null},"treatment":"VSP-04-STACKED-FINITE-CELL-KNOCKOFF-CERT-D0"}
```

## Narrow nonclaims

This isolated exact finite-cell contradiction does not establish authentic-request value, training benefit, return, causality, deployment validity, or universal impossibility. It changes neither the frozen information contract nor the policy/recurrent state after feasibility is observed.
