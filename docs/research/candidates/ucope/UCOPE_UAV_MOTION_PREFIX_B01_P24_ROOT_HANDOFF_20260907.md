# UCOPE P24 fresh pairs — corrected P26 source and Root handoff

## Accepted change and exact bindings

[P26](../../portfolio/handoffs/2026-09-07-p26-ucope-fresh-pair-plumbing.md) authorizes only the CLI/declared-pair aggregation correction to the [P24 amendment §§2,5](UCOPE_UAV_MOTION_PREFIX_B01_P24_AMENDMENT_INTAKE_20260907.md). [Card §10](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#10-prospective-p24-fresh-pair-continuation-and-p26-plumbing--2026-09-07), committed in **`8cb59913be5015c3948e4a1c24024147023fdf97`**, fixes **6901 then6902**, exactly two new T→G→H invocations. No fourth comparison or scientific call occurred during this correction/readiness.

**Corrected execution source: `9c541a8047b8c33e90f09aa65e326180343a23a0`.** The source commit includes the amended card. This handoff's documentation-only descendant does not alter that binding. Authoring remains `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, `codex/ucope`. The only source changes from the accepted baseline are `scripts/run_ucope_uav_motion_prefix_b01.py` and `experiments/candidates/ucope/uav_motion_prefix_b01/study.py`; affected fixtures are in `tests/experiments/candidates/ucope/uav_motion_prefix_b01/test_pair_plumbing.py`.

`--pair p24` admits6901/6902 and passes the actual integer into Config and the existing `b=100000*seed` initialization/velocity/duration/reset/evaluation domains. Default `--pair p21` preserves6801/6802 and fixture9001. New summaries label `pair`, `declared_masters` and `card_section`; P24 binds section10, P21 section8, engineering fixtures their own CODE_SPEC section. Historical P21 summaries without new labels remain usable. `--aggregate --pair p24` accepts exactly the two declared new masters with matching real pair/card labels and rejects duplicates, wrong masters/declarations/card sections and synthetic-mixed inputs. It retains exactly-two mean, sample SD, conditional `sqrt(SE1²+SE2²)/2`, MEI and all signs. No four-unit runner or registry was added.

Focused acceptance command (no old learner-fixture replay):

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q tests/experiments/candidates/ucope/uav_motion_prefix_b01/test_pair_plumbing.py
git diff --check
```

Result: **20 passed in0.50s**, whitespace checks pass. Module-boundary stand-ins exercise actual CLI/Config/study stream expressions and reset/evaluation dispatch for6901,6902,6801,6802,9001 without importing Torch, policy, learner or UAV modules. Arithmetic fixtures check valid historical/new pairs, exact formulas, CLI aggregation propagation and rejection cases. Initial five failures were missing `state_dict` on the test stand-in; corrected only that fixture, with no production scientific change. Independent scientific-boundary review: **no material finding**, returned by the reused `/root/ucope_cm_baseline_b01/integration_review` after inspecting the complete production diff and boundary tests. The later CLI-aggregation fixture brings the final total to20; no production change followed review. Prior original12-test/80-step fixture and independent full-code review remain evidence for unchanged learner/environment paths; they were not repeated. No runtime/import probe or admission was performed.

Scope §4 additions: **none**. Source additions remain below2000 lines and runner below600. Host, model, reward, information, hold, recurrent/PPO, optimizer, episode/update counts, final sampled evaluation, dtype and caps are unchanged. New labels identify the issued allocation; they do not rename a seed without propagating it.

## Work, cost, stops and execution ownership

Configured node/interpreter remain `hmasd-wsl-node` / `/home/wu/.venvs/hmasd/bin/python`; CPU FP32 learner, environment internal precision unchanged, one scientific process/compute thread. Each master has131072 training steps and1024 Adam calls per T/G fit plus32 final sampled eval episodes per T/G/H. Per-pair totals286720 team steps,2048 Adam calls,1120 episodes,two constructor resets and1600 diagnostic frames; both new pairs total573440 steps/4096 Adam/2240 episodes/3200 frames.

Per-arm projection is reused from [card/exposure facts](UCOPE_UAV_MOTION_PREFIX_B01_P24_EXPOSURE_AND_COST_20260907.json): **T148.267067s**, including conservative external startup residual; **G141.371892s**, including H/publication; **579.277918s** summed across both prospective pairs. It is a forecast from observed P21 complete-path work, not a guaranteed bound. Complete limits remain **1800s per arm,3600s per pair,7200s new-pair sum**. Startup/common initialization belongs to T; H/pair publication belongs to G. External timeout includes admission overhead conservatively and never resets for a phase. Aggregate CPU/scratch remain unmeasured; summed invocation wall is distinct from study critical path including technical intake intervals.

Post-learner coverage reuses P21's actual completed publication, independent original tests/review and prior terminal collections. The correction touches seed selection/labels/aggregation; its focused fixtures cover those changed dispatch and publication fields. No new numerical learner acceptance claim is inferred from the plumbing fixtures.

Root stages the committed exact source, performs each fresh physical/effective>=4GiB admission joined immediately to its runner with`&&`, launches once via the existing supervisor and observes the accepted handle. CM performs no launch.6902 follows CM technical acceptance of6901 **irrespective of score**. Cap/nonfinite/reward-information-training-primary integrity failure stops its dependent route. No retry, resumed learning, fallback, extra seed/evaluation, pilot, cap reset, third pair or promotion is allocated. Missing hover/diagnostics follows its own dependency without erasing independently complete native primary.

## Exact remote staging and fresh names

Prospective cwd: **`/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p24-20260907`**. Names below are prospective, not accepted handles or asserted absent paths. Root checks actual state before staging/launch; uncertain acceptance is reconciled using the same handle, never by resending blindly.

Root sends this block as LF-normalized remote Bash input. If staging fails, stop before any scientific launch:

```bash
set -e
git -C /home/wu/projects/HMASD fetch origin codex/ucope
git -C /home/wu/projects/HMASD worktree add --detach /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p24-20260907 9c541a8047b8c33e90f09aa65e326180343a23a0
git -C /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p24-20260907 rev-parse HEAD
```

| Master | Supervisor name | Output relative to cwd |
| --- | --- | --- |
| 6901 | `ucope-uav-motion-prefix-b01-6901-p24-20260907` | `temp/directions/ucope/exp/uav-motion-prefix-b01-6901-p24-20260907` |
| 6902 | `ucope-uav-motion-prefix-b01-6902-p24-20260907` | `temp/directions/ucope/exp/uav-motion-prefix-b01-6902-p24-20260907` |

Each output contains its own `resource_admission.json`, `summary.json`, `episodes.jsonl`, `rollouts.jsonl`, `diagnostics.jsonl`, `final_T.pt`, `final_G.pt`. Supervisor logs/status/exit identity are `/home/wu/.agent-tasks/<name>/{task.log,status,pid,start_time,exit_code,runner.sh}`. GNU time's whole wall/peak RSS line is retained in task.log.

## First launch —6901 only

P21's historical6801 scientific output directory acquired a literal trailingCR from Windows pipe transport. Those artifacts and their complete local collection remain unchanged. Strip CR on the remote input stream for all blocks; changing the local string alone does not remove CRLF appended by PowerShell's pipeline. The original harmless LF transport check is reused; no new probe is needed.

```powershell
@'
/usr/local/bin/agent-task run ucope-uav-motion-prefix-b01-6901-p24-20260907 "/usr/bin/time -f whole_wall_seconds=%e,peak_rss_kib=%M /usr/bin/timeout --signal=KILL 3600s /bin/bash --noprofile --norc -c 'cd /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p24-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/uav-motion-prefix-b01-6901-p24-20260907/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_motion_prefix_b01.py --pair p24 --seed 6901 --out temp/directions/ucope/exp/uav-motion-prefix-b01-6901-p24-20260907'"
'@ | ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "tr -d '\015' | /bin/bash -s"
```

## Second launch —6902 after first technical acceptance

```powershell
@'
/usr/local/bin/agent-task run ucope-uav-motion-prefix-b01-6902-p24-20260907 "/usr/bin/time -f whole_wall_seconds=%e,peak_rss_kib=%M /usr/bin/timeout --signal=KILL 3600s /bin/bash --noprofile --norc -c 'cd /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p24-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/uav-motion-prefix-b01-6902-p24-20260907/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_motion_prefix_b01.py --pair p24 --seed 6902 --out temp/directions/ucope/exp/uav-motion-prefix-b01-6902-p24-20260907'"
'@ | ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "tr -d '\015' | /bin/bash -s"
```

Do not concatenate both launch blocks into an unattended two-command sweep; the technical return between them is part of the issued route.

## Observation, collection and two-summary publication

Root follows `EXPERIMENT_MONITOR.md` and `ROOT_OPERATIONS.md`: record actual `(node,accepted handle)` and itself as observer in the existing tracking row; poll only accepted handles via `agent-task status <name>` and, when useful, `logs <name> 40`. Preserve supervisor exit evidence; SSH failure/PID absence alone is unknown. Use the existing goal-driven observation interval, no scheduler/heartbeat/retry layer.3600s is the complete bound.

On each terminal result, collect the output and supervisor files into `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-<master>-p24-20260907/`. Return handle/status/receipt/source/cwd/artifact/timing facts to **`/root/ucope_cm_baseline_b01`**, which retains per-pair collection and technical acceptance. Check mode`UAV_B_EXPLORE`, actual seed6901/6902, pair`p24`, declared masters`[6901,6902]`, card section10, exact launch SHA, complete counts, finite checkpoints/exposure, native arithmetic and original stops. Exit0 alone does not establish scientific validity. **`/root/dm_ucope_p13_intake`** owns scientific intake and the subsequent four-unit descriptive analysis.

After both technical returns, ordinary local read-only aggregation uses only the two new collected summaries; it does not instantiate policy/environment or load checkpoints:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_ucope_uav_motion_prefix_b01.py --pair p24 --aggregate C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-6901-p24-20260907/summary.json C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-6902-p24-20260907/summary.json --out C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-p24-20260907-joint
```

Run from the corrected authoring checkout or a collected exact-source checkout. This output is the new two-pair primary, distinct from P21. Preserve both individual signs/SEs, raw T/G/H and any damaged dependency. Missing summaries are not fabricated or recovered by another scientific invocation. DM may describe all four independent units with the outcome-informed continuation label; the runner has no n4 primary or stable-superiority rule. No new command follows beyond the two allocated pairs and their intake.
