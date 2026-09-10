# FOLR public lifecycle HALF-B01 technical evidence

Current state: RETAIN complete and technically accepted; HALF_EVENT remains preselected and unsubmitted. Earlier preparation boundaries remain chronological evidence.

## 1. Fixed comparison and changed implementation

[Card §§2–6](FOLR_PUBLIC_LIFECYCLE_HALF_B01_SCIENCE_CARD_20260910.md#2-exact-treatment-and-preserved-learner-semantics)
fixes RETAIN and HALF_EVENT at training7807 / evaluation107807. Each arm gets5000
complete training episodes,100000 ticks,4969 RMSprop updates and128 final greedy
episodes/2560 ticks. Only the new complete pair reads `d_HR=J_HALF_EVENT-J_RETAIN`:
`d_HR>=1` → HALF_EVENT_ABOVE_MEI; `d_HR<=-1` → RETAIN_ABOVE_MEI; otherwise WITHIN_MEI.
Prospective forecast is WITHIN_MEI, low confidence; no prediction can yet be scored.

Against ade8a1c7fe92fb420c981e15148ee7166047b122 the non-test diff adds15/deletes4
lines in the existing model, environment, collection and runner. After common carry
masking, HALF_EVENT multiplies incoming state by .5 exactly for continuation & event
before GRU processing. The actor is reused by acting and online/target replay. Native
transition/reward/information, learner, attention and mixer code are unchanged.
The runner accepts the new arm and publishes the separately named attenuation totals;
`half_primary` expresses the fixed complete-pair rule. Old arm operations and default
seed labels stay unchanged; every actual command must pass7807/107807 explicitly.

The named research modules plus runner contain796 lines; runner108. The changed
non-test surface is15 added/4 removed lines, with tests57 added/8 removed separately.
Only the single attenuation aggregate named by card §6 is added under Scope §4.
No new dependency, concurrency, guard, profiler, framework or search is present.
No §5 budget breach was identified. The unchanged scientific card §§2–5 were compared
to their published UTF-8 text. An initial comparison used the Windows default decode
and failed; explicit UTF-8 readback passed. It did not change source or scientific bytes.

## 2. Focused checks and independent semantic review

The bounded implementation executor ran the existing mapped boundary file with
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider
--basetemp <owned scratch> tests/experiments/candidates/vap_folr_core/public_lifecycle_b01/test_boundaries.py`.
Direct output was **26 passed in5.24s**. The enclosing subprocess and cleanup took
**6.578s**. Its TemporaryDirectory was
`temp/directions/vap_folr_core/test/half_b01_check_r68ib396`, under the owned test parent;
the creating process removed it and DM confirmed absence. Older scratch was untouched.

The checks cover signed incoming state and gradient, before-GRU placement, non-event /
entrant / terminal handling, sequential acting/full-replay parity, real learner target
and update/checkpoint behavior, separate attenuation/reset counts, explicit seeds and
128-evaluation routing with stand-ins, no private mask stream for the selected arms,
phase publication and inclusive rule boundaries. These are technical fixtures, not
the new scientific fits. No DM or reviewer reran the suite.

Independent Astra/high reviewer `rev_ah_folr_timing_b02_rng` returned **no material
finding; no repair suggested** after inspecting the diff and reachable dependencies.
It confirmed incoming derivatives0/.5/1 for non-survivor/event-survivor/other-survivor,
FP32/autograd and caller-owned hidden-state preservation, unchanged legacy operations,
and online/target reconstruction through each actor's law. Fixed-length nonterminal
post-transition opportunities correspond to subsequent attenuation applications;
terminal-only controls are excluded. Collection and both result phases propagate the
new total. Review used three read-only commands,2.7044562s summed command wall, no
test/probe/scientific invocation. Full review elapsed is unmeasured.

DM inspected the actual source diff, focused-check output, count mapping, card
preservation and scratch absence and accepts this implementation under evidence
§§11.4,11.8.6–8 and Scope §§4–5/7.3. Technical correctness does not establish useful
memory preservation, native return benefit or a policy intermediate between old arms.
Complete remote runtime, primary publication and wall/CPU remain unobserved.

## 3. Support accounting and current execution boundary

Carried directory tests25.9131638s plus the new6.578s give **32.4911638s** cumulative
directory tests. Scoped support is currently **40.7574900/300s**: those tests, reviewer
2.7044562s, DM diff check.1461988s, both preservation checks.2677569/.1479143s, and a
conservative5s allowance for uninstrumented preparatory source/procedure reads. Ordinary
authoring/Git administration and full end-to-end engineering elapsed are not measured
compute. Later scoped checks, source staging, collection and closeout are added here.

The card allocates exactly RETAIN then HALF_EVENT,1800s complete chain per arm /3600s
pair, both preselected regardless of RETAIN score. No retry, replacement, third arm,
coefficient/seed search or evaluation top-up is included. Portable execution uses the
configured hmasd-wsl-node, exact published source in a detached worktree, CPU FP32 /
Torch1/1, fresh destination memory admission adjacent to each runner in one outer
time/timeout command. No local fallback or model/environment cost pilot is selected.

The initial full-CM handoff was corrected before mutation in the
[Convergence intake](FOLR_PUBLIC_LIFECYCLE_TIMING_FAMILY_CONVERGENCE_INTAKE_20260910.md#operational-ownership-correction-before-implementation).
Under current consolidation this DM owns review disposition, Git/publication, launch,
collection and technical/scientific acceptance. After actual acceptance it dispatches
MONITOR_ADD using the live-primary endpoint; registration and adoption remain separate.
Root owns integration and final execution closure. No scientific handle is yet accepted.

## 4. Decisions this technical acceptance produces

Options: (a) accept the bounded source/check result and publish for the already selected
two-arm allocation; (b) return a concrete source/measurement defect; (c) add an unrequested
diagnostic or repeat checks. Recommend/select **(a)**: no material defect was found and
the changed behavior and primary output have focused coverage. **Owner-delegated decision
(unattended, 2026-09-03 instruction): (a).** This accepts implementation; no performance
result, new allocation or family/Portfolio disposition follows. Live-primary unapplied
owner reviews were `[]`; no owner takeover or prediction was inferred.

Next: publish the full source SHA and exact commands, stage the committed source,
execute the first preselected arm and hand accepted observation to the existing Monitor.

## 5. Published source, transport and exact prepared commands

Accepted source is **c6be208cd514b5d12fb13c7637e2d6376de11eb6**, committed and
immediately pushed. The existing committed-source bundle route was reused after the
prior remote GitHub SSL timeout; no new failed GitHub fetch or scientific fallback
was attempted. Bundle folr-half-b01-c6be208cd.bundle is905410 bytes, SHA-256
`b89483bfa6ea548d0d5cb4a0e29544ef762b63e8a03770dbafcc489dc30ec820`.
It carries this full source and requires e58b4b7a67ad31e2b245002d0f47987d755980a7
and6fb1e1f6d6f726f133e9aab9c9d96758e3b6d36c. Local/remote bundle verification
passed, raw transfer digest matched, and the exact detached worktree was created at
`/home/wu/hmasd-worktrees/folr-public-lifecycle-half-b01-c6be208cd` with clean status.

The local bundle remains under
`temp/directions/vap_folr_core/exp/public_lifecycle_half_b01_control_20260910/`; its
remote input directory `/home/wu/hmasd-inputs/folr-public-lifecycle-half-b01-20260910`
joins the later worktree/two-supervisor closeout inventory. All archive members must
be compared to originals before removal. No scientific output root was created or
accepted invocation submitted during source staging.

Both commands are frozen before submission. Each source/seed/budget is preselected;
HALF_EVENT follows a technically valid RETAIN completion regardless of its score.

### RETAIN — prepared, not submitted

Handle `folr-public-lifecycle-half-b01-retain-20260910`.

```sh
/usr/bin/time -v -o /home/wu/.agent-tasks/folr-public-lifecycle-half-b01-retain-20260910/whole.time /usr/bin/timeout --signal=TERM --kill-after=5s 1800s bash -lc 'cd /home/wu/hmasd-worktrees/folr-public-lifecycle-half-b01-c6be208cd && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/public_lifecycle_half_b01_seed7807_retain_memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_folr_public_lifecycle_b01.py --arm RETAIN --seed 7807 --evaluation-seed 107807 --launch-sha c6be208cd514b5d12fb13c7637e2d6376de11eb6 --out temp/directions/vap_folr_core/exp/public_lifecycle_half_b01_seed7807_retain'
```

### HALF_EVENT — prepared, not submitted

Handle `folr-public-lifecycle-half-b01-half-event-20260910`.

```sh
/usr/bin/time -v -o /home/wu/.agent-tasks/folr-public-lifecycle-half-b01-half-event-20260910/whole.time /usr/bin/timeout --signal=TERM --kill-after=5s 1800s bash -lc 'cd /home/wu/hmasd-worktrees/folr-public-lifecycle-half-b01-c6be208cd && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/public_lifecycle_half_b01_seed7807_half_event_memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_folr_public_lifecycle_b01.py --arm HALF_EVENT --seed 7807 --evaluation-seed 107807 --launch-sha c6be208cd514b5d12fb13c7637e2d6376de11eb6 --out temp/directions/vap_folr_core/exp/public_lifecycle_half_b01_seed7807_half_event'
```

Source-route read/transfer/import checks add2.9893583s, taking scoped support to **43.7468483s/300s**. Git bundle construction and publication are administrative. No scientific result or full runtime has yet been observed.

Both exact commands passed `bash -n`; both named supervisor/output roots were absent. The record whitespace check passed. This check took 0.7180000s, making current scoped support **44.4648483s/300s**. No command payload was executed by the syntax check.

## 6. RETAIN accepted and direct observation handed over

Source c6be208cd and command publication3a3ea076d5db7d52dd357e278a83ee3031a3995f
were both pushed before submission. At **2026-09-10T21:59:27.130588+00:00** this DM
submitted only the original RETAIN command; the supervisor returned exit0 with explicit
tmux-start at **2026-09-10T21:59:27.768852+00:00**. Actual handle is
`folr-public-lifecycle-half-b01-retain-20260910`, tmux
`agent_folr-public-lifecycle-half-b01-retain-20260910`. The exact frozen source surface
passed its currentness comparison, and the handle was absent before submission.
[RESULT_SUMMARY](FOLR_PUBLIC_LIFECYCLE_HALF_B01_RESULT_SUMMARY_20260910.json) preserves
the complete submission command, clocks and raw stdout/stderr; local original receipt
is in `public_lifecycle_half_b01_control_20260910/retain_launch_receipt.json`.

This is accepted invocation **1 of2**. Fresh destination admission and the exact
runner share the outer1800s chain; their actual memory receipt, learner progress and
primary output have not been collected. Supervisor acceptance alone establishes no
valid run or result. HALF_EVENT remains the single unsubmitted preselected second arm.

DM sent MONITOR_ADD directly to the live-primary configured Monitor
`01a087e5-2044-7301-abb6-7a1709a98197`; app delivery succeeded. Root subsequently confirmed **actual Monitor adoption**
for this same handle/source/cwd and the source/command integrations29e0f2f07→74f8e7ce9.
The forwarded adoption receipt supplies no separate observation timestamp; the
submission timestamp is not relabeled as adoption time. Original collection/acceptance/science
owner is `/root/dm_folr_p68_reentry`; parent/receipt Root is
`01a07249-b095-7821-8ce2-e9c32ba85267`. No optional implementation executor owns the
scientific handle and no duplicate DM polling follows. Root resumes this same DM
for terminal collection and technical acceptance, then the already selected HALF_EVENT
submission if RETAIN completed validly, followed by complete-pair scientific intake
and scoped closeout. A failed original invocation stops the dependent sequence under
the card; there is no replacement or additional allocation.

The source check and submission took0.6410000s. Current scoped support is **45.1058483s/300s**; directory tests remain32.4911638s. Complete scientific wall/CPU and study elapsed remain unobserved. Root receives this accepted-handle boundary for integration and observation continuation; source, budgets and outcome interpretation remain with this direction.

The final accepted-handle/source/command/count/scratch/publication check passed in0.1100000s; scoped support at this handover is **45.2158483s/300s**. It confirmed one accepted handle, no complete result, unchanged accepted source/tests and one preselected unsubmitted arm. No scientific replay, new test or status poll was performed.

## 7. Restart recovery and RETAIN terminal acceptance

Root explicitly transferred remaining DM responsibility to `/root/dm_folr_restart_recovery`
after the app restart. The shared checkout was at command commit3a3ea076d with two
dirty result-record files containing the prior acceptance/adoption facts; those facts
are preserved above. Source and tests still match c6be208cd. No legacy CM was resumed.
The live-primary Monitor endpoint remains01a087e5-2044-7301-abb6-7a1709a98197.

Root routed the original-handle terminal receipt, and this DM collected the complete
RETAIN output/checkpoint, seven supervisor files and fresh memory receipt. All **10**
local file lengths/digests match remote originals; the compact receipt is
`evidence/2026-09-10-folr-public-lifecycle-half-b01-retain-collection.json`.
Raw copies remain in the owned control directory's `collected/`. No remote root has
been removed. The source-input directory, complete exact-SHA worktree and two named
supervisors form the later closeout inventory; HALF_EVENT's supervisor is still absent.

RETAIN finished exit0 at2026-09-11T06:12:00+08:00. Its summary and final log object
agree:5000 train episodes/100000 ticks/4969 RMSprop,128 final episodes/2560 ticks,
all25 progress rows, CPU FP32 and Torch1/1. The128 recorded returns recompute to
**1.68046875** (conditional sample SD5.60026938); cumulative training sum−26706.82,
mean−5.341364. Both phase attenuation and full-reset totals are zero. Fresh actual-node
admission passed at21:59:27.415727Z with15,632,941,056 physical/effective available bytes.
Complete outer wall **753.10s**, user/system CPU732.34/22.12s, total754.46 CPU-s;
narrower runner wall752.75510065s. These satisfy this arm's1800s cap. No pair branch
can be read before HALF_EVENT's completion.

The Monitor text labels its local observation22:13:12−07:00, inconsistent with the
same receipt's remote terminal clock and current UTC chronology. Preserve that label
as supplied; do not use it for study elapsed or change the scientific result. Direct
supervisor start/exit clocks and `/usr/bin/time` provide the execution facts.

Technical acceptance is recorded separately in the [intake](FOLR_PUBLIC_LIFECYCLE_HALF_B01_INTAKE_20260910.md#1-recovery-and-retain-technical-acceptance).
No source repair, new test, policy replay or scientific retry occurred. Recovery
procedure/source reads are conservatively charged10s; collection4.1652834s and
acceptance analysis0.0490410s bring scoped support to **59.4301727s/300s**.
Whole engineering/Monitor elapsed is unmeasured and is not invented as zero.
