"""Masked service/member/duration law with explicit semantic deployment."""

from __future__ import annotations

import gymnasium as gym
import numpy as np
from stable_baselines3.common.distributions import CategoricalDistribution
from stable_baselines3.common.policies import ActorCriticPolicy
import torch
from torch import nn
from torch.distributions import Bernoulli, Categorical
from torch.nn import functional as F

from .constants import N_ACTIONS


class CommitmentDistribution(CategoricalDistribution):
    def proba_distribution_net(self, latent_dim):
        return nn.Linear(latent_dim, 1 + 8 + 24)

    def proba_distribution(self, action_logits, member_mask=None):
        if member_mask is None or action_logits.shape[1] != 33:
            raise ValueError("commitment distribution requires logits and the current mask")
        self.gate_logits = action_logits[:, 0]
        self.has_choice = member_mask.bool().any(dim=1)
        safe = member_mask.bool().clone()
        safe[~self.has_choice, 0] = True
        self.member_logits = action_logits[:, 1:9].masked_fill(~safe, -torch.inf)
        self.duration_logits = action_logits[:, 9:].reshape(-1, 8, 3)
        member_logp = F.log_softmax(self.member_logits, dim=1)
        duration_logp = F.log_softmax(self.duration_logits, dim=2)
        service_logp = torch.where(self.has_choice, F.logsigmoid(self.gate_logits), 0.0)
        dispatch_logp = torch.where(self.has_choice, F.logsigmoid(-self.gate_logits), -torch.inf)
        joint = dispatch_logp[:, None, None] + member_logp[:, :, None] + duration_logp
        self.distribution = Categorical(logits=torch.cat((service_logp[:, None], joint.flatten(1)), dim=1))
        return self

    def mode(self):
        member = torch.argmax(self.member_logits, dim=1)
        duration = torch.argmax(self.duration_logits[torch.arange(len(member)), member], dim=1)
        dispatch = self.has_choice & (self.gate_logits < 0)
        return torch.where(dispatch, 1 + member * 3 + duration, 0)

    def statistics(self):
        members = Categorical(logits=self.member_logits)
        durations = Categorical(logits=self.duration_logits)
        return {
            "service_probability": torch.where(self.has_choice, torch.sigmoid(self.gate_logits), 1.0),
            "gate_entropy": torch.where(self.has_choice, Bernoulli(logits=self.gate_logits).entropy(), 0.0),
            "member_entropy": torch.where(self.has_choice, members.entropy(), 0.0),
            "duration_entropy": torch.where(self.has_choice,
                                            (members.probs * durations.entropy()).sum(dim=1), 0.0),
            "joint_entropy": self.entropy(),
        }


class CommitmentPolicy(ActorCriticPolicy):
    def _build(self, lr_schedule):
        if not isinstance(self.action_space, gym.spaces.Discrete) or self.action_space.n != N_ACTIONS:
            raise ValueError("policy requires service plus eight members times three durations")
        if not self.share_features_extractor:
            raise ValueError("this fixed policy uses one identity feature extractor")
        self.action_dist = CommitmentDistribution(N_ACTIONS)
        super()._build(lr_schedule)
        with torch.no_grad():
            self.action_net.weight.zero_()
            self.action_net.bias.zero_()

    def _distribution(self, latent_pi, obs):
        return self.action_dist.proba_distribution(self.action_net(latent_pi), obs[:, :8] > .5)

    def forward(self, obs, deterministic=False):
        features = self.extract_features(obs)
        latent_pi, latent_vf = self.mlp_extractor(features)
        distribution = self._distribution(latent_pi, obs)
        actions = distribution.get_actions(deterministic=deterministic)
        return actions.reshape((-1, *self.action_space.shape)), self.value_net(latent_vf), distribution.log_prob(actions)

    def get_distribution(self, obs):
        features = self.extract_features(obs, self.pi_features_extractor)
        return self._distribution(self.mlp_extractor.forward_actor(features), obs)

    def evaluate_actions(self, obs, actions):
        features = self.extract_features(obs)
        latent_pi, latent_vf = self.mlp_extractor(features)
        distribution = self._distribution(latent_pi, obs)
        return self.value_net(latent_vf), distribution.log_prob(actions), distribution.entropy()


def policy_statistics(model, features, action=None):
    observation, _ = model.policy.obs_to_tensor(np.asarray(features, dtype=np.float32))
    with torch.no_grad():
        distribution = model.policy.get_distribution(observation)
        selected = distribution.mode() if action is None else torch.as_tensor([action], device=observation.device)
        result = {key: float(value.item()) for key, value in distribution.statistics().items()}
        result["selected_joint_probability"] = float(torch.exp(distribution.log_prob(selected)).item())
        result["probabilities"] = distribution.distribution.probs[0].cpu().tolist()
        return result
