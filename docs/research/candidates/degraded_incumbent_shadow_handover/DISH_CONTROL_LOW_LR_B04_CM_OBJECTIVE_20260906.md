# CM objective — DISH-CONTROL-LOW-LR-B04 thin entry (2026-09-06)

Card: `DISH_CONTROL_LOW_LR_B04_SCIENCE_CARD_20260906.md` (sections 2, 3, 4, 6, 7 bind).
Implementer: Grok Build (CLAUDE.md Grok Build route), worktree `.claude/worktrees/grok-dish-b04`,
branch `grok/dish-control-low-lr-b04-20260906`; hub review and pathspec commit. Base: current
`main` (contains `forecast_package_b03/`, `init_witness_a01/` and the r06 modules unchanged).

## Objective

Provide a runnable B04 entry that trains the inherited CONTROL learner (`forecast_package=False`)
in two arms differing only in the AdamW learning rate (`CONTROL` 3e-4, `LOW_LR` 3e-5, applied to
**both** original parameter groups for all sixteen updates), on one new paired seed 89, with a
four-row zero-update reference of the same initialization on the raw interface, the four seed-89
evaluation resets recorded and shared, and a paired publication of `Delta_LR`, `D_CONTROL_new`
and `D_LOW_LR_new`. Everything else (host, initializer, training flow, exposure, evaluation,
publication fields, cap law) is B03's, reused by import.

## Owned paths (create only; nothing else is edited)

- `experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/__init__.py`
- `experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/study.py`
- `scripts/run_dish_control_low_lr_b04.py`
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/__init__.py`
  (mirror the B03 test package)
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/test_study_b04.py`
- `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_CONTROL_LOW_LR_B04_CM_RECORD_20260906.md`

Not edited: `forecast_package_b02/**`, `forecast_package_b03/**`, `init_witness_a01/**`, every
`degraded_incumbent_shadow_handover_rbhr_r06/**` source, existing scripts and tests, cards,
intakes, governance files.

## Engineering facts that fix the design (verified by the hub, 2026-09-06)

- The optimizer that steps is a local of `run_full_4096_dry_update`
  (`production_training_engine.py:524-530`), rebuilt with `lr=3e-4` at every update and then, when
  `resume_checkpoint_bytes` is given, overwritten by `optimizer.load_state_dict(restored_input["optimizer"])`
  (`:533-536`). `PersistentTrainer.run_update` always passes its current `checkpoint_bytes`
  (`production_training.py:71-81`), and `NativePersistentTrainingFlow` requires the initial bytes
  (`production_recurrent_trainer.py:399-400`), so the restore fires at every one of the sixteen
  updates, starting from the initializer payload. The optimizer state is written back right after
  the step (`production_training_engine.py:640`), and `optimizer.step()` never changes `lr`.
- Consequently the learning rate in effect for the whole chain is whatever `param_groups[i]["lr"]`
  the **initializer payload's** optimizer state carries. No live optimizer is reachable from a
  study; no `lr` keyword exists on the flow, trainer or `run_arm`.
- The two groups are built identically at both sites (`production_recurrent_trainer.py:218-224`,
  `production_training_engine.py:524-530`): group 0 matrix weights (weight decay 1e-4), group 1
  everything else including biases, `log_std` and the `flex_*` layers (weight decay 0.0). Both must
  be rewritten; a single-group edit is a silent partial violation.
- B03's `configuration()["learning_rate"]` is a literal; B04's must be derived from the same value
  that is written into the payload.
- The witness entry (`init_witness_a01/study.py`) already shows the zero-update raw-interface
  evaluation pattern (`BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=initial, state=RecurrentRolloutState.fresh("STRUCTURED", width=1), forecast_package=False)` + `evaluate_episode`).
- The cone sparse checkout on `wsl_4070` omits `docs/`; B04 reads nothing under `docs/`, so no
  staging is needed (the shared folder lives under `temp/`).

## Design (fixed)

1. `control_low_lr_b04/study.py` imports from `forecast_package_b02.study` and
   `forecast_package_b03.study` what it reuses (`HOST`, `HARD_EVENTS`, `planned_cost`,
   `new_progress`, `check_time`, `TrainingMeasurements`, `parameter_movement`, `evaluate_episode`,
   `exposure`, `backend`, `EvaluationCoordinate`, `load_host`, `_reset_row`, and the r06 imports
   B03 uses), and defines:
   - `OBJECT = "DISH-CONTROL-LOW-LR-B04"`, `SEED = 89`, `ARMS = ("CONTROL", "LOW_LR")`,
     `LEARNING_RATES = {"CONTROL": 3e-4, "LOW_LR": 3e-5}`, `SCALE_TICKS = 24`,
     `RENEWAL_BOUNDARY` (B03's literal);
   - `master()` = `hashlib.sha256(f"{OBJECT}/seed/{SEED}".encode("ascii")).digest()` (hex
     `665c8d879ef9d289d4ad6d4d3bf051643d9f17bb05c97521566dc48a77071c9d`);
   - `set_learning_rate(payload: bytes, lr: float) -> bytes`: `torch.load` the payload
     (`weights_only=False`), set `group["lr"] = lr` for **every** entry of
     `loaded["optimizer"]["param_groups"]` and nothing else, `torch.save` back to bytes; raise if
     the group count is not 2;
   - `learning_rates(checkpoint: bytes) -> list[float]`: the `lr` of every param group of the
     checkpoint's optimizer state (`torch.load`, read-only);
   - `coordinates()` = the four `EvaluationCoordinate(0, regime, schedule, "SPEED_4", 0)` in B03
     order; `recorded_resets(master)` = `{coordinate.canonical_key(): _reset_row(master, coordinate)}`;
   - `configuration(arm)`: B03's dictionary with `"object": OBJECT`, `"seed": 89`, `"master_hex"`,
     `"arm": arm`, `"underlying_arm": "STRUCTURED"`, `"forecast_package": False`,
     `"learning_rate": LEARNING_RATES[arm]`, `"learning_rate_mechanism": "initializer payload optimizer param_groups[*].lr rewritten before training; engine restores optimizer state at every update"`,
     `"renewal_boundary": RENEWAL_BOUNDARY`, `"scale_ticks": 24`; the two arms' dictionaries
     differ only in `arm` and `learning_rate` (test);
   - `prepare_shared(output, deadline, progress)`: `torch.set_num_threads(1)`; `load_host`; **one**
     `build_master_addressed_initial_state(master(), block=0, arm="STRUCTURED")` call, saved as
     `output / "initial_state.pt"`; record `initializer_calls`, the parameter L2 norm
     (`initial_model_norm`), the three Welford counts (must be 0), `learning_rates(initial)` (both
     3e-4 as constructed); `recorded_resets` written to `output / "resets.json"`; then the
     zero-update reference: for each coordinate, `native_batch_from_rows((row,), library)`,
     fresh `RecurrentRolloutState`, `BatchedRecurrentPolicy(..., checkpoint_bytes=initial, forecast_package=False)`,
     `evaluate_episode` into `progress["reference_rows"]` with
     `source = "new:zero_update:raw"`; `reference_mean_service_ticks`; zero-training counters
     asserted; parameter norm before and after equal; `status = "COMPLETE"`;
   - `run_arm(arm, output, deadline, progress, shared)`: B03's `run_arm` body with these changes:
     read `shared / "initial_state.pt"` (no initializer call); `initial = set_learning_rate(bytes, LEARNING_RATES[arm])`;
     record `initial_model_norm` (must equal the shared value; test) and
     `configuration(arm)`; `forecast_package=False` in the flow and in every policy; after each
     `apply_update`, append to the curve entry `"learning_rates": learning_rates(flow.trainer.checkpoint_bytes)`
     and raise `RuntimeError("B04 learning rate drift")` if any entry differs from
     `LEARNING_RATES[arm]`; evaluate the four coordinates using the rows loaded from
     `shared / "resets.json"` after asserting each equals `_reset_row(master(), coordinate)`;
     each evaluation row records `source = f"new:{arm}:update16"`; checkpoint name
     `checkpoint_update16.pt`; everything else identical (curves fields, nonfinite check,
     `parameter_movement`, `mean_service_ticks`, `status`);
   - `paired_result(control, low_lr, reference)`: `object`, `seed`, `scale_ticks: 24`,
     `reference_mean`, `control_mean`, `low_lr_mean`, `delta_lr` (mean of `low_lr − control` over
     the four coordinates), `d_control_new`, `d_low_lr_new`, `rows` (one entry per coordinate with
     the three service values, the three sources, `low_lr_minus_control`, `control_minus_reference`,
     `low_lr_minus_reference`), joined **by coordinate key**, raising on a missing coordinate or a
     non-`COMPLETE` input.
2. `scripts/run_dish_control_low_lr_b04.py`: copy of the B03 runner shape with modes
   `shared`, `run`, `project-cost`:
   - `shared --admission <receipt> --out <shared dir>`: runs `prepare_shared`, publishes
     `summary.json` with wall (`prepublication_wall_seconds`), CPU and RSS as the B03 runner
     records them; no allowance argument (the operator's `/usr/bin/time` and the reported wall
     give `S`);
   - `run --arm {CONTROL,LOW_LR} --seed 89 --shared <shared dir> --shared-preparation-seconds <S> --admission <receipt> --out <arm dir> [--control-summary <control/summary.json>]`:
     allowance `1800 − S/2`, SIGALRM, the B03 status/charged-wall law unchanged, `S` here is the
     whole shared item (focused check + shared preparation) as the operator measures it; the
     `LOW_LR` arm with `--control-summary` also publishes `paired.json` from
     `paired_result(control, low_lr, shared summary)`;
   - keep `import resource` at top (Linux route); runner ≤ 200 lines.
3. `test_study_b04.py` (fast, no learner run, no native host, no development panel):
   - master hex equals the value above and differs from B03's seed-73 master;
   - `set_learning_rate` on a real initializer payload (call
     `build_master_addressed_initial_state` once with the B04 master) rewrites `lr` in both groups
     to 3e-5 and leaves `betas`, `eps`, `weight_decay`, the model state and the Welford states
     byte-identical; `learning_rates` reads back `[3e-5, 3e-5]`; with 3e-4 it reads `[3e-4, 3e-4]`;
   - **chained engine updates carry the rate**: `first = run_full_4096_dry_update(arm="STRUCTURED", resume_checkpoint_bytes=set_learning_rate(payload, 3e-5), forecast_package=False)`,
     `second = run_full_4096_dry_update(..., resume_checkpoint_bytes=first["private_checkpoint_bytes"], ...)`;
     `learning_rates(first["private_checkpoint_bytes"]) == [3e-5, 3e-5]` and the same for `second`;
     `second["update"] == 2`; and the model state actually moved less than the 3e-4 chain from the
     same payload over one update (compare L2 displacement of the two one-update results; a strict
     inequality, no ratio claim);
   - `configuration("CONTROL")` and `configuration("LOW_LR")` differ only in `arm` and
     `learning_rate`; `forecast_package is False` in both; `learning_rate` equals
     `learning_rates(set_learning_rate(payload, LEARNING_RATES[arm]))[0]`;
   - `recorded_resets` round-trip: each recorded row equals `_reset_row(master(), coordinate)`
     after a JSON round-trip; four keys in B03 order;
   - `paired_result` on three hand-written `COMPLETE` summaries publishes the object, the three
     means, `delta_lr`, `d_control_new`, `d_low_lr_new` and four rows with the right sources, and
     raises on a missing coordinate;
   - the runner module's `publish` is exercised only under `pytest.importorskip("resource")`.
4. CM record `DISH_CONTROL_LOW_LR_B04_CM_RECORD_20260906.md`: files with A/D counts, the exact
   local pytest command and verbatim summary, the frozen `wsl_4070` commands below, the
   shared-item definition, the cost range from B03/witness timings (references, not projections),
   and what remains unverified.

## Frozen node commands (write them into the CM record verbatim, substituting the sha)

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
and the same with `--arm LOW_LR`, `admission_low_lr.json`, `--out .../low_lr`,
`--control-summary .../control/summary.json`.

## Local checks (Windows, hub interpreter)

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/test/b04-grok tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04 tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b03 tests/experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01
```
`test_package.py` does not collect on Windows; report that, do not stub `resource`.

## Acceptance

- Diff limited to the owned paths; B02, B03, witness and r06 bytes unchanged (`git status`
  shows only new files).
- New source ≤ 450 lines total; runner ≤ 200 lines; no new guard, registry, validator, retry,
  resume or telemetry beyond wall/RSS/CPU already in the B03 runner; the learning-rate drift
  `RuntimeError` and the reset-equality assertion are the card's acceptance checks, not guards.
- Local pytest green for the B04 tests plus B03 and witness tests; the `resource` skip reported.
- CM record present with the frozen commands, the A/D table and the cost range.
