from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b01.feedback import FeedbackParams
from experiments.candidates.energy_relay_benchmark.b01.heuristic import VARIANTS
from experiments.candidates.energy_relay_benchmark.b01.observation import own_positions
from experiments.candidates.energy_relay_diagnostics.b01.instrumentation import ActionInputRecorder
from experiments.candidates.uav_service_auxiliary.b01.native import make_env, seed_everything
from hmasd.agent import HMASDAgent
from hmasd.baselines import apply_algorithm_config


POLICY_SEED = 925031
WORLD_SEED = 955001
SHIELD = FeedbackParams(100.0, 101.0)


def _same_native(left, right):
    assert {key: value for key, value in left["row"].items()
            if key not in {"wall_seconds", "worker_peak_rss_kib"}} == {
                key: value for key, value in right["row"].items()
                if key not in {"wall_seconds", "worker_peak_rss_kib"}}
    assert left["identity"] == right["identity"]
    assert left["arrays"].keys() == right["arrays"].keys()
    for key in left["arrays"]:
        assert np.array_equal(left["arrays"][key], right["arrays"][key]), key


@pytest.fixture
def checkpoint(tmp_path):
    config = ev.make_eval_config(12, POLICY_SEED)
    seed_everything(POLICY_SEED, torch.device("cpu"))
    agent = HMASDAgent(config, log_dir=str(tmp_path / "agent"), device=torch.device("cpu"))
    path = tmp_path / "agent.pt"
    agent.save_model(path)
    return path


@pytest.mark.parametrize("mode,draw", [("deterministic", None), ("stochastic", 0)])
def test_learned_task_observation_keeps_native_and_rng(tmp_path, checkpoint, mode, draw):
    task = ev.WorldTask(controller="N", seed=WORLD_SEED, params=SHIELD, horizon=12,
                        policy_seed=POLICY_SEED, threads=1, checkpoint=str(checkpoint),
                        log_dir=str(tmp_path), action_mode=mode, draw=draw)
    before = ev.evaluate_task(task)
    numpy_before = np.random.get_state()
    torch_before = torch.get_rng_state().clone()
    observed = ev.evaluate_task(task, observer_factory=lambda _: ActionInputRecorder())
    _same_native(before, observed)
    assert np.array_equal(torch_before, torch.get_rng_state())
    numpy_after = np.random.get_state()
    assert all(np.array_equal(a, b) for a, b in zip(numpy_before, numpy_after))
    trace = observed["observation"]
    assert trace["t"].tolist() == list(range(12))
    assert trace["proposal_t"].shape == trace["submitted_t"].shape == (12, 8, 4)
    assert trace["own_xyz_t"].shape == trace["own_xyz_t1"].shape == (12, 8, 3)
    assert np.array_equal(trace["own_xyz_t"], observed["arrays"]["own_xyz"])
    assert np.array_equal(trace["own_xyz_t"][1:], trace["own_xyz_t1"][:-1])
    assert trace["actor_mean_raw"].shape == trace["actor_scale_raw"].shape == (12, 8, 4)
    assert (trace["actor_scale_raw"] > 0).all()
    assert trace["actor_distribution"] == "tanh_gaussian"
    assert "observations_t" not in trace and "held_state" not in trace
    if mode == "deterministic":
        np.testing.assert_allclose(trace["proposal_t"], np.tanh(trace["actor_mean_raw"]),
                                   rtol=0, atol=1e-7)
    else:
        assert not np.array_equal(trace["proposal_t"], trace["actor_mean_raw"])


def test_shield_and_full_inputs_are_distinct_owned_times(tmp_path):
    task = ev.WorldTask(controller="Hlocal", seed=WORLD_SEED, params=SHIELD, horizon=20,
                        policy_seed=POLICY_SEED, threads=1,
                        heuristic=replace(VARIANTS["H1"], information="local"),
                        log_dir=str(tmp_path))
    plain = ev.evaluate_task(task)
    observed = ev.evaluate_task(task, observer_factory=lambda _: ActionInputRecorder(capture_inputs=True))
    _same_native(plain, observed)
    trace = observed["observation"]
    assert "actor_mean_raw" not in trace and "actor_distribution" not in trace
    assert trace["observations_t"].shape == trace["observations_t1"].shape == (20, 8, 365)
    assert trace["state_t"].shape == trace["state_t1"].shape
    assert np.array_equal(trace["observations_t"][1:], trace["observations_t1"][:-1])
    assert np.array_equal(trace["state_t"][1:], trace["state_t1"][:-1])
    assert np.array_equal(trace["own_xyz_t"], np.asarray([own_positions(obs)
                                                         for obs in trace["observations_t"]]))
    assert np.array_equal(trace["own_xyz_t1"], np.asarray([own_positions(obs)
                                                           for obs in trace["observations_t1"]]))
    assert np.any(trace["proposal_t"] != trace["submitted_t"])
    first = trace["observations_t"][0].copy()
    trace["observations_t"][0].fill(0)
    assert np.array_equal(trace["observations_t1"][0], trace["observations_t"][1])
    assert not np.array_equal(first, trace["observations_t"][0])


def _snapshot_agent(tmp_path):
    config = apply_algorithm_config(ev.make_eval_config(12, POLICY_SEED), "mappo")
    config.k = 10
    config.use_central_snapshot_in_flat_actor = True
    config.calculate_and_set_buffer_sizes()
    config.validate_config()
    seed_everything(POLICY_SEED, torch.device("cpu"))
    agent = HMASDAgent(config, log_dir=str(tmp_path / "snapshot-agent"), device=torch.device("cpu"))
    agent.train(False)
    return config, agent


def test_actual_tanh_head_snapshot_hold_and_hook_teardown(tmp_path):
    config, agent = _snapshot_agent(tmp_path)
    controller = ev.PolicyController(agent)
    recorder = ActionInputRecorder(capture_inputs=True, capture_held_snapshot=True)
    head = agent.skill_discoverer.actor.act.action_out
    original_hooks = (len(head.fc_mean._forward_hooks), len(head.logstd._forward_hooks))
    env = make_env(config, WORLD_SEED)
    try:
        row, _ = ev.evaluate_world(controller, env, config, WORLD_SEED, SHIELD,
                                   observer=recorder)
    finally:
        env.close()
    trace = recorder.as_arrays()
    assert row["actual_length"] == 12
    assert trace["actor_distribution"] == "tanh_gaussian"
    assert trace["held_source_t"].tolist() == [0] * 10 + [10] * 2
    assert trace["held_age"].tolist() == list(range(10)) + [0, 1]
    assert np.array_equal(trace["held_state"][0], trace["held_state"][9])
    assert np.array_equal(trace["held_observations"][0], trace["held_observations"][9])
    assert np.array_equal(trace["held_state"][0], trace["state_t"][0])
    assert np.array_equal(trace["held_observations"][10], trace["observations_t"][10])
    np.testing.assert_allclose(trace["proposal_t"], np.tanh(trace["actor_mean_raw"]),
                               rtol=0, atol=1e-7)
    assert (trace["actor_scale_raw"] > 0).all()
    assert (len(head.fc_mean._forward_hooks), len(head.logstd._forward_hooks)) == original_hooks

    def fail(*_args):
        raise RuntimeError("forced proposal failure")

    controller.propose = fail
    env = make_env(config, WORLD_SEED)
    try:
        with pytest.raises(RuntimeError, match="forced proposal failure"):
            ev.evaluate_world(controller, env, config, WORLD_SEED, SHIELD,
                              observer=ActionInputRecorder())
    finally:
        env.close()
    assert (len(head.fc_mean._forward_hooks), len(head.logstd._forward_hooks)) == original_hooks
