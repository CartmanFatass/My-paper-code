# ACVC fresh DENSE reuse B01 — engineering and execution

Date: 2026-09-10. **Source accepted; the single scientific submission is next.**

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

Current new support used: **3.7175557s**. Current scientific accepted invocations: **0**.
No model, RNG master, native episode, learner update or evaluation has been created by
this engineering assignment.

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
Supervisor handle: `acvc-fresh-dense-b01-8921-60d42dd73`. One submission is selected, not yet accepted.
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
