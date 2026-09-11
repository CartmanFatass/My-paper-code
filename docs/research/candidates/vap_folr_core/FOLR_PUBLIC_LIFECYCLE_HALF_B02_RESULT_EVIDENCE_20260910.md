# FOLR public-lifecycle HALF-B02 technical evidence

Current state: both arms complete and intaken under RETAIN_ABOVE_MEI; scoped remote closeout is verified. Root integration and reclamation acceptance remain.

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

## 6. RETAIN terminal collection and technical acceptance

Root routed the original accepted handle's exit0 terminal fact. Its supervisor started
at **2026-09-10T23:47:46Z** and ended **2026-09-11T00:00:15Z**, an integer-clock749s.
The complete outer `time` chain measured **748.47s**, below1800s, with732.50s user,
17.53s system and656744KiB peak RSS. Runner wall was748.1175824130187s and its peak
644236KiB. These nested timings are not added together. Fresh admission at
23:47:46.781396Z measured physical and effective available memory **15631994880 bytes**,
both above4GiB, before the fresh learner. No cap stop or scientific retry occurred.

The [collection receipt](evidence/2026-09-10-folr-public-lifecycle-half-b02-retain-collection.json)
records all **10 files /4675780 bytes** matching original remote lengths and SHA256:
summary/checkpoint, seven supervisor files and the memory receipt. The original
Monitor terminal text is also retained. Exact source surfaces still matchc6be208cd;
the raw final log JSON equals `summary.json`, all25 progress rows have episode200..5000
and updates=episode−31, and `final.pt` exists at4662779 bytes. No checkpoint was loaded
or re-evaluated. Raw copies remain under the named B02 control root's `collected/`.

RETAIN completed **5000 train episodes /100000 ticks /4969 updates**, then **128 final
episodes /2560 ticks** with training7808/evaluation107808 and Torch1/1. All128 returns
and25 progress rows are preserved in the result summary. Final mean native return is
**9.471796875**; sample SD9.89217605684 describes rollouts conditional on this fitted
policy, not training-instance uncertainty. Training return sum is−1567.5800000000443,
mean−.31351600000000884. Train phase counts are births23382, departures11932,
event-survivor opportunities54125 and eligible survivor controls242948; final counts
are709,435,1616,5657 respectively. Both phases have zero full resets and attenuations.

These facts technically accept this arm under the card's original counts and endpoint.
HALF_EVENT's trained result is absent, so `d_HR`, the branch and prediction scoring
remain pending. RETAIN's point does not select a replacement arm or change the fixed.5
coefficient. The two arms were already selected regardless of the first arm's score.

Monitor reports **4.476s** of measured queries, with twelve components preserved in the
summary; additional yielded query runtimes and messaging remain unmeasured. Its local
observation label00:00:52−07 conflicts with the native00:00:15Z terminal; preserve that
label but use supervisor/whole-chain clocks for elapsed. It has no scientific polarity.
After collection and acceptance arithmetic, known DM support is **18.5884657s**, plus
4.476s measured Monitor work: **23.0644657s known support**. The earlier bookkeeping
duration and omitted Monitor durations remain unknown, not zero; later publication,
HALF_EVENT support and required preservation are still to be charged. No complete300s
or3900s compliance is asserted. Unchanged short remaining support is still credible
within the allocation; no concrete exhaustion has been observed. No cost experiment,
support transfer or extra invocation is introduced.

The remote B02 worktree remains needed by the preselected second arm; retain its
evidence and RETAIN supervisor until complete-pair archive verification and scoped
closeout. No remote or local evidence has been removed. Primary owner reviews again
returned no unapplied items at this boundary.

## 7. HALF_EVENT accepted and observation adopted

RETAIN acceptance and its collection receipt were committed and immediately pushed
at **fb98e0fe8afab80d51553ac274b99479acfdaad2** before the second submission. The
HALF_EVENT command was checked against the original published ea73b1c3d payload;
source surfaces still matched **c6be208cd514b5d12fb13c7637e2d6376de11eb6**, and its
supervisor/output/memory paths were absent. No source or scientific input changed.

The sole remaining preselected arm was submitted at **2026-09-11T00:08:07.523443Z**;
explicit tmux-start returned **00:08:08.331457Z**, command exit0 and no stderr. Handle
`folr-public-lifecycle-half-b02-half-event-20260910` runs in the original B02 remote
worktree with output `public_lifecycle_half_b02_seed7808_half_event`. The original
receipt is retained under the B02 control root and in the result summary. Fresh
destination admission and the exact runner share the original outer 1800s chain.
This is accepted invocation **2 of 2**; no scientific allocation remains unsubmitted.

Direct MONITOR_ADD succeeded and Root confirmed actual adoption of this same handle,
source, cwd, output and supervisor root. No separate adoption observation time was
supplied; the tmux clock remains supervisor acceptance only. Monitor owns observation
and actual query-cost accounting; this DM stops routine remote polling and retains
terminal collection, technical acceptance, pair intake and verified scoped closeout.
Root routes the terminal fact to `/root/dm_folr_restart_recovery`.

Known invoked support through second submission and direct dispatch is **29.0471481s**:
24.5711481s DM plus4.476s measured RETAIN Monitor work. This excludes later publication
and the explicitly unmeasured bookkeeping/query/messaging durations; it is not a
complete bill or a 300s/3900s compliance claim. The caps and no-transfer rule remain
unchanged. No retry, third fitting pair, additional arm or successor is allocated.

## 8. HALF_EVENT terminal collection and technical acceptance

Root routed the original second handle's exit0 terminal. Supervisor start/end were
**2026-09-11T00:08:07Z /00:20:56Z**, integer769s. The complete outer chain measured
**768.73s**, below1800s, with744.43s user,25.62s system and678048KiB peak RSS.
Runner wall767.4672104330966s and peak646488KiB are nested measurements. Fresh
admission at00:08:08.011234Z measured physical/effective available memory
**15626715136 bytes**, both above4GiB before learner construction.

The [HALF_EVENT collection receipt](evidence/2026-09-10-folr-public-lifecycle-half-b02-half-event-collection.json)
verifies all **10 files /4676090 bytes** against remote originals. Together with RETAIN,
all **20 raw files /9351870 bytes** match their length/SHA256 records. Both checkpoints
are retained at4662779 bytes each. Source surfaces still matchc6be208cd; the final raw
log JSON equals the run summary, all25 progress rows show episode200..5000 and
updates=episode−31, and every expected count/seed/thread field matches the card.
No checkpoint was loaded and no new learner, evaluation or retry was invoked.

HALF_EVENT completed5000 train episodes/100000 ticks/4969 updates, then128 final
episodes/2560 ticks. Final mean is **5.17875**, conditional rollout sample SD6.96587;
training return sum is−18675.840000000044 and mean−3.735168. Train phase counts are
births21038, departures7507, event-survivor opportunities46657 and eligible controls
264581; final counts are574,232,1409,6517. Full survivor resets are zero in both phases.
Applied half attenuations equal event-survivor opportunities: **46657 train /1409 final**,
17.6343%/21.6204% of eligible controls. The counters describe actual acting exposure;
correct replay/acting conformance does not identify a causal explanation for return.

Technical acceptance is complete for both arms. Their total exposure is **10000 train
episodes /200000 training ticks /9938 RMSprop updates**, plus **256 final episodes /
5120 evaluation ticks =205120 native ticks**. All256 final returns and50 progress rows
remain in the summary. Whole-chain wall sums to **1517.20s** (within3600s); CPU sums
to1520.08s. Runner wall sum1515.5847928461153s is not added again. Study elapsed from
first supervisor start to final terminal is1990s, including the inter-arm collection/
publication gap; it is distinct from summed invocation wall and aggregate CPU work.

## 9. Frozen paired result, prediction and bounded reading

Using only the new matched7808 fitting instance and its fixed107808 final evaluation:

| Arm | Final mean native return | Cumulative training mean | Complete outer wall |
| --- | ---: | ---: | ---: |
| RETAIN | 9.471796875 | −.313516 | 748.47s |
| HALF_EVENT | 5.17875 | −3.735168 | 768.73s |

**`d_HR=5.17875−9.471796875=−4.293046875`.** The frozen rule
**`RETAIN_ABOVE_MEI: d_HR<=-1`** applies at absolute MEI1. The prospective DM
**WITHIN_MEI, low confidence** forecast missed; owner prediction is **not taken
(unattended)**. The old positive HALF-B01 point is retained separately and not pooled
into this reading. The earlier practical gain did not recur in this new instance.

The [run-level analysis](evidence/2026-09-10-folr-public-lifecycle-half-b02-run-analysis.json)
uses exactly two endpoint rows, one per fitted arm, paired by training-instance7808.
It reports one paired difference and no training-population SD or interval. The128
rollouts per arm are conditional evaluations; their indices are not paired native
worlds because policy-dependent RNG paths diverge. Cumulative training mean also
favors RETAIN by3.421652 as a separate observation, not a recorded learning curve.

This is a bounded loss of the complete fixed-.5 trained package to generic retention
in this fitting instance. It supports neither stable superiority of RETAIN nor a
general failure of attenuation. B01's+1.56546875 remains the strongest direct support
for this same law; the present−4.293046875 is direct contrary evidence. Useful history,
representation/optimization, action-dependent data and partner co-adaptation remain
possible contributors. No memory-content fraction, timing effect, causal staleness,
RANDOM/full-EVENT superiority, original-CAMA, headroom, transfer/UAV/C or Portfolio
claim follows. The allocation has no successor; there is no local family disposition.

## 10. Support accounting and preservation inventory

Monitor reports4.476s for RETAIN and16.431s for HALF_EVENT, **20.907s measured query
work** in total, attributed as reported for the named handles. Yielded RETAIN queries,
the HALF_EVENT post-loop terminal query and messaging were not fully timed. One
earlier DM bookkeeping command also lacks its elapsed receipt. These remain
**resources_unmeasured**, not zero. The native chains' times/RSS and required memory
admissions are measured; their trustworthy primary returns remain reportable.

Known DM work through collection/analysis-contract reads is32.9635344s, giving
53.8705344s known support before final analysis, publication and closeout. Later
measured work is added at its natural boundary in the summary. Full support300s and
complete3900s compliance cannot be certified from the incomplete support bill. No
measured overrun, source-scope budget breach or additional invocation was observed;
native savings do not fund support. Monitor's−07 local labels again conflict with
the native UTC terminal clocks; originals are retained and not used for elapsed.

Preserve the complete B02 detached source worktree, including ignored/raw evidence,
both completed supervisor roots and all local collected artifacts. No B02 input-stage
directory was created. The three exact remote roots are the worktree named in §2 and
the RETAIN/HALF_EVENT supervisor roots. Preserve a source recovery ref, compare every
archive member with its original before deletion, verify retained local archive bytes,
reconcile unchanged originals immediately before deletion, then verify disk and Git
worktree-registration absence. The shared local authoring checkout and older objects
remain intact. Root integrates published evidence and accepts reclamation.

## 11. Verified preservation and scoped closeout

The [archive verification receipt](evidence/2026-09-10-folr-public-lifecycle-half-b02-archive-verification.json)
and [remote closeout receipt](evidence/2026-09-10-folr-public-lifecycle-half-b02-remote-closeout.json)
record the completed preservation/removal sequence. All **2708 members** (2350 regular
files,358 directories,zero symlinks) were compared by content/type/mode with original
members before removal. This includes2692 worktree members and16 supervisor members.
`worktree.tar.gz` is17107603 bytes; `supervisors.tar.gz` is5000 bytes. Both retained
local archives, **17112603 bytes** total, match the verified remote SHA256/lengths.
The full member inventory and original verification receipt are retained with them.

Archive/original verification completed **2026-09-11T00:34:08.186904Z**; local archive
preservation passed **00:35:16.478752Z**. Original content/metadata were rechecked
unchanged immediately before removal at **00:36:44.727865Z**. Disk absence for all
three exact completed roots, plus worktree-registration absence, was verified at
**00:36:44.836110Z**. The source worktree was removed through Git worktree removal;
only the two named completed supervisor roots were removed with it. No rejection or
fallback deletion occurred. No input stage existed for this object.

Retained archives live under the B02 local control root's
`folr-public-lifecycle-half-b02-20260910/` directory and the remote recovery directory
of the same name. All local `collected/` raw files, checkpoints and receipts remain.
Control and compute Git both retain `refs/archive/folr-public-lifecycle-half-b02-20260910`
at exact sourcec6be208cd514b5d12fb13c7637e2d6376de11eb6. The shared local
`C:/Projects/HMASD-worktrees/codex-vap-folr` checkout and all older objects remain
intact. Root integrates the published result/closeout commits and accepts reclamation.

Known support through verified closeout and the final owner/artifact checks is **67.6955750s**
(46.7885750s DM +20.907s measured Monitor queries). This final publication
command is reported separately in the handoff. Missing historical support durations
remain unmeasured; no complete300s/3900s compliance is certified. Native whole-chain
wall is1517.20s and both arm caps passed. Primary owner reviews returned no unapplied
items. The paired result, prediction score and no-successor allocation are unchanged.
