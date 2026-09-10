# FOLR public lifecycle TIMING-B02 technical evidence

## Source and focused acceptance

Allocation and scientific meaning: [card §§1–6](FOLR_PUBLIC_LIFECYCLE_TIMING_B02_SCIENCE_CARD_20260910.md).
Implementation and acceptance: [intake §3](FOLR_PUBLIC_LIFECYCLE_TIMING_B02_INTAKE_20260910.md#3-engineering-acceptance-before-launch).
The only production edit is the runner's new instance/RNG binding. Scientific modules
retain accepted source74d023d7d semantics. Three changed stand-in cases passed; independent
Astra/high RNG review found no material defect. No scientific calls occurred in checks.
Source commit will be recorded immediately after commit/push, before the first invocation.

The fixed three fits use7805/107805; RANDOM private mask streams207805/307805. Each arm
has5000 train episodes,4969 updates and128 final episodes. Total307680 native ticks,
14907 optimizer calls,384 final episodes; all three laws are selected before output.
Complete per-law cap1800s, summed triple5400s, separate support300s, cumulative directory
tests preserved. Old whole-chain charges739/788/820s are point projections at unchanged
work, not guarantees. The source runner's wall alone does not include admission.

## Execution route and accounting

Configured remote `hmasd-wsl-node`, Python `/home/wu/.venvs/hmasd/bin/python`, CPU FP32,
Torch compute/interop1. Reuse the shared authoring checkout/branch; stage a new detached
exact-source remote worktree after source commit/push. Each `agent-task` command uses
outer `/usr/bin/time -v` and timeout around the `admit-memory && runner` chain so time
includes admission, imports/initialization, training, final evaluation, publication and
exit. Store its outer time record in that supervisor's existing directory; runner roots
are created only after successful fresh destination admission. A timeout/failure preserves
partial independently trustworthy facts and stops dependent sequence without replacement.

Live Monitor configuration: `C:/Projects/HMASD/.codex/hmasd-monitor.toml`, task
`01a087e5-2044-7301-abb6-7a1709a98197`, Root `01a07249-b095-7821-8ce2-e9c32ba85267`.
The DM sends MONITOR_ADD for each actually accepted handle and records dispatch separately
from Root-confirmed adoption. No concurrent DM status polling after handover. Terminal
notice is not result acceptance; this DM retains collection and scientific interpretation.

## Current cost and unresolved operational fact

Supporting charge18.0821851/300s before publication/staging/collection, including10s
conservative preparatory charge,6.3634804s tests and1.7187047s reviewer command wall.
Directory tests25.9131638/300s cumulatively. No new scientific execution or completed
result yet. Source lines and infrastructure remain within the unchanged research budget.
The test's original combined command was rejected before execution (`blocked by policy`);
the permitted test-only command passed. Named scratch `temp/directions/vap_folr_core/test/timing_b02_check01`
remains DM-owned because deletion was rejected, with no bypass. This is separate from
the scientific budget/polarity and does not authorize further scientific calls.

Publication/source-command readbacks add1.2265025s as itemized in intake §3; current
support charge **19.3086876/300s** before staging and collection. The only publication
check correction normalized a Markdown line wrap when matching a retained quote; no
card, source, result or quoted words changed. No additional test/target execution.

## RETAIN accepted; observation dispatched, adoption pending

The DM committed/pushed source `6a8eacdad072c37d477aca95a9c871aba68cee78`; Root accepted
and integrated it as main `8eb423ff2`. The configured network shell fetched that branch
and staged detached worktree `/home/wu/hmasd-worktrees/folr-public-lifecycle-timing-b02-6a8eacda`.
Readback confirmed exact HEAD, clean declared source surface, runner/preflight presence
and configured interpreter. This readback took0.6473996s, bringing supporting charge to
**19.9560872/300s** before handover publication and collection. Git/staging transport is
separate control-plane work. Latest all-age owner reviews were `[]` before submission.

Accepted handle: `folr-public-lifecycle-timing-b02-retain-20260910`, tmux
`agent_folr-public-lifecycle-timing-b02-retain-20260910`. The supervisor returned acceptance
and `/home/wu/.agent-tasks/folr-public-lifecycle-timing-b02-retain-20260910/task.log`.
Exactly one RETAIN submission is accepted; EVENT/RANDOM have not been submitted.

```sh
/usr/bin/time -v -o /home/wu/.agent-tasks/folr-public-lifecycle-timing-b02-retain-20260910/whole.time /usr/bin/timeout --signal=TERM --kill-after=5s 1800s bash -lc 'cd /home/wu/hmasd-worktrees/folr-public-lifecycle-timing-b02-6a8eacda && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b02_seed7805_retain_memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_folr_public_lifecycle_b01.py --arm RETAIN --seed 7805 --evaluation-seed 107805 --launch-sha 6a8eacdad072c37d477aca95a9c871aba68cee78 --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b02_seed7805_retain'
```

`whole.time` encloses the full admission/runner command, including its shell startup,
initialization/imports, learning, evaluation, publication and exit. It is separate from
the runner summary's narrower wall. A TERM/kill-after failure is an incomplete invocation,
not permission to claim cap conformance or submit a replacement.

Direct MONITOR_ADD to the live configured task returned that task's threadId with
`isError=false`. It carries handle, full source/cwd/root, memory/whole.time/log paths,
Root destination and original execution/scientific owner `/root/dm_folr_p68_reentry`.
Dispatch is accepted; **actual adoption is pending** at this record. Root was notified
natively; this DM performs no parallel status poll. No summary, admission pass, training
count, native return or terminal exit is inferred from supervisor acceptance. Root resumes
this DM at terminal for collection and the next already allocated law.

## RETAIN actual Monitor adoption confirmed

After the pending record was published at `b3b2251cd5d9213f8c0b3d60d9b6f70f4cb23b0a`,
Root's 2026-09-10 native continuation confirmed **direct actual Monitor adoption** of
`folr-public-lifecycle-timing-b02-retain-20260910` on the declared node/supervisor with
the identical full source, detached cwd and result root. Observation is now owned by the
shared Monitor. This DM returns pending terminal collection and performs no parallel
polls. EVENT/RANDOM remain unsubmitted; no terminal, resource or scientific result fact
is supplied by this adoption update. Root will resume this same DM on terminal notice.

## RETAIN terminal collection and technical acceptance

Root delivered the Monitor terminal notice observed `2026-09-10T17:04:06.0084286Z`:
finished/exit0, remote start `2026-09-11T00:49:37+08:00`, exit
`2026-09-11T01:03:30+08:00`, integer supervisor duration833s. The DM collected raw
summary/checkpoint, memory receipt, full outer time, log, command wrapper, status and exit
witness into local `temp/directions/vap_folr_core/exp/public_lifecycle_timing_b02_seed7805_retain`
plus sibling `_memory.json`; all **8 remote/local SHA256 mappings agree**. The Monitor
receipt is copied there as `monitor_terminal.txt`. Full raw mapping, all128 returns,
25 progress rows and measured quantities are in the
[result summary](FOLR_PUBLIC_LIFECYCLE_TIMING_B02_RESULT_SUMMARY_20260910.json).

The exact source/seeds7805/107805, complete status,5000 training episodes/100000 native
training ticks/4969 RMSprop steps/128 final episodes/2560 final ticks and Torch threads1/1
match the card. Every final return is finite, the recomputed mean is **2.64265625**, and
the printed final log summary equals the published JSON. The25 progress rows end at
episode5000/update4969. The native training return sum is−22343.380000000183, mean
**−4.468676000000037**. No training-return curve is reconstructed from progress timing.

Training counters: births20978, departures8373, event-bound survivor opportunities46007,
all eligible survivor opportunities260235, resets0. Final counters:588/306/1402/6159/0.
The zero-reset RETAIN law and nonzero eligible exposure agree. No new learned fit,
checkpoint reload, simulator call or evaluation occurred during collection.

Fresh admission at `2026-09-10T16:49:37.756230Z` passed both physical/effective4GiB
floors, each15631716352 bytes. Null cgroup headroom/current/max remain
`resources_unmeasured`; the passing recorded measurements support this invocation only.
The actual outer `whole.time` encloses the full admission-through-exit chain:
**832.49s wall;812.40s user +20.47s system =832.87 CPU-s;651624KiB peak RSS; exit0**.
The summary's **790.0774647570215s** wall and632060KiB RSS are narrower runner records.
The42.41253524297849s outer-minus-runner difference is observed but not attributed to
a specific phase; no profiling or cost experiment is needed for this accepted budget.
The whole measurement and rounded supervisor duration are consistent, and the1800s
complete-law cap is met. Remaining two laws are unexecuted, so no complete-triple wall,
contrast, combined branch or scientific winner exists yet.

Supporting accounting now includes the prior handover read0.2805764s, terminal/owner
read0.4673387s, remote raw read0.7006461s, hash read0.8426555s and enclosing local
readback/assembly command0.1811988s: **22.4285027/300s** through this collection.
The assembly's internal0.0142466s is nested and is not charged again. SCP transport
6.3356898s is separate administrative transfer. Tests remain25.9131638/300s cumulative.
No source or test changed and no existing blocked scratch was touched.

Technical decision: accept intact RETAIN and proceed to the **already-preselected EVENT**.
No concrete primary, information, training, budget or publication defect supports
quarantine. This is execution of the fixed sequence, independent of the RETAIN sign;
RANDOM remains unsubmitted. Scientific interpretation waits for all allocated outcomes.

## EVENT accepted and actual Monitor adoption confirmed

RETAIN acceptance/E0/intake was committed and pushed at
`015c05eb5ecc032ae6841c894e585fe37ca51b3e` before submitting the second preselected law.
Scientific source remains `6a8eacdad072c37d477aca95a9c871aba68cee78`; there is no source
change, new fit allocation, test, retry or outcome-based arm choice.

Accepted EVENT handle `folr-public-lifecycle-timing-b02-event-20260910`, tmux
`agent_folr-public-lifecycle-timing-b02-event-20260910`, same exact-source detached cwd.
The supervisor accepted this command:

```sh
/usr/bin/time -v -o /home/wu/.agent-tasks/folr-public-lifecycle-timing-b02-event-20260910/whole.time /usr/bin/timeout --signal=TERM --kill-after=5s 1800s bash -lc 'cd /home/wu/hmasd-worktrees/folr-public-lifecycle-timing-b02-6a8eacda && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b02_seed7805_event_memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_folr_public_lifecycle_b01.py --arm EVENT --seed 7805 --evaluation-seed 107805 --launch-sha 6a8eacdad072c37d477aca95a9c871aba68cee78 --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b02_seed7805_event'
```

Fresh destination admission precedes this arm's new model/RNG/result creation within
the same complete outer time/timeout command. Submission acceptance alone does not
establish resource/count/result conformance; those are checked at terminal collection.
Direct MONITOR_ADD returned the live Monitor task ID with `isError=false`. Root then
confirmed **actual direct Monitor adoption** with the identical handle/source/cwd and
`_seed7805_event` result root, acknowledging RETAIN predecessor collection. Monitor owns
observation; DM returns pending terminal collection and does not poll. RANDOM is still
unsubmitted and remains the already-selected next law after complete EVENT acceptance.

## EVENT terminal collection and technical acceptance

Root delivered Monitor's terminal observation `2026-09-10T17:23:20.5924043Z`: finished,
exit0, remote start `2026-09-11T01:10:24+08:00`, exit `2026-09-11T01:23:14+08:00`,
rounded duration770s. The DM collected the same8 artifact types as RETAIN into local
`temp/directions/vap_folr_core/exp/public_lifecycle_timing_b02_seed7805_event` plus sibling
`_memory.json`; **all8 remote/local hashes agree**. The copied Monitor terminal receipt,
all128 returns, progress rows and full hash/source mapping are retained alongside the
expanded result summary. No model/checkpoint reload or scientific call was made.

EVENT is complete at the frozen source/seeds7805/107805, with5000 training episodes,
100000 training ticks,4969 optimizer steps,128 final episodes/2560 ticks and threads1/1.
All128 finite returns reproduce the published **2.051953125** mean to native-return
precision; the final printed log JSON equals the file and progress ends at5000/4969.
Training sum−25009.600000000064 gives mean **−5.001920000000013**. Actual training
counters are births21773/departures8704/event-bound survivor opportunities47153/all
eligible260059/resets47153; final562/201/1262/6746/1262. EVENT resets equal the eligible
event-bound survivor opportunities, with nonzero control exposure. Terminal and common
freshness conventions remain those of the accepted source.

Fresh admission assessed `2026-09-10T17:10:24.790916Z` passes physical/effective floors
at15603605504 bytes each. Null cgroup fields remain `resources_unmeasured`. Outer
whole-chain wall is **769.66s**, user754.09s + system17.91s = **772.00 CPU-s**,
peak RSS658888KiB, exit0; cap1800s is met. Runner wall727.8214852970559s/RSS641220KiB
remain separate. The outer-minus-runner interval is not assigned to a specific phase.
Two completed laws sum1602.15s whole wall and1604.87 CPU-s; RANDOM and full study elapsed
remain pending. The whole-triple cap is not inferred from an unfinished triple.

The observed EVENT−RETAIN point is **−0.590703125**, inside the ±1 MEI, with EVENT's
lower cumulative training return preserved. This is a partial comparison, not a selected
two-arm replacement for the allocated triple or a completed three-arm reading. No
intermediate sign changes which law runs next. The fixed RANDOM submission remains due.

Supporting charge through this collection is **24.6055824/300s**: preceding EVENT
handover0.4067036s, terminal/owner read0.3910993s, remote raw read0.7249654s, remote hash
read0.4488745s, local enclosing readback/assembly0.2054369s added to22.4285027s. Its
internal0.0169563s is nested, not double charged. SCP4.9776862s is administrative
transport. No new tests; cumulative directory test time stays25.9131638/300s.

Technical acceptance is complete and supports the preselected **RANDOM** under the
existing finite allocation. No primary/learning/information/publication/budget defect
was found; no retry, replacement, source change, added test or extra evaluation is needed.
