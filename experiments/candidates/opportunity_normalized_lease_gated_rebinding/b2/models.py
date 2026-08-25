"""Matched B2 event actors, centralized critic, and behavior-frozen PPO."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import TYPE_CHECKING, Iterable

import numpy as np
import torch
from torch import nn

from .config import (
    ARMS, GAMMA_TICK, GRADIENT_NORM_CAP, LAMBDA_TICK, LEARNING_RATE,
    PPO_CLIP, PPO_EPOCHS, RHO, TRAIN_SCHEDULES, VALUE_COEFFICIENT,
)
from .rng import namespace_seed

if TYPE_CHECKING:
    from .host import EpisodeResult

ACTOR_WIDTH = 7
CRITIC_WIDTH = 39
_DTYPE = torch.float64
_LOG_TWO = math.log(2.0)


def softplus_inverse(value: float) -> float:
    if value <= 0.0:
        raise ValueError("softplus inverse requires a positive value")
    return math.log(math.expm1(value))


def initial_rate() -> float:
    return -math.log(0.8) / 8.0


def initial_event_bias() -> float:
    return softplus_inverse(initial_rate())


def analytic_probability(logit: np.ndarray | float, exposure: np.ndarray | float) -> np.ndarray:
    """Stable float64 eligible-exposure event probability."""
    g = np.asarray(logit, dtype=np.float64)
    e = np.asarray(exposure, dtype=np.float64)
    rate = np.logaddexp(0.0, g)
    value = -np.expm1(-rate * e)
    return np.where(e > 0.0, value, 0.0)


def analytic_probability_jacobian(logit: float, exposure: float) -> tuple[float, float]:
    """Return du/dg and du/de for the registered probability map."""
    if exposure <= 0.0:
        return 0.0, 0.0
    rate = float(np.logaddexp(0.0, np.float64(logit)))
    survival = math.exp(-rate * exposure)
    sigmoid = 1.0 / (1.0 + math.exp(-logit))
    return exposure * survival * sigmoid, rate * survival


class EventActor(nn.Module):
    """The exact 7-32-32-1 tanh network; CONST zeroes only its input."""

    def __init__(self, arm: str) -> None:
        super().__init__()
        if arm not in ARMS:
            raise ValueError(f"unknown B2 arm: {arm}")
        self.arm = arm
        self.input_layer = nn.Linear(ACTOR_WIDTH, 32, dtype=_DTYPE)
        self.hidden_layer = nn.Linear(32, 32, dtype=_DTYPE)
        self.output_layer = nn.Linear(32, 1, dtype=_DTYPE)

    def actor_input(self, features: torch.Tensor) -> torch.Tensor:
        if features.shape[-1] != ACTOR_WIDTH:
            raise ValueError("B2 actor input must have exactly seven coordinates")
        return torch.zeros_like(features) if self.arm == "RATE-CONST" else features

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        x = self.actor_input(features)
        x = torch.tanh(self.input_layer(x))
        x = torch.tanh(self.hidden_layer(x))
        return self.output_layer(x).squeeze(-1)

    def rate_and_probability(
        self, features: torch.Tensor, exposure: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        logits = self(features)
        rate = torch.nn.functional.softplus(logits)
        event = -torch.expm1(-rate * exposure)
        event = torch.where(exposure > 0.0, event, torch.zeros_like(event))
        return logits, rate, event

    def categorical_log_probabilities(
        self, features: torch.Tensor, exposure: torch.Tensor, actions: torch.Tensor,
    ) -> torch.Tensor:
        logits = self(features)
        eligible = exposure > 0.0
        log_keep = -torch.nn.functional.softplus(logits) * exposure
        safe_log_keep = torch.where(eligible, log_keep, torch.full_like(log_keep, -1.0))
        log_event = torch.log(-torch.expm1(safe_log_keep))
        selected = torch.where(actions == 0, log_keep, log_event - _LOG_TWO)
        return torch.where(eligible, selected, torch.zeros_like(selected))


class CentralCritic(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(CRITIC_WIDTH, 64, dtype=_DTYPE), nn.Tanh(),
            nn.Linear(64, 64, dtype=_DTYPE), nn.Tanh(),
            nn.Linear(64, 1, dtype=_DTYPE),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features).squeeze(-1)


def paired_modules(seed: int, arm: str) -> tuple[EventActor, CentralCritic]:
    """Construct bit-matched tensors; only the actor's input operation differs."""
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(namespace_seed("MODEL_INITIALIZATION", seed))
        actor = EventActor(arm)
        critic = CentralCritic()
    with torch.no_grad():
        actor.output_layer.weight.zero_()
        actor.output_layer.bias.fill_(initial_event_bias())
    return actor, critic


@dataclass(frozen=True)
class PPOUpdateFacts:
    update_index: int
    optimizer_steps: int
    complete_episodes: int
    boundary_rows: int
    genuine_joint_policy_rows: int
    episodes_by_schedule: dict[str, int]
    actor_joint_rows_by_schedule: dict[str, int]
    behavior_log_probabilities_cached_before_epochs: bool
    behavior_critic_values_cached_before_epochs: bool
    advantages_cached_before_epochs: bool
    lambda_returns_cached_before_epochs: bool
    caches_unchanged_all_epochs: bool
    terminal_behavior_value: float
    actor_global_scale: float
    advantage_normalization: bool
    value_clipping: bool
    value_coefficient_applications: int


class B2Learner:
    def __init__(self, seed: int, arm: str) -> None:
        self.seed = int(seed)
        self.arm = arm
        self.actor, self.critic = paired_modules(seed, arm)
        self.optimizer = torch.optim.Adam(
            (*self.actor.parameters(), *self.critic.parameters()), lr=LEARNING_RATE,
        )

    @property
    def actor_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.actor.parameters())

    @property
    def critic_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.critic.parameters())

    def policy(
        self, features: np.ndarray, exposure: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        with torch.no_grad():
            x = torch.as_tensor(features, dtype=_DTYPE)
            e = torch.as_tensor(exposure, dtype=_DTYPE)
            logits, rate, event = self.actor.rate_and_probability(x, e)
        return logits.numpy(), rate.numpy(), event.numpy()

    def value(self, features: np.ndarray) -> float:
        with torch.no_grad():
            x = torch.as_tensor(features, dtype=_DTYPE).unsqueeze(0)
            return float(self.critic(x).item())

    def joint_log_probability(
        self, features: np.ndarray, exposure: np.ndarray,
        actions: np.ndarray, policy_mask: np.ndarray,
    ) -> float:
        with torch.no_grad():
            x = torch.as_tensor(features, dtype=_DTYPE)
            e = torch.as_tensor(exposure, dtype=_DTYPE)
            a = torch.as_tensor(actions, dtype=torch.long)
            mask = torch.as_tensor(policy_mask, dtype=torch.bool)
            values = self.actor.categorical_log_probabilities(x, e, a)
            return float(torch.where(mask, values, torch.zeros_like(values)).sum().item())

    def update(self, episodes: Iterable["EpisodeResult"], update_index: int) -> PPOUpdateFacts:
        episode_objects = list(episodes)
        if len(episode_objects) != 32:
            raise ValueError("B2 PPO requires exactly 32 complete episodes")
        rows_by_episode = [episode.training_records for episode in episode_objects]
        if any(not rows or sum(row.duration for row in rows) != 256 for rows in rows_by_episode):
            raise ValueError("B2 PPO requires complete 256-tick SMDP trajectories")
        schedule_names = [episode.schedule for episode in episode_objects]
        episodes_by_schedule = {name: schedule_names.count(name) for name in TRAIN_SCHEDULES}
        if episodes_by_schedule != {name: 8 for name in TRAIN_SCHEDULES}:
            raise ValueError("each update requires eight episodes from every training tape")

        flat = [row for rows in rows_by_episode for row in rows]
        actor_x = torch.as_tensor(np.stack([row.actor_features for row in flat]), dtype=_DTYPE)
        critic_x = torch.as_tensor(np.stack([row.critic_features for row in flat]), dtype=_DTYPE)
        exposure = torch.as_tensor(np.stack([row.exposure for row in flat]), dtype=_DTYPE)
        actions = torch.as_tensor(np.stack([row.actions for row in flat]), dtype=torch.long)
        masks = torch.as_tensor(np.stack([row.policy_mask for row in flat]), dtype=torch.bool)
        behavior_log = torch.as_tensor([row.behavior_joint_log_prob for row in flat], dtype=_DTYPE)
        behavior_values = torch.as_tensor([row.behavior_value for row in flat], dtype=_DTYPE)
        episode_index = torch.as_tensor(
            [index for index, rows in enumerate(rows_by_episode) for _ in rows], dtype=torch.long,
        )
        genuine_rows = masks.any(dim=1)
        if not bool(genuine_rows.any()):
            raise ValueError("B2 PPO update contains no genuine stochastic joint row")

        # These are the immutable behavior-policy caches used by every epoch.
        advantages: list[float] = []
        targets: list[float] = []
        offset = 0
        for rows in rows_by_episode:
            local_values = behavior_values[offset:offset + len(rows)].detach().clone()
            local_adv = [0.0] * len(rows)
            gae = 0.0
            for index in range(len(rows) - 1, -1, -1):
                row = rows[index]
                next_value = 0.0 if index + 1 == len(rows) else float(local_values[index + 1])
                gamma = GAMMA_TICK ** row.duration
                lam = LAMBDA_TICK ** row.duration
                delta = row.segment_reward + gamma * next_value - float(local_values[index])
                gae = delta + gamma * lam * gae
                local_adv[index] = gae
            advantages.extend(local_adv)
            targets.extend(float(local_values[index]) + local_adv[index] for index in range(len(rows)))
            offset += len(rows)
        advantage = torch.as_tensor(advantages, dtype=_DTYPE).detach()
        lambda_return = torch.as_tensor(targets, dtype=_DTYPE).detach()
        cache_fingerprint = (
            behavior_log.clone(), behavior_values.clone(), advantage.clone(), lambda_return.clone(),
        )

        actor_scale = 1.0 / 256.0
        schedule_masks = {
            schedule: torch.as_tensor([name == schedule for name in schedule_names], dtype=torch.bool)
            for schedule in TRAIN_SCHEDULES
        }

        def balanced_actor_loss(terms: torch.Tensor) -> torch.Tensor:
            per_episode = torch.stack([
                actor_scale * terms[episode_index == index].sum()
                for index in range(len(rows_by_episode))
            ])
            return torch.stack([
                per_episode[schedule_masks[schedule]].mean() for schedule in TRAIN_SCHEDULES
            ]).mean()

        for _epoch in range(PPO_EPOCHS):
            flat_log = self.actor.categorical_log_probabilities(
                actor_x.reshape(-1, ACTOR_WIDTH), exposure.reshape(-1), actions.reshape(-1),
            ).reshape(-1, 2)
            joint_log = torch.where(masks, flat_log, torch.zeros_like(flat_log)).sum(dim=1)
            ratio = torch.exp(joint_log - behavior_log)
            clipped = torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP)
            surrogate = torch.minimum(ratio * advantage, clipped * advantage)
            actor_loss = balanced_actor_loss(-surrogate * genuine_rows.to(_DTYPE))

            predicted = self.critic(critic_x)
            squared_error = (predicted - lambda_return) ** 2
            per_episode_value = torch.stack([
                squared_error[episode_index == index].mean()
                for index in range(len(rows_by_episode))
            ])
            critic_loss = torch.stack([
                per_episode_value[schedule_masks[schedule]].mean()
                for schedule in TRAIN_SCHEDULES
            ]).mean()
            objective = actor_loss + VALUE_COEFFICIENT * critic_loss
            self.optimizer.zero_grad(set_to_none=True)
            objective.backward()
            norm = nn.utils.clip_grad_norm_(
                (*self.actor.parameters(), *self.critic.parameters()), GRADIENT_NORM_CAP,
            )
            self.optimizer.step()

        caches_unchanged = all(torch.equal(before, after) for before, after in zip(
            cache_fingerprint, (behavior_log, behavior_values, advantage, lambda_return), strict=True,
        ))
        return PPOUpdateFacts(
            update_index=int(update_index), optimizer_steps=PPO_EPOCHS,
            complete_episodes=len(episode_objects), boundary_rows=len(flat),
            genuine_joint_policy_rows=int(genuine_rows.sum()),
            episodes_by_schedule=episodes_by_schedule,
            actor_joint_rows_by_schedule={
                schedule: sum(
                    int(genuine_rows[episode_index == index].sum())
                    for index, name in enumerate(schedule_names) if name == schedule
                ) for schedule in TRAIN_SCHEDULES
            },
            behavior_log_probabilities_cached_before_epochs=True,
            behavior_critic_values_cached_before_epochs=True,
            advantages_cached_before_epochs=True, lambda_returns_cached_before_epochs=True,
            caches_unchanged_all_epochs=caches_unchanged, terminal_behavior_value=0.0,
            actor_global_scale=actor_scale, advantage_normalization=False, value_clipping=False,
            value_coefficient_applications=1,
        )

    def checkpoint(self, completed_updates: int, update_facts: list[PPOUpdateFacts]) -> dict[str, object]:
        return {
            "seed": self.seed, "arm": self.arm, "completed_updates": completed_updates,
            "actor": self.actor.state_dict(), "critic": self.critic.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "actor_parameter_count": self.actor_parameter_count,
            "critic_parameter_count": self.critic_parameter_count,
            "update_facts": [asdict(fact) for fact in update_facts],
        }

    def load_checkpoint(self, payload: dict[str, object]) -> None:
        if payload.get("seed") != self.seed or payload.get("arm") != self.arm:
            raise ValueError("checkpoint coordinate mismatch")
        self.actor.load_state_dict(payload["actor"])
        self.critic.load_state_dict(payload["critic"])
        self.optimizer.load_state_dict(payload["optimizer"])


def initialization_report(seed: int = 137) -> dict[str, object]:
    rows: dict[str, object] = {}
    arbitrary = torch.as_tensor(
        [[0.1, 0.2, 0.3, 1.0, 0.0, 0.5, 0.25]], dtype=_DTYPE,
    )
    for arm in ARMS:
        actor, critic = paired_modules(seed, arm)
        exposures = torch.as_tensor(list((1, 4, 8, 16, 24, 32)), dtype=_DTYPE)
        features = arbitrary.repeat(len(exposures), 1)
        with torch.no_grad():
            logits, rates, probabilities = actor.rate_and_probability(features, exposures)
        rows[arm] = {
            "logits": tuple(float(value) for value in logits),
            "rates": tuple(float(value) for value in rates),
            "probabilities": tuple(float(value) for value in probabilities),
            "output_weights_exact_zero": bool(torch.count_nonzero(actor.output_layer.weight) == 0),
            "output_bias": float(actor.output_layer.bias.item()),
            "actor_parameter_count": sum(p.numel() for p in actor.parameters()),
            "critic_parameter_count": sum(p.numel() for p in critic.parameters()),
        }
    return rows
