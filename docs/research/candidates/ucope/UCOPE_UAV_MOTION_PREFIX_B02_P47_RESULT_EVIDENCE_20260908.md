# UCOPE UAV motion prefix B02 — P47 result evidence, 2026-09-08

**E0: COMPLETE / DOWN, B/EXPLORE.** Both allocated matched training pairs,
7001 and 7002, are valid and retained. The common per-agent-clipping T/G
comparison has mean native T−G **−0.026701655118179134**. This is adverse
evidence for this fixed task, opening prefix and learner budget. It is not
a causal comparison of clipping methods or a direction disposition.

## Rule applied verbatim and selection

[B02 card §5](UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md#5-native-primary-mei-and-reading-rule),
prospectively fixed at `1d46ddc2b142a2c2b98922a8f46e2d2609bda859`:

> Delta<-.01: adverse native evidence for this task/prefix/learner budget; local movement or information changes do not compensate.

The selected absolute MEI is 0.01 in complete time-average native team
reward. Each episode uses `J=sum_t sum(info['rewards_dict'].values())/256`.
Each master averages its 32 paired final episode differences; the primary
equally averages the two master endpoints. Neither the adapter's extra
agent average nor a reconstructed reward replaces the native measurement.
The card's other branches remain UP for Delta>.01 and WITHIN for
-.01<=Delta<=.01. No threshold or endpoint was selected after output.

There are **two independent matched training pairs**, four fitted learners,
and final-only sampled evaluation. The second pair ran after technical
acceptance of the first irrespective of its adverse sign. Episodes, agents,
frames and chunks are not additional training units. No old UAV or finite-host
result is pooled into B02. No third pair, retry, checkpoint choice or extra
evaluation occurred.

## Native endpoints and uncertainty

| Master | T mean J | G mean J | H mean J | T−G | Conditional SE | G−H | Conditional SE | T−H | Conditional SE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 7001 | 0.14909714127451154 | 0.19636424569819022 | 0.17158544962861455 | −0.04726710442367869 | 0.009568020281619656 | +0.024778796069575677 | 0.012014136875474236 | −0.022488308354103006 | 0.011239083046653865 |
| 7002 | 0.12314745662552364 | 0.12928366243820322 | 0.14753964411323622 | −0.0061362058126795795 | 0.008186926654579155 | −0.018255981675033013 | 0.013412586657048335 | −0.024392187487712595 | 0.01380510652790013 |

| Contrast | Equal-pair mean | Training-endpoint sample SD | Combined conditional evaluation SE | Role |
| --- | ---: | ---: | ---: | --- |
| T−G | **−0.026701655118179134** | **0.029083937324133818** | **0.006296284224781783** | Frozen primary: DOWN |
| G−H | +0.003261407197271332 | 0.030430183170068723 | 0.009003290588660638 | Descriptive comparator context |
| T−H | −0.0234402479209078 | 0.0013462458459349096 | 0.00890081392312317 | Descriptive native harm context |

Each conditional SE is the sample SD of 32 whole-episode paired differences
divided by sqrt(32); the joint value is `sqrt(SE_7001²+SE_7002²)/2`. Endpoint
SD uses ddof=1. These are different quantities; conditional evaluation SE
does not estimate training-population uncertainty. No confidence interval,
significance claim, stable harm or equivalence claim is inferred from n=2.

7001 has 23 negative and nine positive T−G episode differences; 7002 has 18
negative and 14 positive. Their minima are −0.21207451597848476 and
−0.09622602548480638. All **192 T/G/H J values**, episode IDs, signed
contrasts, exposure and receipt digests are preserved in the
[result summary](UCOPE_UAV_MOTION_PREFIX_B02_P47_RESULT_SUMMARY_20260908.json).
H is an untuned fixed hover reference without a learner. Its values and
the mixed G−H signs establish no tuned same-information headroom record.

## Actual work and learner exposure

The task is fixed at five UAVs, 50 users and 256 primitive steps. T owns one
opening velocity/duration-1-or-4 compound action per UAV, observes throughout
holds and resumes primitive feedback. G can select every legal velocity at
every step from the same free local information. Both use the same
agent-compound clipping, scalar native team-advantage credit, recurrent
architecture, FP32 CPU learner and declared RNG domains. Each fit has
131,072 training steps, 256 two-episode rollouts and 1,024 Adam calls at
lr=0.0003. There are no model-selection candidates or diagnostic runs.

| Actual work | 7001 | 7002 | Selected total |
| --- | ---: | ---: | ---: |
| Real fitted learners | 2 | 2 | 4 |
| Training team steps | 262144 | 262144 | 524288 |
| Final evaluation team steps | 24576 | 24576 | 49152 |
| Total team / native step calls | 286720 | 286720 | 573440 |
| Adam calls | 2048 | 2048 | 4096 |
| Training / final evaluation episodes | 1024 / 96 | 1024 / 96 | 2048 / 192 |
| Rollouts | 512 | 512 | 1024 |
| Diagnostic frames | 1600 | 1600 | 3200 |
| Constructors / constructor resets | 2 / 2 | 2 / 2 | 4 / 4 |
| Explicit resets | 1120 | 1120 | 2240 |
| Partial episode steps | 0 | 0 | 0 |

Actual velocity decisions total 2,777,303, duration decisions 5,440 and
recurrent observations 2,785,280. T's training d4 counts are 1,277 / 1,212;
its final d4 counts are 80/160 and 90/160 decisions, frequencies .50 and
.5625. Counts report real sampled exposure, not evidence that those holds
are useful. H adds no optimizer calls or independent fitted endpoint.

Machine-generated exposure line (absolute displacement and ratio to initial
total parameter norm; the full groups are in the result summary):

```text
master 7001 T: parameters=66441, Adam=1024, lr=0.0003, displacement=8.40929508, relative_to_initial=0.54403882;
master 7001 G: parameters=66311, Adam=1024, lr=0.0003, displacement=8.18938637, relative_to_initial=0.529811807;
master 7002 T: parameters=66441, Adam=1024, lr=0.0003, displacement=5.46673965, relative_to_initial=0.352969559;
master 7002 G: parameters=66311, Adam=1024, lr=0.0003, displacement=7.85659885, relative_to_initial=0.507274977
```

T's zero-initialized duration heads move by 0.1528752148 / 0.1861178130.
Their epsilon-normalized relative values are not meaningful relative effect
sizes. CM checked finite FP32 checkpoints and recorded post-update counters;
DM did not reload them or repeat the learning/checkpoint verification.
Real exposure establishes learning, not competence or a clipping mechanism.

## Recorded local changes and native consequences

The following is descriptive arithmetic over the already selected episode
and t0–t4 diagnostic records, computed after seeing the result. No trajectory
replay, reward recomputation or diagnostic experiment was performed.

| Master / arm | Mean opening displacement per UAV, m | Opening local-user entries, total | Mean served connections per step | Opening reward contribution to J |
| --- | ---: | ---: | ---: | ---: |
| 7001 T | 85.011066 | 133 | 8.758545 | 0.002601469 |
| 7001 G | 60.245107 | 157 | 11.753540 | 0.002734496 |
| 7002 T | 90.524514 | 188 | 7.029907 | 0.002557481 |
| 7002 G | 58.941880 | 169 | 7.560913 | 0.002425562 |

Displacement averages 32 episodes ×five UAVs. Entry totals sum set additions
between four consecutive t0→t4 diagnostic transitions for each episode/UAV;
they are neither unique users nor extra independent observations. Global
diagnostic identity sets do not enter an actor. They do not prove useful
information or a competent changed action.

7001's opening/suffix T−G contributions are −0.0001330268257367447 /
−0.04713407759794194. In 7002 they are +0.00013191875023219263 /
−0.006268124562911769. The prefix is t0–t3 native reward divided by256,
and the suffix is the rest of the same native episode. They sum to the
primary pair contrasts within ordinary floating-point accumulation. Larger
opening displacement occurs with both losses. The second pair's small
positive local prefix and increased user-entry total coexist with adverse
complete native return; no information-value conclusion follows.

## Source, receipts, resources and deviations

Exact scientific source: **`6374063408208ba67b8cb7c69ebc0babb0f00259`**.
Both pairs ran detached on `hmasd-wsl-node` in
`/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b02-p47-20260908`, using
the selected CPU FP32 / one-Torch-thread route. Remote output roots retain
their original `temp/directions/ucope/exp/uav-motion-prefix-b02-<master>-p47-20260908`
names. Collection copies are under the same relative paths in
`C:/Projects/HMASD/`.

| Master | Actual supervisor | UTC start → terminal | Exit / PID | Physical and effective available bytes |
| --- | --- | --- | --- | ---: |
| 7001 | `ucope-uav-motion-prefix-b02-7001-p47-20260908-cwd02` | 17:58:59 → 18:03:52, 2026-09-08 | 0 / 2781871 | 15639519232 |
| 7002 | `ucope-uav-motion-prefix-b02-7002-p47-20260908` | 19:14:37 → 19:19:22, 2026-09-08 | 0 / 2783664 | 15646416896 |

Each fresh actual-node admission passed the required 4,294,967,296-byte
physical/effective floors before scientific execution. `/proc/meminfo` is
the measured source; cgroup-specific fields remain null. Actual resource
facts are available; aggregate CPU work is unmeasured.

| Clock | 7001 seconds | 7002 seconds | Sum seconds |
| --- | ---: | ---: | ---: |
| T complete arm, including startup | 137.78884596005082 | 138.25656845699996 | 276.0454144170508 |
| G complete arm, including H/publication | 137.53816204698524 | 134.6804691849975 | 272.2186312319827 |
| Runner complete pair | 275.32700927200494 | 272.93703864404233 | 548.2640479160473 |
| External joined admission/runner | 293.10 | 284.84 | **577.94** |

External peak RSS is 553596 / 554792 KiB. Every internal arm is below1800s,
each complete external pair below3600s and the sum below7200s. The observed
first-start-to-second-terminal interval is 4823s, including the control-plane
gap; it is not summed compute or aggregate CPU work. The scientific route
used two actual invocations; the CM's one arithmetic-only aggregate took
0.156s and is separately recorded.

[7001 technical acceptance](UCOPE_UAV_MOTION_PREFIX_B02_P47_7001_TECHNICAL_ACCEPTANCE_20260908.md)
at `c838cfe2926e1b9d484e9cd73fd945a0464ff473` and
[7002/joint technical acceptance](UCOPE_UAV_MOTION_PREFIX_B02_P47_7002_AND_JOINT_TECHNICAL_ACCEPTANCE_20260908.md)
at `79ddbdda511a75852f513934c5fb07ed96ee7e7c` identify the raw source/configuration,
13-file hash correspondence per pair, complete episode/rollout/diagnostic
checks and caps. Root integrated the latter at `16640d462`. DM read these
records, raw primary/configuration/counts/exposure, admission/terminal bytes
and necessary diagnostics; no remote collection, model or technical checker
was repeated. The summary SHA-256 values are
`1f621ccc727bce4705356a5e1dafe08f95ec78968c8f297f3986837cf7138500` /
`8363eaf807068c36929074e2387d6fd8d9f8ce050e7ed07d9b6a2bf86b9b50a0`.

The original sole synthetic fixture's **80.578s/60s** engineering breach
remains under P48's named functional acceptance. The first 7001 supervisor
failed its wrong `cd` before preflight and scientific work; it remains
preserved with zero scientific exposure, alongside P50 staging failures.
Neither is a trained third pair or a scientific negative. No current
primary-integrity gap, partial scientific row, scientific cap breach or
missing required publication remains. Engineering scope §4: **none**.

DM used the scientific-tools run summarizer once on four final T/G scores
with explicitly declared paired masters; H was kept as a nonlearned reference.
The task-local [analysis script](C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906/temp/directions/ucope/exp/uav-motion-prefix-b02-p47-20260908-dm-intake/analyze_existing.py)
adds arithmetic over stored episode/diagnostic records. The generic table's
subtract-means order differs in the last floating-point bit from the card's
mean-of-differences order; the frozen primary and label above use the latter.
No scientific invocation, source edit, dependency change or new check suite
was added for this intake. Scientific decisions and predictions are in the
[DM intake](UCOPE_UAV_MOTION_PREFIX_B02_P47_INTAKE_20260908.md).
