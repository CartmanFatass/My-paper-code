# DISH-FORECAST-PACKAGE-B03 CM record (2026-09-06)

Worktree `C:/Projects/HMASD/.claude/worktrees/grok-dish-b03`, branch
`grok/dish-b03-thin-entry-20260906`. Grok Build implemented the thin B03 entry;
Git commit/push is the hub's pathspec step (this session ran no git commands).
Scope §4: none. Launch sha `<sha>` (hub fills at launch).

## Files created (A/D)

All owned paths are new files (D=0). B02 test package has no `__init__.py`; none
was created under the B03 test directory.

| Path | A | D | Role |
| --- | ---: | ---: | --- |
| `experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03/__init__.py` | 1 | 0 | package marker |
| `experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03/study.py` | 122 | 0 | B03 object/seed/master/configuration; copied `run_arm` / `paired_result` |
| `scripts/run_dish_forecast_package_b03.py` | 113 | 0 | B03 runner (`import resource` kept; no stub) |
| `tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03/test_study_b03.py` | 132 | 0 | seed/object/configuration/pair/boundary; `publish` under `importorskip("resource")` |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B03_CM_RECORD_20260906.md` | 122 | 0 | this record |

Non-test source A=236, D=0, runner 113. Budget: source ≤ 400, runner ≤ 200.

Helpers reused by import from `forecast_package_b02.study` (not copied):
`HOST`, `ARMS`, `HARD_EVENTS`, `planned_cost`, `new_progress`, `check_time`,
`TrainingMeasurements`, `parameter_movement`, `evaluate_episode`, `exposure`,
`backend`, `EvaluationCoordinate`, `BatchedRecurrentPolicy`,
`RecurrentRolloutState`, `NativePersistentTrainingFlow`,
`MasterAddressedTrainResetFactory`, `build_master_addressed_initial_state`,
`load_host`, `_reset_row`. B02 and r06 source bytes were not edited.

## Substitutions relative to B02

| Item | B02 | B03 |
| --- | --- | --- |
| object id | `DISH-FORECAST-PACKAGE-B02` | `DISH-FORECAST-PACKAGE-B03` |
| seed literal | `61` | `73` |
| master string | ASCII `DISH-FORECAST-PACKAGE-B02/seed/61` | ASCII `DISH-FORECAST-PACKAGE-B03/seed/73` |
| master hex | `ef9ec35ce27cf52e4c1d82292b22cfbe4926183ec1f29b19657280f6234814b1` | `b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a` |
| runner `--seed` | `choices=(61,), default=61` | `choices=(73,), default=73` |
| runner study import | `forecast_package_b02.study` | `forecast_package_b03.study` |
| runner TimeoutError | `B02 whole-arm wall allowance reached` | `B03 whole-arm wall allowance reached` |

Configuration additions versus the B02 `progress["configuration"]` dictionary:
`"seed": 73`, `"master_hex": master().hex()`, `"object": OBJECT`,
`"forecast_package": arm == "FORECAST_PACKAGE"`, and
`"renewal_boundary": "corrected: observation['renew'] = countdown == 0 (3f4d447f6); raw flag renew_completed"`.
Remaining configuration keys match B02.

Copied `run_arm` retains B02's `FloatingPointError("B02 nonfinite learner update")`.
Imported `check_time` still raises `TimeoutError("B02 complete-arm wall allowance exhausted")`.

## Local pytest (Windows, hub interpreter)

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/test/b03-grok tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03 tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a02.py tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a01.py
```

Summary line: `15 passed, 1 skipped, 1 warning in 4.27s`.

The skip is `test_runner_publish_under_resource` (`pytest.importorskip("resource")`).
The warning is pytest `cache_dir` under `-p no:cacheprovider`.
`tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_package.py`
cannot collect on Windows: module-level `from scripts.run_dish_forecast_package_b02 import publish`
executes `import resource` (`ModuleNotFoundError: No module named 'resource'`).
That gap is not closed by stubbing; the node focused check collects it.

## Frozen `wsl_4070` commands (launch sha `<sha>`)

Worktree on the node: `/home/wu/hmasd-worktrees/n3-b03-20260906` at `<sha>`;
interpreter `/home/wu/.venvs/hmasd/bin/python`; `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1`; output root
`temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/`.

Shared preparation `C` (timed, one command, task `n3_b03_focused_20260906`):

```
/usr/bin/time -v bash -lc 'cd /home/wu/hmasd-worktrees/n3-b03-20260906 && python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/admission_focused.json && python -m pytest -q -p no:cacheprovider tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02 tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03'
```

`C` is the measured elapsed wall of that command; each arm's `--shared-preparation-seconds`
is `C`. The focused pytest includes `forecast_package_b02` (`test_package.py` collects
on Linux) and `forecast_package_b03`.

CONTROL (task `n3_b03_control_20260906`):

```
/usr/bin/timeout --signal=ALRM <1800 - C/2 - 3.4>s bash -lc 'cd /home/wu/hmasd-worktrees/n3-b03-20260906 && python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/admission_control.json && python scripts/run_dish_forecast_package_b03.py run --arm CONTROL --seed 73 --shared-preparation-seconds <C> --admission temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/admission_control.json --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/control'
```

FORECAST_PACKAGE (task `n3_b03_forecast_package_20260906`, after the control summary exists):

```
/usr/bin/timeout --signal=ALRM <1800 - C/2 - 3.4>s bash -lc 'cd /home/wu/hmasd-worktrees/n3-b03-20260906 && python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/admission_forecast_package.json && python scripts/run_dish_forecast_package_b03.py run --arm FORECAST_PACKAGE --seed 73 --shared-preparation-seconds <C> --admission temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/admission_forecast_package.json --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/forecast_package --control-summary temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/control/summary.json'
```

No result-bearing arm was launched from this worktree.

## Cost projection (runner law; not a launch)

`planned_cost()` (imported from B02): law `N ordinary + L next-label + 2E delay + H consequence; H <= 20E`;
`N=65536`, `L=65536`, `native_training_calls_upper=1572864`, `evaluation_ticks_upper=4800`,
`optimizer_steps=512`, `projected_wall_seconds=None`,
`projection_status=unmeasured on this host; not inferred from native work bound`,
`whole_arm_cap_seconds=1800`, shared charge `measured shared wall / 2`.
B02 complete-arm walls 337.23 s / 298.60 s (charged 340.645 / 302.015 s) are planning
references from the B03 card; `E/H` may change on the corrected boundary. Neither
reference exceeds 1800 s. The B03 runner was not executed (Windows has no `resource`;
no training/evaluation launched).

Post-learner publication path: B03 `paired_result` of two handwritten `COMPLETE`
summaries is asserted locally; runner `publish` is skipped on Windows and is part
of the node focused check.

## Unverified

- Node focused check (shared preparation `C`), including collection and pass of
  `forecast_package_b02/test_package.py` and B03 `test_runner_publish_under_resource`.
- Both arms' wall, RSS, CPU, actual exposure, checkpoints and paired primary on
  `wsl_4070` at `<sha>`.
- Numeric fill-in of `<C>` and `<1800 - C/2 - 3.4>` after `C` is measured.

scope: none

## Execution addendum (hub, 2026-09-06 10:35 PDT)

Launch sha `ad01757c43cb3a3df6549b024367b5f9307246b8` (main; the Grok branch commit 78f07a0de was
cherry-picked as ad01757c4). The frozen commands above omitted `PYTHONPATH=<worktree>`, which
B02's commands set; the first CONTROL attempt therefore failed at 2.48 s with
`ModuleNotFoundError: experiments` before any RNG/model/learner work (record preserved under
`forecast_package_b03_20260906/` on the node), after an earlier attempt that died in the
operator's SSH quoting layer (0 s). Attempt 3 ran from launch scripts with `PYTHONPATH`
exported and output root `forecast_package_b03_20260906_r3/`: shared preparation
`n3_b03_focused_20260906` 21 passed in 4.37 s (includes `test_package.py` and
`test_runner_publish_under_resource`), `C = 4.94 s`; CONTROL `n3_b03_control_20260906_r3`
exit 0, wall 211.04 s; FORECAST_PACKAGE `n3_b03_forecast_package_20260906_r3` exit 0, wall
196.18 s; both `COMPLETE`, paired primary `COMPLETE`. Evidence copied to
`b03_forecast_package_20260906/`; result intake
`DISH_FORECAST_PACKAGE_B03_RESULT_INTAKE_20260906.md`.
