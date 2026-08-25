# VSPC1 constrained fourth-corner code-science index

## Bound treatment

- Design: `VSP-C1-CCLC-BOUND-A-V1`
- Treatment: `VSPC1-A1-CONSTRAINED-FOURTH-CORNER-LOGIT-COMPLETION`
- Candidate: `CAND-VSP-C1-CROSSED_IDENTITY_PERIOD_FACTORIZATION@constrained-fourth-corner-v9`
- Evidence/runtime class: A / `A_READONLY_OR_ZERO_RUNTIME`
- Pool units: `0`

The registered audit is a prospective first-action-kernel construction only.
It does not run an environment, learner, trainer, optimizer, return evaluator,
stochastic action, sweep, retry, or rescue.

## Source and consumer locators

- Semantic implementation and independent validator:
  `experiments/candidates/vsp_c1/constrained_fourth_corner_logit_completion.py`
- One-shot registered entry point:
  `scripts/run_vspc1_a1_constrained_fourth_corner_logit_completion.py`
- Focused wrong-implementation evidence:
  `tests/experiments/candidates/vsp_c1/test_constrained_fourth_corner_logit_completion.py`
- Direct consumer: Code Project Manager publishes and technically accepts the
  one registered JSON result; Independent Research Explorer consumes that
  accepted packet and alone chooses any scientific successor.

## Observable invariant map

| Frozen claim surface | Source symbol | Focused rejection evidence |
|---|---|---|
| Only an explicitly registered authenticated identity×period four-clone constructor may become the host; toy, ORBIT, lifecycle, and MSSR substitutions are rejected | `HOST_CONTRACT_ID`, `observe_registered_host`, `run_registered_audit` | `test_registered_host_observation_fails_closed_without_constructing_a_substitute` |
| The first two metadata-ordered identity and period levels fix `i0,i1,p0,p1`; `T=(i0p0,i0p1,i1p0)` and `H=i1p1` are frozen before kernel reads | `validate_state_manifest` | `test_joint_key_and_post_kernel_selection_loopholes_fail_before_reads` |
| All actor-visible, router, recurrent, partner, roster, checkpoint, age, gradient, legal-action, and RNG bytes are equal across clones apart from the two registered factor fields; each live handle exposes the same captured bytes and exact manifest digest | `PORT_FREE_STATE_FIELDS`, `nonfactor_state_sha256`, `validate_state_manifest`, `_validate_cell_sources` | port-free mismatch and live-binding drift tests |
| The four cells require distinct live clone, reader, model-graph, and kernel-source objects and unique manifest identities; aliased wrappers and sequential reuse of one model are rejected before T | `_validate_cell_sources` | `test_four_live_cell_sources_reject_object_aliasing_before_t` and `test_sequential_one_model_reuse_and_live_binding_drift_fail_before_t` |
| No joint identity-period key or descendant reaches either predictor; every cell has the same ordered positive legal support | `validate_state_manifest`, `_validate_kernel` | joint-key and common-support focused tests |
| Candidate and null each fit exactly `3*d` float64-equivalent scalar values and reconstruct all three T logits exactly | `_fit_payloads` | `test_complete_predictors_use_exact_three_d_capacity_and_seal_before_h` |
| `q_C=softmax(L_i1p0+L_i0p1-L_i0p0)` and `q_N=softmax((L_i0p0+L_i0p1+L_i1p0)/3)` are sealed without H-derived fields | `_fit_payloads` receipt digest | seal-tamper parameterization in `test_independent_validator_rejects_seal_logit_order_branch_and_counter_tamper` |
| `JS(q_C,q_N)<0.02` terminates before H; otherwise H is read exactly once after both seals | `execute_complete_rectangle`, `validate_audit_result` | `test_pre_reveal_nondiscrimination_never_reads_h` and transcript tamper test |
| Every returned kernel carries the exact per-cell clone/kernel-source binding; call counts and attempted-read receipts increment at invocation, even when capture validation fails | `_validate_kernel`, `execute_complete_rectangle`, `validate_audit_result` | `test_capture_source_mismatch_counts_the_attempted_invocation` and invalid-kernel cases |
| `D_C`, `D_N`, `Delta`, the mixed-logit residual, and literal `<`, `>=`, `<=` terminal precedence are independently recomputed from exact kernels and seals | `select_terminal_branch`, `validate_audit_result` | adjacent-boundary and branch/logit/receipt tamper tests |
| Output and the shared one-audit claim are each exclusively reserved before registered source inspection; either existing path prevents `run_registered_audit`, and a second output cannot bypass the same claim | `claim_and_run_registered_audit`, reservation-gated `run_registered_audit` | `test_output_and_shared_claim_are_exclusive_before_registered_source_execution` and `test_registered_audit_cannot_start_without_active_reservation` |

## Registered host observation and current expected branch

The production supplied-executor module exposes ordinary and MSSR model/runtime
factories plus a kernel-capture hook, but no callable marked with the exact
`vspc1.authenticated-identity-period-four-clone-host.v1` contract. The MSSR
runtime factory shares its model owner across cores and therefore is not an
authenticated identity×period four-clone rectangle. The registered observation
constructs no model, runtime core, clone, or kernel.

Consequently the current one-shot audit must return
`A1_HOST_RECTANGLE_UNREACHABLE`, with one registered audit and every
construction, kernel, predictor, seal, environment, learner, trainer,
optimizer, return, model-fit, stochastic, retry, and rescue count equal to
zero. No fixture accepted by `execute_complete_rectangle` is reachable from the
registered runner unless production code separately registers the exact host
contract. A future registered host must return four per-cell source packages;
each package owns distinct live clone/model and reader/kernel-source handles,
and every captured kernel must echo its manifest-bound source receipt.

## Branch precedence

1. `A1_INVALID_CONSTRUCTION` for state mismatch, joint-key leakage,
   common-support failure, nonfinite kernel, outcome-conditioned selection, or
   an unsealed/tampered prediction.
2. `A1_HOST_RECTANGLE_UNREACHABLE` when the exact registered four-clone host is
   absent.
3. `A1_PRE_REVEAL_NONDISCRIMINATING` when `JS(q_C,q_N)<0.02` nats.
4. `A1_CONSTRAINED_SUCCESSOR_FALSIFIED` when `D_C>=0.05` or
   `D_C-D_N>=0.02`.
5. `A1_LOCAL_FOURTH_CORNER_PREDICTION_SUPPORTED` when `D_C<=0.01` and
   `Delta>=0.02`.
6. `A1_VALID_AMBIGUOUS` otherwise.

## Claim boundary and publication binding

A positive branch supports only one local constrained additive fourth-corner
action-kernel prediction unavailable to the equal-`3*d` support-saturated
null. It does not establish semantic identity, global factorization,
same-support superiority, task return, transfer, learning/sample complexity,
formal promotion, ranking, retirement, or a Pro disposition.

Accepted source/result commits and the public result locator are intentionally
left unset by the runtime artifact. They are Code Project Manager-owned facts
added to the accepted technical packet after integration and publication; the
audit cannot truthfully predict its own future Git identity.

The CLI requires both `--output` and one shared `--claim`. It creates both with
exclusive semantics before calling the reservation-gated registered audit.
Claims are never recycled after source execution begins; a failure leaves the
reservation in place so neither a new output name nor a retry can consume a
second registered audit.

## Accepted VSPC1-A1 publication receipt

- Source commit: `01ccf191d268a99bd97f2dd93cae95765a5049f3` (branch
  `A1_HOST_RECTANGLE_UNREACHABLE`).
- Source readiness receipt: `temp/sessions/code_project_manager/vspc1_a1_source_readiness_r2.json`.
- Registered audit: `1`; focused production kernel calls: `0`; all runtime,
  learner, trainer, optimizer, return, stochastic, sweep/retry/rescue,
  construction and predictor-fit counts are zero.
- Validator: pass (retained raw result is valid JSON and byte-identical to the
  registered-audit result; SHA-256 `BECAE21752B7A0431B8F8D02E7D9B0D454BA4CF66521B5EE51557295CFE0A4E8`).
- Operator receipt: terminal `ERROR` solely because this single-audit runner
  has no evaluate/analyze phases (N/A),
  `temp/sessions/code_project_manager/vspc1_a1_operator_receipt.json`.
- Result: `docs/research/candidates/vsp_c1/VSPC1_A1_CONSTRAINED_FOURTH_CORNER_LOGIT_COMPLETION_RESULT.json`;
  source: `experiments/candidates/vsp_c1/constrained_fourth_corner_logit_completion.py`;
  receipt: `temp/sessions/code_project_manager/vspc1_a1_operator_receipt.json`.
- Nonclaims: no B/C/Pro disposition, no successor selection, and no new
  science or acceptance beyond the recorded unreachable-host branch.
