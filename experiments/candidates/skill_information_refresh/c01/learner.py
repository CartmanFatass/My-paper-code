"""One small local-observation PPO scheduler; fixed controllers are never trained."""

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .host import OBS_SIZE, simple_requests


class Scheduler(nn.Module):
    def __init__(self):
        super().__init__()
        # Separate networks: value learning cannot silently train a masked actor.
        self.actor = nn.Sequential(nn.Linear(OBS_SIZE, 32), nn.Tanh(),
            nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, 1))
        self.critic = nn.Sequential(nn.Linear(OBS_SIZE, 32), nn.Tanh(),
            nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, 1))
        for net in (self.actor, self.critic):
            for layer in net:
                if isinstance(layer, nn.Linear):
                    nn.init.orthogonal_(layer.weight, 2 ** .5)
                    nn.init.zeros_(layer.bias)
        nn.init.orthogonal_(self.actor[-1].weight, .01)
        nn.init.constant_(self.actor[-1].bias, -1.1)
        nn.init.orthogonal_(self.critic[-1].weight, 1)

    def forward(self, features):
        return self.actor(features).squeeze(-1), self.critic(features).squeeze(-1)


def build_scheduler(seed):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(seed))
        return Scheduler()


def flat_parameters(module):
    return torch.cat([p.detach().flatten() for p in module.parameters()]).clone()


def log_probability(logits, actions):
    return -F.binary_cross_entropy_with_logits(logits, actions, reduction="none")


@dataclass
class Rollout:
    features: torch.Tensor
    actions: torch.Tensor
    old_logp: torch.Tensor
    values: torch.Tensor
    rewards: torch.Tensor
    mask: torch.Tensor


def collect(host, *, model=None, rng=None, arm="LEARNED", stochastic=False,
            distance_delta=2, age_limit=None, counts=None, phase="eval", retain_trace=False):
    if arm == "LEARNED" and model is None:
        raise ValueError("learned scheduling requires a model")
    if stochastic and rng is None:
        raise ValueError("stochastic collection requires its explicit RNG")
    features, actions, logps, values, rewards, masks = [], [], [], [], [], []
    sent_trace = []
    while host.t < host.horizon:
        view = host.view()
        x = torch.from_numpy(view.features())
        mask = torch.from_numpy(view.choice_mask)
        if model is not None and arm == "LEARNED":
            with torch.no_grad():
                logits, value = model(x)
                probability = logits.sigmoid()
                requested = (torch.rand(host.batch, generator=rng) < probability if stochastic
                             else probability >= .5)
                action = requested.float()
                lp = log_probability(logits, action)
        else:
            requested = torch.from_numpy(simple_requests(view, arm, distance_delta, age_limit))
            action = requested.float()
            value = lp = torch.zeros(host.batch)
        if stochastic or retain_trace:
            features.append(x)
            actions.append(action)
            masks.append(mask)
        if stochastic:
            logps.append(lp)
            values.append(value)
        if retain_trace:
            sent_trace.append(view.available & (requested.numpy() | view.forced))
        reward = host.step(requested.numpy())
        if stochastic:
            rewards.append(torch.from_numpy(reward))
        if counts is not None:
            counts[f"{phase}_transitions"] += host.batch
            counts[f"{phase}_choice_opportunities"] += int(mask.sum())
    if counts is not None:
        counts[f"{phase}_episodes"] += host.batch
    rollout = None
    if stochastic:
        rollout = Rollout(*(torch.stack(xs) for xs in (features, actions, logps, values, rewards, masks)))
    trace = None
    if retain_trace:
        trace = dict(features=torch.stack(features).numpy().transpose(1, 0, 2),
            requested=torch.stack(actions).numpy().T.astype(bool),
            choice_mask=torch.stack(masks).numpy().T,
            sent=np.stack(sent_trace).T,
            world_ids=np.asarray(host.worlds.ids, dtype=np.int64))
    return host.rows(), rollout, trace


def advantages(rollout, gamma=.99, lam=.95):
    """H is an actual terminal boundary; no truncation bootstrap is omitted."""
    result = torch.zeros_like(rollout.rewards)
    carry = torch.zeros_like(rollout.rewards[0])
    next_value = torch.zeros_like(carry)
    for tick in reversed(range(len(result))):
        delta = rollout.rewards[tick] + gamma * next_value - rollout.values[tick]
        carry = delta + gamma * lam * carry
        result[tick] = carry
        next_value = rollout.values[tick]
    return result, result + rollout.values


def update(model, optimizer, rollout, epochs=4, record_update=None):
    adv, returns = advantages(rollout)
    x = rollout.features.flatten(0, 1)
    action = rollout.actions.flatten()
    old_logp = rollout.old_logp.flatten()
    mask = rollout.mask.flatten()
    advantage = adv.flatten()
    target = returns.flatten()
    if mask.any():
        selected = advantage[mask]
        advantage = (advantage - selected.mean()) / (selected.std(unbiased=False) + 1e-8)
    records = []
    for epoch in range(epochs):
        logits, value = model(x)
        value_loss = .5 * (value - target).square().mean()
        if mask.any():
            ratio = (log_probability(logits[mask], action[mask]) - old_logp[mask]).exp()
            policy_loss = -torch.minimum(ratio * advantage[mask],
                ratio.clamp(.8, 1.2) * advantage[mask]).mean()
            entropy = (F.softplus(logits[mask]) - logits[mask].sigmoid() * logits[mask]).mean()
        else:
            policy_loss = entropy = torch.tensor(0., dtype=x.dtype)
        loss = policy_loss + .5 * value_loss - .01 * entropy
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite PPO loss")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient = torch.nn.utils.clip_grad_norm_(model.parameters(), .5)
        if not torch.isfinite(gradient):
            raise FloatingPointError("non-finite PPO gradient")
        optimizer.step()
        record = dict(epoch=epoch, loss=float(loss.detach()),
            policy_loss=float(policy_loss.detach()), value_loss=float(value_loss.detach()),
            entropy=float(entropy.detach()), gradient_norm=float(gradient),
            transitions=len(x), actor_samples=int(mask.sum()))
        records.append(record)
        if record_update is not None:
            record_update(record)
    return records
