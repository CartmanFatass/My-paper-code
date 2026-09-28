"""Frozen program identities and telemetry must leave native behavior unchanged."""

from __future__ import annotations

from copy import copy
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.energy_relay_availability.b04.transit_hold import TransitHoldController
from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world, make_eval_config
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_energy_coordination.b01.controller import AnalyticalController
from experiments.candidates.uav_energy_coordination.b01.runner import CoordinationObserver
from experiments.candidates.uav_energy_coordination.b02 import controller as module
from experiments.candidates.uav_service_auxiliary.b01.native import make_env


def test_source_identity_is_exact_and_drift_is_visible(monkeypatch):
    records = module.source_records()
    assert len(records['sha256']) == 7
    first = next(iter(module.FROZEN_SHA256))
    monkeypatch.setitem(module.FROZEN_SHA256, first, 'different')
    with pytest.raises(ValueError, match='frozen I/P source differs'):
        module.source_records()


def test_rejects_an_added_arm_before_construction():
    with pytest.raises(ValueError, match='only frozen I and P'):
        module.FrozenController('C', None, None)


def test_p_costs_keep_shared_q0_and_do_not_invent_model_steps():
    wrapped = object.__new__(module.FrozenController)
    wrapped.arm = 'P'
    wrapped.base = SimpleNamespace(
        plan_input_steps=[0, 10, 20],
        heuristic=SimpleNamespace(service_snapshot_calls=24, decision_records=[
            {'fallback': None, 'candidate_count': 9, 'snapshot_calls': 19},
            {'fallback': 'return_shield_active', 'candidate_count': 1, 'snapshot_calls': 0},
            {'fallback': None, 'candidate_count': 2, 'snapshot_calls': 5},
        ]))
    wrapped._reset_telemetry()
    costs = wrapped.costs
    assert costs['score_requests'] == costs['model_evaluations'] == 11
    assert costs['service_snapshots'] == 24
    assert costs['p_shared_baseline_snapshots'] == 2
    assert costs['p_projected_positions'] == 22
    assert costs['decision_clocks'] == costs['central_input_calls'] == 3
    assert costs['primitive_forecast_steps'] == costs['event_count'] == 0
    wrapped.base.heuristic.service_snapshot_calls += 1
    assert wrapped.costs['service_snapshots'] == 25  # Known partial-clock work is not lost.


@pytest.mark.parametrize('arm', ['I', 'P'])
def test_wrapper_preserves_seeded_native_trajectory_and_decisions(arm):
    results = []
    for instrumented in (False, True):
        config = make_eval_config(3000, 0)
        fixture_config = copy(config)
        fixture_config.episode_length = 12
        env = make_env(config, 70292)
        policy = (module.FrozenController(arm, env, config) if instrumented else
                  AnalyticalController('I', env, config) if arm == 'I' else
                  TransitHoldController(env))
        observer = CoordinationObserver(env.env)
        try:
            # Keep the H3000 model/physics, but stop this identity fixture after 12 steps.
            with pytest.raises(RuntimeError, match='did not reach native termination/truncation'):
                    evaluate_world(policy, env, fixture_config, 70292, PRODUCTION_PARAMS,
                               observer=observer)
            observed = observer.as_arrays()
            results.append((observed, observer.digests()))
            if instrumented:
                arrays = policy.validate_trace(12)
                expected = [0] if arm == 'I' else [0, 10]
                assert arrays['telemetry_step'].tolist() == expected
                assert policy.costs['controller_ticks'] == 12
                assert policy.costs['central_input_calls'] == len(expected)
                assert policy.costs['controller_wall_seconds'] >= policy.costs['decision_tick_wall_seconds']
                if arm == 'P':
                    assert policy.costs['service_snapshots'] == int(arrays['transit_snapshot_calls'].sum())
                    assert policy.costs['service_snapshots'] <= 38
                policy.reset()
                assert policy.costs['controller_ticks'] == 0
                assert policy.costs['service_snapshots'] == 0
        finally:
            close = getattr(policy, 'close', None)
            if close is not None:
                close()
            env.close()
    for field in ('observed_native_reward', 'observed_native_metrics', 'observed_battery_ratio',
                  'proposed_actions', 'submitted_actions', 'actual_xyz_post_m', 'user_xy_m'):
        np.testing.assert_array_equal(results[0][0][field], results[1][0][field])
    assert results[0][1] == results[1][1]
