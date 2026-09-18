"""Versioned derived records for the research support suite.

This module is the single definition of the data the suite moves between a producer
(a running environment), a store (trace files) and a consumer (viewer, report, reader).
It has three jobs:

1. Keep *missing*, *unsupported*, *invalid* and a measured numeric zero distinct.
   ``0.0`` is a measurement; ``None`` with a :class:`Validity` reason is not.
2. Give every entity and link a **stable identity** that survives array reordering,
   masking, reset and roster change, so a departing UE cannot inherit the colour and
   history of a later arrival that reused its array slot.
3. Encode to JSON that a browser can parse: standard finite values only, with
   non-finite numbers carried as ``null`` plus an explicit validity mask.

Nothing here imports a renderer, a web server, a GUI toolkit, torch, or any
environment. It is safe to import inside a scientific process.
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

# --------------------------------------------------------------------------------------
# Schema versions
# --------------------------------------------------------------------------------------

#: Scene packet schema. Bump the minor number for an additive field, the major number
#: when a consumer that understands the old version would misread the new one.
SCENE_SCHEMA = "research_support.scene.1"

#: Long-form metric record schema (Section 4.2 of the plan).
METRIC_SCHEMA = "research_support.metric.1"

#: Run identity record schema (Section 4.1).
RUN_SCHEMA = "research_support.run.1"

#: Trace index schema written next to the chunk files.
TRACE_INDEX_SCHEMA = "research_support.trace_index.1"


# --------------------------------------------------------------------------------------
# Validity
# --------------------------------------------------------------------------------------


class Validity(str, Enum):
    """Why a value is or is not usable.

    ``OK`` is the only status whose value may be read as a measurement. Every other
    status means the number is absent, and a consumer must not substitute a default,
    a present-day configuration value, or zero.
    """

    OK = "ok"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"
    NOT_APPLICABLE = "not_applicable"
    MISSING_ARTIFACT = "missing_artifact"
    INVALID = "invalid"
    NOT_RECORDED = "not_recorded"

    @property
    def is_value(self) -> bool:
        return self is Validity.OK


@dataclass(frozen=True)
class Measured:
    """One scalar plus the evidence for trusting it.

    ``value`` is ``None`` unless ``validity`` is :attr:`Validity.OK`. A ``Measured`` with
    ``value=0.0`` and ``validity=OK`` is a measured zero and is never equal to a missing
    value, which is the distinction the whole suite depends on.
    """

    value: float | int | str | bool | None
    validity: Validity = Validity.OK
    unit: str | None = None
    source: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.validity is Validity.OK and self.value is None:
            raise ValueError("Measured(validity=OK) requires a value; use a reason instead")
        if self.validity is not Validity.OK and self.value is not None:
            raise ValueError(
                f"Measured(validity={self.validity.value}) must not carry a value; "
                "a non-OK status means the number is absent"
            )
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError(
                "Measured cannot hold a non-finite float; use "
                "Measured.invalid('non_finite') so the consumer sees why"
            )

    # Constructors ---------------------------------------------------------------------

    @classmethod
    def ok(
        cls,
        value: float | int | str | bool,
        *,
        unit: str | None = None,
        source: str | None = None,
    ) -> "Measured":
        return cls(value=value, validity=Validity.OK, unit=unit, source=source)

    @classmethod
    def absent(
        cls,
        validity: Validity,
        reason: str,
        *,
        unit: str | None = None,
        source: str | None = None,
    ) -> "Measured":
        if validity is Validity.OK:
            raise ValueError("Measured.absent requires a non-OK validity")
        return cls(value=None, validity=validity, unit=unit, source=source, reason=reason)

    @classmethod
    def unknown(cls, reason: str, **kwargs: Any) -> "Measured":
        return cls.absent(Validity.UNKNOWN, reason, **kwargs)

    @classmethod
    def unsupported(cls, reason: str, **kwargs: Any) -> "Measured":
        return cls.absent(Validity.UNSUPPORTED, reason, **kwargs)

    @classmethod
    def not_recorded(cls, reason: str, **kwargs: Any) -> "Measured":
        return cls.absent(Validity.NOT_RECORDED, reason, **kwargs)

    @classmethod
    def missing_artifact(cls, reason: str, **kwargs: Any) -> "Measured":
        return cls.absent(Validity.MISSING_ARTIFACT, reason, **kwargs)

    @classmethod
    def invalid(cls, reason: str, **kwargs: Any) -> "Measured":
        return cls.absent(Validity.INVALID, reason, **kwargs)

    @classmethod
    def not_applicable(cls, reason: str, **kwargs: Any) -> "Measured":
        return cls.absent(Validity.NOT_APPLICABLE, reason, **kwargs)

    @classmethod
    def from_float(
        cls,
        value: Any,
        *,
        unit: str | None = None,
        source: str | None = None,
        missing_reason: str = "absent_in_source",
    ) -> "Measured":
        """Coerce a possibly missing/non-finite source value without inventing a number."""

        if value is None:
            return cls.absent(Validity.UNKNOWN, missing_reason, unit=unit, source=source)
        try:
            number = float(value)
        except (TypeError, ValueError):
            return cls.absent(
                Validity.INVALID, f"not_numeric:{value!r}", unit=unit, source=source
            )
        if not math.isfinite(number):
            return cls.absent(Validity.INVALID, "non_finite", unit=unit, source=source)
        return cls(value=number, validity=Validity.OK, unit=unit, source=source)

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"value": self.value, "validity": self.validity.value}
        if self.unit is not None:
            payload["unit"] = self.unit
        if self.source is not None:
            payload["source"] = self.source
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


# --------------------------------------------------------------------------------------
# Stable identity
# --------------------------------------------------------------------------------------


class EntityKind(str, Enum):
    """What a ground marker actually is.

    ``AGGREGATE_DEMAND_POINT`` is a demand proxy for a source grid cell. It is not a
    person, a subscriber or a tracked device, and the UI must label it as an aggregate.
    """

    UAV = "uav"
    SITE = "site"
    CORE = "core"
    INDIVIDUAL_UE = "individual_ue"
    AGGREGATE_DEMAND_POINT = "aggregate_demand_point"
    SOURCE_GRID_CELL = "source_grid_cell"

    @property
    def is_aggregate(self) -> bool:
        return self in (EntityKind.AGGREGATE_DEMAND_POINT, EntityKind.SOURCE_GRID_CELL)


@dataclass(frozen=True, order=True)
class EntityId:
    """Identity of one simulated entity across frames.

    ``slot`` is the array index the producer happened to use. ``generation`` separates
    two lifetimes that reused the same slot: an entity that leaves at t=40 s and a
    different one that arrives at t=90 s in slot 3 get ``generation`` 0 and 1, so the
    viewer keeps their trails, colours and selection apart.
    """

    kind: EntityKind
    slot: int
    generation: int = 0
    label: str | None = None

    @property
    def key(self) -> str:
        return f"{self.kind.value}:{int(self.slot)}:{int(self.generation)}"

    def to_json(self) -> dict[str, Any]:
        payload = {
            "key": self.key,
            "kind": self.kind.value,
            "slot": int(self.slot),
            "generation": int(self.generation),
        }
        if self.label is not None:
            payload["label"] = self.label
        return payload

    @classmethod
    def parse(cls, key: str) -> "EntityId":
        kind, slot, generation = key.split(":")
        return cls(kind=EntityKind(kind), slot=int(slot), generation=int(generation))


def canonical_link_key(
    source: EntityId | tuple[str, int],
    target: EntityId | tuple[str, int],
    link_class: str,
    *,
    resource_domain: str | None = None,
) -> str:
    """Directed link identity derived from endpoints, not from a solver enumeration index.

    The service-restoration scheduler rebuilds its graph every substep, so integer
    ``link_id`` values are local to one solve: link 7 at t=10 s and link 7 at t=20 s can
    join unrelated nodes. Cross-frame comparison therefore uses endpoint identity plus
    link class, and the radio resource identity when one link class can appear on more
    than one resource.
    """

    def _part(value: EntityId | tuple[str, int]) -> str:
        if isinstance(value, EntityId):
            return f"{value.kind.value}:{int(value.slot)}:{int(value.generation)}"
        kind, index = value
        return f"{kind}:{int(index)}:0"

    key = f"{_part(source)}->{_part(target)}|{link_class}"
    if resource_domain:
        key = f"{key}@{resource_domain}"
    return key


class LifetimeRegistry:
    """Assigns generation numbers so a reused array slot is not a reused identity.

    The producer calls :meth:`observe` once per frame with the slots that are currently
    active. A slot that goes inactive and later becomes active again receives the next
    generation.
    """

    def __init__(self) -> None:
        self._generation: dict[tuple[str, int], int] = {}
        self._active: set[tuple[str, int]] = set()

    def observe(self, kind: EntityKind, active_slots: Iterable[int]) -> None:
        current = {(kind.value, int(slot)) for slot in active_slots}
        previous = {item for item in self._active if item[0] == kind.value}
        for item in current - previous:
            if item in self._generation:
                # Departed earlier and came back: a new lifetime in the same slot.
                self._generation[item] += 1
            else:
                self._generation[item] = 0
        self._active = (self._active - previous) | current

    def entity(self, kind: EntityKind, slot: int, label: str | None = None) -> EntityId:
        generation = self._generation.get((kind.value, int(slot)), 0)
        return EntityId(kind=kind, slot=int(slot), generation=generation, label=label)

    def generation(self, kind: EntityKind, slot: int) -> int:
        return self._generation.get((kind.value, int(slot)), 0)

    def snapshot(self) -> dict[str, Any]:
        return {
            "generation": {f"{k[0]}:{k[1]}": v for k, v in sorted(self._generation.items())},
            "active": sorted(f"{k[0]}:{k[1]}" for k in self._active),
        }


# --------------------------------------------------------------------------------------
# Provenance and capability
# --------------------------------------------------------------------------------------


class SourceKind(str, Enum):
    """Where a frame's numbers came from, which governs what may be claimed about them."""

    #: A real environment executed with a rule controller or fixed actions.
    RULE_CONTROLLER_ROLLOUT = "rule_controller_rollout"
    #: A real environment executed by a loaded policy checkpoint, forward-only.
    CHECKPOINT_EVALUATION = "checkpoint_evaluation"
    #: Captured from an instrumented training process.
    INSTRUMENTED_TRAINING = "instrumented_training"
    #: Constructed analytically by a test fixture generator. Never an algorithm result.
    SYNTHETIC_FIXTURE = "synthetic_fixture"
    #: Read back from a recorded trace.
    RECORDED_TRACE = "recorded_trace"


class PolicyKind(str, Enum):
    RULE_CONTROLLER = "rule_controller"
    FIXED_ACTION = "fixed_action"
    RANDOM = "random"
    TRAINED_CHECKPOINT = "trained_checkpoint"
    UNTRAINED_CHECKPOINT = "untrained_checkpoint"
    UNKNOWN = "unknown"


class FrameKind(str, Enum):
    INITIAL = "initial"
    TRANSITION = "transition"
    SUBSTEP = "substep"
    EVENT = "event"
    FINAL = "final"
    #: Recorded in place of a frame that the gates or the byte budget refused.
    GAP_MARKER = "gap_marker"


class StreamState(str, Enum):
    WAITING = "WAITING"
    LIVE = "LIVE"
    STALE = "STALE"
    DISCONNECTED = "DISCONNECTED"
    ENDED = "ENDED"
    INCOMPLETE_TRACE = "INCOMPLETE_TRACE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SceneCapability:
    """Which optional scene sections a route can actually fill.

    The UI activates a layer only when its flag is true. A legacy relay environment with
    no traffic demand model reports ``has_demand_rates=False``, and the viewer then shows
    association and SINR rather than inventing Mbps.
    """

    has_uav_positions: bool = False
    has_uav_velocity: bool = False
    has_requested_action: bool = False
    has_skill_labels: bool = False
    has_energy: bool = False
    has_individual_ues: bool = False
    has_aggregate_demand: bool = False
    has_demand_rates: bool = False
    has_delivered_rates: bool = False
    has_sites: bool = False
    has_links: bool = False
    has_link_flows: bool = False
    has_link_capacity: bool = False
    has_resource_domains: bool = False
    has_candidate_paths: bool = False
    has_sinr: bool = False
    has_association: bool = False
    has_observation_view: bool = False
    has_roster_changes: bool = False
    has_altitude: bool = False
    has_interval_metrics: bool = False
    notes: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            **{
                f.name: getattr(self, f.name)
                for f in dataclasses.fields(self)
                if f.name != "notes"
            },
            "notes": list(self.notes),
        }

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "SceneCapability":
        known = {f.name for f in dataclasses.fields(cls)} - {"notes"}
        kwargs = {name: bool(payload.get(name, False)) for name in known}
        return cls(**kwargs, notes=tuple(payload.get("notes", ())))


# --------------------------------------------------------------------------------------
# Scene frame
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SceneIdentity:
    run_id: str
    trace_id: str
    episode_id: str
    world_id: str
    lane_id: int
    sequence: int

    def to_json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "episode_id": self.episode_id,
            "world_id": self.world_id,
            "lane_id": int(self.lane_id),
            "sequence": int(self.sequence),
        }


@dataclass(frozen=True)
class SceneClock:
    """Every time a consumer might confuse.

    ``geometry_time_s`` is when the displayed positions held. ``measurement_start_s`` and
    ``measurement_end_s`` bound the interval a rate or an integral refers to; it is a real
    interval, not a point.

    The two are related by the quadrature rule and are not interchangeable. Under the
    midpoint rule the solve uses the geometry at the middle of its measurement window, so
    ``geometry_time_s == (measurement_start_s + measurement_end_s) / 2``; under a left rule
    it equals ``measurement_start_s``. In neither case is it the interval end, where the UAV
    will be next. Stamping midpoint geometry with the window start mislabels every position
    by up to ``max_speed * window / 2``.
    """

    simulation_time_s: float
    geometry_time_s: float
    decision_step: int
    capture_wall_time_utc: str
    producer_monotonic_s: float
    measurement_start_s: float | None = None
    measurement_end_s: float | None = None
    training_step: int | None = None
    substep_index: int | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "simulation_time_s": float(self.simulation_time_s),
            "geometry_time_s": float(self.geometry_time_s),
            "decision_step": int(self.decision_step),
            "capture_wall_time_utc": self.capture_wall_time_utc,
            "producer_monotonic_s": float(self.producer_monotonic_s),
            "measurement_start_s": _opt_float(self.measurement_start_s),
            "measurement_end_s": _opt_float(self.measurement_end_s),
            "training_step": None if self.training_step is None else int(self.training_step),
            "substep_index": None if self.substep_index is None else int(self.substep_index),
        }


@dataclass(frozen=True)
class SceneProvenance:
    route: str
    environment_id: str
    source_kind: SourceKind
    policy_kind: PolicyKind
    information_condition: str
    frame_kind: FrameKind
    capture_resolution: str
    dataset_hash: str | None = None
    checkpoint_identity: str | None = None
    is_real_activity_data: bool = False
    derived_fields: tuple[str, ...] = ()
    measured_fields: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "environment_id": self.environment_id,
            "source_kind": self.source_kind.value,
            "policy_kind": self.policy_kind.value,
            "information_condition": self.information_condition,
            "frame_kind": self.frame_kind.value,
            "capture_resolution": self.capture_resolution,
            "dataset_hash": self.dataset_hash,
            "checkpoint_identity": self.checkpoint_identity,
            "is_real_activity_data": bool(self.is_real_activity_data),
            "derived_fields": list(self.derived_fields),
            "measured_fields": list(self.measured_fields),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class SceneGeometry:
    """Spatial frame of reference. ``bounds_m`` is ``(min_x, min_y, max_x, max_y)``."""

    bounds_m: tuple[float, float, float, float]
    altitude_convention: str = "metres_above_ground"
    crs: str = "local_metric_enu"
    origin_description: str = "configured region minimum corner"
    vertical_exaggeration: float = 1.0

    def to_json(self) -> dict[str, Any]:
        return {
            "bounds_m": [float(v) for v in self.bounds_m],
            "altitude_convention": self.altitude_convention,
            "crs": self.crs,
            "origin_description": self.origin_description,
            "vertical_exaggeration": float(self.vertical_exaggeration),
        }


@dataclass(frozen=True)
class UavState:
    entity: EntityId
    position_m: tuple[float, float, float]
    active: bool = True
    executed_velocity_mps: tuple[float, float, float] | None = None
    requested_velocity_mps: tuple[float, float, float] | None = None
    team_skill_id: int | None = None
    individual_skill_id: int | None = None
    skill_age_s: Measured | None = None
    energy: Measured | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "entity": self.entity.to_json(),
            "position_m": [float(v) for v in self.position_m],
            "active": bool(self.active),
            "executed_velocity_mps": _opt_vec(self.executed_velocity_mps),
            "requested_velocity_mps": _opt_vec(self.requested_velocity_mps),
            "team_skill_id": _opt_int(self.team_skill_id),
            "individual_skill_id": _opt_int(self.individual_skill_id),
            "skill_age_s": None if self.skill_age_s is None else self.skill_age_s.to_json(),
            "energy": None if self.energy is None else self.energy.to_json(),
        }


@dataclass(frozen=True)
class GroundEntityState:
    """One UE or one aggregate demand point.

    ``offered_mbps`` and ``delivered_mbps`` are :class:`Measured`, so an environment
    without a traffic model reports ``NOT_APPLICABLE`` instead of zero, and an unobserved
    cell reports ``UNKNOWN`` instead of a served-with-no-demand marker.
    """

    entity: EntityId
    position_m: tuple[float, float, float]
    active: bool = True
    offered_mbps: Measured | None = None
    delivered_mbps: Measured | None = None
    observed: bool = True
    age_s: Measured | None = None
    service_status: str | None = None
    associated_to: str | None = None
    sinr_db: Measured | None = None
    represents_count: int = 1

    def to_json(self) -> dict[str, Any]:
        return {
            "entity": self.entity.to_json(),
            "position_m": [float(v) for v in self.position_m],
            "active": bool(self.active),
            "offered_mbps": _opt_measured(self.offered_mbps),
            "delivered_mbps": _opt_measured(self.delivered_mbps),
            "observed": bool(self.observed),
            "age_s": _opt_measured(self.age_s),
            "service_status": self.service_status,
            "associated_to": self.associated_to,
            "sinr_db": _opt_measured(self.sinr_db),
            "represents_count": int(self.represents_count),
        }


@dataclass(frozen=True)
class SiteStateRecord:
    entity: EntityId
    position_m: tuple[float, float, float]
    radio_up: bool | None = None
    core_link_up: bool | None = None
    access_capacity_scale: Measured | None = None
    backhaul_capacity_scale: Measured | None = None
    observed: bool = True
    age_s: Measured | None = None
    degraded: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            "entity": self.entity.to_json(),
            "position_m": [float(v) for v in self.position_m],
            "radio_up": self.radio_up,
            "core_link_up": self.core_link_up,
            "access_capacity_scale": _opt_measured(self.access_capacity_scale),
            "backhaul_capacity_scale": _opt_measured(self.backhaul_capacity_scale),
            "observed": bool(self.observed),
            "age_s": _opt_measured(self.age_s),
            "degraded": bool(self.degraded),
        }


class LinkActivity(str, Enum):
    """Whether a link merely exists or actually carries traffic.

    A geometrically feasible link with zero flow must not look like a successful service
    path, so these are separate UI toggles rather than one "connected" style.
    """

    AVAILABLE = "available"
    ACTIVE = "active"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LinkRecord:
    link_key: str
    source: EntityId
    target: EntityId
    link_class: str
    activity: LinkActivity
    capacity_mbps: Measured | None = None
    flow_mbps: Measured | None = None
    utilization: Measured | None = None
    resource_domain: str | None = None
    snr_db: Measured | None = None
    distance_m: Measured | None = None
    #: Solver-local index, kept only for cross-referencing inside one frame.
    producer_local_id: int | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "link_key": self.link_key,
            "source": self.source.key,
            "target": self.target.key,
            "link_class": self.link_class,
            "activity": self.activity.value,
            "capacity_mbps": _opt_measured(self.capacity_mbps),
            "flow_mbps": _opt_measured(self.flow_mbps),
            "utilization": _opt_measured(self.utilization),
            "resource_domain": self.resource_domain,
            "snr_db": _opt_measured(self.snr_db),
            "distance_m": _opt_measured(self.distance_m),
            "producer_local_id": _opt_int(self.producer_local_id),
        }


@dataclass(frozen=True)
class ResourceDomainRecord:
    domain_id: str
    description: str
    link_keys: tuple[str, ...]
    utilization: Measured | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "description": self.description,
            "link_keys": list(self.link_keys),
            "utilization": _opt_measured(self.utilization),
        }


@dataclass(frozen=True)
class PathRecord:
    """A candidate or carrying path, identified by node/link identity not enumeration."""

    demand_entity: str
    node_keys: tuple[str, ...]
    link_keys: tuple[str, ...]
    backhaul_hops: int
    flow_mbps: Measured | None = None
    selected: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            "demand_entity": self.demand_entity,
            "node_keys": list(self.node_keys),
            "link_keys": list(self.link_keys),
            "backhaul_hops": int(self.backhaul_hops),
            "flow_mbps": _opt_measured(self.flow_mbps),
            "selected": bool(self.selected),
        }


@dataclass(frozen=True)
class DecisionEvent:
    """A real decision or exogenous event, with the time it actually occurred."""

    time_s: float
    event_type: str
    description: str
    entity: str | None = None
    team_skill_id: int | None = None
    individual_skill_ids: tuple[int, ...] | None = None
    renew: bool | None = None
    availability: str = "recorded"

    def to_json(self) -> dict[str, Any]:
        return {
            "time_s": float(self.time_s),
            "event_type": self.event_type,
            "description": self.description,
            "entity": self.entity,
            "team_skill_id": _opt_int(self.team_skill_id),
            "individual_skill_ids": (
                None
                if self.individual_skill_ids is None
                else [int(v) for v in self.individual_skill_ids]
            ),
            "renew": self.renew,
            "availability": self.availability,
        }


@dataclass(frozen=True)
class StreamHealth:
    state: StreamState
    dropped_display_frames: int = 0
    missing_sequences: int = 0
    refused_by_gate: int = 0
    refused_by_byte_budget: int = 0
    trace_status: str = "open"
    producer_status: str = "running"
    last_error: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "dropped_display_frames": int(self.dropped_display_frames),
            "missing_sequences": int(self.missing_sequences),
            "refused_by_gate": int(self.refused_by_gate),
            "refused_by_byte_budget": int(self.refused_by_byte_budget),
            "trace_status": self.trace_status,
            "producer_status": self.producer_status,
            "last_error": self.last_error,
        }


@dataclass(frozen=True)
class ObservationView:
    """What the policy was actually permitted to see at the decision time.

    Filled from the environment's own policy-facing store. It must never be completed
    from privileged truth: an unknown field stays unknown here even when the simulator
    knows the answer, because that difference is exactly what the owner inspects.
    """

    values: Mapping[str, Any] = field(default_factory=dict)
    masks: Mapping[str, list[bool]] = field(default_factory=dict)
    ages_s: Mapping[str, list[float | None]] = field(default_factory=dict)
    field_provenance: Mapping[str, str] = field(default_factory=dict)
    information_condition: str = "unknown"

    def to_json(self) -> dict[str, Any]:
        return {
            "values": _json_safe(self.values),
            "masks": {k: [bool(b) for b in v] for k, v in self.masks.items()},
            "ages_s": {k: [_opt_float(x) for x in v] for k, v in self.ages_s.items()},
            "field_provenance": dict(self.field_provenance),
            "information_condition": self.information_condition,
        }


@dataclass(frozen=True)
class SceneFrame:
    """One validated, immutable display/replay packet.

    Every array reaching this type must already be an owned copy. The producer builds a
    frame only after the eligibility gates pass, so constructing a ``SceneFrame`` is
    itself evidence that a sample was admitted.
    """

    identity: SceneIdentity
    clock: SceneClock
    provenance: SceneProvenance
    geometry: SceneGeometry
    capability: SceneCapability
    uavs: tuple[UavState, ...] = ()
    ground_entities: tuple[GroundEntityState, ...] = ()
    sites: tuple[SiteStateRecord, ...] = ()
    links: tuple[LinkRecord, ...] = ()
    resource_domains: tuple[ResourceDomainRecord, ...] = ()
    paths: tuple[PathRecord, ...] = ()
    events: tuple[DecisionEvent, ...] = ()
    interval_metrics: Mapping[str, Measured] = field(default_factory=dict)
    observation_view: ObservationView | None = None
    stream_health: StreamHealth | None = None
    schema: str = SCENE_SCHEMA

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "identity": self.identity.to_json(),
            "clock": self.clock.to_json(),
            "provenance": self.provenance.to_json(),
            "geometry": self.geometry.to_json(),
            "capability": self.capability.to_json(),
            "uavs": [u.to_json() for u in self.uavs],
            "ground_entities": [g.to_json() for g in self.ground_entities],
            "sites": [s.to_json() for s in self.sites],
            "links": [l.to_json() for l in self.links],
            "resource_domains": [d.to_json() for d in self.resource_domains],
            "paths": [p.to_json() for p in self.paths],
            "events": [e.to_json() for e in self.events],
            "interval_metrics": {k: v.to_json() for k, v in self.interval_metrics.items()},
            "observation_view": (
                None if self.observation_view is None else self.observation_view.to_json()
            ),
            "stream_health": (
                None if self.stream_health is None else self.stream_health.to_json()
            ),
        }

    def to_bytes(self) -> bytes:
        return dumps(self.to_json()).encode("utf-8")


def validate_scene_json(payload: Mapping[str, Any]) -> list[str]:
    """Return a list of contract violations; an empty list means the frame is usable.

    Validation is deliberately a report rather than an exception: a partially written
    trace should still be readable up to its last valid frame.
    """

    problems: list[str] = []
    schema = payload.get("schema")
    if schema != SCENE_SCHEMA:
        problems.append(f"schema mismatch: {schema!r} != {SCENE_SCHEMA!r}")
    for key in ("identity", "clock", "provenance", "geometry", "capability"):
        if not isinstance(payload.get(key), Mapping):
            problems.append(f"missing or malformed section: {key}")
    clock = payload.get("clock")
    if isinstance(clock, Mapping):
        start = clock.get("measurement_start_s")
        end = clock.get("measurement_end_s")
        if start is not None and end is not None and float(end) < float(start):
            problems.append("measurement interval ends before it starts")
    link_keys = set()
    for link in payload.get("links", ()) or ():
        if not isinstance(link, Mapping):
            problems.append("malformed link entry")
            continue
        key = link.get("link_key")
        if key in link_keys:
            problems.append(f"duplicate link_key: {key}")
        link_keys.add(key)
    entity_keys: set[str] = set()
    for section in ("uavs", "ground_entities", "sites"):
        for item in payload.get(section, ()) or ():
            if not isinstance(item, Mapping):
                problems.append(f"malformed {section} entry")
                continue
            entity = item.get("entity") or {}
            key = entity.get("key") if isinstance(entity, Mapping) else None
            if key is None:
                problems.append(f"{section} entry without an entity key")
            elif key in entity_keys:
                problems.append(f"duplicate entity key: {key}")
            else:
                entity_keys.add(key)
    for path in payload.get("paths", ()) or ():
        if not isinstance(path, Mapping):
            continue
        for key in path.get("link_keys", ()) or ():
            if link_keys and key not in link_keys:
                problems.append(f"path references unknown link_key: {key}")
    return problems


# --------------------------------------------------------------------------------------
# Metric records
# --------------------------------------------------------------------------------------


class XKind(str, Enum):
    """The x axis a metric value sits on. Never mix two of these on one unlabelled axis."""

    TRAINING_TEAM_STEP = "training_team_step"
    TRAINING_AGENT_TRANSITION = "training_agent_transition"
    UPDATE_INDEX = "update_index"
    WALL_TIME_S = "wall_time_s"
    EPISODE_STEP = "episode_step"
    SIMULATED_SECOND = "simulated_second"
    EPISODE_INDEX = "episode_index"
    CHECKPOINT_STEP = "checkpoint_step"
    NONE = "none"


class Phase(str, Enum):
    TRAINING = "training"
    EVALUATION = "evaluation"
    UNTRAINED_DEMO = "untrained_demo"
    SYNTHETIC_FIXTURE = "synthetic_fixture"
    DIAGNOSTIC_ROLLOUT = "diagnostic_rollout"


class AggregationLevel(str, Enum):
    EPISODE = "episode"
    WORLD = "world"
    REPLICATE = "replicate"
    METHOD = "method"
    SUBINTERVAL = "subinterval"


@dataclass(frozen=True)
class MetricRecord:
    """One long-form measurement.

    Identity fields distinguish an independent training replicate from an extra
    evaluation episode of the same replicate, which is the difference between more
    evidence and more precision about one fit.
    """

    run_id: str
    method_id: str
    metric_name: str
    value: Measured
    x_kind: XKind
    x_value: float | int | None
    phase: Phase
    aggregation_level: AggregationLevel
    training_replicate_id: str | None = None
    checkpoint_id: str | None = None
    world_id: str | None = None
    episode_id: str | None = None
    lane_id: int | None = None
    unit: str | None = None
    definition_id: str | None = None
    direction: str = "unknown"
    interval_start_s: float | None = None
    interval_end_s: float | None = None
    source_path: str | None = None
    source_row_or_key: str | None = None
    schema: str = METRIC_SCHEMA

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "method_id": self.method_id,
            "training_replicate_id": self.training_replicate_id,
            "checkpoint_id": self.checkpoint_id,
            "world_id": self.world_id,
            "episode_id": self.episode_id,
            "lane_id": _opt_int(self.lane_id),
            "phase": self.phase.value,
            "metric_name": self.metric_name,
            "value": self.value.value,
            "validity": self.value.validity.value,
            "reason": self.value.reason,
            "unit": self.unit or self.value.unit,
            "definition_id": self.definition_id,
            "direction": self.direction,
            "x_kind": self.x_kind.value,
            "x_value": self.x_value,
            "interval_start_s": _opt_float(self.interval_start_s),
            "interval_end_s": _opt_float(self.interval_end_s),
            "aggregation_level": self.aggregation_level.value,
            "source_path": self.source_path,
            "source_row_or_key": self.source_row_or_key,
        }

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "MetricRecord":
        validity = Validity(payload.get("validity", "ok"))
        if validity is Validity.OK:
            measured = Measured.ok(payload["value"], unit=payload.get("unit"))
        else:
            measured = Measured.absent(
                validity, payload.get("reason") or "unspecified", unit=payload.get("unit")
            )
        return cls(
            run_id=payload["run_id"],
            method_id=payload["method_id"],
            metric_name=payload["metric_name"],
            value=measured,
            x_kind=XKind(payload.get("x_kind", "none")),
            x_value=payload.get("x_value"),
            phase=Phase(payload.get("phase", "evaluation")),
            aggregation_level=AggregationLevel(payload.get("aggregation_level", "episode")),
            training_replicate_id=payload.get("training_replicate_id"),
            checkpoint_id=payload.get("checkpoint_id"),
            world_id=payload.get("world_id"),
            episode_id=payload.get("episode_id"),
            lane_id=payload.get("lane_id"),
            unit=payload.get("unit"),
            definition_id=payload.get("definition_id"),
            direction=payload.get("direction", "unknown"),
            interval_start_s=payload.get("interval_start_s"),
            interval_end_s=payload.get("interval_end_s"),
            source_path=payload.get("source_path"),
            source_row_or_key=payload.get("source_row_or_key"),
        )


# --------------------------------------------------------------------------------------
# Run identity record
# --------------------------------------------------------------------------------------


@dataclass
class RunRecord:
    """Normalised identity of one run, as read from its artifacts.

    Every optional field is a :class:`Measured` or an explicit ``None`` with a status in
    :attr:`field_status`, so a report can print "not recorded" instead of a present-day
    default that the run never used.
    """

    run_id: str
    reader: str
    reader_version: str
    source_paths: list[str] = field(default_factory=list)
    source_hashes: dict[str, str] = field(default_factory=dict)
    fields: dict[str, Measured] = field(default_factory=dict)
    field_status: dict[str, str] = field(default_factory=dict)
    coverage: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    schema: str = RUN_SCHEMA

    def set(self, name: str, value: Measured, *, evidence: str | None = None) -> None:
        self.fields[name] = value
        self.field_status[name] = evidence or (
            "recorded" if value.validity is Validity.OK else value.validity.value
        )

    def get(self, name: str) -> Measured:
        return self.fields.get(name, Measured.unknown(f"field_not_read:{name}"))

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "reader": self.reader,
            "reader_version": self.reader_version,
            "source_paths": list(self.source_paths),
            "source_hashes": dict(self.source_hashes),
            "fields": {k: v.to_json() for k, v in sorted(self.fields.items())},
            "field_status": dict(sorted(self.field_status.items())),
            "coverage": _json_safe(self.coverage),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


# --------------------------------------------------------------------------------------
# JSON encoding
# --------------------------------------------------------------------------------------


class _SafeEncoder(json.JSONEncoder):
    """JSON with no ``NaN``/``Infinity`` tokens and no surprise pickling.

    ``json.dumps`` emits bare ``NaN`` by default, which is not JSON and which several
    strict parsers reject. Non-finite floats therefore become ``null``; the surrounding
    record carries the validity that explains why.
    """

    def default(self, o: Any) -> Any:  # noqa: D102
        if isinstance(o, Measured):
            return o.to_json()
        if isinstance(o, EntityId):
            return o.to_json()
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            value = float(o)
            return value if math.isfinite(value) else None
        if isinstance(o, np.bool_):
            return bool(o)
        if isinstance(o, np.ndarray):
            return _json_safe(o.tolist())
        if isinstance(o, (set, frozenset)):
            return sorted(_json_safe(v) for v in o)
        if isinstance(o, bytes):
            return base64.b64encode(o).decode("ascii")
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            if hasattr(o, "to_json"):
                return o.to_json()
            return _json_safe(dataclasses.asdict(o))
        return super().default(o)


def _json_safe(value: Any) -> Any:
    """Recursively replace non-finite floats with ``None`` and normalise numpy scalars."""

    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (np.floating,)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def dumps(payload: Any, *, indent: int | None = None) -> str:
    """Serialise to strict JSON that is also safe to embed in an HTML ``<script>``.

    ``</script>`` inside a string would otherwise close the element early, and ``<!--``
    can start an HTML comment inside a script body, so both are escaped.
    """

    text = json.dumps(
        _json_safe(payload), cls=_SafeEncoder, indent=indent, allow_nan=False, sort_keys=False
    )
    return (
        text.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )


def loads(text: str | bytes) -> Any:
    """Parse JSON, refusing the non-standard ``NaN``/``Infinity`` tokens."""

    def _reject(value: str) -> float:
        raise ValueError(
            f"non-standard JSON constant {value!r}; records encode missing values as "
            "null plus a validity reason"
        )

    return json.loads(
        text.decode("utf-8") if isinstance(text, bytes) else text,
        parse_constant=_reject,
    )


def content_hash(payload: Any) -> str:
    """Stable content hash of a record, for provenance links between figures and data."""

    canonical = json.dumps(_json_safe(payload), cls=_SafeEncoder, sort_keys=True, allow_nan=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def file_hash(path: str, *, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return "sha256:" + digest.hexdigest()


# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------


def _opt_float(value: Any) -> float | None:
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _opt_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _opt_vec(value: Sequence[float] | None) -> list[float] | None:
    return None if value is None else [float(v) for v in value]


def _opt_measured(value: Measured | None) -> dict[str, Any] | None:
    return None if value is None else value.to_json()


def measured_array(
    values: np.ndarray,
    *,
    observed: np.ndarray | None = None,
    unit: str | None = None,
    unobserved_validity: Validity = Validity.UNKNOWN,
    unobserved_reason: str = "not_observed",
) -> list[Measured]:
    """Convert a numeric array into per-element :class:`Measured` values.

    ``observed=False`` yields an absent value, not zero. A finite value at an observed
    position is reported as measured even when it is exactly ``0.0``.
    """

    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    mask = (
        np.ones(flat.shape, dtype=bool)
        if observed is None
        else np.asarray(observed, dtype=bool).reshape(-1)
    )
    if mask.shape != flat.shape:
        raise ValueError(f"observed mask shape {mask.shape} != values shape {flat.shape}")
    out: list[Measured] = []
    for value, seen in zip(flat.tolist(), mask.tolist()):
        if not seen:
            out.append(Measured.absent(unobserved_validity, unobserved_reason, unit=unit))
        elif not math.isfinite(value):
            out.append(Measured.invalid("non_finite", unit=unit))
        else:
            out.append(Measured.ok(value, unit=unit))
    return out
