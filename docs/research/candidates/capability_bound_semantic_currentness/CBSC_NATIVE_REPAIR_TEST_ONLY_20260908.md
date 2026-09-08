# CBSC native crash repair: TEST_ONLY adapter isolation

The owner-directed repair investigation built and executed a non-learning adapter
replay. **PASS / historical crash not reproduced; root cause unresolved.** There
is no evidenced production repair or before/after production comparison. P28,
P32 and P36 artifacts and their conclusions are preserved.

## Delivered change and bounded question

Root's new repair assignment under `解决原生崩溃问题` superseded the old P36
preparation-only stop for this engineering task. It requested a compact TEST_ONLY
adapter replay from P32 `adapters.py:128`, byte/assertion checks within120s, then
an evidenced semantics-preserving repair or a current concrete blocker. It did
not authorize a study resumption, scientific arms/seeds, security changes,
replacement client or children. None occurred.

Authoring checkout: `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`, branch
`codex/cbsc`, initially clean at `01ef63b1ce2fbecaeb4810ed925c6c4764db0066`.
Test commit `61f3243cfe5d01079f0a01c7f0d29a13889773eb` was pushed before execution.
The109-line addition is
`tests/experiments/candidates/capability_bound_semantic_currentness/omrc_b01/test_raw_native_replay.py`.
No production path changed and no scope-spec §4 machinery was added. Main's
comparison record confirms all three temporary CM comparison batches completed.

Inspection traced immutable `PrimitiveToken` -> literal codec/masks ->
`RawHistoryAdapter`'s episode-local four-element Python list -> immutable emitted
bytes -> NumPy FP32 rows -> `torch.from_numpy` -> repeated projection and stack.
Each projection constructs a fresh adapter. Line128 is the Python iteration over
selected bytes; its loop body updates the list by slice assignment. This source
contains no explicit unsafe memory access or foreign pointer operation. That is
not proof that the runtime or an earlier operation could not corrupt memory.
`adapters.py`, `token.py` and `engine.py` have no diff from P32's `d2753be86...`.

The fixture has152 synthetic, codec-valid public tokens covering all14 event
kinds, flag/no-flag appends and active/no-op opportunities. It uses no host RNG,
research seed, model, optimizer, evaluator or reward. It is an adapter input
fixture, not a simulation of host chronology. An independent append-only bytes
reference with pinned literal masks checks every emitted FIFO byte, per-token
work and final state. It checks32 fresh direct replays, then32 doubled replays
through the actual `_project_panel`, all168 FP32 channels against Python bit
extraction, and input immutability. These cover14,592 adapter process calls.

## Execution and retained evidence

One accepted handle: `cbsc-test-only-native-replay-20260908`, PID2773952,
node `wsl_4070`, exact-SHA detached cwd
`/home/wu/hmasd-worktrees/cbsc-test-only-native-replay-20260908`.
Interpreter remained the P32 lexical path:
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`.
Observed Python3.12.3, Torch2.7.0+cu118, Torch threads1, CPU FP32.

The frozen literal and argv are in `launch.json` under the retained local root
`temp/directions/capability_bound_semantic_currentness/test/native_replay_20260908_control/`.
It uses existing `agent-task`, outer GNU time, TERM115s/KILL5s, existing numeric
library thread limits, a non-login inner shell, adjacent memory admission `&&`
and `exec python -X faulthandler <test>`. No debugger or inferior is involved.
The stop is the first assertion/fatal failure, normal completion or the120s cap.

Cost recorded before launch: one TEST_ONLY process with32x152 direct and
32x2x152 projected adapter calls; measured time initially unknown, complete cap120s.
There are no scientific arms to project. Post-learner coverage is inapplicable:
the primary output is assertion completion and flushed PASS lines in task.log.

Admission passed at2026-09-08T14:20:43.980169Z: physical/effective available
15,644,688,384bytes against4,294,967,296bytes. Terminal exit0, inactive tmux,
start14:20:43Z/end14:20:45Z. Complete GNU-time wall2.02s and peak RSS385,748KiB.
Both direct replay and projection PASS lines were inspected. Aggregate CPU is
unmeasured. Copies of supervisor records and admission, plus status/logs and
the launch literal, are retained under the local root above. Collection exits0.
Local AST/path checks and `git diff --check` also passed; no repeated suite ran.

Source staging initially stalled in an unconfigured fetch shell. The owned
stalled process chain was terminated and checked absent. Configured `zsh -lic`
then fetched bytes, but updating `origin/codex/cbsc` encountered the existing
`origin/codex/cbsc/defect8-20260904` ref namespace. The fetched exact commit was
present, and its detached checkout completed using that configured network shell,
without deleting refs. No duplicate test launch followed staging. A local bundle
creation attempt failed before any transfer; no bundle was used.

## Remaining concrete gap and owner

The isolated adapter/projection path did not reproduce signal11 or a byte
mismatch on the implicated interpreter. The test omits P32's preceding tape
generation, model/optimizer initialization and their allocation/import order;
it also does not recover P32's missing faulting tape/token index. Therefore it
cannot identify a corrupting writer or distinguish an input-specific fault from
an earlier runtime-state failure. A speculative FIFO rewrite would lack causal
evidence and would not establish a crash repair.

Return this current reproduction gap to Root/DM for the next bounded diagnostic
scope if continuing the repair. No scientific result, safety clearance of the
old run, production repair or study resumption is claimed.
