# CBSC P47 minimal-prefix independent technical review

Reviewed the retained test change at `ae9383512f7754813c4fcde8de86154a5b4daef4`
against its parent and the [P47 card](CBSC_P47_PROJECTION_REPAIR_CARD_20260908.md),
especially Source, Work and the reading rule. This review owns only this file;
it performs no diagnostic execution, production edit, delegation or commit.

**No material finding was found in the test change or the narrowly stated
failure-boundary evidence.** The projection/input-comparison question remains
unresolved. This is independent technical evidence, not an approval or terminal
disposition.

## Evidence and affected behavior

Raw evidence root:
`temp/directions/capability_bound_semantic_currentness/test/p47_projection_20260908_control/`.
Read `launch.json`, staging/reference-digest output, copied
`cbsc-p47-minimal-prefix-20260908/{runner.sh,task.log,exit_code,status}`, adjacent
`p47_minimal_20260908/admission.json`, and the collected output directory.
`collection_facts.json` agrees with these sources; its zero counts are source
inferences, not independently instrumented counters.

- The log reports SIGSEGV, exit 139, while `run.py:122` is constructing TRAIN
  tapes. Its stack passes through `host.py:595` / `_finish:522`, codec `pack:251`,
  `flag_values:164`, and Python Enum `value`. The fixed field-name access and
  packing source identify the observed operation, not the corrupting writer or
  a supported repair.
- `run.py:123` begins evaluation-input construction only after TRAIN completes;
  model/trainer initialization is at 127–128 and initial projection at 132.
  Fixed-rule scoring starts at 138, policy evaluation at 147, and checkpointing
  later. Thus the observed source boundary supports zero evaluation tapes,
  model/optimizer initializations, projection/adapter calls, score evaluations,
  learning, checkpoints and scientific publication. At this initial log-only
  stage, completed training tapes, partially packed tokens and the faulting
  episode/token index were unknown; the offline-core extension below refines
  the episode/count evidence.
  The planned 416 tapes and 9,728 adapter calls are not completed-work evidence.
- The test's `initial_panel` calls the original projection, then checks shape
  and saved public bytes, writes TEST_ONLY JSON and raises `PrefixComplete`.
  Failure in those assertions or writes also cannot return into scoring.
  The retained exception is caught only outside `run_arm`, and the monkeypatches
  are restored in `finally`. The observed crash happened before this wrapper
  ran; the empty TEST_ONLY directory confirms no primary diagnostic output.
  There is no measured input equality, projection shape, or successful stop.
- The actual export and indexed logging operations would run only at projection,
  but variant differences already exist earlier: argparse processes the reference
  argument before `main`, and `main` conditionally omits installing the indexed
  observation wrapper before `run_arm`. Allocation and process-state effects
  are not isolated. The fatal event precedes projection/model initialization;
  it does not establish that reduced instrumentation caused or prevented it.

## Resource and scope boundaries

The recorded runner uses the selected original lexical Python on `wsl_4070`,
one detached task, and the existing numeric-library environment limits of one.
`run.py:110` sets Torch compute threads to one before tape construction. No
threading, mutable-state ownership, batching, dependency, precision or RNG change
is added. This unchanged runtime was not subjected to a new internal-thread
census; configured limits are not presented as measured complete topology.

Admission was captured at `2026-09-08T16:11:36.758134Z`, immediately before the
test in the same command chain, and reports physical/effective available
15,641,853,952 bytes against 4,294,967,296 required, with both floors passing.
Its cgroup fields are null; this review does not infer additional measurements.
GNU time surrounds the timeout and admission/test chain: 7.37 seconds and
615,928 KiB peak RSS. The supervisor footer records 8 seconds at integer-second
resolution. Both are below the 120-second card bound; termination was the fatal
event, not timeout. Aggregate CPU and broader staging/collection elapsed time
are unmeasured. Missing diagnostic publication remains explicit rather than
being treated as a completed projection measurement.

Applied runtime-spec General requirements, then scope-spec sections 4 and 5.
The runtime VNFC appendix and older CBSC B1 publication-repair exception do not
allocate changes to this P47 test-only diagnostic. Git reports 25 added / 8
deleted test lines, zero production changes against historical
`d2753be86c12bfa63c404ac2cac513b914371115` across `omrc_b01/` and
`opportunity_credit_b04/`. No prohibited section 4 item is added without a card
line, and no concrete source, runner, test-time or invocation-budget breach was
found. The saved-byte comparison is the selected diagnostic measurement; it is
not a new provenance launch guard. No scientific runtime probe was run for review.

## Residual risk and suggested repair

No code correction is supported by this evidence. The earlier fatal boundary is
usable engineering evidence, while the intended reduced-instrumentation
projection comparison is unresolved. The technical result must distinguish
measured and inferred partial work and retain the pre-TRAIN variant caveat above. In particular,
claiming that all variant differences begin after setup would overstate causal
isolation; CM qualified that wording, and the revised result's Concrete gap
section was checked. Neither this observation nor
the unchanged-production diff clears P28/P32, demonstrates input/process-state
identity, supports a scientific effect, or supplies a learner retry allocation.
DM owns intake and any subsequently selected diagnostic scope.

## Extension: new P47 core, offline observation

Reviewed the same control root's `offline_launch.json`, copied
`cbsc-p47-offline-core-20260908/{runner.sh,task.log,exit_code}`, and
`p47_offline_core_20260908/admission.json`. This is the newly generated P47 core
ending `1788883898-2777975-_usr_bin_python3.12-11.dmp`; no old core was reread
and the reviewer ran no GDB or target process. The recorded GDB command loads
the saved core and existing symbols/helper, prints bounded backtraces/locals,
and contains no inferior run, resume or attach command. Automatic script loading
and debuginfod are disabled; the named Python helper is explicitly sourced.

The saved Python frame output consistently identifies `split='TRAIN'`,
`episode_id=51` in `_finish` and `build_stochastic`, and generator `e=51`
(`task.log:91–100`, 106–109, 125–127). Combined with the sequential
`range(updates * 8)` generator at `run.py:122`, this supports **51 prior tape
completions as a source-order inference**. It is not a separately counted or
validated set of 51 retained tapes. The in-progress episode is 51; the complete
training tuple still had not returned. Earlier log-only uncertainty was correct
at that stage and is now narrowed by the saved process state.

The codec `pack` and packing-generator locals report the active token's event
kind as `NOOP_SEMANTIC` (`task.log:85–90`), while Enum `value`/descriptor frames
report `REQUEST_ACTIVE`. These are observed field identities, not evidence that
the field is malformed or causally responsible. Full token values and the active
packing index are truncated. In particular, `build_stochastic`'s final loop
locals (`opportunity=23`, `position=3`) are not the active packing token index:
that loop completed before `_finish` traversed the token list.

Native backtrace frames 0–2 show `pthread_kill`, `raise`, and the signal handler;
frame 3 is `_PyEval_EvalFrameDefault` at `Python/bytecodes.c:3475`. The displayed
RIP/R14/RAX were read at frame 0 before the backtrace. They describe the signal
re-raise, not the original fault frame. The observation therefore does not supply
the original fault RIP/R14 or prove an instruction-level match to an older crash.
It still identifies no corrupting writer or supported production correction.

The offline command exited 0 in 2.94 seconds, with 826,268 KiB peak RSS and
a coarse supervisor duration of 3 seconds. Its adjacent admission captured
`2026-09-08T16:18:52.914596Z` reports physical/effective availability of
15,639,044,096 bytes and passing 4-GiB floors. The existing 115-second TERM plus
5-second KILL envelope covers admission and GDB; this observation is within its
120-second cap. CPU remains unmeasured. GDB completion adds no target tape,
model, projection, score or learning execution.

No material finding is added by this extension. A prospective direct TRAIN51
construction would test a narrower path with different preceding allocation
history; it cannot be presumed equivalent to the failed process. Its source,
execution and result are outside this completed review extension. The recovered
episode informs that next hypothesis without establishing a fix or research
outcome.

## Extension: isolated TRAIN51 completion

Reviewed `test_initial_train_episode.py` at
`d843b5f903663dcc5a699c0a85fbae4e5252d20f` against the card's isolated TRAIN51
continuation. The 35-line mapped test imports the original run module and calls
only the original host's TRAIN51 construction, public-byte checks and TEST_ONLY
serialization. No model, optimizer, adapter projection, score, checkpoint or
learning route is called. It exports public fields, not evaluator truth. No
production difference or new scope-spec section 4 machinery is introduced.

Inspected the control root's `train51_launch.json`, copied
`cbsc-p47-train51-20260908/{runner.sh,task.log,exit_code}`, adjacent admission,
and `p47_train51_20260908/TEST_ONLY_episode` outputs. A read-only PowerShell
artifact check independently confirms identity seed21223/TRAIN51, 152 public
records, 2,584 bytes, and SHA256 equal to the JSON primitive digest:
`5b9c4bde5325f4f0ff808a2fb1339b8a76dc834bde707cacc236e4444405797c`.
It confirms 16 `NOOP_SEMANTIC` records with both `request_active` and
`request_need` false for those records. These agree with
`train51_collection_facts.json`. The five reported zero counters agree with
the directly inspected call boundary; they are not runtime instrumentation.

`DynamicHost` stores only run_name/seed and creates a fresh `AuditedCounterPRF`
inside each `build_stochastic` call. Its addresses include seed, split and
episode_id; `addressing.digest/u64` derives values from SHA256 of the address,
and the PRF records are local to that call. There is no preceding-episode RNG
cursor to replay. `host._finish` packs all 152 tokens, then
`EpisodeTape.__post_init__` repacks them for its original canonical check.
Successful return therefore supports 304 packing calls by source inference.
The later public-byte read and digest do not add codec.pack calls.

The raw task exits 0 after its completion marker, with outer wall 1.55 seconds,
381,400 KiB peak RSS and a coarse 2-second supervisor duration. Admission
captured `2026-09-08T16:23:49.985005Z` reports physical/effective availability
15,643,357,184 bytes and passing 4-GiB floors. The recorded original lexical
interpreter and numeric-library limits are retained; Torch compute threads are
set to one. Admission, construction, checks and output publication are inside
the existing timeout/time envelope and below 120 seconds. Artifact arithmetic
confirms 11.86 seconds for the three recorded operation walls; aggregate CPU
and broader study/control-plane elapsed remain unmeasured.

**No material finding was found in this test or its isolated-completion claim.**
The original per-episode input law is retained, but import/wrapper and preceding
allocation state differ from the failed full setup. The output was not matched
against a complete failed-core token or historical P32 bytes. Completion of one
isolated episode neither clears the full prefix nor supplies a production fix.
The result's limitations preserve that distinction.

At this extension's boundary, the proposed retained TRAIN0..51 continuation is
still prospective. Its inspected working diff retains a tuple of 52 original
tapes, reads the reference only after construction returns, compares only the
last episode's public bytes, then serializes and stops. It adds no model,
projection or learning call. This static observation supplies no completion
evidence for that subsequent diagnostic; its eventual terminal evidence requires
its own narrowly scoped supplement. No runtime was executed by this reviewer.
