"""Six 61-call scripted streams per H/F plus one saved-prefix replay each.

All scorers are mocked: no native construction/reset/step/RF, seed or outcome
query. Nominal physics uses public literals. The DM executes this envelope.
"""
from __future__ import annotations
import json
import numpy as np
import pytest
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT, own_positions, E_BATTERY, E_MARGIN, E_AVAILABLE,
)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment import controller as module
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.contract import equal
from experiments.candidates.uav_information_value import controllers as original_planner

class Poison:
    def __getattribute__(self, name):
        raise AssertionError("privileged input read: " + name)
    def __array__(self, *args, **kwargs):
        raise AssertionError("privileged input converted")

def frame(users=(), *, bs=None, stations=((7000., 500., 100.), (1000., 7000., 100.))):
    """Public literals encoded in the retained lawful 365-field interface."""
    layout = S7S2_LAYOUT
    xyz = np.asarray([[900., 900., 100.], [1200., 900., 100.], [1800., 1000., 100.],
                      [2400., 1000., 100.], [3200., 1400., 100.], [4500., 2500., 100.],
                      [6000., 4500., 100.], [7200., 7000., 100.]])
    obs = np.zeros((8, layout.dim), dtype=np.float32)
    obs[:, :2] = xyz[:, :2] / 8000.
    obs[:, 2] = (xyz[:, 2] - 50.) / 150.
    own = own_positions(obs)
    for slot, xy in enumerate(users):
        base = layout.users.start + slot * layout.user_fields
        obs[0, base:base + 2] = (np.asarray(xy) - own[0, :2]) / 8000.
        obs[0, base + 4] = 1.
    for observer in range(8):
        energy = obs[observer, layout.energy_uavs].reshape(8, 13)
        energy[:, :3] = (own - own[observer]) / [8000., 8000., 150.]
        energy[:, E_BATTERY] = .8
        energy[:, E_MARGIN] = .5
        energy[:, E_AVAILABLE] = 1.
        for station, position in enumerate(stations):
            if position is None:
                continue
            base = layout.energy_stations.start + station * layout.energy_station_fields
            obs[observer, base:base + 3] = (np.asarray(position) - own[observer]) / [8000., 8000., 150.]
            obs[observer, base + 3] = np.linalg.norm(np.asarray(position) - own[observer]) / 8000.
            obs[observer, base + 4:base + 6] = 1. / 8.
            obs[observer, base + 7] = 1.
        if bs is not None:
            base = layout.bs.start
            obs[observer, base:base + 2] = (np.asarray(bs) - own[observer, :2]) / 8000.
            obs[observer, base + 2] = (30. - own[observer, 2]) / 200.
            obs[observer, base + 3] = 1.
    return obs


class PublicPhysics:
    time_step = 1.0
    charging_radius_m = 100.0
    charging_capture_radius_m = 10.0
    docking_horizontal_speed_mps = 5.0
    docking_vertical_speed_mps = 1.0
    emergency_return_threshold = .1
    limp_home_speed_mps = 10.0
    max_speed = 30.0
    charging_hover_speed_threshold = 1.0
    charging_power_w = 100.0
    battery_capacity_wh = 100.0
    return_reserve_ratio = .05
    service_cutoff_threshold = .01
    def _calculate_power_consumption(self, horizontal, vertical):
        return np.zeros_like(horizontal, dtype=np.float64)


@pytest.fixture(scope="module", autouse=True)
def measured_mock_work(record_testsuite_property):
    module.TOTALS.clear()
    yield
    counts = json.dumps(module.TOTALS, sort_keys=True)
    record_testsuite_property("b10_scripted_mock_counts", counts)
    print("B10 scripted mock/nominal attempted work: " + counts)
    assert module.TOTALS.get("proposals", 0) <= 1464
    assert module.TOTALS.get("candidate_forecasts", 0) <= 1152
    assert module.TOTALS.get("model_constructions", 0) == 0
    assert module.TOTALS.get("model_rf_calls", 0) == 0


@pytest.mark.parametrize("arm", ["H_A", "F_A"])
@pytest.mark.parametrize("case", range(6), ids=[
    "sparse-absent-bs", "actual-roles", "aliases-base-tie",
    "strict-first-lex", "commit-clock-hold-F-release", "failed-corrupt-prefix",
])
def test_scripted_stream_and_one_prefix_replay(monkeypatch, arm, case):
    """One original stream plus one replay, each at most 61 primitive calls."""
    class MockModel:
        def __init__(self, counts, seed):
            assert seed == 0
            self.counts, self.calls = counts, 0
            self.raw = PublicPhysics()
            module.bump(counts, "mock_model_constructions")
        def score(self, xyz, battery, users, bs):
            sample = self.calls % 3
            candidate = (self.calls // 3) % 16
            self.calls += 1
            module.bump(self.counts, "mock_model_score_calls")
            if case == 5 and arm == "F_A" and self.calls == 3:
                raise RuntimeError("scripted third RF interruption")
            # A score gap below B09 tolerance must still select the first pair.
            score = (1e-11 if candidate in (1, 2) else 0.0) if case == 3 else (
                1.0 if candidate == 1 else 0.0) if case == 4 else 0.0
            return dict(qos=score / 10.0 if sample == 0 else 0.0, digest="00" * 32)
        def close(self):
            pass
    monkeypatch.setattr(module, "LawfulServiceModel", MockModel)
    if case == 5 and arm == "H_A":
        original_forecast = module.forecast
        def interrupted_forecast(*args, **kwargs):
            on_tick = kwargs["on_tick"]
            def stop(number, digest):
                on_tick(number, digest)
                if number == 7:
                    raise RuntimeError("scripted nominal interruption")
            kwargs["on_tick"] = stop
            return original_forecast(*args, **kwargs)
        monkeypatch.setattr(module, "forecast", interrupted_forecast)
    if case == 2:
        def duplicate_centers(points, k, iterations):
            return np.repeat(points[:1], k, axis=0), np.ones(k, dtype=np.int64)
        monkeypatch.setattr(original_planner, "estimator_kmeans", duplicate_centers)
    historical_inputs = []
    assign = module.ProvenanceHeuristic._assign_targets
    def inspect_history(self, own_xy, uavs, points, targets):
        if self._assignment_call == 0:
            historical_inputs.append((self.calls, self.targets_xy.copy()))
        return assign(self, own_xy, uavs, points, targets)
    monkeypatch.setattr(module.ProvenanceHeuristic, "_assign_targets", inspect_history)
    observations, masks = [], []
    for step in range(61):
        users = [(1100. + 250 * i + step, 1200. + 130 * i) for i in range(6)]
        if case == 0:
            users = users[:1] if step < 30 else users
        if case == 1:
            users = users[:1] if 30 <= step < 60 else users[:3]
        if case == 5 and step < 60:
            users = []
        stations = (None, (1000., 7000., 100.)) if case == 0 else (
            (7000., 500., 100.), (1000., 7000., 100.))
        obs = frame(users, stations=stations)
        mask = np.zeros(8, dtype=bool)
        if case == 1:
            mask[6:] = True
        if case == 4 and step == 0:
            mask[7] = True
            for observer in range(8):
                obs[observer, S7S2_LAYOUT.energy_uavs].reshape(8, 13)[7, E_MARGIN] = 0.0
        observations.append(obs)
        masks.append(mask)
    first, replay = module.make_controller(arm), module.make_controller(arm)
    actions, decisions, chosen = [], {}, {}
    try:
        for step, (obs, modes) in enumerate(zip(observations, masks)):
            old = obs.copy()
            if case == 5 and step == 60:
                with pytest.raises(RuntimeError, match="scripted"):
                    first.propose(obs, Poison(), step, Poison(), modes)
                break
            actions.append(first.propose(obs, Poison(), step, Poison(), modes))
            np.testing.assert_array_equal(obs, old)
            assert first.heuristic.calls == step + 1
            if step % 30 == 0:
                decisions[step] = first.last_decision.copy()
                chosen[step] = first.targets_xy
                np.testing.assert_array_equal(first.heuristic.last_plan["targets"], first.targets_xy)
                d = decisions[step]
                np.testing.assert_array_equal(first.targets_xy[~d["eligible"]], d["ordinary_targets"][~d["eligible"]])
                ordinary = d["ordinary_targets"]
                actual = first.targets_xy
                order = lambda a: np.lexsort((a[:, 1], a[:, 0]))
                np.testing.assert_array_equal(actual[order(actual)], ordinary[order(ordinary)])
        saved = first.audit_arrays()["candidate_records"].copy()
        if case == 0:
            assert len(saved) == 0
            assert decisions[0]["fallback"] == 2
            assert first.model is None
            assert first.counters.get("future_projections", 0) == 0
        if case == 1:
            d = decisions[0]
            assert np.count_nonzero(d["assignment_role"] == module.ROLE_RELAY) == 2
            assert np.count_nonzero(d["assignment_role"] == module.ROLE_SERVICE) == 3
            assert np.count_nonzero(d["assignment_role"] == module.ROLE_RING) == 1
            assert d["candidate_count"] == 4
            assert decisions[30]["fallback"] == 1
            assert decisions[30]["candidate_count"] == 0
            assert decisions[30]["future_xy"].shape == (3, 0, 2)
            assert len(decisions[30]["current_velocities"]) == 1
            assert not d["eligible"][6:].any()
            assert np.all(d["assignment_column"][6:] == -1)
        if case == 2:
            assert len(saved) == 48
            assert saved["alias_base"].sum() == 45
            assert all(d["selected"] == 0 for d in decisions.values())
        if case == 3:
            assert all(d["selected"] == 1 for d in decisions.values())
            for step, d in decisions.items():
                eligible = np.flatnonzero(d["eligible"])
                np.testing.assert_array_equal(d["selected_pair"], eligible[:2])
                r = saved[saved["step"] == step]
                assert r["score"][1] == r["score"][2] > r["score"][0]
        if case == 4:
            for boundary, previous in historical_inputs:
                if boundary:
                    np.testing.assert_array_equal(previous, chosen[boundary - 30])
            assert np.all(actions[1][7, :2] == 0.0)
            rows = saved[saved["step"] == 0]
            assert rows["hold_xy"][:, 7].all()
            assert not np.array_equal(rows[0]["xyz"][0, 7, :2], own_positions(observations[0])[7, :2])
            np.testing.assert_array_equal(rows[0]["xyz"][0, 7, :2], rows[0]["xyz"][2, 7, :2])
        if case != 0 and case != 5:
            assert all(d["candidate_count"] <= 16 for d in decisions.values())
            for d in decisions.values():
                if d["candidate_count"] == 0:
                    continue
                q = len(d["current_velocities"])
                assert d["future_xy"].shape == (3, q, 2)
                if d["step"] >= 30:
                    assert np.any(d["current_velocities"] != 0.0)
        if case == 5:
            assert len(saved) == 1 and not saved[0]["completed"]
            if arm == "F_A":
                assert saved[0]["rf_started"] == 3 and saved[0]["rf_completed"] == 2
            else:
                assert saved[0]["ticks"] == 7 and saved[0]["rf_started"] == 0
            corrupt = saved[0].copy()
            corrupt["completed"] = True
            with pytest.raises(ValueError, match="corrupt"):
                module.validate_candidate_record(corrupt)
        replay.replay_prefix = saved
        for step, (obs, modes) in enumerate(zip(observations, masks)):
            if case == 5 and step == 60:
                with pytest.raises(module.ReplayBoundary, match="prefix exhausted"):
                    replay.propose(obs, Poison(), step, Poison(), modes)
                break
            actual = replay.propose(obs, Poison(), step, Poison(), modes)
            np.testing.assert_array_equal(actual, actions[step])
        rebuilt = replay.audit_arrays()["candidate_records"]
        for name in saved.dtype.names:
            if case != 5 or name != "rf_started":
                equal(rebuilt[name], saved[name], "scripted/replay/" + name)
        if case == 5:
            expected_rf = 2 if arm == "F_A" else 0
            assert replay.counters.get("mock_model_score_calls", 0) == expected_rf
            assert rebuilt[0]["rf_started"] == expected_rf
        else:
            assert first.counters == replay.counters
        assert first.counters["associations"] == 61
        assert first.counters["canonicalizations"] == 64
    finally:
        first.close()
        replay.close()
