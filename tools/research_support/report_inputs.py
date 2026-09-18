"""Turn a recorded scene trace into the chart inputs it can honestly support.

``cmd_report`` used to put a trace *path string* into the inputs mapping, which no chart
reads, so a report built from a real trace came out as fourteen missing panels. This module
closes that gap by materialising records from the trace - and, just as importantly, by
refusing to materialise the ones a scene trace cannot support.

What a scene trace is: one rollout of one episode of one world, with per-interval scene
frames. What it is not: an experiment. It contains no training replicate, no checkpoint
sweep, no recovery criterion and no cross-fit evidence, and this checkout has zero training
fits. So exactly four chart inputs are derivable from one trace -

* ``service_timeseries`` (C03) from the recorded interval quantities, with each record
  keeping its own interval bounds and the recorded events supplying C03's event times;
* ``link_frames`` (C05) from the per-frame link records, with activity, flow, isolated
  capacity, utilization and resource domain;
* ``ground_entities`` (C06) from one frame's ground markers, keeping offered and delivered
  as :class:`~tools.research_support.records.Measured` so "no traffic model" stays distinct
  from "unobserved" and from a measured zero;
* ``uav_frames`` (C07) from the per-frame UAV states.

- and every other registry key is deliberately absent with a stated reason, so the report
shows the named missing panel instead of a fabricated curve. Two traces of the *same*
recorded world can additionally populate ``world_differences`` (C14); two traces of
different worlds cannot, and the mismatch is recorded as a reason instead of being
differenced.

Times follow the rule that capture time must match the quantity displayed: scene geometry
uses ``geometry_time_s`` (the quadrature point the positions and link flows belong to),
while interval quantities are placed at their own recorded interval end and carry their
bounds. The one transformation applied anywhere here is an exact unit conversion of a
recorded per-interval amount (Mbit) into the rate (Mbps) the charts plot, using that
record's own recorded interval width; multiplying back by the same width returns the
recorded amount, and the conversion is named in every record's ``definition_id``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .capture.trace_store import TraceReadResult, TraceReader
from .records import (
    AggregationLevel,
    DecisionEvent,
    EntityId,
    EntityKind,
    GroundEntityState,
    LinkActivity,
    LinkRecord,
    Measured,
    MetricRecord,
    Phase,
    ResourceDomainRecord,
    SceneCapability,
    SceneGeometry,
    UavState,
    Validity,
    XKind,
)

#: Chart inputs this adapter can derive from a single recorded scene trace.
SCENE_DERIVABLE: tuple[str, ...] = (
    "service_timeseries",
    "link_frames",
    "ground_entities",
    "uav_frames",
)

#: Every other registry input, with the reason a scene trace cannot supply it. A reason is
#: refined from the trace's own capability flags where they say something more specific.
_UNSUPPORTED_REASONS: dict[str, str] = {
    "evaluation_curve": (
        "a scene trace records one rollout, not an evaluation curve over checkpoints or "
        "training steps; no training replicate exists in this trace"
    ),
    "training_reward": (
        "no training process produced this trace; a rollout reward is not a training curve"
    ),
    "fit_endpoints": (
        "no independent training fit exists; a rule-controller or fixed-action rollout is "
        "not a fit and must not be drawn as one"
    ),
    "recovery_outcomes": (
        "the trace records no per-episode recovery outcome: no restoration criterion, "
        "deadline or censoring reason is declared in it, and inventing one here would "
        "decide the science from the plotting layer"
    ),
    "skill_segments": (
        "no skill assignment is recorded in this trace"
    ),
    "membership_intervals": (
        "no roster join or leave is recorded in this trace"
    ),
    "sweep_records": (
        "a robustness sweep is a set of runs across a predeclared factor; one trace is a "
        "single factor level and no study is launched to fill this panel"
    ),
    "cost_records": (
        "no measured wall time or training exposure is recorded in this trace"
    ),
    "training_diagnostics": (
        "no actor/critic loss, entropy, KL or clip fraction is recorded: this trace comes "
        "from a rollout, not from an optimiser, and nothing is recomputed here"
    ),
    "information_records": (
        "no observation-age or missingness time series is recorded; an observation view, "
        "where present, is a per-frame snapshot and is not converted into an age curve here"
    ),
    "world_differences": (
        "a shared-world comparison needs at least two traces of the same recorded world"
    ),
}


# --------------------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TraceProvenance:
    """Where a set of derived inputs came from, and whether the trace was complete.

    ``status`` is carried verbatim from :class:`TraceReadResult`; an incomplete or
    budget-exhausted trace is reported as such in the report rather than being silently
    treated as a finished episode.
    """

    directory: str
    trace_id: str
    status: str
    complete: bool
    n_frames: int
    problems: tuple[str, ...]
    truncated_after_sequence: int | None
    run_id: str | None = None
    episode_id: str | None = None
    world_id: str | None = None
    lane_id: int | None = None
    route: str | None = None
    environment_id: str | None = None
    source_kind: str | None = None
    policy_kind: str | None = None
    controller: str | None = None
    controller_kind: str | None = None
    information_condition: str | None = None
    seed: int | None = None
    dataset_hash: str | None = None
    checkpoint_identity: str | None = None
    first_time_s: float | None = None
    last_time_s: float | None = None
    manifest: Mapping[str, Any] = field(default_factory=dict)

    @property
    def method_id(self) -> str:
        return str(self.controller or self.policy_kind or self.run_id or self.trace_id)

    def to_json(self) -> dict[str, Any]:
        return {
            "directory": self.directory,
            "trace_id": self.trace_id,
            "status": self.status,
            "complete": bool(self.complete),
            "n_frames": int(self.n_frames),
            "problems": list(self.problems),
            "truncated_after_sequence": self.truncated_after_sequence,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "world_id": self.world_id,
            "lane_id": self.lane_id,
            "route": self.route,
            "environment_id": self.environment_id,
            "source_kind": self.source_kind,
            "policy_kind": self.policy_kind,
            "controller": self.controller,
            "controller_kind": self.controller_kind,
            "information_condition": self.information_condition,
            "seed": self.seed,
            "dataset_hash": self.dataset_hash,
            "checkpoint_identity": self.checkpoint_identity,
            "first_time_s": self.first_time_s,
            "last_time_s": self.last_time_s,
            "method_id": self.method_id,
            "manifest": dict(self.manifest),
        }


def read_trace(trace_dir: Path | str) -> TraceReadResult:
    """Read a trace directory, tolerating an interrupted producer."""

    return TraceReader(Path(trace_dir)).read()


def trace_provenance(result: TraceReadResult, trace_dir: Path | str) -> TraceProvenance:
    first = result.frames[0] if result.frames else {}
    identity = dict(first.get("identity") or {})
    provenance = dict(first.get("provenance") or {})
    manifest = dict(result.manifest or {})
    return TraceProvenance(
        directory=str(Path(trace_dir)),
        trace_id=result.trace_id,
        status=result.status,
        complete=result.complete,
        n_frames=len(result.frames),
        problems=tuple(result.problems),
        truncated_after_sequence=result.truncated_after_sequence,
        run_id=identity.get("run_id"),
        episode_id=identity.get("episode_id"),
        world_id=identity.get("world_id"),
        lane_id=identity.get("lane_id"),
        route=provenance.get("route") or manifest.get("route"),
        environment_id=provenance.get("environment_id") or manifest.get("environment_id"),
        source_kind=provenance.get("source_kind") or manifest.get("source_kind"),
        policy_kind=provenance.get("policy_kind"),
        controller=manifest.get("controller"),
        controller_kind=manifest.get("controller_kind"),
        information_condition=provenance.get("information_condition"),
        seed=manifest.get("seed"),
        dataset_hash=provenance.get("dataset_hash") or manifest.get("dataset_hash"),
        checkpoint_identity=provenance.get("checkpoint_identity"),
        first_time_s=result.index.first_time_s,
        last_time_s=result.index.last_time_s,
        manifest=manifest,
    )


# --------------------------------------------------------------------------------------
# Payload to record helpers
# --------------------------------------------------------------------------------------


def _measured(payload: Any) -> Measured | None:
    """Rebuild a :class:`Measured` without ever turning an absent value into a number."""

    if payload is None:
        return None
    if isinstance(payload, Measured):
        return payload
    if not isinstance(payload, Mapping):
        return Measured.from_float(payload)
    try:
        validity = Validity(str(payload.get("validity", "ok")))
    except ValueError:
        validity = Validity.INVALID
    unit = payload.get("unit")
    source = payload.get("source")
    value = payload.get("value")
    if validity is Validity.OK:
        if value is None:
            return Measured.invalid("ok_status_without_value", unit=unit, source=source)
        return Measured.ok(value, unit=unit, source=source)
    return Measured.absent(
        validity, str(payload.get("reason") or "unspecified"), unit=unit, source=source
    )


def _entity_id(payload: Any) -> EntityId:
    if isinstance(payload, EntityId):
        return payload
    if isinstance(payload, str):
        return EntityId.parse(payload)
    data = dict(payload or {})
    try:
        kind = EntityKind(str(data.get("kind", "uav")))
    except ValueError:  # an unknown kind must not silently become a UAV
        return EntityId.parse(str(data.get("key", "uav:0:0")))
    return EntityId(
        kind=kind,
        slot=int(data.get("slot", 0)),
        generation=int(data.get("generation", 0)),
        label=data.get("label"),
    )


def _position(payload: Any) -> tuple[float, float, float]:
    values = [float(v) for v in (payload or (0.0, 0.0, 0.0))]
    while len(values) < 3:
        values.append(0.0)
    return (values[0], values[1], values[2])


def _vector(payload: Any) -> tuple[float, float, float] | None:
    if payload is None:
        return None
    return _position(payload)


def _ground_entity(payload: Mapping[str, Any]) -> GroundEntityState:
    return GroundEntityState(
        entity=_entity_id(payload.get("entity")),
        position_m=_position(payload.get("position_m")),
        active=bool(payload.get("active", True)),
        offered_mbps=_measured(payload.get("offered_mbps")),
        delivered_mbps=_measured(payload.get("delivered_mbps")),
        observed=bool(payload.get("observed", True)),
        age_s=_measured(payload.get("age_s")),
        service_status=payload.get("service_status"),
        associated_to=payload.get("associated_to"),
        sinr_db=_measured(payload.get("sinr_db")),
        represents_count=int(payload.get("represents_count", 1) or 1),
    )


def _link_record(payload: Mapping[str, Any]) -> LinkRecord:
    try:
        activity = LinkActivity(str(payload.get("activity", "unknown")))
    except ValueError:
        activity = LinkActivity.UNKNOWN
    return LinkRecord(
        link_key=str(payload.get("link_key", "")),
        source=_entity_id(payload.get("source")),
        target=_entity_id(payload.get("target")),
        link_class=str(payload.get("link_class", "")),
        activity=activity,
        capacity_mbps=_measured(payload.get("capacity_mbps")),
        flow_mbps=_measured(payload.get("flow_mbps")),
        utilization=_measured(payload.get("utilization")),
        resource_domain=payload.get("resource_domain"),
        snr_db=_measured(payload.get("snr_db")),
        distance_m=_measured(payload.get("distance_m")),
        producer_local_id=payload.get("producer_local_id"),
    )


def _resource_domain(payload: Mapping[str, Any]) -> ResourceDomainRecord:
    return ResourceDomainRecord(
        domain_id=str(payload.get("domain_id", "")),
        description=str(payload.get("description", "")),
        link_keys=tuple(str(k) for k in payload.get("link_keys", ()) or ()),
        utilization=_measured(payload.get("utilization")),
    )


def _uav_state(payload: Mapping[str, Any]) -> UavState:
    return UavState(
        entity=_entity_id(payload.get("entity")),
        position_m=_position(payload.get("position_m")),
        active=bool(payload.get("active", True)),
        executed_velocity_mps=_vector(payload.get("executed_velocity_mps")),
        requested_velocity_mps=_vector(payload.get("requested_velocity_mps")),
        team_skill_id=payload.get("team_skill_id"),
        individual_skill_id=payload.get("individual_skill_id"),
        skill_age_s=_measured(payload.get("skill_age_s")),
        energy=_measured(payload.get("energy")),
    )


def _decision_event(payload: Mapping[str, Any]) -> DecisionEvent:
    individual = payload.get("individual_skill_ids")
    return DecisionEvent(
        time_s=float(payload.get("time_s", 0.0)),
        event_type=str(payload.get("event_type", "event")),
        description=str(payload.get("description", "")),
        entity=payload.get("entity"),
        team_skill_id=payload.get("team_skill_id"),
        individual_skill_ids=None if individual is None else tuple(int(v) for v in individual),
        renew=payload.get("renew"),
        availability=str(payload.get("availability", "recorded")),
    )


def _scene_geometry(payload: Mapping[str, Any] | None) -> SceneGeometry | None:
    if not payload:
        return None
    bounds = [float(v) for v in payload.get("bounds_m", ()) or ()]
    if len(bounds) != 4:
        return None
    return SceneGeometry(
        bounds_m=(bounds[0], bounds[1], bounds[2], bounds[3]),
        altitude_convention=str(payload.get("altitude_convention", "metres_above_ground")),
        crs=str(payload.get("crs", "local_metric_enu")),
        origin_description=str(payload.get("origin_description", "")),
        vertical_exaggeration=float(payload.get("vertical_exaggeration", 1.0) or 1.0),
    )


def _capability(frames: Sequence[Mapping[str, Any]]) -> SceneCapability:
    for frame in frames:
        payload = frame.get("capability")
        if isinstance(payload, Mapping):
            return SceneCapability.from_json(payload)
    return SceneCapability()


# --------------------------------------------------------------------------------------
# Interval quantities
# --------------------------------------------------------------------------------------

#: Substrings that identify the offered/delivered/unmet service triple in a route's own
#: interval-metric names. Anything else in ``interval_metrics`` (reward terms, counters,
#: flags) is deliberately left out of the service series, because plotting a reward and a
#: rate on one axis is how a chart starts lying about units.
_SERVICE_TOKENS: tuple[str, ...] = ("offered", "delivered", "unmet")


def _interval_bounds(metrics: Mapping[str, Any], clock: Mapping[str, Any]) -> tuple[float | None, float | None, str]:
    """Recorded interval the amount belongs to, and where the bound came from.

    The reward interval and the geometry substep are different windows: in the service
    restoration trace the clock's measurement window is a one-second quadrature substep
    while the reward interval is the ten-second decision interval. Dividing an interval
    amount by the wrong one would inflate the rate tenfold, so the interval metrics' own
    bounds win.
    """

    start = _measured(metrics.get("interval_start_s"))
    end = _measured(metrics.get("interval_end_s"))
    if start is not None and end is not None and start.validity is Validity.OK and end.validity is Validity.OK:
        return float(start.value), float(end.value), "interval_metrics.interval_start_s/interval_end_s"
    reference = _measured(metrics.get("reference_dt_s"))
    if reference is not None and reference.validity is Validity.OK:
        end_time = clock.get("simulation_time_s")
        if end_time is not None:
            width = float(reference.value)
            return float(end_time) - width, float(end_time), "interval_metrics.reference_dt_s"
    start_s = clock.get("measurement_start_s")
    end_s = clock.get("measurement_end_s")
    if start_s is not None and end_s is not None:
        return float(start_s), float(end_s), "clock.measurement_start_s/measurement_end_s"
    return None, None, "not recorded"


def _rate_name(name: str) -> str:
    """Name of the rate derived from a recorded per-interval amount."""

    base = name
    for suffix in ("_mbit_interval", "_mbit", "_interval"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    return f"{base}_mbps"


def _service_records(
    frames: Sequence[Mapping[str, Any]],
    provenance: TraceProvenance,
    *,
    source_path: str,
) -> tuple[list[MetricRecord], list[str]]:
    """Offered, delivered and unmet service as rate records with their interval bounds."""

    rows: list[MetricRecord] = []
    notes: list[str] = []
    converted = 0
    skipped_no_width = 0
    for frame in frames:
        metrics = frame.get("interval_metrics") or {}
        if not isinstance(metrics, Mapping) or not metrics:
            continue
        clock = dict(frame.get("clock") or {})
        identity = dict(frame.get("identity") or {})
        start_s, end_s, bound_source = _interval_bounds(metrics, clock)
        width = None if start_s is None or end_s is None else float(end_s) - float(start_s)
        for name, payload in metrics.items():
            lowered = str(name).lower()
            if not any(token in lowered for token in _SERVICE_TOKENS):
                continue
            measured = _measured(payload)
            if measured is None:
                continue
            unit = (measured.unit or "").lower()
            if unit in ("mbps", "mbit/s", "mbit_per_s"):
                value = measured
                metric_name = str(name)
                definition_id = f"recorded:{name} (rate as recorded)"
            elif unit in ("mbit", "mb", "megabit"):
                metric_name = _rate_name(str(name))
                definition_id = (
                    f"derived:{name} [Mbit] divided by its own recorded interval width "
                    f"[s] from {bound_source}; multiplying the plotted rate by the same "
                    "width returns the recorded amount exactly"
                )
                if measured.validity is not Validity.OK:
                    value = measured
                elif width is None or width <= 0.0:
                    skipped_no_width += 1
                    value = Measured.invalid(
                        "recorded interval width is absent or non-positive; the recorded "
                        "amount cannot be expressed as a rate",
                        unit="Mbps",
                    )
                else:
                    value = Measured.ok(float(measured.value) / width, unit="Mbps")
                    converted += 1
            else:
                # An unrecognised unit is carried through untouched rather than guessed at.
                value = measured
                metric_name = str(name)
                definition_id = f"recorded:{name} (unit {measured.unit or 'not recorded'})"
            rows.append(
                MetricRecord(
                    run_id=str(provenance.run_id or provenance.trace_id),
                    method_id=provenance.method_id,
                    metric_name=metric_name,
                    value=value,
                    x_kind=XKind.SIMULATED_SECOND,
                    x_value=end_s if end_s is not None else clock.get("simulation_time_s"),
                    phase=_phase_for(provenance),
                    aggregation_level=AggregationLevel.SUBINTERVAL,
                    world_id=identity.get("world_id"),
                    episode_id=identity.get("episode_id"),
                    lane_id=identity.get("lane_id"),
                    unit=value.unit,
                    definition_id=definition_id,
                    interval_start_s=start_s,
                    interval_end_s=end_s,
                    source_path=source_path,
                    source_row_or_key=f"sequence={identity.get('sequence')}:{name}",
                )
            )
    if converted:
        notes.append(
            f"{converted} recorded per-interval amounts were expressed as rates by dividing "
            "by each record's own recorded interval width; the conversion is exact and is "
            "named in every record's definition_id"
        )
    if skipped_no_width:
        notes.append(
            f"{skipped_no_width} interval amount(s) carry no usable interval width and are "
            "marked invalid rather than plotted"
        )
    return rows, notes


def _phase_for(provenance: TraceProvenance) -> Phase:
    """A rollout is a diagnostic rollout, not an evaluation of a trained policy."""

    source_kind = str(provenance.source_kind or "")
    policy_kind = str(provenance.policy_kind or "")
    if source_kind == "synthetic_fixture":
        return Phase.SYNTHETIC_FIXTURE
    if source_kind == "instrumented_training":
        return Phase.TRAINING
    if source_kind == "checkpoint_evaluation":
        return (
            Phase.UNTRAINED_DEMO
            if policy_kind == "untrained_checkpoint"
            else Phase.EVALUATION
        )
    return Phase.DIAGNOSTIC_ROLLOUT


def _episode_totals(
    frames: Sequence[Mapping[str, Any]],
    provenance: TraceProvenance,
    *,
    source_path: str,
) -> list[MetricRecord]:
    """Episode totals of the recorded interval amounts, one row per world and method.

    Summing a route's own recorded per-interval amounts over the episode is an integral of
    recorded numbers, not a model: the unit is unchanged and every contributing row is in
    the trace. A row is produced only when every contributing interval was valid, so a
    partial episode cannot masquerade as a complete total.
    """

    totals: dict[str, dict[str, Any]] = {}
    for frame in frames:
        metrics = frame.get("interval_metrics") or {}
        if not isinstance(metrics, Mapping):
            continue
        for name, payload in metrics.items():
            lowered = str(name).lower()
            if not any(token in lowered for token in _SERVICE_TOKENS):
                continue
            measured = _measured(payload)
            if measured is None:
                continue
            unit = (measured.unit or "").lower()
            if unit not in ("mbit", "mb", "megabit"):
                continue
            entry = totals.setdefault(str(name), {"total": 0.0, "n": 0, "invalid": 0, "unit": measured.unit})
            if measured.validity is Validity.OK:
                entry["total"] += float(measured.value)
                entry["n"] += 1
            else:
                entry["invalid"] += 1
    identity = dict((frames[-1] if frames else {}).get("identity") or {})
    rows: list[MetricRecord] = []
    for name, entry in sorted(totals.items()):
        metric_name = f"{_rate_name(name)[:-5]}_mbit_episode_total"
        if entry["invalid"] or not entry["n"]:
            value: Measured = Measured.invalid(
                f"{entry['invalid']} of {entry['invalid'] + entry['n']} recorded intervals "
                "are not usable; no episode total is reported",
                unit=entry["unit"],
            )
        else:
            value = Measured.ok(entry["total"], unit=entry["unit"])
        rows.append(
            MetricRecord(
                run_id=str(provenance.run_id or provenance.trace_id),
                method_id=provenance.method_id,
                metric_name=metric_name,
                value=value,
                x_kind=XKind.NONE,
                x_value=None,
                phase=_phase_for(provenance),
                aggregation_level=AggregationLevel.WORLD,
                world_id=identity.get("world_id"),
                episode_id=identity.get("episode_id"),
                lane_id=identity.get("lane_id"),
                unit=entry["unit"],
                definition_id=(
                    f"derived:sum of the recorded {name} over the {entry['n']} recorded "
                    "intervals of this episode; unit unchanged"
                ),
                source_path=source_path,
                source_row_or_key=f"episode_total:{name}",
            )
        )
    return rows


# --------------------------------------------------------------------------------------
# Scene sections
# --------------------------------------------------------------------------------------


def _link_frames(frames: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    """Per-frame links and resource domains at the geometry time they belong to.

    The second return value says whether any link carried a value C05 can actually draw. A
    route that records link topology but no flow or utilization returns ``False``, and the
    caller then leaves ``link_frames`` absent instead of shipping an empty panel.
    """

    out: list[dict[str, Any]] = []
    drawable = False
    for frame in frames:
        links = [
            _link_record(payload)
            for payload in frame.get("links") or ()
            if isinstance(payload, Mapping)
        ]
        domains = [
            _resource_domain(payload)
            for payload in frame.get("resource_domains") or ()
            if isinstance(payload, Mapping)
        ]
        if not links and not domains:
            continue
        clock = dict(frame.get("clock") or {})
        time_s = clock.get("geometry_time_s")
        if time_s is None:
            time_s = clock.get("simulation_time_s", 0.0)
        out.append({"time_s": float(time_s), "links": links, "resource_domains": domains})
        for link in links:
            if (link.utilization is not None and link.utilization.validity is Validity.OK) or (
                link.flow_mbps is not None and link.flow_mbps.validity is Validity.OK
            ):
                drawable = True
        for domain in domains:
            if domain.utilization is not None and domain.utilization.validity is Validity.OK:
                drawable = True
    return out, drawable


def _uav_frames(frames: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for frame in frames:
        uavs = [
            _uav_state(payload)
            for payload in frame.get("uavs") or ()
            if isinstance(payload, Mapping)
        ]
        if not uavs:
            continue
        clock = dict(frame.get("clock") or {})
        time_s = clock.get("geometry_time_s")
        if time_s is None:
            time_s = clock.get("simulation_time_s", 0.0)
        out.append({"time_s": float(time_s), "uavs": uavs})
    return out


def _select_ground_frame(
    frames: Sequence[Mapping[str, Any]], selector: str
) -> Mapping[str, Any] | None:
    """Pick the frame the spatial map shows, by a rule that does not look at outcomes.

    ``last`` and ``first`` are fixed positions in the recording. A "worst frame" rule is
    deliberately not offered: choosing the frame by its own value is selection after the
    fact, and the map would then over-state how bad the episode was.
    """

    candidates = [frame for frame in frames if frame.get("ground_entities")]
    if not candidates:
        return None
    if selector == "first":
        return candidates[0]
    if selector.startswith("sequence="):
        wanted = selector.split("=", 1)[1]
        for frame in candidates:
            if str((frame.get("identity") or {}).get("sequence")) == wanted:
                return frame
        return None
    return candidates[-1]


def _world_events(frames: Sequence[Mapping[str, Any]]) -> list[DecisionEvent]:
    """Distinct recorded events, keyed by their own recorded time.

    A producer that restates a standing condition in every frame - the service restoration
    trace repeats its ``full_site_failure`` in all 49 frames after the failure - must not
    become 49 vertical lines at 49 different times. Identity is the event's own recorded
    ``time_s`` plus type, entity and description, so the marker lands where the event
    actually happened.
    """

    seen: dict[tuple[Any, ...], DecisionEvent] = {}
    for frame in frames:
        for payload in frame.get("events") or ():
            if not isinstance(payload, Mapping):
                continue
            event = _decision_event(payload)
            key = (event.time_s, event.event_type, event.entity, event.description)
            seen.setdefault(key, event)
    return [seen[key] for key in sorted(seen, key=lambda item: (float(item[0]), str(item[1])))]


# --------------------------------------------------------------------------------------
# Public adapter
# --------------------------------------------------------------------------------------


def _unsupported_reasons(capability: SceneCapability, derived: Iterable[str]) -> dict[str, str]:
    reasons = dict(_UNSUPPORTED_REASONS)
    if not capability.has_skill_labels:
        reasons["skill_segments"] = (
            "this environment records no skill labels (capability.has_skill_labels is "
            "false); no skill sequence is invented for a controller that has none"
        )
    if not capability.has_roster_changes:
        reasons["membership_intervals"] = (
            "this environment records no roster change (capability.has_roster_changes is "
            "false); membership cannot be reconstructed from array slots"
        )
    if capability.has_observation_view:
        reasons["information_records"] = (
            "an observation view is recorded per frame, but no observation-age or "
            "missingness time series is; deriving one is a separate reader, not a plotting "
            "step, so this panel stays empty"
        )
    for key in derived:
        reasons.pop(key, None)
    return reasons


def inputs_from_trace(
    trace_dir: Path | str,
    *,
    ground_frame_selector: str = "last",
) -> dict[str, Any]:
    """Materialise the chart inputs one recorded scene trace can honestly support.

    The returned mapping is ready for :class:`~tools.research_support.reports.ReportRequest`.
    Alongside the chart inputs it carries the trace's provenance and read status, the list
    of keys actually derived, and the reason every other registry key is absent, so the
    report can state what it was built from and the operator can see what was refused.
    """

    directory = Path(trace_dir)
    result = read_trace(directory)
    provenance = trace_provenance(result, directory)
    source_path = str(directory)
    frames = result.frames
    notes: list[str] = []
    inputs: dict[str, Any] = {}
    # A scene-derivable key that this particular route does not carry gets its own reason,
    # so "this trace has no traffic model" never reads the same as "nobody implemented it".
    scene_absent: dict[str, str] = {}

    if not frames:
        notes.append(
            f"no readable frame in {source_path}: the trace reports status {result.status}"
        )

    service_rows, service_notes = _service_records(frames, provenance, source_path=source_path)
    notes.extend(service_notes)
    if service_rows:
        inputs["service_timeseries"] = service_rows
        unmet = [row for row in service_rows if "unmet" in row.metric_name.lower()]
        if unmet:
            inputs["unmet_traffic"] = unmet
    else:
        scene_absent["service_timeseries"] = (
            "this route records no offered, delivered or unmet service quantity in its "
            "interval metrics"
            + (
                "; the environment models no traffic demand"
                if not _capability(frames).has_demand_rates
                else ""
            )
        )

    events = _world_events(frames)
    if events:
        inputs["world_events"] = events
        notes.append(
            f"{len(events)} distinct recorded event(s) at their own recorded times; a "
            "standing condition repeated in later frames is one event, not many"
        )

    link_frames, link_drawable = _link_frames(frames)
    if link_frames and link_drawable:
        inputs["link_frames"] = link_frames
    elif link_frames:
        scene_absent["link_frames"] = (
            "link records exist but carry no recorded flow or utilization, so there is no "
            "capacity or contention quantity to draw; an empty panel would suggest the "
            "measurement was taken and came out flat"
        )
        notes.append(scene_absent["link_frames"])
    else:
        scene_absent["link_frames"] = "no link record is present in this trace"

    ground_frame = _select_ground_frame(frames, ground_frame_selector)
    if ground_frame is None:
        scene_absent["ground_entities"] = "no recorded frame carries a ground marker"
    if ground_frame is not None:
        entities = [
            _ground_entity(payload)
            for payload in ground_frame.get("ground_entities") or ()
            if isinstance(payload, Mapping)
        ]
        if not entities:
            scene_absent["ground_entities"] = "the selected frame carries no ground marker"
        if entities:
            inputs["ground_entities"] = entities
            geometry = _scene_geometry(ground_frame.get("geometry"))
            if geometry is not None:
                inputs["geometry"] = geometry
            identity = dict(ground_frame.get("identity") or {})
            clock = dict(ground_frame.get("clock") or {})
            frame_rule = (
                f"{ground_frame_selector} recorded frame carrying ground markers "
                f"(sequence {identity.get('sequence')}, geometry time "
                f"{clock.get('geometry_time_s')} s); the frame is chosen by position in the "
                "recording, never by its own values"
            )
            notes.append(f"spatial map frame: {frame_rule}")
            inputs.setdefault("chart_options_by_id", {}).setdefault("C06", {})[
                "checkpoint_rule"
            ] = frame_rule

    uav_frames = _uav_frames(frames)
    if uav_frames:
        inputs["uav_frames"] = uav_frames
    else:
        scene_absent["uav_frames"] = "no recorded frame carries a UAV state"

    for key in ("scene_source_path", "link_source_path", "uav_source_path"):
        inputs[key] = source_path

    capability = _capability(frames)
    derived = [key for key in SCENE_DERIVABLE if key in inputs]
    inputs["source_kind"] = provenance.source_kind
    inputs["trace_provenance"] = [provenance.to_json()]
    inputs["derived_inputs"] = derived
    inputs["absent_inputs"] = {**_unsupported_reasons(capability, derived), **scene_absent}
    inputs["read_status"] = {provenance.trace_id: provenance.status}
    inputs["episode_totals"] = _episode_totals(frames, provenance, source_path=source_path)
    if not provenance.complete:
        notes.append(
            f"trace {provenance.trace_id} is not a cleanly closed recording: status "
            f"{provenance.status}"
            + (f"; {len(provenance.problems)} read problem(s)" if provenance.problems else "")
            + ". Every panel below is drawn from a partial episode."
        )
    inputs["notes"] = notes
    return inputs


def inputs_from_traces(
    trace_dirs: Sequence[Path | str],
    *,
    ground_frame_selector: str = "last",
) -> dict[str, Any]:
    """Derive inputs from one or more traces, adding a shared-world comparison when earned.

    The scene panels come from the first trace, because C03, C05, C06 and C07 each describe
    one episode of one world and splicing two episodes into one panel would be a fabricated
    rollout. Additional traces contribute only the shared-world difference, and only when
    the recorded world identities actually match.
    """

    paths = [Path(p) for p in trace_dirs]
    if not paths:
        return {
            "derived_inputs": [],
            "absent_inputs": dict(_UNSUPPORTED_REASONS),
            "trace_provenance": [],
            "notes": ["no trace supplied"],
        }

    primary = inputs_from_trace(paths[0], ground_frame_selector=ground_frame_selector)
    if len(paths) == 1:
        return primary

    notes: list[str] = list(primary.get("notes") or ())
    provenances: list[dict[str, Any]] = list(primary.get("trace_provenance") or ())
    read_status: dict[str, Any] = dict(primary.get("read_status") or {})
    totals: list[MetricRecord] = list(primary.get("episode_totals") or ())
    method_ids = [str(provenances[0].get("method_id"))] if provenances else []
    world_ids = [provenances[0].get("world_id")] if provenances else []
    environments = [provenances[0].get("environment_id")] if provenances else []

    for extra in paths[1:]:
        derived = inputs_from_trace(extra, ground_frame_selector=ground_frame_selector)
        extra_provenance = list(derived.get("trace_provenance") or ())
        provenances.extend(extra_provenance)
        read_status.update(dict(derived.get("read_status") or {}))
        totals.extend(list(derived.get("episode_totals") or ()))
        notes.extend(str(note) for note in derived.get("notes") or ())
        if extra_provenance:
            method_ids.append(str(extra_provenance[0].get("method_id")))
            world_ids.append(extra_provenance[0].get("world_id"))
            environments.append(extra_provenance[0].get("environment_id"))

    merged = dict(primary)
    merged["trace_provenance"] = provenances
    merged["read_status"] = read_status
    merged["episode_totals"] = totals
    notes.append(
        "scene panels come from the first trace; the other traces contribute only the "
        "shared-world comparison"
    )

    absent = dict(merged.get("absent_inputs") or {})
    distinct_worlds = {str(world) for world in world_ids}
    distinct_environments = {str(env) for env in environments}
    distinct_methods = {method for method in method_ids}
    usable_totals = [row for row in totals if row.value.validity is Validity.OK]

    if len(distinct_environments) > 1:
        absent["world_differences"] = (
            "the traces come from different environments ("
            + ", ".join(sorted(distinct_environments))
            + "); their metrics are not comparable and no difference is computed"
        )
    elif len(distinct_worlds) > 1:
        absent["world_differences"] = (
            "the recorded world identities differ, so these are not the same exogenous "
            "world: " + " | ".join(sorted(distinct_worlds))
        )
    elif len(distinct_methods) < 2:
        absent["world_differences"] = (
            "the traces report the same method identity ("
            + ", ".join(sorted(distinct_methods))
            + "); a difference needs two distinguishable arms"
        )
    elif not usable_totals:
        absent["world_differences"] = (
            "no usable episode total is recorded in these traces, so there is nothing to "
            "difference"
        )
    else:
        merged["world_differences"] = totals
        merged["method_a"] = method_ids[0]
        merged["method_b"] = method_ids[1]
        # The two arms ran on the same identified exogenous world, which is the pairing
        # evidence the statistics module recognises; it is not a matching seed number.
        merged["pairing_evidence"] = "verified_world_identity"
        metric_names = sorted({row.metric_name for row in usable_totals})
        preferred = next(
            (name for name in metric_names if "delivered" in name), metric_names[0]
        )
        options = dict(merged.get("chart_options_by_id") or {})
        c14 = dict(options.get("C14") or {})
        c14["metric_name"] = preferred
        c14["statistical_unit"] = (
            "one shared recorded world (a single matched block; not a cross-fit summary)"
        )
        options["C14"] = c14
        merged["chart_options_by_id"] = options
        absent.pop("world_differences", None)
        notes.append(
            f"shared-world comparison on world identity {world_ids[0]!r} between "
            f"{method_ids[0]} and {method_ids[1]}; one matched world, so the interval is "
            "reported by the statistics module or declared unavailable"
        )

    merged["absent_inputs"] = absent
    merged["derived_inputs"] = [
        key
        for key in (*SCENE_DERIVABLE, "world_differences")
        if key in merged and merged.get(key)
    ]
    merged["notes"] = notes
    return merged


__all__ = [
    "SCENE_DERIVABLE",
    "TraceProvenance",
    "inputs_from_trace",
    "inputs_from_traces",
    "read_trace",
    "trace_provenance",
]
