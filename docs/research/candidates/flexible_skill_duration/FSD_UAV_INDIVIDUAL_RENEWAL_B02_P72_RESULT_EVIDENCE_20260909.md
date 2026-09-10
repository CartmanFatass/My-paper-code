# FSD UAV individual-renewal B02 / P72 — result evidence

## 1. Complete result and rule applied

**Valid complete B/EXPLORE; one new matched training pair; `opposite_sign`.**
The original [card §§2–4](FSD_UAV_INDIVIDUAL_RENEWAL_B02_SCIENCE_CARD_20260908.md)
is unchanged. Both original arms completed at accepted source
`08199a932671d9bacdbe4eb0bfebab38c37fca1f`, CPU4/FP32 on `hmasd-wsl-node`.
CM's [technical evidence](FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_TECHNICAL_EVIDENCE_20260908.md)
was committed and pushed as `0ae90f0e31daa9d468844c5748a807c9e9bc1ada`.

Card §3 rule applied verbatim:

> | <−.01 | Opposite native performance on the new pair; the exact .25 configuration has a beyond-MEI native loss in both observed learning instances. Still not stable D0 superiority or broad closure. |

D0 mean native J is **0.4854120288125866** and I is **0.45009930351470057**.
The 32 paired I−D0 differences have mean **−0.035312725297886094**, sample
SD **0.07084355729934733** and conditional SE **0.012523489942436556**.
There are 9 positive and 23 negative endpoint differences; all are retained.
The independent training unit is this one new pair. Endpoint SD/SE describe
its learners' panel, not uncertainty over independent training seeds.

The [DM analysis](FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_DM_ANALYSIS_20260909.json)
retains ordered U/J/differences, both complete five-row training records,
configs, losses, parameter exposure, counters, admissions, hashes and the
existing run-summary tool's input/output. Its primary arithmetic agrees with
the published pair. No model, environment or evaluator was invoked at intake.

## 2. Native components and separate training signal

The learner still uses the original adapter reward U. Reporting computes
`J=6*U/500`; the native objective is `.7*coverage + .3*quality - altitude_penalty`.
The existing field `energy_penalty` is the altitude component. No reward,
normalizer, value target or learning loss was rescaled.

| Observable | D0 | I | I−D0 |
| --- | ---: | ---: | ---: |
| Raw adapter episode U | 40.45100240104888 | 37.50827529289171 | −2.94272710815717 |
| Native mean J | .4854120288125866 | .45009930351470057 | −.035312725297886094 |
| Coverage | .6221899999999996 | .5695912500000007 | −.05259874999999892 |
| Quality | .18192697255677431 | .18367311867020852 | +.0017461461134342104 |
| Altitude penalty | .004699062954445523 | .003716507086362047 | −.0009825558680834762 |

Coverage contributes −.03681912499999924 to the contrast, quality
+.0005238438340302631 and lower altitude cost +.0009825558680834762.
The small quality and altitude benefits do not offset the coverage loss.
This is reward accounting, not a causal explanation of the learned motion.

I's recorded stochastic training return is higher on rollouts 2–5, while its
final deterministic native endpoint is lower. The five native training means
are retained below and in the JSON; they are neither extra evaluation points
nor independent training instances.

| Rollout | D0 sampled training J | I sampled training J |
| --- | ---: | ---: |
| 1 | .23932652226302936 | .2330399174374506 |
| 2 | .15876695362476242 | .2226187703439438 |
| 3 | .18396404549580508 | .24996768804195463 |
| 4 | .23147043398473738 | .24726314602419047 |
| 5 | .13445342978777022 | .2832216120232257 |

## 3. Two learning instances, with every outcome preserved

P70 remains the original separate result. It never supplied this run's D0
companion, model, data or checkpoint. The same method is used with the explicit
new training/evaluation keys; the binding-only source change was checked before
launch. Each row below represents one independent matched learning instance.

| Pair | Training / evaluation base | D0 J | I J | I−D0 J | Conditional endpoint SE |
| --- | --- | ---: | ---: | ---: | ---: |
| P70 / B01 | 770503 / 780503 | .26946095234781076 | .21979038918069888 | −.049670563167111874 | .023762591435853447 |
| P72 / B02 | 770603 / 780603 | .4854120288125866 | .45009930351470057 | −.035312725297886094 | .012523489942436556 |

The two card pair means have descriptive mean **−.04249164423249899** and
sample SD **.01015252452050656**. The existing scientific-tools
`summarize_runs.py --paired --baseline D0` was applied to four arm scores,
each already averaged over its final endpoint panel. Its subtraction of arm
means differs from the card's mean of ordered differences only in final
summation digits. Its input CSV and complete descriptive output are in the DM
JSON; no episode row or repeated checkpoint became a training seed.

Both observed comparisons exceed the .01 loss threshold. Two instances with
fresh finite panels do not isolate training-only variance, establish stable
population superiority, or support a 64-training-seed calculation. P70's
coverage gain with quality/altitude harm and P72's coverage loss with small
quality/altitude gains remain separate. Altitude harm is not a common necessary
accounting explanation for both native losses.

## 4. Exposure, training and renewal activity

Each arm uses six fixed UAVs/fifty users, uniform/free-space H500, latent6/6,
common team k10/caps10, delta1/ageoff and the original recurrent stack.
Training770603/evaluation780603 and their private lanes match the card.
I uses individual .25/team Infinity; authentic D0 uses numeric Infinity for
both costs in D2 mode. Every-step information and native continuous actions
remain intact. Both arms own their later RNG consumption, data, optimizers,
normalizers and parameters after the declared matched initialization/reset law.

Machine-computed P72 exposure: **80000 collected/stored training transitions,
160 training episodes,10 update stages;32000 scoring steps,64 final episodes;
112000 environment steps,672000 agent-step observations,6000 batch control
calls;4 model constructions,2 training starts,0 checkpoint loads;
50040 optimizer.step calls;1 new independent training pair.**
Each endpoint follows update5 and has 32 episodes of exactly 500 steps, with
zero evaluator optimizer calls. No intermediate evaluation, selection, retry,
resume, pilot or additional scientific validation panel occurred.

| Actual optimizer calls | D0 | I |
| --- | ---: | ---: |
| Coordinator | 525 | 3765 |
| Discoverer actor | 11250 | 11250 |
| Discoverer critic | 11250 | 11250 |
| Team discriminator | 75 | 75 |
| Individual discriminator | 300 | 300 |
| Evaluator, all groups | 0 | 0 |

All five active groups have finite nonzero first/fifth parameter movement;
initial norms and the complete movements remain in the JSON and CM record.
Unused process-encoder loss fields remain zero. Parameter movement establishes
learner exposure, not native competence.

During training I has **65761** individual gap decisions, **89761** sampled
individual positions and **31821** joint rows, versus D0's 0/24000/4000.
Both have 4000 team decisions. I's individual segment means are 2.52–2.83
primitive steps per rollout, against D0's 10; both team means remain 10.
Training token switches total72935 I/19784 D0. A sample need not switch a token.

At the deterministic endpoint both arms have **zero gap causes**,1600 team
decisions and9600 individual samples; token switches differ:1272 I/760 D0.
The new result again measures a package changed during training with no extra
endpoint gap renewals. Empty evaluator storage/segment tables are **unmeasured
duration statistics**, not zero-duration native skills. This limits those
statistics under evidence-spec §11.8.7, while the native primary and decision
counters remain independently trustworthy.

## 5. Receipts, complete cost and deviations

One accepted handle per arm, both finished/exit0 and collected:
`fsd_uav_b02_p72_D0_08199a932`, `fsd_uav_b02_p72_I_08199a932`.
Remote cwd: `/home/wu/hmasd-worktrees/fsd-uav-b02-p72-08199a932`.
Remote staging: `/home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908`.
The scientific roots are its `temp/directions/flexible_skill_duration/exp/`
`uav_individual_renewal_b02_770603/{D0,I}`. Original supervisor directories
remain under `/home/wu/.agent-tasks/<handle>/`; CM was sole observer/collector.

Local collection root is
`temp/directions/flexible_skill_duration/exp/uav_b02_p72_control_20260908`.
It retains both evidence tar files, extracted original summaries/supervisor
files, adjacent admission receipts, full time records, launch/stdout and source
verification. DM read the original summaries and resource/terminal receipts;
CM's archive-hash verification and technical coverage were accepted without
repeating collection or a scientific invocation.

| Receipt | D0 | I |
| --- | --- | --- |
| Original summary SHA256 | `6d84eaf98151954e0ad21fab301123d5cf0b33cbc17ade05eb9f50de83f08891` | `ce88a406fee0f0eb2784af8650be74a458460df36ca04276f9b0ed2c14f95573` |
| Admission UTC | 2026-09-09T06:30:06.778598Z | 2026-09-09T06:40:20.027389Z |
| Physical/effective available bytes | 15633887232 / 15633887232 | 15635578880 / 15635578880 |
| Complete wall seconds | 471.50 | 1297.28 |
| Peak RSS KiB | 1659568 | 1610200 |
| User / system CPU seconds | 1840.09 / 17.63 | 5128.39 / 30.74 |

Both original adjacent admissions passed the4294967296-byte floors before
scientific construction. Complete wall sum **1768.78s** fits the21600s cap;
individual walls fit3600/18000s. Aggregate CPU is **7016.85s**. Study critical
path is **1911s** at supervisor1s resolution and includes the between-arm gap.
I uses2.7514 times D0's measured complete wall. Continuous free-memory telemetry
is unmeasured; admissions and peak RSS are measured. The earlier summary
publication time is not substituted for full process wall.

The two scoped UAV B results together used3462.16s summed complete wall and
13739.12s aggregate CPU; these are separate from historical corridor work and
engineering checks. P72's scientific budget is complete: no authorized accepted
submissions remain. Engineering scope §4 additions: none. Shared runner428
lines/thin runner16/new tests124, with9.0115169s source-check wall; no §5 breach.
Blocked P69/P72 scratch remains after automatic approval review rejected its
deletion as “blocked by policy”; no bypass occurred. This housekeeping issue
does not supply scientific polarity.

The owner soft stop arrived after I was terminal. Collection and this intake
finish the current batch. No subsequent arm, seed, object or Pro request is
launched. [Restart handoff](FSD_P72_RESTART_HANDOFF_20260909.md) records the held
boundary; neither this B nor prior A/B objects acquire a C consumption state.
