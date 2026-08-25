# VSP03-A1 event-certified boundary confirmation: code-science index

## Frozen outcome

The registered current-revision audit returns
`A1_INVALID_EVENT_CAUSALITY_OR_SCOPE`. The codebase has
`NO_GENUINE_TARGET_NEGATIVE_CAUSAL_DEPLOYMENT_EVENT_SEAM`: generic debouncer,
roster, and timestamp observations are not authenticated evidence for the
target-negative primitive event `e`. The registered runner therefore binds no
source, fabricates no `e`, performs zero lookup evaluations, and performs zero
environment, policy, learner, trainer, optimizer, evaluation, model-fit,
return, or RNG activity.

This is a causal-information-interface result with no natural value, novelty, return, or deployment claim.

## Critical observable bindings

| Frozen claim or contract | Code owner | Observable evidence | Focused rejection |
|---|---|---|---|
| Missing authenticated event causality/scope fails before lookup | `EventSourceBinding`, `_source_failures`, `_build_result` | Unbound source selects `A1_INVALID_EVENT_CAUSALITY_OR_SCOPE`, zero lookup/runtime activity, and zero fabricated event latches | `test_unbound_source_fails_before_lookup_or_runtime_activity`, `test_every_causal_source_or_scope_defect_dominates_without_lookup` |
| Full future-source lookup is `D=a AND y`, `B=a AND y AND NOT e` | `FROZEN_TRUTH_TABLE`, `_truth_table_audit` | All eight complete two-bit rows are exactly `000->00`, `001->00`, `010->00`, `011->00`, `100->00`, `101->00`, `110->11`, `111->10`; unarmed-latch rows are explicitly invalid causal states | `test_frozen_future_source_truth_table_is_complete_and_exact`, `test_complete_future_source_exercises_truth_table_traces_and_only_lookup_activity`, `test_untraced_valid_bctt_row_mismatch_cannot_reach_supported_branch` |
| Boundary state is evaluate-before-update | `evaluate_boundary` | `INITIAL` evaluates false from `a_-1=0,y0=1`, then arms for the next interval | `test_complete_future_source_exercises_truth_table_traces_and_only_lookup_activity`, `test_each_lifecycle_clause_is_observable_in_frozen_traces` |
| The first negative primitive event while armed latches and stays sticky through reentry | `observe_negative_event`, `observe_reentry` | `EXCURSION_REENTRY` yields debounce=true and BCTT-EC=false; the continuing BCTT-EC boundary update clears the latch and keeps `a=1` | `test_sticky_latch_ignores_unarmed_negative_and_survives_reentry_until_boundary_update` |
| Clean hold and clean `tau_2` retain baseline behavior | `_trace_audit` | Both arms complete on `HOLD`; continuing BCTT-EC completes on `CLEAN_TAU2` | `test_complete_future_source_exercises_truth_table_traces_and_only_lookup_activity` |
| Termination, identity change, and reset clear both state bits and permit reset/rearm | `reset_state`, `evaluate_boundary`, `_trace_audit` | Immediate cleared state is receipted; first positive rearms and the next clean positive completes | `test_each_lifecycle_clause_is_observable_in_frozen_traces` |
| The first-passage, absorbing, and safety-handoff bypass completes on first positive | `BYPASS_SCOPES`, `evaluate_boundary`, `_trace_audit` | Both arms complete immediately in every bypass scope without entering the persistent-occupancy lookup | `test_complete_future_source_exercises_truth_table_traces_and_only_lookup_activity` |
| Comparator parity includes bit-identical inputs, primitive events, clocks, eligibility classes, resets, termination cause and credit assignment | `ParityCauseCreditContract`, `_parity_failures` | Both arms have one armed bit, one costed event latch, and equal-width three-input lookup | `test_parity_cause_credit_and_cost_contract_is_fail_closed` |
| Seven-way precedence is fail-closed | `TerminalBranch`, `_choose_branch` | Earlier causality, parity/cause, debounce, hold, collapse, and lifecycle failures dominate later support | `test_authoritative_branch_precedence_reaches_each_post_contract_failure`, `test_branch_precedence_is_exact_and_earlier_failures_dominate` |
| Publication is one-shot before audit work begins | `publish_registered_audit_once` | Exclusive output claim exists and is empty before audit; existing claims are never overwritten or reused | `test_one_shot_claim_is_reserved_before_audit_and_never_overwritten`, `test_runner_help_and_one_shot_source_free_artifact` |
| Serialized receipts are deterministic and tamper-evident | `AuditResult`, `validate_audit_result` | Validator recomputes the exact typed manifest result and separately enforces zero-runtime and unbound-source invariants | `test_validator_rejects_identity_branch_activity_trace_and_source_tampering` |

## Scope and limits

- The future-source manifest and its complete truth/trace audit are a contract
  exerciser, not evidence that such a source exists in this codebase.
- `event_observations=[]` in the registered result is intentional. Neither a
  timestamp nor generic negative occupancy is relabelled as causal `e`.
- The audit is pure and proof-sized: `H=0`, `K_search=0`, and hypothetical
  transitions are zero.
- No registered result artifact, readiness receipt, or scientific disposition
  is created by this implementation package.

## Publication receipt (mechanical)

- Source `22024051_r1` is published byte-for-byte from the registered audit;
  SHA-256 is `54690645D300A43FC0239A6AA2A77F643550AE682349D3683034756AEE1030DF`.
- Branch: `A1_INVALID_EVENT_CAUSALITY_OR_SCOPE`; source is unbound with no
  authenticated causal source. Lookup evaluations and all runtime activity are
  zero. Validator pass is recorded in the source readiness receipt.
- Source readiness receipt: `temp/sessions/code_project_manager/vsp03_a1_source_readiness_22024051_r1.py`.
- Operator receipt file is authoritative: `temp/sessions/code_project_manager/vsp03_a1_operator_receipt.json`
  reports terminal `ERROR`, phase `NONE`, direct error code branch despite
  runner exit 0; the final message inconsistency is retained as observation.
- Exact publication result: `docs/research/candidates/vsp_03/VSP03_A1_EVENT_CERTIFIED_BOUNDARY_CONFIRMATION_RESULT.json`.
- No supported divergence, value, learning, B/C, Pro, or successor claim is
  made.
