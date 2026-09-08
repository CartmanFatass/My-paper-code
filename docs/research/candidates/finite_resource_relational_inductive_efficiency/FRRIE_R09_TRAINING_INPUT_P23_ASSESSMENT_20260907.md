# FRRIE R09 training-input P23 assessment — 2026-09-07

**No source correction is justified by the retained evidence.** The missing fact is the live address/field-container/generator state at the first exception, together with the failed update. The recommended next observation is one separately allocated first-exception capture on the unchanged original schedule, bounded to120s for the complete chain. P23 authorizes neither that observation nor a source repair.

Contract: [P23 handoff](../../portfolio/handoffs/2026-09-07-p23-frrie-training-input-assessment.md), main `309f4ab1787aab40c839a44f48263042d8c49a84`; [P22 E0](FRRIE_R09_OFFLINE_P22_RESULT_EVIDENCE_20260907.md) at `dd6fd9bdac3d806842a0622372e87befb7096212`; [DM intake §§3–4](FRRIE_R09_OFFLINE_P22_INTAKE_20260907.md) at `ff33e4e7334b4532ccb720c21ff586d86b7f0661`. Evidence-spec §§4,11.8.5–11.8.7 apply. All source references below bind original `43eec21e9584c83e5e8d940402d7e4570b454e59`, not a substitute trainer.

## What the source establishes

Paths below are relative to `experiments/candidates/finite_resource_relational_inductive_efficiency/` unless stated otherwise.

| Retained surface | Direct static fact and limit |
| --- | --- |
| `b01_contact_r02/experiment.py:153–242` | Production setup builds evaluation tapes and native adapter, completes uniform and checkpoint0 evaluation, then calls `production_training_inputs(root, seed_label, number)`. `number = update + 1` at241; the first call is update1. Later calls share this site. No retained value identifies which call failed in P22. |
| `b01_contact_r02/tapes.py:225–254` | Each call creates an `AddressedRNG`, both origin schedules and coordinate mapping, then constructs64 episode tapes in `(9,15)*32` order. The failure was inside that tuple's generator, before this call returned. No native adapter is passed into tape construction. |
| `tapes.py:69–102,311–375` | `_semantic_address` explicitly supplies all14 coordinates to a fresh `SemanticRNGAddress(...).validate()`. The failing call constructs the uplink address from validated loop coordinates, including receiver, and passes it to `uniform_float32`. No address field-table assignment appears in this path. |
| `rng.py:109–205,232–274` | `SemanticRNGAddress` is `@dataclass(frozen=True, slots=True)` with14 declared scalar/nullable coordinates. Validation reads fields and enforces coordinate domains. `canonical_bytes` validates then passes `asdict(self)` to canonical JSON; `block` prefixes the frozen schema/root and appends block index before SHA256. These operations are RNG meaning, not replaceable diagnostic formatting. |
| `rng.py:208–212,237–243` | Mapping conversion reads the class field table and constructs another validated instance; the observed constructor path already supplies a `SemanticRNGAddress`, not a mapping. Reads of `__dataclass_fields__` are not writes. |
| Retained system `dataclasses.py:1271–1286,1319–1334` | `fields` retrieves `class_or_instance.__dataclass_fields__`, then filters `fields.values()` through a generator. `asdict` reaches `_asdict_inner`, which calls `fields(obj)`. Traceback ends in that generator with `TypeError: 'Field' object is not iterable`. The text does not identify the actual field container, iterator or offending object's identity. |
| `native_adapter.py:395–450`; `b01/r128_smoke.py:198–275` | The previously reached environment boundary receives packed ctypes arrays/counts for reset/observe/step. The RNG address/class is not an intentional native argument. Native calls preceding tape construction do not prove or exclude memory corruption; this limited interface read identifies no concrete overwrite. No binary was loaded or ABI experiment performed. |

Scoped mutation search covered the address module, the two tape modules and contact package. Their `object.__setattr__` sites freeze array attributes on tape objects (`tapes.py:178,230`; contact `tapes.py:150`), not the address class or its field table. No inspected assignment to `SemanticRNGAddress.__dataclass_fields__`, serialization monkeypatch or explicit frame-local manipulation explains this exception. Frozen instances do not prove a class table or native memory cannot change. This is not an exhaustive absence proof or a diagnosis of Python/native correctness.

The current six inspected source files match retained P22 bytes and the bound Git blobs (working-tree CRLF normalized only for that comparison). Non-executing AST parsing confirms14 declared address fields. P22's existing62-path byte receipt remains the broader source identity evidence; no new census or collection was performed.

## Exact missing state

The required observation is small: (1) actual exception-frame code identity/line and frame names; (2) the address's actual type and14 scalar coordinates; (3) instance/class `__dataclass_fields__` identity and exact type, and, only if an ordinary dict, its14 keys and each value's type/name/field-kind identity; (4) the `fields()` frame's local `fields` type/identity and generator frame's `.0` type/identity plus `f` if present; (5) `number`, `update`, `paired_updates`, per-arm Adam/backward/training-slot counters from `execute`.

Do not advance the generator, serialize with `asdict`, mutate frame locals, call the RNG again, or inspect unrestricted object graphs to obtain this state. Select existing traceback frames by module/function identity, not by assuming a fixed stack depth. Bound inventory to the expected14 fields and scalar counters; unexpected types are reported as types/identities instead of invoking their custom iteration or representation.

P22's original debugger `up 2` lands in `_asdict_inner`, while the subsequent `up 6` lands in the tape tuple generator. Its `obj/self/number` expressions therefore failed. That explains the missing diagnostic values, not the original TypeError: the traceback predates those commands. Original528-byte stdin, its digest and q/EOF termination remain intact as evidence. Its restart message/module-line1/EOF is not evidence of another scientific traversal.

## One prospective observation, not allocated

**Options and recommendation:** (a) stop after the first training-input return, before any collector/Adam work; (b) retain the original128-update schedule and observe the first exception, normal completion or a fixed120s complete cap. Option(a) bounds optimizer exposure to zero but a successful first input would add only that one-call completion fact; it would not resolve a possibly later training-dependent failure or justify another real-B decision. The existing record already establishes native/checkpoint0 reachability. **Recommend(b)**: do not remove a potentially relevant phase merely to minimize exposure. This follows the DM's P23 decision-value correction and evidence-spec §11.8's dependency standard. Nonreproduction under either option cannot clear P22.

Use original source43ee, CPU/root3/LR0.003/beta boxes/FP32/FP64/Torch1/four-worker/native32 semantics and all128 paired updates/checkpoints/uniform/rosters. Pin the proposal to P22's same `hmasd-wsl-node` host and `/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python`, system CPython3.12.3/GCC13.3.0 with its retained23 installed pins. Reuse this existing environment without package changes; no new setup or package acquisition is needed. Reuse the configured `/usr/local/bin/agent-task` supervisor; stage a fresh detached exact-source cwd, fresh output root and fresh handle. Preserve all P22 artifacts and its source/native binary; the new tree follows the original native build/load route. No alternate trainer, serialization workaround, seed change, phase cutoff or independent import/smoke certificate.

Use the existing pdb facility: on the **first uncaught exception**, capture the bounded state above once and quit, without continuing or stepping the scientific program. Preserve q/EOF termination and retain the complete original exception separately from debugger exit. Admission failure, hard failure, normal completion or timeout also ends the sole attempt. No breakpoint shortens a successfully progressing learner, and no retry, later extension or automatic repaired run follows.

**Explicit meaning boundary:** this requires a newly frozen *diagnostic* pdb command file that selects the relevant exception frames, and the separately allocated120s complete-chain stop. The historical fixed528-byte input is not edited or silently replaced in R09. Keeping that input byte-for-byte as the only commands cannot recover the missing frames. DM must explicitly select this narrow diagnostic-input/cap amendment before Portfolio allocates it. P23 does not authorize it. The diagnostic follows the original scientific schedule until a terminal boundary; it is not a substitute shorter R09 result. On normal completion retain all outputs for DM review, without inferring general reliability or successful cause isolation.

| Complete prospective bound | Value and basis |
| --- | --- |
| Invocations / setup / native builds | At most1 complete detached chain /0 new environment setups or installs /1 original native build in the fresh exact-source tree; no separate probes |
| Complete wall, including setup, evaluation, training, state capture, publication and termination |120s hard envelope: TERM115s plus at most5s grace; first terminal boundary ends earlier |
| Cost evidence | P22's complete chain was61.54s, setup-to-learner admission interval6.712115s.120s is a proposed observation ceiling, not a duration prediction or recurrence guarantee. Failure may be later or intermittent. No new timing pilot. |
| Per-arm / shared allocation | Original per-arm maxima:128 updates,8192 factual episodes,2048 learned evaluation episodes;512 uniform episodes shared. Each arm's attributed wall is bounded by the120s chain, below original14400s/28800s caps. All initialization/build/observation work is charged inside the same120s; no separate allowance or cap reset. |
| Maximum native environment work |1261568 training slots plus55296 evaluation slots =1316864 slots. Full18 cells,4608 evaluation episodes. A partial failed update can add native collection work without completing Adam; actual counters must be observed. |
| Input-generation work |At most8192 training tapes and512 evaluation tapes, reused across arms/checkpoints as originally defined; no second root or input sweep. |
| Maximum learner exposure |128 paired updates,256 backward/Adam calls,16384 factual training episodes/196608 learner transitions. Per-arm nominal LR exposure≤128×0.003=0.384, not a parameter-motion bound. Actual failed update and counts remain unknown until captured; no assumption of zero work. |
| Resources / placement | `hmasd-wsl-node`; one fresh existing source-bound preflight adjacent to program entry, physical/effective availability≥4GiB. P22 admission cannot be reused; no setup admission is needed because no setup is proposed. Retain wall/peak RSS; aggregate CPU and scratch are unknown unless existing receipts provide them. No CPU rate inferred from wall/thread counts. No local fallback is proposed. |

These are the original schedule's maxima under one shorter diagnostic wall envelope, not a forecast that all work fits120s. Summed invocation wall and elapsed critical path are each at most120s for this one chain; aggregate CPU remains unknown. A later executable assignment must freeze exact diagnostic input bytes/digest, argv/cwd/output/handle and syntax-check its frame-selection/termination recipe without scientific execution before its sole allocation. Original model, RNG, numerical schedule, source and program arguments stay unchanged apart from fresh paths; the explicit future amendments are observation input and outer diagnostic time bound.

Discriminating outcomes:

- Same error with malformed address field table or unexpected container/iterator state: locates the corrupted object/state boundary. It does not identify the writer or prove native/runtime causation; return that narrow state, no automatic repair.
- Same error with apparently ordinary captured table/fields: rejects the simple persistent-malformed-table explanation at observation time. Generator/frame/runtime behavior or transient corruption remains unresolved; do not conclude Python is at fault from this alone.
- No corresponding exception before the cap, or normal completion: preserve reached work/all outputs and captured counters where available. Neither clears P22, establishes reliability nor identifies its cause. A complete output receives separate ordinary DM validity review; timeout grants no extension.
- Different exception, timeout, admission failure or missing state: preserve it and stop as inconclusive for the intended discriminator. No retries or alternative probes.

## Acceptance and return

P22 remains `R09_INVALID_INCOMPLETE`; ≥1536 evaluation episodes/18432 slots are conditional source-flow lower bounds, while its actual optimizer/update counters and scores remain unknown. The card's six-branch rule, MEI0.005 and conditional `R09_N15_WITHIN_MEI` prediction remain unchanged and unscored. Historical quarantine and all outcomes remain. No static finding supports bypassing `asdict`, changing address serialization, removing pdb, or substituting the later trainer.

Checks: existing-file reads, six retained/bound source comparisons, non-executing AST parsing and integer exposure arithmetic only. Zero setup, imports of scientific modules, native builds/loads, tape/model/learner calls or result-bearing invocations. This assessment adds no engineering-scope §4 machinery. **CM comparison exclusion:** P23 is read-only failure assessment, no new coding implementation; Root records that concrete exclusion once in its log.

Authoring began clean at `ff33e4e7334b4532ccb720c21ff586d86b7f0661` on shared `codex/frrie`, `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`. Own this document only. DM next decides whether the proposed first-exception capture justifies its explicit diagnostic-input/cap amendment and120s allocation request, or returns a different scientific need. No source correction or observation is ready to execute under P23 itself.

## DM intake — assessment and proposal only

**Accept the bounded static finding and recommend the first-exception proposal for
the next separately scoped assignment.** This is technical preparation at a
source/measurement-path ceiling. It creates no runtime result, diagnostic card
freeze, source correction, amended input or invocation allocation.

DM read the complete CM assessment at
`ff8339f3fcae316f730e43c60584c2a06f4c5be1`, the P23 acceptance, P22's original
traceback/call-order evidence and R09's current card. The retained address declaration,
`canonical_bytes` and system `fields` implementation corroborate the central mapping:
14 declared coordinates, canonical serialization through `asdict(self)`, and a
generator over the retrieved field table. CM's scoped mutation/native-interface
reads and six byte comparisons are reused; DM did not repeat that engineering review.
The actual inspection does not support a serializer rewrite or prove absence of
all source/native defects.

P23's controlling acceptance, verbatim:

> return the smallest justified correction with owned files and preservation/check requirements if static evidence identifies a defect. If it does not, state the actual missing object/field-container/update fact, the smallest targeted prospective observation, its discriminating outcomes, complete cost/exposure bound and stop.

The second clause is satisfied. The assessment identifies the missing address,
instance/class field table, `fields()` local, generator iterator and execute counters;
it gives one capture, its outcomes and a complete bound. It leaves the observation
unallocated. No stronger claim or silent exception to the R09 card is accepted.

The next observation must distinguish a visibly malformed persistent field state
from an apparently ordinary state at the same failure boundary, while recording
where the original schedule had reached. That can change the next repair or
measurement choice. It need not explain every old failure or prove a runtime culprit.
The first-input-only cut was considered and rejected: its successful completion
would not resolve a failure after a later learning update. An unchanged full B could
again lose this state, as P22 did. One bounded first-exception capture addresses the
actual missing fact without using a zero-learner prefix as another B prerequisite.

Its strongest support is the existing first traceback plus the source-confirmed
wrong-frame debugger lookups. Its strongest limitation is that P22's failed update
is unknown: a later/intermittent failure may not recur in 120 s, and normal captured
state does not prove that transient or native corruption is absent. A nonreproduction
must not be converted into learner readiness or trigger automatic extensions.

DM used local AST parsing and integer arithmetic to check the 14 fields and maxima:
`2 arms ×128 updates ×64 factual episodes`, 256 Adam calls, 1,261,568 training-native
slots plus 55,296 evaluation slots, and `115+5=120` complete seconds. The receipt is
`temp/directions/finite_resource_relational_inductive_efficiency/exp/p23_dm_assessment_20260907/intake_checks.json`.
These are proposed upper bounds, not actual or predicted work. One fresh native
build, original initialization/evaluation/training and bounded debugger capture
would all lie inside that ceiling; optional validation adds no separate invocation.
P23 actual setup/scientific-import/native/model/tape/learner/reproduction counts are all zero.
No per-update rate or claim that the full schedule fits the cap is inferred from
P22's 61.54 s. The read-only assessment itself has no new algorithm-effect measurement.

### Decisions this intake produces

Options: (a) accept the scoped no-supported-correction finding and forward the
first-exception proposal for a future diagnostic-input/cap amendment; (b) propose
changing `asdict` despite no identified source defect; (c) make first-input completion
the next prerequisite; (d) retry the unchanged full P22 chain.
Recommend/select **(a), assessment and proposal only**.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This object-tier
choice prepares the next need; it neither freezes a new diagnostic nor releases it.
Owner flag: none. The runner-up's first-input cut cannot answer the later-update
uncertainty, so this is not a close-call disposition.

**Exact next-command need through Root to Portfolio:** prepare one explicit
diagnostic card/input and exact command for the proposed same-host first-exception
capture, then allocate at most one 120 s chain if that next task authorizes execution.
The missing executable input is the bounded, frame-identity-based debugger recipe,
with its exact bytes, fresh paths/handle and q/EOF behavior; the historical 528-byte
file stays unchanged. No source repair is ready or justified. This is a concrete
technical assignment recommendation, not a request for Root to select the science.
If preparation entails new coding, its complete common task/spec/source/checks go
to Root before CM implementation under the applicable comparison instructions.

P22 remains `R09_INVALID_INCOMPLETE`, with conditional evaluation lower bounds and
unknown optimizer counts. R09's native-return prediction remains unscored; owner
prediction not taken. The question still connects partially observed partner
information through beta aggregation, native actions and RSCF/Adam exposure to
return under tight/wide boxes. This assessment measures none of that performance.
R06's conditional N15 support, R07's contrary recurrence evidence, the R08 qualifier,
MEI0.005 and absent tuned same-information headroom remain as recorded in P22.
No stable benefit, cause attribution, transfer, UAV entry, family closure or recast
is inferred, and DIRECTION needs no new mechanism-level conclusion.

At the clean boundary, main's `item.py reviews --json` returned `[]` and relevant
FRRIE ledger owner cells were empty. No reply required application or scoring.
No P1/P2 item is created for this ordinary assessment/proposal: no new card or
direction/Portfolio disposition is frozen. The
[Chinese brief](../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-07_P23-training-input-assessment.md)
states the zero-execution boundary. Engineering-scope §4 additions and new §5
source-budget breaches: none. The existing pdb facility is a proposed reuse; its
new input has not been implemented.

DM appends this intake to the same assessment and adds only that brief in the shared
`codex/frrie` checkout after CM returned ownership. R09 source/card, P22 evidence,
DIRECTION and shared control-plane files remain unchanged. Root integrates the CM
assessment and DM appendix commits if absent, retains P22's supplied audit row,
and appends this new row; it is not claimed already appended here:

```text
| 2026-09-07T22:14:12-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) retain no-supported-fix finding and prepare first-exception proposal; (b) rewrite asdict; (c) require first-input completion; (d) blind P22 retry | (a):explicit future diagnostic-input/cap preparation recommended,one proposed120s unchanged-schedule chain;no source fix,input amendment,card freeze or runtime allocation in P23 | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P23 retained-source assessment | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_TRAINING_INPUT_P23_ASSESSMENT_20260907.md | none | |
```

scope: none
