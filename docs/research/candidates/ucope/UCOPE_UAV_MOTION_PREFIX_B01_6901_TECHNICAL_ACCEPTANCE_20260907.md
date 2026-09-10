# UCOPE P24 master6901 — technical acceptance

**PASS. The already allocated6902 route is released irrespective of score.** The [P24 handoff](UCOPE_UAV_MOTION_PREFIX_B01_P24_ROOT_HANDOFF_20260907.md) and card§10 remain unchanged; CM does not launch, retry or alter the comparison. All scientific work observed here belongs to Root's accepted6901 invocation. Collection added zero UAV/optimizer calls and no trajectory replay.

## Exact identity and terminal conformance

Accepted handle `ucope-uav-motion-prefix-b01-6901-p24-20260907`, node `hmasd-wsl-node`, detached cwd `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p24-20260907`, full source **`9c541a8047b8c33e90f09aa65e326180343a23a0`**. Retained supervisor status is `finished`, exit0, LF-only command with `--pair p24 --seed 6901`. Root's terminal report records inactive tmux and285s supervisor duration. GNU time whole wall is **284.29s**, peak RSS **554072KiB**. Admission passed physical/effective **15,653,224,448 bytes**, both above4GiB.

Root-collected evidence is `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-6901-p24-20260907/`: admission, summary, three JSONLs, both final checkpoints, supervisor files and CM `technical_verification.json`. The [committed verification](UCOPE_UAV_MOTION_PREFIX_B01_6901_TECHNICAL_VERIFICATION_20260907.json) retains computed counts, endpoints, exposure and limits. The intended artifact path contains all files; the historical P21 CR deviation did not recur.

Offline checks over those actual records establish:

- Summary `UAV_B_EXPLORE/COMPLETE`, seed6901, pair`p24`, declared masters`[6901,6902]`, card section10 and correct source/card path. Config is actual seed6901/horizon256/train512/eval32/chunk32/1800s arm/3600s pair; recorded RNG domains are `100000*6901` plus the prescribed offsets. Checkpoint configurations match.
- **1120 complete episode rows**, in exact T512train/32eval → G512train/32eval → H32eval order, prescribed reset seeds and256 steps each. Counts **286720 team/UAV steps**,1024 train+96eval episodes,two constructors/resets and zero partial episode work reconcile with rows.
- **512 rollout rows**,512 steps/two episodes/four finite epoch records each, sum to **2048 actual Adam calls**,1024 per fit. True velocity/duration/d4 counts reconcile with episode and summary records, including T's omitted held samples; G retains every primitive decision and H has no learner.
- Both final checkpoints contain finite FP32 tensors, correct parameter counts/final norms and nonzero reported displacement. All recorded reward/J and prefix+suffix arithmetic reconciles. Final sampled arrays match episode rows; paired means/differences and conditional evaluation SEs were independently recomputed.
- **1600 diagnostic frames** cover every T/G evaluation agent at t0..4. Last-action inputs, remaining holds, actual-decision masks, d4 command reuse, next-observation clock, source-index bounds and prefix reward sums reconcile. No missing hover/diagnostic dependency is reported.
- Runner wall275.786177s; T140.337403s and G135.448773s including H/publication, both below1800s. Whole invocation below3600s; no cap breach. Aggregate CPU remains unmeasured.

Prior accepted source/review/focused checks support unlogged learner likelihood/gradient internals; raw episode data do not recreate the entire trajectory. No additional smoke or runtime probe was used.

## Preserved observations and next route

Final native means: T **0.1529236927748035**, G **0.10957182628264031**, H **0.13777564272499856**. T−G **0.043351866492163174**, conditional SE **0.010106687010538311**; G−H **−0.02820381644235824**, conditional SE **0.01391658522356752**. T sampled d4 frequency **0.49375**. Negative generic-minus-hover is retained and limits any competent-generic interpretation; it is not an engineering failure or an extra condition on6902. This is only the first P24 pair, not the new two-pair joint result. DM owns scientific interpretation.

Root now uses the **unchanged exact second-launch6902 PowerShell literal** in [P24 handoff](UCOPE_UAV_MOTION_PREFIX_B01_P24_ROOT_HANDOFF_20260907.md#second-launch-6902-after-first-technical-acceptance), with the same full source/cwd, fresh actual-node admission, prospective handle `ucope-uav-motion-prefix-b01-6902-p24-20260907`, relative output `temp/directions/ucope/exp/uav-motion-prefix-b01-6902-p24-20260907`, `--pair p24 --seed 6902`, original1800/3600/7200s caps and CR-stripping remote stdin transport. Root observes and returns that handle to this same CM for terminal technical acceptance. No retry, third pair, cap increase, fallback or promotion follows. Scope§4 additions: **none**.
