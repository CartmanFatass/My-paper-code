# ORBIT verified-owner-binding reachability: code-science index

## Active prospective interface revision

Candidate: `CAND-VAP-ORBIT-LITE@verified-owner-binding-revision-v9`

Treatment: `ORBIT-A2-VERIFIED-OWNER-BINDING-REACHABILITY`

Status: implementation candidate only. The single registered audit has not
been run by the implementer, so this section records the frozen executable
contract and observables rather than a scientific result.

### Typed actor boundary

`VerifiedOwnerBindingView` applies checks in the registered order: trusted
principal, authorization, signature, schema, epoch, payload digest, then source
snapshot digest. A valid certificate exposes exactly
`(VALID, opaque_owner_handle, epoch, payload_digest,
source_snapshot_digest)`. Every invalid cause exposes exactly
`(INVALID, bottom, bottom, bottom, bottom)` and quarantines the payload outside
the actor boundary. Raw certificates, signatures, key IDs, certificate
digests, trust-store indices, cache addresses, internal IDs, payload bytes and
principal IDs are absent from `ActorInput`.

Two independently controlled trusted principals sign one byte-identical sealed
statement. Their handles are distinct equal-format opaque categorical tokens.
Only `owner_by_role_residual` consumes such a token. Its embedding row is unit
normalized and its two equally weighted structural-role residuals sum to zero,
so the owner main effect is zero by construction. The nonprincipal base path is
separate and unrestricted by the owner slice.

The matched `owner_blind` route substitutes one principal-invariant anonymous
owner row while preserving branch width. The `validity_only` route retains
generic validity and a shape-matched zero owner slice. Invalid views on all
three routes invoke `zero_path_owner_bypass(current_state, action_space)`, which
returns centered logits and a masked first-action kernel over the unchanged
ordered legal actions.

### Frozen audit and branch table

The single registered audit freezes float64-scaled logit and kernel tolerances
before any observation. It evaluates four valid cells (two principals crossed
with two structurally cloned roles) and one signature-corrupted invalid cell on
each of three isolated routes: exactly 15 route-cell calls. Model bytes,
recurrence bytes, current state, mask/action order, clocks, roster,
communication state and evaluation mode are identical across fresh clones.
Evaluation clones contain no clone ID, principal label or role metadata;
human-readable reporting IDs are attached only after evaluation completes.
There is no RNG, latency, batch, padding, address, cache, lookup or evaluation
order input. Each route-cell call evaluates its original input and a jointly
relabeled-owner/permuted-embedding-row counterpart, and requires exact equality
of both centered logits and the masked kernel.

Branch precedence is fixed as:

1. `A2_INVALID_CONTROL`
2. `A2_OWNER_ALIAS_NOT_CONSUMED`
3. `A2_NO_LOGIT_ESTIMAND`
4. `A2_FAIL_OPEN_INVALID`
5. `A2_LEAKAGE_OR_UNCONTROLLED_PATH`
6. `A2_GENERIC_PROVENANCE_GATE`
7. `A2_OWNER_MAIN_EFFECT_ONLY`
8. `A2_LOGIT_REACHABILITY_ONLY`
9. `A2_OWNER_BINDING_REACHES_FIRST_ACTION_KERNEL`

Branch 9 requires candidate owner-by-role mixed differences above the frozen
tolerances in centered logits and the masked first-action kernel, candidate
owner main effects within tolerance, both comparator mixed differences within
tolerance, and byte-exact invalid ZERO_PATH fallback. It supports only
interface actionability. It does not establish learned owner meaning, natural
use, utility, persistence, task return or generalization.

### Traceability

| claim_id | frozen assertion | code path and symbol | observable invariant | focused test | alternate explanation excluded |
|---|---|---|---|---|---|
| ORBIT_A2_VIEW | Authentication yields only the typed valid tuple or the all-bottom invalid tuple | `experiments/candidates/orbit_shadow_read/verified_owner_binding_reachability.py::verify_owner_binding`; `::VerifiedOwnerBindingView` | Same sealed content produces distinct equal-format opaque handles; every invalid cause quarantines and returns all bottom | `tests/experiments/candidates/orbit_shadow_read/test_verified_owner_binding_reachability.py::test_verified_view_binds_distinct_opaque_owners_to_identical_content`; `::test_every_invalid_cause_is_all_bottom_and_quarantines_payload` | A raw principal identifier, certificate field, malformed partial view, or unauthenticated payload cannot reach the actor. |
| ORBIT_A2_RESIDUAL | The handle enters only a normalized owner-by-role residual with zero role-weighted owner main effect | `::owner_by_role_residual`; `::build_actor_input` | Unit row norm, exact two-role zero mean, identical nonprincipal tensor under principal swaps | `::test_owner_residual_is_normalized_zero_main_effect_and_alias_row_permutation_invariant`; `::test_principal_swap_is_identical_outside_handle_slice_and_nulls_are_invariant` | A principal-dependent base feature or owner main effect cannot masquerade as the mixed difference. |
| ORBIT_A2_NULLS | Owner-blind and validity-only routes preserve structure without a swappable owner category | `::Route`; `::build_actor_input`; `::_principal_invariant` | Both comparator outputs are principal-invariant at each role and have zero mixed differences within frozen tolerances | `::test_principal_swap_is_identical_outside_handle_slice_and_nulls_are_invariant` | Generic validity, branch presence, or owner-slice capacity cannot explain candidate specificity. |
| ORBIT_A2_INVALID | Every invalid route uses the registered current-state-only bypass | `::zero_path_owner_bypass`; `::evaluate_route_cell` | Centered logits and masked kernel equal the bypass exactly; legal action identity/order is unchanged | `::test_invalid_routes_fail_closed_to_exact_current_state_only_bypass` | A fail-open invalid payload, owner-dependent invalid path, or action-mask substitution is rejected. |
| ORBIT_A2_CONTROL | Route observations use fresh isolated equal-state clones and no reporting-identity side channel | `::RouteClone`; `::evaluate_route_cell`; `::_attach_reporting_identity`; `::run_verified_owner_binding_audit` | Evaluator clone metadata has no clone/principal/role ID; report-only IDs are attached after output; every original versus jointly relabeled/permuted evaluation has exactly equal logits and kernels | `::test_regression_reporting_clone_id_cannot_feed_the_evaluator`; `::test_owner_residual_is_normalized_zero_main_effect_and_alias_row_permutation_invariant`; `::test_registered_audit_is_deterministic_branch_nine_and_uses_exactly_fifteen_cells` | A P0/P1-encoded clone ID, sequential recurrence, mask/order, clock, roster, communication, RNG, lookup or address variation cannot create the contrast. |
| ORBIT_A2_BRANCH | The nine-way terminal is ordered and fail closed | `::Branch`; `::BranchWitnesses`; `::select_branch` | Every earlier failed witness selects its earlier registered branch | `::test_branch_precedence_is_exact_and_fail_closed` | A later favorable witness cannot override an earlier invalid control or leakage finding. |

### Bounded execution

The audit has `H=0`, `K_search=0`, zero hypothetical transitions and exactly 15
pure route-cell calls. Environment transitions, learner/trainer calls,
optimizer updates, return evaluations and model fits are all hard-coded zero.
The runner creates a write-once claim before the first route call and offers no
retry, rescue, sweep, technical-result substitute, B or C path.

The result-bearing command is intentionally not included here until CPM binds
the accepted source commit and registered isolated run root. CLI surface-only
inspection is available with:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_orbit_a2_verified_owner_binding_reachability.py --help
```

## Predecessor v8 evidence retained for contrast

Candidate: `CAND-VAP-ORBIT-LITE@adversarial-revision-v8`

Treatment: proof-sized deterministic `ORBIT-8CELL-SHADOW-READ-D1`

Status: synthetic implementation evidence only. It does not identify owner
specificity, natural use, utility, coordination, or task return.

## Frozen object

One canonical sealed prior-epoch snapshot is serialized once. Deterministic
sibling writes `H_(s,b)` use `B in {0,1}` as their only differing source-time
writer input. The audit restores eight independent immutable clones for the
complete `B x role x Q` block. `q0` is canonical and `q1` is a precommitted
bijective alias; both must produce the same actor input bytes and values.

The implementation owns four explicit field schemas:

- `F_match`: snapshot digest, current state, legal actions, recurrent state.
- `F_TQ`: `F_match` plus public role and age.
- `F_ORBIT`: payload, validity, age, actor tensor, recurrent state, evaluation
  order.
- `F_audit`: source snapshot, writer input, ancestry, and authenticated
  provenance digests.

For centered logits and action kernels:

```text
C(v) = v - mean_actions(v)
d_logit = (1/2) sum_q C(logit_11q-logit_01q-logit_10q+logit_00q)
Theta_logit = ||d_logit||_2
d_kernel = (1/2) sum_q(P_11q-P_01q-P_10q+P_00q)
Theta_kernel = (1/2) ||d_kernel||_1
```

A genuinely disjoint snapshot feeds a duplicate-input calibration manifest.
It freezes `tau=8*max(eta,one_ULP)` and `delta=4*tau` independently for logits
and kernels. The strict temporal null accepts only the sealed snapshot, public
role, and age; it cannot receive `B`, payload bytes/digests, or B-derived cache,
timestamp, hit, or retrieval metadata.

## Exact deterministic result

```text
terminal=PASS_LOGIT_INTERACTION_REACHES_FIRST_ACTION_KERNEL
valid=True
Theta_logit=2.82842712474619
Theta_kernel=0.92423431452002
strict_Theta_logit=0.0
strict_Theta_kernel=0.0
delta_logit=7e-15
delta_kernel=7e-15
owner_agnostic_payload_null_reproduces=True
```

| B | role | Q | logits | kernel |
|---:|---:|---:|---|---|
| 0 | 0 | 0 | `(0.5,-0.5)` | `(0.731058578630005,0.268941421369995)` |
| 0 | 0 | 1 | `(0.5,-0.5)` | `(0.731058578630005,0.268941421369995)` |
| 0 | 1 | 0 | `(-0.5,0.5)` | `(0.268941421369995,0.731058578630005)` |
| 0 | 1 | 1 | `(-0.5,0.5)` | `(0.268941421369995,0.731058578630005)` |
| 1 | 0 | 0 | `(-0.5,0.5)` | `(0.268941421369995,0.731058578630005)` |
| 1 | 0 | 1 | `(-0.5,0.5)` | `(0.268941421369995,0.731058578630005)` |
| 1 | 1 | 0 | `(0.5,-0.5)` | `(0.731058578630005,0.268941421369995)` |
| 1 | 1 | 1 | `(0.5,-0.5)` | `(0.731058578630005,0.268941421369995)` |

All registered invariants pass: whole-block support, sibling-B-only writer
variation, authenticated provenance, ancestry replay, Q lookup equivalence,
eight independent equal-state clones, strict-null B blindness, centered final
residual zero marginals, explicit schemas, and disjoint calibration.

The strongest owner-agnostic null can read the payload and exactly reproduces
the observed cells. Therefore this fixture supports only the narrow claim that
the registered B-by-role interaction reaches centered logits and the first
action kernel. It explicitly does not support an owner-specificity claim.

## Traceability

| claim_id | frozen assertion | code path and symbol | observable invariant | focused test | alternate explanation excluded |
|---|---|---|---|---|---|
| ORBIT_SIBLING | B is the only source-time sibling variation | `experiments/candidates/orbit_shadow_read/eight_cell_audit.py::write_sibling`; `::verify_sibling` | Writer input equality after replacing only B; ancestry and authentication recompute exactly | `tests/experiments/candidates/orbit_shadow_read/test_eight_cell_audit.py::test_sibling_writer_changes_only_b_input_and_authenticates_ancestry` | An unrelated source state, writer schema, or unauthenticated payload cannot create the contrast. |
| ORBIT_CLONES_Q | Complete eight-cell block uses independent clones and byte-equivalent Q aliases | `::restore_clone`; `::q_adapter`; `::run_eight_cell_audit` | Eight unique clone identities share one canonical source digest; q0 and q1 actor inputs are identical | `::test_whole_block_uses_eight_independent_equal_state_clones_and_q_aliases`; `::test_snapshot_restore_is_byte_equivalent_and_rejects_noncanonical_clone_source` | Sequential reuse, mutation, noncanonical restore, and Q routing differences are rejected. |
| ORBIT_ESTIMAND | Centered B-by-role interaction reaches logits and the first action kernel | `::actor`; `::_interaction`; `::run_eight_cell_audit` | Both registered statistics exceed their independently calibrated deltas | `::test_exact_eight_cell_audit_reaches_logit_and_first_action_kernel`; `::test_terminal_classification_is_branch_complete` | The terminal is not inferred from labels, an uncentered logit offset, or an incomplete branch table. |
| ORBIT_STRICT_NULL | Operational temporal/public null is B-blind | `::strict_temporal_null` | Function signature receives no B or payload and both strict interaction statistics are exactly zero | `::test_strict_temporal_null_has_no_payload_or_b_input_and_is_b_blind` | B-derived payload/cache metadata cannot leak into the null. |
| ORBIT_MARGINAL | Final centered residual has zero B and role marginals | `::_zero_marginal`; `::run_eight_cell_audit` | Functional zero-marginal audit passes over the complete block | `::test_centered_interaction_has_zero_margins_and_owner_agnostic_null_replays` | Main effects or a dropped cell cannot masquerade as the interaction. |
| ORBIT_LIMIT | Owner-agnostic payload null reproduces the cells | `::owner_agnostic_payload_null` | Every cell's logits are reproduced without owner identity | `::test_centered_interaction_has_zero_margins_and_owner_agnostic_null_replays` | The eight-cell result cannot be interpreted as owner specificity. |
| ORBIT_CALIBRATION | Duplicate calibration is disjoint and frozen before interpretation | `::calibrate` | Distinct calibration snapshot digest, duplicate manifests, zero measured noise, and ULP-derived positive deltas | `::test_disjoint_duplicate_calibration_freezes_thresholds_from_zero_noise` | Audit-cell reuse and a post-result threshold choice are excluded. |
| ORBIT_SERIALIZATION | Canonical evidence is complete and stable | `AuditResult.to_bytes`; `::_cell_payload` | Eight ordered cells, exact schema/invariant keys, and repeatable canonical bytes | `::test_schema_and_canonical_result_are_complete_and_byte_stable` | Output order and omitted-cell ambiguity cannot explain the result. |

## Bounded execution

The operation performs eight pure actor reads and one disjoint duplicate-input
calibration. It performs no environment transition, gradient update, training,
task-return rollout, parameter tuning, or rescue experiment.

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -c "from experiments.candidates.orbit_shadow_read.eight_cell_audit import run_eight_cell_audit; print(run_eight_cell_audit().to_bytes().decode('utf-8'))"
```

The canonical output contains the eight rows shown above and the exact
aggregate values in this index. Fresh focused validation:

```text
14 passed in 0.13s
```

The source has 476 active lines and is not imported by production packages or
runners. This isolated prototype does not change a production entry, runner
phase, artifact lifecycle, or serialization contract; execution readiness is
therefore not triggered. The accepted revision is the exact commit containing
this index, source, and mirrored test.
