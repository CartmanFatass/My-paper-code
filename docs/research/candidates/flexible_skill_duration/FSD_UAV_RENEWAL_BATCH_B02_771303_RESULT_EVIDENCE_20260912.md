# FSD B02 / 771303 — result evidence

## Result and rule applied verbatim

**Valid complete B/EXPLORE; one matched training pair; `above_mei`.**
The [frozen card](FSD_UAV_RENEWAL_BATCH_B02_771303_SCIENCE_CARD_20260912.md)
states the applicable rule:

> - Mean >+.01: `above_mei`; one additional local package gain.

Mean I1280−authentic-D0 is **+0.0737976491890039 J**, sample SD
**0.07383768297210358**, conditional episode SE **0.013052781584169226**.
The 32 ordered differences contain **26 positive, 6 adverse, 0 zero**, from
−0.07174403514448635 to +0.20940931815020936. This is one additional native
package gain above the .01 MEI. It does not establish stable superiority.

[PAIRED_EPISODES.csv](uav_renewal_batch_b02_771303_20260912/PAIRED_EPISODES.csv)
retains every ordered raw U, native J=6U/500 and contrast.
[PAIR_ANALYSIS.json](uav_renewal_batch_b02_771303_20260912/PAIR_ANALYSIS.json)
records the unchanged source publication and independent standard-library
reduction, which agree. The source's JSON-only publication functions were
extracted without constructing a model or importing the training execution path.
[RUN_SUMMARY.json](uav_renewal_batch_b02_771303_20260912/RUN_SUMMARY.json) uses
the scientific-tools run summarizer on one declared matched training endpoint
per arm; n=1 and training-run SD undefined. No previous pair, endpoint world or
checkpoint becomes another training replicate or enters this pair's primary.

## Native components and separate sampled training

| Final observable | D0 | I1280 | I−D0 |
| --- | ---: | ---: | ---: |
| Native J | 0.420867347699 | 0.494664996888 | +0.073797649189 |
| Coverage | 0.530140000000 | 0.618725000000 | +0.088585000000 |
| Quality | 0.183757450903 | 0.206551967925 | +0.022794517022 |
| Altitude penalty | 0.005357887572 | 0.000408093490 | -0.004949794082 |

The unchanged native objective is .7×coverage + .3×quality − altitude penalty
(source field energy_penalty). All 32 component reconstructions agree with J.
Higher coverage contributes +.0620095, higher quality +.006838355106713001,
and lower altitude penalty +.004949794082291005. These are reward-accounting
facts, not an explanation of the cause of learned spatial behavior.

| Rollout | D0 sampled training J | I1280 sampled training J | I−D0 |
| --- | ---: | ---: | ---: |
| 1 | 0.241012726202 | 0.241577709096 | +0.000564982894 |
| 2 | 0.222734235557 | 0.189436582872 | -0.033297652685 |
| 3 | 0.269838970594 | 0.265381217187 | -0.004457753407 |
| 4 | 0.258503591217 | 0.249621699764 | -0.008881891453 |
| 5 | 0.273082191444 | 0.338691266230 | +0.065609074786 |

I is lower on sampled training rollouts 2–4. The final endpoint remains the
sole card primary; these phase facts add no evaluation panel or selection.

## Actual exposure and preserved meaning

Two real fits/four models completed ten update stages, 80,000 training team
ticks/160 episodes and 32,000 final ticks/64 episodes. Total native exposure is
112,000 team ticks, 672,000 agent opportunities and 6,000 batched controller
calls. There were no checkpoint loads, pilot runs, extra panels or retries.
All five learner modules moved at every update; evaluator optimizer calls are zero.

Both arms preserve scenario1/six fixed UAVs/fifty users/H500, CPU FP32/four
Torch threads, legal local information, private reactive primitive actions,
lane-owned reset/continuing-agent recurrent state, primitive discount, valid
segment credit, lower PPO and isolated evaluator RNG/mode/synchronization.
I is gap .25/batch1280; authentic D0 is infinity/batch128. Partner renewal
retains continuing skills/state; a held skill does not hold primitive action.
This compares the full package, including changed data and advantage grouping.

I has 42,750 individual training gap causes and 24,818 joint rows, versus
0 and 4,000 for D0. I's per-rollout joint rows 4887/5100/4928/4746/5157 give
coordinator steps 60/60/60/60/75, total 315, under the original
15×sum ceil(M_r/1280) cost law; D0 has 525. Each arm has 11,250 actor,
11,250 critic, 75 team-discriminator and 300 individual-discriminator steps.
I's mean training agent segments range from 3.476 to 3.694 ticks versus D0's
10; team segments remain 10. Fewer coordinator steps do not equalize the
complete decoder, credit-row and recurrent work or isolate batching.

The final I panel records 2 individual gap causes versus 0 D0; both record
32 resets and 1568 team-cap events. Endpoint segment storage is empty, so
endpoint duration is unmeasured. Sparse endpoint activity does not establish
whether renewal, grouping, learning-history variation or learned motion caused
the gain. Tuned same-information host headroom remains absent.

## Support, contradiction and claim ceiling

The four previous same-package primaries remain separate: +.0569774672,
+.2062859041, −.0124304306 and +.0125548057. This fifth observation adds
+.0737976492; there are four above-MEI readings and one opposite-sign reading,
with no pooled primary or fixed adequacy threshold. Strongest support is the
large earlier +.2062859041 and this additional native gain. Strongest contrary
evidence remains the unchanged negative pair, this panel's six adverse worlds,
mid-training deficits and I's 2.15342× D0 wall. Older batch128 losses
−.0496705632/−.0353127253 retain their different-package meaning.

The claim is bounded optional-package value on this host and learning history.
Stable advantage, component causality, longer-budget value, transfer and safety
are unresolved. FSD remains scientifically valuable under OWNER_DIRECT; this
finite allocation's completion does not stop or park the direction.

## Technical acceptance, costs and preservation

Exact source 8ea629595da592dfce9b7774341863a7115c7cef; one source delivery,
two detached commands and two fresh adjacent admissions. Both supervisors
finished/exit 0. Both actual unfinished Monitor goals were adopted and then
completed after terminal delivery, with active_set empty. The original runtime
cwd/output and companion digest conform. D0's initial collection assertion
mistook two empty log directories for extra files; the recursive file check
resolved that documentary issue without another run or a data/source change.

| Complete command | Wall seconds | User+system CPU seconds | Peak RSS KiB |
| --- | ---: | ---: | ---: |
| D0 | 458.80 | 1804.26 | 1673964 |
| I1280 | 987.99 | 3914.20 | 3492180 |
| Sum | 1446.79 | 5718.46 | — |

The D0≤900, I≤1800 and native≤2700 caps pass. The sole source helper took
6.344 seconds, within 45 seconds. SUPPORT.json records known support charges
once; unmeasured support/attribution and publication/cleanup tails remain
explicit as resources_unmeasured. Partial telemetry does not certify complete
300/3000-second compliance. No observed cap or Engineering Scope §5 breach,
and no new §4 machinery. Validity follows the intact dependent measurement.
Supervisor D0-start→I-terminal elapsed time is 1911 seconds at one-second
resolution, separate from summed native wall and aggregate CPU.

D0_collection.tar.gz and I_collection.tar.gz preserve all 22 original raw files.
Their published Git blobs match both archives and the collected digests;
RETENTION_CHECK.json records that verification at 476e2e64a. The exact source
worktree is clean with only the six known ignored outputs. CLEANUP_INVENTORY.json
names four terminal remote targets, with removal pending Root's retained-evidence
acceptance. Shared authoring and shared remote source remain in use and outside
cleanup. No new experiment or scientific consultation is included in N closeout.
