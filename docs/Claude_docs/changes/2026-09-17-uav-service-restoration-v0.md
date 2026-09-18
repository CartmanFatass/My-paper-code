# `uav_service_restoration_v0` — implementation delivery report

Date: 2026-09-17. Branch: `main`. Interpreter for every command below:
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` (Python 3.10, NumPy, SciPy,
Gymnasium 1.0.0, PettingZoo 1.24.3). Nothing was installed into either conda environment.

Sources of requirement: `UAV_Service_Restoration_Plan_v1_EN.md` (design and acceptance
specification) and `Claude_Code_UAV_Service_Restoration_Prompt_EN.md` (task scope), both
read in full from `docs/Claude_docs/plans/UAV_Service_Restoration_English_Package.zip`.

## Status

| Field | Value |
| --- | --- |
| `ENVIRONMENT_IMPLEMENTED` | yes — P0–P6 complete |
| `OFFLINE_TESTS_VERIFIED` | yes — 255 passed, 0 failed |
| `LEGACY_NONREGRESSION_VERIFIED` | yes — both scenario fingerprints identical; no tracked file changed except `.gitattributes` |
| `DATA_NOT_VALIDATED` | yes — no real Telecom Italia Milan data is present on this machine |
| `ROLLOUT_ADAPTER_VERIFIED` | yes — the unmodified shared adapter accepts the environment |
| `TRAINER_INTEGRATION_PENDING` | yes — truncation bootstrap blocker, described below, not patched |
| `FORMAL_TRAINING_NOT_RUN` | yes — 0 training fits, 0 optimizer updates |

The owner's research pause was not touched: this is engineering work, no direction was
started or resumed, and no result-bearing run was launched.

## What was built

51 new files, one modified file. Every path is new except `.gitattributes`.

```
envs/uav_service_restoration/
  __init__.py  adapter.py  baselines.py  config.py  demand.py  dynamics.py  env.py
  evaluation.py  events.py  metrics.py  network.py  observations.py
  preprocess_milan.py  radio.py  scheduler.py  types.py  README.md
configs/uav_service_restoration/
  smoke_fixture.json  milan_site_outage.json  milan_temporary_pressure.json
  milan_rush_hour.json  preprocess_milan_reference.json  README.md
scripts/uav_service_restoration/
  _cli.py  inspect_data.py  prepare_milan.py  validate_dataset.py  smoke.py
  evaluate_baselines.py  legacy_baseline_fingerprint.py
tests/envs/uav_service_restoration/
  conftest.py  test_baselines_evaluation.py  test_causality.py  test_cli.py
  test_config.py  test_demand_sources.py  test_env_lifecycle.py  test_events.py
  test_integration_contracts.py  test_milan_preprocess.py  test_network_scheduler.py
  test_observations.py  test_radio_dynamics.py
tests/fixtures/uav_service_restoration/
  legacy_fingerprints/base_seed12345.json
  legacy_fingerprints/belief_map_seed12345.json
  milan_shaped_sample/{README.md, grid_small.geojson, activity_2013-11-01.txt,
                       activity_2013-11-02.txt, preprocess_small.json}
```

`envs/uav_service_restoration/README.md` is the reference for units, formulas, timing,
information conditions and the list of mechanisms **not** implemented.

### Deviations from the specified layout

- `evaluation.py` is an extra module the plan's file list does not name. The counterfactual
  references and the recovery/censoring rules were too large to put in `metrics.py` without
  that module doing two unrelated jobs.
- `scripts/uav_service_restoration/_cli.py` is shared CLI plumbing (path setup, the JSON
  writer, the exit-code contract), not one of the five named commands.
- `legacy_baseline_fingerprint.py` is the non-regression instrument, added so the
  preservation claim is reproducible rather than asserted.

### The one modification to an existing file

`.gitattributes`, +6 lines, scoped to the new paths only:

```
/tests/fixtures/uav_service_restoration/** text eol=lf
/configs/uav_service_restoration/*.json text eol=lf
```

Reason: `preprocess_milan.py` records `raw_file_sha256` for every input, so a fixture whose
checkout line endings vary would produce a different recorded provenance hash on a
different host. This follows the existing convention in that file for byte-addressed
inputs. It changes nothing for any pre-existing path.

## Legacy preservation

`git diff --stat` against the pre-work tree is empty apart from `.gitattributes`. Concretely
unchanged: `envs/pettingzoo/env_adapter.py`, `ha_ctse_process/env_factory.py`,
`ha_ctse_process/standalone_train_runner.py`, `ha_ctse_process/standalone_low_update.py`,
every legacy environment, every legacy config, every default entry point, and all
checkpoint-format code. `env_factory.SCENARIO_ALIASES` has no entry for this environment:
the new CLIs construct it explicitly, so nothing reaches it by accident.

Fingerprint check — a fixed seed, a fixed action sequence from a local
`numpy.random.Generator`, and a hash of what the adapter returns, driven through
`env_factory.make_env` exactly as the standalone trainer does:

```
$ python scripts/uav_service_restoration/legacy_baseline_fingerprint.py compare \
      --baseline tests/fixtures/uav_service_restoration/legacy_fingerprints/base_seed12345.json
LEGACY_FINGERPRINT_IDENTICAL                                                  (exit 0)
$ ... --baseline .../belief_map_seed12345.json
LEGACY_FINGERPRINT_IDENTICAL                                                  (exit 0)
```

Determinism claim: reproducible on the same machine, interpreter and dependency set. No
cross-platform bitwise claim is made.

Existing tests over the shared surfaces:

```
$ python -m pytest -q tests/scenario7_observation_adapter_test.py tests/sharded_vec_env_test.py \
      tests/ha_ctse_process_event_process_runner_test.py tests/gnn_trajectory_gae_test.py
25 passed, 1 skipped in 34.55s                                                (exit 0)
```

Import side effects are pinned by a test: after `import envs.uav_service_restoration`,
`torch`, `matplotlib`, `envs.uav_service_restoration.preprocess_milan`,
`...adapter`, `ha_ctse_process.env_factory` and `envs.pettingzoo.env_adapter` are all
absent from `sys.modules`, and the global NumPy RNG state is unchanged.

## Tests

```
$ python -m pytest -q tests/envs/uav_service_restoration/
255 passed in 236.54s (0:03:56)                                               (exit 0)
```

| File | Tests | Covers |
| --- | --- | --- |
| `test_config.py` | 30 | strict decoding, unknown-field rejection, every validator, all shipped presets |
| `test_radio_dynamics.py` | 17 | link budget, hard cutoffs, unit-ball clamping, substep equivalence |
| `test_network_scheduler.py` | 25 | the six hand-verifiable LP cases, monotonicity, topology gating, size limits |
| `test_events.py` | 13 | combination rule, boundaries, unrepaired events, sampling |
| `test_demand_sources.py` | 26 | fixture and prepared cache, hash verification, split overlap, real-data refusal |
| `test_milan_preprocess.py` | 34 | UTM forward/inverse, grid reading, ingestion accounting, cache writing |
| `test_env_lifecycle.py` | 25 | reset/step contract, spaces, determinism, probe snapshot, summary |
| `test_causality.py` | 7 | identical history / different future ⇒ identical obs and state |
| `test_observations.py` | 15 | masks, TTL, unknown ≠ zero, fixed order, entity limits, declared layout |
| `test_integration_contracts.py` | 19 | shared adapter, legacy fingerprints, import side effects, integration timing |
| `test_baselines_evaluation.py` | 22 | controller contract, information condition, references, recovery semantics |
| `test_cli.py` | 22 | `--help`, invalid arguments, missing data, real round trip, refusals |

### Hand-verified scheduler cases

All six pass with exact expected values: no path to core ⇒ 0; two 8 Mbps demands through a
10 Mbps bottleneck ⇒ 10; a half-duplex relay offered 20 Mbps ⇒ exactly 10, with a companion
test showing 20 when the domain constraint is removed; two UAVs serving one demand point ⇒
bounded by offered demand with airtime charged once; capacity and path-set monotonicity;
all site egress failed ⇒ 0 regardless of UAV placement.

Topology gating verified in the configured preset: every site dead with UAVs directly over
demand ⇒ 0 candidate paths; core link down with radio up ⇒ 0 paths; setting
`accepts_uav_wireless_backhaul = true` creates the reverse link but still yields no live
egress.

### Hand-verified geodesy and ingestion

UTM: a point on the central meridian projects to easting exactly 500000; the inverse round
trip closes to 1e-9 degrees; projected steps match local ellipsoidal metres-per-degree to
2e-3. The shaped grid fixture's cell spacing (2340 m × 2223 m) matches the analytic
expectation for its declared coordinates.

Ingestion accounting on the two-file shaped fixture: 94 raw rows, 92 accepted, 2 empty
fields, 2 missing rows, 276 missing intervals (= 2 × (144 − 6)), observed fraction 0.9583,
and country-code rows summed per cell-interval (13.0 + 12.5 = 25.5).

## Commands executed

Every command below was run in this checkout and its output observed. Nothing in the README
is described as runnable without having been run.

```
$ python scripts/uav_service_restoration/smoke.py \
      --config configs/uav_service_restoration/smoke_fixture.json --steps 32
exit 0
  api_test           {"num_cycles": 60, "output": ["Passed Parallel API test"], "performed": true}
  shapes             n_agents 3, obs_dim 103, state_dim 104, action_dim 3, n_demand_points 9
  scheduler_status   {"optimal": 32}
  data_status        NOT_REAL_DATA
  satisfaction_all   0.7916666666666664
  reward mean        -0.21573305541117277
  timing             1.68 s wall for 32 decision steps (0.0525 s/step)
  fits / updates     0 / 0

$ python scripts/uav_service_restoration/evaluate_baselines.py \
      --config configs/uav_service_restoration/smoke_fixture.json --episodes 2
exit 0   data_status NOT_REAL_DATA, seeds [0, 1], training_fits_performed 0

  controller                satisfaction  restored  recovered  censored  t_recovery
  backhaul_aware_greedy           0.9833    0.9373          2         0      38.0 s
  random                          0.9658    0.8718          0         2           -
  demand_greedy                   0.7333    0.0000          0         2           -
  static_uav                      0.7333    0.0000          0         2           -
  (all censored episodes: threshold_not_reached_within_episode)
```

Read those four rows as a property of this fixture, not as evidence about any algorithm.
They show three things worth having: the scenario has headroom (a static fleet loses ~27% of
offered service), the evaluator separates a controller that reasons about live backhaul from
one that does not, and the sustain requirement does real work — `random` restores 87% of the
lost volume on average yet never holds the threshold for 60 s, so it is censored rather than
credited.

`demand_greedy` matching `static_uav` exactly is correct and deliberate: it reads only
*reported* unmet demand, and the failed site's demand column is unsensed, so its target set
is empty and it never moves. That is the information condition biting, which is the point of
including it.

### Real-data commands, exercised on a shaped fixture

No real Milan data is present, so the real-data **code path** was exercised end to end on
the self-authored `milan_shaped_sample` fixture, which is labelled NOT REAL DATA in its own
README and in the cache it produces.

```
$ python scripts/uav_service_restoration/inspect_data.py \
      --input <fixture>/activity_2013-11-01.txt --grid <fixture>/grid_small.geojson \
      --config <fixture>/preprocess_small.json
exit 0   column_count_matches_declared true, timestamps_aligned_to_interval true,
         distinct_country_codes 2, crs urn:ogc:def:crs:OGC:1.3:CRS84,
         median nearest-neighbour spacing 2221.94 m

$ python scripts/uav_service_restoration/prepare_milan.py --input <both files> \
      --grid <fixture>/grid_small.geojson --config <fixture>/preprocess_small.json \
      --output <new dir> --not-real-data
exit 0   is_real_activity_data false, kind prepared_dataset,
         activity_reference_scale 63.2

$ python scripts/uav_service_restoration/validate_dataset.py --dataset <cache>
exit 0   verdict VALID, data_status NOT_REAL_DATA, all 7 checks true,
         splits {train 1, validation 0, test 1} disjoint,
         observed_fraction 0.9583, missing_rows 2, n_missing_intervals 276

$ python scripts/uav_service_restoration/validate_dataset.py --dataset <cache> \
      --config configs/uav_service_restoration/milan_site_outage.json
exit 3   verdict INVALID
         "source.kind is 'milan_activity' but the prepared cache declares
          kind='prepared_dataset'; synthetic data is never presented as real"

$ python scripts/uav_service_restoration/smoke.py \
      --config configs/uav_service_restoration/milan_rush_hour.json --steps 4
exit 3   "dataset_root does not exist: prepared_datasets\\milan_internet_v1. Run
          prepare_milan.py first; a fixture is not a substitute."
```

A `prepared_dataset` configuration over that cache runs the environment normally
(20 steps, 4 demand points, obs_dim 68, all solves `optimal`), which is what establishes
that the memory-mapped real-data route works. It is still not real data.

### Argument and failure paths

All checked; exit code 2 is usage/configuration, 3 is data, 4 is scheduler runtime.

| Invocation | Exit | Message |
| --- | --- | --- |
| any tool `--help` | 0 | usage printed |
| `smoke` / `evaluate_baselines` with no `--config` | 2 | `--config` is required |
| `prepare_milan` without a provenance flag | 2 | one of `--real-data` / `--not-real-data` is required |
| `smoke --steps 0` | 2 | `--steps must be positive` |
| `evaluate_baselines --episodes 0` | 2 | `--episodes must be positive` |
| `evaluate_baselines --controllers oracle` | 2 | `invalid choice` |
| `inspect_data --max-rows 0` | 2 | `--max-rows must be positive` |
| `prepare_milan` with a duplicate `--input` | 2 | `records are never double-counted` |
| `prepare_milan --output <existing>` | 2 | `already exists` |
| `smoke --output <existing>` | 2 | `already exists` (report not overwritten) |
| `smoke --config <missing>` | 3 | `not found` |
| `validate_dataset --dataset <missing>` | 3 | `not found` |
| `validate_dataset` on an incomplete cache | 3 | names `_PREPARED_COMPLETE.json` |
| real-data preset without a cache | 3 | `a fixture is not a substitute` |

A change made during this exercise: `prepare_milan.py` originally defaulted to *real*
provenance, and a first run marked a fixture-derived cache `is_real_activity_data: true`.
That cache was deleted and the flag made a required mutually exclusive choice, so provenance
can never be claimed by omission. The `--help` refusal is now a test.

## Data status: `DATA_NOT_VALIDATED`

No real Telecom Italia Milan activity file or Milano Grid GeoJSON is present in this
checkout or on this machine. Therefore:

- No real-data experiment was run, and none is claimed.
- The declared column mapping in `preprocess_milan_reference.json` is a **declaration to be
  verified** against the version actually downloaded, not a verified fact. `inspect_data.py`
  exists precisely to check it; a mismatched column count is refused rather than guessed.
- The parser, the projection, the quality accounting, the cache writer, the memory-mapped
  reader, the split logic and the demand mapping are all implemented and tested — on the
  shaped fixture, which is labelled NOT REAL DATA everywhere it appears.
- Nothing silently substitutes a fixture for a real-data configuration. That refusal is
  enforced in three independent places (config validation, `PreparedDatasetDemandSource`
  kind/real checks, and the CLI pre-check) and tested.

## Calibration status

`config.calibration_summary()` reports every radio model as `engineering_assumption`; none
is `empirically_calibrated`. The link model is a log-distance path loss with a Shannon
capacity and a hard range/SNR cutoff — a verifiable geometric model, explicitly not a
cellular physical layer. No fading, interference across domains, MIMO, MAC scheduling or
power control. A delivered-Mbps figure is a property of this model and is not a prediction
about any real network.

Diagnostic provenance: every number in this report is `fixture_based`. Each rollout record
carries `episode.provenance` and `episode.is_real_activity_data` so this cannot be lost
downstream.

## Blocker: trainer integration

**Not patched, by instruction.** Correct integration would require changing shared training
semantics, so the independent environment is complete and the boundary is reported instead.

Where: `ha_ctse_process/standalone_train_runner.py:453-456`

```python
done = bool(terminated or truncated)
```

and `ha_ctse_process/standalone_low_update.py:138-142`

```python
if bool(dones[idx]):
    next_value = default_bootstrap
    next_nonterminal = 0.0
```

Why it matters here: `uav_service_restoration_v0` uses `episode.semantics = "continuing"`.
It never terminates; at the end of the external data window every agent is **truncated**. A
time-limit truncation is not the end of the world, so zeroing `next_nonterminal` discards
the bootstrap value and biases the GAE value targets low at every window boundary. Running
this environment through the standalone trainer as it stands would fit on biased targets.

This is not a defect *for the legacy environments*, which terminate rather than truncate;
that is why no change was made.

### Minimal patch proposal (not applied)

Stated against the code as it is, not against a sketch. `standalone_low_update` already has
the bootstrap machinery it needs: `final_bootstrap`, read from
`rollout.bootstrap_values[env_id]`, is used at the last position of a segment when that
step is *not* flagged done. The defect is only that `dones` cannot distinguish the two
reasons, so a truncation takes the zeroing branch.

1. In `standalone_train_runner.py:456`, keep `done = bool(terminated or truncated)` for
   every existing consumer, and additionally record `terminated` and `truncated` per step
   into separate rollout buffers.

2. In `standalone_low_update.py:138-142`, split the branch. For the common case — a
   `continuing` environment truncated at the end of a rollout segment — no new per-step
   value is needed, because `final_bootstrap` is already the value of the next observation:

   ```python
   if bool(terminateds[idx]):
       next_value = default_bootstrap        # a real terminal state: value is zero
       next_nonterminal = 0.0
   elif bool(truncateds[idx]):
       # A time limit is not a terminal state. Bootstrap through it, but give no credit
       # across the boundary.
       next_value = (
           final_bootstrap if pos + 1 == indices.size
           else truncation_bootstrap_values[idx]
       )
       next_nonterminal = 0.0
   ```

3. A truncation *inside* a segment needs the value of the observation that follows it,
   which nothing stores today. The runner already holds `next_obs` at that step, so it
   would evaluate the low-level critic there and store the result in a new
   `truncation_bootstrap_values` mapping keyed by rollout index. Whether this case arises
   depends on whether the episode horizon aligns with the rollout length, so it cannot be
   assumed away.

4. Default both new buffers to all-False / empty, so any caller that does not supply them
   takes exactly today's branch and reproduces today's arithmetic bit for bit.

5. Guard with an identity test: an existing terminating scenario must produce byte-identical
   advantages and returns before and after. The two fingerprints in
   `tests/fixtures/uav_service_restoration/legacy_fingerprints/` cover the environment side
   of that boundary; the GAE side would need its own.

Until that is decided by whoever owns shared training semantics, the supported use of this
environment is forward-only: `smoke.py`, `evaluate_baselines.py`, and the diagnostic
controllers. That is what was run here.

## Budget

0 training fits. 0 optimizer updates. 0 gradients. The only compute spent was tests
(237 s + 35 s), the smoke and baseline commands (~44 s), and the CLI checks. No detached
run, no node launch, no memory preflight — none was needed, since nothing result-bearing
was executed.

## Scratch

`temp/uav_service_restoration/` was used for the CLI round-trip check and removed.
Test scratch is `tmp_path`-managed and cleaned by the session's own teardown.
