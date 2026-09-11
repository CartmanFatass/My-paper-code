# DISH-CONTROL-LOW-LR-B04 CM record (2026-09-06)

Worktree `C:/Projects/HMASD/.claude/worktrees/grok-dish-b04`, branch
`grok/dish-control-low-lr-b04-20260906`. Grok Build implemented the thin B04 entry;
Git commit/push is the hub's pathspec step (this session ran no git commands that
change state). Scope §4: none. Launch sha `<sha>` (hub fills at launch).

## Files created (A/D)

All owned paths are new files (D=0). `git status` showed only these untracked
paths; B02, B03, witness and r06 bytes were not edited.

| Path | A | D | Role |
| --- | ---: | ---: | --- |
| `experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/__init__.py` | 1 | 0 | package marker |
| `experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/study.py` | 239 | 0 | B04 object/seed/master, `set_learning_rate` / `learning_rates`, shared prep, `run_arm`, `paired_result` |
| `scripts/run_dish_control_low_lr_b04.py` | 156 | 0 | B04 runner (`shared` / `run` / `project-cost`; `import resource` kept; no stub) |
| `tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/__init__.py` | 1 | 0 | test package marker (owned path; B03 test package had none) |
| `tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/test_study_b04.py` | 175 | 0 | master / rate rewrite / chained dry updates / configuration / resets / pair; `publish` under `importorskip("resource")` |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_CONTROL_LOW_LR_B04_CM_RECORD_20260906.md` | 178 | 0 | this record |

Non-test source A=396, D=0 (package marker 1 + study 239 + runner 156). Runner 156.
Budget: new source ≤ 450, runner ≤ 200. Both held. No new guard, registry, validator,
retry, resume or telemetry beyond wall/RSS/CPU already in the B03 runner. The learning-rate
drift `RuntimeError` and the reset-equality assertion are the card's acceptance checks.

## Imports reused (not copied)

From `forecast_package_b02.study`: `HOST`, `HARD_EVENTS`, `planned_cost`, `new_progress`,
`check_time`, `TrainingMeasurements`, `parameter_movement`, `evaluate_episode`, `exposure`,
`backend`, `EvaluationCoordinate`, `load_host`, `_reset_row`.
From `forecast_package_b03.study` (re-exported r06 names B03 already imported):
`BatchedRecurrentPolicy`, `RecurrentRolloutState`, `NativePersistentTrainingFlow`,
`MasterAddressedTrainResetFactory`, `build_master_addressed_initial_state`.
Focused tests import `run_full_4096_dry_update` from r06 `production_training_engine`
and `build_master_addressed_initial_state` from r06 `production_recurrent_trainer`.
B02, B03, witness and r06 source bytes were not edited.

## Learning-rate mechanism as implemented

The optimizer that steps is a local of `run_full_4096_dry_update`, rebuilt with
`lr=3e-4` and then overwritten by `optimizer.load_state_dict` from the previous
checkpoint. No live optimizer is reachable from the study.

- `set_learning_rate(payload, lr)` `torch.load`s the payload (`weights_only=False`),
  sets `group["lr"] = lr` for **every** entry of `loaded["optimizer"]["param_groups"]`
  (raises `RuntimeError` if the group count is not 2), and `torch.save`s back to bytes.
  `betas`, `eps`, `weight_decay`, the model state and the Welford states are not rewritten.
- `learning_rates(checkpoint)` reads `float(group["lr"])` from every optimizer param group
  of a checkpoint (read-only).
- `run_arm` reads shared `initial_state.pt` (no initializer call), then
  `initial = set_learning_rate(bytes, LEARNING_RATES[arm])` before constructing
  `NativePersistentTrainingFlow(..., checkpoint_bytes=initial, forecast_package=False)`.
- After every `apply_update`, `run_arm` records
  `"learning_rates": learning_rates(flow.trainer.checkpoint_bytes)` on the curve entry
  and raises `RuntimeError("B04 learning rate drift")` if any entry differs from
  `LEARNING_RATES[arm]`.
- `configuration(arm)["learning_rate"]` is `LEARNING_RATES[arm]`, the same value written
  into the payload; `learning_rate_mechanism` records the construct-then-restore path.

## Initializer and reset facts observed in the tests

One `build_master_addressed_initial_state(master=master(), block=0, arm="STRUCTURED")`
call (module fixture) on this host, seed 89:

- `master().hex()` = `665c8d879ef9d289d4ad6d4d3bf051643d9f17bb05c97521566dc48a77071c9d`
  (differs from B03 seed-73 `b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a`)
- `initial_model_norm` = `38.26126788822669`
- Welford `actor` / `snapshot` / `critic` counts all 0; counts and mean/m2 bytes unchanged
  after `set_learning_rate`
- constructed `learning_rates(payload)` = `[0.0003, 0.0003]` (`3e-4` on both groups)
- after `set_learning_rate(payload, 3e-5)`: `[3e-05, 3e-05]`; `betas` / `eps` /
  `weight_decay` and model-state bytes unchanged; `set_learning_rate(..., 3e-4)` reads
  back `[3e-4, 3e-4]`
- four `recorded_resets` keys in B03 order; each JSON round-trip equals
  `dict(_reset_row(master(), coordinate))`
- chained `run_full_4096_dry_update` (synthetic fixture, `forecast_package=False`):
  two updates per arm (four calls). `learning_rates` of both LOW_LR checkpoints
  `[3e-5, 3e-5]`, both CONTROL checkpoints `[3e-4, 3e-4]`; `second["update"] == 2`.
  One-update L2 displacement LOW_LR `0.1758037874918696` < CONTROL `0.8080813832152219`.

The r06 C++ RNG backend is used by the initializer (`rng_words_native`); the A03 host
library (`load_host`) is not. Tests do not import B02/B03 runners. The B04 runner is
imported only under `pytest.importorskip("resource")`.

## Local pytest (Windows, hub interpreter)

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/test/b04-grok tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04 tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03 tests/experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01
```

Verbatim summary: `15 passed, 2 skipped, 1 warning in 17.92s`.

The two skips are `test_runner_publish_under_resource` in B03 and in B04
(`pytest.importorskip("resource")`). The warning is pytest `cache_dir` under
`-p no:cacheprovider`.
`tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_package.py`
does not collect on Windows: module-level `from scripts.run_dish_forecast_package_b02 import publish`
executes `import resource` (`ModuleNotFoundError: No module named 'resource'`).
That gap is not closed by stubbing; the file was not in the local command.

Chained-update wall (four synthetic `run_full_4096_dry_update` calls, two per arm):
`8.069271599990316` s (per-call walls `2.097`, `1.991`, `1.972`, `2.003` s).
Pytest call duration for that test was `8.11s` on the instrumented run.

## Frozen `wsl_4070` commands (launch sha `<sha>`)

Worktree `/home/wu/hmasd-worktrees/dish-b04-20260906` at the launch sha; interpreter
`/home/wu/.venvs/hmasd/bin/python`; `PYTHONPATH=/home/wu/hmasd-worktrees/dish-b04-20260906`;
`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`; output root
`temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/`.

Shared item `S` (one timed command, task `dish_b04_shared_20260906`; `S` is its elapsed wall):
```
/usr/bin/time -v bash -lc 'cd /home/wu/hmasd-worktrees/dish-b04-20260906 && python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/admission_shared.json && python -m pytest -q -p no:cacheprovider tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04 && python scripts/run_dish_control_low_lr_b04.py shared --admission temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/admission_shared.json --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/shared'
```
Arms (tasks `dish_b04_control_20260906`, then `dish_b04_low_lr_20260906` after the control
summary exists):
```
/usr/bin/timeout --signal=ALRM <1800 - S/2 - 3.4>s bash -lc 'cd /home/wu/hmasd-worktrees/dish-b04-20260906 && python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/admission_control.json && python scripts/run_dish_control_low_lr_b04.py run --arm CONTROL --seed 89 --shared temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/shared --shared-preparation-seconds <S> --admission temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/admission_control.json --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/control'
```
```
/usr/bin/timeout --signal=ALRM <1800 - S/2 - 3.4>s bash -lc 'cd /home/wu/hmasd-worktrees/dish-b04-20260906 && python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/admission_low_lr.json && python scripts/run_dish_control_low_lr_b04.py run --arm LOW_LR --seed 89 --shared temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/shared --shared-preparation-seconds <S> --admission temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/admission_low_lr.json --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/low_lr --control-summary temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/control/summary.json'
```

Shared item `S` is that one timed command (focused B04 pytest + `prepare_shared`: one
initializer, four-row zero-update raw reference, `resets.json` / `initial_state.pt` /
`summary.json`). No result-bearing arm was launched from this worktree.

## Cost range (B03 / witness timings; references, not projections)

`planned_cost()` (imported from B02): law `N ordinary + L next-label + 2E delay + H consequence; H <= 20E`;
`N=65536`, `L=65536`, `native_training_calls_upper=1572864`, `evaluation_ticks_upper=4800`,
`optimizer_steps=512`, `projected_wall_seconds=None`,
`projection_status=unmeasured on this host; not inferred from native work bound`,
`whole_arm_cap_seconds=1800`, shared charge `measured shared wall / 2`.

References (card §6; not adopted as B04 projections; a tenfold learning-rate cut is not
a tenfold time cut):

| Work type | Reference | Source |
| --- | --- | --- |
| B03 CONTROL prepublication arm wall | 196.83 s | B03 result intake (`ad01757c4`) |
| B03 FORECAST_PACKAGE prepublication arm wall | 185.55 s | same |
| B03 `/usr/bin/time` arm walls | 211.04 s / 196.18 s | same |
| B03 shared focused check `C` | 4.94 s | same |
| B03 complete chain | 412.16 s | 211.04 + 196.18 + 4.94 |
| Witness whole item | 16.23 s | 4.981 s focused + 11.25 s eight-episode run |
| Witness formal prepublication | 10.953 s | witness result intake |
| B04 chained synthetic updates (this host, not node) | 8.07 s for four dry updates | focused check above |

B04 shared `S` is focused B04 pytest plus one initializer plus four raw-interface
episodes (witness did eight episodes in 11.25 s). B04 each arm is the inherited
CONTROL sixteen-update learner (B03 CONTROL 196.83 s prepub). Range from those
references: `S` on the order of tens of seconds (tests plus four-row reference;
native cache/build may add to the first shared command); each arm on the order of
B03's ~180–220 s prepublication / ~200–220 s `/usr/bin/time` wall; pair plus `S`
on the order of B03's 412 s chain, against the B04 caps 1,800 s per arm and
3,600 s for both. No complete-plan range problem relative to those caps is
returned from these references. `E`/`H` may change with seed 89 and the rate;
nominal counts never replace observations. The B04 runner was not executed
(Windows has no `resource`; no training/evaluation launched).

## Unverified

- Node focused check and shared item `S` (initializer on the A03 host, four-row
  zero-update reference, `test_runner_publish_under_resource`, SIGALRM / `resource`
  telemetry).
- Both arms' wall, RSS, CPU, actual exposure, per-update `learning_rates` curves,
  checkpoints, recorded seed-89 resets under training, and `paired.json` on
  `wsl_4070` at `<sha>`.
- Collection and pass of `forecast_package_b02/test_package.py` (not in the local
  command; does not collect on Windows).
- Numeric fill-in of `<S>` and `<1800 - S/2 - 3.4>` after `S` is measured.
- Whether seed-89 `initial_model_norm` `38.26126788822669` equals any later node
  reading (initializer coverage here used the r06 RNG backend only).

scope: none
