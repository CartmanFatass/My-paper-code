from __future__ import annotations

import copy
import importlib
import sys
import types
import subprocess
from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import (
    _module_parameters, _rng_state, make_config, make_env, seed_everything, sha256_file,
)
from experiments.candidates.uav_service_auxiliary.b04 import native
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS, evaluate, metric_row
from hmasd.agent import HMASDAgent


def small_spec(cuda=False):
    return native.B04Spec(lanes=4 if cuda else 1, rollouts=1, rollout_length=20,
                         episode_length=20, eval_seeds=(937001,), final_seeds=(938001,),
                         eval_rollouts=(0, 1), ppo_epochs=1, threads=1,
                         hidden_size=None if cuda else 32, gru_hidden_size=None if cuda else 32)


def controlled_reward_info(cost):
    result = {name: 0.0 for name in TRACE_FIELDS}
    result.update(qos_satisfaction_ratio=.6, return_penalty_coefficient=2.0,
                  return_constraint_cost=cost, scenario7_reward=.6 - 2 * cost)
    return result


def test_native_units_and_fixed_cost_weight_refuse_bad_metrics():
    info = controlled_reward_info(.3)
    assert native.training_reward("N", 0.0, info) == 0.0
    assert native.training_reward("R", 0.0, info) == -.6
    for value in (-.1, 1.1, float("nan")):
        with pytest.raises((ValueError, FloatingPointError)):
            native.training_reward("R", 0.0, {**info, "return_constraint_cost": value})
    with pytest.raises(ValueError, match="coefficient"):
        native.training_reward("R", 0.0, {**info, "return_penalty_coefficient": 4.0})
    info = controlled_reward_info(.2)
    with pytest.raises(ValueError, match="native scalar"):
        metric_row(info["scenario7_reward"] / 8, info)


@pytest.mark.parametrize("device_name", ("cpu", "cuda"))
def test_real_native_collection_update_evaluation_checkpoint(tmp_path, device_name, monkeypatch):
    if device_name == "cuda" and not torch.cuda.is_available():
        pytest.skip("requires actual CUDA")
    spec = small_spec(device_name == "cuda")
    class TerminalCheckingAgent(HMASDAgent):
        def store_transition_batch(self, states, next_states, observations, next_observations,
                                   actions, rewards, dones, **kwargs):
            result = super().store_transition_batch(states, next_states, observations,
                next_observations, actions, rewards, dones, **kwargs)
            if np.any(dones):
                assert not self.config.use_obsnorm and not self.config.use_statenorm
                # Retain the real stored views and separate terminal copies. The
                # collector performs reset after this call and before update.
                recent = list(self.discriminator_buffer.buffer)[-len(dones) * (self.config.n_agents + 1):]
                self.terminal_records = (recent, next_states.copy(), next_observations.copy())
            return result

        def update(self, *args, **kwargs):
            recent, terminal_states, terminal_obs = self.terminal_records
            width = self.config.n_agents + 1
            for lane in range(spec.lanes):
                np.testing.assert_array_equal(recent[lane * width]["state"], terminal_states[lane])
                for index in range(self.config.n_agents):
                    np.testing.assert_array_equal(recent[lane * width + index + 1]["obs"], terminal_obs[lane, index])
                assert not np.array_equal(terminal_states[lane], kwargs["last_state"][lane])
            return super().update(*args, **kwargs)
    monkeypatch.setattr(native, "HMASDAgent", TerminalCheckingAgent)
    results = {}
    for arm in ("N", "R"):
        out = tmp_path / arm
        result = native.run_native(arm=arm, out=out, launch_sha="ENGINEERING-CORRECTNESS",
                                   device_name=device_name, threads=1, spec=spec)
        results[arm] = result
        assert result["status"] == "COMPLETE"
        assert result["counts"]["transitions"] == 20 * spec.lanes
        assert result["counts"]["agent_rows"] == 20 * spec.lanes * 8
        assert result["counts"]["evaluation_transitions"] == 60
        assert result["counts"]["episodes"] == spec.lanes
        assert all(value > 0 for value in result["optimizer_steps"].values())
        assert all(value > 0 for value in result["initialization_displacement_l2"].values())
        assert all(value["min"] > 0 for value in result["optimizer_state_steps"].values())
        for path, digest in result["artifacts"].items():
            assert sha256_file(out / path) == digest
        with np.load(out / "first_rollout_audit.npz", allow_pickle=False) as audit:
            np.testing.assert_allclose(audit["training_reward"],
                                       audit["native_reward"] - native.EXTRA_COST[arm] * audit["return_cost"])
            # This short native check begins safely. Nonzero-cost gradient tested separately below.
            assert not audit["return_cost"].any()
        with np.load(out / "trajectories/evaluation_final.npz", allow_pickle=False) as trace:
            values = trace["episode_0_metrics"]
            columns = {name: i for i, name in enumerate(trace["metric_fields"])}
            rescored = (values[:, columns["qos_satisfaction_ratio"]]
                        - 2 * values[:, columns["return_constraint_cost"]]
                        - values[:, columns["cutoff_event_penalty"]] - values[:, columns["depletion_event_penalty"]]
                        + values[:, columns["graph_potential_delta"]])
            np.testing.assert_allclose(rescored, trace["episode_0_native_reward"], rtol=0, atol=1e-7)
            world = result["final_evaluation"]["worlds"][0]
            assert world["raw_native_J"] == pytest.approx(rescored.sum(), abs=1e-6)
            assert world["episode_minimum_battery_ratio"] == values[:, columns["battery_min_ratio"]].min()
            assert result["final_evaluation"]["new_optimizer_updates"] == 0
        with pytest.raises(FileExistsError):
            native.run_native(arm=arm, out=out, launch_sha="ENGINEERING-CORRECTNESS",
                              device_name=device_name, threads=1, spec=spec)
    for key in ("initialization_sha256", "first_collection_sha256", "first_update_policy_sha256"):
        assert results["N"][key] == results["R"][key]


def test_controlled_cost_flows_through_real_storage_gae_and_actors(tmp_path):
    """Synthetic costs are a correctness fixture, never a scientific result."""
    torch.set_num_threads(1)
    device, spec = torch.device("cpu"), replace(small_spec(), rollout_length=40, episode_length=40)
    runs = {}
    costs = np.asarray([.1, .4, .2, .8, .1, .2, .3, .7, .1, .2, .6, .9, .1, .1, .7, .3, .2, .8, .6, .1])
    costs = np.concatenate((costs, costs[::-1] * .5))
    for arm in ("N", "R"):
        seed_everything(spec.seed, device)
        config = make_config(spec)
        agent = HMASDAgent(config, log_dir=str(tmp_path / arm), device=device)
        env = make_env(config, spec.seed)
        try:
            obs, info = env.reset(seed=spec.seed)
            states, observations = np.asarray([info["state"]], dtype=np.float32), np.asarray([obs])
            dones = np.ones(1, dtype=bool)
            for step, cost in enumerate(costs):
                actions, _, data = agent.step(states, observations, np.asarray([step]), dones,
                                             return_step_data=True, build_infos=False)
                obs, _, terminated, truncated, info = env.step(actions[0])
                next_obs, next_states = np.asarray([obs]), np.asarray([info["next_state"]], dtype=np.float32)
                dones[:] = terminated or truncated
                fixture = controlled_reward_info(cost)
                train = native.training_reward(arm, fixture["scenario7_reward"], fixture)
                agent.store_transition_batch(states, next_states, observations, next_obs, actions,
                    np.asarray([train], dtype=np.float32), dones, infos_batch=[info],
                    rollout_step_idx=step, step_data=data)
                states, observations = next_states, next_obs
            buf = agent.rollout_buffer
            high_rewards, high_mask = buf.high_level_rewards.copy(), buf.high_level_valid_mask.copy()
            initial = _module_parameters(agent)
            agent.update(last_values=np.zeros((1, 8), dtype=np.float32), dones=dones,
                         steps_in_buffer=40, last_state=states, last_observations=observations)
            runs[arm] = {"high_rewards": high_rewards, "high_mask": high_mask,
                         "advantages": buf.advantages.copy(), "weights": _module_parameters(agent),
                         "initial": initial, "reward": buf.reward_env.copy(),
                         "high_actor_grads": {name: p.grad.detach().clone() for name, p in
                             agent.skill_coordinator.named_parameters()
                             if "_skill_head." in name and p.grad is not None}}
        finally:
            env.close()
    expected = np.zeros(40)
    future = 0.0
    for step in reversed(range(40)):
        future = -2 * costs[step] + config.gamma * config.gae_lambda * future
        expected[step] = future
    np.testing.assert_allclose(runs["R"]["advantages"] - runs["N"]["advantages"],
                               np.broadcast_to(expected[:, None, None], (40, 1, 8)), atol=4e-6, rtol=2e-6)
    high_delta = (runs["R"]["high_rewards"] - runs["N"]["high_rewards"])[runs["N"]["high_mask"]]
    np.testing.assert_allclose(high_delta, [-2 * part.sum() for part in costs.reshape(4, 10)], atol=2e-6)
    assert runs["N"]["high_actor_grads"]
    assert any(not torch.allclose(grad, runs["R"]["high_actor_grads"][name], rtol=1e-5, atol=1e-8)
               for name, grad in runs["N"]["high_actor_grads"].items())
    for group in ("high", "low_actor"):
        assert all(torch.equal(a, b) for a, b in zip(runs["N"]["initial"][group], runs["R"]["initial"][group]))
        difference = sum(float((a - b).square().sum()) for a, b in
                         zip(runs["N"]["weights"][group], runs["R"]["weights"][group]))
        assert difference > 1e-12


def test_evaluation_preserves_training_rng_normalizers_optimizers(tmp_path):
    torch.set_num_threads(1)
    device = torch.device("cpu")
    config = make_config(small_spec())
    agent = HMASDAgent(config, log_dir=str(tmp_path / "agent"), device=device)
    before = _rng_state()
    normalizers = copy.deepcopy((agent.obs_norm, agent.state_norm))
    steps = native.optimizer_state_steps(agent)
    panel = evaluate(agent, config, (937001,), device, policy_seed=914021,
                     log_dir=tmp_path / "eval", trace_path=tmp_path / "trace.npz")
    after = _rng_state()
    assert before["python"] == after["python"] and torch.equal(before["torch"], after["torch"])
    np.testing.assert_array_equal(before["numpy"][1], after["numpy"][1])
    assert before["numpy"][2:] == after["numpy"][2:]
    assert (agent.obs_norm, agent.state_norm) == normalizers
    assert native.optimizer_state_steps(agent) == steps
    assert panel["new_optimizer_updates"] == 0


@pytest.mark.parametrize("arm", ("N", "R"))
def test_entry_admission_before_science_and_fixed_prospective(monkeypatch, tmp_path, arm):
    entry = importlib.import_module("scripts.run_uav_service_auxiliary_b04")
    events = []
    admission = types.ModuleType("scripts.hmasd_admission")
    def admit(*args, **kwargs):
        events.append("admission")
        return {"sha": "source"}
    admission.require_admission = admit
    monkeypatch.setitem(sys.modules, "scripts.hmasd_admission", admission)
    candidate = types.ModuleType("experiments.candidates.uav_service_auxiliary.b04.native")
    candidate.production_spec = native.production_spec
    def run(**kwargs):
        assert events == ["admission"]
        return kwargs
    candidate.run_native = run
    monkeypatch.setitem(sys.modules, candidate.__name__, candidate)
    argv = ["--arm", arm, "--seed", "914021", "--out", str(tmp_path / "run"), "--launch-sha", "source"]
    result = entry.main(argv)
    assert result["spec"].transitions == 180000
    assert result["spec"].final_seeds == tuple(range(938001, 938033))
    assert result["device_name"] == "cuda"
    with pytest.raises(SystemExit):
        entry.parse_args([*argv, "--extra-cost", "3"])
    with pytest.raises(SystemExit):
        entry.parse_args([*argv, "--seed", "912211"])
    with pytest.raises(RuntimeError, match="SHA"):
        entry.main([*argv, "--launch-sha", "other"])


def test_direct_cli_without_admission_refuses_before_output(tmp_path):
    entry = importlib.import_module("scripts.run_uav_service_auxiliary_b04")
    out = tmp_path / "never-created"
    result = subprocess.run([sys.executable, entry.__file__, "--arm", "N", "--seed", "914021",
                             "--out", str(out), "--launch-sha", "0" * 40],
                            cwd=entry.ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0 and "missing HMASD admission" in result.stderr
    assert not out.exists()
