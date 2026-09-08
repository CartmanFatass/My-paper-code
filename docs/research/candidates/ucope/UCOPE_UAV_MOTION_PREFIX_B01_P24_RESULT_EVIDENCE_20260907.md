# UCOPE UAV motion prefix B01 — P24 result evidence, 2026-09-07

**E0 / COMPLETE / WITHIN.** The two newly allocated training pairs have
native T−G means **+0.043351866492163174** and **−0.050365422532689566**;
their primary mean is **−0.003506778020263196**. Both signs and the adverse
generic-versus-hover result are retained. This is a valid B/EXPLORE result,
not equivalence, a stable population judgment or a direction disposition.

## Frozen object and rule applied verbatim

Object `UCOPE-UAV-MOTION-PREFIX-B01`, P24 continuation. The [card §10](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#10-prospective-p24-fresh-pair-continuation-and-p26-plumbing--2026-09-07)
was prospectively committed at `8cb59913be5015c3948e4a1c24024147023fdf97`.
It applies the original §4 reading to masters **6901/6902 only**:

> -.01 <= Delta <= .01: no gain at the selected scale under this budget; not stable equivalence.

The applicable qualifier is also unchanged:

> A missing hover or information diagnostic limits competence or attribution; independently trustworthy T−G remains reportable. Native losses are reported separately from any favorable local diagnostic.

Both primary, hover and selected diagnostics are complete. `Delta` is the
equal mean of the two training-pair endpoints; each endpoint averages all
32 declared sampled complete-episode T−G differences. `J` is the sum of
unmodified native team reward over all256 steps, divided by256. No selected
checkpoint, omitted seed, added evaluation or reward substitution enters it.
The independent training unit is the matched T/G training pair, n=2 for P24.

P24 is an outcome-informed continuation after P21. Card §10 separately
requests an equal-weight description of all four named training pairs. That
description does not replace either two-pair primary, constitute a new n=4
decision rule or provide prospective four-pair confirmation. Historical
finite-host B01–B05 are not pooled into any UAV statistic.

## Native endpoints and uncertainty

| Allocation / master | T mean J | G mean J | H mean J | T−G | Conditional SE | G−H | Conditional SE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P21 / 6801 | 0.1981565110 | 0.1914424788 | 0.1490047481 | +0.0067140322 | 0.0111257954 | +0.0424377306 | 0.0120716907 |
| P21 / 6802 | 0.1792768687 | 0.1555560597 | 0.1462546807 | +0.0237208090 | 0.0101315309 | +0.0093013790 | 0.0087827912 |
| P24 / 6901 | 0.1529236928 | 0.1095718263 | 0.1377756427 | +0.0433518665 | 0.0101066870 | −0.0282038164 | 0.0139165852 |
| P24 / 6902 | 0.1120917124 | 0.1624571349 | 0.1453561970 | −0.0503654225 | 0.0097848517 | +0.0171009380 | 0.0118908145 |

| Quantity | Mean T−G | Training-endpoint sample SD | Conditional evaluation SE | Status |
| --- | ---: | ---: | ---: | --- |
| Original P21 primary | +0.015217420622321492 | 0.012025607177551996 | 0.007523816216520829 | Original UP retained |
| New P24 primary | −0.003506778020263196 | 0.06626813058389298 | 0.007033641405302189 | Fixed WITHIN |
| Four-pair description | +0.005855321301029148 | 0.040359534081716275 | 0.005149755379587538 | Outcome-informed description; below0.01 |

Pair SE is the sample SD of its32 paired whole-episode differences divided
by `sqrt(32)`. Joint conditional SE is `sqrt(SE_6901²+SE_6902²)/2`; the
four-pair analogue divides by4. Endpoint SD uses ddof=1. These conditional
evaluation errors do not replace training-population uncertainty. Neither
episodes nor agents become additional training units; no confidence interval
or significance verdict is inferred from these few pairs.

All final episode contrasts remain in the original records. P24 has9/32
adverse T−G episodes in6901 and27/32 in6902, with minima−0.0520269563 and
−0.1453049646. Across the four pairs,62/128 contrasts are adverse; this is
descriptive heterogeneity, not128 independent training observations. The
P24 G−H mean is−0.005551439244279553, endpoint SD0.032035299053513926,
conditional SE0.009152360542971284. H remains an untuned reference, not a
headroom bound. Descriptive T−H is+0.0151480500 in6901 and−0.0332644846 in6902.

## Actual counts, selection and learner exposure

The unchanged task has five jointly learning local actors,50 users and256
primitive steps. T makes one learned opening duration choice1/4 per actor;
G retains every legal primitive velocity action and the same free local
information. Each fit receives131,072 training steps and1,024 positive-lr
Adam calls. The existing final-only evaluation has32 episodes per T/G/H.
Every allocated outcome was retained;6902 ran after technical acceptance of
6901 irrespective of its scores.

| Actual work | Per new pair | P24 total | P21+P24 descriptive total |
| --- | ---: | ---: | ---: |
| Real learned fits | 2 | 4 | 8 |
| Training team/UAV steps | 262144 | 524288 | 1048576 |
| Final evaluation team/UAV steps | 24576 | 49152 | 98304 |
| All team/UAV steps | 286720 | 573440 | 1146880 |
| Adam calls | 2048 | 4096 | 8192 |
| Training / evaluation episodes | 1024 / 96 | 2048 / 192 | 4096 / 384 |
| Constructor resets | 2 | 4 | 8 |
| Selected diagnostic frames | 1600 | 3200 | 6400 |
| Partial episode steps | 0 | 0 | 0 |

P24 contains1,024 training rollouts,2,777,453 actual velocity decisions,
5,440 duration decisions and2,785,280 recurrent observations. T's training
velocity counts are651649/651697 and evaluation counts40723/40744;
its training d4 counts are1237/1221, evaluation79/72. G has655360 training
and40960 evaluation velocity decisions per pair. Held samples are absent
from T's action likelihood while primitive observation/reward/credit continue.
H has no learner. There is no nested candidate search or added validation run.

| Master / arm | Parameters | Initial norm | Final norm | Absolute displacement | Relative displacement |
| --- | ---: | ---: | ---: | ---: | ---: |
| 6901 / T | 66441 | 15.49398994 | 17.81788254 | 8.57486153 | 0.55343146 |
| 6901 / G | 66311 | 15.49399090 | 16.98371887 | 6.82159138 | 0.44027336 |
| 6902 / T | 66441 | 15.44147110 | 17.38687897 | 7.66978788 | 0.49670060 |
| 6902 / G | 66311 | 15.44147110 | 17.51329422 | 7.95038939 | 0.51487254 |

CM verified finite FP32 checkpoint contents and their correspondence to saved
configuration/norms; DM did not execute or reload checkpoints. Duration heads
start at zero and move by0.14413470/0.12135836. Their stored epsilon-normalized
relative values are not meaningful relative effect sizes. Nonzero exposure
establishes actual learning, not policy quality or adequate generic competence.

## Receipts, complete caps and deviations

Both runs use exact source **`9c541a8047b8c33e90f09aa65e326180343a23a0`**,
node `hmasd-wsl-node`, interpreter `/home/wu/.venvs/hmasd/bin/python`,
CPU FP32 learner/one compute thread, and detached cwd
`/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p24-20260907`.
The [bound handoff](UCOPE_UAV_MOTION_PREFIX_B01_P24_ROOT_HANDOFF_20260907.md)
was committed at `4fdf6fb73c06d26fdb84a33b33edde6206c907cb` and DM readiness
at `2a96c7ecdea1fb01fb897912ffbb3f82cf8fb778`. The P26 correction changed
seed admission/pair labels/two-summary plumbing only; accepted learner,
environment, information/reward and numerical training code remain unchanged.

| Master / accepted supervisor | PID | UTC start → terminal | Exit | Whole wall s | Logged T / G wall s | Peak RSS KiB | Admission physical/effective bytes |
| --- | ---: | --- | ---: | ---: | --- | ---: | ---: |
| 6901 / `ucope-uav-motion-prefix-b01-6901-p24-20260907` | 2764097 | 2026-09-08 05:51:01 → 05:55:46 | 0 | 284.29 | 140.337403 / 135.448773 | 554072 | 15653224448 |
| 6902 / `ucope-uav-motion-prefix-b01-6902-p24-20260907` | 2765006 | 2026-09-08 06:01:48 → 06:06:28 | 0 | 280.64 | 136.742595 / 135.930139 | 555104 | 15652552704 |

Each fresh actual-node physical/effective admission exceeds4 GiB and is
joined immediately to the issued runner. Complete limits remain1800 s per
arm,3600 s per pair and7200 s P24 sum, including startup, learning,
evaluation/checking and publication. Startup/common initialization belongs
to T; H/publication belongs to G. Even the conservative whole pair time is
below the per-arm limit. No cap breach is recorded.

P24 summed external wall is **564.93 s per valid two-pair B result**. The
first supervisor start to last terminal is **927 s**, including the intervening
technical-return interval and excluding later DM intake; it is not aggregate
CPU work or the full study's end-to-end elapsed time. P21+P24 sum to1140.17 s
external invocation wall. Aggregate CPU and scratch remain
`resources_unmeasured`; memory admission, wall and peak RSS are measured.
Scope §4 additions: **none**. No §5 engineering budget breach is reported.

Both P24 output roots use the intended LF-safe names. P21's historical6801
CR-suffixed remote artifact path and collection correction remain unchanged;
they did not recur here. The P26 fixture-only correction history stays in its
readiness record. No retry, unallocated invocation, missing primary/hover/
diagnostic or nonfinite result occurred. No scientific polarity is inferred
from terminal success alone.

## Evidence inspected and reproducible analysis

DM read both complete technical returns against card §§2–5,8,10, the retained
verification/count/exposure facts, actual summary bindings/arrays and saved
episode, selected diagnostic and supervisor/admission records. The
[scientific analysis](UCOPE_UAV_MOTION_PREFIX_B01_P24_SCIENTIFIC_ANALYSIS_20260907.json)
recomputes the declared endpoints and selected movement/learning summaries;
it agrees with CM's [unchanged two-summary aggregate](UCOPE_UAV_MOTION_PREFIX_B01_P24_JOINT_AGGREGATE_20260907.json).
Unlogged PPO likelihood/gradient internals rely on accepted source and the
existing independent review/tests; no trajectory replay or test rerun was added.

The local analysis root is
`C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-p24-intake/`,
with `analyze.py`, `analysis.json`, `scores.csv` and `run_summary.json`.
`hmasd-scientific-tools/scripts/summarize_runs.py` received the eight already
paired training-endpoint scores (four masters × T−G/G−H), without a second
`--paired` operation. It corroborates the four-unit descriptive means/SDs.
This analysis imports no experiment/model and adds zero UAV or optimizer calls.

Raw roots are
`C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-<master>-p24-20260907/`
for6901/6902, containing summary, episodes/rollouts/diagnostics JSONLs,
final T/G checkpoints, admission and `supervisor/` receipts. The original
P21 roots/analysis supply6801/6802 unchanged. Durable technical evidence:

- [6901 acceptance](UCOPE_UAV_MOTION_PREFIX_B01_6901_TECHNICAL_ACCEPTANCE_20260907.md)
  and [verification](UCOPE_UAV_MOTION_PREFIX_B01_6901_TECHNICAL_VERIFICATION_20260907.json),
  commit `eb287e235d98eba404f534defbb2b09c4b58fda7`.
- [6902 acceptance](UCOPE_UAV_MOTION_PREFIX_B01_6902_TECHNICAL_ACCEPTANCE_20260907.md)
  and [verification](UCOPE_UAV_MOTION_PREFIX_B01_6902_TECHNICAL_VERIFICATION_20260907.json),
  commit `b5a79533a623b42d1cea4a2a989216c908b1c979`.

The [DM intake](UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md) interprets
these facts, predictions, owner flags and the current task boundary.
