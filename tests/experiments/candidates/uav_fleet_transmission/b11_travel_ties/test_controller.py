"""Six <=61-call H_T mock streams, each with one saved-input replay.

No native/private model/RF construction or query is used. Frozen B10 query
recording runs against explicit scripted forecast/score stubs; all mock effects
are separately counted. DM owns execution of this one finite batch.
"""
from __future__ import annotations
import json
from types import SimpleNamespace
import numpy as np
import pytest
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT, own_positions, E_BATTERY, E_MARGIN, E_AVAILABLE,
)
from experiments.candidates.uav_fleet_transmission.b11_travel_ties import controller as module
from experiments.candidates.uav_fleet_transmission.b10_service_assignment import controller as frozen
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.contract import equal
from experiments.candidates.uav_joint_transition.motion import Forecast

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


@pytest.fixture(scope="module", autouse=True)
def measured_mock_work(record_testsuite_property):
    module.TOTALS.clear()
    yield
    counts = json.dumps(module.TOTALS, sort_keys=True)
    record_testsuite_property("b11_scripted_mock_counts", counts)
    print("B11 scripted mock/controller work: " + counts)
    assert module.TOTALS.get("proposals", 0) <= 732
    assert module.TOTALS.get("candidate_forecasts", 0) <= 576
    assert module.TOTALS.get("mock_joint_forecast_ticks", 0) <= 17280
    assert module.TOTALS.get("model_constructions", 0) == 0
    assert module.TOTALS.get("model_rf_calls", 0) == 0
    assert module.TOTALS.get("joint_forecast_ticks", 0) == 0


@pytest.mark.parametrize("case", range(6), ids=[
    "base-max-tie", "unique-best-and-failed-prefix", "shorter-exact-top-tie",
    "equal-travel-first-index", "tiny-literal-score-gain", "fallback-state-clock",
])
def test_one_scripted_stream_and_one_replay(monkeypatch, case):
    def values(index):
        if case == 0:
            return 1.0, 1000.0 if index == 0 else 1.0
        if case == 1:
            return (2.0 if index == 3 else 1.0), 10000.0 if index == 3 else 1.0
        if case == 2:
            return (2.0 if index in (1, 2, 3) else 1.0), {1: 200., 2: 100., 3: 300.}.get(index, 0.)
        if case == 3:
            return (2.0 if index in (1, 2) else 1.0), 100.0 if index in (1, 2) else 0.0
        if case == 4:
            return (np.nextafter(1.0, np.inf) if index == 1 else 1.0), 10000.0 if index == 1 else 0.0
        return (2.0 if index in (1, 2) else 1.0), 100.0 if index == 2 else 200.0

    class MockModel:
        def __init__(self, counts, seed):
            assert seed == 0
            self.counts = counts
            self.raw = SimpleNamespace(forecasts=0, candidate=0, sample=0)
            frozen.bump(counts, "mock_model_constructions")
        def score(self, xyz, battery, users, bs):
            frozen.bump(self.counts, "mock_model_score_calls")
            sample = self.raw.sample
            self.raw.sample += 1
            # The unique-best case retains a failed final candidate at t60.
            if case == 1 and self.raw.forecasts == 48 and sample == 2:
                raise RuntimeError("scripted final-candidate RF interruption")
            score, _ = values(self.raw.candidate)
            return dict(qos=score / 10.0 if sample == 0 else 0.0, digest="00" * 32)
        def close(self):
            pass

    def scripted_forecast(start, targets, modes, prior_F, raw, *, counters,
                          on_tick, on_tick_started, hold_xy):
        raw.candidate = raw.forecasts % 16
        raw.forecasts += 1
        raw.sample = 0
        frozen.bump(counters, "mock_forecasts")
        for tick in range(1, 31):
            frozen.bump(counters, "mock_joint_forecast_ticks")
            on_tick_started(tick)
            frozen.bump(counters, "mock_joint_forecast_ticks_completed")
            on_tick(tick, "11" * 32)
        xyz = np.repeat(start["xyz"][None], 3, axis=0)
        _, travel = values(raw.candidate)
        return Forecast(xyz, np.repeat(start["battery"][None], 3, axis=0),
            np.full((3, 8), .5), np.zeros((3, 8), dtype=bool),
            np.zeros((3, 8), dtype=np.int64), np.zeros(8, dtype=bool),
            np.zeros(8, dtype=bool), np.zeros(8, dtype=bool),
            np.zeros(8, dtype=bool), travel), "11" * 32

    monkeypatch.setattr(module, "LawfulServiceModel", MockModel)
    monkeypatch.setattr(frozen, "forecast", scripted_forecast)
    if case == 3:
        rank = module.select_travel_tie
        rankings = []
        def interrupted_ranking(records):
            result = rank(records)
            rankings.append(None)
            if len(rankings) == 3:
                raise RuntimeError("scripted full-table selection interruption")
            return result
        monkeypatch.setattr(module, "select_travel_tie", interrupted_ranking)
    history = []
    assign = frozen.ProvenanceHeuristic._assign_targets
    def observe_hysteresis(self, own_xy, uavs, points, targets):
        if self._assignment_call == 0:
            history.append((self.calls, self.targets_xy.copy()))
        return assign(self, own_xy, uavs, points, targets)
    monkeypatch.setattr(frozen.ProvenanceHeuristic, "_assign_targets", observe_hysteresis)
    observations = []
    for step in range(61):
        users = [(1100. + 250 * i + step, 1200. + 130 * i) for i in range(6)]
        bs, stations = None, ((7000., 500., 100.), (1000., 7000., 100.))
        if case == 5 and step < 30:
            stations = (None, stations[1])
        elif case == 5 and step < 60:
            users, bs = users[:1], (1000., 1000.)
        observations.append(frame(users, bs=bs, stations=stations))
    first, replay = module.make_controller("H_T"), module.make_controller("H_T")
    actions, decisions, committed = [], {}, {}
    mask = np.zeros(8, dtype=bool)
    try:
        assert first.arm == "H_A" and first.policy_arm == "H_T"
        assert type(first).__mro__[1] is frozen.ServiceController
        for step, obs in enumerate(observations):
            old = obs.copy()
            if case in (1, 3) and step == 60:
                with pytest.raises(RuntimeError, match="scripted"):
                    first.propose(obs, Poison(), step, Poison(), mask)
                assert first.heuristic.calls == 60
                assert first.last_decision["candidate_count"] == 16
                break
            actions.append(first.propose(obs, Poison(), step, Poison(), mask))
            np.testing.assert_array_equal(obs, old)
            assert first.heuristic.calls == step + 1
            if step % 30 == 0:
                d = first.last_decision.copy()
                decisions[step], committed[step] = d, first.targets_xy
                np.testing.assert_array_equal(first.heuristic.last_plan["targets"], first.targets_xy)
                if d["candidate_count"]:
                    index = d["candidate_first"] + d["selected"]
                    r = first.audit_arrays()["candidate_records"][index]
                    np.testing.assert_array_equal(first.targets_xy, r["targets"][:, :2])
                    np.testing.assert_array_equal(d["selected_pair"], [r["pair_left"], r["pair_right"]])
        saved = first.audit_arrays()["candidate_records"].copy()
        expected_h = [0, 3, 1, 1, 1, 1][case]
        expected_final = [0, 3, 2, 1, 1, 2][case]
        for step, d in decisions.items():
            if not d["candidate_count"]:
                assert d["h_selected"] == -1 and not d["tie_changed"]
                assert d["top_score_mask"].size == d["min_travel_mask"].size == 0
                continue
            assert d["h_selected"] == expected_h
            assert d["selected"] == expected_final
            assert d["tie_changed"] == (expected_h != expected_final)
            rows = saved[saved["step"] == step]
            np.testing.assert_array_equal(np.flatnonzero(rows["selected"]), [expected_final])
            np.testing.assert_array_equal(d["top_score_mask"], rows["score"] == rows["score"].max())
            minimum = rows["forecast_travel"][d["top_score_mask"]].min()
            np.testing.assert_array_equal(d["min_travel_mask"], d["top_score_mask"] & (rows["forecast_travel"] == minimum))
            if case == 2:
                assert rows[1]["accepted"] and not rows[2]["accepted"]
                assert rows[1]["score"] == rows[2]["score"]
                assert rows[2]["forecast_travel"] < rows[1]["forecast_travel"]
            if case == 4:
                assert 0 < rows[1]["score"] - rows[0]["score"] < 1e-10
                assert rows[1]["forecast_travel"] > rows[0]["forecast_travel"]
        if case == 5:
            assert decisions[0]["fallback"] == 2
            assert decisions[30]["fallback"] == 1
            assert decisions[60]["fallback"] == 0
            assert first.counters["mock_model_constructions"] == 1
            assert len(saved) == 16
        for boundary, previous in history:
            if boundary:
                np.testing.assert_array_equal(previous, committed[boundary-30])
        if case == 1:
            assert not saved[-1]["completed"]
            assert saved[-1]["rf_started"] == 3 and saved[-1]["rf_completed"] == 2
            assert not saved[saved["step"] == 60]["selected"].any()
            bad = saved[-1].copy()
            bad["selected"] = True
            with pytest.raises(ValueError, match="incomplete"):
                frozen.validate_candidate_record(bad)
        if case == 3:
            assert saved["completed"].all()
            assert not saved[saved["step"] == 60]["selected"].any()
        # Pure rank assertions use no extra controller/model/candidate calls.
        pure = np.zeros(3, dtype=module.CANDIDATE_DTYPE)
        pure["score"] = [0., 1., 1.]
        pure["forecast_travel"] = [0., 100., np.nextafter(100., 0.)]
        assert module.select_travel_tie(pure)[:2] == (1, 2)
        pure["forecast_travel"][2] = np.nan
        with pytest.raises(FloatingPointError):
            module.select_travel_tie(pure)
        replay.replay_prefix = saved
        for step, obs in enumerate(observations):
            if case in (1, 3) and step == 60:
                with pytest.raises(module.ReplayBoundary, match="RF prefix|before search selection"):
                    replay.propose(obs, Poison(), step, Poison(), mask)
                break
            actual = replay.propose(obs, Poison(), step, Poison(), mask)
            np.testing.assert_array_equal(actual, actions[step])
            if step % 30 == 0:
                for field in ("h_selected", "selected", "tie_changed", "top_score_mask", "min_travel_mask"):
                    equal(replay.last_decision[field], decisions[step][field], "tie-replay/"+field)
        rebuilt = replay.audit_arrays()["candidate_records"]
        for name in saved.dtype.names:
            if case != 1 or name != "rf_started":
                equal(rebuilt[name], saved[name], "candidate/replay/"+name)
        if case == 1:
            assert rebuilt[-1]["rf_started"] == 2
            expected = first.counters.copy()
            expected["mock_model_score_calls"] -= 1
            assert replay.counters == expected
        else:
            assert first.counters == replay.counters
        assert first.counters["proposals"] == 61
        assert first.counters["plans"] == 3
        assert first.counters["canonicalizations"] == 64
        assert first.counters["associations"] == 61
        assert first.counters.get("future_projections", 0) == 0
    finally:
        first.close()
        replay.close()
