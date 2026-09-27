"""Failure-only B01 evidence without a research run or arbitrary local dumps."""

from __future__ import annotations

import errno
import json
import random
import sys
from dataclasses import replace
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_baselines.b01 import configuration as cfg
from experiments.candidates.energy_relay_baselines.b01 import diagnostics, run, training
from experiments.candidates.energy_relay_benchmark.b02 import training as collector
from experiments.candidates.uav_service_auxiliary.b01.native import sha256_file


def _short_spec():
    return replace(cfg.production_spec(cfg.TRAINING_SEEDS[0]), rollouts=1,
                   rollout_length=2, episode_length=20, checkpoint_every_transitions=4)


def test_partial_collector_failure_keeps_original_counts_scalars_and_rng(tmp_path, monkeypatch):
    spec = _short_spec()
    output = tmp_path / f"seed-{spec.seed}"
    make_env = collector.make_env
    lanes = []
    at_failure = {}

    def _wrapfunc():
        obj = np.float64(0.5)
        at_failure["torch"] = torch.get_rng_state().clone()
        at_failure["numpy"] = np.random.get_state()
        at_failure["python"] = random.getstate()
        raise SystemError("injected scalar clip failure")

    def clip():
        a = np.float64(0.5)
        a_min, a_max = 0, 1
        return _wrapfunc()

    def _get_observation_cached_body():
        sinr_db = np.float64(15.0)
        return clip()

    def instrumented_env(config, seed):
        env = make_env(config, seed)
        lanes.append(env)
        if len(lanes) == 2:
            env.step = lambda actions: _get_observation_cached_body()
        return env

    monkeypatch.setattr(collector, "make_env", instrumented_env)
    with pytest.raises(SystemError, match="injected scalar clip failure") as raised:
        training.run_training(out=output, launch_sha="test-source-sha", spec=spec,
                              device_name="cpu", threads=1, argv=["test"])
    assert raised.value.__traceback__ is not None
    summary = json.loads((output / "summary.json").read_text())
    context_path = output / "failure-context.json"
    context = json.loads(context_path.read_text())
    assert summary["status"] == "INCOMPLETE"
    assert summary["counts"] == {"transitions": 0, "rollouts": 0,
                                 "native_episodes": 0, "checkpoints": 1}
    assert summary["artifacts"]["failure-context.json"] == sha256_file(context_path)
    assert context["completed_stored_counts"] == summary["counts"]
    assert context["collector"] == {"rollout": 1, "step": 0, "lane": 1,
                                    "partial_observed_counts": {"transitions": 1,
                                                                "rollouts": 0, "native_episodes": 0}}
    assert context["exception_type"] == "builtins.SystemError"
    names = [row["function"] for row in context["traceback"]["locations"]]
    assert "collect_and_train" in names and "_get_observation_cached_body" in names
    scalar = {row["function"]: row["values"] for row in context["scalar_frames"]}
    assert scalar["_get_observation_cached_body"]["sinr_db"]["value"] == 15.0
    assert scalar["clip"]["a"]["value"] == 0.5
    assert scalar["clip"]["a_min"]["value"] == 0
    assert scalar["clip"]["a_max"]["value"] == 1
    assert scalar["_wrapfunc"]["obj"]["value"] == 0.5
    assert len(context_path.read_bytes()) < 24_000
    assert torch.equal(torch.get_rng_state(), at_failure["torch"])
    assert np.array_equal(np.random.get_state()[1], at_failure["numpy"][1])
    assert random.getstate() == at_failure["python"]


def test_diagnostic_write_failure_cannot_replace_training_exception(tmp_path, monkeypatch):
    spec = _short_spec()
    output = tmp_path / f"seed-{spec.seed}"
    original = SystemError("original training error")
    def fail_agent(*args, **kwargs):
        raise original
    monkeypatch.setattr(training, "new_agent", fail_agent)
    write_summary = training.write_summary
    def fail_diagnostic(path, value):
        if path.name == "failure-context.json":
            raise OSError("diagnostic disk write failed")
        return write_summary(path, value)
    monkeypatch.setattr(training, "write_summary", fail_diagnostic)
    with pytest.raises(SystemError) as raised:
        training.run_training(out=output, launch_sha="test-source-sha", spec=spec,
                              device_name="cpu", threads=1, argv=["test"])
    assert raised.value is original
    assert not (output / "failure-context.json").exists()
    summary = json.loads((output / "summary.json").read_text())
    assert summary["failure"] == {"type": "SystemError", "message": "original training error"}
    assert "failure-context.json" not in summary["artifacts"]
    assert summary["counts"]["transitions"] == 0


def test_loaded_native_module_is_captured_from_cache_without_loading(monkeypatch):
    name = "hmasd_uav_geometry_fake_identity_sourcekey"
    native = ModuleType(name)
    native.__file__ = "/tmp/fake-native/hmasd_uav_geometry_fake_identity_sourcekey.so"
    assert name not in sys.modules
    shared_cache = ModuleType("envs.native.cpp_extension_cache")
    shared_cache._LOADED_MODULES = {("uav_geometry", "identity", "/tmp", "digest"): native}
    shared_cache.load_source_keyed_extension = lambda **kwargs: pytest.fail("native loader called")
    backend_cache = ModuleType("envs.pettingzoo.uav_cpp_backend")
    backend_cache._LOADED_BACKENDS = {"identity": native}
    backend_cache.load_uav_cpp_backend = lambda **kwargs: pytest.fail("backend loader called")
    monkeypatch.setitem(sys.modules, shared_cache.__name__, shared_cache)
    monkeypatch.setitem(sys.modules, backend_cache.__name__, backend_cache)
    try:
        raise RuntimeError("capture cache only")
    except RuntimeError as error:
        captured = diagnostics.failure_context(error, {})["runtime"]["loaded_native_modules"]
    assert captured[name] == native.__file__
    assert name not in sys.modules


@pytest.mark.parametrize("writer", ["summary", "progress"])
def test_broad_enospc_during_failure_finalization_preserves_original(tmp_path, monkeypatch, writer):
    spec = _short_spec()
    output = tmp_path / f"seed-{spec.seed}"
    original = SystemError("original training error")
    failed = False
    def fail_agent(*args, **kwargs):
        nonlocal failed
        failed = True
        raise original
    monkeypatch.setattr(training, "new_agent", fail_agent)
    real_summary, real_progress = training.write_summary, training.append_progress
    def write_summary(path, value):
        if failed and writer == "summary":
            raise OSError(errno.ENOSPC, "disk full")
        return real_summary(path, value)
    def append_progress(out, event, counts):
        if failed and writer == "progress":
            raise OSError(errno.ENOSPC, "disk full")
        return real_progress(out, event, counts)
    monkeypatch.setattr(training, "write_summary", write_summary)
    monkeypatch.setattr(training, "append_progress", append_progress)
    with pytest.raises(SystemError) as raised:
        training.run_training(out=output, launch_sha="test-source-sha", spec=spec,
                              device_name="cpu", threads=1, argv=["test"])
    assert raised.value is original
    if writer == "summary":
        assert not (output / "failure-context.json").exists()
    else:
        assert (output / "failure-context.json").is_file()
        assert json.loads((output / "summary.json").read_text())["failure"]["type"] == "SystemError"


@pytest.mark.parametrize("writer", ["summary", "progress"])
def test_successful_training_still_raises_final_artifact_write_failure(tmp_path, monkeypatch, writer):
    spec = _short_spec()
    output = tmp_path / f"seed-{spec.seed}"
    def fake_agent(config, **kwargs):
        width = training.actor_input_width(config) - config.obs_dim
        agent = SimpleNamespace(skill_discoverer=SimpleNamespace(central_input_dim=width))
        return agent, {"policy_fingerprint": "initial"}
    def fake_checkpoint(agent, config, spec, out, index, **kwargs):
        return {"checkpoint": f"c{index:02d}", "rollout": kwargs["rollout"],
                "transitions": kwargs["transitions"], "optimizer_steps": {"low_actor": 1},
                "wall_seconds": 0.0, "agent_pt_sha256": "test", "policy_fingerprint": "initial"}
    def fake_collect(agent, config, spec, *, feedback, after_rollout):
        after_rollout(1, {"transitions": spec.transitions, "episodes_completed": []})
        return {"wall": {"collection": 0.0, "update": 0.0}}
    monkeypatch.setattr(training, "new_agent", fake_agent)
    monkeypatch.setattr(training, "save_checkpoint", fake_checkpoint)
    monkeypatch.setattr(training, "collect_and_train", fake_collect)
    monkeypatch.setattr(training, "optimizer_steps", lambda agent: {"low_actor": 1, "low_critic": 1})
    monkeypatch.setattr(training, "initialization_fingerprint", lambda agent: "changed")
    real_summary, real_progress = training.write_summary, training.append_progress
    def write_summary(path, value):
        if writer == "summary" and path.name == "summary.json" and value["status"] == "COMPLETE":
            raise OSError(errno.ENOSPC, "disk full")
        return real_summary(path, value)
    def append_progress(out, event, counts):
        if writer == "progress" and event["event"] == "training_exit":
            raise OSError(errno.ENOSPC, "disk full")
        return real_progress(out, event, counts)
    monkeypatch.setattr(training, "write_summary", write_summary)
    monkeypatch.setattr(training, "append_progress", append_progress)
    with pytest.raises(OSError) as raised:
        training.run_training(out=output, launch_sha="test-source-sha", spec=spec,
                              device_name="cpu", threads=1, argv=["test"])
    assert raised.value.errno == errno.ENOSPC


def test_failure_capture_uses_only_allowlisted_scalars(tmp_path):
    class Trap:
        def __repr__(self):
            raise AssertionError("custom repr called")
        def __str__(self):
            raise AssertionError("custom str called")

    def _wrapit():
        obj = torch.ones(100_000)
        raise RuntimeError("fixture failure")

    def clip():
        a = np.ones(100_000)
        a_min, a_max = Trap(), float("inf")
        return _wrapit()

    def _get_observation_cached_body():
        sinr_db = Trap()
        secret = "DO_NOT_SERIALIZE_SECRET"
        return clip()

    try:
        _get_observation_cached_body()
    except RuntimeError as error:
        context = diagnostics.failure_context(error, {"transitions": 8, "rollouts": 2})
    payload = json.dumps(context, allow_nan=False)
    assert len(payload) < 24_000
    assert "DO_NOT_SERIALIZE_SECRET" not in payload
    scalar = {row["function"]: row["values"] for row in context["scalar_frames"]}
    assert "value" not in scalar["_get_observation_cached_body"]["sinr_db"]
    assert "value" not in scalar["clip"]["a"]
    assert "value" not in scalar["clip"]["a_min"]
    assert scalar["clip"]["a_max"]["value"] == "+inf"
    assert "value" not in scalar["_wrapit"]["obj"]


@pytest.mark.parametrize("unsupported", [False, True])
def test_cli_enables_faulthandler_after_admission_before_candidate_spec(tmp_path, monkeypatch, unsupported):
    from scripts import hmasd_admission

    seed = cfg.TRAINING_SEEDS[0]
    output = tmp_path / "runs" / cfg.DIRECTION / "test" / f"seed-{seed}"
    events = []
    def admit(*args, **kwargs):
        events.append("admission")
        return {"sha": "a" * 40}
    def enable(**kwargs):
        events.append("faulthandler")
        assert kwargs["all_threads"] is True
        if unsupported:
            raise RuntimeError("stderr has no file descriptor")
    def spec(value):
        events.append("spec")
        return replace(cfg.B02Spec(seed=value), rollouts=1, rollout_length=2,
                       episode_length=20, checkpoint_every_transitions=4)
    def train(**kwargs):
        events.append("training")
    monkeypatch.setattr(hmasd_admission, "require_admission", admit)
    monkeypatch.setattr(run.faulthandler, "enable", enable)
    monkeypatch.setattr(cfg, "production_spec", spec)
    monkeypatch.setattr(training, "run_training", train)
    assert run.main(["train", "--seed", str(seed), "--out", str(output),
                     "--launch-sha", "a" * 40, "--device", "cpu"]) == 0
    assert events == ["admission", "faulthandler", "spec", "training"]
