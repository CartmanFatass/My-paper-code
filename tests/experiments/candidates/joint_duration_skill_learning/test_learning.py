from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch

from configs.config_1 import Config
from experiments.candidates.joint_duration_skill_learning.learning import (
    DURATION_CAP,
    DurationAgent,
    EventRecord,
    compute_event_gae,
    mask_duration_logits,
)


def make_config(mode: str, *, rollout_length: int = 10, num_envs: int = 2) -> Config:
    config = Config()
    config.seed = 20260921
    config.num_envs = num_envs
    config.rollout_length = rollout_length
    config.episode_length = rollout_length
    config.n_Z = config.n_z = 2
    config.embedding_dim = 16
    config.hidden_size = 16
    config.gru_hidden_size = 16
    config.n_heads = 4
    config.n_encoder_layers = 1
    config.n_decoder_layers = 1
    config.action_dim = 2
    config.k = 10
    config.policy_interruption_mode = "d2"
    config.interruption_cost_c = float("inf")
    config.interruption_cost_c_Z = float("inf")
    config.skill_cap_k_max = 10
    config.team_cap_k_Z = 10
    config.age_feature = "off"
    config.duration_mode = mode
    config.duration_lambda_10 = 0.95
    config.coordinator_batch_size = 1280
    config.ppo_epochs = 15
    config.sequence_batch_size = 2
    config.coordinator_dropout = 0.0
    config.update_env_dims(state_dim=5, obs_dim=3, n_agents=2)
    return config


def make_agent(tmp_path: Path, mode: str = "ar", **kwargs) -> DurationAgent:
    return DurationAgent(
        make_config(mode, **kwargs), log_dir=str(tmp_path / mode), device=torch.device("cpu")
    )


def blank_inputs(num_envs: int = 2):
    states = np.zeros((num_envs, 5), dtype=np.float32)
    observations = np.zeros((num_envs, 2, 3), dtype=np.float32)
    return states, observations


def event_from_log(agent: DurationAgent, log: dict, *, sampled=(True, True)) -> EventRecord:
    return EventRecord(
        env_id=0,
        start_step=0,
        state=np.asarray(log["duration_state"], dtype=np.float32),
        observations=np.asarray(log["duration_observations"], dtype=np.float32),
        context=np.asarray(log["duration_context"], dtype=np.float32),
        team_skill=int(agent.env_team_skills[0]),
        agent_skills=np.asarray(agent.env_agent_skills[0], dtype=np.int64),
        order=np.asarray(log["duration_order"], dtype=np.int64),
        sampled_mask=np.asarray(sampled, dtype=np.bool_),
        sample_Z=True,
        duration_tokens=np.asarray(log["duration_tokens"], dtype=np.int64),
        duration_support=np.asarray(log["duration_support"], dtype=np.int64),
        old_team_log_prob=float(log["team_log_prob"]),
        old_agent_log_probs=np.asarray(log["agent_log_probs"], dtype=np.float32),
        old_duration_log_probs=np.asarray(log["duration_log_probs"], dtype=np.float32),
        old_value=float(log["state_value"]),
    )


def set_duration_bias(agent: DurationAgent, duration: int) -> None:
    with torch.no_grad():
        for parameter in agent.skill_coordinator.duration_head.parameters():
            parameter.zero_()
        agent.skill_coordinator.duration_head.net[-1].bias[duration - 1] = 20.0


def test_masked_two_member_law_and_teacher_forced_replay(tmp_path):
    logits = torch.tensor([[0.2] * DURATION_CAP, [-0.3] * DURATION_CAP])
    masked = mask_duration_logits(logits, torch.tensor([2, 4]))
    probabilities = masked.softmax(-1)
    torch.testing.assert_close(probabilities.sum(-1), torch.ones(2))
    assert torch.equal(probabilities[0, 2:], torch.zeros(8))
    assert torch.equal(probabilities[1, 4:], torch.zeros(6))

    # The two-member joint law is the product of the two legal categorical laws.
    enumerated = sum(
        float(probabilities[0, first] * probabilities[1, second])
        for first in range(2) for second in range(4)
    )
    assert enumerated == pytest.approx(1.0)

    agent = make_agent(tmp_path, "ar")
    states, observations = blank_inputs()
    agent.step(states, observations, np.zeros(2, dtype=np.int64), np.zeros(2, dtype=bool),
               return_step_data=True, build_infos=False)
    event = event_from_log(agent, agent.env_log_probs[0])
    replay = agent._evaluate_events([event])
    assert replay["team_log_probs"].item() == pytest.approx(event.old_team_log_prob, abs=2e-6)
    np.testing.assert_allclose(
        replay["agent_log_probs"].detach().numpy()[0], event.old_agent_log_probs, atol=2e-6
    )
    np.testing.assert_allclose(
        replay["duration_log_probs"].detach().numpy()[0], event.old_duration_log_probs, atol=2e-6
    )


def test_held_and_singleton_duration_factors_have_zero_score_entropy(tmp_path):
    agent = make_agent(tmp_path, "ar")
    states, observations = blank_inputs()
    agent.step(states, observations, np.zeros(2, dtype=np.int64), np.zeros(2, dtype=bool),
               return_step_data=True, build_infos=False)
    log = deepcopy(agent.env_log_probs[0])
    log["duration_sampled_mask"] = np.asarray([True, False])
    log["duration_support"] = [1, 0]
    log["duration_tokens"] = [1, 0]
    log["duration_log_probs"] = [0.0, 0.0]
    event = event_from_log(agent, log, sampled=(True, False))
    replay = agent._evaluate_events([event])
    assert torch.equal(replay["duration_log_probs"], torch.zeros_like(replay["duration_log_probs"]))
    assert torch.equal(replay["duration_entropies"], torch.zeros_like(replay["duration_entropies"]))
    assert replay["agent_log_probs"][0, 1].item() == 0.0
    assert replay["agent_entropies"][0, 1].item() == 0.0
    agent.skill_coordinator.zero_grad(set_to_none=True)
    held_score = replay["agent_log_probs"][0, 1] + replay["duration_log_probs"].sum()
    held_score.backward()
    assert all(
        parameter.grad is None or torch.count_nonzero(parameter.grad).item() == 0
        for parameter in agent.skill_coordinator.parameters()
    )


def _make_prefix_sensitive(agent: DurationAgent) -> None:
    head = agent.skill_coordinator.duration_head.net
    with torch.no_grad():
        for parameter in head.parameters():
            parameter.zero_()
        # Prefix occupies the last n_agents input positions.  Route d_0 to one
        # hidden unit and that unit to the first duration logit.
        head[0].weight[0, -2] = 1.0
        head[2].weight[0, 0] = 3.0


def test_ar_prefix_changes_later_factor_while_factored_is_independent(tmp_path):
    ar = make_agent(tmp_path, "ar")
    factored = make_agent(tmp_path, "factored")
    factored.skill_coordinator.load_state_dict(ar.skill_coordinator.state_dict())
    _make_prefix_sensitive(ar)
    factored.skill_coordinator.load_state_dict(ar.skill_coordinator.state_dict())
    states, observations = blank_inputs()
    ar.step(states, observations, np.zeros(2, dtype=np.int64), np.zeros(2, dtype=bool),
            return_step_data=True, build_infos=False)
    base = event_from_log(ar, ar.env_log_probs[0])
    first = deepcopy(base)
    second = deepcopy(base)
    first.duration_tokens = np.asarray([1, 2])
    second.duration_tokens = np.asarray([9, 2])
    first.duration_support = second.duration_support = np.asarray([10, 10])
    ar_log = ar._evaluate_events([first, second])["duration_log_probs"].detach()
    factored_log = factored._evaluate_events([first, second])["duration_log_probs"].detach()
    assert ar_log[0, 1].item() != pytest.approx(ar_log[1, 1].item())
    assert factored_log[0, 1].item() == pytest.approx(factored_log[1, 1].item())


def test_deadline_edges_held_commitment_cap_and_fixed_ten(tmp_path):
    states, observations = blank_inputs()
    fixed = make_agent(tmp_path, "fixed")
    _, _, first = fixed.step(
        states, observations, np.zeros(2, dtype=np.int64), np.zeros(2, dtype=bool),
        return_step_data=True, build_infos=False,
    )
    assert first["log_probs"][0]["duration_tokens"] == [10, 10]
    for step in range(1, 10):
        _, _, data = fixed.step(
            states, observations, np.full(2, step), np.zeros(2, dtype=bool),
            return_step_data=True, build_infos=False,
        )
        assert not data["d2_decision"].any()
    _, _, cap = fixed.step(
        states, observations, np.full(2, 10), np.zeros(2, dtype=bool),
        return_step_data=True, build_infos=False,
    )
    assert cap["d2_team_decision"].all()
    assert cap["log_probs"][0]["duration_support"] == [10, 10]

    variable = make_agent(tmp_path, "factored")
    set_duration_bias(variable, 1)
    variable.step(states, observations, np.zeros(2, dtype=np.int64), np.zeros(2, dtype=bool),
                  return_step_data=True, build_infos=False)
    _, _, next_step = variable.step(
        states, observations, np.ones(2, dtype=np.int64), np.zeros(2, dtype=bool),
        return_step_data=True, build_infos=False,
    )
    assert next_step["d2_decision"].all(), "d=1 must execute one physical step before renewal"

    # One member expires earlier while the other member's absolute deadline is held.
    variable._duration_agent_deadlines[0] = np.asarray([2, 8])
    variable._duration_agent_commit_start[0] = np.asarray([1, 1])
    variable._duration_team_deadline[0] = 10
    _, _, partial = variable.step(
        states, observations, np.asarray([2, 1]), np.zeros(2, dtype=bool),
        return_step_data=True, build_infos=False,
    )
    assert partial["d2_sampled_mask"][0].tolist() == [True, False]
    assert variable._duration_agent_deadlines[0][1] == 8


def test_terminal_event_gae_and_lambda_one_telescope_across_delayed_reward():
    gamma = 0.9
    # Primitive rewards [1,2,3,4] split into two two-step events.
    event_rewards = [1.0 + gamma * 2.0, 3.0 + gamma * 4.0]
    advantages, returns = compute_event_gae(
        event_rewards, [0.0, 0.0], [2, 2], [False, True], gamma=gamma, lambda_10=1.0
    )
    primitive_return = 1.0 + gamma * 2.0 + gamma**2 * 3.0 + gamma**3 * 4.0
    assert returns[0] == pytest.approx(primitive_return)
    assert advantages[1] == pytest.approx(event_rewards[1])

    delayed_advantage, _ = compute_event_gae(
        [0.0, 1.0], [0.0, 0.0], [2, 3], [False, True], gamma=gamma, lambda_10=1.0
    )
    assert delayed_advantage[0] == pytest.approx(gamma**2)

    # A supplied cutoff value is lawful in the helper, although the native runner rejects it.
    cutoff_advantage, _ = compute_event_gae(
        [0.0], [0.25], [2], [False], gamma=gamma, lambda_10=1.0,
        bootstrap_values={0: 2.0},
    )
    assert cutoff_advantage[0] == pytest.approx(gamma**2 * 2.0 - 0.25)


def test_suffix_dependent_two_factor_score_gradient_is_not_erased():
    theta = torch.tensor(0.4, requires_grad=True)
    p = theta.sigmoid()
    objective = 0.0
    score_estimator = 0.0
    for first in (0.0, 1.0):
        prob_first = p if first else 1.0 - p
        q = 0.25 + 0.5 * first
        for suffix in (0.0, 1.0):
            probability = prob_first * (q if suffix else 1.0 - q)
            objective = objective + probability * suffix
            score = first - p
            score_estimator = score_estimator + probability * score * suffix
    direct_gradient = torch.autograd.grad(objective, theta)[0]
    assert direct_gradient.item() == pytest.approx(0.5 * p.item() * (1.0 - p.item()))
    assert score_estimator.item() == pytest.approx(direct_gradient.item())
    assert direct_gradient.item() > 0.0


def _parameters(module):
    return [parameter.detach().clone() for parameter in module.parameters()]


def _moved(before, module) -> bool:
    return any(not torch.equal(old, new.detach()) for old, new in zip(before, module.parameters()))


def test_collector_storage_and_update_reach_high_low_and_discriminator(tmp_path):
    torch.manual_seed(9)
    np.random.seed(9)
    agent = make_agent(tmp_path, "ar")
    coordinator_before = _parameters(agent.skill_coordinator)
    duration_before = _parameters(agent.skill_coordinator.duration_head)
    discoverer_before = _parameters(agent.skill_discoverer)
    discriminator_before = _parameters(agent.team_discriminator)
    rng = np.random.default_rng(17)
    states = rng.normal(size=(2, 5)).astype(np.float32)
    observations = rng.normal(size=(2, 2, 3)).astype(np.float32)
    dones = np.zeros(2, dtype=bool)
    total_reward = 0.0
    for step in range(10):
        actions, _, step_data = agent.step(
            states, observations, np.full(2, step), dones,
            return_step_data=True, build_infos=False,
        )
        next_states = rng.normal(size=(2, 5)).astype(np.float32)
        next_observations = rng.normal(size=(2, 2, 3)).astype(np.float32)
        rewards = np.asarray([0.1 + 0.01 * step, -0.05 + 0.02 * step], dtype=np.float32)
        next_dones = np.full(2, step == 9, dtype=bool)
        total_reward += float(rewards.sum())
        agent.store_transition_batch(
            states, next_states, observations, next_observations, actions, rewards, next_dones,
            rollout_step_idx=step, step_data=step_data,
        )
        states, observations, dones = next_states, next_observations, next_dones

    assert not agent._duration_open_events
    assert sum(event.elapsed for event in agent._duration_events) == 20
    assert sum(event.reward for event in agent._duration_events) != pytest.approx(0.0)
    result = agent.update(
        last_values=np.zeros((2, 2), dtype=np.float32), dones=dones, steps_in_buffer=10
    )
    assert np.isfinite(result["coordinator_loss"])
    assert _moved(coordinator_before, agent.skill_coordinator)
    assert _moved(duration_before, agent.skill_coordinator.duration_head)
    assert _moved(discoverer_before, agent.skill_discoverer)
    assert _moved(discriminator_before, agent.team_discriminator)
    metrics = agent.get_duration_metrics()
    assert metrics["events"] > 0
    assert metrics["joint_nondegenerate_events"] > 0
    assert metrics["stored_event_elapsed_total"] == 20
    assert metrics["last_update"]["optimizer_steps"] == 15
    assert metrics["replay_pre_max_abs_error"] < 2e-5


def test_nonterminal_update_clear_and_reset_refuse_to_drop_open_event(tmp_path):
    agent = make_agent(tmp_path, "ar", rollout_length=10, num_envs=1)
    states, observations = blank_inputs(1)
    actions, _, step_data = agent.step(
        states, observations, np.zeros(1, dtype=np.int64), np.zeros(1, dtype=bool),
        return_step_data=True, build_infos=False,
    )
    agent.store_transition_batch(
        states, states, observations, observations, actions, np.ones(1), np.zeros(1, dtype=bool),
        rollout_step_idx=0, step_data=step_data,
    )
    with pytest.raises(ValueError, match="terminal-aligned"):
        agent.update(np.zeros((1, 2), dtype=np.float32), np.zeros(1, dtype=bool), 1)
    with pytest.raises(ValueError, match="unclosed"):
        agent.clear_buffers()
    with pytest.raises(ValueError, match="unclosed"):
        agent.reset_env_state(0)


def test_evaluation_finalization_records_terminal_execution_without_training_events(tmp_path):
    agent = make_agent(tmp_path, "fixed", num_envs=1)
    states, observations = blank_inputs(1)
    for step in range(10):
        agent.step(
            states, observations, np.asarray([step]), np.zeros(1, dtype=bool),
            deterministic=True, return_step_data=True, build_infos=False,
        )
    agent.finish_evaluation_episode(np.ones(1, dtype=bool))
    metrics = agent.get_duration_metrics()
    assert metrics["events"] == 1
    assert metrics["joint_nondegenerate_events"] == 0
    assert metrics["stored_events"] == 0
    assert metrics["terminal_boundaries"] == 1
    assert metrics["executed_duration"]["histogram"] == {"10": 2}
