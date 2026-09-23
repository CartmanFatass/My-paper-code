from __future__ import annotations

from dataclasses import replace
import pickle
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.complementary_skill_learning.b02 import runner as r
from experiments.candidates.complementary_skill_learning.b02.learning import ObjectiveComparisonAgent


@pytest.fixture
def spec():
    return replace(r.DEFAULT_SPEC, n_users=8, horizon=20, lanes=2, rollouts=1,
                   eval_lanes=2, threads=1, small_model=True)


def build(tmp_path, spec, arm):
    envs = r.make_envs(spec, spec.lanes, spec.train_world_base)
    config = r.make_config(spec, envs, arm)
    r.seed_rng(spec.init_seed)
    agent = ObjectiveComparisonAgent(config, arm, spec.head_seed, spec.aux_seed,
                                     str(tmp_path / f"logs-{arm}"), torch.device("cpu"))
    return agent, envs


def test_effective_config_includes_inherited_treatment_and_fixed_native_fields(spec):
    envs = r.make_envs(spec, spec.lanes, spec.train_world_base)
    try:
        m = r.effective_config(r.make_config(spec, envs, "M"))
        t = r.effective_config(r.make_config(spec, envs, "T"))
    finally:
        for env in envs:
            env.close()
    assert m["legacy_mi_reward_coef"] == .5 and t["legacy_mi_reward_coef"] == 0
    assert m["effective_team_discriminator_reward_coef"] == .025
    assert m["effective_individual_discriminator_reward_coef"] == .01
    assert t["effective_team_discriminator_reward_coef"] == 0
    assert m["intrinsic_mi_clip"] == t["intrinsic_mi_clip"] == 2.0
    assert not any(m["resolved_switches"].values())
    assert not any(t["resolved_switches"].values())
    for key, value in {"lambda_e": 1., "lambda_D": .05, "lambda_d": .02,
                       "gamma": .99, "gae_lambda": .95,
                       "normalize_intrinsic_mi": False,
                       "use_prior_corrected_intrinsic": False}.items():
        assert m[key] == t[key] == value


def test_caught_native_reward_failure_is_fatal(tmp_path, spec, monkeypatch):
    agent, envs = build(tmp_path, spec, "T")
    try:
        states, observations = r.b01.native._reset_all(envs)
        actions, _, data = agent.step(states, observations, np.zeros(spec.lanes, np.int64),
                                      np.zeros(spec.lanes, bool), deterministic=False,
                                      return_step_data=True, build_infos=False)
        next_states, next_obs, rewards, dones = [], [], [], []
        for lane, env in enumerate(envs):
            ns, no, reward, done, _, _ = r.physical_step(env, actions[lane])
            next_states.append(ns); next_obs.append(no); rewards.append(reward); dones.append(done)
        monkeypatch.setattr(agent, "_team_discriminator_logits",
                            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("fault")))
        with pytest.raises(RuntimeError, match="fell back"):
            agent.store_transition_batch(
                states=states, next_states=np.stack(next_states), observations=observations,
                next_observations=np.stack(next_obs), actions=actions, rewards=np.asarray(rewards),
                dones=np.asarray(dones), infos_batch=None, rollout_step_idx=0, step_data=data,
            )
        assert agent.reward_telemetry()["fallbacks"] == 1
    finally:
        for env in envs:
            env.close()


def test_scalar_and_batch_reward_coefficients_match(tmp_path, spec):
    for arm in ("M", "T"):
        batch_agent, envs = build(tmp_path, spec, arm)
        scalar_agent, scalar_envs = build(tmp_path, spec, arm)
        try:
            states, observations = r.b01.native._reset_all(envs)
            next_state = states[:1]
            next_obs = observations[:1]
            team = np.asarray([2])
            skills = np.asarray([[1, 2, 3, 4, 5, 0]])
            batch = batch_agent._compute_intrinsic_rewards_batch(
                next_state, np.asarray([.125]), next_obs, team, skills
            )
            scalar = scalar_agent._compute_intrinsic_reward(
                next_state[0], .125, next_obs[0, 0], 2, 1
            )
            np.testing.assert_allclose(
                [batch[key][0, 0] for key in
                 ("intrinsic", "env", "team_disc", "ind_disc", "uncertainty")],
                scalar, rtol=2e-5, atol=2e-6,
            )
            if arm == "T":
                assert batch_agent.reward_score_arrays()[0].size
                assert batch["team_disc"][0, 0] == batch["ind_disc"][0, 0] == 0
        finally:
            for env in (*envs, *scalar_envs):
                env.close()


def test_evaluation_resets_world_stream_and_preserves_all_state(tmp_path, spec):
    agent, envs = build(tmp_path, spec, "M")
    try:
        before = r.frozen_digest(agent)
        torch_rng = torch.get_rng_state().clone()
        numpy_rng = pickle.dumps(np.random.get_state())
        own_first = r.evaluate_panel(agent, spec, spec.eval_world_base, "own")
        uniform_second = r.evaluate_panel(agent, spec, spec.eval_world_base, "uniform")
        uniform_first = r.evaluate_panel(agent, spec, spec.eval_world_base, "uniform")
        own_second = r.evaluate_panel(agent, spec, spec.eval_world_base, "own")
        assert r.jsonable(own_first) == r.jsonable(own_second)
        assert r.jsonable(uniform_first) == r.jsonable(uniform_second)
        assert own_first["world_seeds"] == uniform_first["world_seeds"]
        assert own_first["transitions"] == uniform_first["transitions"] == 40
        assert own_first["optimizer_calls"] == uniform_first["optimizer_calls"] == 0
        assert r.frozen_digest(agent) == before
        assert torch.equal(torch_rng, torch.get_rng_state())
        assert numpy_rng == pickle.dumps(np.random.get_state())
    finally:
        for env in envs:
            env.close()


@pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(
    not torch.cuda.is_available(), reason="requires actual CUDA runtime"))])
def test_real_matched_fits_diverge_only_after_native_reward_objective(tmp_path, spec, device):
    summaries = {
        arm: r.run_fit(arm, tmp_path / arm, "technical-check", spec=spec, device=device)
        for arm in ("M", "T")
    }
    m, t = summaries["M"], summaries["T"]
    for arm, summary in summaries.items():
        assert summary["status"] == "complete"
        assert summary["counts"]["training_transitions"] == 40
        assert summary["counts"]["evaluation_transitions"] == 160
        assert summary["counts"]["native_updates"] == 1
        assert summary["native_optimizer_calls"] == {
            "coordinator": 1, "discoverer_actor": 1, "discoverer_critic": 1,
            "team_discriminator": 1, "individual_discriminator": 4,
        }
        assert all(value > 0 for value in
                   summary["training_rows"][0]["relative_initialization_displacement"].values())
        assert summary["training_rows"][0]["reward_path"]["fallbacks"] == 0
        assert summary["training_rows"][0]["auxiliary"]["trunk_optimizer_steps"] == 0
        assert set(summary["panels"]) == {
            "initial_own", "initial_uniform", "final_own", "final_uniform"
        }
        checkpoint = torch.load(tmp_path / arm / "final.pt", map_location="cpu", weights_only=False)
        assert checkpoint["object_id"] == r.OBJECT and checkpoint["arm"] == arm
        assert "diagnostic" not in summary
    assert m["initial_native_digest"] == t["initial_native_digest"]
    m_initial = torch.load(tmp_path / "M" / "initial.pt", map_location="cpu", weights_only=False)
    t_initial = torch.load(tmp_path / "T" / "initial.pt", map_location="cpu", weights_only=False)
    for head in ("g_head", "p_head"):
        for name, value in m_initial["auxiliary"][head].items():
            assert torch.equal(value, t_initial["auxiliary"][head][name])
    assert m["first_rollout_facts_sha256"] == t["first_rollout_facts_sha256"]
    assert (m["auxiliary_history"][0]["raw_target_sha256"]
            == t["auxiliary_history"][0]["raw_target_sha256"])
    m_audit = np.load(tmp_path / "M" / "first_rollout_reward_gae_audit.npz")
    t_audit = np.load(tmp_path / "T" / "first_rollout_reward_gae_audit.npz")
    for key in ("raw_environment_rewards", "unweighted_team_discriminator_scores",
                "unweighted_individual_discriminator_scores", "d2_team_reward",
                "d2_agent_reward"):
        np.testing.assert_array_equal(m_audit[key], t_audit[key])
    assert not np.array_equal(m_audit["stored_low_rewards"], t_audit["stored_low_rewards"])
    assert not np.array_equal(m_audit["low_advantages"], t_audit["low_advantages"])
    assert not np.array_equal(m_audit["low_returns"], t_audit["low_returns"])
    np.testing.assert_array_equal(t_audit["stored_low_rewards"], t_audit["reward_env"])
    assert m["final_native_digest"] != t["final_native_digest"]


def test_entry_refuses_unadmitted_call_before_outputs(tmp_path):
    out = tmp_path / "must-not-exist"
    result = subprocess.run(
        [sys.executable, str(r.b01.ROOT / "scripts/run_complementary_skill_learning_b02.py"),
         "--arm", "M", "--seed", "260923911", "--launch-sha", "unadmitted",
         "--out", str(out)], cwd=r.b01.ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0
    assert not out.exists()
