# UCOPE R01 r03 S1 current-byte engineering request

```text
direction_id=ucope
logical_identity=EM-ucope
generation=1
artifact_role=local_evidence_reconciliation_and_s1_engineering_request
observed_utc=2026-08-25T11:57:50Z
portfolio_decision=Post-evidence manager continuation — 2026-08-25T11:40:48Z
portfolio_sha256=a3da214941f3163f21033991f6d5f2338e2d3b59f32c3ef32cb4dfcc1998f65a
ucope_lifecycle_checkpoint_sha256=95b17c62eeb57583c99385fb5cde683f46c30c0a0b2cb72a0fda62146527f657
registry_revision=7
registry_sha256=fb1c32ce91d10625f7e1117c4fe3cff9f031c9ce66a1b540880d38ce075d3089
frozen_question_sha256=0c608c5f791d055f58fd51a308065b2c4024f1e1b4eeb8ef6b3995bb90eaad58
frozen_evidence_set_sha256=724ce24ab8548807ca400aa8179a05b5e103a023bb61f8f639c9a16b5aeeebee
scientific_command_executed=false
result_or_partial_output_inspected=false
external_review_performed=false
direction_authority_changed=false
s1_engineering_request=true
s2_release=false
```

## Frozen identity and workflow reconciliation

The exact frozen inputs were present at the assignment hashes:

| Reference | SHA-256 |
| --- | --- |
| `docs/research/candidates/ucope/DIRECTION.md` | `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_SCIENCE_CARD_20260823.md` | `e08744fa18d708c9ad570bdce8b71296407991a4f5f79d502d37330913435fd8` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_CURRENT_OBJECT_PORTFOLIO_SELECTION_20260823.md` | `b5789c78a3505eef553bbbf69e03bc8b6a7f4b432bee8b08d421cec5faf8ceed` |
| `docs/research/candidates/ucope/workflow/research/state.json` assignment revision 1 | `ac53f9312209eb3a872a896ba356ad06c779aecc40082914cb6bcf895c3614e2` |
| `docs/research/candidates/ucope/workflow/research/state.json` Root schema-v2 migration revision 2 | `741df5ff851806d98058bf843f358833fa32e67a3b7253f5f00395ef09baeeba` |
| `docs/research/candidates/ucope/workflow/external-review/index.json` revision 1 | `ce294036d6f75b08d5096a37eceeb19969e3e148b911816fca75584eb05037ad` |

Registry revision 7 identifies `ucope` as `ACTIVE`, assigns logical identity
`EM-ucope` generation 1, retains dependencies `[]`, and points to the exact
UCOPE workflow paths. Its UCOPE entry still cites the revision-5
`Post-evidence manager continuation` checkpoint above; the intervening
Portfolio revisions retain UCOPE unchanged while expanding other active work
and retiring the generic `PARKED` lifecycle. Root's compatible schema-v2
migration advanced research state mechanically to revision 2 while retaining
`IDLE`, `actionable=false`, `registry_revision_seen=1`, and no engineering
request; its next-action owner is now explicit as `ROOT`. The external-review
index has no rounds. These are workflow facts, not scientific findings.

The unchanged direction authority records the source-grounded current position:
the variable-k paid-probe object is Pro-closed, S0 is complete, and S1 is the
current engineering continuation. The finite staged construction selection
makes S1 automatic only after all S0 gates and CM acceptance. The later tracked
S0 technical-acceptance intake records every predicate satisfied, recommends
the preauthorized S1 continuation without a new Portfolio vote, and explicitly
leaves S2 unreleased. Registry revision 7 carries this durable current-byte S1
boundary forward unchanged before Root considers CM dispatch.

## Controlling evidence and provenance limits

The request uses these tracked direction-scoped records:

| Reference | SHA-256 | Role |
| --- | --- | --- |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_CHATGPT_PRO_CLOSED_INTAKE_20260823.md` | `03af3ca2011e0d8c41a680faca5fd8aeecbb4724d4de28c37204a8de85ca6944` | Preserved prior closure record; not new provider evidence |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_STATIC_FEASIBILITY_PORTFOLIO_EM_VALUE_INTAKE_20260823.md` | `7586f4624111974dc993c328c7ae47b21adcd7801b38fd7a31e1b6c380112554` | Detailed staged scope, gates, and cost boundary |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_FINITE_STAGED_CONSTRUCTION_PORTFOLIO_SELECTION_20260823.md` | `7818c4b353037243993590a5d4968d429a92433b38ffbea99271789febc18aec` | Portfolio authorization and conditional stage releases |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_S0_CM_TECHNICAL_ACCEPTANCE_PORTFOLIO_EM_INTAKE_20260824.md` | `f7d5522506c3bd96d84c222dc6474cc40b6f4dfbb0aed12b7be68c1bda63b7ae` | Accepted S0 facts and S1-only continuation recommendation |

Four historical locators named by those intakes are not present at their exact
repository paths:

- `temp/handoffs/code_manager_to_root/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_STATIC_NATIVE_FEASIBILITY_CM_RETURN_20260823.md`;
- `docs/session/ROOT_TO_PORTFOLIO_UCOPE_R03_STATIC_NATIVE_FEASIBILITY_CM_RETURN_ACK_20260823.md`;
- `temp/handoffs/code_manager_to_root/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_S0_CM_TECHNICAL_ACCEPTANCE_20260823.md`; and
- `docs/session/ROOT_TO_PORTFOLIO_UCOPE_R03_S0_CM_TECHNICAL_ACCEPTANCE_ACK_20260824.md`.

This reconciliation therefore treats the tracked EM intakes as the exact
repository facts they claim to preserve; it does not claim to have
independently inspected or reperformed the missing CM/Root records. The missing
locators are not assignment inputs and must not be cited as inspected evidence.

The frozen current-object selection embeds older digests
`card_sha256=94fa0ddb...` and `pro_closed_sha256=0e7908ad...`, which do not match
the current bytes frozen above. The path and R03 object identity agree, but the
available evidence does not certify byte identity across those digests. This
checkpoint binds the exact current direction evidence plus the reconciled
registry-revision-7/Portfolio authorities above. It does not use the embedded
historical digests to authenticate current bytes or reinterpret Pro closure.

No UCOPE evidence record defines an R04 scientific object, R04 ABI, or
revision-4 implementation authority. Every controlling scientific reference
names R03. The Portfolio phrase “revision-4-aware” is therefore satisfied only
as current workflow/current-byte reconciliation; it is not converted into an
R04 science or implementation claim.

## Evidence separation

### Repository facts

1. The staged selection defines S1 as the source-bound native semantic core:
   the balanced `PERSISTENT`, `REDRAW`, and `SEVERED` panels; all six frozen
   arms; the fixed counter law; the `13→64→64→1` scorer and `9→32→1` baseline;
   ordinary-FP32 REINFORCE/entropy/AdamW; exact support counters; the 90-slot
   final-checkpoint schema; and atomic batch-frontier crash/resume behavior.
2. S1 permits only nonregistered, result-blind fixtures. It may cover every
   legal action, history, panel, and supported width, but it may not instantiate
   the registered complete training/evaluation population or emit scientific
   values.
3. The current repository already contains an S0/S1 package and two focused
   contract files. `benchmark.py` names their exact source-hash surface and
   exposes a `--stage s1` result-blind benchmark/projection path.
4. Static inspection identifies material current-byte defects or evidence gaps:
   the S0 benchmark body is split into an absent return path plus unreachable
   code; no focused test exercises S1 CLI dispatch; the purported all-six-arm
   helper executes only nonlearned primitives; the 90-slot manifest derives
   synthetic slot digests from one state rather than independently persisted
   slot bytes; two acceptance gates are hard-coded declarations; one reduction
   digest validator is weaker than adjacent digest validators; and malformed
   native reset can leave earlier lanes inserted before a later invalid arm is
   rejected.
5. Research state has no durable request, while engineering state remains
   revision 1 `UNREQUESTED`. Existing source is therefore a candidate to
   reconcile, not evidence of current CM acceptance.

### External evidence

None was collected. No provider was contacted, no external-review round was
opened, and the external index is unchanged. The repository-held Pro closure is
preserved as a prior disposition only; its scientific response is not
reinterpreted here.

### Local inference

The entry predicate for S1 is established by the tracked authority chain, and
the current source/test surface makes one bounded engineering assignment
concrete. The observed defects mean the current bytes cannot be declared
accepted from static inspection. They do not require new scientific design:
one same-direction CM can reconcile and, where necessary, repair the existing
result-blind S1 surface, then return exact current-byte technical evidence.

The 90-slot wording has one remaining implementation-level ambiguity: the
tracked scope requires a “90 final-checkpoint schema,” while current code proves
only a structural TEST manifest derived from one in-memory state. CM may resolve
this only by demonstrating that the existing fixture representation satisfies
the tracked S1 schema boundary or by returning a science-binding ambiguity to
EM. CM must not manufacture registered 90-replica activity to close the gap.

### Speculation excluded

Whether the focused checks pass after repair, whether all S1 current-byte
performance gates pass, whether the 90-slot interpretation is technically
sufficient, and whether the work remains within its caps are unknown until CM
returns evidence. No outcome, efficacy value, registered population, future S2
acceptance, or empirical allocation is predicted here.

## Actionability decision

One S1-only engineering request is directly actionable for Root CM dispatch.
S1's entry rule is satisfied; S1 itself is not yet accepted. S2 remains
unreleased. Root alone may dispatch CM, and CM alone owns construction and
technical acceptance. This EM artifact neither dispatches nor executes.

## Engineering request — S1 current-byte semantic-core verification and repair

### Scope

Reconcile the current retained UCOPE R01 r03 S0/S1 bytes, repair only defects
that prevent the frozen S1 contract, and return one CM-authored current-byte S1
technical-acceptance or exact stop record. Preserve the retained S0 behavior.
The bounded implementation surface is:

1. source/runtime-ABI-keyed C++ host and loader with no Python environment
   fallback;
2. balanced three-panel TEST population and all six frozen arm primitives;
3. frozen counter addresses/sharing, paired initialization, deterministic
   reduction, scorer/baseline, FP32 update, support counters, and stable
   sequential/parallel behavior;
4. atomic work-unit frontier, cold resume without a repeated optimizer step,
   and a strict nonpromotable 90-slot TEST schema; and
5. source-bound result-blind S0/S1 focused checks plus current-byte benchmark,
   resource projection, and result firewall.

The task is verification-and-repair of existing bytes, not a fresh architecture.
A no-source-change CM return is allowed only if every acceptance criterion below
is established directly. Any repair must fix the source defect rather than
weaken a gate, suppress a failure, relabel an observable, or special-case a
fixture.

### Exact assignment paths

These are the complete writable source/test allowlist. No new S2, production,
evaluation, diagnostic, output, or result file is permitted.

| Current path | Current SHA-256 |
| --- | --- |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/__init__.py` | `c0318c8e2c7b5372262676bbbc24c6b1db304766c6304183f7164c042f86d944` |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/contract.py` | `914a2915df1f576a0b280f6de4857316a85cedaec432490eb8de8d3f688c3b59` |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/native/ucope_r01_r03_backend.cpp` | `9c11b1d4c4dfca800c0f89069f2a24e9b7330e3bcd36c6bf34fda22e1d4d998d` |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/native_backend.py` | `faacfa54c91694c3781bb4914f3e97be9bc9d46171f90dcf294b69ac934474ee` |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/reference_oracle.py` | `78afcaae465c93c95ad3def1eee8b1350284e70c9b98db167069a3668566e810` |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/model.py` | `f5c2c969f63ca88d5117fb2f512c9bd103bf274e00a429c0d1acd472deb6d13e` |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/training.py` | `88c41bdd21ca221f198ebd5fe74c9384b23620c363e363764a4f0bf6713c82ab` |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/checkpoint.py` | `41830a868e3bd9bf85c4efbd869d14d0e905f68efed5de62ce6d9bc98859eb2a` |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/s0_coupon.py` | `b3c1c7fc148a5966d903913f24bb048f8064a94600e9b303ef0fb69d1adcb758` |
| `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/benchmark.py` | `ad9f929a7efbfdd981309bcb27bfe2a1aaa6d469aa2ee02b9ac6465b94bbc88f` |
| `envs/native/production_backend.py` | `38b068d4b8e6897706593b762925a9e8f46e85a3c6fa8ec45b5ce67f88cd3e82` |
| `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py` | `8ca94077ef2d928473853206bd9bd1ade4d40a1c34bb2bf1010682c683e61839` |
| `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py` | `a25783cd2af2aa9ba916a61930b1ae130ad507ddce06f6a271599b15d8837f24` |

CM must treat the authority/evidence records above as read-only inputs. CM owns
only its direction engineering state and assignment worktree in addition to the
allowlist; this request grants no EM, Portfolio, registry, runtime, or Git write.

### Required current-byte repairs or dispositions

CM must address each observed item explicitly:

1. restore one coherent S0 benchmark return path, remove the unreachable stale
   duplicate body, and preserve the retained S0 contract;
2. make the exact `benchmark.main --stage s1` dispatch and returned schema a
   focused observable contract;
3. ensure any gate named as all-six-arm coverage actually exercises the three
   learned arms and three nonlearned comparators on TEST fixtures, or split and
   rename gates so no boolean overstates observed coverage;
4. bind the 90-slot TEST schema to the tracked “90 final-checkpoint schema”
   boundary without registered execution or package promotion; if this cannot
   be done without choosing new science, stop and return the ambiguity;
5. derive forecast and activity/firewall acceptance from inspectable evidence
   and CM accounting rather than unconditional `true` literals;
6. apply the same lowercase-hex digest validation to the reduction frontier as
   to adjacent source/native/counter digests;
7. make malformed native reset failure-atomic and cover cleanup/no-partial-state
   behavior; and
8. make S1 TEST versus retained S0 scalar-oracle namespace use explicit and
   nonregistered rather than relying on an unexplained cross-namespace call.

The apparent 16-versus-24 worker boundary is not permission to enlarge TEST:
actual result-blind S1 TEST remains capped at 16 cores. The separate conservative
complete-transaction projection may model at most 24 cores, but it authorizes no
such run and must not be serialized as an executed TEST worker count.

### Preserved invariants

All repairs and evidence must preserve:

- exact R03 identity, `H=12`, one root decision, the three panel laws, six-mark
  protected count, fixed `K_train={1,3,5,7,9}` and held-out
  `K_test={2,4,6,8}`, the six arms, and the sole unshaped return;
- exact feature coordinate order, `13→64→64→1` scorer, `9→32→1` baseline,
  unit-temperature action law and tie order, one joint AdamW step, entropy
  schedule, and ordinary FP32 parameters, activations, rewards, returns,
  gradients, optimizer state, serialization, and reductions;
- the six `REGIME`, `PROBE_ACTUAL`, `PROBE_DISPLAY`, `TAIL_Z`, `ACTION`, and
  `INIT` namespaces and their exact address/sharing law: environment and paired
  initialization sharing as frozen, arm-private `ACTION`, stable batch/slot and
  reduction order, no second shuffle, and no cross-arm parameter/state/reward;
- exact support-counter semantics, atomic frontier replacement, cold-resume
  equality, no repeated committed optimizer step, and a nonpromotable TEST
  manifest; and
- the activity firewall: no registered master seed, production namespace,
  registered panel, scientific value, result/partial output, complete R03
  package, outcome classification, extra episode, extra seed, checkpoint
  selection, restart, tuning, or S2 surface.

A scientific, numerical, RNG, checkpoint, activity-boundary, comparator,
threshold, claim, or Pro-closure change is a stop, not an implementation choice.

### Observable acceptance criteria

CM technical acceptance requires all of the following on the final current
bytes:

1. **Bound source.** The return records base and candidate hashes for every
   touched allowlisted path and reports no out-of-scope source change. The C++
   artifact identity is source/compiler/runtime-ABI keyed, and the shared
   production registry still requires the C++ backend with no Python fallback.
2. **Retained S0 contract.** The exact focused S0 contract still observes
   registered-seed and backend refusal, all six counter namespaces, three-panel
   native/scalar lifecycle equality, malformed/duplicate/mixed-panel refusal,
   sequential/parallel byte equality, FP32 update, atomic cold resume, and no
   wider/proof-grade hot path. The S0 benchmark CLI returns its declared record
   rather than `None` or unreachable code.
3. **S1 semantic contract.** The exact focused S1 contract observes S1
   namespace/request/result refusal; balanced population/oracle behavior for all
   panels; all six arms; masked immediate/probe lifecycle; monotone support
   counters; partition/order-independent fixed FP32 reduction; exact FP32
   update/entropy/optimizer-step behavior; atomic frontier and cold-resume
   equality; strict 90-slot schema; result-firewall immutability; and absence of
   S2 or wider-precision surfaces.
4. **Failure atomicity and validation.** Invalid native reset leaves no live or
   partially installed lanes, and every persisted SHA-256 field rejects
   malformed/non-lowercase-hex input. The S0-oracle/S1-namespace relationship is
   explicit and covered.
5. **Engineering-only benchmark.** The source-bound `--stage s1` path produces
   one fixture-only `UCOPE_R01_R03_S1_RESULT_BLIND_BENCHMARK_V1` record whose
   source hashes match the candidate; no registered seed or numeric scientific
   value is exposed. Each coverage, determinism, resume, firewall, performance,
   and resource gate is derived from named evidence. Declarative cost and
   activity attestations are separately CM-authored and are not smuggled into
   `all_s1_gates_pass` as unconditional literals.
6. **Current-byte S1 gates.** CM accepts native fixture-oracle equality for all
   host components and panel/channel interventions; exact RNG address/sharing
   and arm-private `ACTION`; paired initialization; deterministic reduction;
   sequential/parallel and crash/resume equality; ordinary FP32 plus
   serialization metadata and a narrow result-blind sensitivity check; complete
   frontier/schema/firewall behavior; and current-byte performance/resource
   gates.
7. **Scope interpretation.** CM records exactly how the fixture-only 90-slot
   evidence satisfies the S1 schema boundary. If the tracked evidence cannot
   decide this without registered activity or new scientific semantics, CM
   returns a `SCIENCE_BINDING_AMBIGUITY` stop instead of implementing a choice.
8. **Cost and stop accounting.** Actual S1 engineering and cumulative TEST
   charges are reported against the non-replenishable caps below, with the
   remaining total forecast. Any failed gate, cap overrun, semantic change, RNG
   or resume defect, Python fallback, FP64/proof-grade path, or activity leak
   yields an exact stop record and does not release S2.

The only authorized behavioral evidence surfaces are the two focused test files
listed above and the result-blind benchmark module at
`experiments.candidates.ucope.variable_k_paid_probe_r01_r03.benchmark` with
`--stage s0` or `--stage s1`, a Root-assigned canonical TEST work root, and a
Root-assigned canonical engineering-evidence JSON path. This request does not
execute them. Project-wide validation and every scientific/result command are
outside scope.

### Resource boundary

The envelope is finite and non-replenishable:

- S1 engineering: 6 managed / 7 hard engineer-days;
- cumulative result-blind TEST through S1, including S0 charges: 3 managed / 6
  hard CPU-hours;
- largest S1 TEST command: 25 managed / 45 hard minutes;
- result-blind TEST: CPU only, GPU forbidden, at most 16 cores, 8 GiB peak RSS,
  2 GiB scratch, 0.75 GiB durable evidence, and 8 GiB aggregate read+write I/O;
- total S0+S1+S2 construction: 15 managed / 18 hard engineer-days, with S0
  already charged and no transfer or replenishment; and
- current-byte conservative complete-transaction **projection** gate: at most
  1,800 seconds, 24 CPU cores, 12 CPU-hours, 10 GiB peak RSS, and 6 GiB
  aggregate I/O, with cold compile/load at most six minutes.

The projection gate is not run authority and does not enlarge S1 TEST limits.
If the accepted current bytes cannot remain within every S1 and total cap, CM
stops before S2. The historical selection calls for the same-direction UCOPE CM
and one coherent Sol-high Implementer scope from S0 through S2; Root must
reconcile the live identity rather than revive or infer a missing historical
runtime reference. No Reviewer is authorized before a coherent S2 candidate.

### Required CM return

Return one exact CM envelope through Root, bound to this artifact and the final
source hashes, with:

- disposition `S1_TECHNICALLY_ACCEPTED` or one exact stop classification;
- changed paths and base/candidate hashes;
- focused S0/S1 behavioral evidence refs and engineering-only benchmark ref;
- a gate-by-gate statement for every observable criterion above;
- actual engineering days, cumulative TEST CPU-hours, largest TEST wall,
  cores, peak RSS, scratch, durable bytes, and aggregate I/O;
- the conservative complete-transaction projection and its method, with no
  unmeasured speedup silently applied;
- the 90-slot interpretation or exact ambiguity stop; and
- explicit confirmation that no registered seed, question-relevant output,
  result/partial value, complete package, S2 surface, provider turn, or
  scientific-semantic change occurred.

CM acceptance is engineering evidence only. It returns to Root and EM for a
later Portfolio decision; it does not itself release S2 or any empirical action.

### Explicit non-scope

This request does not authorize:

- the S2 finite evaluator, BELIEF-DP/IMMEDIATE-DP/FORCED-PROBE-BLIND-DP or
  RAW-PERMAVG complete diagnostic package, attribution map, complete output,
  Reviewer, or SANCheck;
- registered master seeds, the complete registered training/evaluation panel,
  a scientific identity/coordinate/lease, an Experiment Operator, a result or
  partial-value command, output inspection, efficacy interpretation, rerun,
  tuning, added seed, or checkpoint change;
- any R04 relabeling, direction-science revision, claim/alternative expansion,
  external provider send, external-index mutation, engineering-state mutation
  by EM, Portfolio/registry/runtime mutation, Git integration, commit, push,
  deployment, publication, UAV transfer, or flight action; or
- a dynamic service/roster successor. Such a successor remains a new object
  requiring a separate Portfolio decision, complete science authority, and Pro
  closure.

## Next action

Root may dispatch one same-direction CM against the engineering-request section
and exact current-byte allowlist above. The CM must verify and repair S1 only,
return its own technical evidence, and stop without S2 release. This EM performs
no dispatch, source mutation, command execution, external review, or Git action.
