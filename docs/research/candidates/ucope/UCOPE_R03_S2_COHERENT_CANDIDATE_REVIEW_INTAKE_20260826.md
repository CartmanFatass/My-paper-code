# UCOPE R03 S2 coherent-candidate review intake

Decision owner: EM-ucope

```text
document_kind=DIRECTION_ENGINEERING_REVIEW_INTAKE
document_revision=S2-REVIEW-INTAKE-R01
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
science_revision=UNCHANGED
construction_disposition=S2_COHERENT_CANDIDATE_READY_FOR_REVIEW
technical_acceptance=false
registered_execution=false
scientific_result=false
candidate_sha=null
reviewer_release=SEPARATE_IMMUTABLE_PACKET_ONLY
sancheck_release=false
repair_release=false
git_effect=false
effect_refs=EMPTY
```

## Idempotent intake and frozen authority

The CM-to-EM Work Packet is intaken idempotently as work id
`c63a8527558867c2236bb962b37da43244fcf6e7db489db8afcf46a406be8fda`.
Its exact packet SHA-256 is
`b694bfd6fc2f7744ca1b7a0c0b97a9164977707e4a3aaeae9925b9880ce51344`.
Before this create-once artifact was written, the official packet validator,
each packet authority ref, the scope ref, all referenced state schemas and
revisions, repository-relative containment, worktree registration, and the
empty Effect set matched current facts. The same checks independently matched
the expected research revision `11` SHA-256
`35c8024954ae5225131900401707b3cd4d34beeac54570125cb980593485bb08`.

The exact frozen authority boundary is:

| Reference | Frozen identity |
| --- | --- |
| `.codex/runtime/work/ready/c63a8527558867c2236bb962b37da43244fcf6e7db489db8afcf46a406be8fda/packet.json` | SHA-256 `b694bfd6fc2f7744ca1b7a0c0b97a9164977707e4a3aaeae9925b9880ce51344` |
| `.codex/runtime/work/ready/6d75ffec394baf60cb8085a11ffa216a5f77ab5b2a861be35b40d63432f0a4fb/packet.json` | SHA-256 `f64aec4ec44436a298086d50eb98ac5d7c3c354881f56f0a904976983b0fffb5` |
| `.codex/runtime/worktrees.json` | revision `11`, SHA-256 `d21cf1c19283d77eaf371289471e4cd2c6c343428f60a90727f5076026c0b755` |
| `docs/research/portfolio/PORTFOLIO.md` | SHA-256 `37248491759e616b772dac89076dd6ba3d7457bfa8f4cb61dc01f5560ce43dc9` |
| `docs/research/portfolio/workflow/registry.json` | revision `9`, SHA-256 `95e3dd2aaf0c54b589b6f29ed51aadd0871300ba6ec528f64e12509550e03941` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_R03_S2_ENGINEERING_REQUEST_20260826.md` | SHA-256 `d0858ad1e19c8b0dd1308bfaf4f55485c9d8bf5fbd0e39f78fc9099caf0d3fef` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_SCIENCE_CARD_20260823.md` | SHA-256 `94fa0ddb4ef4c686a60a1d9386f8b1b6184184f75df6c51a6fb61cedd8185e1c` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `8`, SHA-256 `0cfec99a35233c15db7a4df4ed8dea43ed2c9027406fb4a562263386809ed0e9` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `11`, SHA-256 `35c8024954ae5225131900401707b3cd4d34beeac54570125cb980593485bb08` |
| `docs/research/candidates/ucope/workflow/external-review/index.json` | revision `1`, SHA-256 `ce294036d6f75b08d5096a37eceeb19969e3e148b911816fca75584eb05037ad`, rounds `[]` |
| `temp/directions/ucope/test/s2/c1/S2_COHERENT_CANDIDATE_READY_FOR_REVIEW.json` | SHA-256 `99297c9eb89d5e10e7f2df8e5162d2e8e3fdb41d9f41816933428ff9efe287aa` |
| `temp/runtime/receipts/wt-ucope-engineering-s2c1.json` | SHA-256 `b0e09d489003e5269fff596eda057e30c472b8b7c38ff4afb4e54c8e74f22725` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |
| `scripts/hmasd_work_packet.py` | SHA-256 `a3a7f7b7a62b74fba3ac335e8ffc1897cd9435bcbc41a4549fad1571d3b4d9fb` |

The external-review index remains empty. The independent engineering Reviewer
considered below is not a Gemini/Pro scientific external-review round and does
not change that index.

## Current-byte candidate identity

The evidence-bearing assignment remains `s2c1`, worktree ref
`wt-ucope-engineering-s2c1`, branch `omp/ucope/engineering/s2c1`, lifecycle
`PROVISIONED`, base and head
`ee06a078c3c5ff904e00c727475c467a25ada1ff`, and `candidate_sha=null`.
The live native worktree status contains exactly two untracked direction-owned
paths and no tracked or outside-scope diff:

| Assignment-relative path | SHA-256 |
| --- | --- |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/s2_construction.py` | `b0b453e1a7d62f6db19a26d11fe6ff3a4c4f0791724f7f4b7df3e250a28d2b3f` |
| `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s2.py` | `26ef3d2ab20e0af75f735915d15918ea86845d6faa1daf7c105271e83ecf964a` |

Read-only current-byte verification also matched these assignment-local
technical evidence refs:

| Assignment-relative evidence | SHA-256 |
| --- | --- |
| `temp/directions/ucope/test/s2/c1/S2_COHERENT_CANDIDATE_EVIDENCE.json` | `220a6a56515e68e774a5a35e562197ab15f661ea1184a02c24c001da3451cee8` |
| `temp/directions/ucope/test/s2/c1/CM_FINAL_VERIFICATION_COMMAND_PLAN.json` | `71351401df115e512db6b2e082f4b898af39d9331f2636c320bad0b2cb56f4e9` |
| `temp/directions/ucope/test/s2/c1/cm-final-junit.xml` | `f83cde89ce3e8e8b4a9a533bc536e173a6899eabeffb0cb1e9f977f904b8948f` |
| `temp/directions/ucope/test/s2/c1/cm-final-proxy.json` | `0e31c7014587043f41341d16194f607a8e491277388f4c20df5fdd1959d106bb` |

These byte identities, not a candidate commit, define the current review
object. No commit, cleanup, staging, reuse, or mutation is adopted here.

## Bounded construction conclusion

EM-ucope records exactly the CM disposition
`S2_COHERENT_CANDIDATE_READY_FOR_REVIEW`. The disposition means that the
closed S2 finite evaluator, retained mandatory diagnostics, exhaustive
attribution structure, malformed-input refusal, and fail-closed atomic
complete-only publication boundary are coherent enough for the one independent
current-byte review allowed by the existing S2 request. It is not S2 technical
acceptance, registered execution, a complete R03 package, a scientific result,
an attribution class, or successor eligibility.

The exact construction predicates retained from the CM evidence are:

```text
checkpoint_slots=90
finite_panel_case_counts=128|256|16384
k_test_count=4
k_train_count=5
complete_tail_action_count_per_policy=64
forced_test_value_count=90
paired_contrasts=3
attribution_branches=7
terminal_action_classes=6
complete_only_publication=true
empty_or_incomplete_package_refused=true
cross_section_consistency_recomputed=true
atomic_interruption_leaves_no_final_package=true
malformed_path_object_checkpoint_duplicate_nonfinite_refusals_covered=true
```

The sole Implementer's initial construction had an internal complete-only
consistency gap. The same owner repaired it before the frozen candidate by
requiring strict package validation, exact top-level and 90-slot inventory,
exact current cardinalities, complete tail-action and forced-test retention,
and recomputation of decompositions, intervals, paired contrasts, acquisition
margins, competence, descriptive agreements, headroom, normalization,
attribution, and terminal consistency from retained facts. Synchronized
derived-fact and in-threshold headroom mutations are refused. CM independently
rechecked the repaired current bytes. No second Implementer, repair packet,
Reviewer, Verifier, or SANCheck was used to reach this conclusion.

## Tests, proxy, resources, and firewall

CM's final current-byte checks report AST exit `0`; unchanged S0/S1 plus the
focused S2 file completed with `57 passed`, `0 failed`, in `41.43` seconds.
These are result-blind technical checks, not scientific output.

The final counts-only structural proxy used fixture namespace
`TEST_ONLY_UCOPE_R01_R03_S2_CONSTRUCTION_C1` and records:

| Fact | Value |
| --- | ---: |
| toy cases | `16768` |
| weight checks | `3` |
| permutation checks | `924` |
| measured wall | `0.07389469997724518 s` |
| measured CPU | `0.0625 s` |
| measured peak RSS | `186630144 bytes` |
| measured I/O | `0 bytes` |
| cold load | `1.427850700012641 s` |
| projection scale count | `95` |
| projected wall | `387.3010414039527 s` |
| projected CPU | `0.10728292914058733 CPU-hours` |
| projected cores | `1` |
| projected peak RSS | `515145728 bytes` |
| projected I/O | `2312507074 bytes` |

All six projection gates pass. The formula remains
`r06_planning_reference_plus_measured_structural_coupon_times_ceiling_full_case_ratio`,
with no unmeasured speedup. None of these counts, timings, or projections is an
observed S2 result.

The conservative construction accounting is `0.225` S2 engineer-days,
`0.782` S2 TEST CPU-hours, and `1.1300480933333334` cumulative TEST CPU-hours
including the accepted pre-S2 bound. Maximum observed command wall is `42.89`
seconds; maximum command width is `8` cores; RSS upper bound is `4294967296`
bytes; scratch upper bound is `536870912` bytes; durable TEST upper bound is
`10485760` bytes; per-command I/O upper bound is `2147483648` bytes; cumulative
I/O remains below `8589934592` bytes; and GPU is false. Every frozen labor,
CPU/wall/core/RSS/scratch/durable/I/O/GPU cap remains satisfied and
non-replenished.

The firewall remains:

```text
registered_master_seeds=false
registered_checkpoints=false
complete_registered_panel=false
question_relevant_output=false
partial_values_exposed=false
complete_r03_package=false
result_command=false
run_or_claim=false
operator=false
reviewer=false
verifier=false
sancheck=false
commit=false
push=false
integration=false
external_effect=false
effect_refs=[]
```

## Remaining unknowns

This intake does not resolve:

1. whether the independent current-byte Reviewer finds a material conformance
   defect in the frozen risk cluster;
2. whether the same later current bytes can obtain
   `HMASD-MARL-SANCHECK-V1` status `PASS`;
3. whether CM can later grant S2 technical acceptance after both distinct
   gates; or
4. any registered checkpoint, complete-panel, empirical, attribution,
   successor, or scientific outcome.

## Reviewer release decision

The exact coherent-candidate prerequisite in the S2 request is now satisfied
on the two frozen current-byte digests above. EM-ucope therefore releases only
one independent, read-only engineering Reviewer through a new immutable Work
Packet to canonical `CM-ucope`. This artifact does not create or dispatch CM or
the Reviewer. Root owns reconcile and canonical manager reuse; CM may dispatch
exactly one genuine `hmasd-reviewer` leaf only after all current-byte
prerequisites below pass.

This release is narrower than S2 acceptance. It does not release SANCheck,
repair, test rerun, candidate commit, registered execution, a result command,
or any Git or external Effect. Reviewer output is advisory evidence returned to
CM; EM and CM retain their existing scientific and technical responsibilities.

### Reviewer current-byte prerequisites

Immediately before Reviewer dispatch, CM must verify all of the following
without writing the assignment:

1. the new Reviewer packet, this artifact, engineering revision `8`, the
   successful expected-revision `11` research CAS, S2 request, science card,
   registry revision `9`, worktree registry revision `11`, receipt, and CM
   evidence all match their exact frozen refs;
2. assignment `s2c1` remains `PROVISIONED` on the same branch and base/head,
   with `candidate_sha=null`, no tracked diff, and exactly the two untracked
   owned paths listed above;
3. both source/test SHA-256 digests and all four assignment-local evidence
   digests still match exactly;
4. no active or completed Reviewer already owns this exact current-byte review,
   and no unknown review commitment exists;
5. registered seeds/checkpoints/panel, question-relevant output, partial values,
   a complete R03 package, result command, run/claim/Operator, SANCheck, Git,
   provider, deployment, flight, and external Effect remain absent; and
6. the assignment is held immutable for the duration of the one review. Any
   byte/status/authority drift refuses dispatch and returns the scoped conflict
   below.

### Reviewer scope and return contract

The Reviewer performs read-only current-byte inspection of the frozen source,
focused S2 tests, and bound result-blind technical evidence. The single material
risk cluster is exactly:

- native panel/channel interventions;
- counter sharing and private addresses;
- ordinary-FP32 reduction behavior;
- checkpoint/resume conformance;
- finite-evaluator and mandatory-diagnostic completeness; and
- the fail-closed complete-only activity-boundary firewall.

The Reviewer may not edit, run tests, request registered data, perform
SANCheck, repair, or expand into a second review. Each finding must cite the
exact current-byte path and tight line/predicate reference, distinguish a
material conformance defect from a nonmaterial advisory, and avoid inferring
any R03 result. The return class is exactly one of:

- `S2_INDEPENDENT_REVIEW_CURRENT_BYTES_NO_MATERIAL_DEFECT`;
- `S2_INDEPENDENT_REVIEW_CURRENT_BYTES_MATERIAL_DEFECT`; or
- `S2_INDEPENDENT_REVIEW_EVIDENCE_GAP`.

CM records the exact Reviewer identity, current-byte digests, review return,
and findings in one result-blind review evidence file and advances engineering
state from expected revision `8` through the official state CAS. CM performs no
repair and grants no technical acceptance. A no-material-defect return comes
back to EM for a separately frozen SANCheck decision. A material defect or
evidence gap comes back to EM with exact scope and resume condition before any
repair decision.

## Scoped returns and resume conditions

| Return code | Exact scope | Resume condition |
| --- | --- | --- |
| `S2_REVIEW_AUTHORITY_OR_CAS_CONFLICT` | Any frozen SHA/revision differs, the create-once artifact already existed, or research/engineering CAS loses its expected revision. | Root publishes a new immutable packet binding the observed authority and expected revision; no existing artifact or packet is overwritten or replayed. |
| `S2_REVIEW_CURRENT_BYTES_CHANGED` | Assignment lifecycle/head/status, either source/test digest, or any bound technical-evidence digest differs. | CM returns the observed byte/status set without Reviewer dispatch. EM receives a new current-byte intake and decides whether a new review object is coherent. |
| `S2_REVIEW_OWNER_CONFLICT_OR_UNKNOWN` | An existing Reviewer owns the exact review or a prior dispatch outcome is unknown. | Root/CM observes the existing leaf/return to terminal knowledge; it never dispatches a duplicate Reviewer. |
| `S2_INDEPENDENT_REVIEW_CURRENT_BYTES_MATERIAL_DEFECT` | Reviewer identifies a material defect in the exact six-part risk cluster. | CM records the finding without edit or SANCheck. EM may freeze a separate bounded repair packet only after binding exact affected paths, remaining caps, and current state. |
| `S2_INDEPENDENT_REVIEW_EVIDENCE_GAP` | Reviewer cannot determine conformance from the frozen read-only bytes/evidence. | CM returns the missing exact ref or predicate. EM decides a separate evidence-only or repair authority; the Reviewer is not rerun under this packet. |

None of these is a negative scientific result, S2 technical acceptance, or a
direction-wide bare `BLOCKED` disposition.

## Explicit non-scope

This intake, its state CAS, and the separate Reviewer packet do not authorize:

- Reviewer execution in this EM turn, direct Reviewer creation/dispatch by EM,
  a second Reviewer, Verifier, scientific external review, or provider send;
- source/test/evidence/worktree modification, cleanup, staging, commit, push,
  integration, shared-core change, or any Git effect;
- tests, benchmarks, proxy reruns, SANCheck, repair, technical acceptance,
  registered checkpoint or panel access, result-run prepare/execute, claim,
  Operator, partial/result inspection, or a complete R03 package;
- changes to the R03 object, DIRECTION.md, S2 request, Portfolio, registry,
  external-review index, terminal S1 runs, or any path outside the two inbound
  owned paths; or
- treating coherent construction, Reviewer advice, resource/proxy facts,
  missing evidence, or a material defect as a scientific result, attribution
  class, successor eligibility, empirical release, deployment, or flight.

The next runtime owner is Root for one bounded reconcile of the new immutable
Reviewer packet. Canonical `CM-ucope` then owns current-byte prerequisite checks
and, only if they pass, the one Reviewer handoff. This artifact creates no task,
command, review, run, Git action, external operation, or Effect.
