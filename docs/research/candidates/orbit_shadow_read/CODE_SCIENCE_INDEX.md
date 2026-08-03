# ORBIT eight-cell cloned shadow-read: code-science index

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
