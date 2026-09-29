"""Same-history categorical actor and independent native centralized critic."""

import torch
from torch import nn

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Critic


class SetActor(nn.Module):
    def __init__(self):
        super().__init__()
        self.point = nn.Sequential(nn.Linear(7, 64), nn.Tanh(),
                                   nn.Linear(64, 64), nn.Tanh())
        self.actor = nn.Sequential(nn.Linear(235, 128), nn.Tanh(),
                                   nn.Linear(128, 64), nn.Tanh(), nn.Linear(64, 27))

    def forward(self, context, points, valid):
        if (context.shape[-1] != 107 or points.shape[-2:] != (64, 7)
                or valid.shape[-1] != 64 or context.shape[:-1] != points.shape[:-2]
                or context.shape[:-1] != valid.shape[:-1]):
            raise ValueError('expected context[...,107], points[...,64,7], valid[...,64]')
        valid = valid.bool()
        encoded = self.point(torch.where(valid[..., None], points, 0.0))
        summed = torch.where(valid[..., None], encoded, 0.0).sum(dim=-2)
        mean = summed / valid.sum(dim=-1, keepdim=True).clamp_min(1)
        masked = torch.where(valid[..., None], encoded,
                             torch.finfo(encoded.dtype).min)
        maximum = masked.amax(dim=-2)
        maximum = torch.where(valid.any(dim=-1, keepdim=True), maximum, 0.0)
        return self.actor(torch.cat((context, mean, maximum), dim=-1))


def templates(master):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * int(master) + 11)
        actor = SetActor()
        critic = Critic()
    return actor, critic


def optimizers(actor, critic):
    options = dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                   amsgrad=False, foreach=False, fused=False)
    return (torch.optim.Adam(actor.parameters(), **options),
            torch.optim.Adam(critic.parameters(), **options))


def categorical_terms(logits, action):
    log_probs = logits.log_softmax(dim=-1)
    logp = log_probs.gather(-1, action.long().unsqueeze(-1)).squeeze(-1)
    entropy = -(log_probs.exp() * log_probs).sum(dim=-1)
    return logp, entropy


def sample_action(logits, generator=None, greedy=False):
    if logits.shape[-1] != 27 or not torch.isfinite(logits).all():
        raise ValueError('expected finite logits[...,27]')
    if greedy:
        action = logits.argmax(dim=-1)
    else:
        if generator is None:
            raise ValueError('sampled actions require an explicit CPU generator')
        if logits.device.type != 'cpu' or generator.device.type != 'cpu':
            raise ValueError('B02 action sampling uses CPU tensors and generator')
        probabilities = logits.softmax(dim=-1).reshape(-1, 27)
        action = torch.multinomial(probabilities, 1, generator=generator).reshape(logits.shape[:-1])
    logp, entropy = categorical_terms(logits, action)
    return action, logp, entropy
