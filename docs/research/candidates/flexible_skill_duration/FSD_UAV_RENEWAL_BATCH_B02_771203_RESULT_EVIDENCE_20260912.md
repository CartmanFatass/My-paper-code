# FSD B02 / 771203 — result evidence

## Result and rule applied verbatim

**Valid complete B/EXPLORE; one matched training pair; `above_mei`.**
The [frozen card](FSD_UAV_RENEWAL_BATCH_B02_771203_SCIENCE_CARD_20260912.md)
states the applicable rule:

> - Mean >+.01: `above_mei`; one additional local package gain.

Mean I1280−D0 is **+0.012554805665750726 J**, sample SD
**0.07074935212229413**, conditional episode SE **0.01250683666255726**.
There are **19 positive/13 negative/0 zero** ordered differences, ranging from
−0.11208704599634545 to +0.18244350591515257. This mean is only
.002554805665750726 above the .01 MEI; its relative value is +3.89356% of D0.
It is a small local gain under the frozen branch, not stable superiority.

[ORDERED_PRIMARY.csv](uav_renewal_batch_b02_771203_20260912/ORDERED_PRIMARY.csv)
retains all32 raw U, native J=6U/500 and ordered contrasts.
[PAIRED_ANALYSIS.json](uav_renewal_batch_b02_771203_20260912/PAIRED_ANALYSIS.json)
matches the source-defined complete paired publication; independent Python
statistics give the same reading. [RUN_SUMMARY.json](uav_renewal_batch_b02_771203_20260912/RUN_SUMMARY.json)
uses one final endpoint per arm/training identity, n=1, undefined training-run
SD. No earlier pair, checkpoint or episode is pooled into this primary.

## Native components and separate sampled training

| Final observable | D0 | I1280 | I−D0 |
| --- | ---: | ---: | ---: |
| Raw U | 26.870870131337 | 27.917103936816 | +1.046233805479 |
| Native J | .322450441576 | .335005247242 | +.012554805666 |
| Coverage | .490213750000 | .498823750000 | +.008610000000 |
| Quality | .140431472034 | .129217916836 | −.011213555198 |
| Altitude penalty | .062828625034 | .052936752809 | −.009891872225 |

The unchanged native objective is .7×coverage + .3×quality − altitude penalty
(the existing source field is named energy_penalty). All32 reconstructions
agree with J. Coverage adds .006027 and lower altitude penalty adds
.009891872225; lower quality subtracts .003364066560. This accounts for the
observed gain without explaining the causal origin of learned motion.

| Rollout | D0 sampled training J | I1280 sampled training J | I−D0 |
| --- | ---: | ---: | ---: |
| 1 | .232473724606 | .240126685076 | +.007652960470 |
| 2 | .253550370913 | .239311954714 | −.014238416199 |
| 3 | .272560664947 | .234561763523 | −.037998901424 |
| 4 | .272889893221 | .224760040473 | −.048129852747 |
| 5 | .275979996737 | .310460427770 | +.034480431033 |

I is lower on sampled training rollouts2–4. These facts are separate from the
sole final endpoint, not extra evaluation panels or checkpoint selection.

## Exposure, semantics and interpretation limits

Both arms preserve scenario1/six fixed UAVs/fifty users/H500, CPU FP32/four
Torch threads, identical legal information, private reactive recurrent action,
lane reset/survivor state, primitive discounts, segment credit and evaluator
RNG/mode/sync. I retains gap.25/batch1280 versus authentic D0 infinity/batch128.
Individual renewals keep partner state; held skills do not hold primitive action.
Larger grouping changes normalized advantages and optimizer/data histories.

Actual exposure: two real fits/four models; 80000 training team ticks/160
episodes/ten update stages; 32000 final ticks/64 episodes; 112000 total native
ticks,672000 agent opportunities,6000 batched controller calls. No checkpoint
loads, extra panels, search or replay. Every learner module moved, every stage
optimized, evaluator optimizer calls are zero.

I has47196 individual training gap causes and26340 joint rows versus0/4000 D0.
Its row counts5018/5198/5123/5129/5872 produce coordinator calls60/75/75/75/75,
total360; D0 makes525. Both make11250 actor,11250 critic,75 team discriminator
and300 individual discriminator steps. I training segments average about3.53,
3.47,3.50,3.33,3.07 primitive steps versus10 D0. Fewer coordinator steps do not
equalize decoder/row/recurrent work or isolate a batching effect.

The final I panel has8 individual gap causes versus0 D0, with556 versus549
coordinator inference calls. Both have32 resets and1568 team-cap events.
This is sparse endpoint renewal, not evidence that those events caused the gain.
Endpoint durations remain unmeasured because evaluator segment storage is empty.

The three previous same-package primaries remain separate: +.0569774672,
+.2062859041, −.0124304306; older batch128 losses −.0496705632 and−.0353127253
remain different-package evidence. The current fourth package observation adds
a near-MEI gain with13 adverse episodes and2.19548× D0 wall. Training-instance
variation and learned spatial behavior remain viable explanations. Tuned
same-information headroom is absent. No stable seed, isolated renewal/batching,
longer-budget, transfer or safety claim follows.

## Technical acceptance, cost and preservation

Source9eb99f8b68dd2863212c10693b911746a6d24354; two exact detached commands,
one successful source delivery, both fresh destination admissions passed.
Both supervisors finished/exit0, PIDs and tmux absent at collection. Both actual
unfinished Monitor goals were adopted and completed with terminal delivery and
active_set empty. D0's shortened chat cwd was corrected from original
supervisor/source/output bytes; it was not an execution or science defect.

| Complete command | Wall seconds | User+system CPU seconds | Peak RSS KiB |
| --- | ---: | ---: | ---: |
| D0 | 475.03 | 1869.43 | 1663808 |
| I1280 | 1042.92 | 4129.99 | 3476952 |
| Sum | 1517.95 | 5999.42 | — |

Native arm and sum caps pass. The source helper took6.063s, within its sole45s
transaction. SUPPORT.json maintains known support charges through cleanup and
publication, with explicitly unmeasured terms preserved. Partial support
telemetry is `resources_unmeasured`, not zero or full
300/3000s certification. No observed cap or Scope §5 breach; no new §4 machinery.

D0_collection.tar.gz and I_collection.tar.gz preserve22 original raw files,
accepted at main42a483997. The archived files and all remote digests matched
before cleanup; the exact-SHA worktree was clean with only six known ignored
outputs. All four targets in CLEANUP_INVENTORY.json were removed after Root
retention acceptance; CLEANUP_RECEIPT.json verifies disk/Git-registration absence.
Shared authoring, other worktree registrations and old evidence stay intact.
The allocated pair ends at full
intake/closeout: no retry, fifth pair, extra panel, consultation or successor.

Supervisor timestamps put the D0-start→I-terminal elapsed path at1798s
(one-second resolution), including inter-arm collection/publication. This is
separate from1517.95s summed native wall and5999.42s aggregate CPU; no study cap
is inferred from the calendar interval.
