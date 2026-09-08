# P47 native crash repair evidence — 2026-09-08

Status: bounded batch complete; native check passed, input-factory harness failed
before tape generation. Harness correction is unexecuted under Root's explicit
terminal-collection/no-retry instruction. No production correction established.
Authority: P47, “FRRIE and CBSC: repair within the research chains”. This is
technical A/RECON evidence under evidence-spec §§3–4,5.1,11.8.5–7, with zero
learners, optimizer steps, scientific evaluation, or new research seeds.

## Source inspection and retained facts

Authoring checkout: `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`,
`codex/frrie`, clean start `389d6222eb0eefde7f49e47aa35d6a57ecb661c3`.
The P47 handoff confirms all three comparison batches completed. Production
source is unchanged. DM retains scientific intake/card ownership.

Reused the full `NATIVE_CRASH_FORENSIC_RESULT_20260908.md` and its direct static
review and interruption context in `C:/Projects/HMASD/temp/native-crash-repair-20260908/`.
Four matching-symbol core analyses already locate invalid interpreter state,
including the semantic-address validation caller and CBSC Enum/list callers;
they do not identify a corrupting writer. The tape-only and six-million-call
checks did not reproduce failure in those simplified checks.

Inspected `rng.py`, `tapes.py`, B01/R02 tape producers, `native_adapter.py`,
`native/native_abi.py`, the C++ batch exports and their indexed FIFO/pending paths.
Tape construction owns immutable byte-backed arrays. Native payloads pad to21
agents. Adapter calls retain direct ctypes arrays synchronously; snapshots own
exact `STATE_SIZE * count` bytes. ABI argument/restype declarations and state-size
checks match the inspected exports. Pending uplinks are created for listening
relay indices, bounded by the registered roster. No concrete fault was found
in these inspected boundaries; this is not a complete memory-safety proof.
The C++ and ABI source diff against historical `43eec21e9584c83e5e8d940402d7e4570b454e59`
is empty. No production correction is justified by static inspection alone.

## Selected bounded native discriminator (recorded before invocation)

Hypothesis: the retained A07 native library's direct reset/observe/step/state-copy
boundary can reproduce corruption on fixed legal inputs without a learner.
The earlier tape/import checks do not exercise this boundary. Reuse unchanged
`experiments/candidates/finite_resource_relational_inductive_efficiency/native_crash_repair/reproduce_native.py`
at the starting SHA; its previous committed presence is not passing evidence.

The probe uses four rosters (6,9,15,21), eight resets each,32 lanes and12 slots:
32 reset calls plus384 calls each to observe/snapshot/restore/step =1,568 native
calls and12,288 fixed-input lane transitions. It checks allocated buffer borders,
state-copy equality and terminal slot12, without reading an algorithm endpoint.
Expected observation is either a concrete call/assertion/fatal failure or completion
of those checks. A pass cannot clear the production collector, worker topology,
full initialization, interpreter, or historical crashes.

Per-invocation cost projection: no complete-path timing yet for this native probe;
known work is the counts above, fixed buffers and existing library load. One
complete invocation is capped at120s (TERM115s plus5s grace), including admission,
imports, calls and output. No fresh build or profiling. This is one diagnostic,
not a scientific arm or sweep; capped wall sum/critical path120s, aggregate CPU
unknown until observed. Focused-test allowance remains separately300s.

Post-learner path coverage: no learner/publication path is changed or claimed.
The diagnostic's primary output is its terminal JSON plus admission, supervisor
exit and wall/RSS receipt. Existing publication failures remain unresolved.

Execution binding: `hmasd-wsl-node`, CPU; historical interpreter
`/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python`;
OMP/MKL/OpenBLAS/NumExpr thread limits1. No host/device substitution.
Fresh detached cwd `/home/wu/hmasd-worktrees/frrie-p47-native-boundary-20260908`
at `389d6222eb0eefde7f49e47aa35d6a57ecb661c3`.
Handle `frrie-p47-native-boundary-20260908`, configured `agent-task` supervisor.
Relative output `temp/directions/finite_resource_relational_inductive_efficiency/exp/p47_native_boundary`.
Adjacent `admit-memory && python -X faulthandler -m experiments.candidates.finite_resource_relational_inductive_efficiency.native_crash_repair.reproduce_native`
uses the existing A07 artifact argument
`/home/wu/hmasd-worktrees/frrie-a07-scheduled-stack-p35-43eec21e/experiments/candidates/finite_resource_relational_inductive_efficiency/_native/libfrrie_ridgegate2z_external.so`.
Preserved artifact reuse is diagnostic only; it does not enter the fresh-build
production loader or change that loader's admission meaning. Artifact identity,
full shell invocation and actual receipts will be retained with the result.

Engineering-scope §4 additions: none. No new process framework, namespace,
utility build, compatibility layer, or production guard. Independent review is
required if a native/semantic production correction emerges; none exists yet.

## Recovery allocation

DM's P47 review identifies no currently runnable learner remainder: R09 is
`NO_RETRY_ALLOCATED`, P22 is one pair/no retry and P35/P37 ended at A07.
P47 authorizes this ordinary non-learning repair work, not another R09 invocation.
Historical failures and all original scientific meanings remain unchanged.

## Native discriminator outcome and next hypothesis

The selected native handle completed exit0 at16:11:18 UTC,2026-09-08. Fresh
admission at16:11:17.692654 UTC measured15,640,145,920 physical/effective available
bytes against4,294,967,296. Primary JSON reports1,568 calls,12,288 fixed-input
transitions, unchanged buffer borders and equal snapshot restores. Process
wall0.33s, peak RSS18,680KiB; supervisor duration1s. Aggregate CPU unmeasured.
The retained library SHA256 was
`0c1af4bfd791337f4b420010a49cc1f156732a840faa7c69580d3aabcf6044b4`.
Full `launch.json`, `admission.json`, `task.log`, `process-time.txt` are collected
under the authoring checkout's relative output named above. Root received the
accepted handle and pre-adoption terminal facts; no relaunch occurred.

Staging fact: plain-shell partial-clone object inspection stalled in Git HTTPS
fetch. The configured network shell fetched the objects but could not update
`origin/codex/frrie` because retained `origin/codex/frrie/dirty-intake-20260904`
occupies its namespace. No refs were deleted. Exact detached checkout succeeded.
This staging issue is separate from diagnostic runtime and crash causality.

No production correction follows from the native pass. Historical A03 tape-only
failures occurred on the separate3.10 runtime with Torch absent. New CBSC P47
evidence reported through DM shows an Enum/token failure during TRAIN tape
generation before projection/model/trainer; it is a caller location, not a
demonstrated shared cause. Do not duplicate CBSC's exact test.

Next selected P47 discriminator, recorded before invocation: execute FRRIE's
actual `production_training_inputs`64-tape tuple and origin-schedule factory
after importing its experiment module and Torch, with Torch threads1. Use only
existing `TEST_ROOT_HEX`/`TEST_SEED_LABEL`, eight coordinate values1–8, yielding
512 tapes/512 origin rows/1,536 selections. These are input-coordinate values,
not learner updates. No model, optimizer, evaluator or native call is invoked.
Source: new standalone `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/native_crash_repair/test_training_input_factory.py`.
This tests grouping, allocation lifetime and broader imports absent from the
prior paired tape-only loop; it does not recreate full original initialization.

Hypothesis/expected observation: a failure may reproduce in this real grouped
input factory without project-native execution; otherwise retain a512-tape
nonreproduction. Existing128 tapes/3.39s suggests approximately14s generation
plus imports/checks, not a guarantee. One complete120s cap includes admission,
imports, factory calls, checks and JSON. Invocation sum cap120s, no sweep;
aggregate CPU unknown. Separate normal focused-test work remains within300s.
Primary publication is progress counts plus terminal JSON/exit/time/admission.
Same pinned host/interpreter/device/thread environment; fresh handle/cwd
`frrie-p47-input-factory-20260908` and relative output
`temp/directions/finite_resource_relational_inductive_efficiency/exp/p47_input_factory`.
The exact new committed source SHA and full command will accompany its receipts.
No production source or §4 machinery is added.

## Input-factory terminal evidence and technical return

Accepted handle `frrie-p47-input-factory-20260908` used source
`2fa3b1da8a9a9f05af73e2ae03bf8204a1f2cb52` and the prospective runtime above.
Supervisor log starts16:16:34 UTC and records exit1 at16:16:35 UTC; process-time
reports1.58s and383,352KiB peak RSS. Admission at16:16:34.170221 UTC passed with
15,641,108,480 physical/effective available bytes. Root independently reported
failed/exit1/tmux inactive; collection used that same handle, without relaunch.
Complete launch/admission/log/time receipts are retained under the authoring
checkout's `temp/directions/finite_resource_relational_inductive_efficiency/exp/p47_input_factory/`.

Direct exception: `AttributeError: 'NoneType' object has no attribute 'set_num_threads'`
at the diagnostic line18. `policy.require_torch()` validates availability and
returns None, so assigning it to `torch` was a harness defect. Imports completed,
but execution did not reach root conversion or `production_training_inputs`.
Actual counts:0 tapes,0 origin rows,0 models,0 optimizer steps,0 native calls,
0 scientific evaluations. No native crash was observed by this attempt; it
also supplies no input-factory success/failure evidence.

Corrected only the test to `import torch`, matching the original experiment's
thread-setting call pattern. AST parsing and `git diff --check` pass. No runtime
check of the corrected harness has occurred. Root explicitly requested terminal
collection with no relaunch/retry after observing this failure; therefore this
batch stops at that instruction, rather than silently allocating another run.
The exact remaining diagnostic is the same512-tape TEST fixture/grouped factory
with the corrected script at the final commit, fresh detached cwd/output/handle,
same historical interpreter, PYTHONPATH=cwd, thread limits1, adjacent memory
admission and complete120s bound. Existing launch JSON supplies the command
structure, but a new accepted handle is required if that work is selected.
DM/Root owns resolving the explicit no-retry boundary; no learner remainder exists.

Acceptance ceiling: the native fixed-input check is publishable narrow E0
nonreproduction evidence. The factory attempt is publishable E0 harness-failure
evidence only. No shared-runtime cause, production repair, or scientific result
is accepted. Native/semantic production source changed by this batch:0 lines.
New diagnostic test:40 lines before the one-line net correction; no production
review obligation was triggered. No separate high-impact reviewer was used.
Both remote handles are terminal. Measured diagnostic process-wall sum1.91s
(0.33+1.58); individual limits120s each were respected. These invocation times
exclude control-plane reading/Git staging/collection. Aggregate CPU remains
unmeasured. Local checks were AST/diff inspection only; no learning/smoke suite.

Remaining engineering gap is a failing FRRIE case tied to a concrete production
fault or a credible independently checked replacement path. Existing cores and
this passing native fixture do not identify that fault. Do not modify the
interpreter, scientific seeds or production implementation speculatively.
