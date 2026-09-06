# CM objective — RCLE-TBCFV-B01-PERSIST-VS-FLEX thin entry, Linux build branch, executability measurement (2026-09-06)

Card: `RCLE_TBCFV_B01_PERSIST_VS_FLEX_SCIENCE_CARD_20260906.md` (sections 2–4, 6, 7 bind).
Implementer: Grok Build (CLAUDE.md Grok route), worktree `.claude/worktrees/grok-rcle-b01`,
branch `grok/rcle-tbcfv-b01-20260906`; independent Opus review (`hmasd-reviewer`) of the
`native_backend.py` change and the RNG/authority seam; hub review and pathspec commit.

## Objective

Make the first bounded B on TBCFV runnable: (1) a thin two-arm, single-seed entry that reuses
the frozen TBCFV science code without the full-panel orchestration; (2) a Linux build branch
in `native_backend.py` so the native kernel can be built on the remote node from the same
source; (3) a bounded zero-learner executability/cost mode; (4) focused tests and a CM record
with frozen node commands. Nothing here changes the host law, model, loss, update rule,
endpoints, package laws or the C++ kernel source.

## Facts the design rests on (from the code map; verify each when you read the code)

- Arms are literal names in `config.py` (`C1P1 = "C1P1-COMMON-PERSISTENT"`, `FLEX = "FLEX-REKEY"`);
  `packages.py` branches on tuple membership; `TBCFVModel.event_plan` hard-masks the update
  heads for non-FLEX arms; FLEX final layers start at zero and train.
- Reusable functions in `empirical_runner.py`: `initialize_block_models(rng)` (one shared init
  tensor copied into a model per learned package; restrict the dict to the two arms),
  `execute_training_update(model, arm, rng, update, baselines, authority_check=None)` (64
  episodes over the eight training cells, `exact_advantage_loss`, one backward,
  `apply_registered_block_update`, returns `(baselines, counts)`; its guard is `0 <= update < 800`),
  `execute_learned_batch(model, arm, rng, coordinates, training=…)` (returns
  `LearnedEpisodeResult(tau, U, F, Y, …)` computed natively), `execute_scripted_batch(package,
  rng, coordinates)` (dispatches `INDEPENDENT_NEAREST` to `scripted.independent_nearest`),
  cells `TRAINING_CELLS` / `HELDOUT_CELLS` from `inference.py`.
- Not reusable: `execute_full_panel`, `analyze_*_panel`, `frontier.publish_*`,
  `result_blind_preactivity_summary` / `full_runner_chain`, `_synthetic_empirical_frontier_chain`,
  `_new_block_runtime`, the 20-block `_materialize_binding` path, `SyntheticTestRNG`, and
  `_cell_mean` orchestration (its 2,048-episode check matches 8 × 256 arithmetically, but write
  your own aggregation).
- Seam to resolve: `SemanticRNG.__init__` requires an authority-shaped object (`require_active`,
  `block_root_digest`, `certificate["native"]`). Build a minimal `B01BlockAuthority` in the new
  attempt directory modelled on `process_workers._ClosedBlockAuthority`, whose root digest is
  computed with the existing `_derive_block_digest(key, identity, index)` from
  `empirical_contract.py` with `key = sha256(b"RCLE-TBCFV-B01-PERSIST-VS-FLEX/seed/17")`,
  identity `"RCLE-TBCFV-B01-PERSIST-VS-FLEX"`, index 0, and whose `certificate["native"]` carries
  the actual built backend's digest/ABI facts as the real path expects. Record the derived
  digest hex in the CM record. Do not use any `fixture_only` / `non_scientific` identity.
- Native backend: `native_backend.py` compiles `native/tbcfv_backend.cpp` through
  `vswhere`/`vcvars64.bat`/MSVC via `subprocess` and loads the `.dll` with ctypes; no Linux
  branch exists; build root `tempfile.gettempdir()/hmasd_rcle_tbcfv_native/<build_key>`
  (overridable with `build_root=`).

## Owned paths

Create:
- `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/__init__.py`, `study.py`
  (authority seam, arm/seed setup, training loop with per-update curve capture, final held-out
  evaluation per scenario, reference row, aggregation, publication), `executability.py`
  (zero-learner scripted mode).
- `scripts/run_rcle_tbcfv_b01.py` (≤ 600 lines): modes `build` (build the native backend for
  this platform into a request-specific `build_root` and print its digest), `executability`
  (≤ 300 s wall, ≤ 8 cells × one 8-episode batch on preparation scenarios derived from a separate
  sub-key `…/seed/17/preparation`, INDEPENDENT-NEAREST only, records per-batch wall, RSS, episode
  and tick counts, τ/U/Y descriptively), `arm --arm {C1P1,FLEX}` (200 updates, 256 episodes ×
  8 held-out cells, `--wall-cap 2700`, admission receipt path, output root; summary.json with
  configuration, counts, curves, per-scenario endpoints, wall/CPU/RSS via `resource`), and
  `reference` (INDEPENDENT-NEAREST on the same 2,048 held-out scenarios, once). The FLEX arm
  invocation additionally takes `--control-summary` (the C1P1 summary) and publishes the paired
  primary: per active path (`8_to_12`, `12_to_8`, ACTIVE_CONTINUATION) both means, FLEX − C1P1
  difference, τ=40 fractions, `delta_tau_b01` = mean of the two path differences (positive
  favours the treatment), companion U/40U, all-cell τ/U/Y and the eight-cell mean.
- `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/test_b01.py`:
  key/digest derivation reproducible and distinct from the preparation sub-key; both arms start
  from identical parameters and FLEX final update layers are zero yet `requires_grad`; a
  two-update run at a tiny width (if the native backend is available on the platform, else
  skipped with the reason) changes parameters by exactly 0.0005 per nonzero update and updates
  baselines after the step; the aggregation on hand-written endpoint tables publishes the
  primary and companion quantities exactly; the executability mode refuses more than 64
  episodes or 300 s.
- `docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B01_CM_RECORD_20260906.md`.

Edit (bounded, reviewed): `experiments/candidates/roster_consistent_latent_exploration_tbcfv/native_backend.py`
only to add a POSIX branch: when not on Windows, compile the same snapshot source with `g++`
(or `clang++` if `g++` is absent) into a shared object with the flag semantics of
`MSVC_COMPILE_FLAGS` translated one-to-one (optimization level, standard, no fast-math, strict
FP as MSVC's default), `-fPIC -shared`, and load it through the same ctypes path; keep the build
key/digest logic, snapshot copy, and all Windows behaviour byte-identical. Record every flag
translation in the CM record. No change to `tbcfv_backend.cpp`.

Not edited: everything else under `roster_consistent_latent_exploration_tbcfv/` (models,
packages, scripted, empirical_runner, empirical_contract, empirical_artifacts, inference,
host_oracle, process_workers, `__main__.py`), existing tests, cards, intakes, governance files.

## Acceptance

- Local (Windows) focused tests green: the new test file plus
  `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_native_host.py`
  and `test_models_and_scripted.py` (they exercise the MSVC build and the oracle; report their
  wall). Command:
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/roster_consistent_latent_exploration/test/b01-grok <paths>`.
- The `native_backend.py` diff is limited to the POSIX branch; Windows path unchanged (`git diff`
  shows additions inside a platform conditional only).
- New source ≤ 2,000 lines; runner ≤ 600; no new guard/registry/validator/lease/retry.
- CM record: files with A/D, the flag translation table, the derived digests, the local test
  summary, and the frozen `wsl_4070` commands in this order (all with
  `PYTHONPATH=/home/wu/hmasd-worktrees/rcle-b01-<sha7>`, `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
  OPENBLAS_NUM_THREADS=1`, `PATH` prefixed with `/home/wu/.venvs/hmasd/bin`, each preceded by
  `python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` joined by `&&`, each
  timed with `/usr/bin/time -v -o <file>`): (1) `run_rcle_tbcfv_b01.py build --build-root
  <root>/build`; (2) `pytest -q -p no:cacheprovider tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_native_host.py
  tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01` (portability:
  oracle conformance of the Linux build); (3) `executability` under `/usr/bin/timeout --signal=TERM 300s`;
  (4) `arm --arm C1P1` under `timeout --signal=ALRM 2696s`; (5) `arm --arm FLEX --control-summary
  <root>/c1p1/summary.json` under the same timeout; (6) `reference`. The card's 5,400 s summed
  budget is checked by the hub from the six timings before (4) is launched: if (1)+(2)+(3) plus a
  credible projection of (4)+(5)+(6) exceeds 5,400 s, the hub decides a symmetric reduction
  before any learning; the runner therefore accepts `--updates` and `--eval-episodes` with
  defaults 200 and 256 and records the values used.
- What remains unverified is stated explicitly (node build, executability, arm walls).
