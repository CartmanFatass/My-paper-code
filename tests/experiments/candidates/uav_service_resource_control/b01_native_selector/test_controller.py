"""Eight61-call mock streams and exactly one replay each; no real RF/physics.

The DM selects execution. Own-edge and H query effects are explicit stubs,
so these streams do not spend the separate public-law check allowance.
"""
from __future__ import annotations

from types import SimpleNamespace
import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT, own_positions
from experiments.candidates.uav_fleet_transmission.b10_service_assignment import controller as b10
from experiments.candidates.uav_fleet_transmission.b11_travel_ties import controller as b11
from experiments.candidates.uav_information_value.controllers import PointSetHeuristic
from experiments.candidates.uav_joint_transition.motion import Forecast
from experiments.candidates.uav_service_resource_control.b01_native_selector import controller as module
from experiments.candidates.uav_service_resource_control.b01_native_selector import features


class Poison:
    def __getattribute__(self, name):
        raise AssertionError("privileged data accessed: " + name)
    def __array__(self, *args, **kwargs):
        raise AssertionError("privileged data converted")


def frame(step, *, bs=True):
    layout = S7S2_LAYOUT
    obs = np.zeros((8, layout.dim), dtype=np.float32)
    obs[:, :2] = np.column_stack((np.arange(8) * .05 + .1, np.full(8, .2)))
    obs[:, 2] = 1. / 3.
    xyz = own_positions(obs)
    # Current anonymous input changes each tick, including C-only intervals.
    for slot in range(6):
        start = layout.users.start + slot * 6
        obs[0, start:start+2] = ([1500. + slot * 300. + step, 2000.] - xyz[0, :2]) / 8000.
        obs[0, start+4] = 1.
    for observer in range(8):
        energy = obs[observer, layout.energy_uavs].reshape(8, 13)
        energy[:, :3] = (xyz - xyz[observer]) / [8000., 8000., 150.]
        energy[:, 3] = .8
        energy[:, 5] = 1.
        energy[:, 12] = .5
        for index, target in enumerate(([7000., 500., 100.], [1000., 7000., 100.])):
            row = obs[observer, layout.energy_stations].reshape(2, 8)[index]
            row[:3] = (target - xyz[observer]) / [8000., 8000., 150.]
            row[4:6] = 1. / 8.
            row[7] = 1.
        if bs:
            row = obs[observer, layout.bs].reshape(3, 4)[0]
            row[:2] = ([1000., 1000.] - xyz[observer, :2]) / 8000.
            row[3] = 1.
    return obs


@pytest.mark.parametrize("case", range(8), ids=[
    "forced-C", "H-base-literal-tie", "alternate-C-first", "alternate-H-first",
    "H-shortest-top", "H-tiny-score-gain", "missing-targets-and-alias",
    "ineligible-and-unlawful-request",
])
def test_scripted_stream_and_one_replay(monkeypatch, case):
    mock = dict(proposals=0, plans=0, queries=0, returns=0, edges=0, model_constructions=0)
    history = []

    def plan(self, observations, modes, plan_inputs=None):
        mock["plans"] += 1
        history.append((self.calls, self.targets_xy.copy()))
        targets = np.column_stack((np.arange(8) * 400. + 1800. + self.calls,
                                   np.full(8, 2400.)))
        self.assignment_role[:] = [1, 1, 2, 2, 2, 2, 2, 2]
        if case == 6:
            if self.calls < 60:
                self.assignment_role[:] = 0
                targets[:] = np.nan
            else:
                targets[3] = targets[2]  # coordinate-alias pair remains an H request
        if case == 7 and self.calls >= 30:
            self.assignment_role[:] = [1, 1, 2, 3, 3, 3, 3, 3]
        self.assignment_column[:] = np.arange(8)
        self.assignment_call[:] = 1
        self.targets_xy = targets
        self.last_plan = dict(call=self.calls, users=plan_inputs["users_xy"].copy(),
            bs_xy=plan_inputs["bs_xy"], targets=targets.copy(), search=False)
        return self.last_plan

    def public_return(target, stations, law, *, counters):
        mock["returns"] += 1
        b10.bump(counters, "mock_return_evaluations")
        return 0, 2.

    def public_edge(xyz, target, battery, return_wh, law, *, counters):
        mock["edges"] += 1
        b10.bump(counters, "mock_flight_edges")
        return 10, 1., float(battery) - 3. / 160. - .10

    def values(index):
        if case in (0, 1, 2, 3, 7):
            return 1., 1000. if index == 0 else 1.
        if case == 4:
            return (2. if index in (1, 2) else 1.), (100. if index == 2 else 200.)
        if case == 5:
            return (np.nextafter(1., np.inf) if index == 1 else 1.), 10000. if index == 1 else 0.
        return (2. if index == 1 else 1.), 10.

    class MockModel:
        def __init__(self, counts, seed):
            assert seed == 0
            mock["model_constructions"] += 1
            self.raw = SimpleNamespace(index=0, sample=0)
        def score(self, xyz, battery, users, bs):
            score, _ = values(self.raw.index)
            sample = self.raw.sample
            self.raw.sample += 1
            return dict(qos=score / 10. if sample == 0 else 0., digest="00" * 32)
        def close(self):
            pass

    query = b11.TravelTieController._query
    def mock_query(self, step, index, *args, **kwargs):
        mock["queries"] += 1
        self.model.raw.index, self.model.raw.sample = index, 0
        return query(self, step, index, *args, **kwargs)

    def forecast(start, targets, modes, prior_F, raw, *, counters, on_tick, on_tick_started, hold_xy):
        for tick in range(1, 31):
            on_tick_started(tick)
            on_tick(tick, "11" * 32)
        xyz = np.repeat(start["xyz"][None], 3, axis=0)
        _, travel = values(raw.index)
        return Forecast(xyz, np.repeat(start["battery"][None], 3, axis=0),
            np.full((3, 8), .5), np.zeros((3, 8), dtype=bool),
            np.zeros((3, 8), dtype=np.int64), *[np.zeros(8, dtype=bool) for _ in range(4)],
            travel), "11" * 32

    monkeypatch.setattr(PointSetHeuristic, "plan", plan)
    monkeypatch.setattr(features, "target_return", public_return)
    monkeypatch.setattr(features, "flight_edge", public_edge)
    monkeypatch.setattr(b11, "LawfulServiceModel", MockModel)
    monkeypatch.setattr(b11.TravelTieController, "_query", mock_query)
    monkeypatch.setattr(b10, "forecast", forecast)
    if case == 7:
        # Legal features retain valid stations, but the original prior is absent.
        from experiments.candidates.uav_information_value.b02 import controller as prior
        monkeypatch.setattr(prior, "station_prior_bs_xy", lambda *args: None)

    def chooser(vector, h_eligible, step):
        assert vector.shape == (327,) and vector.dtype == np.float32
        assert np.isfinite(vector).all()
        assert mock["queries"] == before_choice[0]
        if case == 0:
            action = 0
        elif case in (2, 3):
            action = (step // 30 + (case == 3)) % 2
        elif case == 7:
            action = int(step == 60)  # Must fail at this ineligible boundary.
        else:
            action = int(h_eligible)
        vector[:] = -999.  # The audited vector must survive untrusted mutation.
        return dict(action=int(action), diagnostic_step=int(step))

    first, replay = module.SelectorController(chooser), module.SelectorController(chooser)
    before_choice = [0]
    observations = [frame(t, bs=(case != 7 or t == 30)) for t in range(61)]
    actions, committed, decisions = [], {}, {}
    try:
        for actor_index, actor in enumerate((first, replay)):
            if actor_index:
                actor.replay_prefix = first.audit_arrays()["candidate_records"].copy()
                actor.replay_choice_prefix = first.audit_arrays()["choice_records"].copy()
            for step, obs in enumerate(observations):
                before_choice[0] = mock["queries"]
                mock["proposals"] += 1
                if case == 7 and step == 60:
                    with pytest.raises(ValueError, match="ineligible"):
                        actor.propose(obs, Poison(), step, Poison(), np.zeros(8, dtype=bool))
                    assert actor.heuristic.calls == 60
                    assert actor.choice_records[-1]["requested_action"] == 1
                    assert not actor.choice_records[-1]["completed"]
                    continue
                result = actor.propose(obs, Poison(), step, Poison(), np.zeros(8, dtype=bool))
                assert actor.heuristic.calls == step + 1
                if actor_index:
                    np.testing.assert_array_equal(result, actions[step])
                else:
                    actions.append(result.copy())
                if step % 30 == 0:
                    row = actor.choice_records[-1]
                    assert row["features_available"] and np.all(row["features"] != -999.)
                    assert actor.last_trace["selector_features"].dtype == np.float32
                    np.testing.assert_array_equal(row["ordinary_targets"], actor.last_decision["ordinary_targets"])
                    np.testing.assert_array_equal(actor.heuristic.last_plan["targets"], actor.targets_xy)
                    if step:
                        np.testing.assert_array_equal(row["previous_targets"], committed[(actor_index, step - 30)])
                        previous_row = decisions[(actor_index, step - 30)]
                        assert row["has_previous_choice"]
                        assert row["previous_requested_action"] == previous_row["requested_action"]
                        assert row["features"][320] == 1.
                        assert row["features"][321] == previous_row["requested_action"]
                    else:
                        assert not row["has_previous_choice"]
                        np.testing.assert_array_equal(row["features"][320:323], np.zeros(3))
                    committed[(actor_index, step)] = actor.targets_xy.copy()
                    decisions[(actor_index, step)] = row.copy()
                    if int(row["requested_action"]) == 0:
                        assert not row["h_search"] and row["candidate_count"] == 0
                    else:
                        assert row["h_search"]
                        assert row["candidate_count"] == 1 + int(row["m"]) * (int(row["m"]) - 1) // 2
                        expected = 2 if case == 4 else 1 if case in (5, 6) else 0
                        assert row["selected"] == expected
                        assert row["h_selected_base"] == (expected == 0)
                    if case == 6 and step == 60:
                        assert row["selected_pair_alias"] and row["ordinary_target_alias"]
                    if case == 7:
                        assert row["bs_source"] == (3 if step == 0 else 0)
            assert actor.counters["proposals"] == 61 and actor.counters["plans"] == 3
            assert actor.counters["associations"] == 61
            assert actor.counters.get("model_rf_calls", 0) == 0
            assert actor.counters.get("joint_forecast_ticks", 0) == 0
            assert actor.counters.get("flight_edges", 0) == 0
            assert actor.counters.get("return_evaluations", 0) == 0
            assert actor.cold_costs.get("constant_power_evaluations", 0) == 0
        for key in ("choice_records", "candidate_records"):
            for field in first.audit_arrays()[key].dtype.names:
                b10.equal(first.audit_arrays()[key][field], replay.audit_arrays()[key][field], "mock/replay/" + field)
        assert mock["proposals"] == 122 and mock["plans"] == 6
        assert mock["queries"] <= 96
        for offset, (step, previous) in enumerate(history):
            actor_index = offset // 3
            if step:
                np.testing.assert_array_equal(previous, committed[(actor_index, step - 30)])
        if case == 0:
            assert mock["model_constructions"] == mock["queries"] == 0
        # Reset is a controller reset, never a learner/chooser reset.
        same_chooser = first.chooser
        first.reset()
        assert first.chooser is same_chooser
        assert first._previous_action is None and first._same_choice_count == 0
        assert len(first.choice_records) == 0 and first.model is None
        assert first.heuristic.calls == 0 and np.isnan(first.targets_xy).all()
    finally:
        first.close()
        replay.close()


def test_feature_layout_and_contract_failures(monkeypatch):
    # Pure feature construction; public-edge effects remain stubs.
    monkeypatch.setattr(features, "target_return", lambda *a, **k: (0, 16.))
    monkeypatch.setattr(features, "flight_edge", lambda *a, **k: (300, 8., -.25))
    obs = frame(0)
    arguments = dict(ordinary_targets=np.full((8, 2), np.nan), previous_targets=np.full((8, 2), np.nan),
        roles=np.zeros(8, dtype=np.int8), modes=np.zeros(8, dtype=bool),
        users=np.array([[200., 300.]]), bs_xy=None, bs_source="absent", law=Poison())
    context = features.lawful_context(obs, S7S2_LAYOUT, **arguments)
    result = features.pack_features(context, step=0)
    assert result.shape == (327,) and result.dtype == np.float32
    own = result[:208].reshape(8, 26)
    np.testing.assert_array_equal(own[:, 15:26], np.zeros((8, 11)))
    np.testing.assert_array_equal(result[222:229], [0., 0., 0., 0., 0., 0., 1.])
    np.testing.assert_array_equal(result[229:232], np.array([.025, .0375, 1.], dtype=np.float32))
    assert not context["min_slack_valid"] and context["min_slack"] == 0.
    targets = np.full((8, 2), np.nan)
    targets[2:4] = [[-800., 8800.], [400., 500.]]
    arguments.update(ordinary_targets=targets, roles=np.array([0, 0, 2, 2, 0, 0, 0, 0], dtype=np.int8))
    context = features.lawful_context(obs, S7S2_LAYOUT, **arguments)
    own = features.pack_features(context, step=30, previous_action=1, same_choice_count=3)[:208].reshape(8, 26)
    np.testing.assert_array_equal(own[2, 15:18], np.array([1., -.1, 1.1], dtype=np.float32))
    np.testing.assert_array_equal(own[2, 21:26], np.array([1., .1, .05, .1, -.25], dtype=np.float32))
    assert context["m"] == 2 and not context["h_eligible"]
    # Charging, low battery and unavailable bits do not silently prune E.
    energy = obs[:, S7S2_LAYOUT.energy_uavs].reshape(8, 8, 13)
    energy[2, 2, 3:7] = [.01, 1., 0., 1.]
    context = features.lawful_context(obs, S7S2_LAYOUT, **arguments)
    assert context["eligible"][2]
    mode = arguments["modes"].copy()
    mode[2] = True
    masked = features.lawful_context(obs, S7S2_LAYOUT, **(arguments | dict(modes=mode)))
    assert masked["m"] == 1 and not masked["eligible"][2]
    np.testing.assert_array_equal(masked["edges"][2], np.zeros(5))
    with pytest.raises(ValueError, match="six service"):
        features.lawful_context(obs, S7S2_LAYOUT, **(arguments | dict(
            ordinary_targets=np.zeros((8, 2)), roles=np.full(8, 2, dtype=np.int8))))
    with pytest.raises(ValueError, match="at most30"):
        features.lawful_context(obs, S7S2_LAYOUT, **(arguments | dict(users=np.zeros((31, 2)))))
    bad = obs.copy()
    bad[0, S7S2_LAYOUT.energy_stations.start + 4] = .25
    with pytest.raises(ValueError, match="capacity"):
        features.lawful_context(bad, S7S2_LAYOUT, **arguments)
    bad = targets.copy()
    bad[0] = [np.nan, 0.]
    with pytest.raises(ValueError, match="missing target"):
        features.target_payload(bad)
    for invalid in (True, 0., -1, 2, "1"):
        with pytest.raises(ValueError, match="integer"):
            module._action(invalid)


def test_ordinary_literal_threshold_and_reset_without_encoding(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("ordinary threshold encoded network input")
    monkeypatch.setattr(module, "pack_features", forbidden)
    actor = module.ThresholdController(.10)
    # No propose/act/query/public-law calls; test the literal latch function.
    c = dict(h_eligible=True, min_slack=.10 + .05)
    assert actor._choose(c, 0)["action"] == 1
    c["min_slack"] = np.nextafter(.10, np.inf)
    assert actor._choose(c, 30)["action"] == 1
    c["min_slack"] = .10
    assert actor._choose(c, 60)["action"] == 0
    c["min_slack"] = np.nextafter(.10 + .05, -np.inf)
    assert actor._choose(c, 90)["action"] == 0
    c["min_slack"] = .10 + .05
    assert actor._choose(c, 120)["action"] == 1
    assert actor._choose(c | dict(h_eligible=False), 150)["action"] == 0
    actor._choose(c, 180)
    actor.reset()
    assert actor._latch == 0
    assert type(module.make_controller("C")) is b10.CController
    assert type(module.make_controller("H_T")) is b11.TravelTieController
