"""Environment-neutral continuous recurrent policy for variable rosters.

The policy owns only anonymous active-set aggregation, lifecycle-row recurrent
state, normalized autoregressive action prefixes and tanh-Gaussian sampling.
Environment observations, rewards, ledgers and result semantics remain in the
calling experiment.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import torch
from torch import nn


@dataclass
class ContinuousStepOutput:
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    token_log_probs: torch.Tensor
    token_entropies: torch.Tensor
    value: torch.Tensor
    next_hidden: torch.Tensor
    prefix_action_sums: torch.Tensor
    likelihood_mask: torch.Tensor


class ContinuousRosterPolicy(nn.Module):
    """Capacity-generic tanh-Gaussian actor with active-fraction prefixes."""

    def __init__(
        self,
        observation_dim: int,
        critic_state_dim: int,
        *,
        member_capacity: int,
        action_dim: int,
        hidden_dim: int = 64,
        current_observation_residual: bool = False,
    ) -> None:
        super().__init__()
        self.observation_dim = int(observation_dim)
        self.critic_state_dim = int(critic_state_dim)
        self.member_capacity = int(member_capacity)
        self.action_dim = int(action_dim)
        self.hidden_dim = int(hidden_dim)
        if min(
            self.observation_dim,
            self.critic_state_dim,
            self.member_capacity,
            self.action_dim,
            self.hidden_dim,
        ) <= 0:
            raise ValueError("continuous roster dimensions must be positive")
        if self.observation_dim < 3:
            raise ValueError("continuous roster routing requires three observation fields")

        self.member_encoder = nn.Sequential(
            nn.Linear(self.observation_dim, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.Tanh(),
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(self.hidden_dim + 1, self.hidden_dim), nn.Tanh()
        )
        self.actor_rnn = nn.GRUCell(
            2 * self.hidden_dim + self.action_dim, self.hidden_dim
        )
        self.action_mean = nn.Sequential(
            nn.Linear(self.hidden_dim + self.action_dim, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, self.action_dim),
        )
        self.current_observation_residual = (
            nn.Linear(self.observation_dim, self.action_dim)
            if current_observation_residual
            else None
        )
        self.log_std = nn.Parameter(torch.zeros(self.action_dim))
        self.critic = nn.Sequential(
            nn.Linear(
                self.hidden_dim
                + 1
                + self.critic_state_dim
                + self.member_capacity,
                self.hidden_dim,
            ),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, 1),
        )

    @property
    def parameter_count(self) -> int:
        return int(sum(parameter.numel() for parameter in self.parameters()))

    def _action_mean_for_member(
        self,
        *,
        candidate: torch.Tensor,
        prefix_fraction: torch.Tensor,
        observation: torch.Tensor,
    ) -> torch.Tensor:
        """Return one routed member's pre-squash action mean.

        The hook keeps the base policy behavior unchanged while allowing an
        active research policy to add a source-neutral mean residual without
        copying the autoregressive routing loop.
        """

        mean = self.action_mean(
            torch.cat((candidate, prefix_fraction), dim=-1)
        )
        if self.current_observation_residual is not None:
            mean = mean + self.current_observation_residual(observation)
        return mean

    def _step_action_mean_residuals(
        self,
        *,
        encoded: torch.Tensor,
        context: torch.Tensor,
        observations: torch.Tensor,
        active_mask: torch.Tensor,
        hidden: torch.Tensor,
    ) -> torch.Tensor | None:
        """Optionally provide one precomputed mean residual per member."""

        return None

    def _routing_order(
        self, active_mask: torch.Tensor, observations: torch.Tensor
    ) -> torch.Tensor:
        # The order is a deterministic function of current anonymous content.
        # It never reads the lifecycle storage row.
        priority = (
            observations[:, :, 0]
            + math.sqrt(2.0) * observations[:, :, 1]
            + math.sqrt(3.0) * observations[:, :, 2]
        )
        priority = torch.where(
            active_mask, priority, torch.full_like(priority, float("inf"))
        )
        return torch.argsort(priority, dim=1, stable=True)

    def forward_step(
        self,
        *,
        observations: torch.Tensor,
        active_mask: torch.Tensor,
        critic_state: torch.Tensor,
        hidden: torch.Tensor,
        sampling_noise: torch.Tensor | None = None,
        teacher_pre_tanh: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> ContinuousStepOutput:
        expected_observation_shape = (
            self.member_capacity,
            self.observation_dim,
        )
        if observations.ndim != 3 or observations.shape[1:] != expected_observation_shape:
            raise ValueError("continuous roster actor observation shape mismatch")
        batch = observations.shape[0]
        if active_mask.shape != (batch, self.member_capacity) or active_mask.dtype != torch.bool:
            raise ValueError("continuous roster active mask shape/dtype mismatch")
        if critic_state.shape != (batch, self.critic_state_dim):
            raise ValueError("continuous roster critic state shape mismatch")
        if hidden.shape != (batch, self.member_capacity, self.hidden_dim):
            raise ValueError("continuous roster hidden shape mismatch")
        modes = (
            int(sampling_noise is not None)
            + int(teacher_pre_tanh is not None)
            + int(deterministic)
        )
        if modes != 1:
            raise ValueError("choose exactly one sampling, replay, or deterministic mode")
        expected_action_shape = (batch, self.member_capacity, self.action_dim)
        if sampling_noise is not None and sampling_noise.shape != expected_action_shape:
            raise ValueError("continuous roster sampling-noise shape mismatch")
        if teacher_pre_tanh is not None and teacher_pre_tanh.shape != expected_action_shape:
            raise ValueError("continuous roster teacher-latent shape mismatch")

        active_count = active_mask.sum(dim=1)
        if bool((active_count <= 0).any()):
            raise ValueError("continuous roster policy requires an active lifecycle")
        dtype = observations.dtype
        batch_index = torch.arange(batch, device=observations.device)

        # Encode the active set exactly once per environment step.  The causal
        # autoregressive loop below changes only the prefix and focal state.
        encoded = self.member_encoder(observations)
        member_sum = (encoded * active_mask.to(dtype).unsqueeze(-1)).sum(dim=1)
        count_coordinate = torch.log1p(active_count.to(dtype)).unsqueeze(-1)
        context_input = torch.cat((member_sum, count_coordinate), dim=-1)
        context = self.context_encoder(context_input)
        step_mean_residuals = self._step_action_mean_residuals(
            encoded=encoded,
            context=context,
            observations=observations,
            active_mask=active_mask,
            hidden=hidden,
        )
        if step_mean_residuals is not None:
            if (
                step_mean_residuals.shape
                != (batch, self.member_capacity, self.action_dim)
                or not bool(torch.isfinite(step_mean_residuals).all())
            ):
                raise ValueError("continuous roster mean residual shape/finite mismatch")
            if int(
                torch.count_nonzero(
                    torch.where(
                        active_mask.unsqueeze(-1),
                        torch.zeros_like(step_mean_residuals),
                        step_mean_residuals,
                    )
                )
            ) != 0:
                raise ValueError("continuous roster inactive mean residual must be zero")
        value = self.critic(
            torch.cat((context_input, critic_state, active_mask.to(dtype)), dim=-1)
        ).squeeze(-1)

        order = self._routing_order(active_mask, observations)
        positions = torch.arange(
            self.member_capacity, device=observations.device
        ).unsqueeze(0)
        valid_positions = positions < active_count.unsqueeze(1)
        next_hidden = hidden.clone()
        actions = torch.zeros(expected_action_shape, dtype=dtype, device=observations.device)
        pre_tanh_actions = torch.zeros_like(actions)
        log_probs = torch.zeros(
            (batch, self.member_capacity), dtype=dtype, device=observations.device
        )
        entropies = torch.zeros_like(log_probs)
        prefix_rows = torch.zeros_like(actions)
        prefix_sum = torch.zeros(
            (batch, self.action_dim), dtype=dtype, device=observations.device
        )
        denominator = active_count.to(dtype).unsqueeze(-1)
        log_std = self.log_std.clamp(-5.0, 2.0)
        std = torch.exp(log_std)

        for position in range(self.member_capacity):
            valid = valid_positions[:, position]
            if not bool(valid.any()):
                break
            owner = order[:, position]
            prefix_fraction = prefix_sum / denominator
            candidate = self.actor_rnn(
                torch.cat(
                    (
                        encoded[batch_index, owner],
                        context,
                        prefix_fraction,
                    ),
                    dim=-1,
                ),
                next_hidden[batch_index, owner],
            )
            mean = self._action_mean_for_member(
                candidate=candidate,
                prefix_fraction=prefix_fraction,
                observation=observations[batch_index, owner],
            )
            if step_mean_residuals is not None:
                mean = mean + step_mean_residuals[batch_index, owner]
            distribution = torch.distributions.Normal(mean, std.expand_as(mean))
            if teacher_pre_tanh is not None:
                raw = teacher_pre_tanh[batch_index, owner]
                chosen = torch.tanh(raw)
            elif deterministic:
                raw = mean
                chosen = torch.tanh(raw)
            else:
                assert sampling_noise is not None
                raw = mean + std * sampling_noise[batch_index, owner]
                chosen = torch.tanh(raw)
            log_jacobian = 2.0 * (
                math.log(2.0) - raw - torch.nn.functional.softplus(-2.0 * raw)
            )
            chosen_logp = (distribution.log_prob(raw) - log_jacobian).sum(dim=-1)
            entropy = distribution.entropy().sum(dim=-1)
            valid_batch = batch_index[valid]
            valid_owner = owner[valid]
            next_hidden[valid_batch, valid_owner] = candidate[valid]
            actions[valid_batch, valid_owner] = chosen[valid]
            pre_tanh_actions[valid_batch, valid_owner] = raw[valid]
            log_probs[valid_batch, valid_owner] = chosen_logp[valid]
            entropies[valid_batch, valid_owner] = entropy[valid]
            prefix_rows[:, position] = prefix_sum
            prefix_sum = prefix_sum + torch.where(
                valid.unsqueeze(-1), chosen, torch.zeros_like(chosen)
            )

        return ContinuousStepOutput(
            actions=actions,
            pre_tanh_actions=pre_tanh_actions,
            token_log_probs=log_probs,
            token_entropies=entropies,
            value=value,
            next_hidden=next_hidden,
            prefix_action_sums=prefix_rows,
            likelihood_mask=active_mask,
        )
