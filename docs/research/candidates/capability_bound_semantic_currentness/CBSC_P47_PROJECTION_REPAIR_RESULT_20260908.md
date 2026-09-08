# CBSC P47 projection repair technical evidence

**Fatal during TRAIN-tape construction; no production correction supported.** The
minimal-prefix diagnostic failed before initial projection, model or optimizer
initialization. The selected instrumentation comparison remains unanswered; a
new earlier token-packing failure location is directly reportable.
Authority: [P47 card](CBSC_P47_PROJECTION_REPAIR_CARD_20260908.md), question and preserved-semantics sections.

The retained dirty test was preserved without edits in
`temp/directions/capability_bound_semantic_currentness/test/p47_projection_20260908_control/initial_dirty_variant.py`,
SHA256 `c6cbbab72a427d9df06460487cc533f349caf565e66da7937c2bad0912f82cab`.
The selected source is that retained variant: omit public-byte export and the
indexed build_observations wrapper before the original projection; compare the
saved public bytes only after projection returns, then stop by PrefixComplete.
No scope-spec section 4 machinery or production edit is added.

## Source boundary and focused checks

Direct inspection follows opportunity_credit_b04/run.py:106–132 through
omrc_b01/engine.py:82–115, RawHistoryAdapter.process and the actual relative
omrc_b01/token.py codec. The run creates the original 384 training tapes and
32 evaluation tapes, computes input/action digests, initializes model/trainer,
then enters the initial projection. Each tape owns a fresh adapter per replay;
immutable public bytes expand to NumPy FP32 rows, torch.from_numpy retains the
array storage, and torch.stack returns [32,152,168]. RAW FIFO updates use four
Python integers; the codec uses immutable bytes and ordinary NumPy bit expansion.
No concrete buffer lifetime, shape, or codec defect was found in this inspection.
Both production directories have zero diff against historical P32 d2753be86.

The test's exception prevents return to run_arm after initial projection,
before fixed rules, held-out evaluation, rollouts, Adam steps, checkpoints or
scientific publication. Zero scores/learning are source-bound, not inferred
from a successful process exit. Post-projection JSON is the diagnostic's affected
publication path. Wrapper frames, entry argparse, startup output and allocation
history still differ from historical P32; this is not process-state identity.
AST parsing and git diff --check passed before the diagnostic. No learner smoke.

## Frozen diagnostic

Node wsl_4070; original lexical interpreter
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`;
CPU FP32, Torch1 and existing numeric-library limits. One detached agent-task,
outer GNU time and timeout TERM115s/KILL5s, adjacent original memory admission
requiring physical/effective availability >=4 GiB. Fresh exact-source cwd
`/home/wu/hmasd-worktrees/cbsc-p47-minimal-prefix-20260908`;
handle `cbsc-p47-minimal-prefix-20260908`.
Argv after admission: selected Python -X faulthandler
`tests/experiments/candidates/capability_bound_semantic_currentness/omrc_b01/test_initial_projection_prefix.py`
`<cwd>/temp/directions/capability_bound_semantic_currentness/test/p47_minimal_20260908/TEST_ONLY_prefix`
`--minimal-reference /home/wu/hmasd-inputs/cbsc-p47-20260908/TEST_ONLY_initial_public_tokens.bin`.

The retained reference is 82,688 bytes; SHA256
`ee4df377990ed9d40b7bcec0241a92268f1b78037cfbbcee90b57c113eae7ccb`, bound before staging.
It is the prior indexed diagnostic input, not retained P32 state.
Cost: one original 416-tape setup and 32 x 2 x 152 = 9,728 adapter calls;
82,688-byte post-projection comparison. No sweep. Prior complete-path wall7.23s
is context; normal time remains uncertain, complete cap120s. Aggregate CPU is
unmeasured. The single invocation wall equals its invocation-wall sum; complete
engineering/study elapsed critical path, including staging/collection, is unmeasured.
Post-learner publication is outside this zero-learning diagnostic.
Raw launch/status/admission/log/results are collected in the preservation
root above. No historical RAW/STRUCT retry or scientific exposure is allocated.


## Terminal observations and acceptance

Executed source `ae9383512f7754813c4fcde8de86154a5b4daef4`, committed and pushed
before launch. Staging exact source and reference copy/digest all exited0;
configured interactive zsh printed gitstatus startup warnings but the exact-SHA
worktree command completed. The scientific command used the non-login inner shell.
Agent-task accepted one handle, PID2777970. Supervisor start/end were
2026-09-08T16:11:36Z / 16:11:44Z; terminal failed, exit139, tmux inactive.
GNU time: **7.37 seconds**, **615928 KiB peak RSS**, below the complete120s cap.
Invocation-wall sum is7.37s; aggregate CPU and study elapsed are unmeasured.
Adjacent admission captured16:11:36.758134Z, assessed16:11:36.758380Z,
physical/effective available15641853952 bytes, floor4294967296, passed.

The fatal stack (most recent first) reports enum.py1292 `value`, enum.py212
`__get__`, token.py164 generator / `flag_values`, token.py251 `pack`,
host.py522 generator / `_finish`, host.py595 `build_stochastic`, then
run.py122 TRAIN-tape generator / `run_arm`. The full stack, 24-module extension
list, original command and terminal footer remain in the copied supervisor log.
No native writer attribution follows from the extension list or Python frames.

Direct source ordering establishes that TRAIN construction was unfinished:
completed TRAIN-tape count and faulting token/index are unknown. EVAL-tape
construction, model initialization, optimizer initialization, initial projection,
rule/policy score evaluation, rollout/learning, checkpoints and scientific
publication had not been reached (counts zero by this source boundary).
The fresh output directory is empty; its parent contains admission.json only.
No input-equality, shape, work-total or diagnostic JSON assertion ran. Planned
416 tapes /9728 adapter calls are not reported as completed work.

Both terminal roots were copied successfully. Local collection assertions checked
exit139, the measured wall below120, both memory floors, and admission-only output;
`collection_facts.json` retains the extracted facts and count-inference basis.
This is acceptance of the readable failure boundary, not completion of the
projection/input comparison. Independent review is recorded in the
[review counterpart](CBSC_P47_PROJECTION_REPAIR_REVIEW_20260908.md).

## Concrete gap and handoff

The actual public-byte export and indexed logging calls would run only after
all tape construction and model/trainer setup. This failure occurred earlier.
The minimal-reference argument handling and decision not to install the indexed
wrapper already differ before TRAIN construction, so pre-failure interpreter/heap
perturbations remain possible; neither export/logging nor its omission is isolated
as a cause. It also
shows that executing RAW FIFO projection and model/optimizer initialization is
not necessary for this observed fatal event. It does not exclude import-time
native state, interpreter state or other causes, and does not equate FRRIE/CBSC.

Focused expansion into host._finish and its caller found ordinary Python token
construction and codec packing, with address randomness supplied by the existing
hashlib-based PRF. The implicated flag_values operation obtains fixed Enum field
names and returns Python bool values; no concrete application buffer or lifetime
defect was identified. Replacing Enum access, caching masks, changing the FIFO,
or changing packages would currently be a speculative workaround rather than an
evidenced correction. Production remains unchanged.

Remaining gap: a corrupting operation / defect at the interpreter or earlier
initialized import/tape-construction boundary has not been identified. The failed
TRAIN token and episode index are not retained by this diagnostic. A next useful
hypothesis concerns failure during codec/tape construction before the entire
projection setup, rather than the removed pre-projection I/O. Root has this
concrete earlier-boundary fact for coordinated shared-runtime investigation with
FRRIE; CM does not duplicate its runtime work or change the shared environment.
No identical repetition or additional target launch was made. DM owns intake and
any follow-on scope/allocation; no P28/P32 clearance, paired result or learner
retry follows from this record.

## Next bounded offline observation (prospective)

The new P47 crash generated
`/mnt/c/Users/wu/AppData/Local/Temp/wsl-crashes/wsl-crash-1788883898-2777975-_usr_bin_python3.12-11.dmp`
(509448192 bytes). Lowest-work next discriminator: inspect only this new saved
process, recover original native signal frame and available Python codec locals.
This asks whether the earlier packing failure exposes malformed token/Enum state
or the previously seen interpreter failure context; it cannot identify a writer
from a frame alone. None of the four previously examined cores is reexamined.

One offline GDB invocation, no inferior execution/attach, no new tape, model,
optimizer or target process. Reuse existing matching Python3.12 debug symbols at
`/home/wu/hmasd-inputs/native-crash-static-20260908/python312-symbols/usr/lib/debug`
and explicitly source the existing Python3.12 GDB helper. Disable automatic
script loading and debuginfod. Show registers, bounded native backtrace,
Python backtrace and available Python locals. No utility build/package operation.
Use original wsl_4070, existing detached supervisor, exact published source cwd,
adjacent memory admission and the same GNU-time TERM115/KILL5 envelope.
Handle `cbsc-p47-offline-core-20260908`; output is its supervisor task.log and
admission under the original P47 cwd's `test/p47_offline_core_20260908/`.
Expected work is reading one 486 MiB saved core with bounded printed frames;
normal cost unknown, capped120s; no sweep or new scientific exposure.

## Offline result and exact-episode discriminator

Offline handle finished exit0, PID2778829, start/end16:18:52Z/16:18:55Z;
outer wall2.94s, peak RSS826268KiB. Adjacent admission captured16:18:52.914596Z,
assessed16:18:52.914853Z, physical/effective15639044096 bytes, passed4GiB.
One saved core was read, with no inferior execution. Supervisor/admission roots
and exact offline argv were copied to the same P47 control root.

Native backtrace frame0 is libc pthread_kill/raise, frame2 the signal handler,
frame3 the original _PyEval_EvalFrameDefault at mapped Python/bytecodes.c3475.
Registers printed at frame0 describe the re-raise; no original RIP/R14 claim.
The source mapping alone is not writer attribution. Python locals identify
FlagField.REQUEST_ACTIVE with value request_active and an active codec token
EventKind.NOOP_SEMANTIC. Three consistent frames identify TRAIN episode51:
_finish/build_stochastic episode_id=51 and the sequential generator e=51.
Thus51 earlier TRAIN tape constructions returned by source-flow inference;
this refines the earlier log-only unknown count, not a serialized count.
Full token fields and exact token position were truncated in the debugger output.

Next selected test: `test_initial_train_episode.py` invokes the original imported
run module, sets Torch1, constructs only DynamicHost(B1_RUN_NAME,21223) TRAIN
identity51 and stops after checking/retaining its152 public seventeen-byte tokens
and readable fields. It calls no model/optimizer/projection/scoring/learner route.
Question: does this core-identified episode's original input/codec fail without
preceding episodes0..50? This is not the prior fabricated-token or six-million-call
check, and does not claim original process-state identity or full-prefix safety.
Master, split, episode, host law, lexical interpreter and CPU FP32 are unchanged;
shorter preceding allocation history is the explicit discriminator.

One detached `cbsc-p47-train51-20260908` invocation from a fresh exact-SHA cwd,
original interpreter and numeric-library thread limits, adjacent admission,
GNU-time TERM115/KILL5 envelope. Expected work: one152-token construction/packing,
2584 output bytes plus readable public fields. Normal wall unknown; cap120s,
no sweep. Complete invocation wall/RSS measured; aggregate CPU/study elapsed
unmeasured. Output `<cwd>/temp/directions/capability_bound_semantic_currentness/test/p47_train51_20260908/TEST_ONLY_episode`.
No new section4 machinery. AST/diff checks before first execution; no repeated
learner smoke. A pass establishes only completion for this shortened prefix;
a fatal retains its exact boundary. No hypothetical production fix follows.

Per-episode address check: DynamicHost owns only run_name/seed; each
build_stochastic creates a fresh AuditedCounterPRF and local state/pools. Addresses
include run_name, seed, split and episode_id; values derive from hashlib SHA256.
No prior-episode RNG state is consumed. Isolating51 therefore preserves its
specified input law while deliberately changing preceding process allocations.
The original host._finish packs152 tokens, and EpisodeTape.__post_init__ repacks
all152 for its existing canonical check (304 codec.pack calls on completion).
These are original checks, not added repeated validation. Printed token fields
remain public; evaluator truth is not exported.

## Isolated TRAIN51 result

Source `d843b5f90` was committed/pushed and staged in the fresh exact-SHA cwd
before one accepted handle `cbsc-p47-train51-20260908`, PID2779219.
Supervisor start/end16:23:49Z/16:23:51Z, exit0, tmux inactive; outer wall1.55s,
peak RSS381400KiB. Adjacent admission captured16:23:49.985005Z,
assessed16:23:49.985286Z, physical/effective15643357184 bytes, passed4GiB.
Observed Python3.12.3 / Torch2.7.0+cu118; original lexical interpreter retained.

The original TRAIN51 tape completed once, including its original304 codec.pack
calls and canonical public-byte check. Output contains152 public records and
2584 bytes, SHA256/primitive digest
`5b9c4bde5325f4f0ff808a2fb1339b8a76dc834bde707cacc236e4444405797c`.
There are16 NOOP_SEMANTIC tokens; all exported request_active/request_need fields
are false. Exact token positions/clock fields are in train51_collection_facts.json,
and full public fields in TEST_ONLY_episode_result.json. The current output is
not compared as equal to the partially printed failed-core token or historical
P32 bytes. The core's active NOOP could be any corresponding token; its exact
position remains unknown.

Copied supervisor and output/admission roots, then checked identity21223/TRAIN51,
152 records,2584 bytes, digest agreement,16 no-op flag fields, zero reported
model/optimizer/projection/score/learning counts and passing memory floors.
The zeroes also follow directly from this test's source, which never calls those
routes. No full-prefix runtime or research smoke was repeated for collection.
This pass establishes nonreproduction on one isolated original episode, not full
prefix safety, cause isolation or a repair. Actual summed wall of the three
operations (prefix7.37 + offline2.94 + isolated1.55) is11.86s; each separately met
its120s cap. Scientific exposure remains zero. Aggregate CPU and study elapsed
including control-plane work are unmeasured.

## Current engineering boundary

The selected source inspection and two distinct target discriminators have not
identified a correctable token/adapter defect. Prior-prefix allocation or other
runtime state remains an open condition; the isolated input law is not inevitably
fatal in the observed shorter execution. The minimal prefix's primary projection
comparison remains incomplete. The new saved-core native context is independent
technical evidence, and does not imply a common FRRIE cause.

A concrete next local discriminator, if continued under P47, is the original
TRAIN0..51 prefix with all52 returned tapes retained, stopping immediately before
any evaluation-tape/model/projection work and comparing only the completed51st
identity's public bytes (episode51, the52nd tape) with the saved isolated bytes.
This preserves counter-addressed input but reinstates the missing preceding tape
allocations. It is useful only for distinguishing that prefix from the isolated
case; identical repeat-to-cap is not useful. It remains zero-learning P47 work,
not a new scientific allocation, and has not been executed here. Any shared
allocator/interpreter instrumentation is instead coordinated through Root so it
does not duplicate FRRIE or silently change this slice's preserved environment.
A replacement runtime or speculative Enum/FIFO rewrite is unsupported.

CM returns collected conformance evidence and this explicit unresolved boundary;
DM owns intake and sequencing, Root owns integration and shared-runtime routing.
No process from this slice remains live. Independent review covers the source,
raw facts and limits; it is not crash-fix approval or scientific readiness.

## Final selected retained-prefix discriminator (prospective)

DM selected the concrete next route above under P47: one TRAIN0..51 tuple with
all52 tapes retained, no EVAL/model/projection/scores/learning. The same mapped
test now accepts --retained-prefix-reference, executes that tuple, selects its
last tape, then compares the public bytes only after construction completes.
No prior token/RNG law changes. Original host/tape checks perform52x304=15808
codec.pack calls on completion for7904 public tokens. Only the final episode's
2584 bytes/public fields are published. No prefix search or further automatic
expansion follows this bounded check; return a repair or a coordinated-runtime
scope need. REQUEST_ACTIVE recovered from the core is the Enum field being
accessed, not a recovered true Boolean value; isolated false flags are not a
historical mismatch.

Reference: isolated TRAIN51 TEST_ONLY_public_tokens.bin,2584 bytes,
SHA256 `5b9c4bde5325f4f0ff808a2fb1339b8a76dc834bde707cacc236e4444405797c`,
bound here before staging to
`/home/wu/hmasd-inputs/cbsc-p47-20260908/TEST_ONLY_train51_public_tokens.bin`.
Handle/cwd tag `cbsc-p47-train-prefix52-20260908`, fresh exact-source worktree.
Same original interpreter/thread limits, adjacent >=4GiB admission and GNU-time
TERM115/KILL5 envelope. Output test/p47_prefix52_20260908/TEST_ONLY_episode.
Complete normal cost unknown; prior fatal prefix7.37s/isolated1.55s supply context,
not a promise. Each operation capped120s; no sweep/learner exposure. AST/diff
checks only before this new diagnostic. No new section4 machinery.

## Restricted-turn reconciliation (read-only evidence / documentation)

The assigning DM reported that the preceding turn ended with an automated
possible-cybersecurity-risk restriction, with no individual command named.
The follow-up authorizes read-only reconciliation/documentation only; no target,
debugger, runtime, diagnostic or source action was repeated after that report.
This records the reported restriction without inferring a classifier trigger.

Last executed preparation command before the restriction edited the mapped test
for --retained-prefix-reference, appended its prospective record, parsed its AST
and ran git diff --check; both checks passed. The next communication asked the
existing reviewer to finish its current file. Its completed return reports no
material finding for isolated TRAIN51 and static inspection of the proposed
52-tape variant. No final-prefix commit, staging command, launch command or
accepted handle was attempted in the visible retained sequence.

Read-only reconciliation finds HEAD `d843b5f903663dcc5a699c0a85fbae4e5252d20f`,
previously pushed; index empty. CARD, RESULT, REVIEW and
`test_initial_train_episode.py` are modified; DM's INTAKE is untracked.
The proposed final52-tape source/card/result remain unpublished working changes.
No receipt named cbsc-p47-train-prefix52-20260908 exists in the retained control
root. The only accepted receipts there are launch.stdout (minimal prefix),
offline_launch.stdout (new-core read) and train51_launch.stdout (isolated51).
Their copied exit_code files are139,0,0 respectively; all had terminal status
before this reconciliation. No remote launch/attach/status action was needed.

Prior initial-prefix evidence and the three P47 result/admission/supervisor
collections remain in place unchanged. The four historical core analyses and
new-core original are not modified. The final-prefix outcome, byte comparison,
wall/RSS and admission are missing because no such invocation was accepted.
The remaining restriction boundary goes to DM/Root; static review is not runtime
acceptance, and this reconciliation grants no permission to retry or bypass it.

DM publication note: the preceding HEAD/dirty/unpublished description is the
reconciliation-time snapshot. The retained-prefix source/card, complete evidence
and static review are now preserved with the DM intake at a clean boundary.
This publication does not execute or accept the pending prefix, and the missing
final-prefix observations remain missing.
