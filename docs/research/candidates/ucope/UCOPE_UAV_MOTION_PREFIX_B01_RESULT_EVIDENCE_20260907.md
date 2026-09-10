# UCOPE UAV motion prefix B01 — complete two-pair result evidence

**COMPLETE / joint UP, B/EXPLORE.** The two prospectively selected training-pair
masters 6801 and 6802 complete the original allocation. Mean T−G native return is
**0.015217420622321492**, above the card's absolute 0.01 MEI. This records the
complete fitted-package comparison; its scientific limits and decisions are in
[the joint intake](UCOPE_UAV_MOTION_PREFIX_B01_INTAKE_20260907.md).

## 1. Bound object, source and reading rule

Object: `UCOPE-UAV-MOTION-PREFIX-B01`. The [card §§2–6](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#2-host-information-and-mechanism)
and CODE_SPEC were fixed at `f718134f210889ff14f07deb3846cde853abd7b4`; [card §8](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#8-current-p21-execution-allocation--2026-09-07)
records P21's actual two-pair allocation. Both invocations used exact committed
source **`536949660fee3ab9ac92aba29c2c0455ffe9f6e1`**, on `hmasd-wsl-node`,
CPU FP32 learner, one process and one compute thread, with the unchanged base
`MultiUAVEnv` and existing adapter. The five-UAV/50-user/256-step setting, native
reward, local actor information, centralized critic permissions and final sampled
evaluation remain those on the card. P15's earlier zero-invocation statements are
historical preparation facts.

T learns one opening velocity commitment of duration one or four per agent;
G chooses a legal velocity at every primitive step, with the same free local
information and recurrent memory. H is fixed zero velocity on matched reset
seeds, without learning or tuning. Each T/G fit trains for 131,072 team steps and
1,024 actual joint actor/critic Adam calls; evaluation uses only its final
checkpoint and all 32 sampled episodes. Common initial parameters and reset
seeds pair T/G within a master; their on-policy trajectories remain separate.

The primary is `J=sum_t sum(info['rewards_dict'].values())/256`. It uses the
complete unmodified native team reward, not the adapter's additional agent
average. The original card rule is reproduced verbatim:

| Joint point reading | Rule and bounded interpretation |
| --- | --- |
| `UP` | Delta > .01: preliminary advantage of these fitted control packages under this task and budget. Competent-generic or information-path wording additionally depends on its actual corresponding evidence. |
| `WITHIN` | -.01 <= Delta <= .01: no gain at the selected scale under this budget; not stable equivalence. |
| `DOWN` | Delta < -.01: adverse native evidence for this task/prefix/learner budget. More observations or changed actions do not compensate for it. |
| Partial | Missing T/G primary data do not become zero. Preserve completed facts and identify the damaged dependent claim. |

## 2. All final outcomes and uncertainty

| Quantity | 6801 | 6802 |
| --- | ---: | ---: |
| T mean native J | 0.19815651099380138 | 0.17927686870918463 |
| G mean native J | 0.1914424787546125 | 0.15555605970373051 |
| H mean native J | 0.1490047481461882 | 0.14625468074141884 |
| T−G mean | 0.006714032239188856 | 0.023720809005454126 |
| T−G conditional episode SE | 0.011125795446968265 | 0.010131530857286448 |
| G−H mean | 0.04243773060842434 | 0.009301378962311667 |
| G−H conditional episode SE | 0.012071690736933637 | 0.008782791170015744 |
| T−G positive / negative episodes | 17 / 15 | 21 / 11 |
| G−H positive / negative episodes | 25 / 7 | 20 / 12 |
| Final T d4 choices / duration choices | 83 / 160 | 78 / 160 |

Joint T−G is **0.015217420622321492**; its margin over MEI is
0.005217420622321492. The sample SD of the two training-pair endpoints is
**0.012025607177551996**. Joint conditional evaluation SE is
**0.007523816216520829**, computed as `sqrt(SE_6801^2+SE_6802^2)/2`.
The independent training unit is the prospectively matched pair, **n=2**.
Endpoint sample SD includes evaluation noise; conditional SE conditions on the
fitted policies and does not measure training-population uncertainty. No
population confidence interval, stable-superiority or all-seeds-positive rule is
inferred. The first pair lies within MEI and the second above it; only the fixed
joint point rule supplies the object's `UP` reading.

Joint G−H is 0.025869554785368003 (endpoint sample SD 0.02343093895274829;
conditional SE 0.0074643006702616805). H is a competence reference, not a tuned
baseline or an upper bound. All 192 final evaluation rows, including the adverse
differences, remain in the raw artifacts and the [committed joint aggregate](UCOPE_UAV_MOTION_PREFIX_B01_JOINT_AGGREGATE_20260907.json).
No old finite-host result or training checkpoint is pooled into these figures.

## 3. Actual exposure and complete resource receipts

Each pair has **262,144 training + 24,576 evaluation = 286,720 actual UAV team
steps**, 2,048 Adam calls, 1,024 training + 96 evaluation episodes, two
constructors/internal resets, and 1,600 t0..4 agent diagnostic frames. Across
both pairs this is **573,440 steps, 4,096 updates, 2,240 complete episodes,
four constructor resets and 3,200 diagnostic frames**. There are no partial
episode steps, missing primary/hover rows, diagnostic limits or reported cap
breaches. Added H evaluation accounts for 64 episodes / 16,384 steps; selected
T/G diagnostics account for 6,400 source-index method calls. There is no
candidate search, checkpoint selection, extra fit or rerun.

| Fit | Trainable parameters | Initial total norm | Final total norm | Absolute displacement | Relative displacement | Actual Adam calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 6801 T | 66,441 | 15.4516182 | 17.7714653 | 8.5708237 | 0.5546878 | 1,024 |
| 6801 G | 66,311 | 15.4516191 | 17.8013287 | 8.5625162 | 0.5541501 | 1,024 |
| 6802 T | 66,441 | 15.4393997 | 18.1520615 | 9.2382870 | 0.5983579 | 1,024 |
| 6802 G | 66,311 | 15.4394007 | 17.4954815 | 8.0029421 | 0.5183454 | 1,024 |

The [machine analysis](UCOPE_UAV_MOTION_PREFIX_B01_SCIENTIFIC_ANALYSIS_20260907.json)
retains exact component and total exposure. The common actor moves in all four
fits, not just the critic. T's initially zero duration heads move by 0.1919294
and 0.2033545 in absolute norm. Their raw epsilon-denominator relative values
are retained but have no meaningful initialization-relative scale at zero.
T train velocity decisions are 651,340 / 651,838; train duration decisions
are 2,560 each. G has 655,360 training velocity decisions per fit. Holding
suppresses actual action samples while observations, reward and critic exposure
continue; equality of environment steps is not equality of action-sample counts.

| Receipt | 6801 | 6802 |
| --- | ---: | ---: |
| Supervisor PID, terminal state / exit | 2758585, finished / 0 | 2760832, finished / 0 |
| Supervisor start, UTC | 2026-09-08 04:15:06 | 2026-09-08 04:24:11 |
| Supervisor finish, UTC | 2026-09-08 04:19:55 | 2026-09-08 04:28:57 |
| Admission physical/effective available bytes | 15,651,278,848 | 15,654,449,152 |
| External whole invocation wall, seconds | 288.88 | 286.36 |
| T measured arm wall, seconds | 142.355041 | 141.488827 |
| G measured arm wall, including H/publication, seconds | 141.371892 | 138.092932 |
| Peak RSS, KiB | 553,808 | 557,216 |

Both fresh `/proc/meminfo` receipts pass the 4 GiB physical/effective floor and
occur immediately before their runner in the detached command. Original caps
remain 1,800 s per arm, 3,600 s per pair and 7,200 s summed. External whole wall
is **575.24 s per this valid two-pair B result**, including initialization,
training, final evaluation and publication. The recorded first-start to
second-finish supervisor interval is **831 s**, including the ordered
between-pair technical collection gap. It excludes later local intake and is
not interchangeable with summed machine wall or a complete end-to-end study
duration. Aggregate CPU and scratch usage were not measured:
**`resources_unmeasured`**; no dependent resource-efficiency claim is made.

## 4. Evidence paths, acceptance and deviation

The exact remote cwd was
`/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907`.
Supervisor handles were `ucope-uav-motion-prefix-b01-6801-p21-20260907` and
`ucope-uav-motion-prefix-b01-6802-p21-20260907`. Local collected roots are
`C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-<master>-p21-20260907/`.
Each contains `resource_admission.json`, `summary.json`, `episodes.jsonl`,
`rollouts.jsonl`, `diagnostics.jsonl`, `final_T.pt`, `final_G.pt`,
`technical_verification.json`, and `supervisor/{runner.sh,task.log,status,pid,start_time,exit_code}`.

The [6801 technical acceptance](UCOPE_UAV_MOTION_PREFIX_B01_6801_TECHNICAL_ACCEPTANCE_20260907.md)
and [6802/joint technical acceptance](UCOPE_UAV_MOTION_PREFIX_B01_6802_TECHNICAL_ACCEPTANCE_20260907.md)
are commits `a3603b3897eb5937cc993ccdd2d1d51f60c57b75` and
`6e54db4b4d44d2aa1adc8cd0fc8cf16e5bd37ffd` respectively, integrated on main
as `525ea8580` / `2c74049ae`. CM checked all episode/count/reset identities,
rollout updates, final FP32 checkpoint exposure, native reward arithmetic and
the t0..4 information/action chronology. Existing independent review and
original 12 focused tests supply bounded evidence for unlogged PPO semantics;
neither collection nor this intake repeats the learner or a trajectory.

**6801 transport deviation:** the Windows-to-Bash input left one literal
trailing CR (U+000D) on the remote scientific output directory name; admission
remained in the intended unsuffixed directory. The saved wrapper and CM's
`ls -lb` observation establish the path mismatch. CM copied all six existing
scientific artifacts from that sibling to the intended local collection root.
No remote rename, deletion, source change, new evaluation or relaunch occurred.
The 6802 wrapper was transmitted with LF normalization and used the intended
path. The original deviation remains visible; aggregation reads the complete
local copies, not an assumed unsuffixed 6801 remote summary. No reward,
information, training or primary-data dependency is damaged by this collection
correction.

Scientific analysis reads saved JSON/JSONL bytes only. `analyze.py` under
`temp/directions/ucope/exp/uav-motion-prefix-b01-intake/` generated
`analysis.json` and four `scores.csv` endpoints (one already-paired contrast per
master). The scientific-tools `summarize_runs.py` produced `run_summary.json`
without a second pairing or episode-as-run pooling. The durable analysis
includes selected movement, information, return partitions and training blocks.
Engineering scope §4 additions: **none**; no section 5 budget breach is reported.
