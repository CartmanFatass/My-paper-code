# CM objective — DISH-INIT-WITNESS-A01 thin entry (2026-09-06)

Card: `DISH_INIT_WITNESS_A01_SCIENCE_CARD_20260906.md` (sections 2, 3, 4, 6, 7 bind).
Implementer: Grok Build (CLAUDE.md, Grok Build route), worktree `.claude/worktrees/grok-dish-witness`,
branch `grok/dish-init-witness-a01-20260906`; hub review and pathspec commit. Base: current `main`.

## Objective

Provide a runnable A/RECON entry that, in **one invocation**, reconstructs the B03 seed-73
zero-update state once, evaluates it in the CONTROL (raw-logit) and FORECAST_PACKAGE (sigmoid)
interface views on the four recorded B03 resets with the unchanged `evaluate_episode`, joins the
eight accepted B03 update-16 rows read from the two summaries, and publishes one `summary.json`
with `D_a` per arm. Zero training. Everything scientific is reused by import from
`forecast_package_b02.study`, `forecast_package_b03.study` and the r06 production modules; the new
code is orchestration, publication and tests only.

## Owned paths (create only; nothing else is edited)

- `experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01/__init__.py`
- `experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01/study.py`
- `scripts/run_dish_init_witness_a01.py`
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01/__init__.py` (mirror the
  B03 test package if it has one)
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01/test_study_witness.py`
- `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_INIT_WITNESS_A01_CM_RECORD_20260906.md`

Not edited: `forecast_package_b02/**`, `forecast_package_b03/**`, `first_trigger_source_scout_b01/**`,
every `degraded_incumbent_shadow_handover_rbhr_r06/**` source, existing scripts, tests, cards,
intakes, governance files, and the B03 evidence folder `b03_forecast_package_20260906/` (read only).

## Design (fixed)

1. `init_witness_a01/study.py`:
   - `OBJECT = "DISH-INIT-WITNESS-A01"`; `B03_OBJECT = "DISH-FORECAST-PACKAGE-B03"`; `SEED = 73`;
     `master()` = `hashlib.sha256(f"{B03_OBJECT}/seed/{SEED}".encode("ascii")).digest()` (hex must be
     `b938a93e…543a`); `VIEWS = ("CONTROL", "FORECAST_PACKAGE")`; `EXPECTED_INITIAL_NORM = 38.24996300787587`;
     `B03_ROOT` default `docs/research/candidates/degraded_incumbent_shadow_handover/b03_forecast_package_20260906`;
     `HORIZON = 1200`; `SCALE_TICKS = 24`.
   - imports from `forecast_package_b02.study`: `HOST`, `HARD_EVENTS`, `evaluate_episode`, `new_progress`,
     `check_time`, `parameter_movement` (or the norm helper it uses), and whatever `run_arm` uses to
     obtain the host library and native batches (`load_host`, `native_batch_from_rows`, the
     `EvaluationCoordinate`/`_reset_row` path); from the r06 modules: `build_master_addressed_initial_state`,
     `BatchedRecurrentPolicy`, `RecurrentRolloutState`, `WelfordState` (for the count-0 check).
   - `reconstruct_initial()` → `(bytes, facts)`: one call of
     `build_master_addressed_initial_state(master=master(), block=0, arm="STRUCTURED")`; facts =
     `{"initialization_source": "reconstructed_from_master", "initializer_calls": 1, "initial_model_norm":
     <computed>, "expected_initial_norm": EXPECTED_INITIAL_NORM, "norm_matches": bool, "welford_counts":
     {actor, snapshot, critic}, "helper_constructed_objects": ["model", "optimizer"]}`. A norm mismatch is
     published and sets `status = "INPUT_GAP"`; the run then stops before any episode.
   - `load_b03_rows(root)` → per arm a dict `coordinate_key → row` from
     `<root>/control/summary.json` and `<root>/forecast_package/summary.json` (`evaluation_rows`); assert
     the two arms' `reset` dicts are identical per coordinate and that the four coordinates match B03's
     order; keep the recorded order.
   - `run_witness(output, deadline, progress, b03_root)`: reconstruct once; `library = load_host(HOST)`;
     for `view in VIEWS`: `forecast_package = view == "FORECAST_PACKAGE"`; for each of the four recorded
     resets: `native = native_batch_from_rows((reset,), library=library)`,
     `policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=initial, state=RecurrentRolloutState.fresh("STRUCTURED", width=1), forecast_package=forecast_package)`
     (a fresh policy object per episode is acceptable if that is how `run_arm` obtains fresh recurrent
     state; otherwise reset the state per episode exactly as `run_arm` does; record the construction
     count either way), `record = {"coordinate": …, "view": view, "source": f"new:zero_update:{view}", "reset": reset, …}`,
     `evaluate_episode(native, policy, deadline, progress, record, horizon=HORIZON)`; after each
     episode assert the policy's parameter norm equals the initial norm (publish both). Zero-training
     counters `{"ordinary_training_transitions": 0, "optimizer_steps": 0, "backward_passes": 0,
     "next_label_steps": 0, "passive_label_calls": 0}` are published as literals and the study must not
     import or call `NativePersistentTrainingFlow`, any trainer `update`, or the passive-label interface.
   - `witness_result(new_rows, b03_rows)` → for each arm: `initial_view_mean`, `final_mean` (from the
     reused rows), `rows` = four entries `{coordinate, J_0, J_16, difference, source_new, source_reused}`,
     `D` = mean of the four differences; plus `scale_ticks = 24`, `pattern` = one of
     `"D_C<=-24"`, `"D_C>-24 and D_P<=-24"`, `"both>=+24"`, `"inside_or_heterogeneous"`, `"incomplete"`
     computed per the card's table (descriptive only), and the reused pair's provenance string
     `"B03 Delta = -272.0 from b03_forecast_package_20260906/forecast_package/summary.json paired_primary"`.
   - Published `summary.json` fields: `object`, `configuration` (host, master_hex, seed, block,
     underlying_arm, views, horizon, renewal_boundary string copied from B03, torch_threads 1, native/
     training dtypes), `initialization` facts, `zero_training` counters, `evaluation_rows` (the eight new
     rows with full `evaluate_episode` records), `reused_rows` (the eight B03 rows verbatim with
     `source`), `witness` (the result above), `completed_episodes`, `status` (`COMPLETE` when eight
     episodes finished or terminated legally, `INCOMPLETE` on deadline, `INPUT_GAP` as above),
     `shared_preparation_seconds`, `allowance_seconds`, `prepublication_wall_seconds`, `launch_sha`,
     `admission_receipt`, telemetry (wall, CPU, peak RSS via `resource`), `resources_unmeasured` flag.
2. `scripts/run_dish_init_witness_a01.py`: a copy of `run_dish_forecast_package_b03.py`'s scaffolding
   (argparse, SIGALRM deadline, `git rev-parse HEAD`, telemetry, `publish` with `allow_nan=False` and
   the same non-finite handling) with: single `run` mode (plus `project-cost` printing the tick bound
   9,600 and the cap), `--out`, `--admission` (path recorded), `--shared-preparation-seconds` (float,
   required), `--b03-root` (default above), `--cap-seconds` default `120.0`; allowance =
   `cap − shared_preparation_seconds`; on the alarm, publish whatever rows exist with `status =
   "INCOMPLETE"`. Keep `import resource` at the top (Linux route). No `--arm`, no `--control-summary`.
3. `test_study_witness.py` (fast; no learner; no development panel; no host library):
   - `master().hex()` equals `b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a`;
   - determinism: two calls of `build_master_addressed_initial_state(master=master(), block=0, arm="STRUCTURED")`
     return byte-equal payloads, the loaded `model` state dicts are tensor-equal, all three Welford
     counts are 0, `update == 0`, and the parameter norm equals `EXPECTED_INITIAL_NORM` within 1e-9;
   - recorded-reset round trip: for each of the four rows of `b03_forecast_package_20260906/control/summary.json`,
     the recorded `reset` equals the `_reset_row` (or equivalent) recomputed from the master and the
     row's coordinate, and equals the package summary's reset for the same coordinate;
   - two views on one head: a `BatchedRecurrentPolicy` built from the initializer bytes with
     `forecast_package=False` and one with `True` produce `service_q` outputs where the second equals
     `torch.sigmoid` of the first on the same synthetic hidden input (reuse the pattern of
     `forecast_package_b02/test_package.py::test_genuine_policy_link_and_default_graph` without importing
     the B02 runner), and both report actor Welford count 0;
   - `witness_result` on synthetic rows: means, differences, `D`, `pattern` for each of the five
     table rows, `source` strings; `INCOMPLETE` handling when fewer than four new rows exist for a view.
   - Do not import `scripts.run_dish_*` in the tests (module-level `import resource` does not collect on
     Windows); test `publish` non-finite handling only if the function lives in the study.
4. Budgets: new source ≤ 2,000 lines; runner ≤ 600; no registry, retry, lease, validator, tamper
   evidence, profiler or repeated smoke.

## Frozen node commands (for the operator; not run by the implementer)

`WT=/home/wu/hmasd-worktrees/dish-witness-<sha7>`, `PY=/home/wu/.venvs/hmasd/bin/python`,
`export PYTHONPATH="$WT"`, `ROOT=$WT/temp/directions/degraded_incumbent_shadow_handover/exp/init_witness_a01_20260906`,
single-thread exports as B03. (1) focused check, timed:
`/usr/bin/time -v -o $ROOT/focused.time $PY -m pytest -q -p no:cacheprovider tests/experiments/candidates/degraded_incumbent_shadow_handover/init_witness_a01`
→ `C` = its elapsed wall. (2) formal run:
`$PY scripts/hmasd_resource_preflight.py admit-memory --out $ROOT/receipts/witness.json && /usr/bin/timeout --signal=ALRM 118s /usr/bin/time -v -o $ROOT/witness.time $PY scripts/run_dish_init_witness_a01.py run --out $ROOT/witness --admission $ROOT/receipts/witness.json --shared-preparation-seconds <C>`.
The whole item (C plus the formal wall) is charged against 120 s.

## Report format (CM record)

Files with A/D counts; the exact imports reused; how fresh recurrent state per episode is obtained
(copy of `run_arm`'s way); the initializer facts observed in the tests; local pytest command and
verbatim summary (Windows: the witness tests collect; note anything skipped); line counts; what
remains unverified (node build, actual episode walls, the formal run).
