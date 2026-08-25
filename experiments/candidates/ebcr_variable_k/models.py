from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import torch
from torch import nn

from .config import PPO, RunConfig
from .host import EpisodeResult, TickTrainingRecord
from .rng import namespace_seed


class HazardNetwork(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(10, 32), nn.Tanh(), nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, 1)
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features).squeeze(-1)


class CentralCritic(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(15, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 1)
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features).squeeze(-1)


def _initialized(module_type: type[nn.Module], seed: int) -> nn.Module:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        return module_type()


@dataclass
class PPODiagnostics:
    optimizer_steps: int
    actor_loss: float
    critic_loss: float
    entropy: float
    gradient_norm: float
    tick_records: int
    policy_records: int


class PPOHazardLearner:
    def __init__(self, base_seed: int) -> None:
        # LOCAL and COORD intentionally call this with the same base seed.  They
        # start paired but hold disjoint modules, trajectories and optimizers.
        self.actor = _initialized(
            HazardNetwork, namespace_seed("actor_initialization", base_seed)
        )
        self.critic = _initialized(
            CentralCritic, namespace_seed("critic_initialization", base_seed)
        )
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=PPO["learning_rate"])
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=PPO["learning_rate"])

    def probabilities(self, features: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            logits = self.actor(torch.as_tensor(features, dtype=torch.float32))
            return torch.sigmoid(logits).cpu().numpy()

    def critic_value(self, features: np.ndarray) -> float:
        with torch.no_grad():
            value = self.critic(torch.as_tensor(features, dtype=torch.float32).unsqueeze(0))
            return float(value.item())

    @property
    def actor_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.actor.parameters())

    @property
    def critic_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.critic.parameters())

    def update(
        self, episodes: Iterable[EpisodeResult], *, base_seed: int, arm: str, config: RunConfig
    ) -> PPODiagnostics:
        episode_rows = [episode.training_records for episode in episodes]
        if not episode_rows or any(len(rows) != config.horizon for rows in episode_rows):
            raise ValueError("PPO update requires complete fixed-horizon episodes")
        flat: list[TickTrainingRecord] = [row for episode in episode_rows for row in episode]
        advantages = np.empty(len(flat), dtype=np.float32)
        returns = np.empty(len(flat), dtype=np.float32)
        offset = 0
        gamma = float(PPO["gamma"])
        gae_lambda = float(PPO["gae_lambda"])
        for rows in episode_rows:
            gae = 0.0
            for tick in range(len(rows) - 1, -1, -1):
                next_value = 0.0 if tick == len(rows) - 1 else rows[tick + 1].value
                delta = rows[tick].reward + gamma * next_value - rows[tick].value
                gae = delta + gamma * gae_lambda * gae
                advantages[offset + tick] = gae
                returns[offset + tick] = gae + rows[tick].value
            offset += len(rows)
        actor_x = torch.as_tensor(np.stack([row.actor_features for row in flat]), dtype=torch.float32)
        critic_x = torch.as_tensor(np.stack([row.critic_features for row in flat]), dtype=torch.float32)
        actions = torch.as_tensor(np.stack([row.actions for row in flat]), dtype=torch.float32)
        old_log_probs = torch.as_tensor(np.stack([row.old_log_probs for row in flat]), dtype=torch.float32)
        masks = torch.as_tensor(np.stack([row.policy_mask for row in flat]), dtype=torch.float32)
        advantage_tensor = torch.as_tensor(advantages, dtype=torch.float32)
        return_tensor = torch.as_tensor(returns, dtype=torch.float32)
        valid_advantages = advantage_tensor.repeat_interleave(2)[masks.reshape(-1).bool()]
        if valid_advantages.numel() == 0:
            raise ValueError("PPO batch contains no policy-eligible hazard records")
        advantage_tensor = (advantage_tensor - valid_advantages.mean()) / (
            valid_advantages.std(unbiased=False) + 1e-8
        )
        count = len(flat)
        minibatch = config.minibatch_ticks
        losses: list[tuple[float, float, float, float]] = []
        optimizer_steps = 0
        for epoch in range(config.ppo_epochs):
            generator = np.random.default_rng(namespace_seed(
                "ppo_minibatch_order", base_seed, arm, epoch, count
            ))
            order = generator.permutation(count)
            for start in range(0, count, minibatch):
                indices = torch.as_tensor(order[start:start + minibatch], dtype=torch.long)
                logits = self.actor(actor_x[indices])
                distribution = torch.distributions.Bernoulli(logits=logits)
                new_log_probs = distribution.log_prob(actions[indices])
                ratio = torch.exp(new_log_probs - old_log_probs[indices])
                batch_advantage = advantage_tensor[indices].unsqueeze(1).expand_as(ratio)
                clipped = torch.clamp(ratio, 1.0 - PPO["clip"], 1.0 + PPO["clip"])
                mask = masks[indices]
                denominator = mask.sum().clamp_min(1.0)
                actor_loss = -(
                    torch.minimum(ratio * batch_advantage, clipped * batch_advantage) * mask
                ).sum() / denominator
                entropy = (distribution.entropy() * mask).sum() / denominator
                actor_objective = actor_loss - PPO["entropy_coefficient"] * entropy
                self.actor_optimizer.zero_grad(set_to_none=True)
                actor_objective.backward()
                actor_norm = nn.utils.clip_grad_norm_(self.actor.parameters(), PPO["gradient_norm_cap"])
                self.actor_optimizer.step()

                values = self.critic(critic_x[indices])
                critic_loss = torch.mean((values - return_tensor[indices]) ** 2)
                self.critic_optimizer.zero_grad(set_to_none=True)
                (PPO["value_coefficient"] * critic_loss).backward()
                critic_norm = nn.utils.clip_grad_norm_(self.critic.parameters(), PPO["gradient_norm_cap"])
                self.critic_optimizer.step()
                optimizer_steps += 1
                losses.append((
                    float(actor_loss.detach()), float(critic_loss.detach()),
                    float(entropy.detach()), float(max(float(actor_norm), float(critic_norm))),
                ))
        values = np.asarray(losses, dtype=np.float64)
        return PPODiagnostics(
            optimizer_steps=optimizer_steps,
            actor_loss=float(values[:, 0].mean()), critic_loss=float(values[:, 1].mean()),
            entropy=float(values[:, 2].mean()), gradient_norm=float(values[:, 3].max()),
            tick_records=count, policy_records=int(masks.sum().item()),
        )

    def checkpoint(self) -> dict[str, object]:
        return {
            "actor": self.actor.state_dict(), "critic": self.critic.state_dict(),
            "actor_optimizer": self.actor_optimizer.state_dict(),
            "critic_optimizer": self.critic_optimizer.state_dict(),
            "actor_parameter_count": self.actor_parameter_count,
            "critic_parameter_count": self.critic_parameter_count,
        }
