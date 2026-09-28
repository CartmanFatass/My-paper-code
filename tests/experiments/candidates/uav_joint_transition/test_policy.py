from __future__ import annotations

import gymnasium as gym
import numpy as np
import pytest
import torch
from stable_baselines3 import PPO

from experiments.candidates.uav_joint_transition.policy import PathDistribution, PathPolicy
from experiments.candidates.uav_joint_transition.controllers import FEATURE_DIM


class FeatureFixture(gym.Env):
    observation_space = gym.spaces.Box(-np.inf, np.inf, (FEATURE_DIM,), dtype=np.float32)
    action_space = gym.spaces.MultiDiscrete(np.full(8, 4))


def test_masked_distribution_probability_entropy_and_gradients():
    logits = torch.randn(3, 32, requires_grad=True)
    eligible = torch.tensor([[1]*8, [1, 0]*4, [0]*8], dtype=torch.bool)
    dist = PathDistribution([4]*8).proba_distribution(logits, eligible)
    action = dist.sample()
    assert torch.all(action[~eligible] == 0)
    stats = dist.statistics()
    torch.testing.assert_close(stats["probabilities"].sum(2), torch.ones(3, 8))
    assert stats["non_direct_probability"][-1] == 0
    assert stats["joint_entropy"][-1] == 0
    expected = stats["probabilities"].gather(2, action[..., None]).squeeze(2).log().sum(1)
    torch.testing.assert_close(dist.log_prob(action), expected)
    (-dist.log_prob(action).mean() - .01*dist.entropy().mean()).backward()
    assert torch.isfinite(logits.grad).all()
    assert torch.count_nonzero(logits.grad.reshape(3, 8, 4)[~eligible]) == 0


def test_initial_exact_D_probabilities_save_load_and_update(tmp_path):
    torch.set_num_threads(1)
    model = PPO(PathPolicy, FeatureFixture(), n_steps=4, batch_size=4, seed=62999901,
                policy_kwargs={"net_arch": {"pi": [128, 128], "vf": [128, 128]},
                               "activation_fn": torch.nn.Tanh})
    features = torch.linspace(-1, 1, 3*FEATURE_DIM).reshape(3, FEATURE_DIM)
    features[:, :8] = torch.tensor([[1]*8, [1, 0]*4, [0]*8])
    dist = model.policy.get_distribution(features)
    assert torch.all(dist.mode() == 0)
    stats = dist.statistics()
    torch.testing.assert_close(stats["probabilities"][0], torch.tensor([[.8, 1/15, 1/15, 1/15]]*8))
    assert float(stats["non_direct_probability"][0]) == pytest.approx(1-.8**8, abs=1e-6)
    action = torch.tensor([[0, 1, 2, 3, 0, 1, 2, 3], [1, 0, 2, 0, 3, 0, 1, 0], [0]*8])
    values, log_prob, entropy = model.policy.evaluate_actions(features, action)
    torch.testing.assert_close(log_prob, dist.log_prob(action))
    loss = -log_prob.mean() + values.square().mean() - .01*entropy.mean()
    model.policy.optimizer.zero_grad()
    loss.backward()
    assert torch.isfinite(model.policy.action_net.weight.grad).all()
    assert torch.count_nonzero(model.policy.action_net.weight.grad) > 0
    model.policy.optimizer.step()
    before, _ = model.predict(features.numpy(), deterministic=True)
    model.save(tmp_path/"policy.zip")
    restored = PPO.load(tmp_path/"policy.zip", device="cpu")
    after, _ = restored.predict(features.numpy(), deterministic=True)
    np.testing.assert_array_equal(before, after)
    torch.testing.assert_close(restored.policy.get_distribution(features).statistics()["probabilities"],
                               model.policy.get_distribution(features).statistics()["probabilities"])
