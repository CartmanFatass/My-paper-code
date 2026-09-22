from __future__ import annotations

import importlib
import json
import random
import sys
import types
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import (
    NativeSpec,
    _bootstrap_values,
    _rng_state,
    evaluate,
    make_config,
    make_env,
    run_native,
    seed_everything,
    sha256_file,
)
from hmasd.agent import HMASDAgent


def _small_spec(*, native_width: bool = False) -> NativeSpec:
    return NativeSpec(
        lanes=1,
        rollouts=1,
        rollout_length=10,
        episode_length=10,
        window=3,
        threads=1,
        eval_seeds=(920001,),
        fact_seeds=(930001,),
        ppo_epochs=1,
        hidden_size=None if native_width else 32,
        gru_hidden_size=None if native_width else 32,
    )


def _assert_rng_equal(left, right):
    assert left["python"] == right["python"]
    assert left["numpy"][0] == right["numpy"][0]
    np.testing.assert_array_equal(left["numpy"][1], right["numpy"][1])
    assert left["numpy"][2:] == right["numpy"][2:]
    assert torch.equal(left["torch"], right["torch"])
    if left["cuda"] is not None:
        assert all(torch.equal(a, b) for a, b in zip(left["cuda"], right["cuda"], strict=True))


@pytest.mark.parametrize("device_name", ("cpu", "cuda"))
def test_real_s7_short_native_update_then_auxiliary(tmp_path, device_name):
    if device_name == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA correctness path requires an actual CUDA runtime")
    spec = _small_spec(native_width=device_name == "cuda")
    out = tmp_path / f"detach-{device_name}"
    result = run_native(
        arm="detach",
        out=out,
        launch_sha="ENGINEERING-CORRECTNESS",
        device_name=device_name,
        threads=1,
        spec=spec,
    )

    assert result["status"] == "COMPLETE"
    assert result["counts"]["transitions"] == 10
    assert result["counts"]["rollouts"] == 1
    assert all(step > 0 for step in result["optimizer_steps"].values())
    assert all(distance > 0 for distance in result["initialization_displacement_l2"].values())
    assert result["updates"][0]["auxiliary"]["optimizer_steps"] > 0
    assert result["updates"][0]["auxiliary"]["representation_gradient_norm"] == 0.0
    assert result["training_rollouts"][0]["raw_native_J_by_lane"]
    endpoint_panel = result["evaluations"]["1"]["native"]
    endpoint = endpoint_panel["worlds"][0]
    assert endpoint["actual_length"] == 10
    assert endpoint["terminal_type"] in {"terminated", "truncated"}
    assert np.isfinite(endpoint["raw_native_J"])
    assert endpoint_panel["aggregate"]["primary_native_J_mean"] == pytest.approx(
        endpoint["raw_native_J"]
    )
    assert (out / "checkpoint_final" / "agent.pt").is_file()
    assert (out / "checkpoint_final" / "auxiliary.pt").is_file()
    assert (out / "final_prediction_replay.npz").is_file()
    assert sha256_file(out / "facts.npz") == result["facts_sha256"]
    persisted = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert persisted["status"] == "COMPLETE"

    joint_out = tmp_path / f"joint-{device_name}"
    joint = run_native(
        arm="joint",
        out=joint_out,
        launch_sha="ENGINEERING-CORRECTNESS",
        device_name=device_name,
        threads=1,
        facts=out / "facts.npz",
        facts_sha256=result["facts_sha256"],
        spec=spec,
    )
    assert joint["status"] == "COMPLETE"
    assert joint["facts_sha256"] == result["facts_sha256"]
    assert sha256_file(joint_out / "facts.npz") == result["facts_sha256"]
    assert joint["updates"][0]["auxiliary"]["representation_gradient_norm"] > 0.0


def test_real_s7_reward_and_required_service_metrics_are_native():
    spec = _small_spec()
    config = make_config(spec, lanes=1)
    env = make_env(config, 123)
    try:
        env.reset(seed=123)
        action = np.zeros((config.n_agents, config.action_dim), dtype=np.float32)
        _, reward, _, _, info = env.step(action)
    finally:
        env.close()
    reward_info = info["reward_info"]
    assert reward == pytest.approx(reward_info["scenario7_reward"])
    for field in (
        "qos_satisfaction_ratio",
        "delivered_end_to_end_throughput_mbps",
        "return_constraint_cost",
        "cutoff_event_count",
        "depletion_event_count",
        "charging_uav_count",
        "step_charger_input_wh",
        "battery_min_ratio",
    ):
        assert field in reward_info
        assert np.isfinite(float(reward_info[field]))


def test_unfinished_rollout_boundary_uses_current_native_critic_state(tmp_path):
    spec = _small_spec()
    config = make_config(spec)
    agent = HMASDAgent(config, log_dir=str(tmp_path / "bootstrap-agent"), device=torch.device("cpu"))
    env = make_env(config, spec.seed)
    try:
        observations, info = env.reset(seed=spec.seed)
        actions, _, _ = agent.step(
            np.asarray(info["state"], dtype=np.float32)[None],
            np.asarray(observations, dtype=np.float32)[None],
            np.zeros(1, dtype=np.int64), np.ones(1, dtype=bool),
            deterministic=False, return_step_data=True, build_infos=False,
        )
        _, _, terminated, truncated, next_info = env.step(actions[0])
        assert not (terminated or truncated)
        values = _bootstrap_values(
            agent, np.asarray(next_info["next_state"], dtype=np.float32)[None],
            np.zeros(1, dtype=bool),
        )
    finally:
        env.close()
    assert values.shape == (1, config.n_agents)
    assert np.isfinite(values).all()


def test_evaluation_preserves_global_rng_and_training_normalizers(tmp_path):
    spec = _small_spec()
    device = torch.device("cpu")
    seed_everything(spec.seed, device)
    config = make_config(spec)
    agent = HMASDAgent(config, log_dir=str(tmp_path / "train-agent"), device=device)
    before_rng = _rng_state()
    obs_count = None if agent.obs_norm is None else float(agent.obs_norm.count)
    state_count = None if agent.state_norm is None else float(agent.state_norm.count)

    rows = evaluate(
        agent, config, spec.eval_seeds, device,
        policy_seed=spec.seed, log_dir=tmp_path / "eval-agent",
    )

    assert len(rows) == 1
    _assert_rng_equal(before_rng, _rng_state())
    assert (None if agent.obs_norm is None else float(agent.obs_norm.count)) == obs_count
    assert (None if agent.state_norm is None else float(agent.state_norm.count)) == state_count


def test_launcher_admits_before_importing_scientific_runner(monkeypatch, tmp_path):
    module = importlib.import_module("scripts.run_uav_service_auxiliary_b01")
    candidate_name = "experiments.candidates.uav_service_auxiliary.b01.native"
    monkeypatch.delitem(sys.modules, candidate_name, raising=False)
    events = []

    admission_module = types.ModuleType("scripts.hmasd_admission")
    def admit(*args, **kwargs):
        assert events == []
        events.append("admission")
        return {"sha": "abc"}
    admission_module.require_admission = admit
    monkeypatch.setitem(sys.modules, "scripts.hmasd_admission", admission_module)

    candidate_module = types.ModuleType(candidate_name)
    def fake_run(**kwargs):
        events.append("run")
        return kwargs
    candidate_module.run_native = fake_run
    monkeypatch.setitem(sys.modules, candidate_name, candidate_module)

    result = module.main([
        "--arm", "detach", "--seed", "910021", "--device", "cpu",
        "--threads", "4", "--launch-sha", "abc", "--out", str(tmp_path / "out"),
    ])
    assert events == ["admission", "run"]
    assert result["launch_sha"] == "abc"
