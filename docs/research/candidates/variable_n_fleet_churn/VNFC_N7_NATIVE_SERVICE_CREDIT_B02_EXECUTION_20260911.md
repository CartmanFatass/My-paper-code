# VNFC B02 execution and technical acceptance — 2026-09-11

## Accepted inputs and implementation

The [card](VNFC_N7_NATIVE_SERVICE_CREDIT_B02_SCIENCE_CARD_20260911.md) and
[direction intake section 9](VNFC_NATIVE_SERVICE_CREDIT_REENTRY_INTAKE_20260910.md#9-reconciled-full-response-and-direction-decision--2026-09-11)
were committed/pushed at `3d177d27c`. Source baseline is
`10bb08476ff58afd25b90b21cd2d1a739b25ca4b`; the authoring checkout was clean before this edit.
New code is the 88-line B02 learning module and 35-line runner; N7 B01 collector/update and
publication helpers gain 34 lines and lose27. Total new non-test source157 lines, deleted27;
the 96-line synthetic test is separate. No Engineering Scope section4 machinery is added.
Unchanged native sources, model/input/action functions, original terminal GAE/PPO/AdamW,
RNG derivation and checkpoint/readback path are reused. No core or old result is modified.

Both arms retain seven native counter snapshots alongside public trajectory records.
The new module creates two independent MAPR models from the same externally materialized
fresh tensors, computes own-trajectory INTERVAL targets or the old TERMINAL recursion,
and reuses the existing real PPO update. Counter checks are directly necessary to the
selected reward definition; they are not a provenance/currentness guard. Full result
publication uses actual arm names, final primary, MEI.02 and all existing native contrasts.
Default B01 behavior, including the engineering profile's2700s projection cap, is preserved.

## Focused verification and independent review

One targeted synthetic file covers counter endpoints and failed-zone cutoff; interval-vs-
terminal GAE, detach and normalization ordering; final-vs-midpoint selection, negative zone
tradeoff preservation, JSON readback and both-arm full cost law. No model initialization,
RNG master, environment interaction or native build occurred in these tests.

Initial pytest invocation: two tests passed; the publication test setup failed because the
new scratch parent did not exist (`WinError 3`, before that test body). Internal full command
wall2.9724392s, pytest2.04s. After creating that parent, only the previously unexecuted test
ran: one passed, command2.705745s, pytest1.84s. There was no repeated successful test or
scientific retry. These are included once in support work; pytest and enclosing clocks are
nested and not added together. `git diff --check` passed.

Independent read-only Astra/high reviewer `review_b02_credit` found no material defect,
unselected machinery or line-budget breach. It inspected the changed files and reachable
native/model/RNG/action/optimizer/publication dependencies. It confirmed counter source and
60/120s windows, own-trajectory and behavior-information separation, unchanged TERMINAL
recursion and PPO, cloned initialization/independent optimizers, exposure and final readout,
single-thread/native-session topology and per-arm complete cost law. No test, model or native
execution was performed by the reviewer. Its support cost is3.251s summed displayed command
wall, approximately8.9s enclosing tool wall: nested alternative scopes, not additive.

Review limit accepted: the runner's internal complete wall stops before final stdout and
interpreter exit. The exact scientific command therefore uses existing `/usr/bin/time`
outside Python and OS `timeout`; outer elapsed and supervisor exit will establish the
process-exit-inclusive cost. This does not require another scientific invocation.
Source is technically accepted for the selected run, conditional on the actual primary and
nonzero learner/exposure observations required at terminal collection; no result is accepted yet.

## Support accounting and cleanup ownership

All support draws from300s and the combined900s allocation. Root integration receipt:
5.3663749s internally timed add/commit/push, plus approximately1.0s prior merge conflict,
2.6s audit inspection and0.1s patch. DM card commit/push5.3832615s displayed command wall;
the two tests total5.6781842s internally timed; reviewer3.251s displayed commands (~8.9s
enclosing tool wall). Other preparation/readback/patch commands, source publication,
staging/admission, Monitor commands and collection/cleanup will be included from their
receipts at collection. Unrecorded time is unknown, never zero. Deliberation and idle
queue/network waits are administrative elapsed; complete-cost conformance requires the
actual support record, not an inference from old native timing.

Scratch ownership: this DM created
`C:/Projects/HMASD-worktrees/codex-vnfc/temp/directions/variable_n_fleet_churn/test/b02_credit_20260911_01/`.
An initial combined test/recursive-cleanup command was rejected before execution with
`blocked by policy`; it ran no tests. Tests then ran through permitted non-destructive
commands. A guarded empty-directory cleanup found the test subdirectory and made no deletion.
A subsequent exact literal-file/empty-directory PowerShell cleanup was also rejected
before execution with `blocked by policy`. The existing
`test_primary_round_tradeoffs_p0` subdirectory is preserved; no alternative-shell deletion
or policy bypass was attempted. Root was informed. Cleanup remains DM-owned pending a
permitted operation; this has no scientific polarity and does not alter the invocation cap.

The shared direction authoring checkout remains active for this implementation/execution
and subsequent intake. The old unpublished request draft remains under the preservation
assignment in re-entry intake section7. Terminal collection will preserve unique evidence,
then inventory exact execution/test artifacts for authorized cleanup. Root confirms
integration/retention and eventual worktree reclamation. No remote run is accepted yet.
## Exact execution command

Reviewed scientific source was committed and pushed at
`76d4afca664f988fbaabca2923a0c891f8a784ff`. This exact SHA, not a later documentary HEAD,
is the execution input. Node `wsl_4070`; prospective detached checkout
`/home/wu/hmasd-worktrees/vnfc-b02-credit-20260911-01`; handle
`vnfc-b02-credit-20260911-01`. Source staging alone starts no scientific process.

After committed source staging, the one supervisor command is:

```bash
/usr/local/bin/agent-task run vnfc-b02-credit-20260911-01 "cd /home/wu/hmasd-worktrees/vnfc-b02-credit-20260911-01 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/variable_n_fleet_churn/exp/b02_credit_20260911_01_memory.json && /usr/bin/time -f 'elapsed_seconds=%e\npeak_rss_kib=%M\nexit_status=%x' -o temp/directions/variable_n_fleet_churn/exp/b02_credit_20260911_01_outer_time.txt timeout --signal=TERM --kill-after=1s 600s /home/wu/.venvs/hmasd/bin/python scripts/run_vnfc_native_service_credit_b02.py --seed 2026091101 --eval-seed 2026091102 --out temp/directions/variable_n_fleet_churn/exp/b02_credit_20260911_01 --launch-sha 76d4afca664f988fbaabca2923a0c891f8a784ff"
```

The timer includes the timeout wrapper, Python imports/build through final process exit.
The600s timeout bounds the complete scientific invocation; any kill-grace overshoot is
reported as a cost breach, not accepted as within600s. Native outputs are under the named
run root. The memory receipt and outer time file are sibling files outside that root.
Supervisor log/status are `/home/wu/.agent-tasks/vnfc-b02-credit-20260911-01/`.

The live Monitor endpoint was reread from
`C:/Projects/HMASD/.codex/hmasd-monitor.toml`: `01a087e5-2044-7301-abb6-7a1709a98197`,
Root `01a07249-b095-7821-8ce2-e9c32ba85267`. On acceptance the DM sends the exact handle,
SHA, node/cwd/run/receipt paths and original owners directly, with observation command
wall charged to this object's support budget. Dispatch and actual adoption are separate.
Owner reviews again returned `[]`. No launch acceptance or model result is asserted here.

## Exact source staging receipt

The first remote HTTPS fetch timed out (exit124), outer wall37.02s; no scientific
process existed. The configured network-login shell was not used for that fetch, so
this is a command-level network timeout, not evidence that remote source is unavailable.
The permitted exact-byte alternative used an incremental Git bundle against the
already-present `2482db44052705b130b3970456415d2309c99e2b`. A first bundle command naming
only the raw commit produced `Refusing to create empty bundle`; it transferred nothing.
Using HEAD at the same bound SHA produced89,959 bytes; `git bundle list-heads` returned
`76d4afca664f988fbaabca2923a0c891f8a784ff HEAD`. Creation plus SCP took0.7596152s internally.
Remote import took0.12s; detached worktree creation took0.21s. The new exact checkout
reported the bound SHA and an empty short status. No uncommitted source was staged.
The37.02s fetch wall is conservatively included in support accounting, including its
network wait; no administrative exclusion is used to hide this failed operation.

Local bundle:
`temp/directions/variable_n_fleet_churn/source_staging/b02_76d4afca6.bundle`.
Remote bundle: `/home/wu/hmasd-inputs/vnfc_b02_76d4afca6.bundle`.
Both are this DM's source-staging artifacts for collection-time cleanup after evidence
preservation; the detached execution checkout remains until terminal collection/acceptance.
Source commit/push command added5.3752014s displayed support wall.

## Launch acceptance and Monitor adoption

The exact command above was committed/pushed at `8dc043f2f`. Immediately before dispatch,
the named supervisor handle returned `not_found`; the one `agent-task run` then returned
acceptance into detached tmux. Its command support wall was0.3628601s internally
(1.5257668s displayed enclosing command, including the pre-dispatch handle read).
The source, identity and scientific command were not changed or retried.

Destination admission at `2026-09-11T18:26:52.030302Z` reported
physical/effective available15,636,619,264 bytes against4,294,967,296 bytes and `passed=true`.
The receipt came from `/proc/meminfo` on this exact node. The one launch-acceptance read
then reported `running`, supervisor wrapper PID3347770, uptime35s, exit null and active tmux.
That combined status/receipt read cost0.5249107s displayed command wall. It is a technical
launch observation, not evidence of final learner exposure or a valid scientific result.

Direct `MONITOR_ADD` to the live singleton endpoint was accepted. Root subsequently
confirmed actual adoption of this same handle/SHA/node/cwd/output, still running, with the
same passed admission; adoption observation command wall1.0s. The Monitor's continuing
status/log command costs belong to this object's support accounting. The DM has stopped
routine polling and retains collection, technical acceptance, scientific intake and cleanup.
Root routes the terminal fact to this original DM; no second observer or new invocation exists.

Pending collection: preserve full native summary, curves, all episode rows and six
checkpoints, plus outer time, admission and supervisor terminal log/status. Read primary
and counter targets against the card; report every arm/zone/native metric and actual
nonzero counts/movement, then write the valid-result intake/Chinese brief if supported.
Inventory the exact detached checkout, source bundles and creator-owned scratch for
cleanup only after unique evidence preservation and Root retention/integration reconciliation.
The exact policy rejection in the scratch section remains unresolved; no deletion bypass.
No extra arm, retry, evaluation or successor is authorized by this handover.

Command/staging documentary commit/push added4.6467948s displayed support wall. Final
support accounting will distinguish internal clocks, displayed enclosing alternatives,
approximations and genuinely unmeasured components without double-counting.

## Terminal collection and closeout

Root routed Monitor's terminal fact on2026-09-11: the same handle failed exit139 at
2026-09-12T02:28:09+08:00 after78s. Collection confirms signal11/77.84s, two initial
checkpoints and15 logged arm-rounds, with no complete primary. The
[E0 collection](VNFC_N7_NATIVE_SERVICE_CREDIT_B02_RESULT_EVIDENCE_20260911.md) and
[DM intake](VNFC_N7_NATIVE_SERVICE_CREDIT_B02_RESULT_INTAKE_20260911.md) preserve this
incomplete attempt without performance polarity. No retry, workaround invocation,
extra test, source change or successor occurred. The earlier pending-collection text
is historical launch state, superseded by these terminal records.

Raw11-file archive SHA256
`1bbcfbe499e8a15bb1d5f4a0d4fdaf0fa8a52feda65da4de4f2f3e2abc575de5`
matched remote/local. The additional local recovery archive preserves the unpublished
draft, source bundle and synthetic scratch bytes. Both archives and complete inventories
are under `evidence/b02_credit_20260911_01/`. Exact source remains published and unchanged.
Root source/launch integration through mainf6fb5606b added10.4s displayed support wall;
the shared1.3s RCLE+VNFC terminal observation is charged only to RCLE per Root. Other
timings and missing scopes are explicit in `support_costs.json`; full cost is unestablished.

At first collection publication, scoped remote checkout/staging cleanup awaits Root's
integration acceptance of the preserved evidence. The scratch `blocked by policy`
rejection remains unresolved; no bypass or repeated deletion attempt is authorized.
The shared authoring checkout is retained for this intake/cleanup, with eventual
reclamation owned by Root. Verified deletion or remaining-path facts will follow here.

### Root acceptance and actual cleanup — 2026-09-11

Root integrated the14-file preservation/intake commit
`94c8fdfa888df014fa9fd83a4014a1cb10b7d501` through published main
`cf93e737ee83f2d78d14c5569874590af8ccd347`, then explicitly returned the named cleanup
inventory. Before remote removal, all11 archived byte streams equalled their originals;
the five noncache ignored files were exactly covered, both input-copy digests matched,
and the detached checkout had clean tracked/untracked source at the bound launch SHA.

[Remote cleanup receipt](evidence/b02_credit_20260911_01/remote_cleanup.json) verifies
the exact checkout `/home/wu/hmasd-worktrees/vnfc-b02-credit-20260911-01` is absent on
disk and from `git worktree list --porcelain`. Input copies
`/home/wu/hmasd-inputs/vnfc_b02_76d4afca6.bundle` and
`/home/wu/hmasd-inputs/vnfc_b02_partial_20260911.tgz` are also absent. The small terminal
supervisor directory and its six files remain. No other checkout or source branch was removed.

The remote cleanup command executed its removals, then its final receipt here-document
terminator reached Python as `PY`, causing `NameError` after the absence assertions/JSON
print. No deletion was repeated. A separate read-only reconciliation verified the actual
absence facts above and produced the receipt. The failed command1.0538243s displayed
wall and read-only reconciliation0.4776158s internal wall are both retained as support.

Automatic approval review rejected the separate exact PowerShell local draft/source-copy
cleanup before execution with `blocked by policy`. This new rejection concerns only
the three preserved draft/source files and their empty draft directory; the earlier
blocked test scratch was not targeted again. No alternative deletion method or repeated
attempt followed. [Local cleanup record](evidence/b02_credit_20260911_01/local_cleanup.json)
confirms all four local files (including the earlier scratch) still exist and match the
committed recovery archive. Local cleanup is blocked, not complete. These exact local
paths remain DM-owned; Root owns the shared direction checkout's lifecycle.

`support_costs.json` now includes the collection publication and these closeout operations;
its selected documented component sum is108.999243 s, plus approximate3.7s Root preparation.
Unmeasured scopes remain explicit; final cleanup-record publication timing is returned
to Root separately. The final owner review read returned `[]` and the intake audit owner
cell remained blank. This closeout changes no scientific interpretation or allocation.

## Owner-directed technical repair assignment — 2026-09-11

Root's OWNER_DIRECT correction assigns diagnosis/repair of exit139 and technical readiness
for a future separately allocated invocation. L0 goal: identify an attributable defect and
make the smallest semantics-preserving source repair, or return the exact remaining
diagnostic and a bounded non-result-bearing method. Owned checkout remains
`C:/Projects/HMASD-worktrees/codex-vnfc`, branch `codex/vnfc`; clean starting HEAD0afee6d88
was fast-forwarded/pushed to current mainf2ca4a811. The B02/N7 source surfaces did not change.

Entry points are the preserved11-file archive and supervisor log, the exact launch
source76d4afca6, N7 `native.py`, R09 `native_backend.py`/`native/bpcr_general.hpp`, and
`models.py::exact_binary64_mean` through `torch_models.py::_ExactRosterMean`. This DM
owns the bounded repair record/evidence and any attributable change on that path; a
shared scientific-code change receives independent high-risk review before acceptance.
The card supplies protected seeds, reward/credit, comparator, MEI, dtype and native
semantics. None changes, and the incomplete primary stays incomplete.

Acceptance uses existing-core reads, static source/binary interface checks and bounded
synthetic checks only. No model/environment construction, training, evaluation, RNG master,
native scientific trajectory, resource admission, agent-task launch or scientific retry
is authorized. Individual debugger reads are bounded at45s or less; a focused synthetic
primitive check, if needed, is bounded at20s. This assignment will stop at attributable
repair/readiness or a precise attribution gap, with at most120s additional measured
support work selected locally; this is not an added scientific allowance. All measured
work is reported alongside the unchanged600/300/900 limits and the earlier missing
support scopes. No new machinery under Engineering Scope §4 is selected. Existing local
copies/scratch remain preserved and are explicitly nonblocking; no deletion is attempted.

### Technical investigation closeout — 2026-09-11

**Not ready: the source-level writer remains unattributed.** Root's final instruction
closes the present investigation using the saved/static findings, with no further
diagnostic and no scientific execution. Production source is unchanged. The proposed
integer-ratio mean exists only as the unadopted
[candidate patch](evidence/b02_credit_20260911_01/repair_candidate.patch), not a runnable
repair or a readiness claim. This section supersedes the earlier terminal assignment's
prohibition on all investigation only for the expressly authorized technical work above.
It changes no historical source, scientific result, invocation count or decision rule.

The original WSL crash file was found after the earlier checkout-root inventory, which
had not searched the host crash store. Its argv/PID/time identify the B02 process;
631,513,088 bytes, SHA256
`0698c60ba73088b5c512c1941a2bdfc9cec3e87f22cf8a10adfd2f0a3e32e323`.
[Symbolized core](evidence/b02_credit_20260911_01/repair_core_symbols.json) and
[decoded Python frames](evidence/b02_credit_20260911_01/repair_python_frames.json)
place the stopped call in Fraction deallocation inside `exact_binary64_mean` during
PPO update. The saved stack is a detection site, not the corrupting instruction.
Debugger failures while locating frame/string/NumPy dtype layouts remain in the
`repair_core_python`, `repair_core_frames` and `repair_mean_input` receipts. Their
read-only failures were corrected only to recover existing bytes. Debugger warnings
about executable/CUDA build identity are retained; no stronger binary-identity claim
is inferred from matching function names.

A recovered finite 7×64 binary64 input has SHA256
`b75af3ba32ead6bfc5d08069ff579658643c2cc301818f2493703c3abde87a7a`.
The [isolated primitive check](evidence/b02_credit_20260911_01/repair_primitive_check.json)
passed 1,025 exact-mean calls without importing Torch/native code. The
[isolated autograd check](evidence/b02_credit_20260911_01/repair_autograd_check.json)
passed 64 applications to 24 repeated copies of that matrix (1,536 means and 64
synthetic backward calls). Both retained output digest
`92e005521234d95c422df6e3e9800874fa2b552ab2c79606099f50b6d5811bd7`.
These are fixed-input function checks, with no scientific model, environment,
optimizer, RNG master, trajectory, training or evaluation.

An allocator-guarded version of the same isolated bridge then aborted within its
256-application bound; the completed application count was not printed. The
[recorded failure](evidence/b02_credit_20260911_01/repair_allocator_failure.txt) and
[saved synthetic core](evidence/b02_credit_20260911_01/repair_allocator_core.json)
show a 32-byte CPython API-m block checked while being freed by
`_PyObject_Call_Prepend`, through `slot_tp_new` / `type_call` / Fraction construction.
Its trailing eight bytes contain a pointer-sized value in place of allocator padding.
The current mean's Fraction list comprehension has not completed: its final
`np.array`, following `torch.from_numpy` and outer `torch.stack` have not executed.
This does not establish a numeric output-array overwrite. Earlier operations in the
same process remain possible contributors. No local extension, array operation or
CPython instruction is identified as the writer by these stopped stacks.

The [allocation-trace receipt](evidence/b02_credit_20260911_01/repair_allocator_trace.json)
preserves both outcomes: 1,025 pure arithmetic calls passed; the traced bridge reached
its 20-second bound without output and was terminated. The latter produced no completed
diagnostic result. A [static ABI check](evidence/b02_credit_20260911_01/repair_static_abi.json)
found six archived native-export sizes equal their ctypes declarations; one initial
parser assertion on a differently encoded unused export was retained in accounting.
Size agreement does not prove memory ownership or exclude earlier corruption.

Independent Astra/high review found the integer-ratio candidate preserves the exact
rational mean's final binary64 rounding, input validation, output type and custom
backward `gradient / n`; both arms would share it. It found no material numerical
defect, but correctly limited it to a candidate workaround. A further saved-evidence
review confirmed the call-argument-block attribution gap. The
[review record](evidence/b02_credit_20260911_01/repair_review.md) preserves both findings.
No candidate execution, model test or scientific rerun was used to imply crash repair.

### Remaining diagnostic and concrete exit condition

The missing facts are the damaged block's exact allocation ownership/size operands,
the argument-write extent in the bound CPython executable and its constructor/vectorcall
callees, and evidence identifying the instruction that first changes the trailing bytes.
The bounded future method is a conventional memory-ownership check on the same saved
matrix and isolated function bridge, capped at one 20-second diagnostic process, with
no scientific workload. It must yield either the allocating/writing call sites and
their sizes, or a source-boundary proof that the minimal correction removes the offending
write while preserving the mean/gradient contract. A completed faithful synthetic check
and independent review would then establish only that bounded technical correction.
That method is **not executed or queued by this closeout**. Failure to obtain those
facts leaves readiness unresolved; passing the candidate alone is not the exit condition.
A future result-bearing attempt still needs a separate allocation and its own admission;
the ended B02 allowance, seeds, comparator, MEI and 600/300/900 caps remain unchanged.

Root reported two automated service rejections before any reported command/tool effect.
Their exact attempted methods, rejection text and reported provenance are retained in
[tool events](evidence/b02_credit_20260911_01/repair_tool_events.json). They are rejected
method requests, not performed checks, scientific outcomes or permission to bypass a
restriction. No further dynamic method follows the final closeout instruction.

### Retention and costs

The original scientific core and synthetic allocator-abort core remain in the host's
existing `/mnt/c/Users/wu/AppData/Local/Temp/wsl-crashes/` store at the exact paths in
their receipts. The latter is 537,112,576 bytes, SHA256
`b2dd8cab7946120d68a312189a4a8821e34a4e6a64b3f78d2612c13d1999d2e7`.
Both are retained diagnostic evidence; this DM owns any later preservation/reclamation
handover to Root. Neither core is embedded in Git or deleted here. The original 11-file
archive, supervisor record and four preserved local copies/scratch remain intact.
The previously verified remote checkout/input removal is not repeated. The shared
authoring checkout remains Root's maintained direction checkout.

[Repair costs](evidence/b02_credit_20260911_01/repair_costs.json) distinguish bounded
diagnostic commands, failed reads, synthetic checks, review and publication support;
internal and enclosing alternatives are not summed twice. Additional support does not
alter the prior 77.84-second scientific invocation. Full 300/900-second support/cost
conformance remains unestablished because earlier components were unmeasured. No new
primary, valid-result efficiency ratio or scientific exposure is reported. At the final
owner-review boundary, `item.py reviews --json` returned `[]` and relevant audit owner
cells were blank. No new P1/P2 item or mechanism-level `DIRECTION.md` edit follows.

The documented repair component subtotal is69.756358s through record readback.
Combining the selected prior components and separately returned prior final-publication
clocks gives183.698311s of documented support, plus approximate3.7s prior Root preparation.
This is a partial sum, not a claim that the entire support cap passed. The last record
formatting/restoration command cost0.404504s; final commit/push timing is returned to
Root separately so accounting does not create an endless publication cycle.

## Portfolio-conditioned technical continuation — 2026-09-11

Portfolio response `6c32ade3216c374ecf2f5179b15d559729cd45c9` §6 funds a future fresh
pair conditionally. Its technical acceptance rule is: "The existing technical DM must
demonstrate a supported repair of the affected path, or a credible same-meaning
alternative whose independence from the corruption is established by relevant focused
evidence." The existing workaround algebra alone is explicitly insufficient. The new
900-second scientific allocation is not this repair's diagnostic/support allowance.
Root first limited the continuation to static mapping, then supplied that mapping and
assigned assessment of the minimal replacement, focused regression and independent review.
No scientific execution or Monitor handoff is part of this assignment.

L0: deliver a technically assessed replacement of `models.py::exact_binary64_mean`
that eliminates the implicated Fraction-constructor argument-vector path, or retain
the precise unresolved acceptance gap. DM owns that helper, mirrored
`tests/experiments/candidates/variable_n_fleet_churn_bpcr_r09/test_exact_mean.py` and
this direction's records in the same `codex/vnfc` checkout. Current main was reconciled
by merge `388850322` after fast-forward was correctly refused; no history rewrite.
The independent reviewer owns only its separately coordinated static evidence publication.
Production adoption remains pending the focused evidence and review below.

Preserve the finite, nonempty two-dimensional binary64 input contract, exact rational
summation followed by one binary64 division, order independence, output dtype/shape,
input ownership and `_ExactRosterMean.backward` gradient divided by roster size.
Both arms keep the same helper; every model, seed, reward, information, checkpoint,
optimizer, comparator and native rule is unchanged. The implementation uses existing
integer arithmetic on each float's exact ratio; no new Engineering Scope §4 item.

Acceptance is deliberately bounded: the actual static receipt and its limitation,
one focused remote pytest command on the committed source, independent high-risk review,
and exact source staging/readback. Two tiny deterministic regressions check bitwise
agreement with a Fraction reference over cancellation/rounding/underflow/finite maximum,
and forbid the former constructor path through the real custom-autograd helper while
checking output, gradient and unchanged input. They construct tensors/arrays only,
with no scientific model/environment/optimizer/RNG master, native trajectory, training,
evaluation or scientific result root. No new debugger or allocator trace is planned.
The focused command has a 20-second timeout; maintenance work is bounded at120 seconds
of additional measured support, recorded separately from all scientific allowances.
Stop at accepted bounded alternative or the concrete remaining conformance gap; no
scientific pair launches until Root accepts and integrates readiness.

### Static mapping, review and disposition

The reviewer published the exact installed source/symbol/disassembly bytes at
`06fc94e6268072a3be02abc78738d32813b950f0`, in
[repair_exact_interpreter_static.json](evidence/b02_credit_20260911_01/repair_exact_interpreter_static.json).
Its ELF digest matches the executable digest recorded beside the preserved core:
`ca420bd4614ae7757b4cd4938b3c663e98d2b631bda518610071d9a4ca0b509e`, CPython3.10.21,
Clang22.1.3. This uses the bound remote installation, not the local Windows interpreter.

The declared `Fraction(n,d,_normalize=False)` constructor call adds `cls`, giving three
positional values and one keyword. Exact `_PyStack_UnpackDict` instructions allocate
`(3 + 1 + 1 reserved) ×8 = 40` bytes. The final keyword occupies byte offset32.
Relocating `_Py_FalseStruct` gives exactly the saved tail value `0x5722fcf9bac0`.
Thus `False` there is expected within the40-byte argument vector and conflicts with
the saved debug header's32-byte boundary. The existing binary already includes its
reserved slot; no missing-eight-byte allocation formula is demonstrated. The block
is a CPython argument vector, distinct from Fraction instance storage and the512-byte
numeric output. The static counts are the expected call, not captured allocation-time
operands; that distinction controls the conclusion.

I prepared the same exact-ratio replacement plus two focused tiny-array tests. The
independent reviewer found no numerical/gradient defect and judged the tests meaningful
for exact rounding, cancellation, order, ownership, gradient and former-path exclusion.
It also found a **material readiness gap**: none of those observations establishes
independence from the corruption that may have occurred before detection. Original
primitive/autograd passes already coexist with the later allocator failure. The source
formula and tail identity do not recover the actual allocation-time counts/request or
explain subsequently observed size metadata. The DM accepts this finding.

Consequently the proposed test command was **not run** and the temporary production
edit was restored. The code and regression survive only as an
[unadopted candidate patch](evidence/b02_credit_20260911_01/repair_fraction_path_candidate.patch);
the test draft's SHA256 is `ae06c830e6368954856b2c8dd01b7d79b41af1bf6208e0d9719ecf3cd632e25f`.
No corrected-source remote staging or scientific launch is asserted. The earlier L0
above describes the conditional plan, not completed acceptance. The
[assessment](evidence/b02_credit_20260911_01/repair_fraction_path_assessment.json)
records the arithmetic, exact gap and actual states. Production remains at the
previous accepted implementation. This continuation ran no debugger, fixture, test,
model, environment, optimizer, scientific RNG, training, evaluation or scientific invocation.

The unresolved fact is allocation-time positional/keyword counts and requested size
versus the later debug size metadata, or equivalent evidence establishing that a minimal
alternative is independent of the corruption. Algebraic equivalence and path exclusion
alone are not that fact. Status remains **NOT READY under Portfolio §6**. Its new
scientific funding remains conditional and unused; the earlier incomplete B02 is not
reopened or given performance polarity. Root receives the precise gap rather than a
local relaxation of the Portfolio condition. Both cores and all previously retained
evidence/copies remain preserved; the only removed file was this newly authored,
unrun test draft after its preservation in the candidate patch.

Selected maintenance command costs through assessment preparation total21.0766206s,
including4.9540463s earlier exact-static review,6.3729295s static-artifact publication
and0.6660973s subsequent diff/regression review. The reviewer capture0.6437807s is nested
within its publication cost. These receipts remain separate from the new900-second
scientific allowance; no diagnostic cost is hidden in that allowance. The assessment
write/restoration/audit command added0.3643131s; final checks/publication are returned
separately. No complete aggregate support measurement is claimed.


## Windows recovery: owned mean boundary — 2026-09-12

Root explicitly resumed the existing engineering responsibility, separate from the
unlaunched conditional fresh pair. Its later same-turn instruction authorizes one
new maintenance check of at most20 seconds if independent static review finds it
relevant. This allowance is neither an inference from the earlier incompletely
measured120-second maintenance account nor a debit from the scientific900-second
allocation. There is no second diagnostic fixture, old-path rerun or automatic retry.

Backend probe directly observed Windows10.0.26200, PowerShell Core7.6.4 and
`C:/Program Files/Git/cmd/git.exe`. Starting checkout was clean at `c922b2544`.
The two remote WSL migration commits were retained by fast-forward to `4c3f871aa`;
`2980c7fae` then copied the needed Windows main `0f37c4cbd` control inputs by exact
path and was pushed. The retained WSL inventories are historical. No main edit or
scientific source change was part of that synchronization. Runtime routes are read
from current `C:/Projects/HMASD/.codex`, never this older direction snapshot.

L0: deliver a bounded, technically assessed alternative at the whole exact pooling
boundary. DM owns `models.py::_exact_binary64_column_means` and its NumPy wrapper,
`torch_models.py::_ExactRosterMean`, their one mirrored retained-input test, and this
record in the designated `codex/vnfc` checkout. The source now copies detached CPU
float64 values into private Python lists, uses the previously reviewed exact-integer
ratio arithmetic, and constructs private CPU float64 Torch output. The NumPy-facing
model uses the same helper. Fraction construction and local Torch/NumPy shared-storage
conversions are absent from this boundary. Preserve exact sum/one rounding, roster
order independence, finite/nonempty matrix and zero-column behavior, shapes, input
ownership and backward `g/N`. Both arms retain identical architectures and numerics;
no model, comparator, reward, information, RNG, optimizer, checkpoint or native law
changes. No Engineering Scope section4 item is added.

Independent read-only Astra/high reviewer `review_a_h_vnfc_alternative` found this
whole-boundary proposal a credible same-meaning candidate with a relevant finite
check, while retaining the material limit of any pass. Its first static review cost
1.8918168 seconds across six commands; no numerical work occurred. The recorded
isolated allocator failure already occurred without the native environment or model,
so the relevant check need not reconstruct full training history. Arithmetic-only
and former-constructor-exclusion tests alone remain insufficient. The new actual
source diff receives independent review before executing the one check.

Exact check input is the existing `repair_primitive_check.json` in
`evidence/b02_credit_20260911_01/`: file SHA256
`edfb24771ab20af26949fe4dc29155d1cdb69ec83ed3fb3815ba67854d33cb47`,
decoded7x64 binary64 input SHA256
`b75af3ba32ead6bfc5d08069ff579658643c2cc301818f2493703c3abde87a7a`,
retained64-value mean SHA256
`92e005521234d95c422df6e3e9800874fa2b552ab2c79606099f50b6d5811bd7`.
Use24 copies and256 complete forward/backward applications:256x24x7x64 =
2,752,512 scalar inputs across the changed bridge, plus one448-value NumPy-wrapper
readback. This is fixed small engineering coverage, not sampled trajectories,
independent training evidence or a search. No nn.Module, environment, optimizer,
scientific RNG master, checkpoint or scientific result is constructed.

After exact committed-source staging to
`/home/wu/hmasd-worktrees/vnfc-owned-mean-20260912`, the single command is:

```sh
cd /home/wu/hmasd-worktrees/vnfc-owned-mean-20260912
PYTHONMALLOC=debug PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /usr/bin/timeout --signal=KILL 20s /home/wu/.venvs/hmasd/bin/python -X faulthandler -m pytest -q -s -p no:cacheprovider --basetemp temp/directions/variable_n_fleet_churn/test/owned-mean-20260912 tests/experiments/candidates/variable_n_fleet_churn_bpcr_r09/test_owned_exact_mean.py
```

Expected: one test passes after exactly256 forward/backward completions, retained
exact output agreement, shaped `g/N`, unchanged inputs, declared versions/thread
count and normal interpreter teardown. Retain stderr and actual outer elapsed time.
The20-second ceiling includes interpreter imports, assertions, output and exit;
source transfer/receipt collection/creator scratch cleanup are separately measured
maintenance. A timeout, abnormal exit, incomplete count or mismatch gives no pass
and no automatic alternative fixture. All test scratch is owned by this invocation
and removed after preserving the needed receipt; the temporary detached checkout
is an integration/retention dependency until Root accepts its reclamation.

A pass plus actual source/ownership review may support this bounded alternative
under Portfolio6c32ade32 section6 and empirical11.8.7. It cannot identify the old
writer, resolve the saved40-versus32-byte discrepancy, certify general interpreter
safety, establish complete-pair cost or supply a final scientific primary. No
scientific launch or Monitor handle is asserted by this technical check plan.

Actual-source independent review completed before publication: no material finding;
source/consumer/import and test scope accepted for the single check. Its additional
five read commands took1.6770806 seconds. [Full bounded review](evidence/b02_credit_20260911_01/repair_owned_boundary_review_20260912.md)
retains the counterargument and post-exit evidence requirement. Three changed Python
files passed AST parsing only; no scientific imports or numeric execution occurred locally.


### Actual check and technical acceptance

Published source `d76d96cbe3df9b598e0db695a8b39deb23e7bdb1` was staged once through
the existing binary-stdin/network-context source helper. All four declared source/input
readbacks matched. Interpreter digest `ca420bd4614ae7757b4cd4938b3c663e98d2b631bda518610071d9a4ca0b509e`
matched the retained exact build. The recorded zsh initialization warnings did not
prevent staging; its receipt preserves them. Staging local elapsed6.407 seconds
contains remote5.629739329 seconds, not an additional scientific cost.

The sole check ran on CPython3.10.21/Clang22.1.3, Torch2.7.0+cu118, NumPy1.26.3,
CPU float64, one compute thread and allocator debug. It completed256/256 real
forward/backward applications; exact retained mean, `g/N` and unchanged input checks
passed. Pytest reports1 passed/2.60s. External normal exit0, empty stderr and
3.177215865-second complete process establish teardown. Local SSH/control3.89s
includes that process and the0.000107372-second scratch cleanup. No rerun occurred.

The same independent reviewer accepted these actual receipts with no material gap.
DM **technically accepts this bounded same-meaning alternative** under Portfolio§6.
It supports normal preparation of the independently funded fresh pair; it is neither
a historical writer attribution nor evidence that the primary scientific run succeeded.
The original40-versus32-byte fact and B02 quarantine remain unchanged.

[Acceptance and cost scope](evidence/b02_credit_20260911_01/repair_owned_boundary_acceptance_20260912.json)
links source staging, actual check and review. The selected complete outer maintenance
components total14.0399196 seconds (remote nested clocks excluded); other reads/edits/
Git/integration work is not comprehensively measured. The new20-second check cap passed;
no claim of full historical120/300/900-second cost conformance follows. This maintenance
was explicitly separate from the unused fresh scientific allowance.

Creator test scratch is absent. The exact-source technical checkout and its one JSON
receipt remain only through Root integration/retention acceptance; DM owns their later
reclamation. Historical evidence roots/cores and the shared authoring checkout remain.
