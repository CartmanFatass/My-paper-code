# UCOPE fixed renewal B03 P81 — native result evidence

**B/EXPLORE, valid complete DOWN.** New 8001 gives prospective F−G
**−0.021798883942210363**. F−H **+0.015269670011827153** and G−H
**+0.03706855395403751** remain separate native gains. This repeats the
adverse feedback ordering from P80 while both learned controllers beat hover
on sampled means. It neither rescues the primary nor establishes stable harm.
All 96 returns, three signed vectors, counts, exposure and receipts are in the
[durable summary](UCOPE_UAV_FIXED_RENEWAL_B03_P81_RESULT_SUMMARY_20260909.json).

## E0.1 Frozen object and actual invocation

Object `UCOPE-UAV-FIXED-RENEWAL-B03`, selector `renewal_fixed_b03`, master 8001,
[card §§1–7](UCOPE_UAV_FIXED_RENEWAL_B03_SCIENCE_CARD_20260909.md). Root P81
separately allocated this outcome-informed prospective feedback question;
P80 remains F−H-primary and P78/P79 retain their F−G readings.

| Bound record | Commit |
| --- | --- |
| Card/allocation | 6572984b73536c41b7d46bac13c46a56c0751257 |
| Accepted scientific source | 87e2793098a57a30caf6c816309c42bece30ee98 |
| CM source acceptance/literal payload | 30441aca7e5ee9e318653df3c8186eeafbbd7421 |
| CM terminal collection | 2511c9c0eca8fc231822289b3b69d9589d9568a2 |

The only accepted `hmasd-wsl-node` handle is
`ucope-uav-fixed-renewal-b03-8001-p81-20260909`, CPU FP32/one Torch thread.
Remote cwd is `/home/wu/hmasd-worktrees/` followed by that handle; remote
relative output/local collection is `temp/directions/ucope/exp/` plus the handle.
CM alone observed through collection. PID 3051894 finished, tmux inactive,
exit 0, start **2026-09-09T20:48:15+08:00**, end **20:53:35+08:00**.

Fresh canonical admission at **2026-09-09T12:48:15.308364Z** measured physical
and effective availability **15633784832 bytes** each against 4294967296.
Actual/supervisor copies are byte-identical. The executed 749-byte wrapper
SHA256 `903ad0bdab2b78dbac12c659d6409636d5db993a2caa71bccc2955009872a7ba`
matches the committed payload. [CM intake §§4–6](UCOPE_UAV_FIXED_RENEWAL_B03_P81_INTAKE_20260909.md#4-cm-binding-acceptance)
retains exact source, commands, admission, terminal and collection receipts.

## E0.2 Estimand, rule and checks

`J=sum_t sum(info['rewards_dict'].values())/256`; **Delta_G=mean_e(F−G)** on
32 paired final reset episodes is primary. Conditional evaluation SE is
sample SD of episode differences divided by sqrt(32), conditional on one new
matched training instance. F/G fit separately; untrained H is no training
replicate. No training-population SD or interval is identified.

Card §5 DOWN condition: **Delta_G < −0.01**. Reading applied verbatim:

> Adverse fixed-renewal package evidence on this fit; neither hover gains nor an earlier positive mean rescues this primary.

The unrounded point is **0.011798883942210363 below −0.01**. No added
significance, all-positive or equivalence condition changes the point rule.

DM checked the immutable source/binding diff and focused receipt, then the
result document against the card, configuration/private streams, all 1120
episode rows, terminal/admission/wrapper evidence and CM collection PASS.
All episode identities are complete/unique, with master 8001, declared resets,
256-step horizons and J=reward_sum/256. All 96 returns, vectors, means and SEs
match publication; maximum arithmetic discrepancies are zero.

The new selector uses the unchanged fixed-pair F/G completeness path;
`selected_contrast` is absent by design. That absence is not a hover selection
or missing primary: card/source/fixture bind F−G and its complete F/G panels.
P80 alone keeps its explicit F−H field. Both fits and all three panels completed.

The approved run-summary tool receives this instance's F/G endpoint means only,
n=1. H and earlier objects are excluded from training rows. Its difference
of endpoint means differs from the native mean of paired differences by
**2.08e-17** accumulation rounding, with no reading change. DM accepts CM's
finite-FP32 checkpoint/norm and fixed-head checks without repeating tests,
tensor loading, learner/evaluator/simulator or remote observation.

## E0.3 All native outcomes and separate historical context

| Arm | Mean J | Final episodes |
| --- | ---: | ---: |
| Fixed renewal F | 0.15470866836029662 | 32 |
| Ordinary feedback G | 0.176507552302507 | 32 |
| Untuned hover H | 0.13943899834846948 | 32 |

| Contrast | Mean | Conditional evaluation SE | Positive / negative / zero |
| --- | ---: | ---: | --- |
| F−G, primary | −0.021798883942210363 | 0.010646977126718544 | 12 / 20 / 0 |
| F−H | +0.015269670011827153 | 0.012567527601623765 | 17 / 15 / 0 |
| G−H | +0.03706855395403751 | 0.011330703710254264 | 25 / 7 / 0 |

| Separate instance | F−G | F−H | G−H | Original primary |
| --- | ---: | ---: | ---: | --- |
| P78 / 7701 | +0.026550516654013076 | +0.030122962641204728 | +0.0035724459871916527 | F−G UP |
| P79 / 7801 | +0.030362608571553623 | −0.0035128012832155745 | −0.033875409854769195 | F−G UP |
| P80 / 7901 | −0.025803909613053323 | +0.018660096017418804 | +0.04446400563047213 | F−H UP |
| P81 / 8001 | −0.021798883942210363 | +0.015269670011827153 | +0.03706855395403751 | F−G DOWN |

Original primary conditional SEs: P78 **0.011109495362659165**, P79
**0.008159350975084483**, P80 F−H **0.010755224968186065**. The durable summary
retains every prior contrast's SE. No new cross-instance mean/SD, pooled
primary or population interval is selected; P79's old n=2 record remains its
own description. P77 learned-T losses and earlier renewal reversals stay separate.

The strongest support for native fixed-renewal value is the new F−H gain.
The strongest contradiction to its feedback advantage is this second observed
negative F−G point, with useful G−H on both latest fits. The earlier positive
F−G points and 12/32 favorable new episodes prevent a uniform-harm reading.
No stable superiority/harm, learned-duration value, causal timing/information
effect, tuned competence or deployment conclusion follows.

## E0.4 Exposure, cost and engineering conformance

Each F/G fit completed 512 episodes, 131072 training steps, 256 rollouts and
1024 Adam calls, followed by 32 final evaluations each plus 32 H. Total
**286720 native steps / 2048 Adam / 512 rollouts / 1024 training episodes /
96 evaluations / 1120 explicit and 2 constructor resets**, zero partial steps.
The **1600 existing diagnostic frames** do not add environment transitions.
No T arm/checkpoint/evaluation or additional scientific invocation occurred.

F's entire 2242-parameter head and both layers have zero displacement;
initial/final head/hidden norm **3.291517972946167**, final weight/bias/norm
zero and final relative displacement undefined. F actor/critic moved
**3.0865399837493896 / 7.457614421844482**; G's moved
**2.246004343032837 / 8.171553611755371**. Both have 66311 trainable parameters.
F train/eval renewals **263516/16326**, d4 selections **131669/8279**, suppression
**391844/24634**, censoring **1565/95** give **1613748** head-forward rows.

Complete outer wall **320.29 s**, peak RSS **561664 KiB**. F arm wall
159.52413442503894 s, G including H/publication 146.81889442302054 s,
summed arms 306.3430288480595 s, runner 306.3430306520313 s are nested scopes,
not additive costs. No 1800 s arm/3600 s whole breach. Aggregate CPU is
**resources_unmeasured**. Current cost is 320.29 s per valid P81 result.

Engineering: **17 focused checks passed**, 0.25 s complete wall, RSS 29828 KiB.
Unchanged P78–P80 semantics/review and fixed-pair missing-arm coverage are reused.
Non-test source 26 additions/20 deletions, runner 54 lines, scope §4 none;
no §5 breach, new semantic review, unchanged suite or native smoke repetition.
Engineering PASS does not convert the scientific DOWN into mechanism value.

## E0.5 Predictions and completed boundary

F−G>0.01 at probability 0.50 did not occur, Brier loss 0.25. F−H>0.01 at
0.60 occurred, loss 0.16; mean **0.205**. Owner prediction **not taken
(unattended)**. No pending owner instruction or UCOPE audit override was found.

[DM intake §§7–10](UCOPE_UAV_FIXED_RENEWAL_B03_P81_INTAKE_20260909.md#7-dm-scientific-intake-against-the-card)
accepts DOWN, retains both hover gains and ends P81. It recommends one
separately allocated **shorter fixed-hold F/G/H** comparison, duration support
{1,2} with half probability each and F−G primary, inside the own-expiry family.
This future treatment amendment tests bounded performance, not the cause of
P81's loss; the current {1,4} card is unchanged. Known new head work is stated
in the intake. No successor card/master, source, allowance, run, Pro Send,
recast, C promotion, family closure or Portfolio disposition is created here.
The [Chinese brief](../../portfolio/owner/briefs/ucope/2026-09-09_UCOPE_UAV_FIXED_RENEWAL_B03.md)
and audit accompany intake. Root owns integration and finished remote cleanup
after preservation; the shared local checkout and native evidence remain intact.
