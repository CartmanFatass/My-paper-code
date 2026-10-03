"""Pure synthetic learner checks; at most 16 real Adam steps for the whole file.

Clock/capacity fixtures mock optimization. No environment, controller, radio or
scientific runner imports occur. The DM owns execution and its cumulative budget.
"""
import copy
import math
import random

import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_resource_control.b01_native_selector.learner import (
    BATCH_SIZE, CAPACITY, INPUT_DIM, Learner,
)


SEEDS = dict(init_seed=51030011, exploration_seed=52030011, replay_seed=53030011)


def learner():
    return Learner(**SEEDS)


def features(offset=0.):
    return (np.linspace(-.5, .7, INPUT_DIM) + offset).astype(np.float32)


def mission(agent, index, blocks=1, training=True, partial=30):
    agent.start_episode(index, training)
    for block in range(blocks):
        agent.decide(features(block / 10), block % 2 == 0, block * 30)
        ticks = partial if block == blocks - 1 else 30
        for tick in range(ticks):
            agent.observe_reward((block + 1) * .3 + tick / 100,
                                 block == blocks - 1 and tick == ticks - 1)
    return agent.episode_arrays()


def warmup(agent):
    for index in range(16):
        mission(agent, index, blocks=4)
    assert agent.replay_size == 64 and agent.updates == 0


def replay_fixture(agent):
    # Independent numerical fixture: valid replay data without native effects.
    agent.replay_size = BATCH_SIZE
    for i in range(BATCH_SIZE):
        agent.replay["features"][i] = features(i / 100)
        agent.replay["next_features"][i] = features((i + 1) / 100)
        agent.replay["action"][i] = i % 2
        agent.replay["reward"][i] = .5
        agent.replay["id"][i] = i


def assert_arrays_equal(first, second):
    assert first.keys() == second.keys()
    for key in first:
        np.testing.assert_array_equal(first[key], second[key], err_msg=key)


def fake_optimize(indices):
    return dict(selected_q=np.zeros(64, np.float32), targets=np.zeros(64, np.float32),
                next_actions=np.zeros(64, np.int64), loss=0., gradient_norm=0.)


def test_initialization_global_rng_isolation_and_live_hidden_layers():
    torch_state = torch.random.get_rng_state().clone()
    numpy_state = copy.deepcopy(np.random.get_state())
    python_state = random.getstate()
    agent = learner()
    assert torch.equal(torch_state, torch.random.get_rng_state())
    np.testing.assert_array_equal(numpy_state[1], np.random.get_state()[1])
    assert numpy_state[0] == np.random.get_state()[0]
    assert numpy_state[2:] == np.random.get_state()[2:]
    assert python_state == random.getstate()
    assert sum(p.numel() for p in agent.online.parameters()) == 25282
    assert all(p.dtype == torch.float32 and p.device.type == "cpu" for p in agent.online.parameters())
    for layer in (agent.online[0], agent.online[2]):
        bound = math.sqrt(6 / layer.in_features)
        assert torch.count_nonzero(layer.weight) > 0
        assert torch.max(torch.abs(layer.weight)) <= bound
        assert torch.count_nonzero(layer.bias) == 0
    assert torch.count_nonzero(agent.online[4].weight) == 0
    assert torch.count_nonzero(agent.online[4].bias) == 0
    assert agent.digests()["online"] == agent.digests()["target"]
    agent.start_episode(0, False)
    decision = agent.decide(features(), True, 0)
    assert decision["action"] == 0
    np.testing.assert_array_equal(decision["q_values"], [0., 0.])


def test_partial_terminal_reward_fsum_fixed_divisor_and_reset():
    agent = learner()
    agent.start_episode(0, True)
    agent.decide(features(), False, 0)
    rewards = [1e16, 1., -1e16, .25]
    for i, reward in enumerate(rewards):
        agent.observe_reward(reward, i == len(rewards) - 1)
    arrays = agent.episode_arrays()
    assert arrays["transition_reward64"][0] == math.fsum(rewards) / 30
    assert arrays["transition_reward32"][0] == np.float32(math.fsum(rewards) / 30)
    assert arrays["transition_terminal"].tolist() == [True]
    assert arrays["transition_end_step"].tolist() == [4]
    assert not arrays["transition_next_features"].any()
    assert not arrays["transition_next_h_eligible"].any()
    assert agent.transitions == 1 and agent.updates == 0
    with pytest.raises(RuntimeError):
        agent.decide(features(), True, 30)
    old_rng = copy.deepcopy(agent.exploration_rng.bit_generator.state)
    agent.start_episode(1, True)
    assert old_rng == agent.exploration_rng.bit_generator.state
    assert agent.transitions == 1 and agent.replay_size == 1
    assert agent.episode_arrays()["action_features"].shape == (0, 327)
    assert all(array.dtype.kind != "O" for array in agent.episode_arrays().values())


def test_training_draws_even_forced_and_evaluation_draws_none():
    agent = learner()
    expected = np.random.Generator(np.random.PCG64(SEEDS["exploration_seed"]))
    for index, eligible in enumerate((False, True, False)):
        agent.start_episode(index, True)
        decision = agent.decide(features(), eligible, 0)
        draws = expected.random(2)
        np.testing.assert_array_equal(decision["exploration_draws"], draws)
        assert decision["epsilon"] == 1.
        assert decision["action"] == (math.floor(draws[1] * 2) if eligible else 0)
        agent.observe_reward(0., True)
    before = agent.state()
    mission(agent, 0, training=False, blocks=2)
    assert before["exploration_rng"] == agent.exploration_rng.bit_generator.state
    assert before["replay_rng"] == agent.replay_rng.bit_generator.state
    assert before["counts"]["updates"] == agent.updates
    assert before["counts"]["transitions"] == agent.transitions
    assert agent.episode_arrays()["action_epsilon"].tolist() == [0., 0.]
    assert np.isnan(agent.episode_arrays()["action_exploration_draws"]).all()


def test_boundary_update_precedes_q_and_epsilon_counts_all_transitions(monkeypatch):
    agent = learner()
    warmup(agent)
    def optimize(indices):
        with torch.no_grad():
            agent.online[4].bias.add_(1.)
        return fake_optimize(indices)
    monkeypatch.setattr(agent, "_optimize", optimize)
    agent.start_episode(16, True)
    first = agent.decide(features(), True, 0)
    assert first["epsilon"] == 1. and first["updates"] == 0
    for _ in range(30):
        agent.observe_reward(.3, False)
    assert agent.transitions == 64  # Nonterminal context not fabricated early.
    second = agent.decide(features(.1), False, 30)
    assert second["updates"] == 1 and second["action"] == 0
    assert second["epsilon"] == 1 - .95 / 6400
    np.testing.assert_array_equal(second["q_values"], [1., 1.])
    agent.observe_reward(.6, True)
    assert agent.updates == 2 and agent.postwarmup_transitions == 2
    arrays = agent.episode_arrays()
    assert arrays["transition_terminal"].tolist() == [False, True]
    np.testing.assert_array_equal(arrays["transition_next_features"][0], features(.1))
    assert arrays["update_transition_id"].tolist() == [64, 65]
    for indices in arrays["update_indices"]:
        assert len(set(indices)) == 64


def test_early_endings_skip_until64_without_padding(monkeypatch):
    agent = learner()
    monkeypatch.setattr(agent, "_optimize", fake_optimize)
    for index in range(64):
        mission(agent, index, partial=1)
    assert agent.transitions == 64 and agent.training_ticks == 64
    assert agent.skipped_updates == 47  # Missions16..62, replay17..63.
    assert agent.postwarmup_transitions == 48 and agent.updates == 1
    assert agent.episode_arrays()["transition_update_skipped"].tolist() == [False]
    mission(agent, 64, partial=1)
    assert agent.updates == 2


def test_double_dqn_mask_gamma_one_terminal_and_mean_smooth_l1():
    agent = learner()
    replay_fixture(agent)
    agent.replay["next_h_eligible"][:64] = True
    agent.replay["next_h_eligible"][:16] = False
    agent.replay["terminal"][32:64] = True
    with torch.no_grad():
        agent.online[4].bias.copy_(torch.tensor([1., 3.]))
        agent.target[4].bias.copy_(torch.tensor([5., 7.]))
    result = agent._optimize(np.arange(64))  # One Adam step.
    expected = np.concatenate((np.full(16, 5.5), np.full(16, 7.5), np.full(32, .5))).astype(np.float32)
    selected = np.tile(np.array([1., 3.], np.float32), 32)
    np.testing.assert_array_equal(result["targets"], expected)
    np.testing.assert_array_equal(result["selected_q"], selected)
    assert result["next_actions"][:16].tolist() == [0] * 16
    assert result["next_actions"][16:].tolist() == [1] * 48
    errors = np.abs(selected - expected)
    expected_loss = np.mean(np.where(errors < 1, .5 * errors ** 2, errors - .5))
    assert result["loss"] == float(expected_loss)
    norm_after = torch.sqrt(sum(p.grad.square().sum() for p in agent.online.parameters()))
    assert float(norm_after) <= 10.00001
    assert all(p.grad is None for p in agent.target.parameters())
    assert agent.optimizer.param_groups[0]["lr"] == 3e-4
    assert agent.optimizer.param_groups[0]["eps"] == 1e-8
    assert agent.optimizer.param_groups[0]["betas"] == (.9, .999)


def test_zero_head_then_hidden_layers_train_and_gradient_clips():
    agent = learner()
    replay_fixture(agent)
    agent.replay["reward"][:64] = 100.
    agent.replay["features"][:64] *= 100
    initial_hidden = agent.online[0].weight.detach().clone()
    initial_head = agent.online[4].weight.detach().clone()
    first = agent._optimize(np.arange(64))  # First step moves only the zero head.
    assert first["gradient_norm"] > 10.
    clipped = torch.sqrt(sum(p.grad.square().sum() for p in agent.online.parameters()))
    assert float(clipped) <= 10.00001
    assert not torch.equal(initial_head, agent.online[4].weight)
    assert torch.equal(initial_hidden, agent.online[0].weight)
    agent._optimize(np.arange(64))  # Second step reaches the live hidden layers.
    assert not torch.equal(initial_hidden, agent.online[0].weight)


def test_greedy_action_mask_exact_tie_and_epsilon_floor():
    agent = learner()
    with torch.no_grad():
        agent.online[4].bias.copy_(torch.tensor([1., 3.]))
    arrays = mission(agent, 0, blocks=2, training=False, partial=1)
    assert arrays["action_action"].tolist() == [1, 0]
    with torch.no_grad():
        agent.online[4].bias.fill_(2.)
    assert mission(agent, 1, training=False, partial=1)["action_action"].tolist() == [0]
    # Schedule-only fixture: r includes all completed postwarmup transitions.
    agent.training_missions = 16
    agent.postwarmup_transitions = 10000
    agent.start_episode(16, True)
    assert agent.decide(features(), False, 0)["epsilon"] == .05


def test_target_copy_uses_completed_update_clock_not_mission_clock(monkeypatch):
    agent = learner()
    replay_fixture(agent)
    def optimize(indices):
        with torch.no_grad():
            agent.online[4].bias.add_(.01)
        return fake_optimize(indices)
    monkeypatch.setattr(agent, "_optimize", optimize)
    initial_target = agent.digests()["target"]
    for index in range(199):
        agent._update(index)
    assert agent.updates == 199 and agent.digests()["target"] == initial_target
    agent._update(199)
    assert agent.updates == 200
    assert agent.digests()["target"] == agent.digests()["online"]
    assert agent.episode_arrays()["update_target_copy"].sum() == 1
    assert agent.episode_arrays()["update_target_copy"][-1]


def test_ring_slot_keeps_immutable_transition_ids(monkeypatch):
    agent = learner()
    replay_fixture(agent)
    agent.transitions = CAPACITY
    agent.replay_size = CAPACITY
    agent.training_missions = 16
    agent.start_episode(16, True)
    monkeypatch.setattr(agent, "_optimize", fake_optimize)
    agent.decide(features(), False, 0)
    agent.observe_reward(1., True)
    assert agent.replay["id"][0] == CAPACITY
    assert agent.replay_size == CAPACITY
    assert agent.episode_arrays()["transition_slot"].tolist() == [0]
    assert agent.episode_arrays()["transition_id"].tolist() == [CAPACITY]


def test_compact_checkpoints_initial_reconstruction_and_final_inference_only():
    agent = learner()
    initial = agent.state(include_replay=False)
    assert "replay" not in initial and "rows" not in initial
    clone = learner()
    clone.load_state(initial)
    assert clone.digests() == agent.digests()
    assert_arrays_equal(mission(agent, 0, partial=3), mission(clone, 0, partial=3))
    checkpoint = agent.state(include_replay=False)
    clone.load_state(checkpoint)
    assert clone.digests() == agent.digests()
    with pytest.raises(RuntimeError, match="inference-only"):
        clone.start_episode(1, True)
    arrays = mission(clone, 0, training=False, partial=3)
    assert arrays["action_epsilon"].tolist() == [0.]
    assert clone.updates == 0


def test_every_decision_reward_and_actual_update_reconstructs_from_initial():
    actual = learner()
    initial = actual.state(include_replay=False)
    warmup(actual)
    records = [mission(actual, 16, blocks=2, partial=7), mission(actual, 17, blocks=2, partial=11)]
    replay = learner()
    replay.load_state(initial)
    warmup(replay)
    # Replay chronological inputs alone. Expected actions/targets are never used
    # as learner inputs; each new boundary follows its preceding reward ticks.
    for index, expected in enumerate(records, 16):
        replay.start_episode(index, True)
        actions = dict(zip(expected["action_step"], range(len(expected["action_step"]))))
        for tick, reward, terminal in zip(expected["reward_step"], expected["reward_native_J"], expected["reward_terminal"]):
            if tick in actions:
                row = actions[tick]
                replay.decide(expected["action_features"][row], bool(expected["action_h_eligible"][row]), int(tick))
            replay.observe_reward(float(reward), bool(terminal))
        assert_arrays_equal(expected, replay.episode_arrays())
    assert actual.digests() == replay.digests()
    assert actual.counts() == replay.counts()
    assert actual.updates == 4  # 8 real steps across actual + reconstruction.


def test_full_checkpoint_preserves_pending_accumulation_rng_and_optimizer():
    actual = learner()
    warmup(actual)
    actual.start_episode(16, True)
    actual.decide(features(), True, 0)
    actual.observe_reward(.1, False)
    saved = actual.state()
    clone = learner()
    clone.load_state(saved)
    for agent in (actual, clone):
        agent.observe_reward(.2, True)  # One step per copy.
    assert_arrays_equal(actual.episode_arrays(), clone.episode_arrays())
    assert actual.digests() == clone.digests()
    assert saved["counts"]["updates"] == 0  # Snapshot is not aliased.
    assert saved["pending"]["rewards"] == [.1]


def test_malformed_boundaries_unfinished_reset_and_horizon_rejected():
    agent = learner()
    with pytest.raises(ValueError):
        agent.start_episode(1, True)
    agent.start_episode(0, True)
    with pytest.raises(ValueError):
        agent.decide(np.full(327, np.nan), True, 0)
    with pytest.raises(ValueError):
        agent.decide(features(), True, 30)
    agent.decide(features(), True, 0)
    with pytest.raises(RuntimeError):
        agent.start_episode(1, True)
    with pytest.raises(RuntimeError):
        agent.state(include_replay=False)
    with pytest.raises(RuntimeError):
        agent.decide(features(), True, 0)
    with pytest.raises(ValueError):
        agent.observe_reward(float("inf"), False)
    # Clock-only fixture: H3000 requires the supplied terminal flag.
    agent.pending["step"] = 2970
    agent.pending["rewards"] = [0.] * 29
    with pytest.raises(ValueError, match="H3000"):
        agent.observe_reward(0., False)
    agent.observe_reward(0., True)
    assert agent.episode_arrays()["transition_end_step"].tolist() == [3000]
