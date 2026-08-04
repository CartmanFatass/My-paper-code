# SCOPE-1S Q16 instance certificate: code-science index

Candidate: `CAND-VAP-SCOPE-1S@adversarial-revision-v7`

Treatment: `SCOPE-1S-INSTANCE-CERT-01`

Status: synthetic existence/unit certificate passed; actual project Q16
instance absent. The absence is an engineering binding result, not a negative
scientific disposition. No stochastic package trial, return learning, fitting,
policy learning, selector learning, or partner adaptation was performed.

## Frozen unit witness

The two exact cells are:

```text
s0=(N=3, anonymous_role=0, absence=4, frozen_bundle=chi)
s1=(N=3, anonymous_role=1, absence=8, frozen_bundle=chi)
weights=(1/2,1/2)
B^T=(0,0,0,0,1,1,1,1) independently within each cell
Z={z0,z1}; each atom is exactly 16 bytes; correct Z^T=z_(B^T)
Y=64*1{A=B^T}-4*1{Q16 imported}
```

The actor uses one frozen read path. `z0` maps to action kernel `(1,0)` and
`z1` to `(0,1)`, so their total variation is exactly `1`. Reset uses no import
and chooses the same frozen action-0 kernel. Common-tape crossover values are:

```text
V(0,z0)=60; V(0,z1)=-4; gap=64
V(1,z1)=60; V(1,z0)=-4; gap=64
```

Every behavior-reachable current-only deterministic extreme map chooses one of
`Reset,z0,z1` independently in each of the two cells. The complete `3^2=9`
enumeration is:

| s0 | s1 | expected value |
|---|---|---:|
| Reset | Reset | 32 |
| Reset | z0 | 30 |
| Reset | z1 | 30 |
| z0 | Reset | 30 |
| z0 | z0 | 28 |
| z0 | z1 | 28 |
| z1 | Reset | 30 |
| z1 | z0 | 28 |
| z1 | z1 | 28 |

Thus `C=60`, `R=32`, `G_cur=32`, and `D=28`; the exact gaps are
`C-R=28`, `C-G=28`, and `C-D=32`, all above the registered margin `4` where
applicable.

## X ancestry and compatibility

The byte manifest covers all 38 pre/action-boundary bytes contiguously:

| byte range | field | category |
|---|---|---|
| `[0,4)` | current state | current-only |
| `[4,6)` | action mask | current-only |
| `[6,10)` | recurrent state | current-only |
| `[10,26)` | complete Q16 atom | historical payload |
| `[26,30)` | audit record | audit-only |
| `[30,34)` | source owner/epoch | forbidden leakage |
| `[34,38)` | outcome | post-treatment |

`X` is exactly the first ten current-only bytes. No historical-payload edge
feeds an `X` field; the complete atom reaches the actor only through the frozen
import adapter.

Each compatibility key freezes task/environment hashes, `N`, anonymous role,
exact absence, schema, quantizer, writer, reader, actor, recurrent manifest,
normalizer, action mask, partner checkpoint, import adapter, and cost schedule.
Source owner and source epoch are separate carrier metadata and are deliberately
excluded from `K`; changing them does not change compatibility or actor input.

## Donor and interference certificates

The precommitted zero-based donor permutation is
`(1,4,5,0,2,3,7,6)`, equivalent to the brief's one-based
`(2,5,6,1,3,4,8,7)`. It is applied independently within each compatibility
cell. Every donor transfers the whole 16-byte atom, has no fixed point, and
preserves `X/K`. The exact target/donor table per cell is:

| target B | donor B | count |
|---:|---:|---:|
| 0 | 0 | 2 |
| 0 | 1 | 2 |
| 1 | 0 | 2 |
| 1 | 1 | 2 |

Both clusters have horizon `64`, distinct cluster identities, zero cross-cluster
edges, and identical source/evaluated actor hashes. This proves the synthetic
H=64 interference closure and zero policy-generation distance only.

## Actual project binding result

Bounded production-surface reconnaissance found no active Q16 or SCOPE-1S
object in `ha_ctse_process/`, `envs/`, or `scripts/`:

```powershell
rg -n -i "\bQ16\b|SCOPE-1S|complete atom|historical carrier|import-adapter" ha_ctse_process envs scripts
```

```text
no matches
```

Therefore:

```text
actual_instance_status=ABSENT_ACTIVE_Q16_OBJECTS
```

The minimum missing objects are:

1. A registered complete-Q16 atom/schema/writer/reader/actor binding.
2. A supported same-`X/K`, outcome-divergent pair.
3. An actual H=64 cluster plus zero-policy-generation-distance certificate.

No digest or summary was substituted for a whole payload, and no `X` or `K`
field was weakened to manufacture a binding.

## Traceability

| claim_id | frozen assertion | code path and symbol | observable invariant | focused test | alternate explanation excluded |
|---|---|---|---|---|---|
| SCOPE_X | Every pre-action byte is classified and X has no prior-epoch descendant | `experiments/candidates/scope_1s/instance_certificate.py::build_manifest`; `::validate_manifest`; `::current_x` | Contiguous 38-byte manifest; X is exactly 10 current-only bytes; history-to-current edge fails | `tests/experiments/candidates/scope_1s/test_instance_certificate.py::test_byte_manifest_is_complete_contiguous_and_X_excludes_history_audit_and_post` | Historical payload, audit bytes, owner/epoch and outcome cannot leak into the current-only null. |
| SCOPE_K | Exact compatibility includes every frozen project-facing key except source owner/epoch | `::CompatibilityKey`; `::build_key`; `::build_carriers` | Fixed s0/s1 role-absence pairs; carrier owner/epochs vary while X/K remain identical | `::test_two_registered_cells_freeze_X_and_complete_compatibility_keys`; `::test_source_owner_and_epoch_are_not_compatibility_or_actor_inputs` | Weak K matching and owner semantics cannot create compatibility. |
| SCOPE_ACTOR | Complete Q16 atoms use one frozen actor/read path | `::q16_atom`; `::actor_kernel`; `::total_variation`; `::value` | Exact 16-byte atoms, TV=1 and both crossover gaps=64 | `::test_complete_Q16_atoms_and_frozen_actor_have_registered_TV`; `::test_crossover_runner_has_exact_common_tape_values_and_gaps` | Partial payload, learned selector and tape mismatch cannot explain the crossover. |
| SCOPE_NULL | Strongest current-only family is the complete nine-map envelope | `::enumerate_current_only_maps` | Exactly nine distinct maps; best value exactly 32 | `::test_all_nine_current_only_extreme_maps_are_enumerated_and_bounded_by_32` | An omitted Q16 atom or stochastic mixture cannot improve beyond an enumerated extreme point. |
| SCOPE_DONOR | History null is whole-payload, no-fixed-point and balanced within K | `::build_carriers`; `::donor_rows`; `::verify_donors` | Fixed permutation, 2x2 counts all two, same X/K, whole 16-byte payload | `::test_fixed_whole_payload_donors_are_deranged_balanced_and_within_cell`; `::test_donor_validator_rejects_fixed_point_partial_payload_and_cross_cell` | Outcome-selected donor, fixed point, cross-cell donor and digest-only transport fail. |
| SCOPE_H64 | Unit clusters are isolated and generation distance is zero | `::cluster_certificate`; `::validate_cluster` | Horizon 64, no cross edges, identical actor hashes | `::test_H64_interference_and_zero_generation_distance_certificate_is_strict` | Interference leakage or policy-version drift cannot enter the unit value. |
| SCOPE_BINDING | Actual cell validator has executable pass and every stop branch | `::BoundCell`; `::validate_bound_cell`; `::bind_actual_instances` | Unit object passes; incomplete X, atoms, pair, TV, gaps, donor, H64 and generation-distance mutations fail specifically | `::test_actual_cell_validator_exercises_each_stop_branch`; `::test_actual_binding_reports_absence_without_turning_it_into_scientific_failure` | Missing project objects are reported as binding absence rather than scientific NO_GO. |

## Bounded execution

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -c "from experiments.candidates.scope_1s.instance_certificate import run_instance_certificate as run; print(run().to_bytes().decode())"
```

```json
{"actor_tv":"1","actual_instance_status":"ABSENT_ACTIVE_Q16_OBJECTS","correct_value":"60","crossover_gaps":["64","64"],"current_only_maps":9,"current_only_value":"32","deranged_value":"28","donor_table":[["00",2],["01",2],["10",2],["11",2]],"invariants":[["complete_byte_level_X_ancestry",true],["two_exact_cells_and_complete_atoms",true],["actor_TV_and_crossover",true],["nine_map_current_only_envelope",true],["value_witness",true],["whole_payload_deranged_balance",true],["source_owner_epoch_excluded_from_K",true],["H64_and_zero_generation_distance",true],["validator_positive_and_negative_branches",true]],"missing_actual_objects":["registered_complete_Q16_atom_schema_writer_reader_actor_binding","supported_same_X_K_outcome_divergent_pair","H64_cluster_and_zero_generation_distance_certificate"],"reset_value":"32","terminal":"PASS_SYNTHETIC_UNIT_CERTIFICATE"}
```

Fresh focused validation:

```text
21 passed in 0.12s
```

The source has 390 active lines and no production consumer. This isolated
deterministic certificate does not change a production entry, runner phase,
artifact lifecycle or shared serialization contract; execution readiness is
not triggered. The accepted revision is the exact commit containing this
index, source, and mirrored test.
