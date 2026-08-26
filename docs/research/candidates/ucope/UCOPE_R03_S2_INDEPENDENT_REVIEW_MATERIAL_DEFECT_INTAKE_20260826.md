# UCOPE R03 S2 independent-review material-defect intake

Decision owner: EM-ucope

```text
document_kind=DIRECTION_ENGINEERING_REVIEW_MATERIAL_DEFECT_INTAKE
document_revision=S2-MATERIAL-DEFECT-R01
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
science_revision=UNCHANGED
review_class=S2_INDEPENDENT_REVIEW_CURRENT_BYTES_MATERIAL_DEFECT
material_finding_count=6
repair_decision=AUTHORIZE_BOUNDED_SAME_OWNER_REPAIR_BY_SEPARATE_PACKET
reviewer_rerun=false
sancheck_release=false
technical_acceptance=false
registered_execution=false
scientific_result=false
candidate_sha=null
git_effect=false
effect_refs=EMPTY
```

## Idempotent intake and frozen authority

The CM-to-EM Work Packet is intaken idempotently as work id
`27cbd55ddaaff5446c484acd825de8f4ab084456a114fcee82c15c1710cb1019`.
Its exact packet SHA-256 is
`2ba429b681a0324014ab66625553004dd8faacfe81387135e0cbb74fb7e7cdfb`.
Before this create-once artifact was written, the official Work Packet
validator, every authority ref, the engineering-state scope, five state-schema
validators, worktree registration, expected research revision `12` SHA-256
`8ef986780b12ddb6add4dd67bb37de06464428f423a9020e272218e03daa9044`,
and the empty Effect set matched current facts.

The exact frozen authority boundary is:

| Reference | Frozen identity |
| --- | --- |
| `.codex/runtime/work/ready/27cbd55ddaaff5446c484acd825de8f4ab084456a114fcee82c15c1710cb1019/packet.json` | SHA-256 `2ba429b681a0324014ab66625553004dd8faacfe81387135e0cbb74fb7e7cdfb` |
| `.codex/runtime/work/ready/513caf13fa6eed2a5027644d1e4f1ce82665fb47758a586e0a8f5d2ea28ea54f/packet.json` | SHA-256 `789174007a1834e49045b0362ae0d064e38961e16b9e1e5a7c5c27486aba488c` |
| `.codex/runtime/worktrees.json` | revision `11`, SHA-256 `d21cf1c19283d77eaf371289471e4cd2c6c343428f60a90727f5076026c0b755` |
| `docs/research/portfolio/PORTFOLIO.md` | SHA-256 `37248491759e616b772dac89076dd6ba3d7457bfa8f4cb61dc01f5560ce43dc9` |
| `docs/research/portfolio/workflow/registry.json` | revision `9`, SHA-256 `95e3dd2aaf0c54b589b6f29ed51aadd0871300ba6ec528f64e12509550e03941` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_R03_S2_ENGINEERING_REQUEST_20260826.md` | SHA-256 `d0858ad1e19c8b0dd1308bfaf4f55485c9d8bf5fbd0e39f78fc9099caf0d3fef` |
| `docs/research/candidates/ucope/UCOPE_R03_S2_COHERENT_CANDIDATE_REVIEW_INTAKE_20260826.md` | SHA-256 `760bd50f8485df40a381c9911ef75d23b6d0403c5648d8aca2583bc879e6fc8c` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_SCIENCE_CARD_20260823.md` | SHA-256 `94fa0ddb4ef4c686a60a1d9386f8b1b6184184f75df6c51a6fb61cedd8185e1c` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `9`, SHA-256 `64dfbb3709e1880788dfe875b223dc71bfd596fe16ca4d962be3b3063047abe4` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `12`, SHA-256 `8ef986780b12ddb6add4dd67bb37de06464428f423a9020e272218e03daa9044` |
| `docs/research/candidates/ucope/workflow/external-review/index.json` | revision `1`, SHA-256 `ce294036d6f75b08d5096a37eceeb19969e3e148b911816fca75584eb05037ad`, rounds `[]` |
| `temp/directions/ucope/test/s2/c1/S2_COHERENT_CANDIDATE_READY_FOR_REVIEW.json` | SHA-256 `99297c9eb89d5e10e7f2df8e5162d2e8e3fdb41d9f41816933428ff9efe287aa` |
| `temp/directions/ucope/test/s2/c1/S2_INDEPENDENT_REVIEW_RETURN.json` | SHA-256 `fbaa7c639b0db0aa013fbcc68f1170decd5b09c59fd85215d47ca33feed842aa` |
| `temp/runtime/receipts/wt-ucope-engineering-s2c1.json` | SHA-256 `b0e09d489003e5269fff596eda057e30c472b8b7c38ff4afb4e54c8e74f22725` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |
| `scripts/hmasd_work_packet.py` | SHA-256 `a3a7f7b7a62b74fba3ac335e8ffc1897cd9435bcbc41a4549fad1571d3b4d9fb` |

The sole independent Reviewer was the one recorded runtime identity
`/root/ucope_s2c1_independent_reviewer`, role `hmasd-reviewer`, dispatch count
`1`, with terminal return observed, no unknown dispatch outcome, and no second
Reviewer. This is runtime provenance only. It is not an additional authority
or a reason to rerun review.

## Frozen current-byte object

Assignment `s2c1`, worktree ref `wt-ucope-engineering-s2c1`, branch
`omp/ucope/engineering/s2c1`, base/head
`ee06a078c3c5ff904e00c727475c467a25ada1ff`, lifecycle `PROVISIONED`, and
`candidate_sha=null` remain unchanged. Read-only verification found no tracked
or outside-scope diff and exactly these two untracked direction-owned paths:

| Assignment-relative path | SHA-256 |
| --- | --- |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/s2_construction.py` | `b0b453e1a7d62f6db19a26d11fe6ff3a4c4f0791724f7f4b7df3e250a28d2b3f` |
| `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s2.py` | `26ef3d2ab20e0af75f735915d15918ea86845d6faa1daf7c105271e83ecf964a` |

The four assignment-local technical evidence digests also remain frozen:

| Assignment-relative evidence | SHA-256 |
| --- | --- |
| `temp/directions/ucope/test/s2/c1/S2_COHERENT_CANDIDATE_EVIDENCE.json` | `220a6a56515e68e774a5a35e562197ab15f661ea1184a02c24c001da3451cee8` |
| `temp/directions/ucope/test/s2/c1/CM_FINAL_VERIFICATION_COMMAND_PLAN.json` | `71351401df115e512db6b2e082f4b898af39d9331f2636c320bad0b2cb56f4e9` |
| `temp/directions/ucope/test/s2/c1/cm-final-junit.xml` | `f83cde89ce3e8e8b4a9a533bc536e173a6899eabeffb0cb1e9f977f904b8948f` |
| `temp/directions/ucope/test/s2/c1/cm-final-proxy.json` | `0e31c7014587043f41341d16194f607a8e491277388f4c20df5fdd1959d106bb` |

No source, test, evidence, or worktree byte was changed, cleaned, staged,
committed, replayed, or reused by this intake.

## Recorded disposition

EM-ucope records exactly
`S2_INDEPENDENT_REVIEW_CURRENT_BYTES_MATERIAL_DEFECT`. The six findings are
material engineering conformance defects in the current S2 candidate. They do
not change the R03 object, invalidate S0/S1 evidence, constitute an R03
scientific result, establish an attribution class or successor eligibility, or
fail the UCOPE direction. S2 technical acceptance, SANCheck, registered
execution, a complete R03 package, candidate SHA, and every Git/external Effect
remain absent.

## Six material findings and repair predicates

### S2-REVIEW-M01 — learned and RAW tie semantics

- **Current-byte ref:** `s2_construction.py:370-379,421-434,469-488`;
  predicates `greedy_index`, `raw_permavg_tail_action`, and
  `evaluate_learned_slot`. The missing test boundary is
  `test_variable_k_paid_probe_r01_r03_s2.py:224-231`.
- **Material impact:** learned root/tail and RAW-PERMAVG currently inherit the
  DP `1e-6` comparison tolerance. A later action that is larger by at most
  `1e-6` can be treated as tied, changing actions and downstream retained facts.
- **Repair predicate:** split learned/RAW exact-FP32 greedy selection from the
  DP comparator. Learned root, learned tail, and RAW-PERMAVG retain the first
  action only when compared FP32 scores are exactly equal; a strictly larger
  later FP32 score wins even when its gap is in `(0,1e-6]`. BELIEF-DP and the
  other DP comparators retain the frozen `1e-6` tolerance and tie order.
- **Bound verification:** add exact-tie and positive-near-tie cases for learned
  root, learned tail, RAW-PERMAVG, and unchanged DP behavior.
- **Resume condition:** return current-byte evidence that all four boundaries
  pass without changing any scientific threshold or action order.

### S2-REVIEW-M02 — checkpoint-inventory provenance binding

- **Current-byte ref:** `s2_construction.py:231-280,1607-1645`;
  predicates `validate_checkpoint_inventory` and `publish_complete_package`;
  supporting tests at `test_variable_k_paid_probe_r01_r03_s2.py:77-97,156-197`.
- **Material impact:** caller metadata plus a self-consistent mapping can reach
  `complete_r03_package=true` without proving retained values came from the
  exact cold-loaded final checkpoint bytes.
- **Repair predicate:** validation must derive batch/object/support/model
  identity from cold-loaded checkpoint content; the evaluator binds private
  evaluated material to the exact validated 90-slot inventory and byte digests;
  publication accepts only that sealed binding and revalidates it before the
  completion state. A raw caller mapping, copied metadata, substituted slot,
  or post-evaluation digest mutation is refused.
- **Bound verification:** use only synthetic nonregistered checkpoints to prove
  cold-load derivation, exact slot/digest binding, substitution refusal, manual
  self-consistent package refusal, and publication-time revalidation.
- **Resume condition:** return a current-byte provenance chain from synthetic
  cold-loaded bytes through evaluated private material to the final complete
  binding, with no registered checkpoint access.

### S2-REVIEW-M03 — abrupt-termination pending-byte exposure

- **Current-byte ref:** `s2_construction.py:1646-1661`, predicate
  `publish_complete_package`; the existing caught-exception-only gap is
  `test_variable_k_paid_probe_r01_r03_s2.py:332-356`.
- **Material impact:** termination after pending `package.json` is written but
  before manifest/rename can leave discoverable question-relevant bytes.
- **Repair predicate:** before the final atomic exposure, no discoverable path
  may contain a parseable question-relevant package. Use either staging that
  remains inaccessible and recoverable through observe-before-clean semantics,
  or one atomically exposed fully sealed package/manifest object. An ordinary
  readable sibling `package.json` and caught-exception cleanup are insufficient.
- **Bound verification:** a synthetic subprocess interrupts the real
  publication state machine at each material boundary. Every precommit
  termination leaves no readable question-relevant payload or final package;
  successful completion exposes exactly one sealed complete object. Recovery
  observes residue before any authorized cleanup and never interprets it.
- **Resume condition:** return interruption evidence for the real state machine,
  not a substitute helper, while preserving the complete-only firewall.

### S2-REVIEW-M04 — exact support facts

- **Current-byte ref:** `s2_construction.py:505-520,1368-1380`; predicates
  `validate_support` and complete-package support recomputation.
- **Material impact:** `int()` coercion can admit numeric strings, booleans,
  fractional values, or unexpected keys into `support_pass` and acquisition.
- **Repair predicate:** require the exact support key set; require each value's
  concrete type to be integer while rejecting booleans; require nonnegative
  values and all exact balance/cardinality relations before any threshold or
  acquisition evaluation. No coercion or ignored extra/missing key exists.
- **Bound verification:** reject strings, booleans, integral/nonintegral floats,
  fractions, negatives, missing keys, unexpected keys, and balance mismatch;
  accept only exact valid integer fixtures.
- **Resume condition:** return current-byte negative/positive fixture evidence
  showing fail-closed support parsing before acquisition logic.

### S2-REVIEW-M05 — posterior final-cast-once order

- **Current-byte ref:** `s2_construction.py:331-343`, predicate `_posterior`.
- **Material impact:** intermediate FP32 rounding changes the written posterior
  expression and can alter comparator or learned-channel behavior near a
  decision boundary.
- **Repair predicate:** evaluate the frozen numerator products, denominator,
  and division in the written multiplication/exponent order without
  intermediate FP32 casts, then cast the final scalar exactly once to FP32.
  The S2 comparator must match the already-frozen native learned-channel
  contract; no other source path or precision rule changes.
- **Bound verification:** for every count `N in {0,...,6}`, compare against an
  independent written-order final-cast-once reference, cover REDRAW/SEVERED
  `rho=1/2`, and retain the frozen downstream tie rules.
- **Resume condition:** return all-seven-count current-byte equality evidence
  and an explicit absence of intermediate FP32 casts.

### S2-REVIEW-M06 — complete BELIEF-DP headroom vectors

- **Current-byte ref:** `s2_construction.py:1297-1355`, complete-package
  headroom recomputation.
- **Material impact:** checking regime service probabilities, prior immediate
  values, and selected forced/immediate totals does not cover every BELIEF-DP
  expected action-value vector, so an omitted unintended FP32 tie can pass.
- **Repair predicate:** retain and validate the complete keyed inventory of
  BELIEF-DP root and tail expected action-value vectors over all three panels,
  every displayed six-bit history/posterior, every exposed `K_test` action, and
  every relevant immediate/PROBE choice. Every value is finite; the exact
  inventory is complete; every unintended action-value separation exceeds
  `1e-6`; only a science-card intended null uses the frozen tie rule.
- **Bound verification:** exact inventory/cardinality checks plus deletion,
  extra-key, nonfinite, and synchronized in-threshold mutation refusals must
  fail closed. Valid full synthetic coverage must pass.
- **Resume condition:** return current-byte evidence that every required vector
  participates in headroom validation before the headroom gate can pass.

## Overall repair authority

The six defects share one current-byte source file and one focused test surface,
have exact result-blind acceptance predicates, and require no science change.
The S2 construction evidence has consumed at most `0.225` of the `6` hard S2
engineer-days and reports `1.1300480933333334` cumulative TEST CPU-hours
against the `12` hard cap. EM-ucope therefore freezes one bounded same-object
repair tranche, delivered only through a new immutable packet to canonical
`CM-ucope` after the research CAS succeeds.

The repair tranche is exact:

```text
owner=sole_existing_ucope_s2c1_implementer
source_paths=2
engineer_days=MANAGED_0.75|HARD_1.0
incremental_TEST_CPUh=MANAGED_1|HARD_2
largest_TEST_wall=MANAGED_15_MIN|HARD_30_MIN
CPU_only=true
GPU=false
max_cores=8
max_aggregate_RSS=4_GiB
max_scratch=0.5_GiB
max_durable_TEST=0.05_GiB
max_incremental_aggregate_IO=2_GiB
reviewer_rerun=false
sancheck=false
technical_acceptance=false
registered_or_result_command=false
candidate_commit=false
```

The sole existing Implementer owns all six fixes as one coherent repair. No
second or parallel Implementer is authorized. The only source/test paths that
may change are the two frozen paths above. New result-blind validation evidence
is confined to `temp/directions/ucope/test/s2/c1/repair1/`; the prior coherent-
candidate and Reviewer evidence is immutable.

Before any repair write, CM must revalidate the new packet, this artifact,
research/engineering revisions, assignment lifecycle/head/status, both current
source/test digests, all four prior technical-evidence digests, the review
record, same-owner identity, remaining caps, and absence of any Reviewer rerun,
SANCheck, registered activity, candidate SHA, Git effect, or unknown repair
commitment. Drift returns without mutation.

The allowed validation is result-blind only:

1. AST/static parsing of the two repaired paths;
2. targeted M01--M06 positive and negative fixtures, including real subprocess
   interruption of the publication state machine with synthetic payloads;
3. the unchanged S0/S1 and existing S2 focused suite, with no deletion,
   weakening, xfail, or skipped current test, plus the new targeted tests; and
4. the same counts-only structural proxy and projection formula, with all
   original resource/firewall gates and no unmeasured speedup.

CM records exact precommand argv, cwd, input digests, fixture namespace, and
resource estimates before each allowed command. No `hmasd_run.py`, result
manifest, claim, Operator, registered identity/checkpoint/panel, or
question-relevant value is used.

The only successful repair return class is
`S2_MATERIAL_DEFECT_REPAIR_READY_FOR_SANCHECK_DECISION`. It requires every M01
through M06 predicate and validation above, frozen repaired byte digests,
current resource accounting, unchanged science/firewall, `candidate_sha=null`,
and engineering-state expected-revision `9` CAS with scope_ref still bound to
exact `DIRECTION.md`. It does not release SANCheck or grant technical
acceptance. Any missing or failed predicate returns
`S2_MATERIAL_DEFECT_REPAIR_INCOMPATIBLE` with finding IDs, actual bytes/costs,
and exact resume condition; there is no automatic second repair.

## Remaining unknowns

This intake leaves all of the following unresolved:

- repaired current bytes do not yet exist and have not been observed;
- all six repairs and their result-blind validation remain unperformed;
- the one Reviewer is terminal and will not review repaired bytes again;
- `HMASD-MARL-SANCHECK-V1` remains unauthorized and unperformed;
- S2 technical acceptance remains ungranted; and
- registered cold checkpoint loading, complete registered execution, atomic
  registered publication, empirical values, attribution, successor eligibility,
  and every scientific result remain unauthorized and unobserved.

## Scoped returns and resume conditions

| Return code | Exact scope | Resume condition |
| --- | --- | --- |
| `S2_REPAIR_AUTHORITY_OR_CAS_CONFLICT` | Any frozen SHA/revision differs, this create-once artifact existed, or research/engineering CAS loses its expected revision. | Root publishes a new immutable packet binding observed authority and expected revision; no artifact, packet, evidence, or review is overwritten/replayed. |
| `S2_REPAIR_CURRENT_BYTES_CHANGED` | Assignment lifecycle/head/status, either source/test digest, or any bound evidence/review digest differs before repair. | CM returns observed bytes/status without write. EM receives a new current-byte intake and re-evaluates the six-finding scope. |
| `S2_REPAIR_OWNER_CONFLICT_OR_UNKNOWN` | The sole Implementer identity cannot be reused safely, another owner is active, or prior repair commitment is unknown. | Root/CM observes the exact owner/commitment to terminal knowledge; it never dispatches a second Implementer or repeats an unknown write. |
| `S2_REPAIR_RESOURCE_ENVELOPE_INCOMPATIBLE` | The bounded tranche would exceed any incremental or cumulative labor/TEST/resource cap. | CM returns actual estimate/measurement and smallest safe reduction/batch/shard plan. Portfolio must explicitly revise any enlarged envelope; this authority does not. |
| `S2_MATERIAL_DEFECT_REPAIR_INCOMPATIBLE` | One or more M01--M06 predicates, unchanged-suite checks, proxy/resource gates, or firewall facts fail on repaired bytes. | CM returns exact failing finding IDs, bytes, tests, costs, and smallest same-object next condition. EM decides a new packet; no Reviewer/SANCheck/second repair starts automatically. |
| `S2_REGISTERED_OR_RESULT_BOUNDARY_ATTEMPTED` | Any repair or validation requests registered seeds/checkpoints/panel, question-relevant output, result root, claim, or Operator. | Stop before launch when possible; otherwise Root performs Effect-scoped observation/recovery. No command is replayed and no output is interpreted. |

None of these is an R03 scientific result, successor decision, UCOPE direction
failure, or direction-wide bare `BLOCKED` disposition.

## Explicit non-scope

This intake, state CAS, and separate repair packet do not authorize:

- repair in this EM turn, direct CM/Implementer creation or dispatch by EM, a
  second Implementer, Reviewer rerun, second Reviewer, Verifier, scientific
  external review, or provider send;
- any source/test/evidence/worktree change outside the two exact repaired paths
  and new `repair1` TEST evidence, or mutation/cleanup/reuse of prior evidence;
- SANCheck, S2 technical acceptance, registered checkpoint/panel execution,
  result-run prepare/execute, claim, Operator, partial/result inspection, or a
  complete R03 package;
- candidate SHA, staging, commit, push, integration, shared-core change, Git
  effect, deployment, flight, or other external Effect;
- R03 science, DIRECTION.md, Portfolio, registry, research authority other than
  the expected-revision CAS, prior immutable artifacts, terminal S1 runs, or
  external-review-index changes; or
- treating a Reviewer defect, repaired fixture, proxy/resource fact, missing
  output, or repair incompatibility as an R03 value, attribution class,
  successor eligibility, scientific result, or direction failure.

After the expected-revision research CAS and immutable repair-packet
publication, the exact next runtime owner is Root for one bounded reconcile.
Canonical `CM-ucope` then owns current-byte prerequisites and the single repair
tranche. This artifact itself creates no task, leaf, command, repair, run, Git
action, provider operation, or Effect.
