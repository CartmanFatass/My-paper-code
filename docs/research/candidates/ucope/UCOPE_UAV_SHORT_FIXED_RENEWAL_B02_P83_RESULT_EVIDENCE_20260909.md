# UCOPE short fixed renewal B02 P83 — native result evidence

**B/EXPLORE, valid complete UP.** New 8201 gives prospective F−G
**+0.04205514630433558**. F−H **+0.01688043904880538** is a separate gain;
G−H **−0.025174707255530195** is a separate native loss. This supports a
preliminary package advantage on this fit, with comparator competence and
variation across training histories unresolved. The [durable summary](UCOPE_UAV_SHORT_FIXED_RENEWAL_B02_P83_RESULT_SUMMARY_20260909.json)
retains all 96 returns, three signed vectors, counts, exposure and receipts.

## E0.1 Frozen object and invocation

Object `UCOPE-UAV-SHORT-FIXED-RENEWAL-B02`, selector `renewal_short_fixed_b02`,
master 8201, [card §§1–7](UCOPE_UAV_SHORT_FIXED_RENEWAL_B02_SCIENCE_CARD_20260909.md).
Root P83 allocated one fresh learning history with the same fixed {1,2},
half-each F/G/H recipe. P82 and older results retain their original primaries.

| Bound record | Commit |
| --- | --- |
| Card/allocation | 15c790b474ebad7d20f6a4ca240cd234e1825486 |
| Scientific source | a2dbdc2452ecf17ef4578962abb20c0cea617d43 |
| CM acceptance/literal payload | d26979eab78b4bd9f0e1435a61c64de783ba70b2 |
| CM terminal collection | ad642f0adf2768976e9167c4b3e38f2cbf3db24f |

One accepted `hmasd-wsl-node` handle
`ucope-uav-short-fixed-renewal-b02-8201-p83-20260909`, CPU FP32/one Torch
thread. Remote cwd is `/home/wu/hmasd-worktrees/` plus this handle; relative
output/local collection is `temp/directions/ucope/exp/` plus the handle.
CM alone observed and collected. PID 3056496 finished, exit 0/tmux inactive,
start **2026-09-09T22:13:38+08:00**, end **22:18:56+08:00**.

Canonical admission **2026-09-09T14:13:38.979275Z** measured physical/effective
availability **15629881344 bytes** each against 4294967296. Actual/supervisor
copies agree. Executed wrapper: 791 bytes, SHA256
`092ef5c44857a2d0921ef10ffee6cda0c912a018b0e45d2fe99435fab1c6deae`.
[CM intake §§4–6](UCOPE_UAV_SHORT_FIXED_RENEWAL_B02_P83_INTAKE_20260909.md#4-cm-binding-acceptance)
contains exact source/payload, admission, terminal and collection receipts.

## E0.2 Estimand, rule and checks

`J=sum_t sum(info['rewards_dict'].values())/256`; primary
**Delta_G=mean_e(F−G)** over 32 paired final reset episodes. SE is sample
SD of episode differences/sqrt(32), conditional on one new matched training
instance. F/G fit separately; H is untrained. No training-population SD or
interval is identified. Card §5 UP condition: **Delta_G > +0.01**.
Rule applied verbatim:

> Preliminary favorable short fixed-renewal package evidence on this fresh fit; it does not establish stable advantage across training histories.

The unrounded primary is **0.03205514630433558 above +0.01**. Both hover
contrasts stay separate and do not change the selected primary.

DM checked source/card/CM result, raw focused receipt, reused P82 review,
config/private streams, admission, terminal and collection evidence. One
episode-byte arithmetic pass finds all 1120 identities complete/unique,
correct master/reset/horizon, J=reward_sum/256, and exact matches for 96 J
values and three vectors/means/SEs. F/G completeness governs F−G; absent
`selected_contrast` is intentional on this fixed path. P80 remains F−H-primary.

The approved run-summary tool receives only new 8201 F/G fitted endpoints,
n=1; H and older fits do not enter its training rows. Its difference of means
differs from the native mean of differences by floating-point roundoff only;
the native value above remains primary. CM checkpoint/group/physical-duration
checks are accepted without repeated tests, tensor/model execution or remote
observation by DM.

## E0.3 All outcomes and bounded reading

| Arm | Mean J | Final episodes |
| --- | ---: | ---: |
| Short fixed renewal F | 0.16472782101275252 | 32 |
| Ordinary feedback G | 0.12267267470841695 | 32 |
| Untuned hover H | 0.14784738196394714 | 32 |

| Contrast | Mean | Conditional evaluation SE | Positive / negative / zero |
| --- | ---: | ---: | --- |
| F−G, primary | +0.04205514630433558 | 0.008895069330742151 | 24 / 8 / 0 |
| F−H | +0.01688043904880538 | 0.011210216975722664 | 18 / 14 / 0 |
| G−H | −0.025174707255530195 | 0.011893075742872027 | 14 / 18 / 0 |

**Strongest support:** above-MEI F−G and a separate F−H gain after real
learning; P82 also has a positive F−H point. **Strongest contradiction to a
stable, competent-feedback advantage:** G loses to hover here and P82 F−G
is WITHIN; eight new F−G and fourteen F−H episode differences are adverse.
The G loss limits stronger comparator claims without invalidating this B
comparison or erasing F's hover gain.

P82 remains F−G +0.008551004914111454 (WITHIN), F−H +0.02854870179583208,
G−H +0.019997696881720626. Its conditional SEs and individual P78–P81 {1,4}
outcomes remain in the summary. P79 hover losses/old n=2 and P77 learned-T
losses remain. No new cross-instance mean/SD, pooled primary, causal
support-change estimate or training-population interval is made.

Useful motion, feedback optimization variation, altered action opportunities,
evaluation variation and partner co-adaptation survive. Direct service versus
information value, shortening effects and learned-duration value are not
identified; F's duration law is fixed. No stable superiority/harm, equivalence,
tuned competence or deployment claim follows. Reused verified UTE grounding
frames temporal-action tradeoffs; it does not explain G's hover loss.

## E0.4 Exposure, engineering and cost

Completed **286720 native steps/2048 Adam/512 rollouts/1024 training episodes/
96 final evaluations/1120 explicit and 2 constructor resets**. F/G each train
131072 steps with 1024 updates; H has 32 untrained final episodes. Existing
1600 diagnostic frames add no environment transitions.

F train/final renewals **437288/27362**; d2 **218945/13650**, d4 zero.
Suppression **218072/13598**, censored holds **873/52**. Every F episode has
d2=suppression+censoring; all published levels, physical expiry/held motion
and remaining/4 features agree. F head work is **2678452 rows / 5914022016
dense MACs**, inside prospective bounds.

All **2242** F-head parameters and both layers stay fixed, reported norm
**3.2730531692504883** before/after; final weight/bias zero, relative movement
from zero null. F actor/critic move **2.4717350006103516/8.48689079284668**;
G **2.9776387214660645/6.18130350112915**. Both have 66311 trainable parameters.
Intentional freezing and real learning remain distinct facts.

Whole invocation **317.61 s**, RSS **554456 KiB**; nested F/G arm times
167.0972740459838/133.13975488004507 s, runner 300.2370302210329 s.
Study critical path and sum of invocation wall are 317.61 s for this one
serial invocation. Nested times exclude outer startup/tail. Aggregate CPU
is **resources_unmeasured**. Complete seconds per valid result and accepted-
attempt seconds per valid result are both 317.61. No controlled efficiency
comparison follows. No cap, partial, limit or §5 budget breach.

Production source adds 27/removes 21 lines, runner 54; §4 machinery **none**.
Focused check: 14 passed, 0.25 s outer. P82 semantic review/checks reused,
own scratch removed. Seven native/admission and seven supervisor digests
match CM collection. No extra scientific invocation occurred.

## E0.5 Predictions, decisions and recovery

P(F−G>0.01)=0.45 was true, Brier 0.3025; P(F−H>0.01)=0.60 was true,
Brier 0.16; mean **0.23125**. Owner prediction **not taken (unattended)**.
Both review views and UCOPE audit owner columns have no unapplied instruction
at intake. Owner flags none.

DM accepts **UP** at object tier, preserves F−H gain/G−H loss and ends P83.
Recommend one separately allocated fresh same-recipe F/G/H fit to observe
the full contrast pattern in another learning history, especially G−H.
All future signs would remain; no favorable-sign requirement or tuned-baseline
prerequisite follows. No next card/master/source/budget, automatic repeat,
support change, Pro Send, family/recast/C or Portfolio disposition is created.

Known suggested work remains 286720 steps/2048 Adam/96 evaluations and F
head 2007040–4014080 rows; 317.61 s is a reference only. Tuned headroom
absent, recasts 1. [Intake §9](UCOPE_UAV_SHORT_FIXED_RENEWAL_B02_P83_INTAKE_20260909.md#9-decisions-this-completed-intake-produces)
records options/rationale; [Chinese brief](../../portfolio/owner/briefs/ucope/2026-09-09_UCOPE_UAV_SHORT_FIXED_RENEWAL_B02.md)
and audit rows 29–30 preserve the decision. Root owns integration and P83
remote scientific/check checkout and wrapper reclamation after preserving
evidence. Both handles are terminal; shared local checkout remains in use.
