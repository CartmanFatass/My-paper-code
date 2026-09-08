# FSD native renewal A01 — P21 Root execution handoff

2026-09-07. Ready command preparation for the existing accepted baseline; no scientific
invocation, selected-checkpoint load or fresh fixture was performed in this preparation.
Comparison exclusion: continuation command preparation/collection for the existing batch-02
assignment, not a genuinely new engineering assignment. No new enrollment applies.

## Authority, source and ownership

[P21 FSD](../../portfolio/handoffs/2026-09-07-p21-fsd-ucope-frrie-continuations.md#fsd--codecard-readiness-through-the-selected-a-panel)
and [card section 7](FSD_NATIVE_RENEWAL_CONTROL_A01_SCIENCE_CARD_20260907.md#7-current-execution-allocation--p21-2026-09-07)
release only the selected G → C → H panel. Card sections 1–5 and
[CM spec sections 2–5](FSD_NATIVE_RENEWAL_CONTROL_A01_CM_SPEC_20260907.md) retain their meaning.

**Accepted full launch SHA: `01770d8dd6bb59460667efa26e3d94677e65ab37`.** It includes the
accepted baseline `4c87eecdde0f67eef7e1f9b872d10f13dca68d40` and P21 allocation. The source
comparison against that baseline is empty for the new runner/test, `config.py`, `config_1.py`,
`hmasd/`, `envs/relay_corridor/`, and the E2/E3 runners. Documentation publication after this
SHA does not change the launch binding. The designated authoring checkout is
`C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`; it was clean at entry.
No source correction is selected. Engineering scope section 4 additions: none.

Root owns exact-SHA staging, each fresh admission, each detached launch, and routine
observation. CM `/root/fsd_cm_baseline_a01` retains technical collection/acceptance;
DM `/root/dm_fsd_p13_reentry` retains scientific interpretation. This document releases the
CM's authoring ownership after its commit/push; no run is claimed accepted by these commands.

## Reused technical acceptance evidence

The independent reviewer `/root/fsd_cm_baseline_a01/fsd_integration_review` reviewed the
accepted baseline during normal integration and reported **no material findings**. Its
specific inspected conclusions remain applicable to unchanged source: active modules load
strictly; both enabled ValueNorm stores restore; C/H state and recurrence stay independent;
H substitutes only the copied pre-step public mask; service uses scoring-time labels;
float64 reward, full/post denominators, ordered pairing and ddof1 errors are correct; and
loading through closed-file publication shares the deadline. Scope and source budgets pass.
That review did not load the artifact, run science, or certify remote runtime conformance.

Original baseline check facts (same CM spec section 5 commands): 12 pytest cases passed,
exit 0, pytest 1.83 s; fixture exit 0, final complete wall 0.19599719997495413 s, no cap breach;
readback exit 0, `fixture readback OK`. Normal authoring integration ran the explicitly
requested checks: 12 passed, pytest 2.13 s (command wall 3.2705261 s); fixture exit 0,
complete wall 0.1965028999838978 s, no cap breach; readback exit 0. The sole warning was
pytest's existing cache_dir option with cacheprovider disabled. Staged and working diff
checks passed. Integration removed only trailing test-file blank lines; 342 runner and
296 test lines were committed. No checks are repeated for this documentation-only handoff.

Existing artifacts, kept at their actual paths:

- Accepted comparison fixture:
  `C:/Projects/HMASD/temp/cm-model-comparison/20260907/batch-02/worktrees/baseline/temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_engineering_fixture/summary.json`.
- Root's archived baseline return:
  `C:/Projects/HMASD/temp/cm-model-comparison/20260907/batch-02/outputs/baseline/turn-01/return/`, specifically `checks.json`, `FINAL_RESPONSE.md` and `fixture/summary.json`. The archived `checks.json` was read during this preparation and confirms the original 12-pass/exit-0/fixture/readback facts.
- Authoring integration fixture:
  `C:/Projects/HMASD-worktrees/codex-fsd/temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_engineering_fixture/summary.json`.

Fixture counts are 6 completed engineering episodes, 24 scoring steps, 144 agent
observations, 8 fake controller batches, 4 Greedy batches, zero actual HMASD constructions,
checkpoint loads, training starts/transitions or optimizer steps. These are engineering
outputs, not native results for the selected checkpoint. The reviewer return and original
command outputs are also retained in this CM's existing native conversation; the facts above
make its acceptance inspectable from the repository without another execution.

## Frozen destination and input staging

Node `wsl_4070`, SSH `hmasd-wsl-node`, host `LAPTOP-U9TDKC8A`; configured interpreter
`/home/wu/.venvs/hmasd/bin/python`, Python 3.10.21, Torch 2.7.0+cu118, NumPy 1.26.3.
CPU only, learned networks/actions FP32 and Torch four threads; host/reward accumulation
float64. G uses the existing NumPy Greedy and has no model or Torch load. No GPU/local
fallback or environment modification is selected. These are the existing declared runtime
facts, not a new import-probe result.

Detached cwd:
`/home/wu/hmasd-worktrees/fsd-native-renewal-a01-p21-01770d8dd`.
Root fetches the pushed source and creates this detached worktree at the full launch SHA;
ensure the existing source/import files are present under the configured sparse-checkout
route. Do not copy uncommitted source or change the execution revision to the doc commit.

Selected checkpoint source (read/copy bytes only during staging):
`C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d2_seed2/checkpoint_final.pt`.
Stage with the existing scp-with-declared-digest route to:
`/home/wu/hmasd-inputs/fsd-native-renewal-a01-p21/large_d2_seed2/checkpoint_final.pt`.
Exact size 64,782,527 bytes; SHA256
`2f9f6c771d757db51991bab71b53687f34057dc4ddae5132b24d42afae683b89`.
Root verifies those bytes at the destination during staging and records the concrete result;
the runner's expected identity fields are labels, not a runtime digest certification.
No unpickling, actual HMASD construction or real-checkpoint smoke is part of staging.
A mismatch is a staging conflict, not permission to substitute weights.

Under the detached cwd, the output parent is
`temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907`.
Create its G, C and H subdirectories before dispatch (directory setup only). Each contains
`admission.json`, `process_time.txt` and the runner's `summary.json`; C/H also use `agent/`.
G/C summaries are the exact H panel inputs below. Do not reuse a previous result root.

## Literal ordered remote commands

Execute each block on the declared node using its configured Bash shell. These are three
separate supervisor calls, **not** three submissions issued together. First run G; only after
its terminal evidence meets the continuation conditions run C; only after C meets them run H.
The supervisor name is proposed until the corresponding run call returns actual acceptance.
No selected checkpoint is opened by G.

G:

```bash
/usr/local/bin/agent-task run fsd_native_a01_p21_G_01770d8dd 'bash -lc "cd /home/wu/hmasd-worktrees/fsd-native-renewal-a01-p21-01770d8dd && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/G/admission.json && /usr/bin/time -v -o temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/G/process_time.txt /usr/bin/timeout --signal=KILL 180s /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_native_renewal_control_a01.py --policy G --seed 770103 --launch-sha 01770d8dd6bb59460667efa26e3d94677e65ab37 --out temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/G"'
```

C:

```bash
/usr/local/bin/agent-task run fsd_native_a01_p21_C_01770d8dd 'bash -lc "cd /home/wu/hmasd-worktrees/fsd-native-renewal-a01-p21-01770d8dd && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/C/admission.json && /usr/bin/time -v -o temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/C/process_time.txt /usr/bin/timeout --signal=KILL 180s /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_native_renewal_control_a01.py --policy C --seed 770103 --launch-sha 01770d8dd6bb59460667efa26e3d94677e65ab37 --out temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/C --checkpoint /home/wu/hmasd-inputs/fsd-native-renewal-a01-p21/large_d2_seed2/checkpoint_final.pt"'
```

H:

```bash
/usr/local/bin/agent-task run fsd_native_a01_p21_H_01770d8dd 'bash -lc "cd /home/wu/hmasd-worktrees/fsd-native-renewal-a01-p21-01770d8dd && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/H/admission.json && /usr/bin/time -v -o temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/H/process_time.txt /usr/bin/timeout --signal=KILL 180s /home/wu/.venvs/hmasd/bin/python scripts/run_fsd_native_renewal_control_a01.py --policy H --seed 770103 --launch-sha 01770d8dd6bb59460667efa26e3d94677e65ab37 --out temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/H --checkpoint /home/wu/hmasd-inputs/fsd-native-renewal-a01-p21/large_d2_seed2/checkpoint_final.pt --panel-inputs temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/G/summary.json temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/C/summary.json"'
```

Fresh `admit-memory` is adjacent to the exact bounded runner through `&&` in every supervisor
command. It requires physical and effective available memory each >=4 GiB; a failed admission
runs no policy. The existing external timeout has no grace-period cap extension; it covers
Python startup, imports, load, reset, all scoring and closed-file publication. `/usr/bin/time`
surrounds that command, retaining complete elapsed/user/system/RSS and exit facts even on
termination. Runner deadlines remain unchanged. Supervisor duration also includes admission
and is not substituted for policy wall. Late numerical files alone never establish success.

Supervisor evidence for each accepted name is under
`/home/wu/.agent-tasks/fsd_native_a01_p21_{G,C,H}_01770d8dd/`:
`task.log`, `status`, `pid`, `exit_code`, `start_time`; tmux session
`agent_fsd_native_a01_p21_{G,C,H}_01770d8dd`. The installed supervisor's source/help was read
for these paths and literal run syntax; no task was launched by that inspection. All literal Bash blocks passed remote `bash -n` syntax checking (exit 0) over stdin; this parsed commands without executing them.
Use the actual accepted name, e.g.:

```bash
/usr/local/bin/agent-task status fsd_native_a01_p21_G_01770d8dd
/usr/local/bin/agent-task logs fsd_native_a01_p21_G_01770d8dd 40
```

## Cost, publication coverage and technical continuation

Per-arm cost projection is unchanged from card section 5: G 12,800 scoring steps/400 batched
acts; C and H each 12,800 scoring steps/400 batched controller calls, one construction/load.
Historical learned-arm linear anchors 8.79968751346875 s and 14.72 s exclude standalone
load, batch32 and publication; G complete cost is unknown. No new complete-path cost estimate
or probe is invented. The originally allocated hard caps remain 180 s each and 540 s summed.
Study elapsed critical path also includes staging/admission/observation gaps and is reported
separately from summed policy wall and measured aggregate user+system CPU. This is one
sequential three-process list, not a parallel throughput allocation.

Post-learner/publication path coverage: there is no learner. The original engineering fixture
exercised the three loops and panel serialization/readback; synthetic tests covered loading
and deadline failure, and direct review covered H's nonrecursive attached panel. Actual
selected-weight load and full batch32 runtime remain unverified and are exercised only inside
C and H's allocated invocations. Missing optional RSS is `resources_unmeasured`, not a native
return failure.

After each terminal policy, Root reads the existing artifacts (no new environment or model
calls) and requires for continuation: supervisor terminal exit 0; runner's final one-line JSON
`status=complete`, `cap_breached=false`, complete wall <=180 s; outer process time <=180 s;
summary status complete/failure null with the bound policy, launch SHA, master770103,
ordered IDs0–31, original N6/K2/Z4/H400/Delta1/hazards(.02,.20), and actual counts of
32 completed episodes,12,800 scoring steps,76,800 agent observations. G must have 400 Greedy
batches and zero constructions/loads; C/H each 400 agent batches and one construction/load,
CPU/four threads, disabled observation/state normalization and successful required module/
ValueNorm facts. All arms have zero training starts/transitions/optimizer steps. Both full
and post outcome arrays have 32 finite entries and required counters/losses remain present.
H must retain G/C exact order and its `panel` with four 32-entry paired difference vectors,
means and ddof1 standard errors; totals 96 episodes/38,400 scoring steps/230,400 agent
observations,800 agent batches,400 Greedy batches,2 constructions/loads and zero training.

These are the existing measurement contract, not a new scientific pass test. Numeric sign,
MEI size or G/C/H ranking does not select continuation. Check G before C and C before H;
if a concrete conformity/cap/dependent failure occurs, stop the ordered list and return the
same CM for technical classification with raw output. Preserve G or other independently
trustworthy completed facts. Do not rerun, swap weights/seeds, add diagnostics/episodes,
recombine partial attempts or extend caps. Admission failure or unknown supervisor acceptance
requires exact state reconciliation, never a blind second launch. Any repair after launch
requires a newly selected attempt; this handoff allocates no retry.

Root records actual accepted handles and observation ownership in the existing tracking
record per [EXPERIMENT_MONITOR](../../../project/EXPERIMENT_MONITOR.md) and
[ROOT_OPERATIONS](../../../project/ROOT_OPERATIONS.md). It follows the same handle to terminal
facts and sends the logs, admissions, process times and summaries to this CM through the
existing native route (running: message; idle: follow-up). The DM resumes this same CM for
collection/technical acceptance of the same panel without relaunch. CM then returns technical
conformance/dependent gaps to the DM; DM applies the original conditional-A reading and
brief/audit. No learning-family successor, direction closure or UAV entry follows automatically.
