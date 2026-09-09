# UCOPE renewal B02 P71 — native result evidence

**B/EXPLORE, valid UP on new matched training pair7401.** The above-MEI
native package margin recurs: T−G +0.024658177040921356, conditional
evaluation SE0.011145715505143731. T−H and G−H are positive on this panel.
P70 remains separate; two favorable fitted observations do not establish stable
training-population superiority or isolate renewal/information value.
The [machine-computed summary](UCOPE_UAV_RENEWAL_COMMITMENT_B02_P71_RESULT_SUMMARY_20260908.json)
retains all 96 final returns and all three signed paired vectors.

## E0.1 Object, frozen inputs and actual invocation

Object `UCOPE-UAV-RENEWAL-COMMITMENT-B02`, master **7401**, selector
`renewal_b02`. [Card §§1–7](UCOPE_UAV_RENEWAL_COMMITMENT_B02_SCIENCE_CARD_20260908.md)
and P71's cohesive allocation were prospective at
`ba0915bb0269050609bee9b4d5d988cef913cd2c`.

- Accepted scientific source: `7adc5aae35542ba35b4b8a2c07fc8285e958ce4d`.
- Source acceptance and literal payload record: `0f65cf3771bbc119f303afd378f6132a44e6589a`.
- CM terminal collection: `90b02fba8cccdd51da50bbee98b3a278454c684f`, with a
  trailing-space-only correction at `aea0b6114d005207100fd3661283ec074ebcd690`.
- Node: configured `hmasd-wsl-node`, CPU FP32, one Torch thread.
- Supervisor: `ucope-uav-renewal-b02-7401-p71-20260908`.
- Remote cwd: `/home/wu/hmasd-worktrees/ucope-uav-renewal-b02-7401-p71-20260908`.
- Output relative to cwd: `temp/directions/ucope/exp/ucope-uav-renewal-b02-7401-p71-20260908`.
- Local collection: that same relative path under
  `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`.

Exactly one accepted detached submission; CM remained the sole observer through
collection. The raw supervisor log records start **2026-09-09T14:05:15+08:00**,
exit **2026-09-09T14:10:21+08:00**, code **0**. Terminal readback reports
finished, PID3026239, inactive tmux and the exact source. Its later uptime372s
is the age of a snapshot, not the invocation wall. Native status is **COMPLETE**,
with empty limits and no cap breach or partial steps.

The executed 707-byte LF wrapper retains SHA256
`fc26523a08e89c9e84fbb65b20ab79768207ddf647bae6a19742d4f6a5a0abbb`.
Fresh canonical actual-node admission at **2026-09-09T06:05:15.185521Z**
measured physical/effective available memory both **15640408064 bytes**,
above **4294967296**, before scientific creation. Its supervisor and output
copies are one byte-identical measurement, not independent admissions.
The [CM intake §§4–6](UCOPE_UAV_RENEWAL_COMMITMENT_B02_P71_INTAKE_20260908.md#4-cm-binding-source-acceptance)
records source/payload checks, acceptance, admission, learner progress and
terminal collection as distinct facts.

## E0.2 Native estimand and rule applied verbatim

For each final episode, `J=sum_t sum(info['rewards_dict'].values())/256`.
The primary is the mean of the 32 paired-episode T−G differences for 7401 only.
DM read-only analysis confirms all recorded `J=reward_sum/256`, final IDs0..31
and matched reset association, all 96 returns and three paired vectors, and
their native means/conditional SEs. No simulator, checkpoint rollout, CM suite
or tensor verification was repeated.

Applied card §5 UP rule, verbatim:

> Delta>+0.01: the above-MEI native package margin recurs on this new fit; consider a separately justified bounded follow-up with both fitted outcomes visible.

Comparator qualification, verbatim:

> Weak/negative G−H narrows improvement-over-competent-control wording without erasing trustworthy T−G. Positive T−H never reverses primary loss.

`Delta=+0.024658177040921356` exceeds +0.01 by **0.014658177040921356**:
**UP** under the unchanged point rule. Conditional evaluation SE is
**0.011145715505143731**, for the 32 episode pairs conditional on these
policies. This card's independent training **n=1** supplies no training-
population SD or interval. The run-level utility receives one selected endpoint
per trained T/G arm and one declared matched training seed. H is an untuned
fixed reference. The utility's difference of arm means differs only in the last
floating-point digit from the native mean of episode differences; the latter
remains the primary. No old endpoint is pooled into the reading.

## E0.3 Complete outcomes and separate fitted observations

| Arm | Final mean J | Evaluation episodes |
| --- | ---: | ---: |
| Renewal T | 0.1848478520611129 | 32 |
| Ordinary feedback G | 0.16018967502019155 | 32 |
| Untuned hover H | 0.14769953379747316 | 32 |

| Contrast | Mean paired difference | Conditional evaluation SE | Positive / negative / zero episodes |
| --- | ---: | ---: | ---: |
| T−G | +0.024658177040921356 | 0.011145715505143731 | 22 / 10 / 0 |
| T−H | +0.03714831826363973 | 0.014042694092488053 | 22 / 10 / 0 |
| G−H | +0.012490141222718373 | 0.009774298009822923 | 18 / 14 / 0 |

All adverse episodes remain. T−H supports the positive native package
observation. G−H's sampled point is positive on this panel, so P70's negative
hover point does not recur here. Its conditional uncertainty and the untuned
reference leave general comparator competence unestablished.

| Separate object/master | T−G | Conditional evaluation SE | T−H | G−H |
| --- | ---: | ---: | ---: | ---: |
| B01/P70, 7301 | +0.055673191348834944 | 0.011556059794903147 | +0.05305453732049459 | −0.002618654028340355 |
| B02/P71, 7401 | +0.024658177040921356 | 0.011145715505143731 | +0.03714831826363973 | +0.012490141222718373 |

These are **two independent fitted observations**, each with its own final
panel. Both are above the same MEI; the second is smaller. Neither the changing
magnitude nor changing G−H can be attributed solely to training: fitted histories
and evaluation panels both differ. This is a descriptive repeatability result,
not a pooled primary, a stable population interval or a causal renewal contrast.
Historical opening-family results remain separate and unchanged.

## E0.4 Actual learner exposure and native path

Each T/G arm completes 512 training episodes, 131072 training native steps,
256 two-episode rollouts and 1024 Adam calls, followed by 32 stochastic final
evaluations. H completes32. Total: **286720 native steps, 2048 Adam calls,
96 final evaluations**, 1120 explicit resets, two constructor resets,
512 rollouts and 1600 prescribed diagnostic rows; zero partial steps.

| T phase | Owned velocity/duration selections | d4 selections | Actually suppressed decisions | Horizon-censored holds |
| --- | ---: | ---: | ---: | ---: |
| Training | 247346 | 137057 | 408014 | 1570 |
| Final evaluation | 15261 | 8628 | 25699 | 99 |

G has 655360 training and40960 final velocity selections, with zero duration
selections; H has no selected decisions. The frozen actual path yields
`6*247346+2*15261 = 1514598` T head-forward rows, or **3344232384** dense
forward multiply-adds. These are counts from the same execution, not a timing
probe. Selected-d4 fractions are 0.5541104363927454/0.5653626892077845
for training/final evaluation. No favorable count or movement is a success rule.

Parameter totals match T68553/G66311 and T head2242. Absolute total movement is
T8.74242877960205/G8.507596969604492; T duration displacement0.8151726722717285,
hidden0.7989710569381714 and final0.16171500086784363. The zero-initial final
layer retains undefined relative displacement. Full norms and displacement
groups remain in the summary. CM's checkpoint comparisons use appropriate
FP32 tolerance; DM does not claim bit-equal norm reductions or replay learning.

This connects the implemented own-expiry/private-history/action/credit path to
nonzero learner exposure and measured native return. Persistence, geometry,
capacity, gradient exposure and partner co-adaptation remain unseparated.
Prior verified UTE/ACAC evidence supports the renewal-event distinction; neither
it nor head movement establishes information value or explains the gain.

## E0.5 Resources, conformance and preserved receipts

External whole wall **306.04s**, peak RSS **553464KiB**. Runner whole
**296.60590592201333s**; T/G complete arm wall **158.1893359690439s /
138.41656891599996s**, summed **296.60590488504386s**. All fit the original
1800s arm /3600s complete caps. The different timer boundaries do not localize
overhead. `resources_unmeasured`: aggregate CPU and system-wide peak memory;
admission, whole wall and external peak RSS are measured.

New invocation wall per valid result is **306.04s**. Across the two separately
accepted complete renewal fits, whole invocation walls sum to **610.89s**,
**305.445s per valid fit**. This excludes engineering and older opening regimes;
it is not total study/session critical path or aggregate CPU work.

Engineering conformance is separate: source +25/−20 and two test files +21/−13;
runner54 lines; **scope§4 none**, no §5 budget breach. One exact-source suite
passed89 tests, complete check wall3.92s of300s. The intermediate syntax-edit
error was corrected before source acceptance, with no scientific effect.
DM inspected the binding diff and original acceptance record; no independent
review was needed for a binding-only change and no credit scope gap arose.

All seven remote/local output SHA256 values match in CM's collection report and
are retained in the durable summary. DM additionally checked the collected
summary, episode and admission digests and the executed wrapper, then read the
supervisor boundaries and readback. The raw root contains source/check receipts,
the exact submission, `summary.json`, episode/rollout/diagnostic rows, T/G final
checkpoints, admission, supervisor files and read-only collection verification.
No new suite, rollout, checkpoint evaluation, simulation or replay was performed.

## E0.6 Predictions, decision and claim boundary

Recorded UP0.55 and G−H>0 at0.55 both occur: **2/2**, mean Brier score
**0.2025**. Owner prediction: **not taken (unattended)**. P70's prediction
scores remain historical. Predictions do not change the point rule.

DM accepts **valid UP** and ends P71 under its all-outcome boundary. The strongest
support is a second above-MEI native T−G observation with positive T−H, now with
positive sampled G−H. The strongest limits are only two fitted observations,
conditional evaluation noise and P70's weak G−H; prior opening losses remain
contrary evidence about those other packages. A separately allocated additional
independent same-package pair is the recommended next learning discriminator.
No new master, card, run, tuning, retry/resume, extra evaluation, family decision,
C promotion, Portfolio action or stable/causal claim follows from this intake.
See [DM intake §§7–10](UCOPE_UAV_RENEWAL_COMMITMENT_B02_P71_INTAKE_20260908.md#7-dm-all-outcome-check-and-reading)
and the [Chinese owner brief](../../portfolio/owner/briefs/ucope/2026-09-08_UCOPE_UAV_RENEWAL_COMMITMENT_B02_P71.md).
