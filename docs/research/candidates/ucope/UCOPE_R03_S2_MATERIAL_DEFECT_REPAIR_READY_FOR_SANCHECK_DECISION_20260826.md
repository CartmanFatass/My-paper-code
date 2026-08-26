# UCOPE R03 S2 material-defect repair ready for SANCheck decision

Decision owner: EM-ucope

```text
document_kind=DIRECTION_ENGINEERING_REPAIR_READY_SANCHECK_DECISION
document_revision=S2-SANCHECK-DECISION-R01
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
science_revision=UNCHANGED
repair_disposition=S2_MATERIAL_DEFECT_REPAIR_READY_FOR_SANCHECK_DECISION
sancheck_decision=RELEASE_ONE_EVIDENCE_ONLY_HMASD_MARL_SANCHECK_V1_BY_SEPARATE_PACKET
sancheck_status=UNOBSERVED
technical_acceptance=false
registered_execution=false
scientific_result=false
candidate_sha=null
git_effect=false
effect_refs=EMPTY
```

## Idempotent intake and frozen authority

The CM-to-EM Work Packet is intaken idempotently as work id
`674132efc33aee13a08a7524a347224f10f4d657da49bec4c738fd0df4b9bbad`.
Its exact packet SHA-256 is
`390d0f631067349e66e6adaa3bc51938dc89c9bcb2bfa43b709b74f976689f19`.
Before this create-once artifact was written, the official Work Packet
validator, every authority ref, engineering scope, five state validators,
worktree registration, expected research revision `13` SHA-256
`ee3bfeffc53f01459485dc12d39585a6bf77ee1fb47459cc9d3b2ded242b0f13`,
and the empty Effect set matched current facts.

The exact frozen authority boundary is:

| Reference | Frozen identity |
| --- | --- |
| `.codex/runtime/work/ready/674132efc33aee13a08a7524a347224f10f4d657da49bec4c738fd0df4b9bbad/packet.json` | SHA-256 `390d0f631067349e66e6adaa3bc51938dc89c9bcb2bfa43b709b74f976689f19` |
| `.codex/runtime/work/ready/6714dbb10dc9d3316645e57c43c1108ea1cb9dec5a37120684e5fdb07f714086/packet.json` | SHA-256 `cb9ce92356721dd27276ae4d957616f77a057bf30a6fd37ea50ba5e3178e70e6` |
| `.codex/runtime/worktrees.json` | revision `11`, SHA-256 `d21cf1c19283d77eaf371289471e4cd2c6c343428f60a90727f5076026c0b755` |
| `docs/research/portfolio/PORTFOLIO.md` | SHA-256 `37248491759e616b772dac89076dd6ba3d7457bfa8f4cb61dc01f5560ce43dc9` |
| `docs/research/portfolio/workflow/registry.json` | revision `9`, SHA-256 `95e3dd2aaf0c54b589b6f29ed51aadd0871300ba6ec528f64e12509550e03941` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_R03_S2_ENGINEERING_REQUEST_20260826.md` | SHA-256 `d0858ad1e19c8b0dd1308bfaf4f55485c9d8bf5fbd0e39f78fc9099caf0d3fef` |
| `docs/research/candidates/ucope/UCOPE_R03_S2_INDEPENDENT_REVIEW_MATERIAL_DEFECT_INTAKE_20260826.md` | SHA-256 `55444593513aaecc9efa10673a0b39610139cf7174710781a9bfb63c3cbe8120` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_TECHNICAL_ACCEPTANCE_R06_20260826.md` | SHA-256 `86e6e08bf8269a3da1fa6aadd0eacdbf20a3c437c24be51a2184222c33d5ce81` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_SCIENCE_CARD_20260823.md` | SHA-256 `94fa0ddb4ef4c686a60a1d9386f8b1b6184184f75df6c51a6fb61cedd8185e1c` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `10`, SHA-256 `c9d0b0b42ffdbd0582da9d168369f91ddb0cf6ba9db3ef3aa8c36ce2174cda0b` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `13`, SHA-256 `ee3bfeffc53f01459485dc12d39585a6bf77ee1fb47459cc9d3b2ded242b0f13` |
| `docs/research/candidates/ucope/workflow/external-review/index.json` | revision `1`, SHA-256 `ce294036d6f75b08d5096a37eceeb19969e3e148b911816fca75584eb05037ad`, rounds `[]` |
| `temp/directions/ucope/test/s1/r6/R06_S1_TECHNICAL_ACCEPTANCE.json` | SHA-256 `eb346b006c271892b4419c3f9a24290474107299d589d23c6062104fde89c4fb` |
| `temp/directions/ucope/test/s2/c1/S2_COHERENT_CANDIDATE_READY_FOR_REVIEW.json` | SHA-256 `99297c9eb89d5e10e7f2df8e5162d2e8e3fdb41d9f41816933428ff9efe287aa` |
| `temp/directions/ucope/test/s2/c1/S2_INDEPENDENT_REVIEW_RETURN.json` | SHA-256 `fbaa7c639b0db0aa013fbcc68f1170decd5b09c59fd85215d47ca33feed842aa` |
| `temp/directions/ucope/test/s2/c1/repair1/S2_MATERIAL_DEFECT_REPAIR_READY_FOR_SANCHECK_DECISION.json` | SHA-256 `316e503afdba45de521294bc836ea35edf8a13798558b8191c81d2902a57cab2` |
| `temp/runtime/receipts/wt-ucope-engineering-s2c1.json` | SHA-256 `b0e09d489003e5269fff596eda057e30c472b8b7c38ff4afb4e54c8e74f22725` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |
| `scripts/hmasd_work_packet.py` | SHA-256 `a3a7f7b7a62b74fba3ac335e8ffc1897cd9435bcbc41a4549fad1571d3b4d9fb` |

The empty external-review index remains unchanged. `HMASD-MARL-SANCHECK-V1`
is a local engineering admission receipt, not a Gemini/Pro scientific external
review and not a provider operation.

## Repaired current-byte object

Assignment `s2c1`, worktree ref `wt-ucope-engineering-s2c1`, branch
`omp/ucope/engineering/s2c1`, base/head
`ee06a078c3c5ff904e00c727475c467a25ada1ff`, lifecycle `PROVISIONED`, and
`candidate_sha=null` remain unchanged. The current worktree has no tracked or
outside-scope diff and exactly these two untracked direction-owned paths:

| Assignment-relative path | Repaired SHA-256 |
| --- | --- |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/s2_construction.py` | `99847de2913c8aa34cbc889683849d6387ef3c430172d87d316c503fce34569b` |
| `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s2.py` | `96ba6d6bb2f6949ddacf62953a6eeda0fe63adaa1e8213a1801aa783f4a40c24` |

The same sole Implementer `ucope_s2c1_implementer` produced the repair. No
second or parallel Implementer, Reviewer rerun, Verifier, SANCheck, candidate
commit, or external Effect occurred.

## Recorded repair-ready disposition

EM-ucope records exactly
`S2_MATERIAL_DEFECT_REPAIR_READY_FOR_SANCHECK_DECISION`. This is a bounded
current-byte engineering conclusion: it is not S2 technical acceptance, an
R03 value or attribution class, successor eligibility, a registered package,
or a direction-level conclusion.

The finding-by-finding result-blind evidence is:

| Finding | Frozen repaired evidence |
| --- | --- |
| `M01` | Learned root/tail and RAW use exact-FP32 first-action tie semantics; every positive gap through `1e-6` selects the larger later score; DP retains the frozen `1e-6` tolerance and action order. |
| `M02` | Cold-loaded bytes derive checkpoint identity/provenance; exact `90`-slot digest inventory and evaluated material are sealed and revalidated; metadata, substitution, manual-package, and post-evaluation mutations fail closed. |
| `M03` | Six abrupt subprocess boundaries expose zero parseable precommit question payloads; the one success transition exposes exactly one sealed object; residue is observed before cleanup. |
| `M04` | Support requires the exact key set and concrete nonboolean nonnegative integers with exact balance/cardinality; malformed/coerced support fails closed. |
| `M05` | All seven posterior count cases use frozen written order, no intermediate FP32 casts, and exactly one final FP32 cast; REDRAW/SEVERED `rho=1/2` and learned-channel consistency hold. |
| `M06` | The exact BELIEF-DP inventory covers three panels, `64` displayed histories per panel, four `K_test` actions, `15` root and `768` tail action values; finiteness, separation, deletion/extra/nonfinite/synchronized-mutation gates pass. |

The assignment-local Implementer evidence is
`temp/directions/ucope/test/s2/c1/repair1/S2_MATERIAL_DEFECT_REPAIR_EVIDENCE.json`
at SHA-256
`12035baffa769142f0a9b3c6e90634e512aa322b247b4d50291ed856693c88fd`.
CM's final current-byte plan/result refs are:

| Purpose | Plan SHA-256 | Result SHA-256 |
| --- | --- | --- |
| AST | `56ad1c6e3d2d54d2f5f984d28346678e52d9f474eae3361ef7b48a614ef2b40d` | `87ca7bd573f70b3ffe1a36b64fa21c5b3b56770320b05ca9dfb69a387f9d3813` |
| full S0/S1/S2 suite | `d421d4c9c3a4bd5a176dbaa287f58c40f3f3add253619f6216e26f99084e242e` | `b1f7198c92e215e620fbeb6560ff510139ec3c166b2438c0459969219386cc93` |
| counts-only proxy | `9031939e9d16c180be84bd7068e3365f0067fca8245b7f07d49b948a338b382e` | `aefb1b420efa26b18b51a68608321f4446928539fb720654daf574caaf00c7d5` |

AST exited `0`. The unchanged S0/S1 and repaired S2 focused suite completed
with `61 passed`, `0 failed`; the CM record reports `45.53` seconds and the
conservative repair envelope records maximum observed command wall `45.97`
seconds.

The final CM counts-only proxy at SHA-256
`b69e2f19de7fcfd01231ff150063dd0da667f27a6ab4d3be278e949b069f4181`
records:

| Fact | Value |
| --- | ---: |
| toy cases | `16768` |
| checkpoint slots | `90` |
| attribution branches | `7` |
| measured wall | `0.07207619998371229 s` |
| measured CPU | `0.078125 s` |
| measured peak RSS | `185110528 bytes` |
| measured I/O | `0 bytes` |
| cold load | `1.379940400016494 s` |
| projected wall | `387.12828390456707 s` |
| projected CPU | `0.10769525552947623 CPU-hours` |
| projected cores | `1` |
| projected peak RSS | `515145728 bytes` |
| projected I/O | `2312507074 bytes` |

Every structural/projection gate is true and no unmeasured speedup is applied.
These values remain technical proxy facts, not observed S2 performance or a
scientific result.

The conservative repair accounting is `0.5` engineer-days, `0.8` incremental
TEST CPU-hours, `8` cores, `3758096384` RSS bytes, `268435456` scratch bytes,
`2884004` retained bytes, and `2087713000` incremental I/O bytes, with GPU
false. All bounded repair and original cumulative caps remain satisfied and
non-replenished.

The firewall remains:

```text
fixture_namespace=TEST_ONLY_UCOPE_R01_R03_S2_REPAIR1
registered_master_seeds=false
complete_registered_panel=false
question_relevant_output=false
result_run=false
operator=false
claim=false
reviewer_rerun=false
verifier=false
sancheck=false
commit=false
push=false
integration=false
effect_refs=[]
```

## SANCheck release decision

The repaired current bytes satisfy every M01--M06 repair predicate and all
result-blind construction/resource/firewall gates. The earlier R06 S1 technical
acceptance remains exact on the unchanged tracked native substrate and records
source-bound native preflight, guarded C++ reset/step/terminal with no Python
fallback, measured batching/parallel efficiency and phase facts, ordinary-FP32
hot-path conformance with no precision exception, and a counts-only complete
projection below `1800` seconds. The repaired S2 bytes supply the current
evaluator/firewall and projection evidence. Therefore the smallest lawful next
step is one separate current-byte `HMASD-MARL-SANCHECK-V1` receipt gate.

EM-ucope releases that one gate only through a new immutable Work Packet to
canonical `CM-ucope` after the research CAS succeeds. This artifact and inbound
packet do not run SANCheck or create a leaf. CM owns the evidence-only receipt
check; Root owns reconcile and canonical manager reuse.

### SANCheck current-byte prerequisites

Immediately before the one SANCheck receipt, CM must verify without candidate
execution or assignment mutation:

1. the new packet, this artifact, research revision produced by expected-
   revision `13` CAS, engineering revision `10`, DIRECTION, R03/S2 authorities,
   S1 R06 acceptance, registry/worktree revisions, receipt, review record, and
   repair return all match exact refs;
2. assignment `s2c1` remains `PROVISIONED` at the frozen branch/base/head with
   `candidate_sha=null`, no tracked/outside-scope diff, exactly the two
   authorized untracked paths, and the repaired source/test hashes above;
3. the Implementer evidence and all three CM final plan/result pairs plus final
   proxy hashes match; the prior coherent-candidate and Reviewer evidence is
   unchanged;
4. no SANCheck receipt path exists, no prior SANCheck owner/commitment is active
   or unknown, and no Reviewer rerun, repair, registered activity, result
   command, Git or external Effect has occurred; and
5. the assignment and evidence remain immutable from prerequisite observation
   through receipt/state persistence. Any drift refuses the gate.

### Evidence-only allowed behavior

The SANCheck packet permits only:

- read-only file hashing, worktree status/head observation, schema parsing, and
  tight static inspection of current source/evidence;
- arithmetic recomputation of thresholds, resource caps, projection gates, and
  the receipt's evidence-binding digest from immutable facts; and
- creation of one SANCheck receipt plus engineering-state expected-revision
  `10` CAS in their exact owned paths.

It permits no AST, test, build, benchmark, proxy, candidate-module execution,
subprocess, `hmasd_run.py`, claim, Operator, registered materialization,
Reviewer, Verifier, repair, SANCheck leaf, provider, or network action. The
freshness claim is byte/status/evidence freshness, not a rerun.

### HMASD-MARL-SANCHECK-V1 receipt contract

The create-once receipt path is
`temp/directions/ucope/test/s2/c1/sancheck1/HMASD_MARL_SANCHECK_V1_RECEIPT.json`.
It binds exact current source/test digests, tracked base/head, every authority
and evidence digest, the five SANCheck evidence groups, resource arithmetic,
firewall facts, status, and next owner.

The five evidence groups are:

1. **Source-bound native artifact and positive preflight:** unchanged tracked
   native substrate at the frozen base/head, R06 positive preflight/acceptance,
   and the repaired S2 source/test byte bindings.
2. **Guarded native lifecycle:** C++ reset/root-step/probe/tail-step/terminal,
   no Python environment fallback, exact checkpoint/frontier behavior, and the
   repaired complete-only publication binding.
3. **Actual batching/parallel efficiency and phase profiling:** R06 effective
   concurrency `0.8328877055612846`, overhead `0.20064204732869495`, throughput
   `147.57733033688447x`, cold load `7.667973400006304` seconds, stable ordering,
   and current repair resource/proxy evidence.
4. **Ordinary-FP32 hot path:** R06 exact FP32 learning/reduction evidence plus
   repaired M01 exact learned tie semantics and M05 final-cast-once posterior;
   no FP64, proof-grade lane, or precision exception.
5. **Positive complete toy-plan projection:** current counts-only projection
   wall `387.12828390456707 <= 1800` seconds, `1 <= 24` cores,
   `0.10769525552947623 <= 12` CPU-hours, `515145728 <= 10 GiB` RSS,
   `2312507074 <= 6 GiB` I/O, cold load below `360` seconds, and no unmeasured
   speedup.

The receipt status is exactly one of `PASS`, `EXPLANATION_REQUIRED`,
`EXPLANATION_RECORDED`, or `REPAIR_REQUIRED`. `PASS` requires all five groups,
all object-specific resource/firewall gates, and every exact byte/status binding
to pass with no unexplained deviation. `PASS` returns only
`S2_SANCHECK_PASS_READY_FOR_TECHNICAL_ACCEPTANCE_DECISION`; it does not itself
grant technical acceptance. Any other status returns
`S2_SANCHECK_NONPASS_ENVELOPE_RETURN` with exact failed/deviating predicates and
ends this automatic construction envelope without repair or empirical authority.

CM persists the receipt once and advances engineering state from expected
revision `10` through the official state CAS, retaining scope_ref on exact
`DIRECTION.md`, `candidate_sha=null`, and all firewall facts. Both outcomes
return to EM-ucope. A later technical-acceptance decision, or any non-PASS
Portfolio disposition, requires a new immutable authority.

## Remaining unknowns

This intake does not resolve:

- the SANCheck receipt status, which is unobserved and uncomputed;
- S2 technical acceptance, which remains ungranted;
- any candidate commit/integration decision;
- registered cold checkpoint loading, complete registered execution, atomic
  registered publication, empirical values, attribution, successor eligibility,
  or scientific result.

## Scoped returns and resume conditions

| Return code | Exact scope | Resume condition |
| --- | --- | --- |
| `S2_SANCHECK_AUTHORITY_OR_CAS_CONFLICT` | Any frozen SHA/revision differs, this create-once artifact existed, or research/engineering CAS loses its expected revision. | Root publishes a new immutable packet binding observed authority and expected revision; no artifact or receipt is overwritten/replayed. |
| `S2_SANCHECK_CURRENT_BYTES_CHANGED` | Assignment lifecycle/head/status, source/test digest, or any bound evidence digest differs. | CM returns observed facts without receipt. EM receives a new current-byte intake and re-evaluates SANCheck eligibility. |
| `S2_SANCHECK_OWNER_OR_RECEIPT_CONFLICT` | A receipt path exists, SANCheck commitment is active/unknown, or duplicate ownership is observed. | Root/CM observes the existing commitment/receipt to terminal knowledge; no duplicate receipt or SANCheck occurs. |
| `S2_SANCHECK_EVIDENCE_INCOMPLETE` | One of the five evidence groups cannot be verified read-only from exact refs. | CM returns the missing exact ref/predicate without executing candidate code. EM decides a separate evidence authority; no implicit rerun or repair occurs. |
| `S2_SANCHECK_NONPASS_ENVELOPE_RETURN` | Receipt status is EXPLANATION_REQUIRED, EXPLANATION_RECORDED, or REPAIR_REQUIRED. | CM records the exact status/reason and returns to EM/Portfolio. No technical acceptance, repair, SANCheck retry, or empirical authority follows automatically. |

None is an R03 result, successor decision, UCOPE direction failure, or a bare
`BLOCKED` disposition.

## Explicit non-scope

This intake, state CAS, and separate SANCheck packet do not authorize:

- SANCheck execution in this EM turn, direct task/leaf creation or dispatch by
  EM, a SANCheck leaf, Reviewer rerun, second Reviewer, Verifier, scientific
  external review, or provider send;
- source/test/evidence/worktree mutation, further repair, cleanup, staging,
  commit, push, integration, shared-core change, Git effect, deployment, flight,
  or any external Effect;
- AST/tests/build/benchmark/proxy reruns, candidate-module execution,
  registered checkpoint/panel activity, result-run prepare/execute, claim,
  Operator, partial/result inspection, or a complete R03 package;
- S2 technical acceptance, candidate SHA, empirical release, R03
  interpretation, attribution class, or successor decision;
- changes to R03 science, DIRECTION.md, Portfolio, registry, research authority
  outside expected-revision CAS, prior immutable artifacts/evidence, terminal
  S1 runs, or the external-review index; or
- treating repair readiness, SANCheck evidence/status, resource/proxy facts, or
  a non-PASS receipt as a scientific result or direction failure.

After the research CAS and immutable SANCheck packet publication, the next
runtime owner is Root for one bounded reconcile. Canonical `CM-ucope` then owns
the evidence-only receipt and engineering-state return. This artifact itself
creates no task, leaf, command, SANCheck receipt, run, Git action, provider
operation, or Effect.
