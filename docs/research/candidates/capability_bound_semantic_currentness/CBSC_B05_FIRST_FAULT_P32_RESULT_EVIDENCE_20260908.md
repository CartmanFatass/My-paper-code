# CBSC B05 first-fault P32 execution evidence

**Location-bearing fatal context collected.** The single P32 process terminated
with signal11/exit139 after15.25s. Its fatal Python report locates the active RAW
adapter call path during initial evaluation-panel projection. No training update,
checkpoint, evaluation result or summary was published. This establishes reported
operation context only; the corrupting writer and historical cause remain unknown.

## Binding and executed scope

[P32 card](CBSC_B05_FIRST_FAULT_P32_SCIENCE_CARD_20260908.md) and
[Root handoff](CBSC_B05_FIRST_FAULT_P32_ROOT_HANDOFF_20260908.md), committed at
`67222c4434e796cdedde44b277d7097959087186`, bind the one observation under Portfolio
assignment `0c6bf8e175632098e46fcff1417d5d3c078962c9`. Root launched and observed;
Root also executed the exact terminal collection block, reporting zero return
codes for status/log retrieval and both copied roots. CM inspected those retained
bytes without repeating collection or invoking the target.

Scientific source: `d2753be86c12bfa63c404ac2cac513b914371115`; separate preflight
provenance `ec8866b3968fcb1566976ce405d7c552d4d9a5de`. Existing remote cwd:
`/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907`, node wsl_4070.
Copied supervisor `runner.sh` contains the declared outer GNU time, TERM115/KILL5,
non-login shell, adjacent admission `&&` runner, selected numeric-library thread
limits, and lexical interpreter
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`
with `-X faulthandler` before the script. Arguments remain
`--b05 --arm RAW-GRU --seed 21223` with fresh P32 `raw/` output. No checkpoint
resume, source edit, alternative runtime, package operation or additional probe.
The P17/P28 runtime observations are reused; this run published no version summary.

## Terminal, admission and cap

| Field | Collected fact |
| --- | --- |
| Handle | cbsc-b05-first-fault-p32-20260908 |
| Supervisor PID | 2766935 |
| Start / end UTC | 2026-09-08T07:28:36Z / 07:28:52Z |
| Terminal | failed; exit139; tmux inactive |
| Fatal report | Fatal Python error: Segmentation fault; signal11 |
| Complete outer wall | 15.25s |
| Supervisor rounded duration | 16s |
| GNU-time peak RSS | 799632KiB |
| Candidate invocations | 1; no STRUCT |

Actual wall is below the120s complete cap; this was a fatal event rather than a
timeout-cap termination. Collection-time uptime117s is not run wall. Aggregate
CPU was not measured. Memory admission from `/proc/meminfo` was captured at
07:28:36.833001Z and assessed at07:28:36.833284Z: physical/effective available
15646052352bytes, floor4294967296bytes, `passed=true`. Admission and peak RSS are
distinct observations and do not establish a cause.

## First reported fatal call path

Both2858-byte copies (`logs.txt` and copied supervisor `task.log`) are byte-identical
and contain one fatal report. Most-recent frame first, under the bound cwd:

| Repository-relative file | Line | Reported function |
| --- | ---: | --- |
| experiments/candidates/capability_bound_semantic_currentness/omrc_b01/adapters.py |128|process|
| experiments/candidates/capability_bound_semantic_currentness/omrc_b01/adapters.py |93|`<genexpr>`|
| experiments/candidates/capability_bound_semantic_currentness/omrc_b01/adapters.py |93|replay|
| experiments/candidates/capability_bound_semantic_currentness/omrc_b01/engine.py |89|build_observations|
| experiments/candidates/capability_bound_semantic_currentness/omrc_b01/engine.py |108|_project_panel|
| experiments/candidates/capability_bound_semantic_currentness/opportunity_credit_b04/run.py |132|run_arm|
| scripts/run_cbsc_opportunity_credit_b04.py |56|main|
| scripts/run_cbsc_opportunity_credit_b04.py |63|`<module>`|

Local read-only `git show` of the bound source connects adapters.py128 to
`for value in appended:` in `RawHistoryAdapter.process`; engine.py108 is the
second `build_observations` call used for replay comparison; run.py132 projects
the initial evaluation tapes. The exact tape/opportunity/token index is absent.
The log also lists24 extension modules, but that list identifies no responsible
module. These frames are an active Python call path, not a native C backtrace,
faulting memory access attribution or proof that the displayed source line caused
corruption. No additional runtime inspection or diagnostic was performed.

## Durable work and missing observations

Copied P32 output parent contains only the504-byte admission receipt and an empty
`raw/` directory. There is no `updates.jsonl`, checkpoint or `summary.json`.
Durable update rows:0. Source ordering at run.py132 places the reported fatal event
before the training loop, policy evaluation and three RAW rule panels. Therefore
no rollout update/Adam step, sampled training episode/transition, policy evaluation
execution or fixed-rule score had been reached in this execution (counts0 by
source-flow inference, not a serialized terminal counter).

The same source ordering shows construction of the384 TRAIN and32 EVAL tapes,
action-uniform bookkeeping and model/trainer initialization before this call.
Tape construction is not learner interaction; model initialization is not an
optimizer update. Partial adapter projection work occurred, but completed tape or
token counts are unavailable. The scheduled48 rollouts/768Adam/384 training
episodes/64 evaluations are ceilings and are not reported as completed exposure.
No parameter displacement, native return, rule comparison or endpoint publication
is available. No pair was requested or reconstructed.

## Reading applied and retained evidence

Card reading, verbatim:

> A location-bearing fatal stack supports only the active reported call path in
> this execution; it does not identify the corrupting writer or historical cause.
> A fatal event without a usable stack, a timeout or nonreproduction leaves the
> missing context unresolved and never clears P28 or authorizes a retry.
> A complete normal RAW output receives a separate validity review as diagnostic
> execution evidence; it does not replace P28 RAW or form its absent pair.
> Every outcome ends this allocation. Retain terminal facts and durable work;
> no repair, extra probe, STRUCT, new seed, repeat or extension follows.

The collected frame locations provide the requested technical observable beyond
P28's signal-only record. DM owns prediction/technical-MEI intake and any later
bounded task selection. P28 remains INCOMPLETE_RAW with24 durable updates and no
pair; P32 does not replace it, repair it or transfer causes/exposure to FRRIE.

Local collection in `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`:
`temp/directions/capability_bound_semantic_currentness/exp/b05_first_fault_p32_20260908_collection/`.
It retains status/logs (empty retrieval stderr), copied
`cbsc-b05-first-fault-p32-20260908/` supervisor records including literal runner,
output/admission tree `b05_first_fault_p32_20260908/`, and CM's compact
`collection_facts.json` from local JSON/log/directory reads. The full fatal-report
path is the copied supervisor `task.log`; no separate core path is claimed.
Remote originals remain under the same cwd's declared P32 output parent and
`/home/wu/.agent-tasks/cbsc-b05-first-fault-p32-20260908/`.

Technical collection is complete. No retry, source repair or further invocation
was made. Root integrates this explicit evidence commit; DM owns intake, brief,
audit and the next concrete task need.
