# CBSC B05 P28 execution evidence

**Technical status: incomplete RAW; dependent STRUCT not invoked.** RAW terminated
by signal 11 (supervisor exit 139) after 39.83 s. Its initial checkpoint and 24
complete update records are retained. Final summary/checkpoint and the paired
primary measurement are absent. No native-return result or missing-pair zero is
substituted. The cause of the signal is not established by this evidence.

## Binding and rule applied

Allocation [P28](../../portfolio/handoffs/2026-09-07-p28-cbsc-b05-pair-execution.md)
was published at `8347aab8b9a5f368a5009bd1b8eb44aba95f78cd` and recorded before
launch in the [B05 card, P28 exact execution allocation](CBSC_OPPORTUNITY_CREDIT_B05_SCIENCE_CARD_20260907.md#p28-exact-execution-allocation--2026-09-07)
at `ece1eb2355a870e839deb425777a1140931e2e07` on `codex/cbsc`.
Accepted P20 DM intake on main: `d24b7b9a27be84ed6e0989327b82777f11e621cb`.

Scientific command source: `d2753be86c12bfa63c404ac2cac513b914371115`.
Separate preflight provenance: `ec8866b3968fcb1566976ce405d7c552d4d9a5de`.
Exact five control-plane blocks were extracted from the
[handoff](CBSC_OPPORTUNITY_CREDIT_B05_ROOT_HANDOFF_20260907.md) at
`87c1f2f01466e8ce0a558fc939b3f774b02af9f2`. Only block 0 (source provisioning),
block 1 (RAW launch) and block 2 (RAW collection) were executed. Blocks 3 and 4
were not executed. Source provisioning printed the exact detached source SHA;
no source changes, readiness suite or new engineering invocation occurred.

Applicable card rule, verbatim:

> A concrete primary, seed/runtime/identity, information/reward/training or pairing
> defect, failed required admission or complete-cap breach stops dependent work;
> retain every trustworthy narrower fact and the failed/missing arm. Do not fill a
> missing pair with zero.

RAW's failed terminal and missing final primary output stop the dependent STRUCT
under this rule. Its score did not select that stop: no final score is available.
The card's incomplete-pair reading applies; DM owns scientific interpretation,
prediction assessment, MEI reading and the next task. P28 authorizes no retry,
extra seed, runtime diagnostic, package acquisition or dependency series.

## Actual execution and terminal observation

Local control cwd: `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`.
Execution node: `wsl_4070` via `hmasd-wsl-node`.
Remote detached cwd:
`/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907`.
Output parent relative to that cwd:
`temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907`.
RAW output is `raw/`; admission is sibling `raw-admission.json`.

The immutable RAW literal ran once through `/usr/local/bin/agent-task`, with
outer GNU time and 598-second TERM / 2-second KILL envelope around the non-login
shell, fresh admission and selected runner. Admission was joined directly to the
runner with `&&`. RAW used `--b05 --arm RAW-GRU --seed 21223` and fresh state.
Selected CPU FP32 / Torch1 and numeric-library limits were unchanged.

| Fact | Observation |
| --- | --- |
| Accepted handle | cbsc-b05-raw-20260907 |
| Supervisor PID | 2766073 |
| Start | Unix 1788848689; 2026-09-08T06:24:49Z |
| Terminal | 2026-09-08T06:25:29Z; failed; exit 139; tmux inactive |
| Actual complete outer wall | 39.83 s |
| Supervisor whole-second duration | 40 s |
| GNU-time peak RSS | 849140 KiB |
| Error text | monitored command dumped core; Command terminated by signal 11 |
| RAW / STRUCT candidate invocations | 1 / 0 |

The accepted handle and identity were promptly sent to Root and DM. CM retained
observation before adoption ACK and observed the same handle terminal; Root also
reported the same failed terminal and directed the existing collection route.
No duplicate launch occurred. Collection-time supervisor uptimes (96/121 s) are
ages at observation, not run wall. The failure occurred below 600 s and was not
a cap-triggered termination. Aggregate CPU and study critical path were not
measured; only the one arm's 39.83 s executed wall is available. No time or
exposure from an unexecuted STRUCT is imputed.

Fresh `/proc/meminfo` admission was captured at 2026-09-08T06:24:49.695772Z and
assessed at 06:24:49.696034Z. Physical/effective available memory both
15647051776 bytes exceeded the 4294967296-byte floor; `passed=true`. Admission
is distinct from the observed GNU-time RSS and does not identify the crash cause.

## Retained exposure and missing primary measurement

The collected `updates.jsonl` is 796885 bytes and contains 24 complete JSON rows,
updates 0..23, each with 16 loss records. The last durable record covers TRAIN
IDs 184..191, with these counters:

| Quantity | Last durable RAW count | Planned full RAW |
| --- | ---: | ---: |
| Rollout updates | 24 | 48 |
| Adam steps | 384 | 768 |
| Training episodes | 192 | 384 |
| Training transitions | 29184 | 58368 |
| Training decisions | 4608 | 9216 |

Recorded sampled action totals over these rows: REFRESH 4285, SERVE 189 and
SAFE_FALLBACK 134 (4608 total). These are partial training counts, not endpoint
performance. The last loss reports optimizer step 384. Work completed after that
last durable row is unknown; these counts are not an exact reconstruction of
all work at process death.

`update-0.pt` is retained at 1478489 bytes. By the unchanged runner's ordering,
reaching this checkpoint and subsequent update rows entails the initial 32-episode
evaluation and RAW rule-panel construction. Their return records were not separately
published before the summary stage, so no initial/native rule score is supplied
from reconstruction. No final update-48 evaluation completion is established.
The 64 planned evaluation executions cannot be reported as completed.

A local stdlib ZIP/pickle-opcode inspection of the retained initial checkpoint,
without unpickling, importing Torch or executing a target-runtime probe, observes:
B05 object, RAW-GRU, seed 21223, namespace `CBSC-OMRC-B1-THREE-SEED-SCOUT`,
source SHA `d2753be86c12bfa63c404ac2cac513b914371115`, lexical interpreter
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`,
Python `3.12.3 (main, Jul 15 2026, 23:46:41) [GCC 13.3.0]`, and Torch
`2.7.0+cu118`. This records actual initial artifact identity; it does not establish
final acceptance or interpreter reliability. P17 remains the existing package
metadata evidence. The failed attempt does not identify a historical failure cause.

Missing: RAW `summary.json`, `update-48.pt`, final parameter displacement/native
returns, every STRUCT artifact, and `paired_summary.json` with its 32 signed
endpoint differences. There is no accepted paired performance result, endpoint
REQUEST_ONLY comparison or final displacement result. Old B04 RAW remains separate.

## Collection and evidence locations

Exact block 2 returned zero for status, logs and both scp operations, retaining
both the output tree and supervisor directory. Status/log stderr files are empty.
No extra evaluator, pair reconstruction, target import, readiness/probe, learner
or remote diagnostic was used. Local JSON/opcode reading only summarizes recorded
bytes and does not supply missing results.

Local control receipts and immutable extracted blocks:
`temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907_control/`
(`block_0.py` through `block_4.py`, execution logs for 0/1/2 and accepted identity
receipts). Local complete collection:
`temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907_collection/raw/`.
It contains `status.txt`, `logs.txt`, the copied `cbsc-b05-raw-20260907/` supervisor
records, copied `opportunity_credit_b05_20260907/` output/admission, and compact
`collection_facts.json` with inventory/counts/static checkpoint identity.

Remote evidence remains in the declared output root and
`/home/wu/.agent-tasks/cbsc-b05-raw-20260907/` (`runner.sh`, start_time, pid,
status, exit_code and task.log). No evidence tree was removed or rewritten.
Source staging and collection succeeded; the observed failure belongs to the
accepted RAW process. No further root-cause location is established.

Technical collection is complete. Root integrates this explicit evidence commit;
DM owns intake/brief/audit and any subsequent task request. The unused dependent
STRUCT allocation is not a standalone retry allowance.
