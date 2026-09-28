import json
from types import SimpleNamespace

import numpy as np

from experiments.candidates.energy_relay_availability.b04.transit_hold import TransitHoldController
from experiments.candidates.energy_relay_benchmark.b01.evaluation import make_eval_config
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    PRODUCTION_PARAMS, apply_feedback_params,
)
from experiments.candidates.uav_persistent_service.controllers import (
    Commitment, CommitmentController, DURATIONS, FEATURE_DIM, N_ACTIONS,
    _arrival_time, ordinary_dispatch,
)
from experiments.candidates.uav_service_auxiliary.b01.native import make_env


def _dispatch(*, deadlines, tau_in, tau_out, stations=None, eligible=None,
              free=None, remaining=3000, load=None):
    deadlines = np.asarray(deadlines, dtype=float)
    return ordinary_dispatch(
        np.ones(8, bool) if eligible is None else np.asarray(eligible, bool),
        np.ones(8, bool) if free is None else np.asarray(free, bool),
        np.zeros(8, int) if stations is None else np.asarray(stations, int),
        deadlines * 168.49 / (160 * 3600), np.full(8, 168.49),
        np.asarray(tau_in, float), np.asarray(tau_out, float),
        np.zeros(8) if load is None else np.asarray(load, float), remaining)


def test_corrected_ordinary_occupancy_and_rank():
    eligible = [True, False] + [False]*6
    free = [True, True] + [False]*6
    # Competitor D=600, tau=100 arrives at 700. Candidate's 100+600 fits.
    assert _dispatch(deadlines=[200, 600]+[9999]*6,
                     tau_in=[100, 100]+[0]*6, tau_out=[20, 20]+[0]*6,
                     eligible=eligible, free=free) == 3
    # D, rather than D-tau, orders the dispatchable members.
    assert _dispatch(deadlines=[100, 110]+[9999]*6,
                     tau_in=[90, 1]+[0]*6, tau_out=[0]*8,
                     stations=[0, 1]+[1]*6,
                     eligible=[True, True]+[False]*6,
                     free=[True, True]+[False]*6) == 3


def test_corrected_ordinary_restoration_horizon_and_missing_target():
    eligible = [True]+[False]*7
    free = eligible
    base = dict(deadlines=[100]+[9999]*7, tau_in=[100]+[0]*7,
                eligible=eligible, free=free)
    assert _dispatch(**base, tau_out=[280]+[0]*7, remaining=1000) == 3  # d=600
    assert _dispatch(**base, tau_out=[290]+[0]*7, remaining=1000) == 3  # equality
    assert _dispatch(**base, tau_out=[771]+[0]*7, remaining=1000) == 0
    assert _dispatch(**base, tau_out=[np.inf]+[0]*7) == 0
    assert _dispatch(deadlines=[1000]+[9999]*7, tau_in=[0]*8,
                     tau_out=[0]*8, eligible=eligible, free=free,
                     remaining=1000) == 0
    assert DURATIONS == (120, 300, 600)
    assert _arrival_time(np.zeros(3)) == 0


def test_option_elapsed_release_station_change_timeout_and_censor():
    controller = object.__new__(CommitmentController)
    controller.heuristic = SimpleNamespace(committed=np.zeros(8, bool), layout=None)
    controller.options = {0: Commitment(0, 0, 120, 0)}
    controller._pending_restoration = set()
    controller.events = []
    controller._last_observed_step = None
    controller._battery_history = __import__("collections").deque(maxlen=32)
    from experiments.candidates.uav_persistent_service import controllers as module
    original_energy = module.own_energy
    original_positions = module.own_positions
    original_decode = module.decode_legal_observations
    try:
        module.own_energy = lambda *_: {"battery": np.full(8, .5),
                                        "charging": np.zeros(8, bool)}
        module.own_positions = lambda *_: np.zeros((8, 3))
        nearest = np.zeros(8, int)
        distances = np.full(8, 100.)
        module.decode_legal_observations = lambda *_: (
            np.ones(8), np.full(8, .5), nearest, distances, np.zeros((8, 3)))
        nearest[0] = 1
        distances[0] = 20
        controller._observe(None, 20)
        assert controller.options[0].station == 1
        assert controller.options[0].arrival == 20
        distances[0] = 100
        controller._observe(None, 139)
        assert 0 in controller.options
        controller._observe(None, 140)
        assert 0 not in controller.options
        assert controller._pending_restoration == {0}
        assert [e["kind"] for e in controller.events] == ["station_change", "arrival", "release"]
        assert controller.events[-1]["dwell_elapsed"] == 120
        controller.options[1] = Commitment(1, 0, 600, 0)
        controller._observe(None, 900)
        assert controller.events[-1]["reason"] == "timeout_no_arrival"
        controller.options[3] = Commitment(3, 0, 600, 901)
        module.own_energy = lambda *_: {"battery": np.asarray([.5, .5, .5, 1.0]+[.5]*4),
                                        "charging": np.zeros(8, bool)}
        controller._observe(None, 902)
        assert controller.events[-1]["reason"] == "full"
        controller.options[2] = Commitment(2, 0, 600, 200)
        controller.finish(3000)
        assert controller.events[-1]["kind"] == "censored"
        assert controller.events[-1]["member"] == 2
        json.dumps(controller.events)
    finally:
        module.own_energy = original_energy
        module.own_positions = original_positions
        module.decode_legal_observations = original_decode


def test_native_no_commit_identity_seed_70293():
    steps, seed = 12, 70293
    config = make_eval_config(steps, policy_seed=0)
    original_env = make_env(config, seed)
    wrapper_env = make_env(config, seed)
    try:
        original = TransitHoldController(original_env)
        wrapper = CommitmentController(wrapper_env, config)
        original.reset()
        wrapper.reset()
        obs_p, state_p = original_env.reset(seed=seed)
        obs_w, state_w = wrapper_env.reset(seed=seed)
        modes_p = np.zeros(8, bool)
        modes_w = np.zeros(8, bool)
        for step in range(steps):
            np.testing.assert_array_equal(obs_p, obs_w)
            if step % 30 == 0:
                features = wrapper.prepare(obs_w, modes_w, step)
                assert features.shape == (FEATURE_DIM,)
                assert features.dtype == np.float32
                assert np.isfinite(features).all()
                assert len(features[:8]) == 8
                assert N_ACTIONS == 25
                decision = wrapper.apply_choice(0)
                assert decision["eligible"] == bool(features[:8].any())
                assert not decision["requested_member_eligible"]
                json.dumps(decision)
            action_p = original.propose(obs_p, state_p, step, None, modes_p)
            action_w = wrapper.propose(obs_w, state_w, step, None, modes_w)
            np.testing.assert_array_equal(action_p, action_w)
            np.testing.assert_array_equal(original.targets_xy, wrapper.targets_xy)
            decision_p = apply_feedback_params(obs_p, action_p, modes_p, PRODUCTION_PARAMS)
            decision_w = apply_feedback_params(obs_w, action_w, modes_w, PRODUCTION_PARAMS)
            np.testing.assert_array_equal(decision_p.submitted_actions, decision_w.submitted_actions)
            modes_p, modes_w = decision_p.modes, decision_w.modes
            obs_p, reward_p, term_p, trunc_p, _ = original_env.step(decision_p.submitted_actions)
            obs_w, reward_w, term_w, trunc_w, _ = wrapper_env.step(decision_w.submitted_actions)
            np.testing.assert_array_equal(reward_p, reward_w)
            np.testing.assert_array_equal((term_p, trunc_p), (term_w, trunc_w))
        np.testing.assert_array_equal(obs_p, obs_w)
        assert original.heuristic.service_snapshot_calls == wrapper.heuristic.service_snapshot_calls
        assert original.heuristic.calls == wrapper.heuristic.calls == steps
        assert wrapper.costs["source_calls"] == steps
        assert wrapper.costs["native_steps"] == steps
    finally:
        original_env.close()
        wrapper_env.close()


def test_native_commitment_excludes_assignment_without_f_fallback():
    steps, seed = 11, 70294
    config = make_eval_config(steps, policy_seed=0)
    env = make_env(config, seed)
    try:
        controller = CommitmentController(env, config)
        obs, state = env.reset(seed=seed)
        modes = np.zeros(8, bool)
        features = controller.prepare(obs, modes, 0)
        eligible = np.flatnonzero(features[:8])
        assert len(eligible) > 0
        member = int(eligible[0])
        action_id = 1 + member * 3
        decision = controller.apply_choice(action_id)
        assert decision["executed_action"] == action_id
        assert controller.commitment_snapshot()["active"][member]
        for step in range(steps):
            action = controller.propose(obs, state, step, None, modes)
            assert action[member, 3] == 1.0
            decision_f = apply_feedback_params(obs, action, modes, PRODUCTION_PARAMS)
            modes = decision_f.modes
            obs, _, _, _, _ = env.step(decision_f.submitted_actions)
        assert np.isnan(controller.heuristic.h1_targets_xy[member]).all()
        assert controller.heuristic.decision_records[-1]["fallback"] is None
        assert controller.costs["p_plan_calls"] == 2
        controller.finish(steps, obs, modes)
        assert controller.events[-1]["kind"] == "censored"
    finally:
        env.close()
