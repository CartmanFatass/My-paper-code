"""Masks, identity ordering, padding, entity limits and the declared layout."""

from __future__ import annotations

import numpy as np
import pytest

from envs.uav_service_restoration import UAVServiceRestorationEnv, config_from_dict
from envs.uav_service_restoration.demand import SyntheticFixtureDemandSource
from envs.uav_service_restoration.observations import (
    DEMAND_FEATURES,
    PEER_FEATURES,
    SELF_FEATURES,
    SITE_FEATURES,
    DemandPointLayout,
    EntityLimitExceeded,
    ObservationBuilder,
    capacity_feature,
)


# --------------------------------------------------------------------------------------
# Demand-point layout
# --------------------------------------------------------------------------------------


def test_layout_is_identity_when_within_the_limit():
    positions = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0]])
    layout = DemandPointLayout.build(positions, 8, "error")
    assert not layout.aggregated
    assert layout.n_slots == 3
    np.testing.assert_array_equal(layout.group_of_cell, [0, 1, 2])
    np.testing.assert_allclose(layout.aggregate_demand(np.array([1.0, 2.0, 3.0])), [1.0, 2.0, 3.0])


def test_entity_limit_errors_rather_than_dropping_points():
    positions = np.column_stack([np.arange(10.0), np.zeros(10)])
    with pytest.raises(EntityLimitExceeded, match="never dropped"):
        DemandPointLayout.build(positions, 4, "error")


def test_aggregation_conserves_total_demand_exactly():
    positions = np.column_stack([np.arange(12.0), np.zeros(12)])
    layout = DemandPointLayout.build(positions, 4, "aggregate")
    assert layout.aggregated
    assert layout.n_slots == 4
    assert layout.group_sizes.sum() == 12
    demand = np.arange(1.0, 13.0)
    aggregated = layout.aggregate_demand(demand)
    assert aggregated.sum() == pytest.approx(demand.sum(), abs=0.0)
    # The hardest point is folded into a group, never discarded.
    assert aggregated.max() >= demand.max()


def test_aggregated_slot_is_observed_only_if_every_member_is():
    positions = np.column_stack([np.arange(6.0), np.zeros(6)])
    layout = DemandPointLayout.build(positions, 3, "aggregate")
    mask = np.array([True, True, True, False, True, True])
    aggregated = layout.aggregate_mask(mask)
    assert aggregated.tolist() == [True, False, True]


def test_aggregation_positions_are_fixed_group_centroids():
    positions = np.column_stack([np.arange(6.0) * 100.0, np.zeros(6)])
    layout = DemandPointLayout.build(positions, 3, "aggregate")
    np.testing.assert_allclose(layout.positions_m[:, 0], [50.0, 250.0, 450.0])
    # Identity does not drift between calls.
    again = DemandPointLayout.build(positions, 3, "aggregate")
    np.testing.assert_array_equal(layout.positions_m, again.positions_m)


def test_env_honours_the_aggregate_policy(config_doc):
    config_doc["source"]["max_demand_points"] = 4
    config_doc["observations"]["on_entity_limit_exceeded"] = "error"
    with pytest.raises(EntityLimitExceeded):
        UAVServiceRestorationEnv(config_from_dict(config_doc))

    config_doc["observations"]["on_entity_limit_exceeded"] = "aggregate"
    config_doc["episode"]["duration_s"] = 20.0
    env = UAVServiceRestorationEnv(config_from_dict(config_doc))
    assert env.demand_layout.aggregated
    assert env.demand_layout.n_slots == 4
    env.reset(seed=1)
    env.step({agent: np.zeros(3, dtype=np.float32) for agent in env.agents})
    summary = env.episode_summary()
    # Nine source cells folded into four slots, with total offered demand preserved.
    assert len(summary["offered_mbit_per_point"]) == 4
    assert summary["offered_mbit_total"] > 0.0


# --------------------------------------------------------------------------------------
# Feature encoding
# --------------------------------------------------------------------------------------


def test_capacity_feature_is_monotone_and_zero_at_zero():
    assert float(capacity_feature(0.0)) == 0.0
    values = capacity_feature(np.array([0.0, 1.0, 10.0, 100.0, 1000.0]))
    assert np.all(np.diff(values) > 0.0)


def test_declared_widths_match_the_emitted_vector(smoke_config):
    layout = DemandPointLayout.build(
        SyntheticFixtureDemandSource(smoke_config.source).cell_positions_m(),
        smoke_config.source.max_demand_points,
        smoke_config.observations.on_entity_limit_exceeded,
    )
    builder = ObservationBuilder(smoke_config, layout)
    schema = builder.schema()
    assert sum(block["width"] for block in schema["obs_blocks"]) == builder.obs_dim
    assert sum(block["width"] for block in schema["state_blocks"]) == builder.state_dim
    assert schema["obs_dim"] == builder.obs_dim


def decode(observation, config, layout):
    n_uavs = int(config.n_uavs)
    n_sites = len(config.network.sites)
    slots = max(int(config.source.max_demand_points), layout.n_slots)
    cursor = 0

    def take(width):
        nonlocal cursor
        chunk = observation[cursor : cursor + width]
        cursor += width
        return chunk

    own = take(SELF_FEATURES)
    peers = take(PEER_FEATURES * (n_uavs - 1)).reshape(n_uavs - 1, PEER_FEATURES)
    sites = take(SITE_FEATURES * n_sites).reshape(n_sites, SITE_FEATURES)
    demand = take(DEMAND_FEATURES * slots).reshape(slots, DEMAND_FEATURES)
    return {"own": own, "peers": peers, "sites": sites, "demand": demand, "cursor": cursor}


def test_padding_slots_are_flagged_separately_from_true_zeros(config_doc):
    config_doc["source"]["max_demand_points"] = 16  # nine real cells, seven padding slots
    config_doc["episode"]["duration_s"] = 20.0
    config = config_from_dict(config_doc)
    env = UAVServiceRestorationEnv(config)
    observations, _ = env.reset(seed=2)
    parsed = decode(observations["uav_0"], config, env.demand_layout)
    real = env.demand_layout.n_slots
    assert real == 9
    # slot_valid_mask is the last demand feature.
    assert np.all(parsed["demand"][:real, 6] == 1.0)
    assert np.all(parsed["demand"][real:, 6] == 0.0)
    # Padding rows are entirely zero, and are distinguishable from a real zero-demand
    # slot, which still carries slot_valid_mask == 1.
    assert np.all(parsed["demand"][real:, :] == 0.0)


def test_demand_slot_identity_does_not_re_sort_with_distance(config_doc):
    config_doc["episode"]["duration_s"] = 100.0
    config = config_from_dict(config_doc)
    env = UAVServiceRestorationEnv(config)
    observations, _ = env.reset(seed=6)
    layout = env.demand_layout
    fixed_positions = layout.positions_m.copy()

    generator = np.random.default_rng(5)
    while env.agents:
        parsed = decode(observations["uav_0"], config, layout)
        own_xy = env.uav_positions_m[0, :2]
        scale = float(config.observations.position_reference_m)
        for slot in range(layout.n_slots):
            expected = (fixed_positions[slot] - own_xy) / scale
            np.testing.assert_allclose(
                parsed["demand"][slot, :2], expected, atol=1e-5
            )
        observations, _, _, _, _ = env.step(
            {
                agent: generator.uniform(-1, 1, 3).astype(np.float32)
                for agent in env.agents
            }
        )


def test_own_pose_is_current_and_peers_carry_age_and_mask(config_doc):
    config_doc["episode"]["duration_s"] = 60.0
    config = config_from_dict(config_doc)
    env = UAVServiceRestorationEnv(config)
    observations, _ = env.reset(seed=4)
    parsed = decode(observations["uav_0"], config, env.demand_layout)
    scale = float(config.observations.position_reference_m)
    low, high = config.dynamics.altitude_range_m
    expected = env.uav_positions_m[0].copy()
    np.testing.assert_allclose(parsed["own"][0], expected[0] / scale, atol=1e-6)
    np.testing.assert_allclose(parsed["own"][1], expected[1] / scale, atol=1e-6)
    np.testing.assert_allclose(
        parsed["own"][2], (expected[2] - low) / (high - low), atol=1e-6
    )
    # Peer rows: three relative-position entries, then age, then mask.
    assert parsed["peers"].shape == (config.n_uavs - 1, PEER_FEATURES)
    assert set(np.unique(parsed["peers"][:, 4])) <= {0.0, 1.0}


def test_site_capability_reaches_the_observation_after_a_failure(config_doc):
    config_doc["episode"]["duration_s"] = 300.0
    config = config_from_dict(config_doc)
    env = UAVServiceRestorationEnv(config)
    observations, _ = env.reset(seed=9)
    failing_site = int(config.events.events[0].site_index)
    radio_up_history = []
    while env.agents:
        parsed = decode(observations["uav_0"], config, env.demand_layout)
        radio_up_history.append((env.physical_time_s, float(parsed["sites"][failing_site, 2])))
        observations, _, _, _, _ = env.step(
            {agent: np.zeros(3, dtype=np.float32) for agent in env.agents}
        )
    before = [value for time_s, value in radio_up_history if time_s < 120.0]
    after = [value for time_s, value in radio_up_history if time_s > 150.0]
    assert all(value == 1.0 for value in before)
    assert all(value == 0.0 for value in after)


def test_state_carries_no_more_entities_than_declared(short_config):
    env = UAVServiceRestorationEnv(short_config)
    env.reset(seed=1)
    state = env.state()
    assert state.shape == (env.get_state_dim(),)
    assert np.isfinite(state).all()


def test_ideal_demand_diagnostic_reveals_everything_and_is_named(config_doc):
    config_doc["episode"]["duration_s"] = 600.0
    config_doc["deployment"]["positions_m"] = [
        [200.0, 1500.0, 120.0],
        [200.0, 1000.0, 120.0],
        [200.0, 2000.0, 120.0],
    ]
    config_doc["observations"]["mode"] = "ideal_full_current_demand"
    config_doc["notes"] = "diagnostic condition: upper bound with full demand knowledge"
    config = config_from_dict(config_doc)
    env = UAVServiceRestorationEnv(config)
    observations, _ = env.reset(seed=404)
    for _ in range(35):
        if not env.agents:
            break
        observations, _, _, _, _ = env.step(
            {agent: np.zeros(3, dtype=np.float32) for agent in env.agents}
        )
    parsed = decode(observations["uav_0"], config, env.demand_layout)
    real = env.demand_layout.n_slots
    # Under the diagnostic condition every real slot is observed, including the east.
    assert np.all(parsed["demand"][:real, 5] == 1.0)
    assert env.schema()["information_condition"]["mode"] == "ideal_full_current_demand"


def test_observation_and_state_are_finite_over_a_full_episode(config_doc):
    config_doc["episode"]["duration_s"] = 300.0
    config = config_from_dict(config_doc)
    env = UAVServiceRestorationEnv(config)
    observations, _ = env.reset(seed=31)
    generator = np.random.default_rng(31)
    while env.agents:
        for observation in observations.values():
            assert np.isfinite(observation).all()
            assert observation.dtype == np.float32
        assert np.isfinite(env.state()).all()
        observations, _, _, _, _ = env.step(
            {
                agent: generator.uniform(-1, 1, 3).astype(np.float32)
                for agent in env.agents
            }
        )
