"""Matched marked actors, centralized critic, and ordinary SMDP-GAE PPO."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING, Iterable

import numpy as np
import torch
from torch import nn

from .config import GAMMA_TICK, LAMBDA_TICK, PPO, TRAIN_SCHEDULES
from .rng import namespace_seed

if TYPE_CHECKING:
    from .host import EpisodeResult

ACTOR_WIDTH = 14
CRITIC_WIDTH = 39


def marked_entropy_components(
    event: torch.Tensor, mark: torch.Tensor, masks: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Per-row event, conditional-mark, and applied mark entropy sums."""
    event_entropy = -(
        torch.special.xlogy(event, event)
        + torch.special.xlog1py(1.0 - event, -event)
    )
    mark_entropy = -(
        torch.special.xlogy(mark, mark)
        + torch.special.xlog1py(1.0 - mark, -mark)
    )
    return (
        (event_entropy * masks).sum(dim=1),
        (mark_entropy * masks).sum(dim=1),
        (event * mark_entropy * masks).sum(dim=1),
    )


def _logit(p: float) -> float:
    return math.log(p) - math.log1p(-p)


def initial_event_bias(arm: str) -> float:
    if arm == "RAW-BOUNDARY-LEASE":
        return _logit(0.20)
    if arm in ("ONLGR", "TIMING-ONLY-ONLGR"):
        rate = -math.log(0.80) / 8.0
        return math.log(math.expm1(rate))
    raise ValueError(f"unknown learned arm: {arm}")


class MarkedActor(nn.Module):
    def __init__(self, arm: str) -> None:
        super().__init__()
        self.arm = arm
        self.trunk = nn.Sequential(
            nn.Linear(ACTOR_WIDTH, 32), nn.Tanh(),
            nn.Linear(32, 32), nn.Tanh(),
        )
        self.event_head = nn.Linear(32, 1)
        self.mark_head = nn.Linear(32, 1)

    def forward(self, features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if self.arm == "TIMING-ONLY-ONLGR":
            features = features.clone()
            features[..., (2, 3, 4, 8, 9)] = 0.0
        hidden = self.trunk(features)
        return self.event_head(hidden).squeeze(-1), self.mark_head(hidden).squeeze(-1)

    def probabilities(
        self, features: torch.Tensor, exposure: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        event_logits, mark_logits = self(features)
        if self.arm in ("ONLGR", "TIMING-ONLY-ONLGR"):
            rate = torch.nn.functional.softplus(event_logits)
            event = -torch.expm1(-rate * exposure)
        elif self.arm == "RAW-BOUNDARY-LEASE":
            event = torch.sigmoid(event_logits)
        else:  # pragma: no cover - constructor validation protects this path.
            raise RuntimeError(self.arm)
        event = torch.where(exposure > 0, event, torch.zeros_like(event))
        return event, torch.sigmoid(mark_logits)

    def categorical_log_probabilities(
        self, features: torch.Tensor, exposure: torch.Tensor,
        actions: torch.Tensor,
    ) -> torch.Tensor:
        """Exact stable marked-categorical log probability per agent row."""
        event_logits, mark_logits = self(features)
        eligible = exposure > 0
        if self.arm in ("ONLGR", "TIMING-ONLY-ONLGR"):
            log_keep = -exposure * torch.nn.functional.softplus(event_logits)
            safe_log_keep = torch.where(eligible, log_keep, torch.full_like(log_keep, -1.0))
            log_event = torch.log(-torch.expm1(safe_log_keep))
        elif self.arm == "RAW-BOUNDARY-LEASE":
            log_keep = torch.nn.functional.logsigmoid(-event_logits)
            log_event = torch.nn.functional.logsigmoid(event_logits)
        else:  # pragma: no cover - constructor validation protects this path.
            raise RuntimeError(self.arm)
        is_event = actions > 0
        event_term = torch.where(is_event, log_event, log_keep)
        mark_term = torch.where(
            actions == 1,
            torch.nn.functional.logsigmoid(mark_logits),
            torch.nn.functional.logsigmoid(-mark_logits),
        )
        stochastic = event_term + is_event.to(event_term.dtype) * mark_term
        return torch.where(eligible, stochastic, torch.zeros_like(stochastic))


class CentralCritic(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(CRITIC_WIDTH, 64), nn.Tanh(),
            nn.Linear(64, 64), nn.Tanh(),
            nn.Linear(64, 1),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features).squeeze(-1)


def _paired_modules(seed: int, arm: str) -> tuple[MarkedActor, CentralCritic]:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(namespace_seed("paired_model_initialization", seed))
        actor = MarkedActor(arm)
        critic = CentralCritic()
    with torch.no_grad():
        hidden = actor.trunk(torch.zeros((1, ACTOR_WIDTH), dtype=torch.float32)).squeeze(0)
        actor.event_head.bias.fill_(
            initial_event_bias(arm) - float(torch.dot(actor.event_head.weight.squeeze(0), hidden))
        )
        actor.mark_head.bias.fill_(-float(torch.dot(actor.mark_head.weight.squeeze(0), hidden)))
    return actor, critic


@dataclass(frozen=True)
class PPOUpdate:
    optimizer_steps: int
    actor_loss: float
    critic_loss: float
    event_entropy: float
    mark_entropy: float
    applied_mark_entropy: float
    maximum_gradient_norm: float
    boundary_rows: int
    policy_rows: int
    complete_episodes: int
    actor_global_episode_scale: float
    actor_joint_rows_by_schedule: dict[str, int]
    critic_row_weight_sums: tuple[float, ...]
    episodes_by_schedule: dict[str, int]
    behavior_actor_log_prob_cached_before_epochs: bool
    behavior_critic_values_cached_before_epochs: bool
    lambda_returns_cached_before_epochs: bool
    terminal_behavior_value: float
    advantage_normalization: bool
    value_clipping: bool
    value_coefficient_applications: int


class MarkedLearner:
    def __init__(self, seed: int, arm: str) -> None:
        self.seed = seed
        self.arm = arm
        self.actor, self.critic = _paired_modules(seed, arm)
        self.optimizer = torch.optim.Adam(
            (*self.actor.parameters(), *self.critic.parameters()),
            lr=float(PPO["learning_rate"]),
        )

    @property
    def actor_parameter_count(self) -> int:
        return sum(p.numel() for p in self.actor.parameters())

    @property
    def critic_parameter_count(self) -> int:
        return sum(p.numel() for p in self.critic.parameters())

    def policy(self, features: np.ndarray, exposure: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        with torch.no_grad():
            x = torch.as_tensor(features, dtype=torch.float32)
            e = torch.as_tensor(exposure, dtype=torch.float32)
            logits, marks = self.actor(x)
            event, mark = self.actor.probabilities(x, e)
            return logits.numpy(), event.numpy(), mark.numpy()

    def value(self, features: np.ndarray) -> float:
        with torch.no_grad():
            x = torch.as_tensor(features, dtype=torch.float32).unsqueeze(0)
            return float(self.critic(x).item())

    def joint_log_probability(
        self, features: np.ndarray, exposure: np.ndarray,
        actions: np.ndarray, policy_mask: np.ndarray,
    ) -> float:
        with torch.no_grad():
            x = torch.as_tensor(features, dtype=torch.float32)
            e = torch.as_tensor(exposure, dtype=torch.float32)
            a = torch.as_tensor(actions, dtype=torch.long)
            mask = torch.as_tensor(policy_mask, dtype=torch.bool)
            agent_log = self.actor.categorical_log_probabilities(x, e, a)
            return float(torch.where(mask, agent_log, torch.zeros_like(agent_log)).sum().item())

    def update(self, episodes: Iterable["EpisodeResult"], update_index: int) -> PPOUpdate:
        episode_objects = list(episodes)
        rows_by_episode = [episode.training_records for episode in episode_objects]
        if len(rows_by_episode) != int(PPO["episodes_per_update"]):
            raise ValueError("PPO requires exactly 32 complete episodes")
        if any(not rows or sum(row.duration for row in rows) != 256 for rows in rows_by_episode):
            raise ValueError("PPO requires complete 256-tick boundary trajectories")

        flat = [row for rows in rows_by_episode for row in rows]
        advantages: list[float] = []
        targets: list[float] = []
        for rows in rows_by_episode:
            local_adv = [0.0] * len(rows)
            gae = 0.0
            for index in range(len(rows) - 1, -1, -1):
                row = rows[index]
                next_value = 0.0 if index + 1 == len(rows) else rows[index + 1].value
                gamma = GAMMA_TICK ** row.duration
                lam = LAMBDA_TICK ** row.duration
                delta = row.segment_reward + gamma * next_value - row.value
                gae = delta + gamma * lam * gae
                local_adv[index] = gae
            advantages.extend(local_adv)
            targets.extend(local_adv[i] + rows[i].value for i in range(len(rows)))

        actor_x = torch.as_tensor(np.stack([r.actor_features for r in flat]), dtype=torch.float32)
        critic_x = torch.as_tensor(np.stack([r.critic_features for r in flat]), dtype=torch.float32)
        exposure = torch.as_tensor(np.stack([r.exposure for r in flat]), dtype=torch.float32)
        actions = torch.as_tensor(np.stack([r.actions for r in flat]), dtype=torch.long)
        masks = torch.as_tensor(np.stack([r.policy_mask for r in flat]), dtype=torch.float32)
        old_joint = torch.as_tensor([r.old_joint_log_prob for r in flat], dtype=torch.float32)
        episode_index = torch.as_tensor(
            [i for i, rows in enumerate(rows_by_episode) for _ in rows], dtype=torch.long
        )
        advantage = torch.as_tensor(advantages, dtype=torch.float32)
        targets_t = torch.as_tensor(targets, dtype=torch.float32)
        policy_rows = masks.sum(dim=1) > 0
        if not bool(policy_rows.any()):
            raise ValueError("PPO update has no lease-eligible policy row")
        schedule_names = [episode.schedule for episode in episode_objects]
        episodes_by_schedule = {name: schedule_names.count(name) for name in TRAIN_SCHEDULES}
        if episodes_by_schedule != {name: 8 for name in TRAIN_SCHEDULES}:
            raise ValueError("PPO update requires eight complete episodes from each training schedule")
        actor_scale = 1.0 / 256.0
        def schedule_episode_mean(terms: torch.Tensor) -> torch.Tensor:
            episode_terms = torch.stack([
                actor_scale * terms[episode_index == i].sum()
                for i in range(len(rows_by_episode))
            ])
            return torch.stack([
                episode_terms[torch.as_tensor(
                    [name == schedule for name in schedule_names], dtype=torch.bool
                )].mean() for schedule in TRAIN_SCHEDULES
            ]).mean()

        losses: list[tuple[float, float, float, float, float, float]] = []
        for _epoch in range(int(PPO["epochs"])):
            flat_actor = actor_x.reshape(-1, ACTOR_WIDTH)
            flat_exposure = exposure.reshape(-1)
            event, mark = self.actor.probabilities(flat_actor, flat_exposure)
            event = event.reshape(-1, 2)
            mark = mark.reshape(-1, 2)
            is_event = (actions > 0).to(torch.float32)
            agent_log = self.actor.categorical_log_probabilities(
                flat_actor, flat_exposure, actions.reshape(-1),
            ).reshape(-1, 2)
            agent_log = torch.where(
                masks.bool(), agent_log, torch.zeros_like(agent_log),
            )
            joint_log = agent_log.sum(dim=1)
            ratio = torch.exp(joint_log - old_joint)
            clipped = torch.clamp(ratio, 1.0 - float(PPO["clip"]), 1.0 + float(PPO["clip"]))
            actor_terms = (
                -torch.minimum(ratio * advantage, clipped * advantage)
                * policy_rows.to(torch.float32)
            )
            actor_loss = schedule_episode_mean(actor_terms)

            row_event_entropy, row_mark_entropy, row_applied_mark_entropy = (
                marked_entropy_components(event, mark, masks)
            )
            event_entropy = schedule_episode_mean(row_event_entropy)
            mark_entropy = schedule_episode_mean(row_mark_entropy)
            applied_mark_entropy = schedule_episode_mean(row_applied_mark_entropy)

            values = self.critic(critic_x)
            squared = (values - targets_t) ** 2
            per_episode = torch.stack([
                squared[episode_index == i].mean()
                for i in range(len(rows_by_episode))
            ])
            critic_loss = torch.stack([
                per_episode[torch.as_tensor(
                    [name == schedule for name in schedule_names], dtype=torch.bool
                )].mean() for schedule in TRAIN_SCHEDULES
            ]).mean()
            objective = (
                actor_loss + float(PPO["value_coefficient"]) * critic_loss
            )
            self.optimizer.zero_grad(set_to_none=True)
            objective.backward()
            norm = nn.utils.clip_grad_norm_(
                (*self.actor.parameters(), *self.critic.parameters()),
                float(PPO["gradient_norm_cap"]),
            )
            self.optimizer.step()
            losses.append((
                float(actor_loss.detach()), float(critic_loss.detach()),
                float(event_entropy.detach()), float(mark_entropy.detach()),
                float(applied_mark_entropy.detach()), float(norm),
            ))
        values = np.asarray(losses, dtype=np.float64)
        return PPOUpdate(
            optimizer_steps=int(PPO["epochs"]), actor_loss=float(values[:, 0].mean()),
            critic_loss=float(values[:, 1].mean()), event_entropy=float(values[:, 2].mean()),
            mark_entropy=float(values[:, 3].mean()), applied_mark_entropy=float(values[:, 4].mean()),
            maximum_gradient_norm=float(values[:, 5].max()),
            boundary_rows=len(flat), policy_rows=int(policy_rows.sum()),
            complete_episodes=len(rows_by_episode),
            actor_global_episode_scale=actor_scale,
            actor_joint_rows_by_schedule={
                schedule: sum(
                    int(policy_rows[episode_index == i].sum())
                    for i, value in enumerate(schedule_names) if value == schedule
                ) for schedule in TRAIN_SCHEDULES
            },
            critic_row_weight_sums=tuple(
                float(torch.full_like(
                    targets_t[episode_index == i], 1.0 / len(rows_by_episode[i])
                ).sum())
                for i in range(len(rows_by_episode))
            ),
            episodes_by_schedule=episodes_by_schedule,
            behavior_actor_log_prob_cached_before_epochs=True,
            behavior_critic_values_cached_before_epochs=True,
            lambda_returns_cached_before_epochs=True,
            terminal_behavior_value=0.0,
            advantage_normalization=False,
            value_clipping=False,
            value_coefficient_applications=1,
        )

    def checkpoint(self) -> dict[str, object]:
        return {
            "treatment_arm": self.arm,
            "seed": self.seed,
            "actor": self.actor.state_dict(),
            "critic": self.critic.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "actor_parameter_count": self.actor_parameter_count,
            "critic_parameter_count": self.critic_parameter_count,
        }
