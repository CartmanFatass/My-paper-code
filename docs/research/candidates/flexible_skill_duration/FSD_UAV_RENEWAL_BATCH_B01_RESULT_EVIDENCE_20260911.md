# FSD UAV renewal batch B01 / 770703 — result evidence

## 1. Result and rule applied verbatim

**Valid complete B/EXPLORE; one matched training pair; `above_mei`.**
The [card §5](FSD_UAV_RENEWAL_BATCH_B01_DESIGN_CARD_20260910.md#5-exact-prospective-observation-and-all-sign-reading)
and its reading rule remain unchanged. Both exact commands ran on
`hmasd-wsl-node`, CPU FP32/four Torch threads, at source
`c70f01ea30d6c4d063dcc46d8499b26bfe037da8`.
The card row applied verbatim is:

> | Greater than +.01 | One local package gain; preserve both old losses. Consider one separately selected independent repetition if its work is worthwhile. |

D0 mean native J is **0.4162744505394423** and I1280 is
**0.47325191775912245**. The 32 ordered I1280−D0 differences have mean
**+0.05697746721968016**, sample SD **0.13685461584668487** and conditional
SE **0.024192706725467705**. There are **24 positive, eight negative and zero
zero-valued** differences; range −0.3817552181578228 to +0.34339361701587157.
The gain is 13.68747641029713% of this D0 mean; the declared rule uses absolute .01.

This is one independent matched training pair, not 32 learning samples.
Conditional endpoint uncertainty cannot estimate training-seed uncertainty.
Every raw U, scaled J and ordered difference is in
[ORDERED_PRIMARY.csv](uav_renewal_batch_b01_770703_20260911/ORDERED_PRIMARY.csv); both complete native summaries
and five-row training logs are retained beside it. No old result is pooled.
[PAIRED_ANALYSIS.json](uav_renewal_batch_b01_770703_20260911/PAIRED_ANALYSIS.json) agrees with the runner's full
ordered reduction. The required [run-summary input](uav_renewal_batch_b01_770703_20260911/RUN_SCORES.csv) has
one endpoint row per arm/training instance, and its
[output](uav_renewal_batch_b01_770703_20260911/RUN_SUMMARY.json) correctly reports n=1 with no sample SD.

## 2. Native reward and separate training observations

Learner reward U is unchanged; reporting uses `J=6U/500`.
The native objective remains `.7*coverage + .3*quality - altitude_penalty`;
the existing `energy_penalty` field stores that altitude term.

| Final observable | D0 | I1280 | I1280−D0 |
| --- | ---: | ---: | ---: |
| Raw episode U | 34.689537544953524 | 39.437659813260204 | +4.74812226830668 |
| Native J | .4162744505394423 | .47325191775912245 | +.05697746721968016 |
| Coverage | .5233575000000001 | .6095600000000004 | +.08620250000000029 |
| Quality | .16859029594450917 | .1812237355268749 | +.012633439582365735 |
| Altitude penalty | .0006528882439104148 | .007807202898939975 | +.00715431465502956 |

Weighted coverage contributes +.0603417500000002 and quality
+.0037900318747097206, while higher altitude cost contributes
−.00715431465502956. These sum to the native contrast. This is accounting,
not a causal explanation of the learned motion.

| Rollout | D0 sampled training J | I1280 sampled training J |
| --- | ---: | ---: |
| 1 | .25233067232951384 | .23514736862826457 |
| 2 | .2392202534739341 | .2131000463477556 |
| 3 | .1582849134046337 | .23215681587751202 |
| 4 | .21377952863425612 | .2912050517454202 |
| 5 | .18941985529625777 | .3078861007749171 |

I1280's first two sampled training means are lower and last three are higher.
These are the actual training data, not extra evaluations or checkpoint selection.

## 3. Mechanism path, exposure and contrary evidence

Both arms preserve six UAVs/fifty users, current legal observation and primitive
recurrent actor response. I1280 permits individual renewal at gap .25; D0 uses
infinity, with the shared team clock/caps10. Only the two declared configuration
fields differ: individual threshold and coordinator batch1280 versus128.
Returned rewards and renewal segments reach the native shared learner without
an information, reward, precision or endpoint substitution.

I1280 has **42243** individual gap causes during training; D0 has zero.
I valid joint rows per rollout are5215/4448/4769/4942/5125 versus800 each D0.
The exact coordinator law `15*sum ceil(M_r/batch)` yields **330 versus525**
actual calls (75/60/60/60/75 versus105 each). Thus calls fall37.14% while
valid rows total24499 versus4000, a6.12475× ratio. The change does not remove
row/decoder work or preserve identical gradients/advantage normalization.

Every stage has nonzero optimizer counts and finite nonzero parameter movement.
Both arms have11250 actor and11250 critic calls,75 team-discriminator and300
individual-discriminator calls. Final relative coordinator movement from
initialization is.04270731322134893 I versus.042214461382935886 D0.
I's training individual segment means are3.45/3.90/3.72/3.64/3.45 versus10 D0.

At final evaluation, I has **eight** individual gap causes and D0 zero, with
32 resets and1568 team-cap events each. This is sparse nonzero endpoint renewal,
not the identical timing observed in the older pairs. Evaluator segment storage
is empty, so endpoint duration statistics remain unmeasured; primary returns and
decision counters are intact. The evidence does not identify the eight events'
causal contribution or establish a deployed-renewal advantage.

P70 **−.049670563167111874** and P72 **−.035312725297886094** remain the
strongest historical contradiction to broad benefit. They used the original
I batch128 and different training identities; their scores/checkpoints never
entered this comparison. Their narrower component/training positives remain.
The new native gain supports this package on one instance; it does not show
that increasing the batch caused a reversal or that the package is reliably better.
Tuned same-information UAV headroom remains absent.

Machine-generated actual exposure: **two fits, four models,80000 training
steps/160 episodes/ten update stages;32000 evaluation steps/64 episodes;
112000 total native steps/672000 agent-step observations/6000 batched control
calls; zero checkpoint loads, extra fixtures or validation episodes.**
Intake calculations use preserved bytes only, with zero new learner/environment work.

## 4. Technical acceptance, complete time and limitations

The unchanged accepted entry/shared source and prior focused fixture/review are
reused. New checks cover exact source/identity/configuration, full learning and
endpoint counts, finite data, nonzero learner movement, zero evaluator updates,
raw/native scaling, component accounting and the dependent paired publication.
Both exits are0; both memory admissions pass on the actual node. Collected primary
and admission/time bytes match their remote digests. The initial manifests
predate construction; final summary/training records carry completed learning.

| Complete arm | Wall seconds | Cap | Aggregate CPU seconds | Peak RSS KiB |
| --- | ---: | ---: | ---: | ---: |
| D0 | 519.94 | 900 | 2043.57 | 1620164 |
| I1280 | 1020.68 | 1800 | 4037.22 | 3544424 |
| Sum | 1540.62 | 2700 arm allocation | 6080.79 | not additive |

I uses1.96307× D0 wall. First supervisor start through final supervisor exit is
1982s of study elapsed, distinct from summed invocation wall and aggregate CPU.
Existing OS whole-invocation CPU accounting adds no profiler or learner instrumentation.

**Both arm caps are verified. Support≤300s and complete≤3000s are not fully
certified.** [SUPPORT.json](uav_renewal_batch_b01_770703_20260911/SUPPORT.json) retains known execution charges;
ten earlier Monitor loop command walls and some adoption/native-message
attribution are explicitly unknown. Known I observation commands cost6.893s;
known D0 terminal query costs.598s, a subset of a reported shared1.423s.
Shared time is not added again. No missing value is silently zero, and no
observed cap breach is asserted. Mark `resources_unmeasured` for this partial
support telemetry. Arm wall/RSS/admission and learner-side measurements are present.

This accounting gap limits complete-cost certification; the final native primary
does not depend on Monitor query durations. Evidence-spec §11.8.7 therefore
preserves the valid bounded scientific observation. No frozen meaning is changed,
no retrospective retry is granted, and no C object is consumed.

Exact commands, adoption/terminal routes and receipts are in the
[execution record](FSD_UAV_RENEWAL_BATCH_B01_EXECUTION_20260911.md).
The [intake](FSD_UAV_RENEWAL_BATCH_B01_INTAKE_20260911.md) records decisions,
prediction scoring and the four-path cleanup boundary.
