# UCOPE UAV motion-prefix B01 — P21 Root execution handoff

## Binding and readiness

P21's [UCOPE allocation](../../portfolio/handoffs/2026-09-07-p21-fsd-ucope-frrie-continuations.md#ucope--accepted-uav-b-implementation-through-two-fixed-pairs) and [card §8](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#8-current-p21-execution-allocation--2026-09-07) release exactly masters **6801 then 6802**. Card §§2–6 and the [CODE_SPEC §§2–8](UCOPE_UAV_MOTION_PREFIX_B01_CODE_SPEC_20260907.md) frozen at `f718134f210889ff14f07deb3846cde853abd7b4` retain their meaning. This handoff prepares commands; CM performed **zero UAV construction/reset/step calls, zero scientific invocations and zero resource admissions** during this readiness continuation.

Execute full source SHA **`536949660fee3ab9ac92aba29c2c0455ffe9f6e1`**. It includes the P21 card release and has no differences from accepted implementation `78dd2a461e838b9d863b81ed9e2d5946d011f33a` on the seven owned source/test paths. The authoring checkout is `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch `codex/ucope`; readiness began clean at that SHA. This document's later commit is documentation only and does not replace the exact execution binding.

Reused acceptance evidence, without another launch-boundary smoke:

- All seven transferred files were byte-identical to the accepted batch03 baseline. Integration's original focused pytest returned **12 passed in 4.40 s**. The original synthetic CLI completed in 4.242 s command wall; its summary reports 3.562 s inside the entry script.
- The original readback passed: **32 training + 48 evaluation = 80 synthetic team steps, eight actual Adam calls, ten episode rows, 100 diagnostic frames, zero UAV calls**. Both total parameter displacements were nonzero. Retained local output: `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906/temp/directions/ucope/test/uav_motion_prefix_b01_fixture/` (`summary.json`, `episodes.jsonl`, `rollouts.jsonl`, `diagnostics.jsonl`, `final_T.pt`, `final_G.pt`). These are engineering-fixture artifacts, never scientific endpoints.
- Independent reviewer `/root/ucope_cm_baseline_b01/integration_review` inspected all seven files, CODE_SPEC §§2–8/card §§2–5 and real base/adapter consumers. Its completed return found **no material finding** in information boundaries, holds, native reward, recurrent MC-PPO, RNG, serial execution or dependency-specific incomplete results. Review made no UAV calls and did not repeat the tests. Integration whitespace checks passed; `78dd2a461...` was pushed with a clean checkout.
- Current read-only inspection confirms the CLI selects real mode for `--seed 6801` or `--seed 6802`, the factory is lazy, and real config is horizon256/train512 episodes/eval32/chunk32/arm1800/pair3600. No source correction was needed. `.codex/hmasd-compute.toml`, `EXPERIMENT_MONITOR.md` and `ROOT_OPERATIONS.md` remain the execution/observation route.

**Per-arm cost projection:** T: common startup/initialization + 131072 environment/actor training steps + 1024 full-rollout Adam calls + 8192 sampled evaluation steps + publication; G: 131072 training steps + 1024 Adam calls + 8192 sampled evaluation steps + 8192 hover steps + initialization/publication. Real UAV coefficients remain **unmeasured**; no numeric forecast, measured cap feasibility, synthetic-to-UAV timing extrapolation or extra pilot is claimed. Complete stop caps remain 1800 s/arm and 3600 s/pair, 7200 s summed across pairs. Study critical path includes the ordered pair invocations and intervening technical intake; summed invocation wall is recorded separately. Aggregate CPU is unmeasured and is not substituted for wall.

**Post-learner coverage:** the existing exact fixture exercised actual learner updates, final weight publication, episode/rollout/diagnostic publication and summary readback. Focused tests covered missing hover/diagnostic dependencies, final-fit preservation before failed evaluation, and startup/checkpoint/H/pair-publication deadline charging. This establishes the tested engineering path, not actual UAV runtime or scientific validity.

## Remote source and fresh identities

Node: **`hmasd-wsl-node`**, configured Ubuntu/WSL host `LAPTOP-U9TDKC8A`. Interpreter: `/home/wu/.venvs/hmasd/bin/python`. CPU FP32 learner, one process/compute thread; environment internal precision unchanged. Runner sets OMP/MKL/OPENBLAS/NUMEXPR and Torch intra/inter-op threads to one before numerical work. No accelerator, dependency installation or local fallback is selected.

Both pairs use cwd **`/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907`**, detached at the full SHA above. Read-only remote inspection found that cwd and both proposed supervisor directories absent, and confirmed `/usr/bin/time`, `/usr/bin/timeout`, `/bin/bash` and the installed `agent-task run <name> <cmd...>` interface. These names are prospective, **not accepted handles**. Root must reconcile any uncertain previous dispatch against the same name before sending anything again; `agent-task` permits reuse of a finished name and must not be used to overwrite an attempt.

The optional remote `git cat-file -t` presence read did not finish and was cancelled; this preparation does not assert that the launch commit is already materialized remotely. Root's fetch/exact-SHA worktree staging below resolves that fact before launch. All five Bash blocks passed `/bin/bash -n` on the configured node without execution. Per-pair counts below were recomputed by stdlib arithmetic, without importing a learner or environment.

Root runs this source-staging block on the configured node, before the scientific command. It creates no scientific process or authoring branch:

```bash
set -e
git -C /home/wu/projects/HMASD fetch origin codex/ucope
git -C /home/wu/projects/HMASD worktree add --detach /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907 536949660fee3ab9ac92aba29c2c0455ffe9f6e1
git -C /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907 rev-parse HEAD
```

Run these literal blocks in remote Bash, e.g. send their exact text as stdin to `ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /bin/bash -s`. Do not concatenate the two launch blocks: pair6802 requires the first CM technical return. If staging fails, stop before launch and resolve that exact engineering fact; no alternate SHA or checkout follows.

| Master | Prospective supervisor name | Output relative to cwd | Admission relative to cwd |
| --- | --- | --- | --- |
| 6801 | `ucope-uav-motion-prefix-b01-6801-p21-20260907` | `temp/directions/ucope/exp/uav-motion-prefix-b01-6801-p21-20260907` | `temp/directions/ucope/exp/uav-motion-prefix-b01-6801-p21-20260907/resource_admission.json` |
| 6802 | `ucope-uav-motion-prefix-b01-6802-p21-20260907` | `temp/directions/ucope/exp/uav-motion-prefix-b01-6802-p21-20260907` | `temp/directions/ucope/exp/uav-motion-prefix-b01-6802-p21-20260907/resource_admission.json` |

The worktree was absent, so these nested scientific output paths were absent too. Each actual-node admission writes its ordinary receipt; physical and effective available memory must both be at least 4 GiB. Failed admission prevents its runner via `&&`. The external timeout covers admission, interpreter startup, T/G/H and publication under one 3600 s bound, conservatively including admission overhead. GNU time writes whole wall and peak RSS to the existing supervisor log; no new telemetry service or launcher is added. An indivisible call killed at the bound may leave only partial files. No grace period or extra computation after the cap is allocated.

## Pair6801 — Root launches once

```bash
/usr/local/bin/agent-task run ucope-uav-motion-prefix-b01-6801-p21-20260907 "/usr/bin/time -f whole_wall_seconds=%e,peak_rss_kib=%M /usr/bin/timeout --signal=KILL 3600s /bin/bash --noprofile --norc -c 'cd /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/uav-motion-prefix-b01-6801-p21-20260907/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_motion_prefix_b01.py --seed 6801 --out temp/directions/ucope/exp/uav-motion-prefix-b01-6801-p21-20260907'"
```

## Pair6802 — only after CM technical acceptance of pair6801

Continue irrespective of 6801's score, MEI branch, T−G sign or G−H competence observation. A cap, nonfinite learner or reward/information/training/primary-integrity failure stops the dependent route for a concrete return; no automatic retry or replacement is allocated.

```bash
/usr/local/bin/agent-task run ucope-uav-motion-prefix-b01-6802-p21-20260907 "/usr/bin/time -f whole_wall_seconds=%e,peak_rss_kib=%M /usr/bin/timeout --signal=KILL 3600s /bin/bash --noprofile --norc -c 'cd /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/uav-motion-prefix-b01-6802-p21-20260907/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_motion_prefix_b01.py --seed 6802 --out temp/directions/ucope/exp/uav-motion-prefix-b01-6802-p21-20260907'"
```

## Observation, collection and return

After actual `agent-task` acceptance, Root records the exact `(node, name)`, source/cwd/outputs and itself as observer in the existing experiment tracking row. Supervisor files for each name are `/home/wu/.agent-tasks/<name>/task.log`, `status`, `pid`, `start_time`, `exit_code` and `runner.sh`; no PID is asserted before acceptance. The wrapper's `exit_code`/terminal status is authoritative. SSH failure or absent PID alone does not authorize another launch.

```bash
/usr/local/bin/agent-task status ucope-uav-motion-prefix-b01-6801-p21-20260907
/usr/local/bin/agent-task logs ucope-uav-motion-prefix-b01-6801-p21-20260907 40
/usr/local/bin/agent-task status ucope-uav-motion-prefix-b01-6802-p21-20260907
/usr/local/bin/agent-task logs ucope-uav-motion-prefix-b01-6802-p21-20260907 40
```

Observe only each actually accepted handle. Use the normal at-most-60-second goal-driven observation interval and terminal notification; 3600 s is a stop bound, not a new reminder service. After each terminal return, preserve/copy that output directory and its supervisor files into `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-<master>-p21-20260907/` for collection. Do not copy live trees merely to monitor.

Notify **`/root/ucope_cm_baseline_b01`** with the accepted handle, terminal status/exit, receipt, summary/JSONL/checkpoint paths and whole-wall evidence. CM checks actual completion/exposure and native-primary integrity; **`/root/dm_ucope_p13_intake`** owns scientific intake. Expected complete per-pair counts are 262144 training team steps, 24576 evaluation team steps, **286720 total UAV step calls**, **2048 Adam calls**, 1024 training episodes plus 96 evaluation episodes, two constructor resets and 1600 diagnostic frames. Per-fit training is 131072 steps/1024 Adam calls; T/G final evaluation is sampled at final weights, H has no learner. A successful process exit does not establish those facts by itself.

Retain `summary.json`, `episodes.jsonl`, `rollouts.jsonl`, `diagnostics.jsonl`, `final_T.pt`, `final_G.pt`, admission and supervisor evidence. Missing H or diagnostic information limits its own dependent interpretation without erasing independently complete T/G returns. Missing T/G primary is not zero. Preserve negative/opposite-sign outcomes and actual partial exposure. Actual UAV entry requires accepted launch plus observed real UAV execution, linked to card §8 and direction decision `426513b18b38b477dd255b3e8524424d8deb8a19`; this prepared handoff does not establish entry.

After both technical returns, arithmetic-only aggregation uses the existing CLI and does not import the UAV factory or load weights:

```bash
set -e
cd /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907
/home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_motion_prefix_b01.py --aggregate temp/directions/ucope/exp/uav-motion-prefix-b01-6801-p21-20260907/summary.json temp/directions/ucope/exp/uav-motion-prefix-b01-6802-p21-20260907/summary.json --out temp/directions/ucope/exp/uav-motion-prefix-b01-p21-20260907-joint
```

This read-only analysis of completed outcomes adds no training/evaluation call. Report two independent pair endpoints, their sample SD, conditional episode SEs and the specified joint conditional SE; no primitive-step pooling or historical-result pooling. If either pair lacks a summary, preserve the available narrower facts for CM/DM rather than fabricating input or launching recovery. No successor, promotion, retry, cap increase, fallback or extra seed follows from this handoff. Engineering scope §4 additions: **none**.
