"""SB3 policy with a service gate and a conditional scout-target distribution."""

from __future__ import annotations

import gymnasium as gym
import numpy as np
from stable_baselines3.common.distributions import CategoricalDistribution
from stable_baselines3.common.policies import ActorCriticPolicy
import torch
from torch.distributions import Bernoulli, Categorical
from torch.nn import functional as F


class SemanticDistribution(CategoricalDistribution):
    """The sampled law is joint; deterministic deployment uses staged modes."""

    def proba_distribution(self, action_logits):
        self.gate_logits = action_logits[:, 0]
        self.target_logits = action_logits[:, 1:]
        log_probabilities = torch.cat((
            F.logsigmoid(self.gate_logits[:, None]),
            F.logsigmoid(-self.gate_logits[:, None]) + F.log_softmax(self.target_logits, dim=1),
        ), dim=1)
        self.distribution = Categorical(logits=log_probabilities)
        return self

    def mode(self):
        # Test the raw gate so normalization roundoff cannot change the exact zero tie.
        return torch.where(self.gate_logits >= 0, 0, torch.argmax(self.target_logits, dim=1) + 1)

    def statistics(self):
        return {
            "service_probability": torch.sigmoid(self.gate_logits),
            "gate_entropy": Bernoulli(logits=self.gate_logits).entropy(),
            "target_entropy": Categorical(logits=self.target_logits).entropy(),
            "joint_entropy": self.entropy(),
        }


class SemanticPolicy(ActorCriticPolicy):
    def _build(self, lr_schedule):
        if not isinstance(self.action_space, gym.spaces.Discrete) or self.action_space.n != 257:
            raise ValueError("the sensing policy requires service plus 256 targets")
        self.action_dist = SemanticDistribution(self.action_space.n)
        super()._build(lr_schedule)
        with torch.no_grad():
            self.action_net.weight[0].zero_()
            self.action_net.bias[0].zero_()


def policy_statistics(model, features):
    observation, _ = model.policy.obs_to_tensor(np.asarray(features, dtype=np.float32))
    with torch.no_grad():
        distribution = model.policy.get_distribution(observation)
        action = distribution.mode()
        result = {key: float(value.item()) for key, value in distribution.statistics().items()}
        result["selected_joint_probability"] = float(torch.exp(distribution.log_prob(action)).item())
        result["selected_conditional_target_probability"] = (
            float(torch.softmax(distribution.target_logits, dim=1)[0, int(action.item()) - 1])
            if action.item() else None)
        return result
