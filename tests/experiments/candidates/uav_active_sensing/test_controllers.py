from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_active_sensing.controllers import (
    FEATURE_DIM,
    N_ACTIONS,
    SensingController,
    SURVEY_XY,
    WAYPOINTS_XY,
)
from experiments.candidates.uav_information_value.controllers import make_controller


OWN_XY = [(700.0 + 330.0 * i, 900.0 + 190.0 * i) for i in range(8)]
USERS_XY = [(1000.0 + 850.0 * i, 5000.0 - 240.0 * i) for i in range(8)]


def observations(users=USERS_XY, bs=(700.0, 750.0), own=OWN_XY,
                 margins=None, available=None):
    layout = S7S2_LAYOUT
    obs = np.zeros((8, layout.dim), dtype=np.float32)
    margins = np.full(8, .8) if margins is None else np.asarray(margins)
    available = np.ones(8, dtype=bool) if available is None else np.asarray(available)
    for uav in range(8):
        obs[uav, :2] = np.asarray(own[uav]) / 8000.0
        obs[uav, 2] = (100.0 - 50.0) / 150.0
        decoded = obs[uav, :2].astype(np.float64) * 8000.0
        for slot, user in enumerate(users):
            start = layout.users.start + layout.user_fields * slot
            obs[uav, start:start + 2] = (np.asarray(user) - decoded) / 8000.0
            obs[uav, start + 4] = 1.0
        if bs is not None:
            obs[uav, layout.bs.start:layout.bs.start + 2] = (np.asarray(bs) - decoded) / 8000.0
            obs[uav, layout.bs.start + 3] = 1.0
        station = layout.energy_stations.start + layout.energy_station_fields
        obs[uav, station:station + 2] = (np.asarray((6100.0, 6200.0)) - decoded) / 8000.0
        obs[uav, station + 7] = 1.0
        energy = layout.energy_uavs.start + (uav * layout.energy_uav_fields)
        obs[uav, energy + 5] = float(available[uav])
        obs[uav, energy + 12] = margins[uav]
    return obs


def test_h_matches_h_bs_including_midstep_bs_memory_and_replans():
    actual = SensingController("H")
    reference = make_controller("H_BS")
    absent = observations(users=USERS_XY[:2], bs=None)
    present = observations(users=USERS_XY[:2])
    many = observations()
    modes = np.zeros(8, dtype=bool)
    for step in range(61):
        if step == 30:
            modes[[1, 4]] = True
        if step == 60:
            modes[:] = False
        obs = present if step == 7 else many if step == 60 else absent
        expected = reference.propose(obs, object(), step, None, modes)
        got = actual.propose(obs, object(), step, None, modes)
        np.testing.assert_array_equal(got, expected)
        np.testing.assert_array_equal(actual.targets_xy, reference.targets_xy)
    assert [row["step"] for row in actual.diagnostics] == [0, 30, 60]
    assert actual.diagnostics[0]["bs_known"] is False
    assert actual.diagnostics[1]["bs_known"] is True
    actual.reset()
    actual.prepare(absent, np.zeros(8, bool), 0)
    assert actual.diagnostics[0]["bs_known"] is False


def test_action_library_features_and_legal_fallback():
    assert N_ACTIONS == 257
    np.testing.assert_array_equal(WAYPOINTS_XY[[0, 1, 16, -1]],
                                  [[250, 250], [250, 750], [750, 250], [7750, 7750]])
    controller = SensingController("L")
    obs = observations()
    features = controller.prepare(obs, np.zeros(8, bool), 0)
    assert features.shape == (controller.feature_dim,) == (FEATURE_DIM,)
    assert features.dtype == np.float32
    assert np.isfinite(features).all()
    assert controller.heuristic.last_plan["bs_xy"] is not None
    with pytest.raises(ValueError):
        controller.prepare(obs, np.zeros(8, bool), 0)
    with pytest.raises(ValueError):
        controller.apply_choice(257)
    with pytest.raises(ValueError):
        controller.apply_choice(-1)
    with pytest.raises(ValueError):
        controller.apply_choice(1.5)
    row = controller.apply_choice(1)
    assert row["requested"] == 1
    assert row["executed"] in (0, 1)
    actions = controller.act(obs)
    assert actions.shape == (8, 4)
    assert np.isfinite(actions).all()


def test_h_cannot_be_forced_to_scout():
    controller = SensingController("H")
    controller.prepare(observations(), np.zeros(8, bool), 0)
    assert controller.diagnostics[-1]["eligible"]
    row = controller.apply_choice(1)
    assert (row["requested"], row["executed"], row["fallback"]) == (1, 0, True)
    np.testing.assert_array_equal(controller.targets_xy, controller.heuristic.targets_xy)


def test_relay_protection_and_nominal_target_history():
    obs = observations()
    controller = SensingController("A")
    controller.prepare(obs, np.zeros(8, bool), 0)
    plan = controller.heuristic.last_plan
    assert controller.diagnostics[-1]["eligible"]
    scout = controller.diagnostics[-1]["scout"]
    for relay in plan["relays"]:
        assert np.linalg.norm(plan["targets"][scout] - relay) > 1e-3
    nominal = plan["targets"].copy()
    controller.apply_choice(N_ACTIONS - 1)
    np.testing.assert_array_equal(controller.targets_xy[scout], WAYPOINTS_XY[-1])
    controller.act(obs)
    np.testing.assert_array_equal(controller.heuristic.targets_xy, nominal)
    np.testing.assert_array_equal(controller.heuristic.last_plan["targets"], nominal)
    assert controller.heuristic.calls == 1


def test_highest_margin_service_uav_and_lower_index_tie():
    baseline = SensingController("H")
    baseline.prepare(observations(), np.zeros(8, bool), 0)
    plan = baseline.heuristic.last_plan
    service = [uav for uav, target in enumerate(plan["targets"])
               if np.any(np.linalg.norm(plan["centroids"] - target, axis=1) < 1e-3)
               and not np.any(np.linalg.norm(plan["relays"] - target, axis=1) < 1e-3)]
    assert len(service) >= 2
    margins = np.full(8, .1)
    margins[service[:2]] = .9
    controller = SensingController("A")
    controller.prepare(observations(margins=margins), np.zeros(8, bool), 0)
    assert controller.diagnostics[-1]["scout"] == min(service[:2])


@pytest.mark.parametrize("users,bs,modes,margins", [
    (USERS_XY[:5], (700, 750), None, None),
    (USERS_XY, None, None, None),
    (USERS_XY, (700, 750), np.ones(8, bool), None),
    (USERS_XY, (700, 750), None, np.full(8, .20)),
])
def test_ineligible_request_falls_back_without_exposing_hidden_sources(users, bs, modes, margins):
    obs = observations(users=users, bs=bs, margins=margins)
    controller = SensingController("L")
    controller.prepare(obs, np.zeros(8, bool) if modes is None else modes, 0)
    assert controller.diagnostics[-1]["eligible"] is False
    row = controller.apply_choice(19)
    assert (row["requested"], row["executed"], row["fallback"]) == (19, 0, True)
    np.testing.assert_array_equal(controller.targets_xy, controller.heuristic.targets_xy)


def test_survey_full_cell_visibility_expiry_and_reset():
    controller = SensingController("H")
    far = observations(users=[], bs=None, own=[(0.0, 0.0)] * 8)
    distant = observations(users=[], bs=None, own=[(8000.0, 8000.0)] * 8)
    start_features = controller.prepare(far, np.zeros(8, bool), 0)
    near_index = int(np.where(np.all(SURVEY_XY == [125.0, 125.0], axis=1))[0][0])
    far_index = int(np.where(np.all(SURVEY_XY == [7875.0, 7875.0], axis=1))[0][0])
    assert controller._survey_expiry[near_index] > 0
    assert controller._survey_expiry[far_index] == -np.inf
    start_freshness = start_features[8 * 365 + 3 + near_index]
    controller.apply_choice(0)
    for _ in range(30):
        controller.act(distant)
    aged_features = controller.prepare(distant, np.zeros(8, bool), 30)
    assert aged_features[8 * 365 + 3 + near_index] == pytest.approx(
        max(0.0, start_freshness - 30.0 / 500.0), abs=1e-6)
    assert aged_features[-1] == pytest.approx(.01)
    controller.reset()
    assert np.all(controller._survey_expiry == -np.inf)


def test_prior_and_selectors_have_finite_actions_and_no_rng():
    obs = observations()
    for mode in ("H", "P", "A"):
        controller = SensingController(mode)
        features = controller.prepare(obs, np.zeros(8, bool), 0)
        assert np.isfinite(features).all()
        choice = controller.choose_default()
        assert 0 <= choice < N_ACTIONS
        if mode == "H":
            assert choice == 0
        controller.apply_choice(choice)
        assert controller.act(obs).shape == (8, 4)


def test_between_boundary_visibility_updates_bs_but_not_survey():
    controller = SensingController("H")
    far = observations(users=[], bs=None, own=[(0.0, 0.0)] * 8)
    transient = observations(users=[], bs=(700.0, 750.0), own=[(8000.0, 8000.0)] * 8)
    index = int(np.where(np.all(SURVEY_XY == [7875.0, 7875.0], axis=1))[0][0])
    controller.prepare(far, np.zeros(8, bool), 0)
    controller.apply_choice(0)
    for step in range(30):
        controller.act(transient if step == 7 else far)
    controller.prepare(far, np.zeros(8, bool), 30)
    assert controller._survey_expiry[index] == -np.inf
    assert controller.diagnostics[-1]["bs_known"]


def test_policy_adapter_requests_deterministic_choice_and_ignores_state():
    class Policy:
        def predict(self, features, deterministic):
            assert deterministic is True
            assert features.shape == (FEATURE_DIM,)
            return 1, None

    obs = observations()
    controller = SensingController("L", Policy())
    actions = controller.propose(obs, object(), 0, object(), np.zeros(8, bool))
    assert actions.shape == (8, 4)
    assert controller.diagnostics[-1]["requested"] == 1
