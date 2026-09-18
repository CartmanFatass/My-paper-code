# Findings: defects in existing code, observed while building the research-support suite

**Date:** 2026-09-18
**Status:** reported, **not fixed**. None of these was touched. They were found while reading
code the visualization suite had to consume, and fixing a scientific defect under a
visualization patch would hide it.

The separate, larger finding about `UAVForcedRelayEnv`'s downlink SINR has its own note:
[`2026-09-18-forced-relay-downlink-sinr-and-dead-backhaul-adjacency.md`](2026-09-18-forced-relay-downlink-sinr-and-dead-backhaul-adjacency.md).

Each item below states whether I confirmed it by reading the code myself.

---

## 1. A prepared dataset's arrays are authenticated; its metadata is not

**Confirmed directly.** `envs/uav_service_restoration/preprocess_milan.py:829-834`:

```python
content = hashlib.sha256()
content.update(PREPARED_SCHEMA_VERSION.encode("ascii"))
for name in sorted(arrays):
    content.update(name.encode("ascii"))
    content.update(np.ascontiguousarray(arrays[name]).tobytes())
content_hash = content.hexdigest()
```

`content_sha256` covers the schema version, the five array names and their bytes. `file_sha256`
covers the same five `.npy` files. **`metadata.json`, `splits.json` and `quality_report.json`
are covered by nothing.**

Consequences:

- `is_real_activity_data` is a metadata field. The guard in `PreparedDatasetDemandSource` that
  refuses a `milan_activity` preset over a non-real cache is therefore defeated by a
  one-character edit to a file no integrity check reads.
- `activity_reference_scale`, `kind`, `source_url` and `activity_field` are equally editable.
- **The train/validation/test date lists live in `splits.json`.** A split boundary can be moved
  after preparation and every reader check still passes — which is exactly the situation a
  held-out claim must be able to rule out.
- `_load_metadata` checks only that `_PREPARED_COMPLETE.json` exists. It never compares that
  marker's `content_sha256` against `metadata.json`'s, so a completion marker from a different
  preparation run is accepted.

Smallest fix: fold the three JSON documents into `content_sha256`, and have `_load_metadata`
compare the marker's hash with the metadata's.

## 2. "No evidence" is published as a measured zero in the quality report

**Confirmed directly.** `envs/uav_service_restoration/preprocess_milan.py:849,858`:

```python
"observed_fraction": float(observed.mean()) if observed.size else 0.0,
"total_activity":    float(activity[observed].sum()) if observed.any() else 0.0,
```

An empty or fully unobserved cache publishes `0.0` for both — indistinguishable from a
genuinely measured zero coverage and zero activity. The inconsistency is inside one dict: the
same block correctly uses `None` for `activity_quantiles` when there is nothing to quantile.

Smallest fix: `None` in both places, as the neighbouring field already does.

## 3. Episodes dropped from a mean are still counted in its *n*

**Confirmed directly.** `scripts/uav_service_restoration/evaluate_baselines.py:99-104`:

```python
"n_episodes": len(records),
"controller_satisfaction_mean": float(np.nanmean(satisfaction)) if satisfaction.size else None,
"controller_satisfaction_min":  float(np.nanmin(satisfaction))  if satisfaction.size else None,
"controller_satisfaction_max":  float(np.nanmax(satisfaction))  if satisfaction.size else None,
```

An episode whose satisfaction is NaN leaves both the numerator and the denominator of
`nanmean`, but remains in the published `n_episodes`. A reader cannot tell what the reported
mean's real sample size was. The censoring handling for recovery times in the same function is
done carefully and explicitly; this is only the NaN path.

Smallest fix: report the finite count alongside the statistic, or refuse the statistic when any
contributing episode is NaN.

## 4. Evaluation correctness depends on remembering `.eval()`, and one path does not call it

**Confirmed directly, with a caveat.** The observation and state normalisers mutate running
statistics, gated at `hmasd/agent.py:1376` and `:1428`:

```python
if self.training and update:
    ...
    self.state_norm.update(states_np)
```

`self.training` defaults to `True` (`hmasd/agent.py:1044`) and is changed only through the mode
setter at `:1068`. So the gate protects evaluation **only if** the caller sets eval mode.
`assign_skills` (`:1873`) and `select_action` (`:1800`) both call the normalisers with the
default `update=True`, while `:1789` and `:3570` correctly pass `update=False` — the safe and
unsafe uses sit side by side with no invariant enforcing the distinction.

`ha_ctse_process/standalone_evaluation.py` contains **no** `.eval()` or `train(False)` call
anywhere in the file (`_evaluate_impl` at `:78`).

**Caveat:** I did not trace whether some caller upstream of `_evaluate_impl` sets eval mode
before it runs, so I am not claiming a live defect — I am claiming the invariant is unguarded.
If nothing upstream sets it, then evaluating a model changes it. That is worth one deliberate
check, and a test pinning it either way.

The new `record-eval` command avoids the question entirely: it calls `.eval()` on every module
and runs under `torch.no_grad()`.

---

## Reported by reading passes, **not** independently confirmed here

These were raised by subagents that read the code while building parts of this suite. I did not
verify them myself; they are recorded so they are not lost, and each needs its own check before
anyone acts on it.

- `ha_ctse_process/checkpoint_io.py::load_checkpoint` can migrate an R30 runtime from a
  `legacy_duration` source by copying a whitelisted subset of parameters and leaving the rest
  randomly initialised — a partial load that a caller checking only "did it raise?" cannot
  distinguish from a faithful restore. It does record `checkpoint_migration_mode`.
- `hmasd/baselines.py:417 HeuristicBaselineAgent.load_model` returns successfully when the model
  file does not exist.
- `--episodes-file` carries two incompatible schemas across the repo: a bare list of integer
  seeds (`scripts/uav_service_restoration/evaluate_baselines.py`) and a list of episode objects.
- `envs/uav_service_restoration/demand.py` raises
  `DemandDataError(f"prepared cache is missing splits.json")` — an f-string with no
  placeholder. Cosmetic.
