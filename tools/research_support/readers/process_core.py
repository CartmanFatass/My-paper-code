"""Reader for the process-core run directory: train/evaluation manifests plus analysis.

Built against the actual files in this checkout, not against the plan's description of
them.  The two runs read while writing it were::

    logs/formal_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_cpu_20260727_96e35dd_r1/
    logs/formal_continuous_roster_native_six_g31_direction_balance_attribution_g42_cpu_20260727_a6c3c29_r1/

whose ``train_manifest.json`` top level is::

    accepted_anchor_artifact_digests, accepted_anchor_root, accepted_anchor_root_mode,
    algorithm, aligned_source_commit, alignment_audit_id, alignment_disposition,
    alignment_stage_commit, authorization_token, conclusion_evidence, configuration,
    cpu_execution (schema_version 2 only), formal, native_backend,
    preflight_artifact_digests, preflight_root, replicate_results, runtime, schema_version,
    source_commit, source_controls, source_id, stage, stage_wall_time_seconds, status

The two runs differ in ``schema_version`` (2 vs 1) and the older one has no
``cpu_execution`` block, so every key here is read optionally and a missing one becomes an
explicit absence rather than a default.

Three facts drive the design:

* **There is no reward definition, no dataset hash and no information condition in this
  family.**  What exists is ``configuration.channel_composition``,
  ``configuration.normalization_unit`` and ``configuration.normalization_rows``, which
  together define what the recorded utility *is*; they are surfaced as
  ``metric_semantics`` so a comparison can refuse to pool two different quantities.
  ``dataset_identity`` stays ``NOT_RECORDED``: ``source_controls.training_source`` is a
  declared label ("G32 capacity-8 fixed paired source"), not a content hash, and pairing
  needs a hash.
* **The evaluation manifest does carry a real world realisation.**  Every
  ``cells[].episodes[]`` entry has a ``signature`` naming event times, event order, profile
  and roster transitions, so ``event_realization`` and ``initial_world_config`` can be
  evidenced even though ``dataset_identity`` cannot.  That is exactly the state the plan
  labels ``pairing_unverified``: some world identity, not all of it.
* **Neither manifest records any boundary flag.**  ``legacy_truncation_as_termination`` and
  the ``low_boundary_*`` runtime flags are absent from all six files of both runs, so the
  observed boundary semantics of these runs are UNVERIFIED.  The scan below looks in every
  place they are actually written (see ``ha_ctse_process/standalone_manifest.py`` and
  ``standalone_low_update.py``) and reports their absence instead of assuming the corrected
  arithmetic ran.

Static only: JSON parsing.  ``checkpoints/*.pt`` files are referenced by digest from the
manifest and are never opened, let alone unpickled.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.research_support.readers import (
    BOUNDARY_DECLARED_KEY,
    BOUNDARY_RUNTIME_KEYS,
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
    FIELD_NORMALIZATION,
    FIELD_OBSERVATION_SCHEMA,
    FIELD_REWARD_DEFINITION,
    FIELD_ROUTE,
    FIELD_SOURCE_DIRTY,
    FIELD_SOURCE_SHA,
    FIELD_STATISTICAL_UNIT,
    FIELD_TERMINATION_DECLARED,
    FIELD_TERMINATION_OBSERVED,
    FIELD_TRAINING_EXPOSURE,
    FIELD_TRAINING_SEED,
    ReadResult,
    UnsupportedSourceError,
    boundary_measures,
    boundary_semantics,
    default_run_id,
    dig,
    ensure_identity_fields,
    first_present,
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

#: Upper bound on emitted metric records.  A single evaluation manifest holds 72 cells of
#: 48 episodes, and a train manifest 3 replicates of 100 update records; the cap keeps an
#: inspection call bounded and is reported in coverage when it bites.
MAX_METRIC_RECORDS = 60_000

#: Schema versions this reader was written against.  An unseen version is still read - the
#: keys are all optional - but the run record carries a warning.
KNOWN_SCHEMA_VERSIONS = (1, 2)

_TRAIN = "train_manifest.json"
_EVAL = "evaluation_manifest.json"
_ANALYSIS = "analysis_result.json"

#: Episode keys that are identity or label, not measurements.
_EPISODE_SKIP = frozenset({"episode_id", "local_episode_id", "signature", "profile"})

#: Update-record keys that are identity, not measurements.
_UPDATE_SKIP = frozenset({"update_index"})


class ProcessCoreReader:
    """Reads a process-core run directory into run identity plus long-form metrics."""

    name = "process_core"
    version = "1"

    # Detection -----------------------------------------------------------------------

    def detect(self, root: Path) -> bool:
        """Require one of the two distinctive manifest names.

        ``analysis_result.json`` alone does not trigger detection: the name is generic
        enough to appear in unrelated output, and detection must not be a guess.  It is
        still read when a manifest is present.
        """

        root = Path(root)
        return (root / _TRAIN).is_file() or (root / _EVAL).is_file()

    # Reading -------------------------------------------------------------------------

    def read(self, root: Path) -> ReadResult:
        root = Path(root)
        result = ReadResult()
        result.coverage.update(
            {"reader": self.name, "reader_version": self.version, "root": str(root)}
        )
        if not self.detect(root):
            raise UnsupportedSourceError(
                f"{root} holds neither {_TRAIN} nor {_EVAL}; this reader requires a named "
                "process-core manifest"
            )

        run = RunRecord(
            run_id=default_run_id(self.name, root), reader=self.name, reader_version=self.version
        )
        payloads: list[tuple[str, Any]] = []
        for filename in (_TRAIN, _EVAL, _ANALYSIS):
            path = root / filename
            if not path.is_file():
                result.note_file(path, "skipped", detail="not present in this run directory")
                continue
            digest = register_source(run, path)
            try:
                payload, warnings = load_json_file(path)
            except (OSError, ValueError) as error:
                result.errors.append(f"{path}: {error}")
                result.note_file(path, "unsupported", detail=str(error), digest=digest)
                continue
            result.warnings.extend(warnings)
            if not isinstance(payload, Mapping):
                detail = f"top level is {type(payload).__name__}, expected a JSON object"
                result.errors.append(f"{path}: {detail}")
                result.note_file(path, "unsupported", detail=detail, digest=digest)
                continue
            result.note_file(path, "parsed", digest=digest, rows=len(payload))
            payloads.append((filename, payload))

        if not payloads:
            result.errors.append(f"{root}: no process-core manifest could be parsed")
            ensure_identity_fields(run, reason="no_manifest_parsed", evidence="missing_artifact")
            run.errors.extend(result.errors)
            result.run_records.append(run)
            return result

        by_name = dict(payloads)
        train = by_name.get(_TRAIN)
        evaluation = by_name.get(_EVAL)
        analysis = by_name.get(_ANALYSIS)

        self._read_identity(run, result, payloads)
        self._read_boundary(run, result, train)
        self._read_world_identity(run, result, evaluation)
        self._read_checkpoints(run, result, train)
        if evaluation is not None:
            self._emit_evaluation_metrics(result, run, evaluation, root / _EVAL)
        if train is not None:
            self._emit_update_metrics(result, run, train, root / _TRAIN)
        if analysis is not None:
            self._emit_analysis_metrics(result, run, analysis, root / _ANALYSIS)

        run.set(
            FIELD_ARTIFACT_LOCATIONS,
            Measured.ok(joined_locations(run.source_paths)),
            evidence=f"{self.name}:run_directory",
        )
        run.set(
            FIELD_STATISTICAL_UNIT,
            Measured.ok(
                "independent_unit=replicate_results[].replicate; an evaluation episode adds "
                "precision about one fit, not another fit"
            ),
            evidence=f"{_TRAIN}:replicate_results[].replicate",
        )
        ensure_identity_fields(
            run,
            reason="not_recorded_in_process_core_manifest",
            evidence="absent:process_core",
        )
        run.coverage = {"reader": self.name, "reader_version": self.version}
        run.errors.extend(result.errors)
        for warning in result.warnings:
            if warning not in run.warnings:
                run.warnings.append(warning)
        result.run_records.append(run)
        result.coverage["metric_record_count"] = len(result.metric_records)
        return result

    # Identity ------------------------------------------------------------------------

    def _read_identity(
        self, run: RunRecord, result: ReadResult, payloads: Sequence[tuple[str, Any]]
    ) -> None:
        def take(dotted: str) -> tuple[Any, str | None]:
            return first_present(payloads, dotted)

        schema_version, schema_evidence = take("schema_version")
        if schema_version is not None and int(schema_version) not in KNOWN_SCHEMA_VERSIONS:
            result.warnings.append(
                f"schema_version={schema_version} is outside {list(KNOWN_SCHEMA_VERSIONS)}; "
                "fields are read optionally, but an added key is not interpreted"
            )
        for name, dotted in (
            ("schema_version", "schema_version"),
            ("source_id", "source_id"),
            ("aligned_source_sha", "aligned_source_commit"),
            ("alignment_stage_sha", "alignment_stage_commit"),
            ("alignment_disposition", "alignment_disposition"),
            ("authorization_token", "authorization_token"),
            ("formal", "formal"),
            ("training_source", "source_controls.training_source"),
            ("evaluation_source", "source_controls.evaluation_source"),
            ("optimizer_steps", "configuration.optimizer_steps"),
            ("total_real_transitions", "configuration.total_real_transitions"),
            ("training_capacity", "configuration.training_capacity"),
            ("evaluation_capacities", "configuration.evaluation_capacities"),
            ("replicate_count", "configuration.replicates"),
            ("native_backend_build_identity", "native_backend.build_identity"),
            ("runtime_torch", "runtime.torch"),
            ("runtime_backend", "runtime.backend"),
        ):
            value, evidence = take(dotted)
            if value is not None:
                run.set(name, measured_text(value, evidence=evidence or dotted, absent_reason=dotted), evidence=evidence)

        sha, sha_evidence = take("source_commit")
        run.set(
            FIELD_SOURCE_SHA,
            measured_text(sha, evidence=sha_evidence or "source_commit", absent_reason="source_commit_absent"),
            evidence=sha_evidence or "absent:source_commit",
        )
        run.set(
            FIELD_SOURCE_DIRTY,
            Measured.not_recorded(
                "no working-tree dirty flag is recorded; the manifest names a commit, not "
                "whether the tree matched it"
            ),
            evidence="absent:process_core",
        )
        algorithm, algorithm_evidence = take("algorithm")
        run.set(
            FIELD_ALGORITHM,
            measured_text(algorithm, evidence=algorithm_evidence or "algorithm", absent_reason="algorithm_absent"),
            evidence=algorithm_evidence or "absent:algorithm",
        )
        run.set(
            FIELD_ROUTE,
            Measured.not_recorded(
                "the manifest records no runner route or agent class; see algorithm_label, "
                "source_id and environment_identity"
            ),
            evidence="absent:process_core",
        )

        backend, backend_evidence = take("configuration.environment_backend")
        kind, kind_evidence = take("native_backend.kind")
        build, _ = take("native_backend.build_identity")
        fallback, _ = take("native_backend.python_fallback")
        parts = []
        if backend is not None:
            parts.append(f"backend={backend}")
        if kind is not None:
            parts.append(f"native={kind}" + (f"@{build}" if build else ""))
        if fallback is not None:
            parts.append(f"python_fallback={bool(fallback)}")
        run.set(
            FIELD_ENVIRONMENT,
            Measured.ok(";".join(parts)) if parts else Measured.not_recorded("no environment identity recorded"),
            evidence=backend_evidence or kind_evidence or "absent:process_core",
        )
        run.set(
            FIELD_DATASET,
            Measured.not_recorded(
                "no dataset or data-content hash is recorded; source_controls.training_source "
                "and evaluation_source are declared source labels, not content identities"
            ),
            evidence="absent:process_core",
        )
        run.set(
            FIELD_REWARD_DEFINITION,
            Measured.not_recorded(
                "the manifest records no reward definition; the recorded quantity is a "
                "utility whose composition appears in metric_semantics"
            ),
            evidence="absent:process_core",
        )
        composition, composition_evidence = take("configuration.channel_composition")
        normalization_unit, normalization_evidence = take("configuration.normalization_unit")
        normalization_rows, _ = take("configuration.normalization_rows")
        semantics_parts = []
        if composition is not None:
            semantics_parts.append(f"channel_composition={composition}")
        if normalization_unit is not None:
            semantics_parts.append(f"normalization_unit={normalization_unit}")
        if normalization_rows is not None:
            semantics_parts.append(f"normalization_rows={normalization_rows}")
        run.set(
            FIELD_METRIC_SEMANTICS,
            Measured.ok(";".join(semantics_parts))
            if semantics_parts
            else Measured.not_recorded("no channel composition or normalization unit recorded"),
            evidence=composition_evidence or normalization_evidence or "absent:process_core",
        )
        if normalization_unit is not None or normalization_rows is not None:
            run.set(
                FIELD_NORMALIZATION,
                Measured.ok(
                    ";".join(
                        part
                        for part in (
                            None if normalization_unit is None else f"unit={normalization_unit}",
                            None if normalization_rows is None else f"rows={normalization_rows}",
                        )
                        if part
                    )
                ),
                evidence=normalization_evidence or "configuration.normalization_rows",
            )

        observation_dim, observation_evidence = take("configuration.stored_training_observation_dim")
        if observation_dim is not None:
            run.set(
                FIELD_OBSERVATION_SCHEMA,
                Measured.ok(f"stored_training_observation_dim={observation_dim}"),
                evidence=observation_evidence,
            )
        horizon, horizon_evidence = take("configuration.horizon")
        if horizon is not None:
            run.set(
                FIELD_HORIZON,
                Measured.ok(int(horizon), unit="decision_steps"),
                evidence=horizon_evidence,
            )
        selection, selection_evidence = take("configuration.checkpoint_selection")
        if selection is not None:
            run.set(
                FIELD_CHECKPOINT_SELECTION,
                measured_text(
                    selection,
                    evidence=selection_evidence or "configuration.checkpoint_selection",
                    absent_reason="checkpoint_selection_absent",
                ),
                evidence=selection_evidence,
            )
        transitions, transitions_evidence = take("configuration.training_transitions")
        if transitions is not None:
            run.set(
                FIELD_TRAINING_EXPOSURE,
                Measured.ok(int(transitions), unit="environment_transitions"),
                evidence=transitions_evidence,
            )
        run.set(
            FIELD_AGENT_COUNT,
            Measured.not_recorded(
                "no fixed agent count exists in this family: the roster size varies within an "
                "episode; see training_capacity and evaluation_capacities"
            ),
            evidence="absent:process_core",
        )
        run.set(
            FIELD_INFORMATION_CONDITION,
            Measured.not_recorded("the manifest records no observation information condition"),
            evidence="absent:process_core",
        )

        statuses = [
            (name, dig(payload, "status"), dig(payload, "stage"))
            for name, payload in payloads
        ]
        recorded = [
            f"{stage or name}={status}" for name, status, stage in statuses if status is not None
        ]
        absent = [name for name, status, _ in statuses if status is None]
        run.set(
            FIELD_COMPLETION_STATUS,
            Measured.ok(";".join(recorded))
            if recorded
            else Measured.not_recorded("no stage recorded a status"),
            evidence="status+stage of each parsed manifest",
        )
        if absent:
            result.warnings.append(f"no status recorded in: {absent}")
        result.coverage["stage_status"] = {
            (stage or name): status for name, status, stage in statuses
        }

        seed_bases, seed_evidence = take("source_controls.seed_bases")
        if isinstance(seed_bases, Mapping):
            training = {k: v for k, v in sorted(seed_bases.items()) if not str(k).startswith("evaluation")}
            evaluating = {k: v for k, v in sorted(seed_bases.items()) if str(k).startswith("evaluation")}
            if training:
                run.set(
                    FIELD_TRAINING_SEED,
                    Measured.ok(";".join(f"{k}={v}" for k, v in training.items())),
                    evidence=seed_evidence,
                )
            if evaluating:
                run.set(
                    FIELD_EVALUATION_SEED,
                    Measured.ok(";".join(f"{k}={v}" for k, v in evaluating.items())),
                    evidence=seed_evidence,
                )

    # Boundary semantics ---------------------------------------------------------------

    def _read_boundary(self, run: RunRecord, result: ReadResult, train: Any) -> None:
        """Look for the declared switch and the runtime resolution flags where they are written.

        ``legacy_truncation_as_termination`` is a ``TRAINING_MANIFEST_FIELDS`` entry, so it
        appears at the manifest top level or inside ``configuration``.  The ``low_boundary_*``
        flags are per-update metrics written by ``standalone_low_update.py``, so they appear
        inside ``replicate_results[].update_records[]``.  Both places are searched, and an
        absence is reported as an absence.
        """

        found: dict[str, tuple[Any, str]] = {}
        details: dict[str, Any] = {"searched": [], "updates_with_flags": 0, "update_count": 0}
        if train is None:
            semantics = boundary_semantics(found)
            details["searched"].append("no train_manifest.json")
        else:
            containers: list[tuple[str, Any]] = [
                (_TRAIN, train),
                (f"{_TRAIN}:configuration", dig(train, "configuration")),
                (f"{_TRAIN}:source_controls", dig(train, "source_controls")),
            ]
            for label, container in containers:
                details["searched"].append(label)
                if not isinstance(container, Mapping):
                    continue
                for key in (BOUNDARY_DECLARED_KEY, *BOUNDARY_RUNTIME_KEYS):
                    if key in container and key not in found:
                        found[key] = (container[key], f"{label}.{key}")

            resolved_values: list[float] = []
            collapse_values: list[float] = []
            truncation_rows: list[float] = []
            replicates = dig(train, "replicate_results") or []
            for replicate_index, replicate in enumerate(replicates):
                if not isinstance(replicate, Mapping):
                    continue
                for key in (BOUNDARY_DECLARED_KEY, *BOUNDARY_RUNTIME_KEYS):
                    if key in replicate and key not in found:
                        found[key] = (
                            replicate[key],
                            f"{_TRAIN}:replicate_results[{replicate_index}].{key}",
                        )
                updates = replicate.get("update_records") or []
                details["update_count"] += len(updates)
                details["searched"].append(
                    f"{_TRAIN}:replicate_results[{replicate_index}].update_records[*]"
                )
                for update_index, update in enumerate(updates):
                    if not isinstance(update, Mapping):
                        continue
                    location = (
                        f"{_TRAIN}:replicate_results[{replicate_index}]"
                        f".update_records[{update_index}]"
                    )
                    sources: list[tuple[str, Mapping[str, Any]]] = [(location, update)]
                    for key, value in update.items():
                        if isinstance(value, Mapping):
                            sources.append((f"{location}.{key}", value))
                    hit = False
                    for label, container in sources:
                        if BOUNDARY_DECLARED_KEY in container and BOUNDARY_DECLARED_KEY not in found:
                            found[BOUNDARY_DECLARED_KEY] = (
                                container[BOUNDARY_DECLARED_KEY],
                                f"{label}.{BOUNDARY_DECLARED_KEY}",
                            )
                        if "low_boundary_flags_resolved" in container:
                            resolved_values.append(float(container["low_boundary_flags_resolved"]))
                            hit = True
                            found.setdefault(
                                "low_boundary_flags_resolved",
                                (
                                    container["low_boundary_flags_resolved"],
                                    f"{label}.low_boundary_flags_resolved",
                                ),
                            )
                        if "low_boundary_legacy_collapse" in container:
                            collapse_values.append(float(container["low_boundary_legacy_collapse"]))
                            found.setdefault(
                                "low_boundary_legacy_collapse",
                                (
                                    container["low_boundary_legacy_collapse"],
                                    f"{label}.low_boundary_legacy_collapse",
                                ),
                            )
                        if "low_truncation_rows" in container:
                            truncation_rows.append(float(container["low_truncation_rows"]))
                            found.setdefault(
                                "low_truncation_rows",
                                (container["low_truncation_rows"], f"{label}.low_truncation_rows"),
                            )
                    if hit:
                        details["updates_with_flags"] += 1

            # Worst-case aggregation across updates: one update that fell back to the
            # collapsed reading makes the run's arithmetic collapsed for that update, and a
            # report that averaged the flag away would hide it.
            if resolved_values:
                found["low_boundary_flags_resolved"] = (
                    min(resolved_values),
                    found["low_boundary_flags_resolved"][1] + " (min over updates)",
                )
                details["updates_unresolved"] = sum(1 for v in resolved_values if v < 1.0)
            if collapse_values:
                found["low_boundary_legacy_collapse"] = (
                    max(collapse_values),
                    found["low_boundary_legacy_collapse"][1] + " (max over updates)",
                )
                details["updates_legacy_collapse"] = sum(1 for v in collapse_values if v > 0.0)
            if truncation_rows:
                found["low_truncation_rows"] = (
                    sum(truncation_rows),
                    found["low_truncation_rows"][1] + " (sum over updates)",
                )
            semantics = boundary_semantics(found)

        declared, observed = boundary_measures(semantics)
        run.set(
            FIELD_TERMINATION_DECLARED,
            declared,
            evidence=semantics["declared"].get("evidence") or "absent:process_core",
        )
        run.set(
            FIELD_TERMINATION_OBSERVED,
            observed,
            evidence="unverified:no_runtime_boundary_flag_recorded"
            if semantics["unverified"]
            else "recorded:low_boundary_flags",
        )
        semantics["scan"] = details
        result.coverage["boundary_semantics"] = semantics
        if semantics["unverified"]:
            result.warnings.append(
                "episode-boundary execution is UNVERIFIED: no low_boundary_flags_resolved / "
                "low_boundary_legacy_collapse / low_truncation_rows value is recorded in this "
                "run, so whether truncation was collapsed into termination cannot be read off "
                "the artifacts"
            )
        for note in semantics["notes"]:
            result.warnings.append(f"boundary semantics: {note}")

    # World identity -------------------------------------------------------------------

    def _read_world_identity(self, run: RunRecord, result: ReadResult, evaluation: Any) -> None:
        if evaluation is None:
            return
        cells = dig(evaluation, "cells") or []
        signatures: list[str] = []
        episode_ids: list[int] = []
        profiles: set[str] = set()
        capacities: set[Any] = set()
        cell_names: set[str] = set()
        deterministic: set[Any] = set()
        optimizer_steps: set[Any] = set()
        checkpoints: set[str] = set()
        arms: set[str] = set()
        for cell in cells:
            if not isinstance(cell, Mapping):
                continue
            cell_names.add(str(cell.get("cell")))
            capacities.add(cell.get("capacity"))
            deterministic.add(cell.get("deterministic"))
            optimizer_steps.add(cell.get("optimizer_steps"))
            if cell.get("checkpoint") is not None:
                checkpoints.add(str(cell["checkpoint"]))
            if cell.get("arm") is not None:
                arms.add(str(cell["arm"]))
            for episode in cell.get("episodes") or []:
                if not isinstance(episode, Mapping):
                    continue
                if episode.get("signature") is not None:
                    signatures.append(str(episode["signature"]))
                if episode.get("profile") is not None:
                    profiles.add(str(episode["profile"]))
                try:
                    episode_ids.append(int(episode["episode_id"]))
                except (KeyError, TypeError, ValueError):
                    pass

        if signatures:
            run.set(
                FIELD_EVENT_REALIZATION,
                Measured.ok(world_identity_hash(sorted(signatures))),
                evidence=f"{_EVAL}:cells[].episodes[].signature (n={len(signatures)})",
            )
        if episode_ids:
            run.set(
                FIELD_EPISODE_INTERVAL,
                Measured.ok(
                    f"episode_id=[{min(episode_ids)}..{max(episode_ids)}];n={len(episode_ids)}"
                ),
                evidence=f"{_EVAL}:cells[].episodes[].episode_id",
            )
        if profiles or capacities:
            run.set(
                FIELD_INITIAL_WORLD_CONFIG,
                Measured.ok(
                    world_identity_hash(
                        [sorted(profiles), sorted(str(c) for c in capacities)]
                    )
                ),
                evidence=f"{_EVAL}:cells[].capacity + cells[].episodes[].profile",
            )
        if cell_names or capacities:
            run.set(
                FIELD_EVALUATION_WORLD,
                Measured.ok(
                    f"cells={sorted(cell_names)};capacities={sorted(str(c) for c in capacities)}"
                ),
                evidence=f"{_EVAL}:cells[].cell + cells[].capacity",
            )
        if cell_names:
            run.set(
                FIELD_EVALUATION_POLICY_MODE,
                Measured.ok(
                    f"cells={sorted(cell_names)};deterministic={sorted(str(d) for d in deterministic)};"
                    f"optimizer_steps={sorted(str(s) for s in optimizer_steps)}"
                ),
                evidence=f"{_EVAL}:cells[].deterministic + cells[].optimizer_steps",
            )
            if optimizer_steps and optimizer_steps != {0}:
                result.warnings.append(
                    f"evaluation cells record optimizer_steps={sorted(str(s) for s in optimizer_steps)}; "
                    "a non-zero value means the evaluation was not forward-only"
                )
        result.coverage["evaluation_cells"] = {
            "n_cells": len(cells),
            "arms": sorted(arms),
            "cell_names": sorted(cell_names),
            "checkpoints": sorted(checkpoints),
            "n_episodes": len(signatures),
            "n_distinct_signatures": len(set(signatures)),
        }

    # Checkpoints ----------------------------------------------------------------------

    def _read_checkpoints(self, run: RunRecord, result: ReadResult, train: Any) -> None:
        if train is None:
            return
        entries: list[dict[str, Any]] = []
        for index, replicate in enumerate(dig(train, "replicate_results") or []):
            if not isinstance(replicate, Mapping):
                continue
            anchor = replicate.get("accepted_anchor")
            entry: dict[str, Any] = {"replicate": replicate.get("replicate", index)}
            if isinstance(anchor, Mapping):
                entry["checkpoint_reference"] = anchor.get("checkpoint_reference")
                entry["complete_state_digest"] = anchor.get("complete_state_digest")
                entry["checkpoint_kind"] = anchor.get("checkpoint_kind")
            entry["accepted_anchor_state_digest"] = replicate.get("accepted_anchor_state_digest")
            entries.append(entry)
        digests = dig(train, "accepted_anchor_artifact_digests")
        if entries or isinstance(digests, Mapping):
            run.set(
                FIELD_CHECKPOINT_IDENTITY,
                Measured.ok(
                    world_identity_hash(
                        [entries, dict(sorted(digests.items())) if isinstance(digests, Mapping) else None]
                    )
                ),
                evidence=(
                    f"{_TRAIN}:replicate_results[].accepted_anchor.complete_state_digest + "
                    "accepted_anchor_artifact_digests"
                ),
            )
            result.coverage["checkpoints"] = {
                "replicates": entries,
                "accepted_anchor_artifact_digests": (
                    dict(sorted(digests.items())) if isinstance(digests, Mapping) else None
                ),
                "note": (
                    "referenced by digest only; no .pt file is opened, and nothing is unpickled"
                ),
            }

    # Metric records -------------------------------------------------------------------

    def _budget_left(self, result: ReadResult) -> int:
        return MAX_METRIC_RECORDS - len(result.metric_records)

    def _note_truncated(self, result: ReadResult, where: str) -> None:
        message = f"metric record cap {MAX_METRIC_RECORDS} reached while reading {where}"
        if message not in result.warnings:
            result.warnings.append(message)
        result.coverage["metric_records_truncated"] = True

    def _emit_evaluation_metrics(
        self, result: ReadResult, run: RunRecord, evaluation: Any, path: Path
    ) -> None:
        non_scalar_sample: list[str] | None = None
        for cell_index, cell in enumerate(dig(evaluation, "cells") or []):
            if not isinstance(cell, Mapping):
                continue
            arm = str(cell.get("arm", "unknown_arm"))
            checkpoint = None if cell.get("checkpoint") is None else str(cell["checkpoint"])
            replicate = cell.get("replicate")
            cell_name = str(cell.get("cell", "unknown_cell"))
            capacity = cell.get("capacity")
            for episode_index, episode in enumerate(cell.get("episodes") or []):
                if not isinstance(episode, Mapping):
                    continue
                if self._budget_left(result) <= 0:
                    self._note_truncated(result, f"{path.name}:cells[].episodes[]")
                    return
                scalars, skipped = flatten_scalars(episode, skip_keys=_EPISODE_SKIP)
                if non_scalar_sample is None:
                    non_scalar_sample = skipped
                signature = episode.get("signature")
                world_id = None if signature is None else str(signature)
                episode_id = episode.get("episode_id")
                local_index = episode.get("local_episode_id")
                for key, value in scalars:
                    result.metric_records.append(
                        MetricRecord(
                            run_id=run.run_id,
                            method_id=arm,
                            metric_name=key,
                            value=Measured.from_float(value, unit=unit_from_key_name(key))
                            if not isinstance(value, bool)
                            else Measured.ok(value),
                            x_kind=XKind.EPISODE_INDEX,
                            x_value=None if local_index is None else int(local_index),
                            phase=Phase.EVALUATION,
                            aggregation_level=AggregationLevel.EPISODE,
                            training_replicate_id=None if replicate is None else f"replicate_{replicate}",
                            checkpoint_id=checkpoint,
                            world_id=world_id,
                            episode_id=None if episode_id is None else str(episode_id),
                            unit=unit_from_key_name(key),
                            definition_id=f"{self.name}:{key}",
                            direction="unknown",
                            source_path=str(path),
                            source_row_or_key=(
                                f"cells[{cell_index}](cell={cell_name},capacity={capacity})"
                                f".episodes[{episode_index}].{key}"
                            ),
                        )
                    )
        if non_scalar_sample is not None:
            result.coverage["evaluation_episode_non_scalar_keys"] = non_scalar_sample
            result.coverage["evaluation_episode_note"] = (
                "per-step traces (reward_trace, roster_size_trace, process_segment_utility) "
                "are present in the source but are not expanded into long-form records here; "
                "their lengths are listed above"
            )

    def _emit_update_metrics(
        self, result: ReadResult, run: RunRecord, train: Any, path: Path
    ) -> None:
        algorithm = dig(train, "algorithm") or "unknown_algorithm"
        non_scalar_sample: list[str] | None = None
        for replicate_index, replicate in enumerate(dig(train, "replicate_results") or []):
            if not isinstance(replicate, Mapping):
                continue
            replicate_id = replicate.get("replicate", replicate_index)
            for update_index, update in enumerate(replicate.get("update_records") or []):
                if not isinstance(update, Mapping):
                    continue
                if self._budget_left(result) <= 0:
                    self._note_truncated(result, f"{path.name}:replicate_results[].update_records[]")
                    return
                scalars, skipped = flatten_scalars(update, skip_keys=_UPDATE_SKIP)
                if non_scalar_sample is None:
                    non_scalar_sample = skipped
                x_value = update.get("update_index", update_index)
                for key, value in scalars:
                    result.metric_records.append(
                        MetricRecord(
                            run_id=run.run_id,
                            method_id=str(algorithm),
                            metric_name=key,
                            value=Measured.ok(value)
                            if isinstance(value, bool)
                            else Measured.from_float(value, unit=unit_from_key_name(key)),
                            x_kind=XKind.UPDATE_INDEX,
                            x_value=int(x_value),
                            phase=Phase.TRAINING,
                            aggregation_level=AggregationLevel.REPLICATE,
                            training_replicate_id=f"replicate_{replicate_id}",
                            unit=unit_from_key_name(key),
                            definition_id=f"{self.name}:{key}",
                            source_path=str(path),
                            source_row_or_key=(
                                f"replicate_results[{replicate_index}]"
                                f".update_records[{update_index}].{key}"
                            ),
                        )
                    )
        if non_scalar_sample is not None:
            result.coverage["update_record_non_scalar_keys"] = non_scalar_sample

    def _emit_analysis_metrics(
        self, result: ReadResult, run: RunRecord, analysis: Any, path: Path
    ) -> None:
        metrics = dig(analysis, "metrics")
        if not isinstance(metrics, Mapping):
            return
        algorithm = dig(analysis, "algorithm") or "unknown_algorithm"
        scalars, skipped = flatten_scalars(metrics, max_items=self._budget_left(result))
        for key, value in scalars:
            result.metric_records.append(
                MetricRecord(
                    run_id=run.run_id,
                    method_id=str(algorithm),
                    metric_name=key,
                    value=Measured.ok(value)
                    if isinstance(value, bool)
                    else Measured.from_float(value, unit=unit_from_key_name(key)),
                    x_kind=XKind.NONE,
                    x_value=None,
                    phase=Phase.EVALUATION,
                    aggregation_level=AggregationLevel.METHOD,
                    unit=unit_from_key_name(key),
                    definition_id=f"{self.name}:analysis.{key}",
                    source_path=str(path),
                    source_row_or_key=f"metrics.{key}",
                )
            )
        result.coverage["analysis_non_scalar_leaves"] = skipped
        result.coverage["analysis_note"] = (
            "confidence-interval triples are lists in the source; they are listed above "
            "rather than flattened into three unlabelled scalars"
        )
