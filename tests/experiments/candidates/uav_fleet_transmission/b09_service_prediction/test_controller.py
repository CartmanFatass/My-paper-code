"""Bounded synthetic, nonempty B09 checks; never reset or step a native world."""
from __future__ import annotations

from dataclasses import fields
import json
import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT, own_positions, E_BATTERY, E_MARGIN, E_AVAILABLE,
)
from experiments.candidates.uav_fleet_transmission.b08_anonymous_memory.controller import MemoryController
from experiments.candidates.uav_fleet_transmission.b09_service_prediction import controller as module
from experiments.candidates.uav_fleet_transmission.b09_service_prediction import nominal
from experiments.candidates.uav_fleet_transmission.b09_service_prediction.model import LawfulServiceModel
from experiments.candidates.uav_fleet_transmission.b09_service_prediction.contract import equal
from experiments.candidates.uav_joint_transition import motion
from experiments.candidates.uav_radio_placement.b01.placement import best_geometric_centers


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


def propose(controller, obs, step, modes=None):
    old = obs.copy()
    action = controller.propose(obs, Poison(), step, Poison(),
                                np.zeros(8, dtype=bool) if modes is None else modes)
    np.testing.assert_array_equal(obs, old)
    return action


@pytest.fixture(scope="module", autouse=True)
def measured_work(record_testsuite_property):
    module.TOTALS.clear()
    yield
    text = json.dumps(module.TOTALS, sort_keys=True)
    record_testsuite_property("b09_controller_check_counts", text)
    print("B09 controller/reference attempted-call totals: " + text)
    assert module.TOTALS.get("candidate_forecasts", 0) <= 512
    assert module.TOTALS.get("lloyd_solves", 0) <= 512
    assert module.TOTALS.get("proposals", 0) <= 1024
    assert module.TOTALS.get("canonicalizations", 0) <= 1024
    assert module.TOTALS.get("associations", 0) <= 1024


def counted_reference(controller, observations, step, modes=None):
    module.TOTALS["proposals"] = module.TOTALS.get("proposals", 0) + 1
    if step % 30 == 0:
        module.TOTALS["canonicalizations"] = module.TOTALS.get("canonicalizations", 0) + 1
        if np.any(observations[:, S7S2_LAYOUT.users]):
            module.TOTALS["lloyd_solves"] = module.TOTALS.get("lloyd_solves", 0) + 1
    return propose(controller, observations, step, modes)


def test_c_is_exact_retained_controller_and_bs_precedence():
    actual, reference = module.CController(), MemoryController("C")
    for step in range(61):
        users = [(1100. + i * 100., 1200. + i * 90.) for i in range(6)]
        obs = frame(users, bs=(3300., 5200.) if step in (7, 60) else None)
        modes = np.zeros(8, dtype=bool)
        modes[6:] = step >= 30
        a = propose(actual, obs, step, modes)
        b = counted_reference(reference, obs, step, modes)
        assert a.tobytes() == b.tobytes()
        assert actual.targets_xy.tobytes() == reference.targets_xy.tobytes()
        assert actual.diagnostics == reference.diagnostics
    assert [row["bs_input_source"] for row in actual.diagnostics] == [
        "inferred", "observed-memory", "observed-current"]
    assert actual.audit_arrays()["candidate_records"].size == 0


def moving_frames():
    result = []
    for step in range(31):
        users = [] if step == 0 else [(1100. + step, 1200.), (1600. + 2 * step, 1500.)]
        if step >= 29:
            users = users[:1]  # Retained second track must advance to common estimated now.
        result.append(frame(users, bs=(1000., 1000.) if step == 7 else None))
    return result


@pytest.mark.parametrize("arm", ["H", "F"])
def test_nonempty_full_search_and_every_candidate_replay(arm):
    observations = moving_frames()
    first, replay = module.ServiceController(arm), module.ServiceController(arm)
    try:
        actions = [propose(first, obs, step) for step, obs in enumerate(observations)]
        records = first.audit_arrays()["candidate_records"]
        assert len(records) == 100
        assert records["completed"].all()
        assert np.all(records["ticks"] == 30)
        assert np.all(records["rf_completed"] == 3)
        assert np.count_nonzero(records["selected"]) == 1
        assert records["kind"][:4].tolist() == [0, 1, 2, 3]
        assert first.counters["model_rf_calls"] == 300
        assert first.counters["model_constructions"] == 1
        trace = first.last_trace
        tracks = trace["tracks"]
        now = np.clip(tracks["last_xy"] + (30 - tracks["last_seen"])[:, None] * tracks["v"], 0, 8000)
        np.testing.assert_array_equal(trace["plan_supplied_xy"], now)
        assert np.any(now != tracks["last_xy"])
        for index, tau in enumerate((10, 20, 30)):
            expected = now if arm == "H" else np.clip(
                tracks["last_xy"] + (30 - tracks["last_seen"] + tau)[:, None] * tracks["v"], 0, 8000)
            np.testing.assert_array_equal(first.last_decision["future_xy"][index], expected)
        assert first.diagnostics[-1]["bs_input_source"] == "observed-memory"
        replay.replay_prefix = records
        for step, obs in enumerate(observations):
            assert propose(replay, obs, step).tobytes() == actions[step].tobytes()
        for name in records.dtype.names:
            equal(replay.audit_arrays()["candidate_records"][name], records[name], name)
        assert first.counters == replay.counters
    finally:
        first.close()
        replay.close()


def test_sparse_geometric_seed_uses_original_eight_lloyd_starts():
    observations = frame()
    own = own_positions(observations)
    modes = np.zeros(8, dtype=bool)
    modes[7] = True
    previous = np.full((8, 2), np.nan)
    counts = module.CostDict()
    for q in (1, 2, 5, 6, 30):
        users = np.column_stack((1100. + 20 * np.arange(q), 1200. + 13 * np.arange(q)))
        centers, populations, info = module.best_centers(users, min(6, q), counts)
        # The frozen implementation is independently executed once per cardinality.
        module.TOTALS["lloyd_solves"] = module.TOTALS.get("lloyd_solves", 0) + 8
        expected_centers, expected_populations, expected_info = best_geometric_centers(users, min(6, q))
        np.testing.assert_array_equal(centers, expected_centers)
        np.testing.assert_array_equal(populations, expected_populations)
        assert info == {key: expected_info[key] for key in info}
        targets, _ = module.geometric_seed(observations, modes, users, np.array([1000., 1000.]), previous, counts)
        assert np.isfinite(targets[~modes]).all()
        assert np.isnan(targets[modes]).all()
        layout = module._layout(targets, own, modes)
        np.testing.assert_array_equal(layout[modes], own[modes])


@pytest.mark.parametrize("users,stations", [
    ([], ((7000., 500., 100.), (1000., 7000., 100.))),
    ([(1100., 1200.), (1600., 1500.)], (None, (1000., 7000., 100.))),
])
def test_fallbacks_are_original_h1_and_do_no_candidate_or_rf_work(users, stations):
    first = module.ServiceController("F")
    reference = MemoryController("C")
    try:
        obs = frame(users, stations=stations)
        for step in range(3):
            modes = np.zeros(8, dtype=bool)
            modes[7] = step < 2  # Original fallback handles an F exit between replans.
            actual = propose(first, obs, step, modes)
            expected = counted_reference(reference, obs, step, modes)
            assert actual.tobytes() == expected.tobytes()
        assert first.counters.get("candidate_forecasts", 0) == 0
        assert first.counters.get("model_rf_calls", 0) == 0
        assert first.last_decision["fallback"] == (1 if not users else 2)
    finally:
        first.close()


def test_missing_necessary_station_is_explicit_before_search():
    controller = module.ServiceController("H")
    try:
        obs = frame([(1100., 1200.)], bs=(1000., 1000.), stations=((7000., 500., 100.), None))
        with pytest.raises(ValueError, match="two valid"):
            propose(controller, obs, 0)
        assert controller.counters.get("candidate_forecasts", 0) == 0
    finally:
        controller.close()


def test_all_prior_f_preserves_duplicate_starts_and_original_first_tie():
    controller = module.ServiceController("H")
    try:
        obs = frame([(1100., 1200.), (1600., 1500.)])
        propose(controller, obs, 0, np.ones(8, dtype=bool))
        records = controller.audit_arrays()["candidate_records"]
        assert len(records) == 4
        assert records["kind"].tolist() == [0, 1, 2, 3]
        assert records["selected"].tolist() == [True, False, False, False]
        assert records["accepted"].tolist() == [True, False, False, False]
        for row in records:
            np.testing.assert_array_equal(row["targets"], own_positions(obs))
        np.testing.assert_array_equal(records["score"], np.repeat(records["score"][0], 4))
        assert controller.counters["model_rf_calls"] == 12
    finally:
        controller.close()


@pytest.mark.parametrize("failure_stage", ["nominal", "third_rf", "travel"])
def test_actual_interrupted_candidate_replays_only_completed_prefix(monkeypatch, failure_stage):
    first, replay = module.ServiceController("H"), module.ServiceController("H")
    try:
        first.model = LawfulServiceModel(first._counts)
        replay.model = LawfulServiceModel(replay._counts)
        obs = frame([(1100., 1200.), (1600., 1500.)])
        start = motion.legal_start(obs)
        target = start["xyz"].copy()
        target[:, 0] = np.clip(target[:, 0] + 300., 0., 8000.)
        future = np.repeat(np.asarray([[[1100., 1200.], [1600., 1500.]]]), 3, axis=0)
        arguments = (0, 0, 0, target, start, np.zeros(8, dtype=bool), future, np.array([1000., 1000.]))
        with monkeypatch.context() as patch:
            if failure_stage == "nominal":
                original = module.forecast

                def interrupted(*args, **kwargs):
                    original_tick = kwargs["on_tick"]

                    def stop(tick, digest):
                        original_tick(tick, digest)
                        if tick == 7:
                            raise RuntimeError("synthetic nominal interruption")

                    kwargs["on_tick"] = stop
                    return original(*args, **kwargs)

                patch.setattr(module, "forecast", interrupted)
            elif failure_stage == "third_rf":
                original = first.model.raw._update_channel_state
                attempts = []

                def interrupted():
                    attempts.append(None)
                    if len(attempts) == 3:
                        raise RuntimeError("synthetic RF interruption")
                    return original()

                patch.setattr(first.model.raw, "_update_channel_state", interrupted)
            else:
                def interrupted(*args):
                    raise RuntimeError("synthetic travel interruption")

                patch.setattr(module, "_travel", interrupted)
            with pytest.raises(RuntimeError, match="synthetic"):
                first._query(*arguments)
        saved = first.audit_arrays()["candidate_records"].copy()
        assert not saved["completed"].any()
        replay.replay_prefix = saved
        with pytest.raises(module.ReplayBoundary):
            replay._query(*arguments)
        rebuilt = replay.audit_arrays()["candidate_records"]
        for name in saved.dtype.names:
            if name != "rf_started":
                equal(rebuilt[name], saved[name], "partial/" + name)
        assert rebuilt["rf_started"][0] == saved["rf_completed"][0]
        assert replay.counters.get("model_rf_calls", 0) == saved["rf_completed"][0]
        assert replay.counters["joint_forecast_ticks_completed"] == saved["ticks"][0]
    finally:
        first.close()
        replay.close()


def test_audited_nominal_equals_retained_motion_and_preserves_allocator_order():
    counts = module.CostDict()
    model = LawfulServiceModel(counts)
    try:
        for scenario in range(3):
            start = motion.legal_start(frame())
            prior = np.zeros(8, dtype=bool)
            if scenario == 1:
                start["xyz"][:] = start["stations"][0]
                start["battery"][:] = .2
                start["margin"][:] = 0.
                start["waits"][:] = [1, 7, 7, 0, 0, 0, 0, 0]
                prior[:] = True
            elif scenario == 2:
                start["battery"][:] = [.5, .2, .1, .05, .01, .001, 0., .8]
                start["margin"][:] = [-.1, .01, .05, .1, .2, .3, .4, .5]
            targets = start["xyz"].copy()
            targets[:, 0] = np.clip(targets[:, 0] + 1100., 0, 8000)
            targets[:, 2] = 150.
            mode = np.zeros(8, dtype=np.int64)
            module.bump(counts, "candidate_forecasts")
            actual, digest = nominal.forecast(start, targets, mode, prior, model.raw, counters=counts)
            module.bump(counts, "candidate_forecasts")
            module.bump(counts, "joint_forecast_ticks", 30)
            expected = motion.forecast(start, targets, mode, prior, model.raw)
            module.bump(counts, "joint_forecast_ticks_completed", 30)
            for field in fields(actual):
                equal(getattr(actual, field.name), getattr(expected, field.name), field.name)
            assert len(digest) == 64
            if scenario == 1:
                assert actual.battery[0, 1] > actual.battery[0, 0]
                # The initial equal-battery/equal-wait tie charges UAV1 before
                # UAV2. Recomputed margin then exits F; no fair cycling promise.
                assert actual.battery[0, 1] > actual.battery[0, 2]
                assert not actual.F[0].any()
    finally:
        model.close()
