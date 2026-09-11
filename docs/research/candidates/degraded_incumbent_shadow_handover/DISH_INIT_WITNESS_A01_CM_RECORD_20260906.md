# DISH-INIT-WITNESS-A01 CM record (2026-09-06)

Worktree `C:/Projects/HMASD/.claude/worktrees/grok-dish-witness`, branch
`grok/dish-init-witness-a01-20260906`. Grok Build implemented the thin A01 entry;
Git commit/push is the hub's pathspec step (this session ran no git commands that
change state). Scope §4: none. Launch sha `<sha>` (hub fills at launch).

## Files created (A/D)

All owned paths are new files (D=0). B03 test package has no `__init__.py`; none
was created under the A01 test directory.

| Path | A | D | Role |
| --- | ---: | ---: | --- |
| `experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01/__init__.py` | 1 | 0 | package marker |
| `experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01/study.py` | 224 | 0 | reconstruct, load B03 rows, two-view evaluation, `witness_result` |
| `scripts/run_dish_init_witness_a01.py` | 102 | 0 | A01 runner (`import resource` kept; no `--arm` / `--control-summary`) |
| `tests/experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01/test_study_witness.py` | 170 | 0 | master / initializer / reset round trip / two views / `witness_result` |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_INIT_WITNESS_A01_CM_RECORD_20260906.md` | 116 | 0 | this record |

Non-test source A=327, D=0, runner 102. Budget: source ≤ 2,000, runner ≤ 600.

## Imports reused (not copied)

From `forecast_package_b02.study`: `HOST`, `HARD_EVENTS`, `evaluate_episode`,
`new_progress`, `check_time`, `backend` (`native_batch_from_rows`),
`EvaluationCoordinate`, `load_host`, `_reset_row`. Local `model_norm` is the same
sum-of-squares helper B03 uses for `initial_model_norm` / `parameter_movement`.
From r06 `production_recurrent_trainer`: `build_master_addressed_initial_state`,
`BatchedRecurrentPolicy`, `RecurrentRolloutState`. From r06
`production_training_engine`: `WelfordState` (count-0 check). B03 constants
copied: object string, seed 73, master ASCII, `EXPECTED_INITIAL_NORM`,
`RENEWAL_BOUNDARY`, coordinate order. The study does not import or call
`NativePersistentTrainingFlow`, any trainer `update`, or the passive-label
interface. B02, B03 and r06 source bytes were not edited.

## Fresh recurrent state per episode

Copy of `forecast_package_b02.study.run_arm` / B03 `run_arm`: a new
`RecurrentRolloutState.fresh("STRUCTURED", width=1)` and a new
`BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=initial, state=state,
forecast_package=package)` per episode. Construction count is recorded
(`policy_constructions` / `checkpoint_loads`; eight when all episodes run). The
card's "one policy object per view" is satisfied by the same bytes and flag;
fresh objects are how `run_arm` obtains fresh recurrent state.

## Initializer facts observed in the tests

`reconstruct_initial()` / two `build_master_addressed_initial_state(master=master(),
block=0, arm="STRUCTURED")` calls on this host:

- `master().hex()` = `b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a`
- two payloads byte-equal; loaded `model` state dicts tensor-equal (`rtol=0, atol=0`)
- `update == 0`; Welford `actor` / `snapshot` / `critic` counts all 0 (`WelfordState`)
- `initial_model_norm` = `38.24996300787587` = `EXPECTED_INITIAL_NORM`; `norm_matches` true (1e-9)
- `initialization_source` = `reconstructed_from_master`; `initializer_calls` = 1 per call
- `helper_constructed_objects` = `["model", "optimizer"]`
- recorded B03 `reset` dicts equal `_reset_row(master(), EvaluationCoordinate(...))` and equal across the two summaries
- `BatchedRecurrentPolicy` from those bytes: `forecast_package=True` `service_q` equals `torch.sigmoid` of the False view on the same synthetic hidden; actor Welford count 0 after construction and after `step_rows`

The r06 C++ RNG backend is used by the initializer (`rng_words_native`); the A03
host library (`load_host`) is not. No test imported `scripts.run_dish_*`.

## Local pytest (Windows, hub interpreter)

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/test/witness-grok tests/experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01
```

Verbatim summary: `5 passed, 1 warning in 9.00s`.

Nothing skipped. The warning is pytest `cache_dir` under `-p no:cacheprovider`.
The five tests collect and run on Windows without the A03 host library and
without importing the runner (`resource`).

## Frozen `wsl_4070` commands (launch sha `<sha>`; not run by the implementer)

`WT=/home/wu/hmasd-worktrees/dish-witness-<sha7>`, `PY=/home/wu/.venvs/hmasd/bin/python`,
`export PYTHONPATH="$WT"`, `ROOT=$WT/temp/directions/degraded_incumbent_shadow_handover/exp/init_witness_a01_20260906`,
single-thread exports as B03.

Focused check, timed (`C` = elapsed wall):

```
/usr/bin/time -v -o $ROOT/focused.time $PY -m pytest -q -p no:cacheprovider tests/experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01
```

Formal run (allowance = `120 − C`; the objective writes a 118 s timeout as the
operator bound):

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out $ROOT/receipts/witness.json && /usr/bin/timeout --signal=ALRM 118s /usr/bin/time -v -o $ROOT/witness.time $PY scripts/run_dish_init_witness_a01.py run --out $ROOT/witness --admission $ROOT/receipts/witness.json --shared-preparation-seconds <C>
```

The whole item (`C` plus the formal wall) is charged against 120 s.

## Cost projection (runner law; not a launch)

`project-cost`: law `2 views x 4 conditions x <= 1200 ticks`;
`evaluation_ticks_upper=9600`; `initializer_calls=1`; `optimizer_steps=0`;
`ordinary_training_transitions=0`; `whole_item_cap_seconds=120.0`;
`projected_wall_seconds=None`;
`projection_status=spend choice; no per-episode evaluation wall in B02/B03 records`.
The runner was not executed (Windows has no `resource`; no evaluation launched).

## Unverified

- Node focused check (shared preparation `C`), including native build or cache
  load of the A03 host library used only by the formal `run_witness` path.
- The eight episode walls, RSS, CPU, reconstructed-init identity against the
  unpublished B03 start, and `summary.json` on `wsl_4070` at `<sha>`.
- Runner `SIGALRM` / `publish` / `resource` telemetry (Linux-only; tests do not
  import the runner).
- Numeric fill-in of `<C>` and the 118 s timeout after `C` is measured.

scope: none
