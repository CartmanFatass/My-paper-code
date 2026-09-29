"""Categorical PPO over measured finite-horizon macro returns."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

from .control import FEATURE_DIM


FIT_SEEDS = (2026092911, 2026092912, 2026092913)
EVAL_IDS = tuple(range(2026093001, 2026093065))


def training_world_ids(seed, count=512):
    rng = np.random.default_rng(np.random.SeedSequence([int(seed), 0x524543]))
    result = []
    seen = set(EVAL_IDS)
    while len(result) < count:
        value = int(rng.integers(1, 2**31))
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


class Policy(nn.Module):
    def __init__(self):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(FEATURE_DIM, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh())
        self.actor = nn.Linear(128, 16)
        self.critic = nn.Linear(128, 1)
        for layer in self.body:
            if isinstance(layer, nn.Linear):
                nn.init.orthogonal_(layer.weight, math.sqrt(2))
                nn.init.zeros_(layer.bias)
        nn.init.orthogonal_(self.actor.weight, 0.01)
        nn.init.zeros_(self.actor.bias)
        nn.init.orthogonal_(self.critic.weight, 1.0)
        nn.init.zeros_(self.critic.bias)

    def forward(self, feature):
        hidden = self.body(feature)
        return self.actor(hidden), self.critic(hidden).squeeze(-1)

    @torch.no_grad()
    def choose(self, feature, *, generator=None, deterministic=False):
        logits, value = self(torch.as_tensor(feature, dtype=torch.float32))
        distribution = torch.distributions.Categorical(logits=logits)
        if deterministic:
            action = torch.argmax(logits)
        else:
            action = torch.multinomial(distribution.probs, 1, generator=generator).squeeze(0)
        return int(action), float(distribution.log_prob(action)), float(value), float(distribution.entropy())


@dataclass
class MacroTransition:
    feature: np.ndarray
    action: int
    log_prob: float
    value: float
    start: int
    stop: int
    reward: float


def episode_gae(transitions, lam=0.95):
    """Gamma=1; the finite H500 endpoint has zero future value."""
    if not transitions:
        raise ValueError("training episode has no learned decisions")
    advantage = np.empty(len(transitions), dtype=np.float32)
    running = 0.0
    next_value = 0.0
    for index in reversed(range(len(transitions))):
        row = transitions[index]
        if row.stop <= row.start or (index and transitions[index-1].stop != row.start):
            raise ValueError("macro intervals must be positive and contiguous")
        delta = row.reward + next_value - row.value
        running = delta + lam * running
        advantage[index] = running
        next_value = row.value
    returns = advantage + np.asarray([row.value for row in transitions], dtype=np.float32)
    return advantage, returns


def ppo_update(policy, optimizer, episodes, minibatch_rng):
    rows = [row for episode in episodes for row in episode]
    if not rows:
        raise ValueError("cannot update on a forced-only collection")
    gaes = [episode_gae(episode) for episode in episodes]
    features = torch.as_tensor(np.stack([row.feature for row in rows]))
    actions = torch.tensor([row.action for row in rows], dtype=torch.long)
    old_log_probs = torch.tensor([row.log_prob for row in rows], dtype=torch.float32)
    advantages = torch.as_tensor(np.concatenate([item[0] for item in gaes]))
    returns = torch.as_tensor(np.concatenate([item[1] for item in gaes]))
    advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)
    metrics = []
    # Every collected row is used exactly once per epoch; array_split retains tails.
    for _ in range(4):
        for indices in np.array_split(minibatch_rng.permutation(len(rows)), 4):
            if not len(indices):
                raise ValueError("fewer than four macro transitions in a collection")
            logits, values = policy(features[indices])
            distribution = torch.distributions.Categorical(logits=logits)
            log_probs = distribution.log_prob(actions[indices])
            log_ratio = log_probs - old_log_probs[indices]
            ratio = log_ratio.exp()
            unclipped = -advantages[indices] * ratio
            clipped = -advantages[indices] * ratio.clamp(0.8, 1.2)
            actor_loss = torch.maximum(unclipped, clipped).mean()
            value_loss = 0.5 * (values - returns[indices]).square().mean()
            entropy = distribution.entropy().mean()
            loss = actor_loss + 0.5 * value_loss - 0.01 * entropy
            if not torch.isfinite(loss):
                raise FloatingPointError("nonfinite PPO loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            grad_norm = nn.utils.clip_grad_norm_(policy.parameters(), 0.5, error_if_nonfinite=True)
            optimizer.step()
            metrics.append({
                "actor_loss": float(actor_loss.detach()), "value_loss": float(value_loss.detach()),
                "entropy": float(entropy.detach()), "gradient_norm_before_clip": float(grad_norm),
                "approx_kl": float(((ratio - 1) - log_ratio).mean().detach()),
                "clip_fraction": float(((ratio - 1).abs() > .2).float().mean().detach()),
            })
    return {
        "optimizer_updates": len(metrics), "macro_rows": len(rows),
        "optimizer_row_exposures": 4 * len(rows),
        **{key: float(np.mean([row[key] for row in metrics])) for key in metrics[0]},
    }


def parameter_vector(policy):
    return torch.cat([parameter.detach().cpu().ravel() for parameter in policy.parameters()]).clone()
