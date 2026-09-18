"""Diagnostics for one scenario configuration: what it declares, and what it actually does.

A configuration document is a claim. It says a region is 3 km across, that a site fails at
t=120 s, that an episode lasts 600 s and that UAVs fly between 90 m and 160 m. Whether the
running environment does those things is a different question, and the two must never be
printed in the same column.

So this module has two modes, with the same separation ``inspect_env.py`` uses:

* **Static** (the default, ``execute=False``) reads the configuration document - and the
  dataset and episode list when they are named - and reports the *declared* scenario. It
  imports no environment package, constructs nothing, steps nothing and starts no process.
  Every quantity that only a run could establish is reported as
  :attr:`~tools.research_support.records.Validity.UNKNOWN` with the reason that nothing was
  executed, and the report's top-level ``provenance`` is ``declared_only``.
* **Executed** (``execute=True``) additionally runs the declared non-learning diagnostic
  set: construct the environment **in a child process**, reset it, step it with a named
  untuned rule controller for a bounded number of episodes and steps, and report
  observed-versus-declared. Observed values get provenance ``verified_runtime``; everything
  else stays declared. The scope is printed first with ``optimizer_updates=0``.

What the executed mode never does: construct an optimizer, load a checkpoint, take a
gradient step, write into the configuration or the dataset, or run unbounded. The child
process is the containment - the parent's RNG state and imported modules are untouched -
and the child reports whether ``torch`` was even imported, so "no optimizer" is checkable
rather than asserted.

Statistical units: one configuration with many episodes is **one scenario**. Episodes of it
are repeated measurements of that one scenario, never independent replicates, and with one
episode there is no dispersion to report - it is absent, not zero-width.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .cli import CliError, announce_execution
from .dataset_report import (
    bullet_list,
    dataset_identity_summary,
    escape_cell,
    html_document,
    html_table,
    measured_cell,
)
from .inspect_env import DEFAULT_PROBE_INTERPRETER
from .records import Measured, Validity, content_hash, dumps, file_hash

#: Report schema, so a consumer can tell two generations of report apart.
SCENARIO_REPORT_SCHEMA = "research_support.scenario_report.1"

#: Identity of the executed diagnostic set, so a report can be matched to what ran.
DIAGNOSTIC_SET_ID = "non_learning_scenario_diagnostic_set.1"

#: Top-level provenance values.
PROVENANCE_DECLARED_ONLY = "declared_only"
PROVENANCE_WITH_RUNTIME = "declared_plus_verified_runtime"

#: Per-value provenance, matching ``inspect_env.py``'s vocabulary.
PROV_RECORDED = "recorded"
PROV_DERIVED = "declared_derived"
PROV_RUNTIME = "verified_runtime"
PROV_UNKNOWN = "unknown"

#: The reason a runtime quantity is absent when nothing was executed. One string, so a
#: consumer can group every unverified quantity by it.
NOT_EXECUTED_REASON = (
    "not executed: scenario-report is static by default, so nothing was constructed, reset "
    "or stepped; pass execute=True (--execute) to run the declared non-learning diagnostic set"
)

#: Bounds of the executed diagnostic set. Both are printed before anything runs.
DEFAULT_CONTROLLER = "backhaul_aware_greedy"
DEFAULT_EPISODES = 1
DEFAULT_MAX_STEPS = 200
DEFAULT_PROBE_TIMEOUT_S = 900.0

_REAL_DATA_KINDS = ("milan_activity", "prepared_dataset")


# --------------------------------------------------------------------------------------
# Report structures
# --------------------------------------------------------------------------------------


@dataclass
class DeclaredField:
    """One declared configuration value, with where it came from."""

    name: str
    raw: Any
    effective: Measured
    unit: str | None
    source_key: str | None
    provenance: str
    note: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "raw": self.raw,
            "effective": self.effective.to_json(),
            "unit": self.unit,
            "source_key": self.source_key,
            "provenance": self.provenance,
            "note": self.note,
        }


@dataclass
class RuntimeQuantity:
    """One quantity only an execution can establish, and the declaration it is checked against.

    With nothing executed, ``value`` is an absence carrying :data:`NOT_EXECUTED_REASON` and
    ``provenance`` is ``declared_only``. An executed value carries ``verified_runtime``.
    """

    name: str
    value: Measured
    unit: str | None
    provenance: str
    declared: Measured | None = None
    agreement: str = "unverifiable"
    comparison: str = "none"
    note: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value.to_json(),
            "unit": self.unit,
            "provenance": self.provenance,
            "declared": None if self.declared is None else self.declared.to_json(),
            "agreement": self.agreement,
            "comparison": self.comparison,
            "note": self.note,
        }


@dataclass
class ScenarioReport:
    """The declared scenario, the executed observations if any, and the gap between them."""

    config_path: str
    config_hash: str | None
    route: str
    preset_name: str | None
    provenance: str = PROVENANCE_DECLARED_ONLY
    declared_fields: list[DeclaredField] = field(default_factory=list)
    entities: dict[str, Any] = field(default_factory=dict)
    failure_schedule: dict[str, Any] = field(default_factory=dict)
    radio_models: list[dict[str, Any]] = field(default_factory=list)
    calibration: dict[str, Any] = field(default_factory=dict)
    dataset: dict[str, Any] = field(default_factory=dict)
    episodes_file: dict[str, Any] = field(default_factory=dict)
    diagnostic_set: dict[str, Any] = field(default_factory=dict)
    runtime: list[RuntimeQuantity] = field(default_factory=list)
    runtime_raw: dict[str, Any] | None = None
    statistical_units: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    schema: str = SCENARIO_REPORT_SCHEMA

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "config_path": self.config_path,
            "config_hash": self.config_hash,
            "route": self.route,
            "preset_name": self.preset_name,
            "provenance": self.provenance,
            "declared_fields": [item.to_json() for item in self.declared_fields],
            "entities": self.entities,
            "failure_schedule": self.failure_schedule,
            "radio_models": self.radio_models,
            "calibration": self.calibration,
            "dataset": self.dataset,
            "episodes_file": self.episodes_file,
            "diagnostic_set": self.diagnostic_set,
            "runtime": [item.to_json() for item in self.runtime],
            "runtime_raw": self.runtime_raw,
            "statistical_units": self.statistical_units,
            "notes": list(self.notes),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    def declared_value(self, name: str) -> Measured | None:
        for item in self.declared_fields:
            if item.name == name:
                return item.effective
        return None


# --------------------------------------------------------------------------------------
# Static reading
# --------------------------------------------------------------------------------------


def _dig(payload: Mapping[str, Any], dotted: str) -> tuple[Any, bool]:
    """``(value, present)`` for a dotted path, mirroring ``inspect_env._dig``."""

    node: Any = payload
    for part in dotted.split("."):
        if isinstance(node, Mapping) and part in node:
            node = node[part]
        else:
            return None, False
    return node, True


def _scalar_measured(value: Any, unit: str | None) -> Measured:
    if isinstance(value, bool) or isinstance(value, (int, float, str)):
        return Measured.ok(value, unit=unit, source=PROV_RECORDED)
    # A list or object is recorded verbatim as JSON text: summarising it here would invent a
    # number the document does not contain.
    return Measured.ok(json.dumps(value), unit=unit, source=PROV_RECORDED)


#: Declared fields, grouped so the report reads like a scenario rather than a flat dump.
#: ``(dotted key, unit)``.
_DECLARED_GROUPS: tuple[tuple[str, tuple[tuple[str, str | None], ...]], ...] = (
    (
        "identity",
        (
            ("environment_id", None),
            ("schema_version", None),
            ("preset_name", None),
            ("seed", None),
            ("notes", None),
        ),
    ),
    (
        "entities",
        (
            ("n_uavs", "count"),
            ("source.max_demand_points", "count"),
            ("deployment.mode", None),
            ("deployment.positions_m", "m"),
            ("deployment.standby_positions_m", "m"),
            ("deployment.alert_delay_s", "s"),
            ("deployment.launch_delay_s", "s"),
        ),
    ),
    (
        "area_and_altitude",
        (
            ("region.min_xy_m", "m"),
            ("region.max_xy_m", "m"),
            ("dynamics.altitude_range_m", "m"),
            ("dynamics.max_speed_mps", "m/s"),
            ("dynamics.bounds_margin_m", "m"),
            ("dynamics.collision_avoidance", None),
            ("dynamics.record_min_separation", None),
        ),
    ),
    (
        "traffic_and_demand",
        (
            ("source.kind", None),
            ("source.demand_scale_mbps", "Mbps"),
            ("source.split", None),
            ("source.region_id", None),
            ("source.activity_field", None),
            ("source.dataset_root", None),
            ("source.reference_scale_override", None),
            ("source.require_fully_observed_episodes", None),
            ("source.event_overlay", None),
            ("source.synthetic_fixture.grid_shape", "count"),
            ("source.synthetic_fixture.cell_spacing_m", "m"),
            ("source.synthetic_fixture.interval_duration_s", "s"),
            ("source.synthetic_fixture.n_intervals", "count"),
            ("source.synthetic_fixture.base_activity", "activity_units"),
            ("source.synthetic_fixture.diurnal_amplitude", "activity_units"),
            ("source.synthetic_fixture.hotspot_gain", "dimensionless"),
        ),
    ),
    (
        "episode",
        (
            ("episode.semantics", None),
            ("episode.duration_s", "s"),
            ("episode.decision_dt_s", "s"),
            ("episode.physics_dt_s", "s"),
            ("episode.quadrature", None),
        ),
    ),
    (
        "observations",
        (
            ("observations.mode", None),
            ("observations.telemetry_delay_s", "s"),
            ("observations.telemetry_ttl_s", "s"),
            ("observations.sensing_radius_m", "m"),
            ("observations.include_time_of_day", None),
            ("observations.include_episode_progress", None),
            ("observations.position_reference_m", "m"),
            ("observations.demand_reference_mbps", "Mbps"),
            ("observations.fixed_entity_order", None),
            ("observations.on_entity_limit_exceeded", None),
        ),
    ),
    (
        "network_and_scheduler",
        (
            ("network.max_backhaul_hops", "count"),
            ("network.access_and_backhaul_share_band", None),
            ("network.allow_spatial_reuse_between_nodes", None),
            ("network.max_candidate_paths_per_demand", "count"),
            ("network.max_total_candidate_paths", "count"),
            ("network.site_access_radius_m", "m"),
            ("scheduler.objective", None),
            ("scheduler.secondary_rule", None),
            ("scheduler.solver_method", None),
            ("scheduler.max_variables", "count"),
            ("scheduler.max_constraints", "count"),
        ),
    ),
    (
        "reward_and_evaluation",
        (
            ("reward.reference_scale_mbps", "Mbps"),
            ("reward.reference_dt_s", "s"),
            ("reward.motion_weight", "dimensionless"),
            ("reward.motion_weight_rationale", None),
            ("evaluation.recovery_fraction_rho", "ratio"),
            ("evaluation.recovery_sustain_s", "s"),
        ),
    ),
)


def _read_declared(payload: Mapping[str, Any], report: ScenarioReport) -> None:
    for group, entries in _DECLARED_GROUPS:
        for key, unit in entries:
            raw, present = _dig(payload, key)
            if present:
                report.declared_fields.append(
                    DeclaredField(
                        name=key,
                        raw=raw,
                        effective=_scalar_measured(raw, unit),
                        unit=unit,
                        source_key=key,
                        provenance=PROV_RECORDED,
                        note=group,
                    )
                )
            else:
                report.declared_fields.append(
                    DeclaredField(
                        name=key,
                        raw=None,
                        effective=Measured.unknown(
                            "absent from the configuration document; the constructor default "
                            "applies but was not observed",
                            unit=unit,
                        ),
                        unit=unit,
                        source_key=None,
                        provenance=PROV_UNKNOWN,
                        note=group,
                    )
                )


def _derived(report: ScenarioReport, payload: Mapping[str, Any]) -> None:
    """Quantities implied by arithmetic on declared values, labelled as declared-derived."""

    def add(name: str, value: Measured, unit: str | None, note: str) -> None:
        report.declared_fields.append(
            DeclaredField(
                name=name,
                raw=value.value,
                effective=value,
                unit=unit,
                source_key=None,
                provenance=PROV_DERIVED,
                note=note,
            )
        )

    duration, has_duration = _dig(payload, "episode.duration_s")
    decision, has_decision = _dig(payload, "episode.decision_dt_s")
    if has_duration and has_decision and float(decision) > 0.0:
        steps = float(duration) / float(decision)
        add(
            "derived.n_decision_steps",
            Measured.ok(int(round(steps)), unit="steps", source=PROV_DERIVED),
            "steps",
            "duration_s / decision_dt_s; the number of steps an episode is declared to last, "
            "not a number of steps anything ran",
        )
    else:
        add(
            "derived.n_decision_steps",
            Measured.unknown("episode.duration_s or episode.decision_dt_s is absent"),
            "steps",
            "cannot be derived from this document",
        )

    low, has_low = _dig(payload, "region.min_xy_m")
    high, has_high = _dig(payload, "region.max_xy_m")
    if has_low and has_high:
        try:
            extent_x = float(high[0]) - float(low[0])
            extent_y = float(high[1]) - float(low[1])
        except (TypeError, ValueError, IndexError):
            extent_x = extent_y = float("nan")
        add("derived.region_extent_x_m", Measured.from_float(extent_x, unit="m"), "m",
            "max_xy_m[0] - min_xy_m[0]")
        add("derived.region_extent_y_m", Measured.from_float(extent_y, unit="m"), "m",
            "max_xy_m[1] - min_xy_m[1]")
        add(
            "derived.region_area_km2",
            Measured.from_float(extent_x * extent_y / 1e6, unit="km^2"),
            "km^2",
            "declared extent product; it is the configured box, not a served area",
        )


def _entities(payload: Mapping[str, Any], report: ScenarioReport) -> None:
    sites = payload.get("network", {}).get("sites") if isinstance(payload.get("network"), Mapping) else None
    sites = sites if isinstance(sites, list) else []
    positions = payload.get("deployment", {}).get("positions_m") if isinstance(
        payload.get("deployment"), Mapping
    ) else None
    positions = positions if isinstance(positions, list) else []
    altitudes = [float(p[2]) for p in positions if isinstance(p, list) and len(p) >= 3]
    report.entities = {
        "n_uavs_declared": payload.get("n_uavs"),
        "n_terrestrial_sites_declared": len(sites),
        "sites": [
            {
                "site_id": site.get("site_id"),
                "position_m": site.get("position_m"),
                "core_egress_capacity_mbps": site.get("core_egress_capacity_mbps"),
                "serves_access": site.get("serves_access"),
                "serves_uav_backhaul": site.get("serves_uav_backhaul"),
                "accepts_uav_wireless_backhaul": site.get("accepts_uav_wireless_backhaul"),
            }
            for site in sites
            if isinstance(site, Mapping)
        ],
        "aggregate_demand_points": {
            "declared_cap": payload.get("source", {}).get("max_demand_points")
            if isinstance(payload.get("source"), Mapping)
            else None,
            "actual_count": Measured.unknown(
                "the number of demand points depends on the demand source's grid and the cap; "
                + NOT_EXECUTED_REASON
            ).to_json(),
            "entity_kind": "aggregate_demand_point",
            "label_rule": (
                "each ground marker is an AGGREGATE DEMAND POINT for one source grid cell. It "
                "is not a person, a subscriber, a device or a tracked user, and no count of "
                "them is a population."
            ),
        },
        "declared_deployment_altitudes_m": {
            "minimum": (
                Measured.ok(min(altitudes), unit="m", source=PROV_RECORDED).to_json()
                if altitudes
                else Measured.absent(
                    Validity.NOT_RECORDED, "no deployment position declares an altitude"
                ).to_json()
            ),
            "maximum": (
                Measured.ok(max(altitudes), unit="m", source=PROV_RECORDED).to_json()
                if altitudes
                else Measured.absent(
                    Validity.NOT_RECORDED, "no deployment position declares an altitude"
                ).to_json()
            ),
        },
    }


def _failure_schedule(payload: Mapping[str, Any], report: ScenarioReport) -> None:
    events_doc = payload.get("events") if isinstance(payload.get("events"), Mapping) else {}
    source_kind = events_doc.get("source_kind", "none")
    entries = events_doc.get("events") if isinstance(events_doc.get("events"), list) else []
    sites = payload.get("network", {}).get("sites") if isinstance(payload.get("network"), Mapping) else []
    site_ids = [
        site.get("site_id") for site in (sites or []) if isinstance(site, Mapping)
    ]

    declared_events: list[dict[str, Any]] = []
    for index, event in enumerate(entries):
        if not isinstance(event, Mapping):
            report.errors.append(f"events.events[{index}] is not an object")
            continue
        start = event.get("start_s_range")
        duration = event.get("duration_s_range")
        site_index = event.get("site_index")
        fixed_start = (
            isinstance(start, list) and len(start) == 2 and float(start[0]) == float(start[1])
        )
        declared_events.append(
            {
                "index": index,
                "event_type": event.get("event_type"),
                "site_index": site_index,
                "site_id": (
                    site_ids[int(site_index)]
                    if isinstance(site_index, int) and 0 <= int(site_index) < len(site_ids)
                    else None
                ),
                "site_choice": event.get("site_choice"),
                "start_s_range": start,
                "duration_s_range": duration,
                "access_capacity_scale": event.get("access_capacity_scale"),
                "backhaul_capacity_scale": event.get("backhaul_capacity_scale"),
                "start_time_is_fixed": bool(fixed_start),
                "never_repaired_within_episode": duration is None,
                "realised_time_s": (
                    Measured.ok(float(start[0]), unit="s", source=PROV_RECORDED).to_json()
                    if fixed_start
                    else Measured.unknown(
                        "the start time is a sampling range, so the time this event actually "
                        "occurs is drawn per episode; " + NOT_EXECUTED_REASON,
                        unit="s",
                    ).to_json()
                ),
            }
        )
    report.failure_schedule = {
        "source_kind": source_kind,
        "n_declared_events": len(declared_events),
        "events": declared_events,
        "schedule_semantics": (
            "an event with duration_s_range null never ends inside the episode: the site is "
            "not repaired. A finite duration IS a repair, and a recovery observed after it "
            "is not evidence that the UAVs restored service."
        ),
        "realised_schedule_status": (
            "declared_only: the per-episode schedule is sampled at reset; " + NOT_EXECUTED_REASON
        ),
    }
    if source_kind == "none":
        report.warnings.append(
            "this scenario declares no capability event: nothing fails, so no restoration "
            "can be measured on it"
        )


def _radio_models(payload: Mapping[str, Any], report: ScenarioReport) -> None:
    models = payload.get("network", {}).get("radio_models") if isinstance(
        payload.get("network"), Mapping
    ) else {}
    models = models if isinstance(models, Mapping) else {}
    fields = (
        ("frequency_hz", "Hz"),
        ("bandwidth_hz", "Hz"),
        ("tx_power_dbm", "dBm"),
        ("antenna_gain_db", "dB"),
        ("noise_figure_db", "dB"),
        ("reference_distance_m", "m"),
        ("reference_loss_db", "dB"),
        ("path_loss_exponent", "dimensionless"),
        ("extra_loss_db", "dB"),
        ("spectral_efficiency", "bit/s/Hz"),
        ("min_snr_db", "dB"),
        ("max_range_m", "m"),
        ("calibration_status", None),
    )
    for name, model in sorted(models.items()):
        if not isinstance(model, Mapping):
            report.errors.append(f"network.radio_models[{name}] is not an object")
            continue
        entry: dict[str, Any] = {"link_class": name}
        for key, unit in fields:
            if key in model:
                entry[key] = Measured.ok(model[key], unit=unit, source=PROV_RECORDED).to_json()
            else:
                entry[key] = Measured.unknown(
                    "absent from the configuration document; the constructor default applies "
                    "but was not observed",
                    unit=unit,
                ).to_json()
        report.radio_models.append(entry)

    assumed = [
        f"network.radio_models[{name}]"
        for name, model in sorted(models.items())
        if isinstance(model, Mapping)
        and model.get("calibration_status") != "empirically_calibrated"
    ]
    calibrated = [
        f"network.radio_models[{name}]"
        for name, model in sorted(models.items())
        if isinstance(model, Mapping)
        and model.get("calibration_status") == "empirically_calibrated"
    ]
    provenance = payload.get("parameter_provenance")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    for key, value in sorted(provenance.items()):
        (calibrated if value == "empirically_calibrated" else assumed).append(key)
    report.calibration = {
        "empirically_calibrated": calibrated,
        "engineering_assumptions": assumed,
        "rule": (
            "mirrors EnvConfig.calibration_summary(): a radio model is calibrated only when it "
            "says so, and a declared parameter_provenance entry is an assumption unless it "
            "says 'empirically_calibrated'"
        ),
    }
    if assumed and not calibrated:
        report.notes.append(
            "every radio and capacity parameter in this scenario is an engineering assumption; "
            "absolute Mbps figures from it characterise the model, not a real network"
        )


def _episodes_file_block(path: Path, report: ScenarioReport) -> list[int]:
    """Read the ``--episodes-file`` list the baseline evaluator consumes."""

    if not path.is_file():
        raise CliError(
            f"episodes file not found: {path}. Nothing is substituted for it: a missing "
            "episode list is not an empty one."
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CliError(f"{path}: invalid JSON ({error})") from error
    if isinstance(payload, Mapping):
        values = payload.get("episode_seeds", payload.get("seeds"))
        if values is None:
            raise CliError(
                f"{path} must hold a list, or an object with 'episode_seeds'/'seeds'; this is "
                "the form scripts/uav_service_restoration/evaluate_baselines.py reads"
            )
    else:
        values = payload
    if not isinstance(values, list) or not values:
        raise CliError(f"{path} holds no episode seed")
    seeds: list[int] = []
    invalid = 0
    for value in values:
        try:
            seeds.append(int(value))
        except (TypeError, ValueError):
            invalid += 1
    duplicates = len(seeds) - len(set(seeds))
    report.episodes_file = {
        "path": str(path.resolve()),
        "sha256": file_hash(str(path)),
        "n_seeds": len(seeds),
        "n_invalid_entries": invalid,
        "n_duplicated_seeds": duplicates,
        "seeds_preview": seeds[:20],
        "note": (
            "these seeds select episodes of THIS one scenario configuration; they are "
            "repeated measurements of one scenario, not independent replicates of a method"
        ),
    }
    if invalid:
        report.errors.append(f"{invalid} entries of the episode list are not integer seeds")
    if duplicates:
        report.errors.append(
            f"{duplicates} episode seeds are repeated; a repeated seed replays the same "
            "episode and is not a second independent observation"
        )
    return seeds


# --------------------------------------------------------------------------------------
# Runtime quantities
# --------------------------------------------------------------------------------------

#: ``(name, unit)`` of every quantity only an execution can establish. Listing them here
#: means the static report names each hole instead of omitting it.
_RUNTIME_QUANTITIES: tuple[tuple[str, str | None], ...] = (
    ("n_agents", "count"),
    ("observation_dim", "count"),
    ("observation_dtype", None),
    ("observation_shape", None),
    ("state_dim", "count"),
    ("state_shape", None),
    ("action_dim", "count"),
    ("action_space_low", None),
    ("action_space_high", None),
    ("n_aggregate_demand_slots", "count"),
    ("episode_steps_observed", "steps"),
    ("episode_length_steps", "steps"),
    ("n_episodes_terminated", "count"),
    ("n_episodes_truncated", "count"),
    ("uav_x_min_m", "m"),
    ("uav_x_max_m", "m"),
    ("uav_y_min_m", "m"),
    ("uav_y_max_m", "m"),
    ("uav_altitude_min_m", "m"),
    ("uav_altitude_max_m", "m"),
    ("max_interval_mean_speed_mps", "m/s"),
    ("n_non_finite_observation_vectors", "count"),
    ("n_non_finite_state_vectors", "count"),
    ("n_non_finite_rewards", "count"),
    ("n_action_shape_violations", "count"),
    ("n_action_range_violations", "count"),
    ("n_non_finite_actions", "count"),
    ("reward_min", "reward"),
    ("reward_max", "reward"),
    ("dataset_hash_at_runtime", None),
    ("is_real_activity_data", None),
    ("episode_id", None),
    ("episode_split", None),
    ("scheduler_status", None),
    ("realised_event_times_s", "s"),
    ("optimizer_updates", "count"),
    ("checkpoints_loaded", "count"),
    ("torch_imported", None),
)


def _unverified_runtime(report: ScenarioReport) -> None:
    for name, unit in _RUNTIME_QUANTITIES:
        report.runtime.append(
            RuntimeQuantity(
                name=name,
                value=Measured.unknown(NOT_EXECUTED_REASON, unit=unit),
                unit=unit,
                provenance=PROVENANCE_DECLARED_ONLY,
                declared=None,
                agreement="unverifiable",
                comparison="none",
            )
        )


def _failed_runtime(report: ScenarioReport, reason: str) -> None:
    """Every runtime quantity after a failed execution: absent with the failure reason.

    A failed diagnostic run is never reported as a passed check or as a default value.
    """

    for name, unit in _RUNTIME_QUANTITIES:
        report.runtime.append(
            RuntimeQuantity(
                name=name,
                value=Measured.absent(Validity.MISSING_ARTIFACT, reason, unit=unit),
                unit=unit,
                provenance=PROVENANCE_DECLARED_ONLY,
                declared=None,
                agreement="unverifiable",
                comparison="none",
            )
        )


def _observed(
    report: ScenarioReport,
    name: str,
    value: Any,
    unit: str | None,
    *,
    declared: Measured | None = None,
    comparison: str = "none",
    note: str | None = None,
) -> None:
    """Record one observed quantity and, when a declaration exists, how the two relate."""

    if value is None:
        measured = Measured.absent(
            Validity.NOT_RECORDED, f"the diagnostic run reported no {name}", unit=unit
        )
    elif isinstance(value, bool) or isinstance(value, (int, str)):
        measured = Measured.ok(value, unit=unit, source=PROV_RUNTIME)
    elif isinstance(value, (list, tuple)):
        measured = Measured.ok(json.dumps(list(value)), unit=unit, source=PROV_RUNTIME)
    else:
        measured = Measured.from_float(value, unit=unit, source=PROV_RUNTIME)

    agreement = "no_declaration"
    if declared is not None and declared.validity is Validity.OK and measured.validity is Validity.OK:
        agreement = _agreement(declared.value, measured.value, comparison)
    elif declared is not None:
        agreement = "unverifiable"
    report.runtime.append(
        RuntimeQuantity(
            name=name,
            value=measured,
            unit=unit,
            provenance=PROV_RUNTIME,
            declared=declared,
            agreement=agreement,
            comparison=comparison,
            note=note,
        )
    )
    if agreement in ("mismatch", "exceeds_declared_bound"):
        report.warnings.append(
            f"observed {name} = {measured.value!r} against declared {declared.value!r} "
            f"({agreement})"
        )


def _agreement(declared: Any, observed: Any, comparison: str) -> str:
    try:
        if comparison == "equality":
            if isinstance(declared, str) or isinstance(observed, str):
                return "match" if str(declared) == str(observed) else "mismatch"
            return "match" if float(declared) == float(observed) else "mismatch"
        if comparison == "upper_bound":
            return (
                "within_declared_bound"
                if float(observed) <= float(declared) + 1e-6
                else "exceeds_declared_bound"
            )
        if comparison == "lower_bound":
            return (
                "within_declared_bound"
                if float(observed) >= float(declared) - 1e-6
                else "exceeds_declared_bound"
            )
    except (TypeError, ValueError):
        return "unverifiable"
    return "no_declaration"


# --------------------------------------------------------------------------------------
# The executed diagnostic set (child process)
# --------------------------------------------------------------------------------------

_PROBE_SOURCE = r'''
import json, sys
sys.path.insert(0, {repo!r})
import numpy as np

config_path = {config!r}
dataset_root = {dataset!r}
controller_name = {controller!r}
episodes = int({episodes!r})
max_steps = int({max_steps!r})
seeds = list({seeds!r})

from envs.uav_service_restoration.baselines import CONTROLLER_NAMES, build_controller
from envs.uav_service_restoration.config import load_config
from envs.uav_service_restoration.env import UAVServiceRestorationEnv

if controller_name not in CONTROLLER_NAMES:
    raise SystemExit("unknown controller %r; available: %s" % (controller_name, CONTROLLER_NAMES))

out = {{
    "controller": controller_name,
    "controller_kind": "untuned_diagnostic_rule",
    "optimizer_updates": 0,
    "checkpoints_loaded": 0,
    "episodes_run": [],
}}

config = load_config(config_path)
env = UAVServiceRestorationEnv(config, dataset_root=dataset_root)
first = env.possible_agents[0]
action_space = env.action_space(first)
obs_space = env.observation_space(first)
low = np.asarray(action_space.low, dtype=np.float64)
high = np.asarray(action_space.high, dtype=np.float64)
out["constructor"] = "envs.uav_service_restoration.env.UAVServiceRestorationEnv"
out["n_agents"] = int(len(env.possible_agents))
out["observation_dim"] = int(env.get_obs_dim())
out["state_dim"] = int(env.get_state_dim())
out["action_dim"] = int(np.prod(action_space.shape))
out["action_space"] = {{
    "shape": [int(v) for v in action_space.shape],
    "low": [float(v) for v in low.reshape(-1)],
    "high": [float(v) for v in high.reshape(-1)],
    "dtype": str(action_space.dtype),
}}
out["observation_space"] = {{
    "shape": [int(v) for v in obs_space.shape],
    "dtype": str(obs_space.dtype),
}}
out["n_aggregate_demand_slots"] = int(env.demand_layout.n_slots)
out["schema"] = env.schema()

controller = build_controller(controller_name, config, seed=int(seeds[0]))
decision_dt_s = float(config.episode.decision_dt_s)

for index in range(episodes):
    seed = int(seeds[index % len(seeds)])
    controller.reset()
    observations, _infos = env.reset(seed=seed)
    record = {{"episode_index": index, "seed": seed}}
    positions = np.asarray(env.uav_positions_m, dtype=np.float64)
    mins = positions.min(axis=0).tolist()
    maxs = positions.max(axis=0).tolist()
    previous = positions.copy()
    max_mean_speed = 0.0
    non_finite_obs = 0
    non_finite_state = 0
    non_finite_reward = 0
    action_shape_violations = 0
    action_range_violations = 0
    non_finite_actions = 0
    rewards = []
    steps = 0
    terminated = False
    truncated = False
    for value in observations.values():
        if not np.all(np.isfinite(np.asarray(value, dtype=np.float64))):
            non_finite_obs += 1
    record["observation_dtype"] = str(np.asarray(next(iter(observations.values()))).dtype)
    record["observation_shape"] = [
        int(v) for v in np.asarray(next(iter(observations.values()))).shape
    ]
    state = np.asarray(env.state(), dtype=np.float64)
    record["state_shape"] = [int(v) for v in state.shape]
    if not np.all(np.isfinite(state)):
        non_finite_state += 1
    while env.agents and steps < max_steps:
        view = env.get_current_state()
        actions = controller.act(view, list(env.agents))
        for value in actions.values():
            array = np.asarray(value, dtype=np.float64)
            if tuple(array.shape) != tuple(action_space.shape):
                action_shape_violations += 1
                continue
            if not np.all(np.isfinite(array)):
                non_finite_actions += 1
            elif np.any(array < low - 1e-9) or np.any(array > high + 1e-9):
                action_range_violations += 1
        observations, reward, term, trunc, _infos = env.step(actions)
        steps += 1
        terminated = bool(any(term.values())) if term else terminated
        truncated = bool(any(trunc.values())) if trunc else truncated
        for value in observations.values():
            if not np.all(np.isfinite(np.asarray(value, dtype=np.float64))):
                non_finite_obs += 1
        state = np.asarray(env.state(), dtype=np.float64)
        if not np.all(np.isfinite(state)):
            non_finite_state += 1
        for value in reward.values():
            number = float(value)
            if np.isfinite(number):
                rewards.append(number)
            else:
                non_finite_reward += 1
        positions = np.asarray(env.uav_positions_m, dtype=np.float64)
        mins = np.minimum(mins, positions.min(axis=0)).tolist()
        maxs = np.maximum(maxs, positions.max(axis=0)).tolist()
        if decision_dt_s > 0.0:
            travelled = np.linalg.norm(positions - previous, axis=1) / decision_dt_s
            max_mean_speed = max(max_mean_speed, float(travelled.max()))
        previous = positions.copy()
    record["steps"] = int(steps)
    # ``agents`` is emptied only when the episode really finished, so this distinguishes a
    # completed episode from one the step cap cut short.
    record["episode_completed"] = bool(not env.agents)
    record["step_cap_reached"] = bool(steps >= max_steps and env.agents)
    record["terminated"] = bool(terminated)
    record["truncated"] = bool(truncated)
    record["position_min_m"] = [float(v) for v in mins]
    record["position_max_m"] = [float(v) for v in maxs]
    record["max_interval_mean_speed_mps"] = float(max_mean_speed)
    record["n_non_finite_observation_vectors"] = int(non_finite_obs)
    record["n_non_finite_state_vectors"] = int(non_finite_state)
    record["n_non_finite_rewards"] = int(non_finite_reward)
    record["n_action_shape_violations"] = int(action_shape_violations)
    record["n_action_range_violations"] = int(action_range_violations)
    record["n_non_finite_actions"] = int(non_finite_actions)
    record["reward_min"] = float(min(rewards)) if rewards else None
    record["reward_max"] = float(max(rewards)) if rewards else None
    diagnostics = env.get_privileged_diagnostics()
    record["episode_id"] = diagnostics.get("episode_id")
    record["split"] = diagnostics.get("split")
    record["dataset_hash"] = diagnostics.get("dataset_hash")
    record["scheduler_status"] = diagnostics.get("scheduler_status")
    record["exogenous_events"] = diagnostics.get("exogenous_events")
    record["source_metadata"] = diagnostics.get("source_metadata")
    record["episode_summary"] = env.episode_summary()
    out["episodes_run"].append(record)

env.close()
# Structural evidence for the claim that nothing here can train: the learning stack was
# never even imported by this process.
out["torch_imported"] = bool("torch" in sys.modules)
sys.stdout.write("<<<SCENARIO_JSON>>>" + json.dumps(out, default=str))
'''


def run_diagnostic_probe(
    *,
    config_path: Path,
    dataset: Path | None,
    controller: str,
    episodes: int,
    max_steps: int,
    seeds: Sequence[int],
    interpreter: str | None = None,
    repo_root: str | None = None,
    timeout_s: float = DEFAULT_PROBE_TIMEOUT_S,
) -> tuple[str, dict[str, Any]]:
    """Run the bounded rule-controller rollout in a child process.

    A child process is the containment, exactly as in ``inspect_env.run_probe``: whatever the
    constructor and the scheduler do, the parent's RNG state, imported modules and global
    configuration are untouched. No optimizer is constructed and no checkpoint is opened;
    the child reports whether ``torch`` was imported at all.
    """

    root = repo_root or str(Path(__file__).resolve().parents[2])
    source = _PROBE_SOURCE.format(
        repo=root,
        config=str(config_path),
        dataset=None if dataset is None else str(dataset),
        controller=controller,
        episodes=int(episodes),
        max_steps=int(max_steps),
        seeds=[int(seed) for seed in seeds],
    )
    executable = interpreter or DEFAULT_PROBE_INTERPRETER
    if not Path(executable).exists():
        executable = sys.executable
    try:
        completed = subprocess.run(
            [executable, "-c", source],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except subprocess.TimeoutExpired:
        return "timeout", {"error": f"the diagnostic run did not finish within {timeout_s} s"}
    marker = "<<<SCENARIO_JSON>>>"
    if marker in completed.stdout:
        payload = completed.stdout.split(marker, 1)[1]
        try:
            return "ok", json.loads(payload)
        except json.JSONDecodeError as error:
            return "malformed", {"error": str(error), "stdout_tail": payload[-2000:]}
    return "failed", {
        "returncode": completed.returncode,
        "stderr_tail": completed.stderr[-4000:],
        "stdout_tail": completed.stdout[-2000:],
    }


def _absorb_runtime(report: ScenarioReport, payload: Mapping[str, Any]) -> None:
    """Turn the child's observations into runtime quantities checked against declarations."""

    episodes = list(payload.get("episodes_run") or [])
    report.runtime_raw = dict(payload)

    _observed(report, "n_agents", payload.get("n_agents"), "count",
              declared=report.declared_value("n_uavs"), comparison="equality")
    _observed(report, "observation_dim", payload.get("observation_dim"), "count")
    _observed(report, "state_dim", payload.get("state_dim"), "count")
    _observed(report, "action_dim", payload.get("action_dim"), "count")
    space = payload.get("action_space") or {}
    _observed(report, "observation_dtype",
              (episodes[0].get("observation_dtype") if episodes else None), None)
    _observed(
        report,
        "observation_shape",
        (episodes[0].get("observation_shape") if episodes else None),
        None,
        note="the per-agent observation vector shape the environment actually produced",
    )
    _observed(report, "state_shape", (episodes[0].get("state_shape") if episodes else None), None)
    _observed(report, "action_space_low", space.get("low"), None)
    _observed(report, "action_space_high", space.get("high"), None)
    _observed(
        report,
        "n_aggregate_demand_slots",
        payload.get("n_aggregate_demand_slots"),
        "count",
        declared=report.declared_value("source.max_demand_points"),
        comparison="upper_bound",
        note=(
            "slots are aggregate demand points, capped by source.max_demand_points; they are "
            "not people"
        ),
    )

    if not episodes:
        report.errors.append(
            "the diagnostic run reported no episode; no observed quantity is available and "
            "none is substituted"
        )
        return

    steps = [int(item.get("steps", 0)) for item in episodes]
    completed = [bool(item.get("episode_completed")) for item in episodes]
    _observed(report, "episode_steps_observed", int(max(steps)), "steps",
              note="the largest number of decision steps this run actually executed")
    declared_steps = report.declared_value("derived.n_decision_steps")
    if all(completed):
        _observed(
            report,
            "episode_length_steps",
            int(max(steps)),
            "steps",
            declared=declared_steps,
            comparison="equality",
            note="every executed episode ran to its own end, so this is the episode length",
        )
    else:
        report.runtime.append(
            RuntimeQuantity(
                name="episode_length_steps",
                value=Measured.unknown(
                    "the step cap stopped at least one episode before it ended, so the "
                    "observed step count is a lower bound on the episode length, not the "
                    "length itself",
                    unit="steps",
                ),
                unit="steps",
                provenance=PROV_RUNTIME,
                declared=declared_steps,
                agreement="unverifiable",
                comparison="equality",
            )
        )
        report.warnings.append(
            "the bounded diagnostic set reached its step cap; the episode length is reported "
            "as unverified rather than as the number of steps that ran"
        )

    _observed(report, "n_episodes_terminated",
              int(sum(1 for item in episodes if item.get("terminated"))), "count",
              note="declared episode.semantics decides which of termination and truncation "
                   "a horizon boundary produces")
    _observed(report, "n_episodes_truncated",
              int(sum(1 for item in episodes if item.get("truncated"))), "count")
    semantics = report.declared_value("episode.semantics")
    if semantics is not None and semantics.validity is Validity.OK and all(completed):
        expected = "truncation" if semantics.value == "continuing" else "termination"
        observed_kind = (
            "truncation"
            if all(item.get("truncated") for item in episodes)
            else "termination"
            if all(item.get("terminated") for item in episodes)
            else "mixed_or_neither"
        )
        report.runtime.append(
            RuntimeQuantity(
                name="boundary_kind_at_horizon",
                value=Measured.ok(observed_kind, source=PROV_RUNTIME),
                unit=None,
                provenance=PROV_RUNTIME,
                declared=Measured.ok(expected, source=PROV_RECORDED),
                agreement="match" if observed_kind == expected else "mismatch",
                comparison="equality",
                note=(
                    "a 'continuing' episode must end in truncation; reporting it as "
                    "termination would bootstrap a value of zero past the horizon"
                ),
            )
        )
        if observed_kind != expected:
            report.errors.append(
                f"declared episode.semantics {semantics.value!r} implies {expected} at the "
                f"horizon, but the run produced {observed_kind}"
            )

    mins = [item.get("position_min_m") or [None, None, None] for item in episodes]
    maxs = [item.get("position_max_m") or [None, None, None] for item in episodes]

    def column(values: Sequence[Sequence[Any]], axis: int, reducer: Any) -> float | None:
        numbers = [
            float(row[axis])
            for row in values
            if isinstance(row, (list, tuple)) and len(row) > axis and row[axis] is not None
        ]
        return reducer(numbers) if numbers else None

    region_min = report.declared_value("region.min_xy_m")
    region_max = report.declared_value("region.max_xy_m")
    bounds: list[float] | None = None
    if region_min is not None and region_max is not None:
        try:
            low_xy = json.loads(str(region_min.value)) if isinstance(region_min.value, str) else None
            high_xy = json.loads(str(region_max.value)) if isinstance(region_max.value, str) else None
            if low_xy and high_xy:
                bounds = [float(low_xy[0]), float(low_xy[1]), float(high_xy[0]), float(high_xy[1])]
        except (TypeError, ValueError, IndexError):
            bounds = None

    for axis, label in ((0, "x"), (1, "y")):
        low_value = column(mins, axis, min)
        high_value = column(maxs, axis, max)
        _observed(
            report,
            f"uav_{label}_min_m",
            low_value,
            "m",
            declared=(
                Measured.ok(bounds[axis], unit="m", source=PROV_RECORDED) if bounds else None
            ),
            comparison="lower_bound",
            note="the lowest coordinate any UAV reached, against the declared region minimum",
        )
        _observed(
            report,
            f"uav_{label}_max_m",
            high_value,
            "m",
            declared=(
                Measured.ok(bounds[2 + axis], unit="m", source=PROV_RECORDED) if bounds else None
            ),
            comparison="upper_bound",
            note="the highest coordinate any UAV reached, against the declared region maximum",
        )

    altitude_range = report.declared_value("dynamics.altitude_range_m")
    altitude_low = altitude_high = None
    if altitude_range is not None and isinstance(altitude_range.value, str):
        try:
            parsed = json.loads(altitude_range.value)
            altitude_low, altitude_high = float(parsed[0]), float(parsed[1])
        except (TypeError, ValueError, IndexError):
            altitude_low = altitude_high = None
    _observed(
        report,
        "uav_altitude_min_m",
        column(mins, 2, min),
        "m",
        declared=(
            Measured.ok(altitude_low, unit="m", source=PROV_RECORDED)
            if altitude_low is not None
            else None
        ),
        comparison="lower_bound",
    )
    _observed(
        report,
        "uav_altitude_max_m",
        column(maxs, 2, max),
        "m",
        declared=(
            Measured.ok(altitude_high, unit="m", source=PROV_RECORDED)
            if altitude_high is not None
            else None
        ),
        comparison="upper_bound",
    )
    _observed(
        report,
        "max_interval_mean_speed_mps",
        max(
            (float(item.get("max_interval_mean_speed_mps") or 0.0) for item in episodes),
            default=None,
        ),
        "m/s",
        declared=report.declared_value("dynamics.max_speed_mps"),
        comparison="upper_bound",
        note=(
            "displacement between consecutive decision times divided by decision_dt_s: a "
            "decision-interval average, so being under the declared instantaneous limit is "
            "consistency, not proof of it"
        ),
    )

    for name in (
        "n_non_finite_observation_vectors",
        "n_non_finite_state_vectors",
        "n_non_finite_rewards",
        "n_action_shape_violations",
        "n_action_range_violations",
        "n_non_finite_actions",
    ):
        total = int(sum(int(item.get(name) or 0) for item in episodes))
        _observed(report, name, total, "count")
        if total:
            report.errors.append(
                f"the diagnostic run observed {total} {name.replace('_', ' ')}; this is a "
                "defect in the scenario or the environment, not a tolerance"
            )

    reward_mins = [item.get("reward_min") for item in episodes if item.get("reward_min") is not None]
    reward_maxs = [item.get("reward_max") for item in episodes if item.get("reward_max") is not None]
    _observed(report, "reward_min", min(reward_mins) if reward_mins else None, "reward")
    _observed(report, "reward_max", max(reward_maxs) if reward_maxs else None, "reward")

    first = episodes[0]
    metadata = first.get("source_metadata") or {}
    _observed(report, "dataset_hash_at_runtime", first.get("dataset_hash"), None)
    _observed(report, "is_real_activity_data", metadata.get("is_real_activity_data"), None)
    _observed(report, "episode_id", first.get("episode_id"), None)
    _observed(
        report,
        "episode_split",
        first.get("split"),
        None,
        declared=report.declared_value("source.split"),
        comparison="equality",
    )
    _observed(report, "scheduler_status", first.get("scheduler_status"), None)
    events = first.get("exogenous_events")
    _observed(
        report,
        "realised_event_times_s",
        json.dumps(events, default=str) if events is not None else None,
        "s",
        note="the schedule this episode actually sampled, from the privileged diagnostics",
    )
    _observed(report, "optimizer_updates", int(payload.get("optimizer_updates", 0)), "count")
    _observed(report, "checkpoints_loaded", int(payload.get("checkpoints_loaded", 0)), "count")
    _observed(report, "torch_imported", bool(payload.get("torch_imported", False)), None,
              note="structural evidence that no learning stack was even imported")
    if metadata.get("is_real_activity_data") is False:
        report.notes.append(
            "the executed run confirms the demand source is NOT real activity data"
        )
    if payload.get("optimizer_updates", 0) != 0 or payload.get("torch_imported", False):
        report.errors.append(
            "the diagnostic run reported an optimizer update or a torch import; that "
            "contradicts this command's zero-fit contract and the result must not be used"
        )


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def _statistical_units(report: ScenarioReport, *, episodes_run: int) -> None:
    absent_sd = Measured.absent(
        Validity.NOT_APPLICABLE,
        "n=1 scenario configuration: a standard deviation across scenarios does not exist; "
        "it is absent, not zero-width",
    )
    if episodes_run >= 2:
        episode_dispersion: dict[str, Any] = {
            "status": "computable",
            "note": (
                f"{episodes_run} episodes of ONE configuration: a dispersion over them is "
                "within-scenario variation, never a between-replicate error bar"
            ),
        }
    else:
        episode_dispersion = {
            "status": "absent",
            "value": Measured.absent(
                Validity.NOT_APPLICABLE,
                f"n={episodes_run} executed episode: SD, SE and CI do not exist for a single "
                "observation; they are absent, not zero-width",
            ).to_json(),
        }
    report.statistical_units = {
        "unit_of_analysis": "one scenario configuration",
        "n_scenario_configurations": 1,
        "n_episodes_executed": episodes_run,
        "dispersion_across_scenarios": absent_sd.to_json(),
        "dispersion_across_episodes": episode_dispersion,
        "rule": (
            "one configuration with many episodes is ONE scenario. Episodes are repeated "
            "measurements of it and never independent replicates of a method; an independent "
            "replicate needs its own training fit or its own configuration."
        ),
    }


def inspect_scenario(
    *,
    config_path: Path,
    dataset: Path | None = None,
    episodes_file: Path | None = None,
    execute: bool = False,
    controller: str = DEFAULT_CONTROLLER,
    episodes: int = DEFAULT_EPISODES,
    max_steps: int = DEFAULT_MAX_STEPS,
    output_dir: Path | None = None,
    interpreter: str | None = None,
) -> ScenarioReport:
    """Build the scenario report. ``execute=False`` reads files and runs nothing."""

    config_path = Path(config_path)
    if not config_path.is_file():
        raise CliError(
            f"scenario configuration not found: {config_path}. No preset is substituted for "
            "it; name the configuration you mean."
        )
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CliError(f"{config_path}: invalid JSON ({error})") from error
    if not isinstance(payload, Mapping):
        raise CliError(f"{config_path}: expected a JSON object at the top level")

    environment_id = payload.get("environment_id")
    if environment_id != "uav_service_restoration_v0":
        raise CliError(
            f"{config_path} declares environment_id {environment_id!r}; this report understands "
            "'uav_service_restoration_v0' only. Use `inspect-env --route <route>` for another "
            "route rather than reading this document against the wrong contract."
        )

    report = ScenarioReport(
        config_path=str(config_path.resolve()),
        config_hash=file_hash(str(config_path)),
        route="service-restoration",
        preset_name=payload.get("preset_name"),
    )
    _read_declared(payload, report)
    _derived(report, payload)
    _entities(payload, report)
    _failure_schedule(payload, report)
    _radio_models(payload, report)

    source = payload.get("source") if isinstance(payload.get("source"), Mapping) else {}
    kind = source.get("kind")
    declared_root = source.get("dataset_root")
    if dataset is not None:
        report.dataset = dataset_identity_summary(Path(dataset))
        report.dataset["declared_dataset_root"] = declared_root
        report.dataset["used_by_this_scenario"] = kind in _REAL_DATA_KINDS
        if kind not in _REAL_DATA_KINDS:
            report.warnings.append(
                f"source.kind is {kind!r}, a self-contained fixture: the dataset you named is "
                "reported for identity only and is NOT read by this scenario"
            )
        elif declared_root and Path(declared_root).name != Path(dataset).name:
            report.warnings.append(
                f"the configuration declares dataset_root {declared_root!r} but this report "
                f"was given {str(dataset)!r}; the run would read the one passed here"
            )
    else:
        report.dataset = {
            "path": None,
            "status": "not_provided",
            "declared_dataset_root": declared_root,
            "used_by_this_scenario": kind in _REAL_DATA_KINDS,
            "reason": (
                "no dataset was named; the configuration's declared dataset_root is reported "
                "as declared and was not opened"
            ),
        }
    if kind == "synthetic_fixture":
        report.notes.append(
            "this scenario's demand source is an ANALYTIC FIXTURE: not real activity data, "
            "not measured Mbps and not a population count"
        )

    seeds: list[int] = []
    if episodes_file is not None:
        seeds = _episodes_file_block(Path(episodes_file), report)
    else:
        report.episodes_file = {
            "path": None,
            "status": "not_provided",
            "reason": "no episode list was named; seeds come from the configuration's seed",
        }
    if not seeds:
        declared_seed = payload.get("seed")
        seeds = [int(declared_seed)] if isinstance(declared_seed, int) else [17]

    diagnostic_set = {
        "id": DIAGNOSTIC_SET_ID,
        "controller": controller,
        "controller_kind": "untuned_diagnostic_rule, no learned parameter",
        "episodes_requested": int(episodes),
        "max_steps_per_episode": int(max_steps),
        "seeds": [int(seed) for seed in seeds[: max(1, int(episodes))]],
        "steps": [
            "construct the environment in a child process",
            "reset it once per episode with a fixed seed",
            "step it with the named untuned rule controller, bounded by max_steps_per_episode",
            "record observation/state/action shapes, non-finite checks and action-space "
            "conformance",
            "record the coordinates and altitudes actually reached, and the boundary kind",
            "read the privileged diagnostics for the episode identity and realised events",
        ],
        "optimizer_updates": 0,
        "checkpoints_loaded": 0,
        "formal_training_fits": 0,
        "runs_in_child_process": True,
    }

    if not execute:
        diagnostic_set["status"] = "not_run"
        diagnostic_set["status_detail"] = (
            "declared here so a reader can see what --execute would do; nothing in this "
            "report was executed"
        )
        report.diagnostic_set = diagnostic_set
        report.provenance = PROVENANCE_DECLARED_ONLY
        _unverified_runtime(report)
        _statistical_units(report, episodes_run=0)
        report.notes.append(
            "static report: no environment was constructed, no episode was run and no process "
            "was started. Every runtime quantity above is UNKNOWN, which is not a pass."
        )
        return report

    if kind in _REAL_DATA_KINDS and dataset is None:
        candidate = Path(str(declared_root)) if declared_root else None
        if candidate is None or not candidate.is_dir():
            raise CliError(
                f"source.kind is {kind!r} and the declared dataset_root "
                f"{declared_root!r} is not a directory in this checkout. Pass the prepared "
                "cache with --dataset; there is no synthetic fallback for a real-data "
                "configuration."
            )
    dataset_for_run = dataset if dataset is not None else (
        Path(str(declared_root)) if kind in _REAL_DATA_KINDS and declared_root else None
    )
    if dataset_for_run is not None and not Path(dataset_for_run).is_dir():
        raise CliError(f"dataset root is not a directory: {dataset_for_run}")

    announce_execution(
        what=(
            "bounded forward-only rule-controller rollout of one scenario configuration "
            "(the declared non-learning diagnostic set)"
        ),
        route="service-restoration",
        source_kind="rule_controller_rollout",
        policy_identity=f"{controller} (untuned diagnostic rule, no learned parameter)",
        output=Path(output_dir) if output_dir is not None else None,
        optimizer_updates=0,
        extra=[
            f"config              : {config_path.resolve()}",
            f"dataset             : {dataset_for_run or 'none (self-contained fixture)'}",
            f"episodes            : {episodes}",
            f"max steps / episode : {max_steps}",
            f"seeds               : {diagnostic_set['seeds']}",
            "checkpoints loaded  : 0",
            "child process       : yes (the parent's RNG state is untouched)",
        ],
    )

    status, probe_payload = run_diagnostic_probe(
        config_path=config_path,
        dataset=dataset_for_run,
        controller=controller,
        episodes=int(episodes),
        max_steps=int(max_steps),
        seeds=diagnostic_set["seeds"],
        interpreter=interpreter,
    )
    diagnostic_set["status"] = status
    report.diagnostic_set = diagnostic_set
    if status != "ok":
        detail = probe_payload.get("error") or (probe_payload.get("stderr_tail") or "")[-600:]
        report.provenance = PROVENANCE_DECLARED_ONLY
        report.runtime_raw = dict(probe_payload)
        report.errors.append(
            f"the diagnostic run did not complete ({status}): {detail}. Nothing observed is "
            "reported, and no declared value is promoted in its place."
        )
        _failed_runtime(report, f"diagnostic run {status}: {detail}"[:400])
        _statistical_units(report, episodes_run=0)
        return report

    report.provenance = PROVENANCE_WITH_RUNTIME
    _absorb_runtime(report, probe_payload)
    episodes_run = len(probe_payload.get("episodes_run") or [])
    diagnostic_set["episodes_executed"] = episodes_run
    _statistical_units(report, episodes_run=episodes_run)
    report.notes.append(
        f"executed: {episodes_run} bounded episode(s) with the {controller} untuned rule "
        "controller, zero optimizer updates and no checkpoint. Quantities marked "
        f"{PROV_RUNTIME} were observed; everything else remains declared."
    )
    return report


# --------------------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------------------


def _render_scenario_html(report: ScenarioReport, *, data_link: str) -> str:
    banners: list[str] = []
    if report.provenance == PROVENANCE_DECLARED_ONLY:
        banners.append(
            "DECLARED ONLY - nothing was executed. Every runtime quantity below is UNKNOWN "
            "with a reason; an unknown is not a passed check."
        )
    else:
        banners.append(
            "DECLARED PLUS A BOUNDED NON-LEARNING DIAGNOSTIC RUN - an untuned rule controller "
            "on one configuration, zero optimizer updates, no checkpoint. Not an algorithm "
            "result."
        )
    if report.dataset.get("is_real_activity_data") is False or any(
        "ANALYTIC FIXTURE" in note for note in report.notes
    ):
        banners.append(
            "THE DEMAND SOURCE IS NOT REAL ACTIVITY DATA - the numbers characterise a model, "
            "not a measured network"
        )
    if report.errors:
        banners.append("UNRESOLVED DEFECTS ARE LISTED IN THE ERRORS SECTION")

    declared_rows = []
    for item in report.declared_fields:
        declared_rows.append(
            [
                f"<td>{escape_cell(item.name)}</td>",
                measured_cell(item.effective),
                f"<td>{escape_cell(item.unit)}</td>",
                f"<td>{escape_cell(item.provenance)}</td>",
                f"<td>{escape_cell(item.note)}</td>",
            ]
        )
    runtime_rows = []
    for item in report.runtime:
        runtime_rows.append(
            [
                f"<td>{escape_cell(item.name)}</td>",
                measured_cell(item.value),
                measured_cell(item.declared),
                (
                    f"<td>{escape_cell(item.agreement)}</td>"
                    if item.agreement in ("match", "within_declared_bound", "no_declaration")
                    else f"<td class='absent'>{escape_cell(item.agreement)}</td>"
                ),
                f"<td>{escape_cell(item.provenance)}</td>",
            ]
        )
    radio_rows = []
    for model in report.radio_models:
        radio_rows.append(
            [
                f"<td>{escape_cell(model.get('link_class'))}</td>",
                measured_cell(model.get("frequency_hz")),
                measured_cell(model.get("bandwidth_hz")),
                measured_cell(model.get("tx_power_dbm")),
                measured_cell(model.get("path_loss_exponent")),
                measured_cell(model.get("min_snr_db")),
                measured_cell(model.get("max_range_m")),
                measured_cell(model.get("calibration_status")),
            ]
        )
    event_rows = []
    for event in report.failure_schedule.get("events", []):
        event_rows.append(
            [
                f"<td>{escape_cell(event.get('event_type'))}</td>",
                f"<td>{escape_cell(event.get('site_id') or event.get('site_index'))}</td>",
                f"<td>{escape_cell(event.get('start_s_range'))}</td>",
                f"<td>{escape_cell(event.get('duration_s_range'))}</td>",
                measured_cell(event.get("realised_time_s")),
                f"<td>{escape_cell(event.get('never_repaired_within_episode'))}</td>",
            ]
        )

    def kv(payload: Mapping[str, Any]) -> str:
        rows = []
        for key, value in payload.items():
            rendered = (
                json.dumps(value, default=str)[:600]
                if isinstance(value, (Mapping, list, tuple))
                else value
            )
            rows.append([f"<td>{escape_cell(key)}</td>", f"<td>{escape_cell(rendered)}</td>"])
        return html_table(["key", "value"], rows)

    sections = [
        (
            "Scenario identity",
            kv(
                {
                    "configuration": report.config_path,
                    "configuration sha256": report.config_hash,
                    "route": report.route,
                    "preset": report.preset_name,
                    "provenance": report.provenance,
                }
            ),
        ),
        ("Declared configuration", html_table(
            ["field", "declared value", "unit", "provenance", "group"], declared_rows)),
        ("Entities", kv(report.entities)),
        (
            "Failure schedule",
            html_table(
                ["event", "site", "start range (s)", "duration range (s)", "realised time",
                 "never repaired"],
                event_rows,
            )
            + f'<p class="meta">{escape_cell(report.failure_schedule.get("schedule_semantics"))}</p>',
        ),
        (
            "Radio models",
            html_table(
                ["link class", "frequency", "bandwidth", "tx power", "path loss exp",
                 "min SNR", "max range", "calibration"],
                radio_rows,
            ),
        ),
        ("Calibration", kv(report.calibration)),
        ("Dataset", kv(report.dataset)),
        ("Episode list", kv(report.episodes_file)),
        ("Diagnostic set", kv(report.diagnostic_set)),
        (
            "Observed versus declared",
            html_table(
                ["quantity", "observed", "declared", "agreement", "provenance"], runtime_rows
            )
            + '<p class="meta">An UNKNOWN row means nothing established the value. It is not a '
            "pass, not a zero and not a default.</p>",
        ),
        ("Statistical units", kv(report.statistical_units)),
        ("Notes", bullet_list(report.notes, css_class="notes", empty="no note")),
        ("Warnings", bullet_list(report.warnings, css_class="notes", empty="no warning")),
        ("Errors", bullet_list(report.errors, css_class="errors", empty="no error")),
    ]
    return html_document(
        title=f"Scenario report: {report.preset_name or Path(report.config_path).stem}",
        subtitle=f"{report.provenance} - {SCENARIO_REPORT_SCHEMA}",
        banners=banners,
        sections=sections,
        data_link=data_link,
        footer=(
            "Generated by tools.research_support.scenario_report. Formal training fits: 0. No "
            "optimizer was constructed, no checkpoint was loaded and no gradient was taken; "
            "an executed diagnostic run is a forward-only rollout of an untuned rule in a "
            "child process."
        ),
    )


def write_scenario_report(report: ScenarioReport, output_dir: Path) -> Path:
    """Write ``scenario_report.json`` and ``scenario_report.html``; return the HTML path."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    payload = report.to_json()
    payload["report_content_hash"] = content_hash(payload)
    (directory / "scenario_report.json").write_text(
        dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    html_path = directory / "scenario_report.html"
    html_path.write_text(
        _render_scenario_html(report, data_link="scenario_report.json"), encoding="utf-8"
    )
    return html_path


def scenario_report(
    *,
    config_path: Path,
    dataset: Path | None,
    episodes_file: Path | None,
    output_dir: Path,
    execute: bool,
    controller: str = DEFAULT_CONTROLLER,
    episodes: int = DEFAULT_EPISODES,
    max_steps: int = DEFAULT_MAX_STEPS,
    interpreter: str | None = None,
) -> Path:
    """Report one scenario configuration and write it. Returns the HTML path.

    ``execute=False`` (the default) reads files only. ``execute=True`` announces its scope
    with ``optimizer_updates=0`` and then runs the bounded non-learning diagnostic set in a
    child process.
    """

    report = inspect_scenario(
        config_path=Path(config_path),
        dataset=None if dataset is None else Path(dataset),
        episodes_file=None if episodes_file is None else Path(episodes_file),
        execute=bool(execute),
        controller=controller,
        episodes=episodes,
        max_steps=max_steps,
        output_dir=Path(output_dir),
        interpreter=interpreter,
    )
    return write_scenario_report(report, Path(output_dir))


__all__ = [
    "DIAGNOSTIC_SET_ID",
    "NOT_EXECUTED_REASON",
    "PROVENANCE_DECLARED_ONLY",
    "PROVENANCE_WITH_RUNTIME",
    "SCENARIO_REPORT_SCHEMA",
    "DeclaredField",
    "RuntimeQuantity",
    "ScenarioReport",
    "inspect_scenario",
    "run_diagnostic_probe",
    "scenario_report",
    "write_scenario_report",
]
