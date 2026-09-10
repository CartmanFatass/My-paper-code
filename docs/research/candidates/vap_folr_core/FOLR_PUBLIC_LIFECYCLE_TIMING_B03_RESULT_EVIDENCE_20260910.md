# FOLR public lifecycle TIMING-B03 technical evidence

## Prospective source and selected execution

[Card §§1–6](FOLR_PUBLIC_LIFECYCLE_TIMING_B03_SCIENCE_CARD_20260910.md) fixes the new
RETAIN/EVENT pair at7806/107806, MEI1 and WITHIN_MEI low-confidence forecast. Root's
independent-direction steering is applied in [intake §§1–4](FOLR_PUBLIC_LIFECYCLE_TIMING_B03_INTAKE_20260910.md#1-next-question-and-object-tier-selection).
No invocation has been accepted yet. The shared authoring branch is synchronized at
35eb3f6c55; runner/scientific/test bytes match accepted6a8eacda without edits.

Explicit CLI values seed all three base streams before construction and again before
the final environment; actual output metadata uses those values. No private mask RNG
is created for RETAIN or EVENT. Historical default labels/docstring and unused RANDOM
constants remain unchanged. Existing focused tests and independent RNG review apply to
the same source surface; no new test, high-impact code change or target call is introduced.

The [machine plan](evidence/2026-09-10-folr-public-lifecycle-timing-b03-plan.json) records
205120 native ticks/9938 updates/256 final episodes. Two complete-chain point costs
832.49/769.66s project1602.15s. Caps are1800s per arm/3600s pair plus300s support, with
exactly one accepted RETAIN then EVENT invocation, both preselected. Preparatory support
charge5s is rounded and separate; cumulative directory tests25.9131638s remains unchanged.

## Required route and closeout boundary

Configured hmasd-wsl-node, exact published SHA in a detached worktree, CPU FP32/Torch1/1,
fresh destination admission adjacent to each runner in one outer time/timeout chain.
Direct Monitor registration follows acceptance; adoption is recorded from its actual
receipt. The DM does not duplicate Monitor polling after transfer. Source commit, exact
commands, handles, roots, memory, clocks and all results will be appended as observed.

After both terminal results are collected, preserve the exact new worktree/two supervisors,
compare archive members with their originals before removal, then verify exact path/
registration absence. The old B02 pre-delete comparison omission stays recorded; old
rejected local scratch is not touched. Root retains final integration/closure acceptance.

New-card item20260910-folr-002 is published with the prospective selection record.
Source quotations passed the bounded check; support is5.3660909/300s before remaining
publication/staging/collection reads. No new scientific invocation has been accepted.

Final prospective card/count/link/source checks passed, with no scientific import/test.
Their measured0.7068222s brings pre-staging support to **6.0729131/300s**. Live-primary
owner reviews again returned `[]`; the selected pair proceeds under existing authority.

## Source transport exception and exact-SHA staging

Initial remote `git fetch origin codex/vap-folr` failed with exit128:
`fatal: unable to access 'https://github.com/CartmanFatass/My-paper-code.git/': SSL connection timeout`.
The staging script stopped before `git worktree add` and before any scientific submission.
A bounded process inspection found the exact fetch and its HTTP child still active at
254.66s elapsed. Its subsequent `git cat-file -e` source lookup itself triggered a lazy
HTTP fetch; only that owned read-only probe and descendants were terminated after the
confirmed transport failure. The raw lookup's false return reflects interrupted resolution,
not a trustworthy object-absence verdict. The execution cwd was observed absent. No
accepted scientific process, model, RNG master or result root was stopped or retried.

The permitted transport alternative packages already committed/pushed Git objects, preserving
the full frozen source, host/device, seeds and budget. Local Git bundle creation and verification
bind `refs/heads/codex/vap-folr` to `6fb1e1f6d6f726f133e9aab9c9d96758e3b6d36c`, with required existing commits
`d526dcc3578b7604487b372000813c0f69e72dc8` and
`6a8eacdad072c37d477aca95a9c871aba68cee78`.
The source bundle is 1764814 bytes, SHA-256
`701b0261baba830e6258e217ef78571f55c4492c2a41fa72419d55592cfa3b32`.

Local retained source input:
`temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_control_20260910/folr-timing-b03-6fb1e1f6.bundle`.
Remote staged input:
`/home/wu/hmasd-inputs/folr-public-lifecycle-timing-b03-20260910/folr-timing-b03-6fb1e1f6.bundle`.
SCP completed; the remote whole-file digest matched, `git bundle verify` passed and local-file
Git fetch imported the exact objects. The new detached cwd `/home/wu/hmasd-worktrees/folr-public-lifecycle-timing-b03-6fb1e1f6` was created at full
source `6fb1e1f6d6f726f133e9aab9c9d96758e3b6d36c`; `git status --short` was empty. Staging completed at
2026-09-10T19:30:11.938989Z with zero scientific submissions at that time.

The source-input staging directory is now part of this object's explicit closeout inventory,
alongside the exact worktree and its two eventual supervisors. Preserve its bundle and verify
archive-versus-original bytes before any later scoped removal. This input is committed source,
not an uncommitted-source offload, local scientific fallback or extra scientific attempt.
No global Git configuration, interpreter, dependency or launch code changed.

## RETAIN accepted and actual Monitor adoption confirmed

The first and only allocated RETAIN submission was made at 2026-09-10T19:31:43.425234Z;
`agent-task run` returned 0 and explicit tmux-start receipt at 19:31:43.439557Z.
Handle: `folr-public-lifecycle-timing-b03-retain-20260910`. Detached tmux: `agent_folr-public-lifecycle-timing-b03-retain-20260910`.
Cwd: `/home/wu/hmasd-worktrees/folr-public-lifecycle-timing-b03-6fb1e1f6`. Full source: `6fb1e1f6d6f726f133e9aab9c9d96758e3b6d36c`.
Output root: `temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_seed7806_retain`; adjacent admission receipt: `temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_seed7806_retain_memory.json`.
Supervisor files: `/home/wu/.agent-tasks/folr-public-lifecycle-timing-b03-retain-20260910/task.log`, `whole.time`, `runner.sh`, `status` and `exit_code`.

Accepted command (shell syntax checked once; no target call in that check):

```sh
/usr/bin/time -v -o /home/wu/.agent-tasks/folr-public-lifecycle-timing-b03-retain-20260910/whole.time /usr/bin/timeout --signal=TERM --kill-after=5s 1800s bash -lc 'cd /home/wu/hmasd-worktrees/folr-public-lifecycle-timing-b03-6fb1e1f6 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_seed7806_retain_memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_folr_public_lifecycle_b01.py --arm RETAIN --seed 7806 --evaluation-seed 107806 --launch-sha 6fb1e1f6d6f726f133e9aab9c9d96758e3b6d36c --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_seed7806_retain'
```

The fresh destination admission and real runner are adjacent inside one complete 1800s
outer time/timeout chain. Expected counts remain 5000 train/100000 ticks/4969 RMSprop,
128 final/2560 ticks, CPU FP32/Torch1/1. Admission contents, actual progress/counts,
whole clocks and primary outputs will be collected from terminal artifacts; no pass or
performance claim is invented from submission alone.

The live primary Monitor endpoint was read from `C:/Projects/HMASD/.codex/hmasd-monitor.toml`:
`01a087e5-2044-7301-abb6-7a1709a98197`, bound Root `01a07249-b095-7821-8ce2-e9c32ba85267`.
Direct MONITOR_ADD carrying exact accepted facts and original owner `/root/dm_folr_p68_reentry`
was accepted by the app tool. Root then explicitly confirmed **actual Monitor adoption** for
this handle/source through native message. The DM receipt did not supply a Monitor observation
timestamp, PID or resource numbers, so none is reconstructed. Monitor is the sole observer;
Root resumes this same DM on terminal for collection and the preselected EVENT.

One of two allocated invocations is accepted; EVENT remains unsubmitted, not selected from
RETAIN's eventual sign. No new source/test change, repeated run or result-bearing probe follows
this handover. The prospective WITHIN_MEI prediction remains unscored and the pair result pending.

Routing/help/source/launch-command reads add 1.9038446s to pre-staging support 6.0729131s:
current scoped support **7.9767577/300s** before later publication/collection reads. The
supervisor's help command returned usage/exit1, which is included; it submitted no task.
Directory tests remain 25.9131638/300s. Git transport is administrative, separate from complete
scientific invocation walls: the short bundle/hash/cancel/copy/import commands have summed
tool wall 3.9806105s, while total failed HTTPS/probe latency is not fully measured here.
The 254.66s observation was a still-running fetch age, not complete elapsed or CPU work.
No failed transfer is assigned scientific polarity or charged as a new fit.

Handover record and live routing reads add 0.6283057s of scoped support, bringing the
current recorded support to **8.6050634/300s** before the final publication check.
No scientific or test invocation was added.

The final preservation/owner-review/whitespace check passed in 0.5827729s, giving
**9.1878363/300s** scoped support through this handover. Live-primary reviews
returned `[]`; the claim and card sections 2-6 remain exactly as frozen.

## RETAIN terminal collection and technical acceptance

Monitor observed the original handle at 2026-09-10T19:44:38.4926524Z: finished, exit 0,
PID 3097075/tmux inactive. Its source receipt is
`C:/Users/fires/Documents/Codex/2026-09-09/hmasd-folr-b02-monitor-20260909/outputs/folr-public-lifecycle-timing-b03-retain-20260910-terminal.txt`;
a byte copy is retained at
`temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_control_20260910/retain_monitor_terminal.txt`.
The terminal log reports 2026-09-11T03:44:18+08:00, equivalent to 2026-09-10T19:44:18Z;
its second-resolution duration is 755s. The direct remote collection at
2026-09-10T19:46:31.611172Z binds full source 6fb1e1f6d6f726f133e9aab9c9d96758e3b6d36c,
clean tracked source, summary/checkpoint/memory and five supervisor files.

All eight files were copied and compared with their pre-copy remote SHA-256 digests.
[RESULT_SUMMARY](FOLR_PUBLIC_LIFECYCLE_TIMING_B03_RESULT_SUMMARY_20260910.json) preserves
the full arm summary, eight mappings/hashes, 25 progress rows, memory receipt and exact
clocks. Raw scientific output is retained at
`temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_seed7806_retain/`, with
supervisor bytes in its `supervisor/` directory and the adjacent `_memory.json`.
No original or staged input has been removed.

Actual exposure: 100000 real training ticks, 4969 actor/mixer RMSprop steps at lr .0005,
128 final greedy evaluations/2560 ticks. Mean 6.893125 recomputes from all 128 finite
returns. Counts, seeds, source and retained summaries satisfy [intake §7](FOLR_PUBLIC_LIFECYCLE_TIMING_B03_INTAKE_20260910.md#7-retain-terminal-technical-acceptance-and-preselected-continuation).
Complete invocation wall 755.40s, CPU 756.45s, peak RSS 677224 KiB; narrower runner
wall 751.362323189s and peak RSS 644796 KiB remain distinct. Physical/effective memory
15321518080 bytes passed; unmeasured cgroup telemetry limits only that resource detail.
Support through this collection is **15.6963948/300s**, including the initial missing
local `outputs/` lookup before resolving the Monitor checkout. No scientific/test replay.
The pair effect and prediction score remain pending EVENT.

## Preselected EVENT command, not yet submitted

Handle `folr-public-lifecycle-timing-b03-event-20260910`; output
`temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_seed7806_event`.
The second arm is the same prospective allocation and exact source; RETAIN's realized
mean does not select it. Commit and push this acceptance before submission.

```sh
/usr/bin/time -v -o /home/wu/.agent-tasks/folr-public-lifecycle-timing-b03-event-20260910/whole.time /usr/bin/timeout --signal=TERM --kill-after=5s 1800s bash -lc 'cd /home/wu/hmasd-worktrees/folr-public-lifecycle-timing-b03-6fb1e1f6 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_seed7806_event_memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_folr_public_lifecycle_b01.py --arm EVENT --seed 7806 --evaluation-seed 107806 --launch-sha 6fb1e1f6d6f726f133e9aab9c9d96758e3b6d36c --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b03_seed7806_event'
```

Fresh admission and the exact runner are one complete invocation. One accepted EVENT
submission remains; no retry or replacement is included. After explicit acceptance,
register it directly with the live Monitor and distinguish registration from adoption.

The RETAIN intake/card-preservation/whitespace check passed in 0.3931626s; support
through that pre-EVENT publication check is **16.0895574/300s**. No scientific source
or test change was made. The live-primary FOLR audit owner column is also empty.
