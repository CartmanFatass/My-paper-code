# CM record — RCLE-TBCFV-B01-PERSIST-VS-FLEX thin entry (2026-09-06)

Implementer: Grok Build (grok-4.6). Worktree `.claude/worktrees/grok-rcle-b01`,
branch `grok/rcle-tbcfv-b01-20260906`. No git commands were run. No training,
evaluation, or result-bearing invocation was launched; `executability` and `arm`
were exercised only by focused tests at tiny width after a local MSVC artifact
load.

Engineering-scope §4: none of the default-prohibited machinery was added.

## 1. Files created / edited (A/D line counts)

| Path | A | D |
| --- | ---: | ---: |
| `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/__init__.py` | 23 | 0 |
| `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/study.py` | 642 | 0 |
| `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/executability.py` | 138 | 0 |
| `scripts/run_rcle_tbcfv_b01.py` | 122 | 0 |
| `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/test_b01.py` | 208 | 0 |
| `docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B01_CM_RECORD_20260906.md` | 291 | 0 |
| `experiments/candidates/roster_consistent_latent_exploration_tbcfv/native_backend.py` | 81 | 0 |

New Python source = 1,133 lines. Runner = 122 ≤ 600. Attempt + runner + tests
= 1,133 ≤ 2,000. `native_backend.py` line count 1,308 → 1,389; insertions only
(POSIX helpers, `POSIX_COMPILE_FLAGS`, and `os.name != "nt"` branches). The
Windows compile command, `/LD` DLL name, `vcvars64.bat` path, and
`MSVC_COMPILE_FLAGS` tuple are unchanged. On this Windows host
`native_toolchain_identity()["compile_flags"]` is still the MSVC list.

## 2. Authority seam and digest derivation

### Facts verified against code (and differences)

- Arm names `C1P1-COMMON-PERSISTENT` / `FLEX-REKEY` in `config.py`;
  `packages.py` branches on tuple membership; `TBCFVModel.event_plan` returns
  the detached base plan for non-FLEX arms; FLEX final layers are
  `DeterministicZeroLinear` and `apply_affine_fixture_uniforms` keeps them at
  zero. Confirmed.
- `initialize_block_models` copies one tensor onto **all five**
  `LEARNED_PACKAGES`. B01 then restricts the dict to the two card arms.
- `execute_training_update` accepts `0 <= update < 800` and always runs the
  eight training cells × eight rows (two native width-32 batches). It does
  **not** return per-episode `Y` or `ParameterUpdateAudit`. B01 therefore
  calls `execute_learned_batch`, `exact_advantage_loss`, and
  `apply_registered_block_update` with the same coordinate grouping, and
  records the curve from `LearnedEpisodeResult.Y`.
- `execute_learned_batch` returns `tau, U, F, Y`. Confirmed.
- `execute_scripted_batch` dispatches `INDEPENDENT-NEAREST` via
  `SCRIPTED_PACKAGES.index`. `ScriptedEpisodeResult` has `tau, U, F` and
  **no `Y`**. Executability and the reference row store `Y` as null and
  record that fact.
- `TRAINING_CELLS` / `HELDOUT_CELLS` live in `inference.py`. Confirmed.
- `SemanticRNG.__init__` reads `require_active`,
  `block_root_digest(block_index)`, and `certificate["native"]` keys
  `source_sha256` and `build_key`, then calls `bind_native_backend()` with
  the **default** build root. `_require_semantic_rng` uses exact `type()`.
- `_derive_block_digest` is HMAC-SHA256 of
  `canonical_json_bytes({"domain":"RCLE-TBCFV-R04/run-block-root/v1",
  "identity": identity, "block_index": index})` under the 32-byte key.
- `ProductionAuthority.block_root_digest` enforces `0 <= index < 20`. B01
  does not use that class.
- `_cell_mean` refuses any cell that is not 2,048 episodes. B01 writes its
  own means over the requested `--eval-episodes` (default 256).
- Held-out coordinates follow the r04 consumer:
  `EpisodeCoordinate(block, cell, start+row, row % 8)` in widths 32, then 8,
  then 1.

### Minimal block authority

`B01BlockAuthority` is a frozen dataclass with:

| Attribute / method | Why it exists |
| --- | --- |
| `certificate` | Mapping; `SemanticRNG` reads `certificate["native"]` |
| `certificate["native"]` | `source_sha256` and `build_key` from `native_artifact_identity()` at the **default** build root (the same bind `SemanticRNG` performs). Also stores artifact sha256, path, ABI, runtime ABI, toolchain path/sha256/flags, resolved root, and load seconds. Extra keys are unused by `SemanticRNG`. |
| `block_index` | `0` |
| `root_digest` | hex from `_derive_block_digest` |
| `require_active(now=)` | no-op; `SemanticRNG` calls it; no lease or expiry |
| `block_root_digest(index)` | returns `root_digest` iff `index == block_index` |

No `ProductionAuthority`, permit, 20-block materialization, or
`fixture_only` / `non_scientific` identity.

`build --build-root` compiles into a request-specific root whose
`build_key` differs from the default root `SemanticRNG` binds (the
resolved path is part of the visible key). Step (1) remains a
portability check of that request-specific artifact. The arms,
executability, and reference then pay a second compile into the default
root; each invocation's `native` block records and validates the
default-root artifact the science actually loads.

`build` also calls `native_artifact_identity()` at the default root and
writes that identity under `default_root` in `native_identity.json` and
in stdout, so the artifact the science loads is built and identified
once before the arms. Request-specific fields stay at the top level.

### Preparation sub-key vs held-out panel

| Stream | ASCII label hashed to 32 bytes | HMAC block digest identity / index | Cell names |
| --- | --- | --- | --- |
| Training, held-out, reference | `RCLE-TBCFV-B01-PERSIST-VS-FLEX/seed/17` | identity `RCLE-TBCFV-B01-PERSIST-VS-FLEX`, index 0 | `TRAINING_CELLS` then `HELDOUT_CELLS` |
| Executability | `RCLE-TBCFV-B01-PERSIST-VS-FLEX/seed/17/preparation` | same identity, index 0, different key | `TRAINING_CELLS` (legal for `_parse_cell`; not the held-out panel) |

The preparation HMAC key is not the seed-17 block digest, so even identical
cell names would not reproduce held-out fixtures.

### Per-scenario rows

One JSON object per scenario:

`{"cell", "index", "arm", "tau", "U", "F", "Y"}`

`index` is `EpisodeCoordinate.update_or_scenario`. Learned rows have `Y`;
scripted rows have `Y: null`.

### Derived hex values, seed 17

Root key = SHA256 of the ASCII string
`RCLE-TBCFV-B01-PERSIST-VS-FLEX/seed/17`:

```
fb5f7dce9ab4cff9cc898c91aa49721936b84a16f202e51bc705504dd1d94c34
```

Block digest = `_derive_block_digest(root_key_bytes, "RCLE-TBCFV-B01-PERSIST-VS-FLEX", 0)`:

```
a67b014451fa8d614c191e82f2e20ded2d8f77f21098dcb52d2744e64d596048
```

Preparation sub-key = SHA256 of
`RCLE-TBCFV-B01-PERSIST-VS-FLEX/seed/17/preparation`:

```
466f5ff780041c45996fa9cd67929b754200dca60e104b0c3d8367b18b90f3ee
```

Preparation block digest (what `SemanticRNG` uses as HMAC key for
executability; recorded for replay, not required by the objective's three-hex
list):

```
59a32b3cc79447350db1e0f2fd785af9b41f38524c14c3f2e8c3046e17565d3d
```

These values were computed with the live `_derive_block_digest` /
`canonical_json_bytes` and re-checked by `test_b01.py`.

## 3. MSVC → g++ flag translation

| MSVC (`MSVC_COMPILE_FLAGS`) | POSIX (`POSIX_COMPILE_FLAGS`) | Role |
| --- | --- | --- |
| `/nologo` | omitted | MSVC banner suppression; GCC/Clang have no equivalent |
| `/std:c++17` | `-std=c++17` | language standard |
| `/O2` | `-O2` | optimization level |
| `/EHsc` | `-fexceptions` | C++ exceptions |
| `/LD` | `-shared` | shared library |
| (implied by `/LD` on Windows) | `-fPIC` | ELF position-independent code |
| `/fp:strict` | `-fno-fast-math` `-ffp-contract=off` `-fno-unsafe-math-optimizations` | no fast-math; no FP contraction; no unsafe FP transforms (MSVC `/fp:strict` default-strict semantics) |

Compiler: `g++`, else `clang++`. Artifact name `tbcfv_backend.so`. Load path
remains `ctypes.CDLL`. Snapshot copy and `_final_build_key` hashing are
shared. POSIX flags enter the visible key only when `os.name != "nt"`.

## 4. Local pytest

Command:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/roster_consistent_latent_exploration/test/b01-grok tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_native_host.py tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_models_and_scripted.py tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/test_b01.py
```

Verbatim summary:

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\..\..\..\Users\fires\.conda\envs\hmasd-amd-cpu\lib\site-packages\_pytest\config\__init__.py:1464
  C:\Users\fires\.conda\envs\hmasd-amd-cpu\lib\site-packages\_pytest\config\__init__.py:1464: PytestConfigWarning: Unknown config option: cache_dir

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 9.04s
```

MSVC request-specific compile wall, timed separately with
`native_artifact_identity(build_root=.../test/b01-grok/msvc-wall)` after the
suite (fresh root, not a training run): **4.461 s** wall
(`load_seconds` 4.460). Artifact
`tbcfv_backend.dll`, flags
`['/nologo', '/std:c++17', '/O2', '/EHsc', '/LD', '/fp:strict']`.
The pytest wall (9.04 s) used the already-warm default MSVC cache plus two
C1P1 training updates and one 8-episode preparation scripted batch.

## 5. Frozen `wsl_4070` commands

Placeholders: `<sha>` full launch sha, `<sha7>` first seven hex characters.
Node python: `/home/wu/.venvs/hmasd/bin/python`. Do not launch from this
session.

```
WT=/home/wu/hmasd-worktrees/rcle-b01-<sha7>
ROOT=$WT/temp/directions/roster_consistent_latent_exploration/exp/tbcfv_b01_20260906
PY=/home/wu/.venvs/hmasd/bin/python
export PYTHONPATH="$WT"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PATH="/home/wu/.venvs/hmasd/bin:$PATH"
cd "$WT"
mkdir -p "$ROOT/receipts" "$ROOT/timings" "$ROOT/build" "$ROOT/executability" "$ROOT/c1p1" "$ROOT/flex" "$ROOT/reference"
```

(1) build

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/build.json" && \
/usr/bin/time -v -o "$ROOT/timings/build.time" \
$PY scripts/run_rcle_tbcfv_b01.py build --build-root "$ROOT/build"
```

(2) Linux oracle / B01 tests (portability of the node build)

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/pytest.json" && \
/usr/bin/time -v -o "$ROOT/timings/pytest.time" \
$PY -m pytest -q -p no:cacheprovider \
  tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_native_host.py \
  tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01
```

(3) executability (≤ 300 s, ≤ 64 episodes)

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/executability.json" && \
/usr/bin/timeout --signal=TERM 300s \
/usr/bin/time -v -o "$ROOT/timings/executability.time" \
$PY scripts/run_rcle_tbcfv_b01.py executability --out "$ROOT/executability" --wall-cap 300
```

Hub check before (4): if (1)+(2)+(3) plus a credible projection of
(4)+(5)+(6) exceeds 5,400 s, do not launch learning; pass `--updates` and
`--eval-episodes` after a symmetric reduction. Defaults 200 and 256.

(4) arm C1P1

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/c1p1.json" && \
/usr/bin/timeout --signal=ALRM 2696s \
/usr/bin/time -v -o "$ROOT/timings/c1p1.time" \
$PY scripts/run_rcle_tbcfv_b01.py arm --arm C1P1 \
  --out "$ROOT/c1p1" --wall-cap 2600 \
  --admission-receipt "$ROOT/receipts/c1p1.json" \
  --launch-sha <sha> --updates 200 --eval-episodes 256
```

(5) arm FLEX

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/flex.json" && \
/usr/bin/timeout --signal=ALRM 2696s \
/usr/bin/time -v -o "$ROOT/timings/flex.time" \
$PY scripts/run_rcle_tbcfv_b01.py arm --arm FLEX \
  --out "$ROOT/flex" --wall-cap 2600 \
  --admission-receipt "$ROOT/receipts/flex.json" \
  --control-summary "$ROOT/c1p1/summary.json" \
  --launch-sha <sha> --updates 200 --eval-episodes 256
```

(6) reference

```
$PY scripts/hmasd_resource_preflight.py admit-memory --out "$ROOT/receipts/reference.json" && \
/usr/bin/time -v -o "$ROOT/timings/reference.time" \
$PY scripts/run_rcle_tbcfv_b01.py reference \
  --out "$ROOT/reference" \
  --admission-receipt "$ROOT/receipts/reference.json" \
  --launch-sha <sha> --eval-episodes 256
```

Single CPU thread is requested by the `OMP_*` / `MKL_*` / `OPENBLAS_*`
exports and `torch.set_num_threads(1)` in the arm path. Cost law in each arm
`summary.json` is episode/tick counts plus a note that wall per update is
measured at runtime; no numeric pre-launch wall exists.

## 6. Unverified

- `g++`/`clang++` compile on `wsl_4070` (POSIX branch never executed here).
- Oracle conformance of a Linux `.so`.
- Node executability wall, RSS, and 64-episode cost.
- Arm walls for 200 updates + 256×8 held-out episodes, and whether they fit
  2,700 s per arm / 5,400 s summed with (1)–(3) and (6).
- Default-root SemanticRNG bind on Linux vs the request-specific
  `--build-root` artifact (`build_key` includes the resolved path). Step
  (1) does not populate that default root by itself; `build` now also
  compiles and identifies the default root in its JSON, and each arm
  still validates the default-root `native` block. Neither compile has
  been executed on `wsl_4070`.
- Cold MSVC compile during the pytest process itself (the 9.04 s suite used
  a warm default cache; the 4.461 s figure is a later request-specific
  compile).
- SIGALRM delivery during a native batch (Python raises only when the
  interpreter is between bytecode; an overrun inside the C++ kernel may
  still rely on the external 2696 s `timeout --signal=ALRM`).

## 7. Review round 1 fixes (2026-09-06)

Independent review: `ACCEPT_WITH_FIXES`. Owned paths only; `native_backend.py`
not edited. POSIX compile debris left in the unowned backend file.

### This-round A/D (net vs the first implementation)

| Path | A | D | lines now |
| --- | ---: | ---: | ---: |
| `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/study.py` | 252 | 0 | 894 |
| `scripts/run_rcle_tbcfv_b01.py` | 25 | 0 | 147 |
| `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/test_b01.py` | 110 | 0 | 318 |
| `docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B01_CM_RECORD_20260906.md` | 115 | 0 | 406 |
| `executability.py`, `__init__.py`, `native_backend.py` | 0 | 0 | unchanged |

Net figures are line-count growth against the §1 table (642 / 122 / 208).
`study.py` was restructured in place (helpers and `run_arm` flow), not
appended-only. New Python source now 1,520 ≤ 2,000. Runner 147 ≤ 600.

### Helpers and call sites

- `ArmWallExpired` — dedicated wall exception. Raised by `check_wall`
  (poll) and by the runner arm-path `SIGALRM` handler
  (`scripts/run_rcle_tbcfv_b01.py` `main` arm branch, POSIX
  `signal.setitimer` / `signal.signal`, disarmed in `finally`). Caught in
  `run_arm` around the training loop and around `evaluate_learned`.
- `check_wall(started, wall_cap)` — `perf_counter` poll used at the start
  of each training update, after the training loop, between held-out
  cells in `evaluate_learned`, and after a complete evaluation.
- `load_control_summary` / `validate_control_summary` /
  `load_and_validate_control_summary` — FLEX `run_arm` calls
  `load_and_validate_control_summary` **before** `started` and any
  training. Requires `arm == C1P1`, `status == COMPLETE`, and equality of
  `object`, `seed`, `block_digest_hex`,
  `configuration["eval_episodes_per_cell"]`, and
  `counts["completed_updates"]` vs `--updates`. Mismatch names the field.
  Missing or unparsable files raise `ValueError` before training.
- `publish_paired_primary_or_error` — public wrapper. Empty control or
  flex scenarios, or any other exception from `publish_paired_primary`,
  become `(None, "<type>: <message>")`. `run_arm` always calls it for
  FLEX after evaluation (including `scenarios == []` technical stop) and
  still writes `summary.json` / `parameters.pt` / curves / native block.
- `paired_difference_se` / `se_of_mean_of_independent_ses` — used inside
  `publish_paired_primary`. Per-path `paired_tau_se` and `paired_U_se`;
  `delta_tau_b01_se = sqrt(se_8to12^2 + se_12to8^2) / 2` (SE of the
  arithmetic mean of two independent path differences; each path SE is
  the paired-scenario Monte Carlo SE, sample sd / sqrt(n), ddof=1). Null
  if either path has n≤1.
- Partial publication: immediately after the training loop,
  `parameters.pt` and `summary.json` with `status = TRAINED_UNEVALUATED`
  (configuration, counts, curves, initial norm, displacement, native
  block). Final write overwrites. Evaluation records `evaluated_cells`
  (fully completed held-out cells only).
- `build_native` now also records default-root `native_artifact_identity()`
  under `default_root`.

### Other small fixes

- Training curve `per_cell` entries keep `tau_mean`, `U_mean`, `F_mean`
  alongside `Y_mean`.
- `peak_rss_bytes` Windows: `GetCurrentProcess.restype = wintypes.HANDLE`
  as `process_workers.py:146-148`. `GetProcessMemoryInfo.argtypes` was
  also set (same file, next lines): restype alone overflows the default
  32-bit first argument on Win64 (`int too long to convert`).
- Aggregate CPU: `RUSAGE_SELF + RUSAGE_CHILDREN` on POSIX (reaped
  children only; no double count with self).
- Runner default `--wall-cap` for `arm` is 2600. Frozen external timeout
  stays `timeout --signal=ALRM 2696s` (§5).

### Local pytest after the fixes

Command:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/roster_consistent_latent_exploration/test/b01-grok-fix tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_native_host.py tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_models_and_scripted.py tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/test_b01.py
```

Verbatim summary:

```
...................................                                      [100%]
============================== warnings summary ===============================
..\..\..\..\..\Users\fires\.conda\envs\hmasd-amd-cpu\lib\site-packages\_pytest\config\__init__.py:1464
  C:\Users\fires\.conda\envs\hmasd-amd-cpu\lib\site-packages\_pytest\config\__init__.py:1464: PytestConfigWarning: Unknown config option: cache_dir

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
35 passed, 1 warning in 7.69s
```

Three new fast tests (no native): empty-control `publish_paired_primary_or_error`;
control-summary validator reject/accept; `delta_tau_b01_se` on a handwritten
table. The two-update native test still ran.

### Not done

- POSIX compile debris in `native_backend.py`: not owned this round.
- `native_backend.py` otherwise: not touched.
- No git. No result-bearing launch.

scope: none
