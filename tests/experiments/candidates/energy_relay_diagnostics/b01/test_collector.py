from dataclasses import replace
import json

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b02 import configuration as cfg
from experiments.candidates.energy_relay_benchmark.b02 import training
from experiments.candidates.energy_relay_diagnostics.b01.collector import evaluate_collector_task
from experiments.candidates.energy_relay_diagnostics.b01.instrumentation import ActionInputRecorder


def task_fixture(tmp_path, horizon=40):
    torch.set_num_threads(1)
    config = cfg.apply_set_switch(ev.make_eval_config(horizon, 925031))
    config.ordinary_completed_segments = False
    ev.seed_everything(925031, torch.device("cpu"))
    agent = ev.HMASDAgent(config, log_dir=str(tmp_path / "source"), device=torch.device("cpu"))
    pt = tmp_path / "agent.pt"
    agent.save_model(pt)
    record = {"config": cfg.config_dict(config), "agent_pt_sha256": ev.sha256_file(pt),
              "policy_fingerprint": ev.initialization_fingerprint(agent),
              "checkpoint": "c00", "rollout": 0, "transitions": 0}
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(record))
    return ev.WorldTask(controller="L", seed=953001, params=PRODUCTION_PARAMS,
                        horizon=horizon, policy_seed=925031, threads=1, checkpoint=str(pt),
                        checkpoint_record=str(record_path), log_dir=str(tmp_path),
                        action_mode="stochastic", draw=0)


def test_actual_storage_path_matches_evaluator_without_update(tmp_path, monkeypatch):
    task = task_fixture(tmp_path)
    original_factory = training.make_env

    def forbidden_update(*args, **kwargs):
        raise AssertionError("a frozen probe must never reach HMASDAgent.update")

    monkeypatch.setattr(ev.HMASDAgent, "update", forbidden_update)
    evaluator = ev.evaluate_task(task, observer_factory=lambda task: ActionInputRecorder(
        capture_inputs=True, capture_held_snapshot=True))
    collector = evaluate_collector_task(task, capture_inputs=True)
    assert training.make_env is original_factory
    assert collector["row"]["optimizer_updates"] == 0
    assert collector["row"]["skipped_update_calls"] == 1
    assert collector["identity"] == evaluator["identity"]
    for key, value in evaluator["arrays"].items():
        np.testing.assert_array_equal(value, collector["arrays"][key], err_msg=key)
    for key, value in evaluator["observation"].items():
        np.testing.assert_array_equal(value, collector["observation"][key], err_msg=key)
    for key, value in evaluator["row"].items():
        if key not in ("wall_seconds", "worker_peak_rss_kib"):
            assert value == collector["row"][key], key


def test_forbidden_world_and_mode_rejected_before_load(tmp_path):
    task = task_fixture(tmp_path, horizon=10)
    with pytest.raises(ValueError, match="sealed"):
        evaluate_collector_task(replace(task, seed=957001))
    with pytest.raises(ValueError, match="stochastic"):
        evaluate_collector_task(replace(task, action_mode="deterministic"))


def test_factory_restored_after_collector_failure(tmp_path, monkeypatch):
    task = task_fixture(tmp_path, horizon=10)
    original_factory = training.make_env

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic collector failure")

    monkeypatch.setattr(training, "collect_and_train", fail)
    with pytest.raises(RuntimeError, match="synthetic collector"):
        evaluate_collector_task(task)
    assert training.make_env is original_factory


def test_early_native_ending_is_retained_after_storage(tmp_path, monkeypatch):
    task = task_fixture(tmp_path, horizon=40)
    factory = training.make_env

    class EarlyEnv:
        def __init__(self, native):
            self.native = native

        def __getattr__(self, key):
            return getattr(self.native, key)

        def step(self, action):
            obs, reward, _, _, info = self.native.step(action)
            return obs, reward, True, False, info

    monkeypatch.setattr(training, "make_env", lambda config, seed: EarlyEnv(factory(config, seed)))
    result = evaluate_collector_task(task)
    assert result["row"]["actual_length"] == result["row"]["stored_transitions"] == 1
    assert result["row"]["terminal_type"] == "terminated"
    assert result["row"]["early_native_ending"] is True
    assert result["row"]["optimizer_updates"] == result["row"]["skipped_update_calls"] == 0
    assert result["arrays"]["ends"].tolist() == [[True, False]]
