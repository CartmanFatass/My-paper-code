# UCOPE mean-velocity renewal B01 P85 — native result evidence

**B/EXPLORE, valid complete WITHIN.** New 8401 gives prospective
F_mean−G_mean **−0.008350131013904307**, conditional SE
**0.006736648533933545**. All four learned-mode hover means are negative;
mean−sampled is **−0.04255880352167644** for F and **−0.05655406829020172**
for G. The [durable summary](UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_RESULT_SUMMARY_20260909.json)
preserves all 160 returns, eight paired vectors, counts, exposure and receipts.

## E0.1 Frozen object and invocation

Object `UCOPE-UAV-MEAN-VELOCITY-RENEWAL-B01`, selector
`renewal_mean_velocity_b01`, master 8401,
[card §§1–7](UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_SCIENCE_CARD_20260909.md).
Unchanged stochastic F/G fitting, then both modes on each final fit plus H;
mean uses tanh(mu), zero Gaussian draws, and F still samples fixed {1,2} durations.

| Bound record | Commit |
| --- | --- |
| Card/allocation | d44b9f40e437b1424d47f23f6371f7d5b62b7caf |
| Scientific source | 52bf50a089d3389d9fada0b531e4f4e56e83f9b8 |
| CM acceptance/literal payload | 328f89ad2c930f07c8b2ab241c9898d5c937f5fd |
| CM terminal collection | 3ed05d42fdfc29a0c7d3eb9cc6b36955b7a76609 |

One accepted `hmasd-wsl-node` handle
`ucope-uav-mean-velocity-renewal-b01-8401-p85-20260909`, CPU FP32/one Torch
thread, PID **3059411**, finished exit 0/tmux inactive. Supervisor start
**2026-09-09T23:50:01+08:00**, end **23:55:32+08:00**. Remote cwd is
`/home/wu/hmasd-worktrees/` plus the handle; relative output/local collection
is `temp/directions/ucope/exp/` plus the handle. Original CM alone observed
and collected; DM made no remote observation or model/native execution.

Joined canonical admission **2026-09-09T15:50:01.191180Z** measured
physical/effective availability **15638007808 bytes** each against 4294967296.
Scientific/supervisor copies agree. Executed wrapper **805 bytes**, SHA256
`3b56828d695c10d16f144c25bda61e4d21eb3a9a01053009483e31c5e9bb2739`.
[CM intake §§4–6](UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_INTAKE_20260909.md#4-cm-source-focused-checks-and-independent-review)
contains exact source/payload, raw tests, independent review, admission,
terminal and collected evidence. Seven local scientific-file hashes match
the accepted collection record.

## E0.2 Estimand, rule and DM checks

J=sum_t sum(info['rewards_dict'].values())/256. Primary
**Delta_mean=mean_e(F_mean−G_mean)** over 32 paired final reset episodes.
SE is sample SD of episode differences/sqrt(32), conditional on the one
matched fitted instance. H is untrained and modes share the same two fits.
Card §5 condition **−0.01 ≤ Delta_mean ≤ +0.01** holds; the point is
**0.0016498689860956935 inside the lower boundary**. Rule applied verbatim:

> No demonstrated point gain at the selected scale on this fresh fit; no equivalence conclusion.

DM read the changed source and affected tests, the independent no-material-
finding review and raw 142-test receipt, then CM's complete result/admission/
terminal/collection records. One recorded-episode arithmetic pass finds all
**1184** identities complete and unique with the right master, reset, horizon
and J=reward_sum/256. All **160 J values and eight difference vectors/means**
match exactly. Primary SE matches exactly; F_mean−H SE differs by
**1.734723475976807e-18** in local arithmetic, with native published SE retained.
This rounding-scale difference changes no point, primary reading or interpretation.

The approved run-summary tool receives only new F_mean/G_mean endpoints,
**n=1**, with modes identified as sharing fits. Its endpoint difference differs
from the paired-episode mean by 1.734723475976807e-18. No training-population
SD/interval, new cross-instance mean/SD, pooled primary or best-mode score.
CM's checkpoint/support readback is accepted without repeating model execution.

## E0.3 All outcomes and bounded reading

| Outcome | Mean J | Final episodes |
| --- | ---: | ---: |
| F_mean | 0.06637304972645941 | 32 |
| G_mean | 0.07472318074036371 | 32 |
| F_sampled | 0.10893185324813584 | 32 |
| G_sampled | 0.13127724903056542 | 32 |
| H | 0.1564698252671263 | 32 |

| Contrast | Mean | Conditional evaluation SE | Positive / negative / zero |
| --- | ---: | ---: | --- |
| F_mean−G_mean, primary | −0.008350131013904307 | 0.006736648533933545 | 13 / 19 / 0 |
| F_sampled−G_sampled | −0.02234539578242959 | 0.011146317759927301 | 12 / 20 / 0 |
| F_mean−H | −0.0900967755406669 | 0.007991683312183612 | 0 / 31 / 1 |
| G_mean−H | −0.0817466445267626 | 0.01058012468337991 | 3 / 29 / 0 |
| F_sampled−H | −0.04753797201899047 | 0.011108766806409685 | 8 / 24 / 0 |
| G_sampled−H | −0.025192576236560876 | 0.012349499534101622 | 11 / 21 / 0 |
| F_mean−F_sampled | −0.04255880352167644 | 0.007527296196624865 | 6 / 26 / 0 |
| G_mean−G_sampled | −0.05655406829020172 | 0.00913219329993519 | 4 / 28 / 0 |

Mean execution reduces native return for both fitted policies here, with a
larger reduction for G. The smaller F−G deficit under mean execution therefore
coexists with deterioration of both policies. None of the four learned-mode
means beats hover; mean F has 31 adverse and one tied hover episode.
The primary remains WITHIN, and the adverse sampled contrast stays secondary.

The strongest surviving favorable evidence for the broader short-renewal
proposal is P83/P84's sampled F−G gain. P85 adds no above-MEI mean-mode gain;
its two mean−sampled losses and four hover losses are the strongest direct
contradiction to adopting mean extraction for native benefit on these fits.
P82 remains WITHIN, P83/P84 retain their original UP primary and native losses,
and all older supports/P77 T outcomes remain separately preserved.

Private recurrent observations → velocity execution at each owner's opportunity
→ held motion and later service/local information → training exposure and
partner co-adaptation remains the mechanism path. Mode changes affect the
closed-loop trajectories; they do not separate service from information value,
training-history variation, optimization or partner interaction. Reused P84
grounding describes mean execution as an option to test, with no guarantee.
This result does not diagnose the cause of older losses or establish stable
harm/superiority, equivalence, learned-duration value, tuned comparator
competence, causal shortening or deployment readiness.

## E0.4 Exposure, engineering and cost

Full **303104 native steps / 2048 Adam / 512 rollouts / 1024 training episodes /
160 final episodes**, **1184 explicit + 2 constructor resets** and **3200
diagnostic frames** completed. F/G each train 131072 steps and take 1024 Adam
steps; final modes each have 8192 steps and no optimizer updates. F's whole
2242-parameter duration head remains fixed, hidden norm **3.3659768104553223**,
final layer zero; relative displacement at its zero norm stays undefined.
Training common-actor displacement F/G **3.0816524028778076 /
2.731663465499878**, critic **6.852802753448486 / 5.5406646728515625**.
All groups have zero post-fit displacement after each evaluation mode;
buffer reports are unchanged, and the reviewed networks have no running-stat buffers.

F renewals are **438136 training + 27386 sampled final + 27386 mean final**.
Both final duration-count vectors agree as prospectively coupled; each has
**13616 d2**, **13574 suppressed decisions**, **42 horizon-censored holds**.
Training d2/suppressed/censored are **218019/217224/795**; d4 is zero.
Actual head work **2738360 rows / 6046298880 dense MACs** is within the card.

Complete outer wall **331.58 s**, peak RSS **556548 KiB**. Nested F
**174.66877074097283 s**, G including H **140.52741507801693 s**, runner
**315.19618722598534 s**. One serial invocation's critical path and sum of
invocation wall coincide; per-valid-result and accepted-attempt-per-valid-result
wall are both 331.58 s. Aggregate CPU and full engineering/collection costs
remain **resources_unmeasured**. No scientific cap or scope §5 budget breach;
no controlled efficiency claim. Scope §4 additions none, non-test +83/−36,
runner 54 lines, focused tests 7.61 s outer/6.42 s pytest.

Automatic approval review rejected exact completed local test-scratch removal
as **blocked by policy**. The scratch is retained with CM cleanup ownership;
no deletion retry or alternate bypass occurred. This engineering limitation
does not change the independently trustworthy native measurements.

## E0.5 Predictions, decision and next responsibility

The four prospective gain events all failed. Brier losses
**0.25 / 0.30250000000000005 / 0.36 / 0.36**, mean **0.318125**.
Owner prediction **not taken (unattended)**. Owner flags none; the primary's
distance to the boundary is reported without an equivalence claim.

Object-tier decision: accept valid complete WITHIN and all adverse mode/hover
observations; **end P85**. Recommend one separately allocated fresh same-five-
mode B to observe whether the full pattern recurs in another learning history,
keeping mean F−G prospective primary and all outcomes. Known unchanged work is
303104 steps/2048 Adam/160 final episodes, with the same head bounds; future
wall remains unknown. No next card/master/source/allowance, extra evaluation,
automatic successor or Pro Send is created. Root owns later allocation,
integration and remote reclamation; CM retains the denied local cleanup.
The no-work alternative is to seek an end to this mean-execution package.
Root allocates no pair now and authorizes a separate consultation-only
Convergence question about marginal value versus that alternative and a concrete
training change. It will return READY to Root with zero new empirical exposure.
See [DM intake §§7–10](UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_INTAKE_20260909.md#7-dm-scientific-intake-against-the-card)
and the [Chinese brief](../../portfolio/owner/briefs/ucope/2026-09-09_UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01.md).
