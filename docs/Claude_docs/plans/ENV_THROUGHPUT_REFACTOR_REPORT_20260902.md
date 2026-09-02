# Environment throughput refactor — implementation report (2026-09-02)

Implementer: Claude Code (Fable 5.1) on `main`. Specification:
`ENV_THROUGHPUT_REFACTOR_PLAN_20260902.md`, phases P0–P3, with the owner decisions of its §6.1
(tolerance-level equivalence at `1e-9` absolute, connections exact, one re-freeze of the D2
fingerprint allowed). P4 was out of scope and was not attempted.

Nothing in this report is experimental evidence. The timing numbers are engineering
measurements of the same fixed workload before and after the change.

Interpreter for every command: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.

---

## 1. Status

| Phase | Commit | Files |
| --- | --- | --- |
| P0 — equivalence harness | `42b75e4eb` | `tests/uav_env_channel_equivalence_test.py` (new) |
| P1 — vectorised channel model | `e2b50f606` | `envs/pettingzoo/uav_env.py`, `envs/pettingzoo/scenario1.py` |
| P2 — observations from the matrices | `c2179d31f` | `envs/pettingzoo/uav_env.py` |
| P3 — re-freeze and re-time | this commit | `docs/Claude_docs/plans/D2_IMPLEMENTATION_REPORT_20260902.md` (addendum), this report |

No file outside the plan's scope was modified. `tests/fixtures/flexible_skill_duration_d2/
fingerprint_off.json` was regenerated and came back byte-identical (§5), so it is not in the
diff. The plan, the ADRs, the reviews and `README` were not edited.

---

## 2. What changed, per phase

### P0 — `tests/uav_env_channel_equivalence_test.py` (new)

Builds `UAVBaseStationEnv(n_uavs=6, n_users=50, area_size=1000, max_steps=500,
user_distribution="uniform", seed=20260902)` for each of the five channel models
`free_space`, `urban`, `suburban`, `3gpp-36777`, `probabilistic`; drives two 500-step episodes
(`reset(seed=20260902 + episode)`) with one fixed action tape
(`RandomState(20260902).uniform(-1, 1, size=(2, 500, 6, 3))`, shared by every model and both
backends); records per step the SINR matrix, the connection matrix, the per-agent rewards, the
per-agent observations and `_get_state()`.

The tape was written once from the code as it stood before P1 to
`temp/directions/flexible_skill_duration/test/uav_env_reference_tape_cf389585ba62.npz`
(gitignored, 31 MB). Its container-independent content digest — sha256 over `(name, dtype,
shape, bytes)` for every array, sorted by name — is
`cf389585ba62371e2c95b63cd645f6de29d87ad0b421de5587e838a17ebf8c02`, recorded in the test as
`EXPECTED_TAPE_CONTENT_SHA256`. If the file is missing, the fixture rebuilds it from
`channel_backend="reference"` and refuses to run unless the digest matches, so a lost tape costs
time and not evidence. `python tests/uav_env_channel_equivalence_test.py --write` regenerates it
and prints the digest.

Functions: `_make_env`, `_action_sequence`, `_drive`, `build_tape`, `content_sha256`,
`write_tape`, fixture `reference_tape`, tests
`test_live_channel_model_matches_reference_tape[<model>]` (5),
`test_reference_backend_reproduces_the_tape` (the scalar oracle, `free_space`, exact array
equality) and `test_step_wall_time_is_reported` (200 warmed steps, printed, not asserted).

The harness passed on the unchanged environment before P1 was written: max abs diff `0.0`
everywhere, `6 passed, 1 skipped in 112.63s` (the skip is the reference-backend test, which had
no `channel_backend` parameter to select yet).

### P1 — `envs/pettingzoo/uav_env.py`, `envs/pettingzoo/scenario1.py`

`MultiUAVEnv.__init__` takes `channel_backend` (`"vectorized"` default, `"reference"` selectable,
validated against the new class attribute `CHANNEL_BACKENDS`); `UAVBaseStationEnv.__init__`
threads it through, appended at the end of the signature so no positional caller moves.

Dispatchers, with the previous bodies moved unedited into `*_reference`:

| Public name (unchanged) | Reference path (moved, unedited) | Vectorised path (new) |
| --- | --- | --- |
| `_prime_path_loss_matrices` | `_prime_path_loss_matrices_reference` | `_prime_path_loss_matrices_vectorized` |
| `MultiUAVEnv._update_channel_state` | `_update_channel_state_reference` | `_update_channel_state_vectorized` |
| `UAVBaseStationEnv._update_channel_state` | `UAVBaseStationEnv._update_channel_state_reference` | inherits `_update_channel_state_vectorized` |

New functions in `MultiUAVEnv`: `_channel_realization_is_stochastic`,
`_user_position_components`, `_uav_user_geometry`, `_compute_path_loss_matrix`,
`_compute_uav_path_loss_matrix`, `_sum_excluding_own_row`, `_sinr_from_path_loss`,
`_compute_uav_user_sinr_matrix`, `_compute_uav_uav_sinr_matrix`,
`_greedy_connection_assignment`, `_vector_channel_state_is_current`. New state:
`self.uav_sinr_matrix` (the `[sender, receiver]` air-to-air SINR matrix) and
`self._channel_state_generation`.

Unchanged and still the per-link API other code calls: `_compute_sinr`,
`_compute_uav_to_uav_sinr`, `_compute_path_loss`, `_compute_path_loss_reference`,
`_compute_uav_path_loss`, `_compute_uav_path_loss_reference`, `_cache_path_loss`,
`_cached_uav_user_path_loss`, `_cached_uav_uav_path_loss`, `_path_loss_key`,
`_position_cache_key`, `_begin_path_loss_step`. Callers searched before touching anything:
`envs/pettingzoo/scenario2.py`, `scenario3.py`, `envs/pettingzoo/relay/*`,
`ha_ctse_process/uav_charge_rotation_g2.py`, `tools/diagnostics/uav/debug_predictive_handover.py`,
`tools/benchmarks/benchmark_uav_path_loss_cache.py`, `tests/uav_path_loss_cache_test.py`,
`tests/scenario7_channel_cache_test.py`, `tests/uav_relay_*`,
`tests/relay_lifecycle_locality_geometry_test.py`. Nothing was renamed.

How the formulas were kept (plan §2 list):

- per-model path loss reproduced term by term, including `max(distance_3d, 1e-6)`, the 2-D user
  convention (`z = 0` when `user_positions` has two columns), the elevation angle from
  `arctan2(height, distance_2d)`, and the explicit `0.0` written on the air-to-air diagonal
  instead of the formula;
- interference is the row sum over the *other* UAVs' linear powers, accumulated in **ascending
  interferer index** — the same order NumPy's own reduction uses for fewer than eight elements —
  so the sum is not merely close but identical at the sizes in play; the air-to-air case zeroes
  the receiver's own entry before accumulating, which reproduces "skip `k == receiver`" exactly
  because adding `0.0` is exact;
- the dBm round trip is preserved literally: `10*log10(T)` then `10**(x/10)` then
  `10*log10(noise_linear + …)`, not the algebraically equal shortcut;
- the zero-interference branch (`total_interference == 0` → `-inf` → interference-plus-noise is
  the bare noise power) is a `np.where` on the same condition;
- the FDMA branch (`rx_power - noise_power`, no interference) is kept;
- the greedy assignment sorts with `np.argsort(-sinr, kind="stable")` over the eligible flat
  positions, which reproduces `list.sort(key=sinr, reverse=True)` including its tie order
  (equal SINR keeps ascending `(uav, user)`); the harness checks this through the connection
  matrices, and the count of mismatches is `0` for every model.

RNG: `3gpp-36777` draws one `uniform(0, 1)` per (UAV, user) link per physical step inside the
path-loss formula. The vectorised path draws them as one `uniform(0, 1, size=(n_uavs, n_users))`
in row-major order, which is bit-identical to the scalar draw sequence and leaves the RNG state
equal (verified directly, and by `tests/uav_path_loss_cache_test.py`'s RNG-state assertions).
With `use_shadowing=True` the uniform and the normal draw interleave per link, so **that
combination still builds the path-loss matrix on the scalar path** and only the SINR arithmetic
is vectorised. The per-link cache dictionary is still filled for `3gpp-36777`, so one link keeps
exactly one realization per physical step for external per-link callers.

### P2 — `envs/pettingzoo/uav_env.py`

| Public name (unchanged) | Reference path (moved, unedited) | Vectorised path (new) |
| --- | --- | --- |
| `_get_local_users` | `_get_local_users_reference` | `_local_user_entries` |
| `_get_local_uavs` | `_get_local_uavs_reference` | `_local_uav_entries` |
| `_get_observation` | `_get_observation_reference` | `_get_observation_vectorized` |

`_local_user_entries` / `_local_uav_entries` read a row of `self.sinr_matrix` /
`self.uav_sinr_matrix`, apply the same `>= self.min_sinr` threshold and the same descending
order with the same stable tie order, and return `(indices, values)` arrays;
`_get_local_users` / `_get_local_uavs` wrap them back into the documented list of
`(index, sinr)` tuples for external callers. `_get_observation_vectorized` assembles the same
104-element layout (own position 3, users `20 × 3`, UAVs `10 × 4`, step 1) from precomputed
relative positions, writing each block as a reshaped view.

The vectorised observation path is taken only when `_vector_channel_state_is_current()` — the
SINR matrices carry the current path-loss generation and context; otherwise the scalar path
answers. So a subclass that calls `_get_observation` without a preceding `_update_channel_state`
keeps its old behaviour rather than reading a stale matrix.

### P3 — no code change

Fixture regeneration (§5), the test set (§6), and the repeated timing run (§7).

---

## 3. Harness numbers

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -s `
  tests/uav_env_channel_equivalence_test.py `
  --basetemp C:/Projects/HMASD/temp/pytest_uav_env_refactor -p no:cacheprovider
```

Live (vectorised) environment against the frozen reference tape, two 500-step episodes per
model, `n_uavs = 6`, `n_users = 50`:

| Channel model | SINR max abs diff | rewards | observations | state | positions > 1e-12 (all quantities) | connection mismatches |
| --- | --- | --- | --- | --- | --- | --- |
| `free_space` | 0.0 | 0.0 | 0.0 | 0.0 | 0 of 1,349,000 | 0 of 300,000 |
| `urban` | 0.0 | 0.0 | 0.0 | 0.0 | 0 of 1,349,000 | 0 of 300,000 |
| `suburban` | 0.0 | 0.0 | 0.0 | 0.0 | 0 of 1,349,000 | 0 of 300,000 |
| `3gpp-36777` | 0.0 | 0.0 | 0.0 | 0.0 | 0 of 1,349,000 | 0 of 300,000 |
| `probabilistic` | 0.0 | 0.0 | 0.0 | 0.0 | 0 of 1,349,000 | 0 of 300,000 |

Per model the tape holds 300,000 SINR positions, 300,000 connection positions, 6,000 rewards,
624,000 observation positions and 119,000 state positions.

**The result is stronger than the accepted tolerance.** The plan expected tolerance-level
equivalence at `1e-9`; the measurement is exact equality on every recorded quantity of every
channel model. Not one position moved by more than `1e-12`, because zero positions moved at all.
The ascending-index accumulation and the preserved dBm round trip are what make the arithmetic
identical rather than merely close, and `test_reference_backend_reproduces_the_tape` confirms the
scalar oracle is still available and still reproduces the tape exactly.

This is a measurement at this configuration, not a proof. At `n_uavs > 9` the interference sum
has eight or more terms and NumPy switches to a pairwise reduction, at which point the two paths
would differ in the last bits and the `1e-9` tolerance would start doing work. Scenario 1 as run
by the E-series uses six UAVs.

Per-step wall time recorded by the harness (not asserted):

| Measurement | Before (scalar) | After (P1) | After (P2) |
| --- | --- | --- | --- |
| `test_step_wall_time_is_reported`, 200 warmed steps, `free_space` | 24.585 ms | 5.762 ms | 0.470–0.482 ms |
| driving loop, `free_space` (1,000 steps incl. tape bookkeeping) | 14.3 ms | 5.43 ms | 0.55 ms |
| driving loop, `urban` | 14.1 ms | 5.52 ms | 0.53 ms |
| driving loop, `suburban` | 26.0 ms | 5.50 ms | 0.57 ms |
| driving loop, `3gpp-36777` | 25.0 ms | 6.31 ms | 1.16 ms |
| driving loop, `probabilistic` | 27.6 ms | 5.54 ms | 0.58 ms |

The spread across models in the "before" column (14–28 ms for formulas of near-identical scalar
cost) is machine noise inside one run, not a per-model effect; the warmed 200-step measurement is
the number to quote. Environment step: **24.6 ms → 0.48 ms, about 51×**, against the plan's
estimate of "1–3 ms".

---

## 4. What the vectorised backend changes besides speed

Declared, because CLAUDE.md's integrity rule asks for material assumptions to be stated:

1. **Scenario 2 and scenario 3 inherit the change.** The plan names `uav_env.py` and
   `scenario1.py` as the target, but `UAVCooperativeNetworkEnv` and `UAVMultiHopEnv` inherit
   `_update_channel_state` and `_get_observation` from `MultiUAVEnv`, so the default backend now
   serves them too. Their own methods (`_compute_uav_to_bs_sinr`, routing, backhaul, rewards)
   were not touched. `tests/uav_path_loss_cache_test.py` exercises all three scenarios and its
   bitwise cache-vs-reference oracle passes for each; there is no separate reference tape for
   scenarios 2 and 3. `channel_backend` is **not** threaded through their constructors, so they
   can only use the default (the base class attribute can still be set after construction).
2. **The relay environments are untouched.** `UAVRoutedRelayEnv`, `UAVForcedRelayEnv`,
   `UAVBeliefMapEnv`, `UAVEnergyAwareRelayEnv`, `UAVProgressiveRelayEnv` derive from
   `ParallelEnv` + `RelayChannelGeometry`, not from `MultiUAVEnv`. The plan's §5 statement about
   them holds trivially.
3. **The per-link cache dictionary is no longer filled for deterministic models.** The
   vectorised prime builds the two matrices and, for `3gpp-36777` only, also fills
   `_path_loss_cache` link by link (needed: one stochastic realization per link per step). For
   `free_space` / `urban` / `suburban` / `probabilistic` the dictionary stays empty, so an
   external per-link call recomputes the deterministic formula and is counted as a miss instead
   of a hit. **No value changes** — the formula is deterministic and the recomputation is
   bit-identical — only `_path_loss_cache_hits` / `_path_loss_cache_misses` and the dictionary's
   occupancy. `tests/uav_path_loss_cache_test.py` asserts relative counter movements and passes.
4. **`step_path_loss_cache=False` no longer suppresses the matrices.** Under the vectorised
   backend the two matrices *are* the evaluation mechanism, so they are built every step
   regardless of the flag; the flag still governs `_cache_path_loss`'s dictionary for per-link
   calls. Because the matrices are what both settings now read, `step_path_loss_cache=False` and
   `=True` produce identical output and identical RNG state, which is exactly what
   `test_reference_and_cache_paths_are_bitwise_equivalent` and the benchmark's oracle require.
   The consequence is that `tools/benchmarks/benchmark_uav_path_loss_cache.py` now compares two
   settings that do the same work: its `optimized_default_eligible` gate (optimized median
   strictly faster) is a coin flip, and `main()` may return 1 for that reason. The pytest
   contract (`test_benchmark_contract_runs_bitwise_oracle`) does not assert that gate and passes;
   `test_benchmark_main_always_fails_a_nonpositive_gate` monkeypatches the result. **Flagged for
   the owner**: that benchmark's premise no longer matches the default backend.
5. **`info["sinr_matrix"]` aliasing is preserved.** `_update_channel_state_vectorized` writes the
   new SINR values into the existing `self.sinr_matrix` object rather than rebinding it, so the
   views handed out in `infos` keep the pre-existing (aliasing) semantics. `self.connections` is
   rebound each step, as the scalar code already did.
6. **Nothing was changed in the reward, the observation layout, the RNG schedule, the config, or
   the learner.** `_compute_reward` in both `uav_env.py` and `scenario1.py` is untouched,
   including its per-pair Python loop; it is now a visible share of the remaining 0.48 ms and is
   the obvious next target if the environment is profiled again.

---

## 5. D2 fingerprint

Regenerated on the vectorised environment as the plan directed, after a passing preflight
(`temp/uav_refactor_preflight/preflight_p3_fixture.json`):

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe tests/flexible_skill_duration_d2_test.py
```

| Digest | Old (pre-refactor) | New (regenerated on the vectorised environment) |
| --- | --- | --- |
| canonical-JSON sha256 (what test 1 compares) | `3c525b9c3d26ef0385231c660f25a962eccdee87103feb39a4fc361dd225d937` | `3c525b9c3d26ef0385231c660f25a962eccdee87103feb39a4fc361dd225d937` |
| raw file sha256 | `6ba55c2eb310aa011f34933a1bc79566029a2db2dd2d461c18472ca0d7cf30b4` | `6ba55c2eb310aa011f34933a1bc79566029a2db2dd2d461c18472ca0d7cf30b4` |

**The fixture did not move.** `git status --porcelain tests/fixtures/flexible_skill_duration_d2/`
was empty afterwards, so the file in Git is still the phase-0 baseline produced before any D2
edit, and the one re-freeze the owner authorised in plan §6.1 remains unspent. The addendum
required by the plan is appended to `D2_IMPLEMENTATION_REPORT_20260902.md` and says the same
thing.

---

## 6. Tests

Each file run separately, same interpreter, `--basetemp C:/Projects/HMASD/temp/pytest_uav_env_refactor
-p no:cacheprovider`. A resource preflight (`scripts/hmasd_resource_preflight.py admit-memory
--out temp/uav_refactor_preflight/preflight_p3_tests.json`) passed immediately before the D2 file,
which builds models. Verbatim summary lines:

```
### tests/flexible_skill_duration_d2_test.py
13 passed, 14 warnings in 13.29s
### tests/relay_corridor_host_test.py
9 passed in 9.15s
### tests/relay_corridor_hmasd_test.py
4 passed, 14 warnings in 9.24s
### tests/uav_env_channel_equivalence_test.py
7 passed in 18.05s
### tests/uav_path_loss_cache_test.py
21 passed, 14 warnings in 1.19s
### tests/hmasd_r_mappo_utils_contract_test.py
5 passed in 2.05s
```

`tests/uav_path_loss_cache_test.py` and `tests/hmasd_r_mappo_utils_contract_test.py` are the
pre-existing tests that touch the UAV environment (found by searching `tests/` for
`UAVBaseStationEnv`, `MultiUAVEnv`, `scenario1`, `uav_env`); the first covers scenarios 1–3, both
cache settings, `free_space` and `3gpp-36777`, the 3GPP one-realization-per-link rule, the
seeding-isolation rules, the observation-space contracts and the benchmark contract.

---

## 7. E0 timing run, old versus new

Repeated exactly as `E0_EXPOSURE_PROBE_SET_RESULT_20260902.md` §2 ran it (the runner performs its
own resource preflight as its first action; both new runs wrote a passing `preflight.json`):

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_flexible_skill_duration_e0.py `
  --arm off --seed 1 --rollouts 2 --num-envs 32 --threads 1 `
  --run-name timing_off_1thread_vectorized `
  --output-root temp/directions/flexible_skill_duration/exp/E0_20260902

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_flexible_skill_duration_e0.py `
  --arm off --seed 1 --rollouts 2 --num-envs 32 --threads 4 `
  --run-name timing_off_4thread_vectorized `
  --output-root temp/directions/flexible_skill_duration/exp/E0_20260902
```

| Setting | collection s (r1, r2) | update s (r1, r2) | evaluation s | rollout+update mean s | 2-rollout wall s |
| --- | --- | --- | --- | --- | --- |
| 1 thread, before | 242.0, 241.7 | 330.9, 331.1 | 60.8 | 572.8 | 1209.3 |
| 1 thread, **after** | **19.1, 19.0** | 333.5, 335.8 | **5.3** | **353.7** | **714.6** |
| 4 threads, before | 239.7, 240.5 | 181.3, 182.8 | 61.0 | 422.2 | 908.4 |
| 4 threads, **after** | **19.1, 16.7** | 188.1, 187.9 | **4.4** | **205.9** | **418.5** |

Collection 241.9 s → 19.1 s (12.7×) at 1 thread and 240.1 s → 17.9 s (13.4×) at 4 threads;
evaluation 60.8 s → 5.3 s and 61.0 s → 4.4 s (about 12×); the whole 2-rollout wall time falls
1.69× at 1 thread and 2.17× at 4 threads. 4 threads remains the faster setting (1.72× per
rollout now, up from 1.36×, because the update is now the whole cost).

The update seconds moved by +0.8% (1 thread) and +3.6% (4 threads) against the old run. The
update code was not touched by this refactor; that drift is run-to-run machine variation, and it
sets the scale of the uncertainty on the collection and evaluation comparisons too (a few
percent, far below the 12× effect).

**Integrity cross-check.** Both new runs reproduced the old evaluation return mean exactly at the
same thread count: `40.09186398791525` at 1 thread and `39.84203863517143` at 4 threads,
bit-identical to `timing_off_1thread` / `timing_off_4thread`. Optimizer step counts, transitions,
episodes and the exposure line are unchanged. That is an independent confirmation, through the
whole learner, that the environment's numbers did not move.

Consequence for the E-series as sized in ADR 01 (32 lanes, 500 steps, 200 rollouts) at 4
threads: about 422 s per rollout before, about 206 s now, i.e. roughly 23 h → 11.4 h per arm.
The update is now 91% of a rollout at 4 threads (188 s of 206 s), which is the P4 decision the
plan defers to this measurement.

---

## 8. Plan-versus-code discrepancies

1. **Plan §2 says the channel model consumes no RNG** ("the environment's random draws are per
   reset and per user-movement step, none inside the channel model"). False for
   `3gpp-36777`: `_compute_path_loss_reference` draws one `uniform` per link per step, plus one
   `normal` per link when `use_shadowing` is on. Handled by drawing the uniforms as one
   row-major array (bit-identical stream) and by leaving the shadowing combination on the scalar
   matrix path. The base environment also never moves users, so the "per user-movement step"
   draws do not exist in scenario 1 either.
2. **Plan §1's profile attribution is confirmed**: `_get_local_users` did recompute
   `_compute_sinr` for every (UAV, user) pair a second time per step, and removing that
   duplication (P2) is where 5.76 ms → 0.48 ms came from, i.e. the larger half of the win.
3. **Tolerance was not needed.** The plan's §5 assumed array operations would change summation
   order and budgeted a fingerprint re-freeze. Ordering the interference accumulation by
   ascending interferer index and keeping the dBm round trip made the two paths bit-identical at
   the sizes in play, so the re-freeze did not happen (§5) and the `1e-9` allowance was never
   consumed.
4. **The plan's file scope understates the blast radius**: `uav_env.py` is the base class of
   scenarios 2 and 3, which therefore also switch to the vectorised backend by default (§4.1).
5. **`channel_backend` was appended to the end of `UAVBaseStationEnv.__init__`**, not inserted
   where the plan's prose might suggest, so that positional callers of `min_sinr`,
   `max_connections`, `coverage_weight`, `quality_weight` and `step_path_loss_cache` keep working.
6. **The path-loss cache benchmark's premise is now stale** (§4.4). It compares
   `step_path_loss_cache` False against True, which the vectorised backend makes equivalent in
   work as well as in output.

---

## 9. Could not verify

- **`3gpp-36777` with `use_shadowing=True` at the harness configuration.** Scenario 1 never
  enables shadowing (`MultiUAVEnv` defaults it to `False` and `UAVBaseStationEnv` does not expose
  it), so the harness does not cover it. By construction that combination falls back to the
  scalar matrix build, and it is covered only by
  `tests/uav_path_loss_cache_test.py::test_3gpp_realization_is_sampled_once_per_link_and_generation`
  at `n_uavs = 2, n_users = 2`, which passes. No tape exists for it.
- **`use_fdma=True`.** Not reachable from `UAVBaseStationEnv`'s constructor and not set anywhere
  in the repository; the vectorised FDMA branch was written from the scalar formula and is
  exercised by no test.
- **Three-column user positions.** `_user_position_components` implements the reference's
  "user already has a z" branch, but no environment in the repository produces such positions,
  so that branch is untested.
- **`n_uavs` above nine.** As §3 notes, the interference sum crosses NumPy's pairwise-reduction
  threshold there and exact equality is no longer expected; the harness runs at six.
  Scenario 3's defaults (`n_uavs = 20`) are past that line, and only its cache-vs-reference
  oracle (both sides vectorised) was checked, not a scalar-versus-vectorised comparison.
- **Whether the E0 timing difference is entirely the refactor.** The runs were taken on the same
  machine on the same day but not interleaved, and the untouched update phase drifted by up to
  3.6%, so the collection and evaluation ratios carry that same few-percent uncertainty.
- **P4** (the update phase) was not attempted, as instructed. At 4 threads the update is now 91%
  of a rollout, so the plan's own precondition for P4 ("only if measured to matter") is met.
- **`tests/production_backend_policy_test.py`** was not run; the D2 report already records it as
  failing for unrelated reasons (pinned C++ source digests under `experiments/candidates/*` with
  uncommitted changes from other work lines). Nothing in this refactor touches it.
