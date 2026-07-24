"""Prefix-contextual frozen-anchor residual representation for G26."""

from __future__ import annotations

from typing import Any

import torch
from torch import nn

from ha_ctse_process.anchored_residual_g19 import FastAnchoredResidualPolicy
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy


class PrefixContextualResidualContinuousRosterPolicy(ContinuousRosterPolicy):
    """Add one routed residual from direct set context and the live prefix."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.delayed_residual = nn.Sequential(
            nn.Linear(
                3 * self.hidden_dim
                + self.action_dim
                + self.observation_dim,
                self.hidden_dim,
            ),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, self.action_dim),
        )
        final = self.delayed_residual[-1]
        assert isinstance(final, nn.Linear)
        nn.init.zeros_(final.weight)
        nn.init.zeros_(final.bias)
        for parameter in self.delayed_residual.parameters():
            parameter.requires_grad_(False)

    def residual_proposal(
        self,
        *,
        encoded_member: torch.Tensor,
        context: torch.Tensor,
        hidden: torch.Tensor,
        prefix_fraction: torch.Tensor,
        observation: torch.Tensor,
    ) -> torch.Tensor:
        features = torch.cat(
            (
                encoded_member.detach(),
                context.detach(),
                hidden.detach(),
                prefix_fraction.detach(),
                observation.detach(),
            ),
            dim=-1,
        )
        return self.delayed_residual(features)

    def _action_mean_for_member(
        self,
        *,
        candidate: torch.Tensor,
        prefix_fraction: torch.Tensor,
        observation: torch.Tensor,
        encoded_member: torch.Tensor,
        context: torch.Tensor,
        hidden: torch.Tensor,
    ) -> torch.Tensor:
        anchor = super()._action_mean_for_member(
            candidate=candidate,
            prefix_fraction=prefix_fraction,
            observation=observation,
            encoded_member=encoded_member,
            context=context,
            hidden=hidden,
        )
        return anchor + self.residual_proposal(
            encoded_member=encoded_member,
            context=context,
            hidden=hidden,
            prefix_fraction=prefix_fraction,
            observation=observation,
        )


class PrefixContextualResidualPolicy(FastAnchoredResidualPolicy):
    """Frozen fast actor plus the G26 routed prefix-contextual head."""

    def __init__(
        self,
        observation_dim: int,
        critic_state_dim: int,
        *,
        member_capacity: int,
        action_dim: int,
        hidden_dim: int = 32,
        current_observation_residual: bool = True,
    ) -> None:
        super().__init__(
            observation_dim,
            critic_state_dim,
            member_capacity=member_capacity,
            action_dim=action_dim,
            hidden_dim=hidden_dim,
            current_observation_residual=current_observation_residual,
            policy_type=PrefixContextualResidualContinuousRosterPolicy,
        )
