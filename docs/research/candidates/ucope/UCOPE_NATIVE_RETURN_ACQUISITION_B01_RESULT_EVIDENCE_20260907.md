# UCOPE native-return acquisition B01 — technical result evidence

Both selected formal invocations completed and their collected outputs are technically accepted. This record reports direct execution and measurement facts; DM owns the frozen reading rule, prediction scoring and scientific interpretation. No retry, resume, tuning, additional seed, repeated evaluation or source edit occurred.

## Assignment and source

Executed [technical intake §6](UCOPE_NATIVE_RETURN_ACQUISITION_B01_TECHNICAL_INTAKE_20260907.md#6-formal-execution-assignment--prepared-not-dispatched), integrated intake commit `98c43eca05f5d0b09cb673a5de3a894abc8985a5`, under [card §§1–5](UCOPE_NATIVE_RETURN_ACQUISITION_B01_SCIENCE_CARD_20260907.md). Root explicitly dispatched the assignment to this CM. The exact commands are retained in intake §6 and were executed without argv changes.

Accepted source and recorded launch SHA: `a0b00f561159ddeedf66b65711cf3f7d2ec93b04`. Remote cwd: `/home/wu/hmasd-worktrees/cm-ucope-native-return-b01-20260907`; execution node `wsl_4070`, SSH `hmasd-wsl-node`, interpreter `/home/wu/.venvs/hmasd/bin/python`. Before launch, Git comparison of the actor/evaluator/runner and four bound historical modules against the accepted source was empty. Both proposed handles were `not_found` before dispatch. Existing technical checks/review were reused; no new test run was required.

Runtime for both: Python 3.10.21, Torch 2.7.0+cu118 on CPU, FP32 learner, one scientific process, Torch intra-op/inter-op threads 1/1. Host Python-float evaluation moments preserve the card’s float64 accumulation. No GPU, native team or additional machinery.

## Terminal and resource facts

| Seed / handle suffix | Start (node time) | Terminal (node time) | Status | Whole-process wall s | Peak RSS KiB |
| --- | --- | --- | --- | ---: | ---: |
| 6301 | 2026-09-07T15:47:47+08:00 | 2026-09-07T15:47:56+08:00 | finished / exit 0 / COMPLETE | 8.80 | 510200 |
| 6302 | 2026-09-07T15:48:45+08:00 | 2026-09-07T15:48:55+08:00 | finished / exit 0 / COMPLETE | 9.67 | 506720 |

Handles are `ucope-native-return-b01-seed6301` and `ucope-native-return-b01-seed6302`. Seed 6301 reached terminal before monitoring adoption; CM collected its outputs and found no shared technical failure before launching seed 6302. Root adopted seed 6302 under the active shared heartbeat, then supplied its terminal notification. CM collected only terminal outputs. Neither handle is live.

Each runner followed its own fresh destination `admit-memory` via `&&`; each complete process was enclosed by `/usr/bin/timeout --signal=INT --kill-after=2s 600s`, with `/usr/bin/time -f %e,%M` outside timeout. Neither timeout fired, and neither consumed cleanup allowance. Both physical and effective availability passed the 4 GiB floor:

| Seed | Admission UTC | Physical/effective available bytes |
| --- | --- | ---: |
| 6301 | 2026-09-07T07:47:47.878406Z | 15670321152 / 15670321152 |
| 6302 | 2026-09-07T07:48:45.967189Z | 15664181248 / 15664181248 |

Summed whole-invocation wall is **18.47 s**, below the selected 1,200 s summed maximum and each 600 s cap. Rounded supervisor start-to-last-terminal study elapsed is **68 s**, including the sequential collection/dispatch gap and admissions. These differ from aggregate CPU work, which the exact formal command does not measure. Peak RSS values are invocation process maxima, not summed simultaneous memory. Git/SSH staging and artifact-copy time are not formal invocation wall. The prelaunch projection was 53.394020374 s per seed; measured whole-process costs are reported without changing that prospective record.

The runner summaries retain `resources_unmeasured` because they do not ingest external RSS. The external wall/RSS files supply the resource facts above; no result is invalidated by this label. Internal summary wall excludes interpreter startup and final refresh write; external time covers complete process exit.

## Actual exposure

| Seed | Training episodes | Training probes | Training transitions | Evaluation episodes (both policies) | Evaluation transitions | Total episodes | Total transitions | Joint steps / tail-active batches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 6301 | 262144 | 62521 | 899414 | 65536 | 131072 | 327680 | 1030486 | 1024 / 1024 |
| 6302 | 262144 | 63721 | 906614 | 65536 | 131072 | 327680 | 1037686 | 1024 / 1024 |

Formal total: **655360 episodes, 2068172 host-event transitions, 2,048 joint optimizer steps**, 126242 probes, 2638802 committed period units and 252484 probe time units. Each seed has 32,768 evaluation episodes per policy (4,096 paired indices in each of eight contexts). Neither evaluation policy probed. The separate technical seed 9006301 is excluded from all formal counts.

| Seed | Training period units | Training probe-time units | Actor eval period units | Reference eval period units |
| --- | ---: | ---: | ---: | ---: |
| 6301 | 1050378 | 125042 | 131072 | 131072 |
| 6302 | 1064136 | 127442 | 131072 | 131072 |

Machine-generated exposure from each summary:

| Seed / component | Initial L2 | Displacement L2 | Maximum absolute movement | Displacement / initial L2 |
| --- | ---: | ---: | ---: | ---: |
| 6301 / root | 0 | 4.46557664871 | 1.2914429903 | not defined: zero root initialization |
| 6301 / tail | 4.66333913803 | 3.13666534424 | 0.363628447056 | 0.6726221815303509 |
| 6302 / root | 0 | 4.32141971588 | 1.2701830864 | not defined: zero root initialization |
| 6302 / tail | 4.48822402954 | 3.95900964737 | 0.499769687653 | 0.8820882427685433 |

## Measured final endpoint

Both saved modal root vectors are `[0,0,0,0,0,0,0,0]`, where 0 denotes IMMEDIATE-4. Each context’s actor/reference paired difference, paired sample variance, probe frequency and mean paid component is zero. This is the direct final-policy observation; it does not establish a cause of learning behavior or performance beyond the frozen population.

| Seed | Actor mean return | IMMEDIATE-4 mean return | Delta_s | Conditional MC SE |
| --- | ---: | ---: | ---: | ---: |
| 6301 | 0.79122900390625 | 0.79122900390625 | 0.0 | 0.0 |
| 6302 | 0.791259521484375 | 0.791259521484375 | 0.0 | 0.0 |

Context values retain all outcomes. Actor and reference values are equal within every row; probe frequencies and paid components for both policies are 0 throughout.

| Seed | Context | Actor mean | Reference mean | Difference |
| --- | --- | ---: | ---: | ---: |
| 6301 | LINKED-p13_20-c9_100 | 0.783599609375 | 0.783599609375 | 0.0 |
| 6301 | LINKED-p13_20-c7_50 | 0.787505859375 | 0.787505859375 | 0.0 |
| 6301 | LINKED-p17_20-c9_100 | 0.7867734375 | 0.7867734375 | 0.0 |
| 6301 | LINKED-p17_20-c7_50 | 0.7984921875 | 0.7984921875 | 0.0 |
| 6301 | SEVERED-p13_20-c9_100 | 0.788970703125 | 0.788970703125 | 0.0 |
| 6301 | SEVERED-p13_20-c7_50 | 0.792876953125 | 0.792876953125 | 0.0 |
| 6301 | SEVERED-p17_20-c9_100 | 0.79995703125 | 0.79995703125 | 0.0 |
| 6301 | SEVERED-p17_20-c7_50 | 0.79165625 | 0.79165625 | 0.0 |
| 6302 | LINKED-p13_20-c9_100 | 0.7809140625 | 0.7809140625 | 0.0 |
| 6302 | LINKED-p13_20-c7_50 | 0.79800390625 | 0.79800390625 | 0.0 |
| 6302 | LINKED-p17_20-c9_100 | 0.799224609375 | 0.799224609375 | 0.0 |
| 6302 | LINKED-p17_20-c7_50 | 0.781646484375 | 0.781646484375 | 0.0 |
| 6302 | SEVERED-p13_20-c9_100 | 0.793609375 | 0.793609375 | 0.0 |
| 6302 | SEVERED-p13_20-c7_50 | 0.790923828125 | 0.790923828125 | 0.0 |
| 6302 | SEVERED-p17_20-c9_100 | 0.79409765625 | 0.79409765625 | 0.0 |
| 6302 | SEVERED-p17_20-c7_50 | 0.79165625 | 0.79165625 | 0.0 |

Per-seed `batch_branch: INCOMPLETE` is the runner’s intentional placeholder: that process cannot decide a two-seed batch. Both per-seed `status` fields are COMPLETE. DM receives both accepted summaries to apply `reading_rule`, without changing raw artifacts or treating contexts/episodes as training seeds.

## Collection and technical acceptance

For each seed the remote result root is `temp/directions/ucope/exp/native-return-b01-seed<seed>/` under the exact-source worktree. Terminal artifacts were copied to the same relative roots under `C:/Projects/HMASD-worktrees/cm-ucope-native-return-b01-20260907/`. Each contains `summary.json`, `training.jsonl`, `final_parameters.pt`, `resource_admission.json`, `process_time.csv`, plus collected `supervisor.log` and `supervisor_status.json`. Original supervisor records remain under `/home/wu/.agent-tasks/ucope-native-return-b01-seed<seed>/`.

CM readback used JSON parsing and `torch.load(..., weights_only=True)` only: each final state has 468 finite FP32 parameters; each log has the ordered updates 1–1024; final training episode counters and summed per-batch probe counts match the summary; each of eight context rows has `complete=true` and 4,096 pairs; source identity, admission, terminal exit and complete-process cap facts agree. All required primary/count/exposure fields are present. No learning or evaluation was repeated for collection.

No technical dependency remains incomplete. Scope additions and source changes in this execution assignment: none. Root integrates this evidence; DM owns scientific intake, result-rule application and next-object selection. No further invocation is authorized by this result.
