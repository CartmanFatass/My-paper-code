# N3 DISH B01 C04 — CM technical return

Technical readiness exists for DM launch selection at pushed source
`e0541d0cb3e9e63731c72f4dacb10b44d268fd39`. The eight requested tests are covered by
seven unchanged passes and the repaired-node pass; direct project-cost completed. No scientific
seed, admission, learner run, result checkpoint, evaluation panel or FTS branch was produced.
Engineering conformance does not establish source value or scientific validity of future outputs.

## Contract and source facts

Objective: `N3_DISH_B01_C04_OBJECTIVE_20260904.md`, committed at
`271489d16d1bc7e9acf5c741e9d2bf9f2e7fd3fe`. CM worktree is
`C:/Projects/HMASD-worktrees/cm-n3-dish-c04-20260904`, branch
`cm/n3-dish-c04-20260904`. Implementer used its separate
`C:/Projects/HMASD-worktrees/impl-n3-dish-c04-20260904` and branch
`codex/impl-n3-dish-c04-20260904`. Both code branches were pushed immediately after each commit.
Saved dirty project and historical worktrees were preserved.

All eleven selected paths at current baseline equalled `38429fb7e18781b874a079ddc023bfde7995f3cc`:
five existing production files, six absent additions. Commit
`e15c1794ee2be2907d3b692f8ab7c347c5bc688e` transferred only those exact blobs from
`b0c63b69cabd1cdaceac4ea6370def6d97a93c15`; unrelated candidate ancestry was not integrated.
CM inspected the selected diff and equality; all eleven candidate blobs were identical.
The prior complete independent review was reused under the explicit C04 objective.

Final delta from the objective baseline (prefixes below are repository-relative):

| Path | Added | Deleted |
| --- | ---: | ---: |
| `experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/__init__.py` | 6 | 0 |
| Same directory `result_rule.py` | 29 | 0 |
| Same directory `study.py` | 314 | 0 |
| `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp` | 179 | 31 |
| Same R06 directory `production_backend.py` | 250 | 30 |
| Same R06 directory `production_evaluator.py` | 14 | 2 |
| Same R06 directory `production_recurrent_trainer.py` | 128 | 48 |
| Same R06 directory `production_training_engine.py` | 160 | 46 |
| `scripts/run_dish_first_trigger_source_scout_b01.py` | 118 | 0 |
| `tests/experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/test_b01.py` | 146 | 0 |
| `tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_b01_production_conformance.py` | 234 | 0 |

Total source/test delta: **+1,578/-157**. Added non-test research lines remain **1,198**;
runner **118**; unchanged reviewed conservative orchestration **274/1,198 = 22.9%**.
Section-4 additions: **none**. The only departure from candidate bytes is a **+13/-1 test-only**
repair in the final row. All nine non-test files remain exactly the reviewed candidate blobs.

Protected meaning is unchanged: seeds 11/29/47 and SHA256 master law, 64 updates, 32 lanes,
16 evaluation rows, first-valid post-arrival/post-assimilation/pre-CAS/pre-GRU fork, 100 ticks,
RETAIN/COPY/SHADOW mapping, same-information comparison, native authority, FP32 CPU policy,
float64 native physics, one Torch thread, RNG coordinates/draws, optimizer and Welford ordering,
checkpoint payload and external effects. No production kernel, efficacy threshold or result rule
changed. Five service ticks is descriptive only. Binary service sums over 100 ticks to [0,100];
five ticks is five percentage points of full scale, not five percent relative to COPY.

## Reproduced C03 launcher defect

Old remote SHA/worktree:
`b0c63b69cabd1cdaceac4ea6370def6d97a93c15`,
`/home/wu/hmasd-worktrees/dish-b01-c03-b0c63b69`.
Original task `dish_b01_c03_final_b0c63b69_01` remains failed exit 4.
Its wrapper and log remain under `/home/wu/.agent-tasks/dish_b01_c03_final_b0c63b69_01/`.

Read-only inspection found `tests` in sparse checkout, all four frozen test files matching Git
blobs, and all four specified function nodes present by AST. The first file's birth/mtime
`2026-09-05 01:38:30 +08` precedes task start `01:39:56 +08`. Thus the historical missing-sparse-
file attribution is contradicted. The saved command actually begins unquoted
`bash -lc cd /home/wu/hmasd-worktrees/dish-b01-c03-b0c63b69 && ...`.
The child cd cannot change the outer shell's directory.

Bounded reproduction used subprocess cwd `/home/wu` and this command:

```sh
bash -lc cd /home/wu/hmasd-worktrees/dish-b01-c03-b0c63b69 && pwd && PYTHONDONTWRITEBYTECODE=1 /home/wu/.venvs/hmasd/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_r06_conformance.py::test_native_abi_binds_exact_r06_population_row
```

Direct output: cwd `/home/wu`, returncode 4, zero collected and the same missing relative target.
No test function executed. C04 fixes the supervisor command directly, with one string beginning
`cd <cwd> && pwd && ...`; no wrapper/guard implementation was added.

## Remote preparation and verification

Node `wsl_4070`, SSH alias `hmasd-wsl-node`; interpreter
`/home/wu/.venvs/hmasd/bin/python`. Observed Python 3.10.21, NumPy 1.26.3, Torch 2.7.0+cu118,
pytest 7.0.1, g++ 13.3.0; c++ and /usr/bin/time available. CPU remains the selected device.
Remote GitHub fetch remained silent for approximately two minutes; owned fetch processes were
terminated. This is an observed transport stall, not a diagnosed network cause. A small first
bundle lacked remote prerequisite objects; preparation remained unaccepted. A 1,677,225-byte
Git bundle including the missing committed ancestry was then unbundled, and the test-only commit
was supplied by another Git bundle. All source had already been committed and pushed; no
uncommitted source was copied. Detached worktrees were clean and included the configured tests.

First accepted task: `dish_b01_c04_final_e15c1794_01`, source `e15c1794ee2be2907d3b692f8ab7c347c5bc688e`.
Working directory `/home/wu/hmasd-worktrees/dish-b01-c04-e15c1794`.
Its command was the following concatenation (shell cd and invocation share the outer shell):

```sh
cd /home/wu/hmasd-worktrees/dish-b01-c04-e15c1794 && pwd && /usr/bin/time -f TEST_WALL_SECONDS=%e /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --durations=0 --basetemp /home/wu/hmasd-worktrees/dish-b01-c04-e15c1794/temp/directions/degraded_incumbent_shadow_handover/test/dish_b01_c04_final_e15c1794_01 tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_r06_conformance.py::test_native_abi_binds_exact_r06_population_row tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_r06_conformance.py::test_r06_production_entry_refuses_without_later_decision_and_lease tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_source_factored_native.py::test_source_factored_native_three_way_clone_is_atomic_and_truthful tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_source_factored_native.py::test_source_factored_native_alpha_equivalence_and_combined_predicate tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_b01_production_conformance.py tests/experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/test_b01.py && /usr/bin/time -f PROJECT_COST_WALL_SECONDS=%e /home/wu/.venvs/hmasd/bin/python scripts/run_dish_first_trigger_source_scout_b01.py project-cost
```

Terminal exit 1: **7 passed, 1 failed**, pytest 4.68 s, process wall 5.04 s.
Native compile/load regression passed (2.06 s). Prepared-branch smoke passed (1.23 s), including
its internal project-cost subprocess. The final direct cost was skipped by `&&`.

The failure at conformance test line 127 was reproduced by the implementer over exact unchanged
remote bytes. Two bounded stdin probes used runpy to invoke only that function and inspect its
assertion frame. Observations: 169 action differences, maximum 1.1920928955078125e-7, none on
nonrenewed entries; per-tick versus batched motion heads differed at 247 entries, maximum
2.9802322387695312e-8; prepare/commit were identical. Per-tick projection matched actual actions
exactly. Both batched and per-tick old log probabilities matched behavior exactly, and ratios
were exactly one. The initial float64-NumPy-projection hypothesis was rejected: production also
uses FP32 Torch tanh. The isolated cause is FP32 head GEMM grouping across ticks.

The test-only repair computes expected actions from per-tick heads of the exactly verified
replay hidden states. A direct batched-motion comparison remains, bounded elementwise by
`eps(float32) * max(1, abs(step_motion))`. This dtype-derived tolerance applies to this unit-scale
sentinel, not a universal GEMM error theorem. Exact actions, hidden states, normalization,
promotion, discrete outcomes, log probabilities and ratio checks remain. Original batched heads
still supply replay likelihood. Independent reviewer `rev_ah_n3_c04_precision` inspected the
complete +13/-1 diff and returned no material finding; DM accepted the within-precision reading.

Second accepted task: `dish_b01_c04_repair_e0541d0c_01`, final source SHA above.
Exact command:

```sh
cd /home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c && pwd && /usr/bin/time -f TEST_WALL_SECONDS=%e /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --durations=0 --basetemp /home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c/temp/directions/degraded_incumbent_shadow_handover/test/dish_b01_c04_repair_e0541d0c_01 tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_b01_production_conformance.py::test_live_fragment_replay_has_one_exact_fp32_behavior_law && /usr/bin/time -f PROJECT_COST_WALL_SECONDS=%e /home/wu/.venvs/hmasd/bin/python scripts/run_dish_first_trigger_source_scout_b01.py project-cost
```

Terminal exit 0: **1 passed**, pytest 1.26 s (test call 0.15 s), process wall 1.67 s;
direct cost wall 1.27 s. Unchanged seven passes and smoke were not repeated. Both pytest commands
reported only `PytestConfigWarning: Unknown config option: cache_dir`, with cacheprovider disabled.
No test-directory five-minute budget or smoke sixty-second budget was exceeded.

Generated direct cost: law `1.5 * (64 * 10.672341100056656 + 300)`, updates 64, cap 1800.
Seeds **11, 29, 47 each project 1474.544745605439 s**. RETAIN, TRANSFER_COPY, TRANSFER_SHADOW
each receive the entire **1474.544745605439 s** charge; all three `within_cap=true`.
These are runner-generated projections, not measured seed runtime or measured resource conformance.

## Artifacts, coverage and next step

Tracker `/root/tracker_tl_experiments` acknowledged each accepted handle and was sole observer;
CM collected only after terminal notices. No live verification remains. Original supervisor
`task.log`, `runner.sh`, status and exit witnesses remain under each task's `/home/wu/.agent-tasks/`
directory. Local collected logs/commands and exact diagnostic scripts are under CM-worktree
`temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/`:
`verification01.log`, `verification02.log`, `verification01-command.sh`,
`verification02-command.sh`, `c03-original-command.sh`, `diagnostic01.py`, `diagnostic02.py`.

**Post-learner path coverage is an open engineering item.** Existing smoke traverses production
prepared branches, JSON serialization of a small list and real project-cost. It does not execute
runner `_run`, final checkpoint/summary file publication, real learner updates, full 16-row
evaluation, or actual parameter displacement. No B01 post-learner failure has occurred; this is
recorded coverage debt, not an additional B launch gate. Carry it on every result until addressed.
Actual exposure/nonzero work and complete publication must be inspected in the future real run.

Result resource telemetry is not applicable: no result invocation exists. Test wall times above
are measured; test peak RSS was not measured. No admission receipt was requested or created.
Next action belongs to DM: select the concrete unchanged seed invocation(s), freeze exact command,
and join fresh node-local >=4 GiB physical/effective admission with runner by `&&`. Keep admission
and logs outside the absent output child because `_run` creates that child at publication.
Scientific output root remains the objective's `temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/`.
This CM return authorizes no scientific run by itself and assigns no FTS polarity.

## Accepted seed 11 launch — 2026-09-05 00:12:03 UTC

DM subsequently accepted the technical return and selected only seed 11 in
`N3_DISH_B01_C04_LAUNCH_INTAKE_20260904.md`, pushed commit `551fd251f`.
Before dispatch, task `dish_b01_c04_seed11_e0541d0c_a1` returned `not_found`; its output child
and admission path were absent. The execution worktree was clean at exact source
`e0541d0cb3e9e63731c72f4dacb10b44d268fd39`. No repeated smoke was performed.

The following exact single command string was accepted once by `/usr/local/bin/agent-task run`
on `wsl_4070` via `hmasd-wsl-node`:

```sh
cd /home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_first_trigger_source_scout_b01.py run --seed 11 --admission temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1_admission.json --out temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1
```

- Supervisor task: `dish_b01_c04_seed11_e0541d0c_a1`; tmux `agent_dish_b01_c04_seed11_e0541d0c_a1`.
- Supervisor start epoch: `1788567123` (2026-09-05 00:12:03 UTC / September 4 17:12:03 PDT).
- Supervisor PID: `112219`; this is launch metadata, not proof of learner completion.
- Cwd: `/home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c`.
- Log: `/home/wu/.agent-tasks/dish_b01_c04_seed11_e0541d0c_a1/task.log`;
  existing `status`, `exit_code` when terminal, `start_time`, `pid`, `runner.sh` reside beside it.
- Receipt relative to cwd:
  `temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1_admission.json`.
- Output relative to cwd:
  `temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1`.

Destination receipt captured at `2026-09-05T00:12:03.356900Z`, assessed at
`2026-09-05T00:12:03.357208Z`, measurement `/proc/meminfo`:
physical available **12,531,122,176 bytes**, effective available **12,531,122,176 bytes**;
minimum **4,294,967,296 bytes**; both floor flags and `passed` true; failure reasons empty.
The receipt lives outside the absent-at-launch result child, and `&&` admits only this invocation.
These admission readings do not establish runtime peak RSS or resource conformance.

Expected duration remains 1474.544745605439 seconds, charged independently to each arm;
the 1800-second stop is checked at the runner's declared boundaries. CPU/one Torch thread,
FP32 learner/float64 native and all scientific semantics are unchanged.

Tracker `/root/tracker_tl_experiments` ACKed adoption of this exact scientific handle and is
the sole observer/reminder for terminal, observation-loss and bound events. CM read only the
initial admission and start metadata after acceptance, then released polling. DM is
`/root/dm_amx_n3_continue`; CM collector is `/root/dm_amx_n3_continue/cm_am_n3_dish_c04`.
No terminal result is claimed here. Seeds **29 and 47 remain queued**, contingent only on
seed 11 technical completeness, with no efficacy/trigger-support screening or changed seed law.
The recorded learner/publication coverage limitation remains open pending collection.

## Accepted seed 29 launch — 2026-09-05 00:47:14 UTC

DM accepted complete seed 11 and selected only unchanged seed 29 in
`N3_DISH_B01_C04_SEED11_INTAKE_20260904.md`, pushed commit `0554e85b1`.
Before dispatch, `dish_b01_c04_seed29_e0541d0c_a1` returned `not_found`; output
`seed29_a1` and receipt `seed29_a1_admission.json` were absent. The existing remote worktree
was clean at source `e0541d0cb3e9e63731c72f4dacb10b44d268fd39`. No tests or source changes occurred.

Accepted once as one `/usr/local/bin/agent-task run` command string on `wsl_4070`:

```sh
cd /home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed29_a1_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_first_trigger_source_scout_b01.py run --seed 29 --admission temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed29_a1_admission.json --out temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed29_a1
```

- Task `dish_b01_c04_seed29_e0541d0c_a1`; tmux `agent_dish_b01_c04_seed29_e0541d0c_a1`.
- Supervisor start epoch `1788569234` (2026-09-05 00:47:14 UTC / September 4 17:47:14 PDT), PID `607075`.
- Cwd `/home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c`.
- Log `/home/wu/.agent-tasks/dish_b01_c04_seed29_e0541d0c_a1/task.log`; status, eventual exit_code,
  start_time, pid and runner.sh beside it.
- Receipt and output are the exact cwd-relative paths in the command; receipt is outside output.

Fresh receipt capture `2026-09-05T00:47:14.317386Z`, assessment
`2026-09-05T00:47:14.317661Z`: physical available and effective available each
**15,432,970,240 bytes**, minimum **4,294,967,296 bytes**, both floor flags and `passed` true,
failure reasons empty, source `/proc/meminfo`. This is admission, not runtime resource telemetry.
Expected cost remains **1474.544745605439 seconds per fully charged source arm**, cap **1800**
at declared boundaries, with CPU one Torch thread, FP32 learner and float64 native unchanged.

Tracker `/root/tracker_tl_experiments` ACKed adoption and alone observes/reminds at terminal,
observation loss or cap. DM `/root/dm_amx_n3_continue`; CM collector
`/root/dm_amx_n3_continue/cm_am_n3_dish_c04`. CM read initial receipt/start metadata only and
released polling. Seed **47 remains queued**. Seed 11's empty-support default differences are
not effects and did not change seed selection. No seed 29 completion or scientific result is
claimed at this accepted detached boundary.
