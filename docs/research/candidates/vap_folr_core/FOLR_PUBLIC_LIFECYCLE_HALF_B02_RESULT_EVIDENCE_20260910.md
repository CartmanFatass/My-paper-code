# FOLR public-lifecycle HALF-B02 technical evidence

Current state: RETAIN accepted and Monitor adoption confirmed by Root; HALF_EVENT remains preselected and unsubmitted. No scientific result collected.

## 1. Accepted reuse and focused new binding

[Card §§2–5](FOLR_PUBLIC_LIFECYCLE_HALF_B02_SCIENCE_CARD_20260910.md#2-reused-intervention-task-and-learner)
reuses sourcec6be208cd514b5d12fb13c7637e2d6376de11eb6, its26 focused checks and independent
semantic review from HALF-B01. Current module/runner/preflight/test content matches that
accepted source. New source lines0; no model load, suite, pilot or scientific execution.
Training7808/evaluation107808 are new explicit process arguments, retaining the existing
Python/global NumPy/Torch setup before construction and final reset. Native/replay RNG,
CPU FP32/Torch1/1, before-GRU attenuation, acting/online/target reconstruction, reward,
information, optimizer and endpoint remain unchanged. No private mask stream is added.

The actual runner AST contains training `range(1,5001)` and final `range(128)`.
Machine-generated [plan](evidence/2026-09-10-folr-public-lifecycle-half-b02-plan.json)
reports2×102560=205120 native ticks,9938 RMSprop and256 final episodes. Every arm's
new command passes `--seed 7808 --evaluation-seed 107808` explicitly; old CLI defaults
cannot choose this pair's streams. Previous cumulative directory tests32.4911638s remain.
The unchanged source reuse is technically accepted; final actual admission, learner
counts, outputs, whole timing and comparison still require real execution/collection.

## 2. Exact preselected execution inputs

The [summary](FOLR_PUBLIC_LIFECYCLE_HALF_B02_RESULT_SUMMARY_20260910.json) preserves the
two complete literal command payloads before submission. Remote source worktree:
`/home/wu/hmasd-worktrees/folr-public-lifecycle-half-b02-c6be208cd`, CPU FP32/Torch1/1,
Python `/home/wu/.venvs/hmasd/bin/python`. RETAIN precedes HALF_EVENT, one accepted
invocation each, at the same fixed7808/107808 bindings. Both arms are preselected
regardless of the first return; a failure stops the dependent sequence without retry.

- RETAIN handle `folr-public-lifecycle-half-b02-retain-20260910`; output
  `temp/directions/vap_folr_core/exp/public_lifecycle_half_b02_seed7808_retain`.
- HALF_EVENT handle `folr-public-lifecycle-half-b02-half-event-20260910`; output
  `temp/directions/vap_folr_core/exp/public_lifecycle_half_b02_seed7808_half_event`.

Each fresh memory receipt is the corresponding output path plus `_memory.json`.
The receipt-producing `admit-memory && runner` shares one outer `/usr/bin/time -v`
and `/usr/bin/timeout --signal=TERM --kill-after=5s 1800s` chain. Its complete source,
arm, seed, evaluation-seed and output arguments are fixed in the command record.
No scientific output root is created by preparing these strings or by source staging.

## 3. Runtime support and ownership

The new allocation is1800s per arm,3600s scientific sum and≤300s all additional
runtime support including Monitor,3900s total. Existing command/tool durations charge
preparation/checks/staging, observation, collection/analysis/readback and preservation/
closeout once. No idle wait or already counted native time is duplicated. The summary
maintains attributable DM command seconds and actual Monitor receipts for these two
handles; an old missing total is not imputed zero. Before an accepted handle exists,
this object has invoked zero Monitor work.

This DM owns source/command publication, launch, collection, technical acceptance,
scientific intake and scoped closeout in the shared local checkout. The live-primary
Monitor endpoint is01a087e5-2044-7301-abb6-7a1709a98197 from
`C:/Projects/HMASD/.codex/hmasd-monitor.toml`; Root receipt destination is
01a07249-b095-7821-8ce2-e9c32ba85267. Send actual accepted handles directly, record
dispatch separately from adoption, and request this study's actual Monitor command
cost with adoption/terminal facts. No mirrored DM polling or new monitoring service.

No new scope §4 machinery or source-budget breach is present. The six existing totals
for each phase/arm remain the only selected event instrumentation. Root owns main
integration and accepts completed reclamation. No third pair or successor is allocated.

## 4. Exact source ready and new command readback accepted

The source commit was already published and retained in the compute repository. A
new detached worktree was created at the exact §2 path with sourcec6be208cd and clean
tracked status; no source bundle/input stage was needed. Both prospective supervisor,
scientific output and memory-receipt paths were absent. Each complete literal command
passed `bash -n`, and the isolated runner portion carries the exact7808/107808/arm/
source/output arguments. No command payload, model, optimizer or scientific RNG was
executed by these checks. Local original preparation receipts are in
`temp/directions/vap_folr_core/exp/public_lifecycle_half_b02_control_20260910/`.

The first readback checker selected the first `--out` in the joined command, which
belongs to `admit-memory`, and asserted against the runner output. This was a checker
error after source checkout creation, not a source/command mismatch. The corrected
readback isolates the command after the last `&&`; both commands then passed. Original
stderr is retained; the exact commands and scientific source were never changed.
Zero scientific invocations occurred, and this creates no replacement allowance.

The three Portfolio input files imported from674f246a2 have matching Git blob content;
unrelated histories/paths were not reconciled. Owner CLI created
`docs/research/portfolio/owner/inbox/2026-09-10/20260910-folr-005.json` for the new card.
The selection audit row points to this card/intake and carries the existing unattended
delegation, not a waiting permission question.

At this preparation boundary actual recorded support is **3.4691497s**, including the
failed readback and its corrected follow-up; scientific and Monitor work remain zero.
The summary carries each measured component. Next: commit/push these exact inputs,
submit RETAIN once with its fresh joined admission, and directly hand the accepted
handle to Monitor with this study's inclusive support-attribution instruction.

## 5. Published inputs, RETAIN acceptance and actual Monitor adoption

Selection/card/plan/commands and the three unchanged Portfolio dependency files were
committed and immediately pushed at **ea73b1c3dabafe6482db03df8a9e51c1ad672260**.
Scientific source remains **c6be208cd514b5d12fb13c7637e2d6376de11eb6**; a doc publication
does not substitute different execution bytes. The submitted RETAIN command equals
that published payload, with its fresh memory admission and runner inside one 1800s chain.

This DM submitted RETAIN at **2026-09-10T23:47:46.571111+00:00**; explicit tmux-start
returned at **23:47:46.884434+00:00**, command exit0 and no stderr. Accepted handle is
`folr-public-lifecycle-half-b02-retain-20260910` on hmasd-wsl-node, at the exact source,
cwd and output named in §2. Original receipt is
`public_lifecycle_half_b02_control_20260910/retain_launch_receipt.json`; the committed
summary retains its full command, clocks and raw acceptance output. Source comparison
and absent-handle/output checks passed. This is accepted invocation **1 of 2**.
Actual admission/learning/final data have not yet been collected; supervisor acceptance
is not technical result acceptance. HALF_EVENT is the sole unsubmitted second arm.

Direct MONITOR_ADD to 01a087e5-2044-7301-abb6-7a1709a98197 was delivered successfully,
with the source/cwd/output/root/owner and inclusive 300s support-accounting instructions.
Root confirmed actual adoption of the same RETAIN handle; no distinct observation
timestamp was supplied, so the tmux acceptance clock is not relabeled as adoption.
Monitor will track actual enclosing query seconds and return cumulative attributable
work through the existing receipt path. Its current total is **pending**, not zero.
This DM performs no routine remote polling. Root routes terminal facts back to
`/root/dm_folr_restart_recovery` for collection/acceptance and the preselected second arm.

The initial support subtotal used narrower helper timings. The summary now conservatively
charges enclosing command/tool wall, including startup, nested remote work and source
publication, once. A default Windows decoder failed while reading the Chinese owner
item before that bookkeeping update; explicit UTF-8 readback passed before submission,
and the published scientific card/commands were unaffected. Both mechanical readback
failures remain charged and neither was a scientific invocation.

Known DM command wall through RETAIN submission is **9.7291575s**, plus **.182s** direct
Monitor dispatch, giving **9.9111575s through dispatch**. Later handover/publication work
and actual Monitor seconds remain to be added at the next natural boundary. This is
a current subtotal, not an asserted complete 300s support bill. The 300/3600/3900 caps,
no-transfer rule, required terminal observation and no-retry allocation remain intact.

At the adopted-boundary readback, measured DM support is **10.7798254s**. Primary owner
reviews returned no unapplied items. One handover bookkeeping command has no returned
elapsed receipt; it remains unmeasured, not zero. Final publication and actual Monitor
work are also pending reconciliation, so no complete-support total is claimed here.
