# CM objective — DISH-FORECAST-PACKAGE-B03 thin entry (2026-09-06)

Card: `DISH_FORECAST_PACKAGE_B03_SCIENCE_CARD_20260906.md` (sections 2, 3, 6, 7 bind).
Implementer: Grok Build (Appendix C), worktree `.claude/worktrees/grok-dish-b03`, branch
`grok/dish-b03-thin-entry-20260906`; hub review and pathspec commit. Base: current `main`.

## Objective

Provide a runnable B03 entry that executes the B02 two-arm comparison unchanged in
treatment, control, host, exposure, evaluation and publication, but under the B03 object
id, the new paired seed 73 (master = SHA256 of ASCII `DISH-FORECAST-PACKAGE-B03/seed/73`,
hex `b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a`), and the corrected
ordinary renewal boundary already on `main` (`production_backend.py`, commit `3f4d447f6`).
The corrected boundary needs no study change: B02's `run_arm` consumes `observation["renew"]`
through `NativePersistentTrainingFlow.collect_update`. What must change is only what is
hard-coded to B02: `OBJECT`, the seed literal in the master string, the recorded
configuration seed, the runner's object literal and `--seed` choices.

## Owned paths (create only; nothing else is edited)

- `experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03/__init__.py`
- `experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03/study.py`
- `scripts/run_dish_forecast_package_b03.py`
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03/__init__.py` (if the
  B02 test package has one; mirror it)
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03/test_study_b03.py`
- `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B03_CM_RECORD_20260906.md`

Not edited: `forecast_package_b02/**`, `first_trigger_source_scout_b01/**`, every
`degraded_incumbent_shadow_handover_rbhr_r06/**` source, `scripts/run_dish_forecast_package_b02.py`,
existing tests, cards, intakes, governance files.

## Design (fixed)

1. `forecast_package_b03/study.py` imports from `forecast_package_b02.study` everything it
   reuses (`HOST`, `ARMS`, `HARD_EVENTS`, `planned_cost`, `new_progress`, `check_time`,
   `TrainingMeasurements`, `parameter_movement`, `evaluate_episode`, `exposure`, and the
   r06/B01 imports it needs) and defines:
   - `OBJECT = "DISH-FORECAST-PACKAGE-B03"`, `SEED = 73`;
   - `master()` returning `hashlib.sha256(f"{OBJECT}/seed/{SEED}".encode("ascii")).digest()`;
   - `configuration(arm)` returning the same dictionary B02 records under
     `progress["configuration"]` with `"seed": 73`, `"master_hex": master().hex()`,
     `"object": OBJECT`, `"forecast_package": arm == "FORECAST_PACKAGE"`, and one added
     literal `"renewal_boundary": "corrected: observation['renew'] = countdown == 0 (3f4d447f6); raw flag renew_completed"`;
   - `run_arm(arm, output, deadline, progress)`: a copy of B02's `run_arm` body that uses
     `master()`, `configuration(arm)` and `OBJECT`; every other line identical (same
     initializer, reset factory, flow, 16 updates, curves, nonfinite check, checkpoint name
     `checkpoint_update16.pt`, four evaluation coordinates, `mean_service_ticks`, status);
   - `paired_result(control, package)`: B02's function with `"object": OBJECT` and
     `"MEI_service_ticks": 24` (copy it; do not import B02's, which names B02).
2. `scripts/run_dish_forecast_package_b03.py`: a copy of the B02 runner with the object
   literal `DISH-FORECAST-PACKAGE-B03`, `--seed` `choices=(73,)`, `default=73`, the B03
   study import, and B03 in the two exception strings. Keep `import resource` at the top
   (Linux route; the Windows collection gap is closed by running the focused check on the
   node, not by stubbing). Keep the 1,800 s allowance law, SIGALRM, the paired publication
   for the `FORECAST_PACKAGE` arm and the identical `summary.json` fields.
3. `test_study_b03.py` (fast, no learner, no development panel):
   - `master().hex()` equals the hex above, and differs from B02's seed-61 master;
   - `configuration("CONTROL")["forecast_package"] is False`,
     `configuration("FORECAST_PACKAGE")["forecast_package"] is True`, both record seed 73,
     the B03 object and the corrected-boundary literal;
   - the B03 `run_arm` and `paired_result` are B03's own objects (module `__module__`
     check) and `paired_result` of two `COMPLETE` hand-written summaries publishes
     `object == "DISH-FORECAST-PACKAGE-B03"`, the four paired differences and their mean;
   - corrected boundary reaches the study path: build the smallest native batch the B02
     tests already build for the corrected-boundary assertion (reuse the fixture pattern of
     `test_renewal_boundary_a02.py`), take `native.observe()`, and assert
     `observation["renew"]` equals `countdown == 0` and `renew_completed` is present, using
     the same `backend.native_batch_from_rows` call the study uses;
   - the runner module's `publish` is exercised only under
     `pytest.importorskip("resource")` (skip on Windows, collected on the node).
4. CM record `DISH_FORECAST_PACKAGE_B03_CM_RECORD_20260906.md`: files with A/D counts,
   the exact local pytest command and verbatim summary, the frozen `wsl_4070` commands
   below, the shared-preparation definition, and what remains unverified.

## Frozen node commands (write them into the CM record verbatim, substituting the sha)

Worktree on the node: `/home/wu/hmasd-worktrees/n3-b03-20260906` at the launch sha;
interpreter `/home/wu/.venvs/hmasd/bin/python`; `PYTHONPATH=/home/wu/hmasd-worktrees/n3-b03-20260906`
(as B02's frozen commands; omitted in the first version of this objective, which made the first
CONTROL attempt fail with `ModuleNotFoundError: experiments` before any learner work, 2026-09-06
17:14Z; attempt 3 uses output root `forecast_package_b03_20260906_r3/`); `OMP_NUM_THREADS=1
MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`; output root
`temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/`.

Shared preparation `C` (timed, one command, task `n3_b03_focused_20260906`):
```
/usr/bin/time -v bash -lc 'cd /home/wu/hmasd-worktrees/n3-b03-20260906 && python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/admission_focused.json && python -m pytest -q -p no:cacheprovider tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02 tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03'
```
`C` is the measured elapsed wall of that command; each arm's `--shared-preparation-seconds`
is `C`.

Arms (tasks `n3_b03_control_20260906`, then `n3_b03_forecast_package_20260906` after the
control summary exists):
```
/usr/bin/timeout --signal=ALRM <1800 - C/2 - 3.4>s bash -lc 'cd /home/wu/hmasd-worktrees/n3-b03-20260906 && python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/admission_control.json && python scripts/run_dish_forecast_package_b03.py run --arm CONTROL --seed 73 --shared-preparation-seconds <C> --admission temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/admission_control.json --out temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906/control'
```
and the same with `--arm FORECAST_PACKAGE`, `admission_forecast_package.json`,
`--out .../forecast_package`, `--control-summary .../control/summary.json`.

## Local checks (Windows, hub interpreter)

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/test/b03-grok tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03 tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a02.py tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a01.py
```
`test_package.py` does not collect on Windows; report that, do not stub `resource`.

## Acceptance

- Diff limited to the owned paths; B02 and r06 bytes unchanged (`git status` shows only
  new files).
- New source ≤ 400 lines total; runner ≤ 200 lines; no new guard, registry, validator,
  retry or telemetry beyond wall/RSS/CPU already in the B02 runner.
- Local pytest green for the B03 tests plus A01/A02; the `resource` skip is reported.
- CM record present with the frozen commands and the A/D table.
