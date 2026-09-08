"""Shared recurrent PPO and the in-memory full Adam treatment fork."""
import copy
from dataclasses import dataclass

import torch
from torch import nn
from torch.distributions import Categorical


class RecurrentPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Linear(18, 64)
        self.gru = nn.GRU(64, 64, num_layers=1, batch_first=True, bias=True,
                          dropout=0, bidirectional=False)
        self.actor = nn.Linear(64, 4)
        self.critic = nn.Linear(64, 1)

    def forward(self, obs, hidden=None):
        features, hidden = self.gru(torch.tanh(self.encoder(obs)), hidden)
        return self.actor(features), self.critic(features).squeeze(-1), hidden


def make_optimizer(model):
    return torch.optim.Adam(model.parameters(), lr=0.0003, betas=(0.9, 0.999),
                            eps=1e-8, weight_decay=0, amsgrad=False,
                            foreach=False, fused=False)


def generator(seed):
    return torch.Generator(device='cpu').manual_seed(seed)


def training_streams(seed, adaptation=False):
    offset = 11 if adaptation else 1
    return {name: generator(seed + offset + i)
            for i, name in enumerate(('light', 'action', 'shuffle'))}


@dataclass
class Agent:
    model: RecurrentPolicy
    optimizer: torch.optim.Adam
    streams: dict
    global_steps: int = 0


def fork_agents(prefix, seed):
    streams = training_streams(seed, adaptation=True)
    arms = {}
    for name in ('CARRY', 'RESET'):
        model = copy.deepcopy(prefix.model)
        optimizer = make_optimizer(model)
        optimizer.load_state_dict(copy.deepcopy(prefix.optimizer.state_dict()))
        if name == 'RESET':
            optimizer.state.clear()
        private = {}
        for key, rng in streams.items():
            private[key] = generator(0)
            private[key].set_state(rng.get_state().clone())
        arms[name] = Agent(model, optimizer, private, prefix.global_steps)
    return arms


def compute_gae(rewards, values):
    values = values.detach()
    advantages = torch.zeros_like(rewards)
    following_value = torch.zeros_like(values[:, 0])
    following_advantage = torch.zeros_like(following_value)
    for t in reversed(range(rewards.shape[1])):
        delta = rewards[:, t] + following_value - values[:, t]
        following_advantage = delta + 0.95 * following_advantage
        advantages[:, t] = following_advantage
        following_value = values[:, t]
    return advantages.detach(), (advantages + values).detach()


def clipped_policy_loss(ratio, advantages):
    return -torch.minimum(ratio * advantages,
                          ratio.clamp(0.8, 1.2) * advantages).mean()


def update(agent, rollout, check_deadline, record):
    """Record even an interrupted minibatch sequence, counting real Adam calls."""
    steps = 0
    losses = []
    complete = False
    try:
        advantages, targets = compute_gae(rollout['rewards'], rollout['values'])
        advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)
        for _ in range(4):
            order = torch.randperm(16, generator=agent.streams['shuffle'])
            for indices in order.split(4):
                check_deadline()
                logits, values, _ = agent.model(rollout['obs'][indices])
                distribution = Categorical(logits=logits)
                ratio = (distribution.log_prob(rollout['actions'][indices])
                         - rollout['log_probs'][indices].detach()).exp()
                policy = clipped_policy_loss(ratio, advantages[indices])
                value = (values - targets[indices]).square().mean()
                entropy = distribution.entropy().mean()
                loss = policy + 0.5 * value - 0.01 * entropy
                agent.optimizer.zero_grad()
                loss.backward()
                norm = nn.utils.clip_grad_norm_(agent.model.parameters(), 0.5)
                check_deadline()
                agent.optimizer.step()
                agent.global_steps += 1
                steps += 1
                losses.append((policy.item(), value.item(), entropy.item(), norm.item()))
        complete = True
    finally:
        record(dict(optimizer_steps=steps, total_global_steps=agent.global_steps,
                    complete_update=complete,
                    mean_policy_loss=sum(x[0] for x in losses) / steps if steps else None,
                    mean_value_loss=sum(x[1] for x in losses) / steps if steps else None,
                    mean_entropy=sum(x[2] for x in losses) / steps if steps else None,
                    max_pre_clip_gradient_norm=max((x[3] for x in losses), default=None)))


def parameters(model):
    return torch.cat([p.detach().flatten() for p in model.parameters()]).clone()


def adam_summary(agent):
    states = list(agent.optimizer.state.values())
    steps = [float(s['step']) for s in states]
    return dict(global_steps=agent.global_steps, state_entries=len(states),
                step_min=min(steps, default=0), step_max=max(steps, default=0),
                exp_avg_norm=sum(float(s['exp_avg'].square().sum()) for s in states) ** 0.5,
                exp_avg_sq_norm=sum(float(s['exp_avg_sq'].square().sum()) for s in states) ** 0.5)
