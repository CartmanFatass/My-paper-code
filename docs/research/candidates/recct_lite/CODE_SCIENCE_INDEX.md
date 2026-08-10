# RECCT-LITE A1 directed-edge masked-update binding: code-science index

Candidate: `CAND-VAP-RECCT-LITE@authenticated-edge-intervention-revision-v9`

Treatment: `RECCT-A1-DIRECTED-EDGE-MASKED-UPDATE-BINDING`

Status: prospective result-bearing implementation. The registered five-update
audit has not been executed by the implementation worker. No branch, accepted
commit, publication locator, B design, promotion, or scientific conclusion is
claimed here. Code Project Manager owns the fresh result execution, technical
acceptance, readiness, Git identity, and public result lineage.

## Real learner seam

G40 now exposes a learner-only directed replay seam at the real computation
path by which one active source member's encoded contribution reaches one
receiver's context before aggregation. The authenticated roster registry maps
agent instances to lifecycle slots; observations, parameter coordinates,
optimizer moments, and synthetic edge vectors never establish ownership.

For a registered source `s` and receiver `r`, the ordinary encoded contribution
`x_s` is written as:

```text
x_s.detach() + scale_(s->r) * (x_s - x_s.detach())
```

The forward value is always `x_s`. Each receiver aggregate is constructed by
gating every named source term first and summing those terms exactly once.
Scale one is the ordinary learning path; scale zero supplies only the detached
forward value and structurally removes the named derivative before aggregation.
There is no aggregate-then-cancel or duplicate post-aggregation route.
Therefore masking does not change execution-policy actions,
communication values, the PPO loss, advantage normalization, baseline loss,
entropy term, backward scope, or Adam definition. The all-enabled `11` case
dispatches directly to accepted ordinary `replay_trajectory`, so its learner
and optimizer transition is byte-exact to G40 rather than a copied approximation.

The seam lives at
`ha_ctse_process/continuous_roster_native_six_credit_reduction_g40.py::G40DirectedLearningPort`,
`::_directed_learning_forward_step`, and
`::replay_trajectory_with_directed_learning_ports`.

## Sealed capsule and capabilities

`DirectedEdgeMaskedLearner.seal_capsule` serializes the complete G40 learner
state, complete Adam state, and immutable pretreatment trajectory into private
bytes. Its frozen manifest binds:

- learner instance, G40 member capacity, policy generation, and roster epoch;
- an explicit three-agent instance-to-slot bijection;
- learner/optimizer/batch/parent ancestry digests;
- frozen support, rho, predictor digest, and predeclared selected mask;
- exactly allowlisted site-keyed counters for `learner/replay` and
  `optimizer/adam`; all extra, nested audit/future/global, semantic-label, and
  otherwise undeclared sites reject sealing;
- exact Adam learner configuration and one PPO pass;
- explicit immutable `DISABLED` scheduler, scaler, gradient-clipping, and
  gradient-accumulation states;
- the complete directed-edge registry digest and port payload schema.

Unknown optimizer state values, mutable runtime outcomes/ledgers, nonfinite
batch state, incomplete N=3 activity, ownership/order mismatch, omitted
disabled state, or ancestry mismatch fails sealing.

Only `DirectedEdgeMaskedLearner` mints `OpaqueDirectedHandle` objects. A handle
publicly reveals only its opaque identifier. The learner-held provenance record
binds capsule, roster epoch, source and receiver instances/slots, learner
instance, one unique directed port, payload schema, and mint provenance. It
contains no parameter indices, coordinate mask, edge vector, orientation label,
or usefulness label. Constructor guarding plus object-identity registry lookup
reject forged, copied, cross-capsule, or provenance-lost handles.

## Four shadows and fresh commit

The registered audit calls:

```text
DirectedEdgeMaskedUpdate(capsule, ordered_edge_pair, mask, cloned_counterfactual_rng)
```

for `00`, `10`, `01`, and `11`, restoring the same sealed bytes for every
complete transition and using distinct clones of one logically identical
site-keyed RNG plan. Each call recomputes replay, the full PPO/baseline/entropy
loss, normalization, backward pass, and exactly one Adam transition.

After the capsule's frozen pretreatment selection, `commit_selected_update`
performs a fifth fresh restoration and recomputation. Its signature accepts
only capsule, two handles, the frozen selected mask, and a fresh RNG clone. It
cannot receive a shadow model, gradient, learner state, optimizer state, or
receipt. The predeclared transition predicate compares complete gradient,
parameter delta, learner state, optimizer state, intervention, disabled-state,
and ancestry receipts while excluding only fresh call/RNG-clone lineage.

The intervention receipt derives its declared path count, duplicate-path count,
post-aggregation cancellation count, and structural-gate witness from G40's
validated port inventory; those values are not hard-coded result claims.
Every receipt retains complete named gradient tensors, complete named learner
state, complete Adam parameter/group state, complete parameter deltas, exact
intervention membership, and source/RNG/roster ancestry. No coordinate is
interpreted as edge ownership.

## Registered checks and precedence

The four pure gradients check the exact factorial identity
`G11 - G10 - G01 + G00 = 0` within the declared float32 tolerance. The two
single-edge contrasts must be nonzero, distinct, and confined to the real
`policy.member_encoder.*` source path. This simultaneously checks literal `00`
removal, named-only `10/01` addition, full-gradient conservation, disabled-port
invariance to the opposite port, and enabled-port path-local propagation.

Agent-name permutation is routed only through the explicit registry bijection;
the update callable consumes authenticated slots, never names or observation
coordinates. Focused evidence rebuilds the same capsule under a disjoint name
bijection and requires identical gradients, deltas, learner state, and Adam
state. Future outcome/state, audit seed/outcome, semantic/orientation/usefulness
labels, parameter indices, coordinate masks, edge vectors, and global RNG are
absent from both the capsule schema and update signature.

`classify_a1` implements this exact fail-closed precedence:

1. `A1_MISSING_REAL_CALLABLE_OR_NO_UNIQUE_PREAGGREGATION_PORT`
2. `A1_HANDLE_FORGEABLE_OR_PROVENANCE_LOST`
3. `A1_COMPOUND_INTERVENTION_OR_UNDECLARED_PATH`
4. `A1_MASK_SEMANTICS_FAILURE`
5. `A1_RECOMPUTATION_OR_ANCESTRY_FAILURE`
6. `A1_IDENTITY_STICKY_NONIDENTIFIABILITY`
7. `A1_CALLABLE_BUT_HOST_NONIDENTIFYING`
8. `A1_DIRECTED_EDGE_BINDING_PASS`

Only branch 8 establishes callable intervention-bound directed edge-update
contrasts. It makes a later orientation-paired B designable; it does not run,
support, or select B.

## Traceability

| claim_id | code path and symbol | observable invariant | focused evidence |
|---|---|---|---|
| RECCT_A1_REAL_PORT | `ha_ctse_process/continuous_roster_native_six_credit_reduction_g40.py::G40DirectedLearningPort`; `::directed_learning_port_path_inventory`; `::_directed_learning_forward_step`; `::replay_trajectory_with_directed_learning_ports` | named source term is gated before its receiver sum; no aggregate-then-cancel route; `11` uses ordinary replay byte-exactly; disabled perturbations are invariant; enabled perturbation changes only `policy.member_encoder.*` gradients | `test_structural_gate_precedes_sum_and_has_no_aggregate_then_cancel_route`; `test_mask_11_is_bit_exact_to_the_ordinary_g40_update`; `test_disabled_port_perturbation_is_invariant_and_enabled_propagation_is_path_local` |
| RECCT_A1_CAPSULE | `experiments/candidates/recct_lite/directed_edge_masked_update.py::SealedLearnerCapsule`; `::DirectedEdgeMaskedLearner.seal_capsule` | complete immutable learner/Adam/batch/roster/ancestry/RNG/config/disabled-state binding | `test_capsule_is_complete_handles_are_opaque_and_forged_objects_fail_closed` |
| RECCT_A1_RNG | `::ALLOWED_PRETREATMENT_RNG_SITES`; `::SiteKeyedRNGPlan` | only the two declared pretreatment sites are accepted; exact and nested reserved/undeclared namespaces fail closed | `test_rng_plan_rejects_every_nonallowlisted_reserved_namespace` |
| RECCT_A1_HANDLE | `::OpaqueDirectedHandle`; `::DirectedEdgeMaskedLearner.handle`; `::_record_for` | only learner-minted object identity plus full private provenance authenticates a unique port | `test_capsule_is_complete_handles_are_opaque_and_forged_objects_fail_closed` |
| RECCT_A1_MASK | `::DirectedEdgeMaskedUpdate`; `::_factorial_conservation`; `::_port_contrast_norms`; `::_port_contrast_changed_names` | four same-capsule pure masks, named-only membership, conserved full gradients, live path-local directed contrasts | `test_four_pure_masks_conserve_full_gradient_and_bind_only_named_ports` |
| RECCT_A1_COMMIT | `::commit_selected_update`; `::UpdateReceipt.transition_predicate` | fresh selected recomputation accepts no shadow object and equals its selected shadow except lineage | `test_fresh_commit_api_accepts_no_shadow_objects_and_matches_frozen_mask` |
| RECCT_A1_IDENTITY | authenticated roster registry and G40 slot seam | disjoint agent-name bijection preserves complete transition evidence | `test_agent_name_permutation_is_equivariant_and_coordinates_never_mint_identity` |
| RECCT_A1_PRECEDENCE | `::A1Checks`; `::classify_a1` | first false condition selects exactly the declared branch, all true selects branch 8 | `test_eight_branch_precedence_is_exact` |
| RECCT_A1_RUNNER | `scripts/run_recct_a1_directed_edge_masked_update_binding.py` | one sealed N=3 batch, four shadows plus fresh selected commit, five learner calls/Adam transitions, zero environment/policy/trainer/evaluation/model-fit calls | fresh CPM-owned result execution; not run during implementation |

## Bounded evidence and implementation receipt

The registered runner has fixed `N=3`, one immutable batch, four fixed shadow
masks, one fixed selected commit, five learner calls, and five optimizer
transitions. It introduces no trajectory search (`K_search=0`), hypothetical
transition, nested rollout, retry, rescue, sweep, environment transition,
execution-policy call, trainer/evaluation episode, or model fit. Its asymptotic
evidence work is constant in the registered batch and below the project search
ceiling.

Implementation-worker proof (smaller one-step technical fixtures only):

```text
17 passed in 3.87s
```

Focused compatibility attempt over the existing G40/RECCT tests:

```text
29 passed; 8 environment-backed checks could not start because the registered
MSVC/Ninja backend was unavailable during toolchain activation.
```

The eight blocked checks fail before learner execution in
`envs.continuous_roster.cpp_backend._configure_windows_toolchain`; they are not
a RECCT-A1 assertion failure. The implementation worker did not repair the
external toolchain, run execution readiness, or invoke the registered
five-transition audit.

Registered result command (reserved for CPM-authorized result execution):

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_recct_a1_directed_edge_masked_update_binding.py
```

## RECCT-A1 registered audit publication (2026-08-10)

The technically verified result is materialized at
`RECCT_A1_DIRECTED_EDGE_MASKED_UPDATE_BINDING_RESULT.json` from the
PowerShell-captured UTF-16LE input
`temp/sessions/code_project_manager/recct_a1_registered_audit_010da9a8_r1/raw_result.json`.
The source commit is `010da9a8bc3204d2363cfebaed022b130baa08e1` on branch
`A1_DIRECTED_EDGE_BINDING_PASS`. Input SHA-256 is
`86acb6f2a1ebe978421a632f25ea1fde5233df3b677c89dc70007e92ff56aef1`;
canonical public UTF-8 (sorted keys, indent=2, LF) SHA-256 is
`11880d1db9e9c8c2691c26ca4442756d4567f2d08a9eeeec8d891627f5febd8e`.
Independent parsing of both encodings asserted semantic equality.

The receipt records masks `00`, `10`, `01`, `11`, plus a fresh selected `10`
commit; five learner calls and five optimizer transitions; and zero environment,
policy, trainer, evaluation, model-fit, and retry calls. All seven checks are
true. Claims are strict finite-host observations only and make no value,
performance, generalization, or scientific nonclaims beyond the recorded
mechanical binding. The Experiment Operator terminal `ERROR` is solely because
the train/evaluate/analyze receipt schema does not apply to this single audit;
the underlying runner exited 0 and retained mechanical validation passed.
