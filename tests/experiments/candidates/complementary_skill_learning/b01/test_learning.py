from __future__ import annotations

import copy
import math
import random
from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner
from experiments.candidates.complementary_skill_learning.b01.learning import (
    AUXILIARY_DISCOUNT,
    ComplementaryAgent,
    MixtureSkillDecoder,
)
from hmasd.agent import HMASDAgent
from hmasd.networks import SkillDecoder


TECHNICAL_SEED = 7319


def technical_spec():
    return replace(
        runner.DEFAULT_SPEC,
        horizon=20,
        lanes=2,
        rollouts=1,
        eval_lanes=2,
        diagnostic_lanes=2,
        prefix_steps=10,
        small_model=True,
    )


def build(tmp_path, arm="D", seed=TECHNICAL_SEED):
    spec = technical_spec()
    envs = runner.make_envs(spec, spec.lanes, spec.train_world_base)
    config = runner.make_config(spec, envs)
    runner.seed_rng(seed)
    agent = ComplementaryAgent(
        config=config,
        arm=arm,
        head_seed=spec.head_seed,
        aux_seed=spec.aux_seed,
        log_dir=str(tmp_path / f"agent-{arm}-{seed}"),
        device=torch.device("cpu"),
    )
    return spec, envs, config, agent


def state_dict_copy(module):
    return {name: value.detach().clone() for name, value in module.state_dict().items()}


def changed(module, before):
    return any(not torch.equal(value.detach(), before[name]) for name, value in module.state_dict().items())


def seed_auxiliary_samples(agent, count=8):
    rng = np.random.default_rng(301)
    for index in range(count):
        agent._auxiliary_samples.append(
            {
                "env_id": index % 2,
                "state": rng.normal(size=agent.config.state_dim).astype(np.float32),
                "observations": rng.normal(
                    size=(agent.config.n_agents, agent.config.obs_dim)
                ).astype(np.float32),
                "entering_hidden": rng.normal(
                    size=(agent.config.n_agents, agent.config.gru_hidden_size)
                ).astype(np.float32),
                "entry_masks": np.asarray(
                    [0.0 if index == 0 else 1.0] * agent.config.n_agents,
                    dtype=np.float32,
                ),
                "step": 10 * index,
                "team_skill": index % 6,
                "agent_skills": (np.arange(agent.config.n_agents) + index) % 6,
                "target": float(index - 3),
            }
        )


def collect_rollout(agent, envs, horizon=20):
    states, observations = runner.native._reset_all(envs)
    lanes = len(envs)
    env_steps = np.zeros(lanes, dtype=np.int64)
    dones = np.zeros(lanes, dtype=bool)
    raw_rewards = np.zeros((horizon, lanes), dtype=np.float64)
    for t in range(horizon):
        actions, _, data = agent.step(
            states,
            observations,
            env_steps,
            dones,
            deterministic=False,
            return_step_data=True,
            build_infos=False,
        )
        next_states, next_observations = [], []
        next_dones = np.zeros(lanes, dtype=bool)
        for lane, env in enumerate(envs):
            state, observation, reward, done, _, _ = runner.physical_step(env, actions[lane])
            next_states.append(state)
            next_observations.append(observation)
            raw_rewards[t, lane] = reward
            next_dones[lane] = done
        next_states = np.stack(next_states)
        next_observations = np.stack(next_observations)
        agent.store_transition_batch(
            states=states,
            next_states=next_states.copy(),
            observations=observations,
            next_observations=next_observations.copy(),
            actions=actions,
            rewards=raw_rewards[t],
            dones=next_dones,
            infos_batch=None,
            rollout_step_idx=t,
            step_data=data,
        )
        for lane, env in enumerate(envs):
            if next_dones[lane]:
                reset_observation, reset_info = env.reset()
                next_observations[lane] = np.asarray(reset_observation, dtype=np.float32)
                next_states[lane] = np.asarray(reset_info["state"], dtype=np.float64)
                agent.reset_env_state(lane)
                env_steps[lane] = 0
            else:
                env_steps[lane] += 1
        states, observations, dones = next_states, next_observations, next_dones
    return states, observations, dones, raw_rewards


def test_mixture_decoder_and_ordered_replay_share_mu_with_forced_zeros(tmp_path):
    _, _, config, agent = build(tmp_path)
    decoder = agent.skill_coordinator.skill_decoder
    assert isinstance(decoder, MixtureSkillDecoder)

    batch, n_agents, embedding = 2, config.n_agents, config.embedding_dim
    encoded_state = torch.linspace(-1, 1, batch * embedding).reshape(batch, 1, embedding)
    encoded_obs = torch.linspace(1, -1, batch * n_agents * embedding).reshape(
        batch, n_agents, embedding
    )
    team = torch.tensor([1, 4])
    native_individual_logits = SkillDecoder.forward(
        decoder,
        encoded_state,
        encoded_obs,
        team,
        None,
        step=1,
        agent_specific_query=encoded_obs[:, :1],
    )
    log_mu = decoder(
        encoded_state,
        encoded_obs,
        team,
        None,
        step=1,
        agent_specific_query=encoded_obs[:, :1],
    )
    expected_mu = 0.9 * native_individual_logits.softmax(-1) + 0.1 / 6.0
    torch.testing.assert_close(log_mu.exp(), expected_mu, rtol=1e-6, atol=1e-7)
    assert float(log_mu.exp().min()) >= 0.1 / 6.0 - 1e-7
    torch.testing.assert_close(
        decoder(encoded_state, encoded_obs),
        SkillDecoder.forward(decoder, encoded_state, encoded_obs),
        rtol=0,
        atol=0,
    )

    states = torch.zeros(batch, config.state_dim)
    observations = torch.zeros(batch, n_agents, config.obs_dim)
    held_z = torch.tensor([[0, 1, 2, 3, 4, 5], [5, 4, 3, 2, 1, 0]])
    sample_z = torch.tensor([False, True])
    sampled = torch.tensor(
        [[False, True, False, True, False, True], [True, False, True, False, True, False]]
    )
    torch.manual_seed(17)
    assigned = agent.skill_coordinator.assign_partial_batch(
        states, observations, team, held_z, sample_z, sampled, deterministic=False
    )
    replay = agent.skill_coordinator.evaluate_training_batch_ordered(
        states,
        observations,
        assigned["team_skills"],
        assigned["agent_skills"],
        assigned["order"],
        sampled,
        sample_z,
    )
    torch.testing.assert_close(replay["team_log_probs"], assigned["team_log_probs"], atol=2e-6, rtol=0)
    torch.testing.assert_close(replay["agent_log_probs"], assigned["agent_log_probs"], atol=2e-6, rtol=0)
    assert torch.count_nonzero(replay["team_log_probs"][~sample_z]) == 0
    assert torch.count_nonzero(replay["team_entropy"][~sample_z]) == 0
    assert torch.count_nonzero(replay["agent_log_probs"][~sampled]) == 0
    assert torch.count_nonzero(replay["agent_entropies"][~sampled]) == 0


def test_head_initialization_and_auxiliary_shuffle_do_not_touch_native_rng(tmp_path):
    spec = technical_spec()
    envs = runner.make_envs(spec, spec.lanes, spec.train_world_base)
    config = runner.make_config(spec, envs)

    def construct(kind):
        runner.seed_rng(818)
        if kind == "native":
            learner = HMASDAgent(
                config, log_dir=str(tmp_path / "native"), device=torch.device("cpu")
            )
        else:
            learner = ComplementaryAgent(
                config, kind, spec.head_seed, spec.aux_seed,
                str(tmp_path / kind), torch.device("cpu"),
            )
        return (
            learner,
            random.getstate(),
            copy.deepcopy(np.random.get_state()),
            torch.get_rng_state().clone(),
        )

    native, py_state, np_state, torch_state = construct("native")
    for arm in "DGP":
        candidate, py_after, np_after, torch_after = construct(arm)
        assert py_after == py_state
        assert np.array_equal(np_after[1], np_state[1])
        assert torch.equal(torch_after, torch_state)
        assert runner.native_digest(candidate) == runner.native_digest(native)

    _, _, _, candidate = build(tmp_path, arm="G", seed=919)
    seed_auxiliary_samples(candidate)
    py_before = random.getstate()
    np_before = copy.deepcopy(np.random.get_state())
    torch_before = torch.get_rng_state().clone()
    candidate._run_auxiliary_update()
    assert random.getstate() == py_before
    assert np.array_equal(np.random.get_state()[1], np_before[1])
    assert torch.equal(torch.get_rng_state(), torch_before)


@pytest.mark.parametrize("arm,expect_trunk_steps", [("D", 0), ("G", 1), ("P", 1)])
def test_auxiliary_gradient_destinations_counts_and_checkpoint(tmp_path, arm, expect_trunk_steps):
    _, _, _, agent = build(tmp_path, arm=arm, seed=617)
    seed_auxiliary_samples(agent)
    trunk_before = {
        name: state_dict_copy(module)
        for name, module in (
            ("base", agent.skill_discoverer.actor.base),
            ("film", agent.skill_discoverer.actor.film_generator),
            ("gru", agent.skill_discoverer.actor.rnn),
        )
    }
    action_head_before = state_dict_copy(agent.skill_discoverer.actor.act)
    g_before, p_before = state_dict_copy(agent.g_head), state_dict_copy(agent.p_head)
    row = agent._run_auxiliary_update()

    assert row["head_optimizer_steps"] == {"G": 1, "P": 1}
    assert row["trunk_optimizer_steps"] == expect_trunk_steps
    assert row["raw_prediction_rows"]["env_id"] == [index % 2 for index in range(8)]
    assert row["raw_prediction_rows"]["boundary_step"] == [10 * index for index in range(8)]
    assert len(row["raw_prediction_rows"]["raw_target"]) == 8
    assert changed(agent.g_head, g_before) and changed(agent.p_head, p_before)
    for name, module in (
        ("base", agent.skill_discoverer.actor.base),
        ("film", agent.skill_discoverer.actor.film_generator),
        ("gru", agent.skill_discoverer.actor.rnn),
    ):
        assert changed(module, trunk_before[name]) is (arm in {"G", "P"})
        assert (row["trunk_relative_movement"][name] > 0) is (arm in {"G", "P"})
    assert not changed(agent.skill_discoverer.actor.act, action_head_before)
    assert abs(agent.parameter_counts["G"] - agent.parameter_counts["P"]) < 1000
    assert row["architecture"]["P_pair_rank"] == 32

    before_prediction_state = {
        "G": state_dict_copy(agent.g_head),
        "P": state_dict_copy(agent.p_head),
        "base": state_dict_copy(agent.skill_discoverer.actor.base),
    }
    sample = agent._auxiliary_samples[:3]
    predictions = agent.predict_returns(
        np.stack([value["state"] for value in sample]),
        np.stack([value["observations"] for value in sample]),
        np.stack([value["entering_hidden"] for value in sample])[:, :, None, :],
        np.stack([value["entry_masks"] for value in sample])[:, :, None],
        np.asarray([value["step"] for value in sample]),
        np.asarray([value["team_skill"] for value in sample]),
        np.stack([value["agent_skills"] for value in sample]),
    )
    assert set(predictions) == {"G", "P"}
    assert predictions["G"].shape == predictions["P"].shape == (3,)
    assert not changed(agent.g_head, before_prediction_state["G"])
    assert not changed(agent.p_head, before_prediction_state["P"])
    assert not changed(agent.skill_discoverer.actor.base, before_prediction_state["base"])

    checkpoint = copy.deepcopy(agent.auxiliary_state_dict())
    expected_next_order = agent._shuffle_rng.permutation(11)
    for parameter in agent.g_head.parameters():
        parameter.data.zero_()
    agent.load_auxiliary_state_dict(checkpoint)
    np.testing.assert_array_equal(agent._shuffle_rng.permutation(11), expected_next_order)


def test_real_collect_store_update_labels_terminal_windows_and_moves_native_groups(tmp_path):
    spec, envs, _, agent = build(tmp_path, arm="G", seed=1221)
    states, observations, dones, rewards = collect_rollout(agent, envs, spec.horizon)

    assert len(agent._auxiliary_samples) == spec.lanes * (spec.horizon // spec.k)
    assert not agent._pending_windows
    discount = AUXILIARY_DISCOUNT ** np.arange(10)
    for boundary_index, start in enumerate((0, 10)):
        for lane in range(spec.lanes):
            sample = agent._auxiliary_samples[boundary_index * spec.lanes + lane]
            assert sample["env_id"] == lane
            assert sample["step"] == start
            assert sample["target"] == pytest.approx(float(discount @ rewards[start:start + 10, lane]))
            np.testing.assert_array_equal(
                sample["entering_hidden"], agent.rollout_buffer.gru_hidden_states[start, lane]
            )
    # The t=19 terminal reward is part of the second real ten-step target.
    assert dones.all()
    assert agent._discarded_terminal_windows == 0

    py_state = random.getstate()
    np_state = copy.deepcopy(np.random.get_state())
    torch_state = torch.get_rng_state().clone()
    replay = agent._native_replay_telemetry(spec.horizon)
    assert random.getstate() == py_state
    assert np.array_equal(np.random.get_state()[1], np_state[1])
    assert torch.equal(torch.get_rng_state(), torch_state)
    assert replay["rows"] == 4
    assert replay["max_sampled_log_mu_discrepancy"] < 1e-5
    assert replay["max_forced_abs_log_probability"] == 0.0

    native_before = {
        name: state_dict_copy(getattr(agent, name))
        for name in runner.MODULES
    }
    result = agent.update(
        last_values=np.zeros((spec.lanes, spec.n_agents), dtype=np.float32),
        dones=dones.copy(),
        steps_in_buffer=spec.horizon,
        last_state=states.copy(),
        last_observations=observations.copy(),
    )
    assert set(result["complementary_auxiliary"]["native_mu_replay"]) >= {
        "old_agent_log_mu", "replayed_agent_log_mu", "sampled_mask"
    }
    assert len(agent.auxiliary_history) == 1
    row = agent.auxiliary_history[0]
    assert row["samples"] == 4
    assert row["head_optimizer_steps"] == {"G": 1, "P": 1}
    assert row["trunk_optimizer_steps"] == 1
    assert row["first_rollout_target_sha256"] == row["raw_target_sha256"]
    for name in runner.MODULES:
        assert changed(getattr(agent, name), native_before[name]), name


def test_terminal_before_ten_drops_window_without_crossing_reset(tmp_path):
    _, _, config, agent = build(tmp_path)
    states = np.zeros((1, config.state_dim), dtype=np.float32)
    observations = np.zeros((1, config.n_agents, config.obs_dim), dtype=np.float32)
    base_data = {
        "d2_team_decision": np.asarray([True]),
        "d2_sampled_mask": np.ones((1, config.n_agents), dtype=bool),
        "team_skills": np.asarray([2]),
        "agent_skills": np.arange(config.n_agents, dtype=np.int64)[None],
        "complementary_steps": np.asarray([0]),
        "complementary_entering_hidden": np.zeros(
            (1, config.n_agents, config.gru_hidden_size), dtype=np.float32
        ),
        "complementary_entry_masks": np.ones((1, config.n_agents), dtype=np.float32),
    }
    agent._capture_auxiliary_transitions(
        states, observations, np.asarray([3.0]), np.asarray([True]), base_data
    )
    assert not agent._pending_windows
    assert not agent._auxiliary_samples
    assert agent._discarded_terminal_windows == 1

