"""The scheduler acceptance cases that must be verifiable by hand.

Each case below is arithmetic a reader can check without running anything, which is the
whole point: the fixed scheduler is the component every control policy is judged through,
so its conservation properties have to be provable rather than plausible.
"""

from __future__ import annotations

import numpy as np
import pytest

from envs.uav_service_restoration import network as net
from envs.uav_service_restoration import scheduler as sched
from envs.uav_service_restoration.config import SchedulerConfig
from envs.uav_service_restoration.types import (
    CandidatePath,
    Link,
    LinkClass,
    NetworkSnapshot,
    Node,
    NodeKind,
    ResourceDomain,
    SchedulerSizeLimitError,
    SchedulerSolveError,
    SchedulerStatus,
    SiteState,
)

CORE = Node(NodeKind.CORE, 0)
SITE0 = Node(NodeKind.SITE, 0)
SITE1 = Node(NodeKind.SITE, 1)
UAV0 = Node(NodeKind.UAV, 0)
UAV1 = Node(NodeKind.UAV, 1)
DEMAND0 = Node(NodeKind.DEMAND, 0)
DEMAND1 = Node(NodeKind.DEMAND, 1)

TOLERANCE = 1e-6


def link(link_id, source, target, link_class, capacity):
    return Link(
        link_id=link_id,
        source=source,
        target=target,
        link_class=link_class,
        capacity_mbps=float(capacity),
        distance_m=0.0,
        snr_db=100.0,
    )


def snapshot(links, paths, demand, domains=(), gateways=None, core_total=None):
    return NetworkSnapshot(
        nodes=(CORE, SITE0, SITE1, UAV0, UAV1, DEMAND0, DEMAND1),
        links=tuple(links),
        resource_domains=tuple(domains),
        paths=tuple(paths),
        demand_mbps=np.asarray(demand, dtype=np.float64),
        gateway_egress_capacity_mbps=dict(gateways or {}),
        core_total_egress_mbps=core_total,
    )


def path(demand_index, link_ids, backhaul_hops=0):
    return CandidatePath(
        demand_index=demand_index,
        node_keys=(("core", 0),),
        link_ids=tuple(link_ids),
        backhaul_hops=backhaul_hops,
    )


@pytest.fixture
def scheduler_config():
    return SchedulerConfig()


# --------------------------------------------------------------------------------------
# Acceptance cases from the specification
# --------------------------------------------------------------------------------------


def test_no_path_to_core_delivers_nothing_however_good_the_access(scheduler_config):
    """High access SNR is worthless without a route to the core."""

    links = [link(0, UAV0, DEMAND0, LinkClass.UAV_ACCESS, 10_000.0)]
    result = sched.solve(snapshot(links, [], [50.0]), scheduler_config)
    assert result.status is SchedulerStatus.TRIVIAL_ZERO
    assert result.delivered_mbps_total == 0.0


def test_two_groups_sharing_a_ten_mbps_bottleneck_get_ten_not_sixteen(scheduler_config):
    """8 + 8 requested through one 10 Mbps edge must deliver 10, not 16."""

    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 10.0),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 1000.0),
        link(2, SITE0, DEMAND1, LinkClass.SITE_ACCESS, 1000.0),
    ]
    paths = [path(0, (0, 1)), path(1, (0, 2))]
    result = sched.solve_or_raise(
        snapshot(links, paths, [8.0, 8.0], gateways={0: 10.0}), scheduler_config
    )
    assert result.delivered_mbps_total == pytest.approx(10.0, abs=TOLERANCE)
    assert result.delivered_mbps_per_demand.sum() == pytest.approx(10.0, abs=TOLERANCE)
    assert result.max_constraint_residual <= TOLERANCE


def test_half_duplex_relay_hop_halves_throughput(scheduler_config):
    """Two equal-capacity hops on one radio cannot both run at full rate.

    ``core -> site0 -> uav0 -> uav1 -> demand0`` with both backhaul hops at 20 Mbps and
    both charged to uav0's radio: ``x/20 + x/20 <= 1`` gives ``x <= 10``.
    """

    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 1000.0),
        link(1, SITE0, UAV0, LinkClass.SITE_UAV_BACKHAUL, 20.0),
        link(2, UAV0, UAV1, LinkClass.UAV_UAV_BACKHAUL, 20.0),
        link(3, UAV1, DEMAND0, LinkClass.UAV_ACCESS, 1000.0),
    ]
    paths = [path(0, (0, 1, 2, 3), backhaul_hops=2)]
    domains = [
        ResourceDomain("backhaul:uav0", "half duplex at the relay", (1, 2)),
        ResourceDomain("backhaul:uav1", "", (2,)),
        ResourceDomain("backhaul:site0", "", (1,)),
        ResourceDomain("access:uav1", "", (3,)),
    ]
    result = sched.solve_or_raise(
        snapshot(links, paths, [100.0], domains=domains), scheduler_config
    )
    assert result.delivered_mbps_total == pytest.approx(10.0, abs=1e-5)
    assert result.domain_utilization["backhaul:uav0"] == pytest.approx(1.0, abs=1e-6)


def test_per_edge_capacity_alone_would_have_allowed_twenty(scheduler_config):
    """Without the conflict domain the same topology would report 20 Mbps.

    This is the error the domain constraints exist to prevent, stated as a test so the
    difference is not a matter of opinion.
    """

    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 1000.0),
        link(1, SITE0, UAV0, LinkClass.SITE_UAV_BACKHAUL, 20.0),
        link(2, UAV0, UAV1, LinkClass.UAV_UAV_BACKHAUL, 20.0),
        link(3, UAV1, DEMAND0, LinkClass.UAV_ACCESS, 1000.0),
    ]
    paths = [path(0, (0, 1, 2, 3), backhaul_hops=2)]
    without_domains = sched.solve_or_raise(
        snapshot(links, paths, [100.0]), scheduler_config
    )
    assert without_domains.delivered_mbps_total == pytest.approx(20.0, abs=1e-5)


def test_two_uavs_serving_one_demand_never_exceed_it(scheduler_config):
    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 1000.0),
        link(1, SITE0, UAV0, LinkClass.SITE_UAV_BACKHAUL, 50.0),
        link(2, SITE0, UAV1, LinkClass.SITE_UAV_BACKHAUL, 50.0),
        link(3, UAV0, DEMAND0, LinkClass.UAV_ACCESS, 50.0),
        link(4, UAV1, DEMAND0, LinkClass.UAV_ACCESS, 50.0),
    ]
    paths = [path(0, (0, 1, 3), 1), path(0, (0, 2, 4), 1)]
    domains = [
        ResourceDomain("backhaul:site0", "site airtime shared over both UAVs", (1, 2)),
        ResourceDomain("access:uav0", "", (3,)),
        ResourceDomain("access:uav1", "", (4,)),
    ]
    result = sched.solve_or_raise(
        snapshot(links, paths, [7.0], domains=domains), scheduler_config
    )
    assert result.delivered_mbps_total <= 7.0 + TOLERANCE
    assert result.delivered_mbps_per_demand[0] <= 7.0 + TOLERANCE
    # Each flow is charged once to the shared site airtime: 7/50 total, not 7/50 twice.
    assert result.domain_utilization["backhaul:site0"] == pytest.approx(7.0 / 50.0, abs=1e-9)


def test_access_node_bandwidth_is_time_shared_not_duplicated(scheduler_config):
    """One access radio serving two demand points cannot give each a full copy."""

    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 1000.0),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 30.0),
        link(2, SITE0, DEMAND1, LinkClass.SITE_ACCESS, 30.0),
    ]
    paths = [path(0, (0, 1)), path(1, (0, 2))]
    domains = [ResourceDomain("access:site0", "site0 airtime", (1, 2))]
    result = sched.solve_or_raise(
        snapshot(links, paths, [30.0, 30.0], domains=domains), scheduler_config
    )
    # x0/30 + x1/30 <= 1  =>  x0 + x1 <= 30, not 60.
    assert result.delivered_mbps_total == pytest.approx(30.0, abs=1e-5)


def test_increasing_capacity_never_reduces_optimal_service(scheduler_config):
    """Monotonicity within the documented epsilon tolerance."""

    totals = []
    for capacity in (1.0, 5.0, 10.0, 25.0, 60.0, 200.0):
        links = [
            link(0, CORE, SITE0, LinkClass.WIRED_CORE, capacity),
            link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 40.0),
            link(2, SITE0, DEMAND1, LinkClass.SITE_ACCESS, 40.0),
        ]
        paths = [path(0, (0, 1)), path(1, (0, 2))]
        domains = [ResourceDomain("access:site0", "", (1, 2))]
        totals.append(
            sched.solve_or_raise(
                snapshot(links, paths, [30.0, 30.0], domains=domains), scheduler_config
            ).delivered_mbps_total
        )
    relative_tolerance = float(scheduler_config.secondary_weight) + 1e-9
    for lower, higher in zip(totals, totals[1:]):
        assert higher >= lower - relative_tolerance * max(lower, 1.0)


def test_expanding_the_path_set_never_reduces_optimal_service(scheduler_config):
    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 20.0),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 12.0),
        link(2, CORE, SITE1, LinkClass.WIRED_CORE, 20.0),
        link(3, SITE1, DEMAND0, LinkClass.SITE_ACCESS, 12.0),
    ]
    one = sched.solve_or_raise(
        snapshot(links, [path(0, (0, 1))], [30.0]), scheduler_config
    ).delivered_mbps_total
    two = sched.solve_or_raise(
        snapshot(links, [path(0, (0, 1)), path(0, (2, 3))], [30.0]), scheduler_config
    ).delivered_mbps_total
    assert two >= one - 1e-9
    assert two == pytest.approx(24.0, abs=1e-5)


def test_all_egress_failed_creates_no_airborne_core(scheduler_config):
    """UAVs alone are not a self-sufficient core network."""

    links = [
        link(0, UAV0, UAV1, LinkClass.UAV_UAV_BACKHAUL, 500.0),
        link(1, UAV1, DEMAND0, LinkClass.UAV_ACCESS, 500.0),
    ]
    result = sched.solve(snapshot(links, [], [40.0]), scheduler_config)
    assert result.delivered_mbps_total == 0.0


def test_core_total_budget_caps_the_sum_over_gateways(scheduler_config):
    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 50.0),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 1000.0),
        link(2, CORE, SITE1, LinkClass.WIRED_CORE, 50.0),
        link(3, SITE1, DEMAND1, LinkClass.SITE_ACCESS, 1000.0),
    ]
    paths = [path(0, (0, 1)), path(1, (2, 3))]
    result = sched.solve_or_raise(
        snapshot(links, paths, [50.0, 50.0], core_total=60.0), scheduler_config
    )
    assert result.delivered_mbps_total == pytest.approx(60.0, abs=1e-5)


# --------------------------------------------------------------------------------------
# Failure reporting and limits
# --------------------------------------------------------------------------------------


def test_repeated_identical_inputs_agree(scheduler_config):
    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 17.5),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 9.25),
        link(2, SITE0, DEMAND1, LinkClass.SITE_ACCESS, 13.75),
    ]
    paths = [path(0, (0, 1)), path(1, (0, 2))]
    domains = [ResourceDomain("access:site0", "", (1, 2))]
    case = snapshot(links, paths, [11.0, 6.0], domains=domains)
    first = sched.solve_or_raise(case, scheduler_config)
    for _ in range(4):
        again = sched.solve_or_raise(case, scheduler_config)
        assert again.delivered_mbps_total == pytest.approx(
            first.delivered_mbps_total, abs=1e-9
        )
        np.testing.assert_allclose(
            again.delivered_mbps_per_demand, first.delivered_mbps_per_demand, atol=1e-9
        )


def test_variable_limit_violation_is_reported_not_truncated():
    config = SchedulerConfig(max_variables=1)
    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 10.0),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 10.0),
        link(2, SITE0, DEMAND1, LinkClass.SITE_ACCESS, 10.0),
    ]
    paths = [path(0, (0, 1)), path(1, (0, 2))]
    with pytest.raises(SchedulerSizeLimitError, match="max_variables"):
        sched.solve(snapshot(links, paths, [5.0, 5.0]), config)


def test_constraint_limit_violation_is_reported_not_truncated():
    config = SchedulerConfig(max_constraints=1)
    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 10.0),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 10.0),
        link(2, SITE0, DEMAND1, LinkClass.SITE_ACCESS, 10.0),
    ]
    paths = [path(0, (0, 1)), path(1, (0, 2))]
    with pytest.raises(SchedulerSizeLimitError, match="max_constraints"):
        sched.solve(snapshot(links, paths, [5.0, 5.0]), config)


def test_negative_demand_is_refused(scheduler_config):
    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 10.0),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 10.0),
    ]
    with pytest.raises(SchedulerSolveError, match="non-negative"):
        sched.solve(snapshot(links, [path(0, (0, 1))], [-1.0]), scheduler_config)


def test_non_finite_demand_is_refused(scheduler_config):
    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 10.0),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 10.0),
    ]
    with pytest.raises(SchedulerSolveError, match="finite"):
        sched.solve(snapshot(links, [path(0, (0, 1))], [np.inf]), scheduler_config)


def test_secondary_rule_removes_pointless_extra_resource_use(scheduler_config):
    """With equal delivery available two ways, the cheaper airtime path is chosen."""

    links = [
        link(0, CORE, SITE0, LinkClass.WIRED_CORE, 1000.0),
        link(1, SITE0, DEMAND0, LinkClass.SITE_ACCESS, 100.0),
        link(2, SITE0, UAV0, LinkClass.SITE_UAV_BACKHAUL, 100.0),
        link(3, UAV0, DEMAND0, LinkClass.UAV_ACCESS, 100.0),
    ]
    direct = path(0, (0, 1))
    relayed = path(0, (0, 2, 3), backhaul_hops=1)
    domains = [
        ResourceDomain("access:site0", "", (1,)),
        ResourceDomain("backhaul:site0", "", (2,)),
        ResourceDomain("backhaul:uav0", "", (2,)),
        ResourceDomain("access:uav0", "", (3,)),
    ]
    case = snapshot(links, [direct, relayed], [40.0], domains=domains)
    result = sched.solve_or_raise(case, scheduler_config)
    assert result.delivered_mbps_total == pytest.approx(40.0, abs=1e-4)
    # The one-wireless-hop direct path costs less normalised airtime than the two-hop
    # relay, so the secondary rule prefers it.
    assert result.path_flows_mbps[0] > result.path_flows_mbps[1]

    neutral = sched.solve_or_raise(case, SchedulerConfig(secondary_rule="none"))
    assert neutral.delivered_mbps_total == pytest.approx(40.0, abs=1e-6)


# --------------------------------------------------------------------------------------
# Topology construction and failure gating
# --------------------------------------------------------------------------------------


def _demand_grid(config):
    xs = np.array([600.0, 1500.0, 2400.0])
    points = np.stack(np.meshgrid(xs, xs, indexing="ij"), axis=-1).reshape(-1, 2)
    return net.demand_positions_from_xy(points, 0.0)


def test_dead_site_stops_serving_access_and_forwarding(smoke_config):
    demands = _demand_grid(smoke_config)
    demand = np.full(demands.shape[0], 10.0)
    uavs = np.array([[1200.0, 1500.0, 120.0]])

    alive = (SiteState(), SiteState())
    dead_west = (
        SiteState(
            radio_up=False,
            core_link_up=False,
            access_capacity_scale=0.0,
            backhaul_capacity_scale=0.0,
        ),
        SiteState(),
    )
    live_snapshot = net.build_snapshot(smoke_config.network, alive, uavs, demands, demand)
    dead_snapshot = net.build_snapshot(smoke_config.network, dead_west, uavs, demands, demand)

    def touches_site(snapshot, index):
        return any(
            link.source.kind is NodeKind.SITE and int(link.source.index) == index
            for link in snapshot.links
        )

    assert touches_site(live_snapshot, 0)
    assert not touches_site(dead_snapshot, 0)


def test_core_link_down_removes_the_gateway_but_not_the_radio(smoke_config):
    demands = _demand_grid(smoke_config)
    demand = np.full(demands.shape[0], 10.0)
    uavs = np.array([[1200.0, 1500.0, 120.0]])
    states = (SiteState(radio_up=True, core_link_up=False), SiteState())
    built = net.build_snapshot(smoke_config.network, states, uavs, demands, demand)
    assert 0 not in built.gateway_egress_capacity_mbps
    assert any(
        link.link_class is LinkClass.SITE_ACCESS and int(link.source.index) == 0
        for link in built.links
    )
    # ...but no path may start at a gateway that has no core link.
    for candidate in built.paths:
        first = built.links[candidate.link_ids[0]]
        assert first.link_class is LinkClass.WIRED_CORE
        assert int(first.target.index) != 0


def test_reverse_uav_backhaul_requires_a_declared_capability(smoke_config, config_doc):
    from envs.uav_service_restoration import config_from_dict

    demands = _demand_grid(smoke_config)
    demand = np.full(demands.shape[0], 10.0)
    uavs = np.array([[1200.0, 1500.0, 120.0]])
    states = (SiteState(), SiteState())

    default = net.build_links(smoke_config.network, states, uavs, demands)
    assert not any(
        link.source.kind is NodeKind.UAV and link.target.kind is NodeKind.SITE
        for link in default.links
    )

    config_doc["network"]["sites"][0]["accepts_uav_wireless_backhaul"] = True
    declared = config_from_dict(config_doc)
    enabled = net.build_links(declared.network, states, uavs, demands)
    assert any(
        link.source.kind is NodeKind.UAV and link.target.kind is NodeKind.SITE
        for link in enabled.links
    )


def test_hop_limit_counts_backhaul_edges_only(smoke_config, config_doc):
    from envs.uav_service_restoration import config_from_dict

    demands = _demand_grid(smoke_config)
    demand = np.full(demands.shape[0], 10.0)
    uavs = np.array(
        [[1000.0, 1500.0, 120.0], [1700.0, 1500.0, 120.0], [2400.0, 1500.0, 120.0]]
    )
    for hops in (0, 1, 2):
        config_doc["network"]["max_backhaul_hops"] = hops
        config = config_from_dict(config_doc)
        built = net.build_snapshot(config.network, (SiteState(), SiteState()), uavs, demands, demand)
        assert all(candidate.backhaul_hops <= hops for candidate in built.paths)
        observed = {candidate.backhaul_hops for candidate in built.paths}
        if hops == 0:
            # Only direct site access survives: no wireless backhaul edge is permitted.
            assert observed <= {0}
        else:
            assert max(observed) == hops


def test_path_count_limit_is_reported_not_truncated(smoke_config, config_doc):
    from envs.uav_service_restoration import config_from_dict

    demands = _demand_grid(smoke_config)
    demand = np.full(demands.shape[0], 10.0)
    uavs = np.array(
        [[1000.0, 1500.0, 120.0], [1700.0, 1500.0, 120.0], [2400.0, 1500.0, 120.0]]
    )
    config_doc["network"]["max_candidate_paths_per_demand"] = 1
    config = config_from_dict(config_doc)
    with pytest.raises(SchedulerSizeLimitError, match="candidate paths"):
        net.build_snapshot(config.network, (SiteState(), SiteState()), uavs, demands, demand)


def test_capacity_scales_apply_to_the_documented_capability(smoke_config):
    demands = _demand_grid(smoke_config)
    demand = np.full(demands.shape[0], 10.0)
    uavs = np.array([[1200.0, 1500.0, 120.0]])

    full = net.build_links(smoke_config.network, (SiteState(), SiteState()), uavs, demands)
    halved_access = net.build_links(
        smoke_config.network,
        (SiteState(access_capacity_scale=0.5), SiteState()),
        uavs,
        demands,
    )
    halved_backhaul = net.build_links(
        smoke_config.network,
        (SiteState(backhaul_capacity_scale=0.5), SiteState()),
        uavs,
        demands,
    )

    def capacity(build, link_class, source_index):
        return sum(
            link.capacity_mbps
            for link in build.links
            if link.link_class is link_class and int(link.source.index) == source_index
        )

    assert capacity(halved_access, LinkClass.SITE_ACCESS, 0) == pytest.approx(
        0.5 * capacity(full, LinkClass.SITE_ACCESS, 0)
    )
    assert capacity(halved_access, LinkClass.SITE_UAV_BACKHAUL, 0) == pytest.approx(
        capacity(full, LinkClass.SITE_UAV_BACKHAUL, 0)
    )
    assert capacity(halved_backhaul, LinkClass.SITE_UAV_BACKHAUL, 0) == pytest.approx(
        0.5 * capacity(full, LinkClass.SITE_UAV_BACKHAUL, 0)
    )
    assert halved_backhaul.links[0].capacity_mbps == pytest.approx(
        0.5 * full.links[0].capacity_mbps
    )


def test_uav_backhaul_domain_holds_incoming_and_outgoing_links(smoke_config):
    demands = _demand_grid(smoke_config)
    uavs = np.array([[1000.0, 1500.0, 120.0], [1700.0, 1500.0, 120.0]])
    built = net.build_links(smoke_config.network, (SiteState(), SiteState()), uavs, demands)
    domains = net.build_resource_domains(built, smoke_config.network)
    by_id = {domain.domain_id: domain for domain in domains}
    uav0 = by_id["backhaul:uav0"]
    incoming = [
        link.link_id
        for link in built.links
        if link.link_class.is_backhaul and link.target.key() == ("uav", 0)
    ]
    outgoing = [
        link.link_id
        for link in built.links
        if link.link_class.is_backhaul and link.source.key() == ("uav", 0)
    ]
    assert incoming and outgoing
    assert set(incoming) | set(outgoing) <= set(uav0.link_ids)


def test_shared_band_merges_access_and_backhaul_domains(smoke_config, config_doc):
    from envs.uav_service_restoration import config_from_dict

    demands = _demand_grid(smoke_config)
    uavs = np.array([[1000.0, 1500.0, 120.0], [1700.0, 1500.0, 120.0]])
    config_doc["network"]["access_and_backhaul_share_band"] = True
    config = config_from_dict(config_doc)
    built = net.build_links(config.network, (SiteState(), SiteState()), uavs, demands)
    domains = net.build_resource_domains(built, config.network)
    assert all(domain.domain_id.startswith("shared:") for domain in domains)
    merged = {domain.domain_id: set(domain.link_ids) for domain in domains}
    uav0 = merged["shared:uav0"]
    assert any(built.links[link_id].link_class.is_access for link_id in uav0)
    assert any(built.links[link_id].link_class.is_backhaul for link_id in uav0)


def test_delivery_never_exceeds_offered_demand_on_random_geometries(smoke_config):
    """Property check over many geometries: conservation is not case specific."""

    generator = np.random.default_rng(4242)
    demands = _demand_grid(smoke_config)
    for _ in range(25):
        uavs = np.column_stack(
            [
                generator.uniform(0.0, 3000.0, size=3),
                generator.uniform(0.0, 3000.0, size=3),
                generator.uniform(90.0, 160.0, size=3),
            ]
        )
        demand = generator.uniform(0.0, 25.0, size=demands.shape[0])
        built = net.build_snapshot(
            smoke_config.network, (SiteState(), SiteState()), uavs, demands, demand
        )
        result = sched.solve_or_raise(built, smoke_config.scheduler)
        assert np.all(result.delivered_mbps_per_demand <= demand + 1e-6)
        assert result.max_constraint_residual <= 1e-6
        for domain_id, utilisation in result.domain_utilization.items():
            assert utilisation <= 1.0 + 1e-6, domain_id
