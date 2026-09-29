from dataclasses import replace
import json

import numpy as np
import pytest

from configs.config_1 import Config
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from experiments.candidates.uav_availability_recovery.predictor import (
    PublicPredictor,
    PublicSnapshot,
    _PublicServiceEnv,
    _project_positions,
    active_probability,
    truncated_horizons,
)


def public_snapshot(*, step=495, age=20, returned=False):
    config = Config("S7-S1")
    positions = np.array(
        [[3700 + 80 * i, 3700 + 40 * (i % 3), 50] for i in range(8)], dtype=float
    )
    active = np.ones(8, dtype=bool)
    if not returned:
        active[2] = False
    user_xy = np.array(
        [[3700 + 35 * (i % 10), 3800 + 25 * (i // 10)] for i in range(30)],
        dtype=np.float64,
    )
    targets = np.broadcast_to(positions, (16, 8, 3)).copy()
    for action in range(16):
        targets[action, 6, 0] += (action // 4) * 50
        targets[action, 7, 1] += (action % 4) * 50
    return PublicSnapshot(
        positions=positions,
        active=active,
        user_xy=user_xy,
        demand_mbps=np.ones(30),
        base_xy=np.array([4000.0, 4000.0]),
        candidate_targets=targets,
        incumbent_action=0,
        physical_step=step,
        absence_age=age,
        event_owner_index=2,
        has_returned=returned,
        max_speed=float(config.max_speed),
        max_vertical_speed_mps=float(config.max_vertical_speed_mps),
        time_step=float(config.time_step),
        area_size=float(config.area_size),
        height_range=tuple(config.height_range),
    )


@pytest.mark.parametrize(
    ("step", "expected_horizons", "expected_weights"),
    [
        (499, (1,), (1,)),
        (495, (5,), (5,)),
        (475, (10, 25), (10, 15)),
        (455, (10, 40, 45), (10, 30, 5)),
        (380, (10, 40, 80, 120), (10, 30, 40, 40)),
    ],
)
def test_truncated_intervals(step, expected_horizons, expected_weights):
    assert truncated_horizons(step) == (expected_horizons, expected_weights)


def test_conditional_duration_support_and_return():
    assert active_probability(0, 79, False) == 0
    assert active_probability(0, 80, False) == pytest.approx(1 / 21)
    assert active_probability(80, 0, False) == 0
    assert active_probability(80, 1, False) == pytest.approx(1 / 20)
    assert active_probability(99, 0, False) == 0
    assert active_probability(99, 1, False) == 1
    assert active_probability(20, 0, True) == 1


def test_public_copy_float32_and_native_speed_projection():
    snapshot = public_snapshot()
    assert snapshot.user_xy.dtype == np.float32
    assert not snapshot.user_xy.flags.writeable
    original = snapshot.positions.copy()
    targets = snapshot.candidate_targets[15].copy()
    targets[6, :2] += [100.0, 100.0]
    projected = _project_positions(snapshot, targets, 1, snapshot.active)
    action_xy = np.clip((targets[6, :2] - original[6, :2]) / snapshot.max_speed, -1, 1)
    expected = action_xy / np.linalg.norm(action_xy) * snapshot.max_speed
    np.testing.assert_allclose(projected[6, :2] - original[6, :2], expected)
    np.testing.assert_array_equal(projected[2], original[2])
    np.testing.assert_array_equal(snapshot.positions, original)


def test_nominal_projection_respects_native_near_zero_stop():
    snapshot = public_snapshot()
    targets = snapshot.positions.copy()
    targets[6, 0] += snapshot.max_speed * 0.5e-8
    projected = _project_positions(snapshot, targets, 40, snapshot.active)
    np.testing.assert_array_equal(projected, snapshot.positions)


def test_native_service_at_public_geometry_and_mask():
    snapshot = public_snapshot()
    env = _PublicServiceEnv()
    observed = env.snapshot_qos(snapshot, snapshot.positions, snapshot.active)

    # Independently materialize the same public geometry in an ordinary S7-S1 env.
    native = UAVEnergyAwareRelayEnv(config=Config("S7-S1"), seed=17)
    native.uav_positions = snapshot.positions.copy()
    native.user_positions = np.column_stack((snapshot.user_xy.astype(float), np.full(30, 1.5)))
    native.ground_bs_positions = np.array([[*snapshot.base_xy, 30.0]])
    native.uav_failed = ~snapshot.active.copy()
    native.connections.fill(False)
    native.sinr_matrix = np.zeros((8, 30))
    native.uav_connections = np.zeros((8, 8), dtype=bool)
    native.uav_bs_connections = np.zeros((8, 1), dtype=bool)
    native.user_serving_uav.fill(-1)
    native.user_serving_sets = [[] for _ in range(30)]
    native.routing_paths = {}
    native._step_communication_cache = None
    native._relay_geometry_state = None
    native._update_channel_state()
    native._update_uav_connections()
    native._compute_routing_paths()
    rates, _, _ = native._calculate_end_to_end_user_rates()
    expected = np.mean(np.minimum(rates / (snapshot.demand_mbps * 1e6), 1.0))
    assert observed == pytest.approx(expected, abs=1e-12)
    assert not np.any(env.connections[2])
    assert not np.any(env.uav_connections[2])


def test_all_candidates_counts_and_state_isolation():
    snapshot = public_snapshot()
    original_positions = snapshot.positions.copy()
    original_map = snapshot.user_xy.copy()
    planner = PublicPredictor()
    decision = planner.score(snapshot)
    assert decision.predictions.shape == (16, 1)
    assert decision.snapshot_calls == 16
    assert 0 <= decision.action < 16
    assert decision.to_dict()["snapshot_calls"] == 16
    assert decision.to_dict()["weights"] == [5]
    json.dumps(decision.to_dict(), allow_nan=False)
    np.testing.assert_array_equal(snapshot.positions, original_positions)
    np.testing.assert_array_equal(snapshot.user_xy, original_map)

    # At a mixed posterior, every candidate uses both declared branches.
    second = planner.score(replace(snapshot, physical_step=450, absence_age=79))
    assert second.snapshot_calls > decision.snapshot_calls
    assert second.predictions.shape == (16, 3)
    assert len(second.active_probabilities) == 3


def test_tie_order_incumbent_then_reserve_travel_then_index(monkeypatch):
    snapshot = public_snapshot()
    values = np.zeros(16)
    values[[1, 2, 3]] = 0.5
    called = 0

    def fixed_service(self, public, positions, active):
        nonlocal called
        result = float(values[called % 16])
        called += 1
        return result

    monkeypatch.setattr(_PublicServiceEnv, "snapshot_qos", fixed_service)
    incumbent = PublicPredictor().score(replace(snapshot, incumbent_action=2))
    assert incumbent.action == 2
    assert incumbent.snapshot_calls == 16
    called = 0
    # Candidate 1 has 50 m travel, candidate 2 has 100 m, candidate 3 has 150 m.
    ordinary = PublicPredictor().score(replace(snapshot, incumbent_action=0))
    assert ordinary.action == 1
    called = 0
    values[2] = 0.5 + 0.5e-10
    within_tolerance = PublicPredictor().score(replace(snapshot, incumbent_action=1))
    assert within_tolerance.action == 1
    called = 0
    values[2] = 0.5
    same_travel_targets = snapshot.candidate_targets.copy()
    same_travel_targets[2] = same_travel_targets[1]
    by_index = PublicPredictor().score(
        replace(snapshot, candidate_targets=same_travel_targets, incumbent_action=0)
    )
    assert by_index.action == 1


def test_snapshot_scoring_does_not_advance_native_rng():
    snapshot = public_snapshot()
    env = _PublicServiceEnv()
    before = env.np_random.get_state()
    env.snapshot_qos(snapshot, snapshot.positions, snapshot.active)
    after = env.np_random.get_state()
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_native_unavailability_masks_service_but_retains_geometric_interference():
    snapshot = public_snapshot()
    env = _PublicServiceEnv()
    env.snapshot_qos(snapshot, snapshot.positions, snapshot.active)
    unavailable_sinr = env.sinr_matrix.copy()
    _, unavailable_access, _ = env._calculate_end_to_end_user_rates()
    env.snapshot_qos(snapshot, snapshot.positions, np.ones(8, dtype=bool))
    active_rows = np.arange(8) != 2
    np.testing.assert_array_equal(unavailable_sinr[active_rows], env.sinr_matrix[active_rows])
    assert np.all(unavailable_access[2] == 0)


def test_no_hidden_state_or_live_environment_payload():
    snapshot = public_snapshot()
    assert set(vars(snapshot)) == {
        "positions", "active", "user_xy", "demand_mbps", "base_xy",
        "candidate_targets", "incumbent_action", "physical_step", "absence_age",
        "event_owner_index", "has_returned", "max_speed", "max_vertical_speed_mps",
        "time_step", "area_size", "height_range",
    }
    with pytest.raises(TypeError):
        PublicPredictor(source=object())
