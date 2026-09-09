# UCOPE B03 7101 — terminal technical acceptance

**Accepted: the single P57 invocation completed at source `70900ac7e7aa3a85b4f4ad6a2a8031ccb346fd44`, with no observed integrity or cap failure.** [Machine-readable collection evidence](UCOPE_UAV_MOTION_PREFIX_B03_7101_COLLECTION_20260908.json) preserves the complete summary, all 32 T/G/H outcomes, paired differences, admission and receipt hashes. DM owns scientific intake under the [frozen card §§4–6](UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md); Root owns integration.

## Accepted handle and collected bytes

Handle `ucope-uav-motion-prefix-b03-7101-p57-20260908` ran on `hmasd-wsl-node` in `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b03-p57-check-20260908`. The collected supervisor runner matches the [bound invocation](UCOPE_UAV_MOTION_PREFIX_B03_P57_ROOT_HANDOFF_20260908.md). Root reported terminal exit 0 and inactive tmux; CM read back the same finished status, exit 0 and terminal log. Current remote HEAD remains the accepted source and its experiments/scripts diff is clean.

All seven output files and the supervisor directory were copied using SCP to `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b03-7101-p57-20260908/`. SHA-256 for all seven output files matches the independently read remote digests. Raw episodes, rollouts, diagnostics and both final checkpoints remain there and on the remote. H is an untrained zero-velocity reference and has no checkpoint. The JSON includes hashes of collected supervisor receipts. Readback script: `verify_collection.py` in that local output directory; it loads stored tensors and JSON only, without a learner or evaluator invocation.

## Technical checks

- Identity is real `UAV_B_EXPLORE`, COMPLETE, B03/7101, card section 5, agent-compound clipping and common entropy coefficient 0. Configuration and both saved checkpoints agree; historical objects were not pooled.
- All 1120 episode rows are complete at 256 steps. T and G each have 512 training episodes with the declared reset seeds and 256 rollout rows of four optimizer steps: 131072 training team steps and 1024 Adam calls per fit, lr 0.0003. Both fits show nonzero recorded parameter displacement.
- All 32 final episode IDs and reset seeds match across T/G/H. Every stored episode J equals its complete reward sum divided by 256, and the 96 final values match the published arrays exactly. This checks recorded native-return publication; it does not independently resimulate rewards.
- Both checkpoint actor/critic state dictionaries contain finite FP32 tensors. There are 1600 diagnostic rows. Counts reconcile to 262144 training plus 24576 evaluation team steps, 286720 scientific UAV calls, 2048 Adam calls and 96 final episodes, with zero partial episode steps.
- Fresh admission records physical and effective available memory of 15645777920 bytes, both above 4 GiB. Complete invocation wall is 283.51s including publication/exit; peak RSS is 554276 KiB. Internal arm charges are T 143.6449222s and G 139.3128413s; pair internal wall is 282.9577648s. These are below 1800s per arm and 3600s per pair. Even the entire external invocation is below either arm cap. No limits or cap breach were emitted. Aggregate CPU was not measured; RSS does not establish system-wide memory usage.

## Preserved endpoint facts and boundary

| Paired native contrast | Mean | Conditional episode SE |
| --- | ---: | ---: |
| T−G | −0.010093085146628955 | 0.008506138301283968 |
| G−H | 0.04756796231762334 | 0.011545966671454506 |
| T−H | 0.03747487717099439 | 0.010037043349360902 |

Readback independently recomputed these statistics from all 32 published values and matched the emitted T−G/G−H statistics. The unrounded primary is below −0.01; DM applies the card rule and predictions without rounding it into the band. Independent training n=1; no training-population uncertainty estimate or multi-pair aggregate is supplied. No entropy-causal, deployment, transfer, stable-performance or family disposition follows from technical acceptance.

Collection added zero model, simulator, learner or evaluator invocations. No relaunch, second pair, extra evaluation or diagnostic run occurred. Existing B02 adverse evidence and historical smoke/cwd deviations are preserved. P57 proceeds to DM all-outcome intake and then its supplied replacement route; no further scientific allocation is implied. Engineering scope §4: none.
