"""Finite B09 adapter checks. Execute only after DM publication/admission.

COUNTERS includes every attempted adapter/reference constructor and query, even
failures. The module fixture emits one aggregate for the DM's counted check run.
References use independent PUBLIC synthetic state and native scalar calculations;
they never reset/step, copy actor truth, or use the adapter's state installer.
"""

from __future__ import annotations

import json
import random

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b09_service_prediction import model as module


COUNTERS: dict[str, int] = {}


def bump(name):
    COUNTERS[name] = COUNTERS.get(name, 0) + 1


def synthetic(q):
    xyz = np.array([[900, 900, 80], [1300, 900, 100], [1800, 1000, 120],
                    [2400, 1000, 140], [3200, 1400, 160], [4500, 2500, 180],
                    [6000, 4500, 100], [7200, 7000, 150]], dtype=np.float64)
    # All arrays derive from public literals; no native generated users are read.
    i = np.arange(q, dtype=np.float64)
    users = np.column_stack((910 + 7 * i, 905 + 3 * i))
    return xyz, np.full(8, 0.8), users, np.array([500.0, 500.0])


@pytest.fixture(scope="module")
def models(record_testsuite_property):
    COUNTERS.clear()
    first = second = reference = None
    try:
        first = module.LawfulServiceModel(COUNTERS)
        second = module.LawfulServiceModel(COUNTERS)
        bump("model_constructions")
        bump("reference_constructions")
        reference = module.UAVEnergyAwareRelayEnv(config=module.public_model_config(), seed=0)
        # This reference forces native scalar radio/capacity calculations, a
        # separate numerical path from the adapter's native cached batch kernel.
        reference._disable_step_communication_cache = True
        reference._disable_directional_path_loss_cache = True
        reference._disable_routing_link_capacity_cache = True
        reference._disable_sinr_matrix_reuse = True
        yield first, second, reference
    finally:
        for value in (first, second, reference):
            if value is not None:
                value.close()
        counts = json.dumps(COUNTERS, sort_keys=True)
        record_testsuite_property("b09_adapter_counts", counts)
        print("B09 adapter/reference attempted-call totals: " + counts)
        assert COUNTERS.get("model_constructions", 0) <= 12
        assert COUNTERS.get("model_rf_calls", 0) <= 80


def reference_score(raw, xyz, battery, users, bs):
    """Independent minimal shape installation and original native pipeline."""
    bump("model_score_calls")
    bump("reference_score_calls")
    q = len(users)
    raw.n_users = q
    raw.uav_positions = np.array(xyz, dtype=np.float64, copy=True)
    raw.uav_battery_ratios = np.array(battery, dtype=np.float64, copy=True)
    raw.uav_failed = np.zeros(8, dtype=bool)
    raw.user_positions = np.empty((q, 3), dtype=np.float64)
    raw.user_positions[:, :2] = users
    raw.user_positions[:, 2] = 1.5
    raw.ground_bs_positions = np.array([[*bs, 30.0]], dtype=np.float64)
    raw.sinr_matrix = np.zeros((8, q))
    raw.connections = np.zeros((8, q), dtype=bool)
    raw.uav_connections = np.zeros((8, 8), dtype=bool)
    raw.uav_bs_connections = np.zeros((8, 1), dtype=bool)
    raw.user_serving_sets = [[] for _ in range(q)]
    raw.user_serving_uav = np.full(q, -1, dtype=int)
    raw.user_handover_history = [[] for _ in range(q)]
    raw.serving_set_changes = raw.uav_joins_count = raw.uav_leaves_count = 0
    raw.current_step = 0
    raw.routing_paths = {}
    raw._relay_geometry_state = raw._step_communication_cache = None
    raw._channel_update_cache_active = False
    for name in ("_sinr_uav_positions", "_sinr_user_positions", "_sinr_unavailable",
                 "_routing_link_capacity_cache"):
        raw.__dict__.pop(name, None)
    if not q:
        return np.zeros(0), np.zeros((8, 0)), np.zeros(8)
    bump("model_rf_calls")
    bump("reference_rf_calls")
    raw._update_channel_state()
    raw._update_uav_connections()
    raw._compute_routing_paths()
    return raw._calculate_end_to_end_user_rates()


@pytest.mark.parametrize("q", [0, 1, 2, 5, 6, 29, 30])
def test_sparse_native_reference_and_public_denominator(models, q):
    adapter, _, reference = models
    state = synthetic(q)
    before = COUNTERS.get("model_rf_calls", 0)
    result = adapter.score(*state)
    assert COUNTERS.get("model_rf_calls", 0) == before + int(q > 0)
    raw = adapter.raw
    rates, access, backhaul = reference_score(reference, *state)
    delivered = np.minimum(rates, 1e6)
    np.testing.assert_allclose(result["delivered_bps"], delivered, rtol=1e-12, atol=1e-7)
    assert result["delivered_bps"].dtype == np.float64
    assert result["delivered_bps"].shape == (q,)
    assert result["qos"] == float(np.clip(result["delivered_bps"] / 1e6, 0, 1).sum() / 30)
    assert 0 <= result["qos"] <= q / 30
    assert len(result["digest"]) == 64
    assert raw.n_users == q
    for name in ("sinr_matrix", "connections", "last_access_capacity_bps"):
        assert getattr(raw, name).shape == (8, q)
    for name in ("user_serving_uav", "last_user_demand_bps", "last_delivered_traffic_bps",
                 "last_user_rates_mbps", "user_pause_times"):
        assert getattr(raw, name).shape == (q,)
    for name in ("user_serving_sets", "user_handover_history"):
        assert len(getattr(raw, name)) == q
    np.testing.assert_array_equal(raw.user_positions[:, 2], np.full(q, 1.5))
    np.testing.assert_array_equal(raw.ground_bs_positions[:, 2], [30.0])
    np.testing.assert_allclose(raw.last_access_capacity_bps, access, rtol=1e-12, atol=1e-7)
    np.testing.assert_allclose(raw.last_backhaul_capacities_bps, backhaul, rtol=1e-12, atol=1e-7)
    if q:
        np.testing.assert_allclose(raw.sinr_matrix, reference.sinr_matrix, rtol=1e-12, atol=1e-10)
        np.testing.assert_array_equal(raw.connections, reference.connections)
        np.testing.assert_array_equal(raw.uav_connections, reference.uav_connections)
        np.testing.assert_array_equal(raw.uav_bs_connections, reference.uav_bs_connections)
        assert raw.user_serving_sets == reference.user_serving_sets
        assert raw.routing_paths == reference.routing_paths
        # Explicit native MAX delivery and per-UAV equal bandwidth allocation.
        per_uav = np.zeros_like(access)
        for i in range(8):
            total = access[i].sum()
            if total > 0:
                per_uav[i] = access[i] * min(1, backhaul[i] / total)
            connected = np.flatnonzero(raw.connections[i])
            if len(connected):
                bandwidth = raw.bandwidth / 8 / len(connected)
                for j in connected:
                    expected = bandwidth * raw._get_spectral_efficiency_from_sinr(raw.sinr_matrix[i, j])
                    assert access[i, j] == expected
        np.testing.assert_allclose(rates, per_uav.max(axis=0), rtol=1e-12, atol=1e-7)
        assert np.any(delivered > 0), "public synthetic fixture must exercise real delivery"
    else:
        assert result["qos"] == 0
        assert raw.routing_paths == {}
        assert raw._step_communication_cache is None
        assert raw._relay_geometry_state is None


def test_alternating_cardinality_and_query_order(models):
    adapter, clean, _ = models
    states = [synthetic(q) for q in (30, 0, 1, 29, 2, 6, 5)]
    expected = {len(s[2]): clean.score(*s) for s in reversed(states)}
    for state in states + states[:1]:
        result = adapter.score(*state)
        old = expected[len(state[2])]
        assert result["digest"] == old["digest"]
        np.testing.assert_array_equal(result["delivered_bps"], old["delivered_bps"])


def test_track_order_and_result_copy(models):
    adapter, _, _ = models
    xyz, battery, users, bs = synthetic(6)
    result = adapter.score(xyz, battery, users, bs)
    order = np.array([3, 0, 5, 1, 4, 2])
    reordered = adapter.score(xyz, battery, users[order], bs)
    np.testing.assert_array_equal(reordered["delivered_bps"], result["delivered_bps"][order])
    result["delivered_bps"].fill(-99)
    assert (adapter.raw.last_delivered_traffic_bps >= 0).all()
    users.fill(-99)
    xyz.fill(-99)
    battery.fill(-99)
    bs.fill(-99)
    assert (adapter.raw.user_positions >= 0).all()
    assert (adapter.raw.uav_positions >= 0).all()
    assert (adapter.raw.uav_battery_ratios >= 0).all()
    assert (adapter.raw.ground_bs_positions >= 0).all()


def same_random_state(left, right):
    assert left[0] == right[0]
    np.testing.assert_array_equal(left[1], right[1])
    assert left[2:] == right[2:]


def test_poisoned_placeholder_history_caches_and_rng(models):
    adapter, _, _ = models
    state = synthetic(5)
    expected = adapter.score(*state)
    raw = adapter.raw
    raw.user_positions = np.full((30, 3), np.nan)
    raw.ground_bs_positions.fill(np.nan)
    raw.uav_positions.fill(np.nan)
    raw.charging_station_positions.fill(np.nan)
    raw.cluster_centers_history.fill(np.nan)
    raw.cluster_velocities.fill(np.nan)
    raw.cluster_waypoints.fill(np.nan)
    raw.user_serving_sets = [[999]] * 30
    raw.user_handover_history = [[(999, 999, 999)]] * 30
    raw.user_serving_uav = np.full(30, 999)
    raw.connections = np.ones((8, 30), dtype=bool)
    raw.uav_failed.fill(True)
    raw.current_step = 999
    raw.routing_paths = {0: ([("fake", 999)], float("nan"))}
    raw._relay_geometry_state = {"poison": True}
    raw._step_communication_cache = {"poison": True}
    raw._channel_update_cache_active = True
    raw._routing_link_capacity_cache = {"poison": True}
    raw._sinr_uav_positions = state[0].copy()
    raw._sinr_user_positions = np.column_stack((state[2], np.full(5, 1.5)))
    raw._sinr_unavailable = np.zeros(8, dtype=bool)
    raw.sinr_matrix = np.full((8, 5), np.nan)
    raw._noise_power_linear_cache = (float(raw.noise_power), float("nan"))
    raw._interference_radius_cache = ((float(raw.tx_power), float(raw.noise_power),
                                     float(raw.carrier_frequency)), float("nan"))
    raw.np_random = np.random.RandomState(0)
    raw.np_random.uniform(size=17)  # Independent public RNG poison, no new world seed.
    private_before = raw.np_random.get_state()
    numpy_before = np.random.get_state()
    python_before = random.getstate()
    result = adapter.score(*state)
    assert result["digest"] == expected["digest"]
    same_random_state(private_before, raw.np_random.get_state())
    same_random_state(numpy_before, np.random.get_state())
    assert python_before == random.getstate()


def test_native_cutoff_charging_neutral_and_all_eight_interferers(models):
    adapter, _, _ = models
    state = synthetic(2)
    base = adapter.score(*state)
    raw = adapter.raw
    # Prior F/charging/dock fields are deliberately outside service availability.
    raw.uav_dock_requests.fill(True)
    raw.uav_charging.fill(True)
    assert adapter.score(*state)["digest"] == base["digest"]
    xyz, battery, users, bs = state
    battery = np.array([0.02, np.nextafter(0.02, 1), 0.0, 0.03, 0.8, 0.8, 0.8, 0.8])
    adapter.score(xyz, battery, users, bs)
    np.testing.assert_array_equal(raw._communication_unavailable_mask(),
                                  [True, False, True, False, False, False, False, False])
    assert not raw.connections[[0, 2]].any()
    assert not raw.uav_connections[[0, 2]].any()
    assert not raw.uav_bs_connections[[0, 2]].any()
    assert 0 not in raw.routing_paths and 2 not in raw.routing_paths
    assert raw._step_communication_cache["radio"].access_sinr.shape == (1, 8, 2)
    # Availability changes masks, never raw RF interference participation.
    original_radio = raw._step_communication_cache["radio"].access_sinr.copy()
    adapter.score(xyz, np.full(8, 0.8), users, bs)
    np.testing.assert_array_equal(raw._step_communication_cache["radio"].access_sinr, original_radio)


def test_native_directed_route_does_not_require_bidirectional_masks(models, monkeypatch):
    adapter, _, _ = models
    capacities = {("uav", 0, "uav", 1): 3e6,
                  ("uav", 1, "ground_bs", 0): 2e6}
    monkeypatch.setattr(adapter.raw, "_get_link_capacity",
                        lambda *edge: capacities.get(edge, 0.0))
    monkeypatch.setattr(adapter.raw, "_compute_uav_to_uav_sinr", lambda *pair: -np.inf)
    adapter.score(*synthetic(1))
    assert not adapter.raw.uav_connections.any()
    assert not adapter.raw.uav_bs_connections.any()
    assert adapter.raw.routing_paths[0] == (
        [("uav", 0), ("uav", 1), ("ground_bs", 0)], 2e6)


def test_digest_covers_native_outputs_and_stable_route_order(models):
    adapter, _, _ = models
    adapter.score(*synthetic(2))
    raw = adapter.raw
    base = module.native_output_digest(raw)
    raw.routing_paths = dict(reversed(list(raw.routing_paths.items())))
    assert module.native_output_digest(raw) == base
    raw.sinr_matrix[0, 0] += 1
    assert module.native_output_digest(raw) != base
    raw.sinr_matrix[0, 0] -= 1
    base = module.native_output_digest(raw)
    raw.last_access_capacity_bps = raw.last_access_capacity_bps.astype(np.float32)
    assert module.native_output_digest(raw) != base


def test_attempts_are_counted_before_validation_and_failure(models, monkeypatch):
    adapter, _, _ = models
    xyz, battery, users, bs = synthetic(2)
    before_scores = COUNTERS["model_score_calls"]
    before_rf = COUNTERS["model_rf_calls"]
    for args in ((xyz[:7], battery, users, bs), (xyz, battery, np.zeros((31, 2)), bs),
                 (xyz, battery, users, [np.nan, 0]), (xyz, battery, np.zeros(2), bs)):
        with pytest.raises(ValueError):
            adapter.score(*args)
    assert COUNTERS["model_score_calls"] == before_scores + 4
    assert COUNTERS["model_rf_calls"] == before_rf

    def fail():
        raise RuntimeError("counted synthetic pipeline failure")

    monkeypatch.setattr(adapter.raw, "_update_channel_state", fail)
    with pytest.raises(RuntimeError, match="counted synthetic"):
        adapter.score(xyz, battery, users, bs)
    assert COUNTERS["model_rf_calls"] == before_rf + 1
    before_constructions = COUNTERS["model_constructions"]

    def fail_constructor(**kwargs):
        assert COUNTERS["model_constructions"] == before_constructions + 1
        raise RuntimeError("counted synthetic constructor failure")

    monkeypatch.setattr(module, "UAVEnergyAwareRelayEnv", fail_constructor)
    bump("mock_constructor_attempts")
    with pytest.raises(RuntimeError, match="constructor failure"):
        module.LawfulServiceModel(COUNTERS)
    assert COUNTERS["model_constructions"] == before_constructions + 1
