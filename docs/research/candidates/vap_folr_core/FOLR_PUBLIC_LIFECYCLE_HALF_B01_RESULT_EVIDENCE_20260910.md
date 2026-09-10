# FOLR public lifecycle HALF-B01 technical evidence

Current state: source and focused checks accepted; no scientific invocation submitted.

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
