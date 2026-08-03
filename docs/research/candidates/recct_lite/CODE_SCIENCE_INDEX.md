# RECCT-LITE dependency noninterference D0: code-science index

Candidate: `CAND-VAP-RECCT-LITE@adversarial-revision-v8`

Treatment: deterministic zero-return
`RECCT-DEPENDENCY-NONINTERFERENCE-D0`

Status: synthetic engineering-conformance evidence only. No active project
implementation or frozen empirical RECCT numeric constants were found, so this
fixture uses short exact rational unit values solely to test the specified
interfaces and invariants. It does not support a four-step utility-sign,
semantic-mediation, cooperation, adaptation, long-horizon, or deployment claim.

## Bound instance

The immutable world has registered `N=3`, anonymous roles `r0,r1,k`, no
lifecycle event, and literal initial learner-update mask `00`. The mask changes
only optimizer exposure; environment, learner metadata, buffer, partner,
queue, normalizer, checkpoint/owner epoch, and disjoint RNG counters are frozen.

The exact configuration is:

```text
epsilon=1/4; rho_cap=1; rho_threshold=1/2
signed_credit_threshold=1/4; eta=1/8
learning_rate=1/4; momentum_beta=1/2
on_transition_cost=1/20; off_transition_cost=1/40
```

Both canonical probes have `mu0=0`, `mu1=3/4`, `sigma=1`, support true,
and signed credit `1/2`; therefore both exact `rho` values are `3/5`.
The pure optimizer receives base gradient `(0,0)`, edge gradients `(-1,0)`
and `(0,-1)`, zero momentum and accumulation, unit scaler/clip, and one
scheduler step. Its algebraic frozen evaluator is
`J^(4)=4*(2*parameter_0-parameter_1)`; this is not a rollout.

Every `00/10/01/11` candidate independently restores the same canonical world
bytes and performs exactly one optimizer transition. Relative to `00`, after
registered transition cost:

| mask | updated parameters | q |
|---|---|---:|
| `00` | `(0,0)` | `0` |
| `10` | `(1/4,0)` | `39/20` |
| `01` | `(0,1/4)` | `-21/20` |
| `11` | `(1/4,1/4)` | `9/10` |

Both edges are feasible and the top gap is strictly greater than `eta`, so the
literal-`00` decision selects `10`. Swapping orientations and their gradient
objects selects `01`, while `00/11` and the two single-edge q values transform
equivariantly.

## Whitelist and firewall

The primary gate accepts only the sealed fold digest, full canonical world
digest, immutable ancestry graph, disjoint local RNG counters, authenticated
equality/epoch flags, two proposals, explicit config, and literal current mask.
Raw owner identity/embedding, audit seed/outcome, semantic `psi`, return,
future state, prior oracle, global RNG, and cache fields fail closed.

The ancestry graph explicitly binds preprocessing, learner recurrence, replay,
normalizer, partner checkpoint and owner epoch. It is acyclic and shares no
mutable ancestor between fitted and evaluation nodes. Audit-typed records are
rejected by fit, normalize, and threshold pipelines.

- `G_SC` computes the semantic branch but forces it to pass; changing `psi`
  cannot change mask or optimizer bytes.
- `G_SD` changes only matched signed-credit signs; it preserves the four
  optimizer inputs and shadow results.
- `G_SEM` and `G_pi` return immutable reporting records only. They have no
  route to the real gate, optimizer, threshold, checkpoint, or mask.

## Actual result

```text
terminal=PASS_DEPENDENCY_NONINTERFERENCE_D0
selected_mask=10
orientation_swapped_mask=01
rho=(3/5,3/5)
q=(00:0,10:39/20,01:-21/20,11:9/10)
all_11_invariants=True
```

The 11 passing invariants cover input/audit isolation, owner-label bijection,
orientation equivariance, four independent byte-identical clones, enumeration
order, ancestry/RNG isolation, the threshold/hysteresis truth table,
real-to-selected-shadow byte equality, the semantic firewall, reporting-only
semantic branches, and matched-sign-null optimizer-input identity.

## Traceability

| claim_id | frozen assertion | code path and symbol | observable invariant | focused test | alternate explanation excluded |
|---|---|---|---|---|---|
| RECCT_D0_INPUT | Only declared pretreatment inputs reach the primary gate | `experiments/candidates/recct_lite/dependency_noninterference.py::build_gate_input`; `::bind_gate_input`; `::validate_gate` | Audit seed/record and owner renaming leave gate bytes and selected optimizer bytes identical; every undeclared field fails closed | `tests/experiments/candidates/recct_lite/test_dependency_noninterference.py::test_audit_seed_record_and_owner_key_never_enter_primary_gate_or_update`; `::test_undeclared_primary_gate_inputs_fail_closed` | Owner/audit/cache/oracle/global-RNG leakage cannot create a gate result. |
| RECCT_D0_ANCESTRY | Fold, preprocessing, recurrence, replay, normalizer, partner checkpoint and owner epoch are immutable and isolated | `::Ancestry`; `::validate_ancestry`; `::fit_pretreatment_records` | Cycles, mutable overlap, invalid epoch/equality/RNG and audit-typed pipeline records fail before evaluation | `::test_invalid_equality_epoch_rng_and_ancestry_fail_before_optimizer_evaluation`; `::test_audit_typed_records_are_rejected_by_every_pretreatment_pipeline` | Post-audit fitting, mutable shared ancestors and invalid identity/epoch cannot contaminate the result. |
| RECCT_D0_THRESHOLDS | Rho, signed credit, feasibility and hysteresis are explicit exact functions | `::rho`; `::edge_feasible_values`; `::choose_mask`; `::truth_table_complete` | Below/at/above, support, strict top-gap, tie, activation, deactivation and literal-00 branches are complete | `::test_rho_signed_credit_and_support_threshold_cells_are_exact`; `::test_hysteresis_has_no_lexicographic_tie_and_requires_strict_gap`; `::test_literal_zero_initialization_and_complete_four_mask_enumeration_fail_closed` | Floating tolerance, lexicographic scientific tie-break and nonliteral initialization cannot select a mask. |
| RECCT_D0_CLONES | Four masks use independent byte-identical full-state restores | `::world_bytes`; `::restore_world`; `::evaluate_masks`; `::optimizer_step` | Order reversal preserves every state; each clone takes one scheduler step while scaler, clipping and all nonoptimizer state remain frozen | `::test_each_mask_restores_one_identical_world_and_one_optimizer_transition` | Sequential mutable optimizer/partner/RNG reuse cannot manufacture q differences. |
| RECCT_D0_Q | One frozen evaluator and registered costs produce exact q values | `::four_step_evaluator`; `::evaluate_masks`; `::decide` | Exact updated parameters and q table above; selected mask is `10` | `::test_exact_optimizer_states_costs_and_q_values_use_one_frozen_evaluator` | Hidden rollout, changed evaluator, double cost, or mask-dependent starting state cannot enter. |
| RECCT_D0_SYMMETRY | Owner labels are absent and orientation swap is equivariant | `::build_gate_input`; `::decide` | Owner bijection preserves bytes; orientation swap maps `10<->01` and preserves `00/11` | `::test_owner_bijection_and_orientation_swap_are_equivariant` | Raw identity or enumeration order cannot determine orientation. |
| RECCT_D0_FIREWALL | Real state equals selected shadow and semantic branches are reporting-only | `::g_sc`; `::g_sd`; `::g_sem`; `::g_pi`; `::run_noninterference_audit` | Changing psi leaves primary bytes fixed; committed bytes equal selected shadow; semantic reports do not mutate world | `::test_real_shadow_bytes_semantic_firewall_and_reporting_sink_are_closed`; `::test_world_mismatch_semantic_schema_and_sign_contract_fail_closed` | Semantic receipt, reporting output or mismatched world cannot influence the primary optimizer update. |

## Bounded execution

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -c "from experiments.candidates.recct_lite.dependency_noninterference import run_noninterference_audit as run; print(run().to_bytes().decode())"
```

```json
{"invariants":{"ancestry_and_rng_isolated":true,"enumeration_order_invariant":true,"four_byte_identical_independent_clones":true,"input_and_audit_isolation":true,"matched_sign_null_preserves_optimizer_inputs":true,"orientation_swap_equivariant":true,"owner_label_bijection_invariant":true,"real_equals_selected_shadow_bytes":true,"semantic_firewall":true,"shadow_reports_do_not_mutate_state":true,"threshold_hysteresis_truth_table_complete":true},"orientation_swapped_mask":"01","q_values":{"00":"0","01":"-21/20","10":"39/20","11":"9/10"},"rho_values":["3/5","3/5"],"selected_mask":"10","terminal":"PASS_DEPENDENCY_NONINTERFERENCE_D0"}
```

Fresh focused validation:

```text
24 passed in 0.16s
```

The source has 497 active lines and no production consumer. The operation is a
zero-return finite conformance pass: no environment step, shadow-utility
rollout, learner training, partner adaptation, tuning, or rescue experiment.
It does not change any production entry, runner phase, artifact lifecycle or
shared serialization contract, so execution readiness is not triggered. The
accepted revision is the exact commit containing this index, source, and
mirrored test.
