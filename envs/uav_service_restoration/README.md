# `uav_service_restoration_v0`

An independent multi-UAV service-restoration environment. Terrestrial cell sites fail from
an exogenous schedule; UAVs fly to restore access service to aggregated demand points,
relaying through surviving sites or each other. A single fixed path-flow linear program
decides delivered service, identically for every control method.

This package is self-contained. It adds no dependency, changes no legacy file, and is not
reachable from any existing entry point: nothing constructs it unless you name it.

- Python: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` (NumPy, SciPy, Gymnasium
  1.0.0, PettingZoo 1.24.3). No GIS package is required — see
  [Milan preprocessing](#milan-preprocessing).
- No torch import anywhere in this package. The environment, the evaluator and the
  diagnostic controllers are forward-only.

## Contents

| Module | Responsibility |
| --- | --- |
| `config.py` | Strict dataclass configuration; unknown fields are refused |
| `types.py` | Value types shared across modules; no logic |
| `radio.py` | Pure link-budget functions |
| `demand.py` | Demand sources: self-contained fixture, prepared read-only cache |
| `preprocess_milan.py` | Raw Milan activity → prepared cache; UTM projection; quality report |
| `events.py` | Exogenous capability events and their combination rule |
| `network.py` | Graph construction, candidate paths, shared-resource domains |
| `scheduler.py` | The fixed path-flow LP |
| `dynamics.py` | Action clamping and motion integration |
| `metrics.py` | Per-subinterval accumulation and the episode summary |
| `observations.py` | Telemetry store, observation and state assembly, masks |
| `env.py` | The PettingZoo `ParallelEnv` |
| `adapter.py` | `make_parallel_env` / `make_array_env` over the shared adapter |
| `baselines.py` | Non-learning diagnostic controllers |
| `evaluation.py` | Counterfactual references and the recovery verdict |

`evaluation.py` is an addition to the layout the design document lists: the counterfactual
references and the recovery/censoring rules were too large to leave inside `metrics.py`
without making that module do two jobs.

## Units and conventions

Field names carry their unit. Every quantity below is in these units throughout.

| Suffix | Unit |
| --- | --- |
| `_m` | metres |
| `_s` | seconds |
| `_hz` | hertz |
| `_mbps` | megabits per second (10⁶ bit/s) |
| `_mbit` | megabits |
| `_dbm`, `_db` | dBm, dB |
| `_utc_ms` | integer milliseconds since the Unix epoch, UTC |

Positions are a local Cartesian frame in metres: `x` east, `y` north, `z` altitude above
the ground plane, origin at `region.min_xy_m`. Demand points sit at `z = 0`. Distances are
3-D Euclidean. Time-of-day labels use `Europe/Rome`; the time *axis* is always integer UTC
milliseconds.

## Radio model

A log-distance path-loss model with a Shannon capacity. This is a **verifiable geometric
link model, not a cellular physical layer**: there is no fading, no interference between
transmissions in different resource domains, no MIMO, no scheduler at the MAC layer, no
mobility-induced Doppler, and no per-user power control.

```
PL(d)   = reference_loss_db + 10 · n · log10(d / reference_distance_m) + extra_loss_db
N       = -174 + 10 · log10(bandwidth_hz) + noise_figure_db        [dBm]
SNR     = tx_power_dbm + antenna_gain_db - PL(d) - N               [dB]
C       = spectral_efficiency · bandwidth_hz · log2(1 + SNR_linear) / 1e6   [Mbps]
```

`C` is exactly zero beyond `max_range_m` or below `min_snr_db` — a hard cutoff, not a
taper. `antenna_gain_db` is a single combined transmit-plus-receive gain, applied once.

Every radio model carries a `calibration_status`. In all shipped presets it is
`engineering_assumption`: the parameters are plausible and internally consistent, and they
have **not** been fitted to measurements. `config.calibration_summary()` reports this split
and the CLIs print it. Treat a delivered-Mbps number as a property of this model, never as
a prediction about a real network.

Four named models are configured independently: `site_access`, `uav_access`,
`site_uav_backhaul`, `uav_uav_backhaul`.

## Network and the fixed scheduler

The graph is: a single core source → terrestrial sites → (optionally UAVs, by wireless
backhaul) → aggregated demand points.

Terrestrial capability is four independent fields per site
(`radio_up`, `core_link_up`, `access_capacity_scale`, `backhaul_capacity_scale`), and they
gate distinct edges:

| Field | Gates |
| --- | --- |
| `radio_up` | every radio function of the site: access **and** UAV backhaul |
| `core_link_up` | the wired core → site edge |
| `access_capacity_scale` | the site → demand access edges |
| `backhaul_capacity_scale` | the core → site wired edge **and** the site → UAV wireless edge |

A fully failed site therefore neither serves access nor forwards traffic. Losing wired
backhaul does **not** make a site able to accept wireless backhaul from a UAV: that
capability exists only where `accepts_uav_wireless_backhaul` is explicitly true, and it is
false in every shipped preset. There is no airborne core: with every site's egress down,
delivered service is exactly zero however the UAVs are placed.

Delivered service is a linear program over enumerated candidate paths, solved once per
subinterval:

```
maximise    Σ_p rate_p  -  ε · Σ_p (normalised resource cost of p) · rate_p
subject to  Σ_{p → i} rate_p ≤ offered_demand_i          for each demand point i
            Σ_{p ∋ l} rate_p ≤ capacity_l                for each link l
            Σ_{l ∈ D} (Σ_{p ∋ l} rate_p) / capacity_l ≤ 1 for each resource domain D
            rate_p ≥ 0
```

The ε term is a tie-break toward cheaper paths; because the resource cost is normalised to
`[0, 1]`, it bounds the relative loss in delivered service by `secondary_weight`. Paths are
enumerated cycle-free with a hop limit that counts **wireless backhaul edges only**.
Exceeding `max_candidate_paths_per_demand` or `max_total_candidate_paths` raises
`SchedulerSizeLimitError`: the path set is never silently truncated, because a truncated set
would quietly change what "achievable" means.

Resource domains are what make airtime finite. Each node has an access domain over its
access links. Each UAV has one backhaul domain covering its incoming **and** outgoing
backhaul links, which is half duplex: a relay that receives 20 Mbps and forwards it
delivers 10 Mbps, not 20. Access and backhaul share a band only if
`access_and_backhaul_share_band` is set.

Exact solves use a method ladder (`highs`, `highs-ds`, `highs-ipm`) and the result reports
`solver_method_used`. A solve that no method resolves raises `SchedulerSolveError`; it never
returns a partial allocation as if it were optimal.

## Timing and integration

Three timescales, all explicit:

- `decision_dt_s` — one agent action per decision step.
- `physics_dt_s` — motion substeps inside a decision step.
- the source interval (600 s for both shipped sources) — how often offered demand changes.

Each decision interval is partitioned at event boundaries, demand-interval boundaries, and
then `physics_dt_s` substeps. Each subinterval is solved once with the **midpoint** UAV
position (`quadrature: "midpoint"`; `"left"` is available for comparison) and the volume
credited is `rate × subinterval duration`. So a long decision interval is not credited at
the UAV's end position, and motion inside the interval is not ignored either — both
directions are pinned by tests in `test_integration_contracts.py`.

Motion: the action is a normalised 3-D velocity request, clamped to the **unit ball** (not
per-axis), so a diagonal request cannot exceed `max_speed_mps`. Altitude and the region
rectangle are hard bounds; the realised velocity reported back is the achieved displacement
divided by `dt`, not the request.

Episode semantics: `continuing` (the default) never terminates. At the end of the external
window every agent is `truncated`, and the real terminal observation is returned. See
[Trainer integration](#trainer-integration) — this is where the one open blocker is.

## Information condition

Default mode `central_delayed_telemetry`. The learner never sees the exogenous future.
Excluded by construction: future demand intervals, future or scheduled events, the episode
id or source cursor, offered demand at unsensed demand points, and all privileged state.

- A 600 s source aggregate does not become an observation at the start of its window.
  Telemetry is per-entity, with an explicit measurement `age_s` and a TTL
  (`telemetry_ttl_s`); past the TTL the entity's `observed_mask` goes to 0.
- **Unknown is not zero.** An unobserved demand point reports `observed_mask = 0`,
  `offered = 0`, `slot_valid_mask = 1` — meaning "this slot exists and we do not know",
  which is distinguishable from a known-idle point.
- A demand point is sensed if within `sensing_radius_m` of a UAV, or registered if within
  `site_access_radius_m` of a site whose radio is up.
- Temporal causality is a test, not a claim: two episodes with identical history and
  different futures produce byte-identical observations and states
  (`test_causality.py`).

Observation is 103 floats and state 104 in the smoke preset (both depend on entity counts);
`env.schema()` reports the exact block layout, and `env.get_obs_dim()` / `get_state_dim()`
are what the adapter reads. Entity order is fixed. Exceeding an entity limit raises
`EntityLimitExceeded` unless `on_entity_limit_exceeded` is `"aggregate"`, which performs a
demand-conserving contiguous aggregation.

`get_current_state()` is the leak-free diagnostic view a controller may read.
`get_privileged_diagnostics()` is the evaluator channel and carries the episode id, dataset
hash and the true event list; it is never merged into an observation or into `info`.

## Reward

```
reward = -(unmet Mbit over the interval) / (reference_scale_mbps · reference_dt_s)
         - motion_weight · (motion effort in s) / reference_dt_s
```

One identical team scalar per agent, never divided by `n_uavs`. This matters for the shared
adapter, which reduces a reward dict by the **mean** over agents: a uniform team reward
passes through unchanged. `motion_weight` defaults to 0 and requires a written
`motion_weight_rationale` before it may be non-zero. `info["reward_info"]` carries the nine
decomposition fields so the two terms can always be separated.

## Demand sources

Both are explicit; `source.kind` has no default.

**`synthetic_fixture`** — a self-contained analytic fixture. NOT real data: no Telecom
Italia record, no measured traffic, no population count. Used by `smoke_fixture.json` and
by the offline tests.

**`milan_activity`** / **`prepared_dataset`** — a read-only memory-mapped cache produced by
`prepare_milan.py`. `reset`/`step` never parse a raw file. The cache's declared per-file
SHA-256 hashes are verified on open, and `milan_activity` refuses a cache that is not marked
`is_real_activity_data`. There is **no synthetic fallback**: a missing dataset raises.

Demand mapping, fitted on the training split only:

```
d_i = demand_scale_mbps · activity_i / activity_reference_scale
```

`activity_reference_scale` is a quantile of strictly positive observed training activity.
`demand_scale_mbps` is a **simulated load scale, not measured Mbps**. No slice is
normalised to sum to 1, and nothing is rescaled in response to a failure or to a policy's
score.

## Milan preprocessing

`preprocess_milan.py` uses only the standard library and NumPy. GeoJSON is parsed with
`json`; the WGS84 → UTM projection is a self-contained transverse-Mercator series verified
against known values in `test_milan_preprocess.py`. **There is no optional GIS dependency**
(no `shapely`, `pyproj` or `geopandas`), so there is no missing-optional-dependency failure
path — a deliberate choice to keep the real-data path installable everywhere.

What the preprocessing does and records:

- Verifies the declared column mapping against the file; a mismatched column count is
  refused, not guessed. Run `inspect_data.py` first.
- Internet activity is the only v0 signal. SMS and call activity are not summed into it.
- Country-code rows are summed per `(square_id, time_interval)`: the country code is a
  dimension of the same cell, never a separate location. Duplicate input paths are refused.
- Explicit zeros, empty fields, missing rows and missing intervals are counted **separately**
  in `quality_report.json`. Missing values are not set to zero; `observed_mask` marks them
  unknown.
- Splits are complete UTC dates, disjoint by construction, and the reference scale is fitted
  on training dates only.
- Provenance recorded in `metadata.json`: raw-file SHA-256, source URL, licence note,
  dataset version, schema, CRS and local origin, region-selection rule, column mapping,
  aggregation and duplicate rules, parameters, and a content hash over all arrays.
- The completion marker is written last, so a reader that finds it knows the cache is whole.
  An existing output directory is refused.

Raw files and caches are **not** committed. The publisher's licence governs the data and is
separate from this repository's code licence.

## Evaluation

For each rollout the evaluator recomputes two references over the identical exogenous world,
with no UAVs: the **healthy** trace (the failure removed) and the **failed** trace. The
affected demand set is where their delivered volumes differ — a definition that does not
mention the evaluated policy, so two controllers produce byte-identical references.

Recovery is declared at the first instant at or after the first capability loss where the
controller delivers at least `recovery_fraction_rho` of the healthy reference on the
affected set, and keeps doing so for `recovery_sustain_s`. Instants where the healthy
reference delivers nothing on the affected set carry no evidence: they are never divided by,
they may bridge a sustain window, and they may not open one; their count is reported.

Censoring is explicit, never a zero: `threshold_not_reached_within_episode`,
`repaired_before_recovery_threshold_reached`,
`threshold_first_met_after_automatic_repair`, `episode_ended_before_failure`. An automatic
repair is therefore never credited to a UAV.

`energy_joules` is `None`, with `energy_status` stating why: v0 implements no battery or
hover-power model. `motion_effort_integral_s` is a time integral, not energy.

## Commands

All verified against this checkout; see `docs/Claude_docs/changes/` for the recorded run
output. Use the repository's chosen interpreter and run the scripts by path.

```powershell
$py = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe'

# Needs no download: the self-contained fixture.
& $py scripts/uav_service_restoration/smoke.py `
    --config configs/uav_service_restoration/smoke_fixture.json --steps 32

& $py scripts/uav_service_restoration/evaluate_baselines.py `
    --config configs/uav_service_restoration/smoke_fixture.json --episodes 2

# Real data. Inspect before preparing; the provenance claim is required, never a default.
& $py scripts/uav_service_restoration/inspect_data.py `
    --input <raw_activity_file> --grid <milano-grid.geojson> `
    --config configs/uav_service_restoration/preprocess_milan_reference.json

& $py scripts/uav_service_restoration/prepare_milan.py `
    --input <raw_file> [<raw_file> ...] --grid <milano-grid.geojson> `
    --config configs/uav_service_restoration/preprocess_milan_reference.json `
    --output <new_cache_dir> --real-data

& $py scripts/uav_service_restoration/validate_dataset.py --dataset <cache_dir>

& $py scripts/uav_service_restoration/evaluate_baselines.py `
    --config configs/uav_service_restoration/milan_site_outage.json `
    --dataset <cache_dir> --episodes-file <heldout_episode_seeds.json>

& $py -m pytest -q tests/envs/uav_service_restoration/
```

Exit codes: `0` success, `2` usage or configuration, `3` data, `4` runtime (scheduler).

The three Milan presets (`milan_site_outage`, `milan_temporary_pressure`,
`milan_rush_hour`) each require a local prepared cache and will not fall back to a fixture.

## Integration with the existing repository

`make_array_env` wraps the environment in the **unmodified** shared
`envs.pettingzoo.env_adapter.ParallelToArrayAdapter`. `ServiceRestorationArrayAdapter`
subclasses it and adds read-only passthroughs only — it overrides no adapter behaviour.
`ha_ctse_process.env_factory` is untouched and has no alias for this environment: the CLIs
construct it explicitly.

### Trainer integration

**Open blocker.** `standalone_train_runner.py:456` collapses `terminated or truncated` into
one `done` flag, and `standalone_low_update.py:140-142` then sets
`next_nonterminal = 0.0` and discards the bootstrap value. For a `continuing` task that is
wrong: a time-limit truncation is not the end of the world, so dropping the bootstrap biases
the value targets low at every window boundary.

The environment is left as it is — correct truncation semantics — and no legacy training
file was modified. Running this environment through the standalone trainer as it stands
would fit on biased value targets. The minimal patch is to carry `truncated` separately and
bootstrap on it; that is a change to shared training semantics and is not made here.

## Not implemented in v0

Deliberately absent, so nothing in this package is mistaken for it:

- battery, hover power, energy or charging rotations (`energy_joules` is `None`)
- collision avoidance and any safety constraint beyond the region box and altitude bounds
- fading, interference across resource domains, MIMO, MAC-layer scheduling, power control
- learned or distributed routing — the scheduler is fixed for every control method
- variable UAV count or variable skill duration; `n_uavs` is fixed and the action space is a
  fixed 3-D velocity
- individual trajectories or mobility traces (NetMob23, SUMO), ns-3, or any packet simulator
- SMS and call activity as demand signals
- a cellular physical layer, and any claim that delivered Mbps predicts a real network
