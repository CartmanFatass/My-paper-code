"""Same-information DENSE motion learners; only LEARNED has sampled sends."""

import math
import torch
from torch import nn
from torch.nn import functional as F

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob, sample

INPUT_SIZE, CRITIC_SIZE = 171, 451


class DenseEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.raw = nn.Linear(INPUT_SIZE, 64)
        self.hidden = nn.Linear(INPUT_SIZE, 16)
        self.context = nn.Linear(16, 64, bias=False)
        nn.init.zeros_(self.hidden.bias)
        nn.init.zeros_(self.context.weight)

    def forward(self, x):
        return self.raw(x) + self.context(torch.tanh(self.hidden(x)))


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = DenseEncoder()
        self.gru = nn.GRU(64, 64)
        self.mean = nn.Linear(64, 3)
        self.log_std = nn.Parameter(torch.zeros(3))
        self.duration = None  # Reuse the intact sampled primitive-motion function.
        self.send = None

    def forward(self, observations, hidden):
        recurrent, hidden = self.gru(torch.tanh(self.encoder(observations)), hidden)
        return self.mean(recurrent), recurrent, hidden


class Critic(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(nn.Linear(CRITIC_SIZE, 128), nn.Tanh(),
                                     nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 1))

    def forward(self, x):
        return self.network(x).squeeze(-1)


def build_arm(master, arm):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * master + 11)
        actor, critic = Actor(), Critic()
        if arm == "LEARNED":
            torch.manual_seed(100000 * master + 12)
            actor.send = nn.Linear(64, 1)
            nn.init.zeros_(actor.send.weight)
            nn.init.zeros_(actor.send.bias)
    return actor, critic


def action_terms(actor, mean, recurrent, u, sends, eligible):
    logp = tanh_log_prob(u, mean, actor.log_std)
    gaussian_entropy = (actor.log_std.clamp(-5, 2) + .5 * math.log(2 * math.pi * math.e)).sum()
    entropy = torch.ones_like(logp).sum(-1) * gaussian_entropy
    if actor.send is not None:
        logits = actor.send(recurrent).squeeze(-1)
        send_lp = -F.binary_cross_entropy_with_logits(logits, sends.float(), reduction="none")
        bern_entropy = F.softplus(logits) - logits * logits.sigmoid()
        logp = logp + torch.where(eligible, send_lp, 0)
        entropy = entropy + torch.where(eligible, bern_entropy, 0).sum(-1)
    return logp, entropy


def sample_actions(actor, mean, recurrent, eligible, t, motion_rng, send_rng):
    u, _ = sample(actor, mean, recurrent, [True] * 5, False, motion_rng, send_rng)
    sends = torch.zeros(5, dtype=torch.bool)
    if actor.send is None:
        sends[t % 5] = eligible[t % 5]
    else:
        p = actor.send(recurrent[eligible]).squeeze(-1).sigmoid()
        sends[eligible] = torch.rand(int(eligible.sum()), generator=send_rng) < p
    return u, sends


def snapshot(actor, critic):
    groups = {"actor": list(actor.parameters()), "critic": list(critic.parameters())}
    if actor.send is not None:
        groups["send"] = list(actor.send.parameters())
    return {k: torch.cat([p.detach().flatten() for p in group]).clone() for k, group in groups.items()}


def exposure(initial, actor, critic):
    current = snapshot(actor, critic)
    answer = {}
    for name, before in initial.items():
        initial_norm = float(before.norm())
        movement = float((current[name] - before).norm())
        answer[name] = dict(parameters=before.numel(), initial_norm=initial_norm,
                            displacement=movement, relative_displacement=(movement / initial_norm if initial_norm else None))
    return answer
