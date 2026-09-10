# RCLE B03 S20 technical result evidence — 2026-09-09

**Technical acceptance: PASS.** The one allocated fresh seed20 pair and reference are
complete. Source4d96a832eeaa875b2e6178bd9014067ce32d0339; scientific freeze2da8ec66,
Root allocationfb4f3e0ae. [Card](RCLE_B03_S20_SCIENCE_CARD_20260909.md),
[CM/review record](RCLE_B03_S20_CM_RECORD_20260909.md),
[exact launch](RCLE_B03_S20_LAUNCH_20260909.md).
No extra fit, panel, retry, native probe or diagnostic was performed during collection.
DM owns scientific intake and the next decision; no successor is allocated.

## Primary and complete publication

| ACTIVE_CONTINUATION path | W1 U | W100 U | Init U | W1−W100 | Conditional SE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8→12 | 0.6876790364583333 | 0.6777587890625 | 0.68916015625 | 0.009920247395833335 | 0.0016407600424031047 |
| 12→8 | 0.710595703125 | 0.7018676757812501 | 0.71048583984375 | 0.008728027343749997 | 0.0023602243253760744 |

Equal-path Delta_U **+0.009324137369791666**, SE0.0014372501854969077;
approximate conditional95% interval[0.0065071270062177266,0.012141147733365606].
G_U_W1=0.0006856282552083343; G_U_W100=0.010009765625. W1's12→8 gain is
−0.000109863281250002; preserve this path-level deterioration.
Arithmetic was independently reconstructed from the actual new W1/W100 rows and
matched the emitted primary. Each cell carries256 matched unique indices0…255;
distinct cell-domain uncertainty is conditional on the fitted policies, not training variance.

All eight learned U means favor W100; all learned final and init tau values are40.
Eight-cell W1/W100/reference U:0.7001439412434896 /0.6903803507486979 /0.28551025390625.
Corresponding Y:0.30066776275634766 /0.3112955093383789 /null; reference null retains
`ScriptedEpisodeResult has no Y; Y is null`. Reference tau mean39.400390625,
tau40 fraction0.97998046875. Reference is the unchanged achievable simple level, not
an upper or tuned baseline. H_A1 remains unidentified.

| Final-roster12 cell | W100−W1 fragmentation F |
| --- | ---: |
| 12→12 ACTIVE_CONTINUATION | −0.00035807291666667407 |
| 12→12 NEW_EPOCH | −0.0005859374999999944 |
| 8→12 ACTIVE_CONTINUATION | +0.0027018229166666796 |
| 8→12 NEW_EPOCH | +0.0011393229166666574 |

Every cell's U/Y/tau/F difference and levels are retained; F is not the reward.
The [full summary](RCLE_B03_S20_RESULT_SUMMARY_20260909.json) contains primary,
all-cell means, initial means, final baselines, receipts, native/source identity,
supervisor bytes and23 verified output/supervisor file hashes.
[SCENARIOS.csv](b03_actor100_s20_20260909/SCENARIOS.csv) publishes all8192 rows across
init/W1/W100/reference; [CURVES.json](b03_actor100_s20_20260909/CURVES.json) publishes
all400 update records, each with eight cell Y/U/tau/F curves. No endpoint or cell selected away.

## Actual generating inputs and learning acceptance

All three summaries carry seed20, reporting objectRCLE-TBCFV-B03-ACTOR100-S20,
launch source4d96a832e, root065798a1a4115ac244accada16fc267f814deb622cfd05b9657418892c656e3b
and block digestff12639b17ff1d6ab0297322f7a62ffcdd7cc8b3d1c6d718e22ceeaeee623516.
The original RNG namespace/block0/packageFLEX remain; reporting labels are outside addresses.
Native source18d45b95a29c1ca8d17b4d192a9328ddc9c56a821a2690f118de44dbf0054819
and artifact5b918da7e23d7b65251fb20efcb6678e4a17e62538f6ebdedbda1d9e96221983
match across the three invocations; ABI/toolchain details are in the summary.

Both initial checkpoint dictionaries were loaded as tensors, not models. All26161
FP64 scalars match exactly within the pair and differ from retained seed19 tensors.
Initial norm21.169477626755096; measured final displacements W1 0.39759874927951655,
W1000.5640297973052217, independently reconstructed from final tensors. Fresh source
constructs initial models and zero baselines without any checkpoint/control model load.
Starting from eight zeros and applying the unchanged0.95/0.05 recurrence to all retained
cell Y curves reproduces each final baseline vector (maximum differences4.44e−16 and
3.89e−16). This checks zero-start consistency; no new learner call was made.

Both200-row completed_blocks.jsonl files exactly match the corresponding summary curves;
update indices0…199,64 episodes/4096 ticks per block, eight cells×eight, step-before-baseline,
all400 nonzero steps and measured delta norms0.02. Each final model moved from initialization.
W100 used only the fixed new-root W1 summary; its primary matches reconstruction from
that collected summary and its own panel. No historical fitted state or unknown prefix reused.
No scientific reward/information/model/loss/native change was introduced by the seed plumbing.

## Exposure and frozen branch facts

New total33792 episodes/2162688 primitive ticks/400 backward-step calls;12 allocations
comprise2 fits and10 untrained helpers. Training25600 episodes/1638400 ticks; four panels8192
rows/524288 ticks. Each fit has200 nonzero/zero0 steps. Training agent ticks6553600 and
claim decisions1638400 per fit are additional counts, not independent experimental units.
The focused supplied-output check had no model/native/backward exposure; its synthetic
update records are excluded from all scientific counts.

Known B03 cumulative total is67584 episodes/4325376 ticks/800 calls plus the unchanged
unknown original failed-W100 prefix bounded by12800/819200/200. Nominal80384/5144576/1000
are bounds, not measurements. Thirty scientific allocations include five started fits
(one old failure) and25 helpers. This adds one independent training pair; old seed19
Delta_U+0.013224283854166657, all four old final-roster12 F losses and historical failure
remain alongside this result. No evaluation-row pooling or training-population claim.

The original card's nine overlapping branch conditions are preserved. Direct facts:
Delta_U is positive below0.05 (small-positive row); absDelta_U<0.05, both G_U small and
tau saturated (end-this-spend/return-to-selection row). Neither MEI-level positive nor
zero/adverse Delta_U rows apply; neither G_U reaches0.05; W100 G_U is positive; primary
paths agree and the conditional interval does not cross0 or0.05. No damaged-primary
condition observed. F companions contain two losses and two improvements; no U/tau
reverse tradeoff is hidden. These are measured conditions, not an automatic next allocation.
No pure actor-credit cause, stable superiority, recovery-time success or UAV claim follows.

## Runtime and complete cost

wsl_4070 CPU FP64/thread1; one shared detached supervisor with three sequential interpreters.
W1 admission23:05:00.781170Z:15209025536 bytes physical/effective; W10023:06:30.650915Z:
15215370240; reference23:07:51.320271Z:15197548544. All exceeded4GiB immediately before
its own runner. Source-only staging failures occurred before scientific submission and
were resolved with the identical committed-object bundle; their charge remains included.

Monitor actual adoption23:05:47.1858946Z, terminal observation23:08:07.1818809Z;
actual supervisor exit23:07:54Z, statusfinished/exit0/tmuxfalse, PID3079849, integer duration174s.
Root resumed this original CM for collection; no parallel routine CM/DM polling.

Complete process wall W1 **89.83s≤600**, W100 **80.62s≤600**, reference **2.85s≤30**;
sum173.30s. Sequential chain including admissions **173.43s≤1150**, charged once rather
than adding the arm sum again. Peak RSS W1/chain591868KiB, W100591164KiB, reference429380KiB.
These are runtime observations; admission estimates alone do not establish resource use.
Aggregate CPU and common whole-study elapsed remain unmeasured, not zero or equal to wall.

Preserved conservative prelaunch debit250s includes15s DM,8.5911985s focused check and
source-staging delays. Measured collection3.6190638s and complete tensor/arithmetic readback
2.2984716s are inside a conservative25s collection/publication charge, including final
short Git/document operations. **Technical complete charge448.43s =250+173.43+25**, below1500.
This leaves75s of the originally reserved100s publication/support window for subsequent
DM intake; no new experiment is authorized by any unspent balance. Previous named
B03-window261.3980053s remains separate: sum709.8280053s through this technical result,
not a full-history elapsed/CPU measure. DM adds its actual intake support explicitly.

## Retention and next owner

Shared source and evidence are committed/pushed; release index to original DM for full
scientific intake/brief/prediction and owner records. Root accepts integration and later
triggers scoped closeout. Retain remote checkout `/home/wu/hmasd-worktrees/rcle-b03-s20-20260909`,
supervisor `/home/wu/.agent-tasks/rcle-b03-s20-20260909`, and source-only bundle stage
`/home/wu/hmasd-inputs/rcle-b03-s20-20260909` until verified preservation/removal is authorized.
Local scientific raw root is `temp/directions/roster_consistent_latent_exploration/exp/b03-actor100-s20-20260909`;
local preparation/supervisor/hashes/check receipt are under the adjacent `s20-preparation/`.
Native cache, old evidence, shared authoring and blocked historical scratch stay untouched.
No remaining technical gap limits the primary; scientific interpretation belongs to DM.
