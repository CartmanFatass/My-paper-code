# ACVC fresh DENSE reuse B01 — engineering and execution

Date: 2026-09-10. **One run completed and technically accepted; scientific intake and scoped remote closeout complete. Monitor cost-accounting deviation retained.**

## Authority and owned work

[Portfolio allocation/conformance](../../portfolio/decisions/2026-09-10-acvc-fresh-dense-allocation.md)
and [execution mapping](../../portfolio/pro_packets/20260910_acvc_fresh_dense_allocation/EXECUTION_MAPPING.md)
are published at `cc3569d3f0a17f2df6a12c4a05ca008850944376`.
Root accepted/integrated the application as main1e5ab4dab and assigned the complete batch.
Card§§2–5 and allocation§8 govern the scientific semantics and one-study limit.

DM owns engineering acceptance, Git, exact execution, collection and separate scientific
intake in `C:/Projects/HMASD-worktrees/codex-acvc`, branch `codex/acvc`.
Optional Implementer `im_sm_acvc_fresh_dense_b01` owns only the new Python runner and
one focused synthetic test. It has zero runtime/model/test/launch authority and no Git
or child delegation. The DM owns the small adjacent shell wrapper and this record.
Independent high-risk review will inspect the actual changed initialization, optimizer,
RNG/recurrent/command state, checkpoint and primary publication boundaries.

New source is `scripts/run_acvc_fresh_dense_reuse_b01.py` and its small `.sh` invocation;
new check is
`tests/experiments/candidates/acvc/native_link_loss_b01/test_fresh_dense_b01.py`.
Existing learner/policy/environment, MGTAP geometry, ACVC Binding/model/collector/report
remain read-only reuse. Engineering-scope§4 additions: **none**. Existing2000-line
attempt/600-line runner budgets remain. No scientific meaning is delegated to the Implementer.

## One complete cost boundary

The one allocation is whole supervised task≤330s, cumulative runtime support≤30s,
complete charge≤360s. The scientific task includes its actual-node memory admission,
imports/initialization,512 training episodes/1024 Adam calls, all three64-episode final
panels, checkpoint/publication and actual descendant exit. Support includes every required
runtime check, collection/readback and numerical reduction; it is charged once and never
reset by a correction. Reading, authoring, Git and review deliberation are outside that
runtime bill and are not represented as measured end-to-end engineering cost.

Existing accepted focused checks in this research directory are14.2369735s(P78),
5.4396806s(P79) and4.35s(E01), total24.0266541s. Sources are the two native-link-loss
intakes and E01 TECHNICAL_COLLECTION. Even charging all new30s support as tests would
give54.0266541s under300s; this is arithmetic over prior receipts, not new checking.
The new study still has only30s support, including later readback.

The outer existing `/usr/bin/time` and `timeout` command will enclose the admission
plus runner shell, not start after admission. Planned outer TERM deadline327s with
kill-after1s reserves two seconds of the330s limit for supervisor startup/exit accounting;
the runner's320s internal allowance leaves publication time before the outer deadline.
These are stricter implementation stop points within the same cap, not new allowances.
The actual complete charge must cover the supervisor start/end boundary conservatively;
fractional command wall and final supervisor wall are reported separately. Any measured
cap breach is retained. No timing probe or uncharged verification phase is selected.

Current measured DM runtime support: **8.0564878s**. Current scientific accepted invocations: **1**, complete.
Before submission no model, RNG master, native episode, learner update or evaluation
had been created by this engineering assignment. Actual exposure awaits collection.

## Exact execution inputs

Node is `wsl_4070` / `hmasd-wsl-node`, repository `/home/wu/projects/HMASD`,
interpreter `/home/wu/.venvs/hmasd/bin/python`, CPU FP32 and Torch intra/inter-op1/1.
After the source is committed/pushed, use one detached exact-SHA checkout under
`/home/wu/hmasd-worktrees/`. Existing supervisor is `/usr/local/bin/agent-task`.

The planned scientific output is
`temp/directions/acvc/exp/fresh_dense_reuse_b01_8921_20260910` inside that checkout.
The adjacent admission receipt and whole-command timing file use the direction's temp
parent; no scientific output root is created before admission. The shell joins fresh
destination-node `admit-memory` and the fixed runner with `&&`, requiring physical
and effective availability≥4GiB. Published source, literal command, actual handle and
receipts will be recorded below before/after their real acceptance, not inferred here.

Monitor endpoint is read from the live primary control
`C:/Projects/HMASD/.codex/hmasd-monitor.toml`; currently
`01a087e5-2044-7301-abb6-7a1709a98197`.
After accepted submission, DM directly sends MONITOR_ADD for that same handle and
records adoption pending until Root forwards confirmation. Monitor owns observation;
DM retains collection/technical/scientific intake. An uncertain receipt is reconciled
against its original identity; no second scientific invocation follows.

Stop at complete all-outcome intake or bounded failure. No retry, slice, replacement,
extra panel, dropped panel, tuning, retained-base substitution or successor is allocated.
ACVC's second-recast lowest contention priority and learned T/G end remain unchanged.

## Published candidate and independent review

Candidate080f4502cd6116b96fa3d87cf9ff3b6e4e109f89 was committed/pushed before any
remote verification. Its source has412 new non-test lines:403-line Python runner and
9-line shell; the focused test has195 lines. Protected dependencies are unchanged.
The Implementer returned zero runtime/import/model/test/launch/Git work. DM inspected
the changed orchestration, CLI, output/count schema, test and unchanged dependency diff.

Independent read-only Reviewer `rv_ah_acvc_fresh_dense_b01` found the normal path
conforming on initialization/draw order, optimizer and objective, replay, checkpoint,
fixed-rule state/command ownership and paired primary reading. It identified two P2
partial-failure defects: the computation alarm remains armed during final publication,
and an interrupted four-epoch helper call can have more backward/replay work than the
completed Adam count while returning no partial epoch records. No added prohibited
machinery or source/runner-budget breach was found. No runtime verification was performed.

DM returned both defects to the same Implementer. The selected remedy is to disarm the
inner alarm on entering finalization while retaining the outer task timeout, and to
report completed-Adam lower bounds plus explicitly unavailable interrupted-update work
and records. Healthy complete-run counts remain unchanged. Alternatives were changing
the protected helper for per-epoch publication or accepting inaccurate exact partial
counts. The first expands an unnecessary shared-code surface; the second is rejected.
**Owner-delegated decision (unattended,2026-09-03 instruction): explicit lower bounds
and unavailable partial quantities.** This follows empirical§11.8.7 and the card's
trustworthy-partial-facts clause; no performance polarity or scientific recipe changes.
The same Reviewer inspected the precise correction and resolved both material findings;
no new material issue remains. The changed runner has432 lines plus the9-line shell
(441 non-test lines total), with266 test lines. The same focused synthetic test now
checks disarmed-alarm ordering and a mocked two-Adam interrupted update. DM checked the
actual correction diff. The four-epoch helper and all protected scientific paths remain
unchanged. Real gradients, native checkpoint loading and timing remain facts for the
one actual study; no separate native pilot is required or allocated. Focused runtime
verification is next; the candidate is independently source-reviewed, not launched.

## Focused verification and source acceptance

Final source **60d42dd739ef125a505772f2b1d698b099b43a16** is independently reviewed and now technically accepted
for its exact one-study execution. No scientific result has yet been accepted.
The remote detached checkout is `/home/wu/hmasd-worktrees/acvc-fresh-dense-b01-60d42dd73`; its HEAD and clean initial status were
read directly after creation. Required missing blobs were hydrated through the configured
`zsh -lic` network shell with the configured sparse source directories. An old
`origin/codex/acvc/next-object-20260904` tracking ref prevented writing the new parent
tracking-ref name, but the exact published commit was fetched and used directly. No old
ref was deleted or rewritten. The first non-network-shell fetch/hydration stalled;
only their verified owned process groups were stopped, and Git removed its unfinished
checkout. The subsequent exact-SHA sparse checkout completed. These were Git preparation,
not scientific attempts or runtime tests; their wall is outside the allocated runtime bill.

One focused test target, under the source above:
`tests/experiments/candidates/acvc/native_link_loss_b01/test_fresh_dense_b01.py::test_fresh_dense_orchestration_counts_and_publication`.
The enclosing check also ran `bash -n scripts/run_acvc_fresh_dense_reuse_b01.sh`.
Both used the configured remote Python, disabled bytecode/cache, and explicit owned temp
paths. No real model, native environment or learning/evaluation panel was executed by the
synthetic check. Its complete, evaluation-failure and two-Adam interrupted-update cases
exercise the changed orchestration/primary publication and alarm ordering.

| Check invocation | Observation | Remote process wall | Charged client wall including SSH/readback/cleanup |
|---|---|---:|---:|
| first | Fixture setup error: missing parent of pytest basetemp; test body did not run |1.61s|2.3801562s|
| second, after creating the exact test parent | **1 passed**, pytest0.72s; shell syntax passed |0.95s|1.3373995s|

Both owned scratch directories are directly confirmed absent after creator cleanup.
Failure and success logs/time files remain separately under the checkout's
`temp/directions/acvc/fresh_dense_b01_support_check{,_02}{.log,_time.txt}`.
No test failure or charged time is discarded. New support used is **3.7175557s**;
**26.2824443s** remains for collection/readback and numerical intake. Conservatively
charging both client walls to the existing directory test total gives27.7442098s/300s.
No further source change or repeated check is needed absent a new concrete defect.

## Frozen single submission

Source SHA: `60d42dd739ef125a505772f2b1d698b099b43a16`. Node/interpreter/device/thread boundary remains above.
Supervisor handle: `acvc-fresh-dense-b01-8921-60d42dd73`. One submission was accepted below.
Scientific output and admission/timing paths remain those named above. The exact command
passed as one `agent-task run` payload is:

```bash
cd /home/wu/hmasd-worktrees/acvc-fresh-dense-b01-60d42dd73 && export HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= && /usr/bin/time -f 'whole_command_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x' -o temp/directions/acvc/fresh_dense_reuse_b01_8921_task_time.txt timeout --signal=TERM --kill-after=1 327 bash scripts/run_acvc_fresh_dense_reuse_b01.sh 60d42dd739ef125a505772f2b1d698b099b43a16
```

The shell's admission and runner remain joined by&&; the whole outer timer includes
admission/startup and subsequent publication/exit. The supervisor's own start/end/exit
witness will supply the wider task boundary; a conservative charge includes timestamp
rounding and its final short exit delay. The actual330s task and30s support sublimits
remain independent. No admission receipt or launch handle is inferred from source acceptance.

At this clean boundary the primary owner's review directory still contains only the
previously handled September4–5 reviews. The ACVC instruction at
`reviews/2026-09-05.md:19` remains continue at lowest sequencing priority; no new
review or owner override changes this allocated batch. Source acceptance and the
partial-record correction are recorded in the September10 audit ledger.

## Accepted submission and observation handover

The one supervisor submission started at `2026-09-10T18:37:58.6419883Z` and
returned exit0 in0.6461753s client wall. Direct receipt:

> Task 'acvc-fresh-dense-b01-8921-60d42dd73' started in tmux session 'agent_acvc-fresh-dense-b01-8921-60d42dd73'.

Its log is `/home/wu/.agent-tasks/acvc-fresh-dense-b01-8921-60d42dd73/task.log`.
This is process acceptance, not admission success or completed scientific evidence.
The exact source and command are unchanged from the published pre-submission record309c5b1a5.
The submit-client interval is retained for conservative wider task charging at intake.

DM directly sent MONITOR_ADD to the live primary-configured monitor task
`01a087e5-2044-7301-abb6-7a1709a98197`; the app accepted the message.
Root subsequently forwarded **actual monitor adoption confirmed** for the exact
handle/source/cwd/root on wsl_4070, with the independent monitor goal active. Root is
`01a07249-b095-7821-8ce2-e9c32ba85267`, original native execution/science owner
`/root/dm_acvc_p68_reentry` (source task01a08447-a33c-7881-8c2a-a6e7e918b2a7).
DM has no parallel polling loop and retains collection, engineering acceptance and
separate scientific intake. There is no second submission, retry or successor.

## Terminal collection and engineering acceptance

Root forwarded the adopted monitor's terminal receipt, directly observed at
`2026-09-10T18:40:50.1426335Z`: finished, exit0, tmux inactive, remote start
`2026-09-11T02:37:57+08:00`, remote exit `2026-09-11T02:40:46+08:00`, integer
supervisor duration169s. The full direct witness and supervisor files are preserved in
[fresh_dense_reuse_b01_20260910](fresh_dense_reuse_b01_20260910/).

The allocated endpoint completed:512 training episodes,256 rollouts,1024 finite update
records/Adam calls, one final checkpoint and192 final evaluation rows. All704 raw rows,
reset keys, update rollout/epoch keys and finite S=256J values were checked. Independent
finite reduction from the raw rows matched all paired vectors, means, conditional SEs,
reading-rule labels and intervention totals. Actual nonzero actor/critic movements are
published in the summary. No partial-update or publication limit occurred.

The actual-node admission passed both4GiB floors with15633838080 bytes available;
its source is/proc/meminfo and cgroup headroom was unmeasured. The outer timer reports
168.37s admission-through-command-exit and555852KiB peak RSS. Runner-to-summary is
157.50844278297154s and is not substituted for the whole task. The wider conservative
supervisor charge is172s, including timestamp granularity, its final one-second sleep
and the full0.6461753s submit-client interval. Aggregate CPU work remains unmeasured.

The [collection receipt](ACVC_FRESH_DENSE_REUSE_B01_COLLECTION_20260910.json) records
all charged support calls and preservation state. The complete local tar archive hash
matches the remote441de0bda690b1d99c2cfc653c2cd3c088f4bb434062117df755db18942c16a4.
All16 native/support/supervisor files are inventoried; the final282957-byte checkpoint
is retained in the archive and extracted runtime root. Every other file is also copied
into the durable result folder. No retry, extra test/panel, replacement or model loading
occurred during collection. Scientific interpretation is in the separate intake.

## Scoped closeout and final accounting limitation

Raw evidence was committed/pushed at809ecf104, followed by otherwise ignored supervisor
and check logs at236dc02fa. All16 captured files, including the final checkpoint, are in
the verified local collection archive; every noncheckpoint file also has a durable copy.
After confirming terminal state, no live tmux session, exact source and no tracked change,
only the owned remote execution checkout and supervisor root were removed. The cleanup
receipt directly confirms both paths absent and no Git worktree registration, at remote
2026-09-11T02:50:53+08:00. Cleanup/readback tool wall1.3301567s is included in DM support.
The shared local authoring checkout and local scientific archive remain for Root.

The final known native-task-plus-DM subtotal is180.0564878s:172s conservative whole task
and8.0564878s measured DM runtime support. Independent Monitor bookkeeping subsequently
returned retained tool-wall parts30.2s+14.14s for its terminal query, with other approximate
status/log/delivery costs and an unavailable exact aggregate. Root confirmed a separate
retained lower bound>44.34s; no observation was rerun. Do not silently add it to or exclude
it from either existing boundary. Complete≤360s and support≤30s conformance is unestablished
if Monitor observation is included; its lower bound alone is above30s. This is an explicit
budget/accounting deviation, with intact native scientific counts/results. No new local
allocation, successor or scientific polarity follows. The collection receipt and
[intake](ACVC_FRESH_DENSE_REUSE_B01_INTAKE_20260910.md) return the same-Portfolio-node
consequence to Root while completing this assignment's numerical work and cleanup.
