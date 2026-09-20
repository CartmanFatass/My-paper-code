"""Whole-mask J/I policies and PPO utilities for team-conditioned termination.

The policy owns only optional END decisions.  Mandatory END bits are supplied by
the caller, participate in the joint policy's realized prefix, and are excluded
from actor likelihoods.  The value function is deliberately a separate,
context-only module.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Callable
from typing import Literal

import torch
from torch import nn
from torch.nn import functional as F


PolicyMode = Literal["joint", "independent"]


def _require_positive_int(name: str, value: int) -> int:
    value = int(value)
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _seeded_build(seed: int, build: Callable[[], nn.Module]) -> nn.Module:
    """Build a module reproducibly without advancing PyTorch's global RNG."""

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(seed))
        return build()


@dataclass(frozen=True)
class MaskEvaluation:
    log_prob: torch.Tensor
    entropy: torch.Tensor
    logits: torch.Tensor
    bit_log_prob: torch.Tensor
    bit_entropy: torch.Tensor


@dataclass(frozen=True)
class MaskSample:
    actions: torch.Tensor
    log_prob: torch.Tensor
    entropy: torch.Tensor
    logits: torch.Tensor


class _MaskActor(nn.Module):
    def __init__(self, input_dim: int, hidden_size: int, initial_logit: float) -> None:
        super().__init__()
        self.body = nn.Sequential(
            nn.Linear(input_dim, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
        )
        self.logit_head = nn.Linear(hidden_size, 1)
        nn.init.zeros_(self.logit_head.weight)
        nn.init.zeros_(self.logit_head.bias)
        self.register_buffer("initial_logit", torch.tensor(float(initial_logit)))

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.logit_head(self.body(features)).squeeze(-1) + self.initial_logit


class MaskPolicy(nn.Module):
    """Canonical-order binary mask policy.

    ``joint`` conditions each bit on the already realized mask prefix.  The
    otherwise identical ``independent`` policy replaces that prefix with zeros.
    Context and masks are batched as ``[batch, context_dim]`` and
    ``[batch, n_agents]`` respectively.
    """

    def __init__(
        self,
        context_dim: int,
        n_agents: int,
        mode: PolicyMode,
        hidden_size: int = 128,
        seed: int = 0,
        end_probability: float = 0.1,
    ) -> None:
        super().__init__()
        self.context_dim = _require_positive_int("context_dim", context_dim)
        self.n_agents = _require_positive_int("n_agents", n_agents)
        self.hidden_size = _require_positive_int("hidden_size", hidden_size)
        if mode not in ("joint", "independent"):
            raise ValueError("mode must be 'joint' or 'independent'")
        self.mode: PolicyMode = mode
        if not math.isfinite(end_probability) or not 0.0 < end_probability < 1.0:
            raise ValueError("end_probability must be finite and strictly between zero and one")
        initial_logit = math.log(end_probability / (1.0 - end_probability))
        input_dim = self.context_dim + 2 * self.n_agents
        self.actor = _seeded_build(
            seed,
            lambda: _MaskActor(input_dim, self.hidden_size, initial_logit),
        )
        self._sample_seed = int(seed)
        self._sample_generators: dict[str, torch.Generator] = {}

    def _generator_for(self, device: torch.device) -> torch.Generator:
        key = str(device)
        generator = self._sample_generators.get(key)
        if generator is None:
            generator = torch.Generator(device=device)
            generator.manual_seed(self._sample_seed)
            self._sample_generators[key] = generator
        return generator

    def _validate_inputs(
        self,
        context: torch.Tensor,
        eligible: torch.Tensor,
        forced_end: torch.Tensor,
        actions: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if context.ndim != 2 or context.shape[1] != self.context_dim:
            raise ValueError(
                f"context must have shape [batch, {self.context_dim}], got {tuple(context.shape)}"
            )
        if not context.is_floating_point():
            raise TypeError("context must be a floating-point tensor")
        if not bool(torch.isfinite(context).all()):
            raise ValueError("context must be finite")
        expected = (context.shape[0], self.n_agents)
        if eligible.shape != expected or forced_end.shape != expected:
            raise ValueError(f"eligible and forced_end must have shape {expected}")
        if eligible.dtype is not torch.bool or forced_end.dtype is not torch.bool:
            raise TypeError("eligible and forced_end must be bool tensors")
        if eligible.device != context.device or forced_end.device != context.device:
            raise ValueError("context and masks must be on the same device")
        if bool(torch.any(eligible & forced_end)):
            raise ValueError("forced END bits cannot also be actor-eligible")
        if actions is not None:
            if actions.shape != expected or actions.dtype is not torch.bool:
                raise TypeError(f"actions must be a bool tensor with shape {expected}")
            if actions.device != context.device:
                raise ValueError("context and actions must be on the same device")
            fixed = ~eligible
            if bool(torch.any(actions[fixed] != forced_end[fixed])):
                raise ValueError("actions must equal forced values outside eligibility")
        return eligible, forced_end

    def _agent_logits(
        self, context: torch.Tensor, realized_actions: torch.Tensor, agent: int
    ) -> torch.Tensor:
        identity = F.one_hot(
            torch.full(
                (context.shape[0],), agent, dtype=torch.long, device=context.device
            ),
            num_classes=self.n_agents,
        ).to(dtype=context.dtype)
        prefix = torch.zeros_like(realized_actions, dtype=context.dtype)
        if self.mode == "joint" and agent:
            prefix[:, :agent] = realized_actions[:, :agent].to(dtype=context.dtype)
        features = torch.cat((context, identity, prefix), dim=-1)
        return self.actor(features)

    @staticmethod
    def _bit_terms(
        logits: torch.Tensor, actions: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        log_prob = torch.where(
            actions,
            -F.softplus(-logits),
            -F.softplus(logits),
        )
        # This symmetric form remains finite for very large finite logits.  The
        # clamp also makes diagnostic entropy safe if a masked logit overflows.
        magnitude = logits.abs().clamp_max(80.0)
        entropy = F.softplus(-magnitude) + magnitude * torch.sigmoid(-magnitude)
        return log_prob, entropy

    @classmethod
    def _eligible_bit_terms(
        cls,
        logits: torch.Tensor,
        actions: torch.Tensor,
        eligible: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        # Replace forced/inactive logits before nonlinear terms.  This avoids
        # relying on zero times an undefined diagnostic to remove actor terms.
        actor_logits = torch.where(eligible, logits, torch.zeros_like(logits))
        return cls._bit_terms(actor_logits, actions)

    def evaluate_actions(
        self,
        context: torch.Tensor,
        eligible: torch.Tensor,
        forced_end: torch.Tensor,
        actions: torch.Tensor,
    ) -> MaskEvaluation:
        """Teacher-force a stored whole mask and return one team likelihood."""

        eligible, _ = self._validate_inputs(context, eligible, forced_end, actions)
        logits = torch.stack(
            [self._agent_logits(context, actions, agent) for agent in range(self.n_agents)],
            dim=-1,
        )
        bit_log_prob, bit_entropy = self._eligible_bit_terms(logits, actions, eligible)
        zeros = torch.zeros((), dtype=logits.dtype, device=logits.device)
        team_log_prob = torch.where(eligible, bit_log_prob, zeros).sum(dim=-1)
        conditional_entropy = torch.where(eligible, bit_entropy, zeros).sum(dim=-1)
        return MaskEvaluation(
            log_prob=team_log_prob,
            entropy=conditional_entropy,
            logits=logits,
            bit_log_prob=bit_log_prob,
            bit_entropy=bit_entropy,
        )

    def sample(
        self,
        context: torch.Tensor,
        eligible: torch.Tensor,
        forced_end: torch.Tensor,
        generator: torch.Generator | None = None,
        deterministic: bool = False,
    ) -> MaskSample:
        """Sample or greedily choose one complete legal mask in canonical order."""

        eligible, forced_end = self._validate_inputs(context, eligible, forced_end)
        actions = forced_end.clone()
        logits_by_agent: list[torch.Tensor] = []
        active_generator = generator
        if active_generator is None and not deterministic:
            active_generator = self._generator_for(context.device)
        for agent in range(self.n_agents):
            logits = self._agent_logits(context, actions, agent)
            logits_by_agent.append(logits)
            optional = eligible[:, agent]
            if deterministic:
                selected = logits >= 0.0
            else:
                assert active_generator is not None
                uniforms = torch.rand(
                    logits.shape,
                    dtype=logits.dtype,
                    device=logits.device,
                    generator=active_generator,
                )
                selected = uniforms < torch.sigmoid(logits)
            actions[:, agent] = torch.where(optional, selected, actions[:, agent])
        logits = torch.stack(logits_by_agent, dim=-1)
        bit_log_prob, bit_entropy = self._eligible_bit_terms(logits, actions, eligible)
        zeros = torch.zeros((), dtype=logits.dtype, device=logits.device)
        return MaskSample(
            actions=actions,
            log_prob=torch.where(eligible, bit_log_prob, zeros).sum(dim=-1),
            entropy=torch.where(eligible, bit_entropy, zeros).sum(dim=-1),
            logits=logits,
        )


class _ValueNetwork(nn.Module):
    def __init__(self, context_dim: int, hidden_size: int) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(context_dim, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1),
        )

    def forward(self, context: torch.Tensor) -> torch.Tensor:
        return self.network(context).squeeze(-1)


class ValueCritic(nn.Module):
    """Native-return critic whose only input is the predecision context."""

    def __init__(
        self, context_dim: int, hidden_size: int = 128, seed: int = 0
    ) -> None:
        super().__init__()
        self.context_dim = _require_positive_int("context_dim", context_dim)
        self.hidden_size = _require_positive_int("hidden_size", hidden_size)
        self.network = _seeded_build(
            seed, lambda: _ValueNetwork(self.context_dim, self.hidden_size)
        )

    def forward(self, context: torch.Tensor) -> torch.Tensor:
        if context.ndim != 2 or context.shape[1] != self.context_dim:
            raise ValueError(
                f"context must have shape [batch, {self.context_dim}], got {tuple(context.shape)}"
            )
        return self.network(context)


def compute_gae(
    rewards: torch.Tensor,
    values: torch.Tensor,
    next_values: torch.Tensor,
    terminated: torch.Tensor,
    truncated: torch.Tensor,
    gamma: float,
    gae_lambda: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Compute ``[time, batch]`` GAE with explicit boundary semantics.

    Actual terminals have zero bootstrap.  Continuation truncations bootstrap
    from the supplied next value.  Both kinds of boundary stop the backward
    eligibility trace, so no following episode or rollout segment leaks back.
    """

    if rewards.ndim != 2:
        raise ValueError("GAE tensors must have shape [time, batch]")
    if rewards.shape[0] == 0 or rewards.shape[1] == 0:
        raise ValueError("GAE time and batch dimensions must be nonempty")
    if any(tensor.shape != rewards.shape for tensor in (values, next_values, terminated, truncated)):
        raise ValueError("all GAE tensors must have the same shape")
    if terminated.dtype is not torch.bool or truncated.dtype is not torch.bool:
        raise TypeError("terminated and truncated must be bool tensors")
    if any(not tensor.is_floating_point() for tensor in (rewards, values, next_values)):
        raise TypeError("rewards, values, and next_values must be floating-point tensors")
    if values.dtype != rewards.dtype or next_values.dtype != rewards.dtype:
        raise TypeError("rewards, values, and next_values must have the same dtype")
    if bool(torch.any(terminated & truncated)):
        raise ValueError("a transition cannot be both terminal and continuation-truncated")
    if not math.isfinite(gamma) or not 0.0 <= gamma <= 1.0:
        raise ValueError("gamma must be finite and in [0, 1]")
    if not math.isfinite(gae_lambda) or not 0.0 <= gae_lambda <= 1.0:
        raise ValueError("gae_lambda must be finite and in [0, 1]")
    if rewards.device != values.device or any(
        tensor.device != rewards.device
        for tensor in (next_values, terminated, truncated)
    ):
        raise ValueError("all GAE tensors must be on the same device")

    stopped_values = values.detach()
    stopped_next_values = next_values.detach()
    advantages = torch.empty_like(rewards)
    following_advantage = torch.zeros_like(rewards[0])
    for step in range(rewards.shape[0] - 1, -1, -1):
        terminal = terminated[step]
        boundary = terminal | truncated[step]
        bootstrap = torch.where(
            terminal,
            torch.zeros((), dtype=rewards.dtype, device=rewards.device),
            stopped_next_values[step],
        )
        delta = rewards[step] + gamma * bootstrap - stopped_values[step]
        trace = torch.where(
            boundary,
            torch.zeros((), dtype=rewards.dtype, device=rewards.device),
            following_advantage,
        )
        following_advantage = delta + gamma * gae_lambda * trace
        advantages[step] = following_advantage
    returns = advantages + stopped_values
    return advantages.detach(), returns.detach()


@dataclass(frozen=True)
class RolloutBatch:
    context: torch.Tensor
    actions: torch.Tensor
    eligible: torch.Tensor
    forced_end: torch.Tensor
    old_log_prob: torch.Tensor
    advantages: torch.Tensor
    returns: torch.Tensor


class PPOUpdater:
    """Bounded full-mask PPO with separate actor and context-only critic steps."""

    def __init__(
        self,
        policy: MaskPolicy,
        critic: ValueCritic,
        *,
        learning_rate: float = 3e-4,
        critic_learning_rate: float | None = None,
        clip_epsilon: float = 0.2,
        entropy_coef: float = 0.0,
        value_coef: float = 0.5,
        max_grad_norm: float = 0.5,
        epochs: int = 4,
        minibatch_size: int = 64,
        seed: int = 0,
    ) -> None:
        if policy.context_dim != critic.context_dim:
            raise ValueError("policy and critic context dimensions must match")
        self.policy = policy
        self.critic = critic
        self.epochs = _require_positive_int("epochs", epochs)
        self.minibatch_size = _require_positive_int("minibatch_size", minibatch_size)
        for name, value in (
            ("learning_rate", learning_rate),
            ("clip_epsilon", clip_epsilon),
            ("value_coef", value_coef),
            ("max_grad_norm", max_grad_norm),
        ):
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if not math.isfinite(entropy_coef) or entropy_coef < 0.0:
            raise ValueError("entropy_coef must be finite and nonnegative")
        if critic_learning_rate is None:
            critic_learning_rate = learning_rate
        if not math.isfinite(critic_learning_rate) or critic_learning_rate <= 0.0:
            raise ValueError("critic_learning_rate must be finite and positive")
        self.clip_epsilon = float(clip_epsilon)
        self.entropy_coef = float(entropy_coef)
        self.value_coef = float(value_coef)
        self.max_grad_norm = float(max_grad_norm)
        self.actor_optimizer = torch.optim.Adam(policy.parameters(), lr=float(learning_rate))
        self.critic_optimizer = torch.optim.Adam(
            critic.parameters(), lr=float(critic_learning_rate)
        )
        self._shuffle_generator = torch.Generator(device="cpu")
        self._shuffle_generator.manual_seed(int(seed))

    def _validate_batch(self, batch: RolloutBatch) -> int:
        if batch.context.ndim != 2 or batch.context.shape[1] != self.policy.context_dim:
            raise ValueError("batch context has the wrong shape")
        if not batch.context.is_floating_point():
            raise TypeError("batch context must be floating point")
        rows = batch.context.shape[0]
        if rows == 0:
            raise ValueError("PPO batch cannot be empty")
        mask_shape = (rows, self.policy.n_agents)
        if any(
            tensor.shape != mask_shape
            for tensor in (batch.actions, batch.eligible, batch.forced_end)
        ):
            raise ValueError("batch action and mask tensors have the wrong shape")
        if any(
            tensor.shape != (rows,)
            for tensor in (batch.old_log_prob, batch.advantages, batch.returns)
        ):
            raise ValueError("batch scalar tensors must have shape [rows]")
        if any(
            not tensor.is_floating_point()
            for tensor in (batch.old_log_prob, batch.advantages, batch.returns)
        ):
            raise TypeError("batch scalar tensors must be floating point")
        self.policy._validate_inputs(
            batch.context, batch.eligible, batch.forced_end, batch.actions
        )
        tensors = (
            batch.actions,
            batch.eligible,
            batch.forced_end,
            batch.old_log_prob,
            batch.advantages,
            batch.returns,
        )
        if any(tensor.device != batch.context.device for tensor in tensors):
            raise ValueError("all rollout tensors must be on the same device")
        if not bool(torch.isfinite(batch.context).all()):
            raise ValueError("batch context must be finite")
        if any(
            not bool(torch.isfinite(tensor).all())
            for tensor in (batch.old_log_prob, batch.advantages, batch.returns)
        ):
            raise ValueError("batch likelihoods, advantages, and returns must be finite")
        return rows

    def update(self, batch: RolloutBatch) -> dict[str, float | int]:
        rows = self._validate_batch(batch)
        optional_rows = batch.eligible.any(dim=-1)
        normalized_advantages = torch.zeros_like(batch.advantages)
        if bool(optional_rows.any()):
            actor_advantages = batch.advantages[optional_rows].detach()
            mean = actor_advantages.mean()
            variance = ((actor_advantages - mean) ** 2).mean()
            normalized_advantages[optional_rows] = (actor_advantages - mean) / torch.sqrt(
                variance + 1e-8
            )

        actor_steps = 0
        critic_steps = 0
        visited_rows = 0
        actor_visited_rows = 0
        max_minibatch_size = 0
        actor_loss_sum = 0.0
        critic_loss_sum = 0.0
        entropy_sum = 0.0
        max_actor_grad_norm = 0.0
        max_critic_grad_norm = 0.0

        for _epoch in range(self.epochs):
            order = torch.randperm(rows, generator=self._shuffle_generator)
            for start in range(0, rows, self.minibatch_size):
                cpu_indices = order[start : start + self.minibatch_size]
                indices = cpu_indices.to(device=batch.context.device)
                minibatch_rows = int(indices.numel())
                visited_rows += minibatch_rows
                max_minibatch_size = max(max_minibatch_size, minibatch_rows)

                local_optional = optional_rows[indices]
                optional_count = int(local_optional.sum().item())
                if optional_count:
                    actor_indices = indices[local_optional]
                    evaluation = self.policy.evaluate_actions(
                        batch.context[actor_indices],
                        batch.eligible[actor_indices],
                        batch.forced_end[actor_indices],
                        batch.actions[actor_indices],
                    )
                    ratio = torch.exp(
                        evaluation.log_prob - batch.old_log_prob[actor_indices].detach()
                    )
                    advantage = normalized_advantages[actor_indices].detach()
                    clipped_ratio = torch.clamp(
                        ratio, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon
                    )
                    actor_loss = -torch.minimum(
                        ratio * advantage, clipped_ratio * advantage
                    ).mean()
                    entropy = evaluation.entropy.mean()
                    objective = actor_loss - self.entropy_coef * entropy
                    self.actor_optimizer.zero_grad(set_to_none=True)
                    objective.backward()
                    actor_grad_norm = nn.utils.clip_grad_norm_(
                        self.policy.parameters(), self.max_grad_norm
                    )
                    self.actor_optimizer.step()
                    actor_steps += 1
                    actor_visited_rows += optional_count
                    actor_loss_sum += float(actor_loss.detach()) * optional_count
                    entropy_sum += float(entropy.detach()) * optional_count
                    max_actor_grad_norm = max(
                        max_actor_grad_norm, float(actor_grad_norm.detach())
                    )

                predicted_values = self.critic(batch.context[indices])
                critic_loss = torch.mean(
                    (predicted_values - batch.returns[indices].detach()) ** 2
                )
                self.critic_optimizer.zero_grad(set_to_none=True)
                (self.value_coef * critic_loss).backward()
                critic_grad_norm = nn.utils.clip_grad_norm_(
                    self.critic.parameters(), self.max_grad_norm
                )
                self.critic_optimizer.step()
                critic_steps += 1
                critic_loss_sum += float(critic_loss.detach()) * minibatch_rows
                max_critic_grad_norm = max(
                    max_critic_grad_norm, float(critic_grad_norm.detach())
                )

        return {
            "planned_rows": rows,
            "optional_rows": int(optional_rows.sum().item()),
            "visited_rows": visited_rows,
            "actor_visited_rows": actor_visited_rows,
            "actor_optimizer_steps": actor_steps,
            "critic_optimizer_steps": critic_steps,
            "max_minibatch_size": max_minibatch_size,
            "actor_loss": actor_loss_sum / max(actor_visited_rows, 1),
            "critic_loss": critic_loss_sum / visited_rows,
            "entropy": entropy_sum / max(actor_visited_rows, 1),
            "max_actor_grad_norm": max_actor_grad_norm,
            "max_critic_grad_norm": max_critic_grad_norm,
        }
