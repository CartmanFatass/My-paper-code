"""Fixed C-prior categorical law and isolated CPU random addresses for B03."""

import hashlib
import math
import operator

import torch
from torch import nn
from torch.nn import functional as F

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Critic


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.table = nn.Parameter(torch.zeros(27, 26, dtype=torch.float32, device='cpu'))
        options = dict(dtype=torch.float32, device='cpu')
        self.mlp = nn.Sequential(nn.Linear(120, 64, **options), nn.Tanh(),
                                 nn.Linear(64, 64, **options), nn.Tanh(),
                                 nn.Linear(64, 27, **options))
        with torch.no_grad():
            self.mlp[4].weight.zero_()
            self.mlp[4].bias.zero_()

    def forward(self, context, c_index):
        if (context.shape[-1:] != (120,) or context.shape[:-1] != c_index.shape
                or context.dtype != torch.float32 or context.device.type != 'cpu'
                or c_index.dtype != torch.long or c_index.device.type != 'cpu'):
            raise ValueError('expected FP32 CPU context[...,120] and long CPU c_index[...]')
        if not torch.isfinite(context).all():
            raise FloatingPointError('nonfinite actor context')
        if (c_index < 0).any() or (c_index >= 27).any():
            raise ValueError('C indices must be in [0,27)')
        actions = torch.arange(27, device='cpu')
        diagonal = actions == c_index[..., None]
        # Each stored row is ordered by action, omitting its fixed diagonal.
        offsets = (actions - (actions >= c_index[..., None]).long()).clamp_min(0)
        table = self.table[c_index].gather(-1, offsets)
        table = torch.where(diagonal, 0.0, table)
        prior = math.log(234.0) * F.one_hot(c_index, 27).to(torch.float32)
        return prior + table + self.mlp(context)


def templates(master):
    """Draw W1,b1,W2,b2 after reseeding; leave caller CPU RNG unchanged."""
    master = operator.index(master)
    with torch.random.fork_rng(devices=[]):
        actor = Actor()
        torch.manual_seed(100000 * master + 11)
        with torch.no_grad():
            for layer in (actor.mlp[0], actor.mlp[2]):
                bound = 1 / math.sqrt(layer.in_features)
                layer.weight.uniform_(-bound, bound)
                layer.bias.uniform_(-bound, bound)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * master + 17)
        critic = Critic()
    return actor, critic


def optimizers(actor, critic):
    options = dict(betas=(.9, .999), eps=1e-8, weight_decay=0,
                   amsgrad=False, foreach=False, fused=False)
    aopt = torch.optim.Adam([{'params': [actor.table], 'lr': .01},
                            {'params': actor.mlp.parameters(), 'lr': .0003}], **options)
    copt = torch.optim.Adam(critic.parameters(), lr=.0003, **options)
    return aopt, copt


def _validate_logits(logits):
    if (logits.shape[-1:] != (27,) or logits.dtype != torch.float32
            or logits.device.type != 'cpu'):
        raise ValueError('expected FP32 CPU logits[...,27]')
    if not torch.isfinite(logits).all():
        raise FloatingPointError('nonfinite categorical logits')


def categorical_terms(logits, actions):
    """Density belongs to the requested category, even for physical aliases."""
    _validate_logits(logits)
    if (actions.shape != logits.shape[:-1] or actions.dtype != torch.long
            or actions.device.type != 'cpu'
            or (actions < 0).any() or (actions >= 27).any()):
        raise ValueError('expected matching long CPU actions in [0,27)')
    log_probs = logits.log_softmax(dim=-1)
    logp = log_probs.gather(-1, actions.unsqueeze(-1)).squeeze(-1)
    entropy = -(log_probs.exp() * log_probs).sum(dim=-1)
    if not torch.isfinite(logp).all() or not torch.isfinite(entropy).all():
        raise FloatingPointError('nonfinite categorical density')
    return logp, entropy


def address_seed(domain, master, world_seed, macro_index, agent_index):
    if domain not in ('train', 'eval'):
        raise ValueError('categorical domain must be train or eval')
    fields = tuple(operator.index(item) for item in
                   (master, world_seed, macro_index, agent_index))
    if any(item < 0 for item in fields):
        raise ValueError('address integers must be nonnegative')
    address = 'b03-c-prior-v1|' + domain + '|' + '|'.join(map(str, fields))
    return int.from_bytes(hashlib.sha256(address.encode('ascii')).digest()[:8],
                          'little') & ((1 << 63) - 1)


def sample_actions(logits, *, domain=None, master=None, world_seed=None,
                   macro_index=None, greedy=False):
    """One [5,27] clock, with one fresh generator and multinomial per agent."""
    _validate_logits(logits)
    if logits.shape != (5, 27):
        raise ValueError('sample_actions requires one clock of logits[5,27]')
    seeds = None
    if greedy:
        actions = logits.argmax(dim=-1)
    else:
        seeds = torch.tensor([address_seed(domain, master, world_seed, macro_index, agent)
                              for agent in range(5)], dtype=torch.long, device='cpu')
        actions = torch.stack([
            torch.multinomial(logits[agent].softmax(dim=-1), 1,
                              generator=torch.Generator(device='cpu').manual_seed(int(seeds[agent])))[0]
            for agent in range(5)])
    logp, entropy = categorical_terms(logits, actions)
    return actions, logp, entropy, seeds
