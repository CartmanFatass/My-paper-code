"""Network graph, candidate paths and shared-resource domains.

Topology
--------
``core -> site`` (wired) ``-> demand`` (site access radio), and
``core -> site -> uav [-> uav ...] -> demand`` (wireless backhaul then UAV access radio).

Capability mapping, stated explicitly because ``SiteState`` has four independent fields:

============================  ====================================================
field                         what it gates
============================  ====================================================
``radio_up``                  every radio function of the site: its access links to
                              demand points *and* the wireless backhaul it offers to
                              UAVs.  A dead site provides neither.
``core_link_up``              the wired ``core -> site`` edge.
``access_capacity_scale``     multiplies ``site -> demand`` access capacity.
``backhaul_capacity_scale``   multiplies both the wired ``core -> site`` capacity and
                              the ``site -> uav`` wireless backhaul capacity.
============================  ====================================================

A UAV never delivers traffic *into* a terrestrial site unless that site declares
``accepts_uav_wireless_backhaul``.  v0 leaves it False: an ordinary site is not assumed
to have the hardware to accept reverse wireless backhaul, so a site whose wired link is
down cannot be revived by a UAV.  UAVs instead serve terminals through surviving egress
points.

Hop limit
---------
``max_backhaul_hops`` is the maximum number of **wireless backhaul edges**
(``site -> uav`` and ``uav -> uav``) on a path.  The final access edge and the wired core
edge are excluded from that count, consistently, in both enumeration and reporting.

Shared resources
----------------
Resource domains express time sharing of one radio:

* one **access** domain per transmitting node (each site, each UAV) over its outgoing
  access links - a node cannot give every demand point an independent copy of its
  bandwidth;
* one **backhaul** domain per UAV over *all* backhaul links incident to it, incoming and
  outgoing - this is the half-duplex constraint, so a relay cannot receive and forward at
  full rate simultaneously;
* one **backhaul** domain per site over its outgoing ``site -> uav`` links.

With ``access_and_backhaul_share_band`` the access and backhaul domains of a node are
merged into one.  Distinct nodes are never placed in a common domain: v0 assumes
unrestricted spatial reuse between different radios and models no interference.  That is
a simplification, not a validated IAB contention model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .config import EnvConfig, NetworkConfig
from .radio import capacity_mbps, snr_db
from .types import (
    CandidatePath,
    Link,
    LinkClass,
    NetworkSnapshot,
    Node,
    NodeKind,
    ResourceDomain,
    SchedulerSizeLimitError,
    SiteState,
)

CORE_NODE = Node(kind=NodeKind.CORE, index=0)


@dataclass(frozen=True)
class _LinkBuildResult:
    links: tuple[Link, ...]
    outgoing: dict[tuple[str, int], tuple[int, ...]]


def _node_key(kind: NodeKind, index: int) -> tuple[str, int]:
    return (kind.value, int(index))


def build_links(
    network: NetworkConfig,
    site_states: Sequence[SiteState],
    uav_positions_m: np.ndarray,
    demand_positions_m: np.ndarray,
) -> _LinkBuildResult:
    """Enumerate every currently usable directed link with its isolated capacity.

    Links whose capacity is zero - out of range, below the SNR floor, or gated off by a
    failure - are omitted, so a failed node retains no invalid access or forwarding path.
    """

    sites = network.sites
    if len(site_states) != len(sites):
        raise ValueError("site_states length does not match the configured site count")
    uavs = np.asarray(uav_positions_m, dtype=np.float64).reshape(-1, 3)
    demands = np.asarray(demand_positions_m, dtype=np.float64).reshape(-1, 3)
    models = network.radio_models

    links: list[Link] = []
    outgoing: dict[tuple[str, int], list[int]] = {}

    def add(
        source: Node,
        target: Node,
        link_class: LinkClass,
        capacity: float,
        distance: float,
        snr: float,
    ) -> None:
        if not np.isfinite(capacity) or capacity <= 0.0:
            return
        link = Link(
            link_id=len(links),
            source=source,
            target=target,
            link_class=link_class,
            capacity_mbps=float(capacity),
            distance_m=float(distance),
            snr_db=float(snr),
        )
        links.append(link)
        outgoing.setdefault(source.key(), []).append(link.link_id)

    # -- wired core edges --------------------------------------------------------------
    for site_index, (site, state) in enumerate(zip(sites, site_states)):
        if not state.core_link_up:
            continue
        capacity = float(site.core_egress_capacity_mbps) * float(state.backhaul_capacity_scale)
        add(
            CORE_NODE,
            Node(NodeKind.SITE, site_index),
            LinkClass.WIRED_CORE,
            capacity,
            0.0,
            float("inf"),
        )

    # -- site access edges -------------------------------------------------------------
    site_positions = np.asarray([site.position_m for site in sites], dtype=np.float64)
    access_model = models["site_access"]
    for site_index, (site, state) in enumerate(zip(sites, site_states)):
        if not (state.radio_up and site.serves_access):
            continue
        if demands.shape[0] == 0:
            continue
        distances = np.sqrt(
            np.sum((demands - site_positions[site_index][None, :]) ** 2, axis=1)
        )
        capacities = capacity_mbps(distances, access_model) * float(state.access_capacity_scale)
        snrs = snr_db(distances, access_model)
        radius = network.site_access_radius_m
        for demand_index in range(demands.shape[0]):
            if radius is not None and distances[demand_index] > float(radius):
                continue
            add(
                Node(NodeKind.SITE, site_index),
                Node(NodeKind.DEMAND, demand_index),
                LinkClass.SITE_ACCESS,
                float(capacities[demand_index]),
                float(distances[demand_index]),
                float(snrs[demand_index]),
            )

    # -- site <-> UAV backhaul ---------------------------------------------------------
    backhaul_model = models["site_uav_backhaul"]
    for site_index, (site, state) in enumerate(zip(sites, site_states)):
        if not (state.radio_up and site.serves_uav_backhaul):
            continue
        if uavs.shape[0] == 0:
            continue
        distances = np.sqrt(np.sum((uavs - site_positions[site_index][None, :]) ** 2, axis=1))
        capacities = capacity_mbps(distances, backhaul_model) * float(
            state.backhaul_capacity_scale
        )
        snrs = snr_db(distances, backhaul_model)
        for uav_index in range(uavs.shape[0]):
            add(
                Node(NodeKind.SITE, site_index),
                Node(NodeKind.UAV, uav_index),
                LinkClass.SITE_UAV_BACKHAUL,
                float(capacities[uav_index]),
                float(distances[uav_index]),
                float(snrs[uav_index]),
            )
            if site.accepts_uav_wireless_backhaul:
                add(
                    Node(NodeKind.UAV, uav_index),
                    Node(NodeKind.SITE, site_index),
                    LinkClass.SITE_UAV_BACKHAUL,
                    float(capacities[uav_index]),
                    float(distances[uav_index]),
                    float(snrs[uav_index]),
                )

    # -- UAV <-> UAV backhaul ----------------------------------------------------------
    uav_model = models["uav_uav_backhaul"]
    for i in range(uavs.shape[0]):
        for j in range(uavs.shape[0]):
            if i == j:
                continue
            distance = float(np.sqrt(np.sum((uavs[i] - uavs[j]) ** 2)))
            add(
                Node(NodeKind.UAV, i),
                Node(NodeKind.UAV, j),
                LinkClass.UAV_UAV_BACKHAUL,
                float(capacity_mbps(distance, uav_model)),
                distance,
                float(snr_db(distance, uav_model)),
            )

    # -- UAV access edges --------------------------------------------------------------
    uav_access_model = models["uav_access"]
    for uav_index in range(uavs.shape[0]):
        if demands.shape[0] == 0:
            continue
        distances = np.sqrt(np.sum((demands - uavs[uav_index][None, :]) ** 2, axis=1))
        capacities = capacity_mbps(distances, uav_access_model)
        snrs = snr_db(distances, uav_access_model)
        for demand_index in range(demands.shape[0]):
            add(
                Node(NodeKind.UAV, uav_index),
                Node(NodeKind.DEMAND, demand_index),
                LinkClass.UAV_ACCESS,
                float(capacities[demand_index]),
                float(distances[demand_index]),
                float(snrs[demand_index]),
            )

    return _LinkBuildResult(
        links=tuple(links),
        outgoing={key: tuple(value) for key, value in outgoing.items()},
    )


def enumerate_paths(
    build: _LinkBuildResult,
    network: NetworkConfig,
    n_demand_points: int,
) -> tuple[CandidatePath, ...]:
    """Depth-first enumeration of cycle-free, hop-limited core-to-demand paths.

    Deterministic: links are visited in ascending ``link_id`` order, which is itself fixed
    by the construction order in :func:`build_links`.

    Exceeding ``max_candidate_paths_per_demand`` or ``max_total_candidate_paths`` raises
    :class:`SchedulerSizeLimitError`.  The problem is never silently truncated while
    still being described as the same exact model.
    """

    paths: list[CandidatePath] = []
    per_demand = [0] * int(n_demand_points)
    max_per_demand = int(network.max_candidate_paths_per_demand)
    max_total = int(network.max_total_candidate_paths)
    max_hops = int(network.max_backhaul_hops)

    def walk(
        node: Node,
        visited: frozenset[tuple[str, int]],
        link_ids: tuple[int, ...],
        node_keys: tuple[tuple[str, int], ...],
        backhaul_hops: int,
    ) -> None:
        for link_id in build.outgoing.get(node.key(), ()):
            link = build.links[link_id]
            target_key = link.target.key()
            if target_key in visited:
                continue
            next_hops = backhaul_hops + (1 if link.link_class.is_backhaul else 0)
            if next_hops > max_hops:
                continue
            if link.target.kind is NodeKind.DEMAND:
                demand_index = int(link.target.index)
                per_demand[demand_index] += 1
                if per_demand[demand_index] > max_per_demand:
                    raise SchedulerSizeLimitError(
                        f"demand point {demand_index} has more than "
                        f"{max_per_demand} candidate paths; raise "
                        "network.max_candidate_paths_per_demand or reduce the topology "
                        "rather than truncating the model"
                    )
                if len(paths) + 1 > max_total:
                    raise SchedulerSizeLimitError(
                        f"candidate path count exceeds network.max_total_candidate_paths "
                        f"({max_total})"
                    )
                paths.append(
                    CandidatePath(
                        demand_index=demand_index,
                        node_keys=node_keys + (target_key,),
                        link_ids=link_ids + (link_id,),
                        backhaul_hops=next_hops,
                    )
                )
                continue
            walk(
                link.target,
                visited | {target_key},
                link_ids + (link_id,),
                node_keys + (target_key,),
                next_hops,
            )

    walk(CORE_NODE, frozenset({CORE_NODE.key()}), (), (CORE_NODE.key(),), 0)
    return tuple(paths)


def build_resource_domains(
    build: _LinkBuildResult, network: NetworkConfig
) -> tuple[ResourceDomain, ...]:
    """Group wireless links into the time-sharing domains described in the module docstring."""

    access_by_node: dict[tuple[str, int], list[int]] = {}
    backhaul_by_node: dict[tuple[str, int], list[int]] = {}

    for link in build.links:
        if not link.link_class.is_wireless:
            continue
        if link.link_class.is_access:
            access_by_node.setdefault(link.source.key(), []).append(link.link_id)
        else:
            # Half-duplex: a backhaul link occupies the radio of both endpoints when the
            # endpoint is a UAV.  Sites are charged only for what they transmit.
            backhaul_by_node.setdefault(link.source.key(), []).append(link.link_id)
            if link.target.kind is NodeKind.UAV:
                backhaul_by_node.setdefault(link.target.key(), []).append(link.link_id)

    domains: list[ResourceDomain] = []
    if network.access_and_backhaul_share_band:
        keys = sorted(set(access_by_node) | set(backhaul_by_node))
        for key in keys:
            link_ids = sorted(set(access_by_node.get(key, [])) | set(backhaul_by_node.get(key, [])))
            if not link_ids:
                continue
            domains.append(
                ResourceDomain(
                    domain_id=f"shared:{key[0]}{key[1]}",
                    description=(
                        f"{key[0]} {key[1]} radio airtime, access and backhaul in one band"
                    ),
                    link_ids=tuple(link_ids),
                )
            )
        return tuple(domains)

    for key in sorted(access_by_node):
        link_ids = sorted(set(access_by_node[key]))
        domains.append(
            ResourceDomain(
                domain_id=f"access:{key[0]}{key[1]}",
                description=f"{key[0]} {key[1]} access radio airtime",
                link_ids=tuple(link_ids),
            )
        )
    for key in sorted(backhaul_by_node):
        link_ids = sorted(set(backhaul_by_node[key]))
        domains.append(
            ResourceDomain(
                domain_id=f"backhaul:{key[0]}{key[1]}",
                description=(
                    f"{key[0]} {key[1]} backhaul radio airtime, half-duplex across "
                    "incident links"
                ),
                link_ids=tuple(link_ids),
            )
        )
    return tuple(domains)


def build_snapshot(
    network: NetworkConfig,
    site_states: Sequence[SiteState],
    uav_positions_m: np.ndarray,
    demand_positions_m: np.ndarray,
    demand_mbps: np.ndarray,
) -> NetworkSnapshot:
    """Assemble everything the scheduler needs for one instant."""

    demands = np.asarray(demand_positions_m, dtype=np.float64).reshape(-1, 3)
    offered = np.asarray(demand_mbps, dtype=np.float64).reshape(-1)
    if offered.shape[0] != demands.shape[0]:
        raise ValueError("demand_mbps length does not match demand_positions_m")
    build = build_links(network, site_states, uav_positions_m, demands)
    paths = enumerate_paths(build, network, demands.shape[0])
    domains = build_resource_domains(build, network)

    gateway_capacity: dict[int, float] = {}
    for site_index, (site, state) in enumerate(zip(network.sites, site_states)):
        if not state.core_link_up:
            continue
        gateway_capacity[site_index] = float(site.core_egress_capacity_mbps) * float(
            state.backhaul_capacity_scale
        )

    nodes: list[Node] = [CORE_NODE]
    nodes.extend(Node(NodeKind.SITE, index) for index in range(len(network.sites)))
    nodes.extend(
        Node(NodeKind.UAV, index)
        for index in range(np.asarray(uav_positions_m).reshape(-1, 3).shape[0])
    )
    nodes.extend(Node(NodeKind.DEMAND, index) for index in range(demands.shape[0]))

    return NetworkSnapshot(
        nodes=tuple(nodes),
        links=build.links,
        resource_domains=domains,
        paths=paths,
        demand_mbps=offered,
        gateway_egress_capacity_mbps=gateway_capacity,
        core_total_egress_mbps=network.core_total_egress_mbps,
    )


def snapshot_from_env_config(
    config: EnvConfig,
    site_states: Sequence[SiteState],
    uav_positions_m: np.ndarray,
    demand_positions_m: np.ndarray,
    demand_mbps: np.ndarray,
) -> NetworkSnapshot:
    """Convenience wrapper that reads the network section of a full configuration."""

    return build_snapshot(
        config.network, site_states, uav_positions_m, demand_positions_m, demand_mbps
    )


def demand_positions_from_xy(xy_m: np.ndarray, altitude_m: float = 0.0) -> np.ndarray:
    """Lift 2-D aggregated demand-point coordinates to 3-D at a fixed altitude."""

    flat = np.asarray(xy_m, dtype=np.float64).reshape(-1, 2)
    out = np.zeros((flat.shape[0], 3), dtype=np.float64)
    out[:, :2] = flat
    out[:, 2] = float(altitude_m)
    return out
