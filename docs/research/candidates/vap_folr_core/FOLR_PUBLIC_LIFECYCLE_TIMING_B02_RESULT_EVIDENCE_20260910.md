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
