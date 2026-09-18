"""Reader for the UAV service-restoration diagnostic evaluation report.

The producer is ``scripts/uav_service_restoration/evaluate_baselines.py``, and the per-episode
record shape comes from ``envs/uav_service_restoration/evaluation.py::evaluate_rollout()``:
``episode``, ``exogenous_events``, ``references``, ``affected_points``, ``recovery``,
``episode_summary``, ``calibration_summary``, plus the ``controller`` block that
``rollout_controller`` attaches and the ``episode_seed`` the CLI attaches.

The single most important thing this reader does is **label what these numbers are**.  They
are forward-only rollouts of untuned rule controllers - the report itself says
``training_fits_performed: 0``, ``optimizer_updates: 0`` and carries an
``interpretation_note`` to that effect.  Read carelessly, a table of "controller
satisfaction mean over 20 episodes" looks exactly like a table of twenty independent
learning results.  Every record therefore gets ``phase=DIAGNOSTIC_ROLLOUT``, no
``training_replicate_id``, and a ``statistical_unit_kind`` field that says in words that an
episode here is not a training replicate.

Two further honesty rules follow the producer's own semantics:

* ``time_to_recovery_s_mean_over_recovered`` is ``None`` when nothing recovered.  That is an
  absence, never zero seconds: the CLI's own ``aggregation_rule`` says a censored episode is
  never counted as a recovery of zero.
* The report records the *path* of the configuration, not a hash of its content, so
  ``initial_world_config`` stays ``NOT_RECORDED`` and pairing can only ever be
  ``pairing_unverified`` from this family alone.

Static only: JSON parsing.  The environment is never imported and no episode is re-run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from tools.research_support.readers import (
    FIELD_AGENT_COUNT,
    FIELD_ALGORITHM,
    FIELD_ARTIFACT_LOCATIONS,
    FIELD_CHECKPOINT_IDENTITY,
    FIELD_CHECKPOINT_SELECTION,
    FIELD_COMPLETION_STATUS,
    FIELD_DATASET,
    FIELD_ENVIRONMENT,
    FIELD_EPISODE_INTERVAL,
    FIELD_EVALUATION_POLICY_MODE,
    FIELD_EVALUATION_SEED,
    FIELD_EVALUATION_WORLD,
    FIELD_EVENT_REALIZATION,
    FIELD_HORIZON,
    FIELD_INFORMATION_CONDITION,
    FIELD_INITIAL_WORLD_CONFIG,
    FIELD_METRIC_SEMANTICS,
    FIELD_REWARD_DEFINITION,
    FIELD_ROUTE,
    FIELD_SOURCE_SHA,
    FIELD_SPLIT,
    FIELD_STATISTICAL_UNIT,
    FIELD_TERMINATION_DECLARED,
    FIELD_TERMINATION_OBSERVED,
    FIELD_TRAINING_EXPOSURE,
    FIELD_TRAINING_SEED,
    FIELD_UNIT_DEFINITION,
    ReadResult,
    UnsupportedSourceError,
    boundary_measures,
    boundary_semantics,
    default_run_id,
    dig,
    ensure_identity_fields,
    flatten_scalars,
    joined_locations,
    load_json_file,
    measured_text,
    register_source,
    unit_from_key_name,
    world_identity_hash,
)
from tools.research_support.records import (
    AggregationLevel,
    Measured,
    MetricRecord,
    Phase,
    RunRecord,
    XKind,
)

#: Marker the producer writes as the first key of its report.
TOOL_MARKER = "evaluate_baselines"

#: Bytes read from a candidate file before deciding to parse it fully.  Keeps detection
#: cheap in a directory that also holds large unrelated JSON.
_SNIFF_BYTES = 8192

#: Preferred file names, tried before any other ``*.json`` in the directory.
_PREFERRED = (
    "evaluate_baselines.json",
    "baselines.json",
    "service_restoration_baselines.json",
)

#: Keys of one per-episode record that are identity or structure, not measurements.
_EPISODE_SKIP = frozenset({"episode", "calibration_summary", "controller", "episode_seed"})

#: Aggregate keys the reader labels as counts of episodes rather than measurements.
_COUNT_KEYS = frozenset(
    {"n_episodes", "n_recovered", "n_censored", "n_not_applicable"}
)


class ServiceRestorationReader:
    """Reads one ``evaluate_baselines`` report into per-controller diagnostic records."""

    name = "service_restoration_eval"
    version = "1"

    # Detection -----------------------------------------------------------------------

    def detect(self, root: Path) -> bool:
        return self._locate(Path(root)) is not None

    def _candidates(self, root: Path) -> list[Path]:
        if root.is_file():
            return [root] if root.suffix == ".json" else []
        if not root.is_dir():
            return []
        preferred = [root / name for name in _PREFERRED if (root / name).is_file()]
        others = sorted(
            path for path in root.glob("*.json") if path.is_file() and path not in preferred
        )
        return preferred + others

    def _locate(self, root: Path) -> Path | None:
        """First file that actually declares itself an ``evaluate_baselines`` report."""

        for path in self._candidates(root):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    head = handle.read(_SNIFF_BYTES)
            except OSError:
                continue
            if TOOL_MARKER not in head:
                continue
            try:
                payload, _ = load_json_file(path)
            except (OSError, ValueError):
                continue
            if (
                isinstance(payload, Mapping)
                and payload.get("tool") == TOOL_MARKER
                and isinstance(payload.get("controllers"), Mapping)
            ):
                return path
        return None

    # Reading -------------------------------------------------------------------------

    def read(self, root: Path) -> ReadResult:
        root = Path(root)
        result = ReadResult()
        result.coverage.update(
            {"reader": self.name, "reader_version": self.version, "root": str(root)}
        )
        path = self._locate(root)
        if path is None:
            for candidate in self._candidates(root):
                result.note_file(
                    candidate,
                    "unsupported",
                    detail=f"not an {TOOL_MARKER} report (no tool marker or no controllers block)",
                )
            raise UnsupportedSourceError(
                f"{root} holds no {TOOL_MARKER} report; this reader requires a JSON object "
                f"with tool=={TOOL_MARKER!r} and a controllers block"
            )

        payload, warnings = load_json_file(path)
        result.warnings.extend(warnings)
        controllers = payload.get("controllers") or {}
        per_episode = payload.get("per_episode") or {}
        result.coverage["report_path"] = str(path)
        result.coverage["controllers"] = sorted(map(str, controllers.keys()))
        result.coverage["has_per_episode_records"] = bool(per_episode)
        if not per_episode:
            result.warnings.append(
                "the report holds aggregates only (--per-episode was not used): dataset hash, "
                "event realisation and per-episode values are unavailable, so world identity "
                "cannot be established from this file"
            )

        for controller_name in sorted(map(str, controllers.keys())):
            aggregate = controllers.get(controller_name) or {}
            episodes = per_episode.get(controller_name) or []
            run = RunRecord(
                run_id=default_run_id(self.name, root, suffix=controller_name),
                reader=self.name,
                reader_version=self.version,
            )
            digest = register_source(run, path)
            self._fill_fields(run, result, payload, controller_name, aggregate, episodes, path)
            self._emit_aggregate_metrics(result, run, controller_name, aggregate, path)
            self._emit_episode_metrics(result, run, controller_name, episodes, path)
            run.coverage = {
                "reader": self.name,
                "reader_version": self.version,
                "controller": controller_name,
                "n_episode_records": len(episodes),
                "report_sha256": digest,
            }
            run.errors.extend(result.errors)
            for warning in result.warnings:
                if warning not in run.warnings:
                    run.warnings.append(warning)
            result.run_records.append(run)

        result.note_file(path, "parsed", rows=len(controllers))
        result.coverage["metric_record_count"] = len(result.metric_records)
        result.coverage["run_record_count"] = len(result.run_records)
        result.coverage["unit_kind_note"] = (
            "one run record per rule controller; a record is a diagnostic rollout batch, not "
            "an independent RL fit"
        )
        return result

    # Fields ---------------------------------------------------------------------------

    def _fill_fields(
        self,
        run: RunRecord,
        result: ReadResult,
        payload: Mapping[str, Any],
        controller_name: str,
        aggregate: Mapping[str, Any],
        episodes: list[Any],
        path: Path,
    ) -> None:
        source = f"{path.name}"
        run.set(
            FIELD_ROUTE,
            Measured.ok(f"cli:{payload.get('tool')}"),
            evidence=f"{source}:tool",
        )
        run.set(
            FIELD_ALGORITHM,
            Measured.ok(f"rule_controller:{controller_name}"),
            evidence=f"{source}:controllers[{controller_name}]",
        )
        run.set(
            FIELD_SOURCE_SHA,
            Measured.not_recorded(
                "the report records no source commit; it names the configuration path only"
            ),
            evidence=f"absent:{source}",
        )
        run.set(
            FIELD_ENVIRONMENT,
            measured_text(
                payload.get("environment_id"),
                evidence=f"{source}:environment_id",
                absent_reason="environment_id_absent",
            ),
            evidence=f"{source}:environment_id",
        )
        run.set(
            FIELD_INFORMATION_CONDITION,
            measured_text(
                dig(payload, "information_condition"),
                evidence=f"{source}:information_condition",
                absent_reason="information_condition_absent",
            ),
            evidence=f"{source}:information_condition",
        )
        recovery_definition = payload.get("recovery_definition")
        if isinstance(recovery_definition, Mapping):
            run.set(
                FIELD_METRIC_SEMANTICS,
                Measured.ok(
                    ";".join(
                        f"{key}={recovery_definition[key]}"
                        for key in sorted(recovery_definition.keys())
                    )
                ),
                evidence=f"{source}:recovery_definition",
            )
        run.set(
            FIELD_REWARD_DEFINITION,
            Measured.not_recorded(
                "the report records controller reward sums but not the reward definition; "
                "the recovery definition is in metric_semantics"
            ),
            evidence=f"absent:{source}",
        )
        run.set(
            FIELD_UNIT_DEFINITION,
            Measured.ok(
                "units are carried by key-name suffixes: _mbit volumes, _mbps rates, _s "
                "seconds, _m metres; satisfaction and fraction keys are unitless ratios"
            ),
            evidence=f"derived_from_key_names_lower_confidence:{source}",
        )
        optimizer_updates = payload.get("optimizer_updates")
        fits = payload.get("training_fits_performed")
        controller_updates = (
            dig(episodes[0], "controller.optimizer_updates") if episodes else None
        )
        run.set(
            FIELD_EVALUATION_POLICY_MODE,
            Measured.ok(
                "rule_controller_forward_only;"
                f"training_fits_performed={fits};optimizer_updates={optimizer_updates}"
                + (
                    f";per_episode_controller_optimizer_updates={controller_updates}"
                    if controller_updates is not None
                    else ""
                )
            ),
            evidence=f"{source}:training_fits_performed,optimizer_updates",
        )
        if fits == 0:
            run.set(
                FIELD_TRAINING_EXPOSURE,
                Measured.not_applicable(
                    "diagnostic rollout of an untuned rule controller: no training exposure "
                    "exists to report"
                ),
                evidence=f"{source}:training_fits_performed=0",
            )
        run.set(
            FIELD_CHECKPOINT_IDENTITY,
            Measured.not_applicable("a rule controller has no checkpoint"),
            evidence=f"{source}:controllers[{controller_name}]",
        )
        run.set(
            FIELD_CHECKPOINT_SELECTION,
            Measured.not_applicable("a rule controller has no checkpoint to select"),
            evidence=f"{source}:controllers[{controller_name}]",
        )
        run.set(
            FIELD_STATISTICAL_UNIT,
            Measured.ok(
                "diagnostic_rollout_episode_of_a_rule_controller;"
                "not_an_independent_training_replicate;"
                "adding episodes adds precision about one fixed rule, not another fit"
            ),
            evidence=f"{source}:interpretation_note,training_fits_performed",
        )
        seeds = payload.get("episode_seeds")
        if isinstance(seeds, list) and seeds:
            run.set(
                FIELD_EVALUATION_SEED,
                Measured.ok(
                    f"episode_seeds=[{min(seeds)}..{max(seeds)}];n={len(seeds)};"
                    f"provenance={payload.get('episode_seed_provenance')}"
                ),
                evidence=f"{source}:episode_seeds",
            )
        if payload.get("controller_seed") is not None:
            run.set(
                "controller_seed",
                Measured.ok(int(payload["controller_seed"])),
                evidence=f"{source}:controller_seed",
            )
        run.set(
            FIELD_TRAINING_SEED,
            Measured.not_applicable("no training run exists for a rule controller"),
            evidence=f"{source}:training_fits_performed",
        )
        if payload.get("data_status") is not None:
            run.set(
                "data_status",
                Measured.ok(str(payload["data_status"])),
                evidence=f"{source}:data_status",
            )
        if payload.get("config") is not None:
            run.set(
                "configuration_path",
                Measured.ok(str(payload["config"])),
                evidence=f"{source}:config",
            )
        run.set(
            FIELD_INITIAL_WORLD_CONFIG,
            Measured.not_recorded(
                "the report records the configuration file path, not a hash of its content; "
                "an initial-world identity cannot be established from it"
            ),
            evidence=f"absent:{source}",
        )
        declared, observed = boundary_measures(boundary_semantics({}))
        run.set(FIELD_TERMINATION_DECLARED, declared, evidence=f"absent:{source}")
        run.set(FIELD_TERMINATION_OBSERVED, observed, evidence=f"unverified:{source}")

        # Everything below needs per-episode records.
        if not episodes:
            run.set(
                FIELD_DATASET,
                Measured.not_recorded(
                    "aggregate-only report: no per-episode dataset_hash is available"
                ),
                evidence=f"absent:{source}",
            )
            run.set(
                FIELD_COMPLETION_STATUS,
                Measured.unknown(
                    "aggregate-only report: the number of completed episodes cannot be "
                    "checked against the requested seeds"
                ),
                evidence=f"absent:{source}",
            )
        else:
            hashes = sorted(
                {
                    str(dig(record, "episode.dataset_hash"))
                    for record in episodes
                    if dig(record, "episode.dataset_hash") is not None
                }
            )
            if not hashes:
                run.set(
                    FIELD_DATASET,
                    Measured.not_recorded("no episode recorded a dataset_hash"),
                    evidence=f"absent:{source}",
                )
            elif len(hashes) == 1:
                run.set(
                    FIELD_DATASET,
                    Measured.ok(hashes[0]),
                    evidence=f"{source}:per_episode[{controller_name}][].episode.dataset_hash",
                )
            else:
                run.set(
                    FIELD_DATASET,
                    Measured.unknown(f"episodes mix {len(hashes)} dataset hashes: {hashes}"),
                    evidence=f"{source}:per_episode[{controller_name}][].episode.dataset_hash",
                )
                result.warnings.append(
                    f"controller {controller_name}: episodes mix several dataset hashes {hashes}"
                )
            splits = sorted(
                {
                    str(dig(record, "episode.split"))
                    for record in episodes
                    if dig(record, "episode.split") is not None
                }
            )
            if splits:
                run.set(
                    FIELD_SPLIT,
                    Measured.ok("|".join(splits)),
                    evidence=f"{source}:per_episode[{controller_name}][].episode.split",
                )
            events = [record.get("exogenous_events") for record in episodes]
            if any(event is not None for event in events):
                run.set(
                    FIELD_EVENT_REALIZATION,
                    Measured.ok(world_identity_hash(events)),
                    evidence=f"{source}:per_episode[{controller_name}][].exogenous_events",
                )
            episode_ids = [
                dig(record, "episode.episode_id")
                for record in episodes
                if dig(record, "episode.episode_id") is not None
            ]
            durations = [
                dig(record, "episode_summary.total_time_s")
                for record in episodes
                if dig(record, "episode_summary.total_time_s") is not None
            ]
            if episode_ids or durations:
                run.set(
                    FIELD_EPISODE_INTERVAL,
                    Measured.ok(
                        f"episode_ids={sorted(map(str, episode_ids))};"
                        f"durations_s={sorted(set(map(float, durations)))}"
                    ),
                    evidence=(
                        f"{source}:per_episode[{controller_name}][].episode.episode_id + "
                        "episode_summary.total_time_s"
                    ),
                )
            if durations:
                unique = sorted(set(map(float, durations)))
                run.set(
                    FIELD_HORIZON,
                    Measured.ok(unique[0], unit="s")
                    if len(unique) == 1
                    else Measured.unknown(f"episodes have different durations: {unique}"),
                    evidence=f"{source}:per_episode[{controller_name}][].episode_summary.total_time_s",
                )
            uav_counts = sorted(
                {
                    len(dig(record, "episode_summary.flight_distance_m_per_uav") or [])
                    for record in episodes
                }
            )
            if uav_counts and uav_counts != [0]:
                run.set(
                    FIELD_AGENT_COUNT,
                    Measured.ok(int(uav_counts[0]))
                    if len(uav_counts) == 1
                    else Measured.unknown(f"episodes report different UAV counts: {uav_counts}"),
                    evidence=(
                        f"{source}:per_episode[{controller_name}][]"
                        ".episode_summary.flight_distance_m_per_uav"
                    ),
                )
            requested = payload.get("episode_seeds")
            expected = len(requested) if isinstance(requested, list) else None
            reported = aggregate.get("n_episodes")
            if expected is not None and reported is not None and int(reported) == expected == len(episodes):
                run.set(
                    FIELD_COMPLETION_STATUS,
                    Measured.ok(f"complete;n_episodes={len(episodes)}"),
                    evidence=f"{source}:episode_seeds vs controllers[{controller_name}].n_episodes",
                )
            else:
                run.set(
                    FIELD_COMPLETION_STATUS,
                    Measured.unknown(
                        f"episode counts disagree: requested_seeds={expected}, "
                        f"aggregate_n_episodes={reported}, per_episode_records={len(episodes)}"
                    ),
                    evidence=f"{source}:episode_seeds vs controllers[{controller_name}].n_episodes",
                )
                result.warnings.append(
                    f"controller {controller_name}: episode counts disagree "
                    f"(seeds={expected}, aggregate={reported}, records={len(episodes)})"
                )
            calibration = dig(episodes[0], "calibration_summary")
            if isinstance(calibration, Mapping):
                run.set(
                    "calibration_status",
                    Measured.ok(
                        f"empirically_calibrated={len(calibration.get('empirically_calibrated') or [])};"
                        f"engineering_assumptions={len(calibration.get('engineering_assumptions') or [])}"
                    ),
                    evidence=f"{source}:per_episode[{controller_name}][0].calibration_summary",
                )

        run.set(
            FIELD_EVALUATION_WORLD,
            Measured.ok(
                f"environment_id={payload.get('environment_id')};"
                f"data_status={payload.get('data_status')}"
            )
            if payload.get("environment_id") is not None
            else Measured.not_recorded("no environment identity recorded"),
            evidence=f"{source}:environment_id,data_status",
        )
        run.set(
            FIELD_ARTIFACT_LOCATIONS,
            Measured.ok(joined_locations(run.source_paths)),
            evidence=f"{self.name}:report_file",
        )
        ensure_identity_fields(
            run,
            reason="not_recorded_in_service_restoration_report",
            evidence=f"absent:{source}",
        )

    # Metric records -------------------------------------------------------------------

    def _emit_aggregate_metrics(
        self,
        result: ReadResult,
        run: RunRecord,
        controller_name: str,
        aggregate: Mapping[str, Any],
        path: Path,
    ) -> None:
        """Method-level aggregates, with ``None`` kept as an absence.

        ``time_to_recovery_s_mean_over_recovered`` is the one to watch: the producer sets it
        to ``None`` when no episode recovered, and the surrounding ``aggregation_rule``
        states that a censored episode is never a recovery of zero seconds.
        """

        for key in sorted(aggregate.keys()):
            value = aggregate[key]
            if isinstance(value, Mapping) or isinstance(value, (list, tuple)):
                continue
            if isinstance(value, str):
                continue
            if value is None:
                measured = Measured.not_applicable(
                    f"{key} is null in the source: no episode contributed a value, and a "
                    "censored or not-applicable episode is never counted as zero"
                )
            elif isinstance(value, bool):
                measured = Measured.ok(value)
            else:
                measured = Measured.from_float(
                    value,
                    unit="count" if key in _COUNT_KEYS else unit_from_key_name(key),
                )
            result.metric_records.append(
                MetricRecord(
                    run_id=run.run_id,
                    method_id=f"rule_controller:{controller_name}",
                    metric_name=key,
                    value=measured,
                    x_kind=XKind.NONE,
                    x_value=None,
                    phase=Phase.DIAGNOSTIC_ROLLOUT,
                    aggregation_level=AggregationLevel.METHOD,
                    training_replicate_id=None,
                    unit="count" if key in _COUNT_KEYS else unit_from_key_name(key),
                    definition_id=f"{self.name}:aggregate.{key}",
                    source_path=str(path),
                    source_row_or_key=f"controllers.{controller_name}.{key}",
                )
            )

    def _emit_episode_metrics(
        self,
        result: ReadResult,
        run: RunRecord,
        controller_name: str,
        episodes: list[Any],
        path: Path,
    ) -> None:
        non_scalar_sample: list[str] | None = None
        for index, record in enumerate(episodes):
            if not isinstance(record, Mapping):
                result.errors.append(
                    f"{path}: per_episode[{controller_name}][{index}] is not an object"
                )
                continue
            scalars, skipped = flatten_scalars(record, skip_keys=_EPISODE_SKIP)
            if non_scalar_sample is None:
                non_scalar_sample = skipped
            episode_id = dig(record, "episode.episode_id")
            dataset_hash = dig(record, "episode.dataset_hash")
            world_id = world_identity_hash(
                [dataset_hash, record.get("exogenous_events"), record.get("episode_seed")]
            )
            for key, value in scalars:
                unit = unit_from_key_name(key)
                if value is None:
                    measured = Measured.not_applicable(
                        f"{key} is null in the source; an absent recovery is not a zero"
                    )
                elif isinstance(value, bool):
                    measured = Measured.ok(value)
                else:
                    measured = Measured.from_float(value, unit=unit)
                result.metric_records.append(
                    MetricRecord(
                        run_id=run.run_id,
                        method_id=f"rule_controller:{controller_name}",
                        metric_name=key,
                        value=measured,
                        x_kind=XKind.EPISODE_INDEX,
                        x_value=index,
                        phase=Phase.DIAGNOSTIC_ROLLOUT,
                        aggregation_level=AggregationLevel.EPISODE,
                        training_replicate_id=None,
                        checkpoint_id=None,
                        world_id=world_id,
                        episode_id=(
                            None
                            if episode_id is None and record.get("episode_seed") is None
                            else str(
                                episode_id
                                if episode_id is not None
                                else f"seed_{record.get('episode_seed')}"
                            )
                        ),
                        unit=unit,
                        definition_id=f"{self.name}:episode.{key}",
                        source_path=str(path),
                        source_row_or_key=f"per_episode.{controller_name}[{index}].{key}",
                    )
                )
        if non_scalar_sample is not None:
            result.coverage.setdefault("episode_non_scalar_keys", {})[controller_name] = (
                non_scalar_sample
            )
