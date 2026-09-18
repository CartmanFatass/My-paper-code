"""Value types for ``uav_service_restoration_v0``.

Every quantity carries its unit in the field name.  Rates are Mbps, accumulated volumes
are Mbit, distances are metres, times are simulated seconds unless the name says
``_utc_ms``, powers are dBm, bandwidths are Hz.

Nothing in this module reads a file, touches global state or imports an optional
dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

import numpy as np

# --------------------------------------------------------------------------------------
# Demand
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class DemandMetadata:
    """Provenance of a demand source.

    ``kind`` is the machine-readable source identity and is the single place that
    distinguishes an explicitly synthetic fixture from real activity data.
    """

    kind: str
    schema_version: str
    is_real_activity_data: bool
    description: str
    dataset_hash: str
    source_url: str | None = None
    license_note: str | None = None
    activity_field: str | None = None
    demand_scale_mbps: float | None = None
    activity_reference_scale: float | None = None
    interval_duration_s: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EpisodeDescriptor:
    """Identity of one episode's exogenous demand window.

    ``history_start_utc_ms`` is the earliest source interval the episode is permitted to
    read; it exists so that the first permitted observation has real history behind it
    instead of a wrap-around to the beginning of a day.
    """

    episode_id: str
    split: str
    region_id: str
    start_utc_ms: int
    end_utc_ms: int
    history_start_utc_ms: int
    dataset_hash: str

    def contains(self, timestamp_utc_ms: int) -> bool:
        return self.history_start_utc_ms <= int(timestamp_utc_ms) < self.end_utc_ms


@dataclass(frozen=True)
class DemandFrame:
    """One source interval of offered demand.

    ``activity`` holds the raw source activity values and ``demand_mbps`` the mapped
    simulation demand proxy.  ``observed_mask`` is False where the source has no record;
    a False entry is *unknown*, never a measured zero.
    """

    interval_start_utc_ms: int
    interval_end_utc_ms: int
    cell_ids: np.ndarray
    activity: np.ndarray
    demand_mbps: np.ndarray
    observed_mask: np.ndarray

    def __post_init__(self) -> None:
        n = int(self.cell_ids.shape[0])
        for name in ("activity", "demand_mbps", "observed_mask"):
            value = getattr(self, name)
            if value.shape != (n,):
                raise ValueError(
                    f"DemandFrame.{name} has shape {value.shape}; expected {(n,)}"
                )
        if self.interval_end_utc_ms <= self.interval_start_utc_ms:
            raise ValueError("DemandFrame interval must be a positive half-open range")


@runtime_checkable
class DemandSource(Protocol):
    """Read-only exogenous demand.

    This interface is consumed by the simulator only.  It is never handed to a policy:
    it can read any interval of the underlying trace, including future ones.
    """

    def metadata(self) -> DemandMetadata: ...

    def cell_positions_m(self) -> np.ndarray: ...

    def cell_ids(self) -> np.ndarray: ...

    def sample_episode(self, split: str, rng: np.random.Generator) -> EpisodeDescriptor: ...

    def read_interval(
        self, episode: EpisodeDescriptor, timestamp_utc_ms: int
    ) -> DemandFrame: ...


# --------------------------------------------------------------------------------------
# Terrestrial network state and exogenous events
# --------------------------------------------------------------------------------------


@dataclass
class SiteState:
    """Capability of one terrestrial site.

    Four independent fields rather than one ``failed`` flag, so that "the radio is dead"
    and "the wired backhaul is dead" are distinguishable and separately testable.
    """

    radio_up: bool = True
    core_link_up: bool = True
    access_capacity_scale: float = 1.0
    backhaul_capacity_scale: float = 1.0

    def copy(self) -> "SiteState":
        return SiteState(
            radio_up=bool(self.radio_up),
            core_link_up=bool(self.core_link_up),
            access_capacity_scale=float(self.access_capacity_scale),
            backhaul_capacity_scale=float(self.backhaul_capacity_scale),
        )

    def as_vector(self) -> np.ndarray:
        return np.array(
            [
                1.0 if self.radio_up else 0.0,
                1.0 if self.core_link_up else 0.0,
                float(self.access_capacity_scale),
                float(self.backhaul_capacity_scale),
            ],
            dtype=np.float64,
        )


class EventType(str, Enum):
    FULL_SITE_FAILURE = "full_site_failure"
    CAPACITY_DEGRADATION = "capacity_degradation"
    WIRED_BACKHAUL_OUTAGE = "wired_backhaul_outage"


@dataclass(frozen=True)
class NetworkEvent:
    """One exogenous capability event over the half-open interval ``[start_s, end_s)``.

    ``end_s is None`` means the event never ends inside the episode: the site is not
    repaired.  A finite ``end_s`` *is* the repair; capability returns to its configured
    value when the interval closes, and never in response to a policy score.
    """

    event_type: EventType
    site_index: int
    start_s: float
    end_s: float | None = None
    access_capacity_scale: float = 1.0
    backhaul_capacity_scale: float = 1.0
    event_source: str = "configured"

    def active_at(self, time_s: float) -> bool:
        if float(time_s) < float(self.start_s):
            return False
        if self.end_s is None:
            return True
        return float(time_s) < float(self.end_s)

    def boundaries(self) -> tuple[float, ...]:
        if self.end_s is None:
            return (float(self.start_s),)
        return (float(self.start_s), float(self.end_s))


# --------------------------------------------------------------------------------------
# Network graph and scheduler results
# --------------------------------------------------------------------------------------


class NodeKind(str, Enum):
    CORE = "core"
    SITE = "site"
    UAV = "uav"
    DEMAND = "demand"


class LinkClass(str, Enum):
    WIRED_CORE = "wired_core"
    SITE_ACCESS = "site_access"
    UAV_ACCESS = "uav_access"
    SITE_UAV_BACKHAUL = "site_uav_backhaul"
    UAV_UAV_BACKHAUL = "uav_uav_backhaul"

    @property
    def is_wireless(self) -> bool:
        return self is not LinkClass.WIRED_CORE

    @property
    def is_access(self) -> bool:
        return self in (LinkClass.SITE_ACCESS, LinkClass.UAV_ACCESS)

    @property
    def is_backhaul(self) -> bool:
        return self in (LinkClass.SITE_UAV_BACKHAUL, LinkClass.UAV_UAV_BACKHAUL)


@dataclass(frozen=True)
class Node:
    kind: NodeKind
    index: int

    def key(self) -> tuple[str, int]:
        return (self.kind.value, int(self.index))


@dataclass(frozen=True)
class Link:
    """A directed link with its isolated capacity.

    ``capacity_mbps`` is the rate the link would carry if it owned its radio resource
    outright.  Shared-resource limits are applied separately by the scheduler, so a
    per-link capacity alone never implies schedulability.
    """

    link_id: int
    source: Node
    target: Node
    link_class: LinkClass
    capacity_mbps: float
    distance_m: float
    snr_db: float


@dataclass(frozen=True)
class ResourceDomain:
    """A set of wireless links that share one radio resource in time.

    The constraint is ``sum_l rate_l / isolated_capacity_l <= 1``: the most conservative
    easily testable time-sharing statement.
    """

    domain_id: str
    description: str
    link_ids: tuple[int, ...]


@dataclass(frozen=True)
class CandidatePath:
    """A cycle-free core-to-demand path.

    ``backhaul_hops`` counts wireless *backhaul* edges only.  The final access edge and
    the wired core edge are deliberately excluded from that count.
    """

    demand_index: int
    node_keys: tuple[tuple[str, int], ...]
    link_ids: tuple[int, ...]
    backhaul_hops: int


@dataclass
class NetworkSnapshot:
    """Everything the scheduler needs for one instant."""

    nodes: tuple[Node, ...]
    links: tuple[Link, ...]
    resource_domains: tuple[ResourceDomain, ...]
    paths: tuple[CandidatePath, ...]
    demand_mbps: np.ndarray
    gateway_egress_capacity_mbps: dict[int, float]
    core_total_egress_mbps: float | None = None


class SchedulerStatus(str, Enum):
    OPTIMAL = "optimal"
    TRIVIAL_ZERO = "trivial_zero"
    INFEASIBLE = "infeasible"
    SOLVER_FAILED = "solver_failed"
    NON_FINITE = "non_finite"


@dataclass
class SchedulerResult:
    """Structured outcome of one scheduler solve.

    A failure is reported, never silently replaced by an approximation.
    """

    status: SchedulerStatus
    delivered_mbps_per_demand: np.ndarray
    delivered_mbps_total: float
    path_flows_mbps: np.ndarray
    link_flow_mbps: dict[int, float]
    domain_utilization: dict[str, float]
    gateway_utilization: dict[int, float]
    max_constraint_residual: float
    n_variables: int
    n_constraints: int
    solver_message: str = ""
    solver_method_used: str = ""

    @property
    def ok(self) -> bool:
        return self.status in (SchedulerStatus.OPTIMAL, SchedulerStatus.TRIVIAL_ZERO)


class SchedulerError(RuntimeError):
    """Base class for scheduler failures that must not be silently absorbed."""


class SchedulerSizeLimitError(SchedulerError):
    """The problem exceeded a configured size limit; it was not truncated."""


class SchedulerSolveError(SchedulerError):
    """The linear program was infeasible, non-finite or failed to solve."""

    def __init__(self, message: str, result: SchedulerResult | None = None) -> None:
        super().__init__(message)
        self.result = result


# --------------------------------------------------------------------------------------
# Telemetry
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TelemetryRecord:
    """Aggregated report of one completed control interval.

    Produced only after the interval it describes has finished, and released to the
    policy only after ``telemetry_delay_s`` has elapsed.
    """

    interval_start_s: float
    interval_end_s: float
    release_time_s: float
    uav_positions_m: np.ndarray
    uav_velocities_mps: np.ndarray
    site_state_vectors: np.ndarray
    site_state_observed: np.ndarray
    demand_offered_mbps: np.ndarray
    demand_delivered_mbps: np.ndarray
    demand_observed: np.ndarray
