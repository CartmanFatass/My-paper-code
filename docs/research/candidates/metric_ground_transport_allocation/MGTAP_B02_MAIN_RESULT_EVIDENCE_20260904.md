# MGTAP B02 main panel — complete, technically accepted

The exact frozen main panel exists and passes technical acceptance: six fits,
each with 256 real learner updates and all 17 evaluation points. Recomputed
episode arrays agree with every reported N/load/aggregate curve. The card's
ordered rule returns **B02_INSIDE_MEI**: mean METRIC-minus-FREE curve AUC
contrast **0.008396685564959483**, below the declared absolute MEI 0.01.
All three seed contrasts are positive. This is a preliminary bundled
coordinate/finite-SGD comparison on the trained N=4/8 allocation toy; it does
not establish metric-specific causality, stable superiority or equivalence.

Card: `MGTAP_B02_CURVES_SCIENCE_CARD_20260904.md`. Technical implementation and
independent review: `MGTAP_B02_TECHNICAL_EVIDENCE_20260904.md`. Main machine
summary: `MGTAP_B02_MAIN_SUMMARY_20260904.json` (all seed/N/load curves, counts,
runtime measurements, source/command paths, admission receipts). Pilot is
separately recorded in `MGTAP_B02_PILOT_RESULT_EVIDENCE_20260904.md` and excluded
from this estimand. DM accepted its unchanged cost law and released the main
panel in committed/pushed intake `9145a4c3a` before main activity.

## Exact execution and terminal evidence

Source SHA **f3595bfe3e90024f3b31eb8a82910304b90543d3**, pushed before launch;
CPU float64, one thread, configured node `wsl_4070` (SSH `hmasd-wsl-node`, host
`LAPTOP-U9TDKC8A`). Cwd `/home/wu/hmasd-worktrees/mgtap_b02_20260904` remained
detached at the same source SHA used by the pilot. No source edits or new
configuration occurred after the pilot.

The accepted task was **mgtap_b02_main_203_211_223_f3595bfe**, a fixed sequential
list under the existing `/usr/local/bin/agent-task` supervisor. PID 103077;
terminal `finished`, exit 0, at `2026-09-05T06:47:40+08:00`
(`2026-09-04T22:47:40Z`), supervisor wall 11 seconds. Log:
`/home/wu/.agent-tasks/mgtap_b02_main_203_211_223_f3595bfe/task.log`; terminal
exit is in that task directory's `exit_code`. The task was launched once.
CM sent its handle immediately and observed terminal on its first bounded
status read before tracker adoption. Tracker received the same terminal
handle; no routine polling followed adoption.

Each seed has its own root under cwd:
`temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_main_<seed>`.
The three roots were copied without modification to the same relative paths
under `C:/Projects/HMASD-worktrees/cm-n5-b02-20260904`. Each contains
`admission.json`, `summary.json`, `oracle_returns.npy`, and both arms'
`<ARM>_training.json` and `<ARM>_evaluation.npz`.

The accepted command was `cd` to the cwd, then these six commands joined by
`&&` in the shown order (interpreter `/home/wu/.venvs/hmasd/bin/python` each):

```text
scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_main_203/admission.json
scripts/run_mgtap_b02_curves.py --mode main --seed 203 --oracle /home/wu/hmasd-worktrees/mgtap_b02_20260904/temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907/oracle_returns.npy --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_main_203
scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_main_211/admission.json
scripts/run_mgtap_b02_curves.py --mode main --seed 211 --oracle /home/wu/hmasd-worktrees/mgtap_b02_20260904/temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907/oracle_returns.npy --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_main_211
scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_main_223/admission.json
scripts/run_mgtap_b02_curves.py --mode main --seed 223 --oracle /home/wu/hmasd-worktrees/mgtap_b02_20260904/temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907/oracle_returns.npy --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_main_223
```

Every node-local receipt passed both physical and effective 4-GiB floors
immediately before its invocation. Available bytes were respectively
15,429,967,872 at `22:47:29.631981Z`, 15,435,071,488 at `22:47:33.676492Z`,
and 15,433,801,728 at `22:47:37.250912Z` on 2026-09-04. No local receipt was
used for remote admission. The pilot oracle was loaded read-only by all main
seeds; collected arrays match it exactly. It never enters actor inputs/labels.

## Card rule and curve measurements

For each seed, equal-weight N=4/8 native return is integrated with the complete
grid `[0,16,...,256]`, using trapezoidal area divided by 256. The pilot seed
1907 is not included. There is no checkpoint or hyperparameter selection.

| Seed | METRIC AUC | FREE AUC | d_s | Delta at 16 | Delta at 64 | Delta at 256 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 203 | 0.409158579508464 | 0.401116858588325 | 0.008041720920139 | 0.002360026041667 | 0.006822374131944 | 0.006727430555556 |
| 211 | 0.406846957736545 | 0.399160342746311 | 0.007686614990234 | 0.002794053819444 | 0.007896592881944 | 0.007560221354167 |
| 223 | 0.408928510877821 | 0.399466790093316 | 0.009461720784505 | 0.003268771701389 | 0.010348849826389 | 0.007500542534722 |

Mean d_s = **0.008396685564959483**; range
`[0.007686614990234375, 0.009461720784505134]`; sample standard deviation
**0.0009392816774098368**. The mean contrasts at 16/64/256 are respectively
0.002807617187500, 0.008355938946759, and 0.007262731481481.

Ordered reading: positive branch requires D >= 0.01 and at least two positive
d_s; false because D < 0.01. Negative branch requires D <= -0.01 and at least
two negative d_s; false. Third branch requires abs(D) < 0.01; true, hence
`B02_INSIDE_MEI`. Three training seeds do not justify a stable-performance
confidence claim, and the evaluation tapes are not additional training replicates.

The immediate-allocation oracle is 0.668750000000000 at each N, with load means
SLACK 0.584722222222222 and OVERLOAD 0.752777777777778. Final equal-weight
return is 0.491427951388889 (METRIC) and 0.484165219907407 (FREE), giving
oracle gaps 0.177322048611111 and 0.184584780092593. This untuned FREE result
does not complete the historical tuned held-out-size headroom record. Generic
conditioning and effective step size remain live alternatives.

## Actual learner counts and measurement acceptance

| Quantity | Per arm/seed | Complete main panel |
| --- | ---: | ---: |
| Optimizer updates | 256 | 1,536 |
| Training allocation transitions | 24,576 | 147,456 |
| Training autoregressive agent steps | 147,456 | 884,736 |
| Evaluation episodes | 13,056 | 78,336 |
| Evaluation allocation decisions | 26,112 | 156,672 |
| Evaluation autoregressive agent steps | 156,672 | 940,032 |

Each fit has 256 finite trace rows, 17 checkpoint vectors of length 60, and
episode-return arrays of shape `(17,2,12,2,16)` with explicit N/pair/load axes.
CM checked exact update/checkpoint sequences, nonzero first steps, zero initial
parameters, finite measurements, all counts, matching initial episode returns
between arms, terminal parameter norms against displacement traces, and every
checkpoint's aggregate/N/load returns recomputed from raw arrays (absolute
tolerance 1e-15). All passed. The shared deterministic oracle arrays match the
pilot exactly. Complete-grid aggregation was run offline over the three
existing summaries through the runner's `--mode summarize --inputs ... --out
temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_main_aggregate`
path; no learner was run during this collection.

| Seed | Arm | First step L2 | Final distance L2 | Cumulative path L2 |
| --- | --- | ---: | ---: | ---: |
| 203 | METRIC | 0.013332512750303 | 2.414847679465533 | 3.440035084852661 |
| 203 | FREE | 0.013062735141931 | 2.396114130651889 | 3.540496773236419 |
| 211 | METRIC | 0.014276015200858 | 2.362505931113395 | 3.371913141147122 |
| 211 | FREE | 0.014555366097114 | 2.352359328704311 | 3.460859207741955 |
| 223 | METRIC | 0.020372191061355 | 2.402658057842639 | 3.431710398136845 |
| 223 | FREE | 0.019094437463268 | 2.386210639723374 | 3.486188430911521 |

Static main exposure: 60 parameters, zero initializer, lr 0.1, gradient clip 5,
256 updates, maximum path L2 128 against a unit-logit reference. Real movement
and full learning curves are observed. No stationarity/competence gate was
applied; no old C registered activity, CUT arm, alternative seed, weight decay
or RNG-law modification was introduced.

## Resource accounting and final technical boundary

Before main, the accepted pilot projected METRIC 11.4792425385 seconds and FREE
6.1553556643 seconds over all three seeds using the frozen factor-two law;
both were below 300 seconds per arm. These projections were recorded before
launch and were not replaced by main observations.

| Seed | METRIC arm wall s | FREE arm wall s | Shared setup s | Runner wall s | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| 203 | 1.957890727 | 1.026300055 | 0.010505360 | 2.997007007 | 482,041,856 |
| 211 | 1.542273256 | 1.019690662 | 0.009988047 | 2.573378199 | 482,988,032 |
| 223 | 1.558097292 | 1.032986636 | 0.010001674 | 2.602393602 | 482,304,000 |

Main runner wall totals **8.172778808002477 seconds**. Total runner wall
including the separately labeled pilot is **8.939538596001512 seconds**.
Supervisor wall is **11 seconds main / 13 seconds including pilot**; this
coarser clock includes preflight/interpreter/import overhead. Total shared
setup across pilot and main is **0.095476074995531 seconds**, below 60.
Every main arm/seed is below its 100-second bound; all resources are measured.
Fixed arm order and first-arm optimizer warm-up make arm wall scheduling data,
not evidence that one coordinate system is causally more compute efficient.

The main learner, `--oracle` loading, complete 17-point publication and offline
aggregate path now have actual runtime coverage; the prelaunch tests had nine
passes and independent focused inspection had no material finding. No source
repair, failed learner, retry, truncated arm, missing required measurement or
scientific deviation occurred. Scope remains none; no extra test reruns or
result-bearing invocations followed this panel. Technical conformance does not
establish scientific truth. DM owns scientific intake and interpretation.

At this boundary all assigned computation is terminal, outputs are retained,
and this result ends the authorized round. No successor object is selected or
launched.

## Complete equal-weight mean curves

Each point averages three training seeds and N=4/8 equally. Individual seed,
N and load curves remain in the machine summary; the mean does not replace them.

| Update | METRIC | FREE | METRIC minus FREE |
| --- | ---: | ---: | ---: |
| 0 | 0.251869936342593 | 0.251869936342593 | 0.000000000000000 |
| 16 | 0.283346896701389 | 0.280539279513889 | 0.002807617187500 |
| 32 | 0.311472800925926 | 0.305705656828704 | 0.005767144097222 |
| 48 | 0.335453739872685 | 0.328709129050926 | 0.006744610821759 |
| 64 | 0.357381184895833 | 0.349025245949074 | 0.008355938946759 |
| 80 | 0.379633246527778 | 0.369110785590278 | 0.010522460937500 |
| 96 | 0.398196976273148 | 0.387114800347222 | 0.011082175925926 |
| 112 | 0.413484700520833 | 0.404034649884259 | 0.009450050636574 |
| 128 | 0.427091471354167 | 0.418298791956019 | 0.008792679398148 |
| 144 | 0.438604058159722 | 0.429205548321759 | 0.009398509837963 |
| 160 | 0.449239547164352 | 0.438704427083333 | 0.010535120081018 |
| 176 | 0.457715747974537 | 0.447897677951389 | 0.009818070023148 |
| 192 | 0.467135054976852 | 0.456948061342593 | 0.010186993634259 |
| 208 | 0.473784722222222 | 0.465045392071759 | 0.008739330150463 |
| 224 | 0.481722909432870 | 0.471629955150463 | 0.010092954282407 |
| 240 | 0.487069589120370 | 0.478647641782407 | 0.008421947337963 |
| 256 | 0.491427951388889 | 0.484165219907407 | 0.007262731481481 |
