# `uav_service_restoration_v0` presets

`smoke_fixture.json` is self-contained: the demand trace is an analytic fixture generated
in process, so it needs no dataset path and no download. Use it for smoke runs, tests and
API checks. Nothing derived from it is a result about real demand.

`preprocess_milan_reference.json` is the ingestion configuration for the real dataset. It
declares the column mapping, the region bounding box, the missing-data policy and the
train/validation/test dates. **Verify the column mapping and the dates against the exact
published version you download before trusting a run**; the split dates below are a
placeholder weekday/held-out arrangement, not a validated choice.

The three real-data presets require an explicit local `dataset_root` and fail with a
specific error when it is absent. They never fall back to the fixture.

| preset | window | split | network process |
|---|---|---|---|
| `milan_site_outage.json` | 30 min | `test` | one site fails completely between 300 s and 600 s and is not repaired |
| `milan_temporary_pressure.json` | 2 h | `train` | one site's access capacity degraded to 0.4 for an hour, plus a `synthetic_overlay` demand envelope |
| `milan_rush_hour.json` | 2 h | `test` | unchanged terrestrial network |

What is real and what is not, in every real-data preset:

* real: the spatial and temporal variation of aggregated Internet activity;
* simulated: the mapping from activity to an offered rate in Mbps, the terrestrial
  topology, the site capacities, the failures, the propagation model, the resource
  sharing, and the UAV dynamics.

The site positions, egress capacities, radio parameters, failure timings and deployment
positions in these files are engineering assumptions chosen to exercise the mechanism.
They are recorded under `parameter_provenance` and reported separately from anything
calibrated. Before a real run, read the prepared cache's `metadata.json` and
`quality_report.json` and reconcile `region`, `source.max_demand_points`, the candidate
path limits and the site positions with the extent and cell count the cache actually has.
