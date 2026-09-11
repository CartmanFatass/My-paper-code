Claim: one bounded first-exception capture can distinguish malformed from apparently ordinary address/dataclass state at the observed failure boundary, without identifying its causal writer.
Binding structure: `systems / information flow` — role/sender/receiver coordinates address exogenous random fields used by partially observed agents, so corruption of this path threatens the paired learner comparison.

# FRRIE R09 first-exception A05 card — 2026-09-07

Object: `FRRIE-R09-FIRST-EXCEPTION-A05-P27-20260907`.
Class: **A/RECON**. Status: `ATTEMPT_ENDED / A05_INCONCLUSIVE`.
Allocation: the sole P27 diagnostic chain ran for42.71s and is terminal. Remaining
P27 allowance is zero; section8 links the frozen-rule intake. A has no consumption state.

## 1. Question, authority and amendment

Authority: [P27](../../portfolio/handoffs/2026-09-07-p27-frrie-first-exception-capture.md)
at `a10e37e5161ae444f24db08844c621738ddbad7d`, following the
[P23 assessment and DM intake](FRRIE_R09_TRAINING_INPUT_P23_ASSESSMENT_20260907.md)
at `4f49b033b864cc6e4fbd5a0071f6efb7a26cbc44`.

Question: if the first uncaught exception on the original schedule again occurs
in `SemanticRNGAddress.canonical_bytes → asdict → dataclasses.fields`, what actual
address, field container, generator iterator and update/counter state is present?
The [P22 intake](FRRIE_R09_OFFLINE_P22_INTAKE_20260907.md) retains the original
`TypeError: 'Field' object is not iterable`, empty learner output, and unknown
failed update. Its fixed-depth debugger commands did not capture the relevant state.
The static P23 read found no justified source correction.

DM explicitly selects a **separate diagnostic observation input and 120 s complete
cap**. The historical 528-byte R09 pdb input is preserved byte-for-byte; it is not
edited or silently replaced on the R09 card. Original scientific source remains
`43eec21e9584c83e5e8d940402d7e4570b454e59`. The new code/input is post-mortem
observation only and receives its own committed binding before launch.

Use the original 128-update schedule until first uncaught exception, normal
termination or cap. A first-input/zero-Adam cutoff was rejected because P22 may
have failed after a later update; completing that prefix would not clear the
dependent training path. A blind full B would again omit the missing state.
No broad causal panel or complete historical explanation is required.

Non-goals: source repair, bypassing `asdict`, changed RNG/serialization, another
learner comparison, a new seed, altered trainer or numerical profile, package
acquisition, a first-input cutoff, local fallback, retries, extension or automatic
R09 clearance. The A05 ceiling is this observed state/path on the pinned runtime.

## 2. Measurement and allowed observation

Capture once at the first uncaught exception, before any continuation/step of the
failed program. Preserve the full original exception/traceback separately from
capture errors and debugger/supervisor exit. Select traceback frames by source
module/function identity, not a fixed count of `up` commands.

The bounded primary record contains:

- Exception type/message and traceback frame identity/function/line, at most32
  frames, with an explicit truncation flag if that bound is reached.
- Actual address type/identity and its 14 named scalar/nullable coordinates:
  `seed_block,purpose,roster,update,episode,basin,event_ordinal,slot,public_role,
  role_local_index,sender,receiver,kind,draw`.
- Instance/class field-table identities and exact types; only for an ordinary
  dict, at most the 14 expected keys and each value's type/name/field-kind identity.
  Unexpected types are described by type/identity rather than custom iteration.
- The `fields()` frame's local `fields` type/identity and the generator's `.0`
  type/identity, plus `f` if present. An absent local is explicit, not fabricated.
- Existing `execute` locals `number,update,paired_updates` and per-arm Adam,
  backward and training-slot counters. Unknown or malformed values remain labelled.

Do not advance any existing iterator, call `asdict` or RNG again, mutate original
frame locals, invoke custom representations/iteration or traverse unbounded
graphs. Any helper executes in its own namespace and loads no scientific package.
Expected ordinary structure comes from the retained 14-field address declaration
and system `dataclasses.py`; frozen instances do not prove memory is unmodified.
Primitive text rendering is bounded to256 characters per value, with truncation
marked; unexpected objects are never rendered through custom `repr` or `str`.
Bounds on frame/field/primitive rendering protect this specific observation, not
a generic validator. Required missing components and structural mismatches must
be distinguished in the record.

Publish one small diagnostic `summary.json` under the fresh diagnostic output,
and preserve the supervisor log and any original learner outputs. After capture,
quit with the specified q/EOF behavior. Acceptance must establish that there is
no second traversal of the scientific module body, no continuation of the failed
program and at most one capture. Report any standard pdb restart notice/entry
prompt separately from actual program execution; do not infer a second run from
text alone or conceal a real second traversal.

## 3. Reading rule, MEI and prediction

Target exception means the original `TypeError: 'Field' object is not iterable`
at the retained `dataclasses.fields`/generator boundary reached through the address
serialization path. A capture is complete when each requested component is read
or explicitly identifies a structural mismatch; missing frames or failed reads
are not ordinary state. Compare only the source-defined ordinary structure;
source identity never implies output or memory bit equality.

Apply the first matching row:

| Branch | Rule and bounded reading |
| --- | --- |
| `A05_NONCONFORMING` | Original source/runtime/RNG/schedule or approved diagnostic bytes differ, observation mutates/advances scientific state, a second scientific traversal occurs, or the complete cap/allocation is breached. Preserve independent facts; no conforming diagnostic result or algorithm polarity. |
| `A05_TARGET_MALFORMED_STATE` | First original exception is the target, the bounded capture is complete, termination conforms, and at least one source-defined ordinary structure check is false. Localize the observed malformed state; do not identify its writer or a Python/native/host cause. |
| `A05_TARGET_ORDINARY_STATE` | First original exception is the target, the bounded capture is complete, termination conforms, and the inspected structures match the ordinary source-defined shapes/types/identities. This limits a persistent malformed-table explanation at observation time; transient/frame/native/runtime explanations survive. |
| `A05_NORMAL_COMPLETION` | The original program completes normally within the cap with its outputs retained and no uncaught exception. Report bounded nonreproduction and preserve all output for separate validity review; this diagnostic is not a replacement shorter R09 comparison or reliability proof. |
| `A05_INCONCLUSIVE` | Failed admission, different first exception, missing state/publication, timeout or hard failure prevents the preceding readings. Record the exact boundary and every trustworthy partial fact; stop without retry, clearance or scientific polarity. |

Timeout/hard failure during capture is inconclusive even if some fields survived;
their narrower observations remain reportable. Missing optional resource telemetry
does not by itself invalidate a trustworthy state capture. A has no consumption state.

The categorical **minimum effect of interest** is one complete target-state capture
that distinguishes the two declared structural readings, because that can change
the next repair/measurement choice. It is not a return threshold. Above that
threshold, recommend a targeted state-dependent next decision; incomplete or
nonreproduced capture leaves the dependency unresolved; an ordinary-state result
contradicts the persistent-malformed-state prediction without proving another cause.
These narratives do not replace the table. R09's MEI0.005 and absent tuned
same-information host headroom remain unchanged; this does not measure headroom.

DM prediction: **`A05_TARGET_MALFORMED_STATE`, low confidence**. P22 supplies a
specific runtime type failure; P23 cannot locate a source writer, and recurrence
or persistent visible corruption is uncertain. A conforming ordinary-state,
different-error or normal/nonreproduction outcome contradicts the prediction;
failed admission, nonconformance or failed state collection leaves it unscored.
Owner prediction: **not taken (unattended)** unless a reply is available at intake.

## 4. Runtime, work and complete budget

Pin to P22's `hmasd-wsl-node` / `LAPTOP-U9TDKC8A`, Ubuntu24.04/WSL2, and existing
`/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python`:
system CPython3.12.3/GCC13.3.0, NumPy1.26.3/Torch2.7.0+cu118 and all 23 retained
pins in P22 E0. No new setup/install/acquisition or import certificate. Reuse
remote-first control/transport; this diagnostic is host/runtime pinned, with no fallback.

Stage fresh detached scientific cwd
`/home/wu/hmasd-worktrees/frrie-a05-first-exception-p27-43eec21e` at original43ee.
Handle: `frrie-a05-first-exception-p27-43eec21e`.
Output within it: `temp/directions/finite_resource_relational_inductive_efficiency/exp/a05_first_exception_p27`;
original R09 output goes to its `learner/`, diagnostic primary to `summary.json`.
The original native build/load route runs once in this new tree; preserve P22's
binary and outputs. New committed helper/input are staged separately as exact
diagnostic bytes, without replacing original scientific files or importing the
current authoring branch's scientific package.

Root performs original-source `admit-memory` on this actual node immediately
adjacent to the original module entry, joined by `&&`: physical and effective
available memory must each be at least4GiB. Its receipt is fresh for this run.
The sole chain includes admission/startup/imports/native build/initialization/
evaluation/training/capture/publication/termination under **TERM115s + at most5s
grace =120s complete maximum**. No setup allowance or cap reset. Retain wall/peak
RSS; aggregate CPU/scratch are unmeasured unless existing receipts supply them.

Original science remains root3/label `FRRIE-B09-CONTACT-BLOCK-003`, LR0.003,
beta boxes, CPU FP32/original FP64 reductions, Torch1/four-worker/native32,
128 paired updates, original checkpoint/uniform/roster schedule. Link the
[R09 card work/runtime sections](FRRIE_R09_THIRD_ROOT_SCIENCE_CARD_20260905.md)
and P23 cost table; do not shorten phases to manufacture zero learning exposure.

Dominant maximum work: one chain, two arms, one root, `2×128×64=16,384` factual
episodes, 256 Adam/backward calls, 196,608 learner transitions; 1,261,568 training
native slots plus 18 cells/4,608 evaluation episodes/55,296 evaluation slots,
total1,316,864 slots. Input maxima are8,192 training and512 evaluation tapes.
Per-arm nominal LR exposure≤0.384, relative to initialization half-range≤7.68;
neither is a displacement bound. Actual work is whatever the original chain
reaches before its first terminal boundary, not these maxima or assumed zero.
At most one bounded traceback/14-field capture adds observation work.

P22's61.54s is the known complete-chain anchor;120s is an observation ceiling,
not a prediction of recurrence or full-schedule completion. No cost pilot.
Actual algorithm work and the added capture share that one ceiling. Separate
acceptance uses only non-executing syntax checks and, where needed, one small
inert debugger fixture; it supplies no scientific/runtime-reliability evidence.

## 5. Complete bounded CM assignment

1. **Deliverable:** implement one readable post-mortem capture recipe, the exact
   new pdb input and a Root handoff with committed bytes/digests, one literal
   command and all paths from §4. Prepare and check first; CM does not dispatch
   the scientific chain. Root handles admission/dispatch/observation; CM collects
   its terminal E0 and DM intakes the registered reading.
2. **Owned code/data/tests:**
   `experiments/candidates/finite_resource_relational_inductive_efficiency/r09_first_exception_a05/capture.py`;
   `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_FIRST_EXCEPTION_A05_PDB_COMMANDS_20260907.txt`;
   `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/r09_first_exception_a05/test_capture.py`;
   and `FRRIE_R09_FIRST_EXCEPTION_A05_ROOT_HANDOFF_20260907.md` in this direction.
   A helper must load by its standalone staged file into its own namespace,
   without importing the scientific package. No new runner/framework or edits
   to original43ee source, historical input, P22 evidence or shared control plane.
   Reuse `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, `codex/frrie`;
   serialize overlapping edits and preserve other writers' work.
3. **Preserved semantics:** §§1–4 and P23 Exact missing state control. Read actual
   system pdb behavior only as needed to implement frame selection and q/EOF.
   No scientific import/build/tape/model/learner execution during preparation.
   Capture errors must not replace the original exception or trigger a retry.
4. **Original acceptance checks:** parse/compile the helper and embedded command
   without executing science; syntax-check the final Bash command. One inert
   stdlib fixture at the actual system312 interpreter is justified to verify
   (a) a target-like exception at differing stack depth, bounded unexpected
   container handling without advancing/custom rendering, frame/counter mapping
   and one capture; (b) normal completion and q/EOF without a second module-body
   traversal. Use direct
   `/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python tests/experiments/candidates/finite_resource_relational_inductive_efficiency/r09_first_exception_a05/test_capture.py`
   with no package dependency or scientific conftest. At most two inert program
   subprocesses, ≤10s each, ≤25s complete fixture; no extra smoke or scientific
   invocation. The exact fixture command uses the pinned existing interpreter
   and committed source; publish command/readback and preservation checks for
   historical input and original scientific paths. DM accepts the output/stop
   boundaries and freezes exact diagnostic bindings before Root dispatch.
5. **Budget/stop:** scope-spec §5 limits remain; the new code is this one bounded
   capture, not a registry/validator/retry service. The sole named §4 need is
   **reuse of the existing optional pdb exception-state observation** for one
   bounded frame/address/field/counter record; no other §4 facility. Inert checks
   have the separate finite validation bound above and zero scientific exposure.
   After acceptance, P27 supplies one scientific diagnostic chain of at most120s;
   stop at its first terminal boundary. Preserve every result and return any
   future correction/observation need through Root to Portfolio.

The temporary five-arm CM comparison's three batches are complete in main's
`CM_MODEL_COMPARISON_20260907.md`; its enrollment has ended. This is new diagnostic
coding, not falsely labelled collection. Send this identical complete card/task,
committed starting source and checks to Root before the reused CM starts; record
the completed-three-batch exclusion, without a historical replay or new batch.

## 6. Decision and recoverability

Object-tier options: (a) the explicit one-shot diagnostic input/cap amendment;
(b) first-input-only cut; (c) blind full R09 retry or unsupported source rewrite.
Recommend/select **(a)** under P27. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a).** This is an A/RECON diagnostic, not a new family,
direction disposition or changed R09 result. P22 remains incomplete with unknown
counters; original R09 prediction and R06–R08 science are unchanged.

Publish the P2 new-card item and read asynchronous owner instructions at each
clean boundary; no owner response is required to continue the authorized work.
Item: [20260907-frrie-002](../../portfolio/owner/inbox/2026-09-07/20260907-frrie-002.json).
Reviews were empty at the preparation boundary; no owner reply was inferred.
Section7 completes the exact helper/input/command binding and focused acceptance.
Section8 links the sole launch/terminal evidence and intake. The initial74a547f4
freeze fixed the question and budget with bytes pending.

Root appends the supplied preparation decision row at integration; DM edits no
shared audit. DIRECTION changes only if later accepted mechanism-level science
warrants it. All authoring remains in the existing direction checkout/branch.

Append-ready audit row (actual invocation count remains zero at this freeze):

```text
| 2026-09-07T22:35:57-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) separate A05 first-exception input/cap; (b) first-input cut; (c) blind R09 retry/asdict rewrite | (a):P27 diagnostic question frozen with exact bytes pending;one prospective120s original-schedule chain after acceptance,zero actual invocations | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P27 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_FIRST_EXCEPTION_A05_SCIENCE_CARD_20260907.md | none | |
```

## 7. DM acceptance and exact execution binding — 2026-09-07 23:17 PDT

Accept the [CM Root handoff](FRRIE_R09_FIRST_EXCEPTION_A05_ROOT_HANDOFF_20260907.md)
at **`137ed1fda47662f4eb51fa9d70f41a6a3675d2a2`**. Its sole sh fence, staging paths
and runtime in §§1–2 are the exact dispatch handoff. The scientific/preflight tree
is still **`43eec21e9584c83e5e8d940402d7e4570b454e59`**. The separately staged
diagnostic helper/input use **`30643b7359b35c6e9d5751147d0999bc629a966d`**:

| Bound quantity | Bytes | SHA256 |
| --- | ---: | --- |
| Standalone `r09_first_exception_a05/capture.py` | 11464 | `0e75801266db0dc339da63ddd1a1f5a981b5b26bfc4ae243e87f8feb678f87b8` |
| New A05 pdb stdin | 173 | `361c1df2f98b3291416cb1b7f20195440dd1f01a535586123f8889aab4a643f0` |
| Handoff's sole command, extracted exactly as its §2 defines | 1187 | `2976134a5690041fea083bef024aff1e28c92225c4d42479ccca38599893976d` |

The two-line input is used with **`-m pdb -c continue -m
scripts.run_frrie_b01_contact_r09`**. The initial continue enters the original
program once; the subsequent input performs the bounded read, then q/EOF.
Normal-entry `no_active_exception_at_entry_prompt` is a separate record from a
post-mortem capture. Neither an entry prompt nor debugger exit0 establishes
scientific completion; actual termination still receives card §3 intake.

DM checked the complete helper/input and the narrow final missing-attribute fix,
the retained original address declaration and execute counter names, the literal
against the original entry/admission/runtime profile, and the CM's syntax and
remote source-readback receipts. The helper selects module/function/file identities,
uses its own namespace, and does not call the original computation or advance its
iterator. The final two-line helper repair labels an absent field-table attribute
explicitly, without assigning the helper's sentinel a purported live identity.
All ordinary/target paths and the pdb input remain byte-identical to66106b3.

DM read the raw inert target/normal stdout, original target stderr, one-line body
markers, summaries and receipt. Both cases traversed their inert module body once
and published one summary. The target-like11-frame record contains all14 coordinates,
the declared counters and no missing component/capture error; its shape checks are
all true. The normal record has no active exception. The standard pdb restart
notice is retained separately from these one-body marker observations.

The original two-child fixture at66106b3 took0.073838544s. The isolated absent-
attribute assertion at final30643b7 took0.019970510s and launched no further pdb
child. Computed combined inert time is **0.093809054s**, within25s. The existing
two-child evidence was reused after inspecting that exact narrow diff; neither CM
nor DM repeated it. These are preparation facts, with **zero actual scientific
invocations**. They do not demonstrate recurrence, full learner readiness or
P22 cause. Parent byte/arithmetic/receipt readback is retained in
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a05_preparation_p27/dm_acceptance_readback.json`.

Object-tier options: (a) accept these bound bytes and release the sole P27
diagnostic to Root; (b) return an unresolved implementation/acceptance gap.
Recommend/select **(a)**: the identified missing-attribute gap is repaired and
focused acceptance is complete. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a).** Main owner reviews were empty at this clean
boundary. The original §3 reading rule, prediction, scope, work and120s cap are
unchanged. No repeat acceptance check or additional scientific allocation follows.

Root now stages the exact diagnostic bytes outside a fresh original43ee detached
tree and uses the one literal with handle `frrie-a05-first-exception-p27-43eec21e`.
The original4GiB admission is fresh and adjacent within that same TERM115+5 chain.
Root observes the accepted handle; the same CM collects its terminal E0, and DM
applies §3. Any subsequent task returns through Root to Portfolio after intake.

Append-ready technical acceptance row for Root integration:

```text
| 2026-09-07T23:17:01-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) accept bound A05 capture; (b) return unresolved code/check gap | (a):30643b7 helper/input and137ed1f handoff accepted;2 inert pdb children plus focused repair check,0.093809054s;zero actual scientific invocations,one120s P27 dispatch ready | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P27 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_FIRST_EXCEPTION_A05_SCIENCE_CARD_20260907.md#7-dm-acceptance-and-exact-execution-binding--2026-09-07-2317-pdt | none | |
```

## 8. Sole P27 terminal result and intake

Root dispatched handle `frrie-a05-first-exception-p27-43eec21e` once on the pinned
node/source at2026-09-08T06:24:06Z. It ended at06:24:48Z: the shell reports a
segmentation fault for Python PID2765962, supervisor exit139; GNU-time wall42.71s,
peak RSS873284KiB. Fresh admission passed and the accepted command/input bindings
match. No Python traceback, target exception, capture summary or learner file was
retained; the `learner/` directory is empty. Actual learning counts remain unknown.

CM's [E0](FRRIE_R09_FIRST_EXCEPTION_A05_RESULT_EVIDENCE_20260907.md), committed
through `25c04d9a08b23f067f2edf11100204c26347774f`, preserves the artifacts and
limits. DM's [intake](FRRIE_R09_FIRST_EXCEPTION_A05_SCIENTIFIC_INTAKE_20260907.md)
applies the unchanged §3 rule as **`A05_INCONCLUSIVE`**. The categorical target-state
MEI was not met; the low-confidence prediction is unscored because collection
failed, and the owner prediction was not taken. This is not a malformed/ordinary
state verdict, a causal diagnosis or an R09 learning result. P22 and the original
R09 card remain unchanged. The one P27 allowance is finished, with no retry or
continuation released; the separate next-task recommendation returns through Root
to Portfolio. The
[Chinese owner brief](../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-07_A05-first-exception.md)
accompanies the intake.

scope: reuse existing optional pdb exception-state observation for the bounded record in section2
