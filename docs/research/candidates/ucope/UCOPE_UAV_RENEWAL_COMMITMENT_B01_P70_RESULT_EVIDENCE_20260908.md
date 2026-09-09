# UCOPE renewal B01 P70 — native result evidence

**B/EXPLORE, valid UP on one matched training pair.** Renewal T has an above-MEI
native gain over this G fit and over untuned hover H. G's slightly negative
hover contrast prevents an improvement-over-competent-control conclusion.
The [machine-computed summary](UCOPE_UAV_RENEWAL_COMMITMENT_B01_P70_RESULT_SUMMARY_20260908.json)
retains all 96 final returns and all three signed paired-difference vectors.

## E0.1 Object, frozen inputs and actual invocation

Object `UCOPE-UAV-RENEWAL-COMMITMENT-B01`, master **7301**, selector
`renewal_b01`. Original [card §§1–7](UCOPE_UAV_RENEWAL_COMMITMENT_B01_SCIENCE_CARD_20260908.md)
are frozen at `ec82119adb83044ac9eff346a4779d3aceffa334`. The Pro RECAST is
`a54cda020bbcdb5a8fefdd5323fcc5221705f9e8`; P70's actual allocation is
`d749a6a26e450219d4d2f563a3256bc8f6b4fc00`. Source acceptance/P69 remains
separate from this real invocation.

- Scientific source: `a453447cb011d50c6bb63ed7fc40180134a914b5`.
- Literal payload: `345e41b2f83b9ebe86725c9099bf2f5d295358cf`.
- CM terminal collection/technical record: `d165366d815fa6c926023b6e9d9dbf43a93e35fa`.
- Node: configured `hmasd-wsl-node`, CPU FP32, one Torch thread.
- Supervisor: `ucope-uav-renewal-b01-7301-p70-20260908`.
- Remote cwd: `/home/wu/hmasd-worktrees/ucope-uav-renewal-b01-7301-p70-20260908`.
- Output relative to cwd: `temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908`.
- Local collection: the same relative path under
  `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`.

One accepted detached submission; CM retained sole observation through
collection. The raw supervisor log records start **2026-09-09T12:48:23+08:00**
and exit **2026-09-09T12:53:28+08:00**, code **0**. The collected terminal
readback reports finished, PID 3020108, inactive tmux and the exact scientific
SHA. Its later snapshot uptime is not the measured execution wall.
Native runner status is **COMPLETE**, with no limit entries or cap breach.

CM verified all 2176 materialized source files, the canonical preflight helper
and staged literal inputs before submission. The executed 707-byte LF wrapper
has SHA256 `d004393622f42a05b66917f8acf3a2fab2bab0f9579a11f849d2a80ddcfdadb8`.
Fresh admission at **2026-09-09T04:48:23.972732Z** recorded physical and
effective available memory both **15639891968 bytes**, above **4294967296**,
before scientific-state creation. Supervisor and scientific receipt copies
are identical. Acceptance, admission, observed learner progress and native
completion are separately recorded in the
[technical record](UCOPE_UAV_RENEWAL_COMMITMENT_B01_TECHNICAL_ACCEPTANCE_20260908.md#p70-terminal-execution-and-collection-acceptance).

## E0.2 Native estimand and rule applied verbatim

For each final episode, `J=sum_t sum(info['rewards_dict'].values())/256`.
The primary is the mean of the 32 matched-episode T−G differences. DM read-only
analysis confirms every recorded `J=reward_sum/256`, final IDs 0..31 and
matched reset association, all three paired vectors and their published means
and conditional evaluation SEs. No simulator, checkpoint rollout or CM suite
was repeated.

Applied card §5 rule, verbatim:

> Delta>+0.01: preliminary favorable renewable-package evidence on this task, fit and budget; consider a separately justified bounded follow-up, without allocating it automatically.

Comparator qualification, verbatim:

> Weak/negative G−H narrows improvement-over-competent-control wording without erasing trustworthy T−G. Positive T−H never reverses primary loss.

`Delta=+0.055673191348834944` exceeds +0.01 by **0.04567319134883494**:
**UP** under the unchanged point rule. Conditional evaluation SE is
**0.011556059794903147**. This SE concerns the 32 evaluation pairs conditional
on the fitted policies; independent training **n=1** supplies no training-
population SD or interval. The run-level utility receives one selected final
endpoint per trained T/G arm and one declared matched training seed. H remains
an untuned fixed reference, not another independent trained replicate.

## E0.3 Complete native outcomes

| Arm | Final mean J | Evaluation episodes |
| --- | ---: | ---: |
| Renewal T | 0.18553283836801163 | 32 |
| Ordinary feedback G | 0.12985964701917668 | 32 |
| Untuned hover H | 0.13247830104751704 | 32 |

| Contrast | Mean paired difference | Conditional evaluation SE | Positive / negative / zero episodes |
| --- | ---: | ---: | ---: |
| T−G | +0.055673191348834944 | 0.011556059794903147 | 25 / 7 / 0 |
| T−H | +0.05305453732049459 | 0.01182038845858344 | 24 / 8 / 0 |
| G−H | −0.002618654028340355 | 0.011943248746505064 | 17 / 15 / 0 |

All adverse episodes remain in the summary; none is a separate training seed.
T−H supports a positive native package observation against the fixed reference.
G−H is slightly negative relative to its conditional uncertainty: competence
of this G fit is not established, nor is stable inferiority to hover. These
facts qualify the favorable primary rather than replacing it. Historical
opening results are not pooled into this renewal primary.

## E0.4 Actual learner exposure and native path

Each UAV selects a velocity and conditional duration at its own expiry;
held teammates retain commands while private observations and recurrence
continue. The resulting positions/service and future observations feed the
same complete native reward and the unchanged owned compound PPO objective.
Membership is fixed, entity histories persist, and selected durations at the
horizon are administratively censored without extra work. This path is
technically accepted at P69; P70 supplies actual exposure and native return.

| T phase | Velocity/duration selections | Selected d4 | Actual suppressed decisions | Horizon-censored holds |
| --- | ---: | ---: | ---: | ---: |
| Training | 255710 | 134282 | 399650 | 1592 |
| Final evaluation | 15883 | 8419 | 25077 | 93 |

G has 655360 training and 40960 final velocity decisions, and no duration,
suppression or censoring events; H has no policy decisions. Actual head-forward
rows are **1566026** from `6*255710+2*15883`, **99.87410714285714×** B04's
15680 rows. Dense forward work is **3457785408 multiply-adds** at 2208 per
row, excluding sampling, activation, backward and optimizer work. These are
computed event/exposure counts, not profiling or a causal cost measurement.

T/G parameter totals are **68553/66311**; T duration head has **2242**.
Both trained arms have nonzero observed displacement: T total
**8.719639778137207**, G **7.15549898147583**. T duration displacement is
**0.7187902927398682**, hidden **0.6962713599205017**, final
**0.1785096526145935**. Initial/final norms and relative displacements are
retained in the summary. The final head's zero initial norm has **null relative
displacement**. CM checked final checkpoint norms and finite FP32 tensors;
these facts do not identify useful conditioning, recurrence or renewal causality.

## E0.5 Counts, resources and conformance

| Quantity | Actual |
| --- | ---: |
| Learned arms / independent matched training pairs | 2 / 1 |
| Training episodes per learned arm | 512 |
| Native training steps per learned arm | 131072 |
| Rollouts / Adam calls per learned arm | 256 / 1024 |
| Total native steps / total Adam calls | 286720 / 2048 |
| Complete episode rows / explicit resets | 1120 / 1120 |
| Constructor resets / partial episode steps | 2 / 0 |
| Final evaluation episodes / retained diagnostic rows | 96 / 1600 |
| T / G complete-arm wall | 160.45789840299403s / 135.36679288500454s |
| Sum of recorded arm wall / runner whole wall | 295.82469128799857s / 295.8246927349828s |
| Outer whole wall / peak RSS | 304.85s / 556972 KiB |

Outer whole wall includes admission and publication/exit. The difference
between outer and runner clocks is not assigned to an unmeasured kernel.
Both arm and whole limits pass the original 1800s/3600s bounds. Current
invocation wall per valid result is **304.85s / 1**. P69's 3.97s focused suite
is separate engineering work; P70 adds no suite, smoke, pilot, profile, replay,
extra H/evaluation or subsequent submission. Engineering scope §4 **none**;
no §5 source/test budget breach is recorded.

`resources_unmeasured`: aggregate CPU work and system-wide peak memory.
Measured admission, wall and process peak RSS remain reportable. Missing
optional resource fields do not invalidate the intact native primary.
CM's read-only collection checks cover counts, resets, configuration, all
three contrasts, checkpoints and publication. DM inspected those receipts
and recomputed the question-relevant native reading from recorded episode
bytes; it did not repeat the full verifier or load models.

All seven output hashes are retained in the summary and
[CM collection readback](../../../../temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908/collection-readback.json),
matching the remote byte readback. Key SHA256s:
summary `d04ae37aa99ae2a648c1db66494549626a986f42a80e12102da10606920f6e5d`;
episodes `1e7cb79778940283b1eaa3bd67a92b42416cc226984de6ce8f5f24b4d4183811`;
admission `8df70040e845698ff003ac83a8ff7df4dd8d0a053663230e667d2d5c77b5adca`.
DM verified these three local analysis inputs and the executed wrapper digest.

## E0.6 Predictions and fixed end boundary

| Recorded prediction | Probability | Observed event | Brier loss |
| --- | ---: | --- | ---: |
| WITHIN | 0.45 | false: UP | 0.2025 |
| G−H positive | 0.60 | false: negative point | 0.36 |

Prediction hits **0/2**, mean Brier loss **0.28125**. Owner prediction:
**not taken (unattended)**. Forecast errors and all prior scores remain; the
observed UP does not become a retrospectively recorded prediction.

Card §5, verbatim: **Every sign ends this single allocation at intake.**
P70 ends after the [all-outcome intake](UCOPE_UAV_RENEWAL_COMMITMENT_B01_P70_INTAKE_20260908.md).
A separately allocated new independent training pair is recommended to test
the persistence of this package margin, with G/H still visible. No new master,
invocation, retry, tuning, family disposition or C promotion is allocated here.
