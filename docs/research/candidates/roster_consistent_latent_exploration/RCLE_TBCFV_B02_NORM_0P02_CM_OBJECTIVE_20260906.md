# CM objective — RCLE-TBCFV-B02-NORM-0p02 thin entry (2026-09-06)

Card: `RCLE_TBCFV_B02_NORM_0P02_SCIENCE_CARD_20260906.md` (sections 2–4, 6, 7 bind).
Implementer: Grok Build (CLAUDE.md Grok Build route), worktree `.claude/worktrees/grok-rcle-b02`,
branch `grok/rcle-tbcfv-b02-20260906`; hub review and pathspec commit. Base: current `main`
(contains the B01 entry, its POSIX native branch and the review-round-1 fixes).

## Objective

Make the outcome-informed B02 runnable: the B01 two-arm, single-seed comparison unchanged in
host, arms, initialization law, loss, baselines, exposure and endpoints, but (1) with the
full-vector fixed-norm step **0.02** per nonzero joint update in both arms, realised by the new
entry's own parameterised step function (not the registered 0.0005 one); (2) under the new
object id and seed 18; (3) with a shared update-0 evaluation of the C1P1 initialization on the
held-out panel inside the C1P1 invocation; (4) with the primary `ΔU` on the two active paths and
the companion `G_U` per arm; (5) the INDEPENDENT-NEAREST reference on the seed-18 panel; (6) a
600 s per-arm / 1,500 s object cap; (7) focused tests and a CM record with frozen node commands.

## Engineering facts that fix the design (verified by the hub, 2026-09-06)

- `registered_plain_sgd_step(model)` (`roster_consistent_latent_exploration_tbcfv/models.py:374-398`)
  has no norm argument: it reads `LEARNING_RATE` and `GRADIENT_DIRECTION_SCALE` bound at import
  (`models.py:12-23`) and returns `parameter_delta_norm=NONZERO_UPDATE_NORM` (a constant).
  `apply_registered_block_update` (`models.py:408-425`) calls it after `_validated_block_cells`
  and before the `BASELINE_DECAY` baseline update. B01's `execute_b01_training_update`
  (`_tbcfv_b01/study.py:386-450`) publishes `audit.parameter_update.parameter_delta_norm` into
  every curve and `NONZERO_UPDATE_NORM` into `configuration["nonzero_update_norm"]`
  (`study.py:750`). **Reusing either registered function silently keeps 0.0005.** Monkeypatching
  a constant is forbidden (and would not reach the names already bound in `models.py`).
- Seed law (`_tbcfv_b01/study.py:96-103`): `seed_root_key(ascii)` = SHA256; `block_digest_hex(key,
  identity, index)` = `_derive_block_digest`. For B02: ASCII `RCLE-TBCFV-B02-NORM-0p02/seed/18`,
  root hex `fd3cd5cf0f085e880a424f7a546017a62d300676e385e1174676b9f4c14e5093`, identity
  `RCLE-TBCFV-B02-NORM-0p02`, index 0, block digest
  `82593ad701533212112f1e29d22f3d0b701fd8360b88d9bfcb61ac565f6b2210` (computed by the hub with the
  existing functions; assert both in tests).
- The physical / fixture / event materialisation of a held-out scenario depends on key, block,
  cell and index only (no arm), so the initialization panel, both finals and the reference share
  scenarios by `(cell, index)`.
- B01's `evaluate_learned(model, arm, rng, eval_episodes, started, wall_cap)` (`study.py:453-485`)
  evaluates any model on the eight held-out cells; called on the freshly initialised C1P1 model
  before any update it gives the shared update-0 panel. `initialize_b01_models` (via
  `initialize_block_models`) allocates five package models and B01 restricts to two; record this.
- `publish_paired_primary` (`study.py:568-625`) already computes per-path `difference_U_flex_minus_c1p1`
  and `paired_U_se` but aggregates only `delta_tau_b01`; B02 needs its own aggregate.
- Runner `scripts/run_rcle_tbcfv_b01.py`: modes `build`, `executability`, `arm`, `reference`;
  SIGALRM in the `arm` branch (`ArmWallExpired` caught in `run_arm`, partial `TRAINED_UNEVALUATED`
  / `TECHNICAL_STOP` summaries); the memory preflight is external in the `&&` chain. No
  `--shared-preparation-seconds` exists in this direction; shared items are charged in the launch
  ledger by the operator, as in B01.

## Owned paths (create only; nothing else is edited)

- `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/__init__.py`
- `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/study.py`
- `scripts/run_rcle_tbcfv_b02.py` (≤ 600 lines)
- `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/__init__.py`
  (mirror the B01 test package if it has one)
- `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/test_b02.py`
- `docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B02_NORM_0P02_CM_RECORD_20260906.md`

Not edited: `roster_consistent_latent_exploration_tbcfv/**`, `roster_consistent_latent_exploration_tbcfv_b01/**`,
`scripts/run_rcle_tbcfv_b01.py`, existing tests, cards, intakes, governance files. No
`executability.py` for B02: the node build and executability were established by B01 and the
arms validate the native build through their own `native` block; the Linux oracle tests remain
the focused portability check.

## Design (fixed)

1. `_tbcfv_b02/study.py` imports from `_tbcfv_b01.study` every pure function it reuses
   (`seed_root_key`, `block_digest_hex`, `make_semantic_rng`-shape, `initialize_b01_models`,
   `restrict_two_arms`, `flat_parameters`, `evaluate_learned`, `evaluate_scripted`, `scenario_row`,
   `cell_endpoint_means`, `eight_cell_mean`, `paired_difference_se`, `se_of_mean_of_independent_ses`,
   `heldout_batches`, `load_and_validate_control_summary` / `validate_control_summary`,
   `ArmWallExpired`, `peak_rss_bytes`, `process_cpu_seconds`, `_mean`, `_group`, the cell
   constants) and from the TBCFV tree `exact_advantage_loss`, `_validated_block_cells`,
   `BASELINE_DECAY`, `TRAIN_EPISODES_PER_BLOCK`, `TRAIN_CELLS`, `REGISTERED`, `ParameterUpdateAudit`,
   `BlockUpdateAudit`, `TBCFVModel`, `execute_learned_batch`, `EpisodeCoordinate`, and defines:
   - `OBJECT_ID = IDENTITY = "RCLE-TBCFV-B02-NORM-0p02"`, `SEED = 18`,
     `SEED_KEY_ASCII = f"{OBJECT_ID}/seed/{SEED}"`, `BLOCK_INDEX = 0`, `NONZERO_UPDATE_NORM_B02 = 0.02`,
     `PREVIOUS_NONZERO_UPDATE_NORM = 0.0005` (recorded as selection history only),
     `MEI_U = 0.05`, `MEI_TAU_TICKS = 4`;
   - `make_b02_semantic_rng()`: B01's `make_semantic_rng` shape with the B02 key and identity
     (own copy if B01's hard-codes its constants; import if it takes them as arguments);
   - `fixed_norm_sgd_step(model, nonzero_update_norm) -> ParameterUpdateAudit`: a copy of
     `registered_plain_sgd_step` with `multiplier = -nonzero_update_norm / raw_norm`, the same
     26,161-scalar surface check, `raw_gradient_norm` from the same float64 reduction, and, after
     the in-place update, the **measured** L2 norm of the applied delta (compute the delta as
     `multiplier * grad` per parameter in float64 and reduce; no extra pass over the model), returned
     as `parameter_delta_norm=nonzero_update_norm` plus a module-level dataclass or a dict field
     `measured_parameter_delta_norm` (extend by wrapping: return a small `B02StepAudit(audit,
     measured_parameter_delta_norm)` rather than changing the imported dataclass); zero gradient
     → no update, both norms 0.0, `nonzero=False`;
   - `apply_b02_block_update(model, baselines, returns, cell_indices, nonzero_update_norm)`: a copy
     of `apply_registered_block_update` calling `fixed_norm_sgd_step` before the identical
     0.95/0.05 baseline update (event order preserved and recorded);
   - `execute_b02_training_update(...)`: B01's `execute_b01_training_update` body calling
     `apply_b02_block_update(..., NONZERO_UPDATE_NORM_B02)`; the curve entry carries
     `parameter_delta_norm` (= 0.02 when nonzero), `measured_parameter_delta_norm`,
     `raw_gradient_norm`, `nonzero`, `event_order`, `Y_mean`, `per_cell` as in B01;
   - `initialization_panel(model, rng, eval_episodes, started, wall_cap)`: `evaluate_learned` on
     the C1P1 model before any update; rows tagged `arm = "C1P1-INIT"`, `source = "new:init:update0"`;
     returns rows plus `cell_endpoint_means` and the two-path U means;
   - `run_arm(*, arm, out, updates, eval_episodes, wall_cap, admission_receipt, launch_sha,
     control_summary=None)`: B01's `run_arm` body with the B02 constants and functions; for
     `C1P1`, the initialization panel runs right after `initialize_b01_models` and the identical-
     initial-tensor check and before the update loop, and its rows are written to
     `out / "init_scenarios.json"` and summarised in `summary["initialization_panel"]`; for `FLEX`,
     `load_and_validate_control_summary` (same object, seed 18, block digest, updates, episodes)
     and the control summary's `initialization_panel` is required; `summary["configuration"]`
     records `nonzero_update_norm: 0.02`, `previous_nonzero_update_norm: 0.0005`,
     `step_law: "theta <- theta - 0.02 * g / ||g||_2 if g != 0 else no update"`,
     `selection_history: "0.0005 (B01, seed 17) -> 0.02 (B02, seed 18) after B01 intake"`,
     `initial_parameter_norm_reference_b01: 21.186038495201018`, `path_bound: 4.0`, and the B01
     fields; `summary["allocations"]` records the five allocated package models versus the two
     training instances; everything else (curves, display points, `TRAINED_UNEVALUATED` partial,
     final `parameters.pt`, per-scenario rows, native block, wall/RSS/CPU) as B01;
   - `publish_b02_primary(init_rows, treatment_rows, flex_rows)`: B01's `publish_paired_primary`
     per-path fields plus, per path, `init_U_mean`, `G_U_c1p1 = init_U − c1p1_U`,
     `G_U_flex = init_U − flex_U`; aggregates `delta_U_b02` (mean over the two paths of
     `difference_U_flex_minus_c1p1`), `delta_U_b02_se` (from the paired U SEs by
     `se_of_mean_of_independent_ses`), `G_U_c1p1`, `G_U_flex` (two-path means), `delta_tau_b02`
     and its SE (companion), `MEI_U`, `MEI_tau_ticks`, the eight-cell tables for init, C1P1 and
     FLEX, and a `sources` map (`init` → `new:init:update0`, arms → `new:<arm>:update200`,
     reference → `new:INDEPENDENT-NEAREST:seed18`); wrapped by a `_or_error` variant like B01's;
     the FLEX arm publishes it;
   - `run_reference(...)`: B01's with the B02 key/identity, rows tagged with the reference source.
2. `scripts/run_rcle_tbcfv_b02.py`: copy of the B01 runner shape with modes `build`, `arm`,
   `reference` (no `executability`); the thread-env guard before `import torch`; `arm`
   `--wall-cap` default **580** (in-process; the external `timeout --signal=ALRM 600s` is the
   600 s bound); `--updates 200`, `--eval-episodes 256`, `--admission-receipt`, `--launch-sha`,
   `--control-summary` for FLEX; the B02 study import; ≤ 600 lines.
3. `test_b02.py` (fast; Windows MSVC native path as B01's tests):
   - root key and block digest equal the hex values above and differ from B01's;
   - `fixed_norm_sgd_step` on a model with a synthetic nonzero gradient: the applied delta's L2
     norm equals 0.02 within 1e-9 (compute the delta from parameters before/after), the audit's
     `parameter_delta_norm == 0.02` and `measured_parameter_delta_norm ≈ 0.02`; with zero gradient
     no parameter changes and `nonzero is False`; with a different norm argument (e.g. 0.0005) the
     delta norm follows the argument (the function is parameterised, not constant);
   - `apply_b02_block_update` updates parameters before baselines and returns the 0.95/0.05
     baselines (mirror B01's test);
   - FLEX heads start at zero and are trainable while C1P1 masks them (reuse B01's test body);
   - `publish_b02_primary` on hand-written init / C1P1 / FLEX tables: `delta_U_b02`, both `G_U`,
     per-path fields, the SE combination, the sources map; error on mismatched indices;
   - `configuration` literal fields (`nonzero_update_norm` 0.02, history, step law);
   - the two-update tiny executability test from B01 (`test_two_update_and_tiny_executability_if_native_builds`)
     rewritten for B02: after one B02 training update the curve's `parameter_delta_norm` is 0.02
     (or 0.0 if the gradient is zero) and `measured_parameter_delta_norm` agrees.
4. CM record `RCLE_TBCFV_B02_NORM_0P02_CM_RECORD_20260906.md`: files with A/D counts, functions
   reused by import versus copied (and why each copy exists), the step-function diff against
   `registered_plain_sgd_step`, the derived hex values, the local pytest command and verbatim
   summary, the frozen node commands below, the cost references, and what remains unverified.

## Frozen node commands (write them into the CM record verbatim)

```
WT=/home/wu/hmasd-worktrees/rcle-b02-<sha7>
ROOT=$WT/temp/directions/roster_consistent_latent_exploration/exp/tbcfv_b02_20260906
PY=/home/wu/.venvs/hmasd/bin/python
export PYTHONPATH="$WT"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PATH="/home/wu/.venvs/hmasd/bin:$PATH"
cd "$WT"
mkdir -p "$ROOT/receipts" "$ROOT/timings" "$ROOT/build" "$ROOT/c1p1" "$ROOT/flex" "$ROOT/reference"
```
(1) build (charged once if actually paid): as B01 (1) with `run_rcle_tbcfv_b02.py build --build-root "$ROOT/build"`.
(2) focused check: as B01 (2) with `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02` in place of the B01 tests (the oracle test file kept).
(3) arm C1P1:
```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/c1p1.json" && \
/usr/bin/timeout --signal=ALRM 600s \
/usr/bin/time -v -o "$ROOT/timings/c1p1.time" \
$PY scripts/run_rcle_tbcfv_b02.py arm --arm C1P1 \
  --out "$ROOT/c1p1" --wall-cap 580 \
  --admission-receipt "$ROOT/receipts/c1p1.json" \
  --launch-sha <sha> --updates 200 --eval-episodes 256
```
(4) arm FLEX: the same with `--arm FLEX`, `receipts/flex.json`, `timings/flex.time`,
`--out "$ROOT/flex"`, `--control-summary "$ROOT/c1p1/summary.json"`.
(5) reference: as B01 (6) with the B02 runner and `--out "$ROOT/reference"`.
Hub check before (3): if (1)+(2) plus a credible projection of (3)+(4)+(5) exceeds 1,500 s, the
object is not launched (a range problem is returned, not a reduction).

## Local checks (Windows, hub interpreter)

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/roster_consistent_latent_exploration/test/b02-grok tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02 tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01
```

## Acceptance

- Diff limited to the owned paths; TBCFV tree, B01 entry and B01 runner bytes unchanged.
- New non-test source ≤ 1,200 lines; runner ≤ 600; no new guard, registry, validator, retry,
  resume or telemetry beyond wall/RSS/CPU already in B01; the measured delta norm is one
  reduction per update, not a framework.
- No import or call of `registered_plain_sgd_step` / `apply_registered_block_update` /
  `execute_b01_training_update` anywhere in the B02 entry (grep in the CM record); no constant
  patching.
- Local pytest green for the B02 and B01 tests; the CM record present with the frozen commands,
  the A/D table, the reuse/copy table and the derived hex values.
