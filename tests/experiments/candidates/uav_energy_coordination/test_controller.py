"""Contract checks, not an exposed-world evaluation panel."""

import copy

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    central_plan_inputs,
    make_eval_config,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    apply_feedback_params,
    PRODUCTION_PARAMS,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_energy,
    own_positions,
)
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_energy_coordination.b01 import controller as module


def g(x, station=-1, kind="service"):
    return module.Goal((float(x), 0.0, 100.0), station, kind)


def test_independent_joint_veto_uses_best_single_not_bad_assembly():
    base = (g(0), g(0))
    values = {(0, 0): 0, (1, 0): 2, (0, 1): 1, (1, 1): -10}
    calls = []

    def score(plan):
        key = tuple(goal.xyz[0] for goal in plan)
        calls.append(key)
        return values[key]

    result, value = module.improve_goals("I", base, [(g(0), g(1))] * 2, score, 0, 0)
    assert result == (g(1), g(0)) and value == 2
    assert calls == [(0, 0), (1, 0), (0, 0), (0, 1), (1, 1)]


def test_conditioning_and_cyclic_order_are_real_and_only_one_sweep():
    base = (g(0), g(0))
    options = [(g(0), g(1)), (g(0), g(1), g(2))]
    values = {(0, 0): 0, (1, 0): 2, (0, 1): 1, (0, 2): .5,
              (1, 1): 3, (1, 2): 5}
    score = lambda plan: values[tuple(goal.xyz[0] for goal in plan)]
    assert module.improve_goals("I", base, options, score, 0, 0) == ((g(1), g(1)), 3)
    assert module.improve_goals("C", base, options, score, 0, 0) == ((g(1), g(2)), 5)
    assert module.improve_goals("C", base, options, score, 1, 0) == ((g(1), g(1)), 3)


@pytest.mark.parametrize("arm", ["I", "C"])
def test_exact_ties_keep_incumbent_and_float64_small_gain_survives(arm):
    base = (g(0),)
    assert module.improve_goals(arm, base, [(g(1),)], lambda _: 0., 0, 0.) == (base, 0.)
    result, gain = module.improve_goals(arm, base, [(g(1),)], lambda _: 1e-15, 0, 0.)
    assert result == (g(1),) and gain == 1e-15
    with pytest.raises(FloatingPointError):
        module.improve_goals(arm, base, [(g(1),)], lambda _: np.nan, 0, 0.)


def test_library_bounds_and_semantic_station_dedup():
    inputs = dict(users_xy=np.arange(60).reshape(30, 2) * 100., bs_xy=np.zeros((1, 2)))
    stations = np.asarray([[100., 200., 50.], [300., 400., 50.]])
    library = module.goal_library(inputs, stations)
    assert len(library) <= 16
    assert sum(item.station >= 0 for item in library) == 2
    options = module.unique_goals((g(-1), *library, g(-2)))
    assert len(options) <= 18 and options[0] == g(-1)
    assert module.unique_goals((g(0), g(0, kind="hold"), g(0, station=0))) == (g(0), g(0, station=0))


@pytest.fixture
def native():
    config = make_eval_config(120, policy_seed=0)
    env = make_env(config, 70191)
    obs, _ = env.reset(seed=70191)
    try:
        yield config, env, obs
    finally:
        env.close()


def assert_rng_same(a, b):
    assert a[0] == b[0]
    np.testing.assert_array_equal(a[1], b[1])
    assert a[2:] == b[2:]


def test_snapshot_public_inputs_only_and_order_independent(native):
    config, env, observations = native
    raw = env.env
    inputs = central_plan_inputs(env)
    positions = own_positions(observations)
    battery = own_energy(observations)["battery"]
    before = copy.deepcopy((raw.user_positions, raw.uav_positions, raw.connections,
                            raw.routing_paths, raw.np_random.get_state()))
    global_rng = np.random.get_state()
    scorer = module.NativeSnapshotScorer(config)
    try:
        expected = scorer.qos(inputs, positions, battery)
        changed = positions.copy()
        changed[0] += [150, 150, 0]
        scorer.qos(inputs, changed, battery)
        scorer.raw.user_serving_sets = [list(range(8)) for _ in range(30)]
        scorer.raw.connections.fill(True)
        assert scorer.qos(inputs, positions, battery) == expected
        scorer.raw.uav_charging[:] = True
        assert scorer.qos(inputs, positions, battery) == expected
        assert 0 <= expected <= 1
        assert not np.shares_memory(scorer.raw.user_positions, raw.user_positions)
        assert not np.shares_memory(scorer.raw.uav_positions, raw.uav_positions)
        for actual, original in zip((raw.user_positions, raw.uav_positions, raw.connections), before[:3]):
            np.testing.assert_array_equal(actual, original)
        assert raw.routing_paths == before[3]
        assert_rng_same(raw.np_random.get_state(), before[4])
        assert_rng_same(np.random.get_state(), global_rng)
        # Native communication availability depends on battery, not dock/charge.
        scorer.qos(inputs, positions, np.full(8, .01))
        assert scorer.raw._communication_unavailable_mask().all()
        assert scorer.qos(inputs, positions, np.full(8, .01)) == 0
    finally:
        scorer.close()


def test_executor_caps_station_request_and_unchanged_shield(native):
    _, _, obs = native
    stations = module.decode_stations(obs)
    positions = own_positions(obs)
    chosen = np.linalg.norm(positions[:, None, :] - stations, axis=2).argmin(axis=1)
    goals = tuple(module.Goal(tuple(stations[1 - index]), 1 - int(index), "station") for index in chosen)
    actions = module.track_goals(obs, goals)
    assert np.all(actions[:, 3] == 0)
    assert np.all(np.linalg.norm(actions[:, :2], axis=1) <= 1 + 1e-7)
    assert np.all(np.abs(actions[:, 2]) <= 1)
    goals = tuple(module.Goal(tuple(stations[index]), int(index), "station") for index in chosen)
    actions = module.track_goals(obs, goals)
    assert np.all(actions[:, 3] == 1)
    low = obs.copy()
    energy = low[:, -120:-16].reshape(8, 8, 13)
    energy[np.arange(8), np.arange(8), 12] = -.01
    ordinary = module.track_goals(low, tuple(g(4000) for _ in range(8)))
    decision = apply_feedback_params(low, ordinary, np.zeros(8, dtype=bool), PRODUCTION_PARAMS)
    assert decision.modes.all() and np.all(decision.submitted_actions[:, 3] == 1)


@pytest.mark.parametrize("arm", ["I", "C"])
def test_controller_clock_bounds_and_no_hidden_step(native, monkeypatch, arm):
    config, env, observations = native
    controller = module.AnalyticalController(arm, env, config)
    # This is a full integration of the analytical solver/search with synthetic
    # service, not a scientific episode or native outcome comparison.
    calls = []
    original = module.central_plan_inputs
    monkeypatch.setattr(module, "central_plan_inputs", lambda source: (calls.append(source), original(source))[1])
    monkeypatch.setattr(controller.scorer, "qos", lambda inputs, xyz, battery: float(np.mean(battery)))
    monkeypatch.setattr(controller.scorer.env, "step", lambda *_: pytest.fail("planning called env.step"))
    try:
        for step in (0, 1, 59, 60):
            result = controller.propose(observations, None, step, None, np.zeros(8, dtype=bool))
            assert result.shape == (8, 4) and np.isfinite(result).all()
        assert controller.plan_input_steps == [0, 60] and len(calls) == 2
        records = controller.decision_records
        assert [record["horizon"] for record in records] == [120, 60]
        assert all(record["score_requests"] <= module.MAX_REQUESTS[arm] for record in records)
        assert controller.costs["service_snapshots"] == 3 * controller.costs["model_evaluations"]
        assert all(record["selected_score"] >= record["incumbent_score"] for record in records)
        arrays = controller.decision_arrays()
        assert arrays["planner_selected_positions"].shape == (2, 3, 8, 3)
        assert not any(array.dtype == object for array in arrays.values())
    finally:
        controller.close()


def test_short_native_episode_observer_and_exogenous_pairing():
    from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
        HeuristicController, evaluate_world,
    )
    from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
    from experiments.candidates.uav_energy_coordination.b01.runner import CoordinationObserver
    from experiments.candidates.uav_energy_coordination.b01.readout import enrich_world

    config = make_eval_config(6, policy_seed=0)
    records = []
    for arm in ("H", "I", "C"):
        env = make_env(config, 70192)
        controller = None
        try:
            controller = (HeuristicController(variant("H1", information="central"), env)
                          if arm == "H" else module.AnalyticalController(arm, env, config))
            observer = CoordinationObserver(env.env)
            row, steps = evaluate_world(controller, env, config, 70192,
                                        PRODUCTION_PARAMS, observer=observer)
            observed = observer.as_arrays()
            decisions = {} if arm == "H" else controller.decision_arrays()
            enriched = enrich_world(row, steps, observed, decisions,
                                     reserve_ratio=.1, cutoff_ratio=.02, time_step=1.)
            assert row["actual_length"] == 6
            assert observed["proposed_actions"].shape == (6, 8, 4)
            assert observed["actual_xyz_post_m"].shape == (6, 8, 3)
            assert observed["actual_user_delivered_ratio"].shape == (6, 30)
            assert enriched["energy_consumed_wh"] > 0
            assert np.isfinite(steps["metrics"]).all()
            records.append(observer.digests())
        finally:
            if controller is not None and hasattr(controller, "close"):
                controller.close()
            env.close()
    assert records[0] == records[1] == records[2]
