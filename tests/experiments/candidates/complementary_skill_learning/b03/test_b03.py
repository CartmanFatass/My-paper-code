from __future__ import annotations

from dataclasses import replace
import json
import pickle
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from experiments.candidates.complementary_skill_learning.b03 import runner as r


@pytest.fixture
def spec():
    return replace(
        r.DEFAULT_SPEC,
        n_users=8,
        horizon=20,
        lanes=2,
        rollouts=1,
        eval_lanes=2,
        threads=1,
        small_model=True,
    )


def build(tmp_path, spec, arm="D", agent_class=r.AuditedComplementaryAgent, suffix=""):
    envs = r.make_envs(spec, spec.lanes, spec.train_world_base)
    config = r.make_config(spec, envs)
    r.seed_rng(spec.init_seed)
    agent = agent_class(
        config=config,
        arm=arm,
        head_seed=spec.head_seed,
        aux_seed=spec.aux_seed,
        log_dir=str(tmp_path / f"logs-{arm}{suffix}"),
        device=torch.device("cpu"),
    )
    return agent, envs


def one_storage_batch(agent, envs, spec, telemetry):
    states, observations = b01.native._reset_all(envs)
    actions, _, data = agent.step(
        states,
        observations,
        np.zeros(spec.lanes, np.int64),
        np.zeros(spec.lanes, bool),
        deterministic=False,
        return_step_data=True,
        build_infos=False,
    )
    next_states, next_obs, rewards, dones = [], [], [], []
    for lane, env in enumerate(envs):
        state, obs, reward, done, _, _ = r.physical_step(env, actions[lane])
        next_states.append(state)
        next_obs.append(obs)
        rewards.append(reward)
        dones.append(done)
    return r.store_verified_batch(
        agent,
        telemetry,
        states=states,
        next_states=np.stack(next_states),
        observations=observations,
        next_observations=np.stack(next_obs),
        actions=actions,
        rewards=np.asarray(rewards),
        dones=np.asarray(dones),
        infos_batch=None,
        rollout_step_idx=0,
        step_data=data,
    )


def storage_telemetry():
    return {
        "batch_calls": 0,
        "expected_rows": 0,
        "verified_rows": 0,
        "failures": 0,
        "last_failure": None,
    }


def test_frozen_spec_cost_seeds_and_effective_native_config(spec):
    fixed = r.DEFAULT_SPEC
    assert (fixed.init_seed, fixed.head_seed, fixed.train_rng_seed, fixed.aux_seed) == (
        260923921, 260923922, 260923923, 260923924
    )
    assert fixed.eval_rng_seed == 260923905
    assert fixed.train_world_base == 2000000
    assert fixed.eval_world_base == 1700200
    assert fixed.lanes * fixed.horizon * fixed.rollouts == 360000
    assert 4 * fixed.eval_lanes * fixed.horizon == 64000
    assert r._uniform_stream_digest(fixed) == r.EXPECTED_UNIFORM_LABEL_STREAM_SHA256
    assert r.EXPECTED_UNIFORM_LABEL_STREAM_SHA256 == (
        "a45d59f80fca20321df3803745068bb841f30e6c25b6b8c01dd7d0d250a67190"
    )
    assert {fixed.init_seed, fixed.head_seed, fixed.train_rng_seed, fixed.aux_seed}.isdisjoint(
        {
            b01.DEFAULT_SPEC.init_seed,
            b01.DEFAULT_SPEC.head_seed,
            b01.DEFAULT_SPEC.train_rng_seed,
            b01.DEFAULT_SPEC.aux_seed,
            260923911,
            260923912,
            260923913,
            260923914,
        }
    )
    envs = r.make_envs(spec, spec.lanes, spec.train_world_base)
    try:
        config = effective_config(r.make_config(spec, envs))
    finally:
        for env in envs:
            env.close()
    assert config["legacy_mi_reward_coef"] == 0.5
    assert config["effective_team_discriminator_reward_coef"] == 0.025
    assert config["effective_individual_discriminator_reward_coef"] == 0.01
    assert config["gamma"] == 0.99 and config["gae_lambda"] == 0.95
    assert not any(config["resolved_switches"].values())


def test_actual_new_initialization_differs_from_old_block(tmp_path, spec):
    old_spec = replace(
        spec,
        init_seed=b01.DEFAULT_SPEC.init_seed,
        head_seed=b01.DEFAULT_SPEC.head_seed,
        aux_seed=b01.DEFAULT_SPEC.aux_seed,
    )
    new, new_envs = build(tmp_path, spec, suffix="-new")
    old, old_envs = build(tmp_path, old_spec, suffix="-old")
    try:
        assert r.native_digest(new) != r.native_digest(old)
        for head in ("g_head", "p_head"):
            new_state = getattr(new, head).state_dict()
            old_state = getattr(old, head).state_dict()
            assert any(
                not torch.equal(new_state[name], old_state[name]) for name in new_state
            )
        assert not np.array_equal(
            new._shuffle_rng.permutation(32), old._shuffle_rng.permutation(32)
        )
    finally:
        for env in (*new_envs, *old_envs):
            env.close()


def test_audited_agent_matches_plain_b01_on_healthy_storage_path(tmp_path, spec):
    plain, plain_envs = build(
        tmp_path, spec, agent_class=r.ComplementaryAgent, suffix="-plain"
    )
    audited, audited_envs = build(tmp_path, spec, suffix="-audited")
    try:
        assert r.frozen_digest(plain) == r.frozen_digest(audited)

        def collect(agent, envs):
            r.seed_rng(spec.train_rng_seed)
            states, observations = b01.native._reset_all(envs)
            actions, _, data = agent.step(
                states,
                observations,
                np.zeros(spec.lanes, np.int64),
                np.zeros(spec.lanes, bool),
                deterministic=False,
                return_step_data=True,
                build_infos=False,
            )
            next_states, next_obs, rewards, dones = [], [], [], []
            for lane, env in enumerate(envs):
                state, obs, reward, done, _, _ = r.physical_step(env, actions[lane])
                next_states.append(state)
                next_obs.append(obs)
                rewards.append(reward)
                dones.append(done)
            kwargs = {
                "states": states,
                "next_states": np.stack(next_states),
                "observations": observations,
                "next_observations": np.stack(next_obs),
                "actions": actions,
                "rewards": np.asarray(rewards),
                "dones": np.asarray(dones),
                "infos_batch": None,
                "rollout_step_idx": 0,
                "step_data": data,
            }
            return actions, data, kwargs

        plain_actions, plain_data, plain_kwargs = collect(plain, plain_envs)
        audited_actions, audited_data, audited_kwargs = collect(audited, audited_envs)
        np.testing.assert_array_equal(plain_actions, audited_actions)
        for name in (
            "team_skills", "agent_skills", "action_logprobs", "values",
            "d2_team_decision", "d2_sampled_mask",
        ):
            np.testing.assert_array_equal(plain_data[name], audited_data[name])
        plain_result = plain.store_transition_batch(**plain_kwargs)
        telemetry = storage_telemetry()
        assert r.store_verified_batch(audited, telemetry, **audited_kwargs) == spec.lanes
        for plain_row, audited_row in zip(plain_result, [
            {
                "env": audited.rollout_buffer.reward_env[0, lane],
                "team_disc": audited.rollout_buffer.reward_team_disc[0, lane],
                "ind_disc": audited.rollout_buffer.reward_ind_disc[0, lane],
                "process": audited.rollout_buffer.reward_process[0, lane],
            }
            for lane in range(spec.lanes)
        ]):
            for name in audited_row:
                np.testing.assert_array_equal(plain_row[name], audited_row[name])
        for name in (
            "masks", "states", "obs", "actions", "rewards", "dones", "values",
            "log_probs", "team_skills", "agent_skills", "gru_hidden_states",
            "critic_gru_hidden_states", "reward_env", "reward_team_disc",
            "reward_ind_disc", "reward_process",
        ):
            np.testing.assert_array_equal(
                getattr(plain.rollout_buffer, name), getattr(audited.rollout_buffer, name)
            )
    finally:
        for env in (*plain_envs, *audited_envs):
            env.close()


def test_evaluator_matches_frozen_b01_and_preserves_rng(tmp_path, spec):
    agent, envs = build(tmp_path, spec)
    try:
        b01_spec = replace(
            b01.DEFAULT_SPEC,
            n_users=spec.n_users,
            horizon=spec.horizon,
            lanes=spec.lanes,
            rollouts=spec.rollouts,
            eval_lanes=spec.eval_lanes,
            eval_rng_seed=spec.eval_rng_seed,
            uniform_final_base=spec.eval_world_base,
            threads=spec.threads,
            small_model=True,
        )
        before_frozen = r.frozen_digest(agent)
        before_rng = r.rng_state_digest()
        numpy_before = pickle.dumps(np.random.get_state())
        torch_before = torch.get_rng_state().clone()
        old = b01.evaluate_panel(
            agent, b01_spec, spec.eval_world_base, "uniform"
        )
        new = r.evaluate_panel(agent, spec, "uniform")
        for key in (
            "status", "rule", "low_actions", "world_seeds", "transitions",
            "optimizer_calls", "normalizer_updates", "returns_U", "native_scores_J",
            "mean_J", "component_means", "connected_users_per_step",
            "raw_saturation_fraction",
        ):
            if isinstance(old[key], (dict, list, np.ndarray)):
                assert r.jsonable(old[key]) == r.jsonable(new[key])
            else:
                assert old[key] == new[key]
        assert new["selected_label_stream_sha256"] == r._uniform_stream_digest(spec)
        assert new["selected_label_renewals"] == spec.horizon // spec.k
        assert r.frozen_digest(agent) == before_frozen
        assert r.rng_state_digest() == before_rng
        assert pickle.dumps(np.random.get_state()) == numpy_before
        assert torch.equal(torch.get_rng_state(), torch_before)
    finally:
        for env in envs:
            env.close()


@pytest.mark.parametrize("mode", ("healthy", "refused", "corrupted"))
def test_storage_rows_are_verified_before_counting(tmp_path, spec, monkeypatch, mode):
    agent, envs = build(tmp_path, spec)
    telemetry = storage_telemetry()
    original = r.AuditedComplementaryAgent.store_rollout_step
    if mode != "healthy":
        def store_rollout_step(self, *args, **kwargs):
            if mode == "refused" and kwargs["env_id"] == 0:
                return False
            result = original(self, *args, **kwargs)
            if mode == "corrupted" and kwargs["env_id"] == 0:
                self.rollout_buffer.rewards[kwargs["t"], kwargs["env_id"], 0] += 1.0
            return result

        monkeypatch.setattr(r.AuditedComplementaryAgent, "store_rollout_step", store_rollout_step)
    try:
        if mode == "healthy":
            assert one_storage_batch(agent, envs, spec, telemetry) == spec.lanes
            assert telemetry == {
                "batch_calls": 1,
                "expected_rows": spec.lanes,
                "verified_rows": spec.lanes,
                "failures": 0,
                "last_failure": None,
            }
        else:
            with pytest.raises(RuntimeError, match="storage verification failed"):
                one_storage_batch(agent, envs, spec, telemetry)
            assert telemetry["failures"] == 1
            assert telemetry["verified_rows"] == 0
            expected = "refused" if mode == "refused" else "stored low reward"
            assert expected in telemetry["last_failure"]["reason"]
    finally:
        for env in envs:
            env.close()


def test_native_env_only_fallback_is_fatal(tmp_path, spec, monkeypatch):
    agent, envs = build(tmp_path, spec)
    telemetry = storage_telemetry()
    monkeypatch.setattr(
        agent,
        "_team_discriminator_logits",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("injected")),
    )
    try:
        with pytest.raises(RuntimeError, match="fell back to env-only"):
            one_storage_batch(agent, envs, spec, telemetry)
        assert telemetry["verified_rows"] == 0
    finally:
        for env in envs:
            env.close()


def test_runner_failure_reports_partial_verified_storage(tmp_path, spec, monkeypatch):
    original = r.AuditedComplementaryAgent.store_rollout_step

    def refuse_second_lane(self, *args, **kwargs):
        if kwargs["env_id"] == 1:
            return False
        return original(self, *args, **kwargs)

    monkeypatch.setattr(
        r.AuditedComplementaryAgent, "store_rollout_step", refuse_second_lane
    )
    out = tmp_path / "partial"
    with pytest.raises(RuntimeError, match="storage verification failed"):
        r.run_fit("D", out, "technical-check", spec=spec, device="cpu")
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "failed"
    assert summary["storage_verification"]["expected_rows"] == 2
    assert summary["storage_verification"]["verified_rows"] == 1
    assert summary["counts"]["stored_transitions"] == 1
    assert summary["counts"]["native_updates"] == 0
    assert len(summary["training_rows"]) == 0
    assert not (out / "final.pt").exists()


@pytest.mark.parametrize(
    "device",
    [
        "cpu",
        pytest.param(
            "cuda",
            marks=pytest.mark.skipif(
                not torch.cuda.is_available(), reason="requires actual CUDA runtime"
            ),
        ),
    ],
)
def test_real_matched_d_g_fits_and_final_json(tmp_path, spec, device):
    summaries = {
        arm: r.run_fit(
            arm, tmp_path / arm, "technical-check", spec=spec, device=device
        )
        for arm in ("D", "G")
    }
    detach, generic = summaries["D"], summaries["G"]
    for arm, summary in summaries.items():
        assert summary["status"] == "complete"
        assert summary["counts"] == {
            "started_fits": 1,
            "model_constructions": 1,
            "training_transitions": 40,
            "stored_transitions": 40,
            "training_episodes": 2,
            "native_updates": 1,
            "evaluation_transitions": 160,
            "evaluation_episodes": 8,
        }
        assert summary["storage_verification"]["verified_rows"] == 40
        assert summary["storage_verification"]["failures"] == 0
        assert set(summary["panels"]) == {
            "initial_own", "initial_uniform", "final_own", "final_uniform"
        }
        assert len(
            {
                panel["physical_initial_state_sha256"]
                for panel in summary["panels"].values()
            }
        ) == 1
        assert (
            summary["panels"]["initial_uniform"]["selected_label_stream_sha256"]
            == summary["panels"]["final_uniform"]["selected_label_stream_sha256"]
        )
        assert all(
            value > 0
            for value in summary["training_rows"][0][
                "relative_initialization_displacement"
            ].values()
        )
        expected_trunk = 0 if arm == "D" else 1
        assert summary["training_rows"][0]["auxiliary"]["trunk_optimizer_steps"] == expected_trunk
        movements = summary["training_rows"][0]["auxiliary"]["trunk_relative_movement"]
        assert all((value == 0) if arm == "D" else (value > 0) for value in movements.values())
        checkpoint = torch.load(
            tmp_path / arm / "final.pt", map_location="cpu", weights_only=False
        )
        assert checkpoint["object_id"] == r.OBJECT
        assert checkpoint["arm"] == arm
        assert "diagnostic" not in summary
        saved = json.loads((tmp_path / arm / "summary.json").read_text())
        assert saved["status"] == "complete"
        assert saved["checkpoints"]["final"]["sha256"] == summary["checkpoints"]["final"]["sha256"]
    assert detach["initial_native_digest"] == generic["initial_native_digest"]
    assert detach["initial_frozen_digest"] == generic["initial_frozen_digest"]
    assert detach["initial_rng_state_sha256"] == generic["initial_rng_state_sha256"]
    assert detach["first_rollout_facts_sha256"] == generic["first_rollout_facts_sha256"]
    assert (
        detach["auxiliary_history"][0]["raw_target_sha256"]
        == generic["auxiliary_history"][0]["raw_target_sha256"]
    )
    d_initial = torch.load(
        tmp_path / "D" / "initial.pt", map_location="cpu", weights_only=False
    )
    g_initial = torch.load(
        tmp_path / "G" / "initial.pt", map_location="cpu", weights_only=False
    )
    for head in ("g_head", "p_head"):
        for name, value in d_initial["auxiliary"][head].items():
            assert torch.equal(value, g_initial["auxiliary"][head][name])


def test_entry_refuses_unadmitted_call_before_outputs(tmp_path):
    out = tmp_path / "must-not-exist"
    result = subprocess.run(
        [
            sys.executable,
            str(b01.ROOT / "scripts/run_complementary_skill_learning_b03.py"),
            "--arm", "D",
            "--seed", "260923921",
            "--launch-sha", "unadmitted",
            "--out", str(out),
        ],
        cwd=b01.ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert not out.exists()
