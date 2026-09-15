# FSD baseline × interruption B01 — result evidence

## Result and rule applied verbatim

**Valid complete B/EXPLORE: twelve original fits, three arms × four independent training
blocks, all three panels. The primary SI1280 at rollout 15 is a small signed positive
mean (+.00983744 J) inside the ±.05 J MEI band with a df = 3 working-model interval that
includes zero and is not inside the MEI band; the untuned package gaps D1280 − FLAT and
I1280 − FLAT have negative means at rollout 15 with intervals including zero.** The
[card](FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md) §4 as amended by §8
(Portfolio S decision, `PRO_FINAL / OWNER_DELEGATED`) states:

> **MEI .05 J** stays as a cost-sensitive development target; the claim that an effect must
> exceed arm variability to matter is withdrawn. Reading is split: importance (mean above
> +.05 locally substantial positive; below −.05 adverse; inclusive ±.05 small signed) and
> uncertainty (df = 3 working-model interval reported alongside; zero exclusion strengthens
> but is not required; an interval inside ±.05 is a model-conditional small-magnitude
> reading, never equivalence).
>
> **Labels:** `H_r`/`HI_r` are renamed `GAP_D`/`GAP_I`, *untuned cross-information package
> gaps* D1280 − FLAT and I1280 − FLAT; they are not §11.7 headroom and supply no tuned
> same-information reference.
>
> **Rollout-5 accumulation:** four new plus two historical blocks (six, df = 5), new and
> historical groups reported separately first; the combined summary is explicitly
> outcome-informed descriptive accumulation […] **No automatic extension**: a further
> tranche of blocks is a new Portfolio question with the […] numbers on record.

Primary SI1280_15 = J15(I1280) − J15(D1280) by block: +.09835977, +.04471497, −.08340338, −.02032159 J;
mean **+.00983744 J**, sample SD .07885865, SE .03942933, df = 3 working-model
95 % interval **[−.11564245, +.13531733]**. Machine readings: `importance_reading = small_signed`,
`uncertainty_reading = interval_includes_zero`, `interval_inside_mei = false`.
Two blocks are positive and two negative; the block SD (.079 J) is about five times the
within-block conditional panel SE (.013–.016 J), so the 32 nested panel worlds never measured
the relevant uncertainty. Nothing here is equivalence, stable superiority or attribution.

## All endpoints, by arm, block and panel rollout

Each entry is the 32-world mean J of one panel of the named fit (native score factor
6U/500; panels after 5, 10 and 15 rollouts of the same trajectory; the training trajectory
is bit-identical with and without the interim panels, reviewer probe at `dc4dbdfcd`).

| Block (train / eval base) | FLAT 5 | FLAT 10 | FLAT 15 | D1280 5 | D1280 10 | D1280 15 | I1280 5 | I1280 10 | I1280 15 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 772203 / 782203 | .432939 | .343521 | .336531 | .372062 | .354166 | .340767 | .427150 | .430355 | .439126 |
| 772303 / 782303 | .347563 | .499962 | .513592 | .271522 | .300959 | .405663 | .412261 | .406359 | .450378 |
| 772403 / 782403 | .355251 | .331354 | .423893 | .336127 | .317261 | .424325 | .329331 | .445638 | .340921 |
| 772503 / 782503 | .390131 | .312032 | .530132 | .439014 | .506588 | .452340 | .449035 | .403937 | .432018 |
| four-block mean | .381471 | .371717 | .451037 | .354681 | .369743 | .405773 | .404444 | .421572 | .415611 |

## Contrasts per rollout (four blocks each; df = 3 working model)

| Contrast | Rollout | Block 772203 | Block 772303 | Block 772403 | Block 772503 | Mean | Sample SD | SE | Working-model 95 % interval |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| SI1280 | 5 | +.05508808 | +.14073948 | −.00679584 | +.01002085 | +.04976314 | .06603892 | .03301946 | [−.05531799, +.15484427] |
| SI1280 | 10 | +.07618917 | +.10539972 | +.12837682 | −.10265063 | +.05182877 | .10517726 | .05258863 | [−.11552928, +.21918682] |
| **SI1280, primary** | 15 | +.09835977 | +.04471497 | −.08340338 | −.02032159 | +.00983744 | .07885865 | .03942933 | [−.11564245, +.13531733] |
| GAP_D | 5 | −.06087735 | −.07604063 | −.01912377 | +.04888262 | −.02678978 | .05589481 | .02794740 | [−.11572960, +.06215003] |
| GAP_D | 10 | +.01064499 | −.19900279 | −.01409235 | +.19455577 | −.00197359 | .16098694 | .08049347 | [−.25813602, +.25418883] |
| GAP_D | 15 | +.00423585 | −.10792924 | +.00043235 | −.07779277 | −.04526346 | .05634254 | .02817127 | [−.13491570, +.04438879] |
| GAP_I | 5 | −.00578927 | +.06469885 | −.02591961 | +.05890347 | +.02297336 | .04564282 | .02282141 | [−.04965349, +.09560021] |
| GAP_I | 10 | +.08683416 | −.09360307 | +.11428447 | +.09190514 | +.04985518 | .09637954 | .04818977 | [−.10350395, +.20321430] |
| GAP_I | 15 | +.10259562 | −.06321428 | −.08297103 | −.09811436 | −.03542601 | .09311734 | .04655867 | [−.18359432, +.11274230] |

`SI1280` = I1280 − D1280 (high-batch renewal simple effect); `GAP_D` = D1280 − FLAT and
`GAP_I` = I1280 − FLAT are *untuned cross-information package gaps*, never §11.7 headroom
(`contrast_meaning` in `RESULT_SUMMARY.json`). Every contrast passed the runner's comparable-
view check (host, device, threads, precisions, score factor, rollouts, panel rollouts, launch
sha and the non-planned configuration fields identical across the operands); the planned
differences are the arm recipes of card §2 and the inert FLAT switch fields of §8.

## Rollout-5 accumulation (declared in the card, outcome-informed descriptive)

| Group | Blocks | SI1280_5 values | Mean | Sample SD | SE | Working-model 95 % interval |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| new (this object) | 4 | +.05508808, +.14073948, −.00679584, +.01002085 | +.04976314 | .06603892 | .03301946 | [−.05531799, +.15484427] |
| historical (completed factorial, blocks 772003, 772103) | 2 | −.02644030, +.08464985 | +.02910478 | .07855260 | .05554508 | [−.67666206, +.73487161] |
| accumulated | 6 | — | **+.04287702** | .06296499 | .02570535 | [−.02320115, +.10895519] (df = 5) |

The runner's note is quoted: “explicitly outcome-informed descriptive accumulation of the rollout-5 primary over the new blocks and the completed factorial's two blocks; the five-rollout prefix, evaluation and seed semantics are inherited unchanged; not prospective independent confirmation”

## Counts, receipts and integrity

Every fit: `status: complete`, `launch_sha dc4dbdfcdb20ca29a47c1187e9ebf6787483d21b`, model
constructions 2, training starts 1, checkpoint loads 0, training transitions
120,000 (all stored), training episodes 240, update stages 15, evaluation
steps 48,000 in 96 episodes (three panels of 32 worlds), batched control calls
9,000. Twelve fits total 1,440,000 training and 576,000 evaluation team steps, 2,880 + 1,152
episodes, 180 update stages, 24 model constructions, 108,000 batched control calls: exactly the
card §5 S column. Optimizer calls per fit: discoverer actor and critic 33,750 each in every
arm; coordinator 225 (D1280), 960/1065/990/1050 (I1280 by block), 0 (FLAT); team discriminator 225 /
individual discriminator 900 in D1280 and I1280, both 0 in FLAT (the FLAT coordinator and
discriminators are never updated, as the card requires). Every `training.jsonl` row finite.
Per-element `admission.json` on the node passed (≥ 4 GiB physical and effective) immediately
before each fit; supervisor exit 0 for all twelve handles (`fits/block_<seed>_queue.jsonl`);
`learner_logs/` and `evaluation_logs/` were empty on the node. Collected files per fit:
`summary.json`, `manifest.json`, `admission.json`, `training.jsonl`,
`whole_command_resources.json`, queue markers and the supervisor `task.log` (summary sha256
digests in the tracker returns recorded in [EXECUTION.md](baseline_interruption_b01_20260915/EXECUTION.md)).
Reduce: `scripts/run_fsd_baseline_interruption_b01.py reduce` on the Windows control checkout
at main `aff026fea` (the reduce records that checkout's HEAD as its own `launch_sha`; the
fits' launch sha is `dc4dbdfcd`), output copied verbatim to
[RESULT_SUMMARY.json](baseline_interruption_b01_20260915/RESULT_SUMMARY.json).

## Resources (whole-command GNU time on `hmasd-wsl-node`, CPU FP32, 4 threads per fit)

| Fit | Wall s | Peak RSS KiB | Fit | Wall s | Peak RSS KiB | Fit | Wall s | Peak RSS KiB |
| --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |
| 772203_FLAT | 2022.50 | 1,251,540 | 772203_D1280 | 2642.05 | 2,826,100 | 772203_I1280 | 6369.48 | 3,825,768 |
| 772303_FLAT | 2589.24 | 1,234,008 | 772303_D1280 | 2637.78 | 2,881,412 | 772303_I1280 | 6550.17 | 3,817,448 |
| 772403_FLAT | 2551.63 | 1,234,756 | 772403_D1280 | 2617.32 | 2,867,548 | 772403_I1280 | 6353.28 | 3,837,196 |
| 772503_FLAT | 2594.40 | 1,249,204 | 772503_D1280 | 3428.12 | 2,846,552 | 772503_I1280 | 5045.10 | 3,877,192 |
| FLAT sum | 9757.77 | | D1280 sum | 11325.27 | | I1280 sum | 24318.03 | |

Summed native wall **45,401.07 s** (plan 24,000–30,000 s; the plan assumed one fit at a
time, the node ran three to four fits plus the ACVC block-2 fits concurrently, about 3.9 cores
per fit); user CPU about four times wall. Peak RSS by arm about 1.2 GiB (FLAT), 2.8 GiB (D1280),
3.8 GiB (I1280). Not a cap; no stop, retry or replacement.

## Deviations and technical facts without polarity

- 12:36Z quoting defect: the first three queues received one arm instead of two, so the I1280
  originals were launched as single-arm elements at the same source, sha and seeds (EXECUTION.md).
  No I1280 process existed before the relaunch; no result was produced twice.
- The FLAT arm launched after the `k = 10` correction was confirmed (12:55Z); block pairing is
  by fixed base seeds, so arm order within a block does not change the object.
- Scheduling gap 14:15Z–16:01Z (hub session rate-limited); the last five elements ran together.
- `learner_logs/` and `evaluation_logs/` empty on the node (no learner-side log output is part
  of this object's instrumentation); telemetry present for every fit.

