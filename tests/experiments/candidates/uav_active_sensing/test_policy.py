from __future__ import annotations

import gymnasium as gym
import numpy as np
import pytest
import torch
from stable_baselines3 import PPO
from torch.distributions import Bernoulli, Categorical

from experiments.candidates.uav_active_sensing.policy import SemanticDistribution, SemanticPolicy, policy_statistics


def test_joint_probability_log_probability_and_semantic_mode():
    logits = torch.zeros((3, 257), dtype=torch.float64, requires_grad=True)
    with torch.no_grad():
        logits[:, 0] = torch.tensor([0.0, -0.04, 3.0])
        logits[:, 8] = .2
    dist = SemanticDistribution(257).proba_distribution(logits)
    service = torch.sigmoid(logits[:, 0])
    targets = torch.softmax(logits[:, 1:], dim=1)
    expected = torch.cat((service[:, None], (1-service[:, None]) * targets), dim=1)
    torch.testing.assert_close(dist.distribution.probs, expected)
    actions = torch.tensor([0, 8, 200])
    torch.testing.assert_close(dist.log_prob(actions), torch.log(expected[torch.arange(3), actions]))
    assert dist.mode().tolist() == [0, 8, 0]
    assert torch.argmax(expected[1]).item() == 0  # Staged mode is deliberately different.
    expected_entropy = Bernoulli(probs=service).entropy() + (1-service) * Categorical(probs=targets).entropy()
    torch.testing.assert_close(dist.entropy(), expected_entropy)
    (-dist.log_prob(actions).mean()).backward()
    assert torch.isfinite(logits.grad).all()
    assert logits.grad[0, 1:].abs().max() < 1e-14
    assert logits.grad[1, 1:].abs().max() > 0


def test_finite_extreme_gates_and_sampling_mass():
    logits = torch.zeros((3, 257), dtype=torch.float32)
    logits[:, 0] = torch.tensor([-80.0, 0.0, 80.0])
    dist = SemanticDistribution(257).proba_distribution(logits)
    assert torch.isfinite(dist.log_prob(torch.tensor([0, 30, 256]))).all()
    assert torch.isfinite(dist.entropy()).all()
    torch.testing.assert_close(dist.distribution.probs.sum(1), torch.ones(3))
    torch.manual_seed(28179901)
    balanced = SemanticDistribution(257).proba_distribution(torch.zeros((20000, 257)))
    actions = balanced.sample()
    assert .48 < (actions == 0).float().mean() < .52
    assert len(torch.unique(actions[actions > 0])) == 256


class FeatureFixture(gym.Env):
    observation_space = gym.spaces.Box(-1, 1, shape=(11,), dtype=np.float32)
    action_space = gym.spaces.Discrete(257)


def test_initial_service_alias_save_load_and_policy_gradients(tmp_path):
    torch.set_num_threads(1)
    model = PPO(SemanticPolicy, FeatureFixture(), seed=28179902, n_steps=4, batch_size=4,
                policy_kwargs={"net_arch": {"pi": [16], "vf": [16]}})
    features = torch.linspace(-1, 1, 77).reshape(7, 11)
    dist = model.policy.get_distribution(features)
    assert torch.equal(dist.statistics()["service_probability"], torch.full((7,), .5))
    assert dist.mode().tolist() == [0] * 7
    first = policy_statistics(model, features[0].numpy())
    assert first["selected_joint_probability"] == pytest.approx(.5, abs=1e-7)
    assert first["selected_conditional_target_probability"] is None
    action = torch.tensor([0, 1, 2, 0, 256, 4, 0])
    _, actual, _ = model.policy.evaluate_actions(features, action)
    torch.testing.assert_close(actual, dist.log_prob(action))
    (-actual.mean()).backward()
    assert torch.isfinite(model.policy.action_net.weight.grad).all()
    assert model.policy.action_net.weight.grad[0].abs().max() > 0
    assert model.policy.action_net.weight.grad[1:].abs().max() > 0
    with torch.no_grad():
        model.policy.action_net.bias[0].fill_(-.04)
        model.policy.action_net.bias[19].fill_(.9)
    before, _ = model.predict(features.numpy(), deterministic=True)
    assert before.tolist() == [19] * 7
    chosen = policy_statistics(model, features[0].numpy())
    assert chosen["selected_conditional_target_probability"] > 1/256
    assert chosen["selected_joint_probability"] == pytest.approx(
        (1-chosen["service_probability"]) * chosen["selected_conditional_target_probability"], abs=1e-7)
    model.save(tmp_path / "staged.zip")
    loaded = PPO.load(tmp_path / "staged.zip", device="cpu")
    after, _ = loaded.predict(features.numpy(), deterministic=True)
    np.testing.assert_array_equal(before, after)
    torch.testing.assert_close(loaded.policy.get_distribution(features).distribution.probs,
                               model.policy.get_distribution(features).distribution.probs)


def test_policy_refuses_different_action_contract():
    with pytest.raises(ValueError, match="256 targets"):
        SemanticPolicy(gym.spaces.Box(-1, 1, shape=(3,)), gym.spaces.Discrete(2), lambda _: .001)
