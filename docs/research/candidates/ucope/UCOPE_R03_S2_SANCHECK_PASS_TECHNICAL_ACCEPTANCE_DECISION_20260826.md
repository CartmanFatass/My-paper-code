# UCOPE R03 S2 SANCheck PASS technical acceptance decision

Decision owner: EM-ucope

```text
document_kind=DIRECTION_TECHNICAL_ACCEPTANCE
document_revision=S2-SANCHECK-PASS-R01
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
technical_disposition=S2_TECHNICALLY_ACCEPTED_RESULT_BLIND
sancheck_status=PASS
sancheck_class=S2_SANCHECK_PASS_READY_FOR_TECHNICAL_ACCEPTANCE_DECISION
technical_acceptance=true
registered_execution=false
scientific_result=false
attribution=false
successor_decision=false
candidate_sha=null
git_authorization=false
effect_refs=EMPTY
```

## Idempotent intake and frozen authority

The CM-to-EM Work Packet is intaken idempotently as work id
`cae7373be25ad3843f1e1fa7b07f899d240f12db8355b51ebf91597e2c1afc28`.
Its exact packet SHA-256 is
`e2cb1f2ed25a5c203acf09b19c570f649ae84ea17aad8442357a15240c453c2f`.
Before this create-once artifact was written, the official Work Packet
validator, every authority SHA/revision, the engineering scope, five state
validators, expected research revision `14`, the assignment current bytes and
status, the SANCheck receipt, and the empty Effect set all matched current
facts.

The frozen authority boundary is:

| Reference | Frozen identity |
| --- | --- |
| `.codex/runtime/work/ready/cae7373be25ad3843f1e1fa7b07f899d240f12db8355b51ebf91597e2c1afc28/packet.json` | SHA-256 `e2cb1f2ed25a5c203acf09b19c570f649ae84ea17aad8442357a15240c453c2f` |
| `.codex/runtime/work/ready/b9230ea48ba273c43b37d3cbc1d5b3e562732155eb9ad06698007fe228001b0a/packet.json` | SHA-256 `00eb7cddc267b22f495c2a4df6f46364fa98a33a0cbc9ebd73296ce560579951` |
| `.codex/runtime/worktrees.json` | revision `11`, SHA-256 `d21cf1c19283d77eaf371289471e4cd2c6c343428f60a90727f5076026c0b755` |
| `docs/research/portfolio/PORTFOLIO.md` | SHA-256 `37248491759e616b772dac89076dd6ba3d7457bfa8f4cb61dc01f5560ce43dc9` |
| `docs/research/portfolio/workflow/registry.json` | revision `9`, SHA-256 `95e3dd2aaf0c54b589b6f29ed51aadd0871300ba6ec528f64e12509550e03941` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_TECHNICAL_ACCEPTANCE_R06_20260826.md` | SHA-256 `86e6e08bf8269a3da1fa6aadd0eacdbf20a3c437c24be51a2184222c33d5ce81` |
| `docs/research/candidates/ucope/UCOPE_R03_S2_ENGINEERING_REQUEST_20260826.md` | SHA-256 `d0858ad1e19c8b0dd1308bfaf4f55485c9d8bf5fbd0e39f78fc9099caf0d3fef` |
| `docs/research/candidates/ucope/UCOPE_R03_S2_MATERIAL_DEFECT_REPAIR_READY_FOR_SANCHECK_DECISION_20260826.md` | SHA-256 `e8d4ca0b855166cf7b7ebf7ebeaa9f1acdf1d1d94d67e32ac737d42609fefecd` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_SCIENCE_CARD_20260823.md` | SHA-256 `94fa0ddb4ef4c686a60a1d9386f8b1b6184184f75df6c51a6fb61cedd8185e1c` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `14`, SHA-256 `0d2be57362cfcd6a58b20733200781c9b0b4c57fa39dbb2882a85c273efb3dd7` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `11`, SHA-256 `c93cc8e29172f501742396b5f73282114d1e7bb518d332c9ab7570ee97fe78da` |
| `docs/research/candidates/ucope/workflow/external-review/index.json` | revision `1`, SHA-256 `ce294036d6f75b08d5096a37eceeb19969e3e148b911816fca75584eb05037ad`, rounds `[]` |
| `temp/directions/ucope/test/s1/r6/R06_S1_TECHNICAL_ACCEPTANCE.json` | SHA-256 `eb346b006c271892b4419c3f9a24290474107299d589d23c6062104fde89c4fb` |
| `temp/directions/ucope/test/s2/c1/S2_COHERENT_CANDIDATE_READY_FOR_REVIEW.json` | SHA-256 `99297c9eb89d5e10e7f2df8e5162d2e8e3fdb41d9f41816933428ff9efe287aa` |
| `temp/directions/ucope/test/s2/c1/S2_INDEPENDENT_REVIEW_RETURN.json` | SHA-256 `fbaa7c639b0db0aa013fbcc68f1170decd5b09c59fd85215d47ca33feed842aa` |
| `temp/directions/ucope/test/s2/c1/repair1/S2_MATERIAL_DEFECT_REPAIR_READY_FOR_SANCHECK_DECISION.json` | SHA-256 `316e503afdba45de521294bc836ea35edf8a13798558b8191c81d2902a57cab2` |
| `temp/directions/ucope/test/s2/c1/sancheck1/HMASD_MARL_SANCHECK_V1_RECEIPT.json` | SHA-256 `1a2178e05c5fb1178049ac623c3fb27f68a61a82a3d0456c10e74cd15795d4cd` |
| `temp/runtime/receipts/wt-ucope-engineering-s2c1.json` | SHA-256 `b0e09d489003e5269fff596eda057e30c472b8b7c38ff4afb4e54c8e74f22725` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |
| `scripts/hmasd_work_packet.py` | SHA-256 `a3a7f7b7a62b74fba3ac335e8ffc1897cd9435bcbc41a4549fad1571d3b4d9fb` |

The empty external-review index is unchanged. This local technical acceptance
does not trigger scientific external review, an Agentify commitment, a provider
operation, or an archive update.

## Current-byte object

Assignment `s2c1`, worktree ref `wt-ucope-engineering-s2c1`, lifecycle
`PROVISIONED`, branch `omp/ucope/engineering/s2c1`, and base/head
`ee06a078c3c5ff904e00c727475c467a25ada1ff` remain exact. `candidate_sha` and
`integrated_sha` remain null. The fresh read-only observation found no tracked
or outside-scope diff and exactly these two nonignored untracked paths:

| Assignment-relative path | Current SHA-256 |
| --- | --- |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/s2_construction.py` | `99847de2913c8aa34cbc889683849d6387ef3c430172d87d316c503fce34569b` |
| `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s2.py` | `96ba6d6bb2f6949ddacf62953a6eeda0fe63adaa1e8213a1801aa783f4a40c24` |

EM did not import or execute either path, rerun AST/tests/proxy/SANCheck, or
modify the assignment. The prior immutable repair evidence records the sole
Implementer's M01--M06 repair, independent AST pass, `61 passed` and zero
failed S0/S1/S2 focused tests, and all counts-only proxy gates. Those checks are
accepted as frozen evidence and were not replayed in this decision.

## SANCheck PASS evidence

The create-once receipt records `status=PASS`, bounded class
`S2_SANCHECK_PASS_READY_FOR_TECHNICAL_ACCEPTANCE_DECISION`, five of five
evidence groups passing, zero failed predicates, and zero unexplained
deviations. Its receipt gate was read-only: no leaf, candidate execution,
registered materialization, result run, claim, Operator, Reviewer, Verifier,
repair, provider/network operation, Git action, or external Effect occurred.

The five accepted evidence groups are:

1. **Source-bound native artifact and positive R06 preflight.** The unchanged
   tracked native substrate, positive R06 preflight/execute-preflight, memory
   safety, terminal `SUCCEEDED` native artifact, and repaired source/test byte
   bindings are exact.
2. **Guarded native lifecycle and complete-only publication.** Native
   reset/root-step/probe/tail-step/terminal behavior has no Python environment
   fallback; checkpoint/frontier and cold inventory bindings pass; six abrupt
   boundaries expose zero parseable precommit question payloads; one success
   exposes exactly one sealed object; residue is observed before cleanup.
3. **Batching, parallel efficiency, and phase profiling.** Effective
   concurrency, overhead, throughput, cold load, stable ordering, and phase
   profile all satisfy their frozen gates.
4. **Ordinary-FP32 hot path.** R06 ordinary-FP32 learning/reduction remains
   exact; repaired M01 separates exact learned ties from DP tolerance; repaired
   M05 preserves written order, no intermediate FP32 cast, and one final cast;
   there is no FP64/proof-grade lane or precision exception.
5. **Positive complete toy-plan projection.** The current counts-only complete
   projection satisfies wall/CPU/core/RSS/I/O/cold gates with no unmeasured
   speedup. It remains a technical proxy, not observed S2 performance.

The immutable binding set additionally covers the S1 acceptance, S2 request,
coherent-candidate evidence, independent material-defect review, M01--M06
repair evidence, all three CM final plan/result pairs, final proxy, worktree
receipt, current assignment identity, and every authority SHA/revision.

## Arithmetic and resource review

EM independently recomputed `1 / concurrency - 1` from the receipt and obtained
the exact recorded overhead. All threshold comparisons remain true:

| Technical quantity | Current value | Frozen gate |
| --- | ---: | ---: |
| effective concurrency | `0.8328877055612846` | `>= 0.75` |
| recomputed parallel overhead | `0.20064204732869495` | `<= 0.30` |
| native/reference throughput | `147.57733033688447x` | `>= 1.25x` |
| R06 cold load | `7.667973400006304 s` | `<= 360 s` |
| current proxy cold load | `1.379940400016494 s` | `<= 360 s` |
| projected complete wall | `387.12828390456707 s` | `<= 1800 s` |
| projected complete CPU | `0.10769525552947623 CPU-hours` | `<= 12 CPU-hours` |
| projected cores | `1` | `<= 24` |
| projected peak RSS | `515145728 bytes` | `<= 10737418240 bytes` |
| projected I/O | `2312507074 bytes` | `<= 6442450944 bytes` |

The conservative repair accounting also remains within every non-replenished
cap: `0.5 <= 0.75` engineer-days, `0.8 <= 1.0` TEST CPU-hours, `8 <= 8`
cores, `3758096384 <= 4294967296` RSS bytes,
`268435456 <= 536870912` scratch bytes, `2884004 <= 53687091` durable
bytes, and `2087713000 <= 2147483648` incremental I/O bytes; GPU is false.
The original S2 and total construction envelopes are not replenished or
enlarged.

## Bounded S2 technical disposition

EM-ucope accepts the exact current S2 bytes as technically satisfying the
frozen result-blind S2 engineering contract. The disposition is exactly
`S2_TECHNICALLY_ACCEPTED_RESULT_BLIND`.

This acceptance is warranted because the coherent candidate's six material
review defects were repaired on the same exact two paths, the immutable
current-byte validation evidence passes, and `HMASD-MARL-SANCHECK-V1` finds all
five technical evidence groups complete with no unexplained deviation. The
accepted object includes the finite evaluator/diagnostics, complete-only
publication and activity firewall, exact support/provenance/posterior/tie
semantics, complete BELIEF-DP inventory, native/runtime bindings, and bounded
resource projection defined by the S2 request.

This is finite, result-blind technical acceptance only. It is not:

- registered checkpoint or panel execution;
- a partial or complete R03 scientific result;
- an empirical value, performance observation, or attribution class;
- a successor-eligibility, lifecycle, or investment decision;
- a candidate SHA, commit, push, integration, shared-core, or Git authority;
- permission to inspect registered, partial, question-relevant, or result
  bytes; or
- permission to create or dispatch a manager, leaf, run, claim, or Operator.

## Result and activity firewall

The accepted evidence and this decision retain:

```text
registered_master_seeds=false
registered_checkpoints=false
complete_registered_panel=false
registered_cold_load_observed=false
complete_registered_execution=false
atomic_registered_publication_observed=false
partial_result=false
question_relevant_output=false
scientific_result=false
result_run=false
claim=false
operator=false
reviewer_rerun=false
verifier=false
repair_after_sancheck=false
candidate_sha=null
commit=false
push=false
integration=false
provider_or_network=false
effect_refs=[]
```

## Remaining unknowns

Technical acceptance leaves these exact unknowns unresolved:

1. No candidate SHA, commit, push, integration, or durable Git identity exists
   for the two accepted untracked current-byte paths.
2. Registered cold checkpoint loading has not been observed.
3. Complete registered-panel execution has not occurred.
4. Atomic complete-only publication under a registered execution has not been
   observed; the accepted abrupt-boundary evidence is synthetic/result-blind.
5. Empirical values, scientific attribution, claim-class selection, successor
   eligibility, and the R03 scientific disposition remain wholly unobserved.
6. Portfolio has not decided the post-acceptance lifecycle/investment boundary,
   including whether to invest a separate candidate/Git authority, a later
   registered-result reconciliation, defer, park, or close.

None is a defect, a negative result, a direction failure, or a bare `BLOCKED`
state. Each requires its own current authority and immutable packet.

## Portfolio decision request

S2 result-blind technical acceptance is material new direction evidence.
Portfolio owns lifecycle, priority, and investment, while Root owns canonical
task orchestration and final Git integration. EM-ucope therefore publishes one
decision-material-only immutable Work Packet to canonical `Portfolio` after
the research-state expected-revision `14` CAS succeeds.

Portfolio must make one bounded post-acceptance disposition under the unchanged
R03 object, registered/result firewall, current `ACTIVE` lifecycle, remaining
non-replenished caps, exact current-byte digests, and candidate SHA null. It may
invest only a separately frozen next authority, defer while `ACTIVE` with an
exact evidence trigger, park with a registry CAS and reactivation condition, or
close with exact evidence-backed scope. A positive Portfolio disposition does
not itself commit, integrate, or run registered evaluation: candidate/Git and
registered/result execution require distinct later authorities and packets to
their exact owners.

Portfolio may write only its existing authority and, only if lifecycle,
dependency, generation, runtime-ref, or reactivation facts change, registry
revision `9` through the official expected-revision CAS. This EM decision does
not preselect Portfolio's disposition or create/dispatch its task.

## Scoped conflicts and resume conditions

| Return code | Exact scope | Resume condition |
| --- | --- | --- |
| `S2_TECHNICAL_ACCEPTANCE_AUTHORITY_OR_CAS_CONFLICT` | A frozen ref differs, this create-once artifact existed, or research CAS loses expected revision `14`. | Root publishes a new immutable EM packet binding observed bytes/revision; no artifact or state is overwritten. |
| `S2_TECHNICAL_ACCEPTANCE_CURRENT_BYTES_CHANGED` | Assignment lifecycle/head/status or either accepted source/test digest differs before persistence. | CM returns a new exact current-byte/evidence intake; EM reevaluates without importing/executing candidate code. |
| `S2_TECHNICAL_ACCEPTANCE_RECEIPT_CONFLICT` | Receipt SHA/status/class, any evidence-group predicate, failed/deviation list, arithmetic, resource, or firewall fact differs. | CM supplies one new immutable receipt/coherence return; no receipt, SANCheck, check, or repair is replayed implicitly. |
| `S2_POST_ACCEPTANCE_PORTFOLIO_RETURN` | Portfolio defers, parks, closes, or selects a bounded next investment. | Follow only the exact Portfolio authority and new packet; no candidate/Git or registered/result action is inferred from this technical acceptance. |

## Explicit non-scope

This artifact, research-state CAS, and Portfolio decision packet do not
authorize:

- candidate import/execution, AST, tests, build, benchmark, proxy, SANCheck
  replay, Reviewer rerun, Verifier, repair, or mutation of assignment/evidence;
- registered seeds/checkpoints/panel, result-run prepare/execute, claim,
  Operator, partial/result inspection, or a complete R03 package;
- candidate creation, clean/stage/commit/push/integration, shared-core change,
  deployment, flight, or any Git/external Effect;
- provider/network operation, scientific external review, archive/index write,
  or external commitment;
- empirical value, attribution, successor, lifecycle, priority, investment, or
  scientific-result inference by EM; or
- task/leaf creation or direct dispatch by EM.

After the research CAS and packet publication, the next runtime owner is Root
for one bounded reconcile. Canonical `Portfolio` then owns the post-acceptance
investment/lifecycle decision. This artifact itself creates no task, run,
receipt, candidate, Git action, provider operation, registered access, or
Effect.
