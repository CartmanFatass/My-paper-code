# CM record — RCLE-TBCFV-B02-NORM-0p02 thin entry (2026-09-06)

Implementer: Grok Build (grok-4.6). Worktree `.claude/worktrees/grok-rcle-b02`,
branch `grok/rcle-tbcfv-b02-20260906`. No git commands that change state were
run. No training, evaluation, or result-bearing invocation was launched; the
`arm` path was exercised only by focused tests at two-update width after a
local MSVC artifact load.

Engineering-scope §4: none of the default-prohibited machinery was added. The
measured delta norm is one float64 reduction per update, not a framework.

## 1. Files created / edited (A/D line counts)

| Path | A | D |
| --- | ---: | ---: |
| `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/__init__.py` | 19 | 0 |
| `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/study.py` | 699 | 0 |
| `scripts/run_rcle_tbcfv_b02.py` | 135 | 0 |
| `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/test_b02.py` | 421 | 0 |
| `docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B02_NORM_0P02_CM_RECORD_20260906.md` | 300 | 0 |

New non-test source = 19 + 699 + 135 = **853 ≤ 1,200**. Runner = **135 ≤ 600**.
Attempt + runner + tests = 1,274. B01 test package has no `__init__.py`; none
was created for B02. TBCFV tree, B01 entry, and `scripts/run_rcle_tbcfv_b01.py`
were not edited. No `executability.py` for B02.

## 2. Reuse versus copy

| Symbol | Reuse or copy | Why |
| --- | --- | --- |
| `seed_root_key`, `block_digest_hex` | import from B01 | take ASCII / identity / index as arguments |
| `B01BlockAuthority`, `native_certificate_payload`, `build_native`, `native_available` | import from B01 | authority seam and native identity unchanged |
| `initialize_block_models`, `restrict_two_arms`, `initialize_b01_models` | import | five-package draw then two-arm restrict; allocations record the five versus the two |
| `flat_parameters`, `evaluate_learned`, `evaluate_scripted`, `heldout_batches` | import | host evaluation unchanged |
| `cell_endpoint_means`, `eight_cell_mean`, `_mean`, `_group` | import | same cell tables |
| `publish_paired_primary`, `se_of_mean_of_independent_ses` | import | per-path FLEX−C1P1 fields and SE combination; B02 wraps them |
| `paired_difference_se`, `scenario_row` | reused inside the imported helpers | not called by name in B02 |
| `load_control_summary`, `validate_control_summary` | import | FLEX identity check; B02 passes object id / seed 18 |
| `ArmWallExpired`, `check_wall`, `peak_rss_bytes`, `process_cpu_seconds`, `directory_bytes`, `write_json`, `cost_law` | import | same wall / RSS / CPU / publication helpers |
| `TRAINING_CELLS`, `HELDOUT_CELLS`, `PRIMARY_CELLS`, `B01_ARMS` | import | same cells and two arms |
| `exact_advantage_loss`, `_validated_block_cells`, `BASELINE_DECAY`, `TRAIN_EPISODES_PER_BLOCK`, `TRAIN_CELLS`, `REGISTERED`, `ParameterUpdateAudit`, `BlockUpdateAudit`, `TBCFVModel`, `execute_learned_batch`, `EpisodeCoordinate` | import from TBCFV | loss, layout, audit dataclasses, batch executor |
| `make_b02_semantic_rng` | **copy of shape** | B01 `make_semantic_rng` takes `key_ascii` but derives the digest with B01's default identity |
| `fixed_norm_sgd_step` | **copy** | the registered step has no norm argument and stamps 0.0005 |
| `apply_b02_block_update` | **copy** | the registered block update calls the 0.0005 step |
| `execute_b02_training_update` | **copy** | B01's training update calls the registered block update |
| `load_and_validate_b02_control_summary` | **copy of shape** | B01's loader hard-codes B01 object / seed 17; B02 also requires `initialization_panel` |
| `initialization_panel`, `tag_init_rows` | new | shared update-0 C1P1 panel |
| `b02_configuration`, `b02_allocations` | new | 0.02 literals, selection history, five-vs-two allocations |
| `publish_b02_primary` / `_or_error` | **copy of shape** | B01 aggregates only `delta_tau_b01`; B02 adds `ΔU`, `G_U`, init table, sources |
| `run_arm` | **copy of shape** | B01 constants, no init panel, no 0.02 step |
| `run_reference` | **copy of shape** | B01 key / identity; B02 tags `new:INDEPENDENT-NEAREST:seed18` |
| runner `scripts/run_rcle_tbcfv_b02.py` | **copy of shape** | B01 has `executability` and arm `--wall-cap` 2600; B02 is `build`/`arm`/`reference`, default 580 |

B02 does not import or call `registered_plain_sgd_step`,
`apply_registered_block_update`, or `execute_b01_training_update`. It does not
patch `LEARNING_RATE`, `GRADIENT_DIRECTION_SCALE`, or `NONZERO_UPDATE_NORM`.

`initialize_block_models` copies one tensor onto all five `LEARNED_PACKAGES`.
B02 then `restrict_two_arms`. `summary["allocations"]` records
`package_models_allocated_count = 5` and `training_instances_count = 2`.

## 3. Diff of `fixed_norm_sgd_step` against `registered_plain_sgd_step`

Registered (`models.py:374-398`): no norm argument; `multiplier =
-LEARNING_RATE * GRADIENT_DIRECTION_SCALE / raw_norm`; audit
`direction_norm=GRADIENT_DIRECTION_SCALE` (0.05),
`parameter_delta_norm=NONZERO_UPDATE_NORM` (0.0005); no measured delta.

B02: `fixed_norm_sgd_step(model, nonzero_update_norm)`; `multiplier =
-nonzero_update_norm / raw_norm`; same 26,161-scalar check and float64
`raw_gradient_norm`; after the in-place add, measured L2 of
`multiplier * grad` in float64 (no extra model pass); wraps
`ParameterUpdateAudit` in `B02StepAudit(audit, measured_parameter_delta_norm)`;
`direction_norm=1.0` (unit direction); `parameter_delta_norm` is the prescribed
argument. Zero gradient: no update, both norms 0.0, `nonzero=False`.

```
--- registered_plain_sgd_step(model)
+++ fixed_norm_sgd_step(model, nonzero_update_norm)
@@
-def registered_plain_sgd_step(model: TBCFVModel) -> ParameterUpdateAudit:
+def fixed_norm_sgd_step(model: TBCFVModel, nonzero_update_norm: float) -> B02StepAudit:
     parameters = tuple(model.parameters())
     # same 26,161-scalar surface check
     # same float64 squared-sum raw_gradient_norm
     if raw_norm == 0.0:
-        return ParameterUpdateAudit(0.0, 0.0, 0.0, False)
+        return B02StepAudit(ParameterUpdateAudit(0.0, 0.0, 0.0, False), 0.0)
-    multiplier = -LEARNING_RATE * GRADIENT_DIRECTION_SCALE / raw_norm
+    multiplier = -nonzero_update_norm / raw_norm
     with torch.no_grad():
         for parameter in parameters:
             if parameter.grad is not None:
+                grad64 = parameter.grad.detach().to(torch.float64)
+                delta = multiplier * grad64
+                measured_sq = measured_sq + delta.square().sum()
                 parameter.add_(parameter.grad.to(parameter), alpha=multiplier)
-    return ParameterUpdateAudit(
+    return B02StepAudit(ParameterUpdateAudit(
         raw_gradient_norm=raw_norm,
-        direction_norm=GRADIENT_DIRECTION_SCALE,
-        parameter_delta_norm=NONZERO_UPDATE_NORM,
+        direction_norm=1.0,
+        parameter_delta_norm=nonzero_update_norm,
         nonzero=True,
-    )
+    ), measured_parameter_delta_norm=measured)
```

`apply_b02_block_update` is the registered block update with
`fixed_norm_sgd_step` in place of the registered step, then the same 0.95/0.05
baseline update. Event order remains `("parameter_update", "baseline_update")`.

## 4. Derived hex values (seed 18), as tests observed them

Root key = SHA256 of the ASCII string `RCLE-TBCFV-B02-NORM-0p02/seed/18`:

```
fd3cd5cf0f085e880a424f7a546017a62d300676e385e1174676b9f4c14e5093
```

Block digest = `_derive_block_digest(root_key_bytes, "RCLE-TBCFV-B02-NORM-0p02", 0)`:

```
82593ad701533212112f1e29d22f3d0b701fd8360b88d9bfcb61ac565f6b2210
```

`test_seed_and_block_digest_are_reproducible_and_distinct_from_b01` asserted
both and that they differ from B01 seed-17
`fb5f7dce9ab4cff9…` / `a67b014451fa8d61…`.

## 5. Grep proof: forbidden names absent from the B02 entry

Searched files:

```
experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/study.py
experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/__init__.py
scripts/run_rcle_tbcfv_b02.py
tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/test_b02.py
```

Names: `registered_plain_sgd_step`, `apply_registered_block_update`,
`execute_b01_training_update`.

Result: **NO MATCHES**.

B02's own names are `NONZERO_UPDATE_NORM_B02 = 0.02` and
`PREVIOUS_NONZERO_UPDATE_NORM = 0.0005` (selection history only). Configuration
publishes `nonzero_update_norm: 0.02`.

## 6. Local pytest

Command:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/roster_consistent_latent_exploration/test/b02-grok tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02 tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01
```

Verbatim summary:

```
..................                                                       [100%]
============================== warnings summary ===============================
..\..\..\..\..\Users\fires\.conda\envs\hmasd-amd-cpu\lib\site-packages\_pytest\config\__init__.py:1464
  C:\Users\fires\.conda\envs\hmasd-amd-cpu\lib\site-packages\_pytest\config\__init__.py:1464: PytestConfigWarning: Unknown config option: cache_dir

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
18 passed, 1 warning in 5.22s
```

Nine B02 tests and nine B01 tests. Native two-update tests for both objects
ran on this host (MSVC artifact already cached from B01). Interpreter
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, `PYTHONUTF8=1`.

## 7. Frozen `wsl_4070` commands

Placeholders: `<sha>` full launch sha, `<sha7>` first seven hex characters.
Node python: `/home/wu/.venvs/hmasd/bin/python`. Do not launch from this
session.

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

(1) build (charged once if actually paid)

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/build.json" && \
/usr/bin/time -v -o "$ROOT/timings/build.time" \
$PY scripts/run_rcle_tbcfv_b02.py build --build-root "$ROOT/build"
```

(2) focused check (oracle test file kept; B02 tests in place of B01 tests)

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/pytest.json" && \
/usr/bin/time -v -o "$ROOT/timings/pytest.time" \
$PY -m pytest -q -p no:cacheprovider \
  tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_native_host.py \
  tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02
```

(3) arm C1P1

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/c1p1.json" && \
/usr/bin/timeout --signal=ALRM 600s \
/usr/bin/time -v -o "$ROOT/timings/c1p1.time" \
$PY scripts/run_rcle_tbcfv_b02.py arm --arm C1P1 \
  --out "$ROOT/c1p1" --wall-cap 580 \
  --admission-receipt "$ROOT/receipts/c1p1.json" \
  --launch-sha <sha> --updates 200 --eval-episodes 256
```

(4) arm FLEX

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/flex.json" && \
/usr/bin/timeout --signal=ALRM 600s \
/usr/bin/time -v -o "$ROOT/timings/flex.time" \
$PY scripts/run_rcle_tbcfv_b02.py arm --arm FLEX \
  --out "$ROOT/flex" --wall-cap 580 \
  --admission-receipt "$ROOT/receipts/flex.json" \
  --control-summary "$ROOT/c1p1/summary.json" \
  --launch-sha <sha> --updates 200 --eval-episodes 256
```

(5) reference

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/reference.json" && \
/usr/bin/time -v -o "$ROOT/timings/reference.time" \
$PY scripts/run_rcle_tbcfv_b02.py reference \
  --out "$ROOT/reference" \
  --admission-receipt "$ROOT/receipts/reference.json" \
  --launch-sha <sha> --eval-episodes 256
```

Hub check before (3): if (1)+(2) plus a credible projection of (3)+(4)+(5)
exceeds 1,500 s, the object is not launched (a range problem is returned, not
a reduction).

Single CPU thread is requested by the `OMP_*` / `MKL_*` / `OPENBLAS_*`
exports and `torch.set_num_threads(1)` in the arm path. In-process `--wall-cap`
is 580; the external `timeout --signal=ALRM 600s` is the 600 s bound. Cost law
in each arm `summary.json` is episode/tick counts plus a note that wall per
update is measured at runtime; no numeric pre-launch wall exists. Shared
preparation is charged in the launch ledger by the operator, as in B01 (no
`--shared-preparation-seconds`).

## 8. Cost references

Card §6, at their stated scope (B01, not this law):

| Item | Reference | Scope |
| --- | --- | --- |
| B01 C1P1 complete arm wall | ≈ 62.0 s | includes final evaluation; not the 0.02 law and not the init panel |
| B01 FLEX complete arm wall | ≈ 69.8 s | same |
| B01 reference | ≈ 1.5 s | seed-17 panel; B02 uses seed 18 |
| B01 preparation | ≈ 11 s | B01 executability / shared items |
| B01 charged total | ≈ 144.3 s | not end-to-end for B02 |
| B01 cold build | 5.09 s | POSIX node; rebuild charged once if paid |
| Path bound | 200 × 0.02 = 4 | upper bound on displacement, not a movement qualification |
| B01 initial-norm reference | 21.186038495201018 | published in B02 configuration; actual new initial norm is recorded in the charged invocation |
| Per-arm cap | 600 s | complete logical invocation, including C1P1 init panel |
| Object cap | 1,500 s | build + focused check + both arms + reference, each charged once |

The added initial evaluation, the changed update's real cost, checks and
output overhead are unmeasured and are not filled with zero. No calibration
experiment was run.

## 9. Unverified

- `g++`/`clang++` compile on `wsl_4070` (POSIX branch never executed here).
- Oracle conformance of a Linux `.so`.
- Node focused-check wall and RSS.
- Arm walls for 200 updates + 256×8 held-out episodes + the C1P1
  initialization panel, and whether they fit 600 s per arm / 1,500 s with
  (1)+(2)+(5).
- Default-root SemanticRNG bind on Linux versus the request-specific
  `--build-root` artifact (`build_key` includes the resolved path).
- Actual seed-18 initial parameter norm (configuration carries the B01
  reference 21.186038495201018; the invocation records the new value).
- Measured per-update wall of the 0.02 law versus B01's 0.0005 law.
- SIGALRM delivery during a native batch (Python raises only when the
  interpreter is between bytecode; an overrun inside the C++ kernel may
  still rely on the external 600 s `timeout --signal=ALRM`).
- No result-bearing launch. No git commit from this session.

scope: none
