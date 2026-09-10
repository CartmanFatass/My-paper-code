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
