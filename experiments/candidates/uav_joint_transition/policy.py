"""Central factored path policy with forced-D rows and exact all-D initialization."""

from __future__ import annotations

import numpy as np
from stable_baselines3.common.distributions import MultiCategoricalDistribution
from stable_baselines3.common.policies import ActorCriticPolicy
import torch


class PathDistribution(MultiCategoricalDistribution):
    def proba_distribution(self, action_logits, eligible=None):
        if eligible is None or action_logits.shape[1] != 32 or eligible.shape[1] != 8:
            raise ValueError("path distribution requires 32 logits and eight eligibility flags")
        logits = action_logits.reshape(-1, 8, 4)
        forced = ~eligible.bool()
        direct = torch.where(forced, torch.zeros_like(logits[:, :, 0]), logits[:, :, 0])
        alternate = logits[:, :, 1:].masked_fill(forced[:, :, None], -torch.inf)
        return super().proba_distribution(torch.cat((direct[:, :, None], alternate), dim=2).flatten(1))

    def statistics(self):
        probabilities = torch.stack([row.probs for row in self.distribution], dim=1)
        return {"probabilities": probabilities,
                "non_direct_probability": 1 - probabilities[:, :, 0].prod(dim=1),
                "joint_entropy": self.entropy()}


class PathPolicy(ActorCriticPolicy):
    def _build(self, lr_schedule):
        if not np.array_equal(self.action_space.nvec, np.full(8, 4)):
            raise ValueError("path policy requires eight four-way choices")
        self.action_dist = PathDistribution([4] * 8)
        super()._build(lr_schedule)
        with torch.no_grad():
            self.action_net.weight.zero_()
            self.action_net.bias.copy_(torch.as_tensor(np.tile(np.log([.8, 1/15, 1/15, 1/15]), 8),
                                                       dtype=self.action_net.bias.dtype))

    def _distribution(self, latent_pi, obs):
        return self.action_dist.proba_distribution(self.action_net(latent_pi), obs[:, :8] > .5)

    def forward(self, obs, deterministic=False):
        latent_pi, latent_vf = self.mlp_extractor(self.extract_features(obs))
        distribution = self._distribution(latent_pi, obs)
        actions = distribution.get_actions(deterministic=deterministic)
        return actions, self.value_net(latent_vf), distribution.log_prob(actions)

    def get_distribution(self, obs):
        features = self.extract_features(obs, self.pi_features_extractor)
        return self._distribution(self.mlp_extractor.forward_actor(features), obs)

    def evaluate_actions(self, obs, actions):
        latent_pi, latent_vf = self.mlp_extractor(self.extract_features(obs))
        distribution = self._distribution(latent_pi, obs)
        return self.value_net(latent_vf), distribution.log_prob(actions), distribution.entropy()
